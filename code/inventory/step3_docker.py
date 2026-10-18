"""Step 3 — Docker engine facts, hello-world, disk usage, host port availability."""
from __future__ import annotations

import json
import socket

from common import first_lines, run, save_part

PORTS = [1025, 3000, 3001, 5432, 6379, 7233, 8025, 8233, 8333, 8474, 9000, 9001, 3002] + list(range(26000, 26100))


def port_owners() -> dict[int, str]:
    """Map listening TCP port -> owning process name (read-only query)."""
    cmd = ("Get-NetTCPConnection -State Listen | ForEach-Object { "
           "$p = Get-Process -Id $_.OwningProcess -ErrorAction SilentlyContinue; "
           "[pscustomobject]@{port=$_.LocalPort; addr=$_.LocalAddress; proc=$p.ProcessName} } | ConvertTo-Json -Compress")
    r = run(["powershell", "-NoProfile", "-NonInteractive", "-Command", cmd], timeout=120)
    owners: dict[int, str] = {}
    try:
        rows = json.loads(r["out"])
        for row in rows if isinstance(rows, list) else [rows]:
            owners.setdefault(int(row["port"]), f"{row['proc']} ({row['addr']})")
    except Exception:
        pass
    return owners


def bindable(port: int) -> bool:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.bind(("0.0.0.0", port))
        return True
    except OSError:
        return False
    finally:
        s.close()


def main() -> None:
    d: dict = {}
    v = run(["docker", "version", "--format", "{{json .}}"])
    try:
        vj = json.loads(v["out"])
        d["docker_version"] = {"client": vj["Client"]["Version"], "server": vj["Server"]["Version"],
                               "server_os_arch": f"{vj['Server']['Os']}/{vj['Server']['Arch']}",
                               "api": vj["Server"]["ApiVersion"]}
    except Exception:
        d["docker_version"] = {"error": first_lines(v["out"] + v["err"])}
    d["compose_version"] = run(["docker", "compose", "version"])["out"]
    info = run(["docker", "info", "--format", "{{json .}}"])
    try:
        ij = json.loads(info["out"])
        d["docker_info"] = {k: ij.get(k) for k in ("OperatingSystem", "OSType", "KernelVersion", "NCPU", "MemTotal",
                                                   "Driver", "CgroupVersion", "CgroupDriver", "ServerVersion", "Name")}
        d["docker_info"]["MemTotal_GB"] = round(ij.get("MemTotal", 0) / 1024 ** 3, 2)
        d["docker_info"]["backend"] = "WSL2" if "WSL2" in (ij.get("KernelVersion") or "") or "microsoft" in (ij.get("KernelVersion") or "").lower() else "unknown/Hyper-V"
        d["docker_info"]["Name"] = "<host-vm>"
    except Exception:
        d["docker_info"] = {"error": first_lines(info["out"] + info["err"])}
    hw = run(["docker", "run", "--rm", "hello-world"], timeout=300)
    d["hello_world"] = {"ok": hw["rc"] == 0 and "Hello from Docker" in hw["out"], "elapsed_s": hw["elapsed_s"],
                        "error": None if hw["rc"] == 0 else first_lines(hw["err"])}
    d["system_df"] = run(["docker", "system", "df"])["out"].splitlines()

    owners = port_owners()
    taken = {}
    for p in PORTS:
        if p in owners or not bindable(p):
            taken[str(p)] = owners.get(p, "in use (owner not visible)")
    d["ports_checked"] = "1025,3000,3001,3002,5432,6379,7233,8025,8233,8333,8474,9000,9001,26000-26099"
    d["ports_taken"] = taken
    d["ports_free_count"] = len(PORTS) - len(taken)
    save_part("03_docker", d)


if __name__ == "__main__":
    main()
