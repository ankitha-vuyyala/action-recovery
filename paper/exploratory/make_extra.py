"""Numbers, tables and figures for the two exploratory analyses (not pre-registered):
the API census (census/census.csv, coded from vendor documentation) and the horizon replay (horizon.json).
Writes exploratory/numbers_extra.json, which build.py merges into the evidence index."""
import csv, json
from collections import Counter
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

P = Path(__file__).resolve().parent
FIG = P.parent / "figures"
INK, INK2, MUTED, GRID, BASE = "#0b0b0b", "#52514e", "#898781", "#e1e0d9", "#c3c2b7"
RAMP = {"K": "#1d4f91", "A": "#2a78d6", "A-": "#8fb8ea", "C": "#898781"}
DOM = {"payments": "Payments and commerce", "devtools": "Developer and project tools",
       "messaging": "Messaging and e-mail", "crmdata": "CRM, data and cloud"}
OUT = {}


def put(k, v, src):
    OUT[k] = {"value": v, "source": src}


def census():
    rows = list(csv.DictReader(open(P / "census" / "census.csv", encoding="utf-8")))
    src = "exploratory/census/census.csv"
    n = len(rows)
    put("cen.n", n, src)
    c = Counter(r["class"] for r in rows)
    for k in ("K", "A", "A-", "C"):
        put(f"cen.{k}", c[k], src)
        put(f"cen.{k}.frac", c[k] / n, src)
    kl = [r for r in rows if r["class"] != "K"]
    put("cen.keyless", len(kl), src)
    put("cen.keyless.frac", len(kl) / n, src)
    tag = [r for r in kl if r["class"] in ("A", "A-")]
    put("cen.keyless.tag", len(tag), src)
    put("cen.keyless.tag.frac", len(tag) / len(kl), src)
    put("cen.keyless.exact.frac", c["A"] / len(kl), src)
    put("cen.keyless.C.frac", c["C"] / len(kl), src)
    # strict reading: Discord and SES (lookup by list scanning only of uncertain completeness) move to C
    strictC = c["C"] + sum(r["api"] in ("Discord", "Amazon SES v2") for r in rows)
    put("cen.strict.C", strictC, src)
    put("cen.strict.C.frac", strictC / len(kl), src)
    put("cen.near_key", sum(r["key"].startswith("partial") for r in kl), src)
    K = [r for r in rows if r["class"] == "K"]
    short = [r for r in K if r["key_retention"] in ("1 h", "2 h", "6 h", "while alert open")]
    put("cen.K.short", len(short), src)
    put("cen.K.undoc", sum(r["key_retention"] == "undocumented" for r in K), src)
    put("cen.K.nolookup", sum(r["lookup"].startswith(("list", "none")) for r in K), src)
    put("cen.K.payments", sum(r["domain"] == "payments" for r in K), src)
    put("cen.payments", sum(r["domain"] == "payments" for r in rows), src)
    put("cen.K.payments.nolookup", sum(r["domain"] == "payments" and r["lookup"].startswith(("list", "none"))
                                       for r in K), src)
    put("cen.tag.hidden", sum(r["hidden_tag"] == "yes" for r in tag), src)
    put("cen.tag.visible", sum(r["hidden_tag"] == "no" for r in tag), src)
    put("cen.tag.unclear", sum(r["hidden_tag"] == "unclear" for r in tag), src)
    put("cen.keyless.anyfield", sum(r["tag_field"] != "none" for r in kl), src)
    put("cen.K.payments.listscan", sum(r["domain"] == "payments" and r["lookup"].startswith("list") for r in K), src)
    put("cen.A.rev_full", sum(r["class"] == "A" and r["reversible"] == "yes" for r in rows), src)
    put("cen.A.rev_partial", sum(r["class"] == "A" and r["reversible"] == "partial" for r in rows), src)
    # strict reading of lookups: Mailgun (events API, deprecated, retention-limited) and Graph sendMail
    # (copy in Sent Items, freshness undocumented) count as lagged, Discord and SES as C
    put("cen.strict.A", c["A"] - 2, src)
    conv = [r for r in rows if r["class"] == "A" and r["reversible"] != "no"]
    put("cen.A.reversible", len(conv), src)
    put("cen.A.irreversible", sum(r["class"] == "A" and r["reversible"] == "no" for r in rows), src)
    put("cen.verify.n", 12, "exploratory/census/verify_result.json")
    put("cen.verify.class_ok", 12, "exploratory/census/verify_result.json")
    put("cen.verify.fact_errors", 1, "exploratory/census/verify_result.json")
    for d in DOM:
        cd = Counter(r["class"] for r in rows if r["domain"] == d)
        for k in ("K", "A", "A-", "C"):
            put(f"cen.{d}.{k}", cd[k], src)
    # appendix table
    lines = ["| API (operation) | Class | Server-side key (retention) | Tag field | Hidden | Lookup by tag | Undo |",
             "|---|---|---|---|---|---|---|"]
    for d in DOM:
        for r in rows:
            if r["domain"] != d:
                continue
            key = r["key"] if r["key"] != "none" else "none"
            if r["key_retention"] and r["key"] in ("native", "conditional create"):
                key += f" ({r['key_retention']})"
            key = key.replace("7-14 d", "7–14 d").replace(">=30 d", "≥ 30 d")
            lines.append(f"| {r['api']} ({r['operation']}) | {r['class'].replace('A-', 'A−')} | {key} | {r['tag_field']} | {r['hidden_tag']} | "
                         f"{r['lookup']} | {r['reversible']} |")
    put("table.census", "\n".join(lines), src)
    # figure
    fig, ax = plt.subplots(figsize=(7.0, 2.4), dpi=300)
    names = list(DOM)[::-1]
    for i, d in enumerate(names):
        cd = Counter(r["class"] for r in rows if r["domain"] == d)
        left = 0
        for k in ("K", "A", "A-", "C"):
            w = cd[k]
            if not w:
                continue
            ax.barh(i, w, left=left, height=0.62, color=RAMP[k], edgecolor="white", linewidth=1.5)
            ax.text(left + w / 2, i, str(w), ha="center", va="center", fontsize=7,
                    color="white" if k in ("K", "A", "C") else INK)
            left += w
    ax.set_yticks(range(len(names)))
    ax.set_yticklabels([DOM[d] for d in names], fontsize=7.5, color=INK2)
    ax.set_xlabel("APIs examined", fontsize=7.5, color=INK2)
    ax.tick_params(axis="x", labelsize=7, colors=INK2)
    for s in ("top", "right", "left"):
        ax.spines[s].set_visible(False)
    ax.spines["bottom"].set_color(BASE)
    lab = {"K": "K: server-side key", "A": "A: tag + exact lookup", "A-": "A−: tag, lagged or scan lookup",
           "C": "C: no usable tag"}
    from matplotlib.patches import Patch
    ax.legend(handles=[Patch(color=RAMP[k], label=lab[k]) for k in RAMP], loc="upper center",
              bbox_to_anchor=(0.4, -0.3), ncol=4, fontsize=6.5, frameon=False, handlelength=1.2)
    fig.tight_layout()
    fig.subplots_adjust(bottom=0.36)
    fig.savefig(FIG / "fig_census.png")


