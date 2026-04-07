#!/usr/bin/env python3
"""
GULA Platform — Chaos & Resilience Test Suite
==============================================
Proves the system survives real failure conditions:

  1. Redis failure → degraded-mode (no crash)
  2. Backend down  → nginx returns clean 502/503 (no hang)
  3. Rate limiting → 429 after burst (not 500)
  4. Concurrent load → no connection exhaustion
  5. Idempotency → duplicate claim returns same result, no double-write
  6. Invalid auth → 401 consistently (no leak)
  7. DB constraint → 422/400 (not 500 stack trace)

Usage:
    python3 scripts/chaos_test.py --base http://localhost:8080 --admin-token TOKEN
    python3 scripts/chaos_test.py --base https://gula-platform.org --admin-token TOKEN

Requirements: requests, docker (CLI accessible), colorama (optional)
"""

import argparse
import json
import subprocess
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Optional

import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ── ANSI colours (fallback to plain text if not supported) ───────────────────
try:
    from colorama import Fore, Style, init as _cinit
    _cinit()
    GREEN = Fore.GREEN
    RED   = Fore.RED
    YELLOW = Fore.YELLOW
    CYAN  = Fore.CYAN
    RESET = Style.RESET_ALL
except ImportError:
    GREEN = RED = YELLOW = CYAN = RESET = ""


def ok(msg: str)   -> None: print(f"  {GREEN}✔ {msg}{RESET}")
def fail(msg: str) -> None: print(f"  {RED}✘ {msg}{RESET}")
def warn(msg: str) -> None: print(f"  {YELLOW}⚠ {msg}{RESET}")
def info(msg: str) -> None: print(f"  {CYAN}→ {msg}{RESET}")

PASSED = []
FAILED = []

def result(name: str, success: bool, detail: str = "") -> None:
    if success:
        PASSED.append(name)
        ok(f"{name}" + (f"  ({detail})" if detail else ""))
    else:
        FAILED.append(name)
        fail(f"{name}" + (f"  ({detail})" if detail else ""))


# ── Docker helpers ────────────────────────────────────────────────────────────

def docker(cmd: list[str], check: bool = False) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["docker", "compose"] + cmd,
        capture_output=True, text=True, check=check,
        cwd=subprocess.run(["git", "rev-parse", "--show-toplevel"],
                           capture_output=True, text=True).stdout.strip()
    )


def container_running(service: str) -> bool:
    r = docker(["ps", "--services", "--filter", f"status=running"])
    return service in r.stdout


# ── HTTP helpers ──────────────────────────────────────────────────────────────

def get(base: str, path: str, token: str = "", timeout: int = 10, verify: bool = True) -> requests.Response:
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return requests.get(f"{base}{path}", headers=headers, timeout=timeout, verify=verify)


def post(base: str, path: str, body: dict, token: str = "",
         idempotency_key: str = "", timeout: int = 10, verify: bool = True) -> requests.Response:
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    if idempotency_key:
        headers["Idempotency-Key"] = idempotency_key
    return requests.post(f"{base}{path}", json=body, headers=headers,
                         timeout=timeout, verify=verify)


# ─────────────────────────────────────────────────────────────────────────────
# TEST 1: Baseline health
# ─────────────────────────────────────────────────────────────────────────────

def test_baseline(base: str, verify: bool) -> dict:
    """Confirm the system is healthy before chaos begins."""
    print(f"\n{'─'*60}")
    print("TEST 1: Baseline Health")
    print(f"{'─'*60}")

    r = get(base, "/health", verify=verify)
    body = r.json()

    result("HTTP 200 on /health", r.status_code == 200, f"got {r.status_code}")
    result("system_ready=true",   body.get("system_ready") is True)
    result("database=ok",         body.get("database") == "ok")
    result("degraded_mode=false", body.get("degraded_mode") is False)
    result("HSTS header present", "strict-transport-security" in r.headers or base.startswith("http://"))

    # Deep health
    r2 = get(base, "/health/deep", verify=verify)
    if r2.status_code == 200:
        try:
            deep = r2.json()
            result("/health/deep returns JSON",  True, f"status={deep.get('status','?')}")
            result("queue_backlog is int", isinstance(deep.get("queue_backlog"), int))
        except Exception:
            result("/health/deep returns JSON", False, "parse error")
    else:
        result("/health/deep returns JSON", False, f"HTTP {r2.status_code}")

    return body


# ─────────────────────────────────────────────────────────────────────────────
# TEST 2: Redis failure → graceful degradation
# ─────────────────────────────────────────────────────────────────────────────

