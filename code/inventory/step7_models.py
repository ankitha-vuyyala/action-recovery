"""Step 7 — models via FREE endpoints only.

* .env: key names and non-empty yes/no (values never printed).
* For each provider with a non-empty key: only the model-listing / key-info endpoint listed in
  docs/02_inventory_instructions.md. No generation, embedding or any other paid endpoint.
* Local: ollama --version / list / ps (no pulls), LM Studio presence.
"""
from __future__ import annotations

import json
import os
from pathlib import Path

import httpx

from common import RUNS, load_env, run, save_part

PROVIDERS = {
    "openai": ("OPENAI_API_KEY", "https://api.openai.com/v1/models", lambda k: {"Authorization": f"Bearer {k}"}),
    "gemini": ("GEMINI_API_KEY", "https://generativelanguage.googleapis.com/v1beta/models", lambda k: {"x-goog-api-key": k}),
    "groq": ("GROQ_API_KEY", "https://api.groq.com/openai/v1/models", lambda k: {"Authorization": f"Bearer {k}"}),
    "openrouter": ("OPENROUTER_API_KEY", "https://openrouter.ai/api/v1/models", lambda k: {}),
}


def model_ids(provider: str, j: dict) -> list[str]:
    if provider == "gemini":
        return [m.get("name") for m in j.get("models", [])]
    return [m.get("id") for m in j.get("data", [])]


def main() -> None:
    env = load_env()
    d: dict = {"env_keys": {k: {"non_empty": bool(v)} for k, v in env.items()}}
    prov = {}
    for name, (var, url, hdr) in PROVIDERS.items():
        key = env.get(var, "")
        if not key:
            prov[name] = {"key_present": False, "called": False}
            continue
        r = httpx.get(url, headers=hdr(key), timeout=30)
        rec = {"key_present": True, "called": url, "http_status": r.status_code}
        if r.status_code == 200:
            ids = model_ids(name, r.json())
            (RUNS / f"models_{name}.json").write_text(json.dumps(sorted(i for i in ids if i), indent=1), encoding="utf-8")
            rec["model_count"] = len(ids)
        elif r.status_code in (401, 403):
            rec["note"] = "key rejected (nothing charged)"
        if name == "openrouter":
            k = httpx.get("https://openrouter.ai/api/v1/key", headers={"Authorization": f"Bearer {key}"}, timeout=30)
            rec["key_info_status"] = k.status_code
            if k.status_code == 200:
                kd = k.json().get("data", {})
                rec["key_info"] = {f: kd.get(f) for f in ("limit", "usage", "is_free_tier")}
        prov[name] = rec
    d["providers"] = prov

    loc: dict = {}
    loc["ollama_version"] = run(["ollama", "--version"])["out"] or run(["ollama", "--version"])["err"]
    try:
        tags = httpx.get(env.get("OLLAMA_BASE_URL", "http://localhost:11434") + "/api/tags", timeout=5)
        loc["ollama_server_running"] = tags.status_code == 200
    except Exception as e:
        loc["ollama_server_running"] = False
        loc["ollama_server_error"] = type(e).__name__
    lst = run(["ollama", "list"])
    loc["ollama_list"] = lst["out"].splitlines() if lst["rc"] == 0 else {"rc": lst["rc"], "err": lst["err"][:300]}
    if loc["ollama_server_running"]:
        models = []
        for m in tags.json().get("models", []):
            det = m.get("details", {})
            models.append({"name": m.get("name"), "size_gb": round(m.get("size", 0) / 1e9, 2),
                           "parameter_size": det.get("parameter_size"), "quantization": det.get("quantization_level"),
                           "family": det.get("family")})
        loc["ollama_models"] = models
        ps = run(["ollama", "ps"])
        loc["ollama_ps_loaded"] = ps["out"].splitlines()
    loc["gpu_offload_note"] = "visible only for loaded models via `ollama ps` (PROCESSOR column); no model was loaded or pulled"
    lms_paths = [Path(os.environ.get("LOCALAPPDATA", "")) / "Programs" / "LM Studio",
                 Path.home() / ".lmstudio", Path.home() / ".cache" / "lm-studio"]
    loc["lm_studio"] = {"installed": any(p.exists() for p in lms_paths),
                        "paths_found": [str(p) for p in lms_paths if p.exists()],
                        "lms_cli": run(["lms", "version"])["rc"] == 0}
    d["local"] = loc
    save_part("07_models", d)
    print(json.dumps(d, indent=1))


if __name__ == "__main__":
    main()
