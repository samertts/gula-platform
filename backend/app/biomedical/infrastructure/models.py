from __future__ import annotations

from sqlalchemy import JSON, Boolean, Column, DateTime, Float, ForeignKey, Integer, String, Text

from app.national.base import TenantAuditEntity, TenantEntity


class MedicalDeviceModel(TenantAuditEntity):
    __tablename__ = "biomed_devices"

    device_name = Column(String(200), nullable=False)
    model = Column(String(200), nullable=True)
    manufacturer = Column(String(200), nullable=True)
    serial_number = Column(String(200), nullable=True, unique=True)
    udi_di = Column(String(100), nullable=True, index=True)
    udi_pi = Column(String(100), nullable=True)
    udi_full = Column(String(200), nullable=True)
    asset_tag = Column(String(100), nullable=True, unique=True)
    category = Column(String(50), default="other")
    risk_class = Column(String(50), default="class_i")
    status = Column(String(50), default="available")
    location_facility_id = Column(String(100), nullable=True)
    location_department = Column(String(200), nullable=True)
    location_room = Column(String(200), nullable=True)
    owning_department = Column(String(200), nullable=True)
    responsible_person = Column(String(200), nullable=True)
    acquisition_date = Column(DateTime(timezone=True), nullable=True)
    installation_date = Column(DateTime(timezone=True), nullable=True)
    commissioning_date = Column(DateTime(timezone=True), nullable=True)
    warranty_start = Column(DateTime(timezone=True), nullable=True)
    warranty_end = Column(DateTime(timezone=True), nullable=True)
    warranty_status = Column(String(50), default="active")
    expected_lifetime_years = Column(Integer, default=10)
    purchase_cost = Column(Float, nullable=True)
    current_value = Column(Float, nullable=True)
    requires_calibration = Column(Boolean, default=False)
    calibration_frequency_days = Column(Integer, default=365)
    last_calibration_date = Column(DateTime(timezone=True), nullable=True)
    next_calibration_due = Column(DateTime(timezone=True), nullable=True)
    requires_pm = Column(Boolean, default=True)
    pm_frequency_days = Column(Integer, default=180)
    last_pm_date = Column(DateTime(timezone=True), nullable=True)
    next_pm_due = Column(DateTime(timezone=True), nullable=True)
    lifecycle_stage = Column(String(50), default="operational")
    vendor_id = Column(String(100), nullable=True)
    vendor_name = Column(String(200), nullable=True)
    contract_id = Column(String(100), nullable=True)
    power_rating = Column(String(100), nullable=True)
    dimensions = Column(String(100), nullable=True)
    weight_kg = Column(Float, nullable=True)
    software_version = Column(String(100), nullable=True)
    firmware_version = Column(String(100), nullable=True)
    network_address = Column(String(100), nullable=True)
    notes = Column(Text, nullable=True)


class WorkOrderModel(TenantAuditEntity):
    __tablename__ = "biomed_work_orders"

    device_id = Column(String(100), ForeignKey("biomed_devices.id"), nullable=False, index=True)
    device_name = Column(String(200), nullable=True)
    work_order_number = Column(String(100), nullable=True, unique=True)
    maintenance_type = Column(String(50), default="corrective")
    priority = Column(String(50), default="medium")
    status = Column(String(50), default="pending")
    title = Column(String(200), nullable=True)
    description = Column(Text, nullable=True)
    reported_by = Column(String(200), nullable=True)
    reported_date = Column(DateTime(timezone=True), nullable=False)
    assigned_to = Column(String(200), nullable=True)
    assigned_date = Column(DateTime(timezone=True), nullable=True)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    verified_by = Column(String(200), nullable=True)
    verified_at = Column(DateTime(timezone=True), nullable=True)
    downtime_hours = Column(Float, nullable=True)
    labor_hours = Column(Float, nullable=True)
    problem_found = Column(Text, nullable=True)
    action_taken = Column(Text, nullable=True)
    parts_used = Column(JSON, nullable=True)
    cost_parts = Column(Float, nullable=True)
    cost_labor = Column(Float, nullable=True)
    cost_total = Column(Float, nullable=True)
    result = Column(Text, nullable=True)
    result_verified = Column(Boolean, default=False)
    notes = Column(Text, nullable=True)


