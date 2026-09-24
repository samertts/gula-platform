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
from collections.abc import Iterable, Iterator
from typing import Any

BACKEND = pathlib.Path(__file__).resolve().parents[1]
APP = BACKEND / "app"
MIGRATIONS = BACKEND / "migrations" / "versions"
EVIDENCE = BACKEND.parent / "docs" / "architecture" / "evidence-created-tables.json"


def parse(path: pathlib.Path) -> ast.Module | None:
    try:
        return ast.parse(path.read_text(encoding="utf-8", errors="ignore"))
    except (SyntaxError, FileNotFoundError):
        return None


def app_modules() -> list[pathlib.Path]:
    return [p for p in APP.rglob("*.py") if "__pycache__" not in p.parts]


def _created_in(path: pathlib.Path) -> set[str]:
    """Tables one migration creates, whether or not the name is a literal.

    Three forms occur in this chain and all three must resolve:

    * ``op.create_table("literal", ...)``;
    * ``op.create_table(_TABLE, ...)`` against a module-level string constant,
      which eight migrations use so the name is stated once;
    * ``op.create_table(name, ...)`` inside a local helper such as
      ``_create_if_missing(name, columns, constraints)``, where the literal
      lives at the **call site** rather than at the create.

    The third form is why this function exists. `evidence-created-tables.json`
    was built by matching literals only, so it recorded three tables as unbuilt
    that `20260814_0002_organization_structure.py` does create --
    `niam_admin_units`, `niam_organization_representatives` and
    `niam_organization_ownerships`. Every ledger keyed on "is this table built?"
    inherited that error in the direction that overstates the problem: rows
    against those tables were counted as reads and writes against nothing.
    """
    tree = parse(path)
    if tree is None:
        return set()

    constants = {
        node.targets[0].id: node.value.value
        for node in tree.body
        if isinstance(node, ast.Assign)
        and len(node.targets) == 1
        and isinstance(node.targets[0], ast.Name)
        and isinstance(node.value, ast.Constant)
        and isinstance(node.value.value, str)
    }

    # Local helpers that forward one of their own parameters to create_table.
    helpers: dict[str, int] = {}
    for fn in (n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)):
        params = [a.arg for a in fn.args.args]
        for call in ast.walk(fn):
            if (
                isinstance(call, ast.Call)
                and isinstance(call.func, ast.Attribute)
                and call.func.attr == "create_table"
                and call.args
                and isinstance(call.args[0], ast.Name)
                and call.args[0].id in params
            ):
                helpers[fn.name] = params.index(call.args[0].id)

    created: set[str] = set()
    for call in ast.walk(tree):
        if not isinstance(call, ast.Call) or not call.args:
            continue
        if isinstance(call.func, ast.Attribute) and call.func.attr == "create_table":
            first = call.args[0]
            if isinstance(first, ast.Constant) and isinstance(first.value, str):
                created.add(first.value)
            elif isinstance(first, ast.Name) and first.id in constants:
                created.add(constants[first.id])
        elif isinstance(call.func, ast.Name) and call.func.id in helpers:
            index = helpers[call.func.id]
            if len(call.args) > index and isinstance(call.args[index], ast.Constant):
                value = call.args[index].value
                if isinstance(value, str):
                    created.add(value)
    return created


@functools.lru_cache(maxsize=1)
def built_tables() -> frozenset[str]:
    """Tables the migration chain actually creates.

    Derived from the migrations rather than read from a snapshot. The snapshot
    at `EVIDENCE` is kept for consumers outside the test suite and is asserted
    equal to this in `test_built_table_evidence.py`; when they disagree, the
    migrations win and the snapshot is regenerated.
    """
    created: set[str] = set()
    for path in sorted(MIGRATIONS.glob("*.py")):
        created |= _created_in(path)
    return frozenset(created)


@functools.lru_cache(maxsize=1)
def declared_built_tables() -> frozenset[str]:
    """What the checked-in snapshot claims, for comparison against the chain."""
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


