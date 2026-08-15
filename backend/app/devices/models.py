"""Persistence models for the GULA device integration hub.

The hub stores connection metadata and safe event summaries only. It never stores
raw clinical payloads or opens a socket from the API process; real adapters belong
to a separately governed gateway.
"""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Index, Integer, JSON, String, Text, UniqueConstraint

from app._compat import UTC
from ..database import Base


DEVICE_CATEGORIES = (
    "medical_measurement",
    "patient_monitor",
    "laboratory_analyzer",
    "imaging",
    "printer",
    "workstation",
    "network",
    "barcode_scanner",
    "other",
)
DEVICE_STATUSES = ("connected", "disconnected", "error", "maintenance", "pending")
DEVICE_PROTOCOLS = (
    "HL7v2_MLLP",
    "ASTM",
    "DICOM",
    "FHIR_Device",
    "TCP_IP",
    "USB_Serial",
    "Bluetooth",
    "WiFi",
    "IPP",
    "ZPL",
    "IPL",
    "PDF",
    "None",
)
DEVICE_TRANSPORTS = ("MLLP", "TCP", "Serial", "USB", "Bluetooth", "WiFi", "HTTP", "File", "None")
EVENT_DIRECTIONS = ("inbound", "outbound", "system")
EVENT_SEVERITIES = ("info", "warning", "error")
PRINT_STATUSES = ("queued", "simulated_success", "failed")
CONNECTOR_MODES = ("simulated", "gateway_pending", "active", "disabled")
CONNECTOR_STATUSES = ("healthy", "degraded", "offline", "error", "maintenance", "pending")
GATEWAY_MODES = ("simulated", "local_pending", "active", "disabled")
GATEWAY_STATUSES = ("healthy", "degraded", "offline", "error", "maintenance", "pending", "revoked")
PROFILE_STATUSES = ("draft", "validated", "retired")
DEVICE_OUTBOX_STATUSES = ("pending", "processing", "retry", "delivered", "dead_letter")
DEVICE_OUTBOX_MAX_ATTEMPTS = 5


def utc_now() -> datetime:
    return datetime.now(UTC)


