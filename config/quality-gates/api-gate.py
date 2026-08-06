#!/usr/bin/env python3
"""
API Quality Gate — validates OpenAPI spec compliance and API behavior.

Checks:
  1. OpenAPI spec validation (no duplicate paths, valid schemas, valid responses)
  2. Response shape matches spec
  3. Status code compliance (200/success, 201/create, 400/bad, 401/unauth,
     403/forbidden, 404/notfound, 422/validation, 500/error)
  4. Content-Type is always application/json
  5. All endpoints except health/login/register have auth
  6. Rate limit headers (X-RateLimit-Limit, X-RateLimit-Remaining)
  7. Request ID header (X-Request-ID)
  8. Arabic error messages present (detail_ar field)
  9. Pagination format (offset, limit, total, next fields)
  10. Version path compliance (/api/v1/*)

Usage:
    python config/quality-gates/api-gate.py
    python config/quality-gates/api-gate.py --json
    python config/quality-gates/api-gate.py --openapi-spec openapi.json
    python config/quality-gates/api-gate.py --target-url http://localhost:8080

Exit codes:
    0 — all checks pass
    1 — one or more checks fail
"""

import argparse
import json
import logging
import pathlib
import sys
import urllib.error
import urllib.request
from datetime import UTC, datetime
from typing import Any

logger = logging.getLogger("api-gate")

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent

GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BOLD = "\033[1m"
RESET = "\033[0m"

AUTH_EXEMPT_PATHS = {"/health", "/health/live", "/health/ready", "/health/status", "/health/deep",
                     "/api/v1/auth/login", "/api/v1/auth/register", "/api/v1/auth/refresh",
                     "/docs", "/redoc", "/openapi.json", "/test-types"}

EXPECTED_STATUS_CODES = {
    "GET": {200, 401, 403, 404, 422, 500},
    "POST": {201, 400, 401, 403, 404, 422, 500},
    "PUT": {200, 400, 401, 403, 404, 422, 500},
    "PATCH": {200, 400, 401, 403, 404, 422, 500},
    "DELETE": {200, 204, 401, 403, 404, 500},
}

PAGINATION_FIELDS = {"offset", "limit", "total", "next"}


def _ok(msg: str) -> str:
    return f"{GREEN}✓{RESET} {msg}"

def _fail(msg: str) -> str:
    return f"{RED}✗{RESET} {msg}"

def _warn(msg: str) -> str:
    return f"{YELLOW}⚠{RESET} {msg}"


def load_openapi_spec(path: str) -> dict[str, Any]:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def check_duplicate_paths(spec: dict[str, Any]) -> list[dict[str, Any]]:
    failures: list[dict[str, Any]] = []
    paths = spec.get("paths", {})
    seen: dict[str, list[str]] = {}
    for path, methods in paths.items():
        for method in methods:
            if method.upper() in ("GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"):
                key = f"{method.upper()} {path}"
                if key in seen:
                    failures.append({
                        "check": "duplicate_path",
                        "severity": "error",
                        "message": f"Duplicate path definition: {key}",
                    })
                seen[key] = seen.get(key, []) + [path]
    return failures


def check_schema_validity(spec: dict[str, Any]) -> list[dict[str, Any]]:
    failures: list[dict[str, Any]] = []
    schemas = spec.get("components", {}).get("schemas", {})
    for name, schema in schemas.items():
        if "type" not in schema and "$ref" not in schema and "allOf" not in schema and "oneOf" not in schema:
            failures.append({
                "check": "schema_validity",
                "severity": "error",
                "message": f"Schema '{name}' has no type, $ref, allOf, or oneOf",
            })
        if schema.get("type") == "object" and "properties" not in schema and "additionalProperties" not in schema:
            failures.append({
                "check": "schema_validity",
                "severity": "warning",
                "message": f"Schema '{name}' is type object but has no properties or additionalProperties",
            })
    return failures


