from datetime import date, datetime
from typing import Any

from fastapi import APIRouter, Depends, Header, HTTPException, Query
from pydantic import BaseModel, field_validator
from sqlalchemy.orm import Session

from ..clinical.command_guard import ClinicalCommandGuard
from ..database import get_db
from ..domain.exceptions import ConflictError, NotFoundError
from ..hospital.models import (
    Bed,
    BedAssignment,
    Campus,
    HospitalDepartment,
    HospitalMaster,
    MedicalEquipment,
    OperationTheater,
)
from ..models.lab_user import LabUser
from ..security.dependencies import get_current_user
from ..services.hospital_service import HospitalService

router = APIRouter(prefix="/hospital", tags=["hospital"])

# ── Schemas ────────────────────────────────────────────────────────────────────


class HospitalCreate(BaseModel):
    code: str
    name: str
    name_ar: str | None = None
    hospital_type: str
    license_number: str | None = None
    phone: str | None = None
    email: str | None = None
    website: str | None = None
    address: str | None = None
    city: str | None = None
    province: str | None = None
    country: str = "IQ"

    @field_validator("code")
    @classmethod
    def validate_code(cls, v):
        if not v.strip():
            raise ValueError("Code is required")
        return v.strip()

    @field_validator("name")
    @classmethod
    def validate_name(cls, v):
        if not v.strip():
            raise ValueError("Name is required")
        return v.strip()

    @field_validator("hospital_type")
    @classmethod
    def validate_type(cls, v):
        allowed = {"general", "specialized", "teaching", "private"}
        if v not in allowed:
            raise ValueError(f"hospital_type must be one of {allowed}")
        return v


class HospitalUpdate(BaseModel):
    name: str | None = None
    name_ar: str | None = None
    hospital_type: str | None = None
    license_number: str | None = None
    phone: str | None = None
    email: str | None = None
    website: str | None = None
    address: str | None = None
    city: str | None = None
    province: str | None = None
    country: str | None = None
    is_active: bool | None = None


class NestedCreate(BaseModel):
    code: str
    name: str
    name_ar: str | None = None

    @field_validator("code")
    @classmethod
    def validate_code(cls, v):
        if not v.strip():
            raise ValueError("Code is required")
        return v.strip()


class CampusCreate(NestedCreate):
    address: str | None = None


class BuildingCreate(NestedCreate):
    floors_count: int = 0


class FloorCreate(NestedCreate):
    floor_number: int


class DepartmentCreate(NestedCreate):
    parent_id: int | None = None
    department_type: str | None = None
    phone: str | None = None


class ClinicCreate(NestedCreate):
    clinic_type: str | None = None
    phone: str | None = None


class RoomCreate(BaseModel):
    code: str
    name: str
    clinic_id: int | None = None
    floor_id: int | None = None
    room_type: str
    capacity: int = 1

    @field_validator("room_type")
    @classmethod
    def validate_type(cls, v):
        allowed = {"ward", "icu", "nicu", "emergency", "operation_theater", "dialysis", "lab", "pharmacy"}
        if v not in allowed:
            raise ValueError(f"room_type must be one of {allowed}")
        return v


class BedCreate(BaseModel):
    bed_number: str
    bed_type: str = "standard"

    @field_validator("bed_type")
    @classmethod
    def validate_type(cls, v):
        allowed = {"standard", "icu", "nicu", "isolation", "recovery"}
        if v not in allowed:
            raise ValueError(f"bed_type must be one of {allowed}")
        return v


class BedAssign(BaseModel):
    patient_id: int
    reason: str | None = None
    diagnosis: str | None = None


class BedDischarge(BaseModel):
    discharge_reason: str | None = None


class BedTransfer(BaseModel):
    to_bed_id: int
    reason: str | None = None


class UnitCreate(NestedCreate):
    unit_type: str

    @field_validator("unit_type")
    @classmethod
    def validate_type(cls, v):
        allowed = {"icu", "nicu", "ccu", "emergency", "dialysis", "operation_theater",
                    "laboratory", "radiology", "pharmacy", "blood_bank"}
        if v not in allowed:
            raise ValueError(f"unit_type must be one of {allowed}")
        return v


class OperationTheaterStatusUpdate(BaseModel):
    status: str
    surgery_id: int | None = None


