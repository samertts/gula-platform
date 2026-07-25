# GSF-002: Identity Security Module

Part of the GULA Security Framework (GSF).

## Components

| Component | File | Description |
|-----------|------|-------------|
| Models | `models.py` | Pydantic models and enums for identity |
| RBAC | `rbac.py` | Role-based access control with hierarchy |
| ABAC | `abac.py` | Attribute-based access control with policies |
| JWT | `jwt.py` | JWT lifecycle management with key rotation |
| PKCE | `pkce.py` | Proof Key for Code Exchange for OAuth2 flows |
| OIDC | `oidc.py` | OpenID Connect provider implementation |
| MFA | `mfa.py` | Multi-factor authentication (TOTP, HOTP, recovery) |
| Passkeys | `passkeys.py` | WebAuthn/FIDO2 passkey authentication |
| Risk Engine | `risk_engine.py` | Risk-based authentication scoring |
| Session | `session.py` | Session lifecycle and hijacking detection |

## Integration

Integrates with:
- `backend/app/security/rbac.py` - Extended RBAC
- `backend/app/security/abac.py` - Backend ABAC engine
- `backend/app/security/auth.py` - JWT blacklist and token helpers
- `backend/app/security/session.py` - Permission version management
- `backend/app/security/mfa_service.py` - Backend MFA service
- `backend/app/security/oauth2_provider.py` - OAuth2/OIDC provider
- `backend/app/security/redis_client.py` - Redis-backed caching
- `shared/rbac/` - Canonical RBAC matrix
