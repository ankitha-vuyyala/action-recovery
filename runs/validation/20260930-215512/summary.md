# Stage-3 environment validation

Run: `20260930-215512` · trials per cell: 10 · tool deadline 4.0 s · late delay 12.0 s · Toxiproxy {"version": "2.12.0"}

## Realized outcome per service and fault

| service | mode | n | expected execs | realized execs (count) | as intended | caller saw | median elapsed s | late after give-up | tag fidelity |
|---|---|---|---|---|---|---|---|---|---|
| mail | held | 10 | 1 | {'1': 10} | 1.0 | {'timeout': 10} | 4.008 |  |  |
| mail | late | 10 | 1 | {'1': 10} | 1.0 | {'timeout': 10} | 4.011 | 1.0 |  |
| mail | lost_ack | 10 | 1 | {'1': 10} | 1.0 | {'error': 10} | 0.036 |  |  |
| mail | none | 10 | 1 | {'1': 10} | 1.0 | {'ok': 10} | 0.02 |  | 1.0 |
| mail | not_exec_err | 10 | 0 | {'0': 10} | 1.0 | {'error': 10} | 0.03 |  |  |
| mail | not_exec_to | 10 | 0 | {'0': 10} | 1.0 | {'timeout': 10} | 4.012 |  |  |
| mail | redelivery | 10 | 2 | {'2': 10} | 1.0 | {'ok': 10} | 0.015 |  |  |
| s3_put | held | 10 | 1 | {'1': 10} | 1.0 | {'timeout': 10} | 4.014 |  |  |
| s3_put | late | 10 | 1 | {'1': 10} | 1.0 | {'timeout': 10} | 4.01 | 1.0 |  |
| s3_put | lost_ack | 10 | 1 | {'1': 10} | 1.0 | {'error': 10} | 0.083 |  |  |
| s3_put | none | 10 | 1 | {'1': 10} | 1.0 | {'ok': 10} | 0.073 |  | 1.0 |
| s3_put | not_exec_err | 10 | 0 | {'0': 10} | 1.0 | {'error': 10} | 0.034 |  |  |
| s3_put | not_exec_to | 10 | 0 | {'0': 10} | 1.0 | {'timeout': 10} | 4.011 |  |  |
| s3_put | redelivery | 10 | 1 | {'1': 10} | 1.0 | {'ok': 10} | 0.118 |  |  |

## Observation equivalence of paired modes

TVD = total variation distance between the (kind, exception type) distributions; 0 means the caller cannot tell the modes apart from the error alone.

Tool-level = what the tool layer reports (transport failures normalized); raw = the client library's own exception type, for audit.

| service | group | TVD tool-level | TVD raw library exception | median elapsed s | equivalent (tool level) |
|---|---|---|---|---|---|
| mail | error | {'lost_ack vs not_exec_err': 0.0} | {'lost_ack vs not_exec_err': 1.0} | {'lost_ack': 0.036, 'not_exec_err': 0.03} | True |
| mail | deadline | {'held vs not_exec_to': 0.0, 'held vs late': 0.0, 'not_exec_to vs late': 0.0} | {'held vs not_exec_to': 0.0, 'held vs late': 0.0, 'not_exec_to vs late': 0.0} | {'held': 4.008, 'not_exec_to': 4.012, 'late': 4.011} | True |
| s3_put | error | {'lost_ack vs not_exec_err': 0.0} | {'lost_ack vs not_exec_err': 0.0} | {'lost_ack': 0.083, 'not_exec_err': 0.034} | True |
| s3_put | deadline | {'held vs not_exec_to': 0.0, 'held vs late': 0.0, 'not_exec_to vs late': 0.0} | {'held vs not_exec_to': 0.0, 'held vs late': 0.0, 'not_exec_to vs late': 0.0} | {'held': 4.014, 'not_exec_to': 4.011, 'late': 4.01} | True |
