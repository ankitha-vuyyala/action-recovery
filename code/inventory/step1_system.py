"""Step 1 — system facts (read-only queries). Run with any Python >= 3.9 (stdlib only)."""
from __future__ import annotations

import json
import shutil

from common import ROOT, first_lines, run, save_part


def ps(cmd: str, timeout: float = 60) -> dict:
    return run(["powershell", "-NoProfile", "-NonInteractive", "-Command", cmd], timeout=timeout)


def ps_json(cmd: str):
    r = ps(cmd + " | ConvertTo-Json -Depth 3 -Compress")
    try:
        return json.loads(r["out"]) if r["out"] else None
    except json.JSONDecodeError:
        return {"error": first_lines(r["out"] + "\n" + r["err"])}


def wsl(args: list[str]) -> dict:
    # wsl.exe writes UTF-16LE; decode by stripping NULs
    r = run(["wsl", *args], timeout=60)
    for k in ("out", "err"):
        r[k] = r[k].replace("\x00", "")
    return r


def main() -> None:
    data: dict = {}
    data["os"] = ps_json("Get-CimInstance Win32_OperatingSystem | Select-Object Caption, Version, BuildNumber, OSArchitecture")
    data["os_display_version"] = ps("(Get-ItemProperty 'HKLM:\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion').DisplayVersion")["out"]
    data["cpu"] = ps_json("Get-CimInstance Win32_Processor | Select-Object Name, NumberOfCores, NumberOfLogicalProcessors")
    mem = ps_json("Get-CimInstance Win32_OperatingSystem | Select-Object TotalVisibleMemorySize, FreePhysicalMemory")
    if isinstance(mem, dict) and "TotalVisibleMemorySize" in mem:
        data["ram_gb"] = {"total": round(int(mem["TotalVisibleMemorySize"]) / 1024 / 1024, 2),
                          "free": round(int(mem["FreePhysicalMemory"]) / 1024 / 1024, 2)}
    du = shutil.disk_usage(ROOT)
    data["disk_root_drive"] = {"drive": str(ROOT)[:2], "total_gb": round(du.total / 1e9, 1), "free_gb": round(du.free / 1e9, 1)}

    smi = run(["nvidia-smi", "--query-gpu=name,memory.total,driver_version", "--format=csv,noheader"])
    if smi["rc"] == 0 and smi["out"]:
        gpus = []
        for line in smi["out"].splitlines():
            name, vram, drv = [x.strip() for x in line.split(",")]
            gpus.append({"name": name, "vram": vram, "driver": drv})
        data["gpu"] = gpus
    else:
        data["gpu"] = "none/unknown"
        data["gpu_error"] = first_lines(smi["err"])
    data["gpu_wmi"] = ps_json("Get-CimInstance Win32_VideoController | Select-Object Name, DriverVersion")

    data["wsl_status"] = wsl(["--status"])
    data["wsl_list"] = wsl(["-l", "-v"])
    data["wsl_version"] = wsl(["--version"])

    root_s = str(ROOT).lower()
    onedrive_env = {k: v for k, v in __import__("os").environ.items() if k.lower().startswith("onedrive")}
    in_od = any(v and root_s.startswith(v.lower()) for v in onedrive_env.values())
    docs_redirect = ps("[Environment]::GetFolderPath('MyDocuments')")["out"]
    data["onedrive"] = {
        "onedrive_env_vars_set": sorted(onedrive_env.keys()),
        "root_inside_onedrive": in_od or ("onedrive" in root_s),
        "documents_folder": docs_redirect,
        "root": str(ROOT),
    }
    save_part("01_system", data)


if __name__ == "__main__":
    main()
