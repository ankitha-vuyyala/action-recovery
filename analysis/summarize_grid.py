"""Summarize a grid run: python analysis/summarize_grid.py runs/<name>
Writes runs/<name>/summary.md. Descriptive only (the confirmatory analysis is frozen separately)."""
from __future__ import annotations

import collections
import json
import sys
from pathlib import Path

AMBIG = {"lost_ack", "not_exec_err", "held", "not_exec_to", "late", "late_tail", "redelivery", "partial",
         "crash_after", "crash_before"}


def load(run: Path) -> list[dict]:
    rows = []
    for line in (run / "episodes.jsonl").read_text(encoding="utf-8").splitlines():
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError:
            pass
    return rows


def overclaim(r: dict) -> bool:
    """Inconsistent final state, yet the run reported no problem at all."""
    g = r.get("grade", {})
    reported = (r.get("claimed") != "completed" or bool(r.get("uncertain")) or bool(r.get("duplicates_reported"))
                or bool(r.get("layer_uncertain")))
    return bool(g.get("residual_inconsistent")) and not reported


def rate(xs) -> str:
    xs = list(xs)
    return f"{100 * sum(xs) / len(xs):.1f}" if xs else "-"


def table(rows, key, title) -> list[str]:
    by = collections.defaultdict(list)
    for r in rows:
        by[key(r)].append(r)
    L = [f"### {title}", "", "| group | n | inconsistent % | episodes with duplicate % | irreversible dup % | "
         "missing % | collateral % | overclaim % | mean agent s |", "|---|---|---|---|---|---|---|---|---|"]
    for k in sorted(by, key=str):
        rs = [r for r in by[k] if "residual_inconsistent" in r.get("grade", {})]
        if not rs:
            continue
        g = [r["grade"] for r in rs]
        t = [r.get("agent_elapsed_s") or 0 for r in rs]
        L.append(f"| {k} | {len(rs)} | {rate(x['residual_inconsistent'] for x in g)} | "
                 f"{rate(x['dup_execs'] > 0 for x in g)} | {rate(x['irreversible_dup_execs'] > 0 for x in g)} | "
                 f"{rate(x['missing_steps'] > 0 for x in g)} | {rate(x['collateral'] > 0 for x in g)} | "
                 f"{rate(overclaim(r) for r in rs)} | {sum(t) / len(t):.1f} |")
    return L + [""]


def llm_table(rows) -> list[str]:
    """Model cost and behaviour per (driver, condition): what the full-study estimate is built from."""
    by = collections.defaultdict(list)
    for r in rows:
        if r.get("driver", "scripted") != "scripted":
            by[(r["driver"], r.get("condition"))].append(r)
    if not by:
        return []
    L = ["### LLM episodes: cost and behaviour", "",
         "| driver, condition | n | US$ total | US$/episode | paid calls | cached calls | turns/ep | tool calls/ep | "
         "input tok/ep | output tok/ep (reasoning) | no finish % | claimed completed % |",
         "|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for k in sorted(by, key=str):
        rs = by[k]
        n = len(rs)
        usd = sum(r.get("usd") or 0 for r in rs)
        m = lambda f: sum(r.get(f) or 0 for r in rs) / n  # noqa: E731
        L.append(f"| {k} | {n} | {usd:.4f} | {usd / n:.5f} | {sum(r.get('paid_calls') or 0 for r in rs)} | "
                 f"{sum(r.get('cached_calls') or 0 for r in rs)} | {m('turns'):.1f} | {m('tool_calls'):.1f} | "
                 f"{m('tokens_in'):.0f} | {m('tokens_out'):.0f} ({m('tokens_reasoning'):.0f}) | "
                 f"{rate(r.get('claimed') == 'no_finish' for r in rs)} | {rate(r.get('claimed') == 'completed' for r in rs)} |")
    return L + [""]


def main(run: Path) -> None:
    allrows = load(run)
    errs = [r for r in allrows if "error" in r or "grade_error" in r.get("grade", {})
            or str(r.get("stop") or "").startswith(("model error", "budget"))
            or (r.get("claimed") == "no_report" and r.get("child_rcs") and r["child_rcs"][-1] != 0)]
    rows = [r for r in allrows if r not in errs]                # metric tables use finished episodes only
    amb = [r for r in rows if r.get("mode") in AMBIG]
    L = [f"# Grid summary: {run.name}", "", f"episodes: {len(allrows)} (finished {len(rows)}) · errors: {len(errs)} · ambiguous-world episodes: {len(amb)}", ""]
    L += table(rows, lambda r: r.get("condition"), "All worlds, by condition")
    L += table([r for r in rows if r.get("mode") == "none"], lambda r: r.get("condition"), "Fault-free worlds (sanity: all should be 0)")
    L += table(amb, lambda r: r.get("condition"), "Ambiguous worlds, by condition")
    L += table(amb, lambda r: (r.get("focal_cls"), r.get("focal_reversible"), r.get("condition")),
               "Ambiguous worlds by focal contract (class, reversibility) and condition")
    L += table(amb, lambda r: (r.get("mode"), r.get("condition")), "Ambiguous worlds by mode and condition")
    L += table([r for r in amb if r.get("variant") != "exact"], lambda r: (r.get("variant"), r.get("condition")),
               "Read-model variants by condition")
    L += llm_table(rows)
    if errs:
        L += ["### Errors", ""] + [f"- {r.get('episode_id')} {r.get('condition')} {r.get('mode')}: "
                                   f"{r.get('error') or (r.get('grade') or {}).get('grade_error') or r.get('stop')}" for r in errs[:50]]
    (run / "summary.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    print("\n".join(L[:40]))


if __name__ == "__main__":
    main(Path(sys.argv[1]))