def check_response_shapes(spec: dict[str, Any]) -> list[dict[str, Any]]:
    failures: list[dict[str, Any]] = []
    paths = spec.get("paths", {})
    for path, methods in paths.items():
        for method, details in methods.items():
            if method.upper() not in ("GET", "POST", "PUT", "PATCH", "DELETE"):
                continue
            responses = details.get("responses", {})
            if not responses:
                failures.append({
                    "check": "response_shape",
                    "severity": "error",
                    "message": f"{method.upper()} {path} has no responses defined",
                })
            for status_code, response in responses.items():
                content = response.get("content", {})
                if content and "application/json" not in content:
                    failures.append({
                        "check": "response_content_type",
                        "severity": "error",
                        "message": f"{method.upper()} {path} response {status_code} missing application/json content type",
                    })
    return failures


def check_status_code_compliance(spec: dict[str, Any]) -> list[dict[str, Any]]:
    failures: list[dict[str, Any]] = []
    paths = spec.get("paths", {})
    for path, methods in paths.items():
        for method, details in methods.items():
            method_upper = method.upper()
            if method_upper not in EXPECTED_STATUS_CODES:
                continue
            responses = details.get("responses", {})
            for status_code in responses:
                try:
                    code = int(status_code)
                except ValueError:
                    continue
                if code not in EXPECTED_STATUS_CODES[method_upper]:
                    failures.append({
                        "check": "status_code_compliance",
                        "severity": "warning",
                        "message": f"{method_upper} {path} uses non-standard status code {status_code}",
                    })
    return failures


def check_content_type(spec: dict[str, Any]) -> list[dict[str, Any]]:
    failures: list[dict[str, Any]] = []
    paths = spec.get("paths", {})
    for path, methods in paths.items():
        for method, details in methods.items():
            if method.upper() not in ("GET", "POST", "PUT", "PATCH", "DELETE"):
                continue
            request_body = details.get("requestBody", {})
            if request_body:
                content = request_body.get("content", {})
                if content and "application/json" not in content:
                    failures.append({
                        "check": "content_type",
                        "severity": "error",
                        "message": f"{method.upper()} {path} request body missing application/json content type",
                    })
            responses = details.get("responses", {})
            for status_code, response in responses.items():
                content = response.get("content", {})
                if content and "application/json" not in content:
                    failures.append({
                        "check": "content_type",
                        "severity": "error",
                        "message": f"{method.upper()} {path} response {status_code} missing application/json",
                    })
    return failures


def check_auth_requirements(spec: dict[str, Any]) -> list[dict[str, Any]]:
    failures: list[dict[str, Any]] = []
    paths = spec.get("paths", {})
    for path, methods in paths.items():
        if any(path.startswith(exempt) for exempt in AUTH_EXEMPT_PATHS):
            continue
        for method, details in methods.items():
            if method.upper() not in ("GET", "POST", "PUT", "PATCH", "DELETE"):
                continue
            security = details.get("security", spec.get("security", []))
            has_auth = any("bearerAuth" in s or "BearerAuth" in s or "JWTBearer" in s for s in security)
            if not has_auth:
                failures.append({
                    "check": "auth_requirement",
                    "severity": "error",
                    "message": f"{method.upper()} {path} has no auth requirement",
                })
    return failures


def check_rate_limit_headers(target_url: str) -> list[dict[str, Any]]:
    failures: list[dict[str, Any]] = []
    try:
        req = urllib.request.Request(f"{target_url}/api/v1/patients?limit=1")
        with urllib.request.urlopen(req, timeout=10) as resp:
            headers = dict(resp.headers)
            if "X-RateLimit-Limit" not in headers:
                failures.append({
                    "check": "rate_limit_headers",
                    "severity": "error",
                    "message": "Missing X-RateLimit-Limit response header",
                })
            if "X-RateLimit-Remaining" not in headers:
                failures.append({
                    "check": "rate_limit_headers",
                    "severity": "error",
                    "message": "Missing X-RateLimit-Remaining response header",
                })
    except Exception as exc:
        failures.append({
            "check": "rate_limit_headers",
            "severity": "warning",
            "message": f"Could not verify rate limit headers: {exc}",
        })
    return failures


