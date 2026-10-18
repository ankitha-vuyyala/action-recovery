"""Run the whole follow-up study (docs/07_followup_plan.md) unattended, resumably, under a hard spending cap.

    .venv\\Scripts\\python code\\tools\\followup.py

Order: freeze check -> scripted grids (free) -> plan-free Settle with the three original models -> frontier price
check (12 episodes) -> frontier grid only if the projection fits the cap -> analysis. Every step appends a line to
runs/FOLLOWUP_STATUS.txt. Re-running the script resumes where it stopped (finished episodes are skipped and paid
model responses are cached). Never reads or prints .env.

Spending: the first run records the ledger total in runs/followup_budget.json; the ceiling for ALL follow-up model
calls is that total + 9.90 US$. guarded_grids.py kills a grid that crosses it, and the frontier grid is skipped if
its projected cost does not fit.
"""
from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RUNS = ROOT / "runs"
STATUS = RUNS / "FOLLOWUP_STATUS.txt"
BUDGET = RUNS / "followup_budget.json"
CAP_NEW_USD = 9.90
MAIN_DIGEST = "dd8b4adba131"            # the main study's final freeze (amendment 2)
PY = sys.executable
sys.path.insert(0, str(ROOT / "code"))
from tools.guarded_grids import ledger_usd  # noqa: E402

SCRIPTED = [("followup_a", "followup_a"), ("followup_b", "followup_b"), ("followup_c", "followup_c")]
LLM_NP = [("followup_llm_np_luna", "llm:gpt-5.6-luna", "2"), ("followup_llm_np_41mini", "llm:gpt-4.1-mini", "1"),
          ("followup_llm_np_nano", "llm:gpt-5.4-nano", "1")]
FRONTIER = ("followup_llm_frontier_sol", "llm:gpt-5.6-sol")
FRONTIER_N = 268
PRICE_CHECK_N = 12


def log(msg: str) -> None:
    line = f"{time.strftime('%Y-%m-%d %H:%M:%S')} {msg}"
    print(line, flush=True)
    with STATUS.open("a", encoding="utf-8") as f:
        f.write(line + "\n")


def run(cmd: list[str], logname: str) -> int:
    (RUNS / "tmp").mkdir(parents=True, exist_ok=True)
    with (RUNS / "tmp" / f"{logname}.log").open("a", encoding="utf-8") as f:
        p = subprocess.run(cmd, cwd=ROOT, stdout=f, stderr=subprocess.STDOUT)
    return p.returncode


def records(name: str) -> list[dict]:
    f = RUNS / name / "episodes.jsonl"
    if not f.exists():
        return []
    out = []
    for line in f.read_text(encoding="utf-8").splitlines():
        try:
            out.append(json.loads(line))
        except json.JSONDecodeError:
            pass
    return out


def errors(name: str) -> int:
    return sum(1 for r in records(name) if "error" in r or "grade_error" in (r.get("grade") or {}))


def smoke_ok() -> bool:
    """Free pre-flight on the development instance: the new fault mode and read variant must realise their
    intended hidden outcome on the real services before any follow-up grid runs."""
    name = "followup_smoke"
    rc = run([PY, "code/run.py", "grid", "--name", name, "--templates", "T1", "--instances", "0",
              "--modes", "lost_ack,redelivery_late", "--variants", "exact,lookalike_other",
              "--conditions", "S2,C5a", "--workers", "3"], name)
    recs = records(name)
    problems = []
    if rc != 0 or not recs:
        problems.append(f"grid rc={rc}, records={len(recs)}")
    for r in recs:
        if "error" in r or "grade_error" in (r.get("grade") or {}):
            problems.append(f"{r.get('episode_id')}: {r.get('error') or r['grade'].get('grade_error')}")
            continue
        ep = RUNS / name / "episodes" / r["episode_id"]
        if r["variant"] == "lookalike_other":
            act = [json.loads(x) for x in (ep / "actor.jsonl").read_text(encoding="utf-8").splitlines() if x.strip()] \
                if (ep / "actor.jsonl").exists() else []
            if not act or any("error" in a or a.get("account") != "other" or not a.get("id") for a in act):
                problems.append(f"{r['episode_id']}: look-alike from the second account not created: {act[:1]}")
        if r["mode"] == "redelivery_late":
            d = [json.loads(x) for x in (ep / "dispatch.jsonl").read_text(encoding="utf-8").splitlines() if x.strip()]
            red = [x for x in d if x.get("type") == "redelivery"]
            if not red or (red[0].get("result") or {}).get("kind") != "ok":
                problems.append(f"{r['episode_id']}: delayed redelivery not executed: {red[:1]}")
    if problems:
        log("STOP: smoke check failed: " + " | ".join(problems[:5]))
        return False
    log(f"smoke check OK ({len(recs)} episodes on the development instance)")
    return True


