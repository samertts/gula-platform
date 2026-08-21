from __future__ import annotations

from collections import Counter
from datetime import datetime, timedelta
from uuid import uuid4

from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app._compat import UTC

from .models import (
    DEVICE_CATEGORIES,
    DEVICE_PROTOCOLS,
    DEVICE_STATUSES,
    DEVICE_TRANSPORTS,
    EVENT_DIRECTIONS,
    EVENT_SEVERITIES,
    PRINT_STATUSES,
    DeviceConnector,
    DeviceEvent,
    DeviceGateway,
    DeviceGatewayAlert,
    DeviceGatewayMetricSnapshot,
    DevicePrintJob,
    DeviceProtocolProfile,
    IntegratedDevice,
    WearableMeasurement,
)
from .outbox import enqueue_message, list_messages as list_outbox_messages, summarize as summarize_outbox
from app.models.patient import Patient
from .schemas import (
    ConnectorRegisterRequest,
    ConnectorStatusUpdateRequest,
    DeviceRegisterRequest,
    DeviceStatusUpdateRequest,
    GatewayAlertAcknowledgeRequest,
    GatewayHeartbeatRequest,
    GatewayMetricIngestRequest,
    GatewayRegistrationRequest,
    PrinterJobRequest,
    ProtocolProfileRequest,
    WearableMeasurementIngestRequest,
)


PROTOCOL_CATALOG = [
    {
        "key": "HL7v2_MLLP",
        "label": "HL7 v2 over MLLP",
        "family": "clinical_messaging",
        "transports": ["MLLP", "TCP"],
        "intended_categories": ["laboratory_analyzer", "patient_monitor", "medical_measurement"],
        "production_requirement": "Server-side MLLP adapter with network allowlist, TLS tunnel, ACK/NAK handling, and message validation.",
    },
    {
        "key": "ASTM",
        "label": "ASTM LIS2-A2 / E1381 family",
        "family": "laboratory_messaging",
        "transports": ["TCP", "Serial"],
        "intended_categories": ["laboratory_analyzer"],
        "production_requirement": "Analyzer-specific adapter with framing, ENQ/ACK sequencing, field mapping, retry, and QC routing.",
    },
    {
        "key": "DICOM",
        "label": "DICOM / DICOM worklist",
        "family": "imaging",
        "transports": ["TCP", "HTTP"],
        "intended_categories": ["imaging"],
        "production_requirement": "PACS/worklist gateway with AE Title, TLS, modality allowlist, and DICOM conformance validation.",
    },
    {
        "key": "FHIR_Device",
        "label": "FHIR Device and Observation",
        "family": "health_data",
        "transports": ["HTTP"],
        "intended_categories": ["medical_measurement", "patient_monitor", "laboratory_analyzer", "imaging"],
        "production_requirement": "Authenticated FHIR server/client adapter with profile validation, provenance, and consent-aware routing.",
    },
    {
        "key": "TCP_IP",
        "label": "Raw TCP/IP",
        "family": "network_transport",
        "transports": ["TCP"],
        "intended_categories": ["network", "laboratory_analyzer", "printer"],
        "production_requirement": "Dedicated gateway with fixed egress policy, timeout, protocol parser, and no arbitrary destination support.",
    },
    {
        "key": "USB_Serial",
        "label": "USB / RS-232 Serial",
        "family": "local_transport",
        "transports": ["USB", "Serial"],
        "intended_categories": ["laboratory_analyzer", "medical_measurement", "barcode_scanner", "printer"],
        "production_requirement": "On-premises connector with OS device permissions, port binding, driver validation, and encrypted upstream channel.",
    },
    {
        "key": "Bluetooth",
        "label": "Bluetooth Low Energy",
        "family": "local_transport",
        "transports": ["Bluetooth"],
        "intended_categories": ["medical_measurement", "patient_monitor"],
        "production_requirement": "Managed local agent with pairing policy, device attestation, characteristic mapping, and encrypted relay.",
    },
    {
        "key": "WiFi",
        "label": "Wi-Fi device transport",
        "family": "network_transport",
        "transports": ["WiFi", "TCP", "HTTP"],
        "intended_categories": ["medical_measurement", "patient_monitor", "workstation", "network"],
        "production_requirement": "Segmented clinical network and gateway policy; Wi-Fi alone is not an application protocol.",
    },
    {
        "key": "ZPL",
        "label": "ZPL barcode labels",
        "family": "printing",
        "transports": ["TCP", "USB"],
        "intended_categories": ["printer"],
        "production_requirement": "Printer gateway with template allowlist, label preview, audit trail, and controlled port 9100/driver access.",
    },
    {
        "key": "IPL",
        "label": "IPL barcode labels",
        "family": "printing",
        "transports": ["TCP", "USB"],
        "intended_categories": ["printer"],
        "production_requirement": "Vendor-specific printer adapter with template validation and test-label workflow.",
    },
    {
        "key": "PDF",
        "label": "PDF report printing",
        "family": "printing",
        "transports": ["HTTP", "File"],
        "intended_categories": ["printer", "workstation"],
        "production_requirement": "Server-side report renderer and print queue with access controls; no direct browser printer trust.",
    },
]


def _event(
    db: Session,
    *,
    device: IntegratedDevice,
    event_type: str,
    summary: str,
    direction: str = "system",
    severity: str = "info",
    message_type: str | None = None,
    safe_metadata: dict | None = None,
) -> DeviceEvent:
    event = DeviceEvent(
        lab_id=device.lab_id,
        device_id=device.id,
        event_type=event_type,
        direction=direction,
        severity=severity,
        message_type=message_type,
        summary=summary,
        correlation_id=str(uuid4()),
        safe_metadata=safe_metadata or {"simulation_only": True},
    )
    db.add(event)
    db.flush()
    enqueue_message(
        db,
        lab_id=device.lab_id,
        event_type=f"device.{event_type}",
        aggregate_type="device_event",
        aggregate_id=device.id,
        idempotency_key=f"device-event:{device.lab_id}:{event.correlation_id}",
        correlation_id=event.correlation_id,
        payload_safe={
            "event_type": event.event_type,
            "direction": event.direction,
            "severity": event.severity,
            "message_type": event.message_type,
            "summary": event.summary,
            "safe_metadata": event.safe_metadata or {},
            "simulation_only": True,
            "raw_payload_stored": False,
        },
    )
    return event