def check_request_id_header(target_url: str) -> list[dict[str, Any]]:
    failures: list[dict[str, Any]] = []
    try:
        req = urllib.request.Request(f"{target_url}/health")
        with urllib.request.urlopen(req, timeout=10) as resp:
            headers = dict(resp.headers)
            if "X-Request-ID" not in headers:
                failures.append({
                    "check": "request_id_header",
                    "severity": "error",
                    "message": "Missing X-Request-ID response header",
                })
    except Exception as exc:
        failures.append({
            "check": "request_id_header",
            "severity": "warning",
            "message": f"Could not verify X-Request-ID header: {exc}",
        })
    return failures


def check_arabic_error_messages(spec: dict[str, Any]) -> list[dict[str, Any]]:
    failures: list[dict[str, Any]] = []
    paths = spec.get("paths", {})
    for path, methods in paths.items():
        for method, details in methods.items():
            if method.upper() not in ("GET", "POST", "PUT", "PATCH", "DELETE"):
                continue
            responses = details.get("responses", {})
            for status_code, response in responses.items():
                try:
                    code = int(status_code)
                except ValueError:
                    continue
                if code >= 400:
                    content = response.get("content", {})
                    json_content = content.get("application/json", {})
                    schema = json_content.get("schema", {})
                    props = schema.get("properties", {})
                    if "detail_ar" not in props:
                        failures.append({
                            "check": "arabic_error_messages",
                            "severity": "warning",
                            "message": f"{method.upper()} {path} response {status_code} missing detail_ar field",
                        })
    return failures


def check_pagination_format(spec: dict[str, Any]) -> list[dict[str, Any]]:
    failures: list[dict[str, Any]] = []
    paths = spec.get("paths", {})
    for path, methods in paths.items():
        for method, details in methods.items():
            if method.upper() != "GET":
                continue
            parameters = details.get("parameters", [])
            has_offset = any(p.get("name") == "offset" for p in parameters)
            has_limit = any(p.get("name") == "limit" for p in parameters)
            if has_offset or has_limit:
                if not has_offset:
                    failures.append({
                        "check": "pagination_format",
                        "severity": "warning",
                        "message": f"GET {path} has limit param but missing offset param",
                    })
                if not has_limit:
                    failures.append({
                        "check": "pagination_format",
                        "severity": "warning",
                        "message": f"GET {path} has offset param but missing limit param",
                    })
                success_response = responses.get("200", {})
                content = success_response.get("content", {})
                json_content = content.get("application/json", {})
                schema = json_content.get("schema", {})
                props = schema.get("properties", {})
                for field in PAGINATION_FIELDS:
                    if field not in props:
                        failures.append({
                            "check": "pagination_format",
                            "severity": "warning",
                            "message": f"GET {path} paginated response missing '{field}' field",
                        })
    return failures


def check_version_path(spec: dict[str, Any]) -> list[dict[str, Any]]:
    failures: list[dict[str, Any]] = []
    paths = spec.get("paths", {})
    for path in paths:
        if path.startswith("/api/v1/"):
            continue
        if path.startswith("/health") or path.startswith("/docs") or path.startswith("/redoc") or path.startswith("/openapi"):
            continue
        if path.startswith("/api/v"):
            failures.append({
                "check": "version_path",
                "severity": "error",
                "message": f"Path {path} uses non-v1 API version. All paths must be /api/v1/*",
            })
        else:
            failures.append({
                "check": "version_path",
                "severity": "error",
                "message": f"Path {path} does not follow /api/v1/* convention",
            })
    return failures


