from sqlalchemy import Boolean, Column, ForeignKey, Index, String, Text
from sqlalchemy import Enum as SAEnum

from app.national.base import TenantAuditEntity
from app.national.enums import FamilyRelationshipType


class EmergencyContact(TenantAuditEntity):
    __tablename__ = "national_emergency_contacts"

    patient_id = Column(
        String(26),
        ForeignKey("national_patients.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    citizen_id = Column(
        String(26),
        ForeignKey("national_citizens.id", ondelete="RESTRICT"),
        nullable=True,
        index=True,
    )

    full_name = Column(String(200), nullable=False)
    relationship = Column(SAEnum(FamilyRelationshipType), nullable=True)
    relationship_other = Column(String(100), nullable=True)

    phone = Column(String(20), nullable=False)
    alternative_phone = Column(String(20), nullable=True)
    email = Column(String(255), nullable=True)

    address_line = Column(String(500), nullable=True)
    city = Column(String(100), nullable=True)
    governorate = Column(String(100), nullable=True)

    is_primary = Column(Boolean, default=True)
    is_authorized = Column(Boolean, default=True)
    is_active = Column(Boolean, default=True)
    notes = Column(Text, nullable=True)

    __table_args__ = (
        Index("ix_national_emergency_contacts_patient", "patient_id"),
        {"extend_existing": True},
    )
