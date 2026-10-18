# Did the Action Already Happen? Reliable Recovery for AI Agents Under Ambiguous Tool Outcomes

Code, service definitions, run records, analysis and paper for a study of how tool-using AI agents should recover when a
write times out or returns an unclear result, so that the agent cannot tell whether the action took effect.

The full paper, with Appendices A–E, is in [`paper/final/`](paper/final/) as PDF and Word.

## What is in the study

- **Theory.** *Attributability* means the client can work out how many effects one of its operations left standing.
  Using it, the paper proves which guarantee (prevention, convergence or honest abstention) each API contract
  and read model allows.
- **API census.** The documented write contracts of 52 widely used APIs are coded by hand from vendor documentation
  (`paper/exploratory/census/`).
- **Settle.** A recovery layer that journals each intent, stamps an operation id into a field the service persists,
  resolves unknown outcomes by that id once the in-flight bound has passed, keeps reconciling up to a horizon, and
  compensates only effects it can prove are surplus (`code/actrec/layers.py`).
- **Evaluation on real services with real faults.** PostgreSQL, Gitea, Mailpit, Redis, SeaweedFS and TigerBeetle
  run in Docker. Toxiproxy injects network faults, process kills simulate agent crashes, and Temporal serves as the
  workflow-engine baseline. Grading reads service-side records only. The study has 17,820 scripted episodes and
  2,680 language-model episodes, plus a separately frozen follow-up study of 4,272 episodes. All model calls together
  cost US$ 9.49 (`runs/cost_ledger.jsonl`).
- **Pre-registration.** Hypotheses, analysis code and source hashes were frozen before the test runs
  (`docs/PROTOCOL.md`, `docs/06_analysis_plan.md`, `docs/07_followup_plan.md`, `FREEZE*.json`).

## Repository layout

| Path | Contents |
|---|---|
| `code/actrec/` | Harness: services, fault injection, scripted and language-model drivers, recovery layers and baselines, grader, runner, freeze |
| `code/run.py` | Entry point (stack, validation, grids, freeze) |
| `code/tools/` | Unattended runners for the follow-up study and for budget-guarded model grids |
| `code/tests/` | Offline tests (no Docker, no API key) |
| `docker/` | Compose file for the eight services; the exact image digests used are recorded in `images.lock.json` |
| `analysis/` | Frozen analysis scripts (confirmatory tests, language-model behaviour coding, follow-up) |
| `results/`, `results_v2/`, `results_followup/` | Analysis outputs used by the paper (`results_v2/` is the first analysis of the main study, kept after an amendment; see `docs/PROTOCOL.md`) |
| `runs/` | Run records: one folder per grid with `episodes.jsonl`, plus the cost ledger and status logs (see `runs/README.md`) |
| `docs/` | Study design, theory notes, analysis plans, protocol and amendments, decision log |
| `paper/` | Scripted paper build (Markdown → Word and LaTeX/PDF), evidence index, exploratory analyses, figures |
| `FREEZE.json` | Current freeze (follow-up study). Earlier freezes are kept as `FREEZE_<date>_*.json` |
| `scripts/pack_raw_runs.py` | Packs the per-episode folders into release archives (see below) |

## Requirements

- Python 3.11. The study ran on Windows 11 and `requirements.txt` was frozen there. It lists two Windows-only
  packages (`pywin32`, `docx2pdf`) that you can skip on Linux or macOS.
- Docker Desktop, needed only to run new episodes.
- An OpenAI API key, needed only to run new language-model episodes.
- To rebuild the paper: pandoc 3.1 or later and a TeX distribution with `xelatex` and the TeX Gyre fonts.

```
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
copy .env.example .env        (fill in only what you use; .env is git-ignored)
```

On Linux or macOS, use `.venv/bin/python` and forward slashes in the commands below.

## Reproduce the paper's numbers (no Docker, no API key)

Every number in the paper is derived by script from the committed records.

```
.venv\Scripts\python code\run.py freeze --check
.venv\Scripts\python analysis\confirmatory.py --scripted runs\test_scripted --llm runs\test_llm_nano runs\test_llm_41mini runs\test_llm_luna --out results
.venv\Scripts\python analysis\followup.py --runs runs --out results
.venv\Scripts\python paper\followup\followup_corrected.py --runs runs --out results_followup
.venv\Scripts\python paper\derive.py --root .
.venv\Scripts\python paper\exploratory\make_extra.py
.venv\Scripts\python paper\followup\derive_followup.py
.venv\Scripts\python paper\build.py
```

`freeze --check` confirms that the frozen code, analysis plans and protocol are byte-identical to the freeze
(digest prefix `87ddadb5`). `paper/build.py` writes `paper/build/paper.docx`, `paper.tex` and `paper.pdf`, and it
reports any number the text references that the evidence index lacks.

`analysis/llm_behaviour.py` codes each saved model conversation, so it needs the per-episode folders from the raw
archive (see below). Its outputs are committed in `results*/llm_behaviour.jsonl`.

One analysis correction was made after the follow-up runs. It is documented in `docs/PROTOCOL_corrections.md`. The
frozen script is unchanged, and the corrected copy is `paper/followup/followup_corrected.py`.

## Run the experiments

```
.venv\Scripts\python -m pytest code\tests -q
.venv\Scripts\python code\run.py stack up --engine
.venv\Scripts\python code\run.py validate --trials 3
.venv\Scripts\python code\run.py grid --name my_smoke --preset smoke --workers 3
.venv\Scripts\python code\run.py stack down
```

- `validate` checks that each injected fault produces its intended hidden outcome, using each service's own records.
- Model grids are capped by `MAX_SPEND_USD` and `MAX_SPEND_PER_RUN_USD` in `.env`. Paid responses are cached in
  `runs/cache/`, so re-running a grid replays them free of charge.
- The code never reads `.env` values back out or prints them.
- `code/tools/followup.py` re-runs the complete follow-up study in order: freeze check, grids, then analysis.

## Raw per-episode records

Each episode also has its own folder (`runs/<grid>/episodes/<id>/`). It holds the configuration, the dispatch and
checkpoint logs, the grader's report and, for model episodes, the full conversation. There are 29,394 such
folders, and they are kept out of git together with the model response cache (`runs/cache/`). They are published as
release archives:

```
.venv\Scripts\python scripts\pack_raw_runs.py
```

This writes `release/raw_<grid>.tar.gz` for every grid and `release/response_cache.tar.gz`, and it refuses to pack
anything that contains a value from `.env`. Upload the files as assets of a GitHub release. To use them, extract
them into the repository root.

## Citation

Ankitha Vuyyala, Independent Researcher, Louisville, Kentucky, USA ·
[ORCID 0009-0004-1916-8070](https://orcid.org/0009-0004-1916-8070) · ankithavuyyala08@gmail.com

```bibtex
@misc{vuyyala2026action,
  author       = {Ankitha Vuyyala},
  title        = {Did the Action Already Happen? Reliable Recovery for {AI} Agents Under Ambiguous Tool Outcomes},
  year         = {2026},
  month        = oct,
  howpublished = {\url{https://github.com/ankitha-vuyyala/action-recovery}},
  note         = {Release v1.0}
}
```

GitHub's "Cite this repository" button reads the same details from `CITATION.cff`.