def list_devices(db: Session, lab_id: int, *, category: str | None = None, status: str | None = None, limit: int = 100) -> tuple[int, list[IntegratedDevice]]:
    query = db.query(IntegratedDevice).filter(IntegratedDevice.lab_id == lab_id)
    if category:
        query = query.filter(IntegratedDevice.category == category)
    if status:
        query = query.filter(IntegratedDevice.status == status)
    total = query.count()
    devices = query.order_by(IntegratedDevice.updated_at.desc()).limit(limit).all()
    return total, devices


def get_device(db: Session, lab_id: int, device_uid: str) -> IntegratedDevice | None:
    return (
        db.query(IntegratedDevice)
        .filter(IntegratedDevice.lab_id == lab_id, IntegratedDevice.device_uid == device_uid)
        .first()
    )


def register_device(db: Session, lab_id: int, payload: DeviceRegisterRequest) -> IntegratedDevice:
    if payload.category not in DEVICE_CATEGORIES or payload.protocol not in DEVICE_PROTOCOLS or payload.transport not in DEVICE_TRANSPORTS:
        raise ValueError("Unsupported device category, protocol, or transport")
    if (
        db.query(IntegratedDevice)
        .filter(
            IntegratedDevice.lab_id == lab_id,
            IntegratedDevice.device_uid == payload.device_uid,
        )
        .first()
    ):
        raise ValueError("device_uid already exists in this laboratory")
    device = IntegratedDevice(
        lab_id=lab_id,
        device_uid=payload.device_uid,
        display_name=payload.display_name,
        category=payload.category,
        vendor=payload.vendor,
        model=payload.model,
        serial_number=payload.serial_number,
        protocol=payload.protocol,
        transport=payload.transport,
        endpoint=payload.endpoint,
        status="pending",
        simulation_only=True,
        capabilities=payload.capabilities,
        printer_profile=payload.printer_profile,
        maintenance_due_at=payload.maintenance_due_at,
        notes=payload.notes,
    )
    db.add(device)
    db.flush()
    _event(
        db,
        device=device,
        event_type="device_registered",
        summary="Device registered in local simulation mode",
        safe_metadata={"simulation_only": True, "protocol": device.protocol, "transport": device.transport},
    )
    db.commit()
    db.refresh(device)
    return device


def update_status(db: Session, lab_id: int, device_uid: str, payload: DeviceStatusUpdateRequest) -> IntegratedDevice:
    if payload.status not in DEVICE_STATUSES:
        raise ValueError("Unsupported device status")
    device = get_device(db, lab_id, device_uid)
    if device is None:
        raise LookupError("device not found")
    old_status = device.status
    device.status = payload.status
    if payload.status == "connected":
        device.last_seen_at = datetime.now(UTC)
    _event(
        db,
        device=device,
        event_type="status_changed",
        summary=f"Status changed from {old_status} to {payload.status}",
        severity="warning" if payload.status in {"error", "maintenance"} else "info",
        safe_metadata={"simulation_only": True, "previous_status": old_status, "reason": payload.reason},
    )
    db.commit()
    db.refresh(device)
    return device


def probe_device(db: Session, lab_id: int, device_uid: str) -> IntegratedDevice:
    device = get_device(db, lab_id, device_uid)
    if device is None:
        raise LookupError("device not found")
    device.status = "connected"
    device.last_seen_at = datetime.now(UTC)
    _event(
        db,
        device=device,
        event_type="connectivity_probe",
        summary="Simulated connectivity probe succeeded",
        safe_metadata={"simulation_only": True, "adapter_required_for_production": True},
    )
    db.commit()
    db.refresh(device)
    return device


def list_events(db: Session, lab_id: int, *, device_uid: str | None = None, severity: str | None = None, limit: int = 100) -> tuple[int, list[tuple[DeviceEvent, str]]]:
    query = (
        db.query(DeviceEvent, IntegratedDevice.device_uid)
        .join(IntegratedDevice, IntegratedDevice.id == DeviceEvent.device_id)
        .filter(DeviceEvent.lab_id == lab_id)
    )
    if device_uid:
        query = query.filter(IntegratedDevice.device_uid == device_uid)
    if severity:
        query = query.filter(DeviceEvent.severity == severity)
    total = query.count()
    return total, query.order_by(DeviceEvent.occurred_at.desc()).limit(limit).all()


def summary(db: Session, lab_id: int) -> dict:
    devices = db.query(IntegratedDevice).filter(IntegratedDevice.lab_id == lab_id).all()
    statuses = Counter(device.status for device in devices)
    categories = Counter(device.category for device in devices)
    recent_cutoff = datetime.now(UTC) - timedelta(hours=24)
    recent_events = (
        db.query(func.count(DeviceEvent.id))
        .filter(DeviceEvent.lab_id == lab_id, DeviceEvent.occurred_at >= recent_cutoff)
        .scalar()
        or 0
    )
    return {
        "total": len(devices),
        "connected": statuses.get("connected", 0),
        "disconnected": statuses.get("disconnected", 0),
        "error": statuses.get("error", 0),
        "maintenance": statuses.get("maintenance", 0),
        "pending": statuses.get("pending", 0),
        "simulation_only": sum(1 for device in devices if device.simulation_only),
        "by_category": dict(categories),
        "recent_events": recent_events,
    }