class SurgicalSafetyChecklistComplete(BaseModel):
    surgery_id: int
    patient_id: int
    procedure_name: str
    procedure_site: str
    planned_laterality: str = "not_applicable"
    patient_identity_confirmed: bool
    procedure_confirmed: bool
    site_marked: bool
    consent_verified: bool
    anesthesia_assessment_complete: bool
    allergy_reviewed: bool
    antibiotic_prophylaxis_confirmed: bool
    blood_products_confirmed: bool
    imaging_reviewed: bool
    team_time_out_completed: bool
    notes: str | None = None


class OperationTheaterCreate(NestedCreate):
    department_id: int | None = None
    theater_type: str

    @field_validator("theater_type")
    @classmethod
    def validate_type(cls, v):
        allowed = {"general", "ortho", "cardiac", "neuro", "ophthalmic", "ent"}
        if v not in allowed:
            raise ValueError(f"theater_type must be one of {allowed}")
        return v


class EquipmentCreate(BaseModel):
    equipment_code: str
    equipment_name: str
    equipment_name_ar: str | None = None
    department_id: int | None = None
    category: str
    manufacturer: str | None = None
    model: str | None = None
    serial_number: str | None = None

    @field_validator("category")
    @classmethod
    def validate_category(cls, v):
        allowed = {"imaging", "lab", "surgical", "life_support", "diagnostic"}
        if v not in allowed:
            raise ValueError(f"category must be one of {allowed}")
        return v


class CostCenterCreate(NestedCreate):
    cost_center_type: str
    budget_amount: float | None = None
    budget_currency: str = "IQD"

    @field_validator("cost_center_type")
    @classmethod
    def validate_type(cls, v):
        allowed = {"clinical", "administrative", "support"}
        if v not in allowed:
            raise ValueError(f"cost_center_type must be one of {allowed}")
        return v


class AppointmentCreate(BaseModel):
    patient_id: int
    provider_id: int | None = None
    facility_id: int | None = None
    appointment_type: str
    scheduled_date: datetime
    duration_minutes: int = 30
    reason: str | None = None
    notes: str | None = None


# ── Helpers ─────────────────────────────────────────────────────────────────────

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
    return {
        "items": items,
        "total": total,
        "skip": skip,
        "limit": limit,
    }


def _run_hospital_command(
    *,
    operation: str,
    resource_type: str,
    resource_id: int,
    state_before: str,
    version_before: int,
    current_user: LabUser,
    db: Session,
    if_match: str | None,
    idempotency_key: str | None,
    mutation,
):
    """Run a state-changing hospital command with durable safety evidence."""
    guard = ClinicalCommandGuard(
        db,
        actor_user_id=current_user.id,
        lab_id=current_user.lab_id,
        actor_role=current_user.role,
    )
    guard.require_expected_version(if_match, current_version=version_before, resource_name=resource_type)
    key = guard.require_idempotency_key(idempotency_key)
    receipt = guard.claim(
        operation=operation,
        resource_type=resource_type,
        resource_id=resource_id,
        idempotency_key=key,
        payload={"if_match": if_match},
    )
    try:
        result, state_after, version_after = mutation()
        guard.complete(
            receipt,
            resource_type=resource_type,
            resource_id=resource_id,
            state_before=state_before,
            state_after=state_after,
            version_before=version_before,
            version_after=version_after,
        )
        db.commit()
    except (HTTPException, ConflictError, NotFoundError) as exc:
        db.rollback()
        guard.reject(
            operation=operation,
            resource_type=resource_type,
            resource_id=resource_id,
            state_before=state_before,
            version_before=version_before,
            reason=str(getattr(exc, "detail", exc)),
        )
        db.commit()
        if isinstance(exc, HTTPException):
            raise
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return result


# ── Hospital CRUD ──────────────────────────────────────────────────────────────


@router.get("/", summary="List hospitals")
def list_hospitals(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: LabUser = Depends(get_current_user),
):
    hospitals = HospitalService.list_hospitals(db, current_user.lab_id, skip, limit)
    total = db.query(HospitalMaster).filter(
        HospitalMaster.lab_id == current_user.lab_id,
        ~HospitalMaster.is_deleted,
    ).count()
    return _paginated_response(
        [_model_to_dict(h) for h in hospitals], total, skip, limit,
    )


