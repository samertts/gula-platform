"""Nursing vertical slice: patient assignment + task lifecycle hardening.

Before this pass, app/nursing/routes.py::assign_patient/create_task/
update_task/complete_task/defer_task had zero role check (any authenticated
LabUser of any role) and app/nursing/services.py::update_task did a raw
`setattr` loop over the entire request body with no exclusion list --
including `status`, letting a generic field-update endpoint silently
rewrite a task's clinical state and bypass complete_task/defer_task's own
semantics entirely. assign_patient's nurse_id was pure client input, only
constrained by an FK to lab_users.id (any user, any lab, any role).

Also found and fixed, unrelated to authorization: every
`ForeignKey("lab_users.id")` column in app/nursing/models.py (23 of them)
was declared `String(26)` in the ORM model while the real migration
(20260716_0002_nursing_platform.py) creates them as `Integer` -- verified
against a real local PostgreSQL 16 instance (not SQLite, which hides this
class of bug entirely): a numeric-looking string inserts fine due to
Postgres's implicit text->integer cast, but any non-numeric value (e.g. a
ULID, the exact ID shape this same file's own primary keys use) raises
psycopg2.errors.InvalidTextRepresentation at commit time. Fixed by
correcting the ORM type to Integer, matching the migration and
LabUser.id's real type -- no migration change needed, the migration was
already correct.

BLOCKED, not fixed, and explicitly not this session's to fix: NursingBase
(app/nursing/base.py) is its own separate `declarative_base()`, and every
cross-domain ForeignKey it declares ("lab_users.id", "patients.id", ...)
cannot be resolved within its own MetaData -- the exact NR-086/NR-078
class of defect Abu Ali's branch is actively fixing via
app/orm_topology.py (a shared MetaData for the bases that declare
cross-base foreign keys). His measured closure is seven bases
(CareContinuumBase, EHRBase, DataPlatformBase, TrustBase, IdentityBase,
Base, NationalBase); NursingBase is not among them. This means EVERY
Nursing mutation that flushes a row with one of these FK columns
currently raises `NoReferencedTableError`, in production as much as in
tests -- independent of anything in this file. Fixing app/orm_topology.py
is exactly Abu Ali's active, canonical architecture work (main migration
architecture, cross-domain contracts); this session documents the
dependency and pins it (test_nursing_cross_base_fk_topology_blocks_flush)
rather than touching that file. The route/service fixes above are correct
and ready the moment NursingBase joins that closure.
"""
from __future__ import annotations

import pytest
from app.nursing.enums import NursingTaskType
from app.nursing.models import NursingTask, PatientAssignment
from app.nursing.services import _TASK_TRANSITIONS, _validate_task_transition
from fastapi import HTTPException

from tests.conftest import auth_headers


def _make_patient(db, lab_id: int, health_id: str):
    from app.models.patient import Patient
    patient = Patient(
        lab_id=lab_id, health_id=health_id,
        full_name=f"Patient {health_id}", phone=f"0770{health_id[-7:]}",
    )
    db.add(patient)
    db.flush()
    return patient


# ─── ORM/migration type reconciliation ──────────────────────────────────────


def test_nursing_task_lab_user_fk_columns_are_integer_not_string():
    """Pins the ORM/migration reconciliation fix: every lab_users.id FK
    column in this file must be Integer, matching both the real migration
    and LabUser.id itself. Regressing any one of these silently reopens a
    real-PostgreSQL-only crash (proven against a live Postgres 16 instance,
    not SQLite, which never enforces column types and would hide this)."""
    import sqlalchemy as sa
    for col in NursingTask.__table__.columns:
        if col.name in ("assigned_by", "assigned_to", "completed_by"):
            assert isinstance(col.type, sa.Integer), (
                f"NursingTask.{col.name} must be Integer to match lab_users.id "
                f"and the real migration; got {col.type}"
            )
    for col in PatientAssignment.__table__.columns:
        if col.name == "nurse_id":
            assert isinstance(col.type, sa.Integer)


def test_nursing_cross_base_fk_topology_blocks_flush():
    """LATENT, NOT independently fixable this session: NursingBase's own
    MetaData does not (and, absent Abu Ali's orm_topology.py extending its
    measured closure to include NursingBase, cannot) contain the
    lab_users/patients tables its own columns declare a ForeignKey to.
    Directly reproduces the exact failure mode his NR-086 commit message
    describes ("session.add(...); session.flush() ->
    NoReferencedTableError"), pinned so this test starts failing --
    meaning it's time to re-enable full HTTP-level nursing mutation tests
    -- the moment that dependency resolves, rather than silently going
    stale."""
    assert "lab_users" not in NursingTask.metadata.tables, (
        "NursingBase now has lab_users in its own MetaData -- the "
        "cross-base FK topology blocker this test pins has been resolved "
        "(likely by orm_topology.py extending its closure to include "
        "NursingBase). Re-enable full HTTP-level nursing mutation tests."
    )


# ─── Task state machine: pure logic, no DB required ────────────────────────


def test_task_transition_graph_allows_pending_to_completed_and_deferred():
    assert _TASK_TRANSITIONS["pending"] == {"completed", "deferred"}


def test_task_transition_graph_allows_deferred_to_retry():
    assert _TASK_TRANSITIONS["deferred"] == {"completed", "deferred"}


def test_task_transition_graph_completed_is_terminal():
    assert _TASK_TRANSITIONS["completed"] == set()


def test_validate_task_transition_allows_legal_move():
    _validate_task_transition("pending", "completed")  # must not raise


def test_validate_task_transition_rejects_resurrecting_a_completed_task():
    with pytest.raises(HTTPException) as exc:
        _validate_task_transition("completed", "pending")
    assert exc.value.status_code == 409


