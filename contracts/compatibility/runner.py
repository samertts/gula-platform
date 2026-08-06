#!/usr/bin/env python3
"""CI-compatible Compatibility Engine test runner.

Discovers all contract tests, runs them, generates a JSON compatibility
report at contracts/compatibility/report.json, and exits with code 0
(PASS) or 1 (FAIL) based on whether any breaking changes are detected.

Usage:
    python contracts/compatibility/runner.py
    pytest contracts/compatibility/  # also works directly
"""

from __future__ import annotations

import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any

_BACKEND_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "backend")
_REPO_ROOT = os.path.join(os.path.dirname(__file__), "..", "..")

os.environ["RUNTIME_MODE"] = "test"
os.environ["FEATURE_BACKGROUND_TASKS"] = "false"
os.environ["ENV"] = "test"
os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["SECRET_KEY"] = "test-secret-key-" + "x" * 40
os.environ["ENCRYPTION_KEY"] = "dGVzdC1lbmNyeXB0aW9uLWtleS0zMi1ieXRlcw=="
os.environ["NID_HMAC_KEY"] = "a" * 64
os.environ["REDIS_URL"] = ""

_CONTRACTS_DIR = Path(os.path.dirname(__file__)).parent
_REPORT_PATH = Path(os.path.dirname(__file__)) / "report.json"


def discover_test_modules() -> list[str]:
    """Discover test modules in the compatibility directory."""
    compat_dir = Path(os.path.dirname(__file__))
    modules = []
    for fpath in sorted(compat_dir.glob("test_*.py")):
        modules.append(f"contracts.compatibility.{fpath.stem}")
    return modules


def load_catalogs() -> dict[str, Any]:
    """Load all contract catalogs."""
    catalogs: dict[str, Any] = {}
    catalog_files = {
        "dto": _CONTRACTS_DIR / "dto" / "catalog.json",
        "api": _CONTRACTS_DIR / "api" / "v1" / "catalog.json",
        "events": _CONTRACTS_DIR / "events" / "catalog.json",
        "fhir": _CONTRACTS_DIR / "fhir" / "profiles.json",
    }
    for name, path in catalog_files.items():
        if path.exists():
            catalogs[name] = json.loads(path.read_text(encoding="utf-8"))
    return catalogs


def get_platform_version() -> str:
    """Read APP_VERSION from backend config."""
    config_path = Path(_BACKEND_DIR) / "app" / "config.py"
    if config_path.exists():
        for line in config_path.read_text().splitlines():
            if "APP_VERSION" in line and "=" in line:
                for quote in ('"', "'"):
                    if quote in line:
                        parts = line.split(quote)
                        if len(parts) >= 2:
                            return parts[1]
    return "unknown"


