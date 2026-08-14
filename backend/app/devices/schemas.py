from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


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


class DeviceEventListResponse(BaseModel):
    total: int
    events: list[DeviceEventRecord]


class PrinterJobListResponse(BaseModel):
    total: int
    jobs: list[PrinterJobRecord]
