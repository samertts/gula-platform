from sqlalchemy import JSON, Boolean, Column, DateTime, ForeignKey, Index, Integer, String, Text

from app.national.base import TenantAuditEntity


class Observation(TenantAuditEntity):
    __tablename__ = "national_observations"

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
    encounter_id = Column(
        String(26),
        ForeignKey("national_encounters.id", ondelete="RESTRICT"),
        nullable=True,
        index=True,
    )
    practitioner_id = Column(
        String(26),
        ForeignKey("national_practitioners.id", ondelete="RESTRICT"),
        nullable=True,
        index=True,
    )

    category = Column(String(50), nullable=True)
    code = Column(String(50), nullable=False)
    code_system = Column(String(50), nullable=True)
    code_display = Column(String(200), nullable=True)
    code_display_ar = Column(String(200), nullable=True)

    value_quantity = Column(String(100), nullable=True)
    value_text = Column(Text, nullable=True)
    value_boolean = Column(Boolean, nullable=True)
    value_integer = Column(Integer, nullable=True)
    value_range_low = Column(String(50), nullable=True)
    value_range_high = Column(String(50), nullable=True)
    unit = Column(String(50), nullable=True)
    data_absent_reason = Column(String(100), nullable=True)

    interpretation = Column(String(50), nullable=True)
    reference_range_low = Column(String(50), nullable=True)
    reference_range_high = Column(String(50), nullable=True)
    reference_range_text = Column(String(500), nullable=True)

    status = Column(String(20), default="final")
    effective_datetime = Column(DateTime(timezone=True), nullable=True)
    issued_at = Column(DateTime(timezone=True), nullable=True)

    body_site = Column(String(100), nullable=True)
    method = Column(String(100), nullable=True)
    device_id = Column(String(26), nullable=True)
    notes = Column(Text, nullable=True)
    metadata_ = Column("metadata", JSON, nullable=True)

    __table_args__ = (
        Index("ix_national_observations_patient", "patient_id"),
        Index("ix_national_observations_citizen", "citizen_id"),
        Index("ix_national_observations_encounter", "encounter_id"),
        Index("ix_national_observations_code", "code"),
        Index("ix_national_observations_status", "status"),
        Index("ix_national_observations_effective", "effective_datetime"),
        {"extend_existing": True},
    )
