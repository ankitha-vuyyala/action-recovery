# Protocol for the test-split runs

Status: **draft for freeze** (1 Oct 2026). Together with `06_analysis_plan.md`, this file becomes binding when `python code/run.py freeze` writes `FREEZE.json`.

The freeze records SHA-256 hashes of:

- `code/actrec/`, `code/tools/`, `code/run.py`;
- `analysis/`;
- `docker/`;
- `docs/04_study_design.md`, `docs/05_theory.md`, this file and `docs/06_analysis_plan.md`;
- `requirements.txt`.

The test presets refuse to start if any of these files changed, or if a preset is narrowed on the command line.

## 1. Order of work

| # | Step | Data | Gate |
|---|---|---|---|
| 1 | LLM pilot | dev split | Every episode finishes; measured cost per episode per model; §7 filled in |
| 1b | LLM check of the hard worlds (`--preset llm_hardcheck`, gpt-5.6-luna) | dev split | Every episode finishes, including crash + resume and long-tail delays |
| 2 | Full environment validation on the final code (`run.py validate`, 10 trials per cell) | — | Every fault mode realises its hidden outcome. Known exception, kept as measured: TigerBeetle not_exec_err / not_exec_to, where the client retries internally and dedupes by session (validation run 20261001-164459: 0.0 and 0.3 as intended); these cells are excluded from equivalence claims |
| 3 | Harness check of the test-only templates (`--preset harness_check`) | T3, T6, T8 on instance **900**, which is not a test instance | 0 errors, fault-free table all 0. Nothing else in this run is read |
| 4 | If step 2 or 3 finds a bug: fix it, log it in `changes_stage3.md`, repeat steps 2–3 | — | — |
| 5 | Freeze: `python code/run.py freeze`, then `--check` | — | Prints OK; `FREEZE.json` committed |
| 6 | Scripted test grid: `grid --name test_scripted --preset test_scripted` | test | Resume until every episode is finished or has failed 3 attempts |
| 7 | LLM test grids: `test_llm` per model in §7, under `code/tools/guarded_grids.py` | test | Spend guard as in §7 |
| 8 | Analysis: `analysis/confirmatory.py`, `analysis/llm_behaviour.py`, `analysis/summarize_grid.py` | test | — |

Nothing measured in steps 6–7 is used to change code, prompts, tasks, parameters or analysis.

## 2. Fixed parameters

These were set on the dev split.

**Tool behaviour**

- Tool deadline: 4 s. An abandoned request keeps its socket open for up to 900 s.
- Late-commit delay: 12 s.
- Late-tail delay: log-uniform from 5 to 120 s, seeded per world.

**Settle and the other recovery methods**

- Settle's assumed in-flight bound Δ: 20 s. Its poll interval and lag allowances are as in `layers.py`.
- C2, C3 and C8 retry 3 times. Temporal (C4) uses 3 activity attempts.
- The scripted driver re-issues once.
- Quiescence before grading: 3 s.

**LLM agents**

- System text, cue, nudge and reflection prompt as in `driver_llm.py`.
- At most 30 turns and 40 tool calls per episode.
- `max_output_tokens` 6000.
- OpenAI Responses endpoint with `store=false`, at each model's **default** reasoning setting.

## 3. Execution rules

- Every episode attempt gets a fresh service namespace (repository, mail address, run id, stream keys, object prefix). Earlier attempts never leak into later ones.
- The grader reads the services directly, with separate credentials, after quiescence. Agents and recovery layers never import it.
- Workers: 3 by default. Up to 6 may be used if the machine stays responsive; this setting has no effect on outcomes, because every episode has its own namespace and per-worker fault proxies.
- Records are append-only. Unfinished records are moved to `episodes_errored.jsonl`, never deleted.
- Model responses are cached by request hash. A re-run of a finished request is free and deterministic, and the cache is released so that every decision can be replayed without an API key.

## 4. What may be looked at, and when

- **During steps 6–7:** progress counts and error records only. Looking at error records is needed to keep the run going.
- **Errors in the test run:**
  - An infrastructure error (Docker, network or disk) is fixed outside the frozen files, and the episode is re-run.
  - A bug in a frozen file stops the run. The fix is a dated amendment (§6), and every affected episode is re-run under the new freeze.
