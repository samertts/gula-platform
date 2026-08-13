from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import or_
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app._compat import UTC
from app.database import get_db
from app.models.lab_user import LabUser
from app.models.patient import Patient
from app.radiology.clinical_read_gate import ClinicalRadiologyReadDenied, ClinicalRadiologyReadGate
from app.radiology.device import (
    DeviceMonitoringService,
    ModalityWorklistService,
    MPPSHandler,
)
from app.radiology.enums import ExamStatus
from app.radiology.pacs import (
    DICOMStorageService,
    DICOMStudyService,
    ImageSharingService,
    ImageViewerService,
)
from app.radiology.services import RadiologyService
from app.security.dependencies import get_current_user

logger = logging.getLogger("gula.radiology.routes")

router = APIRouter(prefix="/radiology", tags=["radiology"])


# ==============================================================================
# Pydantic schemas
# ==============================================================================


class RadiologyOrderCreate(BaseModel):
    patient_id: str
    encounter_id: str | None = None
    ordering_provider_id: str | None = None
    modality: str
    body_part: str | None = None
    clinical_indication: str | None = None
    diagnosis_code: str | None = None
    diagnosis_system: str | None = None
    priority: str = "routine"
    ordering_department_id: str | None = None
    notes: str | None = None
    metadata: dict[str, Any] = {}


class RadiologyAppointmentCreate(BaseModel):
    order_id: str
    patient_id: str
    scheduled_date: str
    scheduled_time: str | None = None
    duration_minutes: int = 30
    modality: str
    room: str | None = None
    technologist_id: str | None = None
    preparation_instructions: str | None = None
    contrast_required: bool = False
    contrast_details: str | None = None
    notes: str | None = None
    metadata: dict[str, Any] = {}


class RadiologyExamCreate(BaseModel):
    order_id: str | None = None
    appointment_id: str | None = None
    patient_id: str
    accession_number: str | None = None
    modality: str
    body_part: str | None = None
    laterality: str | None = None
    protocol_id: str | None = None
    exam_code: str | None = None
    exam_name: str | None = None
    technologist_id: str | None = None
    radiologist_id: str | None = None
    metadata: dict[str, Any] = {}


class RadiologyExamImagesUpdate(BaseModel):
    images_count: int
    series_count: int


class RadiologyExamStatusUpdate(BaseModel):
    status: ExamStatus


class ProtocolCreate(BaseModel):
    code: str
    name: str
    name_ar: str | None = None
    modality: str
    body_part: str | None = None
    protocol_type: str = "standard"
    contrast_protocol: str | None = None
    typical_duration: int | None = None
    typical_dose: str | None = None
    preparation_instructions: str | None = None
    positioning_instructions: str | None = None
    series_parameters: dict[str, Any] = {}
    metadata: dict[str, Any] = {}


class RadiologyReportCreate(BaseModel):
    exam_id: str
    accession_number: str
    patient_id: str
    radiologist_id: str | None = None
    ordering_provider_id: str | None = None
    clinical_indication: str | None = None
    technique: str | None = None
    comparison: str | None = None
    findings: str | None = None
    impression: str | None = None
    conclusion: str | None = None
    recommendation: str | None = None
    body_text: str | None = None
    transcribed_by: str | None = None
    metadata: dict[str, Any] = {}


class RadiologyReportDraftUpdate(BaseModel):
    findings: str | None = None
    impression: str | None = None
    conclusion: str | None = None
    recommendation: str | None = None
    body_text: str | None = None


class RadiologyReportFinalize(BaseModel):
    radiologist_id: str | None = None


class RadiologyReportAmend(BaseModel):
    findings: str
    impression: str
    conclusion: str | None = None
    recommendation: str | None = None
    amended_by: str | None = None


class ReportTemplateCreate(BaseModel):
    template_code: str
    template_name: str
    template_name_ar: str | None = None
    modality: str | None = None
    body_part: str | None = None
    structured_template: dict[str, Any] = {}
    metadata: dict[str, Any] = {}


class CriticalFindingCreate(BaseModel):
    exam_id: str
    report_id: str | None = None
    finding_type: str
    finding_description: str
    notified_by: str | None = None
    notified_to: str | None = None
    notes: str | None = None
    metadata: dict[str, Any] = {}


class CriticalFindingAcknowledge(BaseModel):
    acknowledged_by: str
    notes: str | None = None


class CriticalFindingNotify(BaseModel):
    notified_by: str
    notified_to: str


class ImageShareCreate(BaseModel):
    study_uid: str
    shared_with: str | None = None
    share_type: str = "link"
    expires_in_hours: int = 48
    metadata: dict[str, Any] = {}


class ModalityDeviceCreate(BaseModel):
    device_id: str
    device_name: str
    device_model: str | None = None
    manufacturer: str | None = None
    modality_type: str
    site_name: str | None = None
    department_id: str | None = None
    ip_address: str | None = None
    ae_title: str | None = None
    port: int | None = None
    dicom_protocol: str | None = None
    software_version: str | None = None
    serial_number: str | None = None
    metadata: dict[str, Any] = {}


class DeviceStatusUpdate(BaseModel):
    status: str


class MPPSReceive(BaseModel):
    accession_number: str
    status: str
    series_count: int | None = None
    images_count: int | None = None
    performed_steps: list[dict[str, Any]] = []
    notes: str | None = None
    metadata: dict[str, Any] = {}


class OrderStatusUpdate(BaseModel):
    status: str


# ==============================================================================
# Helper
# ==============================================================================


def _to_dict(obj: Any) -> dict[str, Any]:
    if hasattr(obj, "to_dict"):
        return obj.to_dict()
    return {}


