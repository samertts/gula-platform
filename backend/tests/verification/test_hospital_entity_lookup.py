"""``HospitalService._get_entity`` silently matches nothing, so ten routes are dead.

The helper filters with Python's ``not`` instead of SQLAlchemy's ``~``::

    q = db.query(model).filter(model.id == entity_id, model.lab_id == lab_id,
                               not model.is_deleted)

``model.is_deleted`` is an ``InstrumentedAttribute``, which has no ``__bool__``
override, so ``bool(...)`` is the default object truthiness — ``True`` — and
``not model.is_deleted`` is the plain Python ``False``.  SQLAlchemy coerces that
literal into the WHERE clause and then folds the whole conjunction, because
``a AND b AND false`` is ``false``: the compiled statement is ``WHERE false``.
The id and tenant predicates do not merely fail to match, they disappear.

So ``_get_entity`` never returns a row.  It always raises ``NotFoundError``, and
every one of its ten route call sites answers 404 for a record that exists.  The
route proven here is the WHO surgical safety checklist, whose service locks the
theater and enforces all ten pre-incision checks — none of which is ever reached.

This is a lookup defect, not a tenancy one.  ``WHERE false`` leaks nothing; it
denies everything.  The tenant predicate is restored by the same fix, so the
cross-tenant test below pins that the repair does not turn a blanket denial into
a cross-tenant read.

Two of the ten call sites (``Bed``, ``Campus``, ``MedicalEquipment``) address
tables that do not exist at the canonical head — that is NR-028, awaiting
authorization, and is deliberately not exercised here.  ``OperationTheater`` and
``HospitalDepartment`` are physically present, so the defect is provable now.
"""

from __future__ import annotations

import datetime as dt
import uuid
from typing import Any

import pytest
from sqlalchemy import text

from . import harness

pytestmark = harness.requires_postgres()

LAB_ID = 994801
OTHER_LAB_ID = 994802
ACTOR_ID = 74801
HOSPITAL_ID = 94801
THEATER_ID = 94811
OTHER_THEATER_ID = 94812
CHECKLIST_AUDIT = "surgery.safety_checklist.completed"
GUARD_AUDIT = "clinical.hospital.safety_checklist.complete"

WHO_CHECKS = (
    "patient_identity_confirmed", "procedure_confirmed", "site_marked",
    "consent_verified", "anesthesia_assessment_complete", "allergy_reviewed",
    "antibiotic_prophylaxis_confirmed", "blood_products_confirmed",
    "imaging_reviewed", "team_time_out_completed",
)


def _now() -> dt.datetime:
    return dt.datetime.now(dt.UTC)


@pytest.fixture()
def Session() -> Any:
    S = harness.session_factory(pool_size=4)
    yield S
    harness.dispose(S)


def _purge(S: Any) -> None:
    with S() as s:
        for lab in (LAB_ID, OTHER_LAB_ID):
            for table in ("hospital_surgical_safety_checklists", "hospital_operation_theaters",
                          "hospitals", "clinical_command_receipts"):
                s.execute(text(f"DELETE FROM {table} WHERE lab_id = :l"), {"l": lab})
            s.execute(text("DELETE FROM lab_users WHERE lab_id = :l"), {"l": lab})
            s.execute(text("DELETE FROM labs WHERE id = :l"), {"l": lab})
        s.commit()


@pytest.fixture()
def seeded(Session: Any) -> dict[str, Any]:
    """One available theater in the actor's lab, one in a different lab."""
    _purge(Session)
    now = _now()
    with Session() as s:
        for lab, label in ((LAB_ID, "Theater Lab"), (OTHER_LAB_ID, "Other Lab")):
            s.execute(text("INSERT INTO labs (id,name,is_active) VALUES (:l,:n,true)"),
                      {"l": lab, "n": label})
        s.execute(
            text("INSERT INTO lab_users (id,lab_id,name,email,password_hash,role,is_active,"
                 "perm_version) VALUES (:i,:l,'Theater Actor',:e,'!synthetic','master_admin',true,1)"),
            {"i": ACTOR_ID, "l": LAB_ID, "e": f"theater-{uuid.uuid4().hex[:8]}@example.invalid"},
        )
        s.execute(
            text("INSERT INTO hospitals (id,lab_id,name,code,hospital_type,is_active,is_deleted,"
                 "version,created_at,updated_at) "
                 "VALUES (:i,:l,'Proof Hospital',:c,'general',true,false,1,:n,:n)"),
            {"i": HOSPITAL_ID, "l": LAB_ID, "c": f"HOSP-{uuid.uuid4().hex[:6]}", "n": now},
        )
        for tid, lab in ((THEATER_ID, LAB_ID), (OTHER_THEATER_ID, OTHER_LAB_ID)):
            s.execute(
                text("INSERT INTO hospital_operation_theaters (id,lab_id,hospital_id,code,name,"
                     "theater_type,status,is_active,is_deleted,version,created_at,updated_at) "
                     "VALUES (:i,:l,:h,:c,'Theater 1','general','available',true,false,1,:n,:n)"),
                {"i": tid, "l": lab, "h": HOSPITAL_ID, "c": f"OT-{tid}", "n": now},
            )
        s.commit()
    return {"theater_id": THEATER_ID, "other_theater_id": OTHER_THEATER_ID, "version": 1}


