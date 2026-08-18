"""Doctor Duty API: expanded clinical access is never granted by login alone.

Design reminder: all scope values are checked against server-persisted duty data;
client input is a resource request, not an authority claim. Responses avoid raw
national identifiers and expose only duty metadata needed by the workspace.
"""
from __future__ import annotations

from datetime import datetime
from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.security.dependencies import get_current_user
from app.services.doctor_duty_service import ClinicalRequest, DoctorDutyService, DutyAuthorizationError

router = APIRouter(prefix="/doctor-duty", tags=["doctor-duty"])


class ClinicalAccessRequest(BaseModel):
    purpose: str = Field(min_length=1, max_length=100)
    organization_id: int
    facility_id: int
    department_id: str | None = None
    ward_id: str | None = None
    patient_id: int | None = None
    resource_type: str | None = None
    resource_id: str | None = None
    emergency: bool = False
    request_id: str | None = None
    correlation_id: str | None = None


class BreakGlassRequest(ClinicalAccessRequest):
    reason: str = Field(min_length=10, max_length=2000)
    duration_minutes: int = Field(default=30, ge=1, le=60)


class HandoverRequest(BaseModel):
    incoming_duty_id: int
    patient_ids: list[int] = Field(default_factory=list, max_length=500)
    task_ids: list[str] = Field(default_factory=list, max_length=500)
    notes: str | None = Field(default=None, max_length=4000)


class DutyScheduleRequest(BaseModel):
    user_id: int
    organization_id: int
    facility_id: int
    role_id: str = Field(min_length=1, max_length=100)
    purpose: str = Field(min_length=1, max_length=100)
    starts_at: datetime
    expected_end_at: datetime
    tenant_id: int | None = None
    department_id: str | None = None
    ward_id: str | None = None
    room_id: str | None = None
    assigned_patient_ids: list[int] = Field(default_factory=list, max_length=500)


class DutyExtendRequest(BaseModel):
    new_expected_end_at: datetime


def _service_error(exc: DutyAuthorizationError) -> HTTPException:
    code = exc.code
    http_status = status.HTTP_403_FORBIDDEN
    if code in {"DUTY_NOT_FOUND", "DUTY_CONTEXT_DENIED"}:
        http_status = status.HTTP_404_NOT_FOUND
    if code.startswith("CONCURRENT"):
        http_status = status.HTTP_409_CONFLICT
    return HTTPException(status_code=http_status, detail={"code": code, "message": "Clinical access denied"})


def _request(user: User, payload: ClinicalAccessRequest) -> ClinicalRequest:
    return ClinicalRequest(user_id=user.id, purpose=payload.purpose, organization_id=payload.organization_id,
                           facility_id=payload.facility_id, department_id=payload.department_id, ward_id=payload.ward_id,
                           patient_id=payload.patient_id, resource_type=payload.resource_type, resource_id=payload.resource_id,
                           emergency=payload.emergency, request_id=payload.request_id, correlation_id=payload.correlation_id)


