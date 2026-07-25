from datetime import datetime

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    Date,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)

from app._compat import UTC

from ..base import GovernanceBaseEntity
from ..enums import EQAResult, EquipmentStatus, LabType, QCStatus


class LaboratoryRegistry(GovernanceBaseEntity):
    __tablename__ = "gov_laboratory_registry"

    id = Column(Integer, primary_key=True, autoincrement=True)
    lab_code = Column(String(50), unique=True, nullable=False, index=True)
    name_ar = Column(String(300), nullable=False)
    name_en = Column(String(300), nullable=True)
    lab_type = Column(Enum(LabType), nullable=False, index=True)
    organization_node_id = Column(
        Integer, ForeignKey("gov_hierarchy_nodes.id"), nullable=True, index=True
    )
    license_number = Column(String(100), unique=True, nullable=True, index=True)
    director_name = Column(String(200), nullable=True)
    address = Column(String(500), nullable=True)
    governorate = Column(String(100), nullable=True, index=True)
    district = Column(String(100), nullable=True)
    phone = Column(String(20), nullable=True)
    email = Column(String(200), nullable=True)
    is_active = Column(Boolean, default=True, index=True)
    accreditation_body = Column(String(200), nullable=True)
    accreditation_expiry = Column(Date, nullable=True)
    nhop_lab_code = Column(String(50), nullable=True)
    external_lab_id = Column(String(100), nullable=True)
    metadata_json = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )


class EquipmentRegistry(GovernanceBaseEntity):
    __tablename__ = "gov_equipment_registry"

    id = Column(Integer, primary_key=True, autoincrement=True)
    lab_id = Column(Integer, ForeignKey("gov_laboratory_registry.id"), nullable=False, index=True)
    equipment_code = Column(String(50), unique=True, nullable=False, index=True)
    name_ar = Column(String(300), nullable=False)
    name_en = Column(String(300), nullable=True)
    manufacturer = Column(String(200), nullable=True)
    model = Column(String(200), nullable=True)
    serial_number = Column(String(200), nullable=True)
    category = Column(String(100), nullable=False, index=True)
    status = Column(
        Enum(EquipmentStatus), nullable=False, default=EquipmentStatus.OPERATIONAL, index=True
    )
    installation_date = Column(Date, nullable=True)
    last_maintenance_date = Column(Date, nullable=True)
    next_maintenance_date = Column(Date, nullable=True)
    warranty_expiry = Column(Date, nullable=True)
    location = Column(String(200), nullable=True)
    metadata_json = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )


class AnalyzerRegistry(GovernanceBaseEntity):
    __tablename__ = "gov_analyzer_registry"

    id = Column(Integer, primary_key=True, autoincrement=True)
    lab_id = Column(Integer, ForeignKey("gov_laboratory_registry.id"), nullable=False, index=True)
    analyzer_code = Column(String(50), unique=True, nullable=False, index=True)
    name_ar = Column(String(300), nullable=False)
    name_en = Column(String(300), nullable=True)
    manufacturer = Column(String(200), nullable=True)
    model = Column(String(200), nullable=True)
    serial_number = Column(String(200), nullable=True, index=True)
    analyzer_type = Column(String(100), nullable=False)
    test_menu = Column(JSON, nullable=True)
    status = Column(String(20), default="operational", index=True)
    software_version = Column(String(50), nullable=True)
    interface_type = Column(String(50), nullable=True)
    installation_date = Column(Date, nullable=True)
    last_qc_date = Column(Date, nullable=True)
    next_calibration_date = Column(Date, nullable=True)
    metadata_json = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )


class MaintenanceRecord(GovernanceBaseEntity):
    __tablename__ = "gov_maintenance_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    equipment_id = Column(
        Integer, ForeignKey("gov_equipment_registry.id"), nullable=False, index=True
    )
    maintenance_type = Column(String(50), nullable=False)
    description = Column(Text, nullable=True)
    performed_by = Column(String(200), nullable=True)
    performed_date = Column(Date, nullable=False)
    next_maintenance_date = Column(Date, nullable=True)
    cost = Column(Float, nullable=True)
    parts_replaced = Column(Text, nullable=True)
    status = Column(String(20), default="completed")
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))


class CalibrationRecord(GovernanceBaseEntity):
    __tablename__ = "gov_calibration_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    analyzer_id = Column(
        Integer, ForeignKey("gov_analyzer_registry.id"), nullable=False, index=True
    )
    calibration_type = Column(String(100), nullable=False)
    performed_by = Column(String(200), nullable=True)
    performed_date = Column(Date, nullable=False)
    next_calibration_date = Column(Date, nullable=True)
    calibrator_lot = Column(String(100), nullable=True)
    results = Column(JSON, nullable=True)
    passed = Column(Boolean, nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))


