# Stage-3 environment validation

Run: `20261001-164459` · trials per cell: 10 · tool deadline 4.0 s · late delay 12.0 s · Toxiproxy {"version": "2.12.0"}

## Realized outcome per service and fault

| service | mode | n | expected execs | realized execs (count) | as intended | caller saw | median elapsed s | late after give-up | tag fidelity |
|---|---|---|---|---|---|---|---|---|---|
| gitea_issue | held | 10 | 1 | {'1': 10} | 1.0 | {'timeout': 10} | 4.011 |  |  |
| gitea_issue | late | 10 | 1 | {'1': 10} | 1.0 | {'timeout': 10} | 4.008 | 1.0 |  |
| gitea_issue | lost_ack | 10 | 1 | {'1': 10} | 1.0 | {'error': 10} | 0.417 |  |  |
| gitea_issue | none | 10 | 1 | {'1': 10} | 1.0 | {'ok': 10} | 0.403 |  | 1.0 |
| gitea_issue | not_exec_err | 10 | 0 | {'0': 10} | 1.0 | {'error': 10} | 0.373 |  |  |
| gitea_issue | not_exec_to | 10 | 0 | {'0': 10} | 1.0 | {'timeout': 10} | 4.007 |  |  |
| gitea_issue | redelivery | 10 | 2 | {'2': 10} | 1.0 | {'ok': 10} | 0.477 |  |  |
| mail | held | 10 | 1 | {'1': 10} | 1.0 | {'timeout': 10} | 4.007 |  |  |
| mail | late | 10 | 1 | {'1': 10} | 1.0 | {'timeout': 10} | 4.005 | 1.0 |  |
| mail | lost_ack | 10 | 1 | {'1': 10} | 1.0 | {'error': 10} | 0.051 |  |  |
| mail | none | 10 | 1 | {'1': 10} | 1.0 | {'ok': 10} | 0.032 |  | 1.0 |
| mail | not_exec_err | 10 | 0 | {'0': 10} | 1.0 | {'error': 10} | 0.04 |  |  |
| mail | not_exec_to | 10 | 0 | {'0': 10} | 1.0 | {'timeout': 10} | 4.01 |  |  |
| mail | redelivery | 10 | 2 | {'2': 10} | 1.0 | {'ok': 10} | 0.023 |  |  |
| pg_batch | none | 10 | 6 | {'6': 10} | 1.0 | {'ok': 10} | 0.054 |  |  |
| pg_batch | partial | 10 | 3 | {'3': 10} | 1.0 | {'error': 10} | 0.069 |  |  |
| pg_row | held | 10 | 1 | {'1': 10} | 1.0 | {'timeout': 10} | 4.006 |  |  |
| pg_row | late | 10 | 1 | {'1': 10} | 1.0 | {'timeout': 10} | 4.008 | 1.0 |  |
| pg_row | lost_ack | 10 | 1 | {'1': 10} | 1.0 | {'error': 10} | 0.057 |  |  |
| pg_row | none | 10 | 1 | {'1': 10} | 1.0 | {'ok': 10} | 0.04 |  | 1.0 |
| pg_row | not_exec_err | 10 | 0 | {'0': 10} | 1.0 | {'error': 10} | 0.055 |  |  |
| pg_row | not_exec_to | 10 | 0 | {'0': 10} | 1.0 | {'timeout': 10} | 4.01 |  |  |
| pg_row | redelivery | 10 | 2 | {'2': 10} | 1.0 | {'ok': 10} | 0.037 |  |  |
| redis_counter | held | 10 | 1 | {'1': 10} | 1.0 | {'timeout': 10} | 4.002 |  |  |
| redis_counter | late | 10 | 1 | {'1': 10} | 1.0 | {'timeout': 10} | 4.006 | 1.0 |  |
| redis_counter | lost_ack | 10 | 1 | {'1': 10} | 1.0 | {'error': 10} | 0.046 |  |  |
| redis_counter | none | 10 | 1 | {'1': 10} | 1.0 | {'ok': 10} | 0.029 |  |  |
| redis_counter | not_exec_err | 10 | 0 | {'0': 10} | 1.0 | {'error': 10} | 0.037 |  |  |
| redis_counter | not_exec_to | 10 | 0 | {'0': 10} | 1.0 | {'timeout': 10} | 4.007 |  |  |
| redis_counter | redelivery | 10 | 2 | {'2': 10} | 1.0 | {'ok': 10} | 0.026 |  |  |
| redis_stream | held | 10 | 1 | {'1': 10} | 1.0 | {'timeout': 10} | 4.01 |  |  |
| redis_stream | late | 10 | 1 | {'1': 10} | 1.0 | {'timeout': 10} | 4.004 | 1.0 |  |
| redis_stream | lost_ack | 10 | 1 | {'1': 10} | 1.0 | {'error': 10} | 0.052 |  |  |
| redis_stream | none | 10 | 1 | {'1': 10} | 1.0 | {'ok': 10} | 0.022 |  | 1.0 |
| redis_stream | not_exec_err | 10 | 0 | {'0': 10} | 1.0 | {'error': 10} | 0.039 |  |  |
| redis_stream | not_exec_to | 10 | 0 | {'0': 10} | 1.0 | {'timeout': 10} | 4.011 |  |  |
| redis_stream | redelivery | 10 | 2 | {'2': 10} | 1.0 | {'ok': 10} | 0.026 |  |  |
| s3_put | held | 10 | 1 | {'1': 10} | 1.0 | {'timeout': 10} | 4.014 |  |  |
| s3_put | late | 10 | 1 | {'1': 10} | 1.0 | {'timeout': 10} | 4.014 | 1.0 |  |
| s3_put | lost_ack | 10 | 1 | {'1': 10} | 1.0 | {'error': 10} | 0.088 |  |  |
| s3_put | none | 10 | 1 | {'1': 10} | 1.0 | {'ok': 10} | 0.084 |  | 1.0 |
| s3_put | not_exec_err | 10 | 0 | {'0': 10} | 1.0 | {'error': 10} | 0.05 |  |  |
| s3_put | not_exec_to | 10 | 0 | {'0': 10} | 1.0 | {'timeout': 10} | 4.011 |  |  |
| s3_put | redelivery | 10 | 1 | {'1': 10} | 1.0 | {'ok': 10} | 0.141 |  |  |
| tb_transfer | held | 10 | 1 | {'1': 10} | 1.0 | {'timeout': 10} | 4.01 |  |  |
| tb_transfer | late | 10 | 1 | {'1': 10} | 1.0 | {'timeout': 10} | 4.007 | 1.0 |  |
| tb_transfer | lost_ack | 10 | 1 | {'1': 10} | 1.0 | {'timeout': 10} | 4.006 |  |  |
| tb_transfer | none | 10 | 1 | {'1': 10} | 1.0 | {'ok': 10} | 0.997 |  | 1.0 |
| tb_transfer | not_exec_err | 10 | 0 | {'1': 10} | 0.0 | {'timeout': 10} | 4.006 |  |  |
| tb_transfer | not_exec_to | 10 | 0 | {'1': 7, '0': 3} | 0.3 | {'timeout': 10} | 4.008 |  |  |
| tb_transfer | redelivery | 10 | 1 | {'1': 10} | 1.0 | {'ok': 10} | 1.009 |  |  |