@router.get("/{hospital_id}", summary="Get hospital")
def get_hospital(
    hospital_id: int,
    db: Session = Depends(get_db),
    current_user: LabUser = Depends(get_current_user),
):
    return _model_to_dict(HospitalService.get_hospital(db, hospital_id, current_user.lab_id))


@router.post("/", summary="Create hospital", status_code=201)
def create_hospital(
    body: HospitalCreate,
    db: Session = Depends(get_db),
    current_user: LabUser = Depends(get_current_user),
):
    hospital = HospitalService.create_hospital(
        db, current_user.lab_id, current_user.id, body.model_dump(),
        actor_role=current_user.role,
    )
    return _model_to_dict(hospital)


@router.put("/{hospital_id}", summary="Update hospital")
def update_hospital(
    hospital_id: int,
    body: HospitalUpdate,
    db: Session = Depends(get_db),
    current_user: LabUser = Depends(get_current_user),
):
    data = {k: v for k, v in body.model_dump().items() if v is not None}
    if not data:
        raise HTTPException(status_code=400, detail="No fields to update")
    hospital = HospitalService.update_hospital(
        db, hospital_id, current_user.lab_id, current_user.id, data,
        actor_role=current_user.role,
    )
    return _model_to_dict(hospital)


@router.delete("/{hospital_id}", summary="Deactivate hospital")
def deactivate_hospital(
    hospital_id: int,
    db: Session = Depends(get_db),
    current_user: LabUser = Depends(get_current_user),
):
    HospitalService.deactivate_hospital(
        db, hospital_id, current_user.lab_id, current_user.id,
        actor_role=current_user.role,
    )
    return {"detail": "Hospital deactivated", "detail_ar": "تم إلغاء تنشيط المستشفى"}


# ── Campus CRUD ────────────────────────────────────────────────────────────────


@router.get("/{hospital_id}/campuses", summary="List campuses")
def list_campuses(
    hospital_id: int,
    db: Session = Depends(get_db),
    current_user: LabUser = Depends(get_current_user),
):
    campuses = HospitalService.list_campuses(db, current_user.lab_id, hospital_id)
    return [_model_to_dict(c) for c in campuses]


@router.post("/{hospital_id}/campuses", summary="Create campus", status_code=201)
def create_campus(
    hospital_id: int,
    body: CampusCreate,
    db: Session = Depends(get_db),
    current_user: LabUser = Depends(get_current_user),
):
    campus = HospitalService.create_campus(
        db, current_user.lab_id, current_user.id, hospital_id, body.model_dump(),
        actor_role=current_user.role,
    )
    return _model_to_dict(campus)


@router.put("/campuses/{campus_id}", summary="Update campus")
def update_campus(
    campus_id: int,
    body: CampusCreate,
    db: Session = Depends(get_db),
    current_user: LabUser = Depends(get_current_user),
):
    campus = HospitalService._get_entity(db, Campus, campus_id, current_user.lab_id)
    data = body.model_dump()
    for k, v in data.items():
        setattr(campus, k, v)
    db.flush()
    return _model_to_dict(campus)


# ── Building CRUD ──────────────────────────────────────────────────────────────


@router.get("/campuses/{campus_id}/buildings", summary="List buildings")
def list_buildings(
    campus_id: int,
    db: Session = Depends(get_db),
    current_user: LabUser = Depends(get_current_user),
):
    buildings = HospitalService.list_buildings(db, current_user.lab_id, campus_id)
    return [_model_to_dict(b) for b in buildings]


@router.post("/campuses/{campus_id}/buildings", summary="Create building", status_code=201)
def create_building(
    campus_id: int,
    body: BuildingCreate,
    db: Session = Depends(get_db),
    current_user: LabUser = Depends(get_current_user),
):
    building = HospitalService.create_building(
        db, current_user.lab_id, current_user.id, campus_id, body.model_dump(),
    )
    return _model_to_dict(building)


# ── Floor CRUD ─────────────────────────────────────────────────────────────────


@router.get("/buildings/{building_id}/floors", summary="List floors")
def list_floors(
    building_id: int,
    db: Session = Depends(get_db),
    current_user: LabUser = Depends(get_current_user),
):
    floors = HospitalService.list_floors(db, current_user.lab_id, building_id)
    return [_model_to_dict(f) for f in floors]


