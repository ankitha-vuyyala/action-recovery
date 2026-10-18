"""Step 4 — Temporal (dev server image): activity inserts a row, raises after the insert on attempt 1, is retried."""
from __future__ import annotations

import asyncio
import json
import time
import uuid
from datetime import timedelta
from importlib.metadata import version

import psycopg
from temporalio import activity, workflow
from temporalio.client import Client
from temporalio.common import RetryPolicy
from temporalio.worker import UnsandboxedWorkflowRunner, Worker

from common import save_part
from svc_common import PG_DSN, compose, exc_info

QUEUE = "inv-queue"


@activity.defn
def insert_then_fail_once(op_id: str) -> int:
    with psycopg.connect(PG_DSN, autocommit=True) as c:
        c.execute("insert into inv_ops(op_id, payload) values (%s, %s)", (op_id, f"temporal attempt {activity.info().attempt}"))
    if activity.info().attempt == 1:
        raise RuntimeError("simulated crash after the insert committed")
    return activity.info().attempt


@workflow.defn
class InsertWorkflow:
    @workflow.run
    async def run(self, op_id: str) -> int:
        return await workflow.execute_activity(
            insert_then_fail_once, op_id, start_to_close_timeout=timedelta(seconds=10),
            retry_policy=RetryPolicy(initial_interval=timedelta(milliseconds=200), maximum_attempts=3))


async def main() -> None:
    d: dict = {"mode": "image temporalio/temporal:latest `server start-dev`", "sdk_version": version("temporalio")}
    d["server_cli_version"] = compose("exec", "-T", "temporal", "temporal", "--version")["out"]
    t = time.perf_counter()
    client = await Client.connect("localhost:7233")
    d["client_connect_s"] = round(time.perf_counter() - t, 3)
    try:
        info = await client.service_client.workflow_service.get_system_info(
            __import__("temporalio.api.workflowservice.v1", fromlist=["GetSystemInfoRequest"]).GetSystemInfoRequest())
        d["server_version"] = info.server_version
    except Exception as e:
        d["server_version"] = exc_info(e)
    op = str(uuid.uuid4())
    import concurrent.futures as cf
    with cf.ThreadPoolExecutor(4) as ex:
        async with Worker(client, task_queue=QUEUE, workflows=[InsertWorkflow], activities=[insert_then_fail_once],
                          activity_executor=ex, workflow_runner=UnsandboxedWorkflowRunner()):
            t = time.perf_counter()
            result = await client.execute_workflow(InsertWorkflow.run, op, id=f"inv-{op}", task_queue=QUEUE)
            d["workflow_s"] = round(time.perf_counter() - t, 3)
    d["final_attempt"] = result
    with psycopg.connect(PG_DSN, autocommit=True) as c:
        d["rows_afterwards"] = c.execute("select count(*) from inv_ops where op_id = %s", (op,)).fetchone()[0]
    d["at_least_once_confirmed"] = d["rows_afterwards"] == 2
    save_part("04_temporal", d)
    print(json.dumps(d, indent=1))


if __name__ == "__main__":
    asyncio.run(main())
