from __future__ import annotations

import logging
from datetime import date, datetime, timedelta
from typing import Any

from fastapi import HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from app._compat import UTC
from app.nursing.enums import DelegationStatus
from app.nursing.models import (
    ClinicalChecklist,
    Delegation,
    EscalationRecord,
    FallRiskAssessment,
    FluidBalance,
    NursingCarePlan,
    NursingNote,
    NursingShift,
    NursingTask,
    NutritionAssessment,
    PainAssessment,
    PatientAssignment,
    PressureInjuryAssessment,
    ShiftHandover,
    VitalSignsRecord,
)
from app.services.audit_service import log_action

logger = logging.getLogger("gula.nursing.services")

_NURSING_NS = "nursing"

# Columns the server owns. A client may never set identity, tenancy, audit
# attribution, the optimistic-lock counter or the soft-delete flags, and the
# request body is not allowed to carry a column the table does not have.
_SERVER_OWNED = frozenset({
    "id", "lab_id", "created_by", "updated_by", "version",
    "is_deleted", "deleted_at", "created_at", "updated_at",
})


def _payload(model: type, data: dict) -> dict:
    """A request body reduced to the columns of `model` that a client may set.

    Every nursing service used to splat the raw body straight into a model
    constructor. Two things followed: a request carrying a field the table does
    not have raised TypeError, and a request carrying `id`, `version` or
    `is_deleted` had it written verbatim. Both are closed here, in one place,
    with the same rule the Blood Bank services already apply (NR-021).
    """
    columns = {c.name for c in model.__table__.columns}
    return {k: v for k, v in data.items() if k in columns and k not in _SERVER_OWNED}




