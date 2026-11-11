"""NR-076 / NR-077 — the nursing ORM and the nursing tables are two data models.

This pins a **currently broken** state, on purpose, and it is the second kind of
test this repository keeps: not "the feature works" but "the defect is exactly
this large, and no larger". Every assertion here is expected to change when the
NR-076 decision gate is resolved, and each one says what the resolution would
make it say.

The measurement base matters. These tables are created by
``20260716_0002_nursing_platform.py``, the only migration on any reachable
branch that creates them, and the resulting schema was verified **byte-identical**
between a database built from this branch's own lineage (``alembic upgrade
20260716_0002``, 116 tables) and the harness database. So unlike the hospital
tables of NR-073, nursing carries no foreign-lineage caveat: what is measured
here is what an operator of this branch would get.

Why this was invisible until now: NR-074's split foreign-key namespace made
every nursing write raise ``NoReferencedTableError`` while sorting a mapper's
tables, before a single statement was emitted. With the namespace shared, the
write reaches PostgreSQL and the real disagreement surfaces. One defect had
completely masked the other.

What is NOT asserted anywhere in this file: that any direction of repair is
correct. Both directions cross a documented human-approval gate, and
``docs/architecture/NR-076-nursing-identity-decision.md`` costs them out.
"""

from __future__ import annotations

import pytest
from sqlalchemy import text

from tests.verification.harness import (
    dispose,
    physical_columns,
    physical_tables,
    requires_postgres,
    session_factory,
)

pytestmark = requires_postgres()

NURSING_TABLES = {
    "nursing_care_plans",
    "nursing_clinical_checklists",
    "nursing_delegations",
    "nursing_escalation_records",
    "nursing_fall_risk_assessments",
    "nursing_fluid_balance",
    "nursing_notes",
    "nursing_nutrition_assessments",
    "nursing_pain_assessments",
    "nursing_patient_assignments",
    "nursing_pressure_injury_assessments",
    "nursing_shift_handovers",
    "nursing_shifts",
    "nursing_tasks",
    "nursing_vital_signs",
}

# Measured 2026-09-26 against a database built from this branch's own lineage.
# Subset semantics, as NR-057 established: a repair that shrinks these passes and
# is reported; growth fails. An exact pin would have to be edited by whoever
# fixes the defect, which turns a guard into a chore and invites loosening.
MEASURED_ORM_ONLY_COLUMNS = 149
MEASURED_DB_ONLY_COLUMNS = 176
MEASURED_TYPE_MISMATCHES = 41

#: Which physical types an ORM declaration may legitimately land on. Only the
#: prefixes that actually occur in the nursing models are listed: a prefix that
#: is absent is skipped rather than guessed at, so an unrecognised ORM type is
#: never silently counted as either a match or a mismatch.
_ACCEPTABLE_PHYSICAL_TYPES = {
    "VARCHAR": {"character varying", "text"},
    "INTEGER": {"integer", "bigint", "smallint"},
    "DATETIME": {"timestamp with time zone", "timestamp without time zone"},
    "TEXT": {"text"},
    "BOOLEAN": {"boolean"},
    "JSON": {"json", "jsonb"},
}


@pytest.fixture(scope="module")
def Session():
    s = session_factory()
    yield s
    dispose(s)


@pytest.fixture(scope="module")
def nursing_models():
    """The assembled app, so the shared namespace is complete.

    NR-074: a foreign key resolves only once the *target's* mapper module has
    been imported. Importing ``app.nursing`` alone would reproduce NR-074's
    symptom instead of NR-076's, and the two look nothing alike once you know to
    check which error you got.
    """
    import app.main
    from app.nursing.base import NursingBase
    from app.orm_topology import own_tables

    return {t.key: t for t in own_tables(NursingBase)}


