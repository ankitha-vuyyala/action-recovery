"""Numbers for the follow-up section of the paper (pre-registered follow-up, docs/07_followup_plan.md).
Reads results_followup/followup.json (analysis/followup.py, with the documented zero-rate correction), the follow-up
episode records and the frontier model's behaviour coding; writes paper/followup/numbers_followup.json."""
import json
import sys
from collections import Counter
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = P.parents[1]
RUNS = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "runs"
RES = json.loads((ROOT / "results_followup" / "followup.json").read_text())
BEH = Path(sys.argv[2]) if len(sys.argv) > 2 else ROOT / "results_followup" / "llm_behaviour.jsonl"
OUT = {}
SRC = "results_followup/followup.json"
MODEL = {"llm:gpt-5.6-luna": "gpt-5.6-luna", "llm:gpt-4.1-mini": "gpt-4.1-mini", "llm:gpt-5.4-nano": "gpt-5.4-nano",
         "llm:gpt-5.6-sol": "gpt-5.6-sol"}


def put(k, v, src=SRC):
    OUT[k] = {"value": v, "source": src}


def rate(d, pre):
    put(pre, d["rate"]); put(pre + ".k", d["k"]); put(pre + ".n", d["n"])
    put(pre + ".lo", d["ci95_cluster"][0]); put(pre + ".hi", d["ci95_cluster"][1])


def load(name):
    f = RUNS / name / "episodes.jsonl"
    return [json.loads(l) for l in f.read_text().splitlines() if l.strip()] if f.exists() else []


F1, F2, F3, F4, F5, F6, F7 = (RES[k] for k in ("F1", "F2", "F3", "F4", "F5", "F6", "F7"))
for c, v in F1["core_rates"].items():
    rate(v, f"fu.f1.core.{c}")
eq = F1["a_equivalence_core"]
put("fu.f1.eq.diff", eq["diff"]); put("fu.f1.eq.lo", eq["ci90_cluster"][0]); put("fu.f1.eq.hi", eq["ci90_cluster"][1])
put("fu.f1.eq.pairs", eq["n_pairs"]); put("fu.f1.a_verdict", F1["a_verdict"])
rate(F1["b_redelivery"]["Sp"], "fu.f1.red.Sp"); rate(F1["b_redelivery"]["S"], "fu.f1.red.S")
put("fu.f1.b_verdict", F1["b_verdict"])
lt = F1["c_late_tail"]
put("fu.f1.lt.diff", lt["diff"]); put("fu.f1.lt.pairs", lt["n_pairs"]); put("fu.f1.lt.Sp_only", lt["a_only"])
put("fu.f1.lt.S_only", lt["b_only"]); put("fu.f1.lt.p", lt["p_mcnemar"]); put("fu.f1.c_verdict", F1["c_verdict"])
for c in ("S", "Sp", "S2"):
    put(f"fu.f1.lt.{c}", F1["by_mode"]["late_tail"][c])
lat = F1["d_latency"]
put("fu.f1.lat.diff", lat["diff"]); put("fu.f1.lat.lo", lat["ci95_cluster"][0]); put("fu.f1.lat.hi", lat["ci95_cluster"][1])
for c in ("S", "S2", "Sp"):
    rate(F2[c]["inconsistent"], f"fu.f2.{c}.inc")
    rate(F2[c]["overclaim"], f"fu.f2.{c}.over")
put("fu.f2.verdict", F2["verdict"])
e3 = F3["equivalence_h1"]
put("fu.f3.diff", e3["diff"]); put("fu.f3.lo", e3["ci90_cluster"][0]); put("fu.f3.hi", e3["ci90_cluster"][1])
put("fu.f3.verdict", F3["verdict"]); put("fu.f3.free_time", F3["fault_free_time"]["diff"])
put("fu.f3.free_time.lo", F3["fault_free_time"]["ci95_cluster"][0]); put("fu.f3.free_time.hi", F3["fault_free_time"]["ci95_cluster"][1])
for part in ("reversible", "irreversible", "irreversible_overclaim", "keyed"):
    for c, v in F4[part].items():
        rate(v, f"fu.f4.{part}.{c}")
for k in ("a_verdict", "b_verdict", "c_verdict"):
    put(f"fu.f4.{k}", F4[k])
for c, v in F5["rates"].items():
    rate(v, f"fu.f5.{c}")
for m, d in F5["by_mode"].items():
    for c, v in d.items():
        put(f"fu.f5.mode.{m}.{c}", v)
ni = F5["b_noninferiority"]
put("fu.f5.ni.diff", ni["diff"]); put("fu.f5.ni.hi", ni["ci90_cluster"][1])
put("fu.f5.a_verdict", F5["a_verdict"]); put("fu.f5.b_verdict", F5["b_verdict"])
for c, v in F5["collateral_episodes"].items():
    put(f"fu.f5.coll.{c}", v)
for m, d in F6.items():
    mm = MODEL[m]
    for part in ("hard", "easy"):
        rate(d[part]["S"], f"fu.f6.{mm}.{part}.S"); rate(d[part]["S-np"], f"fu.f6.{mm}.{part}.Snp")
        p = d[part]["paired"]
        put(f"fu.f6.{mm}.{part}.diff", p["diff"]); put(f"fu.f6.{mm}.{part}.hi", p["ci90_cluster"][1])
        put(f"fu.f6.{mm}.{part}.disc", p["a_only"] + p["b_only"])
    put(f"fu.f6.{mm}.verdict", d["verdict"]); put(f"fu.f6.{mm}.nfail", len(d["failures"]))
