"""NR-051 — one physical table, one ORM owner.

A canonical owner needs one authoritative persistence owner. When two ORM
classes map the same `__tablename__`, there are two views of one table and
nothing reconciles them: divergent columns, divergent constraints, divergent
nullability. Writes through one can violate what the other declares.

The scan behind this guard found GULA is already close to that rule -- 829 ORM
classes over 828 distinct tables. Exactly one table has two owners, and that
one is NR-006, open since BATCH-2.

This is an AST scan, not an import: it costs milliseconds, needs no database,
and cannot be defeated by a module that fails to import.
"""

from __future__ import annotations

import ast
from collections import defaultdict
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
APP = BACKEND / "app"

# Tables with more than one ORM owner, as of NR-051. This ledger may shrink.
# It may never grow.
#
# national_facilities: `models.clinical_scope.NationalFacility` (id,
# facility_code, name, status, created_at, updated_at) and
# `national.domain.facility.Facility` (facility_type, name_ar, code,
# organization_id, directorate_id, parent_facility_id, phone, email).
# Migration 20260813_0004_clinical_ehr_scope_bridge.py creates the table with
# the first shape, so the second maps eight columns that do not physically
# exist. Both are currently dormant, which is the only reason this is latent
# rather than live. Resolving it is a canonical-ownership decision (NR-006),
# not a mechanical repair, so it is recorded here rather than changed.
DECLARED_DUPLICATE_TABLE_OWNERS = {
    "national_facilities": {
        "models.clinical_scope.NationalFacility",
        "national.domain.facility.Facility",
    },
}


def _orm_owners() -> dict[str, set[str]]:
    """Every `__tablename__` in app/, mapped to the classes declaring it."""
    owners: dict[str, set[str]] = defaultdict(set)
    for path in APP.rglob("*.py"):
        if "__pycache__" in path.parts:
            continue
        try:
            tree = ast.parse(path.read_text(encoding="utf-8", errors="ignore"))
        except SyntaxError:
            continue
        module = str(path.relative_to(APP)).replace("/", ".")[:-3]
        for node in ast.walk(tree):
            if not isinstance(node, ast.ClassDef):
                continue
            for stmt in node.body:
                if not isinstance(stmt, ast.Assign):
                    continue
                for target in stmt.targets:
                    if (
                        isinstance(target, ast.Name)
                        and target.id == "__tablename__"
                        and isinstance(stmt.value, ast.Constant)
                        and isinstance(stmt.value.value, str)
                    ):
                        owners[stmt.value.value].add(f"{module}.{node.name}")
    return owners


def test_the_orm_scan_finds_the_model_layer() -> None:
    """Guard the guard: a scan that finds nothing would pass vacuously."""
    owners = _orm_owners()
    assert len(owners) >= 800, f"only {len(owners)} tables found; the scan has drifted"


def test_no_table_has_two_orm_owners() -> None:
    """The canonical persistence rule, held.

    A new duplicate is in neither the repository's clean state nor the NR-006
    ledger, so it fails here rather than being discovered years later by a
    column that does not exist.
    """
    offenders = {
        table: sorted(classes)
        for table, classes in _orm_owners().items()
        if len(classes) > 1 and table not in DECLARED_DUPLICATE_TABLE_OWNERS
    }
    assert offenders == {}, (
        "these physical tables are mapped by more than one ORM class, so no "
        f"single model owns them: {offenders}"
    )


def test_the_duplicate_ledger_is_accurate() -> None:
    """A ledger entry that has been resolved should be deleted, not left to rot.

    Fails both ways: if NR-006 is fixed and the entry stays, and if the entry's
    recorded owners stop matching what the code actually declares.
    """
    owners = _orm_owners()
    for table, declared in DECLARED_DUPLICATE_TABLE_OWNERS.items():
        actual = owners.get(table, set())
        assert len(actual) > 1, (
            f"{table} no longer has duplicate owners; remove it from the ledger"
        )
        assert actual == declared, (
            f"{table}'s owners changed: expected {sorted(declared)}, found {sorted(actual)}"
        )
