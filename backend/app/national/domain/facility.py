from sqlalchemy import Boolean, Column, ForeignKey, Index, String, Text
from sqlalchemy import Enum as SAEnum

from app.national.base import AuditEntity
from app.national.enums import FacilityType


class Facility(AuditEntity):
    __tablename__ = "national_facilities"

    facility_type = Column(SAEnum(FacilityType), nullable=False)
    name = Column(String(200), nullable=False)
    name_ar = Column(String(200), nullable=True)
    code = Column(String(20), nullable=True, unique=True, index=True)

    organization_id = Column(String(26), ForeignKey("national_organizations.id", ondelete="RESTRICT"), nullable=True, index=True)
    directorate_id = Column(String(26), ForeignKey("national_directorates.id", ondelete="RESTRICT"), nullable=True, index=True)
    parent_facility_id = Column(String(26), nullable=True, index=True)

    phone = Column(String(20), nullable=True)
    email = Column(String(255), nullable=True)

    address_line = Column(String(500), nullable=True)
    city = Column(String(100), nullable=True)
    governorate = Column(String(100), nullable=True)
    district = Column(String(100), nullable=True)

    latitude = Column(String(20), nullable=True)
    longitude = Column(String(20), nullable=True)

    is_active = Column(Boolean, default=True)
    is_emergency_available = Column(Boolean, default=False)
    operating_hours = Column(Text, nullable=True)

    __table_args__ = (
        Index("ix_national_facilities_type", "facility_type"),
        Index("ix_national_facilities_org", "organization_id"),
        Index("ix_national_facilities_directorate", "directorate_id"),
        {"extend_existing": True},
    )
