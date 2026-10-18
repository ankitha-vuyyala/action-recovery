# 02 — Inventory instructions (stage 2)

Purpose: find out what the experiment machine can actually run before the harness is designed.

## Hard rules

1. **No paid model calls.** Never call any endpoint that generates or embeds tokens (chat, completions, responses, embeddings, audio, images, batch), on any provider, not even a one-token test. The only model-provider endpoints allowed are the free model-listing / key-info endpoints named in step 7.
2. **Never print, log, copy or summarize secret values.** For `.env`, report only key *names* and whether each is non-empty. Load keys into the process environment for step 7 without echoing them. Redact any token that appears in command output.
3. **Work only inside the project folder** `%USERPROFILE%\Documents\action-recovery` (below: `ROOT`). Allowed outside `ROOT`: pulling Docker images, and read-only system queries. Do not change system Python, global packages, WSL or Docker Desktop settings; if a setting blocks a check, report it instead of changing it.
4. **Privacy in outputs.** In every file you write, replace the Windows user name, machine name, e-mail addresses and absolute home paths with `<user>`, `<host>`, `<email>` and `~`.
5. **Save every script you write** under `ROOT\code\inventory\` and every compose file under `ROOT\docker\inventory\`, so the inventory can be re-run.
6. If a check fails, record the exact error (first ~20 lines), try at most one reasonable fix inside `ROOT`, then move on. Do not spend more than ~10 minutes on any single service.
7. Leave the machine clean: stop and remove the inventory containers and volumes at the end (`docker compose down -v`); keep the pulled images.

## Steps

### 1. System
- Windows edition and build; CPU model and core count; total and free RAM; free disk space on the drive holding `ROOT`.
- GPU(s): `nvidia-smi` if present (model, VRAM, driver); otherwise report "none/unknown".
- WSL: `wsl --status`, `wsl -l -v` (distributions, WSL version, default).
- Whether `ROOT` sits inside a OneDrive-synced folder (this affects file locking and many small writes).

### 2. Tooling (versions, or "missing")
- Python launchers and versions: `py -0p`, `python --version`, conda (`conda info --envs` names only), `uv --version`.
- `git`, `gh`, `node`, `npm`, `pandoc`, LibreOffice (`soffice --version`), Microsoft Word present (yes/no, e.g. via registry or `Get-Command winword` / known install path).
- Create a project virtual environment at `ROOT\.venv` with the newest Python 3.11 or 3.12 available (3.13 only if neither exists). Install into it and record exact versions:
  `openai httpx psycopg[binary] redis boto3 tigerbeetle temporalio dbos python-docx docx2pdf matplotlib pandas numpy scipy statsmodels pyyaml pytest`
  Report any package that fails to install, with the error.

### 3. Docker
- `docker version`, `docker compose version`, `docker info` (server OS, backend WSL2/Hyper-V, CPUs and memory available to Docker, storage driver, cgroup version).
- `docker run --rm hello-world`.
- Docker disk usage (`docker system df`).
- Ports free on the host (listening or not): 1025, 3000, 3001, 5432, 6379, 7233, 8025, 8233, 8333, 8474, 9000, 9001, 3002 and 26000–26099 (proxy range). Report which are taken and by what, if visible.

### 4. Services: pull, start, smoke-test
Write one compose file `ROOT\docker\inventory\compose.yml` on a dedicated network, with pinned tags. Use the tag given; if it does not exist, use the newest stable tag and record it. For every image record the resolved tag **and digest**, image size, time to healthy, and the result of each check below. Put credentials in `ROOT\.env` (generate random local passwords if the fields are empty; never print them).

| Service | Image (preferred) | Checks |
|---|---|---|
| PostgreSQL | `postgres:16` | create table with a `op_id text` column; insert; select by `op_id`; round-trip latency (median of 20). |
| Gitea | `gitea/gitea:1.24` (or newest 1.x) | Non-interactive install (SQLite is fine), create admin with the CLI, create an API token, create a repo. Create an issue whose **body** contains a marker line `op-id: <uuid>` and whose title does not. Then: (a) GET the issue and confirm the marker is stored byte-exact; (b) poll the issue search API for the uuid every 0.5 s for up to 120 s and record the **indexer lag** (time until found) with the default indexer, 5 trials; (c) confirm that the repo's plain issue list (`GET /repos/{o}/{r}/issues`) returns the new issue immediately; (d) record whether issues can be deleted via API (admin) and whether closing works (for compensation). |
| Mailpit | `axllent/mailpit:latest` | Send 3 messages over SMTP (port 1025) with a custom header `X-Op-Id: <uuid>` and a custom `Message-ID`. Via the HTTP API: list messages; search for the uuid; fetch headers of a message and confirm `X-Op-Id` and `Message-ID` are preserved exactly; record whether search matches header values or only subject/body. Record whether the API can delete a message (note: deleting from the capture store is not "unsending"). |
| TigerBeetle | `ghcr.io/tigerbeetle/tigerbeetle:latest` | Format a data file and start a single-replica cluster (this may need `--security-opt seccomp=unconfined` or fail on io_uring under WSL2; record exactly what happens). With the Python client: create two accounts; create a transfer with a fixed 128-bit id; submit the **same** transfer again and record the result code (expected: exists); look up by id. |
| Object store A | `minio/minio:latest` (note: community images are no longer maintained) | Put an object with user metadata `x-amz-meta-op-id`; head it and confirm metadata; test a conditional create (`If-None-Match: *`) twice and record whether the second is rejected (412) or silently overwrites; list objects by prefix. |
| Object store B | `chrislusf/seaweedfs:latest` (S3 gateway) | Same checks as object store A. |
| Redis | `redis:7` | `XADD` with a field `op_id`; `XRANGE`; `SET key NX` behavior; latency. |
| Toxiproxy | `ghcr.io/shopify/toxiproxy:latest` | Create proxies in front of PostgreSQL and Gitea (listen ports in 26000–26099). Measure baseline latency through the proxy. Then, one at a time, add and remove: `latency` (5 s downstream), `timeout` (downstream, 0 = hold), `reset_peer`, `limit_data` (downstream, small). For each, record what the client sees (exception type/message, elapsed time) **and whether the write reached the upstream anyway** (check directly on the upstream, not through the proxy). This tells us which toxics produce a real "committed but response lost". |
| Temporal | Python SDK `temporalio.testing.WorkflowEnvironment.start_local()` **or** image `temporalio/temporal:latest` running `server start-dev` | Run a trivial workflow with one activity that inserts a row into PostgreSQL, with a retry policy; force the first attempt to raise after the insert; record how many rows exist afterwards (expected: 2, at-least-once). Record versions and start-up time. |
| DBOS | Python package `dbos` against the PostgreSQL above | Same experiment as Temporal (step raises after insert, retried). Record rows afterwards, version, start-up time. |

### 5. Resource check under load
With all services running, record Docker memory/CPU use (`docker stats --no-stream`) and host free RAM.

### 6. Network
- Proxy settings in the environment (names of variables set; values redacted except host names).
- For each host: DNS resolves (yes/no), HTTPS reachable, median latency of 3 plain `GET /` or `HEAD` requests without credentials: `pypi.org`, `github.com`, `ghcr.io`, `registry-1.docker.io`, `api.openai.com`, `generativelanguage.googleapis.com`, `api.groq.com`, `openrouter.ai`, `huggingface.co`. A 401/403/404 counts as reachable.

### 7. Models (free endpoints only)
- `.env`: list key names and non-empty yes/no. Do not print values.
- For each provider whose key is non-empty, call **only** its model-listing endpoint and save the returned model IDs (not the key) to `ROOT\runs\inventory\models_<provider>.json`:
  - OpenAI: `GET https://api.openai.com/v1/models`
  - Gemini: `GET https://generativelanguage.googleapis.com/v1beta/models` (key as header `x-goog-api-key`, not in the URL)
  - Groq: `GET https://api.groq.com/openai/v1/models`
  - OpenRouter: `GET https://openrouter.ai/api/v1/models` (public) and `GET https://openrouter.ai/api/v1/key` (free-tier/credit status; save only limit/usage/is_free_tier fields)
