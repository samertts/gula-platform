from __future__ import annotations

from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.orm import Session

from app.clinical_gateway.appointment_service import AppointmentCanonicalConflict, AppointmentCanonicalService
from app.clinical_gateway.context import ClinicalGatewayBlocked
from app.database import get_db
from app.identity.api.workspaces import NiamActor, get_current_niam_actor_sync
from app.national.scheduling_platform.api.routes import _get_service
from app.national.scheduling_platform.application.service import SchedulingPlatformService

router = APIRouter(prefix="/api/v1/clinical/appointments", tags=["Canonical Clinical Appointments"])


class AppointmentCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    patient_id: str = Field(min_length=1, max_length=26)
    appointment_type: str = Field(min_length=1, max_length=100)
    start_at: datetime
    end_at: datetime
    title: str = Field(default="", max_length=255)
    description: str = Field(default="", max_length=4000)
    notes: str = Field(default="", max_length=4000)
    idempotency_key: str | None = Field(default=None, min_length=8, max_length=128)


class AppointmentRescheduleRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    start_at: datetime
    end_at: datetime
    expected_version: int | None = Field(default=None, ge=1)
    reason: str = Field(default="", max_length=500)


class AppointmentCancelRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    expected_version: int | None = Field(default=None, ge=1)
    reason: str = Field(default="", max_length=500)


class AppointmentTransitionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: str = Field(min_length=1, max_length=32)
    expected_version: int | None = Field(default=None, ge=1)


def _service(db: Session, scheduler: SchedulingPlatformService) -> AppointmentCanonicalService:
    return AppointmentCanonicalService(db, scheduler)


def _raise(exc: Exception) -> None:
    if isinstance(exc, ClinicalGatewayBlocked):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Appointment authorization denied") from exc
    if isinstance(exc, AppointmentCanonicalConflict):
        if str(exc) == "appointment_not_found":
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Appointment not found") from exc
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    raise exc


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_appointment(
    payload: AppointmentCreateRequest,
    actor: NiamActor = Depends(get_current_niam_actor_sync),
    db: Session = Depends(get_db),
    scheduler: SchedulingPlatformService = Depends(_get_service),
) -> dict[str, Any]:
    try:
        appointment = await _service(db, scheduler).create(
            actor=actor,
            patient_id=payload.patient_id,
            appointment_type=payload.appointment_type,
            start_at=payload.start_at,
            end_at=payload.end_at,
            title=payload.title,
            description=payload.description,
            notes=payload.notes,
            idempotency_key=payload.idempotency_key,
        )
        return AppointmentCanonicalService.to_safe_dict(appointment)
    except (ClinicalGatewayBlocked, AppointmentCanonicalConflict) as exc:
        db.rollback()
        _raise(exc)


@router.get("")
def list_appointments(
    status_filter: str | None = Query(default=None, alias="status", max_length=32),
    limit: int = Query(default=100, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    actor: NiamActor = Depends(get_current_niam_actor_sync),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    try:
        access, rows = AppointmentCanonicalService(db, _get_service(db)).list_for_workspace(
            actor=actor,
            status=status_filter,
            limit=limit,
            offset=offset,
        )
        return {
            "items": [AppointmentCanonicalService.to_safe_dict(row) for row in rows],
            "limit": limit,
            "offset": offset,
            "workspace_id": access.workspace_id,
        }
    except (ClinicalGatewayBlocked, AppointmentCanonicalConflict) as exc:
        db.rollback()
        _raise(exc)


@router.get("/{appointment_id}")
def get_appointment(
    appointment_id: str,
    actor: NiamActor = Depends(get_current_niam_actor_sync),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    try:
        _, appointment = AppointmentCanonicalService(db, _get_service(db)).get(
            actor=actor,
            appointment_id=appointment_id,
        )
        return AppointmentCanonicalService.to_safe_dict(appointment)
    except (ClinicalGatewayBlocked, AppointmentCanonicalConflict) as exc:
        db.rollback()
        _raise(exc)


@router.post("/{appointment_id}/reschedule")
async def reschedule_appointment(
    appointment_id: str,
    payload: AppointmentRescheduleRequest,
    actor: NiamActor = Depends(get_current_niam_actor_sync),
    db: Session = Depends(get_db),
    scheduler: SchedulingPlatformService = Depends(_get_service),
) -> dict[str, Any]:
    try:
        appointment = await _service(db, scheduler).reschedule(
            actor=actor,
            appointment_id=appointment_id,
            start_at=payload.start_at,
            end_at=payload.end_at,
            expected_version=payload.expected_version,
            reason=payload.reason,
        )
        return AppointmentCanonicalService.to_safe_dict(appointment)
    except (ClinicalGatewayBlocked, AppointmentCanonicalConflict) as exc:
        db.rollback()
        _raise(exc)


@router.post("/{appointment_id}/cancel")
async def cancel_appointment(
    appointment_id: str,
    payload: AppointmentCancelRequest,
    actor: NiamActor = Depends(get_current_niam_actor_sync),
    db: Session = Depends(get_db),
    scheduler: SchedulingPlatformService = Depends(_get_service),
) -> dict[str, Any]:
    try:
        appointment = await _service(db, scheduler).cancel(
            actor=actor,
            appointment_id=appointment_id,
            expected_version=payload.expected_version,
            reason=payload.reason,
        )
        return AppointmentCanonicalService.to_safe_dict(appointment)
    except (ClinicalGatewayBlocked, AppointmentCanonicalConflict) as exc:
        db.rollback()
        _raise(exc)


@router.post("/{appointment_id}/transition")
async def transition_appointment(
    appointment_id: str,
    payload: AppointmentTransitionRequest,
    actor: NiamActor = Depends(get_current_niam_actor_sync),
    db: Session = Depends(get_db),
    scheduler: SchedulingPlatformService = Depends(_get_service),
) -> dict[str, Any]:
    try:
        appointment = await _service(db, scheduler).transition(
            actor=actor,
            appointment_id=appointment_id,
            status=payload.status,
            expected_version=payload.expected_version,
        )
        return AppointmentCanonicalService.to_safe_dict(appointment)
    except (ClinicalGatewayBlocked, AppointmentCanonicalConflict) as exc:
        db.rollback()
        _raise(exc)
