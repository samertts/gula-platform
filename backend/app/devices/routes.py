from __future__ import annotations

import hashlib
import hmac
import json
import os
import time

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request, status
from pydantic import ValidationError
from sqlalchemy.orm import Session

from ..database import get_db
from ..models.lab_user import LabUser
from ..security.dependencies import require_institutional_permission
from . import service
from .schemas import (
    ClinicianBaselineSummary,
    ConnectorListResponse,
    ConnectorRecord,
    ConnectorRegisterRequest,
    ConnectorStatusUpdateRequest,
    DeviceEventListResponse,
    DeviceEventRecord,
    DeviceListResponse,
    DeviceOutboxListResponse,
    DeviceOutboxProcessResponse,
    DeviceOutboxRecord,
    DeviceRecord,
    DeviceRegisterRequest,
    DeviceStatusUpdateRequest,
    DeviceSummary,
    GatewayAlertAcknowledgeRequest,
    GatewayAlertRecord,
    GatewayHeartbeatRequest,
    GatewayListResponse,
    GatewayMetricIngestRequest,
    GatewayMetricRecord,
    GatewayMonitoringAlertListResponse,
    GatewayMonitoringSnapshot,
    GatewayRecord,
    GatewayRegistrationRequest,
    PrinterJobListResponse,
    PrinterJobRecord,
    PrinterJobRequest,
    ProtocolDescriptor,
    ProtocolProfileListResponse,
    ProtocolProfileRecord,
    ProtocolProfileRequest,
    SimulationResult,
    SimulatorDescriptor,
    SimulatorRequest,
    WearableMeasurementIngestRequest,
    WearableMeasurementIngestResponse,
    WearableMeasurementListResponse,
    WearableMeasurementRecord,
)

router = APIRouter(prefix="/device-integration", tags=["device-integration"])


def _read_actor() -> LabUser:
    return Depends(require_institutional_permission("lab:read"))  # type: ignore[return-value]


def _write_actor() -> LabUser:
    return Depends(require_institutional_permission("lab:manage"))  # type: ignore[return-value]


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


@router.post("/wearables/webhook/{provider}", status_code=status.HTTP_202_ACCEPTED)
async def ingest_wearable_webhook(
    provider: str,
    request: Request,
    x_signature_256: str | None = Header(default=None, alias="X-Signature-256"),
    x_timestamp: str | None = Header(default=None, alias="X-Webhook-Timestamp"),
    db: Session = Depends(get_db),
):
    """Accept a signed canonical wearable event without persisting raw provider data."""
    normalized_provider = provider.strip().lower()
    allowed_providers = {"apple_health", "fitbit", "google_fit"}
    if normalized_provider not in allowed_providers:
        raise HTTPException(status_code=404, detail="Unsupported wearable provider")

    secret = os.getenv(f"GULA_WEARABLE_WEBHOOK_SECRET_{normalized_provider.upper()}") or os.getenv(
        "GULA_WEARABLE_WEBHOOK_SECRET", ""
    )
    if not secret:
        raise HTTPException(status_code=503, detail="Wearable webhook is not configured")
    if not x_signature_256 or not x_timestamp or not x_timestamp.isdigit():
        raise HTTPException(status_code=401, detail="Missing webhook signature")

    timestamp = int(x_timestamp)
    if abs(time.time() - timestamp) > 300:
        raise HTTPException(status_code=401, detail="Expired webhook signature")

    raw_body = await request.body()
    expected = hmac.new(
        secret.encode("utf-8"),
        f"{timestamp}.".encode("ascii") + raw_body,
        hashlib.sha256,
    ).hexdigest()
    supplied = x_signature_256.removeprefix("sha256=")
    if not hmac.compare_digest(supplied, expected):
        raise HTTPException(status_code=401, detail="Invalid webhook signature")

    try:
        envelope = json.loads(raw_body.decode("utf-8"))
        if not isinstance(envelope, dict):
            raise ValueError("Webhook envelope must be an object")
        lab_id = int(envelope["lab_id"])
        measurement_data = envelope["measurement"]
        if not isinstance(measurement_data, dict):
            raise ValueError("Webhook measurement must be an object")
        payload = WearableMeasurementIngestRequest.model_validate(measurement_data)
    except (
        KeyError,
        TypeError,
        ValueError,
        UnicodeDecodeError,
        json.JSONDecodeError,
        ValidationError,
    ) as exc:
        raise HTTPException(status_code=400, detail="Invalid canonical wearable webhook") from exc

    if payload.source.lower() != normalized_provider:
        raise HTTPException(
            status_code=400, detail="Webhook provider does not match measurement source"
        )
    if not payload.simulation_only:
        raise HTTPException(
            status_code=409,
            detail="Live wearable providers require documented clinical approval",
        )

    try:
        measurement, duplicate = service.ingest_wearable_measurement(db, lab_id, payload)
    except Exception as exc:
        _handle_service_error(exc)
        raise AssertionError("unreachable") from exc

    # Return identifiers only; raw provider payloads are never stored or logged.
    return {
        "accepted": True,
        "provider": normalized_provider,
        "duplicate": duplicate,
        "measurement_id": measurement.id,
        "simulation_only": True,
    }


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
            device = (
                db.query(service.IntegratedDevice)
                .filter(
                    service.IntegratedDevice.id == connector.device_id,
                    service.IntegratedDevice.lab_id == actor.lab_id,
                )
                .first()
            )
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
        raise AssertionError("unreachable") from exc


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
            device = (
                db.query(service.IntegratedDevice)
                .filter(
                    service.IntegratedDevice.id == connector.device_id,
                    service.IntegratedDevice.lab_id == actor.lab_id,
                )
                .first()
            )
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
        raise AssertionError("unreachable") from exc


