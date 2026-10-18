# Stage-3 environment validation

Run: `20260930-202617` · trials per cell: 3 · tool deadline 4.0 s · late delay 12.0 s · Toxiproxy {"version": "2.12.0"}

## Realized outcome per service and fault

| service | mode | n | expected execs | realized execs (count) | as intended | caller saw | median elapsed s | late after give-up | tag fidelity |
|---|---|---|---|---|---|---|---|---|---|
| gitea_issue | held | 3 | 1 | {'1': 3} | 1.0 | {'timeout': 3} | 4.013 |  |  |
| gitea_issue | late | 3 | 1 | {'1': 3} | 1.0 | {'timeout': 3} | 4.013 | 1.0 |  |
| gitea_issue | lost_ack | 3 | 1 | {'1': 3} | 1.0 | {'error': 3} | 0.407 |  |  |
| gitea_issue | none | 3 | 1 | {'1': 3} | 1.0 | {'ok': 3} | 0.483 |  | 1.0 |
| gitea_issue | not_exec_err | 3 | 0 | {'0': 3} | 1.0 | {'error': 3} | 0.454 |  |  |
| gitea_issue | not_exec_to | 3 | 0 | {'0': 3} | 1.0 | {'timeout': 3} | 4.014 |  |  |
| gitea_issue | redelivery | 3 | 2 | {'2': 3} | 1.0 | {'ok': 3} | 0.635 |  |  |
| mail | held | 3 | 1 | {'1': 3} | 1.0 | {'timeout': 3} | 4.003 |  |  |
| mail | late | 3 | 1 | {'1': 3} | 1.0 | {'timeout': 3} | 4.008 | 1.0 |  |
| mail | lost_ack | 3 | 1 | {'1': 3} | 1.0 | {'error': 3} | 0.043 |  |  |
| mail | none | 3 | 1 | {'1': 3} | 1.0 | {'ok': 3} | 0.011 |  | 1.0 |
| mail | not_exec_err | 3 | 0 | {'0': 3} | 1.0 | {'error': 3} | 0.035 |  |  |
| mail | not_exec_to | 3 | 0 | {'0': 3} | 1.0 | {'timeout': 3} | 4.012 |  |  |
| mail | redelivery | 3 | 2 | {'2': 3} | 1.0 | {'ok': 3} | 0.014 |  |  |
| pg_batch | none | 3 | 6 | {'6': 3} | 1.0 | {'ok': 3} | 0.038 |  |  |
| pg_batch | partial | 3 | 3 | {'3': 3} | 1.0 | {'error': 3} | 0.068 |  |  |
| pg_row | held | 3 | 1 | {'1': 3} | 1.0 | {'timeout': 3} | 4.004 |  |  |
| pg_row | late | 3 | 1 | {'1': 3} | 1.0 | {'timeout': 3} | 4.006 | 1.0 |  |
| pg_row | lost_ack | 3 | 1 | {'1': 3} | 1.0 | {'error': 3} | 0.041 |  |  |
| pg_row | none | 3 | 1 | {'1': 3} | 1.0 | {'ok': 3} | 0.03 |  | 1.0 |
| pg_row | not_exec_err | 3 | 0 | {'0': 3} | 1.0 | {'error': 3} | 0.056 |  |  |
| pg_row | not_exec_to | 3 | 0 | {'0': 3} | 1.0 | {'timeout': 3} | 4.01 |  |  |
| pg_row | redelivery | 3 | 2 | {'2': 3} | 1.0 | {'ok': 3} | 0.038 |  |  |
| redis_counter | held | 3 | 1 | {'1': 3} | 1.0 | {'timeout': 3} | 4.007 |  |  |
| redis_counter | late | 3 | 1 | {'1': 3} | 1.0 | {'timeout': 3} | 4.01 | 1.0 |  |
| redis_counter | lost_ack | 3 | 1 | {'1': 3} | 1.0 | {'error': 3} | 0.021 |  |  |
| redis_counter | none | 3 | 1 | {'1': 3} | 1.0 | {'ok': 3} | 0.016 |  |  |
| redis_counter | not_exec_err | 3 | 0 | {'0': 3} | 1.0 | {'error': 3} | 0.031 |  |  |
| redis_counter | not_exec_to | 3 | 0 | {'0': 3} | 1.0 | {'timeout': 3} | 4.004 |  |  |
| redis_counter | redelivery | 3 | 2 | {'2': 3} | 1.0 | {'ok': 3} | 0.021 |  |  |
| redis_stream | held | 3 | 1 | {'1': 3} | 1.0 | {'timeout': 3} | 4.006 |  |  |
| redis_stream | late | 3 | 1 | {'1': 3} | 1.0 | {'timeout': 3} | 4.005 | 1.0 |  |
| redis_stream | lost_ack | 3 | 1 | {'1': 3} | 1.0 | {'error': 3} | 0.021 |  |  |
| redis_stream | none | 3 | 1 | {'1': 3} | 1.0 | {'ok': 3} | 0.021 |  | 1.0 |
| redis_stream | not_exec_err | 3 | 0 | {'0': 3} | 1.0 | {'error': 3} | 0.039 |  |  |
| redis_stream | not_exec_to | 3 | 0 | {'0': 3} | 1.0 | {'timeout': 3} | 4.007 |  |  |
| redis_stream | redelivery | 3 | 2 | {'2': 3} | 1.0 | {'ok': 3} | 0.029 |  |  |
| s3_put | held | 3 | 1 | {'1': 3} | 1.0 | {'timeout': 3} | 4.015 |  |  |
| s3_put | late | 3 | 1 | {'1': 3} | 1.0 | {'timeout': 3} | 4.011 | 1.0 |  |
| s3_put | lost_ack | 3 | 1 | {'0': 3} | 0.0 | {'error': 3} | 0.041 |  |  |
| s3_put | none | 3 | 1 | {'1': 3} | 1.0 | {'ok': 3} | 0.051 |  | 1.0 |
| s3_put | not_exec_err | 3 | 0 | {'0': 3} | 1.0 | {'error': 3} | 0.037 |  |  |
| s3_put | not_exec_to | 3 | 0 | {'0': 3} | 1.0 | {'timeout': 3} | 4.005 |  |  |
| s3_put | redelivery | 3 | 1 | {'1': 3} | 1.0 | {'ok': 3} | 0.036 |  |  |
| tb_transfer | held | 3 | 1 | {'1': 3} | 1.0 | {'timeout': 3} | 4.012 |  |  |
| tb_transfer | late | 3 | 1 | {'1': 3} | 1.0 | {'timeout': 3} | 4.014 | 1.0 |  |
| tb_transfer | lost_ack | 3 | 1 | {'1': 3} | 1.0 | {'timeout': 3} | 4.012 |  |  |
| tb_transfer | none | 3 | 1 | {'1': 3} | 1.0 | {'ok': 3} | 0.977 |  | 1.0 |
| tb_transfer | not_exec_err | 3 | 0 | {'1': 3} | 0.0 | {'timeout': 3} | 4.011 |  |  |
| tb_transfer | not_exec_to | 3 | 0 | {'0': 2, '1': 1} | 0.667 | {'timeout': 3} | 4.007 |  |  |
| tb_transfer | redelivery | 3 | 1 | {'1': 3} | 1.0 | {'ok': 3} | 0.995 |  |  |