def horizon():
    h = json.loads((P / "horizon.json").read_text())
    src = "exploratory/horizon.json"
    put("hz.n_timing", h["n_timing"], src)
    put("hz.agree", h["agree"], src)
    put("hz.agree.frac", h["agree"] / h["n_timing"], src)
    put("hz.n_tail", h["n_tail"], src)
    put("hz.c0_latency", h["c0_median_latency_s"], src)
    for p in h["curve"]:
        d = str(p["delta"]).replace(".", "_")
        put(f"hz.{d}.tail", p["late_tail_inconsistent"], src)
        put(f"hz.{d}.late12", p["late12_inconsistent"], src)
        put(f"hz.{d}.lat", p["median_latency_s"], src)
    xs = [p["delta"] for p in h["curve"]]
    fig, (a, b) = plt.subplots(1, 2, figsize=(7.2, 2.5), dpi=300)
    a.plot(xs, [100 * p["late_tail_inconsistent"] for p in h["curve"]], color="#2a78d6", linewidth=1.3,
           marker="o", markersize=3.5, label="heavy-tailed delay (5–120 s)")
    a.plot(xs, [100 * p["late12_inconsistent"] for p in h["curve"]], color="#eb6834", linewidth=1.3,
           marker="s", markersize=3.5, label="fixed 12 s delay")
    a.axvline(20, color=MUTED, linewidth=1, linestyle=(0, (3, 2)))
    a.text(21.5, 3, "frozen Δ = 20 s", fontsize=6.5, color=INK2)
    a.set_xlabel("assumed in-flight bound Δ (s)", fontsize=7.5, color=INK2)
    a.set_ylabel("inconsistent after Settle (%)", fontsize=7.5, color=INK2)
    a.legend(fontsize=6.5, frameon=False, loc="upper right")
    b.plot(xs, [p["median_latency_s"] for p in h["curve"]], color="#2a78d6", linewidth=1.3, marker="o", markersize=3.5)
    b.axhline(h["c0_median_latency_s"], color=MUTED, linewidth=1, linestyle=(0, (3, 2)))
    b.text(60, h["c0_median_latency_s"] + 4, "plain retry (C0), median", fontsize=6.5, color=INK2)
    b.set_xlabel("assumed in-flight bound Δ (s)", fontsize=7.5, color=INK2)
    b.set_ylabel("median episode time (s),\nlost-reply, timeout, late modes", fontsize=7.5, color=INK2)
    for ax in (a, b):
        ax.tick_params(labelsize=7, colors=INK2)
        ax.grid(color=GRID, linewidth=0.6)
        for s in ("top", "right"):
            ax.spines[s].set_visible(False)
        for s in ("left", "bottom"):
            ax.spines[s].set_color(BASE)
    fig.tight_layout()
    fig.savefig(FIG / "fig_horizon.png")


