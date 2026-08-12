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
from ..enums import BoardStatus, CompetencyLevel, LicenseStatus, ProductivityPeriod


class HealthcareWorker(GovernanceBaseEntity):
    __tablename__ = "gov_healthcare_workers"

    id = Column(Integer, primary_key=True, autoincrement=True)
    employee_code = Column(String(50), unique=True, nullable=False, index=True)
    full_name_ar = Column(String(300), nullable=False)
    full_name_en = Column(String(300), nullable=True)
    national_id_hash = Column(String(255), nullable=True, index=True)
    profession = Column(String(100), nullable=False, index=True)
    specialization = Column(String(200), nullable=True, index=True)
    organization_node_id = Column(Integer, ForeignKey("gov_hierarchy_nodes.id"), nullable=True, index=True)
    department = Column(String(200), nullable=True)
    unit = Column(String(200), nullable=True)
    is_active = Column(Boolean, default=True, index=True)
    employment_date = Column(Date, nullable=True)
    contact_phone = Column(String(20), nullable=True)
    contact_email = Column(String(200), nullable=True)
    metadata_json = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))


class ProfessionalLicense(GovernanceBaseEntity):
    __tablename__ = "gov_professional_licenses"

    id = Column(Integer, primary_key=True, autoincrement=True)
    worker_id = Column(Integer, ForeignKey("gov_healthcare_workers.id"), nullable=False, index=True)
    license_number = Column(String(100), unique=True, nullable=False, index=True)
    license_type = Column(String(100), nullable=False)
    issuing_authority = Column(String(200), nullable=False)
    status = Column(Enum(LicenseStatus), nullable=False, default=LicenseStatus.ACTIVE, index=True)
    issued_date = Column(Date, nullable=False)
    expiry_date = Column(Date, nullable=True)
    verified_at = Column(DateTime(timezone=True), nullable=True)
    verified_by = Column(String(200), nullable=True)
    metadata_json = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))


class BoardCertification(GovernanceBaseEntity):
    __tablename__ = "gov_board_certifications"

    id = Column(Integer, primary_key=True, autoincrement=True)
    worker_id = Column(Integer, ForeignKey("gov_healthcare_workers.id"), nullable=False, index=True)
    board_name = Column(String(200), nullable=False)
    specialty = Column(String(200), nullable=False)
    certificate_number = Column(String(100), nullable=True, index=True)
    issuing_body = Column(String(200), nullable=False)
    status = Column(Enum(BoardStatus), nullable=False, default=BoardStatus.ACTIVE, index=True)
    issued_date = Column(Date, nullable=False)
    expiry_date = Column(Date, nullable=True)
    verified_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))


class TrainingRecord(GovernanceBaseEntity):
    __tablename__ = "gov_training_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    worker_id = Column(Integer, ForeignKey("gov_healthcare_workers.id"), nullable=False, index=True)
    training_name = Column(String(300), nullable=False)
    training_type = Column(String(100), nullable=False)
    provider = Column(String(200), nullable=True)
    start_date = Column(Date, nullable=True)
    end_date = Column(Date, nullable=True)
    hours = Column(Float, nullable=True)
    certificate_obtained = Column(Boolean, default=False)
    certificate_number = Column(String(100), nullable=True)
    completed = Column(Boolean, default=False)
    metadata_json = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))


class CompetencyAssessment(GovernanceBaseEntity):
    __tablename__ = "gov_competency_assessments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    worker_id = Column(Integer, ForeignKey("gov_healthcare_workers.id"), nullable=False, index=True)
    competency_name = Column(String(200), nullable=False)
    level = Column(Enum(CompetencyLevel), nullable=False, index=True)
    assessed_by = Column(String(200), nullable=True)
    assessment_date = Column(Date, nullable=False)
    next_assessment_date = Column(Date, nullable=True)
    score = Column(Float, nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))


class WorkerPrivilege(GovernanceBaseEntity):
    __tablename__ = "gov_worker_privileges"

    id = Column(Integer, primary_key=True, autoincrement=True)
    worker_id = Column(Integer, ForeignKey("gov_healthcare_workers.id"), nullable=False, index=True)
    privilege_name = Column(String(200), nullable=False)
    scope = Column(String(200), nullable=True)
    granted_by = Column(String(200), nullable=True)
    granted_date = Column(Date, nullable=False)
    expiry_date = Column(Date, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))


class RotationRecord(GovernanceBaseEntity):
    __tablename__ = "gov_rotation_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    worker_id = Column(Integer, ForeignKey("gov_healthcare_workers.id"), nullable=False, index=True)
    from_department = Column(String(200), nullable=False)
    to_department = Column(String(200), nullable=False)
    from_node_id = Column(Integer, ForeignKey("gov_hierarchy_nodes.id"), nullable=True)
    to_node_id = Column(Integer, ForeignKey("gov_hierarchy_nodes.id"), nullable=True)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=True)
    reason = Column(Text, nullable=True)
    approved_by = Column(String(200), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))


class AttendanceRecord(GovernanceBaseEntity):
    __tablename__ = "gov_attendance_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    worker_id = Column(Integer, ForeignKey("gov_healthcare_workers.id"), nullable=False, index=True)
    date = Column(Date, nullable=False, index=True)
    check_in = Column(DateTime(timezone=True), nullable=True)
    check_out = Column(DateTime(timezone=True), nullable=True)
    status = Column(String(20), nullable=False, index=True)
    notes = Column(Text, nullable=True)
    recorded_by = Column(String(200), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))


class ProductivityRecord(GovernanceBaseEntity):
    __tablename__ = "gov_productivity_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    worker_id = Column(Integer, ForeignKey("gov_healthcare_workers.id"), nullable=False, index=True)
    period = Column(Enum(ProductivityPeriod), nullable=False, index=True)
    period_start = Column(Date, nullable=False)
    period_end = Column(Date, nullable=False)
    tests_performed = Column(Integer, default=0)
    samples_processed = Column(Integer, default=0)
    reports_generated = Column(Integer, default=0)
    errors_count = Column(Integer, default=0)
    tat_average_minutes = Column(Float, nullable=True)
    quality_score = Column(Float, nullable=True)
    metrics_json = Column(JSON, nullable=True)
    national_rank = Column(Integer, nullable=True)
    governorate_rank = Column(Integer, nullable=True)
    lab_rank = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))
