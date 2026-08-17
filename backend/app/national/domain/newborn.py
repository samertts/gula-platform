from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Index,
    SmallInteger,
    String,
    Text,
)
from app.national.base import TenantAuditEntity


class Newborn(TenantAuditEntity):
    __tablename__ = "national_newborns"

    birth_certificate_number = Column(String(50), nullable=False, index=True)
    hospital_registration_number = Column(String(50), nullable=True, index=True)
    temporary_health_number = Column(String(20), nullable=True, unique=True, index=True)

    first_name = Column(String(100), nullable=True)
    father_name = Column(String(100), nullable=True)
    last_name = Column(String(100), nullable=True)

    date_of_birth = Column(Date, nullable=False)
    birth_time = Column(DateTime(timezone=True), nullable=True)
    gender = Column(String(20), nullable=False)

    birth_weight_grams = Column(SmallInteger, nullable=True)
    birth_length_cm = Column(SmallInteger, nullable=True)
    birth_place = Column(String(200), nullable=True)
    birth_place_type = Column(String(50), nullable=True)
    delivery_method = Column(String(50), nullable=True)

    mother_id = Column(String(26), ForeignKey("national_citizens.id", ondelete="RESTRICT"), nullable=False, index=True)
    mother_name = Column(String(200), nullable=True)
    father_id = Column(String(26), ForeignKey("national_citizens.id", ondelete="RESTRICT"), nullable=True, index=True)

    guardian_id = Column(String(26), ForeignKey("national_guardians.id", ondelete="RESTRICT"), nullable=True, index=True)
    family_id = Column(String(26), ForeignKey("national_families.id", ondelete="RESTRICT"), nullable=True, index=True)

    converted_to_citizen_id = Column(String(26), ForeignKey("national_citizens.id", ondelete="SET NULL"), nullable=True)
    converted_at = Column(DateTime(timezone=True), nullable=True)
    is_converted = Column(Boolean, default=False)

    registered_by_hospital = Column(Boolean, default=True)
    registration_days_after_birth = Column(SmallInteger, nullable=True)

    citizen_id = Column(String(26), ForeignKey("national_citizens.id", ondelete="RESTRICT"), nullable=True)
    notes = Column(Text, nullable=True)

    __table_args__ = (
        Index("ix_national_newborns_mother", "mother_id"),
        Index("ix_national_newborns_father", "father_id"),
        Index("ix_national_newborns_birth_cert", "birth_certificate_number"),
        Index("ix_national_newborns_converted", "converted_to_citizen_id"),
        {"extend_existing": True},
    )
