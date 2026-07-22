#!/usr/bin/env python3
"""
GULA Data Preservation Quality Gate
=====================================
Enforces the Data Preservation Constitution (17 rules).

Exit codes:
  0 — PASS (all checks pass)
  1 — WARNING (some checks need attention)
  2 — FAIL (one or more rules violated — blocks merge)

Usage:
  python scripts/data_preservation_gate.py              # full scan
  python scripts/data_preservation_gate.py --ci         # CI-friendly JSON
  python scripts/data_preservation_gate.py --pre-commit # staged files only
  python scripts/data_preservation_gate.py --verbose    # detailed output
"""

from __future__ import annotations

import argparse
import json
import pathlib
import re
import subprocess
import sys
from datetime import datetime, timezone
from typing import Any

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
MIGRATIONS_DIR = REPO_ROOT / "backend" / "migrations" / "versions"
MODELS_DIR = REPO_ROOT / "backend" / "app" / "models"
CONSTITUTION_DIR = REPO_ROOT / "docs" / "constitution" / "data_preservation"

_RESET = "\033[0m"
_RED = "\033[91m"
_GREEN = "\033[92m"
_YELLOW = "\033[93m"
_CYAN = "\033[96m"
_BOLD = "\033[1m"

_USE_COLOR = sys.stdout.isatty()


def _c(code: str, text: str) -> str:
    if not _USE_COLOR:
        return text
    palette = {
        "red": _RED, "green": _GREEN, "yellow": _YELLOW,
        "cyan": _CYAN, "bold": _BOLD, "reset": _RESET,
    }
    return f"{palette.get(code, _RESET)}{text}{_RESET}"


PASS = "PASS"
WARNING = "WARNING"
FAIL = "FAIL"

PROHIBITED_PATTERNS: list[tuple[str, str, str]] = [
    (r"\bDROP\s+TABLE\b(?!\s*IF\s+EXISTS)", "DROP TABLE", "Rule 4 — prohibited operation"),
    (r"\bDROP\s+COLUMN\b", "DROP COLUMN", "Rule 4 — prohibited operation"),
    (r"\bDROP\s+(?:TABLE|COLUMN)\s+.*\bCASCADE\b", "DROP ... CASCADE", "Rule 1 — cascade drop causes data loss"),
    (r"\bTRUNCATE\b", "TRUNCATE", "Rule 4 — prohibited operation"),
    (r"\bDELETE\s+FROM\b", "DELETE FROM", "Rule 4 — prohibited operation (use soft delete)"),
    (r"\bALTER\s+COLUMN\s+\w+\s+TYPE\b", "ALTER COLUMN TYPE", "Rule 2 — destructive type change"),
    (r"\bRENAME\s+COLUMN\b", "RENAME COLUMN", "Rule 2 — breaks backward compatibility"),
    (r"\bRENAME\s+TABLE\b", "RENAME TABLE", "Rule 2 — breaks backward compatibility"),
]

SAFE_PATTERNS: list[tuple[str, str]] = [
    (r"op\.add_column\(", "ADD COLUMN"),
    (r"op\.create_table\(", "CREATE TABLE"),
    (r"op\.create_index\(", "CREATE INDEX"),
    (r"op\.create_unique_constraint\(", "CREATE UNIQUE CONSTRAINT"),
    (r"op\.create_foreign_key\(", "CREATE FOREIGN KEY"),
    (r"op\.alter_column\(", "ALTER COLUMN (review required)"),
]

PROTECTED_TABLES = [
    "patients", "canonical_patients", "patient_links", "citizen_links",
    "lab_orders", "lab_results", "samples", "test_results",
    "audit_logs", "outbox_events",
    "labs", "organizations", "facilities", "lab_users",
    "users", "roles", "permissions", "role_permissions", "role_assignments",
    "tenants", "subscriptions", "feature_flags",
    "test_types", "quality_control", "consents", "claims", "claim_items",
    "ai_embeddings", "ai_conversations", "ai_conversation_messages",
    "ai_agent_executions", "ai_knowledge_nodes",
    "ai_interactions", "ai_retrieval_refs", "ai_feedback",
    "ai_unresolved_questions", "medical_terminology_normalized",
    "edge_devices", "edge_tasks", "edge_telemetry", "edge_models",
    "edge_model_assignments",
    "mfa_devices", "mfa_sessions",
    "oauth2_clients", "oauth2_tokens",
    "service_accounts",
    "upgrade_requests", "upgrade_demand_scores",
    "notifications", "appointments",
]


