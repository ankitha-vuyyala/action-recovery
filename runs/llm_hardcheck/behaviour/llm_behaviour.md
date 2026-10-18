# LLM behaviour after an ambiguous tool outcome

First action after the first failed/unknown write result, by driver, condition and hidden truth (%).

| driver | condition | hidden truth | n | reissue | check | wait | compensate | other_write | finish | none | checked before re-issue | listed uncertain | uncertainty language | claimed completed | inconsistent |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| llm:gpt-5.6-luna | C0 | committed | 11 | 9 | 64 | 27 | 0 | 0 | 0 | 0 | 67 (of 3) | 27 | 36 | 73 | 18 |
| llm:gpt-5.6-luna | S | committed | 1 | 100 | 0 | 0 | 0 | 0 | 0 | 0 | 0 (of 1) | 100 | 0 | 0 | 0 |
