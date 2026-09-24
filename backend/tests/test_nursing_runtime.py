"""Nursing runtime paths, executed against PostgreSQL (NR-026).

The domain contract proves the ORM matches the schema. This proves the domain
actually works: real writes, real reads, tenant isolation, and the two
workflows that were dead — clinical checklists and clinical escalation.
"""
from __future__ import annotations

import os
from datetime import UTC, date, datetime, time

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker


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


POSTGRES_URL = _schema_database_url()
pytestmark = pytest.mark.skipif(
    not POSTGRES_URL, reason="GULA_SCHEMA_DATABASE_URL is not configured"
)

LAB_A, LAB_B = 990401, 990402
NURSE_A, NURSE_B = 990411, 990412
PATIENT_A, PATIENT_B = 990421, 990422


@pytest.fixture(scope="module")
def Session():
    engine = create_engine(POSTGRES_URL, future=True)
    factory = sessionmaker(bind=engine, expire_on_commit=False)
    with engine.begin() as conn:
        for lab, nurse, patient in (
            (LAB_A, NURSE_A, PATIENT_A),
            (LAB_B, NURSE_B, PATIENT_B),
        ):
            conn.execute(text(
                "INSERT INTO labs (id,name,is_active) VALUES (:i,:n,true) "
                "ON CONFLICT (id) DO NOTHING"), {"i": lab, "n": f"Nursing Lab {lab}"})
            conn.execute(text(
                "INSERT INTO lab_users (id,lab_id,name,email,password_hash,role,is_active,perm_version)"
                " VALUES (:i,:l,:n,:e,'!x','nurse',true,1) ON CONFLICT (id) DO NOTHING"),
                {"i": nurse, "l": lab, "n": f"Nurse {nurse}", "e": f"n{nurse}@example.invalid"})
            # nursing_escalation_records.patient_id is NOT NULL, and the clinical
            # tables key patients by the same integer identity the rest of the
            # platform uses. Seed a real row rather than a synthetic id.
            conn.execute(text(
                "INSERT INTO patients (id,lab_id,full_name,phone) "
                "VALUES (:i,:l,:n,:p) ON CONFLICT (id) DO NOTHING"),
                {"i": patient, "l": lab, "n": f"Nursing Patient {patient}",
                 "p": f"0790{patient}"})
    try:
        yield factory
    finally:
        with engine.begin() as conn:
            # every nursing table this module can write, children first
            for t in ("nursing_escalation_records", "nursing_clinical_checklists",
                      "nursing_delegations", "nursing_tasks", "nursing_notes",
                      "nursing_fluid_balance", "nursing_pain_assessments",
                      "nursing_vital_signs", "nursing_care_plans",
                      "nursing_shift_handovers", "nursing_patient_assignments",
                      "nursing_shifts"):
                conn.execute(text(f"DELETE FROM {t} WHERE lab_id IN (:a,:b)"),
                             {"a": LAB_A, "b": LAB_B})
            conn.execute(text("DELETE FROM patients WHERE id IN (:a,:b)"),
                         {"a": PATIENT_A, "b": PATIENT_B})
        engine.dispose()


def _shift(session, lab: int, nurse: int):
    from app.nursing.models import NursingShift

    shift = NursingShift(lab_id=lab, nurse_id=nurse, shift_type="day",
                         shift_date=date(2026, 9, 10), start_time=time(8, 0),
                         status="scheduled", version=1, is_deleted=False)
    session.add(shift)
    session.commit()
    session.refresh(shift)
    return shift


def test_a_shift_can_be_created_and_read_back(Session) -> None:
    with Session() as s:
        shift = _shift(s, LAB_A, NURSE_A)
        assert isinstance(shift.id, int), "the primary key is a server-assigned integer"
        again = s.query(type(shift)).filter_by(id=shift.id).one()
        assert again.nurse_id == NURSE_A
        assert again.lab_id == LAB_A


def test_the_clinical_checklist_path_works(Session) -> None:
    """One of the two workflows that raised UndefinedTable on every call."""
    from app.nursing.models import ClinicalChecklist
    from app.nursing.services import NursingService

    with Session() as s:
        shift = _shift(s, LAB_A, NURSE_A)
        checklist = NursingService.create_checklist(s, LAB_A, NURSE_A, {
            "patient_id": PATIENT_A, "shift_id": shift.id, "checklist_type": "admission",
            "title": "Admission checklist", "items": [{"text": "ID band", "done": False}],
            "total_items": 1, "status": "pending",
        })
        s.commit()
        assert isinstance(checklist.id, int)
        stored = s.query(ClinicalChecklist).filter_by(id=checklist.id).one()
        assert stored.lab_id == LAB_A
        assert stored.checklist_type == "admission"
        assert stored.patient_id == PATIENT_A