def get_changed_migration_files(staged_only: bool = False) -> list[pathlib.Path]:
    if staged_only:
        result = subprocess.run(
            ["git", "diff", "--cached", "--name-only", "--diff-filter=ACMR"],
            capture_output=True, text=True, timeout=15, cwd=REPO_ROOT,
        )
    else:
        result = subprocess.run(
            ["git", "diff", "--name-only", "--diff-filter=ACMR"],
            capture_output=True, text=True, timeout=15, cwd=REPO_ROOT,
        )
    if result.returncode != 0:
        return []

    files: list[pathlib.Path] = []
    for line in result.stdout.splitlines():
        f = line.strip()
        if f.startswith("backend/migrations/versions/") and f.endswith(".py"):
            full_path = REPO_ROOT / f
            if full_path.exists():
                files.append(full_path)
    return files


def scan_migration_content(migration_file: pathlib.Path) -> dict[str, Any]:
    content = migration_file.read_text(encoding="utf-8", errors="replace")
    violations: list[str] = []
    warnings_list: list[str] = []
    has_downgrade = bool(re.search(r"def downgrade\s*\(", content))

    for lineno, line in enumerate(content.splitlines(), 1):
        stripped = line.strip()
        if stripped.startswith("#") or stripped.startswith('"""'):
            continue
        for pattern, label, rule in PROHIBITED_PATTERNS:
            if re.search(pattern, stripped, re.IGNORECASE):
                violations.append(f"  Line {lineno}: {label} — {rule}")
                break

    for pattern, label in SAFE_PATTERNS:
        if re.search(pattern, content):
            warnings_list.append(f"  Found: {label}")

    return {
        "file": str(migration_file.relative_to(REPO_ROOT)),
        "has_downgrade": has_downgrade,
        "violations": violations,
        "warnings": warnings_list,
        "safe_operations": warnings_list,
    }


def check_migration_safety(
    staged_only: bool = False,
    verbose: bool = False,
) -> dict[str, Any]:
    files = get_changed_migration_files(staged_only=staged_only)
    if not files:
        return {
            "status": PASS,
            "details": ["No migration files changed — check skipped"],
            "files_checked": 0,
        }

    all_violations: list[str] = []
    all_warnings: list[str] = []
    missing_downgrade: list[str] = []

    for mf in files:
        result = scan_migration_content(mf)
        if result["violations"]:
            all_violations.append(f"Violations in {result['file']}:")
            all_violations.extend(result["violations"])
        if not result["has_downgrade"]:
            missing_downgrade.append(result["file"])
        if verbose and result["safe_operations"]:
            all_warnings.extend(result["safe_operations"])

    details: list[str] = []
    if all_violations:
        details.append(f"{len(all_violations)} migration safety violation(s):")
        details.extend(all_violations)
    if missing_downgrade:
        details.append(f"Missing downgrade() in {len(missing_downgrade)} migration(s):")
        for f in missing_downgrade:
            details.append(f"  - {f}")
    if not all_violations and not missing_downgrade:
        details.append(f"Scanned {len(files)} migration file(s)")
        details.append("No prohibited operations detected")
        details.append("All migrations include downgrade()")

    status = PASS
    if all_violations:
        status = FAIL
    elif missing_downgrade:
        status = WARNING

    return {
        "status": status,
        "details": details,
        "files_checked": len(files),
        "violations_found": len(all_violations),
        "missing_downgrade": len(missing_downgrade),
    }


