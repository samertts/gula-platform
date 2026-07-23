# GULA Identity Platform — Security Model

> Generated: 2026-07-23T11:23:43.298256+00:00
> Program: PROGRAM-IDENTITY-ENTERPRISE-001

## Security Controls by Layer

### Transport Security

| Control | Status | Details |
|---------|--------|---------|
| TLS termination | ✅ Complete | Host nginx (Internet → Docker) |
| API Gateway TLS | ✅ Complete | api-gateway nginx on 127.0.0.1:8080 |
| HSTS | ✅ Complete | SecurityHeadersMiddleware |
| CSP headers | ✅ Complete | Content Security Policy enforced |
| httpOnly cookies | ✅ Complete | Access/refresh tokens in httpOnly cookies |

### Password Security

| Control | Status | Details |
|---------|--------|---------|
| Bcrypt hashing | ✅ Complete | bcrypt via passlib (shared/auth) |
| Min length (8) | ✅ Complete | Registration validation |
| Max length (128) | ✅ Complete | Registration validation |
| Mixed character req | ✅ Complete | Upper + lower + digit validation |
| Timing-safe login | ✅ Complete | Dummy hash prevents user enumeration |
| Rate limiting (10/min) | ✅ Complete | `rate_limit_auth()` on login endpoint |

### Token Security

| Control | Status | Details |
|---------|--------|---------|
| HS256 signing | ✅ Complete | HMAC-SHA256 via joserfc |
| Separate refresh secret | ✅ Complete | REFRESH_TOKEN_SECRET independent |
| JTI per token | ✅ Complete | UUID v4 per access/refresh token |
| Redis blacklist | ✅ Complete | O(1) token revocation check |
| Perm-version invalidation | ✅ Complete | Session invalidation on state change |
| Refresh token rotation | ✅ Complete | Old revoked when new issued |
| Short-lived access (30min) | ✅ Complete | Configurable via env var |
| Long-lived refresh (30d) | ✅ Complete | Configurable via env var |
| Bearer + cookie dual-path | ✅ Complete | Mobile (Bearer) + Web (httpOnly) |

### MFA Security

| Control | Status | Details |
|---------|--------|---------|
| TOTP (30s window) | ✅ Complete | Configurable drift window |
| WebAuthn/FIDO2 | ✅ Complete | Passkeys (biometric/hardware) |
| HOTP (counter-based) | ✅ Complete | HMAC-SHA1 counter-based |
| Backup codes (8) | ✅ Complete | One-time use, hashed storage |
| Recovery token (32-byte) | ✅ Complete | URL-safe, one-time use |
| MFASession partial auth | ✅ Complete | Bridges password → MFA |
| Device registration | ✅ Complete | Per-device credential storage |

### Secret Management

| Secret | Storage | Hard Fail on Missing |
|--------|---------|---------------------|
| SECRET_KEY | env var | ✅ Yes |
| REFRESH_TOKEN_SECRET | env var | ✅ Yes |
| ENCRYPTION_KEY | env var | ✅ Yes |
| NID_HMAC_KEY | env var | ✅ Yes |
| DEVICE_HMAC_KEY | env var | ✅ Yes |
| METRICS_BEARER_TOKEN | env var | ✅ Yes (production) |

### OAuth2 Security

| Control | Status | Details |
|---------|--------|---------|
| PKCE (S256) | ✅ Complete | Prevents authorization code interception |
| Confidential clients | ✅ Complete | client_secret hashed at rest |
| Token introspection | ✅ Complete | Validate token status |
| Token revocation | ✅ Complete | Revoke at user or client request |
| Scope validation | ✅ Complete | openid, profile, email, read, write |
| Redirect URI validation | ✅ Complete | Whitelist-based |
| Client authentication | ✅ Complete | Basic or POST body |

### Rate Limiting

| Tier | Rate | Applied To |
|------|------|-----------|
| `auth` | 10 req/min | Login, register endpoints |
| `public` | 30 req/min | Unauthenticated endpoints |
| `user` | 100 req/min | Authenticated user endpoints |
| `admin` | 200 req/min | Admin/batch operations |

### Data Protection

| Control | Status | Details |
|---------|--------|---------|
| NID encryption at rest | ✅ Complete | Encrypted via ENCRYPTION_KEY + HKDF |
| NID HMAC hashing | ✅ Complete | HMAC-SHA256 for lookups |
| Password hashing (bcrypt) | ✅ Complete | Cost factor 12 |
| Field-level encryption | ✅ Complete | FieldSecurity model with masking |
| Audit hash chain | ✅ Complete | SHA-256 linked audit log |
| PII minimization | ✅ Complete | Only essential identity fields stored |
