import json
import time
import requests
from urllib.parse import quote

TARGETS = [
    ("https://www.gula-platform.org/", "GET"),
    ("https://www.gula-platform.org/login", "GET"),
    ("https://www.gula-platform.org/robots.txt", "GET"),
    ("https://www.gula-platform.org/.well-known/security.txt", "GET"),
    ("https://www.gula-platform.org/manifest.webmanifest", "GET"),
    ("https://www.gula-platform.org/sw.js", "GET"),
    ("https://www.gula-platform.org/service-worker.js", "GET"),
    ("https://www.gula-platform.org/api/health", "GET"),
    ("https://www.gula-platform.org/api/v1/health", "GET"),
    ("https://www.gula-platform.org/health", "GET"),
    ("https://api.gula-platform.org/", "GET"),
    ("https://api.gula-platform.org/health", "GET"),
    ("https://api.gula-platform.org/openapi.json", "GET"),
    ("https://api.gula-platform.org/docs", "GET"),
    ("https://www.gula-platform.org/?q=" + quote("<script>alert(1)</script>"), "GET"),
]

HEADERS = {
    "User-Agent": "GULA-authorized-security-audit/1.0",
    "Accept": "text/html,application/json,text/plain,*/*",
}

results = []
for url, method in TARGETS:
    started = time.perf_counter()
    try:
        response = requests.request(method, url, headers=HEADERS, timeout=12, allow_redirects=False)
        elapsed_ms = round((time.perf_counter() - started) * 1000, 1)
        body = response.text[:400].replace("\n", " ")
        results.append({
            "url": url,
            "status": response.status_code,
            "elapsed_ms": elapsed_ms,
            "location": response.headers.get("location"),
            "content_type": response.headers.get("content-type"),
            "server": response.headers.get("server"),
            "allow_origin": response.headers.get("access-control-allow-origin"),
            "body_prefix": body,
            "reflected_test_marker": "<script>" in body or "alert(1)" in body,
        })
    except Exception as exc:
        results.append({"url": url, "error": repr(exc)})

print(json.dumps(results, ensure_ascii=False, indent=2))
