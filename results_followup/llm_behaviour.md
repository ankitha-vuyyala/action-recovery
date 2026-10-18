# LLM behaviour after an ambiguous tool outcome

First action after the first failed/unknown write result, by driver, condition and hidden truth (%).

| driver | condition | hidden truth | n | reissue | check | wait | compensate | other_write | finish | none | checked before re-issue | listed uncertain | uncertainty language | claimed completed | inconsistent |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| llm:gpt-5.6-sol | C0 | committed | 73 | 16 | 77 | 0 | 0 | 7 | 0 | 0 | 68 (of 38) | 16 | 32 | 79 | 25 |
| llm:gpt-5.6-sol | C0 | not_executed | 29 | 14 | 79 | 0 | 0 | 7 | 0 | 0 | 80 (of 20) | 14 | 14 | 86 | 45 |
| llm:gpt-5.6-sol | S-np | committed | 4 | 50 | 0 | 0 | 0 | 50 | 0 | 0 | 0 (of 2) | 100 | 100 | 0 | 0 |
| llm:gpt-5.6-sol | S-np | not_executed | 2 | 50 | 0 | 0 | 0 | 50 | 0 | 0 | 0 (of 1) | 100 | 100 | 0 | 100 |
