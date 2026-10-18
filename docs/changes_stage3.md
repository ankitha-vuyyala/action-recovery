# Stage 3 — changes made during environment validation

| Date | File | Change | Reason |
|---|---|---|---|
| 2026-09-30 | — | No code changes. | The quick run (`validate --trials 3`, run `20260930-202617`, 153 trials) finished without any script error, so there was no bug to fix. Fault definitions and expected outcomes are unchanged. |

Cells whose realized outcome differed from the intended one are measurements, not script errors. They were left as they are and are reported in the validation summary:

- `tb_transfer | not_exec_err` and `tb_transfer | not_exec_to`: the transfer sometimes executes although 0 executions were intended. This is consistent with the TigerBeetle client's internal retry and session dedup, as documented in `code/actrec/services/ledger_tb.py`.
- `s3_put | lost_ack`: 0 executions although 1 was intended, and the caller sees an error. The suspected cause, not verified, is that the PUT waits for a server reply (`Expect: 100-continue`) before sending the body, so a downstream cut stops the request before the body is sent.

## Changes after the full validation run `20260930-204601` (design fixes, not bug fixes)

| Date | File | Change | Reason (evidence) |
|---|---|---|---|
| 2026-09-30 | `code/actrec/services/base.py` | Tool layer reports every transport failure before a complete reply as `ToolTransportError`; the raw library exception is kept in `raw_exc_type`/`raw_exc_msg` and summarized separately. | Mail `lost_ack` vs `not_exec_err` were distinguishable (TVD 1.0): the `limit_data` toxic leaked one byte of the SMTP `250` reply, which smtplib parsed as `SMTPDataError(2, b'')`, revealing success. All other services were already equivalent. |
| 2026-09-30 | `code/actrec/services/objstore.py` | Removed botocore's `Expect: 100-continue` on PutObject (registered on `before-call.s3`; verified offline that the header is gone and `If-None-Match` stays). | Quick run: S3 `lost_ack` gave 0 executions because the reply-path cut hit the `100 Continue` before the body was sent. |
| 2026-09-30 | `code/actrec/validate_env.py`, `docker/compose.yml` | One S3 bucket (`actrec`) for the whole stack with per-run key prefixes; SeaweedFS `-volume.max=100`, `-master.volumeSizeLimitMB=64`. | Full run: every S3 write returned `InternalError`, consistent with volume exhaustion from one new bucket (collection) per run under `-volume.max=8`. |
| 2026-09-30 | — | TigerBeetle cells kept as measured. | Its client retries internally and deduplicates by session: `lost_ack` shows a timeout, and both "not executed" modes are turned into a later single execution once the path clears. This is the native-key contract working, so TigerBeetle provides no 'absent' worlds; it is excluded from observation-equivalence claims. |

## Bug fixes during the smoke grid `runs/dev_smoke` (2026-09-30)

First pass: 156 episodes, 32 errors. All of them were `grade_error` in template T2 (`TypeError: AccountFilter.__init__() missing 6 required positional arguments …`). No fault definitions, conditions, metrics or expected outcomes were changed.

| Date | File | Change | Reason (evidence) |
|---|---|---|---|
| 2026-09-30 | `code/actrec/services/ledger_tb.py` (`Ledger.all_transfers`) | `tb.AccountFilter(...)` now passes every field explicitly. `user_data_128/64/32`, `code`, `timestamp_min`, `timestamp_max` are set to 0, which means "no filter"; `account_id`, `limit` and `flags` are unchanged. | The tigerbeetle-python 0.17.9 dataclass has no defaults, so every call raised `TypeError`. This broke the grader for all transfer steps (32 T2 episodes). It also broke the agent-side content read `Toolbox.by_content("transfer_create")` → `Ledger.by_memo`, so the agent behaviour in those episodes was affected too, and they must be re-run rather than only re-graded. Checked against the live ledger: `all_transfers` and `by_memo` return normally. |
| 2026-09-30 | `code/actrec/runner.py` (`run_grid`, resume) | On resume, records with `error` or `grade.grade_error` no longer count as finished. They are moved from `episodes.jsonl` to `episodes_errored.jsonl` (kept for the audit trail), and those episodes are run again. | Resume used to skip every episode id that had any record, including errored ones, so a re-run could never repair a failed episode. Moving the records keeps exactly one record per episode in `episodes.jsonl`, so `analysis/summarize_grid.py` does not double-count. |