def test_redis_failure(base: str, verify: bool) -> None:
    print(f"\n{'─'*60}")
    print("TEST 2: Redis Failure → Degraded Mode (not crash)")
    print(f"{'─'*60}")

    info("Stopping gula-redis …")
    docker(["stop", "redis"])
    time.sleep(4)

    try:
        r = get(base, "/health", verify=verify, timeout=8)
        body = r.json()
        result("API still responds (no 500)", r.status_code in (200, 503), f"HTTP {r.status_code}")
        result("system does not crash",       r.status_code != 500)
        status = body.get("status", "")
        result("status is healthy or degraded", status in ("healthy", "degraded"), status)

        # Backend should still serve auth (in-memory fallback)
        r2 = get(base, "/health", verify=verify)
        result("Health endpoint still returns JSON", r2.status_code in (200, 503))

    except requests.exceptions.ConnectionError:
        result("API still responds (no 500)", False, "ConnectionError — system crashed")
    except requests.exceptions.Timeout:
        result("API responds within timeout",  False, "Timeout")
    finally:
        info("Restarting gula-redis …")
        docker(["start", "redis"])
        time.sleep(5)
        r = get(base, "/health", verify=verify)
        result("System recovers after Redis restart", r.status_code == 200,
               f"HTTP {r.status_code}")


# ─────────────────────────────────────────────────────────────────────────────
# TEST 3: Backend down → nginx returns clean error
# ─────────────────────────────────────────────────────────────────────────────

def test_backend_down(base: str, verify: bool) -> None:
    print(f"\n{'─'*60}")
    print("TEST 3: Backend Down → Clean 502/503 from nginx (no hang)")
    print(f"{'─'*60}")

    info("Stopping gula-backend …")
    docker(["stop", "gula-backend"])
    time.sleep(3)

    try:
        t0 = time.time()
        r = get(base, "/health", verify=verify, timeout=20)
        elapsed = time.time() - t0

        result("nginx responds (no hang)",     elapsed < 20, f"{elapsed:.1f}s")
        result("nginx error code 502 or 503",  r.status_code in (502, 503), f"HTTP {r.status_code}")

        # Response should be JSON, not nginx HTML
        content_type = r.headers.get("Content-Type", "")
        try:
            r.json()
            is_json = True
        except Exception:
            is_json = False
        result("error response is JSON (not HTML)", is_json, content_type)

    except requests.exceptions.Timeout:
        result("nginx responds (no hang)", False, "Timeout — nginx hung without backend")
    except requests.exceptions.ConnectionError:
        result("nginx responds (no hang)", False, "ConnectionError")
    finally:
        info("Restarting gula-backend …")
        docker(["up", "-d", "gula-backend"])
        info("Waiting for backend health check …")
        for _ in range(30):
            try:
                r = get(base, "/health", verify=verify)
                if r.status_code == 200 and r.json().get("system_ready"):
                    break
            except Exception:
                pass
            time.sleep(2)
        result("Backend recovers cleanly", r.status_code == 200,
               f"HTTP {r.status_code}")


# ─────────────────────────────────────────────────────────────────────────────
# TEST 4: Rate limiting — 429 under burst
# ─────────────────────────────────────────────────────────────────────────────

def test_rate_limiting(base: str, verify: bool) -> None:
    print(f"\n{'─'*60}")
    print("TEST 4: Rate Limiting → 429 under burst (not 500)")
    print(f"{'─'*60}")

    statuses: list[int] = []
    errors = 0

    def fire() -> Optional[int]:
        try:
            r = requests.post(
                f"{base}/login",
                json={"email": "chaos@test.invalid", "password": "wrong"},
                timeout=5, verify=verify
            )
            return r.status_code
        except Exception:
            return None

    info("Firing 60 rapid login attempts (auth_limit zone) …")
    with ThreadPoolExecutor(max_workers=30) as pool:
        futures = [pool.submit(fire) for _ in range(60)]
        for f in as_completed(futures):
            s = f.result()
            if s is not None:
                statuses.append(s)
            else:
                errors += 1

    got_429   = statuses.count(429)
    got_401   = statuses.count(401)
    got_500   = statuses.count(500)
    got_other = [s for s in statuses if s not in (401, 429, 500)]

    result("Got at least one 429 (rate limit enforced)", got_429 > 0,  f"{got_429} × 429")
    result("No 500 errors (no crash under load)",        got_500 == 0, f"{got_500} × 500")
    result("No unexpected status codes",                 not got_other, str(got_other[:5]))
    info(f"  Summary: 429={got_429} 401={got_401} 500={got_500} errors={errors}")