def test_the_clinical_escalation_path_works(Session) -> None:
    """The other dead workflow — how a deteriorating patient reaches a senior clinician."""
    from app.nursing.models import EscalationRecord

    with Session() as s:
        record = EscalationRecord(
            lab_id=LAB_A, patient_id=PATIENT_A, escalated_by=NURSE_A, escalated_to=NURSE_A,
            escalation_level="urgent", reason="Sustained tachycardia",
            status="open", escalated_at=datetime.now(UTC), version=1, is_deleted=False,
        )
        s.add(record)
        s.commit()
        s.refresh(record)

        # the filter that could never run: escalated_to is an integer lab_users key
        open_for_nurse = s.query(EscalationRecord).filter(
            EscalationRecord.escalated_to == NURSE_A,
            EscalationRecord.status == "open",
            EscalationRecord.lab_id == LAB_A,
        ).count()
        assert open_for_nurse >= 1


def test_escalations_do_not_leak_between_laboratories(Session) -> None:
    from app.nursing.models import EscalationRecord

    with Session() as s:
        for lab, nurse, patient in (
            (LAB_A, NURSE_A, PATIENT_A),
            (LAB_B, NURSE_B, PATIENT_B),
        ):
            s.add(EscalationRecord(
                lab_id=lab, patient_id=patient, escalated_by=nurse, escalated_to=nurse,
                escalation_level="urgent", reason="probe", status="open",
                escalated_at=datetime.now(UTC), version=1, is_deleted=False))
        s.commit()

        a = s.query(EscalationRecord).filter(EscalationRecord.lab_id == LAB_A).count()
        b = s.query(EscalationRecord).filter(EscalationRecord.lab_id == LAB_B).count()
        both = s.query(EscalationRecord).filter(
            EscalationRecord.lab_id.in_([LAB_A, LAB_B])).count()
        assert a >= 1 and b >= 1
        assert a < both, "a laboratory-scoped query returned another laboratory's escalations"


def test_a_client_cannot_set_server_owned_columns(Session) -> None:
    """The services splatted the raw request body into the model constructor."""
    from app.nursing.models import NursingNote
    from app.nursing.services import NursingService

    with Session() as s:
        note = NursingService.create_nursing_note(s, LAB_A, NURSE_A, {
            "patient_id": PATIENT_A,
            "note_type": "progress", "title": "probe", "content": "body",
            "written_by": NURSE_A, "written_at": datetime.now(UTC),
            # everything below is attacker-supplied and must be ignored
            "id": 424242, "lab_id": LAB_B, "version": 99, "is_deleted": True,
            "not_a_column": "should not raise",
        })
        s.commit()
        s.refresh(note)
        assert note.id != 424242, "a client-supplied primary key was accepted"
        assert note.lab_id == LAB_A, "a client-supplied lab_id was accepted"
        assert note.is_deleted is not True, "a client-supplied soft-delete flag was accepted"
        stored = s.query(NursingNote).filter_by(id=note.id).one()
        assert stored.lab_id == LAB_A


def test_an_unknown_field_no_longer_crashes_the_endpoint(Session) -> None:
    """Model(**data) raised TypeError for any field the table lacks."""
    from app.nursing.services import NursingService

    with Session() as s:
        note = NursingService.create_nursing_note(s, LAB_A, NURSE_A, {
            "patient_id": PATIENT_A,
            "note_type": "progress", "title": "unknown-field probe", "content": "x",
            "written_by": NURSE_A, "written_at": datetime.now(UTC),
            "encounter_id": "not-a-column", "subjective": "nor this",
        })
        s.commit()
        assert isinstance(note.id, int)


# ── the paths that were silently doing nothing ────────────────────────────────


