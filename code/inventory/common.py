"""Shared helpers for the stage-2 inventory scripts.

Every value written to disk goes through `redact()` so that the Windows user
name, machine name, e-mail addresses, absolute home paths and anything that
looks like a secret never land in an output file.
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RUNS = ROOT / "runs" / "inventory"
PARTS = RUNS / "parts"
PARTS.mkdir(parents=True, exist_ok=True)

_USER = os.environ.get("USERNAME") or os.environ.get("USER") or ""
_HOST = os.environ.get("COMPUTERNAME") or ""
_HOME = str(Path.home())

_EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
# Common token shapes (OpenAI, Groq, OpenRouter, Google, GitHub, Gitea sha1 tokens printed by the CLI)
_TOKEN_RES = [
    re.compile(r"sk-[A-Za-z0-9_\-]{16,}"),
    re.compile(r"gsk_[A-Za-z0-9]{16,}"),
    re.compile(r"AIza[0-9A-Za-z_\-]{20,}"),
    re.compile(r"gh[pousr]_[A-Za-z0-9]{20,}"),
]
_SECRET_VALUES: list[str] = []


def register_secret(value: str | None) -> None:
    """Remember a secret value so redact() strips it from any output."""
    if value and len(value) >= 6 and value not in _SECRET_VALUES:
        _SECRET_VALUES.append(value)


def _home_variants() -> list[str]:
    h = _HOME
    out = {h, h.replace("\\", "/"), h.replace("\\", "\\\\")}
    if len(h) > 2 and h[1] == ":":
        drive = h[0].lower()
        out.add("/" + drive + h[2:].replace("\\", "/"))
        out.add("/mnt/" + drive + h[2:].replace("\\", "/"))
    return sorted(out, key=len, reverse=True)


def redact(text):
    if isinstance(text, dict):
        return {redact(k): redact(v) for k, v in text.items()}
    if isinstance(text, (list, tuple)):
        return [redact(v) for v in text]
    if not isinstance(text, str):
        return text
    s = text
    for sec in _SECRET_VALUES:
        s = s.replace(sec, "<redacted>")
    for pat in _TOKEN_RES:
        s = pat.sub("<redacted-token>", s)
    s = _EMAIL_RE.sub("<email>", s)
    for hv in _home_variants():
        s = re.sub(re.escape(hv), "~", s, flags=re.IGNORECASE)
    if _HOST:
        s = re.sub(re.escape(_HOST), "<host>", s, flags=re.IGNORECASE)
    if _USER:
        s = re.sub(r"(?<![A-Za-z0-9])" + re.escape(_USER) + r"(?![A-Za-z0-9])", "<user>", s, flags=re.IGNORECASE)
    return s


def run(cmd, timeout: float = 120, shell: bool = False, input: str | None = None, env=None) -> dict:
    """Run a command; return exit code, redacted stdout/stderr (first ~20 lines on error) and elapsed time."""
    t0 = time.perf_counter()
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, shell=shell,
                           input=input, env=env, encoding="utf-8", errors="replace")
        rc, out, err = p.returncode, p.stdout, p.stderr
    except FileNotFoundError as e:
        rc, out, err = -1, "", f"missing: {e}"
    except subprocess.TimeoutExpired as e:
        rc, out, err = -2, (e.stdout or "") if isinstance(e.stdout, str) else "", f"timeout after {timeout}s"
    return {"rc": rc, "out": redact(out.strip()), "err": redact(err.strip()),
            "elapsed_s": round(time.perf_counter() - t0, 3)}


def first_lines(s: str, n: int = 20) -> str:
    return "\n".join((s or "").splitlines()[:n])


def save_part(name: str, data) -> Path:
    path = PARTS / f"{name}.json"
    path.write_text(json.dumps(redact(data), indent=2, ensure_ascii=False), encoding="utf-8")
    return path


def load_env() -> dict:
    """Parse ROOT/.env into a dict without printing anything. Secret values are registered for redaction."""
    env = {}
    p = ROOT / ".env"
    if not p.exists():
        return env
    for line in p.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        v = v.strip().strip('"').strip("'")
        env[k.strip()] = v
        if any(t in k.upper() for t in ("KEY", "PASSWORD", "SECRET", "TOKEN")):
            register_secret(v)
    return env
