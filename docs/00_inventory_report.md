# 00 — Inventory report (stage 2)

Run date: 2026-09-30 · Instructions: `docs/02_inventory_instructions.md` · Raw measurements: `runs/inventory/inventory.json` · Scripts: `code/inventory/` · Compose: `docker/inventory/`
Paid model calls: **0**. Redaction: user name → `<user>`, machine name → `<host>`, e-mail → `<email>`, home path → `~`.

## Summary

1. Machine: Windows 11 Pro 25H2 (build 26200), i7-1360P 12 cores/16 threads, 15.7 GB RAM, 517 GB free on C:, RTX 2050 4 GB; Docker Desktop 29.1.3 on WSL2 (7.6 GB, 16 CPUs); project is not in OneDrive.
2. Tooling: `.venv` with Python 3.11.9, and all 17 packages installed; git, gh, node/npm, uv and MS Word are present; pandoc, LibreOffice and conda are missing.
3. Working: PostgreSQL 16.15, Redis 7.4.11, Gitea 1.24.7, Mailpit 1.31.3, SeaweedFS 4.48, Toxiproxy 2.12.0, Temporal (server 1.32.0) and DBOS 3.2.0 all started and passed their checks.
4. FAILED: MinIO (object store A). `minio/minio` no longer exists on Docker Hub, and the one fix tried (`quay.io/minio/minio`) returns 401, so SeaweedFS is the only S3 store.
5. TigerBeetle 0.17.9 fails with the default seccomp profile (`io_uring is not available … PermissionDenied`) but runs with `seccomp=unconfined`. Resending a transfer returns `EXISTS` and it is applied once. It uses about 1.7 GiB RAM.
6. Conditional create works on SeaweedFS: a second `If-None-Match: *` is rejected with **412** (nothing is overwritten), and `x-amz-meta-op-id` metadata round-trips.
7. Gitea stores the `op-id` marker in the body byte-exact. The plain issue list shows new issues immediately, and the default (bleve) search found the body uuid after 0.68–1.88 s (5/5 trials). Issues can be closed and deleted (admin) via the API.
8. Mailpit keeps `X-Op-Id` and `Message-ID` exactly, and the `message-id:` search filter works. Search does **not** match `X-Op-Id` header values (only subject/body), so look messages up by Message-ID.
9. `timeout`, `reset_peer` and `limit_data` (Toxiproxy) each produced a real "committed but response lost" on PostgreSQL and Gitea; 5 s `latency` only delays, and no toxic stopped a write. Temporal and DBOS each left 2 rows (at-least-once).
10. Risks: little host RAM (0.97 GB free with all services up); TigerBeetle needs seccomp off; no MinIO; `.env` has no API keys, so no model lists were fetched. Ollama 0.34.4 has 7 local models. Possible LIMBO code (unverified): github.com/jaxblack/limbo-bench.

## 1. System

| Item | Value |
|---|---|
| Windows | Microsoft Windows 11 Pro, 25H2, version 10.0.26200 (build 26200), 64-bit |
| CPU | 13th Gen Intel Core i7-1360P — 12 cores, 16 logical processors |
| RAM | 15.69 GB total; 1.72 GB free at start (idle desktop), 0.97 GB free with all services running |
| Disk (C:, holds ROOT) | 997.9 GB total, 516.6 GB free |
| GPU | NVIDIA GeForce RTX 2050, 4096 MiB VRAM, driver 610.60 (also Intel Iris Xe and a USB virtual display) |
| WSL | WSL 2.6.3.0, kernel 6.6.87.2-1, default version 2; only distribution: `docker-desktop` (Running, v2, default) |
| OneDrive | `ONEDRIVE` env var is set, but `ROOT` (`~\Documents\action-recovery`) is **not** inside the OneDrive folder; Documents is not redirected |

## 2. Tooling

| Tool | Version |
|---|---|
| `py -0p` | 3.13 (default), 3.11 |
| `python` on PATH | 3.11.9 |
| conda | missing |
| uv | 0.11.7 |
| git | 2.52.0.windows.1 |
| gh | 2.85.0 |
| node / npm | v22.18.0 / 10.9.3 |
| pandoc | **missing** |
| LibreOffice | **missing** (no `soffice`, no default install path) |
| Microsoft Word | present (`Office16\WINWORD.EXE`, App Paths registry key) |

