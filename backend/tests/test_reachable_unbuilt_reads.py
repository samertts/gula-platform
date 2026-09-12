"""NR-064 / NR-067 — a registered route may not read a table no migration builds.

NR-064 was one instance: `POST /admin/citizen-relationships` is registered at
`factory.py:599` and its workflow resolved the subject with `db.query(Citizen)`
over `national_citizens`, which no migration creates. Every create raised
UndefinedTable before a row existed, and the route's `except Exception` reported
it as a generic 500 -- so the operator was told the workflow failed, not that the
schema was absent.

It survived because the only test of that workflow hands it a fake session whose
`query()` returns a `SimpleNamespace`. A fake cannot notice that the table behind
the model does not exist, so the suite was green on a path that could never run.
That is the shape this file guards, and it is why the guard is static rather than
another fake-backed test.

Measured across `app/`: **483** `query(Model)` sites name a table no migration
creates. Of those, **267 are reachable** from a registered router -- either in
the route module itself or one import hop away, which is exactly NR-064's shape
(the route was clean; its service was not).

**Names are resolved through each file's own imports, never by bare class name.**
That is load-bearing: 32 ORM class names in this repository are mapped to more
than one table. `Citizen` is both `app/services/mpi/models.py` (built) and
`app/national/domain/citizen.py` (unbuilt); `Patient` is both `patients` (built)
and `national_patients` (unbuilt). A bare-name scan reported 838 sites where
there are 483 -- a 42% false-positive rate -- and, worse, silently missed
NR-064's own `Citizen` line because the built homonym won the dictionary.

The ledger may shrink. It may never grow, and no new route module may appear.
"""

from __future__ import annotations

import ast
import pathlib
import re

BACKEND = pathlib.Path(__file__).resolve().parents[1]
APP = BACKEND / "app"
EVIDENCE = BACKEND.parent / "docs" / "architecture" / "evidence-created-tables.json"
FACTORY = APP / "factory.py"

#: Registered route modules that reach a read of an unbuilt table, and how many
#: such reads are reachable from each (the module itself plus one import hop).
#: Every one is the NR-064 failure waiting to be triggered.
DECLARED_REACHABLE_UNBUILT_READS = {
    "app/citizen_platform/routes.py": 1,
    "app/national/background_platform/api/routes.py": 26,
    "app/national/document_platform/api/routes.py": 29,
    "app/national/observability/api/routes.py": 29,
    "app/national/rules_engine/api/routes.py": 10,
    "app/national/scheduling_platform/api/routes.py": 41,
    "app/national/task_engine/api/routes.py": 3,
    "app/national/workflow_runtime/api/routes.py": 7,
    "app/nursing/routes.py": 9,
    "app/routes/clinical.py": 57,
    "app/routes/clinical_quality.py": 55,
}

#: The module NR-064 was found in. It is named separately from the ledger above
#: because it is a repaired defect rather than a declared backlog entry: it must
#: stay at zero, and a ledger it is absent from cannot say that.
NR_064_MODULES = (
    "app/routes/citizen_relationship_admin.py",
    "app/identity/services/citizen_relationship_service.py",
)


def _built() -> set[str]:
    import json

    return set(json.loads(EVIDENCE.read_text(encoding="utf-8")))


def _parse(path: pathlib.Path) -> ast.Module | None:
    try:
        return ast.parse(path.read_text(encoding="utf-8", errors="ignore"))
    except (SyntaxError, FileNotFoundError):
        return None


def _qualified_models() -> dict[tuple[str, str], str]:
    """(module path, class name) -> table name.

    Qualified by module on purpose. See the module docstring: bare class names
    are ambiguous 32 times over in this repository.
    """
    out: dict[tuple[str, str], str] = {}
    for path in APP.rglob("*.py"):
        if "__pycache__" in path.parts:
            continue
        tree = _parse(path)
        if tree is None:
            continue
        for cls in (n for n in ast.walk(tree) if isinstance(n, ast.ClassDef)):
            for stmt in cls.body:
                if isinstance(stmt, ast.Assign) and isinstance(stmt.value, ast.Constant):
                    for target in stmt.targets:
                        if isinstance(target, ast.Name) and target.id == "__tablename__":
                            out[(str(path.relative_to(BACKEND)), cls.name)] = stmt.value.value
    return out


def _imports_and_names(
    path: pathlib.Path, qualified: dict[tuple[str, str], str]
) -> tuple[set[str], dict[str, str]]:
    """(app-local modules imported, local name -> table it actually names)."""
    deps: set[str] = set()
    names: dict[str, str] = {}
    tree = _parse(path)
    if tree is None:
        return deps, names
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module and node.module.startswith("app."):
            module = str(pathlib.Path(node.module.replace(".", "/") + ".py"))
            if (BACKEND / module).exists():
                deps.add(module)
            for alias in node.names:
                table = qualified.get((module, alias.name))
                if table:
                    names[alias.asname or alias.name] = table
    rel = str(path.relative_to(BACKEND))
    for (module, cls), table in qualified.items():
        if module == rel:
            names[cls] = table
    return deps, names


