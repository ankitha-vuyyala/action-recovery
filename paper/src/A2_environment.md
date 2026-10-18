# Environment validation {#sec:validation}

Before the test runs, and on the frozen code, the validation ran {{val.trials|int}} trials in total, ten per service and fault mode. The hidden outcome was read from the services' own records (validation run `{{val.run}}`). @tbl:validation reports how many trials produced the intended outcome; {{val.as_intended|int}} of {{val.trials|int}} did.

{{table.validation}}

Table: Environment validation: trials whose realised outcome (number of executions, read from the service) matched the intended hidden outcome of the mode. The SeaweedFS conditional create turns a redelivered request into a refusal (one execution, as intended). {#tbl:validation}

Three further checks passed:

- **Late commits.** In every late-commit trial, the write landed after the caller had given up (minimum share {{val.late_after_giveup_min|pct0}}).
- **Tag fidelity.** The operation tag was read back byte-exact on every taggable service (minimum {{val.tag_fidelity_min|pct0}}).
- **Observation equivalence.** For every service, the paired modes (lost_ack vs not_exec_err; held vs not_exec_to vs late) produced identical tool-level observations: the total variation distance between the distributions of (outcome kind, exception type) was 0. Elapsed times differ by tens of milliseconds at most, well below the variation between services.

For one service the raw client exception *did* differ between the paired modes: the SMTP client raised different exception types for a reply cut after commit and a connection cut before delivery. The tool layer therefore normalises all transport failures to one exception and message, while the raw exception is kept in the logs for audit. A deployed agent whose tool layer passes raw exceptions through may be able to tell some of these worlds apart. My results are thus conservative for such agents only in that respect.

**The TigerBeetle exception.** The TigerBeetle client library retries internally and deduplicates by session. A request whose first transmission was cut is therefore often delivered by the library's own retry: the not_exec modes realised the intended *absent* outcome in 0 and 3 of 10 trials. This is the native-key contract working as designed. I keep these cells as measured, and they enter no equivalence claim.

Crash modes are validated per episode by the child process's exit code (75 at the crash, 0 after the restart). The late-tail mode uses the same mechanism as the late mode, with a per-world delay.
