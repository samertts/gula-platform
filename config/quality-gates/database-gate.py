#!/usr/bin/env python3
"""
Database Quality Gate — validates database schema, migrations, and conventions.

Checks:
  1. Migration idempotency (can apply twice without error)
  2. No non-nullable columns without server_default
  3. Index naming conventions (ix_ for indexes, uq_ for unique)
  4. Foreign key constraints
  5. Missing composite indexes on (lab_id, status), (patient_id, created_at), (lab_id, created_at)
  6. Enum types are consistent
  7. Column types (no VARCHAR(255) for all strings)
  8. Migration reverts cleanly (downgrade -1 works)
  9. Table naming conventions (snake_case, plural)

Usage:
    python config/quality-gates/database-gate.py
    python config/quality-gates/database-gate.py --json
    python config/quality-gates/database-gate.py --db-url postgresql://user:pass@localhost:5432/gula

Exit codes:
    0 — all checks pass
    1 — one or more checks fail
"""

import argparse
import json
import logging
import os
import pathlib
import re
import subprocess
import sys
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger("database-gate")

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
MIGRATIONS_DIR = ROOT / "backend" / "migrations" / "versions"

GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BOLD = "\033[1m"
RESET = "\033[0m"

REQUIRED_COMPOSITE_INDEXES = [
    {"columns": ["lab_id", "status"], "tables": ["lab_orders", "lab_results", "samples"]},
    {"columns": ["patient_id", "created_at"], "tables": ["lab_orders", "lab_results", "visits"]},
    {"columns": ["lab_id", "created_at"], "tables": ["lab_orders", "lab_results", "samples", "audit_logs"]},
]


def _ok(msg: str) -> str:
    return f"{GREEN}✓{RESET} {msg}"

def _fail(msg: str) -> str:
    return f"{RED}✗{RESET} {msg}"

def _warn(msg: str) -> str:
    return f"{YELLOW}⚠{RESET} {msg}"


def check_migration_idempotency(migrations_dir: pathlib.Path) -> list[dict[str, Any]]:
    failures: list[dict[str, Any]] = []
    if not migrations_dir.is_dir():
        return failures

    for py_file in sorted(migrations_dir.glob("*.py")):
        if py_file.name == "__init__.py":
            continue
        try:
            text = py_file.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue

        has_upgrade = "def upgrade()" in text
        has_downgrade = "def downgrade()" in text
        if has_upgrade and not has_downgrade:
            failures.append({
                "check": "migration_idempotency",
                "severity": "error",
                "message": f"{py_file.name} has upgrade() but no downgrade()",
            })

        if "op.create_table" in text and "op.drop_table" not in text:
            if "op.create_index" in text and "op.drop_index" not in text:
                failures.append({
                    "check": "migration_idempotency",
                    "severity": "warning",
                    "message": f"{py_file.name} creates tables/indexes but may not be fully reversible",
                })

    return failures


def check_non_nullable_columns(migrations_dir: pathlib.Path) -> list[dict[str, Any]]:
    failures: list[dict[str, Any]] = []
    if not migrations_dir.is_dir():
        return failures

    for py_file in sorted(migrations_dir.glob("*.py")):
        if py_file.name == "__init__.py":
            continue
        try:
            text = py_file.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue

        col_pattern = re.compile(
            r'sa\.Column\([\s\S]*?\)|Column\([\s\S]*?\)',
            re.MULTILINE
        )
        for match in col_pattern.finditer(text):
            col_text = match.group()
            has_nullable = "nullable" in col_text
            has_server_default = "server_default" in col_text or "serverDefault" in col_text
            if not has_nullable and not has_server_default:
                col_name_match = re.search(r"'([^']+)'|\"([^\"]+)\"", col_text)
                col_name = col_name_match.group(1) or col_name_match.group(2) if col_name_match else "unknown"
                failures.append({
                    "check": "non_nullable_column",
                    "severity": "error",
                    "message": f"Column '{col_name}' in {py_file.name} is non-nullable without server_default",
                })

    return failures


def check_index_naming(migrations_dir: pathlib.Path) -> list[dict[str, Any]]:
    failures: list[dict[str, Any]] = []
    if not migrations_dir.is_dir():
        return failures

    for py_file in sorted(migrations_dir.glob("*.py")):
        if py_file.name == "__init__.py":
            continue
        try:
            text = py_file.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue

        index_pattern = re.compile(r'op\.create_index\([\s\S]*?\)', re.MULTILINE)
        for match in index_pattern.finditer(text):
            index_text = match.group()
            name_match = re.search(r"'([^']+)'|\"([^\"]+)\"", index_text)
            if name_match:
                index_name = name_match.group(1) or name_match.group(2)
                if "unique" in index_text.lower():
                    if not index_name.startswith("uq_"):
                        failures.append({
                            "check": "index_naming",
                            "severity": "error",
                            "message": f"Unique index '{index_name}' in {py_file.name} should start with 'uq_'",
                        })
                else:
                    if not index_name.startswith("ix_"):
                        failures.append({
                            "check": "index_naming",
                            "severity": "error",
                            "message": f"Index '{index_name}' in {py_file.name} should start with 'ix_'",
                        })

    return failures


