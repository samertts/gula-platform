from sqlalchemy import Boolean, Column, Date, ForeignKey, Index, Integer, String, Text

from app.national_data.base import BaseEntity


class ConsentDirective(BaseEntity):
    __tablename__ = "dp_consent_directives"

    consent_id = Column(Integer, ForeignKey("consents.id", ondelete="SET NULL"), nullable=True)
    patient_id = Column(Integer, ForeignKey("patients.id", ondelete="SET NULL"), nullable=True, index=True)
    citizen_id = Column(String(26), nullable=True, index=True)

    consent_type = Column(String(50), nullable=False)
    consent_status = Column(String(20), default="active", nullable=False)

    data_use_purpose = Column(String(100), nullable=False)
    data_categories = Column(String(500), nullable=True)
    authorized_party = Column(String(200), nullable=True)

    granted_at = Column(Date, nullable=False)
    expires_at = Column(Date, nullable=True)
    revoked_at = Column(Date, nullable=True)
    revocation_reason = Column(Text, nullable=True)

    is_active = Column(Boolean, default=True, nullable=False)
    jurisdiction = Column(String(100), nullable=True)

    __table_args__ = (
        Index("ix_dp_consent_patient", "patient_id"),
        Index("ix_dp_consent_type", "consent_type", "consent_status"),
        {"extend_existing": True},
    )
