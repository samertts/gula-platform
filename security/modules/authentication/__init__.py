GSF-004: Authentication Module — Authentication methods and MFA.

Provides comprehensive authentication for the GULA platform including
password-based auth, TOTP, WebAuthn/FIDO2, OAuth2, SAML, and LDAP
integration. Enforces multi-factor authentication (MFA) and supports
step-up authentication for sensitive operations.

Exports:
    Authenticator: Core authentication orchestrator
    PasswordAuthenticator: Argon2id password verification
    TotpAuthenticator: Time-based one-time password (RFC 6238)
    WebAuthnAuthenticator: FIDO2 WebAuthn (passkeys)
    OAuth2Provider: OAuth2 authorization server
    SamlProvider: SAML 2.0 identity provider
    MfaManager: Multi-factor authentication policy enforcer
    SessionManager: Authenticated session management
"""

from security.modules.authentication.authenticator import Authenticator
from security.modules.authentication.password import PasswordAuthenticator
from security.modules.authentication.totp import TotpAuthenticator
from security.modules.authentication.webauthn import WebAuthnAuthenticator
from security.modules.authentication.oauth2 import OAuth2Provider
from security.modules.authentication.saml import SamlProvider
from security.modules.authentication.mfa import MfaManager
from security.modules.authentication.session import SessionManager

__all__ = [
    "Authenticator",
    "PasswordAuthenticator",
    "TotpAuthenticator",
    "WebAuthnAuthenticator",
    "OAuth2Provider",
    "SamlProvider",
    "MfaManager",
    "SessionManager",
]
