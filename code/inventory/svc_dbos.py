"""Step 4 — DBOS against the inventory PostgreSQL: step inserts a row, raises after the insert once, is retried."""
from __future__ import annotations

import json
import time
import uuid
from importlib.metadata import version

import psycopg

from common import save_part
from svc_common import ENV, PG_DSN, exc_info

ATTEMPTS: dict[str, int] = {}


def main() -> None:
    d: dict = {"dbos_version": version("dbos")}
    with psycopg.connect(PG_DSN, autocommit=True) as c:
        if not c.execute("select 1 from pg_database where datname='actrec_dbos_sys'").fetchone():
            c.execute("create database actrec_dbos_sys")
    from dbos import DBOS, DBOSConfig

    sys_url = f"postgresql://actrec:{ENV.get('POSTGRES_PASSWORD', '')}@localhost:5432/actrec_dbos_sys"

    @DBOS.step(retries_allowed=True, max_attempts=3, interval_seconds=0.2, backoff_rate=1.0)
    def insert_then_fail_once(op_id: str) -> int:
        ATTEMPTS[op_id] = ATTEMPTS.get(op_id, 0) + 1
        with psycopg.connect(PG_DSN, autocommit=True) as c:
            c.execute("insert into inv_ops(op_id, payload) values (%s, %s)", (op_id, f"dbos attempt {ATTEMPTS[op_id]}"))
        if ATTEMPTS[op_id] == 1:
            raise RuntimeError("simulated crash after the insert committed")
        return ATTEMPTS[op_id]

    @DBOS.workflow()
    def insert_workflow(op_id: str) -> int:
        return insert_then_fail_once(op_id)

    config: DBOSConfig = {"name": "actrec-inventory", "system_database_url": sys_url, "log_level": "WARNING"}
    t = time.perf_counter()
    try:
        DBOS(config=config)
        DBOS.launch()
        d["launch_s"] = round(time.perf_counter() - t, 3)
        op = str(uuid.uuid4())
        t = time.perf_counter()
        d["final_attempt"] = insert_workflow(op)
        d["workflow_s"] = round(time.perf_counter() - t, 3)
        with psycopg.connect(PG_DSN, autocommit=True) as c:
            d["rows_afterwards"] = c.execute("select count(*) from inv_ops where op_id = %s", (op,)).fetchone()[0]
        d["at_least_once_confirmed"] = d["rows_afterwards"] == 2
    except Exception as e:
        d["error"] = exc_info(e)
    finally:
        try:
            DBOS.destroy()
        except Exception:
            pass
    save_part("04_dbos", d)
    print(json.dumps(d, indent=1))


if __name__ == "__main__":
    main()
