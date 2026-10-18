# runs/

One folder per grid. Each grid folder holds:

- `episodes.jsonl`: one graded record per finished episode, with condition, world, fault mode, outcome, cost and timing. The analysis reads these records.
- `episodes_errored.jsonl`: episodes that did not finish (runner, grader or model errors). The analysis counts them and excludes them.
- `grid.json` and `freeze_log.jsonl`: the grid definition and the freeze digest checked before the grid ran.
- `summary.md`: a descriptive summary written by `analysis/summarize_grid.py`.
- `episodes/<id>/`: the per-episode folder with configuration, dispatch and checkpoint logs, the grader's report and, for model episodes, `conversation.json`. These folders are git-ignored and published as release archives (`scripts/pack_raw_runs.py`).

| Grids | Role |
|---|---|
| `test_scripted`, `test_llm_nano`, `test_llm_41mini`, `test_llm_luna` | Main study, test split (pre-registered) |
| `followup_a`, `followup_b`, `followup_c`, `followup_llm_*` | Follow-up study (separate pre-registration) |
| `dev_*`, `harness_check`, `llm_pilot`, `llm_hardcheck`, `llm_models_*`, `followup_smoke` | Development, pilots and gate checks; not used for confirmatory claims |
| `inventory/`, `validation/` | Stage-2 inventory and fault validation |
| `_refused_chatapi_llm_pilot` | First pilot on the chat-completions endpoint, which refused function tools for one model; replaced by the Responses endpoint (`docs/decisions.md`, 2026-10-01). Cost $0.00 |

Files at this level:

- `cost_ledger.jsonl`: every paid model call with its cost.
- `followup_budget.json`: the follow-up study's spending ceiling.
- `RUN_STATUS.txt` and `FOLLOWUP_STATUS.txt`: time-stamped logs of each step of the main and follow-up runs.
- `cache/`: the model response cache, git-ignored and published as a release archive. With it, model episodes replay without an API key.
