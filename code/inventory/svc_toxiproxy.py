"""Step 4 — Toxiproxy in front of PostgreSQL and Gitea: baseline latency, then one toxic at a time.

For every toxic we record what the client sees (exception, elapsed) and whether the write reached the
upstream anyway (checked directly on the upstream port, not through the proxy).
PostgreSQL: the client connection is opened *before* the toxic is added (pooled-connection case).
Gitea: a fresh HTTP connection per request (typical agent HTTP tool call).
"""
from __future__ import annotations

import concurrent.futures as cf
import json
import time
import uuid

import httpx
import psycopg

from common import first_lines, register_secret, save_part
from svc_common import ENV, PG_DSN, compose, exc_info, lat_stats

TOXI = "http://localhost:8474"
PG_PROXY_PORT, GITEA_PROXY_PORT = 26000, 26001
PG_PROXY_DSN = PG_DSN.replace("port=5432", f"port={PG_PROXY_PORT}")
ADMIN, REPO = "actrec-admin", "inventory-probe"
DEADLINE_S = 15.0

TOXICS = [
    ("latency_5s_downstream", {"type": "latency", "stream": "downstream", "attributes": {"latency": 5000, "jitter": 0}}),
    ("timeout_0_downstream", {"type": "timeout", "stream": "downstream", "attributes": {"timeout": 0}}),
    ("reset_peer_downstream", {"type": "reset_peer", "stream": "downstream", "attributes": {"timeout": 0}}),
    ("limit_data_downstream_16B", {"type": "limit_data", "stream": "downstream", "attributes": {"bytes": 16}}),
]


def gitea_token() -> str:
    r = compose("exec", "-T", "-u", "git", "gitea", "gitea", "admin", "user", "generate-access-token", "--username",
                ADMIN, "--token-name", f"toxi-{int(time.time())}", "--scopes", "all", "--raw")
    tok = r["out"].strip().splitlines()[-1] if r["rc"] == 0 and r["out"] else ""
    register_secret(tok)
    return tok


def pg_rows(op: str) -> int:
    with psycopg.connect(PG_DSN, autocommit=True) as c:
        return c.execute("select count(*) from inv_ops where op_id = %s", (op,)).fetchone()[0]


def gitea_has(op: str, h: dict) -> int:
    lst = httpx.get(f"http://localhost:3000/api/v1/repos/{ADMIN}/{REPO}/issues",
                    params={"state": "all", "type": "issues", "limit": 50}, headers=h, timeout=10).json()
    return sum(1 for x in lst if op in (x.get("body") or ""))


def set_enabled(name: str, enabled: bool) -> None:
    httpx.post(f"{TOXI}/proxies/{name}", json={"enabled": enabled}, timeout=5)


def timed(fn):
    ex = cf.ThreadPoolExecutor(1)
    t = time.perf_counter()
    fut = ex.submit(fn)
    try:
        fut.result(timeout=DEADLINE_S)
        res = {"outcome": "success", "exception": None}
    except cf.TimeoutError:
        res = {"outcome": f"no response within client deadline {DEADLINE_S:.0f}s", "exception": None}
    except Exception as e:
        res = {"outcome": "error", "exception": exc_info(e)}
    res["elapsed_s"] = round(time.perf_counter() - t, 3)
    ex.shutdown(wait=False)
    return res


