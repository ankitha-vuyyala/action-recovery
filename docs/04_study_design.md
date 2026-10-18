# 04 — Study design

Status: draft v1 (30 Sep 2026). This document turns the formal model (`05_theory.md`) into experiments on the services verified in the inventory (`00_inventory_report.md`). Anything marked **[pilot]** is checked in stage 3 before the protocol is frozen.

## 1. Design principle

The theory says the **contract of the write** and the **read model** decide what any recovery policy can achieve. So the study is a factorial over the following, holding everything else fixed:

- contract class: K, A, U × reversible/irreversible;
- read model: exact, lagged, content with look-alikes, aggregate;
- fault world: the hidden outcome;
- condition: recovery method;
- driver: who makes the decisions.

Every world is replayed for every condition, so all comparisons are paired.

There are two kinds of driver (all models from one provider, OpenAI; stated as a limitation):

- **Scripted driver.** A deterministic task program with no model. It isolates the effect of the recovery layer and makes the large grid free.
- **LLM agents.** These answer whether the result holds when a real model plans, re-phrases and retries on its own. They are the part that costs money.

## 2. Services and tool contracts

Each tool is a thin adapter over a real service API. The *tag field* is a field that comparable real APIs also expose, such as an issue body, a mail header, a free-text reference column, stream fields or object metadata. So stamping an operation id there is something a real client can do.

| Tool | Service (verified) | Class | Tag field / key | Exact read path | Other read paths | Compensation |
|---|---|---|---|---|---|---|
| `issue_create` | Gitea 1.24.7 | A, reversible | `op-id:` line in body | repo issue list + body read (immediate) | search (lag 0.7–1.9 s, fuzzy tokens); title search (content) | targeted: delete by number (admin) / close |
| `issue_comment` | Gitea | A, reversible | tag line in comment body | comment list | content | targeted: delete comment |
| `mail_send` | Mailpit 1.31.3 (SMTP) | A, **irreversible** | client `Message-ID` | `message-id:` search | subject/body search (content) | none |
| `mail_send_plain` | Mailpit | content-only, **irreversible** | none (server-assigned id) | — | subject/body search | none |
| `row_insert` | PostgreSQL 16.15 | A, reversible | `reference` text column | select by reference | select by content columns | targeted: delete by row id |
| `event_append` | Redis 7.4.11 stream | A, reversible | `op_id` field | XRANGE scan by field | — | targeted: XDEL id |
| `stock_adjust` | PostgreSQL | U, fungible-reversible | none | `SUM(quantity)` only (aggregate role) | — | fungible: inverse adjustment |
| `counter_incr` | Redis | U, fungible-reversible | none | GET counter (aggregate) | — | fungible: DECRBY |
| `transfer_create` | TigerBeetle 0.17.9 | **K**, reversible | 128-bit transfer id | lookup by id | — | targeted: reversing transfer |
| `object_put` | SeaweedFS 4.48 S3 | **K** (conditional create) | object key + `If-None-Match: *` | HEAD / list | metadata | targeted: delete object |

Faults go through Toxiproxy 2.12.0 on the client path only. Grader reads always go **direct** to the services, with separate credentials.

## 3. Tasks (multi-step workflows)

Each template is instantiated with seeded parameters. Each instance has 3–8 writes across 2–4 services, and its spec states the exact required effects.

| Template | Writes (class) | Why |
|---|---|---|
| T1 incident | issue_create (A), event_append (A), mail_send (A-irr), row_insert (A) | mixed reversible/irreversible |
| T2 payout | transfer_create ×2 (K), row_insert (A), mail_send (A-irr) | K vs A in one workflow |
| T3 release | object_put (K), issue_create (A), issue_comment (A), mail_send_plain (content-irr) | content-only irreversible |
| T4 restock | stock_adjust ×2 (U), counter_incr (U), row_insert (A) | aggregate reads |
| T5 migration batch | row_insert ×6 in one non-atomic batch (A), event_append (A) | partial failure |
| T6 customer notices | mail_send ×3 (A-irr), issue_create (A) | irreversible-heavy |
| T7 ticket triage | issue_create, issue_comment ×2, row_insert (A) | reversible-heavy, look-alike prone |
| T8 refund | transfer_create (K, reversing), row_insert (A), mail_send (A-irr) | compensation-shaped task |

**Splits.**
- *Dev*: T1, T2, T4, T5, T7 with instance seeds 0–9. The method's few parameters (horizon H, poll interval, assumed Δ) are tuned only here.
- *Test*: all eight templates with fresh seeds 100+. T3, T6 and T8 are never seen during development.

## 4. Worlds

### 4.1 Fault modes (one focal write per episode, injected at the n-th matching call)