- **Step 3:** only the error list and the fault-free sanity table are read.

## 5. Records kept

The following are kept for every grid:

- `episodes.jsonl`, `episodes_errored.jsonl` and `episodes_invalidated.jsonl`;
- `grid.json`, which includes the preset, driver, repeats and freeze digest;
- `freeze_log.jsonl`, with one line per start or resume;
- per-episode state folders (journal, dispatch log, actor log, conversation, child logs);
- the LLM response cache and `runs/cost_ledger.jsonl`.

## 6. Amendments

A change to a frozen file after the freeze needs all of the following:

- a dated entry here: what changed, why, and which episodes are affected;
- renaming the old freeze to `FREEZE_<date>.json` (it is never overwritten);
- a new freeze;
- a re-run of every affected test episode under the new freeze.

All amendments are listed in the paper.

## 7. LLM main run

**Preset `test_llm`.** 670 episodes per repeat:
- the first two write steps of each of the 8 templates, on instance 100;
- modes: none, lost_ack, not_exec_err, late, late_tail, crash_after;
- read variants: exact, look-alike, lagged, shared aggregate, wherever they apply;
- conditions: C0, C5, C6, C7, S.

**Measured cost (dev-split pilot, 2026-10-01, Responses API, default reasoning).** In US$ per episode:

| Model | US$ per episode | Episodes measured |
|---|---|---|
| `gpt-5.6-luna` | 0.00106 | 60 |
| `gpt-5.4-mini` | 0.00434 | 8 |
| `gpt-5.4-nano` | 0.00114 | 8 |
| `gpt-4.1-mini` | 0.00216 | 8 |

The pilot spent $0.1247 in total. Budget estimates use these figures × 1.4, to allow for the longer test-only templates and the extra reads in look-alike worlds.

**Models and repeats** (chosen by the user on 2026-10-01). Runs go in this order, so that a stop by the spend guard can only cut the last one:

| # | Grid | Model | Repeat | Estimate |
|---|---|---|---|---|
| 1 | `test_llm_luna` | `gpt-5.6-luna` | repeat 0 | $0.99 |
| 2 | `test_llm_41mini` | `gpt-4.1-mini` | repeat 0 | $2.03 |
| 3 | `test_llm_nano` | `gpt-5.4-nano` | repeat 0 | $1.07 |
| 4 | `test_llm_luna` | `gpt-5.6-luna` | repeat 1 (same grid, `--repeats 2`) | $0.99 |

The estimated total is about $5.10. Each model runs at its default reasoning setting: medium for `gpt-5.6-luna`, none for `gpt-5.4-nano`, and `gpt-4.1-mini` is not a reasoning model.

**Spend guard.**
- `MAX_SPEND_USD` = 6 for the whole project, including the pilot.
- `guarded_grids.py --max-usd` = 5.75, which keeps $0.25 in reserve.
- If the guard stops a grid, finished episodes are kept. Unfinished worlds are reported as not run; they are not imputed.
- H6 is then evaluated on complete pairs only, and the shortfall is reported.

## Amendment log

**Amendment 1 (2026-10-01, during step 7).**
- *What happened.* The spend guard stopped `test_llm_luna` after about 620 of 670 episodes with a `model error` stop. The cause was not the provider. It was a race on the cost-ledger lock file on Windows: `os.open(..., O_CREAT | O_EXCL)` raised `PermissionError` while another worker process was deleting the lock, and `_Lock` only treated `FileExistsError` as "busy".
- *Change.* In `code/actrec/llm_client.py`, `_Lock.__enter__` now also treats `PermissionError` as "busy, retry". Nothing else changed.
- *Affected episodes.* The lock only guards the spending ledger. It does not touch the services, the agent's observations, the recovery layers or the grader, so it cannot change the outcome of a finished episode. The only affected records are the unfinished episodes stopped by the race. They were archived to `episodes_errored.jsonl` and run again under the new freeze, as §3 prescribes for unfinished episodes.
- *Freeze.* The first freeze (digest `51df7cbd…5f56`) is kept as `FREEZE_2026-10-01_v1.json`, and the new freeze is `FREEZE.json`. `freeze_log.jsonl` in each grid records which freeze each start or resume ran under.

