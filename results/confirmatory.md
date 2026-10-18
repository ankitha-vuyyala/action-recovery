# Confirmatory results

Scripted episodes used: 17820 (excluded unfinished: 0). LLM runs: test_llm_luna: 1340 (excluded 0), test_llm_41mini: 670 (excluded 0), test_llm_nano: 670 (excluded 0)

## H1 Settle vs best baseline (A, targeted-reversible, ambiguous)

Verdict: **confirmed**. Criteria: S rate <= 0.05; S - best <= -0.15; cluster 95% CI upper < 0; Holm p < 0.05.

| condition | n | inconsistent % | cluster 95% CI |
|---|---|---|---|
| C0 | 603 | 60.7 | [60.4, 61.0] |
| C1 | 603 | 52.4 | [49.1, 55.6] |
| C2 | 603 | 60.7 | [60.4, 61.0] |
| C3 | 603 | 60.5 | [60.1, 60.9] |
| C4 | 603 | 60.7 | [60.4, 61.0] |
| C5 | 603 | 47.8 | [46.7, 48.8] |
| C6 | 603 | 46.9 | [45.7, 48.1] |
| C8 | 603 | 62.5 | [58.2, 67.9] |
| Gw | 603 | 34.7 | [33.3, 35.9] |
| S | 603 | 3.2 | [2.2, 4.1] |
| O | 603 | 7.0 | [6.8, 7.1] |
| S-j | 603 | 10.6 | [9.5, 11.8] |
| S-t | 603 | 25.0 | [23.7, 26.2] |
| S-h | 603 | 23.2 | [22.2, 24.2] |
| S-c | 603 | 29.9 | [29.3, 30.3] |

Best baseline: Gw.

| S vs | pairs | diff pp | 95% CI | S-only | other-only | Holm p |
|---|---|---|---|---|---|---|
| C0 | 603 | -57.5 | [-58.6, -56.6] | 0 | 347 | 6.3e-104 |
| C1 | 603 | -49.3 | [-52.9, -45.5] | 17 | 314 | 1.2e-71 |
| C2 | 603 | -57.5 | [-58.6, -56.6] | 0 | 347 | 6.3e-104 |
| C3 | 603 | -57.4 | [-58.4, -56.5] | 0 | 346 | 8.4e-104 |
| C4 | 603 | -57.5 | [-58.6, -56.6] | 0 | 347 | 6.3e-104 |
| C5 | 603 | -44.6 | [-46.3, -43.1] | 0 | 269 | 8.4e-81 |
| C6 | 603 | -43.8 | [-45.4, -42.2] | 0 | 264 | 2e-79 |
| C8 | 603 | -59.4 | [-64.8, -55.0] | 3 | 361 | 2.1e-102 |
| Gw | 603 | -31.5 | [-32.5, -30.5] | 0 | 190 | 1.3e-57 |

## H2 Look-alikes

Verdict: **confirmed** (a: confirmed, b: confirmed). (a) every content method >= 0.1; (b) S <= 0.5 x each, CI upper < 0, Holm p < 0.05.

| condition | n | inconsistent % | CI | collateral % |
|---|---|---|---|---|
| C5 | 252 | 54.8 | [51.7, 57.8] | 0.0 |
| C6 | 252 | 54.8 | [51.7, 57.8] | 0.0 |
| S-t | 252 | 69.0 | [65.0, 73.1] | 0.0 |
| S | 252 | 2.4 | [0.0, 5.2] | 0.0 |
| C8 | 252 | 66.7 | [60.6, 72.1] | 14.3 |

## H3 Native keys

Verdict: **confirmed**. 90% cluster CI of S - C4 within +-0.05 (or no discordant pairs). S - C4 = 0.0 pp, 90% CI [0.0, 0.0], discordant 0/0 over 108 pairs. C3 inconsistent in crash worlds 37.5 % vs other worlds 0.0 %.

## H4 Impossibility cells

Verdict: **confirmed** (a: confirmed, b: confirmed, c: confirmed). (a) every non-oracle condition >= 0.25 inconsistent under shared aggregates; (b) S overclaim <= 0.05; (c) every condition incl. oracle has irreversible duplicates or missing effects in irreversible worlds. S overclaim: 4.9 %.

## H5 Cost and latency

Latency: **confirmed**; fault-free S - C6 1.01 s, 95% CI [0.74, 1.29]; ambiguous 15.01 s. Cost ratio per model: llm:gpt-5.6-luna: 0.84 [0.74, 0.94] -> confirmed; llm:gpt-4.1-mini: 0.87 [0.71, 0.99] -> confirmed; llm:gpt-5.4-nano: 0.91 [0.72, 1.16] -> confirmed

## Secondary: ablations in their predicted cells

ablation - S >= 0.1 in its cell with cluster 95% CI lower > 0; the difference outside the cell is reported.

