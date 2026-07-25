"""Trust platform ORM models."""

from datetime import datetime

from sqlalchemy import Column, DateTime, Enum, ForeignKey, Integer, String, Text

from app._compat import UTC
from app.trust.base import TrustBaseEntity
from app.trust.enums import (
    ComplianceStatus,
    ConsentPurpose,
    ConsentStatus,
    DataCategory,
    RetentionPolicy,
    SovereigntyLevel,
    TrustServiceType,
)


class ConsentRecord(TrustBaseEntity):
    __tablename__ = "trust_consent_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False, index=True)
    lab_id = Column(Integer, ForeignKey("labs.id"), nullable=False, index=True)
    purpose = Column(Enum(ConsentPurpose), nullable=False)
    status = Column(Enum(ConsentStatus), nullable=False, default=ConsentStatus.PENDING)
    granted_at = Column(DateTime(timezone=True), nullable=True)
    withdrawn_at = Column(DateTime(timezone=True), nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    data_categories = Column(String(500), nullable=True)
    guardian_id = Column(Integer, ForeignKey("lab_users.id"), nullable=True)
    consent_hash = Column(String(128), nullable=False)
    consent_version = Column(String(20), nullable=False, default="1.0")
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(500), nullable=True)


class DataRetentionPolicy(TrustBaseEntity):
    __tablename__ = "trust_retention_policies"

    id = Column(Integer, primary_key=True, autoincrement=True)
    data_category = Column(Enum(DataCategory), nullable=False)
    retention_period = Column(Enum(RetentionPolicy), nullable=False)
    retention_days = Column(Integer, nullable=False)
    action_on_expiry = Column(String(100), nullable=False, default="anonymize")
    is_active = Column(Integer, nullable=False, default=1)
    policy_version = Column(String(20), nullable=False, default="1.0")


class SovereigntyRule(TrustBaseEntity):
    __tablename__ = "trust_sovereignty_rules"

    id = Column(Integer, primary_key=True, autoincrement=True)
    data_category = Column(Enum(DataCategory), nullable=False)
    sovereignty_level = Column(
        Enum(SovereigntyLevel), nullable=False, default=SovereigntyLevel.NATIONAL_ONLY
    )
    allows_cross_border = Column(Integer, nullable=False, default=0)
    requires_encryption = Column(Integer, nullable=False, default=1)
    requires_consent = Column(Integer, nullable=False, default=1)
    encryption_algorithm = Column(String(100), nullable=False, default="AES-256-GCM")
    key_ownership = Column(String(100), nullable=False, default="national")
    data_residency = Column(String(200), nullable=False, default="IRQ")
    rule_version = Column(String(20), nullable=False, default="1.0")


class TrustServiceLog(TrustBaseEntity):
    __tablename__ = "trust_service_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    service_type = Column(Enum(TrustServiceType), nullable=False)
    request_id = Column(String(64), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("lab_users.id"), nullable=True)
    lab_id = Column(Integer, ForeignKey("labs.id"), nullable=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=True)
    document_hash = Column(String(128), nullable=True)
    signature_value = Column(Text, nullable=True)
    certificate_serial = Column(String(128), nullable=True)
    timestamp_token = Column(Text, nullable=True)
    status = Column(String(50), nullable=False, default="completed")
    result_hash = Column(String(128), nullable=True)
    metadata_json = Column(Text, nullable=True)


class ComplianceEvidence(TrustBaseEntity):
    __tablename__ = "trust_compliance_evidence"

    id = Column(Integer, primary_key=True, autoincrement=True)
    evidence_type = Column(String(100), nullable=False)
    evidence_id = Column(String(128), nullable=False, unique=True)
    source = Column(String(200), nullable=False)
    collected_at = Column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC)
    )
    collected_by = Column(Integer, ForeignKey("lab_users.id"), nullable=True)
    status = Column(Enum(ComplianceStatus), nullable=False, default=ComplianceStatus.PENDING_REVIEW)
    evidence_hash = Column(String(128), nullable=False)
    evidence_data = Column(Text, nullable=True)
    retention_until = Column(DateTime(timezone=True), nullable=True)
    chain_of_custody = Column(Text, nullable=True)


class ComplianceCheck(TrustBaseEntity):
    __tablename__ = "trust_compliance_checks"

    id = Column(Integer, primary_key=True, autoincrement=True)
    check_type = Column(String(100), nullable=False)
    check_name = Column(String(200), nullable=False)
    target_id = Column(String(128), nullable=True)
    target_type = Column(String(50), nullable=True)
    result = Column(Enum(ComplianceStatus), nullable=False)
    score = Column(Integer, nullable=True)
    details = Column(Text, nullable=True)
    checked_by = Column(Integer, ForeignKey("lab_users.id"), nullable=True)
    checked_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))
    next_check_at = Column(DateTime(timezone=True), nullable=True)
    corrective_action_id = Column(String(128), nullable=True)