@router.post("/buildings/{building_id}/floors", summary="Create floor", status_code=201)
def create_floor(
    building_id: int,
    body: FloorCreate,
    db: Session = Depends(get_db),
    current_user: LabUser = Depends(get_current_user),
):
    floor = HospitalService.create_floor(
        db, current_user.lab_id, current_user.id, building_id, body.model_dump(),
    )
    return _model_to_dict(floor)


# ── Department CRUD ────────────────────────────────────────────────────────────


@router.get("/{hospital_id}/departments", summary="List departments")
def list_departments(
    hospital_id: int,
    parent_id: int | None = Query(None),
    db: Session = Depends(get_db),
    current_user: LabUser = Depends(get_current_user),
):
    depts = HospitalService.list_departments(
        db, current_user.lab_id, hospital_id, parent_id,
    )
    return [_model_to_dict(d) for d in depts]


@router.post("/{hospital_id}/departments", summary="Create department", status_code=201)
def create_department(
    hospital_id: int,
    body: DepartmentCreate,
    db: Session = Depends(get_db),
    current_user: LabUser = Depends(get_current_user),
):
    dept = HospitalService.create_department(
        db, current_user.lab_id, current_user.id, hospital_id, body.model_dump(),
    )
    return _model_to_dict(dept)


@router.put("/departments/{dept_id}", summary="Update department")
def update_department(
    dept_id: int,
    body: DepartmentCreate,
    db: Session = Depends(get_db),
    current_user: LabUser = Depends(get_current_user),
):
    dept = HospitalService._get_entity(db, HospitalDepartment, dept_id, current_user.lab_id)
    data = body.model_dump()
    for k, v in data.items():
        setattr(dept, k, v)
    db.flush()
    return _model_to_dict(dept)


# ── Clinic CRUD ────────────────────────────────────────────────────────────────


@router.get("/departments/{dept_id}/clinics", summary="List clinics")
def list_clinics(
    dept_id: int | None = None,
    db: Session = Depends(get_db),
    current_user: LabUser = Depends(get_current_user),
):
    clinics = HospitalService.list_clinics(db, current_user.lab_id, dept_id)
    return [_model_to_dict(c) for c in clinics]


@router.post("/departments/{dept_id}/clinics", summary="Create clinic", status_code=201)
def create_clinic(
    dept_id: int,
    body: ClinicCreate,
    db: Session = Depends(get_db),
    current_user: LabUser = Depends(get_current_user),
):
    clinic = HospitalService.create_clinic(
        db, current_user.lab_id, current_user.id, dept_id, body.model_dump(),
    )
    return _model_to_dict(clinic)


# ── Room CRUD ──────────────────────────────────────────────────────────────────


@router.get("/departments/{dept_id}/rooms", summary="List rooms")
def list_rooms(
    dept_id: int | None = None,
    room_type: str | None = Query(None),
    db: Session = Depends(get_db),
    current_user: LabUser = Depends(get_current_user),
):
    rooms = HospitalService.list_rooms(db, current_user.lab_id, dept_id, room_type)
    return [_model_to_dict(r) for r in rooms]


@router.post("/departments/{dept_id}/rooms", summary="Create room", status_code=201)
def create_room(
    dept_id: int,
    body: RoomCreate,
    db: Session = Depends(get_db),
    current_user: LabUser = Depends(get_current_user),
):
    room = HospitalService.create_room(
        db, current_user.lab_id, current_user.id, dept_id, body.model_dump(),
    )
    return _model_to_dict(room)


# ── Bed CRUD ───────────────────────────────────────────────────────────────────


@router.get("/rooms/{room_id}/beds", summary="List beds")
def list_beds(
    room_id: int | None = None,
    status: str | None = Query(None),
    bed_type: str | None = Query(None),
    db: Session = Depends(get_db),
    current_user: LabUser = Depends(get_current_user),
):
    beds = HospitalService.list_beds(db, current_user.lab_id, room_id, status, bed_type)
    return [_model_to_dict(b) for b in beds]


@router.post("/rooms/{room_id}/beds", summary="Create bed", status_code=201)
def create_bed(
    room_id: int,
    body: BedCreate,
    db: Session = Depends(get_db),
    current_user: LabUser = Depends(get_current_user),
):
    bed = HospitalService.create_bed(
        db, current_user.lab_id, current_user.id, room_id, body.model_dump(),
    )
    return _model_to_dict(bed)