def create_print_job(db: Session, lab_id: int, actor_user_id: int, payload: PrinterJobRequest) -> DevicePrintJob:
    device = get_device(db, lab_id, payload.device_uid)
    if device is None:
        raise LookupError("device not found")
    if device.category != "printer":
        raise ValueError("selected device is not registered as a printer")
    if payload.printer_language not in {"PDF", "ZPL", "IPL"}:
        raise ValueError("unsupported printer language")
    if payload.printer_language == "PDF" and device.protocol not in {"PDF", "None", "IPP"}:
        raise ValueError("printer protocol does not accept PDF jobs")
    if payload.printer_language in {"ZPL", "IPL"} and device.protocol not in {payload.printer_language, "TCP_IP", "USB_Serial", "None"}:
        raise ValueError("printer protocol does not accept this label language")
    now = datetime.now(UTC)
    job = DevicePrintJob(
        lab_id=lab_id,
        device_id=device.id,
        document_type=payload.document_type,
        printer_language=payload.printer_language,
        label_count=payload.label_count,
        status="simulated_success",
        simulation_only=True,
        requested_by=actor_user_id,
        safe_metadata={"template_key": payload.template_key, "simulation_only": True},
        created_at=now,
        completed_at=now,
    )
    db.add(job)
    _event(
        db,
        device=device,
        event_type="print_job_simulated",
        direction="outbound",
        summary=f"Simulated {payload.printer_language} print job completed",
        safe_metadata={"simulation_only": True, "document_type": payload.document_type, "label_count": payload.label_count},
    )
    db.commit()
    db.refresh(job)
    return job


def list_print_jobs(db: Session, lab_id: int, *, device_uid: str | None = None, limit: int = 100) -> tuple[int, list[tuple[DevicePrintJob, str]]]:
    query = (
        db.query(DevicePrintJob, IntegratedDevice.device_uid)
        .join(IntegratedDevice, IntegratedDevice.id == DevicePrintJob.device_id)
        .filter(DevicePrintJob.lab_id == lab_id)
    )
    if device_uid:
        query = query.filter(IntegratedDevice.device_uid == device_uid)
    total = query.count()
    return total, query.order_by(DevicePrintJob.created_at.desc()).limit(limit).all()


def get_connector(db: Session, lab_id: int, connector_uid: str) -> DeviceConnector | None:
    return (
        db.query(DeviceConnector)
        .filter(DeviceConnector.lab_id == lab_id, DeviceConnector.connector_uid == connector_uid)
        .first()
    )


def list_connectors(
    db: Session, lab_id: int, *, status: str | None = None, limit: int = 100
) -> tuple[int, list[tuple[DeviceConnector, str | None]]]:
    query = (
        db.query(DeviceConnector, IntegratedDevice.device_uid)
        .outerjoin(IntegratedDevice, IntegratedDevice.id == DeviceConnector.device_id)
        .filter(DeviceConnector.lab_id == lab_id)
    )
    if status:
        query = query.filter(DeviceConnector.status == status)
    total = query.count()
    return total, query.order_by(DeviceConnector.updated_at.desc()).limit(limit).all()


def register_connector(db: Session, lab_id: int, payload: ConnectorRegisterRequest) -> DeviceConnector:
    if payload.protocol not in DEVICE_PROTOCOLS or payload.transport not in DEVICE_TRANSPORTS:
        raise ValueError("Unsupported connector protocol or transport")
    if payload.mode == "active":
        raise ValueError("active connectors require a separately governed gateway")
    if (
        db.query(DeviceConnector)
        .filter(DeviceConnector.lab_id == lab_id, DeviceConnector.connector_uid == payload.connector_uid)
        .first()
    ):
        raise ValueError("connector_uid already exists in this laboratory")

    device = None
    if payload.device_uid:
        device = get_device(db, lab_id, payload.device_uid)
        if device is None:
            raise LookupError("linked device not found")

    connector = DeviceConnector(
        lab_id=lab_id,
        connector_uid=payload.connector_uid,
        display_name=payload.display_name,
        device_id=device.id if device else None,
        protocol=payload.protocol,
        transport=payload.transport,
        mode=payload.mode,
        status="pending",
        contract_version=payload.contract_version,
        gateway_ref=payload.gateway_ref or (f"gateway://pending/{payload.connector_uid}" if payload.mode == "gateway_pending" else None),
        config_safe=payload.config_safe,
        capability_manifest=payload.capability_manifest,
        enabled=payload.enabled,
        simulation_only=True,
        maintenance_due_at=payload.maintenance_due_at,
    )
    db.add(connector)
    db.flush()
    if device:
        _event(
            db,
            device=device,
            event_type="connector_registered",
            summary="Connector registered in simulation or gateway-pending mode",
            safe_metadata={
                "simulation_only": True,
                "connector_uid": connector.connector_uid,
                "protocol": connector.protocol,
                "transport": connector.transport,
                "mode": connector.mode,
            },
        )
    db.commit()
    db.refresh(connector)
    return connector


def update_connector_status(
    db: Session, lab_id: int, connector_uid: str, payload: ConnectorStatusUpdateRequest
) -> DeviceConnector:
    connector = get_connector(db, lab_id, connector_uid)
    if connector is None:
        raise LookupError("connector not found")
    old_status = connector.status
    connector.status = payload.status
    connector.last_error = payload.last_error or (payload.reason if payload.status == "error" else None)
    if payload.status in {"healthy", "degraded"}:
        connector.last_heartbeat_at = datetime.now(UTC)
    device = db.query(IntegratedDevice).filter(IntegratedDevice.id == connector.device_id, IntegratedDevice.lab_id == lab_id).first()
    if device:
        _event(
            db,
            device=device,
            event_type="connector_status_changed",
            summary=f"Connector status changed from {old_status} to {payload.status}",
            severity="error" if payload.status == "error" else ("warning" if payload.status in {"degraded", "offline", "maintenance"} else "info"),
            safe_metadata={
                "simulation_only": True,
                "connector_uid": connector.connector_uid,
                "previous_status": old_status,
                "reason": payload.reason,
            },
        )
    db.commit()
    db.refresh(connector)
    return connector