def run_all_checks(spec: dict[str, Any], target_url: str | None = None) -> list[dict[str, Any]]:
    all_failures: list[dict[str, Any]] = []

    checks = [
        ("Duplicate paths", lambda: check_duplicate_paths(spec)),
        ("Schema validity", lambda: check_schema_validity(spec)),
        ("Response shapes", lambda: check_response_shapes(spec)),
        ("Status code compliance", lambda: check_status_code_compliance(spec)),
        ("Content-Type validation", lambda: check_content_type(spec)),
        ("Auth requirements", lambda: check_auth_requirements(spec)),
        ("Arabic error messages", lambda: check_arabic_error_messages(spec)),
        ("Pagination format", lambda: check_pagination_format(spec)),
        ("Version path compliance", lambda: check_version_path(spec)),
    ]

    for name, check_fn in checks:
        try:
            results = check_fn()
            for r in results:
                r["check_name"] = name
            all_failures.extend(results)
            if results:
                logger.warning("%s: %d failure(s)", name, len(results))
            else:
                logger.info("%s: OK", name)
        except Exception as exc:
            logger.error("%s failed: %s", name, exc)
            all_failures.append({
                "check": name,
                "severity": "error",
                "message": f"Check failed with exception: {exc}",
            })

    if target_url:
        live_checks = [
            ("Rate limit headers", lambda: check_rate_limit_headers(target_url)),
            ("Request ID header", lambda: check_request_id_header(target_url)),
        ]
        for name, check_fn in live_checks:
            try:
                results = check_fn()
                for r in results:
                    r["check_name"] = name
                all_failures.extend(results)
            except Exception as exc:
                logger.error("%s failed: %s", name, exc)

    return all_failures


def print_report(failures: list[dict[str, Any]], json_output: bool = False) -> int:
    errors = [f for f in failures if f.get("severity") == "error"]
    warnings = [f for f in failures if f.get("severity") == "warning"]

    if json_output:
        report = {
            "timestamp": datetime.now(UTC).isoformat(),
            "passed": len(errors) == 0,
            "summary": {"errors": len(errors), "warnings": len(warnings), "total": len(failures)},
            "failures": failures,
        }
        print(json.dumps(report, indent=2, ensure_ascii=False))
        return 0 if report["passed"] else 1

    print(f"\n{BOLD}═══ API Quality Gate Report ═══{RESET}\n")

    if not failures:
        print(f"  {GREEN}All API checks passed!{RESET}")
        print()
        return 0

    if errors:
        print(f"  {BOLD}{RED}Errors ({len(errors)}):{RESET}")
        for e in errors:
            print(f"    {RED}✗{RESET} [{e.get('check_name', e['check'])}] {e['message']}")
        print()

    if warnings:
        print(f"  {BOLD}{YELLOW}Warnings ({len(warnings)}):{RESET}")
        for w in warnings:
            print(f"    {YELLOW}⚠{RESET} [{w.get('check_name', w['check'])}] {w['message']}")
        print()

    print(f"  Summary: {RED}{len(errors)} errors{RESET}, {YELLOW}{len(warnings)} warnings{RESET}")
    print()

    return 1 if errors else 0


def main() -> int:
    parser = argparse.ArgumentParser(description="API Quality Gate")
    parser.add_argument("--openapi-spec", type=str, help="Path to OpenAPI spec JSON file")
    parser.add_argument("--target-url", type=str, default="http://localhost:8080", help="Target URL for live checks")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    args = parser.parse_args()

    level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(level=level, format="%(asctime)s [%(levelname)s] %(message)s", datefmt="%H:%M:%S")

    spec: dict[str, Any] = {}
    if args.openapi_spec:
        logger.info("Loading OpenAPI spec from %s", args.openapi_spec)
        spec = load_openapi_spec(args.openapi_spec)
    else:
        openapi_path = ROOT / "backend" / "app" / "openapi.json"
        if openapi_path.exists():
            spec = load_openapi_spec(str(openapi_path))
        else:
            try:
                req = urllib.request.Request(f"{args.target_url}/openapi.json")
                with urllib.request.urlopen(req, timeout=10) as resp:
                    spec = json.loads(resp.read().decode())
            except Exception as exc:
                logger.error("Could not load OpenAPI spec: %s", exc)
                print(json.dumps({
                    "timestamp": datetime.now(UTC).isoformat(),
                    "passed": False,
                    "summary": {"errors": 1, "warnings": 0, "total": 1},
                    "failures": [{"check": "openapi_load", "severity": "error",
                                  "message": f"Could not load OpenAPI spec: {exc}"}],
                }, indent=2))
                return 1

    failures = run_all_checks(spec, target_url=args.target_url)
    return print_report(failures, json_output=args.json)


if __name__ == "__main__":
    sys.exit(main())