# ── Bed Assignment Operations ──────────────────────────────────────────────────


@router.post("/beds/{bed_id}/assign", summary="Assign patient to bed")
def assign_bed(
    bed_id: int,
    body: BedAssign,
    db: Session = Depends(get_db),
    current_user: LabUser = Depends(get_current_user),
    if_match: str | None = Header(None, alias="If-Match"),
    idempotency_key: str | None = Header(None, alias="Idempotency-Key"),
):
    bed = HospitalService._get_entity(db, Bed, bed_id, current_user.lab_id)
    assigned = _run_hospital_command(
        operation="hospital.bed.assign",
        resource_type="hospital_bed",
        resource_id=bed_id,
        state_before=bed.status,
        version_before=bed.version,
        current_user=current_user,
        db=db,
        if_match=if_match,
        idempotency_key=idempotency_key,
        mutation=lambda: (
            HospitalService.assign_bed(
                db,
                current_user.lab_id,
                current_user.id,
                bed_id,
                body.patient_id,
                expected_version=bed.version,
                reason=body.reason,
                diagnosis=body.diagnosis,
            ),
            "occupied",
            bed.version,
        ),
    )
    return _model_to_dict(assigned)


@router.post("/beds/{bed_id}/discharge", summary="Discharge patient from bed")
def discharge_bed(
    bed_id: int,
    body: BedDischarge,
    db: Session = Depends(get_db),
    current_user: LabUser = Depends(get_current_user),
    if_match: str | None = Header(None, alias="If-Match"),
    idempotency_key: str | None = Header(None, alias="Idempotency-Key"),
):
    bed = HospitalService._get_entity(db, Bed, bed_id, current_user.lab_id)
    discharged = _run_hospital_command(
        operation="hospital.bed.discharge",
        resource_type="hospital_bed",
        resource_id=bed_id,
        state_before=bed.status,
        version_before=bed.version,
        current_user=current_user,
        db=db,
        if_match=if_match,
        idempotency_key=idempotency_key,
        mutation=lambda: (
            HospitalService.discharge_bed(
                db,
                current_user.lab_id,
                current_user.id,
                bed_id,
                expected_version=bed.version,
                discharge_reason=body.discharge_reason,
            ),
            "cleaning",
            bed.version,
        ),
    )
    return _model_to_dict(discharged)


@router.post("/beds/{bed_id}/transfer", summary="Transfer patient to another bed")
def transfer_bed(
    bed_id: int,
    body: BedTransfer,
    db: Session = Depends(get_db),
    current_user: LabUser = Depends(get_current_user),
    if_match: str | None = Header(None, alias="If-Match"),
    target_if_match: str | None = Header(None, alias="X-Target-Bed-If-Match"),
    idempotency_key: str | None = Header(None, alias="Idempotency-Key"),
):
    source = HospitalService._get_entity(db, Bed, bed_id, current_user.lab_id)
    target = HospitalService._get_entity(db, Bed, body.to_bed_id, current_user.lab_id)
    ClinicalCommandGuard.require_expected_version(
        target_if_match,
        current_version=target.version,
        resource_name="target hospital bed",
    )
    return _run_hospital_command(
        operation="hospital.bed.transfer",
        resource_type="hospital_bed",
        resource_id=bed_id,
        state_before=source.status,
        version_before=source.version,
        current_user=current_user,
        db=db,
        if_match=if_match,
        idempotency_key=idempotency_key,
        mutation=lambda: (
            HospitalService.transfer_bed(
                db,
                current_user.lab_id,
                current_user.id,
                bed_id,
                body.to_bed_id,
                from_expected_version=source.version,
                to_expected_version=target.version,
                reason=body.reason,
            ),
            "cleaning",
            source.version,
        ),
    )


# ── Occupancy ──────────────────────────────────────────────────────────────────


@router.get("/occupancy", summary="Bed occupancy dashboard")
def occupancy_stats(
    hospital_id: int | None = Query(None),
    db: Session = Depends(get_db),
    current_user: LabUser = Depends(get_current_user),
):
    return HospitalService.bed_occupancy_stats(db, current_user.lab_id, hospital_id)


# ── Unit CRUD ──────────────────────────────────────────────────────────────────


