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

Measured across `app/`: **773** `query(Model)` sites name a table no migration
creates. Of those, **418 are reachable** from a registered router across 20 route
modules -- either in the route module itself or one import hop away, which is
exactly NR-064's shape (the route was clean; its service was not).

Both figures are corrections. This file first said 483 and 267 across 11 modules,
because its own resolver handled only absolute `app.*` imports and therefore could
not see a model reached through `from ..models import X` or through a package
re-export such as `from app.ehr.models import CarePlan`. Nine route modules were
invisible entirely, `app/routes/care_continuum.py` (44) and `app/routes/hospital.py`
(17) among them. Resolution now lives in `tests/orm_resolution.py`, once, and that
module records why.

**Names are resolved through each file's own imports, never by bare class name.**
32 ORM class names here map to more than one table -- `Citizen` is both
`app/services/mpi/models.py` (built) and `app/national/domain/citizen.py`
(unbuilt); `Patient` is both `patients` and `national_patients`. A bare-name scan
reported 838 where the true figure was smaller *and* silently missed NR-064's own
`Citizen` line, because the built homonym won the dictionary.

The ledger may shrink. It may never grow, and no new route module may appear.
"""

from __future__ import annotations

import ast
import pathlib
import re

from tests.orm_resolution import (
    APP,
    BACKEND,
    ambiguous_class_names,
    built_tables,
    parse,
    tables_by_local_name,
)

FACTORY = APP / "factory.py"

#: Registered route modules that reach a read of an unbuilt table, and how many
#: such reads are reachable from each (the module itself plus one import hop).
#: Every one is the NR-064 failure waiting to be triggered.
DECLARED_REACHABLE_UNBUILT_READS = {
    "app/citizen_platform/routes.py": 1,
    "app/command_intelligence/routes.py": 10,
    "app/knowledge_graph/routes.py": 20,
    "app/national/background_platform/api/routes.py": 26,
    "app/national/document_platform/api/routes.py": 29,
    "app/national/observability/api/routes.py": 29,
    "app/national/rules_engine/api/routes.py": 10,
    "app/national/scheduling_platform/api/routes.py": 41,
    "app/national/task_engine/api/routes.py": 3,
    "app/national/workflow_runtime/api/routes.py": 7,
    "app/nhdw/routes.py": 7,
    "app/nursing/routes.py": 9,
    "app/roadmap/routes.py": 19,
    "app/routes/care_continuum.py": 44,
    "app/routes/clinical.py": 57,
    "app/routes/clinical_quality.py": 55,
    "app/routes/hospital.py": 17,
    "app/routes/national_data.py": 15,
    "app/routes/national_streaming.py": 6,
    "app/simulation/routes.py": 13,
}

#: The module NR-064 was found in. It is named separately from the ledger above
#: because it is a repaired defect rather than a declared backlog entry: it must
#: stay at zero, and a ledger it is absent from cannot say that.
NR_064_MODULES = (
    "app/routes/citizen_relationship_admin.py",
    "app/identity/services/citizen_relationship_service.py",
)


def _imported_modules(path: pathlib.Path) -> set[str]:
    """App-local modules this file imports, absolute or relative."""
    deps: set[str] = set()
    tree = parse(path)
    if tree is None:
        return deps
    for node in ast.walk(tree):
        if not isinstance(node, ast.ImportFrom):
            continue
        if node.level == 0:
            if not (node.module and node.module.startswith("app.")):
                continue
            candidate = str(pathlib.Path(node.module.replace(".", "/") + ".py"))
        else:
            base = path.parent.relative_to(BACKEND)
            for _ in range(node.level - 1):
                base = base.parent
            if node.module:
                base = base / pathlib.Path(node.module.replace(".", "/"))
            candidate = str(base) + ".py"
        if (BACKEND / candidate).exists():
            deps.add(candidate)
    return deps


def _unbuilt_reads(module: str) -> list[tuple[str, str, int]]:
    path = BACKEND / module
    tree = parse(path)
    if tree is None:
        return []
    names = tables_by_local_name(path)
    built = built_tables()
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
    counts: dict[str, int] = {}
    for route in _registered_route_modules():
        total = len(_unbuilt_reads(route))
        for dep in _imported_modules(BACKEND / route):
            total += len(_unbuilt_reads(dep))
        if total:
            counts[route] = total
    return counts


def test_model_names_are_resolved_through_imports_not_by_bare_name() -> None:
    """Guard the guard, against the specific mistake that hid NR-064.

    If class names were ever resolved without their module, the built homonym
    would win for `Citizen` and `Patient` and this whole file would go quiet on
    exactly the tables it exists to watch.
    """
    ambiguous = ambiguous_class_names()
    for name, expected in (("Citizen", 2), ("Patient", 2)):
        tables = ambiguous.get(name, set())
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
    offending = {
        module: _unbuilt_reads(module)
        for module in NR_064_MODULES
        if _unbuilt_reads(module)
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