def r1(v):
    from decimal import Decimal, ROUND_HALF_UP
    return str(Decimal(str(round(100 * v, 6))).quantize(Decimal("0.1"), rounding=ROUND_HALF_UP))


def robustness():
    rb = json.loads((P / "robustness.json").read_text())
    src = "exploratory/robustness.json"
    conds = ["C0", "C4", "C6", "Gw", "S-h", "S-c", "S-j", "S-t", "S", "O"]
    for m, d in rb["by_mode"].items():
        for c, v in d.items():
            put(f"rb.{m}.{c}", v, src)
    for c, v in rb["core"].items():
        put(f"rb.core.{c}", v, src)
    put("rb.core_n", rb["core_n"], src)
    for k in ("tclust_h1", "tclust_core"):
        for f, v in rb[k].items():
            put(f"rb.{k}.{f}", v, src)
    put("rb.lt_fail_rev", rb["lt_fail_reversible"], src)
    put("rb.lt_fail_irr", rb["lt_fail_irreversible"], src)
    names = {"S-h": "S−h", "S-c": "S−c", "S-j": "S−j", "S-t": "S−t"}
    order = ["lost_ack", "not_exec_err", "held", "not_exec_to", "late", "late_tail", "crash_after", "crash_before",
             "redelivery", "partial"]
    lines = ["| Fault mode | worlds | " + " | ".join(names.get(c, c) for c in conds) + " |",
             "|---|---|" + "---|" * len(conds)]
    for m in order:
        lines.append(f"| {m} | {rb['n_by_mode'][m]} | " +
                     " | ".join(r1(rb['by_mode'][m][c]) for c in conds) + " |")
    lines.append(f"| all but redelivery and partial | {rb['core_n']} | " +
                 " | ".join(r1(rb['core'][c]) for c in conds) + " |")
    put("table.h1modes", "\n".join(lines), src)


def relabel():
    nb = json.loads((P.parent / "build" / "numbers.json").read_text(encoding="utf-8"))
    t = nb["table.map"]["value"].replace("| content-only, irreversible |", "| C, content only, irreversible |")
    put("table.map", t, nb["table.map"]["source"] + " (class label unified)")


if __name__ == "__main__":
    relabel()
    census()
    horizon()
    robustness()
    (P / "numbers_extra.json").write_text(json.dumps(OUT, indent=1, ensure_ascii=False), encoding="utf-8")
    for k, v in OUT.items():
        if not k.startswith("table"):
            print(k, v["value"])
