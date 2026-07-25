from __future__ import annotations

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, String, Text

from app._compat import StrEnum
from app.identity.base import IdentityBaseEntity


class IdentityType(StrEnum):
    citizen = "citizen"
    government_workforce = "government_workforce"
    private_workforce = "private_workforce"
    enterprise = "enterprise"
    machine = "machine"
    temporary = "temporary"
    guest = "guest"
    external_federation = "external_federation"


class IdentityRecord(IdentityBaseEntity):
    __tablename__ = "niam_identities"

    uuid = Column(String(36), unique=True, nullable=False, index=True)
    person_id = Column(
        String(26), ForeignKey("niam_persons.id", ondelete="CASCADE"), nullable=False, index=True
    )

    identity_type = Column(String(30), nullable=False, index=True)
    status = Column(String(20), default="active", nullable=False, index=True)

    verified_at = Column(DateTime(timezone=True), nullable=True)
    verified_by = Column(String(100), nullable=True)
    verification_method = Column(String(50), nullable=True)

    issued_at = Column(DateTime(timezone=True), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=True)

    issued_by_organization = Column(
        String(26), ForeignKey("niam_organizations.id", ondelete="SET NULL"), nullable=True
    )

    notes = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