Project venv `ROOT\.venv`: Python **3.11.9** (3.12 is not installed; 3.11 was the newest allowed choice). All packages installed without errors:

| Package | Version | Package | Version |
|---|---|---|---|
| openai | 3.22.1 | python-docx | 1.2.0 |
| httpx | 0.28.1 | docx2pdf | 0.1.8 |
| psycopg / psycopg-binary | 3.3.6 / 3.3.6 | matplotlib | 3.11.2 |
| redis | 8.1.0 | pandas | 3.0.6 |
| boto3 | 1.43.106 | numpy | 2.4.6 |
| tigerbeetle | 0.17.9 | scipy | 1.17.1 |
| temporalio | 1.34.0 | statsmodels | 0.15.0 |
| dbos | 3.2.0 | pyyaml | 6.0.3 |
| | | pytest | 9.1.1 |

## 3. Docker

| Item | Value |
|---|---|
| Client / server | 29.1.3 / 29.1.3 (API 1.52, linux/amd64) |
| Compose | v2.40.3-desktop.1 |
| Server OS / backend | Docker Desktop, kernel 6.6.87.2-microsoft-standard-WSL2 → **WSL2** |
| Resources available to Docker | 16 CPUs, 7.60 GB memory |
| Storage driver / cgroup | overlayfs / cgroup v2 (cgroupfs driver) |
| `hello-world` | OK (5.1 s) |

`docker system df` before the inventory: 8 images (61.7 GB, 46.0 GB reclaimable), 5 stopped containers (4.6 GB), 4 volumes (1.3 GB), build cache 30.7 GB. These belong to other projects and were not touched; the inventory used its own compose project `actrec-inv`.

Ports 1025, 3000, 3001, 3002, 5432, 6379, 7233, 8025, 8233, 8333, 8474, 9000, 9001 and 26000–26099: **all 113 free** before start.

## 4. Services

Compose file: `docker/inventory/compose.yml` (project `actrec-inv`, network `actrec-inv-net`), with the override `compose.tb-unconfined.yml` for TigerBeetle. Credentials are in `ROOT\.env`: the three empty local passwords were filled with random values and never printed. Time to healthy is measured from `compose up` until a host-side probe succeeds, with images already pulled.

| Service | Resolved tag (version) | Digest | Size | Time to healthy | Result |
|---|---|---|---|---|---|
| PostgreSQL | `postgres:16` (16.15) | `sha256:1a6ab3f5345eb6dbe04a1349529caabdb0ab09293a09590fad07b2246bfa4b54` | 160.3 MB | 5.1 s | OK |
| Gitea | `gitea/gitea:1.24` (1.24.7) | `sha256:918955f16b1e91732af6c449bb2db3a34271748dbed1ccfbae48f8a2fb5480b8` | 75.7 MB | 7.2 s | OK |
| Mailpit | `axllent/mailpit:latest` (v1.31.3) | `sha256:ed9b00c609e77e99c79b93f1178255ebc271868920f2c69a8d166bd5634ed10d` | 14.3 MB | 1.8 s | OK |
| TigerBeetle | `ghcr.io/tigerbeetle/tigerbeetle:latest` (0.17.9) | `sha256:48f623f9c1e9b6cc44d77ca93634595ae99cce3246ded418763eb1a62eee45e9` | 11.2 MB | 4.6 s (format + start, seccomp unconfined) | OK only with `seccomp=unconfined` |
| MinIO | `minio/minio:latest` | — | — | — | **FAILED: image not pullable** |
| SeaweedFS | `chrislusf/seaweedfs:latest` (4.48) | `sha256:4e61d15fd35994cb1e43e1e553dff106794841fd9a99ade2fc8c8bfce4d7872d` | 193.6 MB | 5.4 s | OK |
| Redis | `redis:7` (7.4.11) | `sha256:c6eabf748fc7a61dbb5a705c78bcf3d6377b1127a97d0ce965c11c44ba46896f` | 43.6 MB | 1.6 s | OK |
| Toxiproxy | `ghcr.io/shopify/toxiproxy:latest` (2.12.0) | `sha256:9378ed52a28bc50edc1350f936f518f31fa95f0d15917d6eb40b8e376d1a214e` | 7.6 MB | 2.7 s | OK |
| Temporal | `temporalio/temporal:latest` (CLI 1.9.1, Server 1.32.0, UI 2.54.1) | `sha256:ad4c82c97bd12b417d1ea942610dbcd511afb250c4d5ed26c694009533df447e` | 49.8 MB | 2.0 s | OK |
| DBOS | Python `dbos` 3.2.0 on the PostgreSQL above | — | — | launch 1.5 s | OK |

