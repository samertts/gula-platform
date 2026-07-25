from datetime import datetime

from sqlalchemy import JSON, Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app._compat import UTC

from ..database import Base


class Organization(Base):
    __tablename__ = "organizations"

    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(String(100), unique=True, nullable=False, index=True)
    name_en = Column(String(200), nullable=False)
    name_ar = Column(String(200), nullable=False)
    org_type = Column(String(50), nullable=False, index=True)
    parent_org_id = Column(String(100), nullable=True, index=True)
    tenant_id = Column(
        Integer, ForeignKey("tenants.id", ondelete="SET NULL"), nullable=True, index=True,
    )
    governorate_id = Column(String(50), nullable=True, index=True)
    directorate_id = Column(String(50), nullable=True, index=True)
    is_active = Column(Boolean, default=True)
    contact_email = Column(String(200), nullable=True)
    contact_phone = Column(String(30), nullable=True)
    address = Column(Text, nullable=True)
    extra_metadata = Column("metadata", JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )

    tenant = relationship("Tenant", back_populates="organizations")
    users = relationship("User", back_populates="organization")
    facilities = relationship("Facility", back_populates="organization")


class Facility(Base):
    __tablename__ = "facilities"

    id = Column(Integer, primary_key=True, index=True)
    facility_id = Column(String(100), unique=True, nullable=False, index=True)
    name_en = Column(String(200), nullable=False)
    name_ar = Column(String(200), nullable=False)
    facility_type = Column(String(50), nullable=False, index=True)
    organization_id = Column(
        Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True,
    )
    contact_email = Column(String(200), nullable=True)
    contact_phone = Column(String(30), nullable=True)
    address = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))

    organization = relationship("Organization", back_populates="facilities")