## Smoke grid `dev_smoke`, second finding (design bug in the runner, found by checking the results)

| Date | File | Change | Reason (evidence) |
|---|---|---|---|
| 2026-10-01 | `code/actrec/runner.py`, `code/actrec/temporal_wf.py` | Every episode attempt gets a fresh service namespace (`run = <episode id[:8]>-<random>`): new Gitea repo, mail plus-address, row/stream/counter keys, object prefix and Temporal workflow id. The `run` is stored in each record. | After the re-run of the 32 T2 episodes, all 32 T2 records showed the payout row and the finance e-mail executed twice even in fault-free worlds (e.g. C0/none: `log_batch` 2 executions, `notify_finance` 2). The first, errored attempt had already written them into the same namespace, so the re-run's grading counted both. Every Settle failure and the 20% 'fault-free' inconsistency in the first summary came from these 32 records; outside T2 all 124 records matched the predictions. |
| 2026-10-01 | `code/actrec/runner.py` | New option `--invalidate-template <T>`: moves that template's finished records to `episodes_invalidated.jsonl` (with a reason) so they are re-run in fresh namespaces. | To redo the contaminated T2 records without touching the valid ones. |

## LLM driver added while `dev_grid` was running (2026-10-01, after 625 finished episodes)

| Date | File | Change | Effect on the running scripted grid |
|---|---|---|---|
| 2026-10-01 | `code/actrec/llm_client.py`, `agent_tools.py`, `driver_llm.py` (new) | OpenAI chat-completions driver with response cache, cost ledger and hard caps; agent tool schemas; step mapping; checkpoint-and-replay crash semantics. | None (only imported for `--driver llm:*`). |
| 2026-10-01 | `layers.py` | C7 (reflection) added; key-tools use an agent-supplied `transfer_id` when present. | None: scripted arguments never contain `transfer_id`. |
| 2026-10-01 | `episode.py` | Compensation log records the arguments (content) of what was compensated. | Log field only. |
| 2026-10-01 | `grader.py` | Text comparison is case/whitespace/trailing-period insensitive; agent self-deletions attributed to plan steps by logged content. | None for the running grid (the parent process loaded the grader at start; scripted texts are exact). Re-grading is not needed. |
| 2026-10-01 | `tasks.py` | LLM goal texts state exact strings (T3, T5, T6, T7, T8). Plan steps unchanged. | None (scripted driver does not read goals). |
| 2026-10-01 | `services/ledger_tb.py` | `tag_to_id` accepts any agent-supplied id (non-UUID ids are hashed). | None for UUID ids. |
| 2026-10-01 | `runner.py` | `--driver`, `--repeats`, presets `llm_pilot`, `llm_models`; LLM cost fields in records. | None (parent already loaded). |

## After `dev_grid` (2026-10-01): two artifacts found by auditing the results

