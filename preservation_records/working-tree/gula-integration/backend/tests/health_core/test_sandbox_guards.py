"""Static guardrails proving the Health Core package cannot reach MPI or a DB.

This test uses AST inspection (not string matching) so documentation prose such
as "no MPI calls" does not create false positives. It applies to every file that
any parallel workstream adds under ``app/health_core``.
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

APP_HEALTH_CORE = Path(__file__).resolve().parents[2] / "app" / "health_core"
BACKEND_ROOT = Path(__file__).resolve().parents[2]

FORBIDDEN_IMPORT_PARTS = (
    "mpi",
    "canonical_patient",
    "citizen",
    "nhid",
    "database",
    "sqlalchemy",
    "alembic",
    "httpx",
    "requests",
    "socket",
)
FORBIDDEN_NAMES = {
    "resolve_identity",
    "link_patient",
    "link_citizen",
    "SessionLocal",
    "create_engine",
    "get_db",
    "national_id",
    "nid_hash",
    "health_number",
    "NHID",
}


def _iter_python_files() -> list[Path]:
    assert APP_HEALTH_CORE.is_dir(), f"missing expected package: {APP_HEALTH_CORE}"
    return sorted(APP_HEALTH_CORE.rglob("*.py"))


def test_health_core_package_exists_with_source_files():
    files = _iter_python_files()
    assert len(files) >= 5
    for path in files:
        ast.parse(path.read_text(encoding="utf-8"), filename=str(path))


def test_no_forbidden_imports():
    violations: list[str] = []
    for path in _iter_python_files():
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            module = ""
            if isinstance(node, ast.ImportFrom) and node.module:
                module = node.module
            elif isinstance(node, ast.Import):
                module = node.names[0].name if node.names else ""
            if not module:
                continue
            parts = module.lower().split(".")
            if any(part in FORBIDDEN_IMPORT_PARTS for part in parts):
                violations.append(f"{path.relative_to(BACKEND_ROOT)}:{node.lineno} imports {module}")
    assert violations == [], "forbidden identity/DB/network imports:\n" + "\n".join(violations)


def test_no_forbidden_attribute_or_call_names():
    violations: list[str] = []
    for path in _iter_python_files():
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            name = ""
            if isinstance(node, ast.Attribute):
                name = node.attr
            elif isinstance(node, ast.Name):
                name = node.id
            if name in FORBIDDEN_NAMES:
                violations.append(f"{path.relative_to(BACKEND_ROOT)}:{node.lineno} references {name}")
    assert violations == [], "forbidden names:\n" + "\n".join(violations)


def test_no_production_route_activation():
    factory = (BACKEND_ROOT / "app" / "factory.py").read_text(encoding="utf-8")
    main = (BACKEND_ROOT / "app" / "main.py").read_text(encoding="utf-8")
    for source, label in ((factory, "factory.py"), (main, "main.py")):
        assert "health_core" not in source, f"{label} must not wire health_core routes"
