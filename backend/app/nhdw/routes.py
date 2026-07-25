from __future__ import annotations

from datetime import date, datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app._compat import UTC

from ..database import get_db
from ..models.lab_user import LabUser
from ..security.dependencies import get_current_user
from .enums import (
    AdmissionType,
    AlertSeverity,
    ClinicalTaskStatus,
    DischargeType,
    QueuePriority,
    QueueStatus,
    ShiftType,
)
from .kpi import (
    admission_rate,
    average_length_of_stay,
    bed_occupancy_rate,
    bed_turnover_interval,
    discharge_rate,
    emergency_wait_times,
    executive_summary,
    or_utilization_rate,
    readmission_rate_30d,
    transfer_rate,
)
from .models import (
    Admission,
    ClinicalTask,
    HospitalAlert,
    HospitalMessage,
    QueueEntry,
    WaitingListEntry,
    WardRound,
)
from .services import NHDWService

router = APIRouter(prefix="/nhdw", tags=["nhdw"])


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


class AdmissionCreate(BaseModel):
    patient_id: int
    encounter_id: str | None = None
    hospital_id: int
    department_id: int
    room_id: int | None = None
    bed_id: int | None = None
    admission_type: AdmissionType
    admission_date: datetime | None = None
    expected_discharge_date: datetime | None = None
    diagnosis: str | None = None
    diagnosis_code: str | None = None
    diagnosis_system: str | None = None
    admitting_doctor_id: int | None = None
    referring_doctor_id: int | None = None
    insurance_id: str | None = None
    insurance_policy: str | None = None
    is_emergency: bool = False
    notes: str | None = None
    metadata: dict[str, Any] = {}


class AdmissionUpdate(BaseModel):
    department_id: int | None = None
    room_id: int | None = None
    bed_id: int | None = None
    admission_type: AdmissionType | None = None
    expected_discharge_date: datetime | None = None
    diagnosis: str | None = None
    diagnosis_code: str | None = None
    diagnosis_system: str | None = None
    admitting_doctor_id: int | None = None
    referring_doctor_id: int | None = None
    notes: str | None = None
    metadata: dict[str, Any] = {}


class AdmissionDischarge(BaseModel):
    discharge_type: DischargeType
    discharge_date: datetime | None = None
    discharge_destination: str | None = None
    discharge_summary: str | None = None
    medications_at_discharge: list[dict[str, Any]] = []
    follow_up_instructions: str | None = None
    follow_up_date: datetime | None = None
    follow_up_provider_id: int | None = None
    mortality_review: str | None = None
    notes: str | None = None


class AdmissionTransfer(BaseModel):
    to_department_id: int
    to_room_id: int | None = None
    to_bed_id: int | None = None
    from_doctor_id: int | None = None
    to_doctor_id: int | None = None
    reason: str = "Transfer"
    clinical_summary: list[dict[str, Any]] = []
    transfer_type: str = "intra_hospital"


class QueueCheckIn(BaseModel):
    patient_id: int
    department_id: int
    clinic_id: int | None = None
    priority: QueuePriority = QueuePriority.MEDIUM
    queue_date: date | None = None
    visit_reason: str | None = None
    notes: str | None = None
    metadata: dict[str, Any] = {}


class WaitingListCreate(BaseModel):
    patient_id: int
    department_id: int
    procedure_code: str | None = None
    procedure_name: str | None = None
    priority: QueuePriority = QueuePriority.MEDIUM
    clinical_urgency: str | None = None
    notes: str | None = None
    metadata: dict[str, Any] = {}


class WaitingListConvert(BaseModel):
    hospital_id: int
    room_id: int | None = None
    bed_id: int | None = None
    admission_type: AdmissionType = AdmissionType.ELECTIVE
    notes: str | None = None


class ClinicalTaskCreate(BaseModel):
    patient_id: int
    encounter_id: str | None = None
    assigned_to: int
    task_type: str
    description: str
    priority: QueuePriority = QueuePriority.MEDIUM
    due_date: datetime | None = None
    scheduled_time: datetime | None = None
    notes: str | None = None
    metadata: dict[str, Any] = {}
    is_recurring: bool = False
    recurrence_rule: str | None = None