@router.post("/admin/schedule", status_code=status.HTTP_201_CREATED)
def schedule_duty(payload: DutyScheduleRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    try:
        duty = DoctorDutyService(db).schedule_duty(actor_id=current_user.id, **payload.model_dump())
        db.commit()
        return {"duty_id": duty.id, "status": duty.status, "user_id": duty.user_id, "organization_id": duty.organization_id, "facility_id": duty.facility_id, "starts_at": duty.starts_at, "expected_end_at": duty.expected_end_at}
    except DutyAuthorizationError as exc:
        db.rollback()
        raise _service_error(exc) from exc


@router.post("/admin/{duty_id}/cancel")
def cancel_duty(duty_id: int, reason: str = "cancelled_by_admin", db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    try:
        DoctorDutyService(db).cancel_duty(duty_id, actor_id=current_user.id, reason=reason)
        db.commit()
        return {"duty_id": duty_id, "status": "CANCELLED"}
    except DutyAuthorizationError as exc:
        db.rollback()
        raise _service_error(exc) from exc


@router.post("/admin/{duty_id}/revoke")
def revoke_duty(duty_id: int, reason: str = "revoked_by_admin", db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    try:
        DoctorDutyService(db).revoke_duty(duty_id, actor_id=current_user.id, reason=reason)
        db.commit()
        return {"duty_id": duty_id, "status": "REVOKED", "clinical_access": "REVOKED"}
    except DutyAuthorizationError as exc:
        db.rollback()
        raise _service_error(exc) from exc


@router.post("/admin/{duty_id}/extend")
def extend_duty(duty_id: int, payload: DutyExtendRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    try:
        duty = DoctorDutyService(db).extend_duty(duty_id, actor_id=current_user.id, new_expected_end_at=payload.new_expected_end_at)
        db.commit()
        return {"duty_id": duty.id, "status": duty.status, "expected_end_at": duty.expected_end_at}
    except DutyAuthorizationError as exc:
        db.rollback()
        raise _service_error(exc) from exc


@router.post("/{duty_id}/start", status_code=status.HTTP_201_CREATED)
def start_duty(duty_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    try:
        context = DoctorDutyService(db).start_duty(duty_id, actor_id=current_user.id)
        db.commit()
        return {"duty_context_id": context.id, "status": context.status, "organization_id": context.organization_id, "facility_id": context.facility_id, "department_id": context.department_id, "ward_id": context.ward_id, "expires_at": context.expires_at}
    except DutyAuthorizationError as exc:
        db.rollback()
        raise _service_error(exc) from exc


@router.post("/{context_id}/end")
def end_duty(context_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    try:
        DoctorDutyService(db).end_duty(context_id, actor_id=current_user.id)
        db.commit()
        return {"status": "ENDED", "clinical_access": "REVOKED", "message_ar": "انتهت ورديتك وتم إيقاف صلاحيات الوصول السريري الموسعة."}
    except DutyAuthorizationError as exc:
        db.rollback()
        raise _service_error(exc) from exc


@router.post("/authorize")
def authorize_clinical_access(payload: ClinicalAccessRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    try:
        context = DoctorDutyService(db).authorize(_request(current_user, payload))
        db.commit()
        return {"decision": "ALLOW", "duty_context_id": context.duty_context_id, "scope": {"organization_id": context.organization_id, "facility_id": context.facility_id, "department_id": context.department_id, "ward_id": context.ward_id}, "expires_at": context.expires_at}
    except DutyAuthorizationError as exc:
        db.rollback()
        raise _service_error(exc) from exc


@router.post("/break-glass")
def break_glass(payload: BreakGlassRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    try:
        session = DoctorDutyService(db).open_break_glass(_request(current_user, payload), reason=payload.reason, duration_minutes=payload.duration_minutes)
        db.commit()
        return {"decision": "ALLOW", "break_glass_id": session.id, "expires_at": session.expires_at, "audit_required": True}
    except DutyAuthorizationError as exc:
        db.rollback()
        raise _service_error(exc) from exc


@router.post("/{duty_id}/handover")
def start_handover(duty_id: int, payload: HandoverRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    try:
        handover = DoctorDutyService(db).start_handover(duty_id, payload.incoming_duty_id, actor_id=current_user.id, patient_ids=payload.patient_ids, task_ids=payload.task_ids, notes=payload.notes)
        db.commit()
        return {"handover_id": handover.id, "status": handover.status}
    except DutyAuthorizationError as exc:
        db.rollback()
        raise _service_error(exc) from exc


@router.post("/handover/{handover_id}/confirm")
def confirm_handover(handover_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    try:
        DoctorDutyService(db).confirm_handover(handover_id, actor_id=current_user.id)
        db.commit()
        return {"handover_id": handover_id, "status": "COMPLETED", "outgoing_clinical_access": "REVOKED"}
    except DutyAuthorizationError as exc:
        db.rollback()
        raise _service_error(exc) from exc