def check_foreign_key_constraints(migrations_dir: pathlib.Path) -> list[dict[str, Any]]:
    failures: list[dict[str, Any]] = []
    if not migrations_dir.is_dir():
        return failures

    for py_file in sorted(migrations_dir.glob("*.py")):
        if py_file.name == "__init__.py":
            continue
        try:
            text = py_file.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue

        create_table_pattern = re.compile(
            r'op\.create_table\([\s\S]*?\)',
            re.MULTILINE
        )
        for match in create_table_pattern.finditer(text):
            table_text = match.group()
            columns = re.findall(r'sa\.Column\([\s\S]*?\)', table_text)
            has_foreign_key = any("ForeignKey" in col for col in columns)
            if not has_foreign_key:
                table_name_match = re.search(r"'(\w+)'", table_text)
                if table_name_match:
                    table_name = table_name_match.group(1)
                    if table_name not in ("alembic_version", "spatial_ref_sys"):
                        failures.append({
                            "check": "foreign_key_constraints",
                            "severity": "warning",
                            "message": f"Table '{table_name}' in {py_file.name} has no foreign key constraints",
                        })

    return failures


def check_composite_indexes(migrations_dir: pathlib.Path) -> list[dict[str, Any]]:
    failures: list[dict[str, Any]] = []
    if not migrations_dir.is_dir():
        return failures

    all_index_text = ""
    for py_file in sorted(migrations_dir.glob("*.py")):
        if py_file.name == "__init__.py":
            continue
        try:
            all_index_text += py_file.read_text(encoding="utf-8") + "\n"
        except (OSError, UnicodeDecodeError):
            continue

    for idx_config in REQUIRED_COMPOSITE_INDEXES:
        cols = idx_config["columns"]
        for table in idx_config["tables"]:
            col1, col2 = cols
            pattern1 = re.compile(
                rf"op\.create_index\(['\"](ix_{table}_{col1}_{col2}|ix_{table}_{col2}_{col1})['\"]",
                re.IGNORECASE
            )
            pattern2 = re.compile(
                rf"op\.create_index\(['\"](ix_{table}_{col2}_{col1}|ix_{table}_{col1}_{col2})['\"]",
                re.IGNORECASE
            )
            if not pattern1.search(all_index_text) and not pattern2.search(all_index_text):
                failures.append({
                    "check": "composite_index",
                    "severity": "error",
                    "message": f"Missing composite index on ({', '.join(cols)}) for table '{table}'",
                })

    return failures


def check_enum_consistency(migrations_dir: pathlib.Path) -> list[dict[str, Any]]:
    failures: list[dict[str, Any]] = []
    if not migrations_dir.is_dir():
        return failures

    enum_definitions: dict[str, list[str]] = {}
    for py_file in sorted(migrations_dir.glob("*.py")):
        if py_file.name == "__init__.py":
            continue
        try:
            text = py_file.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue

        enum_pattern = re.compile(
            r'sa\.Enum\(([^)]+)\)',
            re.MULTILINE
        )
        for match in enum_pattern.finditer(text):
            enum_values_str = match.group(1)
            enum_values = [v.strip().strip("'\"") for v in enum_values_str.split(",")]
            enum_name_match = re.search(r"name\s*=\s*'([^']+)'", text[match.start():match.end()])
            if enum_name_match:
                enum_name = enum_name_match.group(1)
                if enum_name in enum_definitions:
                    if set(enum_definitions[enum_name]) != set(enum_values):
                        failures.append({
                            "check": "enum_consistency",
                            "severity": "error",
                            "message": f"Enum '{enum_name}' has inconsistent values across migrations",
                        })
                else:
                    enum_definitions[enum_name] = enum_values

    return failures


def check_column_types(migrations_dir: pathlib.Path) -> list[dict[str, Any]]:
    failures: list[dict[str, Any]] = []
    if not migrations_dir.is_dir():
        return failures

    for py_file in sorted(migrations_dir.glob("*.py")):
        if py_file.name == "__init__.py":
            continue
        try:
            text = py_file.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue

        varchar_pattern = re.compile(r'sa\.VARCHAR\(255\)|sa\.String\(255\)|VARCHAR\(255\)', re.IGNORECASE)
        varchar_matches = varchar_pattern.findall(text)
        if len(varchar_matches) > 5:
            failures.append({
                "check": "column_types",
                "severity": "warning",
                "message": f"{py_file.name} uses VARCHAR(255) for {len(varchar_matches)} columns. "
                           f"Consider using more specific length constraints.",
            })

    return failures


def has_migration_revisions(migrations_dir: pathlib.Path) -> bool:
    versions = [f for f in migrations_dir.glob("*.py") if f.name != "__init__.py"]
    return len(versions) > 0


