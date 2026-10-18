"""Pack the per-episode folders and the model response cache into release archives.

    .venv\\Scripts\\python scripts\\pack_raw_runs.py            (from the repository root)
    .venv\\Scripts\\python scripts\\pack_raw_runs.py --check    (scan only, write nothing)

Writes release/raw_<grid>.tar.gz (runs/<grid>/episodes/) for every grid and release/response_cache.tar.gz
(runs/cache/). These folders are git-ignored because they hold about 200,000 small files; upload the archives as
GitHub release assets. Extracting an archive in the repository root restores the original paths.

Every file is scanned while it is packed. If a file contains a value from .env, or something that looks like an API
key or a private key, the script stops and deletes everything it wrote. The values themselves are never printed,
only the variable names and file paths. Text that contains the absolute path of this checkout (or a path given with
--redact) is replaced by "<repo>" in the archived copy, so the archive does not reveal the local user name. Files on
disk are never changed. Progress is printed every few thousand files.
"""
from __future__ import annotations

import argparse
import io
import re
import sys
import tarfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "release"
# A key starts a token: a match in the middle of a longer base64 string (such as the models' encrypted reasoning
# blobs, "encrypted_content") is a chance substring of ciphertext, not a key.
KEYLIKE = re.compile(rb"(?<![A-Za-z0-9_+/=-])(?:sk-[A-Za-z0-9_-]{20,}|sk-proj-|gsk_[A-Za-z0-9]{20,}|ghp_[A-Za-z0-9]{20,}"
                     rb"|AKIA[0-9A-Z]{16})|-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----")
SKIP_ENV = {"OLLAMA_BASE_URL", "MAX_SPEND_USD", "MAX_SPEND_PER_RUN_USD", "MINIO_ROOT_USER"}


def env_values() -> list[tuple[str, bytes]]:
    f = ROOT / ".env"
    if not f.exists():
        return []
    out = []
    for line in f.read_text(encoding="utf-8", errors="ignore").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        v = v.strip().strip('"').strip("'")
        if k.strip() not in SKIP_ENV and len(v) >= 8:
            out.append((k.strip(), v.encode()))
    return out


def path_forms(extra: list[str]) -> list[bytes]:
    """Spellings of this checkout's absolute path as they appear in logs and JSON (with escaped backslashes)."""
    forms = set()
    for p in [str(ROOT)] + list(extra):
        forms |= {p, p.replace("\\", "/"), p.replace("\\", "\\\\"), p.replace("/", "\\"), p.replace("/", "\\\\")}
    return sorted((f.encode() for f in forms if len(f) > 3), key=len, reverse=True)


def sources() -> list[tuple[str, Path]]:
    runs = ROOT / "runs"
    out = [(f"raw_{d.parent.name}", d) for d in sorted(runs.glob("*/episodes")) if d.is_dir()]
    if (runs / "cache").is_dir():
        out.append(("response_cache", runs / "cache"))
    return out


def problems_in(data: bytes, rel: str, secrets: list[tuple[str, bytes]]) -> list[str]:
    out = [f"{rel}: contains the value of {name}" for name, v in secrets if v in data]
    if KEYLIKE.search(data):
        out.append(f"{rel}: contains something that looks like a key")
    return out


def main(argv: list[str]) -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="scan only, write nothing")
    ap.add_argument("--redact", action="append", default=[], help="another absolute path to replace by <repo>")
    args = ap.parse_args(argv)
    secrets, forms = env_values(), path_forms(args.redact)
    plan = [(name, src, sorted(p for p in src.rglob("*") if p.is_file())) for name, src in sources()]
    total = sum(len(fs) for _, _, fs in plan)
    print(f"{len(plan)} archives, {total} files; checking for {len(secrets)} .env values and key patterns", flush=True)
    if not args.check:
        OUT.mkdir(exist_ok=True)
    problems, done, written, t0 = [], 0, [], time.time()
    for name, src, fs in plan:
        part = OUT / f"{name}.tar.gz.part"
        tar = None if args.check else tarfile.open(part, "w:gz")
        redacted = 0
        for f in fs:
            data = f.read_bytes()
            rel = f.relative_to(ROOT).as_posix()
            problems += problems_in(data, rel, secrets)
            if tar is not None and not problems:
                new = data
                for form in forms:
                    new = new.replace(form, b"<repo>")
                redacted += new != data
                info = tarfile.TarInfo(rel)
                info.size, info.mtime = len(new), int(f.stat().st_mtime)
                tar.addfile(info, io.BytesIO(new))
            done += 1
            if done % 5000 == 0:
                print(f"  {done} of {total} files ({time.time() - t0:.0f} s)", flush=True)
        if tar is not None:
            tar.close()
            written.append((part, redacted, len(fs)))
        if problems:
            break
    if problems:
        for part, _, _ in written:
            part.unlink(missing_ok=True)
        print("STOPPED, nothing kept. Remove or redact these first:")
        for p in problems[:50]:
            print("  " + p)
        sys.exit(1)
    print("scan clean", flush=True)
    for part, redacted, n in written:
        dest = part.with_suffix("")                             # drop ".part"
        part.replace(dest)
        print(f"{dest.relative_to(ROOT).as_posix()}: {n} files, {dest.stat().st_size / 1e6:.1f} MB"
              + (f" ({redacted} with the local path replaced by <repo>)" if redacted else ""))


if __name__ == "__main__":
    main(sys.argv[1:])
