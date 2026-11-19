#!/usr/bin/env python3
"""
GULA Data Preservation Quality Gate
=====================================
Enforces the Data Preservation Constitution (17 rules).

Exit codes:
  0 — PASS (all checks pass)
  1 — WARNING (some checks need attention)
  2 — FAIL (one or more rules violated — blocks merge)

The default scan remains advisory for legacy rollout work (exit 1). Use
--strict for release readiness; real business-model gaps are then blocking.

Usage:
  python scripts/data_preservation_gate.py              # full scan
  python scripts/data_preservation_gate.py --ci         # CI-friendly JSON
  python scripts/data_preservation_gate.py --pre-commit # staged files only
  python scripts/data_preservation_gate.py --verbose    # detailed output
  python scripts/data_preservation_gate.py --ci --strict # release-blocking Rule 10 scan
"""

from __future__ import annotations

import argparse
import ast
import json
import pathlib
import re
import subprocess
import sys
from dataclasses import dataclass
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
    "audit_logs", "outbox_events", "authorization_audit",
    "clinical_command_receipts", "edge_events", "integration_inbox_events",
    "labs", "organizations", "facilities", "lab_users",
    "accessibility_profiles", "health_preferences",
    "users", "roles", "permissions", "role_permissions", "role_assignments",
    "tenants", "lab_subscriptions", "feature_flags",
    "test_types", "quality_controls", "consents", "claims", "claim_items",
    "clinical_lab_facility_bindings", "national_facilities", "clinical_ehr_facility_bindings",
    "ai_embeddings", "ai_conversations", "ai_conversation_messages",
    "ai_agent_executions", "ai_knowledge_nodes", "ai_knowledge_edges",
    "ai_model_registry", "ai_evaluations",
    "ai_interactions", "ai_retrieval_refs", "ai_feedback",
    "ai_unresolved_questions", "medical_terminology_normalized",
    "edge_devices", "edge_tasks", "edge_telemetry", "edge_models",
    "edge_model_assignments", "edge_policies",
    "mfa_devices", "mfa_sessions", "break_glass_sessions",
    "oauth2_clients", "oauth2_tokens",
    "service_accounts", "delegations", "role_groups", "role_group_members",
    "abac_policies", "field_security",
    "upgrade_requests", "upgrade_demand_scores",
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

    model_tables = len(_model_inventory())
    details.append(f"{model_tables} model classes found in backend/app/models/")

    return {"status": status, "details": details}


# These tables are intentionally not soft-deleted.  They are append-only or
# short-lived operational records and have a different lifecycle policy.  Keeping
# the policy explicit prevents a filename heuristic from silently exempting a
# real business entity.
IMMUTABLE_APPEND_ONLY_TABLES: dict[str, str] = {
    "audit_logs": "append-only tamper-evident audit trail; deletion is prohibited",
    "outbox_events": "delivery outbox; lifecycle is replay/retention, not soft delete",
    "authorization_audit": "append-only authorization decision history",
    "clinical_command_receipts": "append-only idempotency claims for clinical commands",
    "edge_events": "append-only edge lifecycle and security event history",
}

TRANSIENT_OPERATIONAL_TABLES: dict[str, str] = {
    "mfa_sessions": "short-lived authentication session with expiry",
    "oauth2_tokens": "revocable/expiring token store",
}


@dataclass(frozen=True)
class ModelInventoryEntry:
    file: str
    model: str
    table: str
    category: str
    fields: tuple[str, ...]
    inherited_soft_delete: bool
    default_filter_verified: bool = False


def _ast_name(node: ast.AST) -> str:
    """Return a stable dotted name for an AST expression."""
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        parent = _ast_name(node.value)
        return f"{parent}.{node.attr}" if parent else node.attr
    return ""


def _ast_string(node: ast.AST | None) -> str | None:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    return None


def _class_assignments(node: ast.ClassDef) -> dict[str, ast.AST]:
    assignments: dict[str, ast.AST] = {}
    for statement in node.body:
        if isinstance(statement, (ast.Assign, ast.AnnAssign)):
            targets: list[ast.AST] = []
            if isinstance(statement, ast.Assign):
                targets = list(statement.targets)
                value = statement.value
            else:
                targets = [statement.target]
                value = statement.value
            for target in targets:
                if isinstance(target, ast.Name):
                    assignments[target.id] = value
    return assignments


