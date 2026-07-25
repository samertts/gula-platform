from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy import Enum as SAEnum

from app._compat import UTC
from app.national.base import TenantAuditEntity
from app.national.enums import ConsentScope, ConsentStatus


class Consent(TenantAuditEntity):
    __tablename__ = "national_consents"

    status = Column(SAEnum(ConsentStatus), nullable=False, default=ConsentStatus.ACTIVE)
    scope = Column(SAEnum(ConsentScope), nullable=False)

    patient_id = Column(
        String(26),
        ForeignKey("national_patients.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    citizen_id = Column(
        String(26),
        ForeignKey("national_citizens.id", ondelete="RESTRICT"),
        nullable=True,
        index=True,
    )

    grantee_id = Column(String(26), nullable=False, index=True)
    grantee_type = Column(String(50), nullable=False)
    granted_by_user_id = Column(String(26), nullable=True)

    granted_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    revoked_at = Column(DateTime(timezone=True), nullable=True)
    revoked_by = Column(String(26), nullable=True)
    revocation_reason = Column(Text, nullable=True)

    purpose = Column(String(200), nullable=True)
    policy_text = Column(Text, nullable=True)
    consent_to_all = Column(Boolean, default=False)

    is_emergency_consent = Column(Boolean, default=False)
    emergency_reason = Column(Text, nullable=True)

    is_active = Column(Boolean, default=True)
    version = Column(Integer, default=1, nullable=False)

    __table_args__ = (
        Index("ix_national_consents_patient", "patient_id"),
        Index("ix_national_consents_grantee", "grantee_id"),
        Index("ix_national_consents_scope", "scope"),
        {"extend_existing": True},
    )
