# Experimental design {#sec:setup}

The design is a paired factorial. Every *world* is replayed under every recovery condition of a driver. A world fixes the task instance, the focal write that receives the fault, the fault mode and the read model the agent sees, so all comparisons between conditions are within-world. The study was pre-registered internally: hypotheses, analysis code, task definitions, prompts and the SHA-256 hashes of all source files were frozen before the first test episode, and the test presets refuse to run if any hashed file changes (@sec:prereg). The freeze is recorded in the released repository rather than with a third-party registry.

## Services, tools and contracts {#sec:services}

All services run unmodified in containers on one workstation: PostgreSQL 16 for records and stock levels; Gitea 1.24 [@sw_gitea] for issues and comments, with its real asynchronous search indexer; Mailpit [@sw_mailpit] for SMTP with a search API; Redis 7 streams and counters [@doc_redis_streams]; SeaweedFS [@sw_seaweedfs] as an S3 object store; and TigerBeetle [@doc_tigerbeetle] for ledger transfers. The agent reaches them through thin tool adapters (@tbl:tools), each a few lines over the service's own API. Where Settle writes a tag, it uses a field of the kind that the census found in real APIs: a body line as in GitHub issues, a mail header as in Gmail, a reference column as in Salesforce's external ids, a stream field as in Kafka headers. The stack covers every row of the achievability map.

| Tool | Service | Class | Reversible | Tag field or key | Read paths |
|---|---|---|---|---|---|
| create issue | Gitea | A | targeted (delete) | `op-id:` line in body | list + body (exact); search (lagged) |
| add comment | Gitea | A | targeted | tag line in body | comment list |
| send e-mail | Mailpit SMTP | A | none | client `Message-ID` | search by header or content |
| send bulk e-mail | Mailpit SMTP | C (content only) | none | none | search by content |
| insert record(s) | PostgreSQL | A | targeted | `reference` column | select |
| append event | Redis stream | A | targeted (XDEL) | `op_id` field | range scan |
| adjust stock | PostgreSQL | U | fungible (inverse) | none | sum only |
| increment counter | Redis | U | fungible (decrement) | none | value only |
| create transfer | TigerBeetle | K | targeted (reversal) | 128-bit transfer id | lookup by id |
| put object | SeaweedFS S3 | K | targeted | key + `If-None-Match: *` | head |