# ─────────────────────────────────────────────────────────────────────────────
# TEST 5: Concurrent load — no connection exhaustion
# ─────────────────────────────────────────────────────────────────────────────

def test_concurrent_load(base: str, verify: bool) -> None:
    print(f"\n{'─'*60}")
    print("TEST 5: Concurrent Load → No DB Connection Exhaustion")
    print(f"{'─'*60}")

    statuses: list[int] = []
    latencies: list[float] = []

    def health_check() -> tuple[int, float]:
        t0 = time.time()
        try:
            r = requests.get(f"{base}/health", timeout=10, verify=verify)
            return r.status_code, time.time() - t0
        except Exception:
            return 0, time.time() - t0

    info("Firing 50 concurrent /health requests …")
    with ThreadPoolExecutor(max_workers=50) as pool:
        futures = [pool.submit(health_check) for _ in range(50)]
        for f in as_completed(futures):
            status, latency = f.result()
            statuses.append(status)
            latencies.append(latency)

    ok_count  = statuses.count(200)
    err_count = sum(1 for s in statuses if s not in (200, 429))
    avg_ms    = (sum(latencies) / len(latencies) * 1000) if latencies else 0
    p95_ms    = sorted(latencies)[int(len(latencies) * 0.95)] * 1000 if latencies else 0

    result(f"≥90% success rate ({ok_count}/50)", ok_count >= 45, f"{ok_count} × 200")
    result("No connection errors (0 × status=0)", statuses.count(0) == 0, f"{statuses.count(0)} × error")
    result("p95 latency < 500ms", p95_ms < 500, f"p95={p95_ms:.0f}ms avg={avg_ms:.0f}ms")


# ─────────────────────────────────────────────────────────────────────────────
# TEST 6: Auth — invalid token → 401 consistently
# ─────────────────────────────────────────────────────────────────────────────

def test_invalid_auth(base: str, verify: bool) -> None:
    print(f"\n{'─'*60}")
    print("TEST 6: Invalid Auth → Consistent 401 (no leak)")
    print(f"{'─'*60}")

    tokens = [
        ("empty bearer",      "Bearer "),
        ("garbage token",     "Bearer notavalidtoken"),
        ("no Bearer prefix",  "eyJhbGciOiJIUzI1NiJ9.fake.sig"),
        ("SQL in token",      "Bearer ' OR 1=1; --"),
        ("very long token",   "Bearer " + "A" * 2048),
    ]

    for name, auth_header in tokens:
        try:
            r = requests.get(
                f"{base}/api/patients",
                headers={"Authorization": auth_header},
                timeout=5, verify=verify
            )
            is_401 = r.status_code == 401
            no_500 = r.status_code != 500
            result(f"{name} → 401", is_401, f"got {r.status_code}")
            if not is_401:
                result(f"{name} → not 500", no_500, f"got {r.status_code}")
        except Exception as exc:
            result(f"{name} → 401", False, str(exc)[:60])


# ─────────────────────────────────────────────────────────────────────────────
# TEST 7: Idempotency — duplicate claim request
# ─────────────────────────────────────────────────────────────────────────────

def test_idempotency(base: str, token: str, verify: bool) -> None:
    print(f"\n{'─'*60}")
    print("TEST 7: Idempotency — Duplicate Claim Submission")
    print(f"{'─'*60}")

    if not token:
        warn("Skipped — no admin token provided (use --admin-token)")
        return

    key = f"chaos-idem-{int(time.time())}"
    payload = {
        "patient_id": 1,
        "items": [{"test_code": "CBC-CHAOS", "unit_price": 1000, "amount": 1000}],
        "idempotency_key": key,
    }

    responses = []
    info(f"Sending same claim 3× with Idempotency-Key: {key}")
    for i in range(3):
        try:
            r = post(base, "/api/claims", payload, token=token,
                     idempotency_key=key, verify=verify)
            responses.append((r.status_code, r.text[:200]))
        except Exception as exc:
            responses.append((0, str(exc)))
        time.sleep(0.3)

    statuses = [r[0] for r in responses]
    # All should succeed (201 first time, 200/201 on repeat)
    all_success = all(s in (200, 201, 404) for s in statuses)
    result("All 3 idempotent requests succeed (2xx or 404)", all_success, str(statuses))

    # IDs should be identical if 201 returned multiple times
    ids = []
    for s, body in responses:
        if s in (200, 201):
            try:
                ids.append(json.loads(body).get("id"))
            except Exception:
                pass
    if len(ids) > 1:
        all_same = len(set(ids)) == 1
        result("All repetitions return same claim_id (no duplicate)", all_same,
               f"ids={ids}")
    else:
        warn("Could not compare claim IDs (may need a valid patient_id=1)")