def test_every_nursing_model_maps_a_table_that_exists(Session, nursing_models):
    """NR-077, and this one is FIXED — it must stay fixed.

    ``ClinicalChecklist`` mapped ``nursing_checklists`` and ``EscalationRecord``
    mapped ``nursing_escalations``. Neither name is created by any migration on
    any reachable branch. The physical tables are
    ``nursing_clinical_checklists`` and ``nursing_escalation_records`` -- which
    is what ``20260716_0002``'s own docstring names, and what the two classes are
    named after. A model pointed at a table that exists nowhere fails with
    ``UndefinedTable``, a different and louder failure than the rest of NR-076,
    and it also made those two tables read as "absent" in every drift
    measurement, which understated the real schema and overstated the missing
    one.
    """
    physical = physical_tables(Session)
    mapped = set(nursing_models)
    assert mapped == NURSING_TABLES, (
        f"the set of mapped nursing tables changed: "
        f"unexpected={sorted(mapped - NURSING_TABLES)}, "
        f"missing={sorted(NURSING_TABLES - mapped)}"
    )
    nonexistent = sorted(mapped - physical)
    assert nonexistent == [], (
        f"these nursing models map tables that do not exist: {nonexistent}. "
        f"Every read and write through them raises UndefinedTable. NR-077 fixed "
        f"exactly this for two tables; a new entry is the same defect again."
    )


