"""Follow-up study analysis, CORRECTED copy (the frozen script is analysis/followup.py; see docs/PROTOCOL_corrections.md,
"Follow-up correction 1"). Only the handling of missing rates differs: a missing rate fails every criterion, and a
measured rate of 0 is no longer read as missing. Kept outside the frozen tree so that the freeze check still passes.
Follow-up study analysis (docs/07_followup_plan.md, freeze v3). Reads the frozen main-study records for the
pairings it needs and the follow-up grids; writes results/followup.json and results/followup.md.

    python analysis/followup.py --runs runs --out results
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "analysis"))
from confirmatory import (AMBIG, amb, easy, hard, inconsistent, load, overclaim, paired, rate,  # noqa: E402
                          mean_diff, holm)

F_EQ = 0.05
F6_NI = 0.10


def h1pop(rows):
    return [r for r in amb(rows) if r["focal_cls"] == "A" and r["focal_reversible"] == "targeted"]


def by(rows, c):
    return [r for r in rows if r["condition"] == c]


def try_load(p: Path):
    return load(p) if (p / "episodes.jsonl").exists() else ([], 0)


def f1(S, A):
    rows = h1pop(S + A)
    core = [r for r in rows if r["mode"] not in ("redelivery", "late_tail")]
    eq = paired(core, "Sp", "S", conf=0.90)
    lo, hi = eq["ci90_cluster"]
    red = [r for r in rows if r["mode"] == "redelivery"]
    lt = [r for r in rows if r["mode"] == "late_tail"]
    ltp = paired(lt, "Sp", "S")
    rs_, rp_ = rate(by(red, "S"))["rate"], rate(by(red, "Sp"))["rate"]
    b = rp_ is not None and rs_ is not None and rp_ >= 0.90 and rs_ <= 0.05
    by_mode = {m: {c: rate(by([r for r in rows if r["mode"] == m], c))["rate"] for c in ("S", "Sp", "S2")}
               for m in sorted({r["mode"] for r in rows})}
    lat = mean_diff([r for r in rows if r.get("agent_elapsed_s") is not None], "Sp", "S", "agent_elapsed_s")
    return {"a_equivalence_core": eq, "a_verdict": "confirmed" if (lo >= -F_EQ and hi <= F_EQ) else "not confirmed",
            "b_redelivery": {"Sp": rate(by(red, "Sp")), "S": rate(by(red, "S"))},
            "b_verdict": "confirmed" if b else "not confirmed",
            "c_late_tail": ltp, "c_verdict": "confirmed" if (ltp["diff"] is not None and ltp["diff"] >= 0) else "not confirmed",
            "d_latency": lat, "by_mode": by_mode,
            "core_rates": {c: rate(by(core, c)) for c in ("S", "Sp", "S2")}}


def f2(S, A):
    cc = [r for r in amb(S + A) if r["focal_cls"] == "C"]
    out = {c: {"inconsistent": rate(by(cc, c)), "overclaim": rate(by(cc, c), overclaim)} for c in ("S", "S2", "Sp")}
    out["verdict"] = "confirmed" if out["S2"]["overclaim"]["k"] == 0 and out["S2"]["overclaim"]["n"] > 0 else "not confirmed"
    return out


def f3(S, A):
    rows = h1pop(S + A)
    eq = paired(rows, "S2", "S", conf=0.90)
    lo, hi = eq["ci90_cluster"]
    free = [r for r in S + A if r["mode"] == "none"]
    return {"equivalence_h1": eq, "verdict": "confirmed" if (lo >= -F_EQ and hi <= F_EQ) else "not confirmed",
            "fault_free_time": mean_diff(free, "S2", "S", "agent_elapsed_s"),
            "h1_rates": {c: rate(by(rows, c)) for c in ("S", "S2")}}


def f4(B_):
    rev = [r for r in B_ if (r["focal_cls"] == "A" and r["focal_reversible"] == "targeted")
           or (r["focal_cls"] == "U")]
    irr = [r for r in B_ if r["focal_reversible"] == "none"]
    key = [r for r in B_ if r["focal_cls"] == "K"]
    conds = ("C0", "Gw", "S", "Sp", "S2", "O")
    ra = {c: rate(by(rev, c)) for c in conds}
    ri = {c: rate(by(irr, c)) for c in conds}
    oi = {c: rate(by(irr, c), overclaim) for c in conds}
    rk = {c: rate(by(key, c)) for c in conds}
    # correction (2026-10-05, after the runs): the frozen version used `rate or 1`, which turns a rate of exactly 0
    # into 1 and so failed the "<= 5%" criteria whenever the rate was 0; a missing rate (None) still fails.
    def le(v, x):
        return v is not None and v <= x

    def ge(v, x):
        return v is not None and v >= x
    a = le(ra["S2"]["rate"], 0.05) and all(ge(ra[c]["rate"], 0.5) for c in ("S", "Sp", "Gw", "C0"))
    b = all(ge(ri[c]["rate"], 0.9) for c in conds) and le(oi["S2"]["rate"], 0.05) and ge(oi["S"]["rate"], 0.5)
    c = all(le(rk[c_]["rate"], 0.05) for c_ in conds)
    return {"reversible": ra, "irreversible": ri, "irreversible_overclaim": oi, "keyed": rk,
            "a_verdict": "confirmed" if a else "not confirmed", "b_verdict": "confirmed" if b else "not confirmed",
            "c_verdict": "confirmed" if c else "not confirmed"}


def f5(C_):
    conds = ("C5", "C5a", "Gw", "Gwa", "S", "Sp", "S2")
    r = {c: rate(by(C_, c)) for c in conds}
    a = all(r[c]["rate"] is not None and r[c]["rate"] >= 0.25 for c in ("C5", "Gw"))
    ni = paired(C_, "Gwa", "S", conf=0.90)               # one-sided 95% upper bound = upper end of the 90% interval
    b = ni["ci90_cluster"][1] <= F_EQ
    modes = {m: {c: rate(by([x for x in C_ if x["mode"] == m], c))["rate"] for c in conds}
             for m in sorted({x["mode"] for x in C_})}
    coll = {c: sum(1 for x in by(C_, c) if x["grade"].get("collateral", 0) > 0) for c in conds}
    return {"rates": r, "a_verdict": "confirmed" if a else "not confirmed", "b_noninferiority": ni,
            "b_verdict": "confirmed" if b else "not confirmed", "by_mode": modes, "collateral_episodes": coll}


def f6(llm_main, llm_np):
    out = {}
    for m, rows in llm_np.items():
        base = [r for r in llm_main.get(m, []) if r["condition"] == "S"]
        both = base + rows
        res = {}
        for part, sel in (("hard", hard), ("easy", easy)):
            pr = [r for r in both if sel(r)]
            p = paired(pr, "S-np", "S", conf=0.90)
            res[part] = {"S": rate(by(pr, "S")), "S-np": rate(by(pr, "S-np")), "paired": p}
        up = res["hard"]["paired"]["ci90_cluster"][1]
        res["verdict"] = "confirmed" if (up is not None and up <= F6_NI) else "not confirmed"
        fails = [r for r in rows if r["mode"] in AMBIG and r["grade"]["residual_inconsistent"]]
        res["failures"] = [{k: r.get(k) for k in ("template", "focal_step", "mode", "variant", "repeat")} | {
            "steps_bad": [s for s, g in (r["grade"].get("steps") or {}).items() if not g.get("ok")]} for r in fails]
        out[m] = res
    return out


def f7(front):
    out = {}
    for m, rows in front.items():
        pr = [r for r in rows if hard(r)]
        p = paired(pr, "S-np", "C0")
        ok = p["n_pairs"] > 0 and p["ci95_cluster"][1] < 0 and p["p_mcnemar"] < 0.05
        out[m] = {"hard": {"C0": rate(by(pr, "C0")), "S-np": rate(by(pr, "S-np")), "paired": p},
                  "easy": {c: rate(by([r for r in rows if easy(r)], c)) for c in ("C0", "S-np")},
                  "usd_per_episode": {c: (sum(r.get("usd") or 0 for r in by(rows, c)) / max(1, len(by(rows, c))))
                                      for c in ("C0", "S-np")},
                  "verdict": "confirmed" if ok else "not confirmed"}
    return out


def pct(x):
    return "n/a" if x is None else f"{100 * x:.1f}%"


def md(res):
    L = ["# Follow-up study results", ""]
    f = res["F1"]
    L += [f"F1a Sp vs S without redelivery/late_tail: diff {pct(f['a_equivalence_core']['diff'])}, 90% CI "
          f"[{pct(f['a_equivalence_core']['ci90_cluster'][0])}, {pct(f['a_equivalence_core']['ci90_cluster'][1])}] "
          f"-> {f['a_verdict']}",
          f"F1b redelivery: Sp {pct(f['b_redelivery']['Sp']['rate'])}, S {pct(f['b_redelivery']['S']['rate'])} -> {f['b_verdict']}",
          f"F1c late_tail Sp - S: {pct(f['c_late_tail']['diff'])} -> {f['c_verdict']}",
          f"F1d time Sp - S (ambiguous): {f['d_latency']['diff']}",
          f"F2 content-only overclaim S2: {res['F2']['S2']['overclaim']['k']} of "
          f"{res['F2']['S2']['overclaim']['n']} -> {res['F2']['verdict']}",
          f"F3 S2 vs S (H1 pop): diff {pct(res['F3']['equivalence_h1']['diff'])} -> {res['F3']['verdict']}; "
          f"fault-free extra time {res['F3']['fault_free_time']['diff']}",
          ]
    if res["F4"]:
        L += [f"F4a {res['F4']['a_verdict']}  F4b {res['F4']['b_verdict']}  F4c {res['F4']['c_verdict']}",
              "  reversible: " + ", ".join(f"{c} {pct(v['rate'])}" for c, v in res['F4']['reversible'].items()),
              "  irreversible: " + ", ".join(f"{c} {pct(v['rate'])}" for c, v in res['F4']['irreversible'].items()),
              "  irreversible overclaim: " + ", ".join(f"{c} {pct(v['rate'])}"
                                                       for c, v in res['F4']['irreversible_overclaim'].items())]
    if res["F5"]:
        L += [f"F5a {res['F5']['a_verdict']}  F5b {res['F5']['b_verdict']}",
              "  rates: " + ", ".join(f"{c} {pct(v['rate'])}" for c, v in res['F5']['rates'].items())]
    for m, v in res["F6"].items():
        L.append(f"F6 {m}: hard S {pct(v['hard']['S']['rate'])} S-np {pct(v['hard']['S-np']['rate'])} -> {v['verdict']}")
    for m, v in res["F7"].items():
        L.append(f"F7 {m}: hard C0 {pct(v['hard']['C0']['rate'])} S-np {pct(v['hard']['S-np']['rate'])} -> {v['verdict']}")
    if not res["F7"]:
        L.append("F7: not run")
    return "\n".join(L) + "\n"


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", default="runs")
    ap.add_argument("--out", default="results")
    a = ap.parse_args(argv)
    R = Path(a.runs)
    S, _ = load(R / "test_scripted")
    A, ba = try_load(R / "followup_a")
    B_, bb = try_load(R / "followup_b")
    C_, bc = try_load(R / "followup_c")
    llm_main = defaultdict(list)
    for d in sorted(R.glob("test_llm_*")):
        rows, _ = load(d)
        for r in rows:
            llm_main[r["driver"]].append(r)
    llm_np, front = defaultdict(list), defaultdict(list)
    excl = {"followup_a": ba, "followup_b": bb, "followup_c": bc}
    for d in sorted(R.glob("followup_llm_np_*")):
        rows, b = load(d)
        excl[d.name] = b
        for r in rows:
            llm_np[r["driver"]].append(r)
    for d in sorted(R.glob("followup_llm_frontier*")):
        rows, b = load(d)
        excl[d.name] = b
        for r in rows:
            front[r["driver"]].append(r)
    res = {"n": {"followup_a": len(A), "followup_b": len(B_), "followup_c": len(C_),
                 "llm_np": {m: len(v) for m, v in llm_np.items()}, "frontier": {m: len(v) for m, v in front.items()}},
           "excluded": excl,
           "F1": f1(S, A), "F2": f2(S, A), "F3": f3(S, A), "F4": f4(B_) if B_ else {}, "F5": f5(C_) if C_ else {},
           "F6": f6(llm_main, llm_np), "F7": f7(front)}
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "followup.json").write_text(json.dumps(res, indent=1, default=str), encoding="utf-8")
    (out / "followup.md").write_text(md(res), encoding="utf-8")
    print(md(res))


if __name__ == "__main__":
    main(sys.argv[1:])
