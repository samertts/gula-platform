from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from ..database import get_db
from ..models.lab_user import LabUser
from ..security.dependencies import require_permission
from . import service
from .schemas import (
    DeviceEventListResponse,
    DeviceEventRecord,
    DeviceListResponse,
    DeviceRecord,
    DeviceRegisterRequest,
    DeviceStatusUpdateRequest,
    DeviceSummary,
    PrinterJobListResponse,
    PrinterJobRecord,
    PrinterJobRequest,
    ProtocolDescriptor,
)

router = APIRouter(prefix="/device-integration", tags=["device-integration"])


def _read_actor() -> LabUser:
    return Depends(require_permission("lab:read"))  # type: ignore[return-value]


def _write_actor() -> LabUser:
    return Depends(require_permission("lab:manage"))  # type: ignore[return-value]


def _device_or_404(db: Session, actor: LabUser, device_uid: str):
    device = service.get_device(db, actor.lab_id, device_uid)
    if device is None:
        raise HTTPException(status_code=404, detail="Device not found")
    return device


def _handle_service_error(exc: Exception) -> None:
    if isinstance(exc, LookupError):
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    if isinstance(exc, ValueError):
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    raise exc


@router.get("/protocols", response_model=list[ProtocolDescriptor])
def list_protocols(_: LabUser = _read_actor()):
    return [ProtocolDescriptor(**descriptor) for descriptor in service.PROTOCOL_CATALOG]


@router.get("/summary", response_model=DeviceSummary)
def device_summary(
    actor: LabUser = _read_actor(),
    db: Session = Depends(get_db),
):
    return service.summary(db, actor.lab_id)


@router.get("/devices", response_model=DeviceListResponse)
def list_devices(
    category: str | None = None,
    device_status: str | None = Query(None, alias="status"),
    limit: int = Query(100, ge=1, le=200),
    actor: LabUser = _read_actor(),
    db: Session = Depends(get_db),
):
    total, devices = service.list_devices(db, actor.lab_id, category=category, status=device_status, limit=limit)
    return DeviceListResponse(total=total, devices=[DeviceRecord.model_validate(device) for device in devices])


@router.get("/devices/{device_uid}", response_model=DeviceRecord)
def get_device(
    device_uid: str,
    actor: LabUser = _read_actor(),
    db: Session = Depends(get_db),
):
    return DeviceRecord.model_validate(_device_or_404(db, actor, device_uid))


@router.post("/devices", response_model=DeviceRecord, status_code=status.HTTP_201_CREATED)
def register_device(
    payload: DeviceRegisterRequest,
    actor: LabUser = _write_actor(),
    db: Session = Depends(get_db),
):
    try:
        return DeviceRecord.model_validate(service.register_device(db, actor.lab_id, payload))
    except Exception as exc:
        _handle_service_error(exc)
        raise AssertionError("unreachable")


@router.post("/devices/{device_uid}/status", response_model=DeviceRecord)
def update_device_status(
    device_uid: str,
    payload: DeviceStatusUpdateRequest,
    actor: LabUser = _write_actor(),
    db: Session = Depends(get_db),
):
    try:
        return DeviceRecord.model_validate(service.update_status(db, actor.lab_id, device_uid, payload))
    except Exception as exc:
        _handle_service_error(exc)
        raise AssertionError("unreachable")


@router.post("/devices/{device_uid}/probe", response_model=DeviceRecord)
def probe_device(
    device_uid: str,
    actor: LabUser = _write_actor(),
    db: Session = Depends(get_db),
):
    try:
        return DeviceRecord.model_validate(service.probe_device(db, actor.lab_id, device_uid))
    except Exception as exc:
        _handle_service_error(exc)
        raise AssertionError("unreachable")


@router.get("/events", response_model=DeviceEventListResponse)
def list_device_events(
    device_uid: str | None = None,
    severity: str | None = None,
    limit: int = Query(100, ge=1, le=200),
    actor: LabUser = _read_actor(),
    db: Session = Depends(get_db),
):
    total, rows = service.list_events(db, actor.lab_id, device_uid=device_uid, severity=severity, limit=limit)
    events = [
        DeviceEventRecord(
            id=event.id,
            device_uid=uid,
            event_type=event.event_type,
            direction=event.direction,
            severity=event.severity,
            message_type=event.message_type,
            summary=event.summary,
            correlation_id=event.correlation_id,
            safe_metadata=event.safe_metadata,
            occurred_at=event.occurred_at,
        )
        for event, uid in rows
    ]
    return DeviceEventListResponse(total=total, events=events)


@router.get("/printer-jobs", response_model=PrinterJobListResponse)
def list_printer_jobs(
    device_uid: str | None = None,
    limit: int = Query(100, ge=1, le=200),
    actor: LabUser = _read_actor(),
    db: Session = Depends(get_db),
):
    total, rows = service.list_print_jobs(db, actor.lab_id, device_uid=device_uid, limit=limit)
    jobs = [
        PrinterJobRecord(
            id=job.id,
            device_uid=uid,
            document_type=job.document_type,
            printer_language=job.printer_language,
            label_count=job.label_count,
            status=job.status,
            simulation_only=job.simulation_only,
            safe_metadata=job.safe_metadata,
            error_message=job.error_message,
            created_at=job.created_at,
            completed_at=job.completed_at,
        )
        for job, uid in rows
    ]
    return PrinterJobListResponse(total=total, jobs=jobs)


@router.post("/printer-jobs", response_model=PrinterJobRecord, status_code=status.HTTP_201_CREATED)
def create_printer_job(
    payload: PrinterJobRequest,
    actor: LabUser = _write_actor(),
    db: Session = Depends(get_db),
):
    try:
        job = service.create_print_job(db, actor.lab_id, actor.id, payload)
        return PrinterJobRecord(
            id=job.id,
            device_uid=payload.device_uid,
            document_type=job.document_type,
            printer_language=job.printer_language,
            label_count=job.label_count,
            status=job.status,
            simulation_only=job.simulation_only,
            safe_metadata=job.safe_metadata,
            error_message=job.error_message,
            created_at=job.created_at,
            completed_at=job.completed_at,
        )
    except Exception as exc:
        _handle_service_error(exc)
        raise AssertionError("unreachable")