| Date | File | Change | Reason (evidence) |
|---|---|---|---|
| 2026-10-01 | `code/actrec/grader.py` | An actor comment counts as collateral damage only if it is missing from **all** comments of the agent's issue, and each actor comment is counted once per episode. | All 120 records with collateral > 0 were T7 look-alike worlds with a comment as focal step, spread evenly over all 15 conditions including the oracle (8 per condition). The grader checked the actor's comment against the comments of the *other* comment step (different text) and counted it as deleted. Example `4f1b10cd27d1` (oracle): the actor comment 1061 still exists. These 120 episodes are re-run. |
| 2026-10-01 | `code/actrec/layers.py` (oracle) | When the oracle knows the focal write took (or will take) effect, it waits until its own effect is visible (it knows the in-flight delay and which records are the actor's) and returns its id. | The oracle returned no issue number, so in T7 the following comments had to find the issue by content: before a late commit lands there is none (6 oracle episodes with missing comments), and with look-alikes the actor's issue could be picked. An upper bound must not fail for such a reason. All 242 oracle episodes are re-run. |
| 2026-10-01 | `code/actrec/driver_scripted.py`, `analysis/summarize_grid.py` | A run that reports unrecoverable duplicates no longer claims "completed"; the summary defines overclaim as an inconsistent final state with **no** problem reported (status completed, nothing uncertain, no duplicate report). | Settle detected the duplicated e-mail in redelivery worlds and listed it, but the driver still wrote "completed". The new definition scores reporting, not wording, and needs no re-run. |
| 2026-10-01 | `code/actrec/runner.py` | `--invalidate-where "key=v1|v2;key=v"` to re-run a selected subset. | For the two re-runs above. |

## Pilot stopped on a provider refusal; client moved to the Responses API (2026-10-01)

The first paid pilot episodes (T1, fault-free, C0 and C5, `gpt-5.6-luna`) were refused with HTTP 400 before any charge: the provider does not accept function tools for this model on `/v1/chat/completions` at its default reasoning setting. The external guard stopped the grid; $0.00 was spent and no ledger line was written.

| Date | File | Change | Reason |
|---|---|---|---|
| 2026-10-01 | `code/actrec/llm_client.py` | Requests go to `/v1/responses` (stateless, `store=false`). Each model runs at its **default** reasoning setting (no `reasoning` field is sent unless a grid sets one). For reasoning models the encrypted reasoning items are requested (`include: reasoning.encrypted_content`) and passed back with the transcript. Usage is read from `input_tokens`, `input_tokens_details.cached_tokens`, `output_tokens` (reasoning tokens are billed inside output tokens and also recorded separately). If the provider refuses an optional field (`parallel_tool_calls`, `include`, `store`) it is dropped and remembered for the episode; these fields are not part of the cache hash, so replay is unaffected. `max_output_tokens` 6000 (includes reasoning). | The alternative (forcing `reasoning_effort: none`) would have changed how the main model reasons in every episode; a deployed agent would run at the default. |
| 2026-10-01 | `code/actrec/driver_llm.py` | Transcript is a list of Responses input items (goal, model output items, `function_call_output`s, nudges, reflection prompts). Resume re-executes every `function_call` without an output. Reasoning items without encrypted content are not passed back. New record fields: `tokens_cached`, `tokens_reasoning`, `incomplete_turns`, `model_latency_s`, `nudges`; the last assistant text is kept when the model never calls `finish`. | Endpoint change. Agent-visible behaviour (system text, goal, tools, cue, nudges, reflection prompt, turn and tool-call limits) is unchanged. |
| 2026-10-01 | `code/actrec/agent_tools.py` | Tool definitions in the Responses format (flat `name`/`description`/`parameters`, `strict: false`). Names, descriptions and parameters unchanged. | Endpoint change. |
| 2026-10-01 | `code/actrec/runner.py`, `analysis/summarize_grid.py` | A record whose `stop` starts with `model error` or `budget` is unfinished: on resume it is archived to `episodes_errored.jsonl` and the episode is run again; the summary counts it as an error and keeps it out of the metric tables. The summary gains an LLM cost table (US$, calls, turns, tokens per driver and condition). | The two refused pilot records had no `error` field and would otherwise have counted as finished episodes. |
| 2026-10-01 | `code/tests/test_llm_driver_fake.py` | Fake model returns Responses output items (encrypted reasoning + function call). New tests: request format per model family, refused-field drop with cache replay, reasoning items passed back, crash resume of an unanswered call, unfinished-record rule. 55 tests pass offline. | — |
| 2026-10-01 | `code/tools/guarded_grids.py` (new, written on the experiment machine) | Runs paid grids one after another and kills a grid's process tree when the ledger total passes `--max-usd` or a record stops with `budget:`/`model error`. | Second, external spending guard on top of the in-process caps. |

## Pre-registration tooling (2026-10-01, written while the LLM pilot was running; no effect on it)

| Date | File | Change |
|---|---|---|
| 2026-10-01 | `docs/06_analysis_plan.md`, `docs/PROTOCOL.md` (new) | Draft analysis plan (H1–H6 with exact criteria, ablation predictions, RQ1 coding) and run protocol (order of work, fixed parameters, what may be looked at, amendments). Binding once frozen. |
| 2026-10-01 | `analysis/confirmatory.py` (new) | Implements the plan: cluster bootstrap (B = 10,000, seed 20261001), exact McNemar, Holm, TOST-by-CI; writes `results/confirmatory.json` (evidence index) and `.md`. Dry run on `dev_grid` only. |
| 2026-10-01 | `analysis/llm_behaviour.py` (new) | RQ1: codes the agent's next action after the first failed/unknown write, checks before re-issue, and the honesty of the final report, by hidden truth. Test added (56 tests pass). |
| 2026-10-01 | `code/actrec/freeze.py` (new), `code/run.py`, `code/actrec/runner.py` | `run.py freeze [--check]` hashes all frozen files; the `test_*` presets refuse to start if the freeze is broken or a preset is narrowed; `grid.json` and `freeze_log.jsonl` record the freeze digest. New presets `harness_check` (test-only templates on non-test instance 900), `test_scripted` (17,820 episodes), `test_llm` (185 episodes per repeat). Child processes do not import these modules, so the running pilot is unaffected. |

## After the LLM pilot (2026-10-01)

| Date | File | Change | Reason |
|---|---|---|---|
| 2026-10-01 | `code/actrec/runner.py` | `test_llm` now covers the first two write steps, adds modes late_tail and crash_after and all read variants (670 episodes per repeat); new dev-split preset `llm_hardcheck` (28 episodes) to exercise those worlds with a real model before the freeze. | The pilot only had easy worlds (exact reads, 12 s delay), where a model that checks state can succeed; the theory's claims about LLM agents concern the hard worlds. |
| 2026-10-01 | `analysis/confirmatory.py`, `docs/06_analysis_plan.md` | H6 tested in hard worlds; easy worlds reported without a directional prediction. H4(b) de-duplicates episodes counted in both sub-populations. H5 marks a model without S/C6 pairs as not tested. | See `decisions.md`, 2026-10-01. |

## After the LLM hard-world check (2026-10-01)

| Date | File | Change | Reason (evidence) |
|---|---|---|---|
| 2026-10-01 | `code/actrec/layers.py`, `code/actrec/driver_llm.py` | Settle now also guards the LLM agent's own deletion and reversal tools by attribution. A deletion goes through only if the target carries one of this task's operation tags and is a surplus copy, not the copy the operation keeps. Deleting an untagged effect (another user's) or the only effect of a completed operation is refused with a note. Other layers, and the S−t ablation (no tags), let deletions through as before. | `runs/llm_hardcheck` (dev): in T1 look-alike/lost_ack under S, Settle had resolved the issue correctly by its tag. The model then listed issues, saw two identical titles and deleted issue #1, which was the background user's (collateral 1). Under C0 the same model deleted its *own* issue and kept the look-alike (missing). Content-based clean-up by the agent is exactly the unsound compensation of P4, and Settle's attribution is what can prevent it. The scripted driver never deletes, so the dev grid is unaffected. Test added (57 pass). |
| 2026-10-01 | `docs/PROTOCOL.md` | The validation gate names the known TigerBeetle exception: not_exec_err 0.0 and not_exec_to 0.3 as intended, from client-side retries. | Full validation 20261001-164459: all other cells pass. |

## Amendment 1 during the test run (2026-10-01)

| Date | File | Change | Reason (evidence) |
|---|---|---|---|
| 2026-10-01 | `code/actrec/llm_client.py` | `_Lock` treats `PermissionError` like `FileExistsError` (lock busy, retry). | The guard stopped `test_llm_luna` at about 620 of 670 episodes with `model error: PermissionError … runs\.cost.lock`, a Windows race while another worker deleted the lock file. The lock only protects the spending ledger, so the outcomes of finished episodes are unaffected. The stopped record was archived and re-run. Recorded as Amendment 1 in `docs/PROTOCOL.md`, with a re-freeze; the old freeze is kept as `FREEZE_2026-10-01_v1.json`. Test added (58 pass). |


## Amendment 2 after the test runs (2026-10-03)

| Date | File | Change | Reason (evidence) |
|---|---|---|---|
| 2026-10-03 | `code/actrec/services/ledger_tb.py`, `code/actrec/contracts.py` | Transfer keys are scoped per run (`Ledger.id_for`); a ledger refusal is surfaced as an error. | Model-chosen keys collided with the same key from earlier episodes of the same task (`EXISTS_WITH_DIFFERENT_DEBIT_ACCOUNT_ID` was reported to the agent as success). This affected 207 of 216 non-Settle T2/T8 luna episodes and 105 of 108 nano episodes; scripted and Settle episodes were unaffected. |
| 2026-10-03 | `code/actrec/driver_llm.py` | The checkpoint `os.replace` retries on `PermissionError`. | 9 LLM episodes crashed with WinError 5 while replacing `conversation.json`. |
| 2026-10-03 | `code/actrec/runner.py`, `analysis/confirmatory.py`, `analysis/summarize_grid.py` | A crashed agent process with no report counts as unfinished and is re-run. | 12 such episodes (9 LLM, 3 scripted) had been counted as finished. |