def list_protocol_profiles(db: Session, lab_id: int, *, status: str | None = None, limit: int = 100) -> tuple[int, list[DeviceProtocolProfile]]:
    query = db.query(DeviceProtocolProfile).filter(DeviceProtocolProfile.lab_id == lab_id)
    if status:
        query = query.filter(DeviceProtocolProfile.status == status)
    total = query.count()
    return total, query.order_by(DeviceProtocolProfile.updated_at.desc()).limit(limit).all()


def register_protocol_profile(db: Session, lab_id: int, actor_user_id: int, payload: ProtocolProfileRequest) -> DeviceProtocolProfile:
    if payload.protocol not in DEVICE_PROTOCOLS:
        raise ValueError("Unsupported protocol profile")
    if (
        db.query(DeviceProtocolProfile)
        .filter(DeviceProtocolProfile.lab_id == lab_id, DeviceProtocolProfile.profile_key == payload.profile_key)
        .first()
    ):
        raise ValueError("profile_key already exists in this laboratory")
    if payload.status == "validated" and not payload.simulator_key:
        raise ValueError("validated profiles require a simulator_key in this phase")
    profile = DeviceProtocolProfile(
        lab_id=lab_id,
        profile_key=payload.profile_key,
        protocol=payload.protocol,
        version=payload.version,
        message_type=payload.message_type,
        framing=payload.framing,
        ack_strategy=payload.ack_strategy,
        encoding=payload.encoding,
        mapping_schema=payload.mapping_schema,
        validation_rules=payload.validation_rules,
        simulator_key=payload.simulator_key,
        status=payload.status,
        simulation_only=True,
        created_by=actor_user_id,
    )
    db.add(profile)
    db.commit()
    db.refresh(profile)
    return profile


SIMULATOR_CATALOG = [
    {
        "key": "hl7v2.oru.r01",
        "label": "HL7 v2 ORU^R01 result",
        "protocol": "HL7v2_MLLP",
        "family": "clinical_messaging",
        "contract_summary": "MSH/ORU^R01 contract with ACK/NAK expectation",
        "output": "safe result envelope metadata only",
    },
    {
        "key": "astm.result",
        "label": "ASTM analyzer result",
        "protocol": "ASTM",
        "family": "laboratory_messaging",
        "contract_summary": "ENQ/ACK frame sequence with result record",
        "output": "safe analyzer result metadata only",
    },
    {
        "key": "dicom.worklist",
        "label": "DICOM Modality Worklist",
        "protocol": "DICOM",
        "family": "imaging",
        "contract_summary": "C-FIND worklist exchange without DICOM objects",
        "output": "safe worklist transaction metadata only",
    },
    {
        "key": "fhir.device-observation",
        "label": "FHIR Device and Observation envelope",
        "protocol": "FHIR_Device",
        "family": "health_data",
        "contract_summary": "Device/Observation profile validation envelope",
        "output": "resource type and profile metadata only",
    },
    {
        "key": "zpl.specimen-label",
        "label": "ZPL specimen label",
        "protocol": "ZPL",
        "family": "printing",
        "contract_summary": "allowlisted specimen label template",
        "output": "label count and template metadata only",
    },
    {
        "key": "pdf.report",
        "label": "PDF laboratory report",
        "protocol": "PDF",
        "family": "printing",
        "contract_summary": "report render and queue contract",
        "output": "document type and page metadata only",
    },
]

_SIMULATOR_BY_KEY = {item["key"]: item for item in SIMULATOR_CATALOG}


def list_simulators() -> list[dict]:
    return list(SIMULATOR_CATALOG)


def simulate_connector(db: Session, lab_id: int, connector_uid: str, payload) -> dict:
    connector = get_connector(db, lab_id, connector_uid)
    if connector is None:
        raise LookupError("connector not found")
    descriptor = _SIMULATOR_BY_KEY.get(payload.simulator_key)
    if descriptor is None:
        raise ValueError("unsupported simulator")
    if descriptor["protocol"] != connector.protocol:
        raise ValueError("simulator protocol does not match connector protocol")
    if not connector.simulation_only or connector.mode == "active":
        raise ValueError("simulation is disabled for active gateway connectors")

    device = db.query(IntegratedDevice).filter(
        IntegratedDevice.id == connector.device_id,
        IntegratedDevice.lab_id == lab_id,
    ).first()
    scenario = payload.scenario
    if scenario == "success":
        connector_status = "healthy"
        outcome = "accepted"
        event_severity = "info"
        device_status = "connected"
        summary = f"Simulated {descriptor['label']} accepted for {payload.item_count} item(s)"
        connector.last_heartbeat_at = datetime.now(UTC)
        connector.last_error = None
    elif scenario == "degraded":
        connector_status = "degraded"
        outcome = "degraded"
        event_severity = "warning"
        device_status = "connected"
        summary = f"Simulated {descriptor['label']} completed with degraded transport"
        connector.last_error = "simulated degraded transport"
    else:
        connector_status = "error"
        outcome = "rejected"
        event_severity = "error"
        device_status = "error"
        reason = "malformed contract" if scenario == "malformed" else "simulated adapter failure"
        summary = f"Simulated {descriptor['label']} rejected: {reason}"
        connector.last_error = reason

    connector.status = connector_status
    event = None
    if device:
        device.status = device_status
        if device_status == "connected":
            device.last_seen_at = datetime.now(UTC)
        event = _event(
            db,
            device=device,
            event_type="simulated_protocol_exchange",
            direction="outbound" if descriptor["family"] == "printing" else "inbound",
            severity=event_severity,
            message_type=payload.message_type or descriptor["key"],
            summary=summary,
            safe_metadata={
                "simulation_only": True,
                "connector_uid": connector.connector_uid,
                "simulator_key": descriptor["key"],
                "scenario": scenario,
                "item_count": payload.item_count,
                "contract_summary": descriptor["contract_summary"],
                "raw_payload_stored": False,
            },
        )
        db.flush()
    db.commit()
    correlation_id = event.correlation_id if event else str(uuid4())
    return {
        "connector_uid": connector.connector_uid,
        "simulator_key": descriptor["key"],
        "scenario": scenario,
        "outcome": outcome,
        "connector_status": connector.status,
        "device_status": device.status if device else None,
        "event_id": event.id if event else None,
        "correlation_id": correlation_id,
        "simulation_only": True,
        "safe_summary": summary,
    }


