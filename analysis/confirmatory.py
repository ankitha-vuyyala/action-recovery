"""Confirmatory analysis, exactly as pre-registered in docs/06_analysis_plan.md (frozen before the test split).

    python analysis/confirmatory.py --scripted runs/test_scripted [--llm runs/test_llm_luna ...] --out results/

Writes <out>/confirmatory.json (every number with a stable key, the evidence index for the paper) and
<out>/confirmatory.md (human-readable verdicts). Only finished episodes are used (runner errors, grading errors,
model errors and budget stops are excluded and counted). Nothing here is tuned on test data: populations,
comparisons, thresholds, bootstrap size and seed are fixed constants below.
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

# ---- frozen constants (docs/06_analysis_plan.md §3) ----------------------------------------------------------
AMBIG = {"lost_ack", "not_exec_err", "held", "not_exec_to", "late", "late_tail", "redelivery", "partial",
         "crash_after", "crash_before"}
BASELINES = ["C0", "C1", "C2", "C3", "C4", "C5", "C6", "C8", "Gw"]          # non-oracle, non-ablation
ABLATIONS = ["S-j", "S-t", "S-h", "S-c"]
CONTENT_METHODS = ["C5", "C6", "S-t"]
LLM_BASELINES = ["C0", "C5", "C6", "C7"]
B = 10000
SEED = 20261001
ALPHA = 0.05
H1_MAX_RATE, H1_MIN_GAP = 0.05, 0.15
H2_MIN_RATE, H2_REL = 0.10, 0.50
H3_MARGIN = 0.05
H4_MIN_RATE, H4_MAX_OVERCLAIM = 0.25, 0.05
H5_FREE_MAX_S, H5_AMB_SLACK_S, H5_COST_RATIO = 2.0, 10.0, 1.25


# ---- data -----------------------------------------------------------------------------------------------------
def unfinished(r: dict) -> bool:
    crashed = r.get("claimed") == "no_report" and bool(r.get("child_rcs")) and r["child_rcs"][-1] not in (0,)
    return ("error" in r or "grade_error" in (r.get("grade") or {}) or crashed     # crashed: amendment 2
            or str(r.get("stop") or "").startswith(("model error", "budget")))


def load(run: Path) -> tuple[list[dict], int]:
    rows, bad = [], 0
    for line in (Path(run) / "episodes.jsonl").read_text(encoding="utf-8").splitlines():
        try:
            r = json.loads(line)
        except json.JSONDecodeError:
            continue
        if unfinished(r):
            bad += 1
        else:
            rows.append(r)
    return rows, bad


def world(r: dict) -> tuple:
    return (r["template"], r["instance"], r["focal_step"], r["mode"], r["variant"], r.get("repeat", 0))


def cluster(r: dict) -> tuple:
    return (r["template"], r["instance"])


def inconsistent(r: dict) -> int:
    return int(bool(r["grade"]["residual_inconsistent"]))


def overclaim(r: dict) -> int:
    g = r["grade"]
    reported = (r.get("claimed") != "completed" or bool(r.get("uncertain")) or bool(r.get("duplicates_reported"))
                or bool(r.get("layer_uncertain")))
    return int(bool(g.get("residual_inconsistent")) and not reported)


# ---- statistics -----------------------------------------------------------------------------------------------
def wilson(k: int, n: int, z: float = 1.959964) -> tuple[float, float]:
    if n == 0:
        return (float("nan"), float("nan"))
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (max(0.0, c - h), min(1.0, c + h))


def _boot(clusters: dict, stat, conf: float) -> tuple[float, float]:
    """Cluster bootstrap (resample template x instance clusters with replacement), percentile interval.
    clusters: {cluster: (sum_numerator, count)}; stat over the pooled resample is sum/count."""
    keys = list(clusters)
    if not keys:
        return (float("nan"), float("nan"))
    num = np.array([clusters[k][0] for k in keys], dtype=float)
    den = np.array([clusters[k][1] for k in keys], dtype=float)
    rng = np.random.default_rng(SEED)
    idx = rng.integers(0, len(keys), size=(B, len(keys)))
    n_s, d_s = num[idx].sum(1), den[idx].sum(1)
    vals = np.where(d_s > 0, n_s / np.maximum(d_s, 1e-12), np.nan)
    lo, hi = np.nanpercentile(vals, [100 * (1 - conf) / 2, 100 * (1 + conf) / 2])
    return (float(lo), float(hi))


def rate(rows: list[dict], f=inconsistent) -> dict:
    n = len(rows)
    k = sum(f(r) for r in rows)
    cl = defaultdict(lambda: [0, 0])
    for r in rows:
        c = cl[cluster(r)]
        c[0] += f(r)
        c[1] += 1
    lo, hi = _boot({k_: tuple(v) for k_, v in cl.items()}, None, 0.95)
    wl, wh = wilson(k, n)
    return {"n": n, "k": k, "rate": (k / n) if n else None, "ci95_cluster": [lo, hi], "ci95_wilson": [wl, wh],
            "clusters": len(cl)}


def mcnemar_exact(b: int, c: int) -> float:
    n = b + c
    if n == 0:
        return 1.0
    m = min(b, c)
    p = sum(math.comb(n, i) for i in range(m + 1)) / 2 ** n
    return min(1.0, 2 * p)


def paired(rows: list[dict], a: str, b: str, f=inconsistent, conf: float = 0.95) -> dict:
    """Paired comparison of condition a vs b over worlds present for both: diff = rate(a) - rate(b)."""
    by = defaultdict(dict)
    for r in rows:
        if r["condition"] in (a, b):
            by[world(r)][r["condition"]] = r
    pairs = [(v[a], v[b]) for v in by.values() if a in v and b in v]
    cl = defaultdict(lambda: [0.0, 0])
    disc_ab = disc_ba = 0
    for ra, rb in pairs:
        x, y = f(ra), f(rb)
        c = cl[cluster(ra)]
        c[0] += x - y
        c[1] += 1
        disc_ab += int(x == 1 and y == 0)
        disc_ba += int(x == 0 and y == 1)
    n = len(pairs)
    d = sum(f(x) - f(y) for x, y in pairs) / n if n else None
    lo, hi = _boot({k: tuple(v) for k, v in cl.items()}, None, conf)
    return {"a": a, "b": b, "n_pairs": n, "diff": d, f"ci{int(conf * 100)}_cluster": [lo, hi],
            "a_only": disc_ab, "b_only": disc_ba, "p_mcnemar": mcnemar_exact(disc_ab, disc_ba)}


def holm(ps: dict) -> dict:
    items = sorted(ps.items(), key=lambda kv: kv[1])
    m, out, run = len(items), {}, 0.0
    for i, (k, p) in enumerate(items):
        run = max(run, min(1.0, (m - i) * p))
        out[k] = run
    return out


def mean_diff(rows, a, b, field, conf=0.95) -> dict:
    by = defaultdict(dict)
    for r in rows:
        if r["condition"] in (a, b) and r.get(field) is not None:
            by[world(r)][r["condition"]] = r
    pairs = [(v[a], v[b]) for v in by.values() if a in v and b in v]
    cl = defaultdict(lambda: [0.0, 0])
    for ra, rb in pairs:
        c = cl[cluster(ra)]
        c[0] += float(ra[field]) - float(rb[field])
        c[1] += 1
    n = len(pairs)
    lo, hi = _boot({k: tuple(v) for k, v in cl.items()}, None, conf)
    return {"a": a, "b": b, "field": field, "n_pairs": n,
            "diff": (sum(float(x[field]) - float(y[field]) for x, y in pairs) / n) if n else None,
            "ci95_cluster": [lo, hi]}


def ratio_of_means(rows, a, b, field) -> dict:
    """Paired ratio mean(a)/mean(b) with a cluster bootstrap interval."""
    by = defaultdict(dict)
    for r in rows:
        if r["condition"] in (a, b) and r.get(field) is not None:
            by[world(r)][r["condition"]] = r
    pairs = [(v[a], v[b]) for v in by.values() if a in v and b in v]
    if not pairs:
        return {"a": a, "b": b, "n_pairs": 0, "ratio": None, "ci95_cluster": [None, None]}
    cl = defaultdict(lambda: [0.0, 0.0])
    for ra, rb in pairs:
        c = cl[cluster(ra)]
        c[0] += float(ra[field])
        c[1] += float(rb[field])
    lo, hi = _boot({k: tuple(v) for k, v in cl.items()}, None, 0.95)
    sa, sb = sum(float(x[field]) for x, _ in pairs), sum(float(y[field]) for _, y in pairs)
    return {"a": a, "b": b, "field": field, "n_pairs": len(pairs), "ratio": (sa / sb) if sb else None,
            "ci95_cluster": [lo, hi]}


# ---- populations ----------------------------------------------------------------------------------------------
def amb(rows):
    return [r for r in rows if r["mode"] in AMBIG]


def cond(rows, c):
    return [r for r in rows if r["condition"] == c]


# ---- hypotheses -----------------------------------------------------------------------------------------------
def h1(S: list[dict]) -> dict:
    pop = [r for r in amb(S) if r["focal_cls"] == "A" and r["focal_reversible"] == "targeted"]
    rates = {c: rate(cond(pop, c)) for c in BASELINES + ["S", "O"] + ABLATIONS}
    present = [c for c in BASELINES if rates[c]["n"]]
    best = min(present, key=lambda c: (rates[c]["rate"], c))
    comps = {c: paired(pop, "S", c) for c in present}
    adj = holm({c: comps[c]["p_mcnemar"] for c in present})
    for c in present:
        comps[c]["p_holm"] = adj[c]
    cb = comps[best]
    ok = (rates["S"]["rate"] <= H1_MAX_RATE and cb["diff"] <= -H1_MIN_GAP and cb["ci95_cluster"][1] < 0
          and cb["p_holm"] < ALPHA)
    return {"population": "scripted; ambiguous modes; focal class A, targeted-reversible; all read variants",
            "rates": rates, "best_baseline": best, "comparisons": comps,
            "criteria": f"S rate <= {H1_MAX_RATE}; S - best <= -{H1_MIN_GAP}; cluster 95% CI upper < 0; Holm p < {ALPHA}",
            "verdict": "confirmed" if ok else "not confirmed"}


def h2(S: list[dict]) -> dict:
    pop = [r for r in amb(S) if r["variant"] == "lookalike"]
    rates = {c: rate(cond(pop, c)) for c in CONTENT_METHODS + ["S", "C8"]}
    coll = {c: rate(cond(pop, c), f=lambda r: int(r["grade"]["collateral"] > 0)) for c in CONTENT_METHODS + ["S", "C8"]}
    comps = {c: paired(pop, "S", c) for c in CONTENT_METHODS if rates[c]["n"]}
    adj = holm({c: v["p_mcnemar"] for c, v in comps.items()})
    for c in comps:
        comps[c]["p_holm"] = adj[c]
    a_ok = all(rates[c]["rate"] is not None and rates[c]["rate"] >= H2_MIN_RATE for c in comps)
    b_ok = all(rates["S"]["rate"] <= H2_REL * rates[c]["rate"] and comps[c]["ci95_cluster"][1] < 0
               and comps[c]["p_holm"] < ALPHA for c in comps)
    return {"population": "scripted; ambiguous modes; look-alike read variant", "rates": rates,
            "collateral": coll, "comparisons": comps,
            "criteria": f"(a) every content method >= {H2_MIN_RATE}; (b) S <= {H2_REL} x each, CI upper < 0, Holm p < {ALPHA}",
            "verdict_a": "confirmed" if a_ok else "not confirmed", "verdict_b": "confirmed" if b_ok else "not confirmed",
            "verdict": "confirmed" if a_ok and b_ok else "not confirmed"}


def h3(S: list[dict]) -> dict:
    pop = [r for r in amb(S) if r["focal_cls"] == "K"]
    eq = paired(pop, "S", "C4", conf=0.90)
    lo, hi = eq["ci90_cluster"]
    degenerate = eq["a_only"] == 0 and eq["b_only"] == 0
    ok = degenerate or (lo >= -H3_MARGIN and hi <= H3_MARGIN)
    crash = [r for r in pop if r["mode"] in ("crash_after", "crash_before")]
    rest = [r for r in pop if r["mode"] not in ("crash_after", "crash_before")]
    n_s = rate(cond(pop, "S"))
    return {"population": "scripted; ambiguous modes; focal class K (native key)",
            "S_vs_C4_equivalence": eq, "rates": {c: rate(cond(pop, c)) for c in ["S", "C3", "C4"]},
            "S_rule_of_three_upper": (3 / n_s["n"]) if n_s["n"] and n_s["k"] == 0 else None,
            "C3_crash_vs_rest": {"crash": rate(cond(crash, "C3")), "rest": rate(cond(rest, "C3"))},
            "criteria": f"90% cluster CI of S - C4 within +-{H3_MARGIN} (or no discordant pairs)",
            "verdict": "confirmed" if ok else "not confirmed"}


def h4(S: list[dict]) -> dict:
    agg = [r for r in amb(S) if r["variant"] == "agg_shared"]
    irr = [r for r in amb(S) if r["focal_reversible"] == "none"]
    conds = BASELINES + ["S"] + ABLATIONS
    agg_rates = {c: rate(cond(agg, c)) for c in conds}
    a_ok = all(v["rate"] is not None and v["rate"] >= H4_MIN_RATE for v in agg_rates.values() if v["n"])
    both = list({r["episode_id"]: r for r in agg + irr}.values())
    over = rate(cond(both, "S"), f=overclaim)
    b_ok = over["rate"] is not None and over["rate"] <= H4_MAX_OVERCLAIM
    irr_tab = {}
    for c in conds + ["O"]:
        rs = cond(irr, c)
        irr_tab[c] = {"irreversible_dup": rate(rs, f=lambda r: int(r["grade"]["irreversible_dup_execs"] > 0)),
                      "missing": rate(rs, f=lambda r: int(r["grade"]["missing_steps"] > 0)),
                      "overclaim": rate(rs, f=overclaim)}
    c_ok = all((v["irreversible_dup"]["k"] > 0 or v["missing"]["k"] > 0) for v in irr_tab.values()
               if v["irreversible_dup"]["n"])
    return {"population": "scripted; ambiguous modes; (a) shared-aggregate variant, (c) irreversible focal write",
            "agg_shared_rates": agg_rates, "S_overclaim_agg_or_irreversible": over, "irreversible": irr_tab,
            "criteria": f"(a) every non-oracle condition >= {H4_MIN_RATE} inconsistent under shared aggregates; "
                        f"(b) S overclaim <= {H4_MAX_OVERCLAIM}; (c) every condition incl. oracle has irreversible "
                        "duplicates or missing effects in irreversible worlds",
            "verdict_a": "confirmed" if a_ok else "not confirmed", "verdict_b": "confirmed" if b_ok else "not confirmed",
            "verdict_c": "confirmed" if c_ok else "not confirmed",
            "verdict": "confirmed" if a_ok and b_ok and c_ok else "not confirmed"}


def h5(S: list[dict], llm: dict[str, list[dict]], delta_s: float) -> dict:
    free = [r for r in S if r["mode"] == "none"]
    d_free = mean_diff(free, "S", "C6", "agent_elapsed_s")
    d_amb = mean_diff(amb(S), "S", "C6", "agent_elapsed_s")
    lat_ok = (d_free["ci95_cluster"][1] <= H5_FREE_MAX_S and d_amb["diff"] is not None
              and d_amb["diff"] <= delta_s + H5_AMB_SLACK_S)
    cost = {m: ratio_of_means(rows, "S", "C6", "usd") for m, rows in llm.items()}
    cost_v = {}
    for m, v in cost.items():
        lo, hi = v["ci95_cluster"]
        if not v["n_pairs"]:
            cost_v[m] = "not tested (no S/C6 pairs)"
            continue
        cost_v[m] = ("confirmed" if hi is not None and hi <= H5_COST_RATIO else
                     "refuted" if lo is not None and lo > H5_COST_RATIO else "inconclusive")
    return {"latency_fault_free": d_free, "latency_ambiguous": d_amb, "delta_assumed_s": delta_s,
            "latency_verdict": "confirmed" if lat_ok else "not confirmed", "llm_cost_ratio_S_over_C6": cost,
            "cost_verdicts": cost_v,
            "criteria": f"fault-free S - C6 time CI upper <= {H5_FREE_MAX_S} s; ambiguous mean S - C6 <= Delta + "
                        f"{H5_AMB_SLACK_S} s; per model S/C6 US$ ratio CI upper <= {H5_COST_RATIO}"}


def hard(r: dict) -> bool:
    """Worlds where checking state is not enough for an agent that only observes (theory: P1 unknown in-flight
    bound, P4 look-alikes, lagged reads, P6 crash + framework replay). Shared aggregates are excluded (H4)."""
    return r["mode"] in AMBIG and r["variant"] != "agg_shared" and (
        r["mode"] in ("late_tail", "crash_after") or r["variant"] in ("lookalike", "lagged"))


def easy(r: dict) -> bool:
    """Ambiguous worlds with exact reads and a short, bounded delay: a careful checking agent can succeed."""
    return r["mode"] in ("lost_ack", "not_exec_err", "late") and r["variant"] == "exact"


def h6(llm: dict[str, list[dict]]) -> dict:
    """Pre-registered after the dev-split pilot showed that a reasoning model checks state before re-issuing:
    the confirmatory claim is restricted to the worlds where the theory says checking cannot suffice; the
    easy worlds are reported with intervals and no directional prediction."""
    out, all_ok = {}, bool(llm)
    for m, rows in llm.items():
        res = {}
        for name, sel in (("hard", hard), ("easy", easy)):
            pop = [r for r in rows if sel(r)]
            present = [c for c in LLM_BASELINES if cond(pop, c)]
            comps = {c: paired(pop, "S", c) for c in present}
            adj = holm({c: v["p_mcnemar"] for c, v in comps.items()})
            for c in comps:
                comps[c]["p_holm"] = adj[c]
            res[name] = {"rates": {c: rate(cond(pop, c)) for c in present + ["S"]}, "comparisons": comps}
        ch = res["hard"]["comparisons"]
        ok = bool(ch) and all(v["diff"] is not None and v["diff"] < 0 and v["ci95_cluster"][1] < 0
                              and v["p_holm"] < ALPHA for v in ch.values())
        out[m] = {**res, "verdict": "confirmed" if ok else "not confirmed"}
        all_ok &= ok
    return {"per_model": out,
            "criteria": f"per model, in hard worlds (late_tail, crash_after, look-alike or lagged reads), S below every "
                        f"LLM baseline: diff < 0, cluster CI upper < 0, Holm p < {ALPHA}; easy worlds reported only",
            "verdict": "not tested (no LLM runs given)" if not llm else ("confirmed" if all_ok else "not confirmed")}


ABLATION_CELLS = {   # secondary predictions (Table P): each component is needed exactly where the theory says
    "S-j": ("journal (P6)", lambda r: r["mode"] == "crash_after"),
    "S-h": ("horizon (P2)", lambda r: r["mode"] in ("late", "late_tail")),
    "S-t": ("tags (P4)", lambda r: r["variant"] == "lookalike" or r["mode"] in ("not_exec_err", "not_exec_to")),
    "S-c": ("compensation (P2)", lambda r: r["mode"] in ("late", "late_tail", "redelivery")
            and r["focal_reversible"] == "targeted"),
}
ABL_MIN_GAP = 0.10


def ablations(S: list[dict]) -> dict:
    out = {}
    for c, (what, cell) in ABLATION_CELLS.items():
        pop = [r for r in amb(S) if cell(r)]
        comp = paired(pop, c, "S")
        rest = [r for r in amb(S) if not cell(r)]
        comp_rest = paired(rest, c, "S")
        ok = comp["diff"] is not None and comp["diff"] >= ABL_MIN_GAP and comp["ci95_cluster"][0] > 0
        out[c] = {"component": what, "in_cell": comp, "outside_cell": comp_rest,
                  "verdict": "confirmed" if ok else "not confirmed"}
    return {"criteria": f"ablation - S >= {ABL_MIN_GAP} in its cell with cluster 95% CI lower > 0; the difference "
                        "outside the cell is reported", "per_ablation": out}


# ---- report ---------------------------------------------------------------------------------------------------
def pct(x) -> str:
    return "-" if x is None or (isinstance(x, float) and math.isnan(x)) else f"{100 * x:.1f}"


def ci(v) -> str:
    return f"[{pct(v[0])}, {pct(v[1])}]"


def md(res: dict) -> str:
    L = ["# Confirmatory results", "", f"Scripted episodes used: {res['n_scripted']} (excluded unfinished: "
         f"{res['excluded_scripted']}). LLM runs: " + ", ".join(f"{m}: {v['n']} (excluded {v['excluded']})"
                                                                for m, v in res["llm_runs"].items()), ""]
    h = res["H1"]
    L += ["## H1 Settle vs best baseline (A, targeted-reversible, ambiguous)", "", f"Verdict: **{h['verdict']}**. "
          f"Criteria: {h['criteria']}.", "", "| condition | n | inconsistent % | cluster 95% CI |", "|---|---|---|---|"]
    L += [f"| {c} | {v['n']} | {pct(v['rate'])} | {ci(v['ci95_cluster'])} |" for c, v in h["rates"].items() if v["n"]]
    L += ["", f"Best baseline: {h['best_baseline']}.", "", "| S vs | pairs | diff pp | 95% CI | S-only | other-only | Holm p |",
          "|---|---|---|---|---|---|---|"]
    L += [f"| {c} | {v['n_pairs']} | {pct(v['diff'])} | {ci(v['ci95_cluster'])} | {v['a_only']} | {v['b_only']} | "
          f"{v['p_holm']:.2g} |" for c, v in h["comparisons"].items()]
    h = res["H2"]
    L += ["", "## H2 Look-alikes", "", f"Verdict: **{h['verdict']}** (a: {h['verdict_a']}, b: {h['verdict_b']}). "
          f"{h['criteria']}.", "", "| condition | n | inconsistent % | CI | collateral % |", "|---|---|---|---|---|"]
    L += [f"| {c} | {v['n']} | {pct(v['rate'])} | {ci(v['ci95_cluster'])} | {pct(h['collateral'][c]['rate'])} |"
          for c, v in h["rates"].items() if v["n"]]
    h = res["H3"]
    e = h["S_vs_C4_equivalence"]
    L += ["", "## H3 Native keys", "", f"Verdict: **{h['verdict']}**. {h['criteria']}. S - C4 = {pct(e['diff'])} pp, "
          f"90% CI {ci(e['ci90_cluster'])}, discordant {e['a_only']}/{e['b_only']} over {e['n_pairs']} pairs. "
          f"C3 inconsistent in crash worlds {pct(h['C3_crash_vs_rest']['crash']['rate'])} % vs other worlds "
          f"{pct(h['C3_crash_vs_rest']['rest']['rate'])} %."]
    h = res["H4"]
    L += ["", "## H4 Impossibility cells", "", f"Verdict: **{h['verdict']}** (a: {h['verdict_a']}, b: {h['verdict_b']}, "
          f"c: {h['verdict_c']}). {h['criteria']}. S overclaim: {pct(h['S_overclaim_agg_or_irreversible']['rate'])} %."]
    h = res["H5"]
    L += ["", "## H5 Cost and latency", "", f"Latency: **{h['latency_verdict']}**; fault-free S - C6 "
          f"{h['latency_fault_free']['diff']:.2f} s, 95% CI [{h['latency_fault_free']['ci95_cluster'][0]:.2f}, "
          f"{h['latency_fault_free']['ci95_cluster'][1]:.2f}]; ambiguous "
          f"{(h['latency_ambiguous']['diff'] or 0):.2f} s. Cost ratio per model: " +
          "; ".join(f"{m}: {(v['ratio'] or 0):.2f} [{(v['ci95_cluster'][0] or 0):.2f}, {(v['ci95_cluster'][1] or 0):.2f}]"
                    f" -> {h['cost_verdicts'][m]}"
                    for m, v in h["llm_cost_ratio_S_over_C6"].items())]
    L += ["", "## Secondary: ablations in their predicted cells", "", res["ablations"]["criteria"] + ".", "",
          "| ablation | component | pairs in cell | diff in cell pp | 95% CI | diff outside pp | verdict |",
          "|---|---|---|---|---|---|---|"]
    L += [f"| {c} | {v['component']} | {v['in_cell']['n_pairs']} | {pct(v['in_cell']['diff'])} | "
          f"{ci(v['in_cell']['ci95_cluster'])} | {pct(v['outside_cell']['diff'])} | {v['verdict']} |"
          for c, v in res["ablations"]["per_ablation"].items()]
    h = res["H6"]
    L += ["", "## H6 Driver invariance (LLM agents)", "", f"Verdict: **{h['verdict']}**. {h['criteria']}."]
    for m, v in h["per_model"].items():
        L += ["", f"### {m}: {v['verdict']}"]
        for part in ("hard", "easy"):
            L += ["", f"{part} worlds: " + ", ".join(f"{c} {pct(x['rate'])} % (n {x['n']})" for c, x in v[part]["rates"].items()),
                  "", "| S vs | pairs | diff pp | 95% CI | Holm p |", "|---|---|---|---|---|"]
            L += [f"| {c} | {x['n_pairs']} | {pct(x['diff'])} | {ci(x['ci95_cluster'])} | {x['p_holm']:.2g} |"
                  for c, x in v[part]["comparisons"].items()]
    return "\n".join(L) + "\n"


def main(argv=None) -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--scripted", required=True)
    ap.add_argument("--llm", nargs="*", default=[])
    ap.add_argument("--delta", type=float, default=20.0)
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    S, bad = load(Path(a.scripted))
    llm, llm_meta = {}, {}
    for p in a.llm:
        rows, b = load(Path(p))
        models = sorted({r["driver"] for r in rows})
        for m in models:
            llm[m] = llm.get(m, []) + [r for r in rows if r["driver"] == m]
        llm_meta[Path(p).name] = {"n": len(rows), "excluded": b, "models": models}
    res = {"n_scripted": len(S), "excluded_scripted": bad, "llm_runs": llm_meta,
           "constants": {"B": B, "seed": SEED, "alpha": ALPHA},
           "H1": h1(S), "H2": h2(S), "H3": h3(S), "H4": h4(S), "H5": h5(S, llm, a.delta), "H6": h6(llm),
           "ablations": ablations(S)}
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "confirmatory.json").write_text(json.dumps(res, indent=1, default=str), encoding="utf-8")
    (out / "confirmatory.md").write_text(md(res), encoding="utf-8")
    print(md(res))


if __name__ == "__main__":
    main(sys.argv[1:])
