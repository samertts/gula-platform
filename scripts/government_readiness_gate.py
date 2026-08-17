#!/usr/bin/env python3
"""Fail-closed preflight gate for GULA government patient-flow rollout.

This gate is intentionally conservative. A green result means only that the
repository and supplied environment passed automated preflight checks; it does
not replace clinical, security, change-control, or disaster-recovery approval.
"""

from __future__ import annotations

import argparse
import json
import os
import pathlib
import subprocess
import sys
from dataclasses import asdict, dataclass
from typing import Any


@dataclass
class Finding:
    check: str
    status: str
    severity: str
    message: str


REQUIRED_FILES = (
    "backend/migrations/versions/20260817_0025_sync_conflict_lock_notifications.py",
    "backend/app/national/api/routes/sync.py",
    "backend/app/services/sync_conflict_service.py",
    "backend/app/tasks/sync_outbox.py",
    "frontend-v3/src/services/offlineQueue.ts",
    "k6/patient_flow_sync_load.js",
    "docs/GULA_OFFLINE_SYNC_IMPLEMENTATION_AR.md",
)


def run(command: list[str], root: pathlib.Path) -> tuple[int, str, str]:
    result = subprocess.run(command, cwd=root, text=True, capture_output=True, check=False)
    return result.returncode, result.stdout.strip(), result.stderr.strip()


def check_required_files(root: pathlib.Path) -> list[Finding]:
    missing = [path for path in REQUIRED_FILES if not (root / path).is_file()]
    if missing:
        return [Finding("required_artifacts", "fail", "P0", f"Missing required artifacts: {', '.join(missing)}")]
    return [Finding("required_artifacts", "pass", "", "All government patient-flow artifacts are present")]


def check_branch(root: pathlib.Path) -> list[Finding]:
    code, branch, error = run(["git", "branch", "--show-current"], root)
    if code != 0:
        return [Finding("branch_guard", "fail", "P0", error or "Cannot determine git branch")]
    if not branch:
        branch = os.getenv("GITHUB_HEAD_REF") or os.getenv("GITHUB_REF_NAME") or "detached"
    if branch in {"main", "master", "production"}:
        return [Finding("branch_guard", "fail", "P0", f"Refusing government gate on protected branch: {branch}")]
    return [Finding("branch_guard", "pass", "", f"Protected branches are not targeted; current branch is {branch}")]


def check_worktree(root: pathlib.Path, allow_dirty: bool) -> list[Finding]:
    code, output, error = run(["git", "status", "--porcelain"], root)
    if code != 0:
        return [Finding("worktree", "fail", "P0", error or "Cannot inspect worktree")]
    if output and not allow_dirty:
        return [Finding("worktree", "fail", "P1", "Working tree is dirty; gate requires a reviewed commit")]
    if output:
        return [Finding("worktree", "warn", "P1", "Working tree is dirty because --allow-dirty was supplied")]
    return [Finding("worktree", "pass", "", "Working tree is clean")]


def check_alembic_heads(root: pathlib.Path) -> list[Finding]:
    code, output, error = run([sys.executable, "-m", "alembic", "-c", "alembic.ini", "heads"], root / "backend")
    if code != 0:
        return [Finding("alembic_single_head", "fail", "P0", error or output or "Alembic heads failed")]
    heads = [line for line in output.splitlines() if line.strip() and "(head)" in line]
    if len(heads) != 1:
        return [Finding("alembic_single_head", "fail", "P0", f"Expected exactly one Alembic head, found {len(heads)}: {heads}")]
    if "20260817_0025" not in heads[0]:
        return [Finding("alembic_single_head", "fail", "P0", f"Sync migration is not the current head: {heads[0]}")]
    return [Finding("alembic_single_head", "pass", "", heads[0])]


def check_sync_contracts(root: pathlib.Path) -> list[Finding]:
    route = (root / "backend/app/national/api/routes/sync.py").read_text(encoding="utf-8")
    service = (root / "backend/app/services/sync_conflict_service.py").read_text(encoding="utf-8")
    queue = (root / "frontend-v3/src/services/offlineQueue.ts").read_text(encoding="utf-8")
    outbox = (root / "backend/app/tasks/sync_outbox.py").read_text(encoding="utf-8")
    offline_service = (root / "backend/app/services/offline_sync_service.py").read_text(encoding="utf-8")
    checks: list[tuple[str, str, str]] = [
        ("device_session_header", "X-Device-Session", "Device session header is enforced by the sync API"),
        ("device_token_hash", "session_hash", "Device session scope is hash-backed"),
        ("offline_aes_gcm", "AES-GCM", "Offline queue uses AES-GCM"),
        ("offline_capacity_guard", "MAX_QUEUE_SIZE", "Offline queue capacity is bounded"),
        ("outbox_backoff", "MAX_BACKOFF_SECONDS", "Outbox retry backoff is bounded"),
        ("manual_conflict_only", "Automatic conflict resolution is disabled", "Automatic clinical conflict resolution remains disabled"),
    ]
    findings = []
    for name, marker, message in checks:
        haystack = route + service + queue + outbox + offline_service
        if marker not in haystack:
            findings.append(Finding(name, "fail", "P0", f"Required contract marker missing: {marker}"))
        else:
            findings.append(Finding(name, "pass", "", message))
    return findings


