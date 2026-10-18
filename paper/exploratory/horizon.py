"""Exploratory (not pre-registered): horizon trade-off replayed from recorded Settle episodes.

Settle's outcome in a late-commit world depends on the commit delay delta only through one comparison:
an irreversible write is re-issued once delta_assumed has passed since the first attempt, and a reversible
write is reconciled for the last time at the end of the episode. Each recorded episode therefore has a
decision time d (Delta for irreversible writes, the measured end-of-episode time for reversible ones), and
Settle leaves a surplus iff the recorded delay exceeds d. We (1) check that rule against the measured
outcomes at the frozen Delta = 20 s, then (2) shift each episode's decision time and latency by
(Delta' - 20 s) to trace the trade-off for other assumed bounds. Keyed (class K) writes never fail.
"""
import json, sys, statistics as st
from pathlib import Path

EP = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("runs/test_scripted/episodes.jsonl")
OUT = Path(__file__).resolve().parent / "horizon.json"
D0 = 20.0
GRID = [5, 7.5, 10, 12.5, 15, 20, 30, 45, 60, 90, 120]


def decision(r):
    if r["focal_cls"] == "K":
        return None                                   # the service deduplicates
    if r["focal_reversible"] == "none" or r["focal_cls"] == "C":
        return D0                                     # re-issue after the in-flight bound
    return r["agent_elapsed_s"]                       # final reconciliation at episode end


def lat(r, sh):
    """Only episodes that waited out the bound (elapsed >= Delta) move with it; episodes resolved by the
    first read (e.g. a lost reply whose effect is already visible) do not wait."""
    e = r["agent_elapsed_s"]
    return e + sh if e >= D0 else e


def main():
    R = [json.loads(l) for l in open(EP)]
    S = [r for r in R if r["condition"] == "S" and r["driver"] == "scripted"]
    timing = [r for r in S if r["mode"] in ("late", "late_tail") and r["variant"] == "exact"]
    agree = sum(((decision(r) is not None and r["delay_s"] > decision(r)) == r["grade"]["residual_inconsistent"])
                for r in timing)
    amb = [r for r in S if r["mode"] in ("lost_ack", "not_exec_to", "late", "late_tail")]
    base_lat = st.median(r["agent_elapsed_s"] for r in R if r["condition"] == "C0"
                         and r["mode"] in ("lost_ack", "not_exec_to", "late", "late_tail"))
    curve = []
    for d in GRID:
        sh = d - D0
        def fails(r):
            dd = decision(r)
            return dd is not None and r["delay_s"] > dd + sh
        tail = [r for r in timing if r["mode"] == "late_tail"]
        fixed = [r for r in timing if r["mode"] == "late"]
        curve.append({"delta": d,
                      "late_tail_inconsistent": sum(map(fails, tail)) / len(tail),
                      "late12_inconsistent": sum(map(fails, fixed)) / len(fixed),
                      "median_latency_s": st.median(lat(r, sh) for r in amb)})
    waited = sum(r["agent_elapsed_s"] >= D0 for r in amb)
    res = {"n_waited": waited, "n_timing": len(timing), "agree": agree, "n_tail": sum(r["mode"] == "late_tail" for r in timing),
           "n_late12": sum(r["mode"] == "late" for r in timing), "n_amb": len(amb),
           "c0_median_latency_s": base_lat, "curve": curve}
    OUT.write_text(json.dumps(res, indent=1))
    print(json.dumps(res, indent=1))


if __name__ == "__main__":
    main()