@router.get("/{hospital_id}/units", summary="List units")
def list_units(
    hospital_id: int,
    db: Session = Depends(get_db),
    current_user: LabUser = Depends(get_current_user),
):
    units = HospitalService.list_units(db, current_user.lab_id, hospital_id)
    return [_model_to_dict(u) for u in units]


@router.post("/{hospital_id}/units", summary="Create unit", status_code=201)
def create_unit(
    hospital_id: int,
    body: UnitCreate,
    db: Session = Depends(get_db),
    current_user: LabUser = Depends(get_current_user),
):
    unit = HospitalService.create_unit(
        db, current_user.lab_id, current_user.id, hospital_id, body.model_dump(),
    )
    return _model_to_dict(unit)


# ── Operation Theater CRUD ─────────────────────────────────────────────────────


@router.get("/{hospital_id}/operation-theaters", summary="List operation theaters")
def list_operation_theaters(
    hospital_id: int,
    db: Session = Depends(get_db),
    current_user: LabUser = Depends(get_current_user),
):
    ots = HospitalService.list_operation_theaters(db, current_user.lab_id, hospital_id)
    return [_model_to_dict(ot) for ot in ots]


@router.post("/{hospital_id}/operation-theaters", summary="Create operation theater", status_code=201)
def create_operation_theater(
    hospital_id: int,
    body: OperationTheaterCreate,
    db: Session = Depends(get_db),
    current_user: LabUser = Depends(get_current_user),
):
    ot = HospitalService.create_ot(
        db, current_user.lab_id, current_user.id, hospital_id, body.model_dump(),
    )
    return _model_to_dict(ot)


@router.post(
    "/operation-theaters/{ot_id}/surgical-safety-checklists",
    summary="Complete surgical safety checklist",
    status_code=201,
)
def complete_surgical_safety_checklist(
    ot_id: int,
    body: SurgicalSafetyChecklistComplete,
    db: Session = Depends(get_db),
    current_user: LabUser = Depends(get_current_user),
    if_match: str | None = Header(None, alias="If-Match"),
    idempotency_key: str | None = Header(None, alias="Idempotency-Key"),
):
    theater = HospitalService._get_entity(db, OperationTheater, ot_id, current_user.lab_id)
    checklist = _run_hospital_command(
        # ``clinical.`` + this name is the audit action, and ``audit_logs.action`` is
        # varchar(50); the longer ``hospital.surgical_safety_checklist.complete`` made
        # that 52 characters, so the audit write — and the whole command — failed.
        operation="hospital.safety_checklist.complete",
        resource_type="hospital_operation_theater",
        resource_id=ot_id,
        state_before=theater.status,
        version_before=theater.version,
        current_user=current_user,
        db=db,
        if_match=if_match,
        idempotency_key=idempotency_key,
        mutation=lambda: (
            HospitalService.complete_surgical_safety_checklist(
                db,
                current_user.lab_id,
                current_user.id,
                {"operation_theater_id": ot_id, **body.model_dump()},
            ),
            theater.status,
            theater.version,
        ),
    )
    return _model_to_dict(checklist)


@router.put("/operation-theaters/{ot_id}/status", summary="Update operation theater status")
def update_ot_status(
    ot_id: int,
    body: OperationTheaterStatusUpdate,
    db: Session = Depends(get_db),
    current_user: LabUser = Depends(get_current_user),
    if_match: str | None = Header(None, alias="If-Match"),
    idempotency_key: str | None = Header(None, alias="Idempotency-Key"),
):
    theater = HospitalService._get_entity(db, OperationTheater, ot_id, current_user.lab_id)
    if body.status not in {"available", "in_use", "cleaning", "maintenance"}:
        raise HTTPException(status_code=400, detail="Unsupported operation theater status")
    updated = _run_hospital_command(
        operation="hospital.operation_theater.status_change",
        resource_type="hospital_operation_theater",
        resource_id=ot_id,
        state_before=theater.status,
        version_before=theater.version,
        current_user=current_user,
        db=db,
        if_match=if_match,
        idempotency_key=idempotency_key,
        mutation=lambda: (
            HospitalService.update_operation_theater_status(
                db,
                current_user.lab_id,
                current_user.id,
                ot_id,
                expected_version=theater.version,
                next_status=body.status,
                surgery_id=body.surgery_id,
            ),
            body.status,
            theater.version,
        ),
    )
    return _model_to_dict(updated)