def test_a_nursing_write_still_fails_and_fails_for_the_recorded_reason(Session, nursing_models):
    """The negative proof, kept live: NR-076 is not fixed, and this says why.

    Asserting the *kind* of error, not merely that an error occurs. A test that
    accepted any exception would keep passing if the cause changed to something
    unrelated -- including to NR-074's ``NoReferencedTableError``, which would
    mean the topology repair had regressed rather than that nursing was still
    broken. The two are different problems and this distinguishes them.

    When the gate is resolved this test must be **deleted, not relaxed**: a
    working write is the acceptance criterion, and an assertion that a write
    fails has no honest weakened form.
    """
    from datetime import UTC, datetime

    import app.nursing.models as nm
    from sqlalchemy.exc import NoReferencedTableError, ProgrammingError

    s = Session()
    try:
        task = nm.NursingTask(
            lab_id=1,
            patient_id=1,
            task_type="medication",
            description="NR-076 pin",
            priority="routine",
            status="pending",
            is_deleted=False,
            version=1,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        s.add(task)
        with pytest.raises(ProgrammingError) as exc:
            s.flush()
        message = str(exc.value)
        assert "does not exist" in message, message
        assert "nursing_tasks" in message, message
        assert "encounter_id" in message, (
            "NR-076 was measured as failing on nursing_tasks.encounter_id, the "
            "first ORM-declared column the table lacks. A different column here "
            "means the schema moved; re-measure before editing this pin."
        )
    finally:
        s.rollback()
        s.close()

    # Guard the guard: the failure above must not be NR-074's, which would mean
    # the shared-MetaData repair had regressed and this file was measuring the
    # wrong defect entirely.
    assert NoReferencedTableError is not ProgrammingError


def test_every_nursing_primary_key_disagrees_about_identity(Session, nursing_models):
    """The identity half of NR-076, stated as the systematic thing it is.

    All fifteen tables, not a few: the ORM declares ``String(26)`` with a ULID
    default through ``NursingBaseEntity``, and every physical table is ``integer``
    driven by a sequence. This is not drift that accumulated -- it is two
    generations of the platform's identity model, and ``NursingBaseEntity`` is
    where the ORM side of it is decided for all fifteen at once.

    Deliberately asserting that ALL fifteen disagree rather than counting: a
    partial conversion would leave the domain in a third state, worse than either
    generation, and this fails the moment that starts.
    """
    with Session() as s:
        rows = s.execute(
            text(
                """
                SELECT c.table_name, c.data_type, c.column_default
                FROM information_schema.columns c
                WHERE c.table_name = ANY(:tables) AND c.column_name = 'id'
                """
            ),
            {"tables": sorted(NURSING_TABLES)},
        ).all()

    assert len(rows) == len(NURSING_TABLES), f"expected 15 id columns, got {len(rows)}"
    integer_pks = {r[0] for r in rows if r[1] == "integer"}
    assert integer_pks == NURSING_TABLES, (
        "the physical nursing primary keys are no longer uniformly integer: "
        f"non-integer = {sorted(NURSING_TABLES - integer_pks)}. If a migration "
        "converted them to ULID, NR-076 has been resolved in the ORM's favour "
        "and this file should be deleted along with the pin above."
    )
    sequence_backed = {r[0] for r in rows if r[2] and "nextval" in r[2]}
    assert sequence_backed == NURSING_TABLES, (
        f"these integer primary keys lost their sequence default: "
        f"{sorted(NURSING_TABLES - sequence_backed)}. An integer primary key "
        f"with no default and no ORM-side generator cannot be inserted at all."
    )

    orm_pk_types = {
        name: str(table.primary_key.columns[0].type)
        for name, table in nursing_models.items()
    }
    non_ulid = {n: t for n, t in orm_pk_types.items() if t != "VARCHAR(26)"}
    assert non_ulid == {}, (
        f"the ORM side is no longer uniformly ULID: {non_ulid}. A mixed state is "
        f"worse than either generation -- see NR-076's decision packet."
    )


def test_the_measured_contradiction_does_not_grow(Session, nursing_models):
    """The size of NR-076, held at its measured value.

    Subset semantics on purpose. A repair in either direction shrinks these and
    passes, and the report below is printed so the shrinkage is visible rather
    than silent. Growth fails, because the one thing that must not happen while
    the gate is open is more of the same disagreement being added.
    """
    orm_only_total = 0
    db_only_total = 0
    mismatch_total = 0
    per_table: list[str] = []

    for name, table in sorted(nursing_models.items()):
        physical = physical_columns(Session, name)
        assert physical, f"{name} has no physical columns; the database is not migrated"
        orm = {c.name: c for c in table.columns}
        orm_only = sorted(set(orm) - physical)
        db_only = sorted(physical - set(orm))
        orm_only_total += len(orm_only)
        db_only_total += len(db_only)
        per_table.append(f"  {name}: orm_only={len(orm_only)} db_only={len(db_only)}")

    with Session() as s:
        rows = s.execute(
            text(
                """
                SELECT table_name, column_name, data_type
                FROM information_schema.columns
                WHERE table_name = ANY(:tables)
                """
            ),
            {"tables": sorted(NURSING_TABLES)},
        ).all()
    physical_types = {(t, c): d for t, c, d in rows}
    for name, table in nursing_models.items():
        for col in table.columns:
            physical_type = physical_types.get((name, col.name))
            if physical_type is None:
                continue
            orm_type = str(col.type).upper()
            for prefix, acceptable in _ACCEPTABLE_PHYSICAL_TYPES.items():
                if orm_type.startswith(prefix):
                    if physical_type not in acceptable:
                        mismatch_total += 1
                    break

    report = "\n".join(per_table)
    assert orm_only_total <= MEASURED_ORM_ONLY_COLUMNS, (
        f"columns the ORM declares and the database lacks grew from "
        f"{MEASURED_ORM_ONLY_COLUMNS} to {orm_only_total}:\n{report}"
    )
    assert db_only_total <= MEASURED_DB_ONLY_COLUMNS, (
        f"columns the database has and the ORM ignores grew from "
        f"{MEASURED_DB_ONLY_COLUMNS} to {db_only_total}:\n{report}"
    )
    assert mismatch_total <= MEASURED_TYPE_MISMATCHES, (
        f"nursing column type mismatches grew from {MEASURED_TYPE_MISMATCHES} "
        f"to {mismatch_total}"
    )
    # Guard the guard: a measurement that silently reached zero would satisfy
    # every assertion above while proving nothing ran.
    assert orm_only_total > 0 and db_only_total > 0, (
        "this file measured no disagreement at all, which on current evidence "
        "means the measurement broke rather than that NR-076 was fixed. If it "
        "really was fixed, delete this file -- do not let it pass vacuously."
    )


def test_no_nursing_row_exists_anywhere_so_no_backfill_is_owed(Session):
    """A fact the decision depends on, asserted so it cannot quietly stop being true.

    Every one of the fifteen tables is empty. That is what makes the identity
    conversion in NR-076's Option B a schema-only change with no backfill and no
    data-loss exposure, and it is the single largest input to costing the gate.
    The day a nursing row exists, the cost of that option changes and the packet
    must be re-read before acting on it -- so this fails then, loudly, rather
    than letting a stale recommendation be executed.
    """
    with Session() as s:
        counts = {
            table: s.execute(text(f"SELECT count(*) FROM {table}")).scalar()
            for table in sorted(NURSING_TABLES)
        }
    non_empty = {t: n for t, n in counts.items() if n}
    assert non_empty == {}, (
        f"nursing tables now hold rows: {non_empty}. NR-076's decision packet "
        f"assumes all fifteen are empty, which is what makes an identity "
        f"conversion backfill-free. Re-cost the options before proceeding."
    )
