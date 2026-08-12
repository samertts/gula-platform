from sqlalchemy import Boolean, Column, Date, DateTime, Index, String, Text
from sqlalchemy import Enum as SAEnum

from app.national.base import TenantAuditEntity
from app.national.enums import Gender


class Visitor(TenantAuditEntity):
    __tablename__ = "national_visitors"

    passport_number = Column(String(50), nullable=False, index=True)
    passport_country = Column(String(100), nullable=False)
    visa_number = Column(String(50), nullable=True, index=True)
    visa_type = Column(String(50), nullable=True)
    visa_expiry = Column(Date, nullable=True)

    temporary_health_number = Column(String(20), nullable=True, unique=True, index=True)

    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)

    date_of_birth = Column(Date, nullable=False)
    gender = Column(SAEnum(Gender), nullable=False)
    nationality = Column(String(100), nullable=False)

    phone = Column(String(20), nullable=True)
    email = Column(String(255), nullable=True)

    address_line = Column(String(500), nullable=True)
    city = Column(String(100), nullable=True)
    country = Column(String(100), nullable=True)

    entry_date = Column(DateTime(timezone=True), nullable=True)
    expected_exit_date = Column(Date, nullable=True)
    purpose_of_visit = Column(String(200), nullable=True)

    is_active = Column(Boolean, default=True)
    has_exited = Column(Boolean, default=False)
    exited_at = Column(DateTime(timezone=True), nullable=True)

    hotel_name = Column(String(200), nullable=True)
    host_name = Column(String(200), nullable=True)
    host_phone = Column(String(20), nullable=True)

    notes = Column(Text, nullable=True)

    __table_args__ = (
        Index("ix_national_visitors_passport", "passport_number", "passport_country"),
        Index("ix_national_visitors_visa", "visa_number"),
        {"extend_existing": True},
    )
