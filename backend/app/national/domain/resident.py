from app.national.base import TenantAuditEntity
from app.national.enums import Gender, MaritalStatus
from sqlalchemy import Boolean, Column, Date, Enum as SAEnum, Index, String, Text


class Resident(TenantAuditEntity):
    __tablename__ = "national_residents"

    original_nationality = Column(String(100), nullable=False)
    residence_permit_number = Column(String(50), nullable=False, index=True)
    residence_permit_expiry = Column(Date, nullable=True)
    residence_permit_type = Column(String(50), nullable=True)

    health_number = Column(String(20), nullable=False, unique=True, index=True)

    first_name = Column(String(100), nullable=False)
    father_name = Column(String(100), nullable=True)
    last_name = Column(String(100), nullable=False)
    full_name_ar = Column(String(400), nullable=True)
    full_name_native = Column(String(400), nullable=True)

    date_of_birth = Column(Date, nullable=False)
    gender = Column(SAEnum(Gender), nullable=False)
    marital_status = Column(SAEnum(MaritalStatus), default=MaritalStatus.UNKNOWN)

    phone = Column(String(20), nullable=True)
    email = Column(String(255), nullable=True)

    address_line = Column(String(500), nullable=True)
    city = Column(String(100), nullable=True)
    governorate = Column(String(100), nullable=True)

    has_biometrics = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)

    sponsor_name = Column(String(200), nullable=True)
    sponsor_id = Column(String(50), nullable=True)

    converted_to_citizen_id = Column(String(26), nullable=True)
    is_converted = Column(Boolean, default=False)

    notes = Column(Text, nullable=True)

    __table_args__ = (
        Index("ix_national_residents_permit", "residence_permit_number"),
        {"extend_existing": True},
    )
