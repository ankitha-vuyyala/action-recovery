"""Step 6 — proxy variables (names only; values redacted except host), DNS, HTTPS reachability, latency.

Only unauthenticated HEAD/GET / requests. A 401/403/404 counts as reachable.
"""
from __future__ import annotations

import os
import socket
import statistics
import time
from urllib.parse import urlparse

import httpx

from common import save_part

HOSTS = ["pypi.org", "github.com", "ghcr.io", "registry-1.docker.io", "api.openai.com",
         "generativelanguage.googleapis.com", "api.groq.com", "openrouter.ai", "huggingface.co"]


def main() -> None:
    d: dict = {}
    proxies = {}
    for k, v in os.environ.items():
        if "proxy" in k.lower():
            host = urlparse(v if "://" in v else "http://" + v).hostname if k.lower() != "no_proxy" else None
            proxies[k] = {"set": bool(v), "host": host}
    d["proxy_env"] = proxies or "none set"
    res = {}
    for h in HOSTS:
        r: dict = {}
        try:
            r["dns"] = bool(socket.getaddrinfo(h, 443))
        except OSError as e:
            r["dns"] = False
            r["dns_error"] = str(e)
        lat, statuses, err = [], [], None
        for _ in range(3):
            t = time.perf_counter()
            try:
                resp = httpx.head(f"https://{h}/", timeout=10, follow_redirects=False)
                statuses.append(resp.status_code)
                lat.append(time.perf_counter() - t)
            except Exception as e:
                err = f"{type(e).__name__}: {e}"[:200]
        r["https_reachable"] = bool(statuses)
        r["statuses"] = statuses
        r["median_ms"] = round(statistics.median(lat) * 1000, 1) if lat else None
        if err:
            r["error"] = err
        res[h] = r
    d["hosts"] = res
    save_part("06_network", d)
    import json
    print(json.dumps(d, indent=1))


if __name__ == "__main__":
    main()
