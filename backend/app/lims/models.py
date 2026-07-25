"""National LIMS Domain Models — Canonical Laboratory Entities.

All LIMS domain models live here as a single bounded context.
Foundation models (Lab, LabOrder, LabResult, Patient, etc.) remain
untouched in app.models.  Governance laboratory models (in
app.governance.models.laboratory) also remain frozen.

Every entity supports:
  - Audit (created_by / updated_by)
  - Versioning (version column)
  - Soft Delete (is_deleted / deleted_at)
  - Optimistic Lock (version column — increment on write)
  - Tenant Isolation (lab_id)
  - Offline Sync (sync_id ULID)
  - Event emission (via outbox pattern)
  - FHIR Mapping (fhir_id / fhir_resource_type)
  - ABAC / RBAC (via lab_id + existing security layer)
"""

from __future__ import annotations

import uuid as _uuid
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
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from app._compat import UTC
from app.database import Base

# ── Reusable enums (living in the LIMS bounded context) ────────────────────


class SpecimenType(str, Enum):
    WHOLE_BLOOD = "whole_blood"
    SERUM = "serum"
    PLASMA = "plasma"
    URINE = "urine"
    STOOL = "stool"
    CSF = "csf"
    SPUTUM = "sputum"
    SWAB = "swab"
    TISSUE = "tissue"
    BONE_MARROW = "bone_marrow"
    AMNIOTIC = "amniotic"
    PLEURAL = "pleural"
    PERICARDIAL = "pericardial"
    PERITONEAL = "peritoneal"
    SYNOVIAL = "synovial"
    SALIVA = "saliva"
    HAIR = "hair"
    NAIL = "nail"
    OTHER = "other"


class SpecimenStatus(str, Enum):
    ORDERED = "ordered"
    REGISTERED = "registered"
    COLLECTED = "collected"
    TRANSPORTING = "transporting"
    RECEIVED = "received"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    ALIQUOTED = "aliquoted"
    PROCESSING = "processing"
    ANALYZING = "analyzing"
    ANALYZED = "analyzed"
    VERIFIED = "verified"
    VALIDATED = "validated"
    RELEASED = "released"
    ARCHIVED = "archived"
    DISPOSED = "disposed"


class OrderStatus(str, Enum):
    PENDING = "pending"
    ACCESSIONED = "accessioned"
    COLLECTING = "collecting"
    COLLECTED = "collected"
    IN_TRANSPORT = "in_transport"
    RECEIVED = "received"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    VALIDATED = "validated"
    RELEASED = "released"
    CANCELLED = "cancelled"
    CORRECTED = "corrected"


class AnalyzerStatus(str, Enum):
    ONLINE = "online"
    OFFLINE = "offline"
    MAINTENANCE = "maintenance"
    CALIBRATING = "calibrating"
    QC_FAILED = "qc_failed"
    ERROR = "error"
    DISABLED = "disabled"


class QCStatus(str, Enum):
    IN_CONTROL = "in_control"
    WARNING = "warning"
    OUT_OF_CONTROL = "out_of_control"
    NOT_RUN = "not_run"


class WestgardViolation(str, Enum):
    ONE_2S = "1_2s"
    ONE_3S = "1_3s"
    TWO_2S = "2_2s"
    R_4S = "r_4s"
    FOUR_1S = "4_1s"
    TEN_X = "10x"
    TWELVE_X = "12x"
    EIGHT_X = "8x"


class ResultFlag(str, Enum):
    NORMAL = "normal"
    HIGH = "high"
    LOW = "low"
    CRITICAL_HIGH = "critical_high"
    CRITICAL_LOW = "critical_low"
    PANIC = "panic"
    DELTA_FAIL = "delta_fail"
    INVALID = "invalid"


class ValidationAction(str, Enum):
    AUTO_VALIDATED = "auto_validated"
    MANUAL_VALIDATED = "manual_validated"
    REJECTED = "rejected"
    FLAGGED = "flagged"
    DELTA_CHECK_FAILED = "delta_check_failed"


class MaintenanceType(str, Enum):
    PREVENTIVE = "preventive"
    CORRECTIVE = "corrective"
    PREDICTIVE = "predictive"
    EMERGENCY = "emergency"
    CALIBRATION = "calibration"
    QUALIFICATION = "qualification"


class CalibrationType(str, Enum):
    STANDARD = "standard"
    FULL = "full"
    VERIFICATION = "verification"
    LOT_CHANGE = "lot_change"
    SCHEDULED = "scheduled"


class AssayCategory(str, Enum):
    CHEMISTRY = "chemistry"
    HEMATOLOGY = "hematology"
    IMMUNOLOGY = "immunology"
    MICROBIOLOGY = "microbiology"
    MOLECULAR = "molecular"
    SEROLOGY = "serology"
    TOXICOLOGY = "toxicology"
    ENDOCRINOLOGY = "endocrinology"
    COAGULATION = "coagulation"
    URINALYSIS = "urinalysis"
    HISTOPATHOLOGY = "histopathology"
    CYTOLOGY = "cytology"
    GENETICS = "genetics"
    BLOOD_BANK = "blood_bank"
    POINT_OF_CARE = "point_of_care"
    OTHER = "other"


class TransportationCondition(str, Enum):
    AMBIENT = "ambient"
    REFRIGERATED = "refrigerated"
    FROZEN = "frozen"
    CRYOGENIC = "cryogenic"
    TEMPERATURE_CONTROLLED = "temperature_controlled"


class ContainerType(str, Enum):
    SST = "sst"  # Serum Separator Tube
    PST = "pst"  # Plasma Separator Tube
    EDTA = "edta"  # EDTA Tube
    CITRATE = "citrate"  # Sodium Citrate
    HEPARIN = "heparin"  # Lithium/Sodium Heparin
    FLUORIDE = "fluoride"  # Sodium Fluoride / Potassium Oxalate
    PLAIN = "plain"  # Plain (no additive)
    STERILE = "sterile"  # Sterile container
    URINE_CUP = "urine_cup"
    STOOL_CUP = "stool_cup"
    SWAB_RED = "swab_red"  # Transport swab
    CULTURE_BOTTLE = "culture_bottle"
    BONE_MARROW = "bone_marrow"
    OTHER = "other"


class ReportStatus(str, Enum):
    DRAFT = "draft"
    FINAL = "final"
    AMENDED = "amended"
    CORRECTED = "corrected"
    CANCELLED = "cancelled"


# ── Helper to assign a ULID-like sync identifier ──────────────────────────


def _sync_id() -> str:
    return _uuid.uuid4().hex[:26]


# ===========================================================================
# CANONICAL LIMS ENTITIES
# ===========================================================================