@router.get("/protocol-profiles", response_model=ProtocolProfileListResponse)
def list_protocol_profiles(
    profile_status: str | None = Query(None, alias="status"),
    limit: int = Query(100, ge=1, le=200),
    actor: LabUser = _read_actor(),
    db: Session = Depends(get_db),
):
    total, profiles = service.list_protocol_profiles(
        db, actor.lab_id, status=profile_status, limit=limit
    )
    return ProtocolProfileListResponse(
        total=total,
        profiles=[ProtocolProfileRecord.model_validate(profile) for profile in profiles],
    )


@router.post(
    "/protocol-profiles", response_model=ProtocolProfileRecord, status_code=status.HTTP_201_CREATED
)
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
        raise AssertionError("unreachable") from exc


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
        return SimulationResult(
            **service.simulate_connector(db, actor.lab_id, connector_uid, payload)
        )
    except Exception as exc:
        _handle_service_error(exc)
        raise AssertionError("unreachable") from exc


@router.get("/devices", response_model=DeviceListResponse)
def list_devices(
    category: str | None = None,
    device_status: str | None = Query(None, alias="status"),
    limit: int = Query(100, ge=1, le=200),
    actor: LabUser = _read_actor(),
    db: Session = Depends(get_db),
):
    total, devices = service.list_devices(
        db, actor.lab_id, category=category, status=device_status, limit=limit
    )
    return DeviceListResponse(
        total=total, devices=[DeviceRecord.model_validate(device) for device in devices]
    )


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
        raise AssertionError("unreachable") from exc


@router.post("/devices/{device_uid}/status", response_model=DeviceRecord)
def update_device_status(
    device_uid: str,
    payload: DeviceStatusUpdateRequest,
    actor: LabUser = _write_actor(),
    db: Session = Depends(get_db),
):
    try:
        return DeviceRecord.model_validate(
            service.update_status(db, actor.lab_id, device_uid, payload)
        )
    except Exception as exc:
        _handle_service_error(exc)
        raise AssertionError("unreachable") from exc


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
        raise AssertionError("unreachable") from exc


@router.get("/events", response_model=DeviceEventListResponse)
def list_device_events(
    device_uid: str | None = None,
    severity: str | None = None,
    limit: int = Query(100, ge=1, le=200),
    actor: LabUser = _read_actor(),
    db: Session = Depends(get_db),
):
    total, rows = service.list_events(
        db, actor.lab_id, device_uid=device_uid, severity=severity, limit=limit
    )
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
        raise AssertionError("unreachable") from exc


@router.get("/gateways", response_model=GatewayListResponse)
def list_registered_gateways(
    gateway_status: str | None = Query(None, alias="status"),
    limit: int = Query(100, ge=1, le=200),
    actor: LabUser = _read_actor(),
    db: Session = Depends(get_db),
):
    total, gateways = service.list_gateways(db, actor.lab_id, status=gateway_status, limit=limit)
    return GatewayListResponse(
        total=total,
        gateways=[GatewayRecord.model_validate(gateway) for gateway in gateways],
    )


@router.post("/gateways", response_model=GatewayRecord, status_code=status.HTTP_201_CREATED)
def register_gateway(
    payload: GatewayRegistrationRequest,
    actor: LabUser = _write_actor(),
    db: Session = Depends(get_db),
):
    try:
        return GatewayRecord.model_validate(service.register_gateway(db, actor.lab_id, payload))
    except Exception as exc:
        _handle_service_error(exc)
        raise AssertionError("unreachable") from exc


@router.post(
    "/gateways/{gateway_ref}/heartbeat",
    response_model=GatewayMetricRecord,
    status_code=status.HTTP_201_CREATED,
)
def record_gateway_heartbeat(
    gateway_ref: str,
    payload: GatewayHeartbeatRequest,
    actor: LabUser = _write_actor(),
    db: Session = Depends(get_db),
):
    if payload.gateway_ref != gateway_ref:
        raise HTTPException(status_code=400, detail="gateway_ref does not match the route")
    try:
        return GatewayMetricRecord.model_validate(
            service.record_gateway_heartbeat(db, actor.lab_id, payload)
        )
    except Exception as exc:
        _handle_service_error(exc)
        raise AssertionError("unreachable") from exc


