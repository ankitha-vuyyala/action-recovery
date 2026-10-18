# 01 — Literature check and proposed claim

Status: approved as starting point · 30 Sep 2026
Working title: *Did the Action Already Happen? Reliable Recovery for AI Agents Under Ambiguous Tool Outcomes*

---

## 1. Closest work (2025–2026)

"Read" = full text checked; "abstract" = abstract/secondary summary only. All entries are re-verified in the reference pass (stage 7).

| Work | What it does | What it leaves open for us | Checked |
|---|---|---|---|
| **Li, "Where Does Exactly-Once Live?" (LIMBO), arXiv 2609.29095, 24 Sep 2026** | 6 *simulated* services, 12 fault modes (incl. late commit, redelivery, partial batch), 9 models, 3 production harnesses, 25,930 episodes. Proves no verification-only policy is exactly-once under late commits without an in-flight bound. Keys cut duplicates 28%→4%. A client-side "guard" (auto-keys, re-verify after lag, block unverifiable repeats, annotate) helps weak models only. Outcome oracle caps client-side policies at 87% on the native contract. | Simulated services (their stated limitation). Objective is *prevention*; a compensated duplicate still counts as failure, and no method tries to *converge* after a late commit. No agent-process crash, no durable journal, no workflow-engine baseline, no rollback/compensation baseline, no concurrent look-alike writers. Short tasks. | Read |
| **Trofimov & Novikov, "When Tool Calls Succeed but Workflows Fail", arXiv 2609.15397, 14 Sep 2026** | Effect-history model; 8 anomalies (A1 duplicated, A2 missing, A3 orphaned compensation, A4 residue, …). Argues that without a primitive giving one authoritative outcome (idempotent re-issue, status endpoint, durable ack) no protocol is both unknown-safe and compensation-safe. MCP census: annotations cannot express these. | Theory and census only, no agent experiments. Does not ask whether an authoritative-outcome primitive can be *constructed* from ordinary API fields. | Read |
| **Mansoor et al., "Verified Tool Calls…", arXiv 2608.02645, Aug 2026** | Verify-before-retry wrapper + idempotency keys; one model, two tasks, simulator. | Simulator only; notes key-less APIs leave a race window; no late commits, crashes or compensation. | Abstract + excerpts |
| **Sun, "Did it happen?", Research Square 2026** | Observation-equivalent counterfactual pairs; 5 models retry blindly ~half the time without a status query or stable key. | Eventual consistency and partial commits out of scope; no mitigation. | Via LIMBO |
| **IdempotencyBench (Gopnal Swamy, 2026, GitHub)** | Hidden effect ledger; scripted agents. | No LLM agents. | Via LIMBO |
| **Atomix, arXiv 2602.14849** | Progress-gated commit, compensation, dedup of ambiguous retries via keys; WebArena/OSWorld/τ-bench with 30% fault injection. | Dedup is in-memory (not crash-safe); relies on keys/known tool semantics. | Abstract + excerpts |
| **Cordon, arXiv 2606.17573** | Semantic transactions, effect outbox, idempotency keys during crash recovery. | External effects assumed keyed; opaque services out of scope. | Abstract |
| **Agentic Transaction, arXiv 2608.13900** | ACID-style semantic atomicity vision for data agents. | Vision/runtime for owned data, not third-party APIs. | Abstract |
| **SagaLLM (PVLDB 18, 2025)**; **RAC, arXiv 2605.03409** | Saga-style compensation; log-based compensation on failure (LangChain, τ-bench). | Assume failures are *detectable*; RAC states it cannot help tools without compensations; compensating under unknown outcome risks A3. | Abstract + excerpts |
| **AgentRewind 2608.14380, DART, GA-Rollback, AgentGit** | Checkpoint/rewind agent context and workspace. | External calls treated as irreversible; restore does not undo the world. | Via citing papers |
| **ACRFence 2603.20625** | After checkpoint-restore, LLMs re-synthesize slightly different requests, so servers see "new" requests (duplicate payments). | Attack/PoC; no recovery evaluation. | Abstract |
| **CapLease 2608.01710** | 39.8% equivalent re-proposals under uncertain outcomes; Issue–Prepare–Commit with stable key. | Authorization layer; keyed downstream. | Abstract |
| **Advani, false success, 2606.09863** | Agents claim completion when state disagrees. | Not about ambiguous writes. | Abstract |
| Durable execution (Temporal, DBOS, Inngest docs); agent-ledger/exactly-once style libraries | Durable progress + retries; libraries dedup at the caller. | Activity retries are at-least-once; "exactly-once end-to-end iff the tool honors the key" — i.e., nothing for key-less APIs. | Docs |