Table: Tool contracts. Class K has a native key, class A is key-less but taggable, class U exposes only an aggregate, and class C can be found only by content. {#tbl:tools}

**Tasks.** Eight task templates (@tbl:tasks) define short workflows of two to four writes across services, one of which (T5) inserts a batch of six records. Each comes with an exact specification of the final state: every write must leave exactly one standing effect, and every aggregate must change by exactly the required amount. The development split consists of five templates on instance 0, and every method parameter was set on it. The test split uses all eight templates on fresh instances 100–102. Three templates (T3, T6, T8) were not used during development; for these, only a fault-free and error check of the harness was run, on an instance outside the test set.

| Template | Workflow | Writes (class) | Stresses |
|---|---|---|---|
| T1 | open an incident | issue (A), event (A), page e-mail (A, irreversible), record (A) | mixed reversibility |
| T2 | pay out a batch | 2 transfers (K), record (A), e-mail (A, irr.) | keyed and key-less in one task |
| T3 | ship a release | object (K), issue (A), comment (A), bulk e-mail (C, irr.) | content-only irreversible write |
| T4 | receive stock | 2 stock adjustments (U), counter (U), record (A) | aggregate reads |
| T5 | migrate a batch | 6 records in one non-atomic batch (A), event (A) | partial failure |
| T6 | send customer notices | 3 e-mails (A, irr.), issue (A) | irreversible-heavy |
| T7 | triage a ticket | issue (A), 2 comments (A), record (A) | dependent steps, look-alike prone |
| T8 | refund a customer | transfer (K), record (A), e-mail (A, irr.) | keyed payment + notification |

Table: Task templates. Test-only templates: T3, T6, T8. {#tbl:tasks}

## Faults and read models {#sec:faults}

**Network and process faults.** The faults are real. They are injected on the client path with Toxiproxy [@sw_toxiproxy], through one proxy per worker, armed by a hook immediately before the focal write's bytes are sent. In *lost_ack*, the request is delivered and committed and the reply is cut. In *not_exec_err*, the connection is cut before the request is delivered, and the agent sees the same error as in lost_ack. In *held*, the reply is withheld past the tool deadline after the request has committed; in *not_exec_to*, the request is held upstream and dropped, and the agent sees the same timeout. In *late*, the request reaches the service 12 s after dispatch, long after the 4 s tool deadline has expired. *late_tail* is like late but draws the delay per world from a log-uniform distribution on 5–120 s, so that in part of the worlds it exceeds Settle's assumed bound of 20 s. In *partial*, a non-atomic batch is cut after its third row. In *redelivery*, the transport delivers the same request twice. In *crash_after* and *crash_before*, the agent process exits (`os._exit`) right after or right before the focal dispatch and is restarted from its checkpoint.

Each pair of modes (lost_ack and not_exec_err, held and not_exec_to, crash_after and crash_before) gives the agent the same observation with opposite hidden outcomes. Transport errors are normalised to one exception type and message, so the pairs are observation-equivalent by construction. The two network pairs make the design symmetric in what it penalises, though not in size (held occurs in 42 of the H1 worlds and not_exec_to in 96; @tbl:h1modes): a method that re-issues too eagerly fails in one mode of each pair, and a method that re-issues too reluctantly fails in the other. The crash pair is not symmetric in this sense. After a crash before dispatch, the driver's checkpoint re-issues the step in every condition, so crash_before ends consistent everywhere, and the pair penalises only eager re-issuing. An environment validation checks on every service, from the service's own records, that each mode produces its intended hidden outcome; {{val.as_intended|int}} of {{val.trials|int}} trials did, and the exceptions are TigerBeetle's not_exec modes, whose client library retries internally (@sec:validation).

**Read models.** The read model is varied per world. Under *exact* reads the agent has the default read paths. Under *lagged* reads it can find issues only through Gitea's asynchronous search index. Under *look-alike*, a background actor creates an effect with content identical to the focal write at the moment of the fault, just before the focal request is sent, through the same service account. This is the worst case for any check by content, since no author or creation-time field separates the two records; a look-alike from another account, or from an earlier time, could be told apart by those fields. Under *shared aggregate*, a background actor adjusts the same counter or stock level.

## Conditions {#sec:conditions}

Every condition sits between the driver and the tools, and only the recovery logic differs.

- **C0 plain:** the agent's own behaviour; for the scripted driver, one immediate re-issue on error.
- **C1 never retry:** stop and report at the first failed write.
- **C2 SDK retry:** transparent client retries, three with back-off.
- **C3 idempotency keys:** a key per call, generated in memory and passed wherever the service honours one, which is common client practice [@doc_stripe].
- **C4 workflow engine:** each write is a Temporal activity with a retry policy of three attempts, and keys are derived from the durable workflow and activity ids [@doc_temporal].
- **C5 verify-before-retry:** re-issue only if a content-based postcondition fails [@mansoor2026verified].
- **C6 guard:** my re-implementation of Li's client-side guard from its published description [@li2026limbo], with automatic keys, a re-check after the documented lag, a block on repeats it cannot verify, and an uncertainty annotation in the observation.
- **Gw guard + wait:** C6, but waiting the same in-flight bound $\Delta$ as Settle. This matched-latency control shows whether waiting alone explains Settle's results.
- **C7 reflection:** after a failed tool call the model is asked to reason about the failure before acting [@shinn2023reflexion]; language-model drivers only.
- **C8 rollback:** on failure, compensate the completed steps from a log, then restart the workflow [@perera2026rac; @chang2025sagallm].
- **S Settle**, and its ablations S−j, S−t, S−h and S−c.
- **O outcome oracle:** knows the hidden outcome that the fault mode is designed to produce for the focal write, including when an in-flight request should land, and re-issues only if the write is designed never to execute. It does not compensate. It shows what perfect knowledge of the focal outcome achieves *without* compensation; it is not a lower bound for methods that compensate, and Settle does better than it where compensation matters.

Retry budgets are small and comparable. The scripted driver re-issues a failed step once, C2 retries up to three times, and the guards and Settle make at most three attempts per write. Language-model conditions share the same model, prompts, and limits of 30 turns and 40 tool calls. Wall-clock time is reported, not capped.

**Limiting bias towards my own method.** Because I designed Settle, the theory and the harness, I took several precautions against a comparison that favours Settle by construction. The predictions of the achievability map that the hypotheses test, including where Settle itself must fail, were frozen with the analysis code before the test runs. Each baseline family is represented by its strongest configuration that I could build without attribution: durable rather than in-memory keys (C4), a guard that waits as long as Settle (Gw), and an outcome oracle. Variants that *do* use the tag but lack another component are the ablations, and I report them next to the baselines so that the contribution of attribution can be separated from that of the journal, the horizon and compensation. Three of the eight test templates were not used during development. The network fault pairs penalise eager and reluctant re-issuing equally. And grading is done by code from the services' own records, independently of every recovery layer. These precautions do not remove the main limitation: the baselines are denied tags by design, so part of the comparison confirms Proposition 4 rather than testing an engineering choice. The re-implemented baselines may also differ from their authors' code in detail; I release mine and describe the behaviour of each.

## Drivers {#sec:drivers}

**Scripted driver.** The scripted driver is a deterministic agent without a model. It executes the plan in order, keeps a durable step checkpoint as agent frameworks do, re-issues a failed step once, finds earlier results by content when it needs them, and reports honestly what it believes. It isolates the effect of the recovery layer and makes the large grid possible.

**Language-model drivers.** Three OpenAI models run, each at its default reasoning setting, through the Responses API [@doc_openai_responses]: `gpt-5.6-luna`, which reasons by default; `gpt-5.4-nano`, which does not; and `gpt-4.1-mini`, which is not a reasoning model. The language-model study does not aim to rank models. It asks two questions that the scripted driver cannot answer: what a model does on its own after an ambiguous write, and whether Settle's guarantee survives an agent that rephrases writes, deletes records, waits, and crashes in the middle of a conversation. Each model receives a system instruction that describes it as an autonomous operations agent; the task goal, with the exact required strings and the sentence "Each action must take effect exactly once."; and the tools of its task, namely writes, reads, its own deletion tools, a wait tool and finish (@sec:agentif). The agent ends by calling finish with a status, a summary and a list of operations whose outcome it is unsure of. The conversation is checkpointed after every tool result. After a crash, the run resumes from the checkpoint and re-executes any pending tool call, which is the replay behaviour of common agent frameworks.

The language-model grid uses the first two writes of every template on test instance 100; the modes none, lost_ack, not_exec_err, late, late_tail and crash_after; all four read models where they apply; and conditions C0, C5, C6, C7 and S. `gpt-5.6-luna` runs two repeats and the other models one, for {{llm.n_planned|int}} planned episodes. Every model response is cached by a hash of the request, so the released cache replays every decision without an API key.

## Grading, statistics and pre-registration {#sec:grading}

**Grading.** Grading is done by code from the services' own records, read with separate credentials after quiescence: PostgreSQL audit triggers; the Redis stream's monotonic `entries-added` counter and an atomic counter-audit list; TigerBeetle's immutable transfer history; Mailpit's capture store, which no tool can delete from; and Gitea state together with a compensation log written by the harness. Background-actor effects are identified from the actor's own log. Neither agents nor recovery layers can import the grader.

**Statistics.** Rates carry cluster-bootstrap 95% intervals that resample template × instance clusters 10,000 times. Paired comparisons use the exact McNemar test with Holm correction within each hypothesis, and equivalence uses two one-sided tests through a 90% interval. Because the scripted driver is deterministic and the instances of a template differ mainly in their strings, worlds are not independent draws, and the intervals measure replication across my design grid rather than uncertainty about a population of deployments. As a sensitivity check I also resample the eight templates as clusters (@sec:h1). The rates themselves are averages over a designed grid of worlds, so I report them per fault mode and per contract cell as well as pooled. The six hypotheses, their thresholds and every analysis deviation are listed in @sec:prereg, and @sec:results reports every hypothesis, confirmed or not. Two analyses are exploratory and were not pre-registered: the API census (@sec:census) and the horizon trade-off (@sec:horizon). I label them as such wherever they appear.