@router.get("/outbox", response_model=DeviceOutboxListResponse)
def list_device_outbox(
    outbox_status: str | None = Query(None, alias="status"),
    gateway_ref: str | None = None,
    limit: int = Query(100, ge=1, le=200),
    actor: LabUser = _read_actor(),
    db: Session = Depends(get_db),
):
    total, messages = service.list_outbox(
        db,
        actor.lab_id,
        status=outbox_status,
        gateway_ref=gateway_ref,
        limit=limit,
    )
    return DeviceOutboxListResponse(
        total=total,
        messages=[DeviceOutboxRecord.model_validate(message) for message in messages],
    )


@router.post(
    "/outbox/process", response_model=DeviceOutboxProcessResponse, status_code=status.HTTP_200_OK
)
def process_device_outbox(
    limit: int = Query(50, ge=1, le=200),
    actor: LabUser = _write_actor(),
    db: Session = Depends(get_db),
):
    return service.process_outbox(db, actor.lab_id, limit=limit)


@router.post(
    "/monitoring/metrics", response_model=GatewayMetricRecord, status_code=status.HTTP_201_CREATED
)
def ingest_monitoring_metrics(
    payload: GatewayMetricIngestRequest,
    actor: LabUser = _write_actor(),
    db: Session = Depends(get_db),
):
    try:
        return GatewayMetricRecord.model_validate(
            service.ingest_gateway_metrics(db, actor.lab_id, payload)
        )
    except Exception as exc:
        _handle_service_error(exc)
        raise AssertionError("unreachable") from exc


@router.get("/monitoring", response_model=GatewayMonitoringSnapshot)
def get_monitoring_snapshot(
    actor: LabUser = _read_actor(),
    db: Session = Depends(get_db),
):
    return GatewayMonitoringSnapshot.model_validate(service.monitoring_snapshot(db, actor.lab_id))


@router.get("/monitoring/alerts", response_model=GatewayMonitoringAlertListResponse)
def list_monitoring_alerts(
    alert_status: str | None = Query(None, alias="status"),
    limit: int = Query(100, ge=1, le=200),
    actor: LabUser = _read_actor(),
    db: Session = Depends(get_db),
):
    total, alerts = service.list_gateway_alerts(
        db, actor.lab_id, alert_status=alert_status, limit=limit
    )
    return GatewayMonitoringAlertListResponse(
        total=total, alerts=[GatewayAlertRecord.model_validate(alert) for alert in alerts]
    )


@router.post("/monitoring/alerts/{alert_id}/acknowledge", response_model=GatewayAlertRecord)
def acknowledge_monitoring_alert(
    alert_id: int,
    payload: GatewayAlertAcknowledgeRequest,
    actor: LabUser = _write_actor(),
    db: Session = Depends(get_db),
):
    try:
        alert = service.acknowledge_gateway_alert(db, actor.lab_id, alert_id, actor.id, payload)
        return GatewayAlertRecord.model_validate(alert)
    except Exception as exc:
        _handle_service_error(exc)
        raise AssertionError("unreachable") from exc


@router.post(
    "/wearables/measurements",
    response_model=WearableMeasurementIngestResponse,
    status_code=status.HTTP_201_CREATED,
)
def ingest_wearable_measurement(
    payload: WearableMeasurementIngestRequest,
    actor: LabUser = _write_actor(),
    db: Session = Depends(get_db),
):
    try:
        measurement, duplicate = service.ingest_wearable_measurement(db, actor.lab_id, payload)
        return WearableMeasurementIngestResponse(
            accepted=True,
            duplicate=duplicate,
            measurement=WearableMeasurementRecord.model_validate(measurement),
        )
    except Exception as exc:
        _handle_service_error(exc)
        raise AssertionError("unreachable") from exc


@router.get(
    "/wearables/measurements",
    response_model=WearableMeasurementListResponse,
)
def list_wearable_measurements(
    patient_id: int = Query(..., ge=1),
    metric_code: str | None = Query(None, min_length=2, max_length=64),
    limit: int = Query(100, ge=1, le=500),
    actor: LabUser = _read_actor(),
    db: Session = Depends(get_db),
):
    total, rows = service.list_wearable_measurements(
        db,
        actor.lab_id,
        patient_id=patient_id,
        metric_code=metric_code,
        limit=limit,
    )
    return WearableMeasurementListResponse(
        total=total,
        measurements=[WearableMeasurementRecord.model_validate(row) for row in rows],
    )


@router.get(
    "/wearables/baseline-summary",
    response_model=ClinicianBaselineSummary,
)
def clinician_baseline_summary(
    patient_id: int = Query(..., ge=1),
    metric_code: str = Query(..., min_length=2, max_length=64),
    limit: int = Query(28, ge=7, le=180),
    actor: LabUser = _read_actor(),
    db: Session = Depends(get_db),
):
    try:
        return service.clinician_baseline_summary(
            db,
            actor.lab_id,
            patient_id,
            metric_code,
            limit=limit,
        )
    except Exception as exc:
        _handle_service_error(exc)
        raise AssertionError("unreachable") from exc
