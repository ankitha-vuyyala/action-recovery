"""Step 4 — PostgreSQL and Redis checks."""
from __future__ import annotations

import time
import uuid

import psycopg
import redis

from common import save_part
from svc_common import PG_DSN, exc_info, lat_stats


def pg() -> dict:
    d: dict = {}
    try:
        with psycopg.connect(PG_DSN, autocommit=True) as c:
            d["server_version"] = c.execute("show server_version").fetchone()[0]
            c.execute("create table if not exists inv_ops (id bigserial primary key, op_id text not null, payload text,"
                      " created_at timestamptz default now())")
            c.execute("create index if not exists inv_ops_op_id on inv_ops(op_id)")
            op = str(uuid.uuid4())
            c.execute("insert into inv_ops(op_id, payload) values (%s, %s)", (op, "hello"))
            row = c.execute("select op_id, payload from inv_ops where op_id = %s", (op,)).fetchone()
            d["insert_select_ok"] = row == (op, "hello")
            samples = []
            for _ in range(20):
                t = time.perf_counter()
                c.execute("select id from inv_ops where op_id = %s", (op,)).fetchone()
                samples.append(time.perf_counter() - t)
            d["select_by_op_id_roundtrip"] = lat_stats(samples)
            samples = []
            for i in range(20):
                t = time.perf_counter()
                c.execute("insert into inv_ops(op_id, payload) values (%s, %s)", (str(uuid.uuid4()), f"lat{i}"))
                samples.append(time.perf_counter() - t)
            d["insert_autocommit_roundtrip"] = lat_stats(samples)
    except Exception as e:
        d["error"] = exc_info(e)
    return d


def rd() -> dict:
    d: dict = {}
    try:
        r = redis.Redis(port=6379, decode_responses=True)
        d["server_version"] = r.info("server")["redis_version"]
        op = str(uuid.uuid4())
        sid = r.xadd("inv:stream", {"op_id": op, "action": "demo"})
        rng = r.xrange("inv:stream", min=sid, max=sid)
        d["xadd_xrange_ok"] = bool(rng) and rng[0][1].get("op_id") == op
        d["xadd_id"] = sid
        key = f"inv:nx:{op}"
        first = r.set(key, "1", nx=True, ex=60)
        second = r.set(key, "2", nx=True, ex=60)
        d["set_nx"] = {"first": bool(first), "second": second, "value_after": r.get(key),
                       "second_rejected": second is None}
        samples = []
        for _ in range(20):
            t = time.perf_counter()
            r.ping()
            samples.append(time.perf_counter() - t)
        d["ping"] = lat_stats(samples)
        samples = []
        for _ in range(20):
            t = time.perf_counter()
            r.xadd("inv:stream", {"op_id": str(uuid.uuid4())})
            samples.append(time.perf_counter() - t)
        d["xadd"] = lat_stats(samples)
    except Exception as e:
        d["error"] = exc_info(e)
    return d


if __name__ == "__main__":
    out = {"postgres": pg(), "redis": rd()}
    save_part("04_pg_redis", out)
    import json
    print(json.dumps(out, indent=1))
