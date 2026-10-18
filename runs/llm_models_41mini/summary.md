# Grid summary: llm_models_41mini

episodes: 8 (finished 8) · errors: 0 · ambiguous-world episodes: 8

### All worlds, by condition

| group | n | inconsistent % | episodes with duplicate % | irreversible dup % | missing % | collateral % | overclaim % | mean agent s |
|---|---|---|---|---|---|---|---|---|
| C0 | 4 | 75.0 | 100.0 | 0.0 | 0.0 | 0.0 | 75.0 | 16.0 |
| S | 4 | 0.0 | 50.0 | 0.0 | 0.0 | 0.0 | 0.0 | 19.2 |

### Fault-free worlds (sanity: all should be 0)

| group | n | inconsistent % | episodes with duplicate % | irreversible dup % | missing % | collateral % | overclaim % | mean agent s |
|---|---|---|---|---|---|---|---|---|

### Ambiguous worlds, by condition

| group | n | inconsistent % | episodes with duplicate % | irreversible dup % | missing % | collateral % | overclaim % | mean agent s |
|---|---|---|---|---|---|---|---|---|
| C0 | 4 | 75.0 | 100.0 | 0.0 | 0.0 | 0.0 | 75.0 | 16.0 |
| S | 4 | 0.0 | 50.0 | 0.0 | 0.0 | 0.0 | 0.0 | 19.2 |

### Ambiguous worlds by focal contract (class, reversibility) and condition

| group | n | inconsistent % | episodes with duplicate % | irreversible dup % | missing % | collateral % | overclaim % | mean agent s |
|---|---|---|---|---|---|---|---|---|
| ('A', 'targeted', 'C0') | 4 | 75.0 | 100.0 | 0.0 | 0.0 | 0.0 | 75.0 | 16.0 |
| ('A', 'targeted', 'S') | 4 | 0.0 | 50.0 | 0.0 | 0.0 | 0.0 | 0.0 | 19.2 |

### Ambiguous worlds by mode and condition

| group | n | inconsistent % | episodes with duplicate % | irreversible dup % | missing % | collateral % | overclaim % | mean agent s |
|---|---|---|---|---|---|---|---|---|
| ('late', 'C0') | 2 | 50.0 | 100.0 | 0.0 | 0.0 | 0.0 | 50.0 | 16.3 |
| ('late', 'S') | 2 | 0.0 | 100.0 | 0.0 | 0.0 | 0.0 | 0.0 | 26.6 |
| ('lost_ack', 'C0') | 2 | 100.0 | 100.0 | 0.0 | 0.0 | 0.0 | 100.0 | 15.8 |
| ('lost_ack', 'S') | 2 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 11.9 |

### Read-model variants by condition

| group | n | inconsistent % | episodes with duplicate % | irreversible dup % | missing % | collateral % | overclaim % | mean agent s |
|---|---|---|---|---|---|---|---|---|

### LLM episodes: cost and behaviour

| driver, condition | n | US$ total | US$/episode | paid calls | cached calls | turns/ep | tool calls/ep | input tok/ep | output tok/ep (reasoning) | no finish % | claimed completed % |
|---|---|---|---|---|---|---|---|---|---|---|---|
| ('llm:gpt-4.1-mini', 'C0') | 4 | 0.0108 | 0.00271 | 28 | 3 | 7.8 | 7.8 | 6173 | 290 (0) | 0.0 | 100.0 |
| ('llm:gpt-4.1-mini', 'S') | 4 | 0.0064 | 0.00161 | 18 | 4 | 5.5 | 5.5 | 3930 | 208 (0) | 0.0 | 100.0 |