| Mode | Mechanism (real, not simulated) | Hidden outcome | Paired with |
|---|---|---|---|
| none | — | executes | — |
| lost_ack | downstream `reset_peer` after the request is delivered (verified) | committed, error | not_exec_err |
| not_exec_err | upstream `reset_peer` before delivery **[pilot: confirm the error text matches lost_ack]** | absent, error | lost_ack |
| held | downstream `timeout` + client timeout T (verified) | committed, timeout | not_exec_to |
| not_exec_to | upstream `timeout`, connection dropped **[pilot]** | absent, timeout | held |
| late_fixed | upstream `latency` δ = 20 s > T **[pilot: write lands after the client gave up]** | executes at t₀ + δ | held, not_exec_to |
| late_tail | upstream latency δ ~ log-uniform 5 s – 10 min, seeded per world **[pilot]** | executes late | same |
| partial | per-row autocommit batch, `reset_peer` after k rows **[pilot]** | k of n committed | — |
| crash_after | driver process killed after dispatch, before the result is recorded; restarted | committed (or late) | crash_before |
| crash_before | driver killed after intent, before dispatch; restarted | absent | crash_after |
| redelivery | transport delivers the same request twice (simulating an at-least-once queue) | executed twice | — |

Paired modes are **observation-equivalent** by construction. The pilot measures this on the real stack: the same client exception and similar timing. If a pair is distinguishable, it is reported and the pair is dropped from equivalence claims.

### 4.2 Read-model variants

| Variant | How it is created |
|---|---|
| exact | default credentials and read paths |
| lagged | the agent's only read path for that tool is the indexed search (Gitea), or a delayed replica view **[pilot: decide if Gitea's ~1–2 s lag is enough or a delayed view is needed]** |
| look-alike | a background actor creates effects with the same content fields (title/subject/body/amount) as the focal write, at a seeded time within ±30 s of the fault; rate 0 / 1 per episode |
| aggregate-exclusive | the agent reads only a count/sum; no other writer |
| aggregate-concurrent | as above, plus a background writer adjusting the same aggregate |

## 5. Conditions

All conditions see the same worlds. Harness-level conditions run with both drivers; prompt-level conditions need an LLM.

| Code | Condition | Level | Faithful to |
|---|---|---|---|
| C0 | vanilla: model decides; scripted = naive retry | — | — |
| C1 | never retry (stop and report on error) | harness | — |
| C2 | SDK retry (transparent retries on error/timeout, ×3, backoff) | harness | common client defaults |
| C3 | idempotency keys where natively supported, else naive | harness | Stripe-style keys |
| C4 | workflow engine: Temporal activities with retry policy (DBOS as a robustness check) | harness | durable execution |
| C5 | verify-before-retry, content-based postcondition | harness | Mansoor et al. 2026 |
| C6 | guard: auto-keys, re-verify after documented lag, block unverifiable repeats, annotate uncertainty | harness | Li 2026 (LIMBO) |
| C7 | reflection after tool errors | prompt | Shinn et al. 2023 |
| C8 | log-based rollback + compensation on failure, then re-run | harness | RAC / SagaLLM |
| **S** | **Settle**: durable intent journal → op-id tag in contract field → resolve unknowns by tag after lag → reconciliation horizon H → targeted compensation of proven surplus; safe abstention where not attributable | harness | this paper |
| S−j | Settle without journal (intent kept in memory) | ablation | P6 |
| S−t | Settle with content matching instead of tags | ablation | P4 |
| S−h | Settle verifying once immediately (no horizon) | ablation | P2 |
| S−c | Settle flagging surplus but not compensating | ablation | P2 |
| G+w | guard + waiting the same total time as Settle (matched latency) | control | — |
| O | outcome oracle: sees ground truth including in-flight requests | bound | — |

**Matched budgets.**
- LLM conditions: same model, same max turns and tool calls per episode.
- Harness conditions: same number of service calls allowed for recovery.
- Wall-clock is reported, never capped differently between conditions. G+w equalizes waiting.

**Intent identity for LLM agents.** Settle binds an op-id to a logical intent using the tool's declared *intent fields* (for example recipient + subject for mail, project + title for an issue). A re-phrased re-issue with the same intent fields maps to the same op-id. Re-issues that escape this mapping are counted as a failure mode, not hidden.

## 6. Ground truth and grading (code only)

- **Effect ledger, independent of the agent and harness:**
  - PostgreSQL: AFTER INSERT/DELETE triggers into a grader-only schema.
  - Gitea: webhooks for issue/comment create and delete, sent to a ledger receiver.
  - Mailpit: every captured message (compensation cannot delete mail).
  - Redis: grader-side `MONITOR` log.
  - TigerBeetle: immutable transfer history.
  - SeaweedFS: bucket listing plus filer event log **[pilot]**.