class ClinicalTaskUpdate(BaseModel):
    description: str | None = None
    priority: QueuePriority | None = None
    due_date: datetime | None = None
    scheduled_time: datetime | None = None
    notes: str | None = None
    metadata: dict[str, Any] = {}


class ClinicalTaskAssign(BaseModel):
    assigned_to: int


class WardRoundCreate(BaseModel):
    patient_id: int
    encounter_id: str | None = None
    department_id: int
    lead_doctor_id: int
    participants: list[dict[str, Any]] = []
    clinical_summary: str | None = None
    assessment: str | None = None
    plan: str | None = None
    medications_reviewed: list[dict[str, Any]] = []
    investigations_ordered: list[dict[str, Any]] = []
    follow_up_plan: str | None = None
    notes: str | None = None
    metadata: dict[str, Any] = {}


class CarePlanCreate(BaseModel):
    patient_id: int
    encounter_id: str | None = None
    diagnosis: str | None = None
    goals: list[dict[str, Any]] = []
    interventions: list[dict[str, Any]] = []
    start_date: datetime | None = None
    review_date: datetime | None = None
    next_review_date: datetime | None = None
    created_by: int | None = None
    approved_by: int | None = None
    care_team: list[dict[str, Any]] = []
    notes: str | None = None
    metadata: dict[str, Any] = {}


class CarePlanUpdate(BaseModel):
    diagnosis: str | None = None
    goals: list[dict[str, Any]] = []
    interventions: list[dict[str, Any]] = []
    review_date: datetime | None = None
    next_review_date: datetime | None = None
    approved_by: int | None = None
    care_team: list[dict[str, Any]] = []
    notes: str | None = None


class CarePlanReview(BaseModel):
    review_notes: str | None = None


class AlertCreate(BaseModel):
    alert_type: str
    severity: AlertSeverity = AlertSeverity.INFO
    title: str
    title_ar: str | None = None
    description: str | None = None
    source_department_id: int | None = None
    patient_id: int | None = None
    metadata: dict[str, Any] = {}


class MessageCreate(BaseModel):
    recipient_id: int
    subject: str
    body: str
    priority: str = "normal"
    department_id: int | None = None
    parent_message_id: str | None = None
    has_attachments: bool = False
    metadata: dict[str, Any] = {}


class TelemedicineSessionCreate(BaseModel):
    patient_id: int
    provider_id: int
    scheduled_at: datetime
    session_type: str = "video"
    platform: str | None = None
    meeting_url: str | None = None
    notes: str | None = None
    metadata: dict[str, Any] = {}


class TelemedicineEnd(BaseModel):
    notes: str | None = None
    recording_url: str | None = None


class ResourceScheduleCreate(BaseModel):
    resource_type: str
    resource_id: int
    scheduled_date: date
    start_time: datetime
    end_time: datetime
    booked_by: int | None = None
    booked_for_patient_id: int | None = None
    notes: str | None = None
    metadata: dict[str, Any] = {}


class ResourceScheduleUpdate(BaseModel):
    start_time: datetime | None = None
    end_time: datetime | None = None
    status: str | None = None
    booked_by: int | None = None
    booked_for_patient_id: int | None = None
    notes: str | None = None


class DashboardConfigCreate(BaseModel):
    role: str | None = None
    department_id: int | None = None
    config_json: dict[str, Any]
    is_default: bool = False


class ShiftReportCreate(BaseModel):
    department_id: int
    shift_type: ShiftType
    shift_date: date
    start_time: datetime
    end_time: datetime | None = None
    patient_count: int = 0
    admissions_count: int = 0
    discharges_count: int = 0
    transfers_count: int = 0
    critical_events: list[dict[str, Any]] = []
    staffing: dict[str, Any] = {}
    issues: list[dict[str, Any]] = []
    notes: str | None = None
    metadata: dict[str, Any] = {}


@router.get("/admissions", summary="List admissions")
def list_admissions(
    department_id: int | None = Query(None),
    status: str | None = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: LabUser = Depends(get_current_user),
):
    admissions = NHDWService.list_admissions(
        db, current_user.lab_id, department_id, status, skip, limit
    )
    total = (
        db.query(Admission)
        .filter(
            Admission.lab_id == current_user.lab_id,
            ~Admission.is_deleted,
        )
        .count()
    )
    return _paginated_response([_model_to_dict(a) for a in admissions], total, skip, limit)