class Department(Base):
    """Laboratory department (e.g., Haematology, Clinical Chemistry)."""

    __tablename__ = "lims_departments"

    id = Column(Integer, primary_key=True, index=True)
    lab_id = Column(Integer, ForeignKey("labs.id", ondelete="CASCADE"), nullable=False, index=True)
    code = Column(String(20), nullable=False, index=True)
    name = Column(String(200), nullable=False)
    name_ar = Column(String(200), nullable=True)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, index=True)
    sort_order = Column(Integer, default=0)
    sync_id = Column(String(26), unique=True, default=_sync_id, index=True)
    fhir_id = Column(String(64), nullable=True, index=True)
    fhir_resource_type = Column(String(32), nullable=True)
    created_by = Column(Integer, nullable=True)
    updated_by = Column(Integer, nullable=True)
    version = Column(Integer, default=1, nullable=False)
    is_deleted = Column(Boolean, default=False, nullable=False)
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
    )

    __table_args__ = (
        Index("ix_lims_dept_lab_code", "lab_id", "code", unique=True),
        Index("ix_lims_dept_not_deleted", "is_deleted", "lab_id"),
    )


class Section(Base):
    """Sub-department section or bench area."""

    __tablename__ = "lims_sections"

    id = Column(Integer, primary_key=True, index=True)
    department_id = Column(
        Integer, ForeignKey("lims_departments.id", ondelete="CASCADE"), nullable=False, index=True,
    )
    code = Column(String(20), nullable=False)
    name = Column(String(200), nullable=False)
    name_ar = Column(String(200), nullable=True)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    sync_id = Column(String(26), unique=True, default=_sync_id, index=True)
    fhir_id = Column(String(64), nullable=True, index=True)
    fhir_resource_type = Column(String(32), nullable=True)
    created_by = Column(Integer, nullable=True)
    updated_by = Column(Integer, nullable=True)
    version = Column(Integer, default=1, nullable=False)
    is_deleted = Column(Boolean, default=False, nullable=False)
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
    )

    __table_args__ = (UniqueConstraint("department_id", "code", name="uq_lims_section_dept_code"),)
    department = relationship("Department", backref="sections")


class Workstation(Base):
    """Physical/named workstation within a section."""

    __tablename__ = "lims_workstations"

    id = Column(Integer, primary_key=True, index=True)
    section_id = Column(
        Integer, ForeignKey("lims_sections.id", ondelete="CASCADE"), nullable=False, index=True,
    )
    code = Column(String(20), nullable=False)
    name = Column(String(200), nullable=False)
    workstation_type = Column(String(50), nullable=True)
    is_active = Column(Boolean, default=True)
    sync_id = Column(String(26), unique=True, default=_sync_id, index=True)
    fhir_id = Column(String(64), nullable=True, index=True)
    fhir_resource_type = Column(String(32), nullable=True)
    created_by = Column(Integer, nullable=True)
    updated_by = Column(Integer, nullable=True)
    version = Column(Integer, default=1, nullable=False)
    is_deleted = Column(Boolean, default=False, nullable=False)
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
    )

    section = relationship("Section", backref="workstations")


class Manufacturer(Base):
    """Equipment / reagent manufacturer."""

    __tablename__ = "lims_manufacturers"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(200), nullable=False)
    name_ar = Column(String(200), nullable=True)
    website = Column(String(300), nullable=True)
    support_phone = Column(String(20), nullable=True)
    support_email = Column(String(100), nullable=True)
    is_active = Column(Boolean, default=True)
    sync_id = Column(String(26), unique=True, default=_sync_id, index=True)
    created_by = Column(Integer, nullable=True)
    updated_by = Column(Integer, nullable=True)
    version = Column(Integer, default=1, nullable=False)
    is_deleted = Column(Boolean, default=False, nullable=False)
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
    )


class InstrumentModel(Base):
    """Specific model of an instrument/analyzer."""

    __tablename__ = "lims_instrument_models"

    id = Column(Integer, primary_key=True, index=True)
    manufacturer_id = Column(
        Integer,
        ForeignKey("lims_manufacturers.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    model_code = Column(String(50), nullable=False, index=True)
    model_name = Column(String(200), nullable=False)
    category = Column(String(50), nullable=True)
    interface_type = Column(String(50), nullable=True)  # astm, hl7, fhir, serial, tcp, usb
    supports_astm = Column(Boolean, default=False)
    supports_hl7 = Column(Boolean, default=False)
    supports_fhir = Column(Boolean, default=False)
    test_menu_capacity = Column(Integer, nullable=True)
    throughput_per_hour = Column(Integer, nullable=True)
    is_active = Column(Boolean, default=True)
    sync_id = Column(String(26), unique=True, default=_sync_id, index=True)
    created_by = Column(Integer, nullable=True)
    updated_by = Column(Integer, nullable=True)
    version = Column(Integer, default=1, nullable=False)
    is_deleted = Column(Boolean, default=False, nullable=False)
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
    )

    manufacturer = relationship("Manufacturer", backref="models")
    __table_args__ = (
        UniqueConstraint("manufacturer_id", "model_code", name="uq_lims_model_mfr_code"),
    )


class Instrument(Base):
    """Physical instrument/analyzer instance in a lab."""

    __tablename__ = "lims_instruments"

    id = Column(Integer, primary_key=True, index=True)
    lab_id = Column(Integer, ForeignKey("labs.id", ondelete="CASCADE"), nullable=False, index=True)
    model_id = Column(
        Integer,
        ForeignKey("lims_instrument_models.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    workstation_id = Column(
        Integer, ForeignKey("lims_workstations.id", ondelete="SET NULL"), nullable=True,
    )
    instrument_code = Column(String(50), nullable=False, index=True)
    serial_number = Column(String(200), nullable=True, index=True)
    asset_number = Column(String(100), nullable=True)
    status = Column(String(20), default="online", index=True)
    software_version = Column(String(50), nullable=True)
    installed_at = Column(DateTime(timezone=True), nullable=True)
    last_connected_at = Column(DateTime(timezone=True), nullable=True)
    ip_address = Column(String(45), nullable=True)
    port = Column(Integer, nullable=True)
    connection_params = Column(JSON, nullable=True)
    is_offline_capable = Column(Boolean, default=False)
    sync_id = Column(String(26), unique=True, default=_sync_id, index=True)
    fhir_id = Column(String(64), nullable=True, index=True)
    fhir_resource_type = Column(String(32), nullable=True)
    created_by = Column(Integer, nullable=True)
    updated_by = Column(Integer, nullable=True)
    version = Column(Integer, default=1, nullable=False)
    is_deleted = Column(Boolean, default=False, nullable=False)
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
    )

    model = relationship("InstrumentModel", backref="instruments")
    workstation = relationship("Workstation", backref="instruments")
    __table_args__ = (Index("ix_lims_inst_lab_status", "lab_id", "status"),)


class Maintenance(Base):
    """Equipment/instrument maintenance record."""

    __tablename__ = "lims_maintenance"

    id = Column(Integer, primary_key=True, index=True)
    instrument_id = Column(
        Integer, ForeignKey("lims_instruments.id", ondelete="CASCADE"), nullable=False, index=True,
    )
    maintenance_type = Column(String(30), nullable=False)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    performed_by = Column(Integer, ForeignKey("lab_users.id", ondelete="SET NULL"), nullable=True)
    performed_at = Column(DateTime(timezone=True), nullable=False)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    next_due_at = Column(DateTime(timezone=True), nullable=True)
    cost = Column(Numeric(12, 2), nullable=True)
    parts_replaced = Column(Text, nullable=True)
    result = Column(String(20), default="completed")
    notes = Column(Text, nullable=True)
    sync_id = Column(String(26), unique=True, default=_sync_id, index=True)
    created_by = Column(Integer, nullable=True)
    updated_by = Column(Integer, nullable=True)
    version = Column(Integer, default=1, nullable=False)
    is_deleted = Column(Boolean, default=False, nullable=False)
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
    )

    instrument = relationship("Instrument", backref="maintenance_records")


