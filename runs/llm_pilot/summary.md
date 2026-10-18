# Grid summary: llm_pilot

episodes: 60 (finished 60) · errors: 0 · ambiguous-world episodes: 45

### All worlds, by condition

| group | n | inconsistent % | episodes with duplicate % | irreversible dup % | missing % | collateral % | overclaim % | mean agent s |
|---|---|---|---|---|---|---|---|---|
| C0 | 12 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 22.3 |
| C5 | 12 | 25.0 | 25.0 | 0.0 | 0.0 | 0.0 | 25.0 | 13.2 |
| C6 | 12 | 16.7 | 0.0 | 0.0 | 16.7 | 0.0 | 0.0 | 19.0 |
| C7 | 12 | 8.3 | 16.7 | 0.0 | 0.0 | 0.0 | 0.0 | 19.1 |
| S | 12 | 0.0 | 25.0 | 0.0 | 0.0 | 0.0 | 0.0 | 18.9 |

### Fault-free worlds (sanity: all should be 0)

| group | n | inconsistent % | episodes with duplicate % | irreversible dup % | missing % | collateral % | overclaim % | mean agent s |
|---|---|---|---|---|---|---|---|---|
| C0 | 3 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 17.8 |
| C5 | 3 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 11.4 |
| C6 | 3 | 33.3 | 0.0 | 0.0 | 33.3 | 0.0 | 0.0 | 6.3 |
| C7 | 3 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 10.7 |
| S | 3 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 10.9 |

### Ambiguous worlds, by condition

| group | n | inconsistent % | episodes with duplicate % | irreversible dup % | missing % | collateral % | overclaim % | mean agent s |
|---|---|---|---|---|---|---|---|---|
| C0 | 9 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 23.8 |
| C5 | 9 | 33.3 | 33.3 | 0.0 | 0.0 | 0.0 | 33.3 | 13.8 |
| C6 | 9 | 11.1 | 0.0 | 0.0 | 11.1 | 0.0 | 0.0 | 23.2 |
| C7 | 9 | 11.1 | 22.2 | 0.0 | 0.0 | 0.0 | 0.0 | 21.9 |
| S | 9 | 0.0 | 33.3 | 0.0 | 0.0 | 0.0 | 0.0 | 21.5 |

### Ambiguous worlds by focal contract (class, reversibility) and condition

| group | n | inconsistent % | episodes with duplicate % | irreversible dup % | missing % | collateral % | overclaim % | mean agent s |
|---|---|---|---|---|---|---|---|---|
| ('A', 'targeted', 'C0') | 6 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 28.2 |
| ('A', 'targeted', 'C5') | 6 | 33.3 | 33.3 | 0.0 | 0.0 | 0.0 | 33.3 | 17.5 |
| ('A', 'targeted', 'C6') | 6 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 28.0 |
| ('A', 'targeted', 'C7') | 6 | 0.0 | 16.7 | 0.0 | 0.0 | 0.0 | 0.0 | 24.1 |
| ('A', 'targeted', 'S') | 6 | 0.0 | 33.3 | 0.0 | 0.0 | 0.0 | 0.0 | 23.2 |
| ('U', 'fungible', 'C0') | 3 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 15.1 |
| ('U', 'fungible', 'C5') | 3 | 33.3 | 33.3 | 0.0 | 0.0 | 0.0 | 33.3 | 6.5 |
| ('U', 'fungible', 'C6') | 3 | 33.3 | 0.0 | 0.0 | 33.3 | 0.0 | 0.0 | 13.7 |
| ('U', 'fungible', 'C7') | 3 | 33.3 | 33.3 | 0.0 | 0.0 | 0.0 | 0.0 | 17.5 |
| ('U', 'fungible', 'S') | 3 | 0.0 | 33.3 | 0.0 | 0.0 | 0.0 | 0.0 | 18.3 |

### Ambiguous worlds by mode and condition

| group | n | inconsistent % | episodes with duplicate % | irreversible dup % | missing % | collateral % | overclaim % | mean agent s |
|---|---|---|---|---|---|---|---|---|
| ('late', 'C0') | 3 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 32.6 |
| ('late', 'C5') | 3 | 100.0 | 100.0 | 0.0 | 0.0 | 0.0 | 100.0 | 15.1 |
| ('late', 'C6') | 3 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 33.0 |
| ('late', 'C7') | 3 | 33.3 | 66.7 | 0.0 | 0.0 | 0.0 | 0.0 | 28.8 |
| ('late', 'S') | 3 | 0.0 | 100.0 | 0.0 | 0.0 | 0.0 | 0.0 | 26.2 |
| ('lost_ack', 'C0') | 3 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 18.6 |
| ('lost_ack', 'C5') | 3 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 15.2 |
| ('lost_ack', 'C6') | 3 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 17.6 |
| ('lost_ack', 'C7') | 3 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 17.1 |
| ('lost_ack', 'S') | 3 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 16.2 |
| ('not_exec_err', 'C0') | 3 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 20.3 |
| ('not_exec_err', 'C5') | 3 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 11.3 |
| ('not_exec_err', 'C6') | 3 | 33.3 | 0.0 | 0.0 | 33.3 | 0.0 | 0.0 | 18.9 |
| ('not_exec_err', 'C7') | 3 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 19.8 |
| ('not_exec_err', 'S') | 3 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 22.2 |

### Read-model variants by condition

| group | n | inconsistent % | episodes with duplicate % | irreversible dup % | missing % | collateral % | overclaim % | mean agent s |
|---|---|---|---|---|---|---|---|---|

### LLM episodes: cost and behaviour

| driver, condition | n | US$ total | US$/episode | paid calls | cached calls | turns/ep | tool calls/ep | input tok/ep | output tok/ep (reasoning) | no finish % | claimed completed % |
|---|---|---|---|---|---|---|---|---|---|---|---|
| ('llm:gpt-5.6-luna', 'C0') | 12 | 0.0173 | 0.00144 | 97 | 31 | 10.7 | 10.7 | 11008 | 590 (242) | 0.0 | 75.0 |
| ('llm:gpt-5.6-luna', 'C5') | 12 | 0.0099 | 0.00083 | 58 | 51 | 9.1 | 9.1 | 8779 | 423 (122) | 0.0 | 100.0 |
| ('llm:gpt-5.6-luna', 'C6') | 12 | 0.0128 | 0.00107 | 82 | 43 | 10.4 | 10.4 | 10972 | 519 (184) | 0.0 | 75.0 |
| ('llm:gpt-5.6-luna', 'C7') | 12 | 0.0141 | 0.00117 | 89 | 44 | 11.1 | 11.1 | 11919 | 595 (234) | 0.0 | 83.3 |
| ('llm:gpt-5.6-luna', 'S') | 12 | 0.0095 | 0.00079 | 59 | 51 | 9.2 | 9.2 | 8980 | 420 (114) | 0.0 | 100.0 |

