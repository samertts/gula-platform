from sqlalchemy import Boolean, Column, ForeignKey, Index, String, Text

from app.national.base import AuditEntity


class Clinic(AuditEntity):
    __tablename__ = "national_clinics"

    name = Column(String(200), nullable=False)
    name_ar = Column(String(200), nullable=True)
    clinic_type = Column(String(50), nullable=False)

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
    hospital_id = Column(
        String(26),
        ForeignKey("national_hospitals.id", ondelete="RESTRICT"),
        nullable=True,
        index=True,
    )

    phone = Column(String(20), nullable=True)
    email = Column(String(255), nullable=True)

    address_line = Column(String(500), nullable=True)
    city = Column(String(100), nullable=True)
    governorate = Column(String(100), nullable=True)

    specialty = Column(String(100), nullable=True)
    is_active = Column(Boolean, default=True)
    operating_hours = Column(Text, nullable=True)

    __table_args__ = (
        Index("ix_national_clinics_org", "organization_id"),
        Index("ix_national_clinics_facility", "facility_id"),
        Index("ix_national_clinics_hospital", "hospital_id"),
        {"extend_existing": True},
    )
