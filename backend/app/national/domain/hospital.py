from sqlalchemy import Boolean, Column, ForeignKey, Index, Integer, String

from app.national.base import AuditEntity


class Hospital(AuditEntity):
    __tablename__ = "national_hospitals"

    name = Column(String(200), nullable=False)
    name_ar = Column(String(200), nullable=True)
    license_number = Column(String(100), nullable=False, unique=True, index=True)

    hospital_type = Column(String(50), nullable=False)
    organization_id = Column(
        String(26),
        ForeignKey("national_organizations.id", ondelete="RESTRICT"),
        nullable=True,
        index=True,
    )
    facility_id = Column(
        String(26),
        ForeignKey("national_facilities.id", ondelete="RESTRICT"),
        nullable=True,
        index=True,
    )

    phone = Column(String(20), nullable=True)
    email = Column(String(255), nullable=True)
    website = Column(String(500), nullable=True)

    address_line = Column(String(500), nullable=True)
    city = Column(String(100), nullable=True)
    governorate = Column(String(100), nullable=True)

    bed_count = Column(Integer, default=0)
    emergency_available = Column(Boolean, default=False)
    ambulance_service = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)

    director_name = Column(String(200), nullable=True)
    accreditation = Column(String(200), nullable=True)

    __table_args__ = (
        Index("ix_national_hospitals_org", "organization_id"),
        Index("ix_national_hospitals_facility", "facility_id"),
        {"extend_existing": True},
    )
