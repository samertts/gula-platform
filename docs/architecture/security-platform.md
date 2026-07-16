# Security Platform — Architecture

## Overview

The GULA Security Platform provides defense-in-depth across all layers:
API, transport, application, database, desktop, mobile, and offline modes.

## Authentication

### Password Authentication
- **File**: `shared/auth/passwords.py`
- bcrypt hashing with per-user salts
- Timing-safe comparison, dummy hash prevents user enumeration

### JWT Tokens
- **File**: `shared/auth/jwt.py`, `backend/app/security/auth.py`
- Access tokens (30min) + Refresh tokens (30 days)
- JTI blacklist in Redis for immediate revocation
- perm_version in DB for full session invalidation
- Token rotation on refresh

### OAuth2 / OIDC
- **File**: `backend/app/security/oauth2_provider.py`
- Authorization code + PKCE (S256), Client Credentials, Refresh
- ID tokens, JWKS endpoint, OpenID Configuration
- Authorization endpoint, Token endpoint, Introspection, Revocation

### MFA
- **File**: `shared/auth/mfa.py`, `backend/app/security/mfa_service.py`
- TOTP (RFC 6238), HOTP (RFC 4226)
- WebAuthn / FIDO2 / Passkeys (`shared/auth/webauthn.py`)
- Backup codes, MFA sessions with time-limited tokens

### SAML
- **File**: `backend/app/security/saml_service.py`
- SAML 2.0 SSO with IdP metadata parsing

### Password Reset
- **File**: `backend/app/routes/password_reset.py`
- Token-based reset with 1-hour expiry
- SHA-256 hashed reset tokens in DB

### Service Accounts & API Keys
- **File**: `backend/app/security/service_accounts.py`
- `gula_` prefixed API keys with role/scoped permissions
- Key rotation, revocation, expiry

### Risk-Based Authentication
- **File**: `backend/app/services/risk_based_auth_service.py`
- Context-aware risk scoring (0-100)
- Factors: device trust, location, time, velocity, failed attempts, VPN/Tor
- Adaptive responses: proceed → step-up → MFA → block
- Impossible travel detection via Haversine distance

## Authorization

### RBAC (Role-Based)
- **File**: `shared/rbac/permissions.py`, `backend/app/security/rbac.py`
- 9 roles with hierarchical permissions
- Role-level hierarchy for management delegation

### ABAC (Attribute-Based)
- **File**: `backend/app/security/abac.py`
- Attribute conditions: equals, not_equals, in, not_in, greater_than, less_than, contains, matches
- Rule engine with priority ordering and resource/action indexing
- First-match-wins with DENY default

## API Security

- **File**: `backend/app/security/rate_limit.py`
- Redis-backed fixed-window rate limiting
- Per-IP, per-user, per-auth, per-admin tiers
- Dynamic IP blocking on abuse
- **File**: `backend/app/core/middleware.py` — Security headers, CORS, CSP, HSTS

## Cryptography

- **File**: `shared/security/encryption.py` — AES-256-GCM via Fernet
- **File**: `shared/security/hmac.py` — HMAC-SHA256 signing
- Envelope encryption for national IDs
- Key rotation support with key versioning
- National ID encryption at rest (never stored as plaintext)

## Device Trust

- **File**: `backend/app/services/device_trust_service.py`
- Device fingerprinting (UA, screen, fonts, canvas, WebGL, audio)
- Trust level escalation (UNKNOWN → TRUSTED)
- Automatic deactivation after 5 failed attempts

## Audit Platform

- **File**: `backend/app/services/audit_service.py`, `shared/audit/service.py`
- SHA-256 hash chain (tamper-evident)
- Anchor file HMAC checkpoints every 100 entries
- Previous key support for rotation
- Chain verification endpoint

## Threat Detection

- **File**: `backend/app/security/intrusion_detection.py`
- Time-windowed attempt tracking
- Per-IP caps with periodic cleanup
- Implicit brute force detection

## Risk Engine

- **File**: `backend/app/core/risk_engine.py`
- Action-level risk scoring (0-10)
- Factors: environment, data impact, frequency, blast radius, reversibility
- Thresholds: low (auto-approve), medium (log), high (warn), critical (block)

## Zero Trust Architecture

- Continuous verification on every request
- Least privilege via RBAC + ABAC
- Explicit authorization (deny by default)
- Policy enforcement at API gateway and application layer
- Context-aware with device, location, time, behavior signals

## Security Headers

- Content-Security-Policy
- Strict-Transport-Security
- X-Frame-Options: DENY
- X-Content-Type-Options: nosniff
- Referrer-Policy: strict-origin-when-cross-origin

## Offline Security

- Encrypted local database (AES-256-GCM)
- Signed synchronization operations
- Replay attack prevention via nonces
- Conflict validation before merge
- Offline audit trail
