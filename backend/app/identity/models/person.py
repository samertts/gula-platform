from __future__ import annotations

from sqlalchemy import JSON, Boolean, Column, Date, DateTime, String, Text

from app.identity.base import IdentityBaseEntity


class Person(IdentityBaseEntity):
    __tablename__ = "niam_persons"

    uuid = Column(String(36), unique=True, nullable=False, index=True)

    national_id_hash = Column(String(255), unique=True, nullable=True, index=True)
    health_id = Column(String(100), unique=True, nullable=True, index=True)
    passport_number = Column(String(50), unique=True, nullable=True, index=True)

    given_name = Column(String(100), nullable=False)
    middle_name = Column(String(100), nullable=True)
    family_name = Column(String(100), nullable=False)
    full_name_ar = Column(String(300), nullable=True)

    gender = Column(String(20), nullable=True)
    birth_date = Column(Date, nullable=True)
    nationality = Column(String(3), default="IRQ", nullable=True)

    email = Column(String(200), nullable=True, index=True)
    phone = Column(String(30), nullable=True, index=True)
    address = Column(Text, nullable=True)

    emergency_contact_name = Column(String(200), nullable=True)
    emergency_contact_phone = Column(String(30), nullable=True)
    emergency_contact_relation = Column(String(50), nullable=True)

    is_deceased = Column(Boolean, default=False, nullable=False)
    deceased_at = Column(DateTime(timezone=True), nullable=True)

    tags = Column(JSON, nullable=True)
    extra_metadata = Column(JSON, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
