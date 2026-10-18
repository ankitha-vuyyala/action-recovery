"""Scan inventory outputs for user name, machine name, e-mail, home path and .env secret values.

Prints only file names and match counts, never the matched values.
"""
from __future__ import annotations

import os
import re
from pathlib import Path

from common import ROOT, load_env

TARGETS = [ROOT / "docs" / "00_inventory_report.md", *sorted((ROOT / "runs" / "inventory").rglob("*.json")),
           *sorted((ROOT / "code" / "inventory").glob("*.py")), *sorted((ROOT / "docker" / "inventory").glob("*.yml"))]


def main() -> None:
    env = load_env()
    secrets = [v for k, v in env.items() if any(t in k for t in ("KEY", "PASSWORD", "SECRET", "TOKEN")) and len(v) >= 6]
    pats = {
        "user": re.compile(r"(?<![A-Za-z0-9])" + re.escape(os.environ.get("USERNAME", "\0")) + r"(?![A-Za-z0-9])", re.I),
        "host": re.compile(re.escape(os.environ.get("COMPUTERNAME", "\0")), re.I),
        "email": re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"),
        "home": re.compile(re.escape(str(Path.home())).replace(r"\\", r"[\\/]+"), re.I),
    }
    bad = 0
    for f in TARGETS:
        t = f.read_text(encoding="utf-8", errors="replace")
        hits = {k: len(p.findall(t)) for k, p in pats.items()}
        hits["secret"] = sum(t.count(s) for s in secrets)
        # e-mail pattern in scripts: allow the synthetic *.invalid test addresses
        if f.suffix == ".py":
            hits["email"] = len([m for m in pats["email"].findall(t) if not m.endswith(".invalid")])
        if any(hits.values()):
            bad += 1
            print(f.relative_to(ROOT), {k: v for k, v in hits.items() if v})
    print(f"scanned {len(TARGETS)} files; files with findings: {bad}")


if __name__ == "__main__":
    main()
