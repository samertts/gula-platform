from __future__ import annotations

import logging
from datetime import date, datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, field_validator
from sqlalchemy.orm import Session

from app._compat import UTC
from app.database import get_db
from app.models.lab_user import LabUser
from app.nursing.clinical_read_gate import ClinicalNursingTaskReadDenied, ClinicalNursingTaskReadGate
from app.nursing.coordination import CareCoordinatorService
from app.nursing.medication import MedicationAdminService
from app.nursing.models import (
    Delegation,
    EscalationRecord,
    NursingShift,
    NursingTask,
    ShiftHandover,
)
from app.nursing.services import NursingService
from app.security.dependencies import get_current_user
from app.security.legacy_referral import block_legacy_referral_write

logger = logging.getLogger("gula.nursing.routes")

router = APIRouter(prefix="/nursing", tags=["nursing"])

_NURSING_NS = "nursing"


def _model_to_dict(model_instance) -> dict[str, Any]:
    exclude = {"lab_id", "is_deleted", "deleted_at", "version"}
    result = {}
    for c in model_instance.__table__.columns:
        if c.key in exclude:
            continue
        val = getattr(model_instance, c.key)
        if isinstance(val, datetime) or (isinstance(val, date) and not isinstance(val, datetime)):
            val = val.isoformat()
        result[c.key] = val
    return result


def _paginated_response(items: list, total: int, skip: int, limit: int) -> dict:
    return {"items": items, "total": total, "skip": skip, "limit": limit}


# ══════════════════════════════════════════════════════════════════════════════
# Schemas
# ══════════════════════════════════════════════════════════════════════════════


class AssignPatientRequest(BaseModel):
    nurse_id: str
    patient_id: int
    assignment_type: str = "primary"
    department_id: int | None = None
    encounter_id: str | None = None
    notes: str | None = None


class UnassignPatientRequest(BaseModel):
    nurse_id: str
    patient_id: int


class TaskCreate(BaseModel):
    patient_id: int
    encounter_id: str | None = None
    assigned_to: str | None = None
    task_type: str
    description: str
    priority: str = "medium"
    status: str = "pending"
    scheduled_time: datetime | None = None
    due_time: datetime | None = None
    is_recurring: bool = False
    recurrence_rule: dict[str, Any] | None = None
    clinical_instruction: str | None = None
    notes: str | None = None


class TaskUpdate(BaseModel):
    description: str | None = None
    priority: str | None = None
    status: str | None = None
    scheduled_time: datetime | None = None
    due_time: datetime | None = None
    assigned_to: str | None = None
    clinical_instruction: str | None = None
    notes: str | None = None


class TaskComplete(BaseModel):
    patient_response: str | None = None
    notes: str | None = None


class TaskDefer(BaseModel):
    new_due_time: datetime | None = None
    reason: str | None = None


class VitalSignsCreate(BaseModel):
    patient_id: int
    encounter_id: str | None = None
    recorded_at: datetime | None = None
    bp_systolic: int | None = None
    bp_diastolic: int | None = None
    heart_rate: int | None = None
    respiratory_rate: int | None = None
    temperature: float | None = None
    temperature_site: str | None = None
    oxygen_saturation: float | None = None
    oxygen_device: str | None = None
    oxygen_flow_rate: float | None = None
    height_cm: float | None = None
    weight_kg: float | None = None
    head_circumference_cm: float | None = None
    pain_score: int | None = None
    consciousness_level: str | None = None
    gcs_eye: int | None = None
    gcs_verbal: int | None = None
    gcs_motor: int | None = None
    pupil_left_size: float | None = None
    pupil_left_reaction: str | None = None
    pupil_right_size: float | None = None
    pupil_right_reaction: str | None = None
    blood_glucose: float | None = None
    glucose_context: str | None = None
    notes: str | None = None


class FluidBalanceCreate(BaseModel):
    patient_id: int
    encounter_id: str | None = None
    recorded_at: datetime | None = None
    balance_type: str
    category: str
    fluid_name: str | None = None
    amount_ml: float
    route: str | None = None
    start_time: datetime | None = None
    end_time: datetime | None = None
    infusion_rate: float | None = None
    bag_volume: float | None = None
    bag_number: str | None = None
    notes: str | None = None