class Calibration(Base):
    """Instrument calibration record."""

    __tablename__ = "lims_calibrations"

    id = Column(Integer, primary_key=True, index=True)
    instrument_id = Column(
        Integer, ForeignKey("lims_instruments.id", ondelete="CASCADE"), nullable=False, index=True,
    )
    calibration_type = Column(String(30), nullable=False)
    performed_by = Column(Integer, ForeignKey("lab_users.id", ondelete="SET NULL"), nullable=True)
    performed_at = Column(DateTime(timezone=True), nullable=False)
    next_due_at = Column(DateTime(timezone=True), nullable=True)
    calibrator_lot = Column(String(100), nullable=True)
    calibrator_expiry = Column(Date, nullable=True)
    results = Column(JSON, nullable=True)
    passed = Column(Boolean, nullable=True)
    notes = Column(Text, nullable=True)
    sync_id = Column(String(26), unique=True, default=_sync_id, index=True)
    created_by = Column(Integer, nullable=True)
    updated_by = Column(Integer, nullable=True)
    version = Column(Integer, default=1, nullable=False)
    is_deleted = Column(Boolean, default=False, nullable=False)
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
    )

    instrument = relationship("Instrument", backref="calibrations")


class QCProgram(Base):
    """Quality Control Program definition."""

    __tablename__ = "lims_qc_programs"

    id = Column(Integer, primary_key=True, index=True)
    lab_id = Column(Integer, ForeignKey("labs.id", ondelete="CASCADE"), nullable=False, index=True)
    code = Column(String(50), nullable=False)
    name = Column(String(200), nullable=False)
    program_type = Column(String(20), nullable=False)  # iqc, eqa
    test_code = Column(String(50), nullable=False, index=True)
    instrument_id = Column(
        Integer, ForeignKey("lims_instruments.id", ondelete="SET NULL"), nullable=True,
    )
    rule_set = Column(String(50), nullable=True)  # westgard, custom
    rules = Column(JSON, nullable=True)  # specific rules configuration
    frequency = Column(String(20), nullable=True)  # per_batch, per_day, per_shift, per_week
    is_active = Column(Boolean, default=True)
    sync_id = Column(String(26), unique=True, default=_sync_id, index=True)
    created_by = Column(Integer, nullable=True)
    updated_by = Column(Integer, nullable=True)
    version = Column(Integer, default=1, nullable=False)
    is_deleted = Column(Boolean, default=False, nullable=False)
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
    )

    __table_args__ = (UniqueConstraint("lab_id", "code", name="uq_lims_qc_program_code"),)
    instrument = relationship("Instrument", backref="qc_programs")


class IQC(Base):
    """Internal Quality Control result."""

    __tablename__ = "lims_iqc"

    id = Column(Integer, primary_key=True, index=True)
    lab_id = Column(Integer, ForeignKey("labs.id", ondelete="CASCADE"), nullable=False, index=True)
    program_id = Column(
        Integer, ForeignKey("lims_qc_programs.id", ondelete="CASCADE"), nullable=False, index=True,
    )
    instrument_id = Column(
        Integer, ForeignKey("lims_instruments.id", ondelete="SET NULL"), nullable=True,
    )
    test_code = Column(String(50), nullable=False, index=True)
    lot_number = Column(String(100), nullable=True, index=True)
    level = Column(String(20), nullable=False)  # low, normal, high, level_1, level_2, level_3
    measured_value = Column(Float, nullable=False)
    expected_value = Column(Float, nullable=True)
    sd = Column(Float, nullable=True)
    mean = Column(Float, nullable=True)
    unit = Column(String(20), nullable=True)
    status = Column(String(20), default="in_control", index=True)
    violation = Column(String(20), nullable=True)  # westgard rule violated
    performed_by = Column(Integer, ForeignKey("lab_users.id", ondelete="SET NULL"), nullable=True)
    performed_at = Column(DateTime(timezone=True), nullable=False)
    notes = Column(Text, nullable=True)
    sync_id = Column(String(26), unique=True, default=_sync_id, index=True)
    created_by = Column(Integer, nullable=True)
    updated_by = Column(Integer, nullable=True)
    version = Column(Integer, default=1, nullable=False)
    is_deleted = Column(Boolean, default=False, nullable=False)
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
    )

    instrument = relationship("Instrument", backref="iqc_results")
    program = relationship("QCProgram", backref="iqc_results")
    __table_args__ = (Index("ix_lims_iqc_lab_test_date", "lab_id", "test_code", "performed_at"),)


class EQA(Base):
    """External Quality Assessment result."""

    __tablename__ = "lims_eqa"

    id = Column(Integer, primary_key=True, index=True)
    lab_id = Column(Integer, ForeignKey("labs.id", ondelete="CASCADE"), nullable=False, index=True)
    program_id = Column(
        Integer, ForeignKey("lims_qc_programs.id", ondelete="SET NULL"), nullable=True,
    )
    test_code = Column(String(50), nullable=False, index=True)
    scheme_name = Column(String(200), nullable=False)
    round_number = Column(String(50), nullable=False)
    sample_id = Column(String(100), nullable=True)
    submitted_value = Column(Float, nullable=True)
    target_value = Column(Float, nullable=True)
    acceptable_range = Column(String(100), nullable=True)
    z_score = Column(Float, nullable=True)
    deviation_percent = Column(Float, nullable=True)
    result = Column(String(20), nullable=True)  # acceptable, borderline, unacceptable
    submitted_by = Column(Integer, ForeignKey("lab_users.id", ondelete="SET NULL"), nullable=True)
    submitted_at = Column(DateTime(timezone=True), nullable=True)
    reviewed_by = Column(Integer, ForeignKey("lab_users.id", ondelete="SET NULL"), nullable=True)
    reviewed_at = Column(DateTime(timezone=True), nullable=True)
    corrective_action = Column(Text, nullable=True)
    sync_id = Column(String(26), unique=True, default=_sync_id, index=True)
    created_by = Column(Integer, nullable=True)
    updated_by = Column(Integer, nullable=True)
    version = Column(Integer, default=1, nullable=False)
    is_deleted = Column(Boolean, default=False, nullable=False)
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
    )

    __table_args__ = (
        UniqueConstraint(
            "lab_id", "scheme_name", "round_number", "test_code", name="uq_lims_eqa_round",
        ),
    )


