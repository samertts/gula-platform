from __future__ import annotations

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, String, Text

from app._compat import StrEnum
from app.identity.base import IdentityBaseEntity


class IdentityType(StrEnum):
    """Canonical national identity types (PROGRAM-STABLE-003).

    This is the ONLY identity type vocabulary allowed across the platform.
    Every domain must map its actors onto one of these types — never create
    a parallel identity model.
    """

    citizen = "citizen"
    healthcare_professional = "healthcare_professional"
    employee = "employee"
    organization_member = "organization_member"
    government_official = "government_official"
    researcher = "researcher"
    external_partner = "external_partner"
    service_account = "service_account"
    robot_account = "robot_account"
    system_account = "system_account"

    # Legacy aliases kept for backward compatibility. New call sites MUST use
    # the canonical types above; these are mapped onto the canonical set.
    government_workforce = "government_workforce"
    private_workforce = "private_workforce"
    enterprise = "enterprise"
    machine = "machine"
    temporary = "temporary"
    guest = "guest"
    external_federation = "external_federation"

    def canonical(self) -> IdentityType:
        """Map legacy aliases onto the canonical national type."""
        aliases = {
            "government_workforce": IdentityType.government_official,
            "private_workforce": IdentityType.employee,
            "enterprise": IdentityType.organization_member,
            "machine": IdentityType.robot_account,
            "temporary": IdentityType.external_partner,
            "guest": IdentityType.external_partner,
            "external_federation": IdentityType.external_partner,
        }
        return aliases.get(self.value, self)


CANONICAL_IDENTITY_TYPES = tuple(
    t.value
    for t in (
        IdentityType.citizen,
        IdentityType.healthcare_professional,
        IdentityType.employee,
        IdentityType.organization_member,
        IdentityType.government_official,
        IdentityType.researcher,
        IdentityType.external_partner,
        IdentityType.service_account,
        IdentityType.robot_account,
        IdentityType.system_account,
    )
)


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
