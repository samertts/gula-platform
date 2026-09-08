"""Deterministic platform self-knowledge.

Reuses the inventories the repository already generates instead of rebuilding
them:

* ``docs/api/backend_inventory.json``      — modules and HTTP endpoints
* ``docs/technical-debt/registry.json``     — existing debt items
* ``docs/architecture/GULA_MASTER_NEGATIVE_REGISTER.json`` — audited findings

What it adds is the part no existing generator covers: ORM table ownership,
the Alembic migration graph, and state-machine transition tables, all parsed
statically so that no application import or database connection is required.
"""
from __future__ import annotations

import ast
import collections
import dataclasses
import json
import pathlib
from typing import Any

REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
BACKEND_APP = REPO_ROOT / "backend" / "app"
MIGRATIONS = REPO_ROOT / "backend" / "migrations" / "versions"


@dataclasses.dataclass
class Inventory:
    tables: dict[str, list[str]]          # table -> owning "app/<package>" paths
    migrations: dict[str, dict[str, Any]]  # revision -> {file, downs}
    endpoints: int
    modules: list[str]
    transition_tables: dict[str, list[list[tuple[str, int]]]]  # file -> per-dict [(key, lineno)]
    sources: dict[str, str]                # which pre-existing artefact was reused

    def summary(self) -> dict[str, Any]:
        return {
            "tables": len(self.tables),
            "migrations": len(self.migrations),
            "endpoints": self.endpoints,
            "modules": len(self.modules),
            "reused_sources": self.sources,
        }


def _module_assign(tree: ast.Module, name: str) -> Any:
    for node in tree.body:
        targets = node.targets if isinstance(node, ast.Assign) else (
            [node.target] if isinstance(node, ast.AnnAssign) else []
        )
        if any(getattr(t, "id", None) == name for t in targets):
            try:
                return ast.literal_eval(node.value)
            except (ValueError, SyntaxError):
                return None
    return None


def _iter_python(root: pathlib.Path):
    for path in sorted(root.rglob("*.py")):
        if "__pycache__" in path.parts:
            continue
        yield path


def collect_tables() -> dict[str, list[str]]:
    """Map every physical table name to the app packages that declare a mapping."""
    owners: dict[str, set[str]] = collections.defaultdict(set)
    for path in _iter_python(BACKEND_APP):
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"))
        except (SyntaxError, UnicodeDecodeError):
            continue
        package = path.relative_to(BACKEND_APP).parts[0]
        for node in ast.walk(tree):
            if not isinstance(node, ast.ClassDef):
                continue
            for stmt in node.body:
                if isinstance(stmt, ast.Assign) and any(
                    getattr(t, "id", None) == "__tablename__" for t in stmt.targets
                ) and isinstance(stmt.value, ast.Constant):
                    owners[stmt.value.value].add(package)
    return {table: sorted(pkgs) for table, pkgs in owners.items()}


def collect_migrations() -> dict[str, dict[str, Any]]:
    """Parse the Alembic graph without importing env.py or touching a database."""
    graph: dict[str, dict[str, Any]] = {}
    duplicates: dict[str, list[str]] = collections.defaultdict(list)
    if not MIGRATIONS.is_dir():
        return graph
    for path in sorted(MIGRATIONS.glob("*.py")):
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"))
        except (SyntaxError, UnicodeDecodeError):
            continue
        revision = _module_assign(tree, "revision")
        if not revision:
            continue
        down = _module_assign(tree, "down_revision")
        downs = list(down) if isinstance(down, (tuple, list)) else ([down] if down else [])
        duplicates[revision].append(path.name)
        graph[revision] = {"file": path.name, "downs": [d for d in downs if d],
                           "files": duplicates[revision]}
    return graph


def collect_transition_tables() -> dict[str, list[list[tuple[str, int]]]]:
    """Find state-transition dict literals so duplicate keys can be detected."""
    found: dict[str, list[list[tuple[str, int]]]] = {}
    for path in _iter_python(BACKEND_APP):
        if "state_machine" not in path.name:
            continue
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"))
        except (SyntaxError, UnicodeDecodeError):
            continue
        rel = str(path.relative_to(REPO_ROOT))
        # Keys are grouped per dict literal.  Pooling them per file would report a
        # name reused by two unrelated maps as a collision, which it is not.
        per_dict: list[list[tuple[str, int]]] = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Dict) and len(node.keys) > 3:
                literal = [
                    (key.value, key.lineno)
                    for key in node.keys
                    if isinstance(key, ast.Constant) and isinstance(key.value, str)
                ]
                if literal:
                    per_dict.append(literal)
        if per_dict:
            found[rel] = per_dict
    return found


def _load_json(rel: str) -> dict[str, Any] | None:
    path = REPO_ROOT / rel
    if not path.is_file():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError):
        return None


def collect() -> Inventory:
    sources: dict[str, str] = {}
    backend = _load_json("docs/api/backend_inventory.json")
    if backend:
        sources["endpoints"] = "docs/api/backend_inventory.json"
        endpoints = int(backend.get("total_endpoints") or 0)
        modules = sorted((backend.get("modules") or {}).keys())
    else:
        endpoints, modules = 0, []
    if _load_json("docs/technical-debt/registry.json"):
        sources["technical_debt"] = "docs/technical-debt/registry.json"
    if _load_json("docs/architecture/GULA_MASTER_NEGATIVE_REGISTER.json"):
        sources["negative_register"] = "docs/architecture/GULA_MASTER_NEGATIVE_REGISTER.json"
    return Inventory(
        tables=collect_tables(),
        migrations=collect_migrations(),
        endpoints=endpoints,
        modules=modules,
        transition_tables=collect_transition_tables(),
        sources=sources,
    )
