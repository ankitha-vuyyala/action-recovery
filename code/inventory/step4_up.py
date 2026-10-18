"""Step 4a — start each inventory service, time until healthy (probed from the host), record tag/digest/size."""
from __future__ import annotations

import json
import sys
import time

import httpx
import psycopg
import redis

from common import first_lines, run, save_part
from svc_common import PG_DSN, compose, tcp_open, wait_until

SERVICES = {
    "postgres": ("postgres:16", lambda: psycopg.connect(PG_DSN, connect_timeout=2).close() is None),
    "gitea": ("gitea/gitea:1.24", lambda: httpx.get("http://localhost:3000/api/healthz", timeout=2).status_code == 200),
    "mailpit": ("axllent/mailpit:latest", lambda: httpx.get("http://localhost:8025/readyz", timeout=2).status_code == 200),
    "tigerbeetle": ("ghcr.io/tigerbeetle/tigerbeetle:latest", lambda: tcp_open(3001)),
    "seaweedfs": ("chrislusf/seaweedfs:latest", lambda: httpx.get("http://localhost:8333/", timeout=2).status_code in (200, 403)),
    "redis": ("redis:7", lambda: redis.Redis(port=6379, socket_timeout=2).ping()),
    "toxiproxy": ("ghcr.io/shopify/toxiproxy:latest", lambda: httpx.get("http://localhost:8474/version", timeout=2).status_code == 200),
    "temporal": ("temporalio/temporal:latest", lambda: tcp_open(7233) and httpx.get("http://localhost:8233/", timeout=2).status_code == 200),
}


def image_info(ref: str) -> dict:
    r = run(["docker", "image", "inspect", ref, "--format", "{{json .}}"])
    if r["rc"] != 0:
        return {"requested": ref, "error": first_lines(r["err"])}
    j = json.loads(r["out"])
    ver_labels = {k: v for k, v in (j.get("Config", {}).get("Labels") or {}).items()
                  if "version" in k.lower()}
    return {"requested": ref, "resolved_tag": ref, "digest": (j.get("RepoDigests") or [None])[0],
            "image_id": j["Id"], "size_mb": round(j["Size"] / 1e6, 1), "created": j.get("Created"),
            "version_labels": ver_labels}


def container_running(svc: str) -> bool:
    r = compose("ps", "--format", "json", svc)
    return '"running"' in r["out"].lower()


def main() -> None:
    only = sys.argv[1:] or list(SERVICES)
    out = {}
    for svc in only:
        ref, probe = SERVICES[svc]
        rec = {"image": image_info(ref)}
        t0 = time.perf_counter()
        up = compose("up", "-d", svc)
        rec["compose_up"] = {"rc": up["rc"], "err_tail": first_lines(up["err"]) if up["rc"] else None}
        tth = wait_until(lambda: container_running(svc) and probe(), timeout=180) if up["rc"] == 0 else None
        rec["time_to_healthy_s"] = round(time.perf_counter() - t0, 2) if tth is not None else None
        rec["healthy"] = tth is not None
        if not rec["healthy"]:
            logs = compose("logs", "--no-color", "--tail", "40", svc)
            rec["logs_tail"] = first_lines(logs["out"] + "\n" + logs["err"], 40)
        out[svc] = rec
        print(svc, "healthy" if rec["healthy"] else "NOT healthy", rec["time_to_healthy_s"])
    # MinIO: record the pull failure
    if "minio" in only or not sys.argv[1:]:
        p1 = run(["docker", "pull", "minio/minio:latest"], timeout=120)
        p2 = run(["docker", "pull", "quay.io/minio/minio:latest"], timeout=120)
        out["minio"] = {"image": {"requested": "minio/minio:latest", "resolved_tag": None, "digest": None},
                        "healthy": False,
                        "pull_error": first_lines(p1["err"]),
                        "fix_attempt": {"image": "quay.io/minio/minio:latest", "pull_error": first_lines(p2["err"]),
                                        "ok": p2["rc"] == 0}}
    save_part("04a_services_up" + ("_" + "_".join(sys.argv[1:]) if sys.argv[1:] else ""), out)


if __name__ == "__main__":
    main()
