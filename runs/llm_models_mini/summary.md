# Grid summary: llm_models_mini

episodes: 8 (finished 8) · errors: 0 · ambiguous-world episodes: 8

### All worlds, by condition

| group | n | inconsistent % | episodes with duplicate % | irreversible dup % | missing % | collateral % | overclaim % | mean agent s |
|---|---|---|---|---|---|---|---|---|
| C0 | 4 | 100.0 | 100.0 | 0.0 | 0.0 | 0.0 | 50.0 | 12.8 |
| S | 4 | 0.0 | 50.0 | 0.0 | 0.0 | 0.0 | 0.0 | 18.2 |

### Fault-free worlds (sanity: all should be 0)

| group | n | inconsistent % | episodes with duplicate % | irreversible dup % | missing % | collateral % | overclaim % | mean agent s |
|---|---|---|---|---|---|---|---|---|

### Ambiguous worlds, by condition

| group | n | inconsistent % | episodes with duplicate % | irreversible dup % | missing % | collateral % | overclaim % | mean agent s |
|---|---|---|---|---|---|---|---|---|
| C0 | 4 | 100.0 | 100.0 | 0.0 | 0.0 | 0.0 | 50.0 | 12.8 |
| S | 4 | 0.0 | 50.0 | 0.0 | 0.0 | 0.0 | 0.0 | 18.2 |

### Ambiguous worlds by focal contract (class, reversibility) and condition

| group | n | inconsistent % | episodes with duplicate % | irreversible dup % | missing % | collateral % | overclaim % | mean agent s |
|---|---|---|---|---|---|---|---|---|
| ('A', 'targeted', 'C0') | 4 | 100.0 | 100.0 | 0.0 | 0.0 | 0.0 | 50.0 | 12.8 |
| ('A', 'targeted', 'S') | 4 | 0.0 | 50.0 | 0.0 | 0.0 | 0.0 | 0.0 | 18.2 |

### Ambiguous worlds by mode and condition

| group | n | inconsistent % | episodes with duplicate % | irreversible dup % | missing % | collateral % | overclaim % | mean agent s |
|---|---|---|---|---|---|---|---|---|
| ('late', 'C0') | 2 | 100.0 | 100.0 | 0.0 | 0.0 | 0.0 | 50.0 | 14.7 |
| ('late', 'S') | 2 | 0.0 | 100.0 | 0.0 | 0.0 | 0.0 | 0.0 | 26.2 |
| ('lost_ack', 'C0') | 2 | 100.0 | 100.0 | 0.0 | 0.0 | 0.0 | 50.0 | 10.8 |
| ('lost_ack', 'S') | 2 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 10.1 |

### Read-model variants by condition

| group | n | inconsistent % | episodes with duplicate % | irreversible dup % | missing % | collateral % | overclaim % | mean agent s |
|---|---|---|---|---|---|---|---|---|

### LLM episodes: cost and behaviour

| driver, condition | n | US$ total | US$/episode | paid calls | cached calls | turns/ep | tool calls/ep | input tok/ep | output tok/ep (reasoning) | no finish % | claimed completed % |
|---|---|---|---|---|---|---|---|---|---|---|---|
| ('llm:gpt-5.4-mini', 'C0') | 4 | 0.0207 | 0.00518 | 24 | 2 | 6.5 | 6.5 | 5586 | 302 (0) | 0.0 | 100.0 |
| ('llm:gpt-5.4-mini', 'S') | 4 | 0.0140 | 0.00351 | 17 | 3 | 5.0 | 5.0 | 4046 | 223 (0) | 0.0 | 100.0 |