class IntegratedDevice(Base):
    __tablename__ = "integrated_devices"
    __table_args__ = (
        Index("ix_integrated_devices_lab_status", "lab_id", "status"),
        UniqueConstraint("lab_id", "device_uid", name="uq_integrated_devices_lab_uid"),
        Index("ix_integrated_devices_lab_category", "lab_id", "category"),
        Index("ix_integrated_devices_last_seen", "last_seen_at"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    lab_id = Column(Integer, ForeignKey("labs.id", ondelete="CASCADE"), nullable=False, index=True)
    device_uid = Column(String(96), nullable=False, index=True)
    display_name = Column(String(200), nullable=False)
    category = Column(String(48), nullable=False, default="other")
    vendor = Column(String(120), nullable=True)
    model = Column(String(120), nullable=True)
    serial_number = Column(String(120), nullable=True)
    protocol = Column(String(32), nullable=False, default="None")
    transport = Column(String(24), nullable=False, default="None")
    endpoint = Column(String(255), nullable=True)
    status = Column(String(24), nullable=False, default="pending")
    simulation_only = Column(Boolean, nullable=False, default=True)
    last_seen_at = Column(DateTime(timezone=True), nullable=True)
    maintenance_due_at = Column(DateTime(timezone=True), nullable=True)
    capabilities = Column(JSON, nullable=True)
    printer_profile = Column(JSON, nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=utc_now)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=utc_now, onupdate=utc_now)


class DeviceGateway(Base):
    """Tenant-scoped registration record for a local or simulated gateway."""

    __tablename__ = "device_gateways"
    __table_args__ = (
        UniqueConstraint("lab_id", "gateway_ref", name="uq_device_gateways_lab_ref"),
        Index("ix_device_gateways_lab_status", "lab_id", "status"),
        Index("ix_device_gateways_heartbeat", "lab_id", "last_heartbeat_at"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    lab_id = Column(Integer, ForeignKey("labs.id", ondelete="CASCADE"), nullable=False)
    gateway_ref = Column(String(160), nullable=False)
    display_name = Column(String(200), nullable=False)
    mode = Column(String(24), nullable=False, default="simulated")
    status = Column(String(24), nullable=False, default="pending")
    gateway_version = Column(String(48), nullable=True)
    contract_version = Column(String(24), nullable=False, default="v1")
    capabilities_safe = Column(JSON, nullable=True)
    last_heartbeat_at = Column(DateTime(timezone=True), nullable=True)
    last_error = Column(String(500), nullable=True)
    enabled = Column(Boolean, nullable=False, default=True)
    simulation_only = Column(Boolean, nullable=False, default=True)
    registered_at = Column(DateTime(timezone=True), nullable=False, default=utc_now)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=utc_now, onupdate=utc_now)


class DeviceConnector(Base):
    """A safe control-plane record for a connector hosted by a future gateway."""

    __tablename__ = "device_connectors"
    __table_args__ = (
        UniqueConstraint("lab_id", "connector_uid", name="uq_device_connectors_lab_uid"),
        Index("ix_device_connectors_lab_status", "lab_id", "status"),
        Index("ix_device_connectors_lab_protocol", "lab_id", "protocol"),
        Index("ix_device_connectors_heartbeat", "last_heartbeat_at"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    lab_id = Column(Integer, ForeignKey("labs.id", ondelete="CASCADE"), nullable=False)
    connector_uid = Column(String(96), nullable=False)
    display_name = Column(String(200), nullable=False)
    device_id = Column(Integer, ForeignKey("integrated_devices.id", ondelete="SET NULL"), nullable=True)
    protocol = Column(String(32), nullable=False)
    transport = Column(String(24), nullable=False)
    mode = Column(String(24), nullable=False, default="simulated")
    status = Column(String(24), nullable=False, default="pending")
    contract_version = Column(String(24), nullable=False, default="v1")
    gateway_ref = Column(String(160), nullable=True)
    config_safe = Column(JSON, nullable=True)
    capability_manifest = Column(JSON, nullable=True)
    last_heartbeat_at = Column(DateTime(timezone=True), nullable=True)
    last_error = Column(String(500), nullable=True)
    enabled = Column(Boolean, nullable=False, default=True)
    simulation_only = Column(Boolean, nullable=False, default=True)
    maintenance_due_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=utc_now)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=utc_now, onupdate=utc_now)


class DeviceProtocolProfile(Base):
    """Versioned, secret-free protocol contract used by simulated or future adapters."""

    __tablename__ = "device_protocol_profiles"
    __table_args__ = (
        UniqueConstraint("lab_id", "profile_key", name="uq_device_protocol_profiles_lab_key"),
        Index("ix_device_protocol_profiles_lab_protocol", "lab_id", "protocol"),
        Index("ix_device_protocol_profiles_lab_status", "lab_id", "status"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    lab_id = Column(Integer, ForeignKey("labs.id", ondelete="CASCADE"), nullable=False)
    profile_key = Column(String(120), nullable=False)
    protocol = Column(String(32), nullable=False)
    version = Column(String(24), nullable=False, default="v1")
    message_type = Column(String(64), nullable=True)
    framing = Column(String(120), nullable=True)
    ack_strategy = Column(String(80), nullable=True)
    encoding = Column(String(40), nullable=True, default="UTF-8")
    mapping_schema = Column(JSON, nullable=True)
    validation_rules = Column(JSON, nullable=True)
    simulator_key = Column(String(80), nullable=True)
    status = Column(String(24), nullable=False, default="draft")
    simulation_only = Column(Boolean, nullable=False, default=True)
    created_by = Column(Integer, ForeignKey("lab_users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=utc_now)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=utc_now, onupdate=utc_now)


class DeviceEvent(Base):
    __tablename__ = "device_events"
    __table_args__ = (
        Index("ix_device_events_lab_occurred", "lab_id", "occurred_at"),
        Index("ix_device_events_device_occurred", "device_id", "occurred_at"),
        Index("ix_device_events_severity", "lab_id", "severity", "occurred_at"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    lab_id = Column(Integer, ForeignKey("labs.id", ondelete="CASCADE"), nullable=False)
    device_id = Column(Integer, ForeignKey("integrated_devices.id", ondelete="CASCADE"), nullable=False)
    event_type = Column(String(64), nullable=False)
    direction = Column(String(16), nullable=False, default="system")
    severity = Column(String(16), nullable=False, default="info")
    message_type = Column(String(64), nullable=True)
    summary = Column(String(500), nullable=False)
    correlation_id = Column(String(96), nullable=True, index=True)
    safe_metadata = Column(JSON, nullable=True)
    occurred_at = Column(DateTime(timezone=True), nullable=False, default=utc_now)


class DeviceOutboxMessage(Base):
    """Tenant-scoped transactional outbox record for safe gateway envelopes."""

    __tablename__ = "device_outbox_messages"
    __table_args__ = (
        UniqueConstraint("lab_id", "idempotency_key", name="uq_device_outbox_lab_idempotency"),
        Index("ix_device_outbox_lab_status_next", "lab_id", "status", "next_attempt_at"),
        Index("ix_device_outbox_gateway_status", "gateway_ref", "status", "next_attempt_at"),
        Index("ix_device_outbox_created", "lab_id", "created_at"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    lab_id = Column(Integer, ForeignKey("labs.id", ondelete="CASCADE"), nullable=False)
    gateway_ref = Column(String(160), nullable=True)
    event_type = Column(String(96), nullable=False)
    aggregate_type = Column(String(64), nullable=False, default="device_event")
    aggregate_id = Column(Integer, nullable=True)
    idempotency_key = Column(String(160), nullable=False)
    correlation_id = Column(String(96), nullable=False)
    payload_safe = Column(JSON, nullable=False)
    status = Column(String(24), nullable=False, default="pending")
    attempts = Column(Integer, nullable=False, default=0)
    max_attempts = Column(Integer, nullable=False, default=DEVICE_OUTBOX_MAX_ATTEMPTS)
    last_error = Column(String(500), nullable=True)
    next_attempt_at = Column(DateTime(timezone=True), nullable=False, default=utc_now)
    locked_at = Column(DateTime(timezone=True), nullable=True)
    delivered_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=utc_now)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=utc_now, onupdate=utc_now)
    simulation_only = Column(Boolean, nullable=False, default=True)


class DevicePrintJob(Base):
    __tablename__ = "device_print_jobs"
    __table_args__ = (
        Index("ix_device_print_jobs_lab_created", "lab_id", "created_at"),
        Index("ix_device_print_jobs_device_status", "device_id", "status"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    lab_id = Column(Integer, ForeignKey("labs.id", ondelete="CASCADE"), nullable=False)
    device_id = Column(Integer, ForeignKey("integrated_devices.id", ondelete="CASCADE"), nullable=False)
    document_type = Column(String(32), nullable=False)
    printer_language = Column(String(16), nullable=False, default="PDF")
    label_count = Column(Integer, nullable=False, default=1)
    status = Column(String(24), nullable=False, default="queued")
    simulation_only = Column(Boolean, nullable=False, default=True)
    requested_by = Column(Integer, ForeignKey("lab_users.id", ondelete="SET NULL"), nullable=True)
    safe_metadata = Column(JSON, nullable=True)
    error_message = Column(String(500), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=utc_now)
    completed_at = Column(DateTime(timezone=True), nullable=True)


class DeviceGatewayMetricSnapshot(Base):
    """Safe operational metrics reported by a local gateway or simulator."""

    __tablename__ = "device_gateway_metric_snapshots"
    __table_args__ = (
        Index("ix_device_gateway_metrics_lab_captured", "lab_id", "captured_at"),
        Index("ix_device_gateway_metrics_gateway_captured", "gateway_ref", "captured_at"),
        Index("ix_device_gateway_metrics_outbox_age", "lab_id", "outbox_oldest_age_seconds"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    lab_id = Column(Integer, ForeignKey("labs.id", ondelete="CASCADE"), nullable=False)
    gateway_ref = Column(String(160), nullable=False)
    gateway_status = Column(String(24), nullable=False, default="healthy")
    gateway_version = Column(String(48), nullable=True)
    outbox_pending_count = Column(Integer, nullable=False, default=0)
    outbox_oldest_age_seconds = Column(Float, nullable=False, default=0)
    outbox_retry_count = Column(Integer, nullable=False, default=0)
    outbox_dead_letter_count = Column(Integer, nullable=False, default=0)
    disk_used_percent = Column(Float, nullable=False, default=0)
    disk_free_bytes = Column(Integer, nullable=False, default=0)
    worker_last_heartbeat_at = Column(DateTime(timezone=True), nullable=True)
    worker_lag_seconds = Column(Float, nullable=False, default=0)
    transport_latency_ms = Column(Float, nullable=True)
    captured_at = Column(DateTime(timezone=True), nullable=False, default=utc_now)
    simulation_only = Column(Boolean, nullable=False, default=True)
    safe_metadata = Column(JSON, nullable=True)


class DeviceGatewayAlert(Base):
    """Tenant-scoped alert state derived from safe gateway metrics."""

    __tablename__ = "device_gateway_alerts"
    __table_args__ = (
        Index("ix_device_gateway_alerts_lab_status", "lab_id", "status", "last_seen_at"),
        Index("ix_device_gateway_alerts_gateway", "gateway_ref", "last_seen_at"),
        Index("ix_device_gateway_alerts_severity", "lab_id", "severity", "status"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    lab_id = Column(Integer, ForeignKey("labs.id", ondelete="CASCADE"), nullable=False)
    gateway_ref = Column(String(160), nullable=False)
    alert_key = Column(String(96), nullable=False)
    severity = Column(String(16), nullable=False, default="warning")
    status = Column(String(24), nullable=False, default="open")
    title = Column(String(200), nullable=False)
    summary = Column(String(500), nullable=False)
    metric_key = Column(String(80), nullable=False)
    current_value = Column(Float, nullable=True)
    threshold_value = Column(Float, nullable=True)
    first_seen_at = Column(DateTime(timezone=True), nullable=False, default=utc_now)
    last_seen_at = Column(DateTime(timezone=True), nullable=False, default=utc_now)
    acknowledged_at = Column(DateTime(timezone=True), nullable=True)
    acknowledged_by = Column(Integer, ForeignKey("lab_users.id", ondelete="SET NULL"), nullable=True)
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    correlation_id = Column(String(96), nullable=False, index=True)
    simulation_only = Column(Boolean, nullable=False, default=True)
    safe_metadata = Column(JSON, nullable=True)