def check_protected_tables(
    verbose: bool = False,
) -> dict[str, Any]:
    details: list[str] = []
    status = PASS

    changed_migration_files = get_changed_migration_files()
    referenced_tables: set[str] = set()

    for mf in changed_migration_files:
        content = mf.read_text(encoding="utf-8", errors="replace")
        for table in PROTECTED_TABLES:
            if re.search(rf"\b{table}\b", content, re.IGNORECASE):
                referenced_tables.add(table)

    altered_protected: list[str] = []
    for mf in changed_migration_files:
        content = mf.read_text(encoding="utf-8", errors="replace")
        for table in PROTECTED_TABLES:
            if re.search(
                rf"\b({table})\b.*(?:drop|alter|rename|modify|change)",
                content,
                re.IGNORECASE,
            ):
                altered_protected.append(table)

    if altered_protected:
        details.append(
            f"WARNING: {len(altered_protected)} protected table(s) referenced "
            f"with DDL operations: {', '.join(sorted(set(altered_protected)))}"
        )
        details.append("  Protected tables require Architecture Board approval")
        status = WARNING

    details.append(f"{len(PROTECTED_TABLES)} protected tables registered")

    model_files = list(MODELS_DIR.rglob("*.py")) if MODELS_DIR.exists() else []
    model_tables = 0
    for mf in model_files:
        if mf.name == "__init__.py" or mf.name == "base.py":
            continue
        content = mf.read_text(encoding="utf-8", errors="replace")
        if re.search(r"class\s+\w+\(Base\)", content):
            model_tables += 1
    details.append(f"{model_tables} model classes found in backend/app/models/")

    return {"status": status, "details": details}


def check_soft_delete_models(verbose: bool = False) -> dict[str, Any]:
    details: list[str] = []
    status = PASS

    if not MODELS_DIR.exists():
        details.append("Models directory not found")
        return {"status": WARNING, "details": details}

    business_models: list[str] = []
    missing_soft_delete: list[str] = []

    skip_files = {"__init__.py", "base.py"}
    for mf in sorted(MODELS_DIR.rglob("*.py")):
        if mf.name in skip_files:
            continue
        content = mf.read_text(encoding="utf-8", errors="replace")
        if not re.search(r"class\s+\w+\(Base\)", content):
            continue

        is_business_model = True
        transient_keywords = ["session", "token", "cache", "temp"]
        if any(kw in mf.stem.lower() for kw in transient_keywords):
            is_business_model = False

        if is_business_model:
            business_models.append(mf.stem)
            has_soft_delete = (
                "deleted_at" in content
                or "is_deleted" in content
                or "deleted_by" in content
            )
            if not has_soft_delete:
                missing_soft_delete.append(mf.stem)

    details.append(f"{len(business_models)} business model(s) checked")
    if missing_soft_delete:
        details.append(
            f"Model(s) without soft delete: {', '.join(missing_soft_delete)}"
        )
        status = WARNING
    else:
        details.append("All business models implement soft delete")

    return {"status": status, "details": details}


def check_constitution_documents(verbose: bool = False) -> dict[str, Any]:
    details: list[str] = []
    status = PASS

    required_docs = [
        ("Constitution Document", CONSTITUTION_DIR.parent / "31_DATA_PRESERVATION_CONSTITUTION.md"),
        ("Migration Safety Policy", CONSTITUTION_DIR / "migration_safety_policy.md"),
        ("Protected Tables Registry", CONSTITUTION_DIR / "protected_tables_registry.md"),
        ("Backup Strategy", CONSTITUTION_DIR / "backup_strategy.md"),
        ("Restore Strategy", CONSTITUTION_DIR / "restore_strategy.md"),
        ("Disaster Recovery Guide", CONSTITUTION_DIR / "disaster_recovery_guide.md"),
        ("Architecture Decision Record", REPO_ROOT / "docs/adr/ADR-025-data-preservation-constitution.md"),
        ("Quality Gate Script", REPO_ROOT / "scripts/data_preservation_gate.py"),
    ]

    missing = []
    for name, path in required_docs:
        if path.exists():
            details.append(f"  {name}: {path.relative_to(REPO_ROOT)}")
        else:
            missing.append(name)
            details.append(f"  {name}: MISSING")

    if missing:
        status = FAIL
        details.insert(0, f"Missing {len(missing)} required document(s): {', '.join(missing)}")
    else:
        details.insert(0, "All 8 required constitution documents present")

    return {"status": status, "details": details}


def check_migration_safety_policy_compliance(
    staged_only: bool = False,
    verbose: bool = False,
) -> dict[str, Any]:
    details: list[str] = []
    status = PASS

    files = get_changed_migration_files(staged_only=staged_only)
    if not files:
        details.append("No migration files to check")
        return {"status": PASS, "details": details}

    for mf in files:
        content = mf.read_text(encoding="utf-8", errors="replace")
        has_docstring = bool(re.search(r'""".*?"""', content, re.DOTALL))
        has_idempotency = (
            "_has_column" in content
            or "_table_exists" in content
            or "_index_exists" in content
        )
        has_upgrade = bool(re.search(r"def upgrade\s*\(", content))
        has_downgrade = bool(re.search(r"def downgrade\s*\(", content))

        if not has_docstring:
            details.append(f"{mf.name}: missing docstring")
            status = WARNING
        if not has_idempotency:
            details.append(f"{mf.name}: missing idempotency guards (_has_column, etc.)")
            status = WARNING
        if not has_upgrade:
            details.append(f"{mf.name}: missing upgrade() function")
            status = FAIL
        if not has_downgrade:
            details.append(f"{mf.name}: missing downgrade() function")
            status = FAIL

    if not details:
        details.append("All migration files comply with Migration Safety Policy")

    return {"status": status, "details": details}


