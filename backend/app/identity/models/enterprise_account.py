from __future__ import annotations

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, String, Text

from app.identity.base import IdentityBaseEntity


class EnterpriseAccount(IdentityBaseEntity):
    __tablename__ = "niam_enterprise_accounts"

    uuid = Column(String(36), unique=True, nullable=False, index=True)
    organization_id = Column(
        String(26),
        ForeignKey("niam_organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    display_name = Column(String(200), nullable=False)

    api_key_prefix = Column(String(10), nullable=True, index=True)
    api_key_hash = Column(String(255), nullable=True)
    api_key_rotated_at = Column(DateTime(timezone=True), nullable=True)

    oauth2_client_id = Column(String(100), unique=True, nullable=True, index=True)
    oauth2_client_secret_hash = Column(String(255), nullable=True)

    certificate = Column(Text, nullable=True)
    certificate_thumbprint = Column(String(100), nullable=True)
    certificate_expires = Column(DateTime(timezone=True), nullable=True)

    digital_signature_key = Column(Text, nullable=True)

    fhir_endpoint = Column(String(500), nullable=True)
    scopes = Column(Text, nullable=True)

    is_active = Column(Boolean, default=True, nullable=False)
    last_used_at = Column(DateTime(timezone=True), nullable=True)
    notes = Column(Text, nullable=True)