- **Final state at H** is read directly from each service. It is compared to the task spec and to a snapshot of other actors' records, to detect collateral damage.
- Graders run in a separate process with separate credentials. No agent or harness code imports them.

## 7. Metrics

- **Primary: residual inconsistency at H.** The episode's final standing state ≠ spec. That covers any required effect missing, any surplus effect standing, or any other actor's effect neutralized.
- **Secondary:**
  - duplicate executions, including compensated ones (comparable to LIMBO);
  - irreversible duplicates;
  - duplicate exposure time;
  - missing effects;
  - collateral damage;
  - time to all required effects;
  - unknown-outcome misclassification rate;
  - honest reporting (no "completed" claim when the state is wrong);
  - abstentions;
  - tool calls, tokens, US$ and wall-clock.

## 8. Predictions (Table P) and hypotheses

Each cell below is a falsifiable prediction derived from `05_theory.md`. Confirmed and refuted cells are both reported.

| # | Cell | Prediction | Source |
|---|---|---|---|
| P-K | K writes, all faults incl. crash | S = C3 = C4(with key) ≈ 0 duplicates; C3 without journal fails only in crash worlds | P1 |
| P-A-exact | A-reversible, exact read, late_fixed | S ≈ 0 residual; S−h fails in late worlds; G+w ≈ S on consistency but slower time-to-effect; C0/C2/C4/C5/C6 > 0 | P2 |
| P-A-tail | A-reversible, late_tail | S residual ≈ P(δ > H − t₀), shrinking with H; G+w residual ≈ P(δ > W) with duplicates | P2 corollary |
| P-A-crash | A-reversible, crash_after/before | S ≈ 0; S−j and C4 (Temporal) duplicate in crash_after | P6 |
| P-irr | A-irreversible (mail) | S duplicates ≈ P(δ > Δ_assumed); no method has zero duplicates AND full completion under late_tail | P3 |
| P-look | look-alike variant | C5, C6, S−t misclassify ∝ look-alike rate; content-based compensation causes collateral damage; S unaffected | P4 |
| P-agg-ex | U, aggregate-exclusive | S converges via delta; C5/C6 cannot verify | P5 |
| P-agg-con | U, aggregate-concurrent | every method fails one of {complete, consistent, honest}; S abstains (honest) | P5 |

Hypotheses for the frozen protocol, to be finalized after the pilot:

- **H1.** Pooled over A-reversible ambiguous worlds, including crash and look-alike variants, S has residual inconsistency ≤ 5%. It is ≥ 15 pp below the best non-oracle baseline, paired, with a cluster-aware 95% CI excluding 0.
- **H2.** Under look-alikes, content-based methods misclassify ≥ 10% of in-doubt outcomes, and tags cut this by ≥ 50% relative.
- **H3.** On K writes, S is equivalent to keys (+ journal) within ±3 pp (TOST).
- **H4.** In the irreversible and aggregate-concurrent cells, no method achieves completion, consistency and honesty together. S has the highest honest-abstention rate.
- **H5.** S's model cost is within +25% of C6's, and its extra latency is dominated by H.
- **H6.** Driver invariance: the ranking S < best baseline on residual inconsistency holds for every driver (scripted and each LLM).

## 9. Statistics

- **Unit.** An episode = (template, instance, focal write, fault mode, read variant, condition, driver, repeat).
- **Pairing and repeats.** Identical worlds across conditions give paired analyses. Late-tail delays and look-alike times are seeded per world. LLM episodes are repeated 3× (scripted episodes are repeated only where timing is random).
- **Intervals.** Cluster bootstrap by template × instance for rates and differences. A mixed-effects logistic model (random intercepts for template and instance) is the confirmatory test for H1. Exact McNemar is used for paired binary outcomes, with Holm correction within families. TOST is used for H3.
- **Power.** Planned from the pilot's variance; the target is a minimum detectable effect of 5 pp on H1.

## 10. Stage-3 pilot (dev split only)

1. **Environment validation (free, scripted).** For every fault × service, run 20 trials and confirm the hidden outcome from the ledger:
   - the error/timeout text in each pair;
   - that late commits really land after the client gives up;
   - tag fidelity;
   - ledger completeness.
2. **Scripted grid (free).** Every harness condition × dev tasks × fault modes × read variants. This debugs the harness and checks Table P with zero model cost.
3. **LLM pilot (paid, OpenAI only, hard cap $6).** `gpt-5.6-luna` on about 60 dev episodes across conditions C0, C5, C6, C7, S, plus about 20 episodes each for `gpt-5.4-mini`, `gpt-5.4-nano` and `gpt-4.1-mini` to check tool-calling reliability and cost. Measure tokens, US$, wall-clock and model-specific failure modes. Output: measured cost per episode per model, and a full-study estimate with options for approval.
