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
creates. Of those, **610 are reachable** from a registered router across 24 route
modules -- either in the route module itself or one import hop away, which is
exactly NR-064's shape (the route was clean; its service was not).

Every figure here is a correction, and the ledger below has now **grown twice**
for the same reason: not because the repository got worse, but because the
instrument could not see it.

* 483 / 267 across 11 modules, first pass. The resolver handled only absolute
  `app.*` imports, so a model reached through `from ..models import X` or a
  package re-export was invisible. Fixed in NR-067; resolution moved to
  `tests/orm_resolution.py`.
* 773 / 418 across 20 modules, second pass.
* **773 / 610 across 24 modules, this pass (NR-079).** Two more blind spots, both
  in the direction of undercounting, and both now removed:
  - **registration was read by regex over `factory.py`.** The factory also has a
    bulk block -- `from .routes import (admin, ehr, ehr_fhir, …)` then
    `for r in core_routes + feature_routes + …: app.include_router(r.router)` --
    that no regex matched. The regex found **79** route modules; the running
    application serves **142**. Zero false positives, 63 false negatives.
  - **`from app.services import ehr_service` was dropped.** A package import
    naming a submodule resolves to `app/services/ehr_service.py`, not to
    `app/services.py`, and the resolver only tried the latter.

  Four route modules were therefore invisible entirely: `app/routes/ehr_fhir.py`
  (77), `app/routes/ehr.py` (63), `app/governance/routes/governance_routes.py`
  (47) and `app/governance/routes/analytics_routes.py` (5). 418 + 192 = 610, and
  **not one already-declared count changed** -- the correction is purely
  additive, which is what distinguishes a repaired instrument from a regression.

Registration is now read from the **running application**, never from the file
that configures it. `route.endpoint.__module__` is what FastAPI will serve, and
it stays correct however `factory.py` is rewritten.

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

import pytest

from tests.orm_resolution import (
    BACKEND,
    ambiguous_class_names,
    built_tables,
    imported_modules,
    parse,
    route_modules,
    tables_by_local_name,
)

#: Registered route modules that reach a read of an unbuilt table, and how many
#: such reads are reachable from each (the module itself plus one import hop).
#: Every one is the NR-064 failure waiting to be triggered.
DECLARED_REACHABLE_UNBUILT_READS = {
    "app/citizen_platform/routes.py": 1,
    "app/command_intelligence/routes.py": 10,
    "app/governance/routes/analytics_routes.py": 5,
    "app/governance/routes/governance_routes.py": 47,
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
    "app/routes/ehr.py": 63,
    "app/routes/ehr_fhir.py": 77,
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


@pytest.fixture()
def registered(client):
    """Route modules the **running** application serves.

    This used to parse `factory.py` with two regexes and missed the bulk
    registration block entirely -- 79 modules found against 142 served, with no
    false positives, so every reachability number derived from it was a strict
    undercount (NR-079). Depending on `client` is what runs the lifespan; this
    platform registers its routers there, so an unstarted app has seven routes.
    """
    from app.main import app

    return route_modules(app)


def _measure(registered: frozenset[str]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for route in registered:
        total = len(_unbuilt_reads(route))
        for dep in imported_modules(BACKEND / route):
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


def test_the_scan_still_finds_registered_routers(registered) -> None:
    """A scan that finds no routers would declare the whole surface unreachable.

    The floor is set against the **served** count (142 at the time of writing),
    not against the 79 the old regex found. A floor of 60 was satisfied by an
    instrument missing 63 modules, which is how NR-079 stayed invisible: a
    guard-the-guard is only worth its distance from the truth.
    """
    assert len(registered) >= 130, (
        f"only {len(registered)} route modules found in the running application; "
        "every reachability claim below would be understated"
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


def test_no_new_route_module_reads_an_unbuilt_table(registered) -> None:
    """A new one is a new endpoint that 500s the first time it is called."""
    appeared = sorted(set(_measure(registered)) - set(DECLARED_REACHABLE_UNBUILT_READS))
    assert appeared == [], (
        "these registered route modules now reach a read of a table no migration "
        "creates. Build the table under an activation review, or stop reading it: "
        f"{appeared}"
    )


def test_the_reachable_unbuilt_read_ledger_does_not_grow(registered) -> None:
    """The ratchet, reported per module so a failure names what to look at."""
    current = _measure(registered)
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
