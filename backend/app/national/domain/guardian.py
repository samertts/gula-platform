from sqlalchemy import Boolean, Column, Date, ForeignKey, Index, String, Text
from sqlalchemy import Enum as SAEnum

from app.national.base import TenantAuditEntity
from app.national.enums import GuardianType


class Guardian(TenantAuditEntity):
    __tablename__ = "national_guardians"

    guardian_type = Column(SAEnum(GuardianType), nullable=False)
    citizen_id = Column(
        String(26),
        ForeignKey("national_citizens.id", ondelete="RESTRICT"),
        nullable=True,
        index=True,
    )

    full_name = Column(String(200), nullable=False)
    relationship = Column(String(100), nullable=False)
    national_id_hash = Column(String(255), nullable=True)
    phone = Column(String(20), nullable=False)
    email = Column(String(255), nullable=True)
    alternative_phone = Column(String(20), nullable=True)

    date_of_birth = Column(Date, nullable=True)
    occupation = Column(String(200), nullable=True)
    address_line = Column(String(500), nullable=True)

    is_verified = Column(Boolean, default=False)
    is_legal_guardian = Column(Boolean, default=False)
    has_custody = Column(Boolean, default=True)
    custody_document_url = Column(String(500), nullable=True)

    is_active = Column(Boolean, default=True)
    notes = Column(Text, nullable=True)

    __table_args__ = (
        Index("ix_national_guardians_citizen", "citizen_id"),
        Index("ix_national_guardians_phone", "phone"),
        {"extend_existing": True},
    )
