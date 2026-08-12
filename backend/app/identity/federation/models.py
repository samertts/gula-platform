from __future__ import annotations

from datetime import datetime

from sqlalchemy import JSON, Boolean, Column, DateTime, ForeignKey, String, Text

from app._compat import UTC
from app.identity.base import IdentityBaseEntity


class FederatedProvider(IdentityBaseEntity):
    __tablename__ = "niam_fed_providers"

    uuid = Column(String(36), unique=True, nullable=False, index=True)
    provider_id = Column(String(100), unique=True, nullable=False, index=True)

    name_en = Column(String(300), nullable=False)
    name_ar = Column(String(300), nullable=True)

    provider_type = Column(
        String(50), nullable=False, index=True,
        default="oauth2",
    )

    issuer_url = Column(String(500), unique=True, nullable=False, index=True)
    authorization_endpoint = Column(String(500), nullable=True)
    token_endpoint = Column(String(500), nullable=True)
    jwks_uri = Column(String(500), nullable=True)
    userinfo_endpoint = Column(String(500), nullable=True)

    client_id = Column(String(500), nullable=True)
    client_secret_encrypted = Column(String(500), nullable=True)

    scopes = Column(JSON, nullable=True)
    redirect_uris = Column(JSON, nullable=True)

    certificate = Column(Text, nullable=True)
    signature_algorithm = Column(String(50), nullable=True)

    status = Column(String(20), default="active", nullable=False, index=True)

    trust_anchor_id = Column(String(100), nullable=True)
    metadata_url = Column(String(500), nullable=True)

    last_sync_at = Column(DateTime(timezone=True), nullable=True)

    is_active = Column(Boolean, default=True, nullable=False)


class FederatedIdentity(IdentityBaseEntity):
    __tablename__ = "niam_fed_identities"

    uuid = Column(String(36), unique=True, nullable=False, index=True)
    fed_id = Column(String(100), unique=True, nullable=False, index=True)

    person_id = Column(
        String(26), ForeignKey("niam_persons.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    identity_id = Column(
        String(26), ForeignKey("niam_identities.id", ondelete="SET NULL"),
        nullable=True, index=True,
    )
    provider_id = Column(
        String(26), ForeignKey("niam_fed_providers.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )

    external_subject_id = Column(String(500), nullable=False, index=True)

    external_attributes = Column(JSON, nullable=True)

    linked_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)
    last_login_at = Column(DateTime(timezone=True), nullable=True)

    status = Column(String(20), default="active", nullable=False, index=True)

    unlinked_at = Column(DateTime(timezone=True), nullable=True)
    unlink_reason = Column(String(500), nullable=True)

    is_active = Column(Boolean, default=True, nullable=False)


class IdentityLink(IdentityBaseEntity):
    __tablename__ = "niam_fed_links"

    uuid = Column(String(36), unique=True, nullable=False, index=True)
    link_id = Column(String(100), unique=True, nullable=False, index=True)

    person_id = Column(
        String(26), ForeignKey("niam_persons.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    source_org_id = Column(
        String(26), ForeignKey("niam_organizations.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    target_org_id = Column(
        String(26), ForeignKey("niam_organizations.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )

    link_type = Column(
        String(30), nullable=False, index=True,
        default="cross_org",
    )

    external_person_id = Column(String(100), nullable=True)
    external_identity_id = Column(String(100), nullable=True)

    linked_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)
    linked_by = Column(String(100), nullable=True)

    verified_at = Column(DateTime(timezone=True), nullable=True)
    verified_by = Column(String(100), nullable=True)

    status = Column(String(20), default="active", nullable=False, index=True)

    expiry = Column(DateTime(timezone=True), nullable=True)

    is_active = Column(Boolean, default=True, nullable=False)


class FederatedSession(IdentityBaseEntity):
    __tablename__ = "niam_fed_sessions"

    uuid = Column(String(36), unique=True, nullable=False, index=True)
    session_id = Column(String(100), unique=True, nullable=False, index=True)

    account_id = Column(
        String(26), ForeignKey("niam_accounts.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    provider_id = Column(
        String(26), ForeignKey("niam_fed_providers.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    fed_identity_id = Column(
        String(26), ForeignKey("niam_fed_identities.id", ondelete="SET NULL"),
        nullable=True, index=True,
    )

    id_token = Column(Text, nullable=True)
    access_token_hash = Column(String(128), nullable=True)
    refresh_token_hash = Column(String(128), nullable=True)

    token_type = Column(String(50), nullable=True)
    scope = Column(String(500), nullable=True)

    session_attributes = Column(JSON, nullable=True)

    started_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    terminated_at = Column(DateTime(timezone=True), nullable=True)

    is_active = Column(Boolean, default=True, nullable=False)


class CrossOrganizationTrust(IdentityBaseEntity):
    __tablename__ = "niam_fed_cross_org_trust"

    uuid = Column(String(36), unique=True, nullable=False, index=True)
    trust_id = Column(String(100), unique=True, nullable=False, index=True)

    source_org_id = Column(
        String(26), ForeignKey("niam_organizations.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    target_org_id = Column(
        String(26), ForeignKey("niam_organizations.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )

    trust_type = Column(String(50), nullable=False, default="bilateral")
    trust_level = Column(String(30), nullable=False, default="full")

    attribute_sharing_agreement = Column(JSON, nullable=True)
    permission_mapping = Column(JSON, nullable=True)
    role_mapping = Column(JSON, nullable=True)

    established_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)
    established_by = Column(String(100), nullable=True)

    expires_at = Column(DateTime(timezone=True), nullable=True)
    last_reviewed = Column(DateTime(timezone=True), nullable=True)

    status = Column(String(20), default="active", nullable=False, index=True)

    is_active = Column(Boolean, default=True, nullable=False)


class FederationAgreement(IdentityBaseEntity):
    __tablename__ = "niam_fed_agreements"

    uuid = Column(String(36), unique=True, nullable=False, index=True)
    agreement_id = Column(String(100), unique=True, nullable=False, index=True)

    name = Column(String(300), nullable=False)

    parties = Column(JSON, nullable=False)
    agreement_type = Column(String(50), nullable=False, index=True)

    scope = Column(JSON, nullable=True)
    terms = Column(JSON, nullable=True)
    security_requirements = Column(JSON, nullable=True)

    signed_by = Column(JSON, nullable=True)
    signed_at = Column(DateTime(timezone=True), nullable=True)

    effective_date = Column(DateTime(timezone=True), nullable=True)
    expiry_date = Column(DateTime(timezone=True), nullable=True)

    status = Column(String(20), default="draft", nullable=False, index=True)

    governing_law = Column(String(100), nullable=True)

    is_active = Column(Boolean, default=True, nullable=False)
