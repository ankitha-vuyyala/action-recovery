# Pre-registration and deviations {#sec:prereg}

**Freeze.** The protocol was frozen on {{freeze.at}} UTC. The freeze consisted of SHA-256 hashes of {{freeze.files|int}} files, with digest prefix `{{freeze.digest_v1}}`. The frozen files were:

- all harness, recovery-layer, driver, task, grader and analysis code;
- the container definitions;
- the study design;
- the theory;
- the analysis plan;
- this protocol.

The test presets check the freeze before every start or resume, and each start is logged with the digest.

**Order of work.**

1. Environment validation and a scripted development grid on the development split.
2. A paid pilot of 84 recorded episodes on the development split: four models (gpt-5.6-luna, gpt-5.4-mini, gpt-5.4-nano and gpt-4.1-mini), five conditions, easy worlds only. gpt-5.4-mini was not carried into the main study: in the pilot it cost about four times as much per episode as gpt-5.6-luna or gpt-5.4-nano (US$ 0.0043 against 0.0011) and, like gpt-5.4-nano and gpt-4.1-mini, re-issued writes without checking, so it would have added cost without adding a distinct behaviour.
3. A check of the hard worlds with one model.
4. Full re-validation on the final code.
5. A harness check of the three test-only templates on a non-test instance; only errors and fault-free outcomes were inspected.
6. The freeze.
7. The test runs.
8. The analysis.

**Hypotheses** (exact criteria; all evaluated by `analysis/confirmatory.py`):

- **H1.** In class-A, targeted-reversible, ambiguous worlds, Settle's inconsistency is at most 5%. Settle is also at least 15 points below the best non-oracle baseline, with a 95% cluster-bootstrap upper bound below 0 and a Holm-adjusted exact McNemar $p < 0.05$. The best baseline is chosen on test data, which is conservative.
- **H2.** Under look-alikes, each content-based method (C5, C6, S−t) is inconsistent in at least 10% of ambiguous worlds, and Settle's rate is at most half of each, with a CI upper bound below 0 and Holm $p < 0.05$.
- **H3.** On class-K writes, Settle is equivalent to the workflow engine with durable keys (C4): the 90% CI of the difference lies within ±5 points.
- **H4.**
  (a) With a shared aggregate, every non-oracle condition is inconsistent in at least 25% of ambiguous worlds.
  (b) Settle overclaims in at most 5% of shared-aggregate or irreversible ambiguous worlds.
  (c) In irreversible worlds, every condition shows duplicates or missing effects.
- **H5.**
  - Settle adds at most 2 s in fault-free worlds (95% upper bound) and at most $\Delta$ + 10 s on average in ambiguous worlds, both relative to the guard.
  - Per model, Settle's US$ per episode relative to the guard is at most 1.25 (95% upper bound).
- **H6.** For every model, in hard worlds (late_tail, crash_after, look-alike or lagged reads), Settle is below each language-model baseline, with a CI upper bound below 0 and Holm $p < 0.05$.
- **Ablations.** Each ablation is at least 10 points worse than Settle in the cell where its component is needed (lower 95% bound above 0).

**Deviations from the original study design.** Each of the following was decided on development data before the freeze, and is logged with its evidence in the released change log.

1. *H1, statistical model.* The mixed-effects logistic model was replaced by cluster bootstrap plus exact McNemar, because of quasi-separation at near-zero rates.
2. *H3, comparator and margin.* The comparator changed from in-memory keys (C3) to durable keys (C4), and the margin widened from ±3 to ±5 points. The reason is that in-memory keys fail in crash worlds exactly as Proposition 1 predicts, and that contrast is reported separately.
3. *Hard worlds in the language-model grid.* The pilot showed that a reasoning model checks state before re-issuing. The language-model grid therefore gained the hard worlds, and H6 was restricted to them.
4. *Settle guards the agent's own deletions.* This was added after a development episode in which the agent deleted another user's look-alike issue.
5. *The OpenAI endpoint changed* from chat completions to the Responses API. Chat completions refused function tools for gpt-5.6-luna, the main model of the language-model study (the only one that reasons by default, and the one run with two repeats), at its default reasoning setting, before any charge.

**Amendments after the freeze.** Both amendments are recorded in the protocol's amendment log with their evidence. Each was followed by a re-freeze, and every freeze is kept.

- **Amendment 1 (during the runs; re-freeze {{freeze.at_v2}} UTC, digest prefix `{{freeze.digest_v2}}`).**
  - *Cause.* The spend guard stopped the first model run on a Windows race in the lock file of the cost ledger.
  - *Fix.* The lock treats `PermissionError` like `FileExistsError`.
  - *Impact.* The lock guards only the spending ledger, so no outcome could change. The stopped episode was re-run.
- **Amendment 2 (after the runs; re-freeze {{freeze.amended_at}} UTC, digest prefix `{{freeze.digest}}`).**
  - *Cause.* The audit before writing found that models choosing their own transfer keys collided with the same key chosen in other episodes that replay the same task. TigerBeetle ids are global, and the tool layer reported the ledger's refusal as success.
  - *Fix.* Keys are now scoped to the episode, and refusals are surfaced as errors.
  - *Re-run.* Every T2 and T8 language-model episode, in all conditions, was re-run (540 episodes). The 12 episodes whose agent process had crashed without a report (9 language-model, 3 scripted) were also re-run; one of them was already among the T2/T8 episodes. A crashed agent process now counts as unfinished.
  - *Scope.* The scripted grid is unaffected by the key collision. Its keys are unique per run, and a status scan of its ledger calls found no `EXISTS_WITH_DIFFERENT_*` refusal; the only repeat answers were the expected `EXISTS` for re-issued keys. Its only re-runs were the three crashed episodes.
  - *Reporting.* @sec:llmresults gives the numbers before and after. The verdicts of H1–H4 and H6 did not change. H5's cost criterion for `gpt-5.4-nano` moved from inconclusive to confirmed.

**Exploratory analyses added after the runs.** Two analyses were added while writing, after all test runs and the confirmatory analysis had finished: the API census (@sec:census) and the horizon replay (@sec:horizon). Neither enters any hypothesis, neither changes a confirmatory number, and both are labelled as exploratory where they appear. The census was coded from public documentation and does not use the test data. The replay reads the recorded test episodes, but computes no rate that a hypothesis depends on. Their code lives outside the frozen source tree, so the freeze still verifies.

**Follow-up study.** The follow-up study (@sec:followup) has its own analysis plan (`docs/07_followup_plan.md`) and freeze (digest prefix `87ddadb5`), written after the main results had been reviewed and before any follow-up episode ran; the main study's freeze was archived first. Its spending was capped at US$ 9.90 and came to {{fu.usd.new|usd}}. A free smoke check on the development instance confirmed that the new fault mode and the new read variant realised their intended hidden outcomes before the grids ran. One correction was made after the runs, to the analysis script only: in two F4 criteria the frozen code read a missing rate as `rate or 1`, which also turns a measured rate of exactly 0 into 1, so the criteria "S2 ≤ 5%" and "S2 overclaims ≤ 5%" failed although S2's measured rates were 0%. With the correction both criteria are confirmed; every other result of the script is unchanged. The frozen script is released unchanged at `analysis/followup.py`, so the freeze check still passes, and the corrected copy, which also treats a missing rate as failing in every criterion, is released at `paper/followup/followup_corrected.py` with both outputs. Under the frozen script, F4(a) and F4(b) read "not confirmed".

**Exclusions.** Unfinished episodes (runner errors, grading errors, model errors or budget stops) are archived and re-run. No scripted or language-model record remained unfinished, so none is excluded.