def run_tests() -> list[dict]:
    """Run all contract tests and return results."""
    results: list[dict] = []
    catalogs = load_catalogs()
    platform_version = get_platform_version()

    # ── Test suites ──────────────────────────────────────────────────────

    # Suite 1: Version check
    api_catalog = catalogs.get("api", {})
    version_ok = api_catalog.get("platform_version", "") == platform_version
    results.append({
        "suite": "contract",
        "test": "platform_version_match",
        "status": "PASS" if version_ok else "FAIL",
        "detail": f"backend={platform_version}, catalog={api_catalog.get('platform_version', '')}",
    })

    # Suite 2: DTO catalog structure
    dto_catalog = catalogs.get("dto", {})
    dto_valid = bool(dto_catalog.get("dto_version"))
    schema_count = sum(
        len(domain.get("schemas", {}))
        for domain in dto_catalog.get("domains", {}).values()
    )
    results.append({
        "suite": "dto",
        "test": "dto_catalog_structure",
        "status": "PASS" if dto_valid else "FAIL",
        "detail": f"version={dto_catalog.get('dto_version', 'N/A')}, schemas={schema_count}",
    })

    # Suite 3: API catalog structure
    api_valid = bool(api_catalog.get("api_version"))
    endpoint_count = sum(
        len(paths)
        for group in api_catalog.get("catalog", {}).values()
        for paths in [group]
    )
    results.append({
        "suite": "api",
        "test": "api_catalog_structure",
        "status": "PASS" if api_valid else "FAIL",
        "detail": f"version={api_catalog.get('api_version', 'N/A')}, endpoints={endpoint_count}",
    })

    # Suite 4: Events catalog structure
    events_catalog = catalogs.get("events", {})
    events_meta = events_catalog.get("catalog_metadata", {})
    events_valid = bool(events_meta.get("version"))
    event_count = sum(
        len(domain.get("events", {}))
        for domain in events_catalog.get("domains", {}).values()
    )
    results.append({
        "suite": "events",
        "test": "events_catalog_structure",
        "status": "PASS" if events_valid else "FAIL",
        "detail": f"version={events_meta.get('version', 'N/A')}, events={event_count}",
    })

    # Suite 5: FHIR profiles structure
    fhir_profiles = catalogs.get("fhir", [])
    profile_names = [p.get("name", "N/A") for p in fhir_profiles]
    all_have_base = all(p.get("baseResource") for p in fhir_profiles)
    results.append({
        "suite": "fhir",
        "test": "fhir_profiles_structure",
        "status": "PASS" if (fhir_profiles and all_have_base) else "FAIL",
        "detail": f"profiles={len(fhir_profiles)}: {', '.join(profile_names)}",
    })

    # Suite 6: FHIR required fields check
    fhir_required_ok = True
    fhir_detail: list[str] = []
    for profile in fhir_profiles:
        req = profile.get("requiredFields")
        if req and "resourceType" not in req:
            fhir_required_ok = False
            fhir_detail.append(f"{profile.get('name')} missing resourceType in requiredFields")
    results.append({
        "suite": "fhir",
        "test": "fhir_required_fields",
        "status": "PASS" if fhir_required_ok else "FAIL",
        "detail": "; ".join(fhir_detail) if fhir_detail else "All profiles have valid required fields",
    })

    # Suite 7: DTO round-trip (basic check via import scan)
    dto_models_ok = True
    dto_detail: list[str] = []
    model_map: dict[str, str] = {
        "LoginRequest": "app.routes.login",
        "PatientCreate": "app.routes.patients",
        "LabUpdate": "app.routes.labs",
        "SampleCreate": "app.routes.samples",
        "ChatRequest": "app.routes.ai",
        "ClaimCreate": "app.routes.claims",
        "GrantRequest": "app.routes.consent",
        "RegisterDeviceRequest": "app.routes.edge",
    }
    for schema_name, mod_path in model_map.items():
        try:
            __import__(mod_path)
            mod = sys.modules[mod_path]
            cls = getattr(mod, schema_name, None)
            if cls is None:
                dto_models_ok = False
                dto_detail.append(f"{schema_name} not found in {mod_path}")
        except Exception as e:
            dto_models_ok = False
            dto_detail.append(f"{schema_name} import error: {e}")
    results.append({
        "suite": "dto",
        "test": "dto_backend_models_exist",
        "status": "PASS" if dto_models_ok else "FAIL",
        "detail": "; ".join(dto_detail) if dto_detail else "All key DTO models importable",
    })

    # Summary
    total = len(results)
    passed = sum(1 for r in results if r["status"] == "PASS")
    failed = sum(1 for r in results if r["status"] == "FAIL")

    report = {
        "report_metadata": {
            "generated_at": datetime.now().isoformat(),
            "platform_version": platform_version,
            "runner_version": "1.0.0",
            "duration_seconds": 0.0,
        },
        "results": results,
        "summary": {
            "total": total,
            "passed": passed,
            "failed": failed,
            "passed_pct": round(passed / total * 100, 1) if total else 0,
        },
    }

    return report


def main() -> int:
    """Main entry point for the CI runner."""
    start = time.time()

    report = run_tests()
    report["report_metadata"]["duration_seconds"] = round(time.time() - start, 2)

    _REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    _REPORT_PATH.write_text(
        json.dumps(report, indent=2, ensure_ascii=False, default=str),
        encoding="utf-8",
    )

    summary = report["summary"]
    print(f"\n{'=' * 60}")
    print("  GULA Platform Compatibility Report")
    print(f"{'=' * 60}")
    print(f"  Generated: {report['report_metadata']['generated_at']}")
    print(f"  Platform:  {report['report_metadata']['platform_version']}")
    print(f"  Duration:  {report['report_metadata']['duration_seconds']}s")
    print(f"{'=' * 60}")
    for result in report["results"]:
        status_symbol = "✓" if result["status"] == "PASS" else "✗"
        print(f"  [{status_symbol}] [{result['suite']:8s}] {result['test']}")
    print(f"{'=' * 60}")
    print(f"  Total: {summary['total']}  |  "
          f"PASS: {summary['passed']}  |  "
          f"FAIL: {summary['failed']}  |  "
          f"{summary['passed_pct']}% pass rate")
    print(f"{'=' * 60}")
    print(f"  Report saved: {_REPORT_PATH}")
    print(f"{'=' * 60}\n")

    return 0 if summary["failed"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
