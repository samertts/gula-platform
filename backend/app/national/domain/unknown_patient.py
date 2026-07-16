from sqlalchemy import Boolean, Column, DateTime, Index, SmallInteger, String, Text
from sqlalchemy import Enum as SAEnum

from app.national.base import TenantAuditEntity
from app.national.enums import Gender


class UnknownPatient(TenantAuditEntity):
    __tablename__ = "national_unknown_patients"

    emergency_health_number = Column(String(20), nullable=False, unique=True, index=True)
    encounter_id = Column(String(26), nullable=True, index=True)
    facility_id = Column(String(26), nullable=True, index=True)

    approximate_age_years = Column(SmallInteger, nullable=True)
    approximate_age_range = Column(String(20), nullable=True)
    gender = Column(SAEnum(Gender), nullable=True)

    distinguishing_features = Column(Text, nullable=True)
    clothing_description = Column(Text, nullable=True)
    found_location = Column(String(500), nullable=True)
    found_date = Column(DateTime(timezone=True), nullable=True)
    brought_in_by = Column(String(200), nullable=True)

    has_identification = Column(Boolean, default=False)
    identification_found = Column(String(500), nullable=True)

    photo_url = Column(String(500), nullable=True)
    fingerprint_hash = Column(String(255), nullable=True)

    merged_to_citizen_id = Column(String(26), nullable=True, index=True)
    merged_to_patient_id = Column(String(26), nullable=True, index=True)
    is_merged = Column(Boolean, default=False)
    merged_at = Column(DateTime(timezone=True), nullable=True)
    merge_method = Column(String(50), nullable=True)

    is_active = Column(Boolean, default=True)
    notes = Column(Text, nullable=True)

    __table_args__ = (
        Index("ix_national_unknown_emergency_hn", "emergency_health_number"),
        {"extend_existing": True},
    )

    def merge_identified(self, citizen_id: str, patient_id: str, method: str) -> None:
        self.merged_to_citizen_id = citizen_id
        self.merged_to_patient_id = patient_id
        self.is_merged = True
        self.is_active = False
        self.merge_method = method
