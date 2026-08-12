from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from app._compat import UTC
from app.biomedical.domain.enums import (
    AssetLifecycleStage,
    CalibrationStatus,
    DeviceCategory,
    DeviceStatus,
    IncidentSeverity,
    MaintenancePriority,
    MaintenanceType,
    RecallClass,
    RiskClass,
    SafetyInspectionResult,
    VerificationResult,
    WarrantyStatus,
    WorkOrderStatus,
)


@dataclass
class MedicalDevice:
    id: str
    device_name: str = ""
    model: str = ""
    manufacturer: str = ""
    serial_number: str = ""
    udi_di: str = ""
    udi_pi: str = ""
    udi_full: str = ""
    asset_tag: str = ""
    category: DeviceCategory = DeviceCategory.OTHER
    risk_class: RiskClass = RiskClass.CLASS_I
    status: DeviceStatus = DeviceStatus.AVAILABLE
    location_facility_id: str = ""
    location_department: str = ""
    location_room: str = ""
    owning_department: str = ""
    responsible_person: str = ""
    acquisition_date: datetime | None = None
    installation_date: datetime | None = None
    commissioning_date: datetime | None = None
    warranty_start: datetime | None = None
    warranty_end: datetime | None = None
    warranty_status: WarrantyStatus = WarrantyStatus.ACTIVE
    expected_lifetime_years: int = 10
    purchase_cost: float | None = None
    current_value: float | None = None
    requires_calibration: bool = False
    calibration_frequency_days: int = 365
    last_calibration_date: datetime | None = None
    next_calibration_due: datetime | None = None
    requires_pm: bool = True
    pm_frequency_days: int = 180
    last_pm_date: datetime | None = None
    next_pm_due: datetime | None = None
    lifecycle_stage: AssetLifecycleStage = AssetLifecycleStage.OPERATIONAL
    vendor_id: str = ""
    vendor_name: str = ""
    contract_id: str = ""
    power_rating: str = ""
    dimensions: str = ""
    weight_kg: float | None = None
    software_version: str = ""
    firmware_version: str = ""
    network_address: str = ""
    notes: str = ""
    created_by: str = ""
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class WorkOrder:
    id: str
    device_id: str = ""
    device_name: str = ""
    work_order_number: str = ""
    maintenance_type: MaintenanceType = MaintenanceType.CORRECTIVE
    priority: MaintenancePriority = MaintenancePriority.MEDIUM
    status: WorkOrderStatus = WorkOrderStatus.PENDING
    title: str = ""
    description: str = ""
    reported_by: str = ""
    reported_date: datetime = field(default_factory=lambda: datetime.now(UTC))
    assigned_to: str = ""
    assigned_date: datetime | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    verified_by: str = ""
    verified_at: datetime | None = None
    downtime_hours: float | None = None
    labor_hours: float | None = None
    problem_found: str = ""
    action_taken: str = ""
    parts_used: list[dict[str, Any]] = field(default_factory=list)
    cost_parts: float | None = None
    cost_labor: float | None = None
    cost_total: float | None = None
    result: str = ""
    result_verified: bool = False
    notes: str = ""
    created_by: str = ""
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class CalibrationRecord:
    id: str
    device_id: str = ""
    device_name: str = ""
    calibration_number: str = ""
    calibration_type: str = "internal"
    status: CalibrationStatus = CalibrationStatus.PENDING
    calibration_date: datetime = field(default_factory=lambda: datetime.now(UTC))
    calibrated_by: str = ""
    due_date: datetime | None = None
    standard_used: str = ""
    standard_id: str = ""
    standard_traceability: str = ""
    ambient_temperature: float | None = None
    ambient_humidity: float | None = None
    results: list[dict[str, Any]] = field(default_factory=list)
    deviations: list[dict[str, Any]] = field(default_factory=list)
    overall_result: str = "pending"
    passed: bool = False
    verified_by: str = ""
    verified_at: datetime | None = None
    notes: str = ""
    created_by: str = ""
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class SafetyInspection:
    id: str
    device_id: str = ""
    device_name: str = ""
    inspection_date: datetime = field(default_factory=lambda: datetime.now(UTC))
    inspected_by: str = ""
    inspection_type: str = "routine"
    electrical_safety_pass: bool = False
    earth_leakage: float | None = None
    ground_resistance: float | None = None
    insulation_resistance: float | None = None
    functional_test_pass: bool = False
    visual_inspection_pass: bool = False
    overall_result: SafetyInspectionResult = SafetyInspectionResult.FAILED
    findings: str = ""
    recommendations: str = ""
    next_inspection_due: datetime | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class PerformanceVerification:
    id: str
    device_id: str = ""
    device_name: str = ""
    verification_date: datetime = field(default_factory=lambda: datetime.now(UTC))
    verified_by: str = ""
    parameters: dict[str, Any] = field(default_factory=dict)
    results: dict[str, Any] = field(default_factory=dict)
    overall_result: VerificationResult = VerificationResult.NOT_PERFORMED
    deviations: list[str] = field(default_factory=list)
    notes: str = ""