class Lot(Base):
    """Reagent/control/calibrator lot tracking."""

    __tablename__ = "lims_lots"

    id = Column(Integer, primary_key=True, index=True)
    lab_id = Column(Integer, ForeignKey("labs.id", ondelete="CASCADE"), nullable=False, index=True)
    lot_number = Column(String(100), nullable=False, index=True)
    item_type = Column(String(30), nullable=False)  # reagent, control, calibrator, consumable
    item_code = Column(String(50), nullable=True)
    item_name = Column(String(200), nullable=False)
    manufacturer_id = Column(
        Integer, ForeignKey("lims_manufacturers.id", ondelete="SET NULL"), nullable=True,
    )
    quantity = Column(Float, nullable=True)
    unit = Column(String(20), nullable=True)
    received_at = Column(Date, nullable=True)
    expiry_at = Column(Date, nullable=True, index=True)
    opened_at = Column(DateTime(timezone=True), nullable=True)
    opened_by = Column(Integer, ForeignKey("lab_users.id", ondelete="SET NULL"), nullable=True)
    storage_condition = Column(String(200), nullable=True)
    certificate = Column(Text, nullable=True)  # COA reference
    is_active = Column(Boolean, default=True)
    is_consumed = Column(Boolean, default=False)
    consumed_at = Column(DateTime(timezone=True), nullable=True)
    sync_id = Column(String(26), unique=True, default=_sync_id, index=True)
    created_by = Column(Integer, nullable=True)
    updated_by = Column(Integer, nullable=True)
    version = Column(Integer, default=1, nullable=False)
    is_deleted = Column(Boolean, default=False, nullable=False)
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
    )

    manufacturer = relationship("Manufacturer", backref="lots")
    __table_args__ = (
        UniqueConstraint("lab_id", "lot_number", "item_type", name="uq_lims_lot"),
        Index("ix_lims_lot_expiry_active", "expiry_at", "is_active"),
    )


class Reagent(Base):
    """Reagent inventory item."""

    __tablename__ = "lims_reagents"

    id = Column(Integer, primary_key=True, index=True)
    lab_id = Column(Integer, ForeignKey("labs.id", ondelete="CASCADE"), nullable=False, index=True)
    reagent_code = Column(String(50), nullable=False, index=True)
    reagent_name = Column(String(200), nullable=False)
    reagent_name_ar = Column(String(200), nullable=True)
    lot_id = Column(Integer, ForeignKey("lims_lots.id", ondelete="SET NULL"), nullable=True)
    manufacturer_id = Column(
        Integer, ForeignKey("lims_manufacturers.id", ondelete="SET NULL"), nullable=True,
    )
    supplier_id = Column(
        Integer, ForeignKey("lims_suppliers.id", ondelete="SET NULL"), nullable=True,
    )
    category = Column(String(50), nullable=True)
    current_quantity = Column(Float, nullable=False, default=0)
    unit = Column(String(20), nullable=False)
    minimum_quantity = Column(Float, nullable=True)
    maximum_quantity = Column(Float, nullable=True)
    storage_location = Column(String(100), nullable=True)
    is_active = Column(Boolean, default=True)
    sync_id = Column(String(26), unique=True, default=_sync_id, index=True)
    created_by = Column(Integer, nullable=True)
    updated_by = Column(Integer, nullable=True)
    version = Column(Integer, default=1, nullable=False)
    is_deleted = Column(Boolean, default=False, nullable=False)
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
    )

    lot = relationship("Lot", backref="reagents")
    manufacturer = relationship("Manufacturer", backref="reagents")
    supplier = relationship("Supplier", backref="reagents")
    __table_args__ = (
        UniqueConstraint("lab_id", "reagent_code", name="uq_lims_reagent_code"),
        Index("ix_lims_reagent_stock", "lab_id", "current_quantity"),
    )


class Supplier(Base):
    """Vendor/supplier of lab items."""

    __tablename__ = "lims_suppliers"

    id = Column(Integer, primary_key=True, index=True)
    lab_id = Column(Integer, ForeignKey("labs.id", ondelete="CASCADE"), nullable=False, index=True)
    code = Column(String(50), nullable=False, index=True)
    name = Column(String(200), nullable=False)
    name_ar = Column(String(200), nullable=True)
    contact_person = Column(String(200), nullable=True)
    phone = Column(String(20), nullable=True)
    email = Column(String(100), nullable=True)
    address = Column(String(500), nullable=True)
    is_active = Column(Boolean, default=True)
    sync_id = Column(String(26), unique=True, default=_sync_id, index=True)
    created_by = Column(Integer, nullable=True)
    updated_by = Column(Integer, nullable=True)
    version = Column(Integer, default=1, nullable=False)
    is_deleted = Column(Boolean, default=False, nullable=False)
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
    )

    __table_args__ = (UniqueConstraint("lab_id", "code", name="uq_lims_supplier_lab_code"),)


class Consumable(Base):
    """Lab consumable tracking."""

    __tablename__ = "lims_consumables"

    id = Column(Integer, primary_key=True, index=True)
    lab_id = Column(Integer, ForeignKey("labs.id", ondelete="CASCADE"), nullable=False, index=True)
    code = Column(String(50), nullable=False, index=True)
    name = Column(String(200), nullable=False)
    name_ar = Column(String(200), nullable=True)
    lot_id = Column(Integer, ForeignKey("lims_lots.id", ondelete="SET NULL"), nullable=True)
    supplier_id = Column(
        Integer, ForeignKey("lims_suppliers.id", ondelete="SET NULL"), nullable=True,
    )
    category = Column(String(50), nullable=True)
    current_quantity = Column(Integer, nullable=False, default=0)
    unit = Column(String(20), nullable=False)
    minimum_quantity = Column(Integer, nullable=True)
    storage_location = Column(String(100), nullable=True)
    is_active = Column(Boolean, default=True)
    sync_id = Column(String(26), unique=True, default=_sync_id, index=True)
    created_by = Column(Integer, nullable=True)
    updated_by = Column(Integer, nullable=True)
    version = Column(Integer, default=1, nullable=False)
    is_deleted = Column(Boolean, default=False, nullable=False)
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
    )

    lot = relationship("Lot", backref="consumables")
    supplier = relationship("Supplier", backref="consumables")
    __table_args__ = (UniqueConstraint("lab_id", "code", name="uq_lims_consumable_code"),)


class Storage(Base):
    """Storage location for specimens/reagents (fridge, freezer, rack, shelf)."""

    __tablename__ = "lims_storage"

    id = Column(Integer, primary_key=True, index=True)
    lab_id = Column(Integer, ForeignKey("labs.id", ondelete="CASCADE"), nullable=False, index=True)
    code = Column(String(50), nullable=False, index=True)
    name = Column(String(200), nullable=False)
    name_ar = Column(String(200), nullable=True)
    storage_type = Column(
        String(30), nullable=True,
    )  # refrigerator, freezer, room, incubator, rack, shelf
    temperature_min = Column(Float, nullable=True)
    temperature_max = Column(Float, nullable=True)
    location = Column(String(200), nullable=True)
    capacity = Column(Integer, nullable=True)
    is_active = Column(Boolean, default=True)
    parent_id = Column(Integer, ForeignKey("lims_storage.id", ondelete="SET NULL"), nullable=True)
    sync_id = Column(String(26), unique=True, default=_sync_id, index=True)
    created_by = Column(Integer, nullable=True)
    updated_by = Column(Integer, nullable=True)
    version = Column(Integer, default=1, nullable=False)
    is_deleted = Column(Boolean, default=False, nullable=False)
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
    )

    parent = relationship("Storage", remote_side="Storage.id", backref="children")
    __table_args__ = (UniqueConstraint("lab_id", "code", name="uq_lims_storage_lab_code"),)


