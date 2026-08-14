from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from ..database import get_db
from ..models.lab_user import LabUser
from ..security.dependencies import require_permission
from . import service
from .schemas import (
    ConnectorListResponse,
    ConnectorRecord,
    ConnectorRegisterRequest,
    ConnectorStatusUpdateRequest,
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
    ProtocolProfileListResponse,
    SimulationResult,
    SimulatorDescriptor,
    SimulatorRequest,
    ProtocolProfileRecord,
    ProtocolProfileRequest,
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


@router.get("/connectors", response_model=ConnectorListResponse)
def list_connectors(
    connector_status: str | None = Query(None, alias="status"),
    limit: int = Query(100, ge=1, le=200),
    actor: LabUser = _read_actor(),
    db: Session = Depends(get_db),
):
    total, rows = service.list_connectors(db, actor.lab_id, status=connector_status, limit=limit)
    connectors = [
        ConnectorRecord(
            id=connector.id,
            connector_uid=connector.connector_uid,
            display_name=connector.display_name,
            device_uid=device_uid,
            protocol=connector.protocol,
            transport=connector.transport,
            mode=connector.mode,
            status=connector.status,
            contract_version=connector.contract_version,
            gateway_ref=connector.gateway_ref,
            config_safe=connector.config_safe,
            capability_manifest=connector.capability_manifest,
            last_heartbeat_at=connector.last_heartbeat_at,
            last_error=connector.last_error,
            enabled=connector.enabled,
            simulation_only=connector.simulation_only,
            maintenance_due_at=connector.maintenance_due_at,
            created_at=connector.created_at,
            updated_at=connector.updated_at,
        )
        for connector, device_uid in rows
    ]
    return ConnectorListResponse(total=total, connectors=connectors)


@router.post("/connectors", response_model=ConnectorRecord, status_code=status.HTTP_201_CREATED)
def register_connector(
    payload: ConnectorRegisterRequest,
    actor: LabUser = _write_actor(),
    db: Session = Depends(get_db),
):
    try:
        connector = service.register_connector(db, actor.lab_id, payload)
        device_uid = None
        if connector.device_id:
            device = db.query(service.IntegratedDevice).filter(
                service.IntegratedDevice.id == connector.device_id,
                service.IntegratedDevice.lab_id == actor.lab_id,
            ).first()
            device_uid = device.device_uid if device else None
        return ConnectorRecord(
            id=connector.id,
            connector_uid=connector.connector_uid,
            display_name=connector.display_name,
            device_uid=device_uid,
            protocol=connector.protocol,
            transport=connector.transport,
            mode=connector.mode,
            status=connector.status,
            contract_version=connector.contract_version,
            gateway_ref=connector.gateway_ref,
            config_safe=connector.config_safe,
            capability_manifest=connector.capability_manifest,
            last_heartbeat_at=connector.last_heartbeat_at,
            last_error=connector.last_error,
            enabled=connector.enabled,
            simulation_only=connector.simulation_only,
            maintenance_due_at=connector.maintenance_due_at,
            created_at=connector.created_at,
            updated_at=connector.updated_at,
        )
    except Exception as exc:
        _handle_service_error(exc)
        raise AssertionError("unreachable")


@router.post("/connectors/{connector_uid}/status", response_model=ConnectorRecord)
def update_connector_status(
    connector_uid: str,
    payload: ConnectorStatusUpdateRequest,
    actor: LabUser = _write_actor(),
    db: Session = Depends(get_db),
):
    try:
        connector = service.update_connector_status(db, actor.lab_id, connector_uid, payload)
        device_uid = None
        if connector.device_id:
            device = db.query(service.IntegratedDevice).filter(
                service.IntegratedDevice.id == connector.device_id,
                service.IntegratedDevice.lab_id == actor.lab_id,
            ).first()
            device_uid = device.device_uid if device else None
        return ConnectorRecord(
            id=connector.id,
            connector_uid=connector.connector_uid,
            display_name=connector.display_name,
            device_uid=device_uid,
            protocol=connector.protocol,
            transport=connector.transport,
            mode=connector.mode,
            status=connector.status,
            contract_version=connector.contract_version,
            gateway_ref=connector.gateway_ref,
            config_safe=connector.config_safe,
            capability_manifest=connector.capability_manifest,
            last_heartbeat_at=connector.last_heartbeat_at,
            last_error=connector.last_error,
            enabled=connector.enabled,
            simulation_only=connector.simulation_only,
            maintenance_due_at=connector.maintenance_due_at,
            created_at=connector.created_at,
            updated_at=connector.updated_at,
        )
    except Exception as exc:
        _handle_service_error(exc)
        raise AssertionError("unreachable")


@router.get("/protocol-profiles", response_model=ProtocolProfileListResponse)
def list_protocol_profiles(
    profile_status: str | None = Query(None, alias="status"),
    limit: int = Query(100, ge=1, le=200),
    actor: LabUser = _read_actor(),
    db: Session = Depends(get_db),
):
    total, profiles = service.list_protocol_profiles(db, actor.lab_id, status=profile_status, limit=limit)
    return ProtocolProfileListResponse(
        total=total,
        profiles=[ProtocolProfileRecord.model_validate(profile) for profile in profiles],
    )


@router.post("/protocol-profiles", response_model=ProtocolProfileRecord, status_code=status.HTTP_201_CREATED)
def register_protocol_profile(
    payload: ProtocolProfileRequest,
    actor: LabUser = _write_actor(),
    db: Session = Depends(get_db),
):
    try:
        return ProtocolProfileRecord.model_validate(
            service.register_protocol_profile(db, actor.lab_id, actor.id, payload)
        )
    except Exception as exc:
        _handle_service_error(exc)
        raise AssertionError("unreachable")


@router.get("/simulators", response_model=list[SimulatorDescriptor])
def list_simulators(_: LabUser = _read_actor()):
    return [SimulatorDescriptor(**descriptor) for descriptor in service.list_simulators()]


@router.post("/connectors/{connector_uid}/simulate", response_model=SimulationResult)
def simulate_connector(
    connector_uid: str,
    payload: SimulatorRequest,
    actor: LabUser = _write_actor(),
    db: Session = Depends(get_db),
):
    try:
        return SimulationResult(**service.simulate_connector(db, actor.lab_id, connector_uid, payload))
    except Exception as exc:
        _handle_service_error(exc)
        raise AssertionError("unreachable")


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
