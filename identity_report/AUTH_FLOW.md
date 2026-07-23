# GULA Identity Platform — Authentication Flow

> Generated: 2026-07-23T11:23:43.297643+00:00
> Program: PROGRAM-IDENTITY-ENTERPRISE-001

## Authentication Mechanisms

| Mechanism | Status | Description |
|-----------|--------|-------------|
| Password + JWT | ✅ Complete | Dual-path (lab staff first, citizen fallback) |
| MFA (TOTP) | ✅ Complete | Time-based one-time passwords |
| MFA (WebAuthn/FIDO2) | ✅ Complete | Passkeys (biometric/hardware) |
| MFA (Backup Codes) | ✅ Complete | 8 one-time use backup codes |
| MFA (Recovery Token) | ✅ Complete | 32-byte URL-safe recovery token |
| OAuth2 Authorization Code | ✅ Complete | With PKCE (S256) |
| OAuth2 Client Credentials | ✅ Complete | Machine-to-machine |
| OAuth2 Refresh Token | ✅ Complete | With rotation |
| OpenID Connect | ✅ Complete | Discovery, ID Token, JWKS |
| API Keys (Service Accounts) | ✅ Complete | `gula_` prefix, rotation, revocation |

## Standard Login Flow

```
┌──────────┐     ┌──────────────┐     ┌──────────┐     ┌─────────┐
│  Browser │     │  API Gateway  │     │ Backend  │     │  Redis  │
└────┬─────┘     └──────┬───────┘     └────┬─────┘     └────┬────┘
     │ POST /login       │                  │               │
     │ (email+password)  │                  │               │
     ├──────────────────►├─────────────────►│               │
     │                   │                  │               │
     │                   │                  ├── Dummy hash  │
     │                   │                  │   (timing-    │
     │                   │                  │    safe)      │
     │                   │                  │               │
     │                   │                  ├── Lookup user │
     │                   │                  │   (LabUser    │
     │                   │                  │    first,     │
     │                   │                  │    User fall- │
     │                   │                  │    back)      │
     │                   │                  │               │
     │                   │                  ├── Verify pw   │
     │                   │                  │   (bcrypt)    │
     │                   │                  │               │
     │                   │                  ├── Check lab   │
     │                   │                  │   active      │
     │                   │                  │               │
     │                   │                  ├── Warm perm   │
     │                   │                  │   version     │
     │                   │                  │   (→ Redis)   │
     │                   │                  │               │
     │                   │                  ├── Build JWT   │
     │                   │                  │   (30min) +   │
     │                   │                  │   Refresh     │
     │                   │                  │   (30d)       │
     │                   │                  │               │
     │                   │                  ├── Audit log   │
     │                   │                  │   login event │
     │                   │                  │               │
     │  Set-cookie       │                  │               │
     │  (httpOnly)       │                  │               │
     │  + JSON body      │                  │               │
     │◄──────────────────├─────────────────►│               │
     │                   │                  │               │
```

## MFA Login Flow

```
Password → 200 (mfa_required=true) → MFASession →
├── TOTP:    POST /mfa/verify → {token} → Full JWT
├── Passkey: navigator.credentials.get() -> {credential} → Full JWT
├── Backup:  POST /mfa/backup → {code} → Full JWT
└── Recovery: POST /mfa/recover → {token} → Full JWT + reset prompt
```

## OAuth2 Authorization Code Flow (with PKCE)

```
┌──────────┐           ┌──────────┐           ┌──────────────┐
│  Client  │           │   User   │           │  GULA Auth   │
│   App    │           │          │           │   Server     │
└────┬─────┘           └────┬─────┘           └──────┬───────┘
     │                      │                        │
     ├── Authorization Request ────────────────────►│
     │   (response_type=code,                        │
     │    code_challenge_method=S256,                │
     │    code_challenge=sha256(verifier))           │
     │                      │                        │
     │◄── Login + Consent ──┤                        │
     │                      │                        │
     │◄── Authorization Code ───────────────────────┤
     │                      │                        │
     ├── Token Request ────────────────────────────►│
     │   (grant_type=authorization_code,             │
     │    code_verifier=original_verifier)           │
     │                      │                        │
     │◄── Access Token + Refresh Token ─────────────┤
     │    + optional ID Token (OIDC)                │
     │                      │                        │
```

## Token Format

### Access Token (JWT, HS256)

```json
{
  "user_id": 1,
  "lab_id": 42,
  "role": "lab_admin",
  "perm_ver": 3,
  "type": "access",
  "jti": "uuid-v4",
  "exp": <30min>,
  "iat": <now>
}
```

### Refresh Token (JWT, HS256, separate secret)

```json
{
  "user_id": 1,
  "lab_id": 42,
  "role": "lab_admin",
  "perm_ver": 3,
  "type": "refresh",
  "jti": "uuid-v4",
  "exp": <30days>,
  "iat": <now>
}
```

## Token Lifecycle

```
Issue → Use → (optional) Refresh → Rotate → Revoke
           │                          │
           └── Check blacklist ───────┘
               (Redis JTI)

Session invalidation triggers:
  - Password change   → perm_version bumped
  - Role change       → perm_version bumped
  - Account deactivation → perm_version bumped
  - Explicit logout   → JTI blacklisted
  - All devices logout → perm_version bumped (all sessions)
```
