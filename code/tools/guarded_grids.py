"""Run paid LLM grids one after another under an external stop guard.

Stops immediately (kills the grid's whole process tree) and does not start the next grid if
  * any record of the running grid has a `stop` field starting with "budget:" or "model error", or
  * the sum of `usd` in runs/cost_ledger.jsonl exceeds --max-usd.
The grids' own caps (MAX_SPEND_USD / MAX_SPEND_PER_RUN_USD in .env) still apply underneath.
Never reads or prints .env.

Usage (from ROOT):  .venv\\Scripts\\python code\\tools\\guarded_grids.py --max-usd 4 -- \\
    "llm_pilot|llm_pilot|llm:gpt-5.6-luna" "llm_models_mini|llm_models|llm:gpt-5.4-mini" ...
Each spec is name|preset|driver[|repeats[|limit]]; workers default to 2. A later spec may name the same grid with more
repeats: finished episodes (same ids) are skipped, so only the new repeats run.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RUNS = ROOT / "runs"
LEDGER = RUNS / "cost_ledger.jsonl"
BAD_STOPS = ("budget:", "model error")


def ledger_usd(run: str | None = None) -> float:
    if not LEDGER.exists():
        return 0.0
    tot = 0.0
    for line in LEDGER.read_text(encoding="utf-8").splitlines():
        try:
            r = json.loads(line)
        except json.JSONDecodeError:
            continue
        if run is None or r.get("run") == run:
            tot += float(r.get("usd", 0) or 0)
    return tot


def bad_records(name: str) -> list[str]:
    f = RUNS / name / "episodes.jsonl"
    if not f.exists():
        return []
    out = []
    for line in f.read_text(encoding="utf-8").splitlines():
        try:
            r = json.loads(line)
        except json.JSONDecodeError:
            continue
        s = str(r.get("stop") or "")
        if s.startswith(BAD_STOPS):
            out.append(f"{r.get('episode_id')} {r.get('condition')} {r.get('mode')}: {s[:200]}")
    return out


def kill_tree(pid: int) -> None:
    subprocess.run(["taskkill", "/PID", str(pid), "/T", "/F"], capture_output=True)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--max-usd", type=float, required=True)
    ap.add_argument("--workers", type=int, default=2)
    ap.add_argument("specs", nargs="+")
    a = ap.parse_args()
    for spec in a.specs:
        parts = spec.split("|")
        name, preset, driver = parts[:3]
        repeats = parts[3] if len(parts) > 3 else "1"
        limit = parts[4] if len(parts) > 4 else ""
        trip = None
        if ledger_usd() > a.max_usd:
            trip = f"ledger total ${ledger_usd():.4f} > ${a.max_usd} before start"
        if not trip:
            log = (RUNS / "tmp" / f"{name}.log").open("w", encoding="utf-8")
            p = subprocess.Popen([sys.executable, "-u", str(ROOT / "code" / "run.py"), "grid", "--name", name,
                                  "--preset", preset, "--driver", driver, "--workers", str(a.workers),
                                  "--repeats", repeats] + (["--limit", limit] if limit else []),
                                 cwd=ROOT, stdout=log, stderr=subprocess.STDOUT)
            print(f"[guard] started {name} ({driver}) pid={p.pid}", flush=True)
            while True:
                done = p.poll() is not None
                tot = ledger_usd()
                bad = bad_records(name)
                if tot > a.max_usd:
                    trip = f"ledger total ${tot:.4f} > ${a.max_usd}"
                elif bad:
                    trip = f"{len(bad)} record(s) with stop budget/model error, first: {bad[0]}"
                if trip and not done:
                    kill_tree(p.pid)
                if trip or done:
                    break
                time.sleep(2)
            p.wait()
            log.close()
            print(f"[guard] {name} rc={p.returncode} grid=${ledger_usd(name):.4f} total=${ledger_usd():.4f}",
                  flush=True)
        if trip:
            print(f"[guard] STOP during {name}: {trip}", flush=True)
            return 2
    print(f"[guard] all grids done, total=${ledger_usd():.4f}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