| ablation | component | pairs in cell | diff in cell pp | 95% CI | diff outside pp | verdict |
|---|---|---|---|---|---|---|
| S-j | journal (P6) | 87 | 96.6 | [92.6, 100.0] | 0.0 | confirmed |
| S-h | horizon (P2) | 252 | 70.2 | [64.7, 75.5] | 0.6 | confirmed |
| S-t | tags (P4) | 462 | 36.4 | [32.3, 40.3] | 0.2 | confirmed |
| S-c | compensation (P2) | 216 | 74.5 | [65.4, 82.4] | 2.7 | confirmed |

## H6 Driver invariance (LLM agents)

Verdict: **confirmed**. per model, in hard worlds (late_tail, crash_after, look-alike or lagged reads), S below every LLM baseline: diff < 0, cluster CI upper < 0, Holm p < 0.05; easy worlds reported only.

### llm:gpt-5.6-luna: confirmed

hard worlds: C0 54.5 % (n 134), C5 64.2 % (n 134), C6 52.2 % (n 134), C7 56.7 % (n 134), S 6.0 % (n 134)

| S vs | pairs | diff pp | 95% CI | Holm p |
|---|---|---|---|---|
| C0 | 134 | -48.5 | [-57.1, -37.1] | 1.6e-17 |
| C5 | 134 | -58.2 | [-68.9, -44.6] | 2.6e-23 |
| C6 | 134 | -46.3 | [-55.9, -34.8] | 6e-17 |
| C7 | 134 | -50.7 | [-59.5, -38.7] | 2e-20 |

easy worlds: C0 12.2 % (n 90), C5 25.6 % (n 90), C6 11.1 % (n 90), C7 12.2 % (n 90), S 0.0 % (n 90)

| S vs | pairs | diff pp | 95% CI | Holm p |
|---|---|---|---|---|
| C0 | 90 | -12.2 | [-23.1, -4.2] | 0.0029 |
| C5 | 90 | -25.6 | [-34.4, -15.6] | 9.5e-07 |
| C6 | 90 | -11.1 | [-21.1, -3.1] | 0.0029 |
| C7 | 90 | -12.2 | [-18.9, -6.7] | 0.0029 |

### llm:gpt-4.1-mini: confirmed

hard worlds: C0 80.6 % (n 67), C5 70.1 % (n 67), C6 56.7 % (n 67), C7 83.6 % (n 67), S 6.0 % (n 67)

| S vs | pairs | diff pp | 95% CI | Holm p |
|---|---|---|---|---|
| C0 | 67 | -74.6 | [-83.6, -67.8] | 5.3e-15 |
| C5 | 67 | -64.2 | [-73.4, -57.1] | 4.5e-13 |
| C6 | 67 | -50.7 | [-56.3, -44.6] | 1.1e-09 |
| C7 | 67 | -77.6 | [-87.3, -69.0] | 1.8e-15 |

easy worlds: C0 62.2 % (n 45), C5 37.8 % (n 45), C6 24.4 % (n 45), C7 51.1 % (n 45), S 0.0 % (n 45)

| S vs | pairs | diff pp | 95% CI | Holm p |
|---|---|---|---|---|
| C0 | 45 | -62.2 | [-71.1, -51.1] | 3e-08 |
| C5 | 45 | -37.8 | [-48.7, -28.6] | 3.1e-05 |
| C6 | 45 | -24.4 | [-31.2, -15.6] | 0.00098 |
| C7 | 45 | -51.1 | [-60.4, -40.5] | 7.2e-07 |

### llm:gpt-5.4-nano: confirmed

hard worlds: C0 62.7 % (n 67), C5 62.7 % (n 67), C6 47.8 % (n 67), C7 68.7 % (n 67), S 6.0 % (n 67)

| S vs | pairs | diff pp | 95% CI | Holm p |
|---|---|---|---|---|
| C0 | 67 | -56.7 | [-70.8, -38.5] | 1.5e-10 |
| C5 | 67 | -56.7 | [-68.5, -41.7] | 2.2e-11 |
| C6 | 67 | -41.8 | [-55.4, -27.4] | 1.9e-06 |
| C7 | 67 | -62.7 | [-71.3, -49.0] | 1.8e-12 |

easy worlds: C0 44.4 % (n 45), C5 24.4 % (n 45), C6 24.4 % (n 45), C7 51.1 % (n 45), S 0.0 % (n 45)

| S vs | pairs | diff pp | 95% CI | Holm p |
|---|---|---|---|---|
| C0 | 45 | -44.4 | [-66.7, -22.9] | 5.7e-06 |
| C5 | 45 | -24.4 | [-31.2, -15.6] | 0.002 |
| C6 | 45 | -24.4 | [-35.7, -12.5] | 0.002 |
| C7 | 45 | -51.1 | [-62.5, -37.5] | 9.5e-07 |