### PostgreSQL
Created table `inv_ops` (with an `op_id text` column and an index), inserted a row and selected it by `op_id`: OK. Round-trip, median of 20: **0.85 ms** (select by `op_id`), 1.94 ms (autocommit insert).

### Gitea
- Non-interactive install through env (`INSTALL_LOCK=true`, SQLite). Admin created with `gitea admin user create`; token created with `gitea admin user generate-access-token --raw`; repo `actrec-admin/inventory-probe` created via the API.
- 5 issues, each with a body line `op-id: <uuid>` and a title without it.
- (a) GET issue: body **byte-exact** (including non-ASCII characters) in 5/5.
- (b) Indexer lag, default indexer (bleve at `/data/gitea/indexers/issues.bleve`), polled every 0.5 s: global search `/repos/issues/search?q=<uuid>` found 5/5 after **0.68, 0.71, 1.20, 1.23, 1.88 s**. The repo-level `?q=` search found them after 0.68–1.88 s. Resolution is ~0.5 s. Searching only the first uuid segment also matches, because the tokenizer splits on `-`. Exact matching therefore has to be confirmed by reading the body.
- (c) The plain list `GET /repos/{o}/{r}/issues` returned the new issue **immediately** in 5/5.
- (d) Close via `PATCH state=closed` → 201, state `closed`. Admin delete via `DELETE /repos/{o}/{r}/issues/{n}` → 204, and a later GET → 404. Both are usable for compensation.

### Mailpit
- Sent 3 messages over SMTP :1025, each with `X-Op-Id: <uuid>` and a custom `Message-ID`. The uuid was placed (1) only in the header, (2) also in the body, (3) also in the subject.
- List via API: 3/3. Headers API: `X-Op-Id` and `Message-ID` **preserved exactly** in 3/3.
- Search: plain `<uuid>` finds messages 2 and 3 but **not** message 1, so search does **not** match header values (it also does not match the uuid inside the Message-ID). `message-id:<id>` finds all 3. `header:"X-Op-Id: …"` returns 200 but finds nothing.
- Delete via `DELETE /api/v1/messages {"IDs":[…]}` → 200, total 3 → 2. This only removes the captured copy; it does not "unsend" anything.

### TigerBeetle
- Attempt 1 (default seccomp): exits during format/start with:
  ```
  error(io): io_uring is not available
  error(io): likely cause: the syscall is disabled by sysctl, try 'sysctl -w kernel.io_uring_disabled=0'
  error: PermissionDenied
  ```
  The sysctl hint was **not** applied, because it would change the Docker Desktop VM.
- Fix (inside ROOT): override `security_opt: seccomp=unconfined` → formatted and listening in 4.6 s, single replica, cluster 0, `--development`, `--cache-grid=256MiB`. The log reports "Allocated 1677MiB during replica init".
- Python client 0.17.9 (the server bundles 0.17.5–0.17.9; minimum client 0.16.4): 2 accounts `CREATED`; a transfer with a fixed 128-bit id → `CREATED`; the **same** transfer again → **`EXISTS`**. Lookup by id found it; balances show it applied once (debits_posted = 10). Median lookup latency 9.1 ms.

### Object store A — MinIO (failed)
```
docker pull minio/minio:latest
Error response from daemon: pull access denied for minio/minio, repository does not exist or may require 'docker login'
```
Fix attempt, `quay.io/minio/minio:latest`:
```
Error response from daemon: unknown: failed to resolve reference "quay.io/minio/minio:latest": unexpected status from HEAD request to https://quay.io/v2/minio/minio/manifests/latest: 401 UNAUTHORIZED
```
No further attempts, per rule 6. The service stays in the compose file under profile `minio`, to document it.

### Object store B — SeaweedFS (S3 gateway, :8333)
Put with `x-amz-meta-op-id` → head returns `op-id` exactly. `If-None-Match: *`: the first put is accepted, the second is rejected with **412 PreconditionFailed**, and the stored body is still the first one (no silent overwrite). List by prefix: 5/5 keys, excluding a key with another prefix.