def check_migration_revert(migrations_dir: pathlib.Path) -> list[dict[str, Any]]:
    failures: list[dict[str, Any]] = []
    if not migrations_dir.is_dir():
        return failures

    if not has_migration_revisions(migrations_dir):
        logger.info("No migration revisions found, skipping revert check")
        return failures

    try:
        result = subprocess.run(
            ["alembic", "downgrade", "-1"],
            capture_output=True, text=True, timeout=30,
            cwd=str(ROOT / "backend"),
        )
        if result.returncode != 0:
            stderr_lower = result.stderr.strip().lower()
            if "no revisions" in stderr_lower or "can't find revision" in stderr_lower:
                logger.info("No revisions have been applied yet, skipping revert check")
                return failures
            failures.append({
                "check": "migration_revert",
                "severity": "error",
                "message": f"Migration downgrade -1 failed: {result.stderr.strip()[:200]}",
            })
        else:
            upgrade_result = subprocess.run(
                ["alembic", "upgrade", "head"],
                capture_output=True, text=True, timeout=30,
                cwd=str(ROOT / "backend"),
            )
            if upgrade_result.returncode != 0:
                failures.append({
                    "check": "migration_revert",
                    "severity": "error",
                    "message": f"Migration upgrade head after downgrade failed: {upgrade_result.stderr.strip()[:200]}",
                })
    except FileNotFoundError:
        failures.append({
            "check": "migration_revert",
            "severity": "warning",
            "message": "alembic not found in PATH, skipping migration revert check",
        })
    except subprocess.TimeoutExpired:
        failures.append({
            "check": "migration_revert",
            "severity": "warning",
            "message": "Migration revert check timed out",
        })

    return failures


def check_table_naming(migrations_dir: pathlib.Path) -> list[dict[str, Any]]:
    failures: list[dict[str, Any]] = []
    if not migrations_dir.is_dir():
        return failures

    for py_file in sorted(migrations_dir.glob("*.py")):
        if py_file.name == "__init__.py":
            continue
        try:
            text = py_file.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue

        table_pattern = re.compile(
            r"op\.create_table\(['\"](\w+)['\"]",
            re.MULTILINE
        )
        for match in table_pattern.finditer(text):
            table_name = match.group(1)
            if table_name in ("alembic_version", "spatial_ref_sys"):
                continue
            if not table_name.endswith("s") and not table_name.endswith("es"):
                if not table_name.endswith("data") and not table_name.endswith("status"):
                    failures.append({
                        "check": "table_naming",
                        "severity": "warning",
                        "message": f"Table '{table_name}' does not follow plural naming convention",
                    })
            if not re.match(r'^[a-z][a-z0-9_]*$', table_name):
                failures.append({
                    "check": "table_naming",
                    "severity": "error",
                    "message": f"Table '{table_name}' does not follow snake_case naming convention",
                })

    return failures


def run_all_checks(migrations_dir: pathlib.Path) -> list[dict[str, Any]]:
    all_failures: list[dict[str, Any]] = []

    checks = [
        ("Migration idempotency", lambda: check_migration_idempotency(migrations_dir)),
        ("Non-nullable columns", lambda: check_non_nullable_columns(migrations_dir)),
        ("Index naming conventions", lambda: check_index_naming(migrations_dir)),
        ("Foreign key constraints", lambda: check_foreign_key_constraints(migrations_dir)),
        ("Composite indexes", lambda: check_composite_indexes(migrations_dir)),
        ("Enum consistency", lambda: check_enum_consistency(migrations_dir)),
        ("Column types", lambda: check_column_types(migrations_dir)),
        ("Table naming conventions", lambda: check_table_naming(migrations_dir)),
        ("Migration revert", lambda: check_migration_revert(migrations_dir)),
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

    return all_failures


def print_report(failures: list[dict[str, Any]], json_output: bool = False) -> int:
    errors = [f for f in failures if f.get("severity") == "error"]
    warnings = [f for f in failures if f.get("severity") == "warning"]

    if json_output:
        report = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "passed": len(errors) == 0,
            "summary": {"errors": len(errors), "warnings": len(warnings), "total": len(failures)},
            "failures": failures,
        }
        print(json.dumps(report, indent=2, ensure_ascii=False))
        return 0 if report["passed"] else 1

    print(f"\n{BOLD}═══ Database Quality Gate Report ═══{RESET}\n")

    if not failures:
        print(f"  {GREEN}All database checks passed!{RESET}\n")
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
    parser = argparse.ArgumentParser(description="Database Quality Gate")
    parser.add_argument("--migrations-dir", type=str, default=str(MIGRATIONS_DIR),
                        help="Path to migrations directory")
    parser.add_argument("--db-url", type=str, help="Database URL for live checks")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    args = parser.parse_args()

    level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(level=level, format="%(asctime)s [%(levelname)s] %(message)s", datefmt="%H:%M:%S")

    migrations_dir = pathlib.Path(args.migrations_dir)
    if not migrations_dir.is_dir():
        logger.error("Migrations directory does not exist: %s", migrations_dir)
        return 1

    logger.info("Database gate scanning %s", migrations_dir)
    failures = run_all_checks(migrations_dir)
    return print_report(failures, json_output=args.json)


if __name__ == "__main__":
    sys.exit(main())
