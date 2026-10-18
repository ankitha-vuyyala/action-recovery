# Stage-3 environment validation

Run: `20260930-204601` · trials per cell: 10 · tool deadline 4.0 s · late delay 12.0 s · Toxiproxy {"version": "2.12.0"}

## Realized outcome per service and fault

| service | mode | n | expected execs | realized execs (count) | as intended | caller saw | median elapsed s | late after give-up | tag fidelity |
|---|---|---|---|---|---|---|---|---|---|
| gitea_issue | held | 10 | 1 | {'1': 10} | 1.0 | {'timeout': 10} | 4.006 |  |  |
| gitea_issue | late | 10 | 1 | {'1': 10} | 1.0 | {'timeout': 10} | 4.008 | 1.0 |  |
| gitea_issue | lost_ack | 10 | 1 | {'1': 10} | 1.0 | {'error': 10} | 0.435 |  |  |
| gitea_issue | none | 10 | 1 | {'1': 10} | 1.0 | {'ok': 10} | 0.52 |  | 1.0 |
| gitea_issue | not_exec_err | 10 | 0 | {'0': 10} | 1.0 | {'error': 10} | 0.405 |  |  |
| gitea_issue | not_exec_to | 10 | 0 | {'0': 10} | 1.0 | {'timeout': 10} | 4.01 |  |  |
| gitea_issue | redelivery | 10 | 2 | {'2': 10} | 1.0 | {'ok': 10} | 0.455 |  |  |
| mail | held | 10 | 1 | {'1': 10} | 1.0 | {'timeout': 10} | 4.011 |  |  |
| mail | late | 10 | 1 | {'1': 10} | 1.0 | {'timeout': 10} | 4.011 | 1.0 |  |
| mail | lost_ack | 10 | 1 | {'1': 10} | 1.0 | {'error': 10} | 0.034 |  |  |
| mail | none | 10 | 1 | {'1': 10} | 1.0 | {'ok': 10} | 0.015 |  | 1.0 |
| mail | not_exec_err | 10 | 0 | {'0': 10} | 1.0 | {'error': 10} | 0.024 |  |  |
| mail | not_exec_to | 10 | 0 | {'0': 10} | 1.0 | {'timeout': 10} | 4.006 |  |  |
| mail | redelivery | 10 | 2 | {'2': 10} | 1.0 | {'ok': 10} | 0.022 |  |  |
| pg_batch | none | 10 | 6 | {'6': 10} | 1.0 | {'ok': 10} | 0.035 |  |  |
| pg_batch | partial | 10 | 3 | {'3': 10} | 1.0 | {'error': 10} | 0.03 |  |  |
| pg_row | held | 10 | 1 | {'1': 10} | 1.0 | {'timeout': 10} | 4.008 |  |  |
| pg_row | late | 10 | 1 | {'1': 10} | 1.0 | {'timeout': 10} | 4.01 | 1.0 |  |
| pg_row | lost_ack | 10 | 1 | {'1': 10} | 1.0 | {'error': 10} | 0.044 |  |  |
| pg_row | none | 10 | 1 | {'1': 10} | 1.0 | {'ok': 10} | 0.029 |  | 1.0 |
| pg_row | not_exec_err | 10 | 0 | {'0': 10} | 1.0 | {'error': 10} | 0.041 |  |  |
| pg_row | not_exec_to | 10 | 0 | {'0': 10} | 1.0 | {'timeout': 10} | 4.012 |  |  |
| pg_row | redelivery | 10 | 2 | {'2': 10} | 1.0 | {'ok': 10} | 0.035 |  |  |
| redis_counter | held | 10 | 1 | {'1': 10} | 1.0 | {'timeout': 10} | 4.002 |  |  |
| redis_counter | late | 10 | 1 | {'1': 10} | 1.0 | {'timeout': 10} | 4.008 | 1.0 |  |
| redis_counter | lost_ack | 10 | 1 | {'1': 10} | 1.0 | {'error': 10} | 0.038 |  |  |
| redis_counter | none | 10 | 1 | {'1': 10} | 1.0 | {'ok': 10} | 0.01 |  |  |
| redis_counter | not_exec_err | 10 | 0 | {'0': 10} | 1.0 | {'error': 10} | 0.023 |  |  |
| redis_counter | not_exec_to | 10 | 0 | {'0': 10} | 1.0 | {'timeout': 10} | 4.011 |  |  |
| redis_counter | redelivery | 10 | 2 | {'2': 10} | 1.0 | {'ok': 10} | 0.023 |  |  |
| redis_stream | held | 10 | 1 | {'1': 10} | 1.0 | {'timeout': 10} | 4.011 |  |  |
| redis_stream | late | 10 | 1 | {'1': 10} | 1.0 | {'timeout': 10} | 4.004 | 1.0 |  |
| redis_stream | lost_ack | 10 | 1 | {'1': 10} | 1.0 | {'error': 10} | 0.028 |  |  |
| redis_stream | none | 10 | 1 | {'1': 10} | 1.0 | {'ok': 10} | 0.013 |  | 1.0 |
| redis_stream | not_exec_err | 10 | 0 | {'0': 10} | 1.0 | {'error': 10} | 0.037 |  |  |
| redis_stream | not_exec_to | 10 | 0 | {'0': 10} | 1.0 | {'timeout': 10} | 4.005 |  |  |
| redis_stream | redelivery | 10 | 2 | {'2': 10} | 1.0 | {'ok': 10} | 0.026 |  |  |
| s3_put | held | 10 | 1 | {'0': 10} | 0.0 | {'timeout': 10} | 4.014 |  |  |
| s3_put | late | 10 | 1 | {'0': 10} | 0.0 | {'timeout': 10} | 4.01 |  |  |
| s3_put | lost_ack | 10 | 1 | {'0': 10} | 0.0 | {'error': 10} | 0.036 |  |  |
| s3_put | none | 10 | 1 | {'0': 10} | 0.0 | {'error': 10} | 0.024 |  | 0.0 |
| s3_put | not_exec_err | 10 | 0 | {'0': 10} | 1.0 | {'error': 10} | 0.04 |  |  |
| s3_put | not_exec_to | 10 | 0 | {'0': 10} | 1.0 | {'timeout': 10} | 4.011 |  |  |
| s3_put | redelivery | 10 | 1 | {'0': 10} | 0.0 | {'error': 10} | 0.024 |  |  |
| tb_transfer | held | 10 | 1 | {'1': 10} | 1.0 | {'timeout': 10} | 4.009 |  |  |
| tb_transfer | late | 10 | 1 | {'1': 10} | 1.0 | {'timeout': 10} | 4.011 | 1.0 |  |
| tb_transfer | lost_ack | 10 | 1 | {'1': 10} | 1.0 | {'timeout': 10} | 4.008 |  |  |
| tb_transfer | none | 10 | 1 | {'1': 10} | 1.0 | {'ok': 10} | 0.987 |  | 1.0 |
| tb_transfer | not_exec_err | 10 | 0 | {'1': 10} | 0.0 | {'timeout': 10} | 4.005 |  |  |
| tb_transfer | not_exec_to | 10 | 0 | {'1': 6, '0': 4} | 0.4 | {'timeout': 10} | 4.006 |  |  |
| tb_transfer | redelivery | 10 | 1 | {'1': 10} | 1.0 | {'ok': 10} | 0.994 |  |  |

