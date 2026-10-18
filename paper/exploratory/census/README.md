# API census

`census.csv` is the authoritative coding used in the paper (52 APIs, one create operation each). The JSON files
(`payments.json`, `devtools.json`, `messaging.json`, `crmdata.json`) are the first-pass research notes with quoted
documentation evidence and links; where a note and the CSV differ (for example, e-mail "undo" is coded `no` in the CSV
because delivered mail cannot be recalled, while the notes record `partial` for queued or scheduled sends), the CSV
reflects the reviewed decision. `verify_sample.json` / `verify_result.json` are the second-pass re-check of a random
sample of 12 entries. Documentation was read in October 2026; vendors change their APIs.