class QCModRecord(GovernanceBaseEntity):
    __tablename__ = "gov_qc_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    lab_id = Column(Integer, ForeignKey("gov_laboratory_registry.id"), nullable=False, index=True)
    analyzer_id = Column(Integer, ForeignKey("gov_analyzer_registry.id"), nullable=True)
    test_code = Column(String(50), nullable=False, index=True)
    control_level = Column(String(50), nullable=False)
    control_lot = Column(String(100), nullable=True)
    result_value = Column(Float, nullable=False)
    mean = Column(Float, nullable=True)
    sd = Column(Float, nullable=True)
    status = Column(Enum(QCStatus), nullable=False, default=QCStatus.IN_CONTROL)
    westgard_rules_violated = Column(JSON, nullable=True)
    performed_by = Column(String(200), nullable=True)
    performed_date = Column(DateTime(timezone=True), nullable=False)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))


class EQARecord(GovernanceBaseEntity):
    __tablename__ = "gov_eqa_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    lab_id = Column(Integer, ForeignKey("gov_laboratory_registry.id"), nullable=False, index=True)
    test_code = Column(String(50), nullable=False, index=True)
    scheme_name = Column(String(200), nullable=False)
    round_number = Column(String(50), nullable=False)
    sample_id = Column(String(100), nullable=True)
    submitted_result = Column(Float, nullable=True)
    target_value = Column(Float, nullable=True)
    acceptable_range = Column(String(100), nullable=True)
    z_score = Column(Float, nullable=True)
    deviation_percent = Column(Float, nullable=True)
    result = Column(Enum(EQAResult), nullable=True)
    submitted_by = Column(String(200), nullable=True)
    submitted_date = Column(Date, nullable=True)
    reviewed_by = Column(String(200), nullable=True)
    reviewed_date = Column(Date, nullable=True)
    corrective_action = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))


class ReagentInventory(GovernanceBaseEntity):
    __tablename__ = "gov_reagent_inventory"

    id = Column(Integer, primary_key=True, autoincrement=True)
    lab_id = Column(Integer, ForeignKey("gov_laboratory_registry.id"), nullable=False, index=True)
    reagent_code = Column(String(50), nullable=False, index=True)
    reagent_name_ar = Column(String(300), nullable=False)
    reagent_name_en = Column(String(300), nullable=True)
    lot_number = Column(String(100), nullable=True, index=True)
    manufacturer = Column(String(200), nullable=True)
    quantity = Column(Float, nullable=False)
    unit = Column(String(20), nullable=False)
    received_date = Column(Date, nullable=True)
    expiry_date = Column(Date, nullable=True)
    storage_condition = Column(String(200), nullable=True)
    minimum_stock_level = Column(Float, nullable=True)
    batch_number = Column(String(100), nullable=True)
    metadata_json = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )


class NationalTestDefinition(GovernanceBaseEntity):
    __tablename__ = "gov_national_tests"

    id = Column(Integer, primary_key=True, autoincrement=True)
    test_code = Column(String(50), unique=True, nullable=False, index=True)
    name_ar = Column(String(300), nullable=False)
    name_en = Column(String(300), nullable=True)
    category = Column(String(100), nullable=False, index=True)
    department = Column(String(100), nullable=True)
    specimen_type = Column(String(50), nullable=True)
    loinc_code = Column(String(20), nullable=True, index=True)
    cpt_code = Column(String(20), nullable=True)
    is_active = Column(Boolean, default=True, index=True)
    is_national_essential = Column(Boolean, default=False)
    tat_target_minutes = Column(Integer, nullable=True)
    reference_range_source = Column(String(200), nullable=True)
    critical_low = Column(String(50), nullable=True)
    critical_high = Column(String(50), nullable=True)
    metadata_json = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )


class NationalPanelDefinition(GovernanceBaseEntity):
    __tablename__ = "gov_national_panels"

    id = Column(Integer, primary_key=True, autoincrement=True)
    panel_code = Column(String(50), unique=True, nullable=False, index=True)
    name_ar = Column(String(300), nullable=False)
    name_en = Column(String(300), nullable=True)
    tests = Column(JSON, nullable=False)
    category = Column(String(100), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )


class NationalReferenceLab(GovernanceBaseEntity):
    __tablename__ = "gov_national_reference_labs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    lab_id = Column(Integer, ForeignKey("gov_laboratory_registry.id"), nullable=False, index=True)
    reference_domain = Column(String(200), nullable=False, index=True)
    is_national = Column(Boolean, default=False)
    is_regional = Column(Boolean, default=False)
    designation_date = Column(Date, nullable=False)
    designation_order = Column(String(200), nullable=True)
    accredited_standards = Column(JSON, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )
