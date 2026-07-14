from app.national.base import TenantAuditEntity
from app.national.enums import ReferralStatus, ReferralPriority
from sqlalchemy import JSON, Column, DateTime, Enum as SAEnum, ForeignKey, Index, String, Text


class Referral(TenantAuditEntity):
    __tablename__ = "national_referrals"

    status = Column(SAEnum(ReferralStatus), nullable=False, default=ReferralStatus.DRAFT)
    priority = Column(SAEnum(ReferralPriority), default=ReferralPriority.ROUTINE)

    patient_id = Column(String(26), ForeignKey("national_patients.id", ondelete="RESTRICT"), nullable=False, index=True)
    citizen_id = Column(String(26), ForeignKey("national_citizens.id", ondelete="RESTRICT"), nullable=True, index=True)

    referring_practitioner_id = Column(String(26), ForeignKey("national_practitioners.id", ondelete="RESTRICT"), nullable=False, index=True)
    referring_facility_id = Column(String(26), ForeignKey("national_facilities.id", ondelete="RESTRICT"), nullable=True, index=True)

    receiving_practitioner_id = Column(String(26), ForeignKey("national_practitioners.id", ondelete="RESTRICT"), nullable=True, index=True)
    receiving_facility_id = Column(String(26), ForeignKey("national_facilities.id", ondelete="RESTRICT"), nullable=True, index=True)
    receiving_department_id = Column(String(26), ForeignKey("national_departments.id", ondelete="RESTRICT"), nullable=True, index=True)

    referral_reason = Column(Text, nullable=False)
    clinical_findings = Column(Text, nullable=True)
    diagnosis_code = Column(String(50), nullable=True)
    icd10_code = Column(String(20), nullable=True)
    additional_notes = Column(Text, nullable=True)

    sent_at = Column(DateTime(timezone=True), nullable=True)
    accepted_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    cancelled_at = Column(DateTime(timezone=True), nullable=True)
    cancellation_reason = Column(Text, nullable=True)

    attachments = Column(JSON, nullable=True)
    response_notes = Column(Text, nullable=True)

    encounter_id = Column(String(26), ForeignKey("national_encounters.id", ondelete="SET NULL"), nullable=True, index=True)

    __table_args__ = (
        Index("ix_national_referrals_patient", "patient_id"),
        Index("ix_national_referrals_referring_facility", "referring_facility_id"),
        Index("ix_national_referrals_receiving_facility", "receiving_facility_id"),
        Index("ix_national_referrals_status", "status"),
        Index("ix_national_referrals_sent", "sent_at"),
        {"extend_existing": True},
    )
