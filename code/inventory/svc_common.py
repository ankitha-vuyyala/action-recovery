"""Helpers shared by the step-4 service scripts (run with ROOT/.venv python)."""
from __future__ import annotations

import socket
import statistics
import time

from common import ROOT, load_env, run

ENV = load_env()
COMPOSE = ["docker", "compose", "-p", "actrec-inv", "--env-file", str(ROOT / ".env"),
           "-f", str(ROOT / "docker" / "inventory" / "compose.yml")]
PG_DSN = f"host=localhost port=5432 dbname=actrec user=actrec password={ENV.get('POSTGRES_PASSWORD', '')}"
S3_KEY = ENV.get("MINIO_ROOT_USER", "actrec")
S3_SECRET = ENV.get("MINIO_ROOT_PASSWORD", "")


def compose(*args: str, timeout: float = 600, extra_files: list[str] | None = None) -> dict:
    cmd = list(COMPOSE)
    for f in extra_files or []:
        cmd += ["-f", str(ROOT / "docker" / "inventory" / f)]
    return run(cmd + list(args), timeout=timeout)


def tcp_open(port: int, host: str = "127.0.0.1", timeout: float = 1.0) -> bool:
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


def wait_until(probe, timeout: float = 180, interval: float = 0.5):
    """Return seconds until probe() is truthy, or None on timeout."""
    t0 = time.perf_counter()
    while time.perf_counter() - t0 < timeout:
        try:
            if probe():
                return round(time.perf_counter() - t0, 2)
        except Exception:
            pass
        time.sleep(interval)
    return None


def lat_stats(samples_s: list[float]) -> dict:
    ms = [x * 1000 for x in samples_s]
    return {"n": len(ms), "median_ms": round(statistics.median(ms), 3), "min_ms": round(min(ms), 3),
            "max_ms": round(max(ms), 3)}


def exc_info(e: BaseException) -> dict:
    return {"type": f"{type(e).__module__}.{type(e).__name__}", "message": str(e)[:300]}