@router.get("/admissions/active", summary="List active admissions")
def list_active_admissions(
    department_id: int | None = Query(None),
    db: Session = Depends(get_db),
    current_user: LabUser = Depends(get_current_user),
):
    admissions = NHDWService.get_active_admissions(db, current_user.lab_id, department_id)
    return [_model_to_dict(a) for a in admissions]


@router.get("/admissions/{patient_id}/history", summary="Get admission history for patient")
def get_admission_history(
    patient_id: int,
    db: Session = Depends(get_db),
    current_user: LabUser = Depends(get_current_user),
):
    admissions = NHDWService.get_admission_history(db, patient_id, current_user.lab_id)
    return [_model_to_dict(a) for a in admissions]


@router.post("/admissions", summary="Create admission", status_code=201)
def create_admission(
    body: AdmissionCreate,
    db: Session = Depends(get_db),
    current_user: LabUser = Depends(get_current_user),
):
    data = body.model_dump()
    if "metadata" in data:
        data["metadata_"] = data.pop("metadata")
    admission = NHDWService.create_admission(db, current_user.lab_id, current_user.id, data)
    return _model_to_dict(admission)


@router.get("/admissions/{admission_id}", summary="Get admission")
def get_admission(
    admission_id: str,
    db: Session = Depends(get_db),
    current_user: LabUser = Depends(get_current_user),
):
    return _model_to_dict(NHDWService.get_admission(db, admission_id, current_user.lab_id))


@router.put("/admissions/{admission_id}", summary="Update admission")
def update_admission(
    admission_id: str,
    body: AdmissionUpdate,
    db: Session = Depends(get_db),
    current_user: LabUser = Depends(get_current_user),
):
    data = {k: v for k, v in body.model_dump().items() if v is not None}
    if "metadata" in data:
        data["metadata_"] = data.pop("metadata")
    admission = NHDWService.update_admission(
        db, current_user.lab_id, current_user.id, admission_id, data
    )
    return _model_to_dict(admission)


@router.post("/admissions/{admission_id}/discharge", summary="Discharge patient")
def discharge_admission(
    admission_id: str,
    body: AdmissionDischarge,
    db: Session = Depends(get_db),
    current_user: LabUser = Depends(get_current_user),
):
    data = body.model_dump(exclude_none=True)
    if "medications_at_discharge" in data and isinstance(data["medications_at_discharge"], list):
        data["medications_at_discharge"] = data["medications_at_discharge"]
    discharge = NHDWService.discharge_patient(
        db,
        current_user.lab_id,
        current_user.id,
        admission_id,
        data,
    )
    return _model_to_dict(discharge)


@router.post("/admissions/{admission_id}/transfer", summary="Transfer patient")
def transfer_admission(
    admission_id: str,
    body: AdmissionTransfer,
    db: Session = Depends(get_db),
    current_user: LabUser = Depends(get_current_user),
):
    transfer = NHDWService.transfer_patient(
        db,
        current_user.lab_id,
        current_user.id,
        admission_id,
        body.model_dump(exclude_none=True),
    )
    return _model_to_dict(transfer)


@router.post("/queue/check-in", summary="Check in patient to queue", status_code=201)
def queue_check_in(
    body: QueueCheckIn,
    db: Session = Depends(get_db),
    current_user: LabUser = Depends(get_current_user),
):
    data = body.model_dump(exclude_none=True)
    if "metadata" in data:
        data["metadata_"] = data.pop("metadata")
    if not data.get("queue_date"):
        data["queue_date"] = date.today()
    data.setdefault("check_in_time", datetime.now(UTC))
    entry = NHDWService.add_queue_entry(db, current_user.lab_id, current_user.id, data)
    return _model_to_dict(entry)


@router.get("/queue", summary="List queue entries")
def list_queue(
    department_id: int | None = Query(None),
    queue_date: date | None = Query(None),
    status: QueueStatus | None = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: LabUser = Depends(get_current_user),
):
    entries = NHDWService.list_queue(
        db,
        current_user.lab_id,
        department_id,
        queue_date,
        status,
        skip,
        limit,
    )
    total = (
        db.query(QueueEntry)
        .filter(
            QueueEntry.lab_id == current_user.lab_id,
            ~QueueEntry.is_deleted,
        )
        .count()
    )
    return _paginated_response([_model_to_dict(e) for e in entries], total, skip, limit)