**Amendment 2 (2026-10-03, after step 10; found while auditing the records before writing).**
- *Finding 1: ledger keys collided across episodes.* In the language-model runs, models often chose their own transfer key, derived from the task text: for example `13050000…` for refund RF-1305, or `…4344` for invoice INV-4344. TigerBeetle transfer ids are global, not per episode, so the same key chosen in an earlier episode of the same task made the ledger answer `EXISTS_WITH_DIFFERENT_DEBIT_ACCOUNT_ID`. The tool layer passed that answer on to the agent as success, so the transfer was missing.
  - It affected 207 of 216 non-Settle T2/T8 episodes of `gpt-5.6-luna` and 105 of 108 of `gpt-5.4-nano`. It did not affect `gpt-4.1-mini`, which never supplies a key.
  - The scripted grid is not affected: its keys are fresh UUIDs or workflow ids per run. Settle is not affected either, because it uses its own operation ids.
  - This is an artifact of replaying the same task across conditions against one shared ledger, and it biases the language-model comparison in Settle's favour.
- *Finding 2: some episodes crashed without a report.* Twelve episodes ended with an exception in the agent process and no report (`claimed = no_report`, exit code 1).
  - Nine language-model episodes failed on a Windows `PermissionError` when replacing the conversation checkpoint.
  - Three scripted episodes failed on a transient HTTP error outside the tool layer.
  - The rule in §3 did not classify them as unfinished, so they stayed in the analysis as graded.
- *Changes.*
  - `services/ledger_tb.py` and `contracts.py`: transfer keys are scoped to the episode's run namespace (`Ledger.id_for`). A refusal by the ledger is now returned to the caller as the service's error instead of as success.
  - `driver_llm.py`: the checkpoint replace retries on a Windows `PermissionError`.
  - `runner.py`, `analysis/confirmatory.py` and `analysis/summarize_grid.py`: an agent process that crashed and left no report is unfinished. It is archived and re-run.
  - Tests were added; 59 pass.
- *Re-run.* Every T2 and T8 episode of all three language-model grids is re-run under the new freeze, for every condition including Settle, so that pairs stay within one code version. All crashed episodes are also re-run. The first analysis is kept as `results_v2/`.
- *Sensitivity, computed before the re-run.* Excluding the 12 crashed episodes changed no verdict. The re-run's effect on H6 is reported in the paper next to the pre-amendment numbers.
- *Freeze.* The previous freeze is kept as `FREEZE_2026-10-03_v2.json`, and the new freeze is `FREEZE.json`.


## Follow-up study (2026-10-04; separate freeze)

The main study above is complete; its records, analysis and verdicts are final and are not changed. A follow-up
study answers open points of two independent reviews of the manuscript. Its design, conditions, grids,
hypotheses (F1–F7) and spending cap are in `docs/07_followup_plan.md`, written before any follow-up episode ran.
- *Code added, not changed.* New conditions (Sp, S2, S-np, C5a, Gwa), a new fault mode (`redelivery_late`), a new
  read variant (`lookalike_other`, with a second ordinary Gitea user created by `stack up`), new presets
  (`followup_*`), `code/tools/followup.py`, `analysis/followup.py` and offline tests. Every pre-existing condition,
  mode, variant and preset behaves exactly as before; the only edits to existing code paths are optional
  arguments that default to the old behaviour (`by_content(..., own_only=False)`, Gitea `own=None`).
- *Freeze.* `code/tools/followup.py` archives the main study's final freeze as `FREEZE_2026-10-03_amend2.json`
  (digest `dd8b4adb…`), writes a new `FREEZE.json` over the follow-up tree (now including
  `docs/07_followup_plan.md`), and refuses to run any `followup_*` preset if the tree changes afterwards. The
  freeze time and digest are logged in `runs/FOLLOWUP_STATUS.txt` before the first follow-up episode.
- *Spending.* All follow-up model calls together are capped at US$ 9.90 on top of the ledger total at the start
  (`runs/followup_budget.json`).