Classical foundations to cite: sagas (Garcia-Molina & Salem 1987), compensating transactions (Korth et al. 1990), Helland "Idempotence is not a medical condition" (2012), RIFL (SOSP 2015), Beldi (OSDI 2020), Stripe idempotent requests, the two-generals/exactly-once barrier.

### What the field has established
1. Retrying after a timeout duplicates effects; frontier models mostly verify first when a read-back can reveal the outcome.
2. When the request is still in flight, verification cannot prevent duplicates; only keys can (proved and measured).
3. Keys and durable execution are the standard answer, and every runtime (Atomix, Cordon, Temporal) gets exactly-once only when the downstream honors a key.

### What nobody has measured
- **Real services.** Every agent study of ambiguous outcomes so far uses simulated services.
- **Convergence instead of prevention.** Nobody measures whether a duplicate that cannot be prevented can still be *detected and repaired* so the final state is right.
- **Key-less APIs that still carry a persisted, queryable field** (issue body/label, mail Message-ID header, row column, object tag, stream field). Such a field can carry an operation ID and act as an outcome query, which is the primitive Trofimov & Novikov say is missing. This is standard practice in payments engineering ("client reference + authoritative lookup") but has never been evaluated for agents.
- **Partial observability beyond lag.** Look-alike records written by other actors and aggregate-only reads break content-based verification (LIMBO's guard, verify-before-retry); nobody has tested this.
- **Agent crashes between dispatch and record**, compared against a real workflow engine and against rollback/compensation methods, all at matched budget.

---

## 2. Proposed claim (one sentence)

> **On real services, which final states end up wrong after an ambiguous tool outcome depends less on the model or the retry policy than on whether each effect can be attributed to its operation. A recovery layer can prevent duplicates where the API offers keys and repair them where it does not. The layer journals every intent durably, stamps the operation ID into whatever persisted field the API exposes, inspects state by that ID, and keeps reconciling for a bounded horizon before compensating any surplus. On key-less services this repair leaves far fewer inconsistent final states than idempotency keys, a workflow engine with retries, verify-before-retry, or rollback/reflection methods. Its advantage disappears exactly where effects are neither attributable nor reversible.**

Relation to LIMBO: we accept its impossibility result for *prevention* and study *convergence*. We report both metrics, so our numbers can be read against theirs.

### Method (working name: **Settle**)
1. **Operation identity**: one stable op-ID per logical intent, pinned by the harness across retries, restarts and model re-phrasings.
2. **Durable intent journal**: write-ahead record `intent → dispatched → {confirmed | absent | unknown}` that survives agent-process crashes.
3. **Attribution**: native key if the API has one; otherwise the op-ID goes into a persisted, queryable field; otherwise the op is marked *unattributable*.
4. **State inspection**: resolve unknowns by counting effects carrying the op-ID, re-querying after documented lag.
5. **Bounded reconciliation horizon**: after the workflow finishes, keep checking in-doubt ops until horizon *H*; catches late commits.
6. **Evidence-gated compensation**: compensate only effects proven surplus by attribution (never under unknown outcome, avoiding A3); for irreversible or unattributable ops, hold, escalate and report "unknown" rather than guess.

### Services and faults (to be confirmed by the inventory)
- **Real services in Docker**: PostgreSQL (rows); Gitea (issues, with a real, lagging search indexer); Mailpit (SMTP plus search API, irreversible); one keyed service (TigerBeetle transfer IDs or S3/MinIO conditional put); Redis streams.
- **Contract classes**:
  - **K**: native key.
  - **A**: key-less but attributable.
  - **U**: key-less and unattributable.
  - Each class is crossed with reversible vs irreversible.
- **Faults (real, not simulated)**:
  - Toxiproxy on the response path after commit (lost acknowledgement).
  - Upstream latency beyond the client timeout (a real in-flight late commit).
  - Connection reset mid-batch (partial failure).
  - Kill of the agent process between dispatch and record (crash while in doubt).
- **Partial observability**:
  - Real search/indexer lag.
  - A background actor writing look-alike records.
  - Aggregate-only read credentials.

### Baselines (matched LLM budget)
- Naive retry.
- Never retry.
- Idempotency keys where supported.
- An ordinary workflow engine with retries (Temporal or DBOS, chosen by inventory).
- Verify-before-retry (Mansoor et al.).
- LIMBO-style guard, reimplemented from its description (the strongest client-side baseline).
- Reflection (Reflexion-style).
- Checkpoint-rollback plus compensation-on-failure (RAC/SagaLLM style).

### Ablations
- Without journal.
- Without attribution (content matching instead).
- Without horizon (verify once).
- Without compensation (flag only).
- **Guard + the same waiting time** (a matched-latency control, so the gain cannot come just from waiting).

### Metrics (all graded by code against the services' real state plus an effect ledger)
- **Primary: residual inconsistency at the horizon.** The final state ≠ spec: a required effect missing, a surplus effect still standing, or damage from a wrong compensation.
- **Secondary:**
  - Duplicate executions, including compensated ones (LIMBO's metric).
  - Duplicate exposure time.
  - Irreversible duplicates.
  - Recovery success (complete and consistent).
  - Honest reporting of unknowns.
  - Escalations.
  - Wall-clock latency.
  - Tokens and dollars.

---

## 3. Falsifiable hypotheses and what would disprove them

| # | Hypothesis | Disproved if |
|---|---|---|
| **H1 (main)** | On class-A reversible writes under ambiguous faults (lost ack, late commit, crash in doubt, partial batch), Settle's residual-inconsistency rate is ≥ 15 pp lower than the best baseline (paired, 95% CI excludes 0) and ≤ 5% absolute. | The gap is < 15 pp, the CI includes 0, or the best baseline is also ≤ 5%. |
| **H2 (partial observability)** | With look-alike writers or aggregate-only reads, content-based verification misclassifies ≥ 10% of in-doubt outcomes (false "done" or false "absent"); attribution cuts misclassification by ≥ 50% relative. | Baseline misclassification < 10%, or reduction < 50%. |
| **H3 (the gain lives where keys are missing)** | On class-K writes, Settle is equivalent to keys + workflow engine (TOST, ±3 pp). On class-A writes, keys and the workflow engine leave ≥ 10% residual inconsistency. | Settle beats keys on class K (the gain would come from something other than attribution), or the workflow engine/keys already reach ≤ 5% on class A. |
| **H4 (predicted limit)** | On class-U irreversible writes, no method achieves both completion and zero duplicates. Settle's duplicate rate is ≤ the guard's, bought with more escalations and lower completion. | Any method achieves both, or Settle duplicates more than the guard. |
| **H5 (cost)** | Settle's model cost is within +25% of the guard's; its extra latency is dominated by the horizon *H*, not by model calls. | Cost > +25%, or latency driven by model calls. |

**What would sink the whole claim:**
- The matched-latency control (guard + same wait) or keys + workflow engine matches Settle on class A.
- Real APIs strip or normalize the tag field, or search cannot find tags within the horizon, so attribution fails in practice.
- Evidence-gated compensation still creates A3/A4 damage that cancels the gain.
- Agents undermine the layer, e.g. re-phrasing requests so they escape the pinned op-ID.

All of these outcomes would be reported as found.

---

## 4. Threats to validity to design around now
- **LIMBO is six days old; reviewers will compare directly.** We adopt its duplicate metric and fault vocabulary, reimplement its guard as a baseline, and state the prevention-vs-convergence distinction up front.
- **Tagging is a known engineering practice.** The contribution is the controlled measurement on real services, the convergence objective, the partial-observability result and the boundary (H3/H4), not the idea of a tag alone.
- **Model coverage.** One paid model plus free/local models. The paper will state the provider scope as a limitation.