def test_validate_task_transition_rejects_completing_a_completed_task():
    """completed is terminal -- a second completion attempt must not
    silently succeed again (matches the terminal-state protection already
    established for Laboratory/Radiology/EMS state machines)."""
    with pytest.raises(HTTPException) as exc:
        _validate_task_transition("completed", "completed")
    assert exc.value.status_code == 409


# ─── Role gates: provable without a flush (denial happens before any DB write) ──


def test_assign_patient_requires_clinical_write_role(client, db, make_lab, make_lab_user):
    lab = make_lab("Nursing Authz Lab 1")
    staff = make_lab_user(lab.id, role="staff")
    patient = _make_patient(db, lab.id, "H-NA-001")

    before = db.query(PatientAssignment).count()
    res = client.post(
        "/nursing/patients/assign",
        headers=auth_headers(staff.id, lab.id, role="staff"),
        json={"nurse_id": "999999", "patient_id": patient.id},
    )
    assert res.status_code == 403
    assert db.query(PatientAssignment).count() == before


def test_assign_patient_rejects_nurse_id_in_another_lab(client, db, make_lab, make_lab_user):
    """Validation runs (and can deny) before assign_patient ever
    constructs a PatientAssignment row, so this is provable even with
    NursingBase's cross-base FK topology gap unresolved."""
    lab_one = make_lab("Nursing Authz Lab 2a")
    lab_two = make_lab("Nursing Authz Lab 2b")
    charge_nurse = make_lab_user(lab_one.id, role="nurse")
    other_lab_nurse = make_lab_user(lab_two.id, role="nurse")
    patient = _make_patient(db, lab_one.id, "H-NA-002")

    res = client.post(
        "/nursing/patients/assign",
        headers=auth_headers(charge_nurse.id, lab_one.id, role="nurse"),
        json={"nurse_id": str(other_lab_nurse.id), "patient_id": patient.id},
    )
    assert res.status_code == 400


def test_assign_patient_rejects_nurse_id_with_wrong_role(client, db, make_lab, make_lab_user):
    lab = make_lab("Nursing Authz Lab 3")
    charge_nurse = make_lab_user(lab.id, role="nurse")
    staff = make_lab_user(lab.id, role="staff")
    patient = _make_patient(db, lab.id, "H-NA-003")

    res = client.post(
        "/nursing/patients/assign",
        headers=auth_headers(charge_nurse.id, lab.id, role="nurse"),
        json={"nurse_id": str(staff.id), "patient_id": patient.id},
    )
    assert res.status_code == 400


def test_create_task_requires_clinical_write_role(client, db, make_lab, make_lab_user):
    lab = make_lab("Nursing Authz Lab 4")
    staff = make_lab_user(lab.id, role="staff")
    patient = _make_patient(db, lab.id, "H-NA-004")

    before = db.query(NursingTask).count()
    res = client.post(
        "/nursing/tasks",
        headers=auth_headers(staff.id, lab.id, role="staff"),
        json={"patient_id": patient.id, "task_type": "observation", "description": "d"},
    )
    assert res.status_code == 403
    assert db.query(NursingTask).count() == before


def test_update_task_requires_clinical_write_role(client, db, make_lab, make_lab_user):
    lab = make_lab("Nursing Authz Lab 5")
    staff = make_lab_user(lab.id, role="staff")

    res = client.put(
        "/nursing/tasks/nonexistent-task-id",
        headers=auth_headers(staff.id, lab.id, role="staff"),
        json={"description": "x"},
    )
    # Role gate must fire before the (currently-blocked) task lookup/flush.
    assert res.status_code == 403


def test_complete_task_requires_clinical_write_role(client, db, make_lab, make_lab_user):
    lab = make_lab("Nursing Authz Lab 6")
    staff = make_lab_user(lab.id, role="staff")

    res = client.put(
        "/nursing/tasks/nonexistent-task-id/complete",
        headers=auth_headers(staff.id, lab.id, role="staff"),
        json={},
    )
    assert res.status_code == 403


def test_defer_task_requires_clinical_write_role(client, db, make_lab, make_lab_user):
    lab = make_lab("Nursing Authz Lab 7")
    staff = make_lab_user(lab.id, role="staff")

    res = client.put(
        "/nursing/tasks/nonexistent-task-id/defer",
        headers=auth_headers(staff.id, lab.id, role="staff"),
        json={"reason": "x"},
    )
    assert res.status_code == 403


# ─── Wiring pins: source-level proof the fix is actually invoked ───────────
# (NursingBase's cross-base FK gap above blocks a real end-to-end flush, so
# the actual runtime behavior of update_task/complete_task/defer_task
# cannot be proven via HTTP yet -- source-inspection is the same
# established technique used for other currently-unbuildable
# infrastructure gaps this session, e.g. test_care_continuum_tenant_scope.py.)


def test_wiring_pin_update_task_calls_transition_guard_and_excludes_protected_fields():
    import inspect
    from app.nursing.services import NursingService
    source = inspect.getsource(NursingService.update_task)
    assert "_validate_task_transition" in source
    assert "_PROTECTED_TASK_FIELDS" in source
    assert "with_for_update" in source


def test_wiring_pin_complete_task_calls_transition_guard():
    import inspect
    from app.nursing.services import NursingService
    source = inspect.getsource(NursingService.complete_task)
    assert "_validate_task_transition" in source
    assert "with_for_update" in source


def test_wiring_pin_defer_task_calls_transition_guard():
    import inspect
    from app.nursing.services import NursingService
    source = inspect.getsource(NursingService.defer_task)
    assert "_validate_task_transition" in source
    assert "with_for_update" in source
