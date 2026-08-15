from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


DeviceCategory = Literal[
    "medical_measurement",
    "patient_monitor",
    "laboratory_analyzer",
    "imaging",
    "printer",
    "workstation",
    "network",
    "barcode_scanner",
    "other",
]
DeviceStatus = Literal["connected", "disconnected", "error", "maintenance", "pending"]
DeviceProtocol = Literal[
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
]
DeviceTransport = Literal["MLLP", "TCP", "Serial", "USB", "Bluetooth", "WiFi", "HTTP", "File", "None"]
ConnectorMode = Literal["simulated", "gateway_pending", "active", "disabled"]
ConnectorStatus = Literal["healthy", "degraded", "offline", "error", "maintenance", "pending"]
ProfileStatus = Literal["draft", "validated", "retired"]

_SECRET_TERMS = ("password", "secret", "token", "private_key", "privatekey", "credential", "authorization")


def _ensure_secret_free(value: Any) -> Any:
    if isinstance(value, dict):
        for key, child in value.items():
            normalized = str(key).lower().replace("-", "_")
            if any(term in normalized for term in _SECRET_TERMS):
                raise ValueError("secret-bearing configuration is not accepted by the device control plane")
            _ensure_secret_free(child)
    elif isinstance(value, list):
        for child in value:
            _ensure_secret_free(child)
    return value


class DeviceRegisterRequest(BaseModel):
    device_uid: str = Field(..., min_length=3, max_length=96, pattern=r"^[A-Za-z0-9._:-]+$")
    display_name: str = Field(..., min_length=2, max_length=200)
    category: DeviceCategory = "other"
    vendor: str | None = Field(None, max_length=120)
    model: str | None = Field(None, max_length=120)
    serial_number: str | None = Field(None, max_length=120)
    protocol: DeviceProtocol = "None"
    transport: DeviceTransport = "None"
    endpoint: str | None = Field(None, max_length=255)
    capabilities: dict[str, Any] | None = None
    printer_profile: dict[str, Any] | None = None
    maintenance_due_at: datetime | None = None
    notes: str | None = Field(None, max_length=2000)


class DeviceStatusUpdateRequest(BaseModel):
    status: DeviceStatus
    reason: str | None = Field(None, max_length=500)