class TemperatureLog(Base):
    """Temperature monitoring log for storage units."""

    __tablename__ = "lims_temperature_logs"

    id = Column(Integer, primary_key=True, index=True)
    lab_id = Column(Integer, ForeignKey("labs.id", ondelete="CASCADE"), nullable=False, index=True)
    storage_id = Column(
        Integer, ForeignKey("lims_storage.id", ondelete="CASCADE"), nullable=False, index=True,
    )
    temperature = Column(Float, nullable=False)
    unit = Column(String(10), default="celsius")
    recorded_at = Column(DateTime(timezone=True), nullable=False)
    recorded_by = Column(Integer, ForeignKey("lab_users.id", ondelete="SET NULL"), nullable=True)
    is_breach = Column(Boolean, default=False)
    breach_notes = Column(Text, nullable=True)
    sync_id = Column(String(26), unique=True, default=_sync_id, index=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)

    storage = relationship("Storage", backref="temperature_logs")
    __table_args__ = (Index("ix_lims_temp_storage_time", "storage_id", "recorded_at"),)


class EquipmentLog(Base):
    """Equipment usage/operation log."""

    __tablename__ = "lims_equipment_logs"

    id = Column(Integer, primary_key=True, index=True)
    instrument_id = Column(
        Integer, ForeignKey("lims_instruments.id", ondelete="CASCADE"), nullable=False, index=True,
    )
    event_type = Column(
        String(30), nullable=False,
    )  # startup, shutdown, error, note, sample_start, sample_end
    description = Column(String(500), nullable=True)
    logged_by = Column(Integer, ForeignKey("lab_users.id", ondelete="SET NULL"), nullable=True)
    logged_at = Column(DateTime(timezone=True), nullable=False)
    metadata_json = Column(JSON, nullable=True)
    sync_id = Column(String(26), unique=True, default=_sync_id, index=True)
    version = Column(Integer, default=1, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)

    instrument = relationship("Instrument", backref="equipment_logs")
    __table_args__ = (Index("ix_lims_eqlog_inst_time", "instrument_id", "logged_at"),)


class SpecimenCatalog(Base):
    """Specimen type catalog — canonical list of specimen types."""

    __tablename__ = "lims_specimen_catalog"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(30), unique=True, nullable=False, index=True)
    name = Column(String(200), nullable=False)
    name_ar = Column(String(200), nullable=True)
    description = Column(Text, nullable=True)
    default_container_type = Column(String(30), nullable=True)
    default_volume_ml = Column(Float, nullable=True)
    storage_condition = Column(String(100), nullable=True)
    stability_hours = Column(Integer, nullable=True)
    is_active = Column(Boolean, default=True)
    loinc_code = Column(String(20), nullable=True)
    snomed_code = Column(String(20), nullable=True)
    sync_id = Column(String(26), unique=True, default=_sync_id, index=True)
    version = Column(Integer, default=1, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
    )


class Container(Base):
    """Specimen container type catalog."""

    __tablename__ = "lims_containers"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(30), unique=True, nullable=False, index=True)
    name = Column(String(200), nullable=False)
    name_ar = Column(String(200), nullable=True)
    container_type = Column(String(30), nullable=False)
    volume_ml = Column(Float, nullable=True)
    additive = Column(String(100), nullable=True)
    color_code = Column(String(20), nullable=True)
    is_active = Column(Boolean, default=True)
    sync_id = Column(String(26), unique=True, default=_sync_id, index=True)
    version = Column(Integer, default=1, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
    )


class Specimen(Base):
    """Complete specimen lifecycle — replaces existing Sample model.

    Supports full state machine: Ordered → Registered → Collected →
    Transporting → Received → Accepted → Aliquoted → Processing →
    Analyzing → Analyzed → Verified → Validated → Released → Archived → Disposed.

    Rejection can occur at Receiving, Acceptance, or any pre-analysis step.
    """

    __tablename__ = "lims_specimens"

    id = Column(Integer, primary_key=True, index=True)
    lab_id = Column(Integer, ForeignKey("labs.id", ondelete="CASCADE"), nullable=False, index=True)
    order_id = Column(
        Integer, ForeignKey("lab_orders.id", ondelete="CASCADE"), nullable=False, index=True,
    )
    parent_specimen_id = Column(
        Integer, ForeignKey("lims_specimens.id", ondelete="SET NULL"), nullable=True,
    )
    barcode = Column(String(30), unique=True, nullable=False, index=True)
    qr_code = Column(Text, nullable=True)
    specimen_type = Column(String(30), nullable=False, index=True)
    container_type = Column(String(30), nullable=True)
    volume_ml = Column(Float, nullable=True)
    status = Column(String(20), default="ordered", nullable=False, index=True)
    collection_time = Column(DateTime(timezone=True), nullable=True)
    collected_by = Column(Integer, ForeignKey("lab_users.id", ondelete="SET NULL"), nullable=True)
    collection_site = Column(String(200), nullable=True)
    collection_notes = Column(Text, nullable=True)
    received_at = Column(DateTime(timezone=True), nullable=True)
    received_by = Column(Integer, ForeignKey("lab_users.id", ondelete="SET NULL"), nullable=True)
    accepted_at = Column(DateTime(timezone=True), nullable=True)
    accepted_by = Column(Integer, ForeignKey("lab_users.id", ondelete="SET NULL"), nullable=True)
    rejection_reason = Column(String(500), nullable=True)
    rejected_at = Column(DateTime(timezone=True), nullable=True)
    rejected_by = Column(Integer, ForeignKey("lab_users.id", ondelete="SET NULL"), nullable=True)
    storage_id = Column(Integer, ForeignKey("lims_storage.id", ondelete="SET NULL"), nullable=True)
    storage_position = Column(String(50), nullable=True)
    analyzed_at = Column(DateTime(timezone=True), nullable=True)
    verified_at = Column(DateTime(timezone=True), nullable=True)
    verified_by = Column(Integer, ForeignKey("lab_users.id", ondelete="SET NULL"), nullable=True)
    validated_at = Column(DateTime(timezone=True), nullable=True)
    validated_by = Column(Integer, ForeignKey("lab_users.id", ondelete="SET NULL"), nullable=True)
    released_at = Column(DateTime(timezone=True), nullable=True)
    released_by = Column(Integer, ForeignKey("lab_users.id", ondelete="SET NULL"), nullable=True)
    archived_at = Column(DateTime(timezone=True), nullable=True)
    disposed_at = Column(DateTime(timezone=True), nullable=True)
    disposal_method = Column(String(100), nullable=True)
    clinical_info = Column(Text, nullable=True)
    is_control = Column(Boolean, default=False)
    control_specimen_id = Column(
        Integer, ForeignKey("lims_specimens.id", ondelete="SET NULL"), nullable=True,
    )
    sync_id = Column(String(26), unique=True, default=_sync_id, index=True)
    fhir_id = Column(String(64), nullable=True, index=True)
    fhir_resource_type = Column(String(32), nullable=True)
    created_by = Column(Integer, nullable=True)
    updated_by = Column(Integer, nullable=True)
    version = Column(Integer, default=1, nullable=False)
    is_deleted = Column(Boolean, default=False, nullable=False)
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
    )

    parent = relationship(
        "Specimen", remote_side="Specimen.id", foreign_keys=[parent_specimen_id], backref="aliquots",
    )
    storage = relationship("Storage", backref="specimens")
    __table_args__ = (
        Index("ix_lims_spec_lab_status", "lab_id", "status"),
        Index("ix_lims_spec_order", "order_id", "status"),
    )