## Observation equivalence of paired modes

TVD = total variation distance between the (kind, exception type) distributions; 0 means the caller cannot tell the modes apart from the error alone.

Tool-level = what the tool layer reports (transport failures normalized); raw = the client library's own exception type, for audit.

| service | group | TVD tool-level | TVD raw library exception | median elapsed s | equivalent (tool level) |
|---|---|---|---|---|---|
| gitea_issue | error | {'lost_ack vs not_exec_err': 0.0} | {'lost_ack vs not_exec_err': 0.0} | {'lost_ack': 0.417, 'not_exec_err': 0.373} | True |
| gitea_issue | deadline | {'held vs not_exec_to': 0.0, 'held vs late': 0.0, 'not_exec_to vs late': 0.0} | {'held vs not_exec_to': 0.0, 'held vs late': 0.0, 'not_exec_to vs late': 0.0} | {'held': 4.011, 'not_exec_to': 4.007, 'late': 4.008} | True |
| mail | error | {'lost_ack vs not_exec_err': 0.0} | {'lost_ack vs not_exec_err': 1.0} | {'lost_ack': 0.051, 'not_exec_err': 0.04} | True |
| mail | deadline | {'held vs not_exec_to': 0.0, 'held vs late': 0.0, 'not_exec_to vs late': 0.0} | {'held vs not_exec_to': 0.0, 'held vs late': 0.0, 'not_exec_to vs late': 0.0} | {'held': 4.007, 'not_exec_to': 4.01, 'late': 4.005} | True |
| pg_row | error | {'lost_ack vs not_exec_err': 0.0} | {'lost_ack vs not_exec_err': 0.0} | {'lost_ack': 0.057, 'not_exec_err': 0.055} | True |
| pg_row | deadline | {'held vs not_exec_to': 0.0, 'held vs late': 0.0, 'not_exec_to vs late': 0.0} | {'held vs not_exec_to': 0.0, 'held vs late': 0.0, 'not_exec_to vs late': 0.0} | {'held': 4.006, 'not_exec_to': 4.01, 'late': 4.008} | True |
| redis_counter | error | {'lost_ack vs not_exec_err': 0.0} | {'lost_ack vs not_exec_err': 0.0} | {'lost_ack': 0.046, 'not_exec_err': 0.037} | True |
| redis_counter | deadline | {'held vs not_exec_to': 0.0, 'held vs late': 0.0, 'not_exec_to vs late': 0.0} | {'held vs not_exec_to': 0.0, 'held vs late': 0.0, 'not_exec_to vs late': 0.0} | {'held': 4.002, 'not_exec_to': 4.007, 'late': 4.006} | True |
| redis_stream | error | {'lost_ack vs not_exec_err': 0.0} | {'lost_ack vs not_exec_err': 0.0} | {'lost_ack': 0.052, 'not_exec_err': 0.039} | True |
| redis_stream | deadline | {'held vs not_exec_to': 0.0, 'held vs late': 0.0, 'not_exec_to vs late': 0.0} | {'held vs not_exec_to': 0.0, 'held vs late': 0.0, 'not_exec_to vs late': 0.0} | {'held': 4.01, 'not_exec_to': 4.011, 'late': 4.004} | True |
| s3_put | error | {'lost_ack vs not_exec_err': 0.0} | {'lost_ack vs not_exec_err': 0.0} | {'lost_ack': 0.088, 'not_exec_err': 0.05} | True |
| s3_put | deadline | {'held vs not_exec_to': 0.0, 'held vs late': 0.0, 'not_exec_to vs late': 0.0} | {'held vs not_exec_to': 0.0, 'held vs late': 0.0, 'not_exec_to vs late': 0.0} | {'held': 4.014, 'not_exec_to': 4.011, 'late': 4.014} | True |
| tb_transfer | error | {'lost_ack vs not_exec_err': 0.0} | {'lost_ack vs not_exec_err': 0.0} | {'lost_ack': 4.006, 'not_exec_err': 4.006} | True |
| tb_transfer | deadline | {'held vs not_exec_to': 0.0, 'held vs late': 0.0, 'not_exec_to vs late': 0.0} | {'held vs not_exec_to': 0.0, 'held vs late': 0.0, 'not_exec_to vs late': 0.0} | {'held': 4.01, 'not_exec_to': 4.008, 'late': 4.007} | True |