class NursingService:

    # ── Patient Assignments ──────────────────────────────────────────────────────

    @staticmethod
    def assign_patient(
        db: Session, lab_id: int, user_id: int, nurse_id: int, patient_id: int,
        assignment_type: str, shift_id: int | None = None,
        ward: str | None = None, bed_number: str | None = None,
        notes: str | None = None,
        *,
        actor_role: str,
    ) -> PatientAssignment:
        existing = db.query(PatientAssignment).filter(
            PatientAssignment.nurse_id == nurse_id,
            PatientAssignment.patient_id == patient_id,
            PatientAssignment.unassigned_at.is_(None),
            PatientAssignment.lab_id == lab_id,
        ).first()
        if existing:
            raise HTTPException(status_code=409, detail="Patient already assigned to this nurse")
        assignment = PatientAssignment(
            lab_id=lab_id, created_by=user_id,
            nurse_id=nurse_id, patient_id=patient_id,
            assignment_type=assignment_type,
            shift_id=shift_id, ward=ward, bed_number=bed_number,
            # NOT NULL, and the server owns it: an assignment starts now.
            assigned_at=datetime.now(UTC),
            notes=notes,
        )
        db.add(assignment)
        db.flush()
        log_action(db, f"{_NURSING_NS}.assign_patient", "patient_assignment", assignment.id, user_id=user_id, user_role=actor_role, lab_id=lab_id, details={
            "nurse_id": nurse_id, "patient_id": patient_id, "type": assignment_type,
        })
        return assignment

    @staticmethod
    def unassign_patient(
        db: Session, lab_id: int, user_id: int, nurse_id: int, patient_id: int,
        unassigned_reason: str | None = None,
        *,
        actor_role: str,
    ) -> None:
        assignment = db.query(PatientAssignment).filter(
            PatientAssignment.nurse_id == nurse_id,
            PatientAssignment.patient_id == patient_id,
            PatientAssignment.unassigned_at.is_(None),
            PatientAssignment.lab_id == lab_id,
        ).first()
        if not assignment:
            raise HTTPException(status_code=404, detail="Active assignment not found")
        # `is_active` and `end_date` are not columns of this table. Assigning
        # them created two instance attributes and left the row untouched, so
        # every unassignment silently did nothing and the nurse kept the
        # patient. `unassigned_at` is the column every query already reads.
        assignment.unassigned_at = datetime.now(UTC)
        if unassigned_reason is not None:
            assignment.unassigned_reason = unassigned_reason
        assignment.updated_by = user_id
        db.flush()
        log_action(db, f"{_NURSING_NS}.unassign_patient", "patient_assignment", assignment.id, user_id=user_id, user_role=actor_role, lab_id=lab_id, details={
            "nurse_id": nurse_id, "patient_id": patient_id,
        })

    @staticmethod
    def get_assigned_patients(
        db: Session, lab_id: int, nurse_id: int,
    ) -> list[dict[str, Any]]:
        assignments = db.query(PatientAssignment).filter(
            PatientAssignment.nurse_id == nurse_id,
            PatientAssignment.unassigned_at.is_(None),
            PatientAssignment.lab_id == lab_id,
        ).all()
        results = []
        for a in assignments:
            results.append({
                "assignment_id": a.id,
                "patient_id": a.patient_id,
                "shift_id": a.shift_id,
                "ward": a.ward,
                "bed_number": a.bed_number,
                "assignment_type": a.assignment_type,
                "assigned_at": a.assigned_at.isoformat() if a.assigned_at else None,
                "notes": a.notes,
            })
        return results

    @staticmethod
    def get_nurse_dashboard(
        db: Session, lab_id: int, nurse_id: str,
    ) -> dict[str, Any]:
        now = datetime.now(UTC)
        today = now.date()
        assigned = db.query(PatientAssignment).filter(
            PatientAssignment.nurse_id == nurse_id,
            PatientAssignment.unassigned_at.is_(None),
            PatientAssignment.lab_id == lab_id,
        ).count()
        tasks_due = db.query(NursingTask).filter(
            NursingTask.assigned_to == nurse_id,
            NursingTask.status.in_(["pending", "in_progress"]),
            NursingTask.due_at <= now,
            NursingTask.lab_id == lab_id,
        ).count()
        vitals_due_today = db.query(VitalSignsRecord).filter(
            VitalSignsRecord.recorded_by == nurse_id,
            func.date(VitalSignsRecord.recorded_at) == today,
        ).count()
        alerts = db.query(EscalationRecord).filter(
            EscalationRecord.escalated_to == nurse_id,
            EscalationRecord.status == "open",
            EscalationRecord.lab_id == lab_id,
        ).count()
        return {
            "assigned_patients": assigned,
            "tasks_due": tasks_due,
            "vitals_due": vitals_due_today,
            "alerts": alerts,
        }

    # ── Tasks ────────────────────────────────────────────────────────────────────

    @staticmethod
    def create_task(
        db: Session, lab_id: int, user_id: int, data: dict,
        *,
        actor_role: str,
    ) -> NursingTask:
        task = NursingTask(lab_id=lab_id, created_by=user_id, **_payload(NursingTask, data))
        db.add(task)
        db.flush()
        log_action(db, f"{_NURSING_NS}.create_task", "nursing_task", task.id, user_id=user_id, user_role=actor_role, lab_id=lab_id, details=data)
        return task

    @staticmethod
    def update_task(db: Session, lab_id: int, user_id: int, task_id: int, data: dict) -> NursingTask:
        task = db.query(NursingTask).filter(
            NursingTask.id == task_id, NursingTask.lab_id == lab_id,
            ~NursingTask.is_deleted,
        ).first()
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        for k, v in _payload(NursingTask, data).items():
            setattr(task, k, v)
        task.updated_by = user_id
        db.flush()
        return task

    @staticmethod
    def complete_task(
        db: Session, lab_id: int, user_id: int, task_id: int,
        outcome: str | None = None, notes: str | None = None,
    ) -> NursingTask:
        task = db.query(NursingTask).filter(
            NursingTask.id == task_id, NursingTask.lab_id == lab_id,
            ~NursingTask.is_deleted,
        ).first()
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        task.status = "completed"
        task.completed_at = datetime.now(UTC)
        task.completed_by = user_id
        if outcome is not None:
            task.outcome = outcome
        if notes is not None:
            task.notes = notes
        task.updated_by = user_id
        db.flush()
        return task

    @staticmethod
    def defer_task(
        db: Session, lab_id: int, user_id: int, task_id: int,
        due_at: datetime | None = None, reason: str | None = None,
    ) -> NursingTask:
        task = db.query(NursingTask).filter(
            NursingTask.id == task_id, NursingTask.lab_id == lab_id,
            ~NursingTask.is_deleted,
        ).first()
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        task.status = "deferred"
        if due_at:
            # `due_time` is not a column: the new deadline was dropped and the
            # task stayed due at its original time.
            task.due_at = due_at
        if reason:
            task.notes = (task.notes or "") + f"\n[Deferred: {reason}]"
        task.updated_by = user_id
        db.flush()
        return task

    @staticmethod
    def get_tasks(
        db: Session, lab_id: int, nurse_id: int | None = None,
        patient_id: int | None = None, status: str | None = None,
        task_type: str | None = None, date_from: date | None = None,
        date_to: date | None = None, skip: int = 0, limit: int = 50,
    ) -> list[NursingTask]:
        q = db.query(NursingTask).filter(
            NursingTask.lab_id == lab_id, ~NursingTask.is_deleted,
        )
        if nurse_id:
            q = q.filter(NursingTask.assigned_to == nurse_id)
        if patient_id:
            q = q.filter(NursingTask.patient_id == patient_id)
        if status:
            q = q.filter(NursingTask.status == status)
        if task_type:
            q = q.filter(NursingTask.task_type == task_type)
        if date_from:
            q = q.filter(NursingTask.due_at >= date_from)
        if date_to:
            q = q.filter(NursingTask.due_at <= date_to)
        return q.order_by(NursingTask.due_at.asc().nullslast()).offset(skip).limit(limit).all()

    @staticmethod
    def get_tasks_by_patient(db: Session, lab_id: int, patient_id: int) -> list[NursingTask]:
        return db.query(NursingTask).filter(
            NursingTask.patient_id == patient_id,
            NursingTask.lab_id == lab_id,
            ~NursingTask.is_deleted,
        ).order_by(NursingTask.due_at.desc().nullslast()).all()

    @staticmethod
    def get_tasks_by_nurse(
        db: Session, lab_id: int, nurse_id: int, task_date: date | None = None,
    ) -> list[NursingTask]:
        q = db.query(NursingTask).filter(
            NursingTask.assigned_to == nurse_id,
            NursingTask.lab_id == lab_id,
            ~NursingTask.is_deleted,
        )
        if task_date:
            q = q.filter(func.date(NursingTask.due_at) == task_date)
        return q.order_by(NursingTask.due_at.asc().nullslast()).all()

    # ── Vital Signs ──────────────────────────────────────────────────────────────

    @staticmethod
    def record_vital_signs(db: Session, lab_id: int, user_id: int, data: dict) -> VitalSignsRecord:
        record = VitalSignsRecord(lab_id=lab_id, created_by=user_id, **_payload(VitalSignsRecord, data))
        if record.height_cm and record.weight_kg and record.height_cm > 0:
            record.bmi = round(record.weight_kg / ((record.height_cm / 100) ** 2), 1)
        if record.gcs_eye is not None and record.gcs_verbal is not None and record.gcs_motor is not None:
            record.gcs_total = record.gcs_eye + record.gcs_verbal + record.gcs_motor
        db.add(record)
        db.flush()
        return record

    @staticmethod
    def get_vital_signs(
        db: Session, lab_id: int, patient_id: int,
        limit: int = 20, skip: int = 0,
    ) -> list[VitalSignsRecord]:
        return db.query(VitalSignsRecord).filter(
            VitalSignsRecord.patient_id == patient_id,
            VitalSignsRecord.lab_id == lab_id,
            ~VitalSignsRecord.is_deleted,
        ).order_by(VitalSignsRecord.recorded_at.desc()).offset(skip).limit(limit).all()

    @staticmethod
    def get_vital_signs_trend(
        db: Session, lab_id: int, patient_id: int, hours: int = 24,
    ) -> list[VitalSignsRecord]:
        cutoff = datetime.now(UTC) - timedelta(hours=hours)
        return db.query(VitalSignsRecord).filter(
            VitalSignsRecord.patient_id == patient_id,
            VitalSignsRecord.lab_id == lab_id,
            ~VitalSignsRecord.is_deleted,
            VitalSignsRecord.recorded_at >= cutoff,
        ).order_by(VitalSignsRecord.recorded_at.asc()).all()

    # ── Fluid Balance ────────────────────────────────────────────────────────────

    @staticmethod
    def record_fluid_balance(db: Session, lab_id: int, user_id: int, data: dict) -> FluidBalance:
        rec = FluidBalance(lab_id=lab_id, created_by=user_id, **_payload(FluidBalance, data))
        db.add(rec)
        db.flush()
        return rec

    @staticmethod
    def get_fluid_balance(
        db: Session, lab_id: int, patient_id: int,
        date_from: date | None = None, date_to: date | None = None,
    ) -> list[FluidBalance]:
        q = db.query(FluidBalance).filter(
            FluidBalance.patient_id == patient_id,
            FluidBalance.lab_id == lab_id,
            ~FluidBalance.is_deleted,
        )
        if date_from:
            q = q.filter(func.date(FluidBalance.recorded_at) >= date_from)
        if date_to:
            q = q.filter(func.date(FluidBalance.recorded_at) <= date_to)
        return q.order_by(FluidBalance.recorded_at.desc()).all()

    @staticmethod
    def get_net_balance(
        db: Session, lab_id: int, patient_id: int, balance_date: date,
    ) -> dict[str, Any]:
        records = db.query(FluidBalance).filter(
            FluidBalance.patient_id == patient_id,
            FluidBalance.lab_id == lab_id,
            ~FluidBalance.is_deleted,
            func.date(FluidBalance.recorded_at) == balance_date,
        ).all()
        # `amount_ml` is not a column — the physical column is `volume_ml`, so
        # every net-balance calculation raised AttributeError.
        total_intake = sum(r.volume_ml for r in records if r.balance_type == "intake" and r.volume_ml)
        total_output = sum(r.volume_ml for r in records if r.balance_type == "output" and r.volume_ml)
        return {
            "patient_id": patient_id,
            "date": balance_date.isoformat(),
            "total_intake_ml": total_intake,
            "total_output_ml": total_output,
            "net_balance_ml": round(total_intake - total_output, 1),
            "record_count": len(records),
        }

    # ── Pain Assessment ──────────────────────────────────────────────────────────

    @staticmethod
    def assess_pain(db: Session, lab_id: int, user_id: int, data: dict) -> PainAssessment:
        assessment = PainAssessment(lab_id=lab_id, created_by=user_id, **_payload(PainAssessment, data))
        db.add(assessment)
        db.flush()
        return assessment

    @staticmethod
    def get_pain_assessments(
        db: Session, lab_id: int, patient_id: int, limit: int = 20,
    ) -> list[PainAssessment]:
        return db.query(PainAssessment).filter(
            PainAssessment.patient_id == patient_id,
            PainAssessment.lab_id == lab_id,
            ~PainAssessment.is_deleted,
        ).order_by(PainAssessment.assessed_at.desc()).limit(limit).all()

    # ── Fall Risk Assessment ─────────────────────────────────────────────────────

    @staticmethod
    def assess_fall_risk(db: Session, lab_id: int, user_id: int, data: dict) -> FallRiskAssessment:
        assessment = FallRiskAssessment(lab_id=lab_id, created_by=user_id, **_payload(FallRiskAssessment, data))
        db.add(assessment)
        db.flush()
        return assessment

    @staticmethod
    def get_fall_risk_assessments(
        db: Session, lab_id: int, patient_id: int, limit: int = 10,
    ) -> list[FallRiskAssessment]:
        return db.query(FallRiskAssessment).filter(
            FallRiskAssessment.patient_id == patient_id,
            FallRiskAssessment.lab_id == lab_id,
            ~FallRiskAssessment.is_deleted,
        ).order_by(FallRiskAssessment.assessed_at.desc()).limit(limit).all()

    # ── Pressure Injury Assessment ───────────────────────────────────────────────

    @staticmethod
    def assess_pressure_injury(db: Session, lab_id: int, user_id: int, data: dict) -> PressureInjuryAssessment:
        assessment = PressureInjuryAssessment(lab_id=lab_id, created_by=user_id, **_payload(PressureInjuryAssessment, data))
        db.add(assessment)
        db.flush()
        return assessment

    @staticmethod
    def get_pressure_injury_assessments(
        db: Session, lab_id: int, patient_id: int, limit: int = 10,
    ) -> list[PressureInjuryAssessment]:
        return db.query(PressureInjuryAssessment).filter(
            PressureInjuryAssessment.patient_id == patient_id,
            PressureInjuryAssessment.lab_id == lab_id,
            ~PressureInjuryAssessment.is_deleted,
        ).order_by(PressureInjuryAssessment.assessed_at.desc()).limit(limit).all()

    # ── Nutrition Assessment ─────────────────────────────────────────────────────

    @staticmethod
    def assess_nutrition(db: Session, lab_id: int, user_id: int, data: dict) -> NutritionAssessment:
        assessment = NutritionAssessment(lab_id=lab_id, created_by=user_id, **_payload(NutritionAssessment, data))
        if assessment.height_cm and assessment.weight_kg and assessment.height_cm > 0:
            assessment.bmi = round(assessment.weight_kg / ((assessment.height_cm / 100) ** 2), 1)
        db.add(assessment)
        db.flush()
        return assessment

    @staticmethod
    def get_nutrition_assessments(
        db: Session, lab_id: int, patient_id: int, limit: int = 10,
    ) -> list[NutritionAssessment]:
        return db.query(NutritionAssessment).filter(
            NutritionAssessment.patient_id == patient_id,
            NutritionAssessment.lab_id == lab_id,
            ~NutritionAssessment.is_deleted,
        ).order_by(NutritionAssessment.assessed_at.desc()).limit(limit).all()

    # ── Care Plans ───────────────────────────────────────────────────────────────

    @staticmethod
    def create_care_plan(db: Session, lab_id: int, user_id: int, data: dict) -> NursingCarePlan:
        plan = NursingCarePlan(lab_id=lab_id, created_by=user_id, **_payload(NursingCarePlan, data))
        db.add(plan)
        db.flush()
        return plan

    @staticmethod
    def update_care_plan(
        db: Session, lab_id: int, user_id: int, plan_id: int, data: dict,
    ) -> NursingCarePlan:
        plan = db.query(NursingCarePlan).filter(
            NursingCarePlan.id == plan_id, NursingCarePlan.lab_id == lab_id,
            ~NursingCarePlan.is_deleted,
        ).first()
        if not plan:
            raise HTTPException(status_code=404, detail="Care plan not found")
        for k, v in _payload(NursingCarePlan, data).items():
            setattr(plan, k, v)
        plan.updated_by = user_id
        db.flush()
        return plan

    @staticmethod
    def get_care_plans(
        db: Session, lab_id: int, patient_id: int,
    ) -> list[NursingCarePlan]:
        return db.query(NursingCarePlan).filter(
            NursingCarePlan.patient_id == patient_id,
            NursingCarePlan.lab_id == lab_id,
            ~NursingCarePlan.is_deleted,
        ).order_by(NursingCarePlan.start_date.desc()).all()

    # ── Nursing Notes ────────────────────────────────────────────────────────────

    @staticmethod
    def create_nursing_note(db: Session, lab_id: int, user_id: int, data: dict) -> NursingNote:
        note = NursingNote(lab_id=lab_id, created_by=user_id, **_payload(NursingNote, data))
        db.add(note)
        db.flush()
        return note

    @staticmethod
    def get_nursing_notes(
        db: Session, lab_id: int, patient_id: int,
        note_type: str | None = None, limit: int = 50,
    ) -> list[NursingNote]:
        q = db.query(NursingNote).filter(
            NursingNote.patient_id == patient_id,
            NursingNote.lab_id == lab_id,
            ~NursingNote.is_deleted,
        )
        if note_type:
            q = q.filter(NursingNote.note_type == note_type)
        return q.order_by(NursingNote.written_at.desc()).limit(limit).all()

    @staticmethod
    def get_nursing_note(db: Session, lab_id: int, note_id: int) -> NursingNote:
        note = db.query(NursingNote).filter(
            NursingNote.id == note_id, NursingNote.lab_id == lab_id,
            ~NursingNote.is_deleted,
        ).first()
        if not note:
            raise HTTPException(status_code=404, detail="Nursing note not found")
        return note

    # ── Shift Management ─────────────────────────────────────────────────────────

    @staticmethod
    def start_shift(db: Session, lab_id: int, user_id: int, data: dict) -> NursingShift:
        existing = db.query(NursingShift).filter(
            NursingShift.nurse_id == user_id,
            NursingShift.clocked_out_at.is_(None),
            NursingShift.lab_id == lab_id,
            ~NursingShift.is_deleted,
        ).first()
        if existing:
            raise HTTPException(status_code=409, detail="Active shift already exists — end it first")
        now = datetime.now(UTC)
        # `start_time` is TIME and `clocked_in_at` TIMESTAMPTZ. The route used
        # to put a datetime into the TIME column; a shift is who clocked in,
        # when, and on which calendar day, so the server supplies all three.
        shift = NursingShift(
            lab_id=lab_id, created_by=user_id, nurse_id=user_id,
            start_time=now.timetz().replace(tzinfo=None),
            clocked_in_at=now, status="active",
            **_payload(NursingShift, data),
        )
        db.add(shift)
        db.flush()
        return shift

    @staticmethod
    def end_shift(db: Session, lab_id: int, user_id: int, shift_id: int) -> NursingShift:
        shift = db.query(NursingShift).filter(
            NursingShift.id == shift_id, NursingShift.lab_id == lab_id,
            ~NursingShift.is_deleted,
        ).first()
        if not shift:
            raise HTTPException(status_code=404, detail="Shift not found")
        if shift.clocked_out_at:
            raise HTTPException(status_code=409, detail="Shift already ended")
        now = datetime.now(UTC)
        shift.end_time = now.timetz().replace(tzinfo=None)
        shift.clocked_out_at = now
        shift.status = "completed"
        shift.updated_by = user_id
        db.flush()
        return shift

    # ── Shift Handover ───────────────────────────────────────────────────────────

    @staticmethod
    def create_shift_handover(db: Session, lab_id: int, user_id: int, data: dict) -> ShiftHandover:
        payload = _payload(ShiftHandover, data)
        payload.setdefault("from_nurse_id", user_id)
        handover = ShiftHandover(
            lab_id=lab_id, created_by=user_id,
            handover_at=datetime.now(UTC),   # NOT NULL, server-owned
            **payload,
        )
        db.add(handover)
        db.flush()
        return handover

    @staticmethod
    def get_shift_handovers(
        db: Session, lab_id: int, department: int | None = None, handover_date: date | None = None,
    ) -> list[ShiftHandover]:
        q = db.query(ShiftHandover).filter(
            ShiftHandover.lab_id == lab_id, ~ShiftHandover.is_deleted,
        )
        if handover_date:
            q = q.filter(func.date(ShiftHandover.handover_at) == handover_date)
        return q.order_by(ShiftHandover.created_at.desc()).all()

    @staticmethod
    def complete_shift_handover(
        db: Session, lab_id: int, user_id: int, handover_id: int,
    ) -> ShiftHandover:
        handover = db.query(ShiftHandover).filter(
            ShiftHandover.id == handover_id, ShiftHandover.lab_id == lab_id,
            ~ShiftHandover.is_deleted,
        ).first()
        if not handover:
            raise HTTPException(status_code=404, detail="Handover not found")
        handover.is_completed = True
        handover.completed_at = datetime.now(UTC)
        handover.updated_by = user_id
        db.flush()
        return handover

    # ── Checklists ───────────────────────────────────────────────────────────────

    @staticmethod
    def create_checklist(db: Session, lab_id: int, user_id: int, data: dict) -> ClinicalChecklist:
        payload = _payload(ClinicalChecklist, data)
        # `total_items` is NOT NULL and is a property of the items themselves,
        # so it is derived rather than trusted from the request body.
        payload["total_items"] = len(payload.get("items") or [])
        payload["completed_count"] = 0
        checklist = ClinicalChecklist(lab_id=lab_id, created_by=user_id, **payload)
        db.add(checklist)
        db.flush()
        return checklist

    @staticmethod
    def get_checklists(
        db: Session, lab_id: int, patient_id: int,
    ) -> list[ClinicalChecklist]:
        return db.query(ClinicalChecklist).filter(
            ClinicalChecklist.patient_id == patient_id,
            ClinicalChecklist.lab_id == lab_id,
            ~ClinicalChecklist.is_deleted,
        ).order_by(ClinicalChecklist.created_at.desc()).all()

    @staticmethod
    def update_checklist_item(
        db: Session, lab_id: int, user_id: int, checklist_id: int,
        item_index: int, completed: bool,
    ) -> ClinicalChecklist:
        checklist = db.query(ClinicalChecklist).filter(
            ClinicalChecklist.id == checklist_id, ClinicalChecklist.lab_id == lab_id,
            ~ClinicalChecklist.is_deleted,
        ).first()
        if not checklist:
            raise HTTPException(status_code=404, detail="Checklist not found")
        items = checklist.items or []
        if item_index < 0 or item_index >= len(items):
            raise HTTPException(status_code=422, detail="Invalid item index")
        items[item_index]["completed"] = completed
        if completed:
            items[item_index]["completed_by"] = user_id
            items[item_index]["completed_at"] = datetime.now(UTC).isoformat()
        else:
            items[item_index].pop("completed_by", None)
            items[item_index].pop("completed_at", None)
        checklist.items = items
        checklist.completed_count = sum(1 for i in items if i.get("completed", False))
        checklist.total_items = len(items)
        all_done = bool(items) and checklist.completed_count == len(items)
        if all_done:
            checklist.status = "completed"
            checklist.completed_by = user_id
            checklist.completed_at = datetime.now(UTC)
        checklist.updated_by = user_id
        db.flush()
        return checklist

    # ── Delegation ───────────────────────────────────────────────────────────────

    @staticmethod
    def delegate_task(db: Session, lab_id: int, user_id: int, data: dict) -> Delegation:
        delegation = Delegation(
            lab_id=lab_id, created_by=user_id, delegated_by=user_id,
            delegated_at=datetime.now(UTC),   # NOT NULL, server-owned
            **_payload(Delegation, data),
        )
        db.add(delegation)
        db.flush()
        return delegation

    @staticmethod
    def accept_delegation(db: Session, lab_id: int, user_id: int, delegation_id: int) -> Delegation:
        del_rec = db.query(Delegation).filter(
            Delegation.id == delegation_id, Delegation.lab_id == lab_id,
            ~Delegation.is_deleted,
        ).first()
        if not del_rec:
            raise HTTPException(status_code=404, detail="Delegation not found")
        if del_rec.delegated_to != user_id:
            raise HTTPException(status_code=403, detail="This delegation is not addressed to you")
        del_rec.status = DelegationStatus.ACCEPTED
        del_rec.accepted_at = datetime.now(UTC)
        del_rec.updated_by = user_id
        db.flush()
        return del_rec

    @staticmethod
    def complete_delegation(db: Session, lab_id: int, user_id: int, delegation_id: int) -> Delegation:
        del_rec = db.query(Delegation).filter(
            Delegation.id == delegation_id, Delegation.lab_id == lab_id,
            ~Delegation.is_deleted,
        ).first()
        if not del_rec:
            raise HTTPException(status_code=404, detail="Delegation not found")
        del_rec.status = DelegationStatus.COMPLETED
        del_rec.completed_at = datetime.now(UTC)
        del_rec.updated_by = user_id
        db.flush()
        return del_rec

    # ── Escalation ───────────────────────────────────────────────────────────────

    @staticmethod
    def escalate(db: Session, lab_id: int, user_id: int, data: dict) -> EscalationRecord:
        rec = EscalationRecord(
            lab_id=lab_id, created_by=user_id, escalated_by=user_id,
            escalated_at=datetime.now(UTC),   # NOT NULL, server-owned
            **_payload(EscalationRecord, data),
        )
        db.add(rec)
        db.flush()
        return rec

    @staticmethod
    def acknowledge_escalation(db: Session, lab_id: int, user_id: int, escalation_id: int) -> EscalationRecord:
        rec = db.query(EscalationRecord).filter(
            EscalationRecord.id == escalation_id, EscalationRecord.lab_id == lab_id,
            ~EscalationRecord.is_deleted,
        ).first()
        if not rec:
            raise HTTPException(status_code=404, detail="Escalation not found")
        rec.status = "acknowledged"
        rec.acknowledged_at = datetime.now(UTC)
        rec.updated_by = user_id
        db.flush()
        return rec

    @staticmethod
    def resolve_escalation(
        db: Session, lab_id: int, user_id: int, escalation_id: int,
        resolution_notes: str | None = None, outcome: str | None = None,
    ) -> EscalationRecord:
        rec = db.query(EscalationRecord).filter(
            EscalationRecord.id == escalation_id, EscalationRecord.lab_id == lab_id,
            ~EscalationRecord.is_deleted,
        ).first()
        if not rec:
            raise HTTPException(status_code=404, detail="Escalation not found")
        rec.status = "resolved"
        rec.resolved_at = datetime.now(UTC)
        # `resolved_by` and `resolution` are not columns: the clinician who
        # closed the escalation and their account of how were both discarded.
        # `updated_by` and `resolution_notes` are the columns that exist.
        if resolution_notes is not None:
            rec.resolution_notes = resolution_notes
        if outcome is not None:
            rec.outcome = outcome
        rec.updated_by = user_id
        db.flush()
        return rec

    # ── Medication Schedule ──────────────────────────────────────────────────────

    @staticmethod
    def get_medication_schedule(
        db: Session, lab_id: int, patient_id: int,
    ) -> list[dict[str, Any]]:
        from app.ehr.models.medication import MedicationAdministration, MedicationRequest

        requests = db.query(MedicationRequest).filter(
            MedicationRequest.patient_id == patient_id,
            MedicationRequest.lab_id == lab_id,
            ~MedicationRequest.is_deleted,
            MedicationRequest.status == "active",
        ).all()
        schedule = []
        for req in requests:
            administrations = db.query(MedicationAdministration).filter(
                MedicationAdministration.medication_request_id == req.id,
                MedicationAdministration.patient_id == patient_id,
            ).order_by(MedicationAdministration.administration_time.desc()).limit(5).all()
            schedule.append({
                "request_id": req.id,
                "medication_name": req.medication_name,
                "medication_name_ar": req.medication_name_ar,
                "dosage_instruction": req.dosage_instruction,
                "route": req.route,
                "frequency": req.frequency,
                "status": req.status,
                "recent_administrations": [
                    {"time": a.administration_time.isoformat() if a.administration_time else None, "status": a.status}
                    for a in administrations
                ],
            })
        return schedule

    @staticmethod
    def get_missed_doses(
        db: Session, lab_id: int, patient_id: int, dose_date: date | None = None,
    ) -> list[dict[str, Any]]:
        from app.ehr.models.medication import MedicationAdministration, MedicationRequest

        dose_date = dose_date or date.today()
        requests = db.query(MedicationRequest).filter(
            MedicationRequest.patient_id == patient_id,
            MedicationRequest.lab_id == lab_id,
            ~MedicationRequest.is_deleted,
            MedicationRequest.status == "active",
        ).all()
        missed = []
        for req in requests:
            administered = db.query(MedicationAdministration).filter(
                MedicationAdministration.medication_request_id == req.id,
                MedicationAdministration.patient_id == patient_id,
                func.date(MedicationAdministration.administration_time) == dose_date,
                MedicationAdministration.status == "completed",
            ).count()
            if administered == 0:
                missed.append({
                    "request_id": req.id,
                    "medication_name": req.medication_name,
                    "dosage_instruction": req.dosage_instruction,
                    "route": req.route,
                    "frequency": req.frequency,
                    "scheduled_date": dose_date.isoformat(),
                    "status": "missed",
                })
        return missed

    @staticmethod
    def get_vitals_due(
        db: Session, lab_id: int, unit_filter: str | None = None, window_minutes: int = 60,
    ) -> list[dict[str, Any]]:
        cutoff = datetime.now(UTC) - timedelta(minutes=window_minutes)
        patients_with_recent = db.query(VitalSignsRecord.patient_id).filter(
            VitalSignsRecord.lab_id == lab_id,
            VitalSignsRecord.recorded_at >= cutoff,
        ).distinct().subquery()
        assigned_ids = db.query(PatientAssignment.patient_id).filter(
            PatientAssignment.unassigned_at.is_(None),
            PatientAssignment.lab_id == lab_id,
        ).distinct()
        overdue = assigned_ids.except_(db.query(patients_with_recent.c.patient_id)).all()
        return [{"patient_id": pid[0]} for pid in overdue]

    @staticmethod
    def get_shift_summary(db: Session, lab_id: int, shift_id: str) -> dict[str, Any]:
        shift = db.query(NursingShift).filter(
            NursingShift.id == shift_id, NursingShift.lab_id == lab_id,
        ).first()
        if not shift:
            raise HTTPException(status_code=404, detail="Shift not found")
        tasks = db.query(NursingTask).filter(
            NursingTask.lab_id == lab_id,
            ~NursingTask.is_deleted,
            func.date(NursingTask.due_at) == shift.shift_date,
        )
        return {
            "shift_id": shift.id,
            "nurse_id": shift.nurse_id,
            "shift_type": shift.shift_type,
            "shift_date": shift.shift_date.isoformat(),
            "start_time": shift.start_time.isoformat() if shift.start_time else None,
            "end_time": shift.end_time.isoformat() if shift.end_time else None,
            "patient_count": shift.patient_count,
            "tasks_assigned": tasks.count(),
            "tasks_completed": tasks.filter(NursingTask.status == "completed").count(),
            "tasks_pending": tasks.filter(NursingTask.status.in_(["pending", "in_progress"])).count(),
        }