## Observation equivalence of paired modes

TVD = total variation distance between the (kind, exception type) distributions; 0 means the caller cannot tell the modes apart from the error alone.

| service | group | TVD by pair | median elapsed s | equivalent |
|---|---|---|---|---|
| gitea_issue | error | {'lost_ack vs not_exec_err': 0.0} | {'lost_ack': 0.435, 'not_exec_err': 0.405} | True |
| gitea_issue | deadline | {'held vs not_exec_to': 0.0, 'held vs late': 0.0, 'not_exec_to vs late': 0.0} | {'held': 4.006, 'not_exec_to': 4.01, 'late': 4.008} | True |
| mail | error | {'lost_ack vs not_exec_err': 1.0} | {'lost_ack': 0.034, 'not_exec_err': 0.024} | False |
| mail | deadline | {'held vs not_exec_to': 0.0, 'held vs late': 0.0, 'not_exec_to vs late': 0.0} | {'held': 4.011, 'not_exec_to': 4.006, 'late': 4.011} | True |
| pg_row | error | {'lost_ack vs not_exec_err': 0.0} | {'lost_ack': 0.044, 'not_exec_err': 0.041} | True |
| pg_row | deadline | {'held vs not_exec_to': 0.0, 'held vs late': 0.0, 'not_exec_to vs late': 0.0} | {'held': 4.008, 'not_exec_to': 4.012, 'late': 4.01} | True |
| redis_counter | error | {'lost_ack vs not_exec_err': 0.0} | {'lost_ack': 0.038, 'not_exec_err': 0.023} | True |
| redis_counter | deadline | {'held vs not_exec_to': 0.0, 'held vs late': 0.0, 'not_exec_to vs late': 0.0} | {'held': 4.002, 'not_exec_to': 4.011, 'late': 4.008} | True |
| redis_stream | error | {'lost_ack vs not_exec_err': 0.0} | {'lost_ack': 0.028, 'not_exec_err': 0.037} | True |
| redis_stream | deadline | {'held vs not_exec_to': 0.0, 'held vs late': 0.0, 'not_exec_to vs late': 0.0} | {'held': 4.011, 'not_exec_to': 4.005, 'late': 4.004} | True |
| s3_put | error | {'lost_ack vs not_exec_err': 0.0} | {'lost_ack': 0.036, 'not_exec_err': 0.04} | True |
| s3_put | deadline | {'held vs not_exec_to': 0.0, 'held vs late': 0.0, 'not_exec_to vs late': 0.0} | {'held': 4.014, 'not_exec_to': 4.011, 'late': 4.01} | True |
| tb_transfer | error | {'lost_ack vs not_exec_err': 0.0} | {'lost_ack': 4.008, 'not_exec_err': 4.005} | True |
| tb_transfer | deadline | {'held vs not_exec_to': 0.0, 'held vs late': 0.0, 'not_exec_to vs late': 0.0} | {'held': 4.009, 'not_exec_to': 4.006, 'late': 4.011} | True |