def test_unassigning_a_patient_actually_ends_the_assignment(Session) -> None:
    """`is_active`/`end_date` are not columns of nursing_patient_assignments.

    Setting them created two instance attributes and left the row untouched, so
    the nurse kept the patient and every later assign returned 409.
    """
    from app.nursing.models import PatientAssignment
    from app.nursing.services import NursingService

    with Session() as s:
        NursingService.assign_patient(
            s, LAB_A, NURSE_A, NURSE_A, PATIENT_A, "primary", notes="probe",
            actor_role="technician")
        s.commit()
        assert NursingService.get_assigned_patients(s, LAB_A, NURSE_A)

        NursingService.unassign_patient(
            s, LAB_A, NURSE_A, NURSE_A, PATIENT_A, "shift end",
            actor_role="technician")
        s.commit()

        row = s.query(PatientAssignment).filter_by(
            lab_id=LAB_A, nurse_id=NURSE_A, patient_id=PATIENT_A).one()
        assert row.unassigned_at is not None, "the assignment is still open in the database"
        assert row.unassigned_reason == "shift end"
        assert NursingService.get_assigned_patients(s, LAB_A, NURSE_A) == []


def test_a_task_can_be_created_completed_and_deferred(Session) -> None:
    """nursing_tasks.title is NOT NULL and had no request field: every POST failed."""
    from app.nursing.models import NursingTask
    from app.nursing.services import NursingService

    with Session() as s:
        task = NursingService.create_task(s, LAB_A, NURSE_A, {
            "patient_id": PATIENT_A, "assigned_to": NURSE_A, "task_type": "vital_signs",
            "title": "Four-hourly observations", "description": "NEWS2 set",
            "due_at": datetime.now(UTC),
        }, actor_role="technician")
        s.commit()
        assert isinstance(task.id, int)

        later = datetime(2026, 9, 11, 8, 0, tzinfo=UTC)
        NursingService.defer_task(s, LAB_A, NURSE_A, task.id, later, "patient off ward")
        s.commit()
        s.refresh(task)
        assert task.due_at == later, "a deferred task kept its original deadline"
        assert task.status == "deferred"

        NursingService.complete_task(s, LAB_A, NURSE_A, task.id, "tolerated well", "done")
        s.commit()
        s.refresh(task)
        assert task.status == "completed"
        assert task.outcome == "tolerated well", "the clinical outcome was discarded"
        assert s.query(NursingTask).filter_by(id=task.id).one().completed_by == NURSE_A


def test_a_shift_starts_and_ends_through_the_service(Session) -> None:
    """start_time is TIME, not TIMESTAMP; the route used to pass a datetime."""
    from app.nursing.services import NursingService

    with Session() as s:
        shift = NursingService.start_shift(s, LAB_B, NURSE_B, {
            "shift_type": "night", "shift_date": date(2026, 9, 10), "ward": "ICU"})
        s.commit()
        assert shift.clocked_in_at is not None
        assert shift.start_time is not None and not isinstance(shift.start_time, datetime)

        ended = NursingService.end_shift(s, LAB_B, NURSE_B, shift.id)
        s.commit()
        assert ended.clocked_out_at is not None
        assert ended.status == "completed"


def test_a_delegation_records_who_delegated_and_when(Session) -> None:
    """delegated_at and task_type are NOT NULL and no caller could supply them."""
    from app.nursing.services import NursingService

    with Session() as s:
        d = NursingService.delegate_task(s, LAB_A, NURSE_A, {
            "patient_id": PATIENT_A, "delegated_to": NURSE_A,
            "task_type": "hygiene", "description": "Assisted wash"})
        s.commit()
        assert d.delegated_at is not None
        assert d.delegated_by == NURSE_A
        assert d.status == "pending"


def test_resolving_an_escalation_keeps_the_clinician_account(Session) -> None:
    """`resolution` was written to an attribute with no column and vanished."""
    from app.nursing.services import NursingService

    with Session() as s:
        rec = NursingService.escalate(s, LAB_A, NURSE_A, {
            "patient_id": PATIENT_A, "escalation_level": "urgent",
            "reason": "New oxygen requirement", "escalated_to": NURSE_A})
        s.commit()
        assert rec.escalated_at is not None

        NursingService.acknowledge_escalation(s, LAB_A, NURSE_A, rec.id)
        s.commit()
        s.refresh(rec)
        assert rec.acknowledged_at is not None

        NursingService.resolve_escalation(
            s, LAB_A, NURSE_A, rec.id, "Reviewed by registrar; oxygen weaned", "improved")
        s.commit()
        s.refresh(rec)
        assert rec.status == "resolved"
        assert rec.resolution_notes == "Reviewed by registrar; oxygen weaned"
        assert rec.outcome == "improved"


