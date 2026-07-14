from app.national.base import TenantAuditEntity
from app.national.enums import Gender, MaritalStatus
from sqlalchemy import Boolean, Column, Date, Enum as SAEnum, Index, String, Text


class Foreigner(TenantAuditEntity):
    __tablename__ = "national_foreigners"

    passport_number = Column(String(50), nullable=False, index=True)
    passport_country = Column(String(100), nullable=False)
    passport_expiry = Column(Date, nullable=True)
    visa_number = Column(String(50), nullable=True, index=True)
    visa_type = Column(String(50), nullable=True)
    visa_expiry = Column(Date, nullable=True)
    residence_card_number = Column(String(50), nullable=True, index=True)
    residence_card_expiry = Column(Date, nullable=True)

    temporary_health_number = Column(String(20), nullable=True, unique=True, index=True)
    permanent_health_number = Column(String(20), nullable=True, unique=True, index=True)

    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    full_name_native = Column(String(400), nullable=True)

    date_of_birth = Column(Date, nullable=False)
    gender = Column(SAEnum(Gender), nullable=False)
    marital_status = Column(SAEnum(MaritalStatus), default=MaritalStatus.UNKNOWN)

    nationality = Column(String(100), nullable=False)
    language = Column(String(10), default="en")

    phone = Column(String(20), nullable=True)
    email = Column(String(255), nullable=True)

    address_line = Column(String(500), nullable=True)
    city = Column(String(100), nullable=True)
    governorate = Column(String(100), nullable=True)

    has_biometrics = Column(Boolean, default=False)
    is_permanent_registration = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)

    sponsor_name = Column(String(200), nullable=True)
    sponsor_id = Column(String(50), nullable=True)
    employer = Column(String(200), nullable=True)

    converted_to_citizen_id = Column(String(26), nullable=True)
    is_converted = Column(Boolean, default=False)

    notes = Column(Text, nullable=True)

    __table_args__ = (
        Index("ix_national_foreigners_passport", "passport_number", "passport_country"),
        Index("ix_national_foreigners_visa", "visa_number"),
        Index("ix_national_foreigners_residence", "residence_card_number"),
        {"extend_existing": True},
    )
