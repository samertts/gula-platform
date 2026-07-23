# GULA Identity Platform — Architecture Document

> Generated: 2026-07-23T11:23:43.291738+00:00
> Program: PROGRAM-IDENTITY-ENTERPRISE-001

## Overview

GULA Identity Platform serves as the **single trusted identity provider** for
the entire GULA ecosystem. No subsystem implements its own authentication or
authorization independently.

## Identity Domains

| Domain | Description | Model | File |
|--------|-------------|-------|------|
| **Users** | Citizen, patient, and healthcare professional identities | `User` | `backend/app/models/user.py` |
| **Lab Users** | Laboratory staff, technicians, and admin users | `LabUser` | `backend/app/models/lab_user.py` |
| **Citizens** | Canonical national identity (MPI) — one row per person | `Citizen` | `backend/app/services/mpi/models.py` |
| **Service Accounts** | Machine-to-machine API keys with scoped access | `ServiceAccount` | `backend/app/models/service_account.py` |
| **OAuth2 Clients** | Third-party applications registered for delegated auth | `OAuth2Client` | `backend/app/models/oauth2_client.py` |
| **OAuth2 Tokens** | Issued access/refresh tokens for OAuth2 flows | `OAuth2Token` | `backend/app/models/oauth2_token.py` |
| **MFA Devices** | Multi-factor authenticators (TOTP, WebAuthn, backup) | `MFADevice` | `backend/app/models/mfa_device.py` |
| **MFA Sessions** | Partial-auth sessions bridging password → MFA | `MFASession` | `backend/app/models/mfa_device.py` |

## Architecture Layers

```
┌─────────────────────────────────────────────────────┐
│                   Frontend (React SPA)                │
│         AuthContext → api/client.ts → Bearer JWT      │
└──────────────────┬──────────────────────────────────┘
                   │ HTTP (Bearer / httpOnly cookie)
┌──────────────────▼──────────────────────────────────┐
│            API Gateway (Docker nginx)                 │
│                 127.0.0.1:8080                        │
└──────────────────┬──────────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────────┐
│         FastAPI Monolith (gula-backend)              │
│                                                      │
│  Dependencies Layer (dependencies.py)                 │
│  ├── get_current_user (JWT decode + blacklist)        │
│  ├── require_permission (permission check)            │
│  ├── require_service_account (dual-path API key/JWT)  │
│  └── get_current_lab (lab context extraction)         │
│                                                      │
│  Auth Layer (auth.py + shared/auth/jwt.py)            │
│  ├── JWT encode/decode (HS256)                        │
│  ├── Token blacklist (Redis JTI)                      │
│  ├── Perm-version session invalidation                │
│  ├── Refresh token rotation                           │
│  └── Dummy hash timing-safe login                     │
│                                                      │
│  Session Layer (session.py)                           │
│  ├── bump_perm_version (invalidate sessions)          │
│  ├── get_perm_version (O(1) Redis fast path)          │
│  └── warm_perm_version (post-login)                   │
│                                                      │
│  Authorization Layer (rbac.py + authorization.py)     │
│  ├── RBAC: 9 roles × 16 permissions                  │
│  ├── ABAC: Policy engine with JSON conditions         │
│  ├── FieldSecurity: Field-level access control        │
│  ├── Delegation: Time-bound role delegation           │
│  ├── BreakGlass: Emergency access sessions            │
│  └── UserTypeEnum: 40+ user types                     │
│                                                      │
│  OAuth2 Server (oauth2.py + oauth2_provider.py)       │
│  ├── Authorization Code + PKCE                        │
│  ├── Client Credentials (machine-to-machine)          │
│  ├── Refresh Token rotation                           │
│  ├── Token introspection + revocation                 │
│  └── OIDC Discovery + ID Token + JWKS                 │
│                                                      │
│  MFA Layer (shared/auth/mfa.py + webauthn.py)         │
│  ├── TOTP (time-based one-time passwords)             │
│  ├── WebAuthn/FIDO2 (passkeys)                        │
│  ├── HOTP (counter-based)                             │
│  ├── Backup codes + recovery tokens                   │
│  └── MFASession (partial auth bridge)                 │
│                                                      │
│  Identity Governance (MPI)                            │
│  ├── Citizen deduplication (Fellegi-Sunter)           │
│  ├── Blocking + scoring + auto-merge pipeline         │
│  ├── IdentityClaim bridge (lab patient → citizen)     │
│  ├── MergeAudit hash-chained ledger                   │
│  └── CanonicalPatient unification                     │
│                                                      │
│  Tenant Model (tenant.py + organization.py)           │
│  ├── Tenant → Organization → Facility hierarchy       │
│  ├── Per-tenant feature flags                         │
│  ├── Subscription-tier resource limits                │
│  └── Bilingual naming (en/ar)                         │
└──────────────────┬──────────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────────┐
│         Data Layer (PostgreSQL + Redis)              │
│  ├── Users, LabUsers, Citizens (PostgreSQL)           │
│  ├── OAuth2 tokens, MFA devices (PostgreSQL)          │
│  ├── JWT blacklist, perm_version cache (Redis)        │
│  ├── Rate limiting counters (Redis)                   │
│  ├── Session data (Redis)                             │
│  └── Audit logs (PostgreSQL, hash-chained)            │
└─────────────────────────────────────────────────────┘
```