def get_gateway(db: Session, lab_id: int, gateway_ref: str) -> DeviceGateway | None:
    return (
        db.query(DeviceGateway)
        .filter(DeviceGateway.lab_id == lab_id, DeviceGateway.gateway_ref == gateway_ref)
        .first()
    )


def list_gateways(db: Session, lab_id: int, *, status: str | None = None, limit: int = 100) -> tuple[int, list[DeviceGateway]]:
    query = db.query(DeviceGateway).filter(DeviceGateway.lab_id == lab_id)
    if status:
        query = query.filter(DeviceGateway.status == status)
    total = query.count()
    return total, query.order_by(DeviceGateway.updated_at.desc()).limit(limit).all()


def register_gateway(db: Session, lab_id: int, payload: GatewayRegistrationRequest) -> DeviceGateway:
    gateway = get_gateway(db, lab_id, payload.gateway_ref)
    if gateway is None:
        gateway = DeviceGateway(
            lab_id=lab_id,
            gateway_ref=payload.gateway_ref,
            display_name=payload.display_name,
            mode=payload.mode,
            status="pending",
            gateway_version=payload.gateway_version,
            contract_version=payload.contract_version,
            capabilities_safe=payload.capabilities_safe,
            enabled=payload.enabled,
            simulation_only=True,
        )
        db.add(gateway)
    else:
        if gateway.status == "revoked":
            raise ValueError("revoked gateway registrations cannot be reused")
        gateway.display_name = payload.display_name
        gateway.mode = payload.mode
        gateway.gateway_version = payload.gateway_version
        gateway.contract_version = payload.contract_version
        gateway.capabilities_safe = payload.capabilities_safe
        gateway.enabled = payload.enabled
        gateway.simulation_only = True
    db.commit()
    db.refresh(gateway)
    return gateway


def _ensure_gateway_from_metrics(db: Session, lab_id: int, payload: GatewayMetricIngestRequest) -> DeviceGateway:
    gateway = get_gateway(db, lab_id, payload.gateway_ref)
    if gateway is not None and (gateway.status == "revoked" or not gateway.enabled):
        raise ValueError("gateway registration is disabled")
    if gateway is None:
        gateway = DeviceGateway(
            lab_id=lab_id,
            gateway_ref=payload.gateway_ref,
            display_name=f"Synthetic gateway {payload.gateway_ref}",
            mode="simulated",
            status=payload.gateway_status,
            gateway_version=payload.gateway_version,
            contract_version="v1",
            enabled=True,
            simulation_only=True,
        )
        db.add(gateway)
    gateway.status = payload.gateway_status
    gateway.gateway_version = payload.gateway_version or gateway.gateway_version
    gateway.last_heartbeat_at = payload.captured_at or datetime.now(UTC)
    gateway.last_error = "reported gateway error" if payload.gateway_status in {"offline", "error"} else None
    gateway.simulation_only = True
    return gateway


def record_gateway_heartbeat(db: Session, lab_id: int, payload: GatewayHeartbeatRequest) -> DeviceGatewayMetricSnapshot:
    gateway = get_gateway(db, lab_id, payload.gateway_ref)
    if gateway is None:
        raise LookupError("gateway is not registered in this laboratory")
    if not gateway.enabled or gateway.status == "revoked":
        raise ValueError("gateway registration is disabled")
    if not payload.simulation_only:
        raise ValueError("gateway heartbeat is simulation-only until gateway authentication is deployed")
    return ingest_gateway_metrics(db, lab_id, payload)


def list_outbox(db: Session, lab_id: int, *, status: str | None = None, gateway_ref: str | None = None, limit: int = 100):
    return list_outbox_messages(db, lab_id, status=status, gateway_ref=gateway_ref, limit=limit)


def process_outbox(db: Session, lab_id: int, *, limit: int = 50) -> dict:
    from .outbox import process_batch

    return process_batch(db, lab_id, limit=limit)


MONITORING_THRESHOLDS = {
    "gateway_heartbeat_warning_seconds": 300.0,
    "gateway_heartbeat_critical_seconds": 900.0,
    "outbox_oldest_age_warning_seconds": 300.0,
    "outbox_oldest_age_critical_seconds": 900.0,
    "disk_used_warning_percent": 85.0,
    "disk_used_critical_percent": 95.0,
    "dead_letter_warning_count": 1.0,
    "dead_letter_critical_count": 10.0,
    "worker_lag_warning_seconds": 120.0,
    "worker_lag_critical_seconds": 600.0,
    "transport_latency_warning_ms": 2000.0,
    "transport_latency_critical_ms": 10000.0,
}


