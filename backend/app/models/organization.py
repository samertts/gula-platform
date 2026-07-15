from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app._compat import UTC

from ..database import Base


class Organization(Base):
    __tablename__ = "organizations"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(300), nullable=False)
    name_ar = Column(String(300), nullable=True)
    org_type = Column(String(50), nullable=False, index=True)
    license_number = Column(String(100), unique=True, nullable=True)
    tax_id = Column(String(100), nullable=True)
    phone = Column(String(20), nullable=True)
    email = Column(String(200), nullable=True)
    website = Column(String(300), nullable=True)
    address = Column(String(500), nullable=True)
    city = Column(String(100), nullable=True)
    province = Column(String(100), nullable=True)
    country = Column(String(100), default="IQ")
    is_active = Column(Boolean, default=True, index=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))

    facilities = relationship("Facility", back_populates="organization", cascade="all, delete-orphan")


class Facility(Base):
    __tablename__ = "facilities"

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(300), nullable=False)
    name_ar = Column(String(300), nullable=True)
    facility_type = Column(String(50), nullable=False, index=True)
    phone = Column(String(20), nullable=True)
    email = Column(String(200), nullable=True)
    address = Column(String(500), nullable=True)
    city = Column(String(100), nullable=True)
    province = Column(String(100), nullable=True)
    is_active = Column(Boolean, default=True, index=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))

    organization = relationship("Organization", back_populates="facilities")


class Appointment(Base):
    __tablename__ = "appointments"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, nullable=False, index=True)
    provider_id = Column(Integer, nullable=True, index=True)
    facility_id = Column(Integer, nullable=True, index=True)
    lab_id = Column(Integer, nullable=False, index=True)
    appointment_type = Column(String(50), nullable=False)
    status = Column(String(20), nullable=False, default="scheduled", index=True)
    scheduled_date = Column(DateTime(timezone=True), nullable=False)
    duration_minutes = Column(Integer, default=30)
    reason = Column(String(500), nullable=True)
    notes = Column(String(1000), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
