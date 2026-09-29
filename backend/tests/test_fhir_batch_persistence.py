"""NR-084 — ``POST /fhir`` must not report success for a write it discards.

The endpoint committed only for ``type: "transaction"``. ``body.get("type",
"batch")`` defaults to ``batch``, and a batch entry's mutation was applied with
``db.add`` and never committed: ``get_db`` does not commit on success and closing
the session rolls the write back. The response still reported ``201``, so the
endpoint answered "created" for clinical data it threw away -- the same false
success NR-064 hid from NR-065.

A second defect sat in the same function: a ``transaction`` bundle committed
whether or not an entry had failed, so it was not all-or-nothing either, and its
response listed ``201`` per entry regardless.

NR-085, found by repairing this, recorded because it bounds what can be asserted
here: ``_create_fhir_resource`` copies only tenancy and audit scaffolding --
lab_id, patient_id, encounter_id, created/updated stamps, version, status,
is_deleted -- and never reads the FHIR resource's clinical content. Of the 12
resource types ``_SUPPORTED_CREATE`` advertises, **none can be inserted**: 9 map
to models whose NOT NULL clinical columns are never populated (``code_display``,
``title``, ``medication_name``, ``vaccine_code`` ...) and 3 (Observation,
Patient, Procedure) have no model at all. So a *created* entry cannot be the
positive control; a batch ``PUT`` against a seeded row is.

WHY THIS DOES NOT USE THE SHARED ``client``/``db`` FIXTURES. Those hand the
endpoint the same session the test holds, inside an outer transaction the harness
rolls back at teardown. A ``db.rollback()`` from inside the request then destroys
the fixtures' own rows -- the first draft of this module failed with
``ObjectDeletedError`` on ``LabUser`` for exactly that reason, which is an
artifact of the harness and not a defect: in production every request gets its
own session. So each call here is given an independent session and the result is
read back through a third one, which is the only way "durable" means anything.

Tables are created from the ORM for the three models involved, scoped with
``__table__.create`` rather than ``create_all`` -- no migration creates any
``ehr_*`` table on any dialect (NR-079), so this is the only way to exercise the
path at all, and it is not evidence that the schema exists anywhere. SQLite is
sufficient because a transaction boundary is dialect-independent; this is
deliberately not a claim about column types.
"""

from __future__ import annotations

from datetime import date
from types import SimpleNamespace

import pytest
from app.ehr.models import ConditionRecord
from app.models.audit_log import AuditLog
from app.routes.ehr_fhir import fhir_batch
from app.services.ehr_service import NationalPatient
from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

_LAB_ID = 7
_PATIENT_ID = "01ARZ3NDEKTSV4RRFFQ69G5FAV"
_ACTOR = SimpleNamespace(id=31337, lab_id=_LAB_ID, role="physician")


@pytest.fixture
def sessions(tmp_path):
    """Independent sessions over one file-backed SQLite database."""
    engine = create_engine(f"sqlite+pysqlite:///{tmp_path / 'nr084.sqlite'}", future=True)
    for model in (NationalPatient, ConditionRecord, AuditLog):
        model.__table__.create(bind=engine)
    Session = sessionmaker(bind=engine, expire_on_commit=False)
    with Session() as seed:
        seed.add(NationalPatient(
            id=_PATIENT_ID, health_number="HN-NR084", first_name="Batch", last_name="Probe",
            date_of_birth=date(1990, 1, 1), gender="FEMALE", lab_id=_LAB_ID, is_deleted=False,
        ))
        seed.commit()
    yield Session
    engine.dispose()


def _seed_conditions(Session, count: int) -> list[str]:
    ids = [f"01ARZ3NDEKTSV4RRFFQ69G5FA{n}" for n in range(count)]
    with Session() as db:
        for cid in ids:
            db.add(ConditionRecord(
                id=cid, patient_id=_PATIENT_ID, code_display="Probe condition",
                version=1, is_deleted=False,
            ))
        db.commit()
    return ids


def _create_entry() -> dict:
    return {
        "resource": {"resourceType": "Condition", "subject": {"reference": f"Patient/{_PATIENT_ID}"}},
        "request": {"method": "POST", "url": "Condition"},
    }


def _update_entry(condition_id: str) -> dict:
    return {
        "resource": {"resourceType": "Condition", "subject": {"reference": f"Patient/{_PATIENT_ID}"}},
        "request": {"method": "PUT", "url": f"Condition/{condition_id}"},
    }


def _unsupported_entry() -> dict:
    return {"resource": {"resourceType": "Unsupported"}, "request": {"method": "POST", "url": "Unsupported"}}


def _call(Session, bundle_type: str, entries: list[dict]) -> dict:
    """One request, one session, closed before anything is read back."""
    with Session() as db:
        return fhir_batch(
            body={"resourceType": "Bundle", "type": bundle_type, "entry": entries},
            current_user=_ACTOR,
            db=db,
        )


def _statuses(result: dict) -> list[str]:
    return [e["entry"][0]["response"]["status"] for e in result["entry"]]


def _version(Session, condition_id: str) -> int:
    with Session() as db:
        return db.query(ConditionRecord).filter(ConditionRecord.id == condition_id).one().version


def _count(Session) -> int:
    with Session() as db:
        return db.query(ConditionRecord).count()


def test_a_batch_entry_that_cannot_be_stored_reports_failure_not_created(sessions):
    """Before the repair this answered 201 and silently discarded the row."""
    before = _count(sessions)

    result = _call(sessions, "batch", [_create_entry()])

    assert _statuses(result) == ["500"], "an unstorable entry must not report 201"
    assert _count(sessions) == before


def test_a_batch_update_reported_successful_is_durable(sessions):
    """The positive control: a 2xx entry survives its session being closed."""
    [cid] = _seed_conditions(sessions, 1)
    assert _version(sessions, cid) == 1

    result = _call(sessions, "batch", [_update_entry(cid)])

    assert _statuses(result) == ["200"], _statuses(result)
    assert _version(sessions, cid) == 2, "the entry reported 200 and was discarded"


def test_one_unstorable_entry_does_not_abort_the_rest_of_the_batch(sessions):
    """Batch entries are independent, so attempting the commit must not fail the call."""
    [cid] = _seed_conditions(sessions, 1)

    result = _call(sessions, "batch", [_unsupported_entry(), _create_entry(), _update_entry(cid)])

    assert _statuses(result) == ["422", "500", "200"], _statuses(result)
    assert _version(sessions, cid) == 2, "a later entry was lost to an earlier entry's failure"


def test_a_transaction_bundle_with_a_failed_entry_applies_nothing_and_says_so(sessions):
    [cid] = _seed_conditions(sessions, 1)

    with pytest.raises(HTTPException) as exc:
        _call(sessions, "transaction", [_update_entry(cid), _unsupported_entry()])

    # All-or-nothing, and the caller is told so rather than handed 201s.
    assert exc.value.status_code == 422
    assert "rolled back" in exc.value.detail
    assert _version(sessions, cid) == 1, "a transaction bundle applied an entry despite a failure"


def test_a_wholly_successful_transaction_bundle_is_durable(sessions):
    """The paired control: the rollback above is not simply discarding everything."""
    first, second = _seed_conditions(sessions, 2)

    result = _call(sessions, "transaction", [_update_entry(first), _update_entry(second)])

    assert _statuses(result) == ["200", "200"], _statuses(result)
    assert _version(sessions, first) == 2
    assert _version(sessions, second) == 2