def _alert_specs(payload: GatewayMetricIngestRequest) -> list[dict]:
    specs: list[dict] = []

    if payload.outbox_oldest_age_seconds >= MONITORING_THRESHOLDS["outbox_oldest_age_critical_seconds"]:
        specs.append({"key": "outbox_oldest_age", "severity": "critical", "title": "تأخير Outbox حرج", "metric": "outbox_oldest_age_seconds", "value": payload.outbox_oldest_age_seconds, "threshold": MONITORING_THRESHOLDS["outbox_oldest_age_critical_seconds"], "summary": "أقدم رسالة في Outbox تجاوزت حد التأخير الحرج."})
    elif payload.outbox_oldest_age_seconds >= MONITORING_THRESHOLDS["outbox_oldest_age_warning_seconds"]:
        specs.append({"key": "outbox_oldest_age", "severity": "warning", "title": "تأخير Outbox مرتفع", "metric": "outbox_oldest_age_seconds", "value": payload.outbox_oldest_age_seconds, "threshold": MONITORING_THRESHOLDS["outbox_oldest_age_warning_seconds"], "summary": "أقدم رسالة في Outbox تجاوزت حد التنبيه."})

    if payload.disk_used_percent >= MONITORING_THRESHOLDS["disk_used_critical_percent"]:
        specs.append({"key": "disk_usage", "severity": "critical", "title": "استهلاك القرص حرج", "metric": "disk_used_percent", "value": payload.disk_used_percent, "threshold": MONITORING_THRESHOLDS["disk_used_critical_percent"], "summary": "استهلاك قرص Gateway تجاوز الحد الحرج؛ يجب إيقاف قبول بيانات جديدة وفق runbook."})
    elif payload.disk_used_percent >= MONITORING_THRESHOLDS["disk_used_warning_percent"]:
        specs.append({"key": "disk_usage", "severity": "warning", "title": "استهلاك القرص مرتفع", "metric": "disk_used_percent", "value": payload.disk_used_percent, "threshold": MONITORING_THRESHOLDS["disk_used_warning_percent"], "summary": "استهلاك قرص Gateway تجاوز حد التنبيه."})

    if payload.outbox_dead_letter_count >= MONITORING_THRESHOLDS["dead_letter_critical_count"]:
        specs.append({"key": "dead_letters", "severity": "critical", "title": "رسائل Dead Letter حرجة", "metric": "outbox_dead_letter_count", "value": float(payload.outbox_dead_letter_count), "threshold": MONITORING_THRESHOLDS["dead_letter_critical_count"], "summary": "تراكمت رسائل Dead Letter وتحتاج مراجعة تشغيلية."})
    elif payload.outbox_dead_letter_count >= MONITORING_THRESHOLDS["dead_letter_warning_count"]:
        specs.append({"key": "dead_letters", "severity": "warning", "title": "رسائل Dead Letter موجودة", "metric": "outbox_dead_letter_count", "value": float(payload.outbox_dead_letter_count), "threshold": MONITORING_THRESHOLDS["dead_letter_warning_count"], "summary": "توجد رسائل Dead Letter تحتاج مراجعة قبل الحذف أو إعادة المعالجة."})

    if payload.worker_lag_seconds >= MONITORING_THRESHOLDS["worker_lag_critical_seconds"]:
        specs.append({"key": "worker_lag", "severity": "critical", "title": "العامل متأخر حرجًا", "metric": "worker_lag_seconds", "value": payload.worker_lag_seconds, "threshold": MONITORING_THRESHOLDS["worker_lag_critical_seconds"], "summary": "تأخر عامل Gateway عن heartbeat أو المعالجة تجاوز الحد الحرج."})
    elif payload.worker_lag_seconds >= MONITORING_THRESHOLDS["worker_lag_warning_seconds"]:
        specs.append({"key": "worker_lag", "severity": "warning", "title": "العامل متأخر", "metric": "worker_lag_seconds", "value": payload.worker_lag_seconds, "threshold": MONITORING_THRESHOLDS["worker_lag_warning_seconds"], "summary": "تأخر عامل Gateway عن heartbeat أو المعالجة تجاوز حد التنبيه."})

    if payload.transport_latency_ms is not None:
        if payload.transport_latency_ms >= MONITORING_THRESHOLDS["transport_latency_critical_ms"]:
            specs.append({"key": "transport_latency", "severity": "critical", "title": "تأخير النقل حرج", "metric": "transport_latency_ms", "value": payload.transport_latency_ms, "threshold": MONITORING_THRESHOLDS["transport_latency_critical_ms"], "summary": "زمن النقل بين Gateway وGULA تجاوز الحد الحرج."})
        elif payload.transport_latency_ms >= MONITORING_THRESHOLDS["transport_latency_warning_ms"]:
            specs.append({"key": "transport_latency", "severity": "warning", "title": "تأخير النقل مرتفع", "metric": "transport_latency_ms", "value": payload.transport_latency_ms, "threshold": MONITORING_THRESHOLDS["transport_latency_warning_ms"], "summary": "زمن النقل بين Gateway وGULA تجاوز حد التنبيه."})

    if payload.gateway_status in {"offline", "error"}:
        specs.append({"key": "gateway_status", "severity": "critical", "title": "Gateway غير متاحة", "metric": "gateway_status", "value": None, "threshold": None, "summary": "حالة Gateway تشير إلى انقطاع أو خطأ حرج."})
    elif payload.gateway_status == "degraded":
        specs.append({"key": "gateway_status", "severity": "warning", "title": "Gateway متدهورة", "metric": "gateway_status", "value": None, "threshold": None, "summary": "Gateway تعمل بحالة متدهورة وتحتاج متابعة."})

    return specs


def _upsert_gateway_alert(db: Session, *, lab_id: int, payload: GatewayMetricIngestRequest, spec: dict, captured_at: datetime) -> DeviceGatewayAlert:
    alert = (
        db.query(DeviceGatewayAlert)
        .filter(
            DeviceGatewayAlert.lab_id == lab_id,
            DeviceGatewayAlert.gateway_ref == payload.gateway_ref,
            DeviceGatewayAlert.alert_key == spec["key"],
            DeviceGatewayAlert.status.in_(["open", "acknowledged"]),
        )
        .order_by(DeviceGatewayAlert.last_seen_at.desc())
        .first()
    )
    if alert is None:
        alert = DeviceGatewayAlert(
            lab_id=lab_id,
            gateway_ref=payload.gateway_ref,
            alert_key=spec["key"],
            first_seen_at=captured_at,
            acknowledged_at=None,
            resolved_at=None,
            correlation_id=str(uuid4()),
            simulation_only=True,
        )
        db.add(alert)
    alert.severity = spec["severity"]
    alert.status = "open" if alert.status != "acknowledged" else alert.status
    alert.title = spec["title"]
    alert.summary = spec["summary"]
    alert.metric_key = spec["metric"]
    alert.current_value = spec["value"]
    alert.threshold_value = spec["threshold"]
    alert.last_seen_at = captured_at
    alert.resolved_at = None
    alert.simulation_only = True
    alert.safe_metadata = {"simulation_only": True, "gateway_status": payload.gateway_status}
    return alert


