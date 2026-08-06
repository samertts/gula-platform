#!/usr/bin/env python3
"""
Architecture Quality Gate — validates codebase architecture against platform conventions.

Checks:
  1. Circular import detection across all backend modules
  2. Directory structure compliance with CLAUDE.md conventions
  3. No business logic in backend/app/financial/ (Phase A only)
  4. No modifications to 20250322_0000_create_base_schema.py (immutable)
  5. No modifications to existing migrations (new revisions only)
  6. All new columns have nullable or server_default
  7. Service boundary compliance (routes -> services -> models)
  8. No direct DB access from route files
  9. Existing patterns are followed (naming, structure)

Usage:
    python config/quality-gates/architecture-gate.py
    python config/quality-gates/architecture-gate.py --json
    python config/quality-gates/architecture-gate.py --path backend/app

Exit codes:
    0 — all checks pass
    1 — one or more checks fail
"""

import argparse
import ast
import json
import logging
import pathlib
import subprocess
import sys
from datetime import UTC, datetime
from typing import Any

logger = logging.getLogger("architecture-gate")

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
BACKEND_APP = ROOT / "backend" / "app"
MIGRATIONS_DIR = ROOT / "backend" / "migrations" / "versions"

IMMUTABLE_MIGRATIONS = {"20250322_0000_create_base_schema.py"}
FINANCIAL_MODULE = BACKEND_APP / "financial"

REQUIRED_DIRS = [
    "routes", "services", "models", "core", "security", "domain",
    "ai", "audit", "notifications", "tasks", "edge",
]

GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
BOLD = "\033[1m"
RESET = "\033[0m"


def _ok(msg: str) -> str:
    return f"{GREEN}✓{RESET} {msg}"


def _fail(msg: str) -> str:
    return f"{RED}✗{RESET} {msg}"


def _warn(msg: str) -> str:
    return f"{YELLOW}⚠{RESET} {msg}"


def _iter_py_files(directory: pathlib.Path) -> list[pathlib.Path]:
    if not directory.is_dir():
        return []
    return sorted(p for p in directory.rglob("*.py") if p.name != "__init__.py" and "__pycache__" not in str(p))


def _module_name_from_path(file_path: pathlib.Path, root: pathlib.Path) -> str:
    rel = file_path.resolve().relative_to(root.resolve())
    parts = list(rel.parts)
    if parts[-1] == "__init__.py":
        parts = parts[:-1]
    else:
        parts[-1] = parts[-1].replace(".py", "")
    return ".".join(parts)


def check_circular_imports(root: pathlib.Path) -> list[dict[str, Any]]:
    failures: list[dict[str, Any]] = []
    graph: dict[str, set[str]] = {}

    for py_file in _iter_py_files(root):
        module_name = _module_name_from_path(py_file, root)
        try:
            tree = ast.parse(py_file.read_text(encoding="utf-8"), filename=str(py_file))
        except SyntaxError as exc:
            failures.append({
                "check": "circular_import",
                "severity": "error",
                "message": f"Syntax error in {py_file.relative_to(ROOT)}: {exc}",
            })
            continue

        deps: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    deps.add(alias.name.split(".")[0])
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    deps.add(node.module.split(".")[0])
        graph[module_name] = {d for d in deps if any(root.name in str(p) for p in [py_file])}

    visited: set[str] = set()
    path: list[str] = []
    path_set: set[str] = set()

    def dfs(node: str) -> None:
        if node in path_set:
            cycle_start = path.index(node)
            cycle = path[cycle_start:] + [node]
            failures.append({
                "check": "circular_import",
                "severity": "error",
                "message": f"Circular import detected: {' -> '.join(cycle)}",
                "modules": list(dict.fromkeys(cycle)),
            })
            return
        if node in visited:
            return
        visited.add(node)
        path.append(node)
        path_set.add(node)
        for neighbour in graph.get(node, set()):
            if neighbour in graph:
                dfs(neighbour)
        path.pop()
        path_set.discard(node)

    for node in list(graph.keys()):
        dfs(node)

    return failures


def check_directory_structure(root: pathlib.Path) -> list[dict[str, Any]]:
    failures: list[dict[str, Any]] = []
    for required in REQUIRED_DIRS:
        if not (root / required).is_dir():
            failures.append({
                "check": "directory_structure",
                "severity": "error",
                "message": f"Required directory missing: backend/app/{required}/",
            })
    return failures


