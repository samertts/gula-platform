from app.national.base import AuditEntity
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Index, String, Text


class DeathRecord(AuditEntity):
    __tablename__ = "national_death_records"

    citizen_id = Column(String(26), ForeignKey("national_citizens.id", ondelete="RESTRICT"), nullable=False, index=True)
    deceased_name = Column(String(200), nullable=False)
    national_id_hash = Column(String(255), nullable=True)
    health_number = Column(String(20), nullable=True, index=True)

    date_of_death = Column(DateTime(timezone=True), nullable=False)
    place_of_death = Column(String(200), nullable=True)
    cause_of_death = Column(Text, nullable=True)
    icd10_code = Column(String(20), nullable=True)

    death_certificate_number = Column(String(50), nullable=False, unique=True, index=True)
    death_certificate_issuer = Column(String(200), nullable=True)
    death_certificate_issued_at = Column(DateTime(timezone=True), nullable=True)

    attending_practitioner_id = Column(String(26), ForeignKey("national_practitioners.id", ondelete="RESTRICT"), nullable=True, index=True)
    attending_practitioner_name = Column(String(200), nullable=True)

    is_verified = Column(Boolean, default=False)
    verified_by = Column(String(26), nullable=True)
    verified_at = Column(DateTime(timezone=True), nullable=True)

    is_natural_cause = Column(Boolean, default=True)
    autopsy_required = Column(Boolean, default=False)
    autopsy_result = Column(Text, nullable=True)

    notification_to_family = Column(Boolean, default=False)
    family_notified_at = Column(DateTime(timezone=True), nullable=True)

    notes = Column(Text, nullable=True)

    __table_args__ = (
        Index("ix_national_death_records_citizen", "citizen_id"),
        Index("ix_national_death_records_certificate", "death_certificate_number"),
        Index("ix_national_death_records_date", "date_of_death"),
        {"extend_existing": True},
    )