def _resolve_missing_alerts(db: Session, *, lab_id: int, payload: GatewayMetricIngestRequest, active_keys: set[str], captured_at: datetime) -> None:
    active_alerts = (
        db.query(DeviceGatewayAlert)
        .filter(
            DeviceGatewayAlert.lab_id == lab_id,
            DeviceGatewayAlert.gateway_ref == payload.gateway_ref,
            DeviceGatewayAlert.status.in_(["open", "acknowledged"]),
        )
        .all()
    )
    for alert in active_alerts:
        if alert.alert_key not in active_keys:
            alert.status = "resolved"
            alert.resolved_at = captured_at
            alert.last_seen_at = captured_at


def ingest_gateway_metrics(db: Session, lab_id: int, payload: GatewayMetricIngestRequest) -> DeviceGatewayMetricSnapshot:
    if not payload.simulation_only:
        raise ValueError("gateway metrics ingestion is simulation-only until gateway authentication is deployed")
    captured_at = payload.captured_at or datetime.now(UTC)
    gateway = _ensure_gateway_from_metrics(db, lab_id, payload)
    gateway.last_heartbeat_at = payload.worker_last_heartbeat_at or captured_at
    snapshot = DeviceGatewayMetricSnapshot(
        lab_id=lab_id,
        gateway_ref=payload.gateway_ref,
        gateway_status=payload.gateway_status,
        gateway_version=payload.gateway_version,
        outbox_pending_count=payload.outbox_pending_count,
        outbox_oldest_age_seconds=payload.outbox_oldest_age_seconds,
        outbox_retry_count=payload.outbox_retry_count,
        outbox_dead_letter_count=payload.outbox_dead_letter_count,
        disk_used_percent=payload.disk_used_percent,
        disk_free_bytes=payload.disk_free_bytes,
        worker_last_heartbeat_at=payload.worker_last_heartbeat_at,
        worker_lag_seconds=payload.worker_lag_seconds,
        transport_latency_ms=payload.transport_latency_ms,
        captured_at=captured_at,
        simulation_only=True,
        safe_metadata=payload.safe_metadata,
    )
    db.add(snapshot)
    for spec in _alert_specs(payload):
        _upsert_gateway_alert(db, lab_id=lab_id, payload=payload, spec=spec, captured_at=captured_at)
    _resolve_missing_alerts(db, lab_id=lab_id, payload=payload, active_keys={spec["key"] for spec in _alert_specs(payload)}, captured_at=captured_at)
    db.commit()
    db.refresh(snapshot)
    return snapshot


def _latest_gateway_metrics(db: Session, lab_id: int, limit: int = 100) -> list[DeviceGatewayMetricSnapshot]:
    rows = (
        db.query(DeviceGatewayMetricSnapshot)
        .filter(DeviceGatewayMetricSnapshot.lab_id == lab_id)
        .order_by(DeviceGatewayMetricSnapshot.captured_at.desc())
        .limit(max(100, limit * 10))
        .all()
    )
    latest: list[DeviceGatewayMetricSnapshot] = []
    seen: set[str] = set()
    for row in rows:
        if row.gateway_ref in seen:
            continue
        seen.add(row.gateway_ref)
        latest.append(row)
        if len(latest) >= limit:
            break
    return latest


def list_gateway_alerts(db: Session, lab_id: int, *, alert_status: str | None = None, limit: int = 100) -> tuple[int, list[DeviceGatewayAlert]]:
    query = db.query(DeviceGatewayAlert).filter(DeviceGatewayAlert.lab_id == lab_id)
    if alert_status:
        query = query.filter(DeviceGatewayAlert.status == alert_status)
    total = query.count()
    return total, query.order_by(DeviceGatewayAlert.last_seen_at.desc()).limit(limit).all()


def monitoring_snapshot(db: Session, lab_id: int) -> dict:
    latest = _latest_gateway_metrics(db, lab_id)
    _, gateways = list_gateways(db, lab_id, limit=100)
    active_query = db.query(DeviceGatewayAlert).filter(
        DeviceGatewayAlert.lab_id == lab_id,
        DeviceGatewayAlert.status.in_(["open", "acknowledged"]),
    )
    alerts = active_query.order_by(DeviceGatewayAlert.last_seen_at.desc()).limit(100).all()
    return {
        "gateway_count": len(latest),
        "healthy_gateway_count": sum(row.gateway_status == "healthy" for row in latest),
        "degraded_gateway_count": sum(row.gateway_status == "degraded" for row in latest),
        "offline_gateway_count": sum(row.gateway_status in {"offline", "error"} for row in latest),
        "latest_metric": latest[0] if latest else None,
        "open_alert_count": len(alerts),
        "critical_alert_count": sum(alert.severity == "critical" for alert in alerts),
        "alerts": alerts,
        "thresholds": MONITORING_THRESHOLDS,
        "simulation_only": True,
        "gateways": gateways,
        "outbox": summarize_outbox(db, lab_id),
    }


def acknowledge_gateway_alert(db: Session, lab_id: int, alert_id: int, actor_user_id: int, payload: GatewayAlertAcknowledgeRequest) -> DeviceGatewayAlert:
    alert = (
        db.query(DeviceGatewayAlert)
        .filter(DeviceGatewayAlert.id == alert_id, DeviceGatewayAlert.lab_id == lab_id)
        .first()
    )
    if alert is None:
        raise LookupError("gateway alert not found")
    if alert.status == "resolved":
        raise ValueError("resolved gateway alerts cannot be acknowledged")
    alert.status = "acknowledged"
    alert.acknowledged_by = actor_user_id
    alert.acknowledged_at = datetime.now(UTC)
    alert.safe_metadata = {**(alert.safe_metadata or {}), "ack_note_present": bool(payload.note), "simulation_only": True}
    db.commit()
    db.refresh(alert)
    return alert


