"""GSF-004: Authentication Module — Authentication methods and MFA.

Provides comprehensive authentication for the GULA platform including
password-based auth, TOTP, WebAuthn/FIDO2, and step-up authentication.

The primary implementation lives in identity/ module:
- mfa.py — TOTP/HOTP/Recovery codes
- passkeys.py — WebAuthn/FIDO2 passkeys
- jwt.py — JWT token management
"""

__all__: list[str] = []