@router.put("/queue/{entry_id}/serve", summary="Serve queue entry")
def serve_queue_entry(
    entry_id: str,
    db: Session = Depends(get_db),
    current_user: LabUser = Depends(get_current_user),
):
    entry = NHDWService.serve_queue_entry(db, current_user.lab_id, current_user.id, entry_id)
    return _model_to_dict(entry)


@router.put("/queue/{entry_id}/complete", summary="Complete queue entry")
def complete_queue_entry(
    entry_id: str,
    db: Session = Depends(get_db),
    current_user: LabUser = Depends(get_current_user),
):
    entry = NHDWService.complete_queue_entry(db, current_user.lab_id, current_user.id, entry_id)
    return _model_to_dict(entry)


@router.put("/queue/{entry_id}/no-show", summary="Mark queue entry as no-show")
def no_show_queue_entry(
    entry_id: str,
    db: Session = Depends(get_db),
    current_user: LabUser = Depends(get_current_user),
):
    entry = NHDWService.no_show_queue_entry(db, current_user.lab_id, current_user.id, entry_id)
    return _model_to_dict(entry)


@router.get("/waiting-list", summary="List waiting list")
def list_waiting_list(
    department_id: int | None = Query(None),
    status: str | None = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: LabUser = Depends(get_current_user),
):
    entries = NHDWService.list_waiting_list(
        db,
        current_user.lab_id,
        department_id,
        status,
        skip,
        limit,
    )
    total = (
        db.query(WaitingListEntry)
        .filter(
            WaitingListEntry.lab_id == current_user.lab_id,
            ~WaitingListEntry.is_deleted,
        )
        .count()
    )
    return _paginated_response([_model_to_dict(e) for e in entries], total, skip, limit)


@router.post("/waiting-list", summary="Add to waiting list", status_code=201)
def create_waiting_list(
    body: WaitingListCreate,
    db: Session = Depends(get_db),
    current_user: LabUser = Depends(get_current_user),
):
    data = body.model_dump(exclude_none=True)
    if "metadata" in data:
        data["metadata_"] = data.pop("metadata")
    entry = NHDWService.add_waiting_list(db, current_user.lab_id, current_user.id, data)
    return _model_to_dict(entry)


@router.put("/waiting-list/{entry_id}/convert", summary="Convert waiting list entry to admission")
def convert_waiting_list(
    entry_id: str,
    body: WaitingListConvert,
    db: Session = Depends(get_db),
    current_user: LabUser = Depends(get_current_user),
):
    admission = NHDWService.convert_waiting_to_admission(
        db,
        current_user.lab_id,
        current_user.id,
        entry_id,
        body.model_dump(),
    )
    return _model_to_dict(admission)


@router.get("/clinical-tasks", summary="List clinical tasks")
def list_clinical_tasks(
    assigned_to: int | None = Query(None),
    status: ClinicalTaskStatus | None = None,
    patient_id: int | None = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: LabUser = Depends(get_current_user),
):
    tasks = NHDWService.list_clinical_tasks(
        db,
        current_user.lab_id,
        assigned_to,
        status,
        patient_id,
        skip,
        limit,
    )
    total = (
        db.query(ClinicalTask)
        .filter(
            ClinicalTask.lab_id == current_user.lab_id,
            ~ClinicalTask.is_deleted,
        )
        .count()
    )
    return _paginated_response([_model_to_dict(t) for t in tasks], total, skip, limit)


@router.post("/clinical-tasks", summary="Create clinical task", status_code=201)
def create_clinical_task(
    body: ClinicalTaskCreate,
    db: Session = Depends(get_db),
    current_user: LabUser = Depends(get_current_user),
):
    data = body.model_dump(exclude_none=True)
    if "metadata" in data:
        data["metadata_"] = data.pop("metadata")
    task = NHDWService.create_clinical_task(db, current_user.lab_id, current_user.id, data)
    return _model_to_dict(task)


@router.put("/clinical-tasks/{task_id}", summary="Update clinical task")
def update_clinical_task(
    task_id: str,
    body: ClinicalTaskUpdate,
    db: Session = Depends(get_db),
    current_user: LabUser = Depends(get_current_user),
):
    data = {k: v for k, v in body.model_dump().items() if v is not None}
    task = NHDWService.update_clinical_task(db, current_user.lab_id, current_user.id, task_id, data)
    return _model_to_dict(task)