_WEARABLE_EXPECTED_UNITS = {
    "heart_rate": {"bpm"},
    "respiratory_rate": {"breaths/min", "bpm"},
    "spo2": {"%"},
    "temperature": {"C", "°C", "F", "°F"},
    "systolic_bp": {"mmHg"},
    "diastolic_bp": {"mmHg"},
    "blood_glucose": {"mg/dL", "mmol/L"},
    "steps": {"count"},
    "weight": {"kg", "lb"},
}


def ingest_wearable_measurement(
    db: Session,
    lab_id: int,
    payload: WearableMeasurementIngestRequest,
) -> tuple[WearableMeasurement, bool]:
    """Persist a canonical wearable reading with tenant and idempotency guards.

    Provider payloads must be normalized by a governed adapter before calling this
    function. The API stores only the safe canonical fields and provenance summary.
    """
    if not payload.simulation_only:
        raise ValueError("live wearable adapters require provider authentication and are not enabled yet")
    if payload.quality_status == "invalid":
        raise ValueError("invalid wearable measurements are not accepted")
    expected_units = _WEARABLE_EXPECTED_UNITS.get(payload.metric_code, set())
    if payload.unit not in expected_units:
        raise ValueError(f"unit {payload.unit!r} is not valid for {payload.metric_code}")

    patient = (
        db.query(Patient)
        .filter(Patient.id == payload.patient_id, Patient.lab_id == lab_id)
        .first()
    )
    if patient is None:
        raise LookupError("patient is not registered in this laboratory")

    device_id = None
    if payload.device_uid:
        device = get_device(db, lab_id, payload.device_uid)
        if device is None:
            raise LookupError("wearable device is not registered in this laboratory")
        device_id = device.id
        device.last_seen_at = payload.measured_at
        device.status = "connected"

    source = payload.source.strip().lower()
    existing = (
        db.query(WearableMeasurement)
        .filter(
            WearableMeasurement.lab_id == lab_id,
            WearableMeasurement.source == source,
            WearableMeasurement.source_event_id == payload.source_event_id,
        )
        .first()
    )
    if existing is not None:
        if (
            existing.patient_id != payload.patient_id
            or existing.metric_code != payload.metric_code
            or existing.value != payload.value
            or existing.unit != payload.unit
        ):
            raise ValueError("source event id was already used with a different measurement")
        return existing, True

    measurement = WearableMeasurement(
        lab_id=lab_id,
        patient_id=payload.patient_id,
        device_id=device_id,
        source=source,
        metric_code=payload.metric_code,
        value=payload.value,
        unit=payload.unit,
        measured_at=payload.measured_at,
        quality_score=payload.quality_score,
        quality_status=payload.quality_status,
        source_event_id=payload.source_event_id,
        provenance=payload.provenance,
        simulation_only=True,
    )
    db.add(measurement)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        existing = (
            db.query(WearableMeasurement)
            .filter(
                WearableMeasurement.lab_id == lab_id,
                WearableMeasurement.source == source,
                WearableMeasurement.source_event_id == payload.source_event_id,
            )
            .first()
        )
        if existing is None:
            raise
        return existing, True
    db.refresh(measurement)
    return measurement, False


def list_wearable_measurements(
    db: Session,
    lab_id: int,
    *,
    patient_id: int,
    metric_code: str | None = None,
    limit: int = 100,
) -> tuple[int, list[WearableMeasurement]]:
    query = db.query(WearableMeasurement).filter(
        WearableMeasurement.lab_id == lab_id,
        WearableMeasurement.patient_id == patient_id,
    )
    if metric_code:
        query = query.filter(WearableMeasurement.metric_code == metric_code)
    total = query.count()
    rows = query.order_by(WearableMeasurement.measured_at.desc()).limit(limit).all()
    return total, rows



def clinician_baseline_summary(
    db: Session,
    lab_id: int,
    patient_id: int,
    metric_code: str,
    *,
    limit: int = 28,
) -> dict:
    """Return an advisory baseline summary for a clinician dashboard.

    This endpoint is deliberately read-only: it reports personal deviation and
    evidence quality, never diagnoses a condition or changes a care plan.
    """
    from app.chronic_care.baselines import build_baseline, evaluate_against_baseline

    if limit < 7 or limit > 180:
        raise ValueError("limit must be between 7 and 180")
    patient = db.query(Patient).filter(Patient.id == patient_id, Patient.lab_id == lab_id).first()
    if patient is None:
        raise LookupError("patient not found in this laboratory")
    rows = (
        db.query(WearableMeasurement)
        .filter(
            WearableMeasurement.lab_id == lab_id,
            WearableMeasurement.patient_id == patient_id,
            WearableMeasurement.metric_code == metric_code,
            WearableMeasurement.quality_status.in_(["good", "unknown"]),
        )
        .order_by(WearableMeasurement.measured_at.desc())
        .limit(limit)
        .all()
    )
    if not rows:
        raise LookupError("no valid measurements found for this metric")

    chronological = list(reversed(rows))
    baseline = build_baseline(metric_code, [row.value for row in chronological], min_samples=7)
    latest = rows[0]
    evaluation = evaluate_against_baseline(baseline, latest.value)
    return {
        "patient_id": patient_id,
        "metric_code": metric_code,
        "measurement_count": len(rows),
        "latest": {
            "value": latest.value,
            "unit": latest.unit,
            "measured_at": latest.measured_at,
            "quality_score": latest.quality_score,
            "source": latest.source,
        },
        "baseline": {
            "status": baseline.status,
            "median": baseline.median,
            "mad": baseline.mad,
            "lower_bound": baseline.lower_bound,
            "upper_bound": baseline.upper_bound,
            "confidence": baseline.confidence,
            "generated_at": baseline.generated_at,
        },
        "evaluation": {
            "is_anomaly": evaluation.is_anomaly,
            "severity": evaluation.severity,
            "deviation_score": evaluation.deviation_score,
            "confidence": evaluation.confidence,
            "explanation": evaluation.explanation,
            "requires_clinician_review": evaluation.requires_clinician_review,
            "advisory_only": True,
        },
    }