class Transportation(Base):
    """Specimen transportation record."""

    __tablename__ = "lims_transportation"

    id = Column(Integer, primary_key=True, index=True)
    lab_id = Column(Integer, ForeignKey("labs.id", ondelete="CASCADE"), nullable=False, index=True)
    specimen_id = Column(
        Integer, ForeignKey("lims_specimens.id", ondelete="CASCADE"), nullable=False, index=True,
    )
    from_location = Column(String(200), nullable=False)
    to_location = Column(String(200), nullable=False)
    condition = Column(String(30), default="ambient")
    courier_name = Column(String(200), nullable=True)
    courier_phone = Column(String(20), nullable=True)
    dispatched_at = Column(DateTime(timezone=True), nullable=True)
    received_at = Column(DateTime(timezone=True), nullable=True)
    temperature_min = Column(Float, nullable=True)
    temperature_max = Column(Float, nullable=True)
    chain_closed = Column(Boolean, default=False)
    notes = Column(Text, nullable=True)
    sync_id = Column(String(26), unique=True, default=_sync_id, index=True)
    created_by = Column(Integer, nullable=True)
    updated_by = Column(Integer, nullable=True)
    version = Column(Integer, default=1, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
    )

    specimen = relationship("Specimen", backref="transportation_records")


class ChainOfCustody(Base):
    """Chain of custody record for legal/forensic specimens."""

    __tablename__ = "lims_chain_of_custody"

    id = Column(Integer, primary_key=True, index=True)
    specimen_id = Column(
        Integer, ForeignKey("lims_specimens.id", ondelete="CASCADE"), nullable=False, index=True,
    )
    event_type = Column(String(30), nullable=False)  # transfer, handover, receive, dispose
    from_person = Column(String(200), nullable=True)
    to_person = Column(String(200), nullable=True)
    timestamp = Column(DateTime(timezone=True), nullable=False)
    reason = Column(String(500), nullable=True)
    signature = Column(Text, nullable=True)  # base64 encoded digital signature
    previous_hash = Column(String(64), nullable=True)
    current_hash = Column(String(64), nullable=True)
    sync_id = Column(String(26), unique=True, default=_sync_id, index=True)
    created_by = Column(Integer, nullable=True)
    version = Column(Integer, default=1, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)

    specimen = relationship("Specimen", backref="chain_of_custody_records")
    __table_args__ = (Index("ix_lims_coc_specimen", "specimen_id", "timestamp"),)


class Order(Base):
    """Laboratory Order — supplements LabOrder with LIMS-specific fields.

    References the existing app.models.LabOrder via order_id.
    """

    __tablename__ = "lims_orders"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(
        Integer,
        ForeignKey("lab_orders.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True,
    )
    lab_id = Column(Integer, ForeignKey("labs.id", ondelete="CASCADE"), nullable=False, index=True)
    accession_number = Column(String(30), unique=True, nullable=False, index=True)
    priority = Column(String(20), default="routine")  # routine, urgent, stat, timed
    order_status = Column(String(20), default="pending", index=True)
    ordered_by = Column(Integer, ForeignKey("lab_users.id", ondelete="SET NULL"), nullable=True)
    ordered_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    requested_completion = Column(DateTime(timezone=True), nullable=True)
    clinical_note = Column(Text, nullable=True)
    diagnosis_code = Column(String(20), nullable=True)
    icd_code = Column(String(20), nullable=True)
    is_referral = Column(Boolean, default=False)
    referring_lab_id = Column(Integer, ForeignKey("labs.id", ondelete="SET NULL"), nullable=True)
    referring_physician = Column(String(200), nullable=True)
    is_printed = Column(Boolean, default=False)
    is_corrected = Column(Boolean, default=False)
    correction_reason = Column(Text, nullable=True)
    original_order_id = Column(
        Integer, ForeignKey("lims_orders.id", ondelete="SET NULL"), nullable=True,
    )
    sync_id = Column(String(26), unique=True, default=_sync_id, index=True)
    fhir_id = Column(String(64), nullable=True, index=True)
    fhir_resource_type = Column(String(32), nullable=True)
    created_by = Column(Integer, nullable=True)
    updated_by = Column(Integer, nullable=True)
    version = Column(Integer, default=1, nullable=False)
    is_deleted = Column(Boolean, default=False, nullable=False)
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
    )

    original_order = relationship("Order", remote_side="Order.id", backref="corrections")
    __table_args__ = (Index("ix_lims_order_lab_status", "lab_id", "order_status"),)


class Panel(Base):
    """Test panel/group (e.g., Complete Blood Count, Liver Panel)."""

    __tablename__ = "lims_panels"

    id = Column(Integer, primary_key=True, index=True)
    lab_id = Column(Integer, ForeignKey("labs.id", ondelete="CASCADE"), nullable=False, index=True)
    code = Column(String(50), nullable=False, index=True)
    name = Column(String(200), nullable=False)
    name_ar = Column(String(200), nullable=True)
    category = Column(String(50), nullable=True)
    description = Column(Text, nullable=True)
    tat_target_minutes = Column(Integer, nullable=True)
    is_active = Column(Boolean, default=True)
    is_national_essential = Column(Boolean, default=False)
    department_id = Column(
        Integer, ForeignKey("lims_departments.id", ondelete="SET NULL"), nullable=True,
    )
    sync_id = Column(String(26), unique=True, default=_sync_id, index=True)
    fhir_id = Column(String(64), nullable=True, index=True)
    fhir_resource_type = Column(String(32), nullable=True)
    created_by = Column(Integer, nullable=True)
    updated_by = Column(Integer, nullable=True)
    version = Column(Integer, default=1, nullable=False)
    is_deleted = Column(Boolean, default=False, nullable=False)
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
    )

    department = relationship("Department", backref="panels")
    __table_args__ = (UniqueConstraint("lab_id", "code", name="uq_lims_panel_lab_code"),)


