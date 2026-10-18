"""Cleanup — stop and remove inventory containers, network and volumes (keeps pulled images)."""
from __future__ import annotations

import json

from common import first_lines, run, save_part
from svc_common import compose


def main() -> None:
    down = compose("--profile", "minio", "down", "-v", "--remove-orphans", timeout=300,
                   extra_files=["compose.tb-unconfined.yml"])
    left_c = run(["docker", "ps", "-a", "--filter", "label=com.docker.compose.project=actrec-inv", "--format", "{{.Names}}"])
    left_v = run(["docker", "volume", "ls", "--filter", "label=com.docker.compose.project=actrec-inv", "--format", "{{.Name}}"])
    left_n = run(["docker", "network", "ls", "--filter", "name=actrec-inv", "--format", "{{.Name}}"])
    imgs = run(["docker", "image", "ls", "--format", "{{.Repository}}:{{.Tag}}"])["out"].splitlines()
    kept = [i for i in imgs if any(s in i for s in ("postgres:16", "gitea/gitea", "mailpit", "tigerbeetle", "seaweedfs",
                                                   "redis:7", "toxiproxy", "temporalio/temporal", "hello-world"))]
    d = {"compose_down_rc": down["rc"], "compose_down_err": first_lines(down["err"]) if down["rc"] else None,
         "containers_left": left_c["out"].splitlines(), "volumes_left": left_v["out"].splitlines(),
         "networks_left": left_n["out"].splitlines(), "images_kept": sorted(kept)}
    d["clean"] = down["rc"] == 0 and not (d["containers_left"] or d["volumes_left"] or d["networks_left"])
    save_part("09_cleanup", d)
    print(json.dumps(d, indent=1))


if __name__ == "__main__":
    main()
