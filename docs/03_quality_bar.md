# 03 — Quality bar

What this paper must have to be read as a top-tier contribution, not an engineering report. Every later design decision is checked against this list.

## 1. A formal core that makes predictions
- Define the **contract classes** of a write: native key (K), key-less but attributable (A), unattributable (U), each reversible or irreversible. Also define what the agent can observe: exact reads, lagged reads, look-alike records, aggregate-only reads.
- Separate two guarantees: **prevention** (no duplicate ever executes) and **convergence** (the final state is correct by horizon *H*).
- State and prove, for each cell of class × observability, which guarantee is achievable by any client-side policy and which is impossible:
  - Build on the late-commit impossibility for prevention (LIMBO, Prop. 1) and the outcome-resolution boundary (Trofimov & Novikov).
  - Add the new positive result: attribution + durable journal + bounded in-flight time give convergence for reversible class-A writes.
  - Add the new negative results: look-alike records defeat content verification; unattributable irreversible writes allow neither guarantee.
- The experiments then **test the theory cell by cell**. A cell that disagrees with the prediction is reported and explained.

## 2. Real phenomena, measured
- Real services in Docker, real network faults (proxy), real process kills, real index lag and real concurrent writers. No simulated service.
- Measure the environment itself before measuring agents: commit-then-lose rates per fault type, index-lag distributions, and whether tags survive each API byte-exact.

## 3. Fair, strong comparisons
- Baselines implemented faithfully:
  - naive retry, never retry, idempotency keys;
  - a real workflow engine with retries;
  - verify-before-retry;
  - a reimplementation of the strongest published client-side guard;
  - reflection;
  - checkpoint-rollback with compensation.
- Matched model budgets, and a **matched-latency control** so no gain can come from waiting alone.
- Ablations remove one component at a time.
- An outcome oracle bounds what any client-side policy could do.

## 4. Generality
- At least two model families, mixing paid, free-tier and local models. Also a policy with no model at all (a scripted agent), to separate the layer's effect from model behavior.
- Several services and task types, including multi-step workflows where partial failure matters.

## 5. Statistical rigor
- Dev/test split. Hypotheses, analysis plan and code hashes frozen before the test split is touched.
- Paired designs over identical worlds and faults; repeated runs.
- Cluster-aware intervals (tasks are correlated); exact paired tests; equivalence tests where a hypothesis predicts "no difference".
- Multiplicity control. Effect sizes with intervals, not only p-values.

## 6. Honesty
- Negative and mixed results reported as found, in the main text.
- Exploratory analyses labeled as exploratory; every deviation from the frozen protocol listed.
- Limitations stated concretely: provider scope, service choice, task length.

## 7. Depth of scholarship
- Related work engages the distributed-systems foundations, not only 2026 agent papers:
  - Two Generals and the exactly-once barrier;
  - sagas and compensating transactions;
  - Helland on idempotence;
  - RIFL, Beldi, durable execution;
  - multilevel transactions.
- The paper also positions precisely against LIMBO, the anomaly catalog, Atomix, Cordon, RAC and SagaLLM.
- Every reference verified against its source.

## 8. Insight, not just numbers
- A failure taxonomy of residual errors, with real traces.
- Clear guidance for three audiences: API designers (what to expose), harness builders (what to own), model developers (what to learn).

## 9. Reproducibility
- Public code, compose files with pinned image digests, raw records, response cache and cost ledger.
- Replay without API keys.
- An evidence index linking every number in the paper to a saved record, checked by an independent agent.