for m, d in F7.items():
    mm = MODEL[m]
    rate(d["hard"]["C0"], f"fu.f7.hard.C0"); rate(d["hard"]["S-np"], f"fu.f7.hard.Snp")
    p = d["hard"]["paired"]
    put("fu.f7.hard.diff", p["diff"]); put("fu.f7.hard.lo", p["ci95_cluster"][0]); put("fu.f7.hard.hi", p["ci95_cluster"][1])
    put("fu.f7.hard.p", p["p_mcnemar"]); put("fu.f7.hard.pairs", p["n_pairs"])
    rate(d["easy"]["C0"], "fu.f7.easy.C0"); rate(d["easy"]["S-np"], "fu.f7.easy.Snp")
    put("fu.f7.usd.C0", d["usd_per_episode"]["C0"]); put("fu.f7.usd.Snp", d["usd_per_episode"]["S-np"])
    put("fu.f7.verdict", d["verdict"])
# frontier: cells of the plain agent and behaviour coding (descriptive)
sol = load("followup_llm_frontier_sol")
src = "runs/followup_llm_frontier_sol/episodes.jsonl"
c0 = [r for r in sol if r["condition"] == "C0"]
inc = lambda r: bool(r["grade"]["residual_inconsistent"])
for name, sel in (("lookalike", lambda r: r["variant"] == "lookalike"),
                  ("crash_after", lambda r: r["mode"] == "crash_after" and r["variant"] == "exact"),
                  ("late_tail", lambda r: r["mode"] == "late_tail" and r["variant"] == "exact"),
                  ("lost_ack", lambda r: r["mode"] == "lost_ack" and r["variant"] == "exact")):
    x = [r for r in c0 if sel(r)]
    put(f"fu.f7.cell.{name}", sum(map(inc, x)) / len(x) if x else None, src)
    put(f"fu.f7.cell.{name}.n", len(x), src)
put("fu.f7.usd.total", sum(r.get("usd") or 0 for r in sol), src)
beh = [json.loads(l) for l in BEH.read_text().splitlines() if l.strip()]
b0 = [b for b in beh if b["condition"] == "C0" and b.get("saw_fault")]
fa = Counter(b.get("first_action") for b in b0)
put("fu.rq1.n", len(b0), "results_followup/llm_behaviour.jsonl")
for k in ("reissue", "check"):
    put(f"fu.rq1.{k}", fa[k] / len(b0), "results_followup/llm_behaviour.jsonl")
put("fu.rq1.listed_uncertain", sum(bool(b.get("listed_uncertain")) for b in b0) / len(b0), "results_followup/llm_behaviour.jsonl")
put("fu.rq1.claimed_completed", sum(b.get("claimed") == "completed" for b in b0) / len(b0), "results_followup/llm_behaviour.jsonl")
# Sp and S2 on the whole H1 population (paired with the frozen S records by world)
fa = load("followup_a")
AMB = {"lost_ack", "not_exec_err", "held", "not_exec_to", "late", "late_tail", "redelivery", "partial",
       "crash_after", "crash_before"}
h1 = [r for r in fa if r["mode"] in AMB and r["focal_cls"] == "A" and r["focal_reversible"] == "targeted"]
for c in ("Sp", "S2"):
    x = [r for r in h1 if r["condition"] == c]
    put(f"fu.h1.{c}", sum(map(inc, x)) / len(x), "runs/followup_a/episodes.jsonl")
    put(f"fu.h1.{c}.k", sum(map(inc, x)), "runs/followup_a/episodes.jsonl")
    put(f"fu.h1.{c}.n", len(x), "runs/followup_a/episodes.jsonl")
lt4 = sorted(r["delay_s"] for r in h1 if r["condition"] == "Sp" and r["mode"] == "late_tail" and inc(r))
put("fu.f1.lt.Sp_fail_delays", lt4, "runs/followup_a/episodes.jsonl")
# sizes and spending
n_s = sum(len(load(g)) for g in ("followup_a", "followup_b", "followup_c"))
n_l = sum(len(load(g)) for g in ("followup_llm_np_luna", "followup_llm_np_41mini", "followup_llm_np_nano"))
put("fu.n.scripted", n_s, "runs/followup_*/episodes.jsonl"); put("fu.n.np", n_l, "runs/followup_llm_np_*")
put("fu.n.sol", len(sol), src); put("fu.n.all", n_s + n_l + len(sol), "runs/followup_*")
put("fu.n.a", len(load("followup_a")), "runs/followup_a"); put("fu.n.b", len(load("followup_b")), "runs/followup_b")
put("fu.n.c", len(load("followup_c")), "runs/followup_c")
put("fu.excluded", sum(RES["excluded"].values()), SRC)
put("fu.usd.new", 6.0870, "runs/FOLLOWUP_STATUS.txt: total new spending")
put("fu.usd.ledger", 9.4853, "runs/FOLLOWUP_STATUS.txt: ledger after the frontier grid")
put("fu.usd.np", 0.4562, "runs/FOLLOWUP_STATUS.txt: plan-free Settle grids")
(P / "numbers_followup.json").write_text(json.dumps(OUT, indent=1))
for k, v in OUT.items():
    print(k, v["value"] if not isinstance(v["value"], float) else round(v["value"], 4))
