from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Index, Integer, JSON, String, Text
from sqlalchemy import Enum as SAEnum

from app.national.base import TenantAuditEntity
from app.national.enums import EncounterStatus, EncounterType


class Encounter(TenantAuditEntity):
    __tablename__ = "national_encounters"

    encounter_type = Column(SAEnum(EncounterType), nullable=False)
    status = Column(SAEnum(EncounterStatus), nullable=False, default=EncounterStatus.PLANNED)
    # Operational flow state is intentionally separate from the FHIR status. It
    # captures the short, high-throughput government-hospital workflow without
    # overloading FHIR's broader lifecycle semantics.
    flow_state = Column(String(30), nullable=False, default="planned")
    hospital_id = Column(Integer, nullable=True, index=True)
    idempotency_key = Column(String(64), nullable=True, index=True)
    arrival_at = Column(DateTime(timezone=True), nullable=True)
    triage_at = Column(DateTime(timezone=True), nullable=True)
    admission_at = Column(DateTime(timezone=True), nullable=True)
    discharge_at = Column(DateTime(timezone=True), nullable=True)

    patient_id = Column(String(26), ForeignKey("national_patients.id", ondelete="RESTRICT"), nullable=False, index=True)
    citizen_id = Column(String(26), ForeignKey("national_citizens.id", ondelete="RESTRICT"), nullable=True, index=True)

    organization_id = Column(String(26), ForeignKey("national_organizations.id", ondelete="RESTRICT"), nullable=True, index=True)
    facility_id = Column(String(26), ForeignKey("national_facilities.id", ondelete="RESTRICT"), nullable=True, index=True)
    department_id = Column(String(26), ForeignKey("national_departments.id", ondelete="RESTRICT"), nullable=True, index=True)

    practitioner_id = Column(String(26), ForeignKey("national_practitioners.id", ondelete="RESTRICT"), nullable=True, index=True)
    referral_id = Column(String(26), ForeignKey("national_referrals.id", ondelete="SET NULL"), nullable=True, index=True)

    period_start = Column(DateTime(timezone=True), nullable=False)
    period_end = Column(DateTime(timezone=True), nullable=True)
    duration_minutes = Column(Integer, nullable=True)

    reason_code = Column(String(50), nullable=True)
    reason_description = Column(Text, nullable=True)
    diagnosis_code = Column(String(50), nullable=True)
    diagnosis_description = Column(Text, nullable=True)
    icd10_code = Column(String(20), nullable=True)

    priority = Column(String(20), default="routine")
    is_emergency = Column(Boolean, default=False)

    disposition = Column(String(200), nullable=True)
    notes = Column(Text, nullable=True)
    metadata_ = Column("metadata", JSON, nullable=True)

    __table_args__ = (
        Index("ix_national_encounters_patient", "patient_id"),
        Index("ix_national_encounters_citizen", "citizen_id"),
        Index("ix_national_encounters_facility", "facility_id"),
        Index("ix_national_encounters_period", "period_start"),
        Index("ix_national_encounters_status", "status"),
        Index("ix_national_encounters_flow_state", "flow_state"),
        {"extend_existing": True},
    )