@dataclass
class DeviceIncident:
    id: str
    device_id: str = ""
    device_name: str = ""
    incident_date: datetime = field(default_factory=lambda: datetime.now(UTC))
    reported_by: str = ""
    incident_type: str = ""
    severity: IncidentSeverity = IncidentSeverity.MINOR
    description: str = ""
    patient_involved: bool = False
    patient_impact: str = ""
    operator_involved: bool = False
    operator_impact: str = ""
    immediate_action: str = ""
    root_cause: str = ""
    corrective_action: str = ""
    fda_reportable: bool = False
    manufacturer_notified: bool = False
    manufacturer_response: str = ""
    closed_at: datetime | None = None
    status: str = "open"
    created_by: str = ""
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class DeviceRecall:
    id: str
    device_id: str = ""
    device_name: str = ""
    model: str = ""
    manufacturer: str = ""
    recall_date: datetime = field(default_factory=lambda: datetime.now(UTC))
    recall_class: RecallClass = RecallClass.CLASS_II
    recall_reason: str = ""
    recall_number: str = ""
    fda_recall_id: str = ""
    affected_serial_numbers: list[str] = field(default_factory=list)
    corrective_action: str = ""
    status: str = "open"
    completed_at: datetime | None = None
    notes: str = ""


@dataclass
class Technician:
    id: str
    user_id: str = ""
    full_name: str = ""
    specialization: str = ""
    certifications: list[str] = field(default_factory=list)
    phone: str = ""
    email: str = ""
    facility_id: str = ""
    is_available: bool = True
    max_work_orders: int = 5
    skills: list[str] = field(default_factory=list)
    is_active: bool = True
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class SparePart:
    id: str
    part_number: str = ""
    part_name: str = ""
    manufacturer: str = ""
    compatible_models: list[str] = field(default_factory=list)
    quantity_in_stock: int = 0
    minimum_stock: int = 1
    unit_cost: float | None = None
    storage_location: str = ""
    supplier_id: str = ""
    lead_time_days: int = 30
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class Vendor:
    id: str
    vendor_name: str = ""
    vendor_type: str = "manufacturer"
    contact_person: str = ""
    phone: str = ""
    email: str = ""
    address: str = ""
    website: str = ""
    service_coverage: str = ""
    is_approved: bool = True
    rating: float | None = None
    notes: str = ""
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class ServiceContract:
    id: str
    device_id: str = ""
    vendor_id: str = ""
    contract_number: str = ""
    contract_type: str = "full_service"
    start_date: datetime | None = None
    end_date: datetime | None = None
    coverage_details: str = ""
    response_time_hours: int = 24
    annual_cost: float | None = None
    includes_parts: bool = True
    includes_labor: bool = True
    includes_calibration: bool = False
    is_active: bool = True
    notes: str = ""
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class DeviceMaintenanceSchedule:
    id: str
    device_id: str = ""
    device_name: str = ""
    maintenance_type: MaintenanceType = MaintenanceType.PREVENTIVE
    frequency_days: int = 180
    last_due_date: datetime | None = None
    next_due_date: datetime | None = None
    estimated_duration_minutes: int = 60
    required_skills: list[str] = field(default_factory=list)
    checklist_items: list[dict[str, Any]] = field(default_factory=list)
    is_active: bool = True
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
