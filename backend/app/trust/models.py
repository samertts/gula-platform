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


def _enum(enum_cls: type, length: int) -> Enum:
    """A SQLAlchemy Enum that agrees with the column the migration actually built.

    NR-085. Every one of these columns is `character varying` in PostgreSQL --
    the database has no native enum types at all -- and every migration wrote its
    `server_default` as the Python enum's **value** (``'pending'``,
    ``'national_only'``). A bare ``Enum(SomeEnum)`` does two things that
    contradict that: it compiles to a native PostgreSQL enum type that does not
    exist, and it persists the member's **name** (``'PENDING'``), because that is
    SQLAlchemy's default and nothing here passed `values_callable`.

    So the schema's own stated default was unreadable by the model that owns the
    column. Executed against PostgreSQL 16 at head, before this change:

        INSERT ... (purpose, ...) VALUES ('TREATMENT', ...)   -- status omitted,
                                                              -- takes the default
        SELECT status ... -> LookupError: 'pending' is not among the defined
                             enum values

    and worse, a plain ``SELECT *`` over the table raised for *every* row once one
    such row existed, while ``WHERE status == ConsentStatus.PENDING`` quietly
    matched only the name-spelled half -- an undercount rather than an error.

    `native_enum=False` makes the type compile to ``VARCHAR(length)``, which is
    what the column is. `values_callable` makes it persist and read the value,
    which is what the default and the migration use. `create_constraint` stays
    False (SQLAlchemy 2.0's default), so no CHECK is added and no schema change is
    implied -- validation stays in Python, where these enums already live.
    """
    return Enum(
        enum_cls,
        native_enum=False,
        length=length,
        values_callable=lambda enum: [member.value for member in enum],
    )


class ConsentRecord(TrustBaseEntity):
    __tablename__ = "trust_consent_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False, index=True)
    lab_id = Column(Integer, ForeignKey("labs.id"), nullable=False, index=True)
    purpose = Column(_enum(ConsentPurpose, 50), nullable=False)
    status = Column(_enum(ConsentStatus, 20), nullable=False, default=ConsentStatus.PENDING)
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
    data_category = Column(_enum(DataCategory, 50), nullable=False)
    retention_period = Column(_enum(RetentionPolicy, 50), nullable=False)
    retention_days = Column(Integer, nullable=False)
    action_on_expiry = Column(String(100), nullable=False, default="anonymize")
    is_active = Column(Integer, nullable=False, default=1)
    policy_version = Column(String(20), nullable=False, default="1.0")


class SovereigntyRule(TrustBaseEntity):
    __tablename__ = "trust_sovereignty_rules"

    id = Column(Integer, primary_key=True, autoincrement=True)
    data_category = Column(_enum(DataCategory, 50), nullable=False)
    sovereignty_level = Column(_enum(SovereigntyLevel, 50), nullable=False, default=SovereigntyLevel.NATIONAL_ONLY)
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
    service_type = Column(_enum(TrustServiceType, 50), nullable=False)
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
    collected_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))
    collected_by = Column(Integer, ForeignKey("lab_users.id"), nullable=True)
    status = Column(_enum(ComplianceStatus, 50), nullable=False, default=ComplianceStatus.PENDING_REVIEW)
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
    result = Column(_enum(ComplianceStatus, 50), nullable=False)
    score = Column(Integer, nullable=True)
    details = Column(Text, nullable=True)
    checked_by = Column(Integer, ForeignKey("lab_users.id"), nullable=True)
    checked_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))
    next_check_at = Column(DateTime(timezone=True), nullable=True)
    corrective_action_id = Column(String(128), nullable=True)