class PainAssessmentCreate(BaseModel):
    patient_id: int
    encounter_id: str | None = None
    assessed_at: datetime | None = None
    pain_score: int
    pain_level: str | None = None
    pain_location: str | None = None
    pain_quality: str | None = None
    pain_pattern: str | None = None
    onset: str | None = None
    duration: str | None = None
    aggravating_factors: str | None = None
    relieving_factors: str | None = None
    pain_goal: int | None = None
    interventions_tried: str | None = None
    effectiveness: str | None = None
    non_verbal_indicators: str | None = None
    notes: str | None = None

    @field_validator("pain_score")
    @classmethod
    def validate_score(cls, v):
        if v < 0 or v > 10:
            raise ValueError("Pain score must be between 0 and 10")
        return v


class FallRiskCreate(BaseModel):
    patient_id: int
    encounter_id: str | None = None
    assessed_at: datetime | None = None
    total_score: int
    risk_level: str
    age_ge_65: bool = False
    fall_history_12mo: bool = False
    secondary_condition: bool = False
    assistive_device: bool = False
    iv_or_heparin_lock: bool = False
    gait_impaired: bool = False
    mental_status: str | None = None
    elimination: str | None = None
    medications: str | None = None
    interventions_ordered: list[str] | None = None
    notes: str | None = None


class PressureInjuryCreate(BaseModel):
    patient_id: int
    encounter_id: str | None = None
    assessed_at: datetime | None = None
    stage: str
    anatomical_location: str | None = None
    length_cm: float | None = None
    width_cm: float | None = None
    depth_cm: float | None = None
    wound_bed: str | None = None
    exudate_type: str | None = None
    exudate_amount: str | None = None
    wound_edges: str | None = None
    periwound_skin: str | None = None
    infection_signs: list[str] | None = None
    wound_culture: str | None = None
    dressing_type: str | None = None
    dressing_frequency: str | None = None
    treatment_plan: str | None = None
    photographs: list[str] | None = None
    notes: str | None = None


class NutritionCreate(BaseModel):
    patient_id: int
    encounter_id: str | None = None
    assessed_at: datetime | None = None
    nutrition_status: str
    weight_kg: float | None = None
    height_cm: float | None = None
    usual_weight_kg: float | None = None
    weight_change_1mo_kg: float | None = None
    appetite: str | None = None
    dietary_restrictions: list[str] | None = None
    chewing_difficulty: bool = False
    swallowing_difficulty: bool = False
    dysphagia_risk: bool = False
    fluid_restriction_ml: float | None = None
    calorie_target_kcal: float | None = None
    protein_target_g: float | None = None
    feeding_method: str | None = None
    supplements: list[str] | None = None
    diet_type: str | None = None
    notes: str | None = None


class CarePlanCreate(BaseModel):
    patient_id: int
    encounter_id: str | None = None
    nursing_diagnosis: str
    goals: list[dict[str, Any]] = []
    interventions: list[dict[str, Any]] = []
    evaluation: str | None = None
    start_date: datetime
    review_date: datetime | None = None
    next_review: datetime | None = None
    status: str = "active"
    notes: str | None = None


class CarePlanUpdate(BaseModel):
    nursing_diagnosis: str | None = None
    goals: list[dict[str, Any]] | None = None
    interventions: list[dict[str, Any]] | None = None
    evaluation: str | None = None
    review_date: datetime | None = None
    next_review: datetime | None = None
    status: str | None = None
    notes: str | None = None


class NursingNoteCreate(BaseModel):
    patient_id: int
    encounter_id: str | None = None
    shift_id: str | None = None
    note_type: str
    subjective: str | None = None
    objective: str | None = None
    assessment: str | None = None
    intervention: str | None = None
    response: str | None = None
    evaluation: str | None = None
    plan: str | None = None
    attachments: list[dict[str, Any]] | None = None
    patient_education: str | None = None
    is_confidential: bool = False


class ShiftStartRequest(BaseModel):
    shift_type: str
    shift_date: date
    department_id: int | None = None
    patient_count: int = 0
    assigned_patients: list[int] | None = None
    notes: str | None = None


class ShiftEndRequest(BaseModel):
    shift_id: str


class HandoverCreate(BaseModel):
    from_shift_id: str | None = None
    to_shift_id: str | None = None
    from_nurse_id: str
    to_nurse_id: str
    handover_type: str
    shift_date: date
    patient_summaries: list[dict[str, Any]] = []
    pending_tasks: list[dict[str, Any]] = []
    critical_alerts: list[dict[str, Any]] = []
    medication_changes: list[dict[str, Any]] = []
    equipment_issues: list[dict[str, Any]] = []
    staffing_issues: str | None = None
    notes: str | None = None