- Also record the HTTP status if a key is rejected (401) — that means the key is wrong, not that anything was charged.
- Local models: `ollama --version`, `ollama list` (names, sizes, quantization if shown), whether the Ollama server is running, and GPU offload if visible. **Do not pull any model.** Also report LM Studio if installed.

### 8. Relevant repositories (read-only reference)
Shallow-clone into `ROOT\external\` (git-ignored). For each: reachable yes/no, license file name, commit hash, size, top-level listing, and the language/runtime it needs. **Do not run their code.**
- `https://github.com/shushuyang231/ambiguous-tool-outcomes-benchmark`
- `https://github.com/gssanjana4/idempotencybench`
- `https://github.com/flame-stream/mcp-annotation-census`
- Also search GitHub (web or `gh search repos`, no auth needed) for a public code release of the LIMBO benchmark (paper arXiv 2609.29095, "Where Does Exactly-Once Live?"); report the URL if one exists, otherwise "not found".

## Outputs
1. `ROOT\runs\inventory\inventory.json`: all measurements, machine-readable (one top-level key per step).
2. `ROOT\docs\00_inventory_report.md`: human-readable report, one section per step. Start with a 10-line summary: what works, what failed, and anything that blocks the planned design (for example TigerBeetle not starting, no conditional create on either object store, a toxic that never lets the write reach the upstream, Gitea search that never finds body text).
3. The scripts and compose file listed in rule 5.
4. At the end, print only the 10-line summary and the list of files written.
