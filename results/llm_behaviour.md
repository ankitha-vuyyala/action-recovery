# LLM behaviour after an ambiguous tool outcome

First action after the first failed/unknown write result, by driver, condition and hidden truth (%).

| driver | condition | hidden truth | n | reissue | check | wait | compensate | other_write | finish | none | checked before re-issue | listed uncertain | uncertainty language | claimed completed | inconsistent |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| llm:gpt-4.1-mini | C0 | committed | 73 | 77 | 23 | 0 | 0 | 0 | 0 | 0 | 20 (of 70) | 1 | 4 | 96 | 93 |
| llm:gpt-4.1-mini | C0 | not_executed | 29 | 90 | 10 | 0 | 0 | 0 | 0 | 0 | 7 (of 28) | 0 | 3 | 97 | 10 |
| llm:gpt-4.1-mini | C6 | committed | 73 | 38 | 60 | 0 | 0 | 1 | 0 | 0 | 47 (of 53) | 11 | 15 | 92 | 33 |
| llm:gpt-4.1-mini | C6 | not_executed | 29 | 34 | 62 | 0 | 0 | 3 | 0 | 0 | 50 (of 22) | 7 | 10 | 93 | 45 |
| llm:gpt-4.1-mini | C7 | committed | 73 | 60 | 40 | 0 | 0 | 0 | 0 | 0 | 29 (of 62) | 0 | 53 | 100 | 82 |
| llm:gpt-4.1-mini | C7 | not_executed | 29 | 55 | 45 | 0 | 0 | 0 | 0 | 0 | 33 (of 24) | 0 | 24 | 100 | 28 |
| llm:gpt-4.1-mini | S | committed | 4 | 50 | 0 | 0 | 0 | 50 | 0 | 0 | 0 (of 4) | 50 | 50 | 50 | 0 |
| llm:gpt-4.1-mini | S | not_executed | 2 | 50 | 0 | 0 | 0 | 50 | 0 | 0 | 0 (of 1) | 0 | 0 | 100 | 100 |
| llm:gpt-5.4-nano | C0 | committed | 73 | 70 | 22 | 0 | 0 | 8 | 0 | 0 | 20 (of 66) | 49 | 37 | 64 | 62 |
| llm:gpt-5.4-nano | C0 | not_executed | 29 | 62 | 21 | 0 | 0 | 14 | 3 | 0 | 22 (of 23) | 48 | 17 | 66 | 34 |
| llm:gpt-5.4-nano | C6 | committed | 73 | 34 | 41 | 0 | 0 | 22 | 3 | 0 | 37 (of 41) | 96 | 93 | 15 | 16 |
| llm:gpt-5.4-nano | C6 | not_executed | 29 | 24 | 59 | 0 | 0 | 17 | 0 | 0 | 56 (of 16) | 93 | 83 | 31 | 72 |
| llm:gpt-5.4-nano | C7 | committed | 73 | 79 | 21 | 0 | 0 | 0 | 0 | 0 | 16 (of 69) | 33 | 22 | 88 | 79 |
| llm:gpt-5.4-nano | C7 | not_executed | 29 | 79 | 21 | 0 | 0 | 0 | 0 | 0 | 18 (of 28) | 21 | 14 | 86 | 10 |
| llm:gpt-5.4-nano | S | committed | 4 | 50 | 0 | 0 | 0 | 50 | 0 | 0 | 0 (of 2) | 100 | 75 | 0 | 0 |
| llm:gpt-5.4-nano | S | not_executed | 2 | 50 | 0 | 0 | 0 | 50 | 0 | 0 | 0 (of 1) | 100 | 100 | 0 | 100 |
| llm:gpt-5.6-luna | C0 | committed | 146 | 16 | 68 | 8 | 0 | 8 | 0 | 0 | 70 (of 81) | 22 | 31 | 81 | 27 |
| llm:gpt-5.6-luna | C0 | not_executed | 58 | 17 | 71 | 5 | 0 | 3 | 3 | 0 | 76 (of 41) | 22 | 21 | 79 | 45 |
| llm:gpt-5.6-luna | C6 | committed | 146 | 8 | 73 | 7 | 0 | 12 | 0 | 0 | 85 (of 82) | 23 | 35 | 80 | 21 |
| llm:gpt-5.6-luna | C6 | not_executed | 58 | 9 | 67 | 10 | 0 | 14 | 0 | 0 | 87 (of 38) | 36 | 47 | 72 | 55 |
| llm:gpt-5.6-luna | C7 | committed | 146 | 14 | 82 | 0 | 0 | 4 | 0 | 0 | 77 (of 87) | 19 | 45 | 84 | 35 |
| llm:gpt-5.6-luna | C7 | not_executed | 58 | 16 | 84 | 0 | 0 | 0 | 0 | 0 | 80 (of 45) | 17 | 17 | 88 | 34 |
| llm:gpt-5.6-luna | S | committed | 8 | 50 | 0 | 0 | 0 | 50 | 0 | 0 | 0 (of 4) | 100 | 88 | 0 | 0 |
| llm:gpt-5.6-luna | S | not_executed | 4 | 50 | 0 | 0 | 0 | 50 | 0 | 0 | 0 (of 2) | 100 | 100 | 0 | 100 |
