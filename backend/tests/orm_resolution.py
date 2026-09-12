"""One correct way to ask "which table does this name mean?".

Three separate guard defects this session came from the same shortcut: mapping a
bare ORM class name to a table. **32 class names in this repository are mapped
to more than one table.** `Citizen` is both `app/services/mpi/models.py` (built)
and `app/national/domain/citizen.py` (unbuilt); `Patient` is both `patients` and
`national_patients`; `ComplianceCheck` is three different tables.

What that shortcut cost, in order:

1. NR-065's audit detector matched `TaskAuditLog(` as the canonical `AuditLog(`
   and passed on exactly the thing it existed to reject.
2. NR-062's ledger counted `query_audit_log(` and `_write_audit` as canonical
   audit calls, hiding two packages and 57 mutating endpoints.
3. NR-067's first scan reported 838 unbuilt reads against a true 483 -- and
   silently missed NR-064's own `Citizen` line, because the built homonym won
   the dictionary.

So resolution lives here, once, and every guard imports it. The rules:

* a name is resolved through the **importing file's own** ImportFrom statements;
* absolute (`from app.x.y import Z`) and relative (`from ..models import Z`)
  imports both resolve;
* a package re-export (`from app.ehr.models import CarePlan`, where
  `app/ehr/models/__init__.py` re-exports from `care_plan.py`) is followed one
  hop, which is what `app/ehr`, `app/services` and `app/national` actually use;
* a name that resolves to no `__tablename__` is **not** an ORM model and is
  excluded rather than guessed. `GatewayMessage` is the live example: it is a
  plain class in `app/integration/gateway/base.py`, and a bare-name scan has no
  way to tell it from a model.

This module is deliberately not named `test_*`, so pytest does not collect it.
"""

from __future__ import annotations

import ast
import functools
import json
import pathlib

BACKEND = pathlib.Path(__file__).resolve().parents[1]
APP = BACKEND / "app"
EVIDENCE = BACKEND.parent / "docs" / "architecture" / "evidence-created-tables.json"


def parse(path: pathlib.Path) -> ast.Module | None:
    try:
        return ast.parse(path.read_text(encoding="utf-8", errors="ignore"))
    except (SyntaxError, FileNotFoundError):
        return None


def app_modules() -> list[pathlib.Path]:
    return [p for p in APP.rglob("*.py") if "__pycache__" not in p.parts]


@functools.lru_cache(maxsize=1)
def built_tables() -> frozenset[str]:
    """Tables an `op.create_table` in the migration chain actually creates."""
    return frozenset(json.loads(EVIDENCE.read_text(encoding="utf-8")))


@functools.lru_cache(maxsize=1)
def qualified_models() -> dict[tuple[str, str], str]:
    """(module path relative to backend/, class name) -> table name."""
    out: dict[tuple[str, str], str] = {}
    for path in app_modules():
        tree = parse(path)
        if tree is None:
            continue
        rel = str(path.relative_to(BACKEND))
        for cls in (n for n in ast.walk(tree) if isinstance(n, ast.ClassDef)):
            for stmt in cls.body:
                if isinstance(stmt, ast.Assign) and isinstance(stmt.value, ast.Constant):
                    for target in stmt.targets:
                        if isinstance(target, ast.Name) and target.id == "__tablename__":
                            out[(rel, cls.name)] = stmt.value.value
    return out


def ambiguous_class_names() -> dict[str, set[str]]:
    """Class names mapped to more than one table -- the reason this module exists."""
    by_name: dict[str, set[str]] = {}
    for (_, cls), table in qualified_models().items():
        by_name.setdefault(cls, set()).add(table)
    return {name: tables for name, tables in by_name.items() if len(tables) > 1}


def _candidate_modules(path: pathlib.Path, node: ast.ImportFrom) -> list[str]:
    """Module file paths an ImportFrom could refer to, relative to backend/."""
    if node.level == 0:
        if not (node.module and node.module.startswith("app.")):
            return []
        base = pathlib.Path(node.module.replace(".", "/"))
    else:
        base = path.parent.relative_to(BACKEND)
        for _ in range(node.level - 1):
            base = base.parent
        if node.module:
            base = base / pathlib.Path(node.module.replace(".", "/"))
    return [str(base) + ".py", str(base / "__init__.py")]


def _lookup(modules: list[str], name: str, depth: int = 0) -> str | None:
    models = qualified_models()
    for module in modules:
        table = models.get((module, name))
        if table:
            return table
    if depth > 1:
        return None
    # Follow a package __init__ re-export one hop.
    for module in modules:
        path = BACKEND / module
        if path.name != "__init__.py" or not path.exists():
            continue
        tree = parse(path)
        if tree is None:
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and any(a.name == name for a in node.names):
                table = _lookup(_candidate_modules(path, node), name, depth + 1)
                if table:
                    return table
    return None


def tables_by_local_name(path: pathlib.Path) -> dict[str, str]:
    """Local name -> table, as *this file* would resolve it.

    Names that resolve to no `__tablename__` are absent, not guessed.
    """
    names: dict[str, str] = {}
    tree = parse(path)
    if tree is None:
        return names
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            candidates = _candidate_modules(path, node)
            for alias in node.names:
                table = _lookup(candidates, alias.name)
                if table:
                    names[alias.asname or alias.name] = table
    rel = str(path.relative_to(BACKEND))
    for (module, cls), table in qualified_models().items():
        if module == rel:
            names[cls] = table
    return names