### Redis
`XADD` with an `op_id` field, then `XRANGE` on that id: OK. `SET key NX`: first → OK, second → nil (rejected); the value stays the first one. Median latency: PING 0.89 ms, XADD 0.48 ms.

### Toxiproxy
Proxies `pg` (:26000 → postgres:5432) and `gitea` (:26001 → gitea:3000). Median baseline, 20 requests each: PostgreSQL `select 1` 0.82 ms direct vs 1.67 ms through the proxy; Gitea `GET /api/v1/version` 2.68 ms direct vs 1.71 ms through the proxy (difference within noise). Toxics were added one at a time and removed afterwards; the client deadline was 15 s. For PostgreSQL the connection was open before the toxic was added. For Gitea each request used a fresh HTTP connection. "Reached upstream" was checked on ports 5432/3000 directly.

| Toxic | PostgreSQL: client sees | PG write reached upstream | Gitea: client sees | Gitea write reached upstream |
|---|---|---|---|---|
| `latency` 5000 ms downstream | success after 5.01 s | yes | success after 5.64 s | yes |
| `timeout` 0 downstream (hold) | no response; client deadline hit at 15.0 s | **yes** | `httpx.ReadTimeout` after 14.5 s | **yes** |
| `reset_peer` downstream | `psycopg.OperationalError: consuming input failed: server closed the connection unexpectedly` after 0.007 s | **yes** | `httpx.RemoteProtocolError: Server disconnected without sending a response` after 0.48 s | **yes** |
| `limit_data` 16 B downstream | same `OperationalError` after 0.008 s | **yes** | same `RemoteProtocolError` after 0.46 s | **yes** |

"Committed but response lost" happened with `timeout`, `reset_peer` and `limit_data` on both upstreams. No toxic stopped a write from reaching the upstream (all toxics are downstream only).

### Temporal
Image `server start-dev` (Server 1.32.0), SDK temporalio 1.34.0; server healthy after 2.0 s, client connect 0.16 s. The workflow has one activity (retry: 200 ms initial, max 3 attempts) that inserts a row and raises on attempt 1 after the insert. It completed on attempt 2 in 1.32 s. **Rows afterwards: 2** (at-least-once, as expected).

### DBOS
dbos 3.2.0, system DB `actrec_dbos_sys` on the same PostgreSQL; launch 1.47 s. Same experiment with `@DBOS.step(retries_allowed=True, max_attempts=3)`: completed on attempt 2 in 0.40 s. **Rows afterwards: 2** (at-least-once).

## 5. Resources under load

All 8 running services (`docker stats --no-stream`):

| Container | CPU | Memory |
|---|---|---|
| tigerbeetle | 0.6 % | **1.668 GiB** |
| gitea | 5.2 % | 210 MiB |
| temporal | 0.5 % | 91 MiB |
| seaweedfs | 0.8 % | 75 MiB |
| postgres | 9.1 % | 64 MiB |
| mailpit | 7.4 % | 14 MiB |
| toxiproxy | 0.0 % | 5 MiB |
| redis | 6.3 % | 4 MiB |
| **Total** | | **≈ 2.17 GiB of 7.6 GiB** |

Host free RAM with everything running: **0.97 GB of 15.69 GB**. There is room inside the Docker VM, but the host itself is tight.

## 6. Network

No proxy environment variables are set. Each result below is 3 unauthenticated `HEAD /` requests, each with a new TLS connection, so the latency includes the handshake.

| Host | DNS | HTTPS reachable | Status | Median |
|---|---|---|---|---|
| pypi.org | yes | yes | 200 | 491 ms |
| github.com | yes | yes | 200 | 607 ms |
| ghcr.io | yes | yes | 405 | 897 ms |
| registry-1.docker.io | yes | yes | 404 | 541 ms |
| api.openai.com | yes | yes | 421 | 697 ms |
| generativelanguage.googleapis.com | yes | yes | 404 | 827 ms |
| api.groq.com | yes | yes | 404 | 669 ms |
| openrouter.ai | yes | yes | 200 | 657 ms |
| huggingface.co | yes | yes | 200 | 576 ms |

## 7. Models

`.env` did not exist before this run. It was created from `.env.example`, and only the three local-service passwords were filled.

