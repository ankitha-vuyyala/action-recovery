# Grid summary: dev_smoke

episodes: 156 · errors: 0 · ambiguous-world episodes: 116

### All worlds, by condition

| group | n | inconsistent % | episodes with duplicate % | irreversible dup % | missing % | collateral % | overclaim % | mean agent s |
|---|---|---|---|---|---|---|---|---|
| C0 | 39 | 74.4 | 74.4 | 0.0 | 0.0 | 0.0 | 74.4 | 2.2 |
| C3 | 39 | 64.1 | 64.1 | 0.0 | 0.0 | 0.0 | 64.1 | 2.2 |
| C6 | 39 | 41.0 | 41.0 | 0.0 | 0.0 | 0.0 | 41.0 | 2.2 |
| S | 39 | 0.0 | 17.9 | 0.0 | 0.0 | 0.0 | 0.0 | 9.7 |

### Fault-free worlds (sanity: all should be 0)

| group | n | inconsistent % | episodes with duplicate % | irreversible dup % | missing % | collateral % | overclaim % | mean agent s |
|---|---|---|---|---|---|---|---|---|
| C0 | 10 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.9 |
| C3 | 10 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.9 |
| C6 | 10 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.9 |
| S | 10 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 1.5 |

### Ambiguous worlds, by condition

| group | n | inconsistent % | episodes with duplicate % | irreversible dup % | missing % | collateral % | overclaim % | mean agent s |
|---|---|---|---|---|---|---|---|---|
| C0 | 29 | 100.0 | 100.0 | 0.0 | 0.0 | 0.0 | 100.0 | 2.7 |
| C3 | 29 | 86.2 | 86.2 | 0.0 | 0.0 | 0.0 | 86.2 | 2.7 |
| C6 | 29 | 55.2 | 55.2 | 0.0 | 0.0 | 0.0 | 55.2 | 2.7 |
| S | 29 | 0.0 | 24.1 | 0.0 | 0.0 | 0.0 | 0.0 | 12.5 |

### Ambiguous worlds by focal contract (class, reversibility) and condition

| group | n | inconsistent % | episodes with duplicate % | irreversible dup % | missing % | collateral % | overclaim % | mean agent s |
|---|---|---|---|---|---|---|---|---|
| ('A', 'targeted', 'C0') | 17 | 100.0 | 100.0 | 0.0 | 0.0 | 0.0 | 100.0 | 2.2 |
| ('A', 'targeted', 'C3') | 17 | 100.0 | 100.0 | 0.0 | 0.0 | 0.0 | 100.0 | 2.2 |
| ('A', 'targeted', 'C6') | 17 | 70.6 | 70.6 | 0.0 | 0.0 | 0.0 | 70.6 | 2.3 |
| ('A', 'targeted', 'S') | 17 | 0.0 | 29.4 | 0.0 | 0.0 | 0.0 | 0.0 | 10.0 |
| ('K', 'targeted', 'C0') | 6 | 100.0 | 100.0 | 0.0 | 0.0 | 0.0 | 100.0 | 4.9 |
| ('K', 'targeted', 'C3') | 6 | 33.3 | 33.3 | 0.0 | 0.0 | 0.0 | 33.3 | 4.9 |
| ('K', 'targeted', 'C6') | 6 | 33.3 | 33.3 | 0.0 | 0.0 | 0.0 | 33.3 | 4.9 |
| ('K', 'targeted', 'S') | 6 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 23.7 |
| ('U', 'fungible', 'C0') | 6 | 100.0 | 100.0 | 0.0 | 0.0 | 0.0 | 100.0 | 1.8 |
| ('U', 'fungible', 'C3') | 6 | 100.0 | 100.0 | 0.0 | 0.0 | 0.0 | 100.0 | 1.8 |
| ('U', 'fungible', 'C6') | 6 | 33.3 | 33.3 | 0.0 | 0.0 | 0.0 | 33.3 | 1.7 |
| ('U', 'fungible', 'S') | 6 | 0.0 | 33.3 | 0.0 | 0.0 | 0.0 | 0.0 | 8.6 |

### Ambiguous worlds by mode and condition

| group | n | inconsistent % | episodes with duplicate % | irreversible dup % | missing % | collateral % | overclaim % | mean agent s |
|---|---|---|---|---|---|---|---|---|
| ('crash_after', 'C0') | 10 | 100.0 | 100.0 | 0.0 | 0.0 | 0.0 | 100.0 | 0.7 |
| ('crash_after', 'C3') | 10 | 100.0 | 100.0 | 0.0 | 0.0 | 0.0 | 100.0 | 0.6 |
| ('crash_after', 'C6') | 10 | 100.0 | 100.0 | 0.0 | 0.0 | 0.0 | 100.0 | 0.7 |
| ('crash_after', 'S') | 10 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 4.9 |
| ('late', 'C0') | 9 | 100.0 | 100.0 | 0.0 | 0.0 | 0.0 | 100.0 | 5.4 |
| ('late', 'C3') | 9 | 77.8 | 77.8 | 0.0 | 0.0 | 0.0 | 77.8 | 5.4 |
| ('late', 'C6') | 9 | 55.6 | 55.6 | 0.0 | 0.0 | 0.0 | 55.6 | 5.5 |
| ('late', 'S') | 9 | 0.0 | 77.8 | 0.0 | 0.0 | 0.0 | 0.0 | 25.7 |
| ('lost_ack', 'C0') | 9 | 100.0 | 100.0 | 0.0 | 0.0 | 0.0 | 100.0 | 2.4 |
| ('lost_ack', 'C3') | 9 | 77.8 | 77.8 | 0.0 | 0.0 | 0.0 | 77.8 | 2.4 |
| ('lost_ack', 'C6') | 9 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 2.4 |
| ('lost_ack', 'S') | 9 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 7.0 |
| ('partial', 'C0') | 1 | 100.0 | 100.0 | 0.0 | 0.0 | 0.0 | 100.0 | 0.5 |
| ('partial', 'C3') | 1 | 100.0 | 100.0 | 0.0 | 0.0 | 0.0 | 100.0 | 0.5 |
| ('partial', 'C6') | 1 | 100.0 | 100.0 | 0.0 | 0.0 | 0.0 | 100.0 | 0.7 |
| ('partial', 'S') | 1 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 20.7 |

### Read-model variants by condition

| group | n | inconsistent % | episodes with duplicate % | irreversible dup % | missing % | collateral % | overclaim % | mean agent s |
|---|---|---|---|---|---|---|---|---|

