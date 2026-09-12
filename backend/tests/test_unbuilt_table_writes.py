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
**147** ORM constructions target a table no migration builds.

The ledger may shrink. It may never grow, and no new package may appear.

`_write_audit` is left in place. Removing it would reduce declared audit
coverage, which CLAUDE.md reserves for a human decision, and repairing it
properly means threading an authenticated actor into a layer that has none.
Both are real work; neither is a side effect of a measurement commit.
"""

from __future__ import annotations

import ast
import collections
import json
import pathlib

BACKEND = pathlib.Path(__file__).resolve().parents[1]
APP = BACKEND / "app"
EVIDENCE = BACKEND.parent / "docs" / "architecture" / "evidence-created-tables.json"

#: Packages constructing ORM models whose tables no migration builds, and how
#: many such constructions each holds.
DECLARED_UNBUILT_WRITES = {
    "app/services": 77,
    "app/national": 43,
    "app/insurance": 20,
    "app/nhdw": 3,
    "app/governance": 2,
    "app/radiology": 1,
    "app/nursing": 1,
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


def _parse(path: pathlib.Path) -> ast.Module | None:
    try:
        return ast.parse(path.read_text(encoding="utf-8", errors="ignore"))
    except (SyntaxError, FileNotFoundError):
        return None


def _qualified_models() -> dict[tuple[str, str], str]:
    """(module path, class name) -> table name. Qualified, never bare."""
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


def _names_in(path: pathlib.Path, qualified: dict[tuple[str, str], str]) -> dict[str, str]:
    names: dict[str, str] = {}
    tree = _parse(path)
    if tree is None:
        return names
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module and node.module.startswith("app."):
            module = str(pathlib.Path(node.module.replace(".", "/") + ".py"))
            for alias in node.names:
                table = qualified.get((module, alias.name))
                if table:
                    names[alias.asname or alias.name] = table
    rel = str(path.relative_to(BACKEND))
    for (module, cls), table in qualified.items():
        if module == rel:
            names[cls] = table
    return names


def _unbuilt_writes() -> list[tuple[str, str, str, int]]:
    """(module, class, table, line) for each construction of an unbuilt model."""
    qualified = _qualified_models()
    built = set(json.loads(EVIDENCE.read_text(encoding="utf-8")))
    found: list[tuple[str, str, str, int]] = []
    for path in APP.rglob("*.py"):
        if "__pycache__" in path.parts:
            continue
        names = _names_in(path, qualified)
        tree = _parse(path)
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
        tree = _parse(path)
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
