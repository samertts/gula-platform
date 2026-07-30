# GSF-004: Authentication Module

**GSF Identifier:** GSF-004
**Status:** Active
**Version:** 1.0.0

## Overview

Provides comprehensive authentication for the GULA platform including password-based auth, TOTP, WebAuthn/FIDO2 passkeys, and step-up authentication. Delegates implementation to the `identity/` module for JWT token management, MFA, and passkeys.

## Architecture

Authentication flows through a multi-layered approach: primary auth (password/SSO), second factor (TOTP/WebAuthn), and step-up for sensitive operations.

## Components

- `identity.mfa` — TOTP/HOTP/Recovery codes for multi-factor auth
- `identity.passkeys` — WebAuthn/FIDO2 passkey registration and verification
- `identity.jwt` — JWT access/refresh token issuance and validation

## Dependencies

- **Internal:** identity, crypto
- **External:** None beyond stdlib

## Usage

```python
from security.modules.identity import mfa, passkeys

# Generate TOTP secret
secret = mfa.generate_totp_secret()

# Verify TOTP code
is_valid = mfa.verify_totp(secret, user_code)
```

## Security Considerations

- All MFA secrets generated with cryptographically secure randomness
- WebAuthn attestation verification for hardware key validation
- JWT tokens signed with rotating keys

## Testing

```bash
pytest security/tests/test_identity.py -v -k "test_mfa"
```

## Future Extensions

- Passkey-backed recovery codes
- Hardware security module (HSM) integration for JWT signing
