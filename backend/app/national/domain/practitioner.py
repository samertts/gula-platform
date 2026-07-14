from app.national.base import AuditEntity
from app.national.enums import PractitionerRole, Gender
from sqlalchemy import Boolean, Column, Date, Enum as SAEnum, ForeignKey, Index, String


class Practitioner(AuditEntity):
    __tablename__ = "national_practitioners"

    role = Column(SAEnum(PractitionerRole), nullable=False)
    full_name = Column(String(200), nullable=False)
    full_name_ar = Column(String(200), nullable=True)

    date_of_birth = Column(Date, nullable=True)
    gender = Column(SAEnum(Gender), nullable=True)
    nationality = Column(String(100), default="Iraqi")

    license_number = Column(String(100), nullable=False, unique=True, index=True)
    national_id_hash = Column(String(255), nullable=True)
    health_profession_number = Column(String(50), nullable=True, index=True)

    phone = Column(String(20), nullable=True)
    email = Column(String(255), nullable=True)

    organization_id = Column(String(26), ForeignKey("national_organizations.id", ondelete="RESTRICT"), nullable=True, index=True)
    facility_id = Column(String(26), ForeignKey("national_facilities.id", ondelete="RESTRICT"), nullable=True, index=True)

    specialty = Column(String(200), nullable=True)
    sub_specialty = Column(String(200), nullable=True)
    qualification = Column(String(500), nullable=True)

    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    available_for_telehealth = Column(Boolean, default=False)

    signature_url = Column(String(500), nullable=True)
    photo_url = Column(String(500), nullable=True)

    __table_args__ = (
        Index("ix_national_practitioners_org", "organization_id"),
        Index("ix_national_practitioners_facility", "facility_id"),
        Index("ix_national_practitioners_license", "license_number"),
        {"extend_existing": True},
    )
