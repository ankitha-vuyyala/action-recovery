"""RQ1 (descriptive, pre-specified in docs/06_analysis_plan.md §5): how do LLM agents treat an ambiguous tool
outcome? Code-only coding of each LLM episode's saved conversation (runs/<grid>/episodes/<id>/conversation.json).

    python analysis/llm_behaviour.py runs/<llm grid> [more grids] --out results/

For the first tool result the agent sees with status error / timeout / unknown / blocked (the injected fault on
the focal write, or the recovery layer's report of it), the agent's NEXT function call is coded as:
  reissue      the same write tool again
  check        a read tool (list/get/search/find/object_exists/get_*)
  compensate   one of the agent's own deletion / reversal tools
  wait         the wait tool
  finish       finish
  other_write  a different write tool (moved on to the next step)
  none         no further call
plus: checked_before_reissue (any read between the fault and the first re-issue), reissues (count of further
calls of that write tool), and the final report: claimed status, uncertain list non-empty, and whether the
summary uses uncertainty language (fixed word list below). The hidden truth is the injected mode: committed
(lost_ack, held, late, late_tail, crash_after, redelivery) or not executed (not_exec_err, not_exec_to,
crash_before). Paired modes give the agent identical observations, so any behavioural difference between the
two hidden truths beyond sampling noise would itself be a finding (a leak in the fault injection).
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "code"))
from actrec.agent_tools import WRITE_TOOLS  # noqa: E402

COMMITTED = {"lost_ack", "held", "late", "late_tail", "crash_after", "redelivery"}
NOT_EXECUTED = {"not_exec_err", "not_exec_to", "crash_before"}
BAD = ('"status": "error"', '"status": "timeout"', '"status": "unknown"', '"status": "blocked"')
COMPENSATE = {"delete_issue", "delete_comment", "delete_record", "delete_event", "reverse_transfer"}
UNCERTAIN_WORDS = re.compile(r"\b(uncertain|unclear|unknown|unsure|not sure|may have|might have|possibly|"
                             r"could not (?:confirm|verify)|cannot (?:confirm|verify)|unable to (?:confirm|verify)|"
                             r"timed out|ambiguous|duplicate)\b", re.I)


def code_episode(conv: dict) -> dict | None:
    items = conv.get("input") or []
    calls = {i["call_id"]: i for i in items if i.get("type") == "function_call"}
    seq = [i for i in items if i.get("type") in ("function_call", "function_call_output")]
    fault_at, fault_tool = None, None
    for n, it in enumerate(seq):
        if it["type"] == "function_call_output" and any(b in it.get("output", "") for b in BAD):
            c = calls.get(it["call_id"])
            if c and c["name"] in WRITE_TOOLS:
                fault_at, fault_tool = n, c["name"]
                break
    if fault_at is None:
        return None
    after = [i for i in seq[fault_at + 1:] if i["type"] == "function_call"]
    nxt = after[0]["name"] if after else None
    if nxt is None:
        first = "none"
    elif nxt == fault_tool:
        first = "reissue"
    elif nxt == "finish":
        first = "finish"
    elif nxt == "wait":
        first = "wait"
    elif nxt in COMPENSATE:
        first = "compensate"
    elif nxt in WRITE_TOOLS:
        first = "other_write"
    else:
        first = "check"
    reissue_idx = next((k for k, c in enumerate(after) if c["name"] == fault_tool), None)
    before = after[:reissue_idx] if reissue_idx is not None else after
    checked = any(c["name"] not in WRITE_TOOLS and c["name"] not in COMPENSATE and c["name"] not in ("finish", "wait")
                  for c in before)
    fin = conv.get("finish") or {}
    text = (fin.get("summary") or "") + " " + " ".join(map(str, fin.get("uncertain_operations") or [])) + " " + \
        (conv.get("last_text") or "")
    return {"first_action": first, "reissues": sum(1 for c in after if c["name"] == fault_tool),
            "checked_before_reissue": checked if reissue_idx is not None else None,
            "claimed": fin.get("status", "no_finish"), "listed_uncertain": bool(fin.get("uncertain_operations")),
            "uncertainty_language": bool(UNCERTAIN_WORDS.search(text)), "fault_tool": fault_tool}


def main(argv=None) -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("runs", nargs="+")
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    coded = []
    for run in a.runs:
        run = Path(run)
        for line in (run / "episodes.jsonl").read_text(encoding="utf-8").splitlines():
            r = json.loads(line)
            if r.get("driver", "scripted") == "scripted" or str(r.get("stop") or "").startswith(("model error", "budget")):
                continue
            ck = run / "episodes" / r["episode_id"] / "conversation.json"
            if not ck.exists():
                continue
            c = code_episode(json.loads(ck.read_text(encoding="utf-8")))
            truth = "committed" if r["mode"] in COMMITTED else "not_executed" if r["mode"] in NOT_EXECUTED else "none"
            coded.append({"episode_id": r["episode_id"], "driver": r["driver"], "condition": r["condition"],
                          "mode": r["mode"], "truth": truth, "template": r["template"], "saw_fault": c is not None,
                          "inconsistent": (r.get("grade") or {}).get("residual_inconsistent"),
                          "dup_execs": (r.get("grade") or {}).get("dup_execs"), **(c or {})})
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "llm_behaviour.jsonl").write_text("".join(json.dumps(x) + "\n" for x in coded), encoding="utf-8")
    by = defaultdict(list)
    for x in coded:
        if x["saw_fault"]:
            by[(x["driver"], x["condition"], x["truth"])].append(x)
    acts = ["reissue", "check", "wait", "compensate", "other_write", "finish", "none"]
    L = ["# LLM behaviour after an ambiguous tool outcome", "",
         "First action after the first failed/unknown write result, by driver, condition and hidden truth (%).", "",
         "| driver | condition | hidden truth | n | " + " | ".join(acts) + " | checked before re-issue | "
         "listed uncertain | uncertainty language | claimed completed | inconsistent |",
         "|" + "---|" * (len(acts) + 9)]
    for k in sorted(by):
        xs = by[k]
        n = len(xs)
        cnt = Counter(x["first_action"] for x in xs)
        rs = [x for x in xs if x["checked_before_reissue"] is not None]
        p = lambda f: f"{100 * sum(1 for x in xs if f(x)) / n:.0f}"  # noqa: E731
        chk = f"{100 * sum(x['checked_before_reissue'] for x in rs) / len(rs):.0f} (of {len(rs)})" if rs else "-"
        L.append(f"| {k[0]} | {k[1]} | {k[2]} | {n} | " + " | ".join(f"{100 * cnt[a_] / n:.0f}" for a_ in acts) +
                 f" | {chk} | {p(lambda x: x['listed_uncertain'])} | {p(lambda x: x['uncertainty_language'])} | "
                 f"{p(lambda x: x['claimed'] == 'completed')} | {p(lambda x: bool(x['inconsistent']))} |")
    (out / "llm_behaviour.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    print("\n".join(L))


if __name__ == "__main__":
    main(sys.argv[1:])