def _get_radiology_service(db: Session) -> RadiologyService:
    return RadiologyService(db)


def _get_storage_service(db: Session) -> DICOMStorageService:
    return DICOMStorageService(db)


def _get_study_service(db: Session) -> DICOMStudyService:
    return DICOMStudyService(db)


def _patient_for_user(db: Session, current_user: LabUser, patient_id: str) -> Patient:
    conditions = [Patient.health_id == patient_id]
    try:
        conditions.append(Patient.id == int(patient_id))
    except (TypeError, ValueError):
        pass
    patient = db.query(Patient).filter(
        Patient.lab_id == current_user.lab_id,
        or_(*conditions),
    ).first()
    if patient is None:
        raise HTTPException(status_code=404, detail="Patient not found in the current laboratory")
    return patient


def _tenant_patient_keys(db: Session, current_user: LabUser) -> set[str]:
    rows = db.query(Patient.id, Patient.health_id).filter(Patient.lab_id == current_user.lab_id).all()
    keys: set[str] = set()
    for patient_id, health_id in rows:
        keys.add(str(patient_id))
        if health_id:
            keys.add(str(health_id))
    return keys


def _critical_finding_for_user(db: Session, current_user: LabUser, finding_id: str):
    svc = _get_radiology_service(db)
    finding = svc.get_critical_finding(finding_id)
    if finding is None:
        raise HTTPException(status_code=404, detail="Critical finding not found")
    exam = svc.get_exam(finding.exam_id)
    if exam is None:
        raise HTTPException(status_code=404, detail="Critical finding not found")
    _patient_for_user(db, current_user, exam.patient_id)
    return finding


def _study_for_user(db: Session, current_user: LabUser, study_uid: str):
    study = _get_study_service(db).get_study(study_uid)
    if study is None:
        raise HTTPException(status_code=404, detail="Study not found")
    _patient_for_user(db, current_user, study.patient_id)
    return study


# ==============================================================================
# Order & Scheduling
# ==============================================================================


@router.post("/orders", status_code=201)
def create_order(
    data: RadiologyOrderCreate,
    db: Session = Depends(get_db),
    current_user: LabUser = Depends(get_current_user),
):
    _patient_for_user(db, current_user, data.patient_id)
    svc = _get_radiology_service(db)
    order = svc.create_order(
        patient_id=data.patient_id,
        encounter_id=data.encounter_id,
        ordering_provider_id=data.ordering_provider_id,
        modality=data.modality,
        body_part=data.body_part,
        clinical_indication=data.clinical_indication,
        diagnosis_code=data.diagnosis_code,
        diagnosis_system=data.diagnosis_system,
        priority=data.priority,
        ordering_department_id=data.ordering_department_id,
        notes=data.notes,
        metadata=data.metadata,
    )
    return _to_dict(order)


@router.get("/orders")
def list_orders(
    patient_id: str | None = None,
    modality: str | None = None,
    status: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    priority: str | None = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: LabUser = Depends(get_current_user),
):
    if patient_id:
        _patient_for_user(db, current_user, patient_id)
    svc = _get_radiology_service(db)
    tenant_patient_ids = _tenant_patient_keys(db, current_user)
    from_ = datetime.fromisoformat(date_from) if date_from else None
    to_ = datetime.fromisoformat(date_to) if date_to else None
    orders = svc.search_orders(
        patient_id=patient_id,
        modality=modality,
        status=status,
        date_from=from_,
        date_to=to_,
        priority=priority,
        skip=skip,
        limit=limit,
        patient_ids=tenant_patient_ids,
    )
    return {"items": [_to_dict(o) for o in orders], "total": len(orders), "skip": skip, "limit": limit}


@router.get("/clinical/orders")
def list_clinical_orders(
    patient_id: str | None = None,
    modality: str | None = None,
    status: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    priority: str | None = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: LabUser = Depends(get_current_user),
):
    """List radiology orders only after an exact clinical scope and policy decision.

    This is deliberately a read-only adapter. It does not reinterpret a legacy
    lab identifier as a facility identifier; the gate resolves the explicit
    bridge and authorizes the canonical person, assignment, organization, and
    facility before the established laboratory-scoped query executes.
    """
    try:
        ClinicalRadiologyReadGate().authorize(db=db, lab_user=current_user)
    except ClinicalRadiologyReadDenied as exc:
        raise HTTPException(status_code=403, detail="Clinical radiology access is not permitted") from exc

    return list_orders(
        patient_id=patient_id,
        modality=modality,
        status=status,
        date_from=date_from,
        date_to=date_to,
        priority=priority,
        skip=skip,
        limit=limit,
        db=db,
        current_user=current_user,
    )


@router.get("/orders/search")
def search_orders(
    patient_id: str | None = None,
    modality: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    status: str | None = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: LabUser = Depends(get_current_user),
):
    if patient_id:
        _patient_for_user(db, current_user, patient_id)
    svc = _get_radiology_service(db)
    tenant_patient_ids = _tenant_patient_keys(db, current_user)
    from_ = datetime.fromisoformat(date_from) if date_from else None
    to_ = datetime.fromisoformat(date_to) if date_to else None
    orders = svc.search_orders(
        patient_id=patient_id,
        modality=modality,
        status=status,
        date_from=from_,
        date_to=to_,
        skip=skip,
        limit=limit,
        patient_ids=tenant_patient_ids,
    )
    return {"items": [_to_dict(o) for o in orders], "total": len(orders), "skip": skip, "limit": limit}