def test_net_fluid_balance_reads_the_column_that_exists(Session) -> None:
    """`amount_ml` is not a column — the calculation raised AttributeError."""
    from app.nursing.services import NursingService

    with Session() as s:
        for balance_type, volume in (("intake", 500.0), ("output", 200.0)):
            NursingService.record_fluid_balance(s, LAB_A, NURSE_A, {
                "patient_id": PATIENT_A, "recorded_at": datetime(2026, 9, 10, 9, tzinfo=UTC),
                "fluid_type": "oral" if balance_type == "intake" else "urine",
                "category": "intake_oral" if balance_type == "intake" else "output_urine",
                "balance_type": balance_type, "volume_ml": volume,
            })
        s.commit()

        net = NursingService.get_net_balance(s, LAB_A, PATIENT_A, date(2026, 9, 10))
        assert net["total_intake_ml"] == 500.0
        assert net["total_output_ml"] == 200.0
        assert net["net_balance_ml"] == 300.0


def test_a_checklist_derives_its_counts_rather_than_trusting_the_client(Session) -> None:
    from app.nursing.services import NursingService

    with Session() as s:
        checklist = NursingService.create_checklist(s, LAB_A, NURSE_A, {
            "patient_id": PATIENT_A, "checklist_type": "admission",
            "title": "Admission checklist",
            "items": [{"text": "ID band"}, {"text": "Allergies confirmed"}],
            "total_items": 99,          # a client may not decide this
        })
        s.commit()
        assert checklist.total_items == 2
        assert checklist.completed_count == 0

        for idx in (0, 1):
            NursingService.update_checklist_item(s, LAB_A, NURSE_A, checklist.id, idx, True)
        s.commit()
        s.refresh(checklist)
        assert checklist.completed_count == 2
        assert checklist.status == "completed"
        assert checklist.completed_by == NURSE_A
        assert checklist.completed_at is not None


def test_a_nursing_mutation_writes_a_correct_audit_row(Session) -> None:
    """log_action's sixth parameter is user_role, not lab_id.

    Nursing called it positionally as (…, resource_id, user_id, lab_id, details),
    so the laboratory landed in user_role, the details dict landed in lab_id —
    which psycopg2 cannot adapt — and the mutation's own transaction died.
    """
    from app.nursing.services import NursingService
    from sqlalchemy import text

    with Session() as s:
        watermark = s.execute(
            text("SELECT coalesce(max(id), 0) FROM audit_logs")).scalar_one()
        NursingService.create_task(s, LAB_A, NURSE_A, {
            "patient_id": PATIENT_A, "task_type": "observation",
            "title": "Audit probe", "due_at": datetime.now(UTC),
        }, actor_role="technician")
        s.commit()

        row = s.execute(text(
            "SELECT action, user_id, user_role, lab_id, details FROM audit_logs "
            "WHERE id > :w ORDER BY id DESC LIMIT 1"), {"w": watermark}).one()
        action, user_id, user_role, lab_id, details = row
        assert action == "nursing.create_task"
        assert user_id == NURSE_A
        # NR-160: the row must name the actor's authority, not just their id.
        assert user_role == "technician", (
            f"the nursing audit row recorded the role as {user_role!r}; before "
            "NR-160 it was NULL for every nursing action")
        assert lab_id == LAB_A, "the laboratory did not reach the lab_id column"
        assert details and "Audit probe" in details, "the details were dropped"


def test_the_api_refuses_a_field_the_schema_cannot_store() -> None:
    """Accepting `pupil_left_size` and discarding it is worse than refusing it.

    A nurse who records a pupil reaction and gets 201 back is entitled to
    believe it was recorded. No nursing table has a column for it.
    """
    import pydantic
    from app.nursing.routes import EscalationCreate, VitalSignsCreate

    with pytest.raises(pydantic.ValidationError):
        VitalSignsCreate(patient_id=PATIENT_A, pupil_left_size=3.0)
    with pytest.raises(pydantic.ValidationError):
        EscalationCreate(patient_id=PATIENT_A, escalation_level="urgent",
                         reason="probe", encounter_id="enc-1")

    # the same request without the unstorable field is still accepted
    assert VitalSignsCreate(patient_id=PATIENT_A, systolic_bp=118).systolic_bp == 118