def _unbuilt_reads(
    module: str, qualified: dict[tuple[str, str], str], built: set[str]
) -> list[tuple[str, str, int]]:
    path = BACKEND / module
    tree = _parse(path)
    if tree is None:
        return []
    _, names = _imports_and_names(path, qualified)
    found: list[tuple[str, str, int]] = []
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr == "query"
            and node.args
            and isinstance(node.args[0], ast.Name)
        ):
            table = names.get(node.args[0].id)
            if table and table not in built:
                found.append((node.args[0].id, table, node.lineno))
    return found


def _registered_route_modules() -> set[str]:
    """Route modules whose router `factory.py` actually includes."""
    source = FACTORY.read_text(encoding="utf-8")
    registered: set[str] = set()
    for match in re.finditer(r"from \.([\w.]+) import (\w+) as (\w+)", source):
        module, _, alias = match.groups()
        if f"{alias}.router" in source or f"include_router({alias}" in source:
            candidate = "app/" + module.replace(".", "/") + ".py"
            if (BACKEND / candidate).exists():
                registered.add(candidate)
    for match in re.finditer(r"from \.routes import (\w+) as (\w+)", source):
        name, alias = match.groups()
        if f"{alias}.router" in source:
            candidate = f"app/routes/{name}.py"
            if (BACKEND / candidate).exists():
                registered.add(candidate)
    return registered


def _measure() -> dict[str, int]:
    qualified = _qualified_models()
    built = _built()
    counts: dict[str, int] = {}
    for route in _registered_route_modules():
        total = len(_unbuilt_reads(route, qualified, built))
        deps, _ = _imports_and_names(BACKEND / route, qualified)
        for dep in deps:
            total += len(_unbuilt_reads(dep, qualified, built))
        if total:
            counts[route] = total
    return counts


def test_model_names_are_resolved_through_imports_not_by_bare_name() -> None:
    """Guard the guard, against the specific mistake that hid NR-064.

    If class names were ever resolved without their module, the built homonym
    would win for `Citizen` and `Patient` and this whole file would go quiet on
    exactly the tables it exists to watch.
    """
    qualified = _qualified_models()
    for name, expected in (("Citizen", 2), ("Patient", 2)):
        tables = {table for (_, cls), table in qualified.items() if cls == name}
        assert len(tables) >= expected, (
            f"{name} no longer maps to at least {expected} distinct tables "
            f"({tables}); the ambiguity this scan resolves may have changed, and "
            "the resolution logic must be rechecked rather than assumed"
        )


def test_the_scan_still_finds_registered_routers() -> None:
    """A scan that finds no routers would declare the whole surface unreachable."""
    registered = _registered_route_modules()
    assert len(registered) >= 60, (
        f"only {len(registered)} registered route modules found; the factory scan "
        "has drifted and every reachability claim below would be understated"
    )


def test_the_citizen_relationship_workflow_reads_only_built_tables() -> None:
    """NR-064, as a regression rather than a memory.

    The create path resolved its subject against `national_citizens` and its
    patient against `national_patients`, neither of which any migration builds.
    Both are gone: the subject resolves against the canonical `niam_persons`, and
    `patient_id` is refused at the API until NR-022 decides the clinical subject.
    """
    qualified = _qualified_models()
    built = _built()
    offending = {
        module: _unbuilt_reads(module, qualified, built)
        for module in NR_064_MODULES
        if _unbuilt_reads(module, qualified, built)
    }
    assert offending == {}, (
        "the citizen relationship workflow reads a table no migration builds "
        "again, so its only write path raises UndefinedTable and surfaces as a "
        f"generic 500: {offending}"
    )


def test_no_new_route_module_reads_an_unbuilt_table() -> None:
    """A new one is a new endpoint that 500s the first time it is called."""
    appeared = sorted(set(_measure()) - set(DECLARED_REACHABLE_UNBUILT_READS))
    assert appeared == [], (
        "these registered route modules now reach a read of a table no migration "
        "creates. Build the table under an activation review, or stop reading it: "
        f"{appeared}"
    )


def test_the_reachable_unbuilt_read_ledger_does_not_grow() -> None:
    """The ratchet, reported per module so a failure names what to look at."""
    current = _measure()
    widened = {
        module: (declared, current[module])
        for module, declared in DECLARED_REACHABLE_UNBUILT_READS.items()
        if current.get(module, 0) > declared
    }
    assert widened == {}, (
        f"reachable reads of unbuilt tables were added (declared -> now): {widened}"
    )
    resolved = sorted(
        module for module in DECLARED_REACHABLE_UNBUILT_READS if module not in current
    )
    assert resolved == [], (
        "these modules no longer read an unbuilt table; remove them from the "
        f"ledger so the ratchet keeps its grip: {resolved}"
    )
