from __future__ import annotations

from sqlalchemy import Boolean, Column, Date, ForeignKey, Integer, String, Text

from app._compat import StrEnum
from app.identity.base import IdentityBaseEntity


class LicenseStatus(StrEnum):
    active = "active"
    expired = "expired"
    suspended = "suspended"
    revoked = "revoked"
    pending = "pending"


class ProfessionalLicense(IdentityBaseEntity):
    __tablename__ = "niam_licenses"

    uuid = Column(String(36), unique=True, nullable=False, index=True)
    person_id = Column(String(26), ForeignKey("niam_persons.id", ondelete="CASCADE"), nullable=False, index=True)

    license_type = Column(String(50), nullable=False, index=True)
    license_number = Column(String(100), nullable=False, index=True)
    license_name = Column(String(200), nullable=False)

    issuing_authority = Column(String(200), nullable=False)
    issuing_country = Column(String(3), default="IRQ")

    issue_date = Column(Date, nullable=False)
    expiry_date = Column(Date, nullable=True)
    verification_date = Column(Date, nullable=True)

    status = Column(String(20), default="active", nullable=False, index=True)
    status_reason = Column(Text, nullable=True)

    board_certification = Column(Boolean, default=False, nullable=False)
    board_name = Column(String(200), nullable=True)
    board_certified_at = Column(Date, nullable=True)

    degree_type = Column(String(50), nullable=True)
    degree_name = Column(String(200), nullable=True)
    degree_institution = Column(String(200), nullable=True)
    degree_year = Column(Integer, nullable=True)
    degree_country = Column(String(3), nullable=True)

    continuing_education_hours = Column(Integer, nullable=True)
    continuing_education_expires = Column(Date, nullable=True)

    verified = Column(Boolean, default=False, nullable=False)
    verified_by = Column(String(100), nullable=True)

    attachments = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
