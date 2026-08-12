from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy import Enum as SAEnum

from app.national.base import TenantAuditEntity
from app.national.enums import VisitStatus, VisitType


class Visit(TenantAuditEntity):
    __tablename__ = "national_visits"

    visit_type = Column(SAEnum(VisitType), nullable=False)
    status = Column(SAEnum(VisitStatus), nullable=False, default=VisitStatus.PENDING)

    patient_id = Column(String(26), ForeignKey("national_patients.id", ondelete="RESTRICT"), nullable=False, index=True)
    citizen_id = Column(String(26), ForeignKey("national_citizens.id", ondelete="RESTRICT"), nullable=True, index=True)
    encounter_id = Column(String(26), ForeignKey("national_encounters.id", ondelete="SET NULL"), nullable=True, index=True)

    facility_id = Column(String(26), ForeignKey("national_facilities.id", ondelete="RESTRICT"), nullable=True, index=True)
    department_id = Column(String(26), ForeignKey("national_departments.id", ondelete="RESTRICT"), nullable=True, index=True)

    practitioner_id = Column(String(26), ForeignKey("national_practitioners.id", ondelete="RESTRICT"), nullable=True, index=True)

    scheduled_date = Column(DateTime(timezone=True), nullable=True)
    check_in_time = Column(DateTime(timezone=True), nullable=True)
    check_out_time = Column(DateTime(timezone=True), nullable=True)
    duration_minutes = Column(Integer, nullable=True)

    reason = Column(String(500), nullable=True)
    notes = Column(Text, nullable=True)
    is_emergency = Column(Boolean, default=False)
    is_telehealth = Column(Boolean, default=False)

    __table_args__ = (
        Index("ix_national_visits_patient", "patient_id"),
        Index("ix_national_visits_facility", "facility_id"),
        Index("ix_national_visits_scheduled", "scheduled_date"),
        Index("ix_national_visits_status", "status"),
        {"extend_existing": True},
    )
