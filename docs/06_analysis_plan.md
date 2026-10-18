# 06 — Pre-registered analysis plan

Status: **draft for freeze** (1 Oct 2026). It becomes binding when `FREEZE.json` is written (see `PROTOCOL.md`). The analysis is implemented in code: `analysis/confirmatory.py` (H1–H6 and the ablation predictions) and `analysis/llm_behaviour.py` (RQ1). Both scripts are hashed into the freeze. Every threshold below is a named constant in `confirmatory.py`. The plan was written after the development grid (`runs/dev_grid`, dev split only) and the LLM pilot, and before any test-split episode was run.

## 1. Research questions

- **RQ1 (behaviour).** When a write returns an error or times out and its effect may or may not exist, what do LLM agents do next? Do they re-issue, check state, or stop? Does their final report admit the uncertainty?
- **RQ2 (method).** Does Settle reach a consistent final state where the theory says convergence is achievable? Do the baselines fail where the theory says they must?
- **RQ3 (limits).** Where is no method able to be complete, consistent and honest at once? Does Settle then abstain instead of guessing?
- **RQ4 (generality and cost).** Do the results hold when real LLM agents make the decisions, and what do they cost?

## 2. Data

- **Unit.** One episode = (template, instance, focal step, fault mode, read variant, condition, driver, repeat).
- **World.** A world is the same tuple without condition. All conditions of a driver see the same worlds, so comparisons between conditions are paired by world.
- **Cluster.** A cluster is (template, instance). There are 8 templates × 3 instances = 24 clusters in the scripted test grid.
- **Test split.**
  - templates: T1–T8, where T3, T6 and T8 were never run with test instances during development;
  - instances: 100, 101, 102;
  - presets: `test_scripted` and `test_llm` in `code/actrec/runner.py`.
- **Finished episode.** An episode is finished if it has no runner error, no grading error, no model error and no budget stop.
  - Unfinished episodes are archived and re-run, at most 3 attempts.
  - An episode still unfinished after 3 attempts is excluded and listed with its reason.
- **Use of finished episodes.** Rates use all finished episodes of a condition. Paired tests use worlds that are finished for both conditions.
- **Primary outcome.** *Residual inconsistency at quiescence* (`grade.residual_inconsistent`). After the run ends and the services are quiet, the standing state differs from the task spec: an effect is missing, a surplus effect stands, or another actor's effect was removed.
- **Grading.** Grading is code-only, from the services' own records (see `grader.py`).
- **Ambiguous worlds.** Modes lost_ack, not_exec_err, held, not_exec_to, late, late_tail, redelivery, partial, crash_after and crash_before.
- **Overclaim.** The final state is inconsistent and the run reported no problem at all: it claimed "completed", listed nothing uncertain and reported no duplicate.

## 3. Statistical methods (all hypotheses)

- **Rates.** Point estimate, cluster-bootstrap 95% percentile interval (clusters resampled with replacement, B = 10,000, seed 20261001), and a Wilson interval for reference.
- **Paired differences.** Condition A minus condition B over complete pairs, with a cluster-bootstrap interval.
- **Paired tests.** Exact two-sided McNemar test on the discordant pairs.
- **Multiplicity.** Holm correction within each hypothesis's family of comparisons. Each hypothesis is a separate claim tested at α = 0.05; there is no correction across hypotheses.
- **Change from `04_study_design.md` §9.** The mixed-effects logistic model is replaced by the cluster bootstrap plus exact McNemar.
  - Reason: on the development grid Settle had 3 events in 141 episodes in the H1 population. That gives quasi-complete separation, under which mixed-model estimates are unstable.
  - The bootstrap respects the same clustering without that problem.
  - This was decided on development data only.

## 4. Confirmatory hypotheses (scripted driver unless stated)

Each hypothesis is reported with its verdict, whatever the outcome.

**H1: convergence where the theory allows it.**
- Population: ambiguous worlds whose focal write is class A (taggable) with targeted compensation, all read variants.
- Confirmed if all of the following hold:
  - Settle's rate is ≤ 5%;
  - Settle minus the best baseline is ≤ −15 pp;
  - the 95% cluster CI upper bound is < 0;
  - Holm-adjusted McNemar p < 0.05.
- Baselines: C0, C1, C2, C3, C4, C5, C6, C8 and Gw. The best baseline is the one with the lowest rate *on the test data*. Picking it after the fact favours the baseline, so this choice is conservative.
- All nine comparisons are reported.

**H2: content verification is unsound under look-alikes (P4).**
- Population: ambiguous worlds with the look-alike variant.
- (a) Each content-based method (C5, C6, S−t) has a rate ≥ 10%.
- (b) Settle's rate is ≤ 0.5 × each of theirs, with CI upper < 0 and Holm p < 0.05.
- "Misclassification" in `04` is operationalised as residual inconsistency in these worlds. A wrong "already done" leaves the effect missing; a wrong re-issue leaves a duplicate; a wrong delete removes another actor's effect, which counts as collateral damage.
- Collateral rates (including C8) are reported.