@router.put("/clinical-tasks/{task_id}/assign", summary="Assign clinical task")
def assign_clinical_task(
    task_id: str,
    body: ClinicalTaskAssign,
    db: Session = Depends(get_db),
    current_user: LabUser = Depends(get_current_user),
):
    task = NHDWService.assign_clinical_task(
        db, current_user.lab_id, current_user.id, task_id, body.assigned_to
    )
    return _model_to_dict(task)


@router.put("/clinical-tasks/{task_id}/complete", summary="Complete clinical task")
def complete_clinical_task(
    task_id: str,
    db: Session = Depends(get_db),
    current_user: LabUser = Depends(get_current_user),
):
    task = NHDWService.complete_clinical_task(db, current_user.lab_id, current_user.id, task_id)
    return _model_to_dict(task)


@router.post("/ward-rounds", summary="Create ward round", status_code=201)
def create_ward_round(
    body: WardRoundCreate,
    db: Session = Depends(get_db),
    current_user: LabUser = Depends(get_current_user),
):
    data = body.model_dump(exclude_none=True)
    if "metadata" in data:
        data["metadata_"] = data.pop("metadata")
    ward_round = NHDWService.create_ward_round(db, current_user.lab_id, current_user.id, data)
    return _model_to_dict(ward_round)


@router.get("/ward-rounds", summary="List ward rounds")
def list_ward_rounds(
    department_id: int | None = Query(None),
    patient_id: int | None = Query(None),
    from_date: datetime | None = Query(None),
    to_date: datetime | None = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: LabUser = Depends(get_current_user),
):
    rounds = NHDWService.list_ward_rounds(
        db,
        current_user.lab_id,
        department_id,
        patient_id,
        from_date,
        to_date,
        skip,
        limit,
    )
    total = (
        db.query(WardRound)
        .filter(
            WardRound.lab_id == current_user.lab_id,
            ~WardRound.is_deleted,
        )
        .count()
    )
    return _paginated_response([_model_to_dict(r) for r in rounds], total, skip, limit)


@router.get("/ward-rounds/{round_id}", summary="Get ward round")
def get_ward_round(
    round_id: str,
    db: Session = Depends(get_db),
    current_user: LabUser = Depends(get_current_user),
):
    return _model_to_dict(NHDWService.get_ward_round(db, round_id, current_user.lab_id))


@router.get("/care-plans/{patient_id}", summary="Get care plans for patient")
def get_care_plans(
    patient_id: int,
    db: Session = Depends(get_db),
    current_user: LabUser = Depends(get_current_user),
):
    plans = NHDWService.get_care_plans(db, patient_id, current_user.lab_id)
    return [_model_to_dict(p) for p in plans]


@router.post("/care-plans", summary="Create care plan", status_code=201)
def create_care_plan(
    body: CarePlanCreate,
    db: Session = Depends(get_db),
    current_user: LabUser = Depends(get_current_user),
):
    data = body.model_dump(exclude_none=True)
    if "metadata" in data:
        data["metadata_"] = data.pop("metadata")
    data.setdefault("created_by", current_user.id)
    plan = NHDWService.create_care_plan(db, current_user.lab_id, current_user.id, data)
    return _model_to_dict(plan)


@router.put("/care-plans/{plan_id}", summary="Update care plan")
def update_care_plan(
    plan_id: str,
    body: CarePlanUpdate,
    db: Session = Depends(get_db),
    current_user: LabUser = Depends(get_current_user),
):
    data = {k: v for k, v in body.model_dump().items() if v is not None}
    plan = NHDWService.update_care_plan(db, current_user.lab_id, current_user.id, plan_id, data)
    return _model_to_dict(plan)


@router.put("/care-plans/{plan_id}/review", summary="Review care plan")
def review_care_plan(
    plan_id: str,
    body: CarePlanReview,
    db: Session = Depends(get_db),
    current_user: LabUser = Depends(get_current_user),
):
    plan = NHDWService.review_care_plan(
        db, current_user.lab_id, current_user.id, plan_id, body.review_notes
    )
    return _model_to_dict(plan)


