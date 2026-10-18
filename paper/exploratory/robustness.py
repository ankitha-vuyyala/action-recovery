"""Exploratory robustness checks on the recorded scripted episodes (not pre-registered).
(1) H1 population broken down by fault mode; (2) H1 without redelivery and partial-batch worlds;
(3) S vs best baseline with templates (8) as bootstrap clusters instead of template x instance (24);
(4) Settle's delay failures split by reversibility."""
import json, random, sys
from collections import defaultdict
from pathlib import Path

EP = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("runs/test_scripted/episodes.jsonl")
OUT = Path(__file__).resolve().parent / "robustness.json"
AMBIG = {"lost_ack", "not_exec_err", "held", "not_exec_to", "late", "late_tail", "redelivery", "partial",
         "crash_after", "crash_before"}
CONDS = ["C0", "C4", "C6", "Gw", "S-h", "S-c", "S-j", "S-t", "S", "O"]
inc = lambda r: bool(r["grade"]["residual_inconsistent"])


def world(r):
    return (r["template"], r["instance"], r["focal_step"], r["mode"], r["variant"], r.get("repeat", 0))


def main():
    R = [json.loads(l) for l in open(EP)]
    h1 = [r for r in R if r["mode"] in AMBIG and r["focal_cls"] == "A" and r["focal_reversible"] == "targeted"]
    res = {"by_mode": {}, "n_by_mode": {}}
    modes = sorted({r["mode"] for r in h1})
    for m in modes:
        res["by_mode"][m] = {}
        for c in CONDS:
            x = [r for r in h1 if r["mode"] == m and r["condition"] == c]
            res["by_mode"][m][c] = sum(map(inc, x)) / len(x) if x else None
            res["n_by_mode"][m] = len(x) if c == "S" else res["n_by_mode"].get(m)
    core = [r for r in h1 if r["mode"] not in ("redelivery", "partial")]
    res["core"] = {c: sum(map(inc, [r for r in core if r["condition"] == c])) /
                   len([r for r in core if r["condition"] == c]) for c in CONDS}
    res["core_n"] = len([r for r in core if r["condition"] == "S"])
    # template-clustered bootstrap of the paired difference S - Gw (H1 population and core population)
    for name, pop in (("h1", h1), ("core", core)):
        pair = defaultdict(dict)
        for r in pop:
            if r["condition"] in ("S", "Gw"):
                pair[world(r)][r["condition"]] = inc(r)
        by_t = defaultdict(list)
        for w, d in pair.items():
            if "S" in d and "Gw" in d:
                by_t[w[0]].append(d["S"] - d["Gw"])
        ts = sorted(by_t)
        rng = random.Random(20261001)
        est = sum(sum(v) for v in by_t.values()) / sum(len(v) for v in by_t.values())
        boots = []
        for _ in range(10000):
            pick = [rng.choice(ts) for _ in ts]
            num = sum(sum(by_t[t]) for t in pick)
            den = sum(len(by_t[t]) for t in pick)
            boots.append(num / den)
        boots.sort()
        res[f"tclust_{name}"] = {"diff": est, "lo": boots[249], "hi": boots[9749], "templates": len(ts),
                                 "pairs": sum(len(v) for v in by_t.values()),
                                 "templates_where_S_not_better": sum(1 for t in ts if sum(by_t[t]) >= 0)}
    # Settle delay failures by reversibility
    S = [r for r in R if r["condition"] == "S" and r["mode"] == "late_tail" and inc(r)]
    res["lt_fail_irreversible"] = sum(r["focal_reversible"] == "none" or r["focal_cls"] == "C" for r in S)
    res["lt_fail_reversible"] = len(S) - res["lt_fail_irreversible"]
    # crash_before for every condition
    res["crash_before"] = {c: sum(map(inc, x)) / len(x) for c in sorted({r["condition"] for r in R})
                           if (x := [r for r in R if r["condition"] == c and r["mode"] == "crash_before"])}
    OUT.write_text(json.dumps(res, indent=1))
    print(json.dumps(res, indent=1))


if __name__ == "__main__":
    main()