| Key | Non-empty |
|---|---|
| OPENAI_API_KEY | no |
| GEMINI_API_KEY | no |
| GROQ_API_KEY | no |
| OPENROUTER_API_KEY | no |
| OLLAMA_BASE_URL | yes |
| MAX_SPEND_USD / MAX_SPEND_PER_RUN_USD | yes (template values) |
| POSTGRES_PASSWORD / GITEA_ADMIN_PASSWORD / MINIO_ROOT_USER / MINIO_ROOT_PASSWORD | yes |

Because every provider key is empty, **no provider endpoint was called** (not even the listing endpoints), and no `models_<provider>.json` files were written. To list models later, fill the keys and re-run `code/inventory/step7_models.py`; it calls only the listing/key-info endpoints.

Local: **Ollama 0.34.4**, server running at `localhost:11434`. Nothing was pulled or loaded.

| Model | Size | Params | Quantization |
|---|---|---|---|
| qwen2.5:1.5b | 0.99 GB | 1.5B | Q4_K_M |
| qwen2.5:3b | 1.93 GB | 3.1B | Q4_K_M |
| llama3.1:8b | 4.92 GB | 8.0B | Q4_K_M |
| phi3:latest | 2.18 GB | 3.8B | Q4_0 |
| llama3:8b / llama3:latest (same blob) | 4.66 GB | 8.0B | Q4_0 |
| nomic-embed-text:latest | 0.27 GB | 137M | F16 |

GPU offload is not visible because no model is loaded (`ollama ps` is empty). With a 4 GB RTX 2050, only the ≤3B models would fit fully in VRAM. LM Studio: not installed.

## 8. Reference repositories

Shallow clones are in `ROOT\external\` (git-ignored). None of their code was run.

| Repo | Reachable | License file | Commit (date) | Size | Top level | Runtime |
|---|---|---|---|---|---|---|
| shushuyang231/ambiguous-tool-outcomes-benchmark | yes | `LICENSE` (MIT), `LICENSE-DATA.md` | `4b626e7cde61ec9275a30e23982d146ee6f4e65d` (2026-08-11) | 10.2 MB | .env.example, ARTIFACT_CANDIDATE_MANIFEST.json, CHANGELOG.md, CITATION.cff, README.md, configs/, data/, paper/, prompts/, protocol/, pyproject.toml, research_sqj_v1_4.md, runs/, scripts/, src/, tests/, tools/ | Python (pyproject.toml); also TeX/PowerShell |
| gssanjana4/idempotencybench | yes | `LICENSE` (MIT) | `1b9b30fd37f983d6e2eb0ebf535bfcb1086fb311` (2026-07-25) | 5.8 MB | CITATION.cff, README.md, figures/, paper.pdf, results/, run_tests.py, src/ | Python (no dependency manifest) |
| flame-stream/mcp-annotation-census | yes | `LICENSE` (MIT) | `5c24643d447402fc7bf8096555f72859b2c126cb` (2026-08-29) | 105.1 MB | REPORT.md, README.md, audit_heuristic.py, census.py, output_full2/, requirements.txt, test_census.py | Python (requirements.txt) |

LIMBO (arXiv 2609.29095, "Where Does Exactly-Once Live?"): the GitHub repository search (unauthenticated REST) found one candidate, **https://github.com/jaxblack/limbo-bench**. Its description says "Code and data for 'Where Does Exactly-Once Live?'". Treat it as **unverified**: the README cites neither the arXiv id nor the paper title, the repo was created 2026-09-24, and it has 0 stars (MIT, Python). It was not cloned.

## Cleanup

`docker compose -p actrec-inv down -v --remove-orphans` → rc 0. No containers, volumes or network of the inventory project remain. Pulled images were kept. Other projects' containers and volumes were not touched.

## Addendum (2026-09-30, step 7 re-run)

After `OPENAI_API_KEY` and `GROQ_API_KEY` were added to `.env`, `code/inventory/step7_models.py` was re-run. Only the free model-listing endpoints were called; no key values were printed.

| Provider | HTTP | Models listed | File |
|---|---|---|---|
| OpenAI | 200 | 133 | `runs/inventory/models_openai.json` |
| Groq | 200 | 11 | `runs/inventory/models_groq.json` |
| Gemini, OpenRouter | not called (no key) | – | – |

Summary line 10 and section 7 above describe the first run, before the keys were added.

