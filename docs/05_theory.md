# 05 — Formal model: when can an agent recover from an ambiguous tool outcome?

Status: draft v1 (30 Sep 2026). This is the theoretical core of the paper. Every proposition below makes a prediction that the experiments test cell by cell (see `04_study_design.md`, Table P). Proofs are sketches here; full proofs go in the paper's appendix.

## 1. Setting

- A **logical operation** ℓ is one intended change to an external service S (create one issue, send one email, transfer once).
- The client makes **attempts** a₁, a₂, … of ℓ. Each attempt is dispatched at time tᵢ.
- Each attempt either **executes** exactly once at an unknown time tᵢ + δᵢ, with δᵢ ≥ 0, or **never executes**.
- An executed attempt produces one **effect** e. An effect is **standing** until it is neutralized.
- The client receives a response oᵢ ∈ {ack(info), error, timeout}, possibly none, and can issue **reads** through the service's read paths.
- The client may crash. Only state written to durable storage survives a crash.

**Hidden world.** The world w fixes, for every attempt, whether and when it executes. Reads also return effects created by **other actors** sharing the service.

**Observation.** The client's history h is the sequence of its own actions, the responses and the read results. A **policy** π maps histories to actions: re-issue, read, wait, compensate an effect, report.

Two worlds are **observation-equivalent up to time t** if every policy receives the same history in both until t.

## 2. Contract properties of a write

Three properties belong to the service's interface, not to the agent:

1. **Native key (K).** Attempts carrying the same key κ produce at most one effect, and repeats return the original outcome.
2. **Read model.** What reads return about standing effects:
   - **exact**: every standing effect, with its fields, immediately;
   - **lagged**: as exact, but only effects older than λ;
   - **content**: effects are returned by content, and other actors may create effects with identical content (look-alikes);
   - **aggregate**: only a count or sum.
3. **Reversibility.** Whether a *targeted* compensation c(e) exists that neutralizes exactly the effect e. Examples: delete issue #n, delete row id r, XDEL entry id. A compensation can also be *fungible*, which neutralizes "one unit" (decrement a counter), or not exist (an email that was sent).

**In-flight bound.** An attempt that has not executed within Δ after dispatch never executes. Δ may be unknown, or the delay distribution may be heavy-tailed.

## 3. The central definition: attributability as identifiability

> **Definition (attributable by time t).** Operation ℓ is *attributable at t* under a read model if the number N_ℓ(t) of standing effects of ℓ is a function of the client's possible observation histories at t. Equivalently, no two worlds that are observation-equivalent up to t disagree on N_ℓ(t).

This one definition unifies four mechanisms that are usually treated separately:

| Source of attributability | How N_ℓ becomes identifiable | Our service |
|---|---|---|
| Native key | the service enforces N_ℓ ≤ 1 and answers "exists" | TigerBeetle transfer id, S3 `If-None-Match` |
| **Client tag** | the client writes an operation id τ into a persisted field; a read returns all effects carrying τ | Gitea issue body, Message-ID, row column, stream field, object metadata |
| Exclusivity | the client is the only writer, so the change in an aggregate equals N_ℓ | counter with no other writers |
| Returned id | the service returns the effect's id in the response | **lost exactly when the response is lost**, so it never helps in the ambiguous case |

The last row is a small but useful observation: the most common API design, "the server returns the new id", gives no attributability in precisely the situations that matter.

## 4. Two guarantees

- **Prevention.** Over the whole episode, ℓ executes exactly once. This is LIMBO's "exactly-once".
- **Convergence at horizon H.** At time H, exactly one effect of ℓ is standing, and no effect of another operation or actor has been neutralized. Transient duplicates are allowed.
- **Safe abstention** (fallback). If neither guarantee is achievable, the policy reports ℓ as *unknown* and never claims completion. This is a property of reporting, not of state.

Prevention implies convergence (with no compensation needed). The reverse does not hold. The paper's thesis is that convergence is the right target wherever prevention is provably impossible and effects are attributable and reversible.

## 5. Propositions

**P1 (prevention needs a durable key; Li 2026, Prop. 1–2, extended to crashes).**
- With a native key, "re-issue with the same key until acknowledged" achieves prevention in every world, provided the key is a function of **durable** state.
- If the key is regenerated after a client crash, as an in-memory UUID would be, then two attempts with different keys can both execute, and prevention fails.
- Without a key, no policy whose actions depend only on observations achieves prevention under late commits when Δ is unknown. This is Li's Proposition 1.

*Prediction:* on K writes, keys and Settle both reach zero duplicates; keys without a journal fail exactly in the crash worlds.

**P2 (convergence for attributable, reversible writes; new, positive).** Assume:
- (a) a durable intent record with tag τ is written **before** the first dispatch;
- (b) every executed attempt persists τ byte-exact;
- (c) the read path is complete and sound for τ after lag λ;
- (d) the in-flight bound Δ holds;
- (e) targeted compensation exists;
- (f) no other actor neutralizes effects carrying τ.

Then the following policy achieves convergence by H = t_last + Δ + λ + (compensation time). It needs no assumption about the model or the order of faults:

1. Wait until t_last + Δ + λ. Read N = |effects with τ|.
2. If N = 0, re-issue with the same τ, then go back to step 1.
3. If N > 1, compensate N − 1 effects, chosen by id. Re-read until N = 1.

