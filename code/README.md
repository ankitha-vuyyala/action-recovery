# code/

Python code for the study. Planned modules (filled in stage 4):

- `harness/`  agent loop, tool adapters for each service, response cache, cost ledger with hard cap
- `method/`   the recovery layer (operation IDs, durable intent journal, attribution, state inspection, reconciliation horizon, evidence-gated compensation)
- `baselines/` naive retry, never retry, idempotency keys, workflow engine with retries, verify-before-retry, guard, reflection, checkpoint-rollback with compensation
- `faults/`   fault injection through the network proxy and agent-process kills
- `graders/`  code-only graders that read real service state and the effect ledger (never imported by agents)
- `inventory/` scripts written during the stage-2 inventory