class DeviceRecord(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    device_uid: str
    display_name: str
    category: str
    vendor: str | None
    model: str | None
    serial_number: str | None
    protocol: str
    transport: str
    endpoint: str | None
    status: str
    simulation_only: bool
    last_seen_at: datetime | None
    maintenance_due_at: datetime | None
    capabilities: dict[str, Any] | None
    printer_profile: dict[str, Any] | None
    notes: str | None
    created_at: datetime
    updated_at: datetime


class ConnectorRegisterRequest(BaseModel):
    connector_uid: str = Field(..., min_length=3, max_length=96, pattern=r"^[A-Za-z0-9._:-]+$")
    display_name: str = Field(..., min_length=2, max_length=200)
    device_uid: str | None = Field(None, min_length=3, max_length=96)
    protocol: DeviceProtocol
    transport: DeviceTransport
    mode: ConnectorMode = "simulated"
    contract_version: str = Field("v1", min_length=1, max_length=24, pattern=r"^[A-Za-z0-9._-]+$")
    gateway_ref: str | None = Field(None, max_length=160)
    config_safe: dict[str, Any] | None = None
    capability_manifest: dict[str, Any] | None = None
    maintenance_due_at: datetime | None = None
    enabled: bool = True

    @field_validator("config_safe", "capability_manifest")
    @classmethod
    def validate_secret_free(cls, value: dict[str, Any] | None) -> dict[str, Any] | None:
        return _ensure_secret_free(value)


class ConnectorStatusUpdateRequest(BaseModel):
    status: ConnectorStatus
    reason: str | None = Field(None, max_length=500)
    last_error: str | None = Field(None, max_length=500)


class ConnectorRecord(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    connector_uid: str
    display_name: str
    device_uid: str | None
    protocol: str
    transport: str
    mode: str
    status: str
    contract_version: str
    gateway_ref: str | None
    config_safe: dict[str, Any] | None
    capability_manifest: dict[str, Any] | None
    last_heartbeat_at: datetime | None
    last_error: str | None
    enabled: bool
    simulation_only: bool
    maintenance_due_at: datetime | None
    created_at: datetime
    updated_at: datetime


class ProtocolProfileRequest(BaseModel):
    profile_key: str = Field(..., min_length=3, max_length=120, pattern=r"^[A-Za-z0-9._:-]+$")
    protocol: DeviceProtocol
    version: str = Field("v1", min_length=1, max_length=24, pattern=r"^[A-Za-z0-9._-]+$")
    message_type: str | None = Field(None, max_length=64)
    framing: str | None = Field(None, max_length=120)
    ack_strategy: str | None = Field(None, max_length=80)
    encoding: str | None = Field("UTF-8", max_length=40)
    mapping_schema: dict[str, Any] | None = None
    validation_rules: dict[str, Any] | None = None
    simulator_key: str | None = Field(None, max_length=80)
    status: ProfileStatus = "draft"

    @field_validator("mapping_schema", "validation_rules")
    @classmethod
    def validate_profile_secret_free(cls, value: dict[str, Any] | None) -> dict[str, Any] | None:
        return _ensure_secret_free(value)


class ProtocolProfileRecord(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    profile_key: str
    protocol: str
    version: str
    message_type: str | None
    framing: str | None
    ack_strategy: str | None
    encoding: str | None
    mapping_schema: dict[str, Any] | None
    validation_rules: dict[str, Any] | None
    simulator_key: str | None
    status: str
    simulation_only: bool
    created_by: int | None
    created_at: datetime
    updated_at: datetime


class SimulatorRequest(BaseModel):
    simulator_key: str = Field(..., min_length=3, max_length=80, pattern=r"^[A-Za-z0-9._:-]+$")
    scenario: Literal["success", "degraded", "failure", "malformed"] = "success"
    message_type: str | None = Field(None, max_length=64)
    item_count: int = Field(1, ge=1, le=100)


class SimulatorDescriptor(BaseModel):
    key: str
    label: str
    protocol: str
    family: str
    contract_summary: str
    output: str
    simulation_only: bool = True


class SimulationResult(BaseModel):
    connector_uid: str
    simulator_key: str
    scenario: str
    outcome: Literal["accepted", "degraded", "rejected"]
    connector_status: str
    device_status: str | None
    event_id: int | None
    correlation_id: str
    simulation_only: bool = True
    safe_summary: str


class DeviceEventRecord(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    device_uid: str
    event_type: str
    direction: str
    severity: str
    message_type: str | None
    summary: str
    correlation_id: str | None
    safe_metadata: dict[str, Any] | None
    occurred_at: datetime


class PrinterJobRequest(BaseModel):
    device_uid: str = Field(..., min_length=3, max_length=96)
    document_type: Literal["report", "barcode_label", "specimen_label", "workstation_document"]
    printer_language: Literal["PDF", "ZPL", "IPL"] = "PDF"
    label_count: int = Field(1, ge=1, le=100)
    template_key: str | None = Field(None, max_length=120)


class PrinterJobRecord(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    device_uid: str
    document_type: str
    printer_language: str
    label_count: int
    status: str
    simulation_only: bool
    safe_metadata: dict[str, Any] | None
    error_message: str | None
    created_at: datetime
    completed_at: datetime | None


class ProtocolDescriptor(BaseModel):
    key: str
    label: str
    family: str
    transports: list[str]
    intended_categories: list[str]
    production_requirement: str
    simulation_supported: bool = True


class DeviceSummary(BaseModel):
    total: int
    connected: int
    disconnected: int
    error: int
    maintenance: int
    pending: int
    simulation_only: int
    by_category: dict[str, int]
    recent_events: int


class DeviceListResponse(BaseModel):
    total: int
    devices: list[DeviceRecord]


class ConnectorListResponse(BaseModel):
    total: int
    connectors: list[ConnectorRecord]


class ProtocolProfileListResponse(BaseModel):
    total: int
    profiles: list[ProtocolProfileRecord]


class DeviceEventListResponse(BaseModel):
    total: int
    events: list[DeviceEventRecord]


class PrinterJobListResponse(BaseModel):
    total: int
    jobs: list[PrinterJobRecord]


GatewayStatus = Literal["healthy", "degraded", "offline", "error", "maintenance", "pending", "revoked"]
GatewayMode = Literal["simulated", "local_pending"]
GatewayAlertSeverity = Literal["info", "warning", "critical"]
GatewayAlertStatus = Literal["open", "acknowledged", "resolved"]
DeviceOutboxStatus = Literal["pending", "processing", "retry", "delivered", "dead_letter"]


class GatewayRegistrationRequest(BaseModel):
    gateway_ref: str = Field(..., min_length=3, max_length=160, pattern=r"^[A-Za-z0-9._:/-]+$")
    display_name: str = Field(..., min_length=2, max_length=200)
    mode: GatewayMode = "simulated"
    gateway_version: str | None = Field(None, max_length=48)
    contract_version: str = Field("v1", min_length=1, max_length=24, pattern=r"^[A-Za-z0-9._-]+$")
    capabilities_safe: dict[str, Any] | None = None
    enabled: bool = True

    @field_validator("capabilities_safe")
    @classmethod
    def validate_capabilities_secret_free(cls, value: dict[str, Any] | None) -> dict[str, Any] | None:
        return _ensure_secret_free(value)


class GatewayMetricIngestRequest(BaseModel):
    gateway_ref: str = Field(..., min_length=3, max_length=160, pattern=r"^[A-Za-z0-9._:/-]+$")
    gateway_status: GatewayStatus = "healthy"
    gateway_version: str | None = Field(None, max_length=48)
    outbox_pending_count: int = Field(0, ge=0, le=10_000_000)
    outbox_oldest_age_seconds: float = Field(0, ge=0, le=31_536_000)
    outbox_retry_count: int = Field(0, ge=0, le=10_000_000)
    outbox_dead_letter_count: int = Field(0, ge=0, le=10_000_000)
    disk_used_percent: float = Field(0, ge=0, le=100)
    disk_free_bytes: int = Field(0, ge=0)
    worker_last_heartbeat_at: datetime | None = None
    worker_lag_seconds: float = Field(0, ge=0, le=31_536_000)
    transport_latency_ms: float | None = Field(None, ge=0, le=86_400_000)
    captured_at: datetime | None = None
    simulation_only: bool = True
    safe_metadata: dict[str, Any] | None = None

    @field_validator("safe_metadata")
    @classmethod
    def validate_metrics_secret_free(cls, value: dict[str, Any] | None) -> dict[str, Any] | None:
        return _ensure_secret_free(value)


class GatewayHeartbeatRequest(GatewayMetricIngestRequest):
    """A signed gateway contract will replace this simulation-only request later."""


class GatewayRecord(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    gateway_ref: str
    display_name: str
    mode: str
    status: str
    gateway_version: str | None
    contract_version: str
    capabilities_safe: dict[str, Any] | None
    last_heartbeat_at: datetime | None
    last_error: str | None
    enabled: bool
    simulation_only: bool
    registered_at: datetime
    updated_at: datetime


class DeviceOutboxRecord(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    gateway_ref: str | None
    event_type: str
    aggregate_type: str
    aggregate_id: int | None
    idempotency_key: str
    correlation_id: str
    payload_safe: dict[str, Any]
    status: str
    attempts: int
    max_attempts: int
    last_error: str | None
    next_attempt_at: datetime
    locked_at: datetime | None
    delivered_at: datetime | None
    created_at: datetime
    updated_at: datetime
    simulation_only: bool


class DeviceOutboxSummary(BaseModel):
    pending_count: int
    processing_count: int
    retry_count: int
    delivered_count: int
    dead_letter_count: int
    oldest_age_seconds: float


class GatewayMetricRecord(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    gateway_ref: str
    gateway_status: str
    gateway_version: str | None
    outbox_pending_count: int
    outbox_oldest_age_seconds: float
    outbox_retry_count: int
    outbox_dead_letter_count: int
    disk_used_percent: float
    disk_free_bytes: int
    worker_last_heartbeat_at: datetime | None
    worker_lag_seconds: float
    transport_latency_ms: float | None
    captured_at: datetime
    simulation_only: bool
    safe_metadata: dict[str, Any] | None


class GatewayAlertRecord(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    gateway_ref: str
    alert_key: str
    severity: str
    status: str
    title: str
    summary: str
    metric_key: str
    current_value: float | None
    threshold_value: float | None
    first_seen_at: datetime
    last_seen_at: datetime
    acknowledged_at: datetime | None
    acknowledged_by: int | None
    resolved_at: datetime | None
    correlation_id: str
    simulation_only: bool
    safe_metadata: dict[str, Any] | None


class DeviceOutboxProcessResponse(BaseModel):
    processed: int
    recovered: int = 0
    delivered: int
    retried: int
    dead_letter: int
    simulation_only: bool = True


class GatewayListResponse(BaseModel):
    total: int
    gateways: list[GatewayRecord]


class DeviceOutboxListResponse(BaseModel):
    total: int
    messages: list[DeviceOutboxRecord]


class GatewayAlertAcknowledgeRequest(BaseModel):
    note: str | None = Field(None, max_length=500)


class GatewayMonitoringSnapshot(BaseModel):
    gateway_count: int
    healthy_gateway_count: int
    degraded_gateway_count: int
    offline_gateway_count: int
    latest_metric: GatewayMetricRecord | None
    open_alert_count: int
    critical_alert_count: int
    alerts: list[GatewayAlertRecord]
    thresholds: dict[str, float]
    simulation_only: bool
    gateways: list[GatewayRecord] = Field(default_factory=list)
    outbox: DeviceOutboxSummary | None = None


class GatewayMonitoringAlertListResponse(BaseModel):
    total: int
    alerts: list[GatewayAlertRecord]