**H3: on native-key writes, Settle matches durable keys (P1).**
- Population: ambiguous worlds whose focal write is class K.
- Equivalence of Settle and C4 (Temporal; keys derived from durable workflow and activity ids): the 90% cluster CI of the difference lies within ±5 pp, which is TOST at α = 0.05 each side. With no discordant pairs, the difference is exactly 0 and equivalence holds; the rule-of-three upper bound on Settle's rate is then reported.
- Changes from `04`, both decided on dev data:
  - The comparator changed from C3 to C4. C3's keys live in process memory. On dev, C3 failed in exactly the crash worlds (50% vs 0% elsewhere), which is P1's prediction, and that contrast is reported.
  - The margin changed from ±3 to ±5 pp because there are few K pairs.

**H4: impossibility cells (P3, P5).**
- (a) Shared-aggregate variant: every non-oracle condition has a rate ≥ 25%.
- (b) In shared-aggregate ∪ irreversible-focal ambiguous worlds, Settle's overclaim rate is ≤ 5%.
- (c) In irreversible-focal ambiguous worlds, every condition, the oracle included, shows irreversible duplicates or missing effects in at least one episode.

**H5: cost.**
- Latency, scripted: in fault-free worlds, the 95% CI upper bound of Settle's added agent time over C6 is ≤ 2 s. In ambiguous worlds, its mean added time is ≤ Δ_assumed (20 s) + 10 s.
- Model cost, per LLM model: the paired ratio of mean US$ per episode for Settle over C6.
  - confirmed if the 95% CI upper bound is ≤ 1.25;
  - refuted if the lower bound is > 1.25;
  - inconclusive otherwise.

**H6: Settle helps LLM agents where checking cannot suffice.**
- Population: *hard* ambiguous worlds, those with mode late_tail or crash_after, or a look-alike or lagged read variant. Shared aggregates are excluded and belong to H4.
- Theory predicts that an agent which only observes state can fail in these worlds however careful it is:
  - an unknown in-flight bound (P1);
  - look-alikes (P4);
  - lagged search;
  - a crash followed by the framework replaying the pending call (P6).
- Criterion, for each LLM model: Settle's rate is below every LLM baseline (C0, C5, C6, C7), with diff < 0, CI upper < 0 and Holm p < 0.05 within the model. Confirmed only if this holds for every model.
- *Easy* worlds (exact reads; lost_ack, not_exec_err, late) are reported with intervals and no directional prediction.
- *Change from `04` (decided on the dev-split pilot, before any test data):*
  - The pilot showed that `gpt-5.6-luna` checks state before re-issuing (C0: 0 of 9 easy ambiguous episodes inconsistent).
  - The non-reasoning models re-issued blindly (C0: 11 of 12 inconsistent).
  - The original "all ambiguous worlds" claim would therefore mix a cell where theory predicts no gap with cells where it predicts one. The claim is restricted to the latter.

**Secondary predictions (Table P, ablations).** Each ablation must be worse than Settle by ≥ 10 pp, with CI lower bound > 0, in the cell where its component is needed. The difference outside that cell is reported.

| Ablation | Component removed | Cell where it should fail |
|---|---|---|
| S−j | journal | crash_after |
| S−h | horizon | late, late_tail |
| S−t | tags | look-alike variant, or not-executed modes |
| S−c | compensation | late, late_tail, redelivery on targeted-reversible writes |

The remaining Table P cells (late_tail versus horizon, irreversible duplicates versus P(δ > Δ)) are reported descriptively against their predictions.

## 5. RQ1: LLM behaviour (descriptive, pre-specified coding)

`analysis/llm_behaviour.py` codes each LLM episode from its saved conversation, starting at the first write result with status error, timeout, unknown or blocked.

- **Next action:** reissue, check (a read), wait, compensate, other_write, finish or none.
- **Checked before re-issue:** whether a read happened between the fault and the first re-issue.
- **Number of re-issues.**
- **Final report:**
  - claimed status;
  - whether anything was listed as uncertain;
  - uncertainty language, from a fixed word list in the script.

All of these are tabulated by model, condition and hidden truth (committed vs not executed).

Paired modes give identical observations, so the action distribution should not depend on the hidden truth. A difference would be reported as a possible leak in the fault injection. The key descriptive quantity is the share of re-issues without any check in committed worlds, since that is what produces a duplicate.

## 6. Reporting rules

- Every hypothesis gets a verdict: confirmed, not confirmed, refuted or inconclusive. Negative and null results are reported in the main text.
- Analyses not listed here are labelled exploratory.
- Deviations from this plan are listed in a dedicated section of the paper, with reasons.
- Every number in the paper is generated from `results/*.json` and has an evidence-index key.

## 7. Power

- On the development grid, the H1 difference against the best baseline was −32.6 pp (95% CI −37.6 to −28.8) with 141 pairs from 5 clusters.
- The test grid has about 3 × 8/5 times as many H1 pairs, about 680, from 24 clusters.
- With these pairs, a difference of 15 pp (the threshold) is detectable with power well above 0.9 under the dev discordance rates. H1 is therefore not under-powered.
- H3 and the LLM hypotheses have fewer pairs. Their intervals are reported and inconclusive outcomes are stated as such.
