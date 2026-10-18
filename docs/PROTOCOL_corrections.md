# Corrections recorded after the follow-up runs

These notes belong to `docs/PROTOCOL.md`. They are kept in this separate file because `PROTOCOL.md` is part of the
follow-up freeze (`FREEZE.json`), so any edit to it would break `code/run.py freeze --check`.

**Follow-up correction 1 (2026-10-05, after the follow-up runs; analysis only).** `analysis/followup.py` evaluated two
F4 criteria with `(rate or 1) <= 0.05`. A measured rate of exactly 0 is falsy in Python, so the expression became
`1 <= 0.05` and the criteria failed although the plan's criteria ("S2 ≤ 5%", "S2 overclaims ≤ 5%") were met (both
rates 0%). The expression now treats only a missing rate as failing. No other output changed (verified by
comparing the two result files). The frozen script stays unchanged at `analysis/followup.py` (the freeze check passes); the corrected copy is
`paper/followup/followup_corrected.py`, which also makes every criterion treat a missing rate as failing. Both outputs are kept
(`results/followup.json` from the frozen script, `results_followup/followup.json` from the corrected one).
