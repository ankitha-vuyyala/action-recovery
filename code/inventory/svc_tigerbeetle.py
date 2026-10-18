"""Step 4 — TigerBeetle: default seccomp attempt, seccomp=unconfined retry, idempotent transfer check."""
from __future__ import annotations

import concurrent.futures as cf
import json
import time

import tigerbeetle as tb

from common import PARTS, first_lines, save_part
from svc_common import compose, exc_info, tcp_open, wait_until

OVR = ["compose.tb-unconfined.yml"]
FIXED_TRANSFER_ID = 0x0123456789ABCDEF_FEDCBA9876543210  # fixed 128-bit id


def with_timeout(fn, seconds=20):
    ex = cf.ThreadPoolExecutor(1)
    try:
        return ex.submit(fn).result(timeout=seconds)
    finally:
        ex.shutdown(wait=False)


def fresh_start(extra_files):
    compose("rm", "-sf", "tigerbeetle", extra_files=extra_files)
    compose("run", "--rm", "--no-deps", "--entrypoint", "sh", "tigerbeetle", "-c", "rm -f /data/0_0.tigerbeetle",
            extra_files=extra_files)
    t0 = time.perf_counter()
    up = compose("up", "-d", "--force-recreate", "tigerbeetle", extra_files=extra_files)

    def listening():
        logs = compose("logs", "--no-color", "tigerbeetle", extra_files=extra_files)["out"]
        if "error" in logs.lower() and "listening" not in logs:
            raise RuntimeError("failed")
        return "listening on" in logs and tcp_open(3001)

    ok = wait_until(listening, timeout=90) is not None
    logs = compose("logs", "--no-color", "--tail", "20", "tigerbeetle", extra_files=extra_files)["out"]
    return {"compose_rc": up["rc"], "started": ok,
            "time_to_listening_s": round(time.perf_counter() - t0, 2) if ok else None,
            "log_tail": first_lines(logs, 20)}


def main() -> None:
    d: dict = {}
    d["attempt_default_seccomp"] = fresh_start([])
    if not d["attempt_default_seccomp"]["started"]:
        d["attempt_seccomp_unconfined"] = fresh_start(OVR)
    started = d["attempt_default_seccomp"]["started"] or d.get("attempt_seccomp_unconfined", {}).get("started")
    d["started"] = bool(started)
    d["needs_seccomp_unconfined"] = not d["attempt_default_seccomp"]["started"] and bool(started)
    if not started:
        save_part("04_tigerbeetle", d)
        return
    alloc = [l for l in d.get("attempt_seccomp_unconfined", d["attempt_default_seccomp"])["log_tail"].splitlines()
             if "Allocated" in l]
    d["memory_allocated_log"] = alloc[0].split("info(main): ")[-1] if alloc else None

    checks: dict = {}
    try:
        client = tb.ClientSync(cluster_id=0, replica_addresses="3001")
        a1, a2 = tb.id(), tb.id()
        t0 = time.perf_counter()
        res = with_timeout(lambda: client.create_accounts([tb.Account(id=a1, ledger=1, code=1),
                                                          tb.Account(id=a2, ledger=1, code=1)]))
        checks["create_accounts"] = [r.status.name for r in res]
        checks["first_request_s"] = round(time.perf_counter() - t0, 3)
        tid = FIXED_TRANSFER_ID + int(time.time())  # stays fixed within this run; unique across re-runs
        tr = tb.Transfer(id=tid, debit_account_id=a1, credit_account_id=a2, amount=10, ledger=1, code=1)
        r1 = with_timeout(lambda: client.create_transfers([tr]))
        r2 = with_timeout(lambda: client.create_transfers([tr]))
        checks["transfer_id_hex"] = hex(tid)
        checks["first_submit_status"] = r1[0].status.name
        checks["second_submit_status"] = r2[0].status.name
        checks["duplicate_is_exists"] = r2[0].status.name == "EXISTS"
        lk = with_timeout(lambda: client.lookup_transfers([tid]))
        checks["lookup_found"] = len(lk) == 1 and lk[0].id == tid
        bal = with_timeout(lambda: client.lookup_accounts([a1, a2]))
        checks["debits_posted_a1"] = bal[0].debits_posted
        checks["credits_posted_a2"] = bal[1].credits_posted
        checks["applied_once"] = bal[0].debits_posted == 10
        t = []
        for _ in range(20):
            s = time.perf_counter()
            with_timeout(lambda: client.lookup_transfers([tid]))
            t.append(time.perf_counter() - s)
        t.sort()
        checks["lookup_latency_median_ms"] = round(t[10] * 1000, 3)
        client.close()
    except Exception as e:  # record exact error
        checks["error"] = exc_info(e)
    d["checks"] = checks
    save_part("04_tigerbeetle", d)
    print(json.dumps({k: v for k, v in d.items() if k != "attempt_default_seccomp"}, indent=1, default=str)[:1500])


if __name__ == "__main__":
    main()