# ── Reachability: which modules the running application can actually reach ────
#
# NR-079. Three guards asked "is this reachable from a registered router?" and
# two of them answered with an instrument that could not see the application:
#
# * registration was read by regex over `factory.py`, matching
#   `from .x import y as z` and `from .routes import name as alias`. The factory
#   also registers a **bulk block** -- `from .routes import (admin, ehr,
#   ehr_fhir, …)` then `for r in core_routes + feature_routes + …:
#   app.include_router(r.router)` -- which no regex matched. Measured against
#   the running application: the regex finds **79** route modules and the app
#   serves **142**. Zero false positives, 63 false negatives; every reachability
#   number built on it was a strict undercount.
# * import resolution handled `from app.x.y import Z` and `from ..models import
#   Z`, and dropped `from app.services import ehr_service` -- a package import
#   naming a **submodule**, which resolves to `app/services/ehr_service.py` and
#   not to `app/services.py`. That single form hid `app/services/ehr_service.py`
#   entirely: 17 unguarded create paths that a first Phase G pass classified as
#   DEAD are reached from `app/routes/ehr.py` line 29.
#
# Together: the reachable closure goes from 612 modules to 994, and NR-067's
# reachable unbuilt reads from 418 across 20 route modules to **610 across 24**.
# No declared module's count changed; four modules were simply invisible.
#
# So registration is now read from the **running application** rather than from
# the file that configures it. `route.endpoint.__module__` is what FastAPI will
# actually serve, and it stays correct however `factory.py` is rewritten.


def every_route(routes: Iterable[Any]) -> Iterator[Any]:
    """Every APIRoute the application will serve, including included routers.

    FastAPI stores an included router as an opaque `_IncludedRouter` holding the
    real one on `original_router`, so one pass over `app.routes` sees ~130
    entries where the served surface is ~2100. Recursing is the difference
    between measuring the application and measuring a wrapper.
    """
    for route in routes:
        original = getattr(route, "original_router", None)
        if original is not None:
            yield from every_route(original.routes)
        elif getattr(route, "dependant", None) is not None:
            yield route


def route_modules(app: Any) -> frozenset[str]:
    """Modules that define a route the running application serves.

    Both `create_app()` and a started application answer the same here --
    measured at 2102 served routes across 141 modules either way. An earlier
    version of this docstring said the app must be *started* because routers
    register from the lifespan, and that `create_app()` alone has seven routed
    paths; neither holds with the FastAPI version in use, which keeps an
    included router as an opaque `_IncludedRouter` on `app.routes` rather than
    flattening it at include time. `every_route` recursing is what matters, not
    startup -- and a probe that skipped it reported zero routes for every
    package before this was corrected.
    """
    found: set[str] = set()
    for route in every_route(app.routes):
        module = getattr(getattr(route, "endpoint", None), "__module__", "")
        if not module.startswith("app."):
            continue
        candidate = str(pathlib.Path(module.replace(".", "/") + ".py"))
        if (BACKEND / candidate).exists():
            found.add(candidate)
    return frozenset(found)


def imported_modules(path: pathlib.Path) -> frozenset[str]:
    """App-local modules this file imports, in every form this repository uses.

    Absolute (`from app.x.y import Z`), relative (`from ..models import Z`),
    package-plus-submodule (`from app.services import ehr_service`, which means
    `app/services/ehr_service.py`) and plain `import app.x.y`. The third form is
    the one that was missing and it is not rare -- it adds 421 edges.
    """
    deps: set[str] = set()
    tree = parse(path)
    if tree is None:
        return frozenset(deps)

    def add(candidate: str) -> None:
        if (BACKEND / candidate).exists():
            deps.add(candidate)

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name.startswith("app."):
                    add(str(pathlib.Path(alias.name.replace(".", "/") + ".py")))
            continue
        if not isinstance(node, ast.ImportFrom):
            continue
        if node.level == 0:
            if not (node.module and node.module.startswith("app.")):
                continue
            base = pathlib.Path(node.module.replace(".", "/"))
        else:
            base = path.parent.relative_to(BACKEND)
            for _ in range(node.level - 1):
                base = base.parent
            if node.module:
                base = base / pathlib.Path(node.module.replace(".", "/"))
        add(str(base) + ".py")
        add(str(base / "__init__.py"))
        for alias in node.names:
            add(str(base / alias.name) + ".py")
    return frozenset(deps)