## Key File Inventory

| File | Lines | Purpose |
|------|-------|---------|
| `shared/auth/jwt.py` | 84 | Core JWT encode/decode (HS256) |
| `shared/auth/mfa.py` | 66 | TOTP, HOTP, backup codes, recovery tokens |
| `shared/auth/webauthn.py` | 108 | WebAuthn/FIDO2 passkey support |
| `shared/rbac/permissions.py` | 233 | RBAC role/permission matrix (9 roles, 16+ perms) |
| `backend/app/security/auth.py` | 117 | JWT blacklist, token creation, dummy hash |
| `backend/app/security/rbac.py` | 150 | RBAC backend + ABAC helpers |
| `backend/app/security/dependencies.py` | 159 | FastAPI DI (get_current_user, require_permission) |
| `backend/app/security/session.py` | 98 | Perm-version cache (Redis) |
| `backend/app/security/service_accounts.py` | 86 | API key CRUD + validation |
| `backend/app/security/oauth2_provider.py` | 193 | OAuth2 authorization server + OIDC |
| `backend/app/security/rate_limit.py` | 202 | 4-tier rate limiting |
| `backend/app/models/authorization.py` | 227 | 10 authorization DB models |
| `backend/app/models/user.py` | 41 | User model (15 identity fields) |
| `backend/app/models/lab_user.py` | 44 | LabUser model (identity + auth fields) |
| `backend/app/routes/login.py` | 228 | Login/logout endpoints |
| `backend/app/routes/register.py` | 656 | Registration (lab, citizen, staff, doctor) |
| `backend/app/routes/oauth2.py` | 388 | OAuth2/OIDC endpoints |
| `backend/app/routes/authorization.py` | 654 | AuthZ management endpoints |
| `backend/app/services/mpi/resolver.py` | 400 | MPI dedup pipeline orchestrator |
| `backend/app/services/mpi/matcher.py` | 215 | Fellegi-Sunter probabilistic scorer |

## Identity Flow Summary

```
Login:    Password → JWT (30min) + Refresh (30d) → httpOnly cookie + JSON
MFA:      Password → MFASession → TOTP/WebAuthn → Full JWT
    API Key:  gula_{uuid}_{hex} → require_service_account → dual-path (key or JWT)
OAuth2:   Client → Authorization Code (PKCE) → Token → Introspection
Logout:   JTI blacklist (Redis) + perm_version bump → all sessions invalidated
Refresh:  Old token revoked → New token issued with rotation
Delegation: Delegator → Delegation (time-bound, scoped) → Delegate acts on behalf
Break Glass: Emergency → Justification → Time-limited access → Audit → Review
```
