from __future__ import annotations

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, String, Text

from app._compat import StrEnum
from app.identity.base import IdentityBaseEntity


class CredentialType(StrEnum):
    password = "password"
    passkey = "passkey"
    fido2 = "fido2"
    otp_secret = "otp_secret"
    authenticator_app = "authenticator_app"
    api_key = "api_key"
    certificate = "certificate"
    smart_card = "smart_card"
    biometric = "biometric"
    oauth2_token = "oauth2_token"
    saml_assertion = "saml_assertion"


class Credential(IdentityBaseEntity):
    __tablename__ = "niam_credentials"

    uuid = Column(String(36), unique=True, nullable=False, index=True)
    account_id = Column(String(26), ForeignKey("niam_accounts.id", ondelete="CASCADE"), nullable=False, index=True)

    credential_type = Column(String(30), nullable=False, index=True)
    credential_value = Column(Text, nullable=False)
    credential_identifier = Column(String(255), nullable=True, index=True)

    is_primary = Column(Boolean, default=False, nullable=False, server_default="false")
    is_revoked = Column(Boolean, default=False, nullable=False)
    revoked_at = Column(DateTime(timezone=True), nullable=True)
    revocation_reason = Column(String(200), nullable=True)

    expires_at = Column(DateTime(timezone=True), nullable=True)
    last_used_at = Column(DateTime(timezone=True), nullable=True)

    device_info = Column(String(500), nullable=True)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)

    is_active = Column(Boolean, default=True, nullable=False)
