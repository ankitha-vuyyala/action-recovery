# Follow-up study: analysis plan (frozen before any follow-up episode; freeze v3)

Written 2026-10-04, after the main study (frozen protocol, docs/06_analysis_plan.md) and before any follow-up
episode ran. The main study's records, analysis and verdicts are not changed by this study. The follow-up answers
the open points of two independent reviews of the manuscript: a tag-aware *prevention* baseline, Settle as
designed (abstention on content-only writes; a sweep that always waits), delayed transport redelivery,
look-alikes from another account, plan-free intent identity for language-model agents, and one frontier model.
Every hypothesis below is evaluated by `analysis/followup.py` exactly as written; results are reported whether or
not they confirm.

## Conditions (code/actrec/layers.py)
- **Sp** tag wait-then-count: durable journal + tag; after an ambiguous outcome wait until Δ (+λ) after the last
  attempt, count by tag, re-issue only if none (Proposition 3 applied to every write); no final sweep, no
  compensation.
- **S2** Settle as designed: as S, plus (i) a content-only write that was ever in doubt is never confirmed by a
  content match and is always reported uncertain, (ii) the final sweep always waits until Δ (+λ) after the last
  attempt of any operation, so a delayed redelivery is caught.
- **S-np** Settle for language-model agents with plan-free intent identity: intent = tool + normalized intent
  fields of the call (no mapping to the task's plan steps).
- **C5a / Gwa** verify-before-retry / guard+wait whose content checks accept only records authored by the agent's
  own account.

## Grids (code/actrec/runner.py presets; scripted grids cost nothing)
- followup_a: every world of the frozen scripted test grid × {Sp, S2} (2,376 episodes). Paired with the frozen
  records of S (same worlds, same seeds; the scripted driver is deterministic).
- followup_b: new mode redelivery_late (the transport delivers an identical copy 8 s after the acknowledged
  request) on every non-batch write of the test split × {C0, Gw, S, Sp, S2, O} (504).
- followup_c: new read variant lookalike_other (the look-alike is created by a second, ordinary Gitea account at
  the moment of the fault) on every Gitea write, modes lost_ack, not_exec_err, not_exec_to, late
  × {C5, C5a, Gw, Gwa, S, Sp, S2} (588).
- followup_llm_np: test_llm worlds × S-np for gpt-5.6-luna (2 repeats), gpt-4.1-mini, gpt-5.4-nano (536).
- followup_llm_frontier: test_llm worlds × {C0, S-np} for gpt-5.6-sol, 1 repeat (268), run only if a price check
  of the first 12 episodes projects the total new spending to stay within the cap below.

## Spending
Hard cap: total new model spending in this follow-up ≤ US$ 10.00, enforced by code/tools/followup.py (ledger
ceiling = ledger total at start + 9.90; the guard stops any grid that crosses it, the client refuses calls that
would cross MAX_SPEND_USD). If the frontier grid does not fit, it is not run and F7 is reported as not run.

## Hypotheses and criteria
Populations: "H1 population" = ambiguous modes, focal class A, targeted-reversible, all read variants (as H1).
Rates are per episode; intervals are 95% cluster bootstraps over template × instance (B = 10,000, seed 20261001)
unless stated; paired tests are exact McNemar with Holm within a hypothesis.

- **F1 prevention vs convergence (Sp vs S, H1 population).**
  (a) Excluding redelivery and late_tail worlds, Sp and S are equivalent within ±5 points (90% paired interval
  inside [−5, +5]).
  (b) In redelivery worlds Sp is inconsistent in ≥ 90% and S in ≤ 5%.
  (c) In late_tail worlds Sp is inconsistent at least as often as S (paired difference Sp − S ≥ 0).
  (d) Descriptive: mean agent time per ambiguous episode, Sp − S, with interval.
- **F2 Settle as designed on content-only writes (S2, followup_a).** In ambiguous content-only (class C) worlds,
  S2 overclaims in 0 episodes; its inconsistency is reported next to S's.
- **F3 S2 elsewhere (followup_a).** In the H1 population, S2 and S are equivalent within ±5 points (90%).
  Descriptive: S2's added time in fault-free worlds relative to S.
- **F4 delayed redelivery (followup_b).** (a) Reversible attributable focal writes (class A targeted, class U
  exclusive): S2 ≤ 5% inconsistent; S, Sp, Gw and C0 each ≥ 50%. (b) Irreversible writes (mail): every condition
  is inconsistent in ≥ 90% (no client policy can prevent a transport duplicate); S2 overclaims in ≤ 5%, S in ≥ 50%.
  (c) Keyed writes: every condition ≤ 5%.
- **F5 look-alikes from another account (followup_c, all worlds).** (a) C5 and Gw (no author filter) are each
  inconsistent in ≥ 25%. (b) Gwa is no more than 5 points worse than S (one-sided 95% upper bound of Gwa − S ≤ 5
  points). (c) Descriptive: C5a by mode (it does not wait, so late commits should still duplicate).
- **F6 plan-free intent identity (S-np vs the frozen S records, per model, hard worlds).** Non-inferiority: the
  one-sided 95% upper bound of S-np − S is ≤ 10 points for each model. Reported also for easy worlds and with the
  causes of every S-np failure.
- **F7 frontier model (gpt-5.6-sol; only if run).** In hard worlds S-np is below C0 (95% upper bound < 0 and
  McNemar p < 0.05). Descriptive: the RQ1 coding of C0 (first action after the first ambiguous write).

## Not changed
The main study's hypotheses H1–H6, their populations and their verdicts. Follow-up results are reported in a
separate section of the paper, labelled as a follow-up study with its own freeze.
