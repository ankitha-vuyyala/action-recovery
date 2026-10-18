# Grid summary: llm_hardcheck

episodes: 28 (finished 28) · errors: 0 · ambiguous-world episodes: 28

### All worlds, by condition

| group | n | inconsistent % | episodes with duplicate % | irreversible dup % | missing % | collateral % | overclaim % | mean agent s |
|---|---|---|---|---|---|---|---|---|
| C0 | 14 | 35.7 | 21.4 | 0.0 | 14.3 | 0.0 | 21.4 | 17.2 |
| S | 14 | 7.1 | 21.4 | 0.0 | 0.0 | 0.0 | 7.1 | 18.0 |

### Fault-free worlds (sanity: all should be 0)

| group | n | inconsistent % | episodes with duplicate % | irreversible dup % | missing % | collateral % | overclaim % | mean agent s |
|---|---|---|---|---|---|---|---|---|

### Ambiguous worlds, by condition

| group | n | inconsistent % | episodes with duplicate % | irreversible dup % | missing % | collateral % | overclaim % | mean agent s |
|---|---|---|---|---|---|---|---|---|
| C0 | 14 | 35.7 | 21.4 | 0.0 | 14.3 | 0.0 | 21.4 | 17.2 |
| S | 14 | 7.1 | 21.4 | 0.0 | 0.0 | 0.0 | 7.1 | 18.0 |

### Ambiguous worlds by focal contract (class, reversibility) and condition

| group | n | inconsistent % | episodes with duplicate % | irreversible dup % | missing % | collateral % | overclaim % | mean agent s |
|---|---|---|---|---|---|---|---|---|
| ('A', 'targeted', 'C0') | 10 | 40.0 | 20.0 | 0.0 | 20.0 | 0.0 | 20.0 | 20.3 |
| ('A', 'targeted', 'S') | 10 | 0.0 | 20.0 | 0.0 | 0.0 | 0.0 | 0.0 | 21.7 |
| ('U', 'fungible', 'C0') | 4 | 25.0 | 25.0 | 0.0 | 0.0 | 0.0 | 25.0 | 9.4 |
| ('U', 'fungible', 'S') | 4 | 25.0 | 25.0 | 0.0 | 0.0 | 0.0 | 25.0 | 8.7 |

### Ambiguous worlds by mode and condition

| group | n | inconsistent % | episodes with duplicate % | irreversible dup % | missing % | collateral % | overclaim % | mean agent s |
|---|---|---|---|---|---|---|---|---|
| ('crash_after', 'C0') | 3 | 100.0 | 100.0 | 0.0 | 0.0 | 0.0 | 100.0 | 11.1 |
| ('crash_after', 'S') | 3 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 11.4 |
| ('late_tail', 'C0') | 3 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 23.2 |
| ('late_tail', 'S') | 3 | 33.3 | 100.0 | 0.0 | 0.0 | 0.0 | 33.3 | 26.8 |
| ('lost_ack', 'C0') | 8 | 25.0 | 0.0 | 0.0 | 25.0 | 0.0 | 0.0 | 17.1 |
| ('lost_ack', 'S') | 8 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 17.2 |

### Read-model variants by condition

| group | n | inconsistent % | episodes with duplicate % | irreversible dup % | missing % | collateral % | overclaim % | mean agent s |
|---|---|---|---|---|---|---|---|---|
| ('agg_shared', 'C0') | 1 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 10.9 |
| ('agg_shared', 'S') | 1 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 3.7 |
| ('lagged', 'C0') | 2 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 15.2 |
| ('lagged', 'S') | 2 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 22.0 |
| ('lookalike', 'C0') | 2 | 100.0 | 0.0 | 0.0 | 100.0 | 0.0 | 0.0 | 27.7 |
| ('lookalike', 'S') | 2 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 25.0 |

### LLM episodes: cost and behaviour

| driver, condition | n | US$ total | US$/episode | paid calls | cached calls | turns/ep | tool calls/ep | input tok/ep | output tok/ep (reasoning) | no finish % | claimed completed % |
|---|---|---|---|---|---|---|---|---|---|---|---|
| ('llm:gpt-5.6-luna', 'C0') | 14 | 0.0124 | 0.00089 | 77 | 81 | 11.3 | 11.3 | 11927 | 589 (229) | 0.0 | 78.6 |
| ('llm:gpt-5.6-luna', 'S') | 14 | 0.0109 | 0.00078 | 71 | 66 | 9.8 | 9.8 | 10160 | 486 (165) | 0.0 | 92.9 |