class ChecklistCreate(BaseModel):
    patient_id: int
    encounter_id: str | None = None
    checklist_type: str
    items: list[dict[str, Any]] = []
    status: str = "draft"
    notes: str | None = None


class ChecklistItemUpdate(BaseModel):
    completed: bool


class DelegationCreate(BaseModel):
    task_id: str | None = None
    delegated_to: str
    reason: str | None = None
    scope_notes: str | None = None
    supervising_instructions: str | None = None


class EscalationCreate(BaseModel):
    patient_id: int
    encounter_id: str | None = None
    escalated_to: str | None = None
    reason: str
    severity: str
    category: str
    notes: str | None = None


class EscalationResolve(BaseModel):
    resolution: str | None = None


class MedicationVerifyRequest(BaseModel):
    right_patient: bool = False
    right_drug: bool = False
    right_dose: bool = False
    right_route: bool = False
    right_time: bool = False


class MedicationAdminRecord(BaseModel):
    medication_request_id: str | None = None
    patient_id: int
    encounter_id: str | None = None
    medication_code: str | None = None
    medication_code_system: str | None = None
    medication_name: str
    medication_name_ar: str | None = None
    status: str = "completed"
    dose_value: str | None = None
    dose_unit: str | None = None
    route: str | None = None
    site: str | None = None
    method: str | None = None
    administration_time: datetime
    reason_not_given: str | None = None
    note: str | None = None


class MedicationSignRequest(BaseModel):
    medication_admin_id: str


class PhysicianMessageRequest(BaseModel):
    physician_id: str
    patient_id: int
    subject: str
    body: str
    priority: str = "normal"


class LabRequest(BaseModel):
    patient_id: int
    tests: list[dict[str, Any]]


class RadiologyRequest(BaseModel):
    patient_id: int
    exam_type: str
    urgency: str = "routine"


class PharmacyRequest(BaseModel):
    patient_id: int
    medication: str
    dose: str
    route: str


class ReferralRequest(BaseModel):
    patient_id: int
    to_specialty: str
    reason: str
    urgency: str = "routine"


class DischargePlanRequest(BaseModel):
    patient_id: int
    expected_date: date
    discharge_needs: dict[str, Any] | None = None


class FamilyCommunicationRequest(BaseModel):
    patient_id: int
    family_contact: str
    message: str


class HomeCareHandoverRequest(BaseModel):
    patient_id: int
    home_care_provider: str
    summary: str


# ══════════════════════════════════════════════════════════════════════════════
# Dashboard
# ══════════════════════════════════════════════════════════════════════════════


