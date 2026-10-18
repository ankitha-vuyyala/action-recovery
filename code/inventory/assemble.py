"""Merge runs/inventory/parts/*.json into runs/inventory/inventory.json (one top-level key per step)."""
from __future__ import annotations

import datetime as dt
import json

from common import PARTS, RUNS, redact


def load(name: str):
    p = PARTS / f"{name}.json"
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else None


def main() -> None:
    up = load("04a_services_up") or {}
    tb = load("04_tigerbeetle") or {}
    pr = load("04_pg_redis") or {}
    if tb.get("needs_seccomp_unconfined"):
        up.setdefault("tigerbeetle", {})["time_to_healthy_s"] = tb["attempt_seccomp_unconfined"]["time_to_listening_s"]
        up["tigerbeetle"]["healthy"] = True
        up["tigerbeetle"]["note"] = ("default seccomp: io_uring PermissionDenied; time_to_healthy is the "
                                     "seccomp=unconfined start incl. format")
    services = {
        "images_and_startup": up,
        "postgres": pr.get("postgres"),
        "gitea": load("04_gitea"),
        "mailpit": load("04_mailpit"),
        "tigerbeetle": tb,
        "object_store_a_minio": {"status": "failed: image not pullable", **(up.get("minio") or {})},
        "object_store_b_seaweedfs": load("04_objstore_seaweedfs"),
        "redis": pr.get("redis"),
        "toxiproxy": load("04_toxiproxy"),
        "temporal": load("04_temporal"),
        "dbos": load("04_dbos"),
    }
    inv = {
        "meta": {"generated": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
                 "instructions": "docs/02_inventory_instructions.md",
                 "paid_model_calls": 0,
                 "redaction": "user name -> <user>, machine name -> <host>, e-mail -> <email>, home path -> ~",
                 "scripts": "code/inventory/", "compose": "docker/inventory/"},
        "step1_system": load("01_system"),
        "step2_tooling": load("02_tooling"),
        "step3_docker": load("03_docker"),
        "step4_services": services,
        "step5_resources": load("05_resources"),
        "step6_network": load("06_network"),
        "step7_models": load("07_models"),
        "step8_repositories": load("08_repos"),
        "cleanup": load("09_cleanup"),
    }
    (RUNS / "inventory.json").write_text(json.dumps(redact(inv), indent=2, ensure_ascii=False), encoding="utf-8")
    print("wrote", RUNS / "inventory.json")


if __name__ == "__main__":
    main()
