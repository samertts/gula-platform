from __future__ import annotations

from sqlalchemy import JSON, Boolean, Column, Date, DateTime, ForeignKey, String, Text

from app._compat import StrEnum
from app.identity.base import IdentityBaseEntity

PROFESSION_CATEGORIES = [
    "doctor",
    "dentist",
    "pharmacist",
    "laboratory_scientist",
    "nurse",
    "radiographer",
    "physiotherapist",
    "veterinarian",
    "researcher",
    "student",
    "retired_professional",
    "foreign_professional",
]


class RegistryStatus(StrEnum):
    pending = "pending"
    verified = "verified"
    suspended = "suspended"
    revoked = "revoked"
    expired = "expired"
    retired = "retired"


class ProfessionalRegistryEntry(IdentityBaseEntity):
    """National professional registry record.

    A professional's operational privileges become active ONLY after the
    responsible authority verifies the entry. Clinical privileges are never
    activated automatically — verification by the issuing authority is
    mandatory before the authorization layer grants operational permissions.
    """

    __tablename__ = "niam_professional_registry"

    uuid = Column(String(36), unique=True, nullable=False, index=True)
    registry_id = Column(String(100), unique=True, nullable=False, index=True)
    person_id = Column(
        String(26), ForeignKey("niam_persons.id", ondelete="CASCADE"), nullable=False, index=True
    )
    identity_id = Column(
        String(26), ForeignKey("niam_identities.id", ondelete="CASCADE"), nullable=False, index=True
    )

    profession = Column(String(50), nullable=False, index=True)
    specialty = Column(String(200), nullable=True)
    registration_number = Column(String(100), unique=True, nullable=False, index=True)

    issuing_authority = Column(String(200), nullable=False)
    issuing_authority_id = Column(
        String(26),
        ForeignKey("niam_identity_authorities.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    issuing_country = Column(String(3), nullable=False, index=True)

    status = Column(String(20), default="pending", nullable=False, index=True)
    status_reason = Column(Text, nullable=True)

    verified = Column(Boolean, default=False, nullable=False)
    verified_at = Column(DateTime(timezone=True), nullable=True)
    verified_by = Column(String(100), nullable=True)
    verification_method = Column(String(100), nullable=True)

    license_number = Column(String(100), nullable=True)
    license_verified = Column(Boolean, default=False, nullable=False)

    issued_at = Column(Date, nullable=False)
    expires_at = Column(Date, nullable=True)

    # Privileges are ONLY granted once verification completes. This flag is a
    # derived, auditable outcome of verification — it is never set directly by
    # the registrant or by any domain that would benefit from it.
    privileges_activated_at = Column(DateTime(timezone=True), nullable=True)
    privileges_activated_by = Column(String(100), nullable=True)

    attachments = Column(JSON, nullable=True)
    notes = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)


class AuthorizationScopeType(StrEnum):
    """Jurisdictional scope of a professional authorization."""

    national = "national"
    directorate = "directorate"
    facility = "facility"


class AuthorizationStatus(StrEnum):
    active = "active"
    suspended = "suspended"
    revoked = "revoked"
    expired = "expired"


class ProfessionalAuthorization(IdentityBaseEntity):
    """Separable operational authorization derived from a registry entry.

    The registry entry records *identity* (who the professional is and whether
    the issuing authority verified them). The authorization records *privilege*
    (what scope the professional may operate in, for how long). They are kept
    separable: an authorization is issued only from a verified, non-expired
    entry, and any registry-level suspension/revocation automatically invalidates
    every derived authorization through :meth:`is_authorized`.
    """

    __tablename__ = "niam_professional_authorizations"

    uuid = Column(String(36), unique=True, nullable=False, index=True)
    authorization_id = Column(String(100), unique=True, nullable=False, index=True)
    registry_id = Column(
        String(26),
        ForeignKey("niam_professional_registry.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    person_id = Column(
        String(26), ForeignKey("niam_persons.id", ondelete="CASCADE"), nullable=False, index=True
    )

    profession = Column(String(50), nullable=False, index=True)

    scope_type = Column(String(30), default="national", nullable=False, index=True)
    scope_id = Column(String(26), nullable=True, index=True)

    status = Column(String(20), default="active", nullable=False, index=True)
    status_reason = Column(Text, nullable=True)

    granted_at = Column(DateTime(timezone=True), nullable=False)
    granted_by = Column(String(100), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=True)

    is_active = Column(Boolean, default=True, nullable=False)