def check_production_environment(production: bool) -> list[Finding]:
    if not production:
        return [Finding("production_environment", "warn", "P1", "Production environment checks were not requested; use --production for fail-closed env validation")]
    findings: list[Finding] = []
    if os.getenv("IS_PRODUCTION", "").lower() != "true":
        findings.append(Finding("is_production", "fail", "P0", "IS_PRODUCTION=true is required"))
    if os.getenv("RUNTIME_MODE") not in {"api", "worker"}:
        findings.append(Finding("runtime_mode", "fail", "P0", "RUNTIME_MODE must be api or worker"))
    if os.getenv("DATABASE_URL", "").startswith("sqlite"):
        findings.append(Finding("database_engine", "fail", "P0", "SQLite is not an approved government production database"))
    required = ("SECRET_KEY", "ENCRYPTION_KEY", "NID_HMAC_KEY", "REFRESH_TOKEN_SECRET", "DEVICE_HMAC_KEY")
    missing = [key for key in required if not os.getenv(key)]
    if missing:
        findings.append(Finding("production_secrets", "fail", "P0", f"Missing required production secrets: {', '.join(missing)}"))
    delivery_backend = os.getenv("GULA_SYNC_OUTBOX_DELIVERY", "").strip().lower()
    if delivery_backend not in {"redis", "broker", "push"}:
        findings.append(Finding("outbox_delivery_backend", "fail", "P0", "GULA_SYNC_OUTBOX_DELIVERY must be redis, broker, or push in production"))
    if not findings:
        findings.append(Finding("production_environment", "pass", "", "Production environment invariants passed"))
    return findings


def run_optional_tests(root: pathlib.Path) -> list[Finding]:
    commands = [
        [sys.executable, "-m", "pytest", "-q", "backend/tests/test_sync_security_and_outbox.py", "backend/tests/test_stress.py"],
    ]
    findings: list[Finding] = []
    for command in commands:
        code, output, error = run(command, root)
        if code != 0:
            findings.append(Finding("automated_tests", "fail", "P0", error[-2000:] or output[-2000:] or "Automated test command failed"))
        else:
            findings.append(Finding("automated_tests", "pass", "", output.splitlines()[-1] if output else "Automated tests passed"))
    return findings


def build_report(root: pathlib.Path, *, allow_dirty: bool, production: bool, run_tests: bool) -> dict[str, Any]:
    findings: list[Finding] = []
    findings.extend(check_required_files(root))
    findings.extend(check_branch(root))
    findings.extend(check_worktree(root, allow_dirty))
    findings.extend(check_alembic_heads(root))
    findings.extend(check_sync_contracts(root))
    findings.extend(check_production_environment(production))
    if run_tests:
        findings.extend(run_optional_tests(root))
    errors = [item for item in findings if item.status == "fail"]
    warnings = [item for item in findings if item.status == "warn"]
    return {
        "passed": not errors,
        "government_production_approval": False,
        "summary": {"pass": len(findings) - len(errors) - len(warnings), "warnings": len(warnings), "failures": len(errors)},
        "findings": [asdict(item) for item in findings],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=pathlib.Path, default=pathlib.Path(__file__).resolve().parents[1])
    parser.add_argument("--allow-dirty", action="store_true")
    parser.add_argument("--production", action="store_true")
    parser.add_argument("--run-tests", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    report = build_report(args.root.resolve(), allow_dirty=args.allow_dirty, production=args.production, run_tests=args.run_tests)
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print("GULA government readiness preflight")
        for item in report["findings"]:
            print(f"[{item['status'].upper():4}] {item['check']}: {item['message']}")
        print(f"Summary: {report['summary']}")
        print("Government production approval: manual change-control, clinical, security and DR approval still required")
    return 1 if report["summary"]["failures"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
