# Grid summary: llm_models_nano

episodes: 8 (finished 8) · errors: 0 · ambiguous-world episodes: 8

### All worlds, by condition

| group | n | inconsistent % | episodes with duplicate % | irreversible dup % | missing % | collateral % | overclaim % | mean agent s |
|---|---|---|---|---|---|---|---|---|
| C0 | 4 | 100.0 | 100.0 | 0.0 | 0.0 | 0.0 | 75.0 | 12.9 |
| S | 4 | 0.0 | 50.0 | 0.0 | 0.0 | 0.0 | 0.0 | 18.6 |

### Fault-free worlds (sanity: all should be 0)

| group | n | inconsistent % | episodes with duplicate % | irreversible dup % | missing % | collateral % | overclaim % | mean agent s |
|---|---|---|---|---|---|---|---|---|

### Ambiguous worlds, by condition

| group | n | inconsistent % | episodes with duplicate % | irreversible dup % | missing % | collateral % | overclaim % | mean agent s |
|---|---|---|---|---|---|---|---|---|
| C0 | 4 | 100.0 | 100.0 | 0.0 | 0.0 | 0.0 | 75.0 | 12.9 |
| S | 4 | 0.0 | 50.0 | 0.0 | 0.0 | 0.0 | 0.0 | 18.6 |

### Ambiguous worlds by focal contract (class, reversibility) and condition

| group | n | inconsistent % | episodes with duplicate % | irreversible dup % | missing % | collateral % | overclaim % | mean agent s |
|---|---|---|---|---|---|---|---|---|
| ('A', 'targeted', 'C0') | 4 | 100.0 | 100.0 | 0.0 | 0.0 | 0.0 | 75.0 | 12.9 |
| ('A', 'targeted', 'S') | 4 | 0.0 | 50.0 | 0.0 | 0.0 | 0.0 | 0.0 | 18.6 |

### Ambiguous worlds by mode and condition

| group | n | inconsistent % | episodes with duplicate % | irreversible dup % | missing % | collateral % | overclaim % | mean agent s |
|---|---|---|---|---|---|---|---|---|
| ('late', 'C0') | 2 | 100.0 | 100.0 | 0.0 | 0.0 | 0.0 | 50.0 | 13.9 |
| ('late', 'S') | 2 | 0.0 | 100.0 | 0.0 | 0.0 | 0.0 | 0.0 | 27.0 |
| ('lost_ack', 'C0') | 2 | 100.0 | 100.0 | 0.0 | 0.0 | 0.0 | 100.0 | 11.8 |
| ('lost_ack', 'S') | 2 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 10.1 |

### Read-model variants by condition

| group | n | inconsistent % | episodes with duplicate % | irreversible dup % | missing % | collateral % | overclaim % | mean agent s |
|---|---|---|---|---|---|---|---|---|

### LLM episodes: cost and behaviour

| driver, condition | n | US$ total | US$/episode | paid calls | cached calls | turns/ep | tool calls/ep | input tok/ep | output tok/ep (reasoning) | no finish % | claimed completed % |
|---|---|---|---|---|---|---|---|---|---|---|---|
| ('llm:gpt-5.4-nano', 'C0') | 4 | 0.0053 | 0.00132 | 23 | 3 | 6.5 | 6.5 | 5535 | 286 (0) | 0.0 | 100.0 |
| ('llm:gpt-5.4-nano', 'S') | 4 | 0.0038 | 0.00096 | 17 | 5 | 5.5 | 5.5 | 4467 | 232 (0) | 0.0 | 100.0 |