## Observation equivalence of paired modes

TVD = total variation distance between the (kind, exception type) distributions; 0 means the caller cannot tell the modes apart from the error alone.

| service | group | TVD by pair | median elapsed s | equivalent |
|---|---|---|---|---|
| gitea_issue | error | {'lost_ack vs not_exec_err': 0.0} | {'lost_ack': 0.407, 'not_exec_err': 0.454} | True |
| gitea_issue | deadline | {'held vs not_exec_to': 0.0, 'held vs late': 0.0, 'not_exec_to vs late': 0.0} | {'held': 4.013, 'not_exec_to': 4.014, 'late': 4.013} | True |
| mail | error | {'lost_ack vs not_exec_err': 1.0} | {'lost_ack': 0.043, 'not_exec_err': 0.035} | False |
| mail | deadline | {'held vs not_exec_to': 0.0, 'held vs late': 0.0, 'not_exec_to vs late': 0.0} | {'held': 4.003, 'not_exec_to': 4.012, 'late': 4.008} | True |
| pg_row | error | {'lost_ack vs not_exec_err': 0.0} | {'lost_ack': 0.041, 'not_exec_err': 0.056} | True |
| pg_row | deadline | {'held vs not_exec_to': 0.0, 'held vs late': 0.0, 'not_exec_to vs late': 0.0} | {'held': 4.004, 'not_exec_to': 4.01, 'late': 4.006} | True |
| redis_counter | error | {'lost_ack vs not_exec_err': 0.0} | {'lost_ack': 0.021, 'not_exec_err': 0.031} | True |
| redis_counter | deadline | {'held vs not_exec_to': 0.0, 'held vs late': 0.0, 'not_exec_to vs late': 0.0} | {'held': 4.007, 'not_exec_to': 4.004, 'late': 4.01} | True |
| redis_stream | error | {'lost_ack vs not_exec_err': 0.0} | {'lost_ack': 0.021, 'not_exec_err': 0.039} | True |
| redis_stream | deadline | {'held vs not_exec_to': 0.0, 'held vs late': 0.0, 'not_exec_to vs late': 0.0} | {'held': 4.006, 'not_exec_to': 4.007, 'late': 4.005} | True |
| s3_put | error | {'lost_ack vs not_exec_err': 0.0} | {'lost_ack': 0.041, 'not_exec_err': 0.037} | True |
| s3_put | deadline | {'held vs not_exec_to': 0.0, 'held vs late': 0.0, 'not_exec_to vs late': 0.0} | {'held': 4.015, 'not_exec_to': 4.005, 'late': 4.011} | True |
| tb_transfer | error | {'lost_ack vs not_exec_err': 0.0} | {'lost_ack': 4.012, 'not_exec_err': 4.011} | True |
| tb_transfer | deadline | {'held vs not_exec_to': 0.0, 'held vs late': 0.0, 'not_exec_to vs late': 0.0} | {'held': 4.012, 'not_exec_to': 4.007, 'late': 4.014} | True |
