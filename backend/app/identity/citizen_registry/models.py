from __future__ import annotations

from sqlalchemy import JSON, Boolean, Column, DateTime, ForeignKey, String

from app._compat import StrEnum
from app.identity.base import IdentityBaseEntity

# Configurable national identity identifiers (country-agnostic). Any identifier
# type may be configured for a deployment — nothing is hard-coded to a specific
# country.
IDENTIFIER_TYPES = [
    "national_id",
    "civil_id",
    "national_health_id",
    "social_security_number",
    "resident_id",
    "passport",
    "tax_number",
    "custom",
]


class ProviderStatus(StrEnum):
    active = "active"
    disabled = "disabled"
    maintenance = "maintenance"


class IdentityProvider(IdentityBaseEntity):
    """A configurable national identity provider.

    Enables country-agnostic citizen registration: each deployment configures
    which identifier types it accepts (National ID, Civil ID, National Health
    ID, Social Security Number, Resident ID, Passport, …) and how they are
    verified. No country-specific rules are hard-coded in the platform.
    """

    __tablename__ = "niam_identity_providers"

    uuid = Column(String(36), unique=True, nullable=False, index=True)
    provider_id = Column(String(100), unique=True, nullable=False, index=True)

    name_en = Column(String(300), nullable=False)
    name_ar = Column(String(300), nullable=True)
    provider_type = Column(String(50), nullable=False, index=True)  # government, national_health, civil_registry, ...
    country = Column(String(3), nullable=False, index=True)

    identifier_types = Column(JSON, nullable=False)
    verification_methods = Column(JSON, nullable=True)
    configuration = Column(JSON, nullable=True)

    status = Column(String(20), default="active", nullable=False, index=True)
    is_default = Column(Boolean, default=False, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)


class CitizenIdentityVerification(IdentityBaseEntity):
    """Verification record linking a citizen to a provider-issued identifier."""

    __tablename__ = "niam_citizen_identity_verifications"

    uuid = Column(String(36), unique=True, nullable=False, index=True)
    verification_id = Column(String(100), unique=True, nullable=False, index=True)
    person_id = Column(
        String(26), ForeignKey("niam_persons.id", ondelete="CASCADE"), nullable=False, index=True
    )
    provider_id = Column(
        String(26),
        ForeignKey("niam_identity_providers.id", ondelete="SET NULL"),
        nullable=False,
        index=True,
    )

    identifier_type = Column(String(50), nullable=False, index=True)
    identifier_hash = Column(String(255), nullable=False, index=True)
    identifier_display = Column(String(100), nullable=True)

    verification_status = Column(String(20), default="pending", nullable=False, index=True)
    verified_at = Column(DateTime(timezone=True), nullable=True)
    verified_by = Column(String(100), nullable=True)

    raw_response = Column(JSON, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