def run_all_checks(
    staged_only: bool = False,
    verbose: bool = False,
) -> list[dict[str, Any]]:
    return [
        {
            "name": "Migration Safety (Rules 1, 2, 4)",
            **check_migration_safety(staged_only=staged_only, verbose=verbose),
        },
        {
            "name": "Migration Policy Compliance (Rules 5, 8)",
            **check_migration_safety_policy_compliance(
                staged_only=staged_only, verbose=verbose
            ),
        },
        {
            "name": "Protected Tables (Rule 15)",
            **check_protected_tables(verbose=verbose),
        },
        {
            "name": "Soft Delete Check (Rule 10)",
            **check_soft_delete_models(verbose=verbose),
        },
        {
            "name": "Constitution Documents (Rule 16)",
            **check_constitution_documents(verbose=verbose),
        },
    ]


def format_results(
    results: list[dict[str, Any]],
    ci: bool = False,
) -> str:
    if ci:
        overall = PASS
        for r in results:
            if r["status"] == FAIL:
                overall = FAIL
                break
            if r["status"] == WARNING:
                overall = WARNING

        return json.dumps({
            "gate": "DATA_PRESERVATION_GATE",
            "overall": overall,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "checks": results,
        }, indent=2)

    lines: list[str] = []
    lines.append("")
    lines.append(
        f"  {_c('bold', '╔════════════════════════════════════════════════════╗')}"
    )
    lines.append(
        f"  {_c('bold', '║    GULA Data Preservation Quality Gate            ║')}"
    )
    lines.append(
        f"  {_c('bold', '╚════════════════════════════════════════════════════╝')}"
    )
    lines.append("")

    for r in results:
        if r["status"] == PASS:
            badge = _c("green", "  PASS  ")
        elif r["status"] == WARNING:
            badge = _c("yellow", " WARNING ")
        else:
            badge = _c("red", "  FAIL  ")
        lines.append(f"  {badge}  {r['name']}")
        for d in r["details"]:
            lines.append(f"         {d}")
        lines.append("")

    lines.append(f"  {_c('bold', '─' * 56)}")

    overall = PASS
    for r in results:
        if r["status"] == FAIL:
            overall = FAIL
            break
        if r["status"] == WARNING:
            overall = WARNING

    if overall == PASS:
        lines.append(
            f"  {_c('green', '✔ DATA_PRESERVATION_GATE: PASS')} "
            f"— all data preservation rules satisfied"
        )
    elif overall == WARNING:
        lines.append(
            f"  {_c('yellow', '⚠ DATA_PRESERVATION_GATE: WARNING')} "
            f"— review warnings before merging"
        )
    else:
        lines.append(
            f"  {_c('red', '✖ DATA_PRESERVATION_GATE: FAIL')} "
            f"— data preservation rules violated — merge blocked"
        )
    lines.append("")

    return "\n".join(lines)


def determine_exit_code(results: list[dict[str, Any]]) -> int:
    for r in results:
        if r["status"] == FAIL:
            return 2
    for r in results:
        if r["status"] == WARNING:
            return 1
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="GULA Data Preservation Quality Gate",
    )
    parser.add_argument(
        "--ci", action="store_true",
        help="CI-friendly JSON output",
    )
    parser.add_argument(
        "--pre-commit", action="store_true",
        help="Pre-commit hook mode (staged files only)",
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true",
        help="Verbose output",
    )
    args = parser.parse_args(argv)

    if args.ci:
        global _USE_COLOR
        _USE_COLOR = False

    results = run_all_checks(
        staged_only=args.pre_commit,
        verbose=args.verbose,
    )

    output = format_results(results, ci=args.ci)
    print(output)

    return determine_exit_code(results)


if __name__ == "__main__":
    sys.exit(main())
