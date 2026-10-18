"""Step 4 — Gitea: CLI admin + token, repo, issue with op-id marker in body, indexer lag, delete/close."""
from __future__ import annotations

import json
import time
import uuid

import httpx

from common import first_lines, register_secret, save_part
from svc_common import ENV, compose, exc_info

BASE = "http://localhost:3000/api/v1"
ADMIN = "actrec-admin"
REPO = "inventory-probe"
TRIALS = 5
POLL_S = 0.5
MAX_WAIT_S = 120


def gitea_cli(*args: str) -> dict:
    return compose("exec", "-T", "-u", "git", "gitea", "gitea", *args, timeout=120)


def main() -> None:
    d: dict = {}
    pw = ENV.get("GITEA_ADMIN_PASSWORD", "")
    register_secret(pw)
    ver = gitea_cli("--version")
    d["version"] = ver["out"]
    d["install"] = "non-interactive via env (INSTALL_LOCK=true, sqlite3)"
    mk = gitea_cli("admin", "user", "create", "--username", ADMIN, "--password", pw,
                   "--email", "admin@inventory.invalid", "--admin", "--must-change-password=false")
    d["admin_create"] = {"rc": mk["rc"], "msg": first_lines(mk["out"] + " " + mk["err"], 5)}
    tok = gitea_cli("admin", "user", "generate-access-token", "--username", ADMIN,
                    "--token-name", f"inv-{int(time.time())}", "--scopes", "all", "--raw")
    token = tok["out"].strip().splitlines()[-1] if tok["rc"] == 0 and tok["out"] else ""
    register_secret(token)
    d["token_create"] = {"rc": tok["rc"], "ok": bool(token), "err": first_lines(tok["err"], 5) or None}
    if not token:
        save_part("04_gitea", d)
        return
    h = {"Authorization": f"token {token}"}
    c = httpx.Client(base_url=BASE, headers=h, timeout=15)
    r = c.post("/user/repos", json={"name": REPO, "private": False, "auto_init": True})
    d["repo_create_status"] = r.status_code  # 409 if already exists on re-run
    d["indexer_config"] = compose("exec", "-T", "gitea", "sh", "-c",
                                  "grep -A3 '^\\[indexer\\]' /data/gitea/conf/app.ini || echo 'no [indexer] section (defaults: ISSUE_INDEXER_TYPE=bleve)'")["out"]

    trials = []
    first_issue = None
    for i in range(TRIALS):
        op = str(uuid.uuid4())
        body = f"Probe issue for the inventory.\n\nop-id: {op}\n\nTrailing line with unicode: é ✓\n"
        t_create = time.perf_counter()
        r = c.post(f"/repos/{ADMIN}/{REPO}/issues", json={"title": f"inventory probe {i + 1}", "body": body})
        created = r.json()
        num = created["number"]
        tr: dict = {"trial": i + 1, "create_status": r.status_code, "issue_number": num}
        g = c.get(f"/repos/{ADMIN}/{REPO}/issues/{num}").json()
        tr["body_byte_exact"] = g["body"].encode() == body.encode()
        tr["marker_line_present"] = f"op-id: {op}" in g["body"].splitlines()
        lst = c.get(f"/repos/{ADMIN}/{REPO}/issues", params={"state": "open", "type": "issues", "limit": 50}).json()
        tr["plain_list_has_issue_immediately"] = any(x["number"] == num for x in lst)
        found_global = found_repo = None
        while time.perf_counter() - t_create < MAX_WAIT_S and (found_global is None or found_repo is None):
            el = round(time.perf_counter() - t_create, 2)
            if found_global is None:
                s = c.get("/repos/issues/search", params={"q": op, "state": "all", "type": "issues"})
                if s.status_code == 200 and any(x["number"] == num and x["repository"]["name"] == REPO for x in s.json()):
                    found_global = el
            if found_repo is None:
                s2 = c.get(f"/repos/{ADMIN}/{REPO}/issues", params={"q": op, "state": "all", "type": "issues"})
                if s2.status_code == 200 and any(x["number"] == num for x in s2.json()):
                    found_repo = el
            time.sleep(POLL_S)
        tr["indexer_lag_s_global_search"] = found_global
        tr["indexer_lag_s_repo_q"] = found_repo
        trials.append(tr)
        if first_issue is None:
            first_issue = (num, op)
        if i >= 1 and all(t["indexer_lag_s_global_search"] is None and t["indexer_lag_s_repo_q"] is None for t in trials):
            d["trials_stopped_early"] = "two trials never found within 120 s; stopped to respect the time budget"
            break
    d["trials"] = trials
    lags = [t["indexer_lag_s_global_search"] for t in trials if t["indexer_lag_s_global_search"] is not None]
    d["indexer_lag_global_found"] = f"{len(lags)}/{len(trials)}"
    d["indexer_lag_global_s"] = sorted(lags)
    # search on a partial token of the marker (does the tokenizer split on '-')?
    num0, op0 = first_issue
    s = c.get("/repos/issues/search", params={"q": op0.split("-")[0], "state": "all", "type": "issues"})
    d["search_by_first_uuid_segment_finds"] = s.status_code == 200 and any(x["number"] == num0 for x in s.json())
    s = c.get("/repos/issues/search", params={"q": f"op-id: {op0}", "state": "all", "type": "issues"})
    d["search_by_full_marker_line_finds"] = s.status_code == 200 and any(x["number"] == num0 for x in s.json())

    # (d) compensation: close and delete
    last = trials[-1]["issue_number"]
    r = c.patch(f"/repos/{ADMIN}/{REPO}/issues/{last}", json={"state": "closed"})
    d["close_via_api"] = {"status": r.status_code, "state_after": r.json().get("state") if r.status_code == 201 else None}
    r = c.delete(f"/repos/{ADMIN}/{REPO}/issues/{last}")
    gone = c.get(f"/repos/{ADMIN}/{REPO}/issues/{last}").status_code
    d["delete_via_api_admin"] = {"status": r.status_code, "get_after_delete": gone, "ok": r.status_code == 204 and gone == 404}
    save_part("04_gitea", d)
    print(json.dumps(d, indent=1)[:3000])


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        save_part("04_gitea_error", {"error": exc_info(e)})
        raise
