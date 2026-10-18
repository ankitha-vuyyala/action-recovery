"""Step 2 — tooling versions and project venv at ROOT/.venv (stdlib only; run with system Python)."""
from __future__ import annotations

import json
import re
from pathlib import Path

from common import ROOT, first_lines, run, save_part

PACKAGES = ["openai", "httpx", "psycopg[binary]", "redis", "boto3", "tigerbeetle", "temporalio", "dbos",
            "python-docx", "docx2pdf", "matplotlib", "pandas", "numpy", "scipy", "statsmodels", "pyyaml", "pytest"]


def ver(cmd: list[str]) -> str:
    r = run(cmd, timeout=60)
    if r["rc"] == -1:
        return "missing"
    txt = (r["out"] or r["err"]).splitlines()
    return txt[0].strip() if txt else f"rc={r['rc']}"


def word_present() -> dict:
    ps = ["powershell", "-NoProfile", "-NonInteractive", "-Command"]
    reg = run(ps + ["(Get-ItemProperty 'HKLM:\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\App Paths\\Winword.exe' -ErrorAction SilentlyContinue).'(default)'"])
    paths = [r"C:\Program Files\Microsoft Office\root\Office16\WINWORD.EXE",
             r"C:\Program Files (x86)\Microsoft Office\root\Office16\WINWORD.EXE"]
    found = [p for p in paths if Path(p).exists()]
    return {"present": bool(reg["out"]) or bool(found), "app_paths_registry": reg["out"] or None, "known_path_hits": found}


def libreoffice() -> str:
    v = ver(["soffice", "--version"])
    if v != "missing":
        return v
    for p in [r"C:\Program Files\LibreOffice\program\soffice.com", r"C:\Program Files (x86)\LibreOffice\program\soffice.com"]:
        if Path(p).exists():
            return ver([p, "--version"])
    return "missing"


def main() -> None:
    d: dict = {}
    d["py_launcher"] = run(["py", "-0p"])["out"].splitlines()
    d["python_on_path"] = ver(["python", "--version"])
    conda = run(["conda", "info", "--envs"])
    d["conda"] = "missing" if conda["rc"] == -1 else [l.split()[0] for l in conda["out"].splitlines() if l and not l.startswith("#")]
    d["uv"] = ver(["uv", "--version"])
    for tool, cmd in {"git": ["git", "--version"], "gh": ["gh", "--version"], "node": ["node", "--version"],
                      "npm": ["npm.cmd", "--version"], "pandoc": ["pandoc", "--version"]}.items():
        d[tool] = ver(cmd)
    d["libreoffice"] = libreoffice()
    d["ms_word"] = word_present()

    # choose interpreter: newest 3.12, else 3.11, else 3.13
    chosen = None
    for v in ("3.12", "3.11", "3.13"):
        if any(re.search(rf"-V:{re.escape(v)}\b", l) for l in d["py_launcher"]):
            chosen = v
            break
    d["venv_python_requested"] = chosen
    venv = ROOT / ".venv"
    vpy = venv / "Scripts" / "python.exe"
    if not vpy.exists():
        d["venv_create"] = run(["py", f"-{chosen}", "-m", "venv", str(venv)], timeout=300)
    d["venv_python"] = ver([str(vpy), "--version"])
    run([str(vpy), "-m", "pip", "install", "-q", "--upgrade", "pip"], timeout=300)

    results = {}
    for pkg in PACKAGES:
        r = run([str(vpy), "-m", "pip", "install", "-q", pkg], timeout=900)
        results[pkg] = "ok" if r["rc"] == 0 else {"error": first_lines(r["err"] or r["out"])}
    d["install_results"] = results
    frz = run([str(vpy), "-m", "pip", "list", "--format=json"])
    installed = {p["name"].lower(): p["version"] for p in json.loads(frz["out"] or "[]")}
    wanted = [re.sub(r"\[.*\]", "", p).lower() for p in PACKAGES] + ["psycopg-binary"]
    d["installed_versions"] = {k: installed.get(k, "not installed") for k in wanted}
    d["failed_packages"] = [k for k, v in results.items() if v != "ok"]
    save_part("02_tooling", d)


if __name__ == "__main__":
    main()
