from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import (
    JSON,
    Boolean,
    CheckConstraint,
    Column,
    DateTime,
    Integer,
    String,
    UniqueConstraint,
)

from app.database import Base


def _id() -> str:
    return uuid.uuid4().hex.upper()[:26]


def _now() -> datetime:
    return datetime.now(UTC)


class CoreLabTestCatalog(Base):
    __tablename__ = "core_lab_test_catalog"
    id = Column(String(26), primary_key=True, default=_id)
    laboratory_id = Column(String(26), nullable=False, index=True)
    organization_id = Column(String(26), nullable=False, index=True)
    facility_id = Column(String(26), nullable=False, index=True)
    canonical_code = Column(String(120), nullable=False)
    local_code = Column(String(120), nullable=True)
    name = Column(String(240), nullable=False)
    system = Column(String(120), nullable=False)
    specimen_type = Column(String(80), nullable=False)
    unit_ucum = Column(String(80), nullable=True)
    method = Column(String(160), nullable=True)
    reference_range = Column(JSON, nullable=False, default=dict)
    critical_range = Column(JSON, nullable=False, default=dict)
    active = Column(Boolean, nullable=False, default=True)
    version = Column(Integer, nullable=False, default=1)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_now)
    __table_args__ = (UniqueConstraint("facility_id", "canonical_code", "version", name="uq_core_lab_test_catalog_version"), CheckConstraint("version > 0", name="ck_core_lab_test_catalog_version"))


class CoreLabAnalyzer(Base):
    __tablename__ = "core_lab_analyzers"
    id = Column(String(26), primary_key=True, default=_id)
    laboratory_id = Column(String(26), nullable=False, index=True)
    organization_id = Column(String(26), nullable=False, index=True)
    facility_id = Column(String(26), nullable=False, index=True)
    section = Column(String(120), nullable=False)
    manufacturer = Column(String(160), nullable=False)
    model = Column(String(160), nullable=False)
    serial_fingerprint = Column(String(128), nullable=False)
    protocol = Column(String(32), nullable=False)
    status = Column(String(24), nullable=False, default="REGISTERED", index=True)
    configuration_version = Column(Integer, nullable=False, default=1)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_now)
    __table_args__ = (UniqueConstraint("facility_id", "serial_fingerprint", name="uq_core_lab_analyzer_serial"), CheckConstraint("status IN ('REGISTERED','VALIDATED','ACTIVE','MAINTENANCE','QUARANTINED','RETIRED')", name="ck_core_lab_analyzer_status"), CheckConstraint("protocol IN ('ASTM','HL7_V2','FHIR','FILE','SYNTHETIC')", name="ck_core_lab_analyzer_protocol"))


class CoreLabAnalyzerMessage(Base):
    __tablename__ = "core_lab_analyzer_messages"
    id = Column(String(26), primary_key=True, default=_id)
    message_id = Column(String(160), nullable=False, unique=True, index=True)
    analyzer_id = Column(String(26), nullable=False, index=True)
    lab_order_id = Column(String(26), nullable=False, index=True)
    specimen_id = Column(String(26), nullable=False, index=True)
    patient_person_id = Column(String(26), nullable=False, index=True)
    test_code = Column(String(120), nullable=False)
    payload_hash = Column(String(64), nullable=False)
    quality_flags = Column(JSON, nullable=False, default=dict)
    status = Column(String(24), nullable=False, default="RECEIVED", index=True)
    source = Column(String(32), nullable=False, default="SYNTHETIC")
    occurred_at = Column(DateTime(timezone=True), nullable=False, default=_now)
    received_at = Column(DateTime(timezone=True), nullable=False, default=_now)
    __table_args__ = (CheckConstraint("status IN ('RECEIVED','VALIDATED','REJECTED','DUPLICATE')", name="ck_core_lab_analyzer_message_status"), CheckConstraint("source IN ('SYNTHETIC','HL7_V2','ASTM','FHIR','FILE')", name="ck_core_lab_analyzer_message_source"))


class CoreLabQualityControl(Base):
    __tablename__ = "core_lab_quality_controls"
    id = Column(String(26), primary_key=True, default=_id)
    result_id = Column(String(26), nullable=False, index=True)
    analyzer_id = Column(String(26), nullable=True, index=True)
    organization_id = Column(String(26), nullable=False, index=True)
    facility_id = Column(String(26), nullable=False, index=True)
    workspace_id = Column(String(26), nullable=False, index=True)
    status = Column(String(24), nullable=False, default="PENDING")
    reason = Column(String(500), nullable=True)
    override_reason = Column(String(500), nullable=True)
    performed_by_account_id = Column(String(26), nullable=False)
    version = Column(Integer, nullable=False, default=1)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_now)
    __table_args__ = (UniqueConstraint("result_id", name="uq_core_lab_qc_result"), CheckConstraint("status IN ('PENDING','PASS','FAILED','OVERRIDDEN')", name="ck_core_lab_qc_status"), CheckConstraint("version > 0", name="ck_core_lab_qc_version"))
