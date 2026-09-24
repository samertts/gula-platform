"""NR-026 — the Nursing domain contract, after reconciliation.

Before BATCH-3 every Nursing model failed on a plain SELECT: all fifteen keyed
on ``String(26)`` against ``INTEGER`` columns, two named tables no migration
creates, 97 type mismatches and 137 mapped columns that did not exist.

The models are now generated from the schema ``20260716_0002`` builds. These
tests derive their expectations from PostgreSQL rather than restating a
snapshot, so they keep working as the schema evolves and fail the moment the ORM
drifts from it again.

Two comparisons are deliberately normalised, because they are spellings of the
same PostgreSQL type rather than differences:

* ``DateTime(timezone=True)`` renders ``TIMESTAMP``;
* ``Float`` renders ``FLOAT``, and PostgreSQL's ``FLOAT`` with no precision *is*
  ``double precision`` — ``pg_typeof(1::float) = pg_typeof(1::double precision)``.
"""
from __future__ import annotations

import os

import pytest


def _schema_database_url() -> str:
    """The database this module inspects, migrated to head.

    DATABASE_URL cannot supply it: conftest pins that variable to in-memory
    SQLite for the whole suite. GULA_SCHEMA_DATABASE_URL is this guard's own
    variable; MIGRATION_DATABASE_URL is the one CI already exports for the
    migrated PostgreSQL service, so the guard runs there without the workflow
    having to name a second variable for the same database.
    """
    return (os.environ.get("GULA_SCHEMA_DATABASE_URL")
            or os.environ.get("MIGRATION_DATABASE_URL", ""))


SCHEMA_DATABASE_URL = _schema_database_url()

pytestmark = pytest.mark.skipif(
    not SCHEMA_DATABASE_URL,
    reason="GULA_SCHEMA_DATABASE_URL is not configured; this contract needs a database migrated to head",
)

NURSING_MODEL_COUNT = 15

# The only foreign-key target inside NursingBase's MetaData. Everything else
# lives on another declarative base, where a ForeignKey cannot resolve and
# breaks the mapper's table sort on INSERT (NR-023) — so those are plain
# columns and PostgreSQL enforces the constraint.
INTRA_DOMAIN_FK_TARGET = "nursing_shifts"
CROSS_BASE_FK_TARGETS = {"labs", "lab_users", "patients", "nhdw_admissions"}


def _compiled(sql_type: object) -> str:
    from sqlalchemy.dialects import postgresql

    try:
        text = sql_type.compile(dialect=postgresql.dialect()).upper()
    except Exception:
        text = str(sql_type).upper()
    return text.replace(" WITHOUT TIME ZONE", "").replace("DOUBLE PRECISION", "FLOAT")


def _models() -> list:
    import app.nursing.models as models

    return [
        obj for name in dir(models)
        if hasattr(obj := getattr(models, name), "__tablename__")
        and hasattr(obj, "__table__")
        and getattr(obj, "__module__", "") == "app.nursing.models"
    ]


@pytest.fixture(scope="module")
def engine():
    from sqlalchemy import create_engine

    eng = create_engine(SCHEMA_DATABASE_URL)
    try:
        yield eng
    finally:
        eng.dispose()


@pytest.fixture(scope="module")
def inspector(engine):
    from sqlalchemy import inspect

    insp = inspect(engine)
    if not insp.get_table_names():
        pytest.skip("database has no tables; not migrated to head")
    return insp


def test_all_fifteen_models_import_and_name_a_real_table(inspector) -> None:
    models = _models()
    assert len(models) == NURSING_MODEL_COUNT, f"expected {NURSING_MODEL_COUNT} models"
    tables = set(inspector.get_table_names())
    missing = {m.__name__: m.__tablename__ for m in models if m.__tablename__ not in tables}
    assert not missing, f"models naming a table no migration creates: {missing}"


def test_every_model_executes_a_plain_select(engine) -> None:
    """The defect in one assertion: before the reconciliation, none of these ran."""
    from sqlalchemy.orm import sessionmaker

    failures = {}
    with sessionmaker(bind=engine)() as session:
        for model in _models():
            try:
                session.query(model).count()
            except Exception as exc:
                failures[model.__name__] = f"{type(exc).__name__}: {str(exc).splitlines()[0]}"
    assert not failures, f"models that cannot be read: {failures}"


def test_no_orm_column_is_absent_from_its_table(inspector) -> None:
    phantom = {}
    for model in _models():
        physical = {c["name"] for c in inspector.get_columns(model.__tablename__)}
        extra = {c.name for c in model.__table__.columns} - physical
        if extra:
            phantom[model.__tablename__] = sorted(extra)
    assert not phantom, f"ORM columns with no physical column: {phantom}"


def test_every_column_type_matches_the_physical_column(inspector) -> None:
    mismatches = []
    for model in _models():
        physical = {c["name"]: c for c in inspector.get_columns(model.__tablename__)}
        for column in model.__table__.columns:
            if column.name not in physical:
                continue
            orm, phys = _compiled(column.type), _compiled(physical[column.name]["type"])
            if orm != phys:
                mismatches.append(f"{model.__tablename__}.{column.name}: ORM {orm} vs {phys}")
    assert not mismatches, "ORM/physical type drift:\n  " + "\n  ".join(mismatches)


