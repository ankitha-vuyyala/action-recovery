"""Step 8 — shallow-clone reference repositories into ROOT/external (read-only; their code is never run),
and search GitHub (unauthenticated REST API) for a public LIMBO benchmark release."""
from __future__ import annotations

import json
import os
from pathlib import Path

import httpx

from common import ROOT, first_lines, run, save_part

REPOS = ["https://github.com/shushuyang231/ambiguous-tool-outcomes-benchmark",
         "https://github.com/gssanjana4/idempotencybench",
         "https://github.com/flame-stream/mcp-annotation-census"]
EXT = ROOT / "external"
MARKERS = {"pyproject.toml": "Python", "requirements.txt": "Python", "setup.py": "Python", "package.json": "Node.js",
           "go.mod": "Go", "Cargo.toml": "Rust", "pom.xml": "Java (Maven)", "build.gradle": "Java/Kotlin (Gradle)",
           "Dockerfile": "Docker", "docker-compose.yml": "Docker Compose", "compose.yml": "Docker Compose",
           "environment.yml": "Conda"}
GH = httpx.Client(base_url="https://api.github.com", timeout=20,
                  headers={"Accept": "application/vnd.github+json", "User-Agent": "actrec-inventory"})


def dir_size_mb(p: Path) -> float:
    total = 0
    for dp, _, files in os.walk(p):
        if ".git" in Path(dp).parts:
            continue
        total += sum((Path(dp) / f).stat().st_size for f in files)
    return round(total / 1e6, 2)


def repo_info(url: str) -> dict:
    owner_repo = url.removeprefix("https://github.com/")
    dest = EXT / owner_repo.replace("/", "__")
    r: dict = {"url": url}
    if not dest.exists():
        cl = run(["git", "clone", "--depth", "1", url, str(dest)], timeout=300,
                 env={**os.environ, "GIT_TERMINAL_PROMPT": "0"})
        r["clone"] = {"rc": cl["rc"], "err": first_lines(cl["err"], 20) if cl["rc"] else None}
    r["reachable"] = dest.exists() and (dest / ".git").exists()
    if not r["reachable"]:
        api = GH.get(f"/repos/{owner_repo}")
        r["github_api_status"] = api.status_code
        return r
    r["commit"] = run(["git", "-C", str(dest), "rev-parse", "HEAD"])["out"]
    r["commit_date"] = run(["git", "-C", str(dest), "log", "-1", "--format=%cs"])["out"]
    top = sorted(os.listdir(dest))
    r["top_level"] = [t + ("/" if (dest / t).is_dir() else "") for t in top if t != ".git"]
    r["license_files"] = [t for t in top if t.upper().startswith(("LICENSE", "LICENCE", "COPYING"))] or "none found"
    if isinstance(r["license_files"], list):
        head = (dest / r["license_files"][0]).read_text(encoding="utf-8", errors="replace")[:200].splitlines()
        r["license_first_line"] = next((l.strip() for l in head if l.strip()), "")
    r["size_mb_working_tree"] = dir_size_mb(dest)
    r["runtime_markers"] = sorted({v for k, v in MARKERS.items() if (dest / k).exists()})
    api = GH.get(f"/repos/{owner_repo}/languages")
    r["github_languages"] = api.json() if api.status_code == 200 else f"status {api.status_code}"
    meta = GH.get(f"/repos/{owner_repo}")
    if meta.status_code == 200:
        m = meta.json()
        r["github_license_spdx"] = (m.get("license") or {}).get("spdx_id")
        r["stars"] = m.get("stargazers_count")
        r["description"] = m.get("description")
    return r


def limbo_search() -> dict:
    queries = ['LIMBO benchmark exactly-once', '"Where Does Exactly-Once Live"', '2609.29095',
               'limbo exactly-once agents', 'LIMBO in:name exactly-once in:description']
    out = {"queries": {}, "candidates": []}
    for q in queries:
        s = GH.get("/search/repositories", params={"q": q, "per_page": 10})
        if s.status_code != 200:
            out["queries"][q] = f"status {s.status_code}"
            continue
        items = s.json().get("items", [])
        out["queries"][q] = [i["html_url"] for i in items]
        for i in items:
            text = f"{i.get('name')} {i.get('description') or ''}".lower()
            if "limbo" in text and ("exactly" in text or "2609.29095" in text or "agent" in text):
                out["candidates"].append({"url": i["html_url"], "description": i.get("description")})
    seen = set()
    out["candidates"] = [c for c in out["candidates"] if not (c["url"] in seen or seen.add(c["url"]))]
    out["result"] = out["candidates"][0]["url"] if out["candidates"] else "not found"
    for c in out["candidates"]:  # verification from metadata + README only (not cloned, not run)
        full = c["url"].removeprefix("https://github.com/")
        m = GH.get(f"/repos/{full}")
        if m.status_code == 200:
            mj = m.json()
            c.update(created_at=mj.get("created_at"), pushed_at=mj.get("pushed_at"), stars=mj.get("stargazers_count"),
                     license_spdx=(mj.get("license") or {}).get("spdx_id"), language=mj.get("language"))
        rd = GH.get(f"/repos/{full}/readme")
        if rd.status_code == 200:
            import base64
            txt = base64.b64decode(rd.json()["content"]).decode("utf-8", "replace")
            c["readme_cites_arxiv_2609_29095"] = "2609.29095" in txt
            c["readme_cites_title"] = "where does exactly-once live" in txt.lower()
        c["verified"] = bool(c.get("readme_cites_arxiv_2609_29095") or c.get("readme_cites_title"))
    return out


def main() -> None:
    EXT.mkdir(exist_ok=True)
    d = {"repos": [repo_info(u) for u in REPOS], "limbo_search": limbo_search(),
         "note": "shallow clones in external/ (git-ignored); no code from them was executed"}
    save_part("08_repos", d)
    print(json.dumps(d, indent=1)[:6000])


if __name__ == "__main__":
    main()