def _model_inventory() -> list[ModelInventoryEntry]:
    """Build a class/table inventory without importing application code.

    The gate must remain safe to run with a broken or unavailable database, so
    this deliberately uses AST inspection rather than SQLAlchemy imports.
    """
    entries: list[ModelInventoryEntry] = []
    if not MODELS_DIR.exists():
        return entries

    for mf in sorted(MODELS_DIR.rglob("*.py")):
        if mf.name in {"__init__.py", "base.py"}:
            continue
        try:
            tree = ast.parse(mf.read_text(encoding="utf-8", errors="replace"), str(mf))
        except SyntaxError:
            # A syntax error is handled by the normal quality gates; do not
            # manufacture a false soft-delete result here.
            continue

        local_classes = {node.name: node for node in tree.body if isinstance(node, ast.ClassDef)}
        soft_aliases = {"SoftDeleteMixin"}
        for node in tree.body:
            if isinstance(node, ast.ImportFrom):
                for alias in node.names:
                    if alias.name == "SoftDeleteMixin":
                        soft_aliases.add(alias.asname or alias.name)

        def inherits_soft(node: ast.ClassDef, seen: set[str] | None = None) -> bool:
            seen = seen or set()
            if node.name in seen:
                return False
            seen.add(node.name)
            for base in node.bases:
                base_name = _ast_name(base).split(".")[-1]
                if base_name in soft_aliases:
                    return True
                parent = local_classes.get(base_name)
                if parent is not None and inherits_soft(parent, seen):
                    return True
            return False

        for node in local_classes.values():
            bases = {_ast_name(base).split(".")[-1] for base in node.bases}
            if "Base" not in bases:
                continue
            assignments = _class_assignments(node)
            table = _ast_string(assignments.get("__tablename__"))
            if not table:
                continue
            fields = tuple(sorted(name for name in {"is_deleted", "deleted_at", "deleted_by"} if name in assignments))
            inherited = inherits_soft(node)
            if table in IMMUTABLE_APPEND_ONLY_TABLES:
                category = "immutable_append_only_exception"
            elif table in TRANSIENT_OPERATIONAL_TABLES:
                category = "transient_operational_exception"
            elif table in PROTECTED_TABLES:
                category = "protected_business"
            else:
                category = "business_unregistered"
            try:
                display_file = str(mf.relative_to(REPO_ROOT))
            except ValueError:
                display_file = str(mf)
            entries.append(ModelInventoryEntry(
                file=display_file,
                model=node.name,
                table=table,
                category=category,
                fields=fields,
                inherited_soft_delete=inherited,
            ))
    return entries


def check_soft_delete_models(
    verbose: bool = False,
    strict: bool = False,
) -> dict[str, Any]:
    details: list[str] = []
    status = PASS
    inventory = _model_inventory()

    if not MODELS_DIR.exists():
        details.append("Models directory not found")
        return {"status": WARNING, "details": details, "inventory": []}

    missing: list[str] = []
    missing_default_filter: list[str] = []
    unregistered: list[str] = []
    exceptions: list[str] = []
    compliant: list[str] = []

    for entry in inventory:
        has_soft_delete = bool(entry.fields) or entry.inherited_soft_delete
        if entry.category.endswith("exception"):
            exceptions.append(f"{entry.table} ({entry.category})")
        elif has_soft_delete:
            compliant.append(entry.table)
            if entry.category == "protected_business" and not entry.default_filter_verified:
                missing_default_filter.append(entry.table)
        else:
            missing.append(entry.table)
            if entry.category == "business_unregistered":
                unregistered.append(entry.table)

    details.append(f"{len(inventory)} model class(es) inventoried at class/table level")
    details.append(f"{len(compliant)} model(s) with direct or inherited soft-delete support")
    if exceptions:
        details.append("Documented lifecycle exceptions: " + ", ".join(sorted(exceptions)))
    if missing:
        details.append(
            "Business model(s) without soft delete: " + ", ".join(sorted(missing))
        )
        details.append(
            "Default query filtering and restore authorization require runtime tests; "
            "static inventory does not claim those controls are present."
        )
        status = FAIL if strict else WARNING
    if unregistered:
        details.append(
            "Unregistered business table(s) require registry ownership: "
            + ", ".join(sorted(unregistered))
        )
        status = FAIL if strict else WARNING
    if missing_default_filter:
        details.append(
            "Default-filter evidence is not statically verified for protected business table(s): "
            + ", ".join(sorted(missing_default_filter))
        )
        status = FAIL if strict else WARNING
    if not missing and not unregistered and not missing_default_filter:
        details.append("All inventoried business models have direct or inherited soft-delete support")

    serialised_inventory = [
        {
            "file": entry.file,
            "model": entry.model,
            "table": entry.table,
            "category": entry.category,
            "fields": list(entry.fields),
            "inherited_soft_delete": entry.inherited_soft_delete,
            "default_filter_verified": entry.default_filter_verified,
        }
        for entry in inventory
    ]
    return {
        "status": status,
        "details": details,
        "inventory": serialised_inventory,
        "strict": strict,
        "missing_soft_delete": sorted(missing),
        "missing_default_filter": sorted(missing_default_filter),
    }


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
    strict: bool = False,
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
            **check_soft_delete_models(verbose=verbose, strict=strict),
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
    parser.add_argument(
        "--strict", action="store_true",
        help="Treat real Rule 10 business-model gaps as blocking failures",
    )
    args = parser.parse_args(argv)

    if args.ci:
        global _USE_COLOR
        _USE_COLOR = False

    results = run_all_checks(
        staged_only=args.pre_commit,
        verbose=args.verbose,
        strict=args.strict,
    )

    output = format_results(results, ci=args.ci)
    print(output)

    return determine_exit_code(results)


if __name__ == "__main__":
    sys.exit(main())