def test_every_primary_key_is_the_integer_the_schema_declares(inspector) -> None:
    """The reason the reconciliation had to move all fifteen together."""
    wrong = []
    for model in _models():
        physical = {c["name"]: c for c in inspector.get_columns(model.__tablename__)}
        pk = model.__table__.primary_key.columns
        assert len(pk) == 1, f"{model.__tablename__} has a composite primary key"
        column = next(iter(pk))
        if _compiled(column.type) != _compiled(physical[column.name]["type"]):
            wrong.append(model.__tablename__)
    assert not wrong, f"primary key type diverges from the physical column: {wrong}"


def test_foreign_keys_match_the_physical_constraints(inspector) -> None:
    mismatches = []
    for model in _models():
        physical = {
            f["constrained_columns"][0]: f["referred_table"]
            for f in inspector.get_foreign_keys(model.__tablename__)
        }
        for column in model.__table__.columns:
            if not column.foreign_keys:
                continue
            target = next(iter(column.foreign_keys)).target_fullname.rsplit(".", 1)[0]
            if physical.get(column.name) != target:
                mismatches.append(
                    f"{model.__tablename__}.{column.name}: ORM -> {target}, "
                    f"physical -> {physical.get(column.name)}"
                )
    assert not mismatches, "foreign key drift:\n  " + "\n  ".join(mismatches)


def test_cross_base_references_are_plain_columns(inspector) -> None:
    """NR-023 in miniature.

    A ForeignKey to a table on another declarative base cannot resolve, and the
    mapper needs to sort tables on every INSERT — so the domain would read but
    never write. Pharmacy solved it the same way. PostgreSQL still enforces the
    physical constraint; this asserts we did not reintroduce the ORM one.
    """
    offenders = []
    for model in _models():
        for column in model.__table__.columns:
            for fk in column.foreign_keys:
                target = fk.target_fullname.rsplit(".", 1)[0]
                if target in CROSS_BASE_FK_TARGETS:
                    offenders.append(f"{model.__tablename__}.{column.name} -> {target}")
                elif target != INTRA_DOMAIN_FK_TARGET:
                    offenders.append(f"{model.__tablename__}.{column.name} -> {target} (unexpected)")
    assert not offenders, (
        "cross-base ForeignKey objects break INSERT on this domain:\n  " + "\n  ".join(offenders)
    )


def test_the_physical_constraints_are_still_enforced_by_postgres(inspector) -> None:
    """Dropping the ORM ForeignKey must not have dropped referential integrity."""
    targets = set()
    for model in _models():
        for fk in inspector.get_foreign_keys(model.__tablename__):
            targets.add(fk["referred_table"])
    assert targets >= CROSS_BASE_FK_TARGETS, (
        f"the database no longer constrains {CROSS_BASE_FK_TARGETS - targets}"
    )


def test_autogenerate_would_not_drop_a_nursing_table_or_column(engine) -> None:
    """The destructive-diff guard for this domain (BATCH-3 §14).

    Before the reconciliation an autogenerate against NursingBase proposed
    dropping and recreating tables wholesale: two models named tables that do
    not exist, thirteen primary keys were the wrong type, and 137 mapped
    columns had no physical column. This asserts the diff now contains no
    destructive operation at all, and that the only remaining differences are
    the cross-base foreign keys PostgreSQL enforces and the ORM deliberately
    does not declare (NR-023).

    A failure here means either the ORM drifted from the schema again, or a
    real schema change arrived without a migration. Neither may be silenced by
    deleting a table to make the diff disappear.
    """
    from alembic.autogenerate import compare_metadata
    from alembic.migration import MigrationContext

    from app.nursing.base import NursingBase

    nursing_tables = set(NursingBase.metadata.tables)
    with engine.connect() as conn:
        ctx = MigrationContext.configure(
            conn,
            opts={
                "compare_type": True,
                "include_object": lambda obj, name, type_, reflected, compare_to: (
                    name in nursing_tables if type_ == "table" else True
                ),
            },
        )
        diffs = compare_metadata(ctx, NursingBase.metadata)

    def op(diff):
        return diff[0] if isinstance(diff, tuple) else diff[0][0]

    destructive = [d for d in diffs if op(d) in (
        "remove_table", "remove_column", "add_table", "add_column", "modify_type",
        "modify_nullable", "modify_default")]
    assert not destructive, (
        "autogenerate would change the shape of a Nursing table:\n  "
        + "\n  ".join(str(d)[:200] for d in destructive)
    )

    # What remains must be only the cross-base foreign keys, plus index names
    # the shared TenantMixin generates for lab_id that differ from the
    # abbreviated names the migrations created.
    for diff in diffs:
        if op(diff) == "remove_fk":
            target = next(iter(diff[1].elements)).target_fullname.rsplit(".", 1)[0]
            assert target in CROSS_BASE_FK_TARGETS, (
                f"autogenerate would drop a foreign key that is not cross-base: {target}"
            )
        else:
            assert op(diff) == "add_index", f"unexpected diff operation: {diff}"
