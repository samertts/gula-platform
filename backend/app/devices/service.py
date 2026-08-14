from __future__ import annotations

from collections import Counter
from datetime import datetime, timedelta
from uuid import uuid4

from sqlalchemy import func
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
    DevicePrintJob,
    DeviceProtocolProfile,
    IntegratedDevice,
)
from .schemas import (
    ConnectorRegisterRequest,
    ConnectorStatusUpdateRequest,
    DeviceRegisterRequest,
    DeviceStatusUpdateRequest,
    PrinterJobRequest,
    ProtocolProfileRequest,
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
    if db.query(IntegratedDevice).filter(IntegratedDevice.device_uid == payload.device_uid).first():
        raise ValueError("device_uid already exists")
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
