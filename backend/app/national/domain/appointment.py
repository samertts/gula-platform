from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy import Enum as SAEnum

from app.national.base import TenantAuditEntity
from app.national.enums import AppointmentStatus


class Appointment(TenantAuditEntity):
    __tablename__ = "national_appointments"

    status = Column(SAEnum(AppointmentStatus), nullable=False, default=AppointmentStatus.PENDING)

    patient_id = Column(String(26), ForeignKey("national_patients.id", ondelete="RESTRICT"), nullable=False, index=True)
    citizen_id = Column(String(26), ForeignKey("national_citizens.id", ondelete="RESTRICT"), nullable=True, index=True)

    practitioner_id = Column(String(26), ForeignKey("national_practitioners.id", ondelete="RESTRICT"), nullable=True, index=True)
    facility_id = Column(String(26), ForeignKey("national_facilities.id", ondelete="RESTRICT"), nullable=True, index=True)
    # The national facility registry and the hospital operations registry use
    # different identifiers. Keep the local hospital scope explicit.
    hospital_id = Column(Integer, nullable=True, index=True)
    department_id = Column(String(26), ForeignKey("national_departments.id", ondelete="RESTRICT"), nullable=True, index=True)

    appointment_type = Column(String(50), nullable=False)
    scheduled_date = Column(DateTime(timezone=True), nullable=False)
    duration_minutes = Column(Integer, default=30)

    reason = Column(String(500), nullable=True)
    notes = Column(Text, nullable=True)
    is_telehealth = Column(Boolean, default=False)
    is_emergency = Column(Boolean, default=False)

    cancellation_reason = Column(String(500), nullable=True)
    no_show = Column(Boolean, default=False)
    idempotency_key = Column(String(64), nullable=True, index=True)

    __table_args__ = (
        Index("ix_national_appointments_patient", "patient_id"),
        Index("ix_national_appointments_practitioner", "practitioner_id"),
        Index("ix_national_appointments_scheduled", "scheduled_date"),
        Index("ix_national_appointments_status", "status"),
        Index("ix_national_appointments_facility_date", "facility_id", "scheduled_date"),
        Index("ix_national_appointments_hospital_date", "hospital_id", "scheduled_date"),
        UniqueConstraint(
            "lab_id", "hospital_id", "idempotency_key",
            name="uq_national_appointments_hospital_idempotency",
        ),
        {"extend_existing": True},
    )