class PanelTest(Base):
    """Many-to-many: Panel <-> Test (with display order)."""

    __tablename__ = "lims_panel_tests"

    id = Column(Integer, primary_key=True, index=True)
    panel_id = Column(
        Integer, ForeignKey("lims_panels.id", ondelete="CASCADE"), nullable=False, index=True,
    )
    test_code = Column(String(50), nullable=False, index=True)
    display_order = Column(Integer, default=0)
    is_required = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)

    __table_args__ = (UniqueConstraint("panel_id", "test_code", name="uq_lims_panel_test"),)


class Result(Base):
    """Individual observation/result for a test on a specimen.

    This is the canonical LIMS result entity. Numeric results use value_numeric
    while textual/coded results use value_text.  Reference ranges, flags, and
    QC information are all captured here.
    """

    __tablename__ = "lims_results"

    id = Column(Integer, primary_key=True, index=True)
    lab_id = Column(Integer, ForeignKey("labs.id", ondelete="CASCADE"), nullable=False, index=True)
    specimen_id = Column(
        Integer, ForeignKey("lims_specimens.id", ondelete="CASCADE"), nullable=False, index=True,
    )
    order_id = Column(
        Integer, ForeignKey("lab_orders.id", ondelete="CASCADE"), nullable=False, index=True,
    )
    test_code = Column(String(50), nullable=False, index=True)
    test_name = Column(String(200), nullable=False)
    test_name_ar = Column(String(200), nullable=True)
    category = Column(String(50), nullable=True)

    # Result values
    value_numeric = Column(Float, nullable=True)
    value_text = Column(Text, nullable=True)
    value_coded = Column(String(50), nullable=True)
    unit = Column(String(20), nullable=True)

    # Reference range
    ref_range_low = Column(Float, nullable=True)
    ref_range_high = Column(Float, nullable=True)
    ref_range_text = Column(String(500), nullable=True)

    # Critical range
    critical_low = Column(Float, nullable=True)
    critical_high = Column(Float, nullable=True)

    # Flagging
    flag = Column(String(20), nullable=True, index=True)
    is_critical = Column(Boolean, default=False)
    is_abnormal = Column(Boolean, default=False)
    is_panic = Column(Boolean, default=False)

    # Instrument information
    instrument_id = Column(
        Integer, ForeignKey("lims_instruments.id", ondelete="SET NULL"), nullable=True,
    )
    instrument_result_id = Column(String(100), nullable=True)

    # QC
    qc_status = Column(String(20), nullable=True)
    delta_check_status = Column(String(20), nullable=True)
    delta_percent = Column(Float, nullable=True)

    # Validation
    validation_status = Column(String(20), default="pending", index=True)
    auto_validated = Column(Boolean, default=False)
    auto_validated_at = Column(DateTime(timezone=True), nullable=True)
    validated_by = Column(Integer, ForeignKey("lab_users.id", ondelete="SET NULL"), nullable=True)
    validated_at = Column(DateTime(timezone=True), nullable=True)
    validation_note = Column(Text, nullable=True)

    # LOINC mapping
    loinc_code = Column(String(20), nullable=True, index=True)
    snomed_code = Column(String(20), nullable=True)

    # Result metadata
    performed_at = Column(DateTime(timezone=True), nullable=True)
    performed_by = Column(Integer, ForeignKey("lab_users.id", ondelete="SET NULL"), nullable=True)
    result_status = Column(String(20), default="final", index=True)

    # Offline / sync
    sync_id = Column(String(26), unique=True, default=_sync_id, index=True)
    fhir_id = Column(String(64), nullable=True, index=True)
    fhir_resource_type = Column(String(32), nullable=True)

    # Audit
    created_by = Column(Integer, nullable=True)
    updated_by = Column(Integer, nullable=True)
    version = Column(Integer, default=1, nullable=False)
    is_deleted = Column(Boolean, default=False, nullable=False)
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
    )

    specimen = relationship("Specimen", backref="results")
    instrument = relationship("Instrument", backref="results")
    __table_args__ = (
        Index("ix_lims_result_lab_test", "lab_id", "test_code"),
        Index("ix_lims_result_validation", "lab_id", "validation_status"),
        Index("ix_lims_result_specimen", "specimen_id", "test_code", unique=True),
    )


class ReferenceRangeDef(Base):
    """Reference range definition per test, method, age, gender."""

    __tablename__ = "lims_reference_ranges"

    id = Column(Integer, primary_key=True, index=True)
    test_code = Column(String(50), nullable=False, index=True)
    lab_id = Column(Integer, ForeignKey("labs.id", ondelete="CASCADE"), nullable=True, index=True)
    instrument_id = Column(
        Integer, ForeignKey("lims_instruments.id", ondelete="SET NULL"), nullable=True,
    )
    method = Column(String(100), nullable=True)
    gender = Column(String(1), nullable=True)  # M, F, or null for both
    age_min_years = Column(Float, nullable=True)
    age_max_years = Column(Float, nullable=True)
    age_min_days = Column(Integer, nullable=True)
    age_max_days = Column(Integer, nullable=True)
    ref_range_low = Column(Float, nullable=True)
    ref_range_high = Column(Float, nullable=True)
    ref_range_text = Column(String(500), nullable=True)
    critical_low = Column(Float, nullable=True)
    critical_high = Column(Float, nullable=True)
    panic_low = Column(Float, nullable=True)
    panic_high = Column(Float, nullable=True)
    unit = Column(String(20), nullable=True)
    source = Column(String(200), nullable=True)
    is_active = Column(Boolean, default=True)
    effective_from = Column(Date, nullable=True)
    effective_until = Column(Date, nullable=True)
    sync_id = Column(String(26), unique=True, default=_sync_id, index=True)
    version = Column(Integer, default=1, nullable=False)
    is_deleted = Column(Boolean, default=False, nullable=False)
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    created_by = Column(Integer, nullable=True)
    updated_by = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
    )

    __table_args__ = (Index("ix_lims_refrange_lookup", "test_code", "lab_id", "gender"),)


class AutoValidationRule(Base):
    """Auto-validation rule configuration."""

    __tablename__ = "lims_auto_validation_rules"

    id = Column(Integer, primary_key=True, index=True)
    lab_id = Column(Integer, ForeignKey("labs.id", ondelete="CASCADE"), nullable=False, index=True)
    rule_name = Column(String(200), nullable=False)
    test_code = Column(String(50), nullable=False, index=True)
    rule_type = Column(String(30), nullable=False)  # range, delta, qc, instrument, combination
    conditions = Column(JSON, nullable=False)  # rule conditions as JSON
    action = Column(String(20), default="validate")  # validate, flag, reject
    priority = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    sync_id = Column(String(26), unique=True, default=_sync_id, index=True)
    version = Column(Integer, default=1, nullable=False)
    is_deleted = Column(Boolean, default=False, nullable=False)
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    created_by = Column(Integer, nullable=True)
    updated_by = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
    )

    __table_args__ = (Index("ix_lims_autovalid_test", "test_code", "lab_id"),)


