# LLM behaviour after an ambiguous tool outcome

First action after the first failed/unknown write result, by driver, condition and hidden truth (%).

| driver | condition | hidden truth | n | reissue | check | wait | compensate | other_write | finish | none | checked before re-issue | listed uncertain | uncertainty language | claimed completed | inconsistent |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| llm:gpt-4.1-mini | C0 | committed | 73 | 78 | 22 | 0 | 0 | 0 | 0 | 0 | 17 (of 69) | 1 | 4 | 96 | 92 |
| llm:gpt-4.1-mini | C0 | not_executed | 29 | 90 | 10 | 0 | 0 | 0 | 0 | 0 | 10 (of 29) | 0 | 3 | 97 | 14 |
| llm:gpt-4.1-mini | C6 | committed | 73 | 37 | 62 | 0 | 0 | 1 | 0 | 0 | 48 (of 52) | 12 | 16 | 90 | 32 |
| llm:gpt-4.1-mini | C6 | not_executed | 29 | 38 | 62 | 0 | 0 | 0 | 0 | 0 | 50 (of 22) | 7 | 10 | 93 | 45 |
| llm:gpt-4.1-mini | C7 | committed | 72 | 58 | 42 | 0 | 0 | 0 | 0 | 0 | 30 (of 60) | 0 | 51 | 99 | 82 |
| llm:gpt-4.1-mini | C7 | not_executed | 29 | 55 | 45 | 0 | 0 | 0 | 0 | 0 | 33 (of 24) | 0 | 24 | 100 | 28 |
| llm:gpt-4.1-mini | S | committed | 4 | 50 | 0 | 0 | 0 | 50 | 0 | 0 | 0 (of 4) | 50 | 50 | 50 | 0 |
| llm:gpt-4.1-mini | S | not_executed | 2 | 50 | 0 | 0 | 0 | 50 | 0 | 0 | 0 (of 1) | 0 | 0 | 100 | 100 |
| llm:gpt-5.4-nano | C0 | committed | 73 | 70 | 22 | 0 | 0 | 8 | 0 | 0 | 21 (of 67) | 48 | 36 | 64 | 78 |
| llm:gpt-5.4-nano | C0 | not_executed | 29 | 59 | 17 | 0 | 0 | 21 | 3 | 0 | 23 (of 22) | 52 | 17 | 62 | 48 |
| llm:gpt-5.4-nano | C6 | committed | 73 | 34 | 42 | 0 | 0 | 21 | 3 | 0 | 40 (of 43) | 92 | 88 | 15 | 36 |
| llm:gpt-5.4-nano | C6 | not_executed | 29 | 24 | 59 | 0 | 0 | 17 | 0 | 0 | 59 (of 17) | 83 | 76 | 34 | 86 |
| llm:gpt-5.4-nano | C7 | committed | 73 | 75 | 25 | 0 | 0 | 0 | 0 | 0 | 20 (of 69) | 33 | 25 | 86 | 92 |
| llm:gpt-5.4-nano | C7 | not_executed | 29 | 76 | 24 | 0 | 0 | 0 | 0 | 0 | 21 (of 28) | 17 | 10 | 86 | 24 |
| llm:gpt-5.4-nano | S | committed | 4 | 50 | 0 | 0 | 0 | 50 | 0 | 0 | 0 (of 2) | 100 | 75 | 0 | 0 |
| llm:gpt-5.4-nano | S | not_executed | 2 | 50 | 0 | 0 | 0 | 50 | 0 | 0 | 0 (of 1) | 100 | 100 | 0 | 100 |
| llm:gpt-5.6-luna | C0 | committed | 146 | 14 | 70 | 8 | 0 | 8 | 0 | 0 | 74 (of 81) | 25 | 33 | 78 | 43 |
| llm:gpt-5.6-luna | C0 | not_executed | 58 | 16 | 72 | 5 | 0 | 3 | 3 | 0 | 78 (of 41) | 26 | 21 | 78 | 59 |
| llm:gpt-5.6-luna | C6 | committed | 146 | 9 | 72 | 7 | 0 | 12 | 0 | 1 | 85 (of 86) | 26 | 38 | 79 | 38 |
| llm:gpt-5.6-luna | C6 | not_executed | 58 | 9 | 67 | 10 | 0 | 14 | 0 | 0 | 87 (of 39) | 41 | 50 | 69 | 69 |
| llm:gpt-5.6-luna | C7 | committed | 146 | 13 | 83 | 0 | 0 | 4 | 0 | 0 | 79 (of 89) | 24 | 44 | 83 | 51 |
| llm:gpt-5.6-luna | C7 | not_executed | 58 | 14 | 86 | 0 | 0 | 0 | 0 | 0 | 82 (of 45) | 19 | 17 | 86 | 48 |
| llm:gpt-5.6-luna | S | committed | 8 | 50 | 0 | 0 | 0 | 50 | 0 | 0 | 0 (of 4) | 88 | 75 | 0 | 0 |
| llm:gpt-5.6-luna | S | not_executed | 4 | 50 | 0 | 0 | 0 | 50 | 0 | 0 | 0 (of 2) | 100 | 100 | 0 | 100 |