*Proof sketch.*
- By (d), after t_last + Δ every attempt has either executed or never will.
- By (b) and (c), the read at t_last + Δ + λ returns exactly the standing effects of ℓ, so N = N_ℓ.
- Targeted compensation is naturally idempotent: deleting a deleted issue returns 404. It can therefore be retried through the same faulty channel until a read confirms it.
- By (f), only the client changes N_ℓ. The loop ends with N_ℓ = 1 with probability 1, provided each attempt succeeds with positive probability. ∎

*Quantitative corollary:* if Δ is unknown and δ has distribution F, the probability of an inconsistent state at a fixed horizon H is at most P(re-issue) · (1 − F(H − t₀)).

*Prediction:* on A-reversible writes, Settle's residual inconsistency is near zero, and it rises exactly when H is shorter than the injected delay. The without-horizon ablation fails in late-commit worlds.

**P3 (irreversible writes: convergence collapses to prevention).**
- If effects cannot be neutralized, convergence at H implies that ℓ never executed twice. So convergence is equivalent to prevention, and P1 applies: without a key, no policy can guarantee both completion and no duplicate when Δ is unknown.
- With a known Δ, "wait Δ + λ, read by τ, re-issue only if N = 0" achieves prevention.
- Attribution makes the "N = 0" test exact. A content-based test can be fooled, as P4 shows.

*Prediction:* on irreversible attributable writes (email by Message-ID), Settle's duplicate rate is about P(δ > Δ_assumed), and below the guard's when look-alikes exist.

**P4 (content-based verification is unsound under look-alikes; new, negative for existing methods).**
- Let w₁ be a world where our attempt executed and no look-alike exists. Let w₂ be a world where our attempt did not execute and another actor created an effect with identical content.
- Under a content read model, w₁ and w₂ are observation-equivalent, and N_ℓ differs (1 vs 0). So ℓ is not attributable.
- Any content-only policy is therefore wrong in at least one of the two worlds:
  - Skipping leaves ℓ missing in w₂.
  - Re-issuing duplicates in w₁.
  - Compensating "one matching record" after a re-issue either deletes the other actor's record in w₂ (collateral damage) or is a coin flip.
- A client tag restores attributability, because look-alikes do not carry τ.

*Prediction:* verify-before-retry and the guard misclassify in proportion to the look-alike rate, and can cause collateral damage when they compensate. Settle is unaffected.

**P5 (aggregate reads: exclusivity is the only route).**
- Under an aggregate read model, ℓ is attributable **iff** no other actor writes to the aggregate during the ambiguity window. In that case, the change in the aggregate determines N_ℓ.
- With concurrent writers, the world where ours executed and the world where another actor's write executed instead give the same aggregate. Then neither prevention nor convergence is achievable without a key, and the only correct behavior is safe abstention.
- Fungible compensation does not help: the number of surplus effects is not identifiable.

*Prediction:* on counters without other writers, Settle converges (by delta). With concurrent writers, every method fails one of completion, consistency or honesty, and Settle should abstain rather than guess.

**P6 (journal before dispatch is necessary across crashes).**
- If the client can crash between dispatch and recording, then a policy that records intent only after dispatch cannot tell "never attempted" from "attempted, outcome unknown" after a restart.
- In the first case it must issue; in the second it must not issue blindly. The two cases are observation-equivalent, so the policy fails in one of them.
- Write-ahead intent (assumption (a) of P2) removes the ambiguity.
- Workflow engines journal *activity scheduling* durably but re-execute the activity at least once. They therefore satisfy (a) only at the step level, not the effect level: durability without attribution yields at-least-once.

*Prediction:* the without-journal ablation fails in crash worlds. Temporal and DBOS converge only on K writes.

## 6. Achievability map (the paper's main figure)

Columns give which guarantee is achievable by *some* client-side policy; the last column names the policy class that attains it.

| Contract | Read model | Prevention | Convergence at H | Attaining policy |
|---|---|---|---|---|
| K, any reversibility | any | ✓ (durable key) | ✓ | key + journal |
| A, reversible | exact / lagged, Δ known | ✗ under late commit | ✓ | tag + journal + horizon + targeted compensation |
| A, reversible | lagged, Δ heavy-tailed | ✗ | with probability F(H − t₀) | same; residual risk shrinks as H grows |
| A, irreversible | exact / lagged | ✓ only if Δ is known and waited | = prevention | tag + wait-then-verify |
| any, key-less | content with look-alikes | ✗ | ✗ for content-only policies; ✓ with a tag | tag |
| U (aggregate), exclusive | aggregate | ✗ under late commit | ✓ if fungibly reversible | delta + horizon |
| U (aggregate), concurrent | aggregate | ✗ | ✗ | safe abstention only |
| U, irreversible | none | ✗ | ✗ | safe abstention only |

The empirical part of the paper fills each row with measured rates for each method, so readers can see the theory's boundaries hold on real services, or where they break.

## 7. What the theory does not cover (stated as limitations)

- Semantic errors: the agent sends the wrong content once.
- Byzantine services: a service that drops or rewrites the tag. This is tested empirically per service (tag fidelity).
- External reactions to a transient duplicate before it is compensated. This is the "phantom compensation" anomaly. We measure **duplicate exposure time** so readers can judge it.
- Multi-effect atomicity across services.