@router.get("/kpi/executive-summary", summary="Executive summary of all KPIs")
def kpi_executive_summary(
    db: Session = Depends(get_db),
    current_user: LabUser = Depends(get_current_user),
):
    return executive_summary(db, current_user.lab_id)


@router.get("/kpi/occupancy", summary="Bed occupancy rate")
def kpi_occupancy(
    department_id: int | None = Query(None),
    db: Session = Depends(get_db),
    current_user: LabUser = Depends(get_current_user),
):
    return bed_occupancy_rate(db, current_user.lab_id, department_id)


@router.get("/kpi/occupancy/{department_id}", summary="Bed occupancy by department")
def kpi_occupancy_by_department(
    department_id: int,
    db: Session = Depends(get_db),
    current_user: LabUser = Depends(get_current_user),
):
    return bed_occupancy_rate(db, current_user.lab_id, department_id)


@router.get("/kpi/admissions", summary="Admission rate")
def kpi_admissions(
    days: int = Query(30, ge=1, le=365),
    department_id: int | None = Query(None),
    db: Session = Depends(get_db),
    current_user: LabUser = Depends(get_current_user),
):
    return admission_rate(db, current_user.lab_id, days, department_id)


@router.get("/kpi/discharges", summary="Discharge rate")
def kpi_discharges(
    days: int = Query(30, ge=1, le=365),
    department_id: int | None = Query(None),
    db: Session = Depends(get_db),
    current_user: LabUser = Depends(get_current_user),
):
    return discharge_rate(db, current_user.lab_id, days, department_id)


@router.get("/kpi/transfers", summary="Transfer rate")
def kpi_transfers(
    days: int = Query(30, ge=1, le=365),
    department_id: int | None = Query(None),
    db: Session = Depends(get_db),
    current_user: LabUser = Depends(get_current_user),
):
    return transfer_rate(db, current_user.lab_id, days, department_id)


@router.get("/kpi/los", summary="Average length of stay")
def kpi_los(
    department_id: int | None = Query(None),
    db: Session = Depends(get_db),
    current_user: LabUser = Depends(get_current_user),
):
    return average_length_of_stay(db, current_user.lab_id, department_id)


@router.get("/kpi/readmission-rate", summary="30-day readmission rate")
def kpi_readmission_rate(
    days: int = Query(30, ge=1, le=90),
    department_id: int | None = Query(None),
    db: Session = Depends(get_db),
    current_user: LabUser = Depends(get_current_user),
):
    return readmission_rate_30d(db, current_user.lab_id, days, department_id)


@router.get("/kpi/emergency-wait-times", summary="Emergency wait times")
def kpi_emergency_wait_times(
    days: int = Query(7, ge=1, le=30),
    db: Session = Depends(get_db),
    current_user: LabUser = Depends(get_current_user),
):
    return emergency_wait_times(db, current_user.lab_id, days)


@router.get("/kpi/or-utilization", summary="OR utilization rate")
def kpi_or_utilization(
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db),
    current_user: LabUser = Depends(get_current_user),
):
    return or_utilization_rate(db, current_user.lab_id, days)


@router.get("/kpi/bed-turnover", summary="Bed turnover interval")
def kpi_bed_turnover(
    department_id: int | None = Query(None),
    db: Session = Depends(get_db),
    current_user: LabUser = Depends(get_current_user),
):
    return bed_turnover_interval(db, current_user.lab_id, department_id)


@router.get("/dashboard/admin", summary="Admin dashboard")
def admin_dashboard(
    db: Session = Depends(get_db),
    current_user: LabUser = Depends(get_current_user),
):
    return NHDWService.admin_dashboard(db, current_user.lab_id)


@router.get("/dashboard/executive", summary="Executive dashboard")
def executive_dashboard(
    db: Session = Depends(get_db),
    current_user: LabUser = Depends(get_current_user),
):
    return NHDWService.executive_dashboard(db, current_user.lab_id)


@router.get("/dashboard/clinical", summary="Clinical dashboard")
def clinical_dashboard(
    db: Session = Depends(get_db),
    current_user: LabUser = Depends(get_current_user),
):
    return NHDWService.clinical_dashboard(db, current_user.lab_id)


