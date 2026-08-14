from __future__ import annotations

from datetime import datetime

from sqlalchemy import JSON, Boolean, Column, DateTime, ForeignKey, Integer, String, Text

from app._compat import UTC, StrEnum
from app.identity.base import IdentityBaseEntity


class VerificationRecordStatus(StrEnum):
    not_started = "not_started"
    pending = "pending"
    in_progress = "in_progress"
    verified = "verified"
    failed = "failed"
    expired = "expired"
    revoked = "revoked"
    requires_review = "requires_review"


class VerificationRecordType(StrEnum):
    contact = "contact"
    identity = "identity"
    professional = "professional"
    organization = "organization"


class ProfessionalType(StrEnum):
    physician = "physician"
    dentist = "dentist"
    pharmacist = "pharmacist"
    nurse = "nurse"
    midwife = "midwife"
    medical_laboratory_scientist = "medical_laboratory_scientist"
    laboratory_technician = "laboratory_technician"
    radiology_professional = "radiology_professional"
    other_healthcare_professional = "other_healthcare_professional"


class VerificationRecord(IdentityBaseEntity):
    """Canonical, minimal verification evidence; never a raw provider payload."""

    __tablename__ = "niam_verification_records"

    uuid = Column(String(36), unique=True, nullable=False, index=True)
    account_id = Column(String(26), ForeignKey("niam_accounts.id", ondelete="CASCADE"), nullable=False, index=True)
    identity_id = Column(String(26), ForeignKey("niam_identities.id", ondelete="CASCADE"), nullable=False, index=True)

    record_type = Column(String(30), nullable=False, index=True)
    method = Column(String(50), nullable=False, index=True)
    provider = Column(String(100), nullable=False)
    status = Column(String(30), nullable=False, default=VerificationRecordStatus.not_started.value, index=True)
    assurance_level = Column(String(10), nullable=False, default="L0")

    requested_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    valid_from = Column(DateTime(timezone=True), nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    revoked_at = Column(DateTime(timezone=True), nullable=True)

    provider_reference = Column(String(255), nullable=True, index=True)
    confidence = Column(Integer, nullable=True)
    failure_reason_code = Column(String(100), nullable=True)
    verification_session_id = Column(String(64), nullable=True, unique=True, index=True)
    verified_by = Column(String(100), nullable=True)

    professional_type = Column(String(60), nullable=True, index=True)
    professional_reference = Column(String(255), nullable=True)
    verified_attributes = Column(JSON, nullable=True)
    attributes_purpose = Column(Text, nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