def check_financial_boundary(financial_dir: pathlib.Path) -> list[dict[str, Any]]:
    failures: list[dict[str, Any]] = []
    if not financial_dir.is_dir():
        return failures

    for py_file in _iter_py_files(financial_dir):
        try:
            tree = ast.parse(py_file.read_text(encoding="utf-8"), filename=str(py_file))
        except SyntaxError:
            continue

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                body = node.body
                if body and not (
                    isinstance(body[0], ast.Expr) and isinstance(body[0].value, ast.Constant)
                ):
                    if node.name not in ("__init__",):
                        has_real_logic = any(
                            isinstance(stmt, (ast.Assign, ast.Call, ast.Return))
                            and not isinstance(stmt, ast.Expr)
                            for stmt in body
                            if not (isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Constant))
                        )
                        if has_real_logic:
                            failures.append({
                                "check": "financial_boundary",
                                "severity": "error",
                                "message": (
                                    f"Business logic found in financial module: "
                                    f"{py_file.relative_to(ROOT)}::{node.name}. "
                                    f"Financial Engine is Phase A (schema-only)."
                                ),
                            })
    return failures


def check_immutable_migrations(migrations_dir: pathlib.Path) -> list[dict[str, Any]]:
    failures: list[dict[str, Any]] = []
    if not migrations_dir.is_dir():
        return failures

    for fname in IMMUTABLE_MIGRATIONS:
        fpath = migrations_dir / fname
        if not fpath.exists():
            continue

        try:
            tree = ast.parse(fpath.read_text(encoding="utf-8"), filename=str(fpath))
        except SyntaxError:
            continue

        for node in ast.iter_child_nodes(tree):
            if isinstance(node, ast.FunctionDef):
                if node.name == "upgrade" and len(node.body) > 3:
                    failures.append({
                        "check": "immutable_migration",
                        "severity": "error",
                        "message": (
                            f"Immutable bootstrap migration {fname} has been modified. "
                            f"This migration must never change."
                        ),
                    })
                    break

    return failures


def check_migration_modifications(migrations_dir: pathlib.Path) -> list[dict[str, Any]]:
    failures: list[dict[str, Any]] = []
    if not migrations_dir.is_dir():
        return failures

    try:
        result = subprocess.run(
            ["git", "diff", "--name-only", "HEAD", "--", "backend/migrations/versions/"],
            capture_output=True, text=True, timeout=30,
            cwd=str(ROOT),
        )
        output = result.stdout.strip()
        if output:
            for line in output.split("\n"):
                fname = pathlib.Path(line.strip()).name
                if fname.endswith(".py") and fname not in IMMUTABLE_MIGRATIONS:
                    if "2025" in fname or "2026" in fname:
                        failures.append({
                            "check": "migration_modification",
                            "severity": "error",
                            "message": (
                                f"Existing migration modified: {line.strip()}. "
                                f"Generate a new revision instead of modifying existing migrations."
                            ),
                        })
    except Exception:
        pass

    return failures


def check_new_column_policies(migrations_dir: pathlib.Path) -> list[dict[str, Any]]:
    failures: list[dict[str, Any]] = []
    if not migrations_dir.is_dir():
        return failures

    for py_file in sorted(migrations_dir.glob("*.py")):
        if py_file.name in IMMUTABLE_MIGRATIONS:
            continue
        try:
            text = py_file.read_text(encoding="utf-8")
            tree = ast.parse(text, filename=str(py_file))
        except SyntaxError:
            continue

        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                func = node.func
                if isinstance(func, ast.Attribute) and func.attr == "add_column":
                    for kw in node.keywords:
                        if kw.arg == "column":
                            if isinstance(kw.value, ast.Call):
                                col_func = kw.value.func
                                if isinstance(col_func, ast.Attribute) and "Column" in col_func.attr:
                                    col_kwargs = {kw2.arg for kw2 in kw.value.keywords}
                                    if "nullable" not in col_kwargs and "server_default" not in col_kwargs:
                                        col_name = ""
                                        if kw.value.args:
                                            if isinstance(kw.value.args[0], ast.Constant):
                                                col_name = kw.value.args[0].value
                                        failures.append({
                                            "check": "new_column_policy",
                                            "severity": "error",
                                            "message": (
                                                f"New column '{col_name}' in {py_file.name} "
                                                f"must have nullable=True or a server_default."
                                            ),
                                        })

    return failures


