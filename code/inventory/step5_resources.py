"""Step 5 — resource use with all inventory services running."""
from __future__ import annotations

import json

from common import run, save_part
from svc_common import compose


def main() -> None:
    d: dict = {}
    ps = compose("ps", "--format", "{{.Service}}\t{{.State}}")
    d["services_running"] = [l.split("\t")[0] for l in ps["out"].splitlines() if l.endswith("running")]
    st = run(["docker", "stats", "--no-stream", "--format", "{{json .}}"], timeout=120)
    rows = []
    for line in st["out"].splitlines():
        j = json.loads(line)
        if j["Name"].startswith("actrec-inv-"):
            rows.append({"name": j["Name"], "cpu": j["CPUPerc"], "mem": j["MemUsage"], "mem_pct": j["MemPerc"]})
    d["docker_stats"] = rows
    total = 0.0
    for r in rows:
        used = r["mem"].split("/")[0].strip()
        num = float(used[:-3]) if used[-3:] in ("MiB", "GiB", "KiB") else 0.0
        total += num / 1024 if used.endswith("KiB") else num * 1024 if used.endswith("GiB") else num
    d["docker_mem_total_used_mib"] = round(total, 1)
    mem = run(["powershell", "-NoProfile", "-Command",
               "Get-CimInstance Win32_OperatingSystem | Select-Object TotalVisibleMemorySize, FreePhysicalMemory | ConvertTo-Json -Compress"])
    m = json.loads(mem["out"])
    d["host_ram_gb"] = {"total": round(int(m["TotalVisibleMemorySize"]) / 1048576, 2),
                        "free": round(int(m["FreePhysicalMemory"]) / 1048576, 2)}
    d["seaweedfs_version"] = compose("exec", "-T", "seaweedfs", "weed", "version")["out"]
    d["redis_image_version"] = compose("exec", "-T", "redis", "redis-server", "--version")["out"]
    save_part("05_resources", d)
    print(json.dumps(d, indent=1))


if __name__ == "__main__":
    main()