@router.get("/dashboard", summary="Nurse dashboard")
def nurse_dashboard(
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return NursingService.get_nurse_dashboard(db, current_user.lab_id, str(current_user.id))


@router.get("/dashboard/shift-summary", summary="Active shift summary")
def shift_summary(
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    shift = db.query(NursingShift).filter(
        NursingShift.nurse_id == str(current_user.id),
        NursingShift.end_time.is_(None),
        NursingShift.lab_id == current_user.lab_id,
    ).first()
    if not shift:
        return {"active_shift": False, "message": "لا يوجد وردية نشطة"}
    return _model_to_dict(shift)


# ══════════════════════════════════════════════════════════════════════════════
# Patient Assignments
# ══════════════════════════════════════════════════════════════════════════════


@router.get("/patients", summary="Assigned patients")
def list_assigned_patients(
    nurse_id: str | None = Query(None),
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    nurse = nurse_id or str(current_user.id)
    return NursingService.get_assigned_patients(db, current_user.lab_id, nurse)


@router.post("/patients/assign", summary="Assign patient to nurse", status_code=201)
def assign_patient(
    body: AssignPatientRequest,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    assignment = NursingService.assign_patient(
        db, current_user.lab_id, current_user.id,
        body.nurse_id, body.patient_id, body.assignment_type,
        body.department_id, body.encounter_id, body.notes,
    )
    return _model_to_dict(assignment)


@router.post("/patients/unassign", summary="Unassign patient from nurse")
def unassign_patient(
    body: UnassignPatientRequest,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    NursingService.unassign_patient(db, current_user.lab_id, current_user.id, body.nurse_id, body.patient_id)
    return {"detail": "Patient unassigned", "detail_ar": "تم إلغاء تعيين المريض"}


# ══════════════════════════════════════════════════════════════════════════════
# Tasks
# ══════════════════════════════════════════════════════════════════════════════


@router.get("/tasks", summary="List nursing tasks")
def list_tasks(
    assigned_to: str | None = Query(None),
    patient_id: int | None = Query(None),
    status: str | None = Query(None),
    task_type: str | None = Query(None),
    date_from: date | None = Query(None),
    date_to: date | None = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    tasks = NursingService.get_tasks(
        db, current_user.lab_id, assigned_to, patient_id,
        status, task_type, date_from, date_to, skip, limit,
    )
    return _paginated_response(
        [_model_to_dict(t) for t in tasks], len(tasks), skip, limit,
    )


@router.get("/clinical/my-tasks", summary="Read only the current nurse's clinical tasks")
def list_clinical_my_tasks(
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Return at most fifty assigned tasks after the clinical gate succeeds.

    The endpoint deliberately exposes no patient, assignment, status, or task
    type filter: callers can read only the current legacy user's own task list.
    Existing task creation and state-change endpoints remain outside this
    contract.
    """
    try:
        ClinicalNursingTaskReadGate().authorize(db=db, lab_user=current_user)
    except ClinicalNursingTaskReadDenied:
        raise HTTPException(status_code=403, detail="Clinical nursing access is not permitted")

    tasks = NursingService.get_tasks(
        db=db,
        lab_id=current_user.lab_id,
        nurse_id=str(current_user.id),
        limit=50,
    )
    return _paginated_response([_model_to_dict(task) for task in tasks], len(tasks), 0, 50)


@router.post("/tasks", summary="Create nursing task", status_code=201)
def create_task(
    body: TaskCreate,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    task = NursingService.create_task(db, current_user.lab_id, current_user.id, body.model_dump(exclude_none=True))
    return _model_to_dict(task)


@router.put("/tasks/{task_id}", summary="Update nursing task")
def update_task(
    task_id: str,
    body: TaskUpdate,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    data = dict(body.model_dump(exclude_none=True).items())
    if not data:
        raise HTTPException(status_code=400, detail="No fields to update")
    task = NursingService.update_task(db, current_user.lab_id, current_user.id, task_id, data)
    return _model_to_dict(task)


@router.put("/tasks/{task_id}/complete", summary="Complete nursing task")
def complete_task(
    task_id: str,
    body: TaskComplete,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    task = NursingService.complete_task(
        db, current_user.lab_id, current_user.id, task_id, body.patient_response, body.notes,
    )
    return _model_to_dict(task)


@router.put("/tasks/{task_id}/defer", summary="Defer nursing task")
def defer_task(
    task_id: str,
    body: TaskDefer,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    task = NursingService.defer_task(
        db, current_user.lab_id, current_user.id, task_id, body.new_due_time, body.reason,
    )
    return _model_to_dict(task)


@router.get("/tasks/overdue", summary="Overdue tasks")
def list_overdue_tasks(
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    now = datetime.now(UTC)
    tasks = db.query(NursingTask).filter(
        NursingTask.assigned_to == str(current_user.id),
        NursingTask.status.in_(["pending", "in_progress"]),
        NursingTask.due_time <= now,
        NursingTask.lab_id == current_user.lab_id,
        ~NursingTask.is_deleted,
    ).order_by(NursingTask.due_time.asc()).all()
    return {"items": [_model_to_dict(t) for t in tasks], "total": len(tasks)}


@router.get("/tasks/patient/{patient_id}", summary="Tasks by patient")
def tasks_by_patient(
    patient_id: int,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    tasks = NursingService.get_tasks_by_patient(db, current_user.lab_id, patient_id)
    return {"items": [_model_to_dict(t) for t in tasks], "total": len(tasks)}


# ══════════════════════════════════════════════════════════════════════════════
# Vital Signs
# ══════════════════════════════════════════════════════════════════════════════


@router.post("/vital-signs", summary="Record vital signs", status_code=201)
def record_vital_signs(
    body: VitalSignsCreate,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    data = body.model_dump(exclude_none=True)
    data["recorded_by"] = str(current_user.id)
    if "recorded_at" not in data:
        data["recorded_at"] = datetime.now(UTC)
    record = NursingService.record_vital_signs(db, current_user.lab_id, current_user.id, data)
    return _model_to_dict(record)


@router.get("/vital-signs/{patient_id}", summary="Get vital signs for patient")
def get_vital_signs(
    patient_id: int,
    limit: int = Query(20, ge=1, le=100),
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    records = NursingService.get_vital_signs(db, current_user.lab_id, patient_id, limit)
    return {"items": [_model_to_dict(r) for r in records], "total": len(records)}


@router.get("/vital-signs/{patient_id}/trend", summary="Vital signs trend")
def vital_signs_trend(
    patient_id: int,
    hours: int = Query(24, ge=1, le=168),
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    records = NursingService.get_vital_signs_trend(db, current_user.lab_id, patient_id, hours)
    return {"items": [_model_to_dict(r) for r in records], "total": len(records), "hours": hours}


@router.get("/vitals-due", summary="Patients with vitals due")
def vitals_due(
    window_minutes: int = Query(60, ge=15, le=480),
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    overdue = NursingService.get_vitals_due(db, current_user.lab_id, window_minutes=window_minutes)
    return {"items": overdue, "total": len(overdue)}


# ══════════════════════════════════════════════════════════════════════════════
# Fluid Balance
# ══════════════════════════════════════════════════════════════════════════════


@router.post("/fluid-balance", summary="Record fluid balance", status_code=201)
def record_fluid_balance(
    body: FluidBalanceCreate,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    data = body.model_dump(exclude_none=True)
    data["recorded_by"] = str(current_user.id)
    rec = NursingService.record_fluid_balance(db, current_user.lab_id, current_user.id, data)
    return _model_to_dict(rec)


@router.get("/fluid-balance/{patient_id}", summary="Get fluid balance records")
def get_fluid_balance(
    patient_id: int,
    date_from: date | None = Query(None),
    date_to: date | None = Query(None),
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    records = NursingService.get_fluid_balance(db, current_user.lab_id, patient_id, date_from, date_to)
    return {"items": [_model_to_dict(r) for r in records], "total": len(records)}


@router.get("/fluid-balance/{patient_id}/net/{balance_date}", summary="Net fluid balance for date")
def net_fluid_balance(
    patient_id: int,
    balance_date: date,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return NursingService.get_net_balance(db, current_user.lab_id, patient_id, balance_date)


# ══════════════════════════════════════════════════════════════════════════════
# Assessments
# ══════════════════════════════════════════════════════════════════════════════


@router.post("/assessments/pain", summary="Record pain assessment", status_code=201)
def assess_pain(
    body: PainAssessmentCreate,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    data = body.model_dump(exclude_none=True)
    data["assessed_by"] = str(current_user.id)
    assessment = NursingService.assess_pain(db, current_user.lab_id, current_user.id, data)
    return _model_to_dict(assessment)


@router.get("/assessments/pain/{patient_id}", summary="Get pain assessments")
def get_pain_assessments(
    patient_id: int,
    limit: int = Query(20, ge=1, le=100),
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    assessments = NursingService.get_pain_assessments(db, current_user.lab_id, patient_id, limit)
    return {"items": [_model_to_dict(a) for a in assessments], "total": len(assessments)}


@router.post("/assessments/fall-risk", summary="Record fall risk assessment", status_code=201)
def assess_fall_risk(
    body: FallRiskCreate,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    data = body.model_dump(exclude_none=True)
    data["assessed_by"] = str(current_user.id)
    assessment = NursingService.assess_fall_risk(db, current_user.lab_id, current_user.id, data)
    return _model_to_dict(assessment)


@router.get("/assessments/fall-risk/{patient_id}", summary="Get fall risk assessments")
def get_fall_risk_assessments(
    patient_id: int,
    limit: int = Query(10, ge=1, le=50),
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    assessments = NursingService.get_fall_risk_assessments(db, current_user.lab_id, patient_id, limit)
    return {"items": [_model_to_dict(a) for a in assessments], "total": len(assessments)}


@router.post("/assessments/pressure-injury", summary="Record pressure injury assessment", status_code=201)
def assess_pressure_injury(
    body: PressureInjuryCreate,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    data = body.model_dump(exclude_none=True)
    data["assessed_by"] = str(current_user.id)
    assessment = NursingService.assess_pressure_injury(db, current_user.lab_id, current_user.id, data)
    return _model_to_dict(assessment)


@router.get("/assessments/pressure-injury/{patient_id}", summary="Get pressure injury assessments")
def get_pressure_injury_assessments(
    patient_id: int,
    limit: int = Query(10, ge=1, le=50),
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    assessments = NursingService.get_pressure_injury_assessments(db, current_user.lab_id, patient_id, limit)
    return {"items": [_model_to_dict(a) for a in assessments], "total": len(assessments)}


@router.post("/assessments/nutrition", summary="Record nutrition assessment", status_code=201)
def assess_nutrition(
    body: NutritionCreate,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    data = body.model_dump(exclude_none=True)
    data["assessed_by"] = str(current_user.id)
    assessment = NursingService.assess_nutrition(db, current_user.lab_id, current_user.id, data)
    return _model_to_dict(assessment)


@router.get("/assessments/nutrition/{patient_id}", summary="Get nutrition assessments")
def get_nutrition_assessments(
    patient_id: int,
    limit: int = Query(10, ge=1, le=50),
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    assessments = NursingService.get_nutrition_assessments(db, current_user.lab_id, patient_id, limit)
    return {"items": [_model_to_dict(a) for a in assessments], "total": len(assessments)}


# ══════════════════════════════════════════════════════════════════════════════
# Care Plans
# ══════════════════════════════════════════════════════════════════════════════


@router.get("/care-plans/{patient_id}", summary="Get care plans for patient")
def get_care_plans(
    patient_id: int,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    plans = NursingService.get_care_plans(db, current_user.lab_id, patient_id)
    return {"items": [_model_to_dict(p) for p in plans], "total": len(plans)}


@router.post("/care-plans", summary="Create care plan", status_code=201)
def create_care_plan(
    body: CarePlanCreate,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    data = body.model_dump(exclude_none=True)
    data["created_by"] = str(current_user.id)
    plan = NursingService.create_care_plan(db, current_user.lab_id, current_user.id, data)
    return _model_to_dict(plan)


@router.put("/care-plans/{plan_id}", summary="Update care plan")
def update_care_plan(
    plan_id: str,
    body: CarePlanUpdate,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    data = dict(body.model_dump(exclude_none=True).items())
    if not data:
        raise HTTPException(status_code=400, detail="No fields to update")
    plan = NursingService.update_care_plan(db, current_user.lab_id, current_user.id, plan_id, data)
    return _model_to_dict(plan)


# ══════════════════════════════════════════════════════════════════════════════
# Notes
# ══════════════════════════════════════════════════════════════════════════════


@router.post("/notes", summary="Create nursing note", status_code=201)
def create_nursing_note(
    body: NursingNoteCreate,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    data = body.model_dump(exclude_none=True)
    data["documented_by"] = str(current_user.id)
    data["documentation_time"] = datetime.now(UTC)
    note = NursingService.create_nursing_note(db, current_user.lab_id, current_user.id, data)
    return _model_to_dict(note)


@router.get("/notes/{patient_id}", summary="Get nursing notes for patient")
def get_nursing_notes(
    patient_id: int,
    note_type: str | None = Query(None),
    limit: int = Query(50, ge=1, le=200),
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    notes = NursingService.get_nursing_notes(db, current_user.lab_id, patient_id, note_type, limit)
    return {"items": [_model_to_dict(n) for n in notes], "total": len(notes)}


@router.get("/notes/detail/{note_id}", summary="Get nursing note by ID")
def get_nursing_note(
    note_id: str,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    note = NursingService.get_nursing_note(db, current_user.lab_id, note_id)
    return _model_to_dict(note)


# ══════════════════════════════════════════════════════════════════════════════
# Shift Management
# ══════════════════════════════════════════════════════════════════════════════


@router.post("/shifts/start", summary="Start a nursing shift", status_code=201)
def start_shift(
    body: ShiftStartRequest,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    data = body.model_dump(exclude_none=True)
    data.setdefault("nurse_id", str(current_user.id))
    data["start_time"] = datetime.now(UTC)
    shift = NursingService.start_shift(db, current_user.lab_id, current_user.id, data)
    return _model_to_dict(shift)


@router.post("/shifts/end", summary="End a nursing shift")
def end_shift(
    body: ShiftEndRequest,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    shift = NursingService.end_shift(db, current_user.lab_id, current_user.id, body.shift_id)
    return _model_to_dict(shift)


@router.post("/handover", summary="Create shift handover", status_code=201)
def create_handover(
    body: HandoverCreate,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    data = body.model_dump(exclude_none=True)
    handover = NursingService.create_shift_handover(db, current_user.lab_id, current_user.id, data)
    return _model_to_dict(handover)


@router.get("/handover", summary="List shift handovers")
def list_handovers(
    department: int | None = Query(None),
    handover_date: date | None = Query(None),
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    handovers = NursingService.get_shift_handovers(db, current_user.lab_id, department, handover_date)
    return {"items": [_model_to_dict(h) for h in handovers], "total": len(handovers)}


@router.get("/handover/{handover_id}", summary="Get handover by ID")
def get_handover(
    handover_id: str,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    handover = db.query(ShiftHandover).filter(
        ShiftHandover.id == handover_id,
        ShiftHandover.lab_id == current_user.lab_id,
        ~ShiftHandover.is_deleted,
    ).first()
    if not handover:
        raise HTTPException(status_code=404, detail="Handover not found")
    return _model_to_dict(handover)


@router.put("/handover/{handover_id}/complete", summary="Complete shift handover")
def complete_handover(
    handover_id: str,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    handover = NursingService.complete_shift_handover(db, current_user.lab_id, current_user.id, handover_id)
    return _model_to_dict(handover)


# ══════════════════════════════════════════════════════════════════════════════
# Checklists
# ══════════════════════════════════════════════════════════════════════════════


@router.post("/checklists", summary="Create clinical checklist", status_code=201)
def create_checklist(
    body: ChecklistCreate,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    data = body.model_dump(exclude_none=True)
    data["created_by"] = str(current_user.id)
    checklist = NursingService.create_checklist(db, current_user.lab_id, current_user.id, data)
    return _model_to_dict(checklist)


@router.get("/checklists/{patient_id}", summary="Get checklists for patient")
def get_checklists(
    patient_id: int,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    checklists = NursingService.get_checklists(db, current_user.lab_id, patient_id)
    return {"items": [_model_to_dict(c) for c in checklists], "total": len(checklists)}


@router.put("/checklists/{checklist_id}/items/{item_idx}", summary="Update checklist item")
def update_checklist_item(
    checklist_id: str,
    item_idx: int,
    body: ChecklistItemUpdate,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    checklist = NursingService.update_checklist_item(
        db, current_user.lab_id, current_user.id, checklist_id, item_idx, body.completed,
    )
    return _model_to_dict(checklist)


# ══════════════════════════════════════════════════════════════════════════════
# Delegations & Escalations
# ══════════════════════════════════════════════════════════════════════════════


@router.post("/delegations", summary="Delegate a task", status_code=201)
def create_delegation(
    body: DelegationCreate,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    data = body.model_dump(exclude_none=True)
    delegation = NursingService.delegate_task(db, current_user.lab_id, current_user.id, data)
    return _model_to_dict(delegation)


@router.get("/delegations", summary="List delegations")
def list_delegations(
    status: str | None = Query(None),
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    q = db.query(Delegation).filter(
        Delegation.lab_id == current_user.lab_id,
        ~Delegation.is_deleted,
    )
    if status:
        q = q.filter(Delegation.status == status)
    result = q.order_by(Delegation.created_at.desc()).all()
    return {"items": [_model_to_dict(d) for d in result], "total": len(result)}


@router.put("/delegations/{delegation_id}/accept", summary="Accept delegation")
def accept_delegation(
    delegation_id: str,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    delegation = NursingService.accept_delegation(db, current_user.lab_id, current_user.id, delegation_id)
    return _model_to_dict(delegation)


@router.put("/delegations/{delegation_id}/complete", summary="Complete delegation")
def complete_delegation(
    delegation_id: str,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    delegation = NursingService.complete_delegation(db, current_user.lab_id, current_user.id, delegation_id)
    return _model_to_dict(delegation)


@router.post("/escalations", summary="Create escalation", status_code=201)
def create_escalation(
    body: EscalationCreate,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    data = body.model_dump(exclude_none=True)
    escalation = NursingService.escalate(db, current_user.lab_id, current_user.id, data)
    return _model_to_dict(escalation)


@router.get("/escalations", summary="List escalations")
def list_escalations(
    status: str | None = Query(None),
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    q = db.query(EscalationRecord).filter(
        EscalationRecord.lab_id == current_user.lab_id,
        ~EscalationRecord.is_deleted,
    )
    if status:
        q = q.filter(EscalationRecord.status == status)
    result = q.order_by(EscalationRecord.created_at.desc()).all()
    return {"items": [_model_to_dict(e) for e in result], "total": len(result)}


@router.put("/escalations/{escalation_id}/acknowledge", summary="Acknowledge escalation")
def acknowledge_escalation(
    escalation_id: str,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    escalation = NursingService.acknowledge_escalation(db, current_user.lab_id, current_user.id, escalation_id)
    return _model_to_dict(escalation)


@router.put("/escalations/{escalation_id}/resolve", summary="Resolve escalation")
def resolve_escalation(
    escalation_id: str,
    body: EscalationResolve,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    escalation = NursingService.resolve_escalation(
        db, current_user.lab_id, current_user.id, escalation_id, body.resolution,
    )
    return _model_to_dict(escalation)


# ══════════════════════════════════════════════════════════════════════════════
# Medication
# ══════════════════════════════════════════════════════════════════════════════


@router.get("/medication-schedule/{patient_id}", summary="Get medication schedule")
def get_medication_schedule(
    patient_id: int,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return {"items": NursingService.get_medication_schedule(db, current_user.lab_id, patient_id)}


@router.get("/medication-schedule/{patient_id}/missed-doses", summary="Get missed doses")
def get_missed_doses(
    patient_id: int,
    dose_date: date | None = Query(None),
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return {"items": NursingService.get_missed_doses(db, current_user.lab_id, patient_id, dose_date)}


@router.get("/medication-schedule/{patient_id}/late-doses", summary="Get late doses")
def get_late_doses(
    patient_id: int,
    window_minutes: int = Query(30, ge=1, le=480),
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return {"items": MedicationAdminService.get_late_doses(db, current_user.lab_id, patient_id, window_minutes)}


@router.get("/medication-alerts/{patient_id}", summary="Get medication alerts")
def get_medication_alerts(
    patient_id: int,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return {"items": MedicationAdminService.get_medication_alerts(db, current_user.lab_id, patient_id)}


@router.post("/medication-admin/verify", summary="Verify five rights")
def verify_five_rights(
    body: MedicationVerifyRequest,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    result = MedicationAdminService.verify_five_rights(
        body.right_patient, body.right_drug,
        body.right_dose, body.right_route, body.right_time,
    )
    return {"passed": result.passed, "checks": result.checks, "message": result.message}


@router.post("/medication-admin/record", summary="Record medication administration", status_code=201)
def record_medication_admin(
    body: MedicationAdminRecord,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    data = body.model_dump(exclude_none=True)
    data["administrator_id"] = str(current_user.id)
    admin = MedicationAdminService.record_administration(db, current_user.lab_id, current_user.id, data)
    return _model_to_dict(admin)


@router.post("/medication-admin/sign", summary="Electronic signature for medication")
def sign_medication_admin(
    body: MedicationSignRequest,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return MedicationAdminService.electronic_signature(
        db, current_user.lab_id, str(current_user.id), body.medication_admin_id,
    )


# ══════════════════════════════════════════════════════════════════════════════
# Coordination
# ══════════════════════════════════════════════════════════════════════════════


@router.post("/coordination/physician-message", summary="Send message to physician")
def send_physician_message(
    body: PhysicianMessageRequest,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return CareCoordinatorService.send_physician_message(
        db, current_user.lab_id, current_user.id,
        body.physician_id, body.patient_id, body.subject, body.body, body.priority,
    )


@router.post("/coordination/lab-request", summary="Request lab collection")
def request_lab_collection(
    body: LabRequest,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return CareCoordinatorService.request_lab_collection(
        db, current_user.lab_id, current_user.id, body.patient_id, body.tests,
    )


@router.post("/coordination/radiology-request", summary="Request radiology exam")
def request_radiology(
    body: RadiologyRequest,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return CareCoordinatorService.coordinate_radiology(
        db, current_user.lab_id, current_user.id, body.patient_id, body.exam_type, body.urgency,
    )


@router.post("/coordination/pharmacy-request", summary="Request pharmacy")
def request_pharmacy(
    body: PharmacyRequest,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return CareCoordinatorService.coordinate_pharmacy(
        db, current_user.lab_id, current_user.id, body.patient_id,
        body.medication, body.dose, body.route,
    )


@router.post("/coordination/referral", summary="Create referral", dependencies=[Depends(block_legacy_referral_write)])
def create_referral(
    body: ReferralRequest,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return CareCoordinatorService.manage_referral(
        db, current_user.lab_id, current_user.id, body.patient_id,
        body.to_specialty, body.reason, body.urgency,
    )


@router.post("/coordination/discharge-plan", summary="Create discharge plan")
def create_discharge_plan(
    body: DischargePlanRequest,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return CareCoordinatorService.plan_discharge(
        db, current_user.lab_id, current_user.id, body.patient_id,
        body.expected_date, body.discharge_needs,
    )


@router.post("/coordination/family-communication", summary="Log family communication")
def family_communication(
    body: FamilyCommunicationRequest,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return CareCoordinatorService.family_communication(
        db, current_user.lab_id, current_user.id, body.patient_id,
        body.family_contact, body.message,
    )


@router.post("/coordination/home-care-handover", summary="Home care handover")
def home_care_handover(
    body: HomeCareHandoverRequest,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return CareCoordinatorService.home_care_handover(
        db, current_user.lab_id, current_user.id, body.patient_id,
        body.home_care_provider, body.summary,
    )