def main() -> int:
    RUNS.mkdir(exist_ok=True)
    log("follow-up start")
    fz = ROOT / "FREEZE.json"
    if fz.exists() and json.loads(fz.read_text(encoding="utf-8")).get("digest", "").startswith(MAIN_DIGEST):
        archive = ROOT / "FREEZE_2026-10-03_amend2.json"
        if archive.exists():
            log("STOP: FREEZE.json is still the main study's freeze but the archive name is taken")
            return 2
        fz.rename(archive)
        if run([PY, "code/run.py", "freeze"], "followup_freeze") != 0:
            log("STOP: writing the follow-up freeze failed")
            return 2
        d = json.loads(fz.read_text(encoding="utf-8"))
        log(f"follow-up freeze written at {d.get('frozen_at_utc')} UTC, digest {d.get('digest')}, "
            f"{len(d.get('files', {}))} files; main-study freeze archived as {archive.name}")
    if run([PY, "code/run.py", "freeze", "--check"], "followup_freeze") != 0:
        log("STOP: freeze check failed (the working tree differs from FREEZE.json)")
        return 2
    log("freeze check OK")
    try:
        from actrec.config import stack_secrets
        if "gitea_other_token" not in stack_secrets():
            raise RuntimeError("no second Gitea user")
    except Exception as e:  # noqa: BLE001
        log(f"STOP: stack not ready ({e}); run `python code/run.py stack up` first")
        return 2
    if BUDGET.exists():
        b = json.loads(BUDGET.read_text(encoding="utf-8"))
    else:
        base = ledger_usd()
        b = {"ledger_at_start": round(base, 6), "cap_new_usd": CAP_NEW_USD, "ceiling": round(base + CAP_NEW_USD, 6),
             "recorded": time.strftime("%Y-%m-%d %H:%M:%S")}
        BUDGET.write_text(json.dumps(b, indent=1), encoding="utf-8")
    ceiling = b["ceiling"]
    log(f"budget: ledger at start ${b['ledger_at_start']:.4f}, ceiling ${ceiling:.4f} (new spending <= ${CAP_NEW_USD})")

    if not smoke_ok():
        return 2

    for name, preset in SCRIPTED:                     # free: no model calls
        for attempt in range(3):
            rc = run([PY, "code/run.py", "grid", "--name", name, "--preset", preset, "--workers", "3"], name)
            n, e = len(records(name)), errors(name)
            log(f"{name}: rc={rc} records={n} errors={e} (attempt {attempt + 1})")
            if rc == 0 and e == 0:
                break
        if errors(name):
            log(f"WARNING: {name} still has {errors(name)} errored records after 3 attempts; continuing")

    specs = [f"{n}|followup_llm_np|{d}|{r}" for n, d, r in LLM_NP]
    rc = run([PY, "code/tools/guarded_grids.py", "--max-usd", f"{ceiling:.4f}", "--"] + specs, "followup_llm_np")
    log(f"plan-free Settle grids: guard rc={rc}; ledger ${ledger_usd():.4f}; new ${ledger_usd() - b['ledger_at_start']:.4f}")
    if rc != 0:
        log("STOP: the guard stopped a model grid (budget or model error); see runs/tmp/followup_llm_np.log")
        return 2

    name, drv = FRONTIER
    spec = f"{name}|followup_llm_frontier|{drv}|1|{PRICE_CHECK_N}"
    rc = run([PY, "code/tools/guarded_grids.py", "--max-usd", f"{ceiling:.4f}", "--", spec], "followup_frontier_check")
    recs = [r for r in records(name) if r.get("usd") is not None]
    if rc != 0 or not recs:
        log(f"frontier price check failed (rc={rc}, records={len(recs)}); frontier grid NOT run")
    else:
        per = sum(r["usd"] for r in recs) / len(recs)
        left = FRONTIER_N - len(records(name))
        projected = per * left * 1.25
        room = ceiling - ledger_usd()
        log(f"frontier price check: {len(recs)} episodes, ${per:.4f}/episode, projected rest ${projected:.2f} "
            f"(x1.25 margin), room ${room:.2f}")
        if projected <= room:
            rc = run([PY, "code/tools/guarded_grids.py", "--max-usd", f"{ceiling:.4f}", "--",
                      f"{name}|followup_llm_frontier|{drv}|1"], "followup_frontier")
            log(f"frontier grid: guard rc={rc}; records={len(records(name))}; ledger ${ledger_usd():.4f}")
        else:
            log("frontier grid NOT run: the projection does not fit the cap")
    rc = run([PY, "analysis/followup.py", "--runs", "runs", "--out", "results"], "followup_analysis")
    log(f"analysis rc={rc}; total new spending ${ledger_usd() - b['ledger_at_start']:.4f}")
    log("FOLLOW-UP DONE")
    return 0


if __name__ == "__main__":
    sys.exit(main())
