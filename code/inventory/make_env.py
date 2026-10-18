"""Create ROOT/.env from .env.example if missing and fill empty local-service passwords with random values.

Prints nothing but the names of fields it filled. Never prints values.
"""
from __future__ import annotations

import secrets

from common import ROOT

LOCAL_FIELDS = {"POSTGRES_PASSWORD", "GITEA_ADMIN_PASSWORD", "MINIO_ROOT_PASSWORD"}


def main() -> None:
    env_p = ROOT / ".env"
    src = env_p if env_p.exists() else ROOT / ".env.example"
    lines = src.read_text(encoding="utf-8").splitlines()
    out, filled = [], []
    for line in lines:
        if "=" in line and not line.lstrip().startswith("#"):
            k, v = line.split("=", 1)
            if k.strip() in LOCAL_FIELDS and not v.strip():
                line = f"{k}={secrets.token_urlsafe(24)}"
                filled.append(k.strip())
        out.append(line)
    env_p.write_text("\n".join(out) + "\n", encoding="utf-8")
    print("created" if src.name == ".env.example" else "updated", ".env; filled:", ", ".join(filled) or "none")


if __name__ == "__main__":
    main()