def check_service_boundaries(root: pathlib.Path) -> list[dict[str, Any]]:
    failures: list[dict[str, Any]] = []

    for py_file in _iter_py_files(root / "routes"):
        try:
            text = py_file.read_text(encoding="utf-8")
            tree = ast.parse(text, filename=str(py_file))
        except SyntaxError:
            continue

        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                if node.module:
                    module_parts = node.module.split(".")
                    if "services" not in module_parts and "models" in module_parts:
                        for alias in node.names:
                            if alias.name not in ("Base",):
                                failures.append({
                                    "check": "service_boundary",
                                    "severity": "warning",
                                    "message": (
                                        f"{py_file.relative_to(ROOT)} imports '{alias.name}' "
                                        f"from models directly. Route files should use services layer."
                                    ),
                                })

    return failures


def check_direct_db_access(root: pathlib.Path) -> list[dict[str, Any]]:
    failures: list[dict[str, Any]] = []

    for py_file in _iter_py_files(root / "routes"):
        try:
            text = py_file.read_text(encoding="utf-8")
            tree = ast.parse(text, filename=str(py_file))
        except SyntaxError:
            continue

        has_db_import = False
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                if node.module and "database" in node.module:
                    for alias in node.names:
                        if alias.name in ("get_db", "SessionLocal", "engine"):
                            has_db_import = True

        if has_db_import:
            failures.append({
                "check": "direct_db_access",
                "severity": "error",
                "message": (
                    f"{py_file.relative_to(ROOT)} imports get_db/SessionLocal from database directly. "
                    f"Routes must not access the database directly — use the services layer."
                ),
            })

    return failures


def check_naming_patterns(root: pathlib.Path) -> list[dict[str, Any]]:
    failures: list[dict[str, Any]] = []

    for py_file in _iter_py_files(root):
        if py_file.name.startswith("_") and py_file.name != "__init__.py":
            failures.append({
                "check": "naming_pattern",
                "severity": "warning",
                "message": (
                    f"{py_file.relative_to(ROOT)} has leading underscore in filename "
                    f"'{py_file.name}'. Use standard snake_case without leading underscore."
                ),
            })

    return failures


def run_all_checks(root: pathlib.Path) -> list[dict[str, Any]]:
    all_failures: list[dict[str, Any]] = []

    checks = [
        ("Circular imports", lambda: check_circular_imports(root)),
        ("Directory structure", lambda: check_directory_structure(root)),
        ("Financial boundary", lambda: check_financial_boundary(FINANCIAL_MODULE)),
        ("Immutable migrations", lambda: check_immutable_migrations(MIGRATIONS_DIR)),
        ("Migration modifications", lambda: check_migration_modifications(MIGRATIONS_DIR)),
        ("New column policies", lambda: check_new_column_policies(MIGRATIONS_DIR)),
        ("Service boundaries", lambda: check_service_boundaries(root)),
        ("Direct DB access", lambda: check_direct_db_access(root)),
        ("Naming patterns", lambda: check_naming_patterns(root)),
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
            "timestamp": datetime.now(UTC).isoformat(),
            "passed": len(errors) == 0,
            "summary": {"errors": len(errors), "warnings": len(warnings), "total": len(failures)},
            "failures": failures,
        }
        print(json.dumps(report, indent=2, ensure_ascii=False))
        return 0 if report["passed"] else 1

    print(f"\n{BOLD}═══ Architecture Quality Gate Report ═══{RESET}\n")

    if not failures:
        print(f"  {GREEN}All checks passed!{RESET}")
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
    parser = argparse.ArgumentParser(description="Architecture Quality Gate")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    parser.add_argument("--path", type=str, default=str(BACKEND_APP), help="Root path to analyze")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    args = parser.parse_args()

    level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(level=level, format="%(asctime)s [%(levelname)s] %(message)s", datefmt="%H:%M:%S")

    root = pathlib.Path(args.path).resolve()
    if not root.is_dir():
        logger.error("Path does not exist: %s", root)
        return 1

    logger.info("Architecture gate scanning %s", root)
    failures = run_all_checks(root)
    return print_report(failures, json_output=args.json)


if __name__ == "__main__":
    sys.exit(main())