class CalibrationRecordModel(TenantAuditEntity):
    __tablename__ = "biomed_calibrations"

    device_id = Column(String(100), ForeignKey("biomed_devices.id"), nullable=False, index=True)
    device_name = Column(String(200), nullable=True)
    calibration_number = Column(String(100), nullable=True, unique=True)
    calibration_type = Column(String(50), default="internal")
    status = Column(String(50), default="pending")
    calibration_date = Column(DateTime(timezone=True), nullable=False)
    calibrated_by = Column(String(200), nullable=True)
    due_date = Column(DateTime(timezone=True), nullable=True)
    standard_used = Column(String(200), nullable=True)
    standard_id = Column(String(100), nullable=True)
    standard_traceability = Column(String(200), nullable=True)
    ambient_temperature = Column(Float, nullable=True)
    ambient_humidity = Column(Float, nullable=True)
    results = Column(JSON, nullable=True)
    deviations = Column(JSON, nullable=True)
    overall_result = Column(String(50), default="pending")
    passed = Column(Boolean, default=False)
    verified_by = Column(String(200), nullable=True)
    verified_at = Column(DateTime(timezone=True), nullable=True)
    notes = Column(Text, nullable=True)


class SafetyInspectionModel(TenantAuditEntity):
    __tablename__ = "biomed_safety_inspections"

    device_id = Column(String(100), ForeignKey("biomed_devices.id"), nullable=False, index=True)
    device_name = Column(String(200), nullable=True)
    inspection_date = Column(DateTime(timezone=True), nullable=False)
    inspected_by = Column(String(200), nullable=True)
    inspection_type = Column(String(50), default="routine")
    electrical_safety_pass = Column(Boolean, default=False)
    earth_leakage = Column(Float, nullable=True)
    ground_resistance = Column(Float, nullable=True)
    insulation_resistance = Column(Float, nullable=True)
    functional_test_pass = Column(Boolean, default=False)
    visual_inspection_pass = Column(Boolean, default=False)
    overall_result = Column(String(50), default="failed")
    findings = Column(Text, nullable=True)
    recommendations = Column(Text, nullable=True)
    next_inspection_due = Column(DateTime(timezone=True), nullable=True)


class PerformanceVerificationModel(TenantAuditEntity):
    __tablename__ = "biomed_performance_verifications"

    device_id = Column(String(100), ForeignKey("biomed_devices.id"), nullable=False, index=True)
    device_name = Column(String(200), nullable=True)
    verification_date = Column(DateTime(timezone=True), nullable=False)
    verified_by = Column(String(200), nullable=True)
    parameters = Column(JSON, nullable=True)
    results = Column(JSON, nullable=True)
    overall_result = Column(String(50), default="not_performed")
    deviations = Column(JSON, nullable=True)
    notes = Column(Text, nullable=True)


class DeviceIncidentModel(TenantAuditEntity):
    __tablename__ = "biomed_incidents"

    device_id = Column(String(100), ForeignKey("biomed_devices.id"), nullable=False, index=True)
    device_name = Column(String(200), nullable=True)
    incident_date = Column(DateTime(timezone=True), nullable=False)
    reported_by = Column(String(200), nullable=True)
    incident_type = Column(String(100), nullable=True)
    severity = Column(String(50), default="minor")
    description = Column(Text, nullable=True)
    patient_involved = Column(Boolean, default=False)
    patient_impact = Column(Text, nullable=True)
    operator_involved = Column(Boolean, default=False)
    operator_impact = Column(Text, nullable=True)
    immediate_action = Column(Text, nullable=True)
    root_cause = Column(Text, nullable=True)
    corrective_action = Column(Text, nullable=True)
    fda_reportable = Column(Boolean, default=False)
    manufacturer_notified = Column(Boolean, default=False)
    manufacturer_response = Column(Text, nullable=True)
    closed_at = Column(DateTime(timezone=True), nullable=True)
    status = Column(String(50), default="open")


