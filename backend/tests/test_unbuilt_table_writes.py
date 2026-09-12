"""NR-066 / NR-067 — the write side of the same question the read guard asks.

`test_reachable_unbuilt_reads.py` holds reads. This holds writes: constructing
an ORM model whose table no migration creates. The two fail differently and the
difference matters. A read raises UndefinedTable and returns nothing. A write
raises it **on flush**, which takes the whole transaction with it -- including
the rows the caller actually meant to write.

NR-066 is the instance that taught this. `GovernanceRepository` -- the shared
base under six governance repositories -- calls `_write_audit` from `add`,
`update` and `delete`, and that method constructs
`HealthNumberAudit(health_number=resource_id, event=action,
changed_by="system")` into `gov_health_number_audit`. That table is not built.
Six of the tables the repositories serve **are** built
(`gov_break_glass_accesses`, `gov_guardians`, `gov_identity_records`,
`gov_merge_proposals`, `gov_qr_codes`, `gov_recovery_requests`), so the audit
insert would fail the flush and roll back the governance mutation with it.

It has never happened, because nothing calls those repositories: their two
persistence services are imported by no module outside `app/governance/services`,
and the registered `governance_router` imports nine other service modules
instead. That is the correction this file records -- the finding first said the
rows existed and "read as coverage". They cannot exist. Nothing writes them.

Measured across `app/` with names resolved through each file's own imports:
**268** ORM constructions target a table no migration builds.

That is a correction. This file first said 147, because its own resolver handled
only absolute `app.*` imports and could not follow `from ..models import X` or a
package re-export such as `from app.ehr.models import CarePlan`. `app/governance`
alone went from 2 to 62 on re-measurement. Resolution now lives in
`tests/orm_resolution.py`, once, and that module records the four separate guard
defects the shortcut caused.

The ledger may shrink. It may never grow, and no new package may appear.

`_write_audit` is left in place. Removing it would reduce declared audit
coverage, which CLAUDE.md reserves for a human decision, and repairing it
properly means threading an authenticated actor into a layer that has none.
Both are real work; neither is a side effect of a measurement commit.
"""

from __future__ import annotations

import ast
import collections
import pathlib

from tests.orm_resolution import (
    APP,
    BACKEND,
    app_modules,
    built_tables,
    parse,
    tables_by_local_name,
)

#: Packages constructing ORM models whose tables no migration builds, and how
#: many such constructions each holds.
DECLARED_UNBUILT_WRITES = {
    "app/command_intelligence": 2,
    "app/document_intelligence": 6,
    "app/financial": 4,
    "app/governance": 62,
    "app/insurance": 20,
    "app/knowledge_graph": 3,
    "app/national": 43,
    "app/nhdw": 3,
    "app/nursing": 1,
    "app/radiology": 1,
    "app/research_platform": 4,
    "app/roadmap": 8,
    "app/services": 106,
    "app/simulation": 5,
}

#: NR-066. The shared governance repository base writes an audit row into an
#: unbuilt table from every create, update and delete. It is unreachable today;
#: if a caller appears, six built governance tables stop accepting mutations.
GOVERNANCE_AUDIT_WRITE = ("app/governance/repositories/base.py", "gov_health_number_audit")

#: Modules that may not import the governance persistence services without the
#: NR-066 write being repaired first: importing them is what makes it reachable.
GOVERNANCE_PERSISTENCE_MODULES = (
    "app/governance/services/citizen_platform_persistence.py",
    "app/governance/services/identity_persistence_service.py",
)


def _unbuilt_writes() -> list[tuple[str, str, str, int]]:
    """(module, class, table, line) for each construction of an unbuilt model."""
    built = built_tables()
    found: list[tuple[str, str, str, int]] = []
    for path in app_modules():
        names = tables_by_local_name(path)
        tree = parse(path)
        if tree is None:
            continue
        module = str(path.relative_to(BACKEND))
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                table = names.get(node.func.id)
                if table and table not in built:
                    found.append((module, node.func.id, table, node.lineno))
    return found


def test_the_write_scan_still_finds_the_surface() -> None:
    """Guard the guard: finding nothing would ratchet nothing."""
    writes = _unbuilt_writes()
    assert len(writes) >= 100, (
        f"only {len(writes)} constructions of unbuilt models found; the scan has "
        "drifted and every count below would be understated"
    )


def test_no_new_package_writes_to_an_unbuilt_table() -> None:
    """A new one is a transaction that will roll back the first time it runs."""
    counts = collections.Counter(module.split("/")[0] + "/" + module.split("/")[1]
                                 for module, _, _, _ in _unbuilt_writes())
    appeared = sorted(set(counts) - set(DECLARED_UNBUILT_WRITES))
    assert appeared == [], (
        "these packages now construct an ORM model whose table no migration "
        "creates. On flush that raises UndefinedTable and takes the caller's own "
        f"rows down with it: {appeared}"
    )


def test_the_unbuilt_write_ledger_does_not_grow() -> None:
    """The ratchet, per package, plus a rot check on resolved entries."""
    counts = collections.Counter(module.split("/")[0] + "/" + module.split("/")[1]
                                 for module, _, _, _ in _unbuilt_writes())
    widened = {
        package: (declared, counts.get(package, 0))
        for package, declared in DECLARED_UNBUILT_WRITES.items()
        if counts.get(package, 0) > declared
    }
    assert widened == {}, (
        f"writes to unbuilt tables were added (declared -> now): {widened}"
    )
    resolved = sorted(p for p in DECLARED_UNBUILT_WRITES if p not in counts)
    assert resolved == [], (
        "these packages no longer write to an unbuilt table; remove them from the "
        f"ledger so the ratchet keeps its grip: {resolved}"
    )


def test_the_governance_audit_write_is_still_unreachable() -> None:
    """NR-066, as a precondition rather than a description.

    `GovernanceRepository._write_audit` inserts into an unbuilt table from every
    create, update and delete. Six of the tables its subclasses serve *are*
    built, so the first reachable caller turns a mis-attributed audit row into a
    failed flush that rolls back the governance mutation itself.

    Nothing imports the two persistence services today. If something does, this
    fails -- and the fix is to repair the audit write first, not to delete this
    test. Repairing it means giving the write a real actor and the canonical
    hash-chained log, which is a deliberate change to audit behaviour rather
    than something to slip into an unrelated commit.
    """
    module, table = GOVERNANCE_AUDIT_WRITE
    still_unbuilt = any(
        m == module and t == table for m, _, t, _ in _unbuilt_writes()
    )
    if not still_unbuilt:
        return  # repaired or rebased; nothing left to hold

    importers = []
    for path in APP.rglob("*.py"):
        if "__pycache__" in path.parts:
            continue
        rel = str(path.relative_to(BACKEND))
        if rel.startswith(
            ("app/governance/services/", "app/governance/repositories/")
        ):
            continue
        tree = parse(path)
        if tree is None:
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module:
                target = str(pathlib.Path(node.module.replace(".", "/") + ".py"))
                if target in GOVERNANCE_PERSISTENCE_MODULES:
                    importers.append(rel)
    assert importers == [], (
        "the governance persistence services are now imported from outside their "
        "package, which makes `GovernanceRepository._write_audit` reachable. It "
        f"inserts into {table}, which no migration builds, so every governance "
        f"create, update and delete would roll back: {sorted(set(importers))}"
    )
