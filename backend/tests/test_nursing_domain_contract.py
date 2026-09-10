"""NR-026 — the Nursing ORM against the schema Alembic actually builds.

BATCH-2.7 recorded this as two nursing features failing because two models named
tables no migration creates. BATCH-2.8 executed the queries instead of reasoning
about them, and the result is worse: **every** nursing model fails on a plain
SELECT.

    ClinicalChecklist  UndefinedTable   relation "nursing_checklists" does not exist
    EscalationRecord   UndefinedTable   relation "nursing_escalations" does not exist
    NursingNote        UndefinedColumn  column nursing_notes.encounter_id does not exist
    NursingShift       UndefinedColumn  column nursing_shifts.department_id does not exist

All fifteen models key on ``String(26)`` while every physical table keys on
``INTEGER``; across the domain there are 97 type mismatches and 137 ORM columns
with no physical column. This is the Pharmacy P0-2 defect at Pharmacy's scale,
in a domain that was never reconciled.

These tests assert the defect, with its exact measured shape. They are the scope
statement for the reconciliation: when it lands they fail, and that is the signal
to delete them — not to widen the numbers.

The physical tables are provably empty, so the reconciliation carries no data
risk: no application code, raw SQL, or seeder anywhere names
``nursing_clinical_checklists`` or ``nursing_escalation_records``, and the ORM
that would have written the other thirteen cannot execute a statement against
them.
"""
from __future__ import annotations

import os

import pytest

SCHEMA_DATABASE_URL = os.environ.get("GULA_SCHEMA_DATABASE_URL", "")

pytestmark = pytest.mark.skipif(
    not SCHEMA_DATABASE_URL,
    reason="GULA_SCHEMA_DATABASE_URL is not configured; this contract needs a database migrated to head",
)

# Measured at head 20260912_0001. Every entry is a defect, not a tolerance.
MODELS_WITH_NO_TABLE = {
    "ClinicalChecklist": "nursing_checklists",
    "EscalationRecord": "nursing_escalations",
}
NURSING_MODEL_COUNT = 15
TOTAL_TYPE_MISMATCHES = 97
TOTAL_PHANTOM_COLUMNS = 137


def _normalise(sql_type: object) -> str:
    text = str(sql_type).upper()
    for old, new in (
        ("CHARACTER VARYING", "STRING"), ("VARCHAR", "STRING"),
        ("TIMESTAMP WITH TIME ZONE", "DATETIME"), ("(TIMEZONE=TRUE)", ""),
        ("DOUBLE PRECISION", "FLOAT"),
    ):
        text = text.replace(old, new)
    return text.replace(" ", "")


def _nursing_models() -> list:
    import app.nursing.models as models

    return [
        obj for name in dir(models)
        if (obj := getattr(models, name)) is not None
        and hasattr(obj, "__tablename__") and hasattr(obj, "__table__")
        and getattr(obj, "__module__", "") == "app.nursing.models"
    ]


@pytest.fixture(scope="module")
def inspector():
    from sqlalchemy import create_engine, inspect

    engine = create_engine(SCHEMA_DATABASE_URL)
    try:
        yield inspect(engine)
    finally:
        engine.dispose()


def test_the_nursing_models_that_name_no_table_are_exactly_the_two_known(inspector) -> None:
    tables = set(inspector.get_table_names())
    if not tables:
        pytest.skip("database has no tables; not migrated to head")

    missing = {
        m.__name__: m.__tablename__ for m in _nursing_models()
        if m.__tablename__ not in tables
    }
    assert missing == MODELS_WITH_NO_TABLE, (
        f"the set of nursing models naming a non-existent table changed: {missing}. "
        "If the reconciliation landed, delete this contract rather than editing it."
    )


def test_every_nursing_model_still_keys_on_a_string_against_an_integer_column(inspector) -> None:
    """The reason a piecemeal fix is impossible: the primary key is wrong on all of them."""
    tables = set(inspector.get_table_names())
    if not tables:
        pytest.skip("database has no tables; not migrated to head")

    models = _nursing_models()
    assert len(models) == NURSING_MODEL_COUNT, (
        f"{len(models)} nursing models found, expected {NURSING_MODEL_COUNT}"
    )

    divergent = []
    for model in models:
        if model.__tablename__ not in tables:
            continue
        physical = {c["name"]: c for c in inspector.get_columns(model.__tablename__)}
        orm = {c.name: c for c in model.__table__.columns}
        if ("id" in orm and "id" in physical
                and _normalise(orm["id"].type) != _normalise(physical["id"]["type"])):
            divergent.append(model.__name__)

    assert len(divergent) == NURSING_MODEL_COUNT - len(MODELS_WITH_NO_TABLE), (
        "the number of nursing models whose primary key type diverges from the "
        f"physical column changed: {sorted(divergent)}. Every one must move "
        "together — the tables reference each other."
    )


def test_the_measured_drift_has_not_grown(inspector) -> None:
    """Pins the reconciliation's size so it cannot quietly get bigger."""
    tables = set(inspector.get_table_names())
    if not tables:
        pytest.skip("database has no tables; not migrated to head")

    mismatches = phantom = 0
    for model in _nursing_models():
        if model.__tablename__ not in tables:
            continue
        physical = {c["name"]: c for c in inspector.get_columns(model.__tablename__)}
        orm = {c.name: c for c in model.__table__.columns}
        mismatches += sum(
            1 for name in set(orm) & set(physical)
            if _normalise(orm[name].type) != _normalise(physical[name]["type"])
        )
        phantom += len(set(orm) - set(physical))

    assert (mismatches, phantom) == (TOTAL_TYPE_MISMATCHES, TOTAL_PHANTOM_COLUMNS), (
        f"nursing drift changed: {mismatches} type mismatches and {phantom} phantom "
        f"columns, was {TOTAL_TYPE_MISMATCHES} and {TOTAL_PHANTOM_COLUMNS}. If it "
        "shrank, update the reconciliation record; if it grew, a new model was "
        "written against a schema that does not exist."
    )
