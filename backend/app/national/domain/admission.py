from app.national.base import TenantAuditEntity
from app.national.enums import AdmissionStatus
from sqlalchemy import Boolean, Column, DateTime, Enum as SAEnum, ForeignKey, Index, String, Text


class Admission(TenantAuditEntity):
    __tablename__ = "national_admissions"

    status = Column(SAEnum(AdmissionStatus), nullable=False, default=AdmissionStatus.PENDING)

    patient_id = Column(String(26), ForeignKey("national_patients.id", ondelete="RESTRICT"), nullable=False, index=True)
    encounter_id = Column(String(26), ForeignKey("national_encounters.id", ondelete="SET NULL"), nullable=True, index=True)

    hospital_id = Column(String(26), ForeignKey("national_hospitals.id", ondelete="RESTRICT"), nullable=False, index=True)
    facility_id = Column(String(26), ForeignKey("national_facilities.id", ondelete="RESTRICT"), nullable=True, index=True)
    ward_id = Column(String(26), ForeignKey("national_wards.id", ondelete="RESTRICT"), nullable=True, index=True)
    room_number = Column(String(20), nullable=True)
    bed_number = Column(String(20), nullable=True)

    admitting_practitioner_id = Column(String(26), ForeignKey("national_practitioners.id", ondelete="RESTRICT"), nullable=True, index=True)
    admission_date = Column(DateTime(timezone=True), nullable=False)
    admission_reason = Column(Text, nullable=True)
    admission_type = Column(String(50), nullable=True)
    referral_id = Column(String(26), ForeignKey("national_referrals.id", ondelete="SET NULL"), nullable=True, index=True)

    expected_discharge_date = Column(DateTime(timezone=True), nullable=True)
    notes = Column(Text, nullable=True)
    is_emergency_admission = Column(Boolean, default=False)

    __table_args__ = (
        Index("ix_national_admissions_patient", "patient_id"),
        Index("ix_national_admissions_hospital", "hospital_id"),
        Index("ix_national_admissions_ward", "ward_id"),
        Index("ix_national_admissions_date", "admission_date"),
        {"extend_existing": True},
    )
