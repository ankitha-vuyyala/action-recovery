"""Derive every number, table and figure the paper uses from the saved results (the paper's evidence index).

    python paper/derive.py --root .        (project root containing results/ and runs/)

Reads
  results/confirmatory.json         the pre-registered analysis (analysis/confirmatory.py)
  results/llm_behaviour.jsonl       RQ1 coding (analysis/llm_behaviour.py)
  runs/test_scripted/episodes.jsonl runs/test_llm_*/episodes.jsonl  raw records (descriptive tables)
  runs/cost_ledger.jsonl            spend;  FREEZE.json  freeze digest
Writes
  paper/build/numbers.json          {key: {"value": ..., "source": "<file>:<path or computation>"}}
  paper/figures/*.png               figures (300 dpi)
Nothing here re-tests a hypothesis: verdicts and intervals are copied from confirmatory.json; descriptive rates
are plain proportions over finished episodes, computed with the same exclusion rule.
"""
from __future__ import annotations

import argparse
import collections
import json
import math
from pathlib import Path

P = Path(__file__).resolve().parent
AMBIG = {"lost_ack", "not_exec_err", "held", "not_exec_to", "late", "late_tail", "redelivery", "partial",
         "crash_after", "crash_before"}
SCRIPTED_ORDER = ["C0", "C1", "C2", "C3", "C4", "C5", "C6", "Gw", "C8", "S", "S-j", "S-t", "S-h", "S-c", "O"]
LLM_ORDER = ["C0", "C5", "C6", "C7", "S"]
COND_NAME = {"C0": "C0 plain", "C1": "C1 never retry", "C2": "C2 SDK retry", "C3": "C3 keys", "C4": "C4 workflow engine",
             "C5": "C5 verify-before-retry", "C6": "C6 guard", "Gw": "Gw guard + wait", "C7": "C7 reflection",
             "C8": "C8 rollback", "S": "S Settle", "S-j": "S−j no journal", "S-t": "S−t no tags",
             "S-h": "S−h no horizon", "S-c": "S−c no compensation", "O": "O oracle"}
MODES = ["lost_ack", "not_exec_err", "held", "not_exec_to", "late", "late_tail", "partial", "redelivery",
         "crash_after", "crash_before"]
MODEL_NAME = {"llm:gpt-5.6-luna": "gpt-5.6-luna", "llm:gpt-4.1-mini": "gpt-4.1-mini", "llm:gpt-5.4-nano": "gpt-5.4-nano"}

# palette (reference instance of the data-viz method; light surface, print)
BLUE, ORANGE, AQUA, YELLOW = "#2a78d6", "#eb6834", "#1baf7a", "#eda100"
INK, INK2, MUTED, GRID, BASE = "#0b0b0b", "#52514e", "#898781", "#e1e0d9", "#c3c2b7"
SEQ = ["#fcfcfb", "#cde2fb", "#9ec5f4", "#6da7ec", "#3987e5", "#256abf", "#184f95", "#0d366b"]

N: dict = {}


def put(key, value, source):
    if isinstance(value, float) and math.isnan(value):
        value = None
    N[key] = {"value": value, "source": source}


# ------------------------------------------------------------------------------------------------ data
def unfinished(r):
    crashed = r.get("claimed") == "no_report" and bool(r.get("child_rcs")) and r["child_rcs"][-1] not in (0,)
    return ("error" in r or "grade_error" in (r.get("grade") or {}) or crashed
            or str(r.get("stop") or "").startswith(("model error", "budget")))


def load(path: Path) -> tuple[list, int]:
    rows, bad = [], 0
    if not path.exists():
        return rows, 0
    for line in path.read_text(encoding="utf-8").splitlines():
        try:
            r = json.loads(line)
        except json.JSONDecodeError:
            continue
        (rows.append(r) if not unfinished(r) else None)
        bad += unfinished(r)
    return rows, bad


def overclaim(r):
    g = r["grade"]
    rep = (r.get("claimed") != "completed" or bool(r.get("uncertain")) or bool(r.get("duplicates_reported"))
           or bool(r.get("layer_uncertain")))
    return bool(g.get("residual_inconsistent")) and not rep


def rate(rs, f):
    return (sum(1 for r in rs if f(r)) / len(rs)) if rs else None


def inc(r):
    return bool(r["grade"]["residual_inconsistent"])


def pct(x):
    return "–" if x is None else f"{100 * x:.1f}"


# ------------------------------------------------------------------------------------------------ tables
def md_table(header, rows) -> str:
    out = ["| " + " | ".join(header) + " |", "|" + "|".join("---" for _ in header) + "|"]
    out += ["| " + " | ".join(str(c) for c in row) + " |" for row in rows]
    return "\n".join(out)