def _actor(lab_id: int = LAB_ID) -> harness.Actor:
    return harness.Actor(user_id=ACTOR_ID, lab_id=lab_id, role="master_admin")


def _body(theater_id: int) -> dict[str, Any]:
    body: dict[str, Any] = {
        "operation_theater_id": theater_id,
        "surgery_id": 5501,
        "patient_id": 7701,
        "procedure_name": "Left inguinal hernia repair",
        "procedure_site": "left inguinal region",
        "planned_laterality": "left",
    }
    body.update(dict.fromkeys(WHO_CHECKS, True))
    return body


def _complete(Session: Any, *, theater_id: int, version: int, actor: harness.Actor) -> Any:
    with harness.client(Session, actor) as client:
        return client.post(
            f"/hospital/operation-theaters/{theater_id}/surgical-safety-checklists",
            json=_body(theater_id),
            headers={"If-Match": str(version), "Idempotency-Key": uuid.uuid4().hex},
        )
    # harness.clear_overrides() runs in harness.client's teardown


def test_a_real_theater_is_found_by_the_entity_helper(Session: Any, seeded: dict[str, Any]) -> None:
    """The route must reach its service instead of denying a theater that exists."""
    response = _complete(Session, theater_id=seeded["theater_id"], version=seeded["version"],
                         actor=_actor())
    assert response.status_code != 404, (
        "the route answered 404 for a theater that is committed in this lab; "
        f"_get_entity matched nothing. body={response.text[:400]}"
    )
    assert response.status_code == 201, response.text[:400]


def test_the_who_checklist_is_durably_recorded(Session: Any, seeded: dict[str, Any]) -> None:
    """A completed checklist must survive as committed state, not just a 201."""
    response = _complete(Session, theater_id=seeded["theater_id"], version=seeded["version"],
                         actor=_actor())
    assert response.status_code == 201, response.text[:400]
    rows = harness.committed(
        Session,
        "SELECT id, operation_theater_id, planned_laterality, completed_by, "
        "patient_identity_confirmed, team_time_out_completed "
        "FROM hospital_surgical_safety_checklists WHERE lab_id = :l",
        l=LAB_ID,
    )
    assert len(rows) == 1, f"expected exactly one durable checklist, got {rows}"
    assert rows[0]["operation_theater_id"] == seeded["theater_id"]
    assert rows[0]["planned_laterality"] == "left"
    assert rows[0]["completed_by"] == ACTOR_ID
    assert rows[0]["patient_identity_confirmed"] is True
    assert rows[0]["team_time_out_completed"] is True
    # Scoped to this checklist's id rather than to the lab: ``audit_logs`` rows are
    # hash-chained, so the fixture must not delete them between tests, and earlier
    # tests in the same run leave their own rows behind under the same lab.
    audits = [
        row for row in harness.audit_rows(Session, lab_id=LAB_ID, action=CHECKLIST_AUDIT)
        if row["resource_id"] == rows[0]["id"]
    ]
    assert len(audits) == 1, f"the completed checklist must be audited exactly once, got {audits}"
    assert audits[0]["user_id"] == ACTOR_ID
    guard_audits = [
        row for row in harness.audit_rows(Session, lab_id=LAB_ID, action=GUARD_AUDIT)
        if row["resource_id"] == seeded["theater_id"]
    ]
    assert guard_audits, (
        "the guard's own completion audit is the row whose 52-character action overflowed "
        f"audit_logs.action(50); it must now persist. rows={guard_audits}"
    )


def test_a_theater_in_another_lab_is_still_refused(Session: Any, seeded: dict[str, Any]) -> None:
    """Restoring the predicate must not widen the lookup across tenants.

    Before the fix this passed for the wrong reason — ``WHERE false`` refuses
    every caller.  It is kept so the repair cannot trade a blanket denial for a
    cross-tenant read.
    """
    response = _complete(Session, theater_id=seeded["other_theater_id"], version=seeded["version"],
                         actor=_actor())
    assert response.status_code == 404, (
        "a theater belonging to another lab must not be reachable; "
        f"got {response.status_code}: {response.text[:400]}"
    )
    assert harness.committed(
        Session,
        "SELECT id FROM hospital_surgical_safety_checklists WHERE lab_id = :l",
        l=OTHER_LAB_ID,
    ) == [], "a cross-tenant call must leave no checklist behind"
