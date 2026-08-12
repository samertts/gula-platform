from datetime import datetime

from sqlalchemy import Boolean, Column, Date, DateTime, ForeignKey, Index, Integer, String, Text

from app._compat import UTC
from app.ehr.base import EHRBaseEntity


class ImmunizationRecord(EHRBaseEntity):
    __tablename__ = "ehr_immunizations"

    patient_id = Column(String(26), ForeignKey("national_patients.id", ondelete="CASCADE"), nullable=False, index=True)
    citizen_id = Column(String(26), ForeignKey("national_citizens.id", ondelete="RESTRICT"), nullable=True, index=True)
    encounter_id = Column(String(26), ForeignKey("national_encounters.id", ondelete="SET NULL"), nullable=True, index=True)
    practitioner_id = Column(String(26), ForeignKey("national_practitioners.id", ondelete="SET NULL"), nullable=True, index=True)
    administrator_id = Column(String(26), ForeignKey("national_practitioners.id", ondelete="SET NULL"), nullable=True, index=True)

    vaccine_code = Column(String(50), nullable=False, index=True)
    vaccine_code_system = Column(String(20), nullable=True)
    vaccine_name = Column(String(300), nullable=False)
    vaccine_name_ar = Column(String(300), nullable=True)

    administration_date = Column(DateTime(timezone=True), nullable=False)
    recorded_date = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=True)

    manufacturer = Column(String(200), nullable=True)
    lot_number = Column(String(100), nullable=True, index=True)
    expiry_date = Column(Date, nullable=True)

    dose_number = Column(Integer, nullable=True)
    dose_series = Column(String(50), nullable=True)
    total_doses = Column(Integer, nullable=True)

    route = Column(String(100), nullable=True)
    site = Column(String(100), nullable=True)
    dose_quantity = Column(String(50), nullable=True)
    dose_unit = Column(String(50), nullable=True)

    is_completed = Column(Boolean, default=True)
    status = Column(String(50), nullable=False, default="completed")
    reason_not_given = Column(String(500), nullable=True)

    adverse_event = Column(Text, nullable=True)
    adverse_event_reported = Column(Boolean, default=False)

    facility_id = Column(String(26), ForeignKey("national_facilities.id", ondelete="SET NULL"), nullable=True, index=True)
    notes = Column(Text, nullable=True)
    metadata_ = Column("metadata", Text, nullable=True)

    __table_args__ = (
        Index("ix_ehr_immunization_patient", "patient_id"),
        Index("ix_ehr_immunization_citizen", "citizen_id"),
        Index("ix_ehr_immunization_vaccine", "vaccine_code"),
        Index("ix_ehr_immunization_date", "administration_date"),
        Index("ix_ehr_immunization_lot", "lot_number"),
        Index("ix_ehr_immunization_facility", "facility_id"),
        Index("ix_ehr_immunization_not_deleted", "is_deleted", "patient_id"),
        {"extend_existing": True},
    )