def scripted_tables(S: list, src: str):
    amb = [r for r in S if r["mode"] in AMBIG]
    rows = []
    for c in SCRIPTED_ORDER:
        rs = [r for r in amb if r["condition"] == c]
        if not rs:
            continue
        t = [r.get("agent_elapsed_s") or 0 for r in rs]
        rows.append([COND_NAME[c], len(rs), pct(rate(rs, inc)), pct(rate(rs, lambda r: r["grade"]["dup_execs"] > 0)),
                     pct(rate(rs, lambda r: r["grade"]["missing_steps"] > 0)),
                     pct(rate(rs, lambda r: r["grade"]["collateral"] > 0)), pct(rate(rs, overclaim)),
                     f"{sum(t) / len(t):.1f}"])
        for k, f in (("inconsistent", inc), ("dup", lambda r: r["grade"]["dup_execs"] > 0),
                     ("missing", lambda r: r["grade"]["missing_steps"] > 0),
                     ("collateral", lambda r: r["grade"]["collateral"] > 0), ("overclaim", overclaim)):
            put(f"amb.{c}.{k}", rate(rs, f), f"{src}: ambiguous worlds, condition {c}, share with {k}")
        put(f"amb.{c}.time", sum(t) / len(t), f"{src}: mean agent_elapsed_s, ambiguous, {c}")
        put(f"amb.{c}.n", len(rs), f"{src}: count")
    put("table.main", md_table(["Condition", "n", "Inconsistent %", "Duplicate executed %", "Missing %", "Collateral %",
                                "Overclaim %", "Mean time (s)"], rows), f"{src}: ambiguous worlds by condition")
    free = [r for r in S if r["mode"] == "none"]
    put("free.max_inconsistent", max((rate([r for r in free if r["condition"] == c], inc) or 0)
                                     for c in SCRIPTED_ORDER), f"{src}: fault-free worlds, max over conditions")
    put("free.n", len(free), f"{src}: fault-free episodes")
    # the achievability map, filled in: inconsistency by contract cell and condition
    cells = [("K", "targeted", "exact", "K, keyed"), ("A", "targeted", "exact", "A, reversible, exact read"),
             ("A", "targeted", "lagged", "A, reversible, lagged read"),
             ("A", "targeted", "lookalike", "A, reversible, look-alikes"),
             ("A", "none", None, "A, irreversible (mail)"), ("C", "none", None, "content-only, irreversible"),
             ("U", "fungible", "exact", "U, exclusive aggregate"), ("U", "fungible", "agg_shared", "U, shared aggregate")]
    show = ["C0", "C3", "C4", "C5", "C6", "Gw", "C8", "S", "O"]
    rows = []
    for cls, rev, var, name in cells:
        rs = [r for r in amb if r["focal_cls"] == cls and r["focal_reversible"] == rev
              and (var is None or r["variant"] == var)]
        if not rs:
            continue
        row = [name, len([r for r in rs if r["condition"] == "S"])]
        for c in show:
            v = rate([r for r in rs if r["condition"] == c], inc)
            row.append(pct(v))
            put(f"cell.{cls}.{rev}.{var}.{c}", v, f"{src}: ambiguous, focal {cls}/{rev}/{var}, condition {c}")
        rows.append(row)
    put("table.map", md_table(["Contract cell (focal write)", "worlds"] + show, rows),
        f"{src}: inconsistency % by contract cell and condition")
    return amb


def heatmap(amb: list, path: Path, src: str):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.colors import LinearSegmentedColormap
    conds = [c for c in SCRIPTED_ORDER if any(r["condition"] == c for r in amb)]
    modes = [m for m in MODES if any(r["mode"] == m for r in amb)]
    M = [[rate([r for r in amb if r["condition"] == c and r["mode"] == m], inc) for m in modes] for c in conds]
    fig, ax = plt.subplots(figsize=(7.2, 4.6), dpi=300)
    cmap = LinearSegmentedColormap.from_list("seq", SEQ)
    import numpy as np
    A = np.array([[np.nan if v is None else v for v in row] for row in M])
    ax.imshow(A, cmap=cmap, vmin=0, vmax=1, aspect="auto")
    for i in range(len(conds)):
        for j in range(len(modes)):
            v = A[i, j]
            if not np.isnan(v):
                ax.text(j, i, f"{100 * v:.0f}", ha="center", va="center", fontsize=6.5,
                        color="white" if v > 0.55 else INK)
    ax.set_xticks(range(len(modes)), [m.replace("_", " ") for m in modes], rotation=35, ha="right", fontsize=7,
                  color=INK2)
    ax.set_yticks(range(len(conds)), [COND_NAME[c] for c in conds], fontsize=7, color=INK2)
    ax.set_xticks([x - 0.5 for x in range(1, len(modes))], minor=True)
    ax.set_yticks([y - 0.5 for y in range(1, len(conds))], minor=True)
    ax.grid(which="minor", color="white", linewidth=1.2)
    ax.tick_params(which="both", length=0)
    for s in ax.spines.values():
        s.set_visible(False)
    ax.set_title("Inconsistent final states (%) by fault mode, scripted driver, all read models", fontsize=8,
                 color=INK, loc="left")
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)


