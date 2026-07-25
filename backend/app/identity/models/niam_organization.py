from __future__ import annotations

from sqlalchemy import JSON, Boolean, Column, DateTime, ForeignKey, String, Text

from app.identity.base import IdentityBaseEntity

ORG_TYPES = [
    "ministry",
    "directorate",
    "government_hospital",
    "private_hospital",
    "primary_healthcare_sector",
    "health_center",
    "government_laboratory",
    "private_laboratory",
    "blood_bank",
    "forensic_medicine",
    "university",
    "research_center",
    "insurance_company",
    "ngo",
    "supplier",
    "vendor",
    "medical_company",
    "pharmacy",
    "external_authority",
]


class NIAMOrganization(IdentityBaseEntity):
    __tablename__ = "niam_organizations"

    uuid = Column(String(36), unique=True, nullable=False, index=True)
    org_id = Column(String(100), unique=True, nullable=False, index=True)

    name_en = Column(String(300), nullable=False)
    name_ar = Column(String(300), nullable=False)
    org_type = Column(String(50), nullable=False, index=True)

    parent_org_id = Column(
        String(26),
        ForeignKey("niam_organizations.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    license_number = Column(String(100), unique=True, nullable=True)
    accreditation = Column(String(200), nullable=True)
    accreditation_expires = Column(DateTime(timezone=True), nullable=True)

    status = Column(String(20), default="active", nullable=False, index=True)

    fhir_endpoint = Column(String(500), nullable=True)
    digital_certificate = Column(Text, nullable=True)
    certificate_expires = Column(DateTime(timezone=True), nullable=True)

    contact_email = Column(String(200), nullable=True)
    contact_phone = Column(String(30), nullable=True)
    address = Column(Text, nullable=True)
    website = Column(String(300), nullable=True)

    governorate = Column(String(50), nullable=True)
    district = Column(String(50), nullable=True)

    subscriptions = Column(JSON, nullable=True)
    settings = Column(JSON, nullable=True)
    tags = Column(JSON, nullable=True)

    is_active = Column(Boolean, default=True, nullable=False)