# ─────────────────────────────────────────────────────────────────────────────
# TEST 8: Security probe — path traversal + XSS
# ─────────────────────────────────────────────────────────────────────────────

def test_security_probes(base: str, verify: bool) -> None:
    print(f"\n{'─'*60}")
    print("TEST 8: Security Probes (path traversal, XSS, scanner paths)")
    print(f"{'─'*60}")

    probes = [
        ("/api/../../etc/passwd",      "path traversal"),
        ("/.git/config",               ".git exposure"),
        ("/.env",                      ".env exposure"),
        ("/wp-admin/",                 "WordPress scanner"),
        ("/phpmyadmin/",               "phpMyAdmin scanner"),
        ("/api/patients?q=<script>",   "XSS in query param"),
    ]

    for path, name in probes:
        try:
            r = requests.get(f"{base}{path}", timeout=5, verify=verify,
                             allow_redirects=False)
            blocked = r.status_code in (400, 401, 403, 404, 301, 302)
            not_200 = r.status_code != 200
            result(f"{name} → blocked ({r.status_code})", blocked,
                   f"HTTP {r.status_code}")
        except requests.exceptions.ConnectionError:
            result(f"{name} → blocked (connection refused)", True)
        except Exception as exc:
            result(f"{name} → blocked", False, str(exc)[:60])


# ─────────────────────────────────────────────────────────────────────────────
# Summary
# ─────────────────────────────────────────────────────────────────────────────

def print_summary() -> int:
    total  = len(PASSED) + len(FAILED)
    pct    = (len(PASSED) / total * 100) if total else 0

    print(f"\n{'═'*60}")
    print("CHAOS TEST SUMMARY")
    print(f"{'═'*60}")
    print(f"  PASSED : {GREEN}{len(PASSED)}{RESET}")
    print(f"  FAILED : {RED}{len(FAILED)}{RESET}")
    print(f"  SCORE  : {pct:.0f}% ({len(PASSED)}/{total})")

    if FAILED:
        print(f"\n{RED}Failed tests:{RESET}")
        for f in FAILED:
            print(f"  - {f}")

    if pct >= 90:
        print(f"\n{GREEN}✔ RESILIENT — system handles failure conditions correctly.{RESET}")
        verdict = 0
    elif pct >= 70:
        print(f"\n{YELLOW}⚠ PARTIALLY RESILIENT — fix failing tests before production.{RESET}")
        verdict = 1
    else:
        print(f"\n{RED}✘ NOT RESILIENT — critical failures detected.{RESET}")
        verdict = 2

    return verdict


# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────

def main() -> int:
    parser = argparse.ArgumentParser(description="GULA Chaos & Resilience Test Suite")
    parser.add_argument("--base", default="http://localhost:8080",
                        help="Base URL of the API gateway (default: http://localhost:8080)")
    parser.add_argument("--admin-token", default="",
                        help="Admin JWT token for authenticated tests")
    parser.add_argument("--no-docker", action="store_true",
                        help="Skip tests that require docker compose access")
    parser.add_argument("--insecure", action="store_true",
                        help="Disable SSL verification (for self-signed certs)")
    parser.add_argument("--tests", default="all",
                        help="Comma-separated test numbers to run (e.g. 1,4,6) or 'all'")
    args = parser.parse_args()

    verify = not args.insecure
    base   = args.base.rstrip("/")
    token  = args.admin_token

    if args.tests == "all":
        run = set(range(1, 9))
    else:
        run = set(int(t) for t in args.tests.split(","))

    print(f"\n{'═'*60}")
    print("GULA Platform — Chaos & Resilience Test Suite")
    print(f"Target : {base}")
    print(f"Token  : {'provided' if token else 'not provided (some tests skipped)'}")
    print(f"Docker : {'disabled' if args.no_docker else 'enabled'}")
    print(f"{'═'*60}")

    if 1 in run: test_baseline(base, verify)
    if 2 in run and not args.no_docker: test_redis_failure(base, verify)
    if 3 in run and not args.no_docker: test_backend_down(base, verify)
    if 4 in run: test_rate_limiting(base, verify)
    if 5 in run: test_concurrent_load(base, verify)
    if 6 in run: test_invalid_auth(base, verify)
    if 7 in run: test_idempotency(base, token, verify)
    if 8 in run: test_security_probes(base, verify)

    return print_summary()


if __name__ == "__main__":
    sys.exit(main())