def dotplot(conf: dict, path: Path):
    """H1 population: inconsistency with cluster-bootstrap 95% CI per condition."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    rates = conf["H1"]["rates"]
    conds = [c for c in SCRIPTED_ORDER if c in rates and rates[c]["n"]]
    fig, ax = plt.subplots(figsize=(6.6, 3.9), dpi=300)
    for i, c in enumerate(conds):
        v = rates[c]
        lo, hi = v["ci95_cluster"]
        col = BLUE if c == "S" else (MUTED if c in ("O",) or c.startswith("S-") else INK2)
        ax.plot([100 * lo, 100 * hi], [i, i], color=col, linewidth=2, solid_capstyle="butt")
        ax.plot(100 * v["rate"], i, "o", color=col, markersize=5, markeredgecolor="white", markeredgewidth=1)
        ax.text(100 * hi + 1.2, i, f"{100 * v['rate']:.1f}", va="center", fontsize=6.5, color=INK2)
    ax.set_yticks(range(len(conds)), [COND_NAME[c] for c in conds], fontsize=7, color=INK2)
    ax.invert_yaxis()
    ax.set_xlim(0, 105)
    ax.set_xlabel("Inconsistent final state (%), 95% cluster-bootstrap interval", fontsize=7, color=INK2)
    ax.grid(axis="x", color=GRID, linewidth=0.6)
    ax.set_axisbelow(True)
    for s in ("top", "right", "left"):
        ax.spines[s].set_visible(False)
    ax.spines["bottom"].set_color(BASE)
    ax.tick_params(axis="x", labelsize=7, colors=INK2)
    ax.tick_params(axis="y", length=0)
    ax.set_title("Class-A reversible writes, ambiguous worlds (H1 population)", fontsize=8, color=INK, loc="left")
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)


# ------------------------------------------------------------------------------------------------ LLM
def llm_tables(L: dict, conf: dict, beh: list, figdir: Path):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    rows = []
    for m, rs in L.items():
        name = MODEL_NAME.get(m, m)
        h6 = conf["H6"]["per_model"].get(m, {})
        for c in LLM_ORDER:
            cr = [r for r in rs if r["condition"] == c]
            if not cr:
                continue
            hard = h6.get("hard", {}).get("rates", {}).get(c, {})
            easy = h6.get("easy", {}).get("rates", {}).get(c, {})
            amb = [r for r in cr if r["mode"] in AMBIG]
            usd = sum(r.get("usd") or 0 for r in cr) / len(cr)
            rows.append([name, COND_NAME[c], pct(hard.get("rate")), pct(easy.get("rate")), pct(rate(amb, overclaim)),
                         f"{sum(r.get('turns') or 0 for r in cr) / len(cr):.1f}", f"{usd:.4f}"])
            put(f"llm.{name}.{c}.hard", hard.get("rate"), "confirmatory.json: H6 per_model hard rates")
            put(f"llm.{name}.{c}.easy", easy.get("rate"), "confirmatory.json: H6 per_model easy rates")
            put(f"llm.{name}.{c}.overclaim", rate(amb, overclaim), "episodes: ambiguous, overclaim share")
            put(f"llm.{name}.{c}.usd", usd, "episodes: mean usd per episode")
            put(f"llm.{name}.{c}.n", len(cr), "episodes: finished")
    put("table.llm", md_table(["Model", "Condition", "Inconsistent %, hard worlds", "Inconsistent %, easy worlds",
                               "Overclaim % (ambiguous)", "Turns", "US$ / episode"], rows),
        "confirmatory.json H6 + test_llm episodes")
    # RQ1: what the agent does right after the first ambiguous write result (C0 = no recovery layer)
    cats = [("reissue", "re-issue at once", ORANGE), ("check", "check state", BLUE), ("wait", "wait", AQUA),
            ("other", "other / stop", YELLOW)]
    groups = []
    trows = []
    for m in L:
        name = MODEL_NAME.get(m, m)
        xs = [x for x in beh if x["driver"] == m and x["condition"] == "C0" and x.get("saw_fault")]
        if not xs:
            continue
        cnt = collections.Counter(x["first_action"] if x["first_action"] in ("reissue", "check", "wait") else "other"
                                  for x in xs)
        share = {k: cnt[k] / len(xs) for k, _, _ in cats}
        groups.append((name, share, len(xs)))
        chk = [x for x in xs if x.get("checked_before_reissue") is not None]
        for k in share:
            put(f"rq1.{name}.{k}", share[k], "llm_behaviour.jsonl: C0, first action after first ambiguous write result")
        put(f"rq1.{name}.n", len(xs), "llm_behaviour.jsonl: C0 episodes that saw a failed write")
        put(f"rq1.{name}.listed_uncertain", rate(xs, lambda x: x["listed_uncertain"]), "llm_behaviour.jsonl")
        put(f"rq1.{name}.claimed_completed", rate(xs, lambda x: x["claimed"] == "completed"), "llm_behaviour.jsonl")
        put(f"rq1.{name}.inconsistent", rate(xs, lambda x: bool(x["inconsistent"])), "llm_behaviour.jsonl")
        for truth in ("committed", "not_executed"):
            t = [x for x in xs if x["truth"] == truth]
            put(f"rq1.{name}.reissue.{truth}", rate(t, lambda x: x["first_action"] == "reissue"),
                f"llm_behaviour.jsonl: C0, hidden truth {truth}")
        trows.append([name, len(xs)] + [f"{100 * share[k]:.0f}" for k, _, _ in cats] +
                     [pct(rate(chk, lambda x: x["checked_before_reissue"])) if chk else "–",
                      pct(rate(xs, lambda x: x["listed_uncertain"])), pct(rate(xs, lambda x: x["claimed"] == "completed")),
                      pct(rate(xs, lambda x: bool(x["inconsistent"])))])
    put("table.rq1", md_table(["Model", "n", "Re-issue %", "Check %", "Wait %", "Other %", "Checked before re-issue %",
                               "Listed as uncertain %", "Claimed completed %", "Inconsistent %"], trows),
        "llm_behaviour.jsonl: C0 episodes that saw a failed write")
    if groups:
        fig, ax = plt.subplots(figsize=(6.4, 1.1 + 0.45 * len(groups)), dpi=300)
        for i, (name, share, n) in enumerate(groups):
            left = 0
            for k, label, col in cats:
                w = 100 * share[k]
                ax.barh(i, w, left=left, color=col, height=0.55, edgecolor="white", linewidth=1.5,
                        label=label if i == 0 else None)
                if w >= 7:
                    ax.text(left + w / 2, i, f"{w:.0f}", ha="center", va="center", fontsize=6.5,
                            color="white" if col in (BLUE, ORANGE) else INK)
                left += w
            ax.text(101, i, f"n={n}", va="center", fontsize=6.5, color=MUTED)
        ax.set_yticks(range(len(groups)), [g[0] for g in groups], fontsize=7, color=INK2)
        ax.invert_yaxis()
        ax.set_xlim(0, 110)
        ax.set_xticks([0, 25, 50, 75, 100])
        ax.tick_params(axis="x", labelsize=7, colors=INK2)
        ax.tick_params(axis="y", length=0)
        for s in ("top", "right", "left"):
            ax.spines[s].set_visible(False)
        ax.spines["bottom"].set_color(BASE)
        ax.legend(ncol=4, fontsize=6.5, frameon=False, loc="lower left", bbox_to_anchor=(0, 1.0))
        ax.set_xlabel("Share of episodes (%): first action after an ambiguous write result, no recovery layer",
                      fontsize=7, color=INK2)
        fig.tight_layout()
        fig.savefig(figdir / "fig_rq1_behaviour.png")
        plt.close(fig)


def validation(path: Path):
    d = json.loads(path.read_text(encoding="utf-8"))
    cells = d["cells"]
    services = ["gitea_issue", "mail", "pg_row", "pg_batch", "redis_stream", "redis_counter", "s3_put", "tb_transfer"]
    label = {"gitea_issue": "Gitea issue", "mail": "Mailpit SMTP", "pg_row": "PostgreSQL row",
             "pg_batch": "PostgreSQL batch", "redis_stream": "Redis stream", "redis_counter": "Redis counter",
             "s3_put": "SeaweedFS S3", "tb_transfer": "TigerBeetle"}
    modes = ["none", "lost_ack", "not_exec_err", "held", "not_exec_to", "late", "redelivery", "partial"]
    rows, n, ok = [], 0, 0
    for sv in services:
        row = [label[sv]]
        for m in modes:
            c = cells.get(f"{sv}|{m}")
            if not c:
                row.append("")
                continue
            n += c["n"]
            ok += round(c["as_intended_rate"] * c["n"])
            row.append(f"{round(c['as_intended_rate'] * c['n'])}/{c['n']}")
        rows.append(row)
    src = f"runs/validation/{path.parent.name}/summary.json"
    put("table.validation", md_table(["Service"] + [m.replace("_", " ") for m in modes], rows), src)
    put("val.trials", n, src)
    put("val.as_intended", ok, src)
    late = [c["late_landed_after_giveup_rate"] for c in cells.values() if c.get("late_landed_after_giveup_rate") is not None]
    put("val.late_after_giveup_min", min(late) if late else None, src)
    tag = [c["tag_fidelity_rate"] for c in cells.values() if c.get("tag_fidelity_rate") is not None]
    put("val.tag_fidelity_min", min(tag) if tag else None, src)
    eq = d["observation_equivalence"]
    put("val.equiv_all", all(g.get("equivalent", g.get("equivalent_tool_level", True)) for g in
                             (eq.values() if isinstance(eq, dict) else eq)) if eq else None, src)
    put("val.run", path.parent.name, src)


def fail_reason(r):
    """Which theory cell explains a Settle failure (the classification is fixed here, before reading the counts)."""
    if r["variant"] == "agg_shared":
        return "P5"                      # shared aggregate: not attributable
    if r["mode"] == "late_tail" and r["delay_s"] > r["delta_assumed_s"]:
        return "P2"                      # in-flight bound exceeded
    if r["focal_reversible"] == "none" and r["mode"] == "redelivery":
        return "P3"                      # irreversible duplicate by the transport
    if r["focal_cls"] == "C":
        return "P4"                      # content-only write
    return "other"


def settle_failures(rows, prefix, src):
    S = [r for r in rows if r["condition"] == "S" and r["mode"] in AMBIG]
    bad = [r for r in S if r["grade"]["residual_inconsistent"]]
    c = collections.Counter(fail_reason(r) for r in bad)
    put(f"{prefix}.S_amb_n", len(S), src)
    put(f"{prefix}.S_fail", len(bad), src + ": Settle, ambiguous, inconsistent")
    for k in ("P2", "P3", "P4", "P5", "other"):
        put(f"{prefix}.S_fail.{k}", c.get(k, 0), src + f": Settle failures explained by {k}")
    put(f"{prefix}.S_fail_reported", sum(1 for r in bad if not overclaim(r)), src + ": inconsistent Settle episodes "
        "that reported a problem")
    for k in ("P2", "P3", "P4", "P5"):
        put(f"{prefix}.S_fail_reported.{k}", sum(1 for r in bad if fail_reason(r) == k and not overclaim(r)), src)
    lt = [r for r in S if r["mode"] == "late_tail"]
    over = [r for r in lt if r["delay_s"] > r["delta_assumed_s"]]
    put(f"{prefix}.lt.n", len(lt), src)
    put(f"{prefix}.lt.over", len(over), src + ": late_tail worlds with delay > assumed bound")
    put(f"{prefix}.lt.fail_over", sum(r["grade"]["residual_inconsistent"] for r in over), src)
    put(f"{prefix}.lt.fail_under", sum(r["grade"]["residual_inconsistent"] for r in lt if r not in over), src)
    put(f"{prefix}.lt.min_fail_delay", min((r["delay_s"] for r in lt if r["grade"]["residual_inconsistent"]), default=None), src)


def llm_figure(conf, path):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    models = [m for m in ("llm:gpt-5.6-luna", "llm:gpt-4.1-mini", "llm:gpt-5.4-nano") if m in conf["H6"]["per_model"]]
    if not models:
        return
    fig, axes = plt.subplots(1, len(models), figsize=(7.2, 2.7), dpi=300, sharey=True)
    axes = axes if len(models) > 1 else [axes]
    for ax, m in zip(axes, models):
        pm = conf["H6"]["per_model"][m]
        for j, (part, col, off) in enumerate((("hard", ORANGE, -0.15), ("easy", BLUE, 0.15))):
            rates = pm[part]["rates"]
            for i, c in enumerate(LLM_ORDER):
                v = rates.get(c)
                if not v or v["rate"] is None:
                    continue
                lo, hi = v["ci95_cluster"]
                ax.plot([100 * lo, 100 * hi], [i + off, i + off], color=col, linewidth=1.6, solid_capstyle="butt")
                ax.plot(100 * v["rate"], i + off, "o", color=col, markersize=4.2, markeredgecolor="white",
                        markeredgewidth=0.8, label=(f"{part} worlds" if i == 0 else None))
        ax.set_title(MODEL_NAME[m], fontsize=7.5, color=INK, loc="left")
        ax.set_yticks(range(len(LLM_ORDER)), [COND_NAME[c] for c in LLM_ORDER], fontsize=6.5, color=INK2)
        ax.invert_yaxis() if ax is axes[0] else None
        ax.set_xlim(0, 100)
        ax.grid(axis="x", color=GRID, linewidth=0.5)
        ax.set_axisbelow(True)
        for sp in ("top", "right", "left"):
            ax.spines[sp].set_visible(False)
        ax.spines["bottom"].set_color(BASE)
        ax.tick_params(axis="x", labelsize=6.5, colors=INK2)
        ax.tick_params(axis="y", length=0)
    axes[0].legend(fontsize=6.5, frameon=False, loc="lower right")
    fig.supxlabel("Inconsistent final state (%), ambiguous worlds, 95% cluster-bootstrap interval", fontsize=7,
                  color=INK2)
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)


def pre_amendment(root: Path):
    """H6 numbers from the analysis before amendment 2 (results_v2), reported next to the final ones."""
    f = root / "results_v2" / "confirmatory.json"
    if not f.exists():
        return
    c = json.loads(f.read_text(encoding="utf-8"))
    for m, v in c["H6"]["per_model"].items():
        name = MODEL_NAME.get(m, m)
        for part in ("hard", "easy"):
            for cond, x in v[part]["rates"].items():
                put(f"pre.{name}.{cond}.{part}", x["rate"], "results_v2/confirmatory.json (before amendment 2)")
        put(f"pre.{name}.verdict", v["verdict"], "results_v2/confirmatory.json")


# ------------------------------------------------------------------------------------------------ main
def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=".")
    a = ap.parse_args(argv)
    root = Path(a.root).resolve()
    figdir = P / "figures"
    figdir.mkdir(exist_ok=True)
    (P / "build").mkdir(exist_ok=True)
    conf = json.loads((root / "results" / "confirmatory.json").read_text(encoding="utf-8"))
    beh = [json.loads(x) for x in (root / "results" / "llm_behaviour.jsonl").read_text(encoding="utf-8").splitlines()
           if x.strip()] if (root / "results" / "llm_behaviour.jsonl").exists() else []
    S, s_bad = load(root / "runs" / "test_scripted" / "episodes.jsonl")
    L, l_bad = {}, 0
    for d in sorted((root / "runs").glob("test_llm_*")):
        rs, b = load(d / "episodes.jsonl")
        l_bad += b
        for r in rs:
            L.setdefault(r["driver"], []).append(r)
    src = "runs/test_scripted/episodes.jsonl"
    put("n.scripted", len(S), src)
    put("n.scripted_excluded", s_bad, src)
    put("n.llm", sum(len(v) for v in L.values()), "runs/test_llm_*/episodes.jsonl")
    put("n.llm_excluded", l_bad, "runs/test_llm_*/episodes.jsonl")
    for m, rs in L.items():
        put(f"n.llm.{MODEL_NAME.get(m, m)}", len(rs), "runs/test_llm_*/episodes.jsonl")
    put("abs.n_episodes", len(S) + sum(len(v) for v in L.values()), "scripted + LLM finished test episodes")
    planned = 0
    for d in sorted((root / "runs").glob("test_llm_*")):
        g = d / "grid.json"
        if g.exists():
            planned += int(json.loads(g.read_text(encoding="utf-8")).get("n_total", 0))
    put("llm.n_planned", planned, "runs/test_llm_*/grid.json: n_total")
    amb = scripted_tables(S, src) if S else []
    # confirmatory numbers (copied, not recomputed)
    h1 = conf["H1"]
    best = h1["best_baseline"]
    put("h1.best", COND_NAME[best], "confirmatory.json: H1.best_baseline")
    put("h1.verdict", h1["verdict"], "confirmatory.json: H1.verdict")
    for c, v in h1["rates"].items():
        put(f"h1.{c}.rate", v["rate"], f"confirmatory.json: H1.rates.{c}.rate")
        put(f"h1.{c}.lo", v["ci95_cluster"][0], f"confirmatory.json: H1.rates.{c}.ci95_cluster[0]")
        put(f"h1.{c}.hi", v["ci95_cluster"][1], f"confirmatory.json: H1.rates.{c}.ci95_cluster[1]")
        put(f"h1.{c}.n", v["n"], f"confirmatory.json: H1.rates.{c}.n")
    for c, v in h1["comparisons"].items():
        put(f"h1.vs.{c}.diff", v["diff"], f"confirmatory.json: H1.comparisons.{c}.diff")
        put(f"h1.vs.{c}.lo", v["ci95_cluster"][0], "confirmatory.json")
        put(f"h1.vs.{c}.hi", v["ci95_cluster"][1], "confirmatory.json")
        put(f"h1.vs.{c}.p", v["p_holm"], "confirmatory.json")
        put(f"h1.vs.{c}.pairs", v["n_pairs"], "confirmatory.json")
    put("abs.S_rate", h1["rates"]["S"]["rate"], "confirmatory.json: H1.rates.S.rate")
    put("abs.best_rate", h1["rates"][best]["rate"], f"confirmatory.json: H1.rates.{best}.rate")
    put("h1.best.diff", h1["comparisons"][best]["diff"], "confirmatory.json")
    put("h1.best.lo", h1["comparisons"][best]["ci95_cluster"][0], "confirmatory.json")
    put("h1.best.hi", h1["comparisons"][best]["ci95_cluster"][1], "confirmatory.json")
    put("h1.best.p", h1["comparisons"][best]["p_holm"], "confirmatory.json")
    h2 = conf["H2"]
    put("h2.verdict", h2["verdict"], "confirmatory.json: H2.verdict")
    for c, v in h2["rates"].items():
        put(f"h2.{c}.rate", v["rate"], "confirmatory.json: H2.rates")
        put(f"h2.{c}.collateral", h2["collateral"][c]["rate"], "confirmatory.json: H2.collateral")
    h3 = conf["H3"]
    e = h3["S_vs_C4_equivalence"]
    put("h3.verdict", h3["verdict"], "confirmatory.json: H3.verdict")
    put("h3.diff", e["diff"], "confirmatory.json: H3.S_vs_C4_equivalence.diff")
    put("h3.lo", e["ci90_cluster"][0], "confirmatory.json")
    put("h3.hi", e["ci90_cluster"][1], "confirmatory.json")
    put("h3.pairs", e["n_pairs"], "confirmatory.json")
    for c, v in h3["rates"].items():
        put(f"h3.{c}.rate", v["rate"], "confirmatory.json: H3.rates")
    put("h3.C3.crash", h3["C3_crash_vs_rest"]["crash"]["rate"], "confirmatory.json")
    put("h3.C3.rest", h3["C3_crash_vs_rest"]["rest"]["rate"], "confirmatory.json")
    put("h3.S.r3", h3.get("S_rule_of_three_upper"), "confirmatory.json")
    h4 = conf["H4"]
    put("h4.verdict", h4["verdict"], "confirmatory.json: H4.verdict")
    for part in ("a", "b", "c"):
        put(f"h4.verdict_{part}", h4[f"verdict_{part}"], "confirmatory.json")
    agg = {c: v["rate"] for c, v in h4["agg_shared_rates"].items() if v["n"]}
    put("h4.agg_min", min(agg.values()) if agg else None, "confirmatory.json: min over H4.agg_shared_rates")
    put("h4.agg_min_cond", COND_NAME[min(agg, key=agg.get)] if agg else None, "confirmatory.json")
    put("h4.S_overclaim", h4["S_overclaim_agg_or_irreversible"]["rate"], "confirmatory.json")
    for c, v in h4["irreversible"].items():
        put(f"h4.irr.{c}.dup", v["irreversible_dup"]["rate"], "confirmatory.json: H4.irreversible")
        put(f"h4.irr.{c}.missing", v["missing"]["rate"], "confirmatory.json: H4.irreversible")
        put(f"h4.irr.{c}.overclaim", v["overclaim"]["rate"], "confirmatory.json: H4.irreversible")
    h5 = conf["H5"]
    put("h5.latency_verdict", h5["latency_verdict"], "confirmatory.json")
    put("h5.free.diff", h5["latency_fault_free"]["diff"], "confirmatory.json")
    put("h5.free.hi", h5["latency_fault_free"]["ci95_cluster"][1], "confirmatory.json")
    put("h5.amb.diff", h5["latency_ambiguous"]["diff"], "confirmatory.json")
    for m, v in h5["llm_cost_ratio_S_over_C6"].items():
        name = MODEL_NAME.get(m, m)
        put(f"h5.cost.{name}.ratio", v["ratio"], "confirmatory.json")
        put(f"h5.cost.{name}.lo", v["ci95_cluster"][0], "confirmatory.json")
        put(f"h5.cost.{name}.hi", v["ci95_cluster"][1], "confirmatory.json")
        put(f"h5.cost.{name}.verdict", h5["cost_verdicts"][m], "confirmatory.json")
    h6 = conf["H6"]
    put("h6.verdict", h6["verdict"], "confirmatory.json")
    for m, v in h6["per_model"].items():
        name = MODEL_NAME.get(m, m)
        put(f"h6.{name}.verdict", v["verdict"], "confirmatory.json")
        for c, x in v["hard"]["comparisons"].items():
            put(f"h6.{name}.vs.{c}.diff", x["diff"], "confirmatory.json")
            put(f"h6.{name}.vs.{c}.p", x["p_holm"], "confirmatory.json")
    rows = []
    for c, v in conf["ablations"]["per_ablation"].items():
        put(f"abl.{c}.diff", v["in_cell"]["diff"], "confirmatory.json: ablations")
        put(f"abl.{c}.out", v["outside_cell"]["diff"], "confirmatory.json: ablations")
        put(f"abl.{c}.verdict", v["verdict"], "confirmatory.json: ablations")
        lo, hi = v["in_cell"]["ci95_cluster"]
        rows.append([COND_NAME[c], v["component"], v["in_cell"]["n_pairs"], f"{100 * v['in_cell']['diff']:+.1f}",
                     f"[{100 * lo:+.1f}, {100 * hi:+.1f}]", f"{100 * (v['outside_cell']['diff'] or 0):+.1f}", v["verdict"]])
    put("table.ablation", md_table(["Ablation", "Component removed", "Pairs in cell", "Δ in cell (pp)", "95% CI",
                                    "Δ outside (pp)", "Verdict"], rows), "confirmatory.json: ablations")
    # spend and freeze
    led = root / "runs" / "cost_ledger.jsonl"
    if led.exists():
        L_ = [json.loads(x) for x in led.read_text(encoding="utf-8").splitlines() if x.strip()]
        put("cost.total", sum(x["usd"] for x in L_), "runs/cost_ledger.jsonl: sum usd")
        put("cost.test", sum(x["usd"] for x in L_ if str(x.get("run", "")).startswith("test_")), "ledger, test runs")
        put("cost.calls", len(L_), "ledger lines")
    fz = root / "FREEZE.json"
    first = sorted(root.glob("FREEZE_*_v1.json"))
    if fz.exists():
        f = json.loads(fz.read_text(encoding="utf-8"))
        put("freeze.digest", f["digest"][:12], "FREEZE.json (current freeze, after amendments)")
        put("freeze.files", len(f["files"]), "FREEZE.json")
        f0 = json.loads(first[0].read_text(encoding="utf-8")) if first else f
        put("freeze.at", f0["frozen_at_utc"].replace("T", " ").replace("Z", ""), (first[0].name if first else "FREEZE.json")
            + ": time of the first freeze")
        put("freeze.digest_v1", f0["digest"][:12], "first freeze digest")
        put("freeze.amended_at", f["frozen_at_utc"].replace("T", " ").replace("Z", ""), "FREEZE.json: re-freeze time")
        v2 = sorted(root.glob("FREEZE_*_v2.json"))
        if v2:
            f2 = json.loads(v2[0].read_text(encoding="utf-8"))
            put("freeze.digest_v2", f2["digest"][:12], v2[0].name)
            put("freeze.at_v2", f2["frozen_at_utc"].replace("T", " ").replace("Z", ""), v2[0].name)
    vals = sorted((root / "runs" / "validation").glob("*/summary.json"))
    if vals:
        validation(vals[-1])
    if amb:
        heatmap(amb, figdir / "fig_modes_heatmap.png", src)
    dotplot(conf, figdir / "fig_h1_dots.png")
    if S:
        settle_failures(S, "sc", src)
    for m, rs in L.items():
        settle_failures(rs, f"llmf.{MODEL_NAME.get(m, m)}", "runs/test_llm_*/episodes.jsonl")
    allL = [r for rs in L.values() for r in rs]
    if allL:
        settle_failures(allL, "llmf.all", "runs/test_llm_*/episodes.jsonl")
    for m, rs in L.items():
        name = MODEL_NAME.get(m, m)
        for c in LLM_ORDER:
            for cell in ("lost_ack", "not_exec_err", "late", "late_tail", "crash_after", "none"):
                x = [r for r in rs if r["condition"] == c and r["mode"] == cell and r["variant"] == "exact"]
                put(f"cell.{name}.{c}.{cell}", rate(x, inc), "test_llm episodes: exact reads, by mode")
            for var in ("lookalike", "lagged", "agg_shared"):
                x = [r for r in rs if r["condition"] == c and r["variant"] == var and r["mode"] in AMBIG]
                put(f"cell.{name}.{c}.{var}", rate(x, inc), "test_llm episodes: ambiguous modes, by read variant")
            x = [r for r in rs if r["condition"] == c]
            put(f"llm.{name}.{c}.collateral_eps", sum(1 for r in x if r["grade"]["collateral"] > 0),
                "test_llm episodes with collateral damage")
    if S:
        for mo in MODES:
            for c in SCRIPTED_ORDER:
                x = [r for r in S if r["condition"] == c and r["mode"] == mo]
                if x:
                    put(f"mode.{mo}.{c}", rate(x, inc), f"{src}: all variants, mode {mo}, condition {c}")
    if S:
        amb_s = [r for r in S if r["mode"] in AMBIG]
        h4 = [r for r in amb_s if r["condition"] == "S" and (r["variant"] == "agg_shared" or r["focal_reversible"] == "none")]
        h4i = [r for r in h4 if inc(r)]
        put("h4b.n", len(h4), src + ": Settle, ambiguous, shared-aggregate or irreversible focal")
        put("h4b.inc", len(h4i), src)
        put("h4b.reported", sum(1 for r in h4i if not overclaim(r)), src)
        put("h4b.over", sum(1 for r in h4 if overclaim(r)), src)
        for c in ("C4", "S", "C3"):
            x = [r for r in S if r["condition"] == c and r["mode"] == "crash_after" and r["focal_cls"] != "K"]
            put(f"crash_keyless.{c}", rate(x, inc), src + ": crash_after, focal write not class K")
            put(f"crash_keyless.{c}.n", len(x), src)
        for c in ("C3", "C4", "C0"):
            x = [r for r in amb_s if r["condition"] == c and r["focal_cls"] != "K"]
            put(f"keyless.{c}", rate(x, inc), src + ": ambiguous, focal write not class K")
    base_coll = sum(1 for rs in L.values() for r in rs if r["condition"] != "S" and r["grade"]["collateral"] > 0)
    put("llm.collateral_baselines", base_coll, "test_llm episodes with collateral damage, all non-Settle conditions")
    hp, lo_, hi_ = [], [], []
    for m, v in conf["H6"]["per_model"].items():
        for c, x in v["hard"]["comparisons"].items():
            hp.append(x["p_holm"])
        for c, x in v["hard"]["rates"].items():
            if c != "S" and x["rate"] is not None:
                lo_.append(x["rate"])
    if hp:
        put("h6.max_p_hard", max(hp), "confirmatory.json: largest Holm p over models x baselines, hard worlds")
        put("h6.base_min", min(lo_), "confirmatory.json: lowest baseline rate in hard worlds over models")
        put("h6.base_max", max(lo_), "confirmatory.json: highest baseline rate in hard worlds over models")
    pre_amendment(root)
    llm_figure(conf, figdir / "fig_llm_dots.png")
    if L:
        llm_tables(L, conf, beh, figdir)
    (P / "build" / "numbers.json").write_text(json.dumps(N, indent=1, ensure_ascii=False, default=str),
                                               encoding="utf-8")
    print(f"{len(N)} numbers; figures in {figdir}")


if __name__ == "__main__":
    main()