@router.get("/messages", summary="List messages")
def list_messages(
    direction: str = Query("received", pattern="^(received|sent)$"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: LabUser = Depends(get_current_user),
):
    messages = NHDWService.list_messages(
        db,
        current_user.lab_id,
        current_user.id,
        direction,
        skip,
        limit,
    )
    total = (
        db.query(HospitalMessage)
        .filter(
            HospitalMessage.lab_id == current_user.lab_id,
            ~HospitalMessage.is_deleted,
            HospitalMessage.recipient_id == current_user.id
            if direction == "received"
            else HospitalMessage.sender_id == current_user.id,
        )
        .count()
    )
    return _paginated_response([_model_to_dict(m) for m in messages], total, skip, limit)


@router.post("/messages", summary="Send message", status_code=201)
def send_message(
    body: MessageCreate,
    db: Session = Depends(get_db),
    current_user: LabUser = Depends(get_current_user),
):
    data = body.model_dump(exclude_none=True)
    if "metadata" in data:
        data["metadata_"] = data.pop("metadata")
    msg = NHDWService.send_message(db, current_user.lab_id, current_user.id, data)
    return _model_to_dict(msg)


@router.get("/messages/{message_id}", summary="Get message details")
def get_message(
    message_id: str,
    db: Session = Depends(get_db),
    current_user: LabUser = Depends(get_current_user),
):
    return _model_to_dict(NHDWService.get_message(db, message_id, current_user.lab_id))


@router.put("/messages/{message_id}/read", summary="Mark message as read")
def mark_message_read(
    message_id: str,
    db: Session = Depends(get_db),
    current_user: LabUser = Depends(get_current_user),
):
    msg = NHDWService.mark_message_read(db, current_user.lab_id, current_user.id, message_id)
    return _model_to_dict(msg)


@router.post("/alerts", summary="Create alert", status_code=201)
def create_alert(
    body: AlertCreate,
    db: Session = Depends(get_db),
    current_user: LabUser = Depends(get_current_user),
):
    data = body.model_dump(exclude_none=True)
    if "metadata" in data:
        data["metadata_"] = data.pop("metadata")
    alert = NHDWService.create_alert(db, current_user.lab_id, current_user.id, data)
    return _model_to_dict(alert)


@router.get("/alerts", summary="List alerts")
def list_alerts(
    severity: AlertSeverity | None = None,
    is_resolved: bool | None = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: LabUser = Depends(get_current_user),
):
    alerts = NHDWService.list_alerts(db, current_user.lab_id, severity, is_resolved, skip, limit)
    total = (
        db.query(HospitalAlert)
        .filter(
            HospitalAlert.lab_id == current_user.lab_id,
            ~HospitalAlert.is_deleted,
        )
        .count()
    )
    return _paginated_response([_model_to_dict(a) for a in alerts], total, skip, limit)


@router.put("/alerts/{alert_id}/acknowledge", summary="Acknowledge alert")
def acknowledge_alert(
    alert_id: str,
    db: Session = Depends(get_db),
    current_user: LabUser = Depends(get_current_user),
):
    alert = NHDWService.acknowledge_alert(db, current_user.lab_id, current_user.id, alert_id)
    return _model_to_dict(alert)


@router.put("/alerts/{alert_id}/resolve", summary="Resolve alert")
def resolve_alert(
    alert_id: str,
    db: Session = Depends(get_db),
    current_user: LabUser = Depends(get_current_user),
):
    alert = NHDWService.resolve_alert(db, current_user.lab_id, current_user.id, alert_id)
    return _model_to_dict(alert)


@router.get("/resource-schedule", summary="List resource schedules")
def list_resource_schedule(
    resource_type: str | None = Query(None),
    resource_id: int | None = Query(None),
    scheduled_date: date | None = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: LabUser = Depends(get_current_user),
):
    schedules = NHDWService.list_resource_schedules(
        db,
        current_user.lab_id,
        resource_type,
        resource_id,
        scheduled_date,
        skip,
        limit,
    )
    return [_model_to_dict(s) for s in schedules]


@router.post("/resource-schedule", summary="Create resource schedule", status_code=201)
def create_resource_schedule(
    body: ResourceScheduleCreate,
    db: Session = Depends(get_db),
    current_user: LabUser = Depends(get_current_user),
):
    data = body.model_dump(exclude_none=True)
    if "metadata" in data:
        data["metadata_"] = data.pop("metadata")
    schedule = NHDWService.create_resource_schedule(db, current_user.lab_id, current_user.id, data)
    return _model_to_dict(schedule)


@router.put("/resource-schedule/{schedule_id}", summary="Update resource schedule")
def update_resource_schedule(
    schedule_id: str,
    body: ResourceScheduleUpdate,
    db: Session = Depends(get_db),
    current_user: LabUser = Depends(get_current_user),
):
    data = {k: v for k, v in body.model_dump().items() if v is not None}
    schedule = NHDWService.update_resource_schedule(
        db, current_user.lab_id, current_user.id, schedule_id, data
    )
    return _model_to_dict(schedule)


@router.get("/telemedicine-sessions", summary="List telemedicine sessions")
def list_telemedicine_sessions(
    patient_id: int | None = Query(None),
    provider_id: int | None = Query(None),
    status: str | None = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: LabUser = Depends(get_current_user),
):
    sessions = NHDWService.list_telemedicine_sessions(
        db,
        current_user.lab_id,
        patient_id,
        provider_id,
        status,
        skip,
        limit,
    )
    return [_model_to_dict(s) for s in sessions]


@router.post("/telemedicine-sessions", summary="Create telemedicine session", status_code=201)
def create_telemedicine_session(
    body: TelemedicineSessionCreate,
    db: Session = Depends(get_db),
    current_user: LabUser = Depends(get_current_user),
):
    data = body.model_dump(exclude_none=True)
    if "metadata" in data:
        data["metadata_"] = data.pop("metadata")
    session = NHDWService.create_telemedicine_session(
        db, current_user.lab_id, current_user.id, data
    )
    return _model_to_dict(session)


@router.put("/telemedicine-sessions/{session_id}/start", summary="Start telemedicine session")
def start_telemedicine_session(
    session_id: str,
    db: Session = Depends(get_db),
    current_user: LabUser = Depends(get_current_user),
):
    session = NHDWService.start_telemedicine_session(db, current_user.lab_id, session_id)
    return _model_to_dict(session)


@router.put("/telemedicine-sessions/{session_id}/end", summary="End telemedicine session")
def end_telemedicine_session(
    session_id: str,
    body: TelemedicineEnd = TelemedicineEnd(),
    db: Session = Depends(get_db),
    current_user: LabUser = Depends(get_current_user),
):
    session = NHDWService.end_telemedicine_session(
        db,
        current_user.lab_id,
        session_id,
        body.model_dump(exclude_none=True),
    )
    return _model_to_dict(session)


@router.get("/dashboard-config/{role}", summary="Get dashboard configuration by role")
def get_dashboard_config(
    role: str,
    db: Session = Depends(get_db),
    current_user: LabUser = Depends(get_current_user),
):
    config = NHDWService.get_dashboard_config(db, current_user.lab_id, role)
    if not config:
        raise HTTPException(
            status_code=404,
            detail="Dashboard configuration not found",
            detail_ar="لم يتم العثور على تكوين لوحة المعلومات",
        )
    return _model_to_dict(config)


@router.post("/dashboard-config", summary="Save dashboard configuration", status_code=201)
def save_dashboard_config(
    body: DashboardConfigCreate,
    db: Session = Depends(get_db),
    current_user: LabUser = Depends(get_current_user),
):
    data = body.model_dump(exclude_none=True)
    config = NHDWService.save_dashboard_config(db, current_user.lab_id, current_user.id, data)
    return _model_to_dict(config)


@router.get("/shift-reports", summary="List shift reports")
def list_shift_reports(
    department_id: int | None = Query(None),
    shift_type: ShiftType | None = None,
    shift_date: date | None = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: LabUser = Depends(get_current_user),
):
    reports = NHDWService.list_shift_reports(
        db,
        current_user.lab_id,
        department_id,
        shift_type,
        shift_date,
        skip,
        limit,
    )
    return [_model_to_dict(r) for r in reports]


@router.post("/shift-reports", summary="Create shift report", status_code=201)
def create_shift_report(
    body: ShiftReportCreate,
    db: Session = Depends(get_db),
    current_user: LabUser = Depends(get_current_user),
):
    data = body.model_dump(exclude_none=True)
    if "metadata" in data:
        data["metadata_"] = data.pop("metadata")
    report = NHDWService.create_shift_report(db, current_user.lab_id, current_user.id, data)
    return _model_to_dict(report)
