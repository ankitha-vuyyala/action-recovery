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

Latency: **confirmed**; fault-free S - C6 1.01 s, 95% CI [0.74, 1.29]; ambiguous 14.99 s. Cost ratio per model: llm:gpt-5.6-luna: 0.89 [0.74, 1.08] -> confirmed; llm:gpt-4.1-mini: 0.87 [0.70, 0.98] -> confirmed; llm:gpt-5.4-nano: 0.98 [0.76, 1.26] -> inconclusive

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

hard worlds: C0 65.7 % (n 134), C5 74.6 % (n 134), C6 63.4 % (n 134), C7 68.7 % (n 134), S 6.7 % (n 134)

| S vs | pairs | diff pp | 95% CI | Holm p |
|---|---|---|---|---|
| C0 | 134 | -59.0 | [-71.7, -50.0] | 1.1e-20 |
| C5 | 134 | -67.9 | [-78.4, -59.1] | 7.6e-26 |
| C6 | 134 | -56.7 | [-72.2, -46.9] | 3.8e-20 |
| C7 | 134 | -61.9 | [-74.0, -54.1] | 1.3e-23 |

easy worlds: C0 37.8 % (n 90), C5 50.0 % (n 90), C6 37.8 % (n 90), C7 37.8 % (n 90), S 1.1 % (n 90)

| S vs | pairs | diff pp | 95% CI | Holm p |
|---|---|---|---|---|
| C0 | 90 | -36.7 | [-67.7, -9.5] | 6.3e-09 |
| C5 | 90 | -48.9 | [-72.6, -27.4] | 5.3e-12 |
| C6 | 90 | -36.7 | [-65.6, -9.5] | 6.3e-09 |
| C7 | 90 | -36.7 | [-66.7, -11.5] | 6.3e-09 |

### llm:gpt-4.1-mini: confirmed

hard worlds: C0 80.6 % (n 67), C5 70.1 % (n 67), C6 55.2 % (n 67), C7 83.6 % (n 67), S 6.0 % (n 67)

| S vs | pairs | diff pp | 95% CI | Holm p |
|---|---|---|---|---|
| C0 | 67 | -74.6 | [-83.7, -68.2] | 5.3e-15 |
| C5 | 67 | -64.2 | [-73.2, -57.0] | 4.5e-13 |
| C6 | 67 | -49.3 | [-56.0, -41.2] | 1e-08 |
| C7 | 67 | -77.6 | [-88.2, -68.8] | 1.8e-15 |

easy worlds: C0 62.2 % (n 45), C5 37.8 % (n 45), C6 24.4 % (n 45), C7 51.1 % (n 45), S 0.0 % (n 45)

| S vs | pairs | diff pp | 95% CI | Holm p |
|---|---|---|---|---|
| C0 | 45 | -62.2 | [-71.1, -51.1] | 3e-08 |
| C5 | 45 | -37.8 | [-48.9, -28.6] | 3.1e-05 |
| C6 | 45 | -24.4 | [-33.3, -15.6] | 0.00098 |
| C7 | 45 | -51.1 | [-62.5, -40.0] | 7.2e-07 |

### llm:gpt-5.4-nano: confirmed

hard worlds: C0 74.6 % (n 67), C5 74.6 % (n 67), C6 61.2 % (n 67), C7 79.1 % (n 67), S 6.0 % (n 67)

| S vs | pairs | diff pp | 95% CI | Holm p |
|---|---|---|---|---|
| C0 | 67 | -68.7 | [-81.4, -54.3] | 7e-13 |
| C5 | 67 | -68.7 | [-79.5, -59.3] | 8.5e-14 |
| C6 | 67 | -55.2 | [-73.7, -39.6] | 3e-09 |
| C7 | 67 | -73.1 | [-80.3, -67.4] | 1.4e-14 |

easy worlds: C0 68.9 % (n 45), C5 48.9 % (n 45), C6 51.1 % (n 45), C7 71.1 % (n 45), S 0.0 % (n 45)

| S vs | pairs | diff pp | 95% CI | Holm p |
|---|---|---|---|---|
| C0 | 45 | -68.9 | [-88.9, -47.9] | 2.8e-09 |
| C5 | 45 | -48.9 | [-72.9, -28.9] | 4.8e-07 |
| C6 | 45 | -51.1 | [-73.8, -31.0] | 4.8e-07 |
| C7 | 45 | -71.1 | [-84.5, -57.1] | 1.9e-09 |