@router.get("/orders/{order_id}")
def get_order(
    order_id: str,
    db: Session = Depends(get_db),
    current_user: LabUser = Depends(get_current_user),
):
    svc = _get_radiology_service(db)
    order = svc.get_order(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    _patient_for_user(db, current_user, order.patient_id)
    return _to_dict(order)


@router.put("/orders/{order_id}/status")
def update_order_status(
    order_id: str,
    data: OrderStatusUpdate,
    db: Session = Depends(get_db),
    current_user: LabUser = Depends(get_current_user),
):
    svc = _get_radiology_service(db)
    order = svc.get_order(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    _patient_for_user(db, current_user, order.patient_id)
    updated = svc.update_order_status(order_id, data.status)
    if not updated:
        raise HTTPException(status_code=404, detail="Order not found")
    return _to_dict(updated)



@router.get("/appointments")
def list_appointments(
    patient_id: str | None = None,
    modality: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    status: str | None = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: LabUser = Depends(get_current_user),
):
    if patient_id:
        _patient_for_user(db, current_user, patient_id)
    svc = _get_radiology_service(db)
    tenant_patient_ids = _tenant_patient_keys(db, current_user)
    from_ = datetime.fromisoformat(date_from) if date_from else None
    to_ = datetime.fromisoformat(date_to) if date_to else None
    apps = svc.list_appointments(
        patient_id=patient_id,
        modality=modality,
        date_from=from_,
        date_to=to_,
        status=status,
        skip=skip,
        limit=limit,
        patient_ids=tenant_patient_ids,
    )
    return {"items": [_to_dict(a) for a in apps], "total": len(apps), "skip": skip, "limit": limit}


@router.post("/appointments", status_code=201)
def create_appointment(
    data: RadiologyAppointmentCreate,
    db: Session = Depends(get_db),
    current_user: LabUser = Depends(get_current_user),
):
    _patient_for_user(db, current_user, data.patient_id)
    svc = _get_radiology_service(db)
    appt = svc.schedule_appointment(
        order_id=data.order_id,
        patient_id=data.patient_id,
        scheduled_date=datetime.fromisoformat(data.scheduled_date) if isinstance(data.scheduled_date, str) else data.scheduled_date,
        scheduled_time=data.scheduled_time,
        duration_minutes=data.duration_minutes,
        modality=data.modality,
        room=data.room,
        technologist_id=data.technologist_id,
        preparation_instructions=data.preparation_instructions,
        contrast_required=data.contrast_required,
        contrast_details=data.contrast_details,
        notes=data.notes,
        metadata=data.metadata,
    )
    return _to_dict(appt)


@router.put("/appointments/{appointment_id}/checkin")
def checkin_appointment(
    appointment_id: str,
    db: Session = Depends(get_db),
    current_user: LabUser = Depends(get_current_user),
):
    svc = _get_radiology_service(db)
    appt = svc.get_appointment(appointment_id)
    if not appt:
        raise HTTPException(status_code=404, detail="Appointment not found")
    _patient_for_user(db, current_user, appt.patient_id)
    appt = svc.check_in_appointment(appointment_id)
    if not appt:
        raise HTTPException(status_code=404, detail="Appointment not found")
    return _to_dict(appt)


@router.put("/appointments/{appointment_id}/arrive")
def arrive_appointment(
    appointment_id: str,
    db: Session = Depends(get_db),
    current_user: LabUser = Depends(get_current_user),
):
    svc = _get_radiology_service(db)
    appt = svc.get_appointment(appointment_id)
    if not appt:
        raise HTTPException(status_code=404, detail="Appointment not found")
    _patient_for_user(db, current_user, appt.patient_id)
    appt = svc.arrive_appointment(appointment_id)
    if not appt:
        raise HTTPException(status_code=404, detail="Appointment not found")
    return _to_dict(appt)


@router.get("/appointments/{appointment_id}")
def get_appointment(
    appointment_id: str,
    db: Session = Depends(get_db),
    current_user: LabUser = Depends(get_current_user),
):
    svc = _get_radiology_service(db)
    appt = svc.get_appointment(appointment_id)
    if not appt:
        raise HTTPException(status_code=404, detail="Appointment not found")
    _patient_for_user(db, current_user, appt.patient_id)
    return _to_dict(appt)


# ==============================================================================
# Exam & Workflow
# ==============================================================================


@router.get("/exams")
def list_exams(
    patient_id: str | None = None,
    modality: str | None = None,
    status: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    technologist_id: str | None = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: LabUser = Depends(get_current_user),
):
    if patient_id:
        _patient_for_user(db, current_user, patient_id)
    svc = _get_radiology_service(db)
    tenant_patient_ids = _tenant_patient_keys(db, current_user)
    from_ = datetime.fromisoformat(date_from) if date_from else None
    to_ = datetime.fromisoformat(date_to) if date_to else None
    exams = svc.list_exams(
        patient_id=patient_id,
        modality=modality,
        status=status,
        date_from=from_,
        date_to=to_,
        technologist_id=technologist_id,
        skip=skip,
        limit=limit,
        patient_ids=tenant_patient_ids,
    )
    return {"items": [_to_dict(e) for e in exams], "total": len(exams), "skip": skip, "limit": limit}


@router.post("/exams", status_code=201)
def create_exam(
    data: RadiologyExamCreate,
    db: Session = Depends(get_db),
    current_user: LabUser = Depends(get_current_user),
):
    _patient_for_user(db, current_user, data.patient_id)
    svc = _get_radiology_service(db)
    exam = svc.create_exam(
        order_id=data.order_id,
        appointment_id=data.appointment_id,
        patient_id=data.patient_id,
        accession_number=data.accession_number,
        modality=data.modality,
        body_part=data.body_part,
        laterality=data.laterality,
        protocol_id=data.protocol_id,
        exam_code=data.exam_code,
        exam_name=data.exam_name,
        technologist_id=data.technologist_id,
        radiologist_id=data.radiologist_id,
        metadata=data.metadata,
    )
    return _to_dict(exam)


@router.get("/exams/{exam_id}")
def get_exam(
    exam_id: str,
    db: Session = Depends(get_db),
    current_user: LabUser = Depends(get_current_user),
):
    svc = _get_radiology_service(db)
    exam = svc.get_exam(exam_id)
    if not exam:
        raise HTTPException(status_code=404, detail="Exam not found")
    _patient_for_user(db, current_user, exam.patient_id)
    return _to_dict(exam)


@router.put("/exams/{exam_id}/status")
def update_exam_status(
    exam_id: str,
    data: RadiologyExamStatusUpdate,
    db: Session = Depends(get_db),
    current_user: LabUser = Depends(get_current_user),
):
    svc = _get_radiology_service(db)
    existing = svc.get_exam(exam_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Exam not found")
    _patient_for_user(db, current_user, existing.patient_id)
    exam = svc.update_exam_status(exam_id, data.status)
    if not exam:
        raise HTTPException(status_code=404, detail="Exam not found")
    return _to_dict(exam)


@router.put("/exams/{exam_id}/images")
def update_exam_images(
    exam_id: str,
    data: RadiologyExamImagesUpdate,
    db: Session = Depends(get_db),
    current_user: LabUser = Depends(get_current_user),
):
    svc = _get_radiology_service(db)
    existing = svc.get_exam(exam_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Exam not found")
    _patient_for_user(db, current_user, existing.patient_id)
    exam = svc.update_exam_images(exam_id, data.images_count, data.series_count)
    if not exam:
        raise HTTPException(status_code=404, detail="Exam not found")
    return _to_dict(exam)


@router.get("/technologist-worklist")
def technologist_worklist(
    modality: str | None = None,
    date: str | None = None,
    db: Session = Depends(get_db),
    current_user: LabUser = Depends(get_current_user),
):
    svc = _get_radiology_service(db)
    tenant_patient_ids = _tenant_patient_keys(db, current_user)
    date_ = datetime.fromisoformat(date) if date else datetime.now(UTC)
    exams = svc.get_technologist_worklist(modality=modality, date=date_, patient_ids=tenant_patient_ids)
    return {"items": [_to_dict(e) for e in exams], "total": len(exams)}


@router.get("/radiologist-worklist")
def radiologist_worklist(
    status: str | None = None,
    priority: str | None = None,
    db: Session = Depends(get_db),
    current_user: LabUser = Depends(get_current_user),
):
    svc = _get_radiology_service(db)
    tenant_patient_ids = _tenant_patient_keys(db, current_user)
    exams = svc.get_radiologist_worklist(status=status, priority=priority, patient_ids=tenant_patient_ids)
    return {"items": [_to_dict(e) for e in exams], "total": len(exams)}


@router.get("/worklist")
def modality_worklist(
    device_id: str | None = None,
    db: Session = Depends(get_db),
    current_user: LabUser = Depends(get_current_user),
):
    svc = _get_radiology_service(db)
    entries = svc.get_modality_worklist(
        modality_device_id=device_id,
        patient_ids=_tenant_patient_keys(db, current_user),
    )
    return {"items": [_to_dict(e) for e in entries], "total": len(entries)}


# ==============================================================================
# Protocols
# ==============================================================================


@router.get("/protocols")
def list_protocols(
    modality: str | None = None,
    body_part: str | None = None,
    db: Session = Depends(get_db),
    current_user: LabUser = Depends(get_current_user),
):
    svc = _get_radiology_service(db)
    protocols = svc.list_protocols(modality=modality, body_part=body_part)
    return {"items": [_to_dict(p) for p in protocols], "total": len(protocols)}


@router.post("/protocols", status_code=201)
def create_protocol(
    data: ProtocolCreate,
    db: Session = Depends(get_db),
    current_user: LabUser = Depends(get_current_user),
):
    svc = _get_radiology_service(db)
    protocol = svc.create_protocol(
        code=data.code,
        name=data.name,
        name_ar=data.name_ar,
        modality=data.modality,
        body_part=data.body_part,
        protocol_type=data.protocol_type,
        contrast_protocol=data.contrast_protocol,
        typical_duration=data.typical_duration,
        typical_dose=data.typical_dose,
        preparation_instructions=data.preparation_instructions,
        positioning_instructions=data.positioning_instructions,
        series_parameters=data.series_parameters,
        metadata=data.metadata,
    )
    return _to_dict(protocol)


@router.get("/protocols/{protocol_id}")
def get_protocol(
    protocol_id: str,
    db: Session = Depends(get_db),
    current_user: LabUser = Depends(get_current_user),
):
    svc = _get_radiology_service(db)
    protocol = svc.get_protocol(protocol_id)
    if not protocol:
        raise HTTPException(status_code=404, detail="Protocol not found")
    return _to_dict(protocol)


# ==============================================================================
# Reporting
# ==============================================================================


@router.get("/reports")
def list_reports(
    patient_id: str | None = None,
    radiologist_id: str | None = None,
    status: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: LabUser = Depends(get_current_user),
):
    if patient_id:
        _patient_for_user(db, current_user, patient_id)
    svc = _get_radiology_service(db)
    tenant_patient_ids = _tenant_patient_keys(db, current_user)
    from_ = datetime.fromisoformat(date_from) if date_from else None
    to_ = datetime.fromisoformat(date_to) if date_to else None
    reports = svc.search_reports(
        patient_id=patient_id,
        radiologist_id=radiologist_id,
        status=status,
        date_from=from_,
        date_to=to_,
        skip=skip,
        limit=limit,
        patient_ids=tenant_patient_ids,
    )
    return {"items": [_to_dict(r) for r in reports], "total": len(reports), "skip": skip, "limit": limit}


@router.get("/reports/search")
def search_reports(
    patient_id: str | None = None,
    radiologist_id: str | None = None,
    status: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    critical: bool | None = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: LabUser = Depends(get_current_user),
):
    if patient_id:
        _patient_for_user(db, current_user, patient_id)
    svc = _get_radiology_service(db)
    tenant_patient_ids = _tenant_patient_keys(db, current_user)
    from_ = datetime.fromisoformat(date_from) if date_from else None
    to_ = datetime.fromisoformat(date_to) if date_to else None
    reports = svc.search_reports(
        patient_id=patient_id,
        radiologist_id=radiologist_id,
        status=status,
        date_from=from_,
        date_to=to_,
        critical_finding=critical,
        skip=skip,
        limit=limit,
        patient_ids=tenant_patient_ids,
    )
    return {"items": [_to_dict(r) for r in reports], "total": len(reports), "skip": skip, "limit": limit}


@router.post("/reports", status_code=201)
def create_report(
    data: RadiologyReportCreate,
    db: Session = Depends(get_db),
    current_user: LabUser = Depends(get_current_user),
):
    _patient_for_user(db, current_user, data.patient_id)
    svc = _get_radiology_service(db)
    report = svc.create_report(
        exam_id=data.exam_id,
        accession_number=data.accession_number,
        patient_id=data.patient_id,
        radiologist_id=data.radiologist_id,
        ordering_provider_id=data.ordering_provider_id,
        clinical_indication=data.clinical_indication,
        technique=data.technique,
        comparison=data.comparison,
        findings=data.findings,
        impression=data.impression,
        conclusion=data.conclusion,
        recommendation=data.recommendation,
        body_text=data.body_text,
        transcribed_by=data.transcribed_by,
        metadata=data.metadata,
    )
    return _to_dict(report)


@router.get("/reports/{report_id}")
def get_report(
    report_id: str,
    db: Session = Depends(get_db),
    current_user: LabUser = Depends(get_current_user),
):
    svc = _get_radiology_service(db)
    report = svc.get_report(report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    _patient_for_user(db, current_user, report.patient_id)
    return _to_dict(report)


@router.put("/reports/{report_id}/draft")
def save_report_draft(
    report_id: str,
    data: RadiologyReportDraftUpdate,
    db: Session = Depends(get_db),
    current_user: LabUser = Depends(get_current_user),
):
    svc = _get_radiology_service(db)
    existing = svc.get_report(report_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Report not found")
    _patient_for_user(db, current_user, existing.patient_id)
    report = svc.save_report_draft(
        report_id=report_id,
        findings=data.findings,
        impression=data.impression,
        conclusion=data.conclusion,
        recommendation=data.recommendation,
        body_text=data.body_text,
    )
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    return _to_dict(report)


@router.put("/reports/{report_id}/finalize")
def finalize_report(
    report_id: str,
    data: RadiologyReportFinalize,
    db: Session = Depends(get_db),
    current_user: LabUser = Depends(get_current_user),
):
    svc = _get_radiology_service(db)
    existing = svc.get_report(report_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Report not found")
    _patient_for_user(db, current_user, existing.patient_id)
    report = svc.finalize_report(report_id, radiologist_id=data.radiologist_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    return _to_dict(report)


@router.put("/reports/{report_id}/amend")
def amend_report(
    report_id: str,
    data: RadiologyReportAmend,
    db: Session = Depends(get_db),
    current_user: LabUser = Depends(get_current_user),
):
    svc = _get_radiology_service(db)
    existing = svc.get_report(report_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Report not found")
    _patient_for_user(db, current_user, existing.patient_id)
    report = svc.amend_report(
        report_id=report_id,
        findings=data.findings,
        impression=data.impression,
        conclusion=data.conclusion,
        recommendation=data.recommendation,
        amended_by=data.amended_by,
    )
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    return _to_dict(report)


@router.put("/reports/{report_id}/verify")
def verify_report(
    report_id: str,
    db: Session = Depends(get_db),
    current_user: LabUser = Depends(get_current_user),
):
    svc = _get_radiology_service(db)
    existing = svc.get_report(report_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Report not found")
    _patient_for_user(db, current_user, existing.patient_id)
    report = svc.verify_report(report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    return _to_dict(report)



@router.get("/report-templates")
def list_report_templates(
    modality: str | None = None,
    body_part: str | None = None,
    db: Session = Depends(get_db),
    current_user: LabUser = Depends(get_current_user),
):
    svc = _get_radiology_service(db)
    templates = svc.list_report_templates(modality=modality, body_part=body_part)
    return {"items": [_to_dict(t) for t in templates], "total": len(templates)}


@router.post("/report-templates", status_code=201)
def create_report_template(
    data: ReportTemplateCreate,
    db: Session = Depends(get_db),
    current_user: LabUser = Depends(get_current_user),
):
    svc = _get_radiology_service(db)
    template = svc.create_report_template(
        template_code=data.template_code,
        template_name=data.template_name,
        template_name_ar=data.template_name_ar,
        modality=data.modality,
        body_part=data.body_part,
        structured_template=data.structured_template,
        metadata=data.metadata,
    )
    return _to_dict(template)


# ==============================================================================
# PACS
# ==============================================================================


@router.get("/studies/search")
def search_studies(
    patient_id: str | None = None,
    modality: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    accession_number: str | None = None,
    study_description: str | None = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: LabUser = Depends(get_current_user),
):
    if patient_id:
        _patient_for_user(db, current_user, patient_id)
    svc = _get_study_service(db)
    tenant_patient_ids = _tenant_patient_keys(db, current_user)
    from_ = datetime.fromisoformat(date_from) if date_from else None
    to_ = datetime.fromisoformat(date_to) if date_to else None
    studies = svc.search_studies(
        patient_id=patient_id,
        modality=modality,
        date_from=from_,
        date_to=to_,
        accession_number=accession_number,
        study_description=study_description,
        skip=skip,
        limit=limit,
        patient_ids=tenant_patient_ids,
    )
    return {"items": [_to_dict(s) for s in studies], "total": len(studies), "skip": skip, "limit": limit}


@router.get("/studies/{study_uid}")
def get_study(
    study_uid: str,
    db: Session = Depends(get_db),
    current_user: LabUser = Depends(get_current_user),
):
    study = _study_for_user(db, current_user, study_uid)
    return _to_dict(study)



@router.get("/studies/{study_uid}/series")
def get_study_series(
    study_uid: str,
    db: Session = Depends(get_db),
    current_user: LabUser = Depends(get_current_user),
):
    _study_for_user(db, current_user, study_uid)
    svc = _get_storage_service(db)
    instances = svc.get_study_instances(study_uid)
    series_set: dict[str, dict[str, Any]] = {}
    for inst in instances:
        uid = inst.series_instance_uid
        if uid not in series_set:
            series_set[uid] = {
                "series_instance_uid": uid,
                "modality": inst.modality.value if hasattr(inst.modality, "value") else str(inst.modality),
                "instance_count": 0,
            }
        series_set[uid]["instance_count"] += 1
    return {"items": list(series_set.values()), "total": len(series_set)}


@router.get("/studies/{study_uid}/series/{series_uid}/images")
def get_series_images(
    study_uid: str,
    series_uid: str,
    db: Session = Depends(get_db),
    current_user: LabUser = Depends(get_current_user),
):
    _study_for_user(db, current_user, study_uid)
    svc = _get_storage_service(db)
    instances = svc.get_series_instances(series_uid, study_instance_uid=study_uid)
    return {"items": [_to_dict(i) for i in instances], "total": len(instances)}


@router.get("/images/{image_uid}/view")
def view_image(
    image_uid: str,
    db: Session = Depends(get_db),
    current_user: LabUser = Depends(get_current_user),
):
    record = _get_storage_service(db).retrieve(image_uid)
    if not record:
        raise HTTPException(status_code=404, detail="Image not found")
    _patient_for_user(db, current_user, record.patient_id)
    viewer = ImageViewerService(db)
    url = viewer.get_streaming_url(image_uid)
    if not url:
        raise HTTPException(status_code=404, detail="Image not found")
    return {"streaming_url": url}


@router.get("/images/{image_uid}/download")
def download_image(
    image_uid: str,
    db: Session = Depends(get_db),
    current_user: LabUser = Depends(get_current_user),
):
    storage_svc = _get_storage_service(db)
    record = storage_svc.retrieve(image_uid)
    if not record:
        raise HTTPException(status_code=404, detail="Image not found")
    _patient_for_user(db, current_user, record.patient_id)
    return {
        "sop_instance_uid": record.sop_instance_uid,
        "file_path": record.file_path,
        "file_size": record.file_size,
        "storage_tier": record.storage_tier.value if hasattr(record.storage_tier, "value") else str(record.storage_tier),
    }


@router.post("/sharing/share", status_code=201)
def create_share(
    data: ImageShareCreate,
    db: Session = Depends(get_db),
    current_user: LabUser = Depends(get_current_user),
):
    _study_for_user(db, current_user, data.study_uid)
    sharing = ImageSharingService(db)
    share = sharing.create_share(
        study_uid=data.study_uid,
        shared_by="",
        shared_with=data.shared_with,
        share_type=data.share_type,
        expires_in_hours=data.expires_in_hours,
        metadata=data.metadata,
    )
    return _to_dict(share)


@router.delete("/sharing/{share_id}")
def revoke_share(
    share_id: str,
    db: Session = Depends(get_db),
    current_user: LabUser = Depends(get_current_user),
):
    sharing = ImageSharingService(db)
    share = sharing.get_share(share_id)
    if not share:
        raise HTTPException(status_code=404, detail="Share not found")
    _study_for_user(db, current_user, share.study_uid)
    revoked = sharing.revoke_share(share_id)
    if not revoked:
        raise HTTPException(status_code=404, detail="Share not found or already revoked")
    return {"status": "revoked", "share_id": share_id}


@router.get("/studies/{study_uid}/thumbnail")
def get_study_thumbnail(
    study_uid: str,
    size: int = Query(256, ge=32, le=1024),
    db: Session = Depends(get_db),
    current_user: LabUser = Depends(get_current_user),
):
    _study_for_user(db, current_user, study_uid)
    storage_svc = _get_storage_service(db)
    instances = storage_svc.get_study_instances(study_uid)
    if not instances:
        raise HTTPException(status_code=404, detail="No images found for this study")
    first = instances[0]
    viewer = ImageViewerService(db)
    url = viewer.get_thumbnail_url(first.sop_instance_uid, size=size)
    return {"thumbnail_url": url, "size": size}


# ==============================================================================
# Device
# ==============================================================================


@router.get("/devices")
def list_devices(
    modality_type: str | None = None,
    status: str | None = None,
    db: Session = Depends(get_db),
    current_user: LabUser = Depends(get_current_user),
):
    device_svc = DeviceMonitoringService(db)
    devices = device_svc.list_devices(modality_type=modality_type, status=status)
    return {"items": [_to_dict(d) for d in devices], "total": len(devices)}


@router.post("/devices", status_code=201)
def register_device(
    data: ModalityDeviceCreate,
    db: Session = Depends(get_db),
    current_user: LabUser = Depends(get_current_user),
):
    device_svc = DeviceMonitoringService(db)
    device = device_svc.register_device(
        device_id=data.device_id,
        device_name=data.device_name,
        device_model=data.device_model,
        manufacturer=data.manufacturer,
        modality_type=data.modality_type,
        site_name=data.site_name,
        department_id=data.department_id,
        ip_address=data.ip_address,
        ae_title=data.ae_title,
        port=data.port,
        dicom_protocol=data.dicom_protocol,
        software_version=data.software_version,
        serial_number=data.serial_number,
        metadata=data.metadata,
    )
    return _to_dict(device)


@router.put("/devices/{device_id}/status")
def update_device_status(
    device_id: str,
    data: DeviceStatusUpdate,
    db: Session = Depends(get_db),
    current_user: LabUser = Depends(get_current_user),
):
    device_svc = DeviceMonitoringService(db)
    device = device_svc.update_device_status(device_id, data.status)
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    return _to_dict(device)


@router.get("/device-worklist/{device_id}")
def get_device_worklist(
    device_id: str,
    db: Session = Depends(get_db),
    current_user: LabUser = Depends(get_current_user),
):
    wl_svc = ModalityWorklistService(db)
    entries = wl_svc.get_worklist_for_device(
        device_id,
        patient_ids=_tenant_patient_keys(db, current_user),
    )
    return {"items": [_to_dict(e) for e in entries], "total": len(entries)}


@router.post("/mpps", status_code=201)
def receive_mpps(
    data: MPPSReceive,
    db: Session = Depends(get_db),
    current_user: LabUser = Depends(get_current_user),
):
    mpps_handler = MPPSHandler(db)
    mpps_data = {
        "accession_number": data.accession_number,
        "status": data.status,
        "series_count": data.series_count,
        "images_count": data.images_count,
        "performed_steps": data.performed_steps,
        "notes": data.notes,
        "metadata": data.metadata,
    }
    mpps = mpps_handler.process_mpps(mpps_data)
    if not mpps:
        raise HTTPException(status_code=400, detail="Failed to process MPPS")
    return _to_dict(mpps)


@router.get("/device-health")
def get_device_health(
    db: Session = Depends(get_db),
    current_user: LabUser = Depends(get_current_user),
):
    device_svc = DeviceMonitoringService(db)
    stale = device_svc.detect_stale_devices()
    health = device_svc.get_device_health()
    return {
        "health": health,
        "stale_devices_detected": len(stale),
        "stale_device_ids": [d.device_id for d in stale],
    }


# ==============================================================================
# Critical Findings
# ==============================================================================


@router.get("/critical-findings")
def list_critical_findings(
    status: str | None = None,
    exam_id: str | None = None,
    notified_to: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: LabUser = Depends(get_current_user),
):
    if exam_id:
        svc = _get_radiology_service(db)
        exam = svc.get_exam(exam_id)
        if exam is None:
            raise HTTPException(status_code=404, detail="Exam not found")
        _patient_for_user(db, current_user, exam.patient_id)
    svc = _get_radiology_service(db)
    tenant_patient_ids = _tenant_patient_keys(db, current_user)
    from_ = datetime.fromisoformat(date_from) if date_from else None
    to_ = datetime.fromisoformat(date_to) if date_to else None
    findings = svc.list_critical_findings(
        status=status,
        exam_id=exam_id,
        notified_to=notified_to,
        date_from=from_,
        date_to=to_,
        skip=skip,
        limit=limit,
        patient_ids=tenant_patient_ids,
    )
    return {"items": [_to_dict(f) for f in findings], "total": len(findings), "skip": skip, "limit": limit}


@router.post("/critical-findings", status_code=201)
def create_critical_finding(
    data: CriticalFindingCreate,
    db: Session = Depends(get_db),
    current_user: LabUser = Depends(get_current_user),
):
    svc = _get_radiology_service(db)
    exam = svc.get_exam(data.exam_id)
    if exam is None:
        raise HTTPException(status_code=404, detail="Exam not found")
    _patient_for_user(db, current_user, exam.patient_id)
    if data.report_id:
        report = svc.get_report(data.report_id)
        if report is None:
            raise HTTPException(status_code=404, detail="Report not found")
        _patient_for_user(db, current_user, report.patient_id)
    finding = svc.create_critical_finding(
        exam_id=data.exam_id,
        finding_type=data.finding_type,
        finding_description=data.finding_description,
        report_id=data.report_id,
        notified_by=data.notified_by,
        notified_to=data.notified_to,
        notes=data.notes,
        metadata=data.metadata,
    )
    return _to_dict(finding)


@router.put("/critical-findings/{finding_id}/acknowledge")
def acknowledge_critical_finding(
    finding_id: str,
    data: CriticalFindingAcknowledge,
    db: Session = Depends(get_db),
    current_user: LabUser = Depends(get_current_user),
):
    _critical_finding_for_user(db, current_user, finding_id)
    svc = _get_radiology_service(db)
    finding = svc.acknowledge_critical_finding(
        finding_id=finding_id,
        acknowledged_by=data.acknowledged_by,
        notes=data.notes,
    )
    if not finding:
        raise HTTPException(status_code=404, detail="Critical finding not found")
    return _to_dict(finding)


@router.post("/critical-findings/notify")
def notify_critical_finding(
    finding_id: str = Query(...),
    notified_by: str = Query(...),
    notified_to: str = Query(...),
    db: Session = Depends(get_db),
    current_user: LabUser = Depends(get_current_user),
):
    _critical_finding_for_user(db, current_user, finding_id)
    svc = _get_radiology_service(db)
    finding = svc.notify_critical_finding(
        finding_id=finding_id,
        notified_by=notified_by,
        notified_to=notified_to,
    )
    if not finding:
        raise HTTPException(status_code=404, detail="Critical finding not found")
    return _to_dict(finding)


# ==============================================================================
# Dashboard
# ==============================================================================


@router.get("/dashboard")
def get_dashboard(
    date_from: str = Query(...),
    date_to: str = Query(...),
    db: Session = Depends(get_db),
    current_user: LabUser = Depends(get_current_user),
):
    svc = _get_radiology_service(db)
    tenant_patient_ids = _tenant_patient_keys(db, current_user)
    from_ = datetime.fromisoformat(date_from)
    to_ = datetime.fromisoformat(date_to)
    volume = svc.get_exam_volume(from_, to_, patient_ids=tenant_patient_ids)
    tat = svc.get_report_tat(from_, to_, patient_ids=tenant_patient_ids)
    utilization = svc.get_modality_utilization(from_, to_, patient_ids=tenant_patient_ids)
    return {
        "exam_volume": volume,
        "report_tat": tat,
        "modality_utilization": utilization,
    }


@router.get("/dashboard/workload")
def get_workload(
    date_from: str = Query(...),
    date_to: str = Query(...),
    db: Session = Depends(get_db),
    current_user: LabUser = Depends(get_current_user),
):
    svc = _get_radiology_service(db)
    tenant_patient_ids = _tenant_patient_keys(db, current_user)
    from_ = datetime.fromisoformat(date_from)
    to_ = datetime.fromisoformat(date_to)
    radiologist_workload = svc.get_workload_by_radiologist(from_, to_, patient_ids=tenant_patient_ids)
    technologist_workload = svc.get_workload_by_technologist(from_, to_, patient_ids=tenant_patient_ids)
    return {
        "radiologists": radiologist_workload,
        "technologists": technologist_workload,
    }


@router.get("/dashboard/report-tat")
def get_report_tat(
    date_from: str = Query(...),
    date_to: str = Query(...),
    db: Session = Depends(get_db),
    current_user: LabUser = Depends(get_current_user),
):
    svc = _get_radiology_service(db)
    tenant_patient_ids = _tenant_patient_keys(db, current_user)
    from_ = datetime.fromisoformat(date_from)
    to_ = datetime.fromisoformat(date_to)
    return svc.get_report_tat(from_, to_, patient_ids=tenant_patient_ids)


@router.get("/dashboard/modality-utilization")
def get_modality_utilization(
    date_from: str = Query(...),
    date_to: str = Query(...),
    db: Session = Depends(get_db),
    current_user: LabUser = Depends(get_current_user),
):
    svc = _get_radiology_service(db)
    tenant_patient_ids = _tenant_patient_keys(db, current_user)
    from_ = datetime.fromisoformat(date_from)
    to_ = datetime.fromisoformat(date_to)
    return {"items": svc.get_modality_utilization(from_, to_, patient_ids=tenant_patient_ids)}


# ==============================================================================
# Citizen
# ==============================================================================


@router.get("/citizen/reports")
def citizen_reports(
    patient_id: str = Query(...),
    status: str | None = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: LabUser = Depends(get_current_user),
):
    _patient_for_user(db, current_user, patient_id)
    svc = _get_radiology_service(db)
    reports = svc.search_reports(
        patient_id=patient_id,
        status=status,
        skip=skip,
        limit=limit,
        patient_ids=_tenant_patient_keys(db, current_user),
    )
    items = []
    for r in reports:
        d = _to_dict(r)
        d.pop("extra_metadata", None)
        items.append(d)
    return {"items": items, "total": len(items), "skip": skip, "limit": limit}


@router.get("/citizen/images")
def citizen_images(
    patient_id: str = Query(...),
    db: Session = Depends(get_db),
    current_user: LabUser = Depends(get_current_user),
):
    _patient_for_user(db, current_user, patient_id)
    storage_svc = _get_storage_service(db)
    records = storage_svc.query(patient_id=patient_id)
    viewer = ImageViewerService(db)
    items = []
    for rec in records:
        items.append({
            "sop_instance_uid": rec.sop_instance_uid,
            "modality": rec.modality.value if hasattr(rec.modality, "value") else str(rec.modality),
            "viewer_url": viewer.get_streaming_url(rec.sop_instance_uid),
        })
    return {"items": items, "total": len(items)}


@router.post("/citizen/share", status_code=201)
def citizen_create_share(
    data: ImageShareCreate,
    db: Session = Depends(get_db),
    current_user: LabUser = Depends(get_current_user),
):
    _study_for_user(db, current_user, data.study_uid)
    sharing = ImageSharingService(db)
    share = sharing.create_share(
        study_uid=data.study_uid,
        shared_by="citizen",
        shared_with=data.shared_with,
        share_type=data.share_type,
        expires_in_hours=data.expires_in_hours,
        metadata=data.metadata,
    )
    return _to_dict(share)