def main() -> None:
    d: dict = {}
    c = httpx.Client(base_url=TOXI, timeout=5)
    d["version"] = c.get("/version").text.strip()
    c.post("/reset")
    for name in ("pg", "gitea"):
        c.delete(f"/proxies/{name}")
    r1 = c.post("/proxies", json={"name": "pg", "listen": f"0.0.0.0:{PG_PROXY_PORT}", "upstream": "postgres:5432"})
    r2 = c.post("/proxies", json={"name": "gitea", "listen": f"0.0.0.0:{GITEA_PROXY_PORT}", "upstream": "gitea:3000"})
    d["proxies_created"] = {"pg": r1.status_code, "gitea": r2.status_code}

    token = gitea_token()
    h = {"Authorization": f"token {token}"}

    # baseline latency: direct vs through proxy
    base = {}
    for label, dsn in (("pg_direct", PG_DSN), ("pg_via_proxy", PG_PROXY_DSN)):
        with psycopg.connect(dsn, autocommit=True) as conn:
            s = []
            for _ in range(20):
                t = time.perf_counter()
                conn.execute("select 1").fetchone()
                s.append(time.perf_counter() - t)
            base[label] = lat_stats(s)
    for label, port in (("gitea_direct", 3000), ("gitea_via_proxy", GITEA_PROXY_PORT)):
        with httpx.Client(timeout=10) as hc:
            s = []
            for _ in range(20):
                t = time.perf_counter()
                hc.get(f"http://localhost:{port}/api/v1/version")
                s.append(time.perf_counter() - t)
            base[label] = lat_stats(s)
    d["baseline"] = base

    results = []
    for tname, toxic in TOXICS:
        row: dict = {"toxic": tname, "spec": toxic}
        # --- PostgreSQL (connection established before toxic) ---
        op = str(uuid.uuid4())
        conn = psycopg.connect(PG_PROXY_DSN, autocommit=True)
        conn.execute("select 1").fetchone()
        add = c.post("/proxies/pg/toxics", json={"name": "t", **toxic})
        res = timed(lambda: conn.execute("insert into inv_ops(op_id, payload) values (%s, 'toxic')", (op,)))
        time.sleep(1.0)
        res["write_reached_upstream"] = pg_rows(op) > 0
        res["committed_but_response_lost"] = res["write_reached_upstream"] and res["outcome"] != "success"
        res["toxic_add_status"] = add.status_code
        c.delete("/proxies/pg/toxics/t")
        set_enabled("pg", False)  # closes lingering connections
        set_enabled("pg", True)
        try:
            conn.close()
        except Exception:
            pass
        row["postgres"] = res
        # --- Gitea (fresh HTTP connection per request) ---
        op = str(uuid.uuid4())
        add = c.post("/proxies/gitea/toxics", json={"name": "t", **toxic})

        def post():
            with httpx.Client(timeout=httpx.Timeout(DEADLINE_S - 1)) as hc:
                r = hc.post(f"http://localhost:{GITEA_PROXY_PORT}/api/v1/repos/{ADMIN}/{REPO}/issues", headers=h,
                            json={"title": f"toxic {tname}", "body": f"toxic probe\n\nop-id: {op}\n"})
                r.raise_for_status()
        res = timed(post)
        time.sleep(1.0)
        res["write_reached_upstream"] = gitea_has(op, h) > 0
        res["committed_but_response_lost"] = res["write_reached_upstream"] and res["outcome"] != "success"
        res["toxic_add_status"] = add.status_code
        c.delete("/proxies/gitea/toxics/t")
        set_enabled("gitea", False)
        set_enabled("gitea", True)
        row["gitea"] = res
        results.append(row)
        print(tname, "pg:", row["postgres"]["outcome"], row["postgres"]["write_reached_upstream"],
              "| gitea:", row["gitea"]["outcome"], row["gitea"]["write_reached_upstream"])
    d["toxics"] = results
    d["toxics_producing_committed_but_response_lost"] = sorted(
        {f"{r['toxic']}:{svc}" for r in results for svc in ("postgres", "gitea") if r[svc]["committed_but_response_lost"]})
    d["toxics_where_write_never_reached_upstream"] = sorted(
        {f"{r['toxic']}:{svc}" for r in results for svc in ("postgres", "gitea") if not r[svc]["write_reached_upstream"]})
    save_part("04_toxiproxy", d)
    print(json.dumps({k: d[k] for k in ("baseline", "toxics_producing_committed_but_response_lost",
                                        "toxics_where_write_never_reached_upstream")}, indent=1))


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        save_part("04_toxiproxy_error", {"error": exc_info(e)})
        raise