# ── Medical Equipment CRUD ─────────────────────────────────────────────────────


@router.get("/{hospital_id}/equipment", summary="List medical equipment")
def list_equipment(
    hospital_id: int,
    category: str | None = Query(None),
    equipment_status: str | None = Query(None, alias="status"),
    db: Session = Depends(get_db),
    current_user: LabUser = Depends(get_current_user),
):
    equipment = HospitalService.list_equipment(
        db, current_user.lab_id, hospital_id, category, equipment_status,
    )
    return [_model_to_dict(e) for e in equipment]


@router.post("/{hospital_id}/equipment", summary="Create medical equipment", status_code=201)
def create_equipment(
    hospital_id: int,
    body: EquipmentCreate,
    db: Session = Depends(get_db),
    current_user: LabUser = Depends(get_current_user),
):
    equip = HospitalService.create_equipment(
        db, current_user.lab_id, current_user.id, hospital_id, body.model_dump(),
    )
    return _model_to_dict(equip)


@router.put("/equipment/{equip_id}", summary="Update medical equipment")
def update_equipment(
    equip_id: int,
    body: EquipmentCreate,
    db: Session = Depends(get_db),
    current_user: LabUser = Depends(get_current_user),
):
    equip = HospitalService._get_entity(db, MedicalEquipment, equip_id, current_user.lab_id)
    for k, v in body.model_dump().items():
        if v is not None:
            setattr(equip, k, v)
    db.flush()
    return _model_to_dict(equip)


# ── Cost Center CRUD ───────────────────────────────────────────────────────────


@router.get("/{hospital_id}/cost-centers", summary="List cost centers")
def list_cost_centers(
    hospital_id: int,
    db: Session = Depends(get_db),
    current_user: LabUser = Depends(get_current_user),
):
    ccs = HospitalService.list_cost_centers(db, current_user.lab_id, hospital_id)
    return [_model_to_dict(cc) for cc in ccs]


@router.post("/{hospital_id}/cost-centers", summary="Create cost center", status_code=201)
def create_cost_center(
    hospital_id: int,
    body: CostCenterCreate,
    db: Session = Depends(get_db),
    current_user: LabUser = Depends(get_current_user),
):
    cc = HospitalService.create_cost_center(
        db, current_user.lab_id, current_user.id, hospital_id, body.model_dump(),
    )
    return _model_to_dict(cc)


# ── Appointment management ─────────────────────────────────────────────────────


@router.get("/appointments", summary="List hospital appointments")
def list_appointments(
    hospital_id: int | None = Query(None),
    patient_id: int | None = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: LabUser = Depends(get_current_user),
):
    appointments = HospitalService.list_appointments(
        db, current_user.lab_id, hospital_id, patient_id, skip, limit,
    )
    return _paginated_response(
        [_model_to_dict(a) for a in appointments],
        len(appointments), skip, limit,
    )


@router.post("/appointments", summary="Create hospital appointment", status_code=201)
def create_appointment(
    body: AppointmentCreate,
    db: Session = Depends(get_db),
    current_user: LabUser = Depends(get_current_user),
):
    apt = HospitalService.create_appointment(
        db, current_user.lab_id, current_user.id, body.model_dump(),
        actor_role=current_user.role,
    )
    return _model_to_dict(apt)


# ── Dashboard / KPIs ───────────────────────────────────────────────────────────


@router.get("/{hospital_id}/dashboard", summary="Hospital KPIs dashboard")
def hospital_dashboard(
    hospital_id: int,
    db: Session = Depends(get_db),
    current_user: LabUser = Depends(get_current_user),
):
    return HospitalService.dashboard(db, current_user.lab_id, hospital_id)


# ── Bed Assignment History ─────────────────────────────────────────────────────


@router.get("/beds/{bed_id}/assignments", summary="Bed assignment history")
def bed_assignment_history(
    bed_id: int,
    db: Session = Depends(get_db),
    current_user: LabUser = Depends(get_current_user),
):
    HospitalService._get_entity(db, Bed, bed_id, current_user.lab_id)
    assignments = db.query(BedAssignment).filter(
        BedAssignment.bed_id == bed_id,
        BedAssignment.lab_id == current_user.lab_id,
        ~BedAssignment.is_deleted,
    ).order_by(BedAssignment.admission_date.desc()).all()
    return [_model_to_dict(a) for a in assignments]
