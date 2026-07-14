from app.national.base import TenantAuditEntity
from app.national.enums import DischargeType
from sqlalchemy import Boolean, Column, DateTime, Enum as SAEnum, ForeignKey, Index, String, Text


class Discharge(TenantAuditEntity):
    __tablename__ = "national_discharges"

    discharge_type = Column(SAEnum(DischargeType), nullable=False)

    patient_id = Column(String(26), ForeignKey("national_patients.id", ondelete="RESTRICT"), nullable=False, index=True)
    admission_id = Column(String(26), ForeignKey("national_admissions.id", ondelete="RESTRICT"), nullable=False, index=True)
    encounter_id = Column(String(26), ForeignKey("national_encounters.id", ondelete="SET NULL"), nullable=True, index=True)

    hospital_id = Column(String(26), ForeignKey("national_hospitals.id", ondelete="RESTRICT"), nullable=False, index=True)
    facility_id = Column(String(26), ForeignKey("national_facilities.id", ondelete="RESTRICT"), nullable=True, index=True)

    discharging_practitioner_id = Column(String(26), ForeignKey("national_practitioners.id", ondelete="RESTRICT"), nullable=True, index=True)
    discharge_date = Column(DateTime(timezone=True), nullable=False)

    discharge_summary = Column(Text, nullable=True)
    follow_up_instructions = Column(Text, nullable=True)
    medications_prescribed = Column(Text, nullable=True)
    follow_up_appointment_id = Column(String(26), nullable=True)

    transfer_to_facility_id = Column(String(26), nullable=True)
    transferred = Column(Boolean, default=False)

    notes = Column(Text, nullable=True)

    __table_args__ = (
        Index("ix_national_discharges_patient", "patient_id"),
        Index("ix_national_discharges_admission", "admission_id"),
        Index("ix_national_discharges_hospital", "hospital_id"),
        {"extend_existing": True},
    )
