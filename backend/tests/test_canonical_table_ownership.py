"""NR-051 — one physical table, one ORM owner.

A canonical owner needs one authoritative persistence owner. When two ORM
classes map the same `__tablename__`, there are two views of one table and
nothing reconciles them: divergent columns, divergent constraints, divergent
nullability. Writes through one can violate what the other declares.

The scan behind this guard found GULA is already close to that rule -- 829 ORM
classes over 828 distinct tables. Exactly one table had two owners, NR-006's
`national_facilities`, and that one is now closed: the second mapper is gone and
the table it anchored is declared as a bare `Table`. The rule now holds with no
exceptions, which is why the ledger below is empty.

The rule itself is checked by AST scan, not by import: it costs milliseconds,
needs no database, and cannot be defeated by a module that fails to import. The
last test is the exception and is deliberately behavioural -- what NR-006 got
wrong was a column list, and only building the table proves that right.
"""

from __future__ import annotations

import ast
from collections import defaultdict
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
APP = BACKEND / "app"

# Tables with more than one ORM owner. This ledger may shrink. It may never grow.
#
# It is empty, and that is a measured state rather than an aspiration: NR-006 was
# its only entry and was closed by this commit. `national.domain.facility.Facility`
# mapped `national_facilities` with 28 columns, 24 of which migration
# 20260813_0004_clinical_ehr_scope_bridge.py never creates -- including
# `facility_type` NOT NULL -- while omitting two that do exist. It had no consumer,
# and any query through it raised UndefinedColumn. It is now a bare `Table` holding
# the foreign-key anchor that fourteen tables in `NationalBase.metadata` need, so
# `models.clinical_scope.NationalFacility` is the sole ORM owner.
DECLARED_DUPLICATE_TABLE_OWNERS: dict[str, set[str]] = {}


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
    """The canonical persistence rule, held with no exceptions.

    The ledger is empty, so this is now an absolute assertion: any table mapped
    twice fails here rather than being discovered years later by a column that
    does not exist.
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

    Vacuous while the ledger is empty, which is the point -- it is what makes an
    entry added later expire on its own instead of becoming a permanent
    exemption. Fails both ways: if a listed duplicate is fixed and the entry
    stays, and if an entry's recorded owners stop matching what is declared.
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


def test_national_facilities_has_exactly_one_orm_owner() -> None:
    """NR-006, named rather than left to the general rule.

    The general assertion above would catch a second mapper appearing anywhere.
    This one says which table and which owner, so a regression reports the
    finding it reopens instead of a bare pair of class names.
    """
    owners = _orm_owners().get("national_facilities", set())
    assert owners == {"models.clinical_scope.NationalFacility"}, (
        "national_facilities must be mapped by NationalFacility alone -- "
        f"found {sorted(owners)}"
    )


def test_the_national_facilities_anchor_is_gone_and_its_dependents_still_resolve() -> None:
    """The invariant that replaced the anchor, and the one it was standing in for.

    NR-006 gave `NationalBase.metadata` a bare `Table` copy of
    `national_facilities`, because fourteen-plus tables in it hold a foreign key
    to that id and SQLAlchemy resolves a foreign key inside the MetaData owning
    the *referring* table. A bare copy could drift from the canonical model
    silently, so this test used to compare them column for column.

    NR-086 removed the reason for the copy: `NationalBase` and `Base` share one
    MetaData, so those foreign keys resolve against `NationalFacility` itself.
    There is nothing left to drift *from*, and the assertion worth making is the
    stronger one — one definition, and every dependent still finding it.
    """
    import app.national.domain  # imported for its side effect: registers the models
    import sqlalchemy as sa
    from app.models.clinical_scope import NationalFacility
    from app.national.base import NationalBase

    registered = NationalBase.metadata.tables["national_facilities"]
    assert registered is NationalFacility.__table__, (
        "national_facilities has two Table objects again; the NR-006 anchor or "
        "another copy has come back, and the copy can drift from the model"
    )
    assert app.national.domain.national_facilities is NationalFacility.__table__, (
        "app.national.domain re-exports a different table than the canonical model"
    )

    dependents = {
        fk.parent.table.name
        for table in NationalBase.metadata.tables.values()
        for fk in table.foreign_keys
        if fk.column.table.name == "national_facilities"
    }
    assert len(dependents) >= 14, (
        "these foreign keys are why the anchor existed; finding almost none "
        f"means the package stopped registering, not that they resolved: {sorted(dependents)}"
    )

    canonical = [c.name for c in NationalFacility.__table__.columns]
    engine = sa.create_engine("sqlite://")
    try:
        NationalBase.metadata.create_all(engine, tables=[registered], checkfirst=True)
        with engine.connect() as conn:
            built = [r[1] for r in conn.exec_driver_sql("PRAGMA table_info(national_facilities)")]
    finally:
        engine.dispose()
    assert built == canonical, (
        f"create_all built a table the migration does not produce: {built}"
    )
