from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class IdentityProvider(str, Enum):
    INTERNAL = "internal"
    LDAP = "ldap"
    OIDC = "oidc"
    SAML = "saml"
    OAUTH2 = "oauth2"
    GOOGLE = "google"
    MICROSOFT = "microsoft"
    APPLE = "apple"
    IRAQI_NATIONAL_ID = "iraqi_national_id"


class AuthenticationMethod(str, Enum):
    PASSWORD = "password"
    MFA_TOTP = "mfa_totp"
    MFA_HOTP = "mfa_hotp"
    WEBAUTHN = "webauthn"
    PASSKEY = "passkey"
    SMS_OTP = "sms_otp"
    EMAIL_OTP = "email_otp"
    BIOMETRIC = "biometric"
    SMART_CARD = "smart_card"
    CERTIFICATE = "certificate"


class AuthFactor(str, Enum):
    PASSWORD = "password"
    TOTP = "totp"
    SMS = "sms"
    EMAIL = "email"
    WEBAUTHN = "webauthn"
    BIOMETRIC = "biometric"
    HARDWARE_TOKEN = "hardware_token"
    SMART_CARD = "smart_card"


class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class SessionInfo(BaseModel):
    session_id: str
    user_id: str
    ip_address: str
    user_agent: str = ""
    auth_methods: list[AuthenticationMethod] = Field(default_factory=list)
    risk_level: RiskLevel = RiskLevel.LOW
    created_at: datetime
    expires_at: datetime
    last_activity: datetime


class UserIdentity(BaseModel):
    user_id: str
    username: str
    email: str = ""
    roles: list[str] = Field(default_factory=list)
    attributes: dict[str, Any] = Field(default_factory=dict)
    provider: IdentityProvider = IdentityProvider.INTERNAL
    mfa_enabled: bool = False
    passkeys: list[dict[str, Any]] = Field(default_factory=list)


class AccessRequest(BaseModel):
    resource: str
    action: str
    context: dict[str, Any] = Field(default_factory=dict)
    user_identity: UserIdentity | None = None


class AccessDecision(BaseModel):
    permitted: bool = False
    reason: str = ""
    obligations: list[str] = Field(default_factory=list)
    advices: list[str] = Field(default_factory=list)


class TokenClaims(BaseModel):
    sub: str
    iss: str = ""
    aud: str | list[str] = ""
    exp: int = 0
    nbf: int = 0
    iat: int = 0
    jti: str = ""
    auth_time: int = 0
    acr: str = ""
    amr: list[str] = Field(default_factory=list)
    roles: list[str] = Field(default_factory=list)
    permissions: list[str] = Field(default_factory=list)