class DeviceRecallModel(TenantAuditEntity):
    __tablename__ = "biomed_recalls"

    device_id = Column(String(100), ForeignKey("biomed_devices.id"), nullable=False, index=True)
    device_name = Column(String(200), nullable=True)
    model = Column(String(200), nullable=True)
    manufacturer = Column(String(200), nullable=True)
    recall_date = Column(DateTime(timezone=True), nullable=False)
    recall_class = Column(String(50), default="class_ii")
    recall_reason = Column(Text, nullable=True)
    recall_number = Column(String(100), nullable=True)
    fda_recall_id = Column(String(100), nullable=True)
    affected_serial_numbers = Column(JSON, nullable=True)
    corrective_action = Column(Text, nullable=True)
    status = Column(String(50), default="open")
    completed_at = Column(DateTime(timezone=True), nullable=True)
    notes = Column(Text, nullable=True)


class TechnicianModel(TenantEntity):
    __tablename__ = "biomed_technicians"

    user_id = Column(String(100), nullable=True)
    full_name = Column(String(200), nullable=False)
    specialization = Column(String(200), nullable=True)
    certifications = Column(JSON, nullable=True)
    phone = Column(String(50), nullable=True)
    email = Column(String(100), nullable=True)
    facility_id = Column(String(100), nullable=True)
    is_available = Column(Boolean, default=True)
    max_work_orders = Column(Integer, default=5)
    skills = Column(JSON, nullable=True)
    is_active = Column(Boolean, default=True)


class SparePartModel(TenantEntity):
    __tablename__ = "biomed_spare_parts"

    part_number = Column(String(100), nullable=True, index=True)
    part_name = Column(String(200), nullable=False)
    manufacturer = Column(String(200), nullable=True)
    compatible_models = Column(JSON, nullable=True)
    quantity_in_stock = Column(Integer, default=0)
    minimum_stock = Column(Integer, default=1)
    unit_cost = Column(Float, nullable=True)
    storage_location = Column(String(200), nullable=True)
    supplier_id = Column(String(100), nullable=True)
    lead_time_days = Column(Integer, default=30)


class VendorModel(TenantEntity):
    __tablename__ = "biomed_vendors"

    vendor_name = Column(String(200), nullable=False)
    vendor_type = Column(String(50), default="manufacturer")
    contact_person = Column(String(200), nullable=True)
    phone = Column(String(50), nullable=True)
    email = Column(String(100), nullable=True)
    address = Column(Text, nullable=True)
    website = Column(String(200), nullable=True)
    service_coverage = Column(String(200), nullable=True)
    is_approved = Column(Boolean, default=True)
    rating = Column(Float, nullable=True)
    notes = Column(Text, nullable=True)


class ServiceContractModel(TenantAuditEntity):
    __tablename__ = "biomed_service_contracts"

    device_id = Column(String(100), ForeignKey("biomed_devices.id"), nullable=True)
    vendor_id = Column(String(100), nullable=True)
    contract_number = Column(String(100), nullable=True, unique=True)
    contract_type = Column(String(50), default="full_service")
    start_date = Column(DateTime(timezone=True), nullable=True)
    end_date = Column(DateTime(timezone=True), nullable=True)
    coverage_details = Column(Text, nullable=True)
    response_time_hours = Column(Integer, default=24)
    annual_cost = Column(Float, nullable=True)
    includes_parts = Column(Boolean, default=True)
    includes_labor = Column(Boolean, default=True)
    includes_calibration = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    notes = Column(Text, nullable=True)


class MaintenanceScheduleModel(TenantEntity):
    __tablename__ = "biomed_maintenance_schedules"

    device_id = Column(String(100), ForeignKey("biomed_devices.id"), nullable=False)
    device_name = Column(String(200), nullable=True)
    maintenance_type = Column(String(50), default="preventive")
    frequency_days = Column(Integer, default=180)
    last_due_date = Column(DateTime(timezone=True), nullable=True)
    next_due_date = Column(DateTime(timezone=True), nullable=True)
    estimated_duration_minutes = Column(Integer, default=60)
    required_skills = Column(JSON, nullable=True)
    checklist_items = Column(JSON, nullable=True)
    is_active = Column(Boolean, default=True)