class DeltaCheckRule(Base):
    """Delta check rule configuration."""

    __tablename__ = "lims_delta_check_rules"

    id = Column(Integer, primary_key=True, index=True)
    lab_id = Column(Integer, ForeignKey("labs.id", ondelete="CASCADE"), nullable=False, index=True)
    test_code = Column(String(50), nullable=False, index=True)
    test_name = Column(String(200), nullable=False)
    delta_percent = Column(Float, nullable=False)
    delta_absolute = Column(Float, nullable=True)
    window_days = Column(Integer, default=30)
    applies_to = Column(String(20), default="all")  # all, increases, decreases
    action = Column(String(20), default="flag")  # flag, block, warn
    is_active = Column(Boolean, default=True)
    sync_id = Column(String(26), unique=True, default=_sync_id, index=True)
    version = Column(Integer, default=1, nullable=False)
    is_deleted = Column(Boolean, default=False, nullable=False)
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    created_by = Column(Integer, nullable=True)
    updated_by = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
    )

    __table_args__ = (UniqueConstraint("lab_id", "test_code", name="uq_lims_delta_check"),)


class ResultValidation(Base):
    """Manual result validation record."""

    __tablename__ = "lims_result_validations"

    id = Column(Integer, primary_key=True, index=True)
    result_id = Column(
        Integer, ForeignKey("lims_results.id", ondelete="CASCADE"), nullable=False, index=True,
    )
    action = Column(String(30), nullable=False)  # validated, rejected, flagged, amended
    validated_by = Column(Integer, ForeignKey("lab_users.id", ondelete="SET NULL"), nullable=False)
    validated_at = Column(DateTime(timezone=True), nullable=False)
    notes = Column(Text, nullable=True)
    is_electronic_signature = Column(Boolean, default=False)
    signature_data = Column(Text, nullable=True)  # base64 encoded signature
    sync_id = Column(String(26), unique=True, default=_sync_id, index=True)
    version = Column(Integer, default=1, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)

    result = relationship("Result", backref="validations")


class ResultRelease(Base):
    """Result release record — tracks when results are released to patient/doctor."""

    __tablename__ = "lims_result_releases"

    id = Column(Integer, primary_key=True, index=True)
    lab_id = Column(Integer, ForeignKey("labs.id", ondelete="CASCADE"), nullable=False, index=True)
    order_id = Column(
        Integer, ForeignKey("lab_orders.id", ondelete="CASCADE"), nullable=False, index=True,
    )
    released_by = Column(Integer, ForeignKey("lab_users.id", ondelete="SET NULL"), nullable=False)
    released_at = Column(DateTime(timezone=True), nullable=False)
    release_channel = Column(String(20), nullable=True)  # portal, print, fhir, hl7, email
    is_patient_notified = Column(Boolean, default=False)
    notified_at = Column(DateTime(timezone=True), nullable=True)
    sync_id = Column(String(26), unique=True, default=_sync_id, index=True)
    version = Column(Integer, default=1, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
    )

    __table_args__ = (Index("ix_lims_release_order", "order_id"),)


class ElectronicSignature(Base):
    """Electronic signature record for compliance (ISO 15189, CAP, CLSI)."""

    __tablename__ = "lims_electronic_signatures"

    id = Column(Integer, primary_key=True, index=True)
    lab_id = Column(Integer, ForeignKey("labs.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(
        Integer, ForeignKey("lab_users.id", ondelete="CASCADE"), nullable=False, index=True,
    )
    signature_type = Column(
        String(30), nullable=False,
    )  # validation, release, correction, amendment
    resource_type = Column(String(30), nullable=False)  # result, report, order
    resource_id = Column(Integer, nullable=False)
    signature_hash = Column(String(128), nullable=False)
    signed_at = Column(DateTime(timezone=True), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    is_revoked = Column(Boolean, default=False)
    revoked_at = Column(DateTime(timezone=True), nullable=True)
    sync_id = Column(String(26), unique=True, default=_sync_id, index=True)
    version = Column(Integer, default=1, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
    )

    __table_args__ = (
        Index("ix_lims_esignature_user", "user_id"),
        Index("ix_lims_esignature_resource", "resource_type", "resource_id"),
    )


class LabReport(Base):
    """Laboratory report — the printable/digital report delivered to clinicians."""

    __tablename__ = "lims_reports"

    id = Column(Integer, primary_key=True, index=True)
    lab_id = Column(Integer, ForeignKey("labs.id", ondelete="CASCADE"), nullable=False, index=True)
    order_id = Column(
        Integer, ForeignKey("lab_orders.id", ondelete="CASCADE"), nullable=False, index=True,
    )
    report_number = Column(String(30), unique=True, nullable=False, index=True)
    status = Column(String(20), default="draft", index=True)
    title = Column(String(300), nullable=True)
    title_ar = Column(String(300), nullable=True)
    report_format = Column(String(20), default="pdf")  # pdf, html, fhir
    generated_by = Column(Integer, ForeignKey("lab_users.id", ondelete="SET NULL"), nullable=True)
    generated_at = Column(DateTime(timezone=True), nullable=True)
    finalized_by = Column(Integer, ForeignKey("lab_users.id", ondelete="SET NULL"), nullable=True)
    finalized_at = Column(DateTime(timezone=True), nullable=True)
    corrected_by = Column(Integer, ForeignKey("lab_users.id", ondelete="SET NULL"), nullable=True)
    corrected_at = Column(DateTime(timezone=True), nullable=True)
    correction_reason = Column(Text, nullable=True)
    is_electronic = Column(Boolean, default=True)
    is_printed = Column(Boolean, default=False)
    printed_at = Column(DateTime(timezone=True), nullable=True)
    printed_by = Column(Integer, ForeignKey("lab_users.id", ondelete="SET NULL"), nullable=True)
    watermark = Column(String(200), nullable=True)
    locale = Column(String(10), default="ar")  # ar, en
    sync_id = Column(String(26), unique=True, default=_sync_id, index=True)
    fhir_id = Column(String(64), nullable=True, index=True)
    fhir_resource_type = Column(String(32), nullable=True)
    created_by = Column(Integer, nullable=True)
    updated_by = Column(Integer, nullable=True)
    version = Column(Integer, default=1, nullable=False)
    is_deleted = Column(Boolean, default=False, nullable=False)
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
    )

    __table_args__ = (Index("ix_lims_report_lab_status", "lab_id", "status"),)


class ReportAttachment(Base):
    """Attachment on a lab report (PDF, image, scanned document)."""

    __tablename__ = "lims_report_attachments"

    id = Column(Integer, primary_key=True, index=True)
    report_id = Column(
        Integer, ForeignKey("lims_reports.id", ondelete="CASCADE"), nullable=False, index=True,
    )
    file_name = Column(String(300), nullable=False)
    file_type = Column(String(100), nullable=True)
    file_size_bytes = Column(Integer, nullable=True)
    storage_path = Column(String(500), nullable=True)
    is_watermarked = Column(Boolean, default=False)
    uploaded_by = Column(Integer, ForeignKey("lab_users.id", ondelete="SET NULL"), nullable=True)
    uploaded_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    sync_id = Column(String(26), unique=True, default=_sync_id, index=True)
    version = Column(Integer, default=1, nullable=False)
    is_deleted = Column(Boolean, default=False, nullable=False)
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)

    report = relationship("LabReport", backref="attachments")
