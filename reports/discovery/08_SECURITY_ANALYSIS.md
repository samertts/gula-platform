# GULA Platform — Security Analysis
**Date:** 2026-07-17

---

## 1. Security Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    Defense-in-Depth Layers                       │
├─────────────────────────────────────────────────────────────────┤
│  TLS 1.2/1.3  ←  Host Nginx (SSL termination)                   │
│  WAF          ←  ModSecurity (SQLi, XSS blocking)               │
│  Rate Limit   ←  Nginx: 10r/s general, 100r/min per IP API     │
│  DDoS         ←  Cloudflare (configured)                        │
│  IDS          ←  Snort rules + Fail2ban                         │
├─────────────────────────────────────────────────────────────────┤
│  JWT Auth     ←  HS256, 30min TTL, refresh rotation             │
│  RBAC         ←  9 roles × 13+ permissions                      │
│  ABAC         ←  Attribute rules (subject, resource, env)       │
│  MFA          ←  TOTP + WebAuthn/FIDO2/Passkeys                 │
│  OAuth2/OIDC  ←  Full authorization server + PKCE               │
│  SAML 2.0     ←  Enterprise SSO                                 │
├─────────────────────────────────────────────────────────────────┤
│  Encryption   ←  Fernet AES-256 at rest                         │
│  HMAC         ←  Signed national IDs + patient card tokens      │
│  Audit        ←  Hash chain (SHA-256) + PG trigger + HMAC files │
│  Rate Limit   ←  4 tiers (auth:10/min, user:60/min, etc.)        │
│  Firewall     ←  API firewall (Redis + local dual-write)        │
│  Circuit      ←  DB/Redis circuit breakers (3 degradation L)    │
├─────────────────────────────────────────────────────────────────┤
│  Startup Guard→  Sealed until DB reachable + migrations checked │
│  Secrets      ←  No defaults, weak-pattern detection (15+)      │
│  Headers      ←  CSP, HSTS, XFO, XSS-Protection, Referrer      │
│  CORS         ←  Whitelist origins only                         │
│  Tenant ISO   ←  All queries filter by lab_id                   │
└─────────────────────────────────────────────────────────────────┘
```

---

## 2. Authentication

### JWT Configuration (`security/auth.py` + `shared/auth/jwt.py`)

| Parameter | Value |
|-----------|-------|
| Algorithm | HS256 (HMAC-SHA256) |
| Access Token TTL | 30 minutes (configurable) |
| Refresh Token TTL | 30 days |
| Payload | user_id, lab_id, role, perm_version, jti, type, exp, iat |
| Blacklisting | Redis-backed (`blacklist:jti:{jti}`) |
| Secret Key | From SECRET_KEY env var (hard fail if missing/weak) |
| Refresh Secret | Separate REFRESH_TOKEN_SECRET |

### Login Security
- **Timing-safe**: Uses pre-computed dummy bcrypt hash to prevent user enumeration
- **Rate limited**: 10 attempts/min per IP (RATE_LIMIT_AUTH)
- **Password hashing**: bcrypt cost 12
- **Failed attempts tracked**: IntrusionDetector (10 attempts/300s window → block)

---

## 3. Authorization

### RBAC (Role-Based Access Control)

**9 Roles with Hierarchical Levels:**
| Role | Level | Scope |
|------|-------|-------|
| master_admin | 100 | All permissions |
| ministry_admin | 90 | Read + platform management |
| province_admin | 80 | Province-scoped admin |
| admin / lab_admin | 50 | Full lab management |
| doctor | 40 | Read-only clinical |
| staff / lab_staff | 20 | Read/write orders/results |
| technician | 20 | Order/result read/write |
| citizen | 10 | Own data only |

**16 String Permissions:**
`patients:read/write/delete`, `orders:read/write`, `results:read/write`, `staff:manage`, `lab:read/manage`, `dashboard:read`, `audit:read`, `platform:manage_labs/users/view_stats`, `system:admin`

### ABAC (Attribute-Based Access Control)
- Full rule engine with operators: equals, not_equals, in, not_in, greater_than, less_than, contains, matches (regex)
- Context merges subject (user), resource, and environment attributes
- Priority-ordered rules with ALLOW/DENY effects
- Default deny

### Tenant Isolation (ABAC at query level)
- All patient-data queries filter by `lab_id = current_user.lab_id`
- `require_own_lab()` dependency enforces at route level
- Platform roles (master_admin, ministry_admin) bypass
- Cross-lab access blocked (returns empty results, not 403)

### Feature Gate Enforcement
- `require_feature()` — checks subscription tier
- `require_feature_for_lab()` — per-lab feature flag
- `assert_lab_within_limit()` — subscription limits

---

## 4. Multi-Factor Authentication

- **TOTP**: Setup with pyotp, QR URI, backup codes
- **WebAuthn/FIDO2/Passkeys**: Full registration + auth flows
- **MFA Sessions**: Temporary tokens (10min TTL) for step-up auth
- **Multiple devices**: Supported per user

---

## 5. OAuth 2.0 / OpenID Connect

- **Full authorization server** mounted at `/oauth2/`
- **Grant types**: authorization_code, client_credentials, refresh_token
- **PKCE**: S256 and plain methods supported
- **OIDC**: `.well-known/openid-configuration`, id_token, JWKS endpoint
- **Token introspection**: RFC 7662
- **Token revocation**: RFC 7009
- **Client auth**: client_secret_basic, client_secret_post, none
- **Scopes**: openid, profile, email, read, write

---

## 6. SAML 2.0

- Assertion parsing (base64 + defusedxml)
- Validation: issuer, audience, time validity (NotBefore/NotOnOrAfter + clock skew)
- Attribute extraction (NameID, AttributeStatement)
- SP metadata generation

---

## 7. Encryption

### At Rest
| Data | Method | Key |
|------|--------|-----|
| Passwords | bcrypt (cost 12) | N/A (one-way) |
| National IDs | Fernet AES-256 + HMAC-SHA256 | ENCRYPTION_KEY + NID_HMAC_KEY |
| JWT Tokens | HS256 | SECRET_KEY |
| Refresh Tokens | HS256 | REFRESH_TOKEN_SECRET |
| Patient Card Tokens | HMAC-SHA256 | DEVICE_HMAC_KEY |

### Format for encrypted NIDs
```
{fernet_encrypted_data}.{hmac_signature}
```

### Key Rotation
- Previous HMAC keys supported via `NID_HMAC_KEY_PREV` env var
- Session invalidation via `bump_perm_version()` (role/password changes)

---

## 8. Audit Logging

### Hash Chain
- `chain_hash = SHA-256(previous_hash + JSON(entry))`
- Genesis hash: `"0" * 64`
- PostgreSQL trigger prevents UPDATE/DELETE

### HMAC Checkpoints
- Every 100 entries → HMAC-SHA256 written to file
- File: `audit_anchors_{YYYY-MM}.log`
- Directory: `AUDIT_ANCHOR_DIR`
- Verification: `verify_audit_chain()` re-computes chain

### Audit Coverage
- All mutations (CREATE, UPDATE, DELETE)
- Login/logout events
- Permission changes
- Emergency consent access (break-glass)
- AI decisions (if configured)

---

## 9. Rate Limiting

| Limiter | Key | Default Rate | Hard Block |
|---------|-----|-------------|------------|
| `rate_limit_public()` | IP | 30/min | 150/min |
| `rate_limit_user()` | user + IP | 60/min | 300/min |
| `rate_limit_auth()` | IP | 10/min | 50/min |
| `rate_limit_admin()` | admin:user + IP | 20/min | 100/min |

Dynamic IP blocking: 5x limit → hard block for `RATE_LIMIT_BLOCK_DURATION_SECONDS` (default 1 hour)

---

## 10. API Security

### Middleware Security Headers
```
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
X-XSS-Protection: 1; mode=block
Referrer-Policy: strict-origin-when-cross-origin
Permissions-Policy: camera=(), microphone=(), geolocation=()
Cross-Origin-Opener-Policy: same-origin
Content-Security-Policy: default-src 'self'; ...
Strict-Transport-Security: max-age=31536000; includeSubDomains
Cache-Control: no-store, no-cache, must-revalidate
```

### CORS
- Whitelist origins from CORS_ORIGINS env var
- Dev fallback includes localhost + Google AI Studio + Claude
- Methods: GET, POST, PUT, DELETE, PATCH, OPTIONS
- Credentials: true

### API Firewall (`firewall/api_firewall.py`)
- Redis-backed IP blocklist with fail-closed guarantee
- Dual-write: Redis + local in-memory store
- Max 5,000 local entries (oldest 20% evicted)
- Max 1 hour local TTL

---

## 11. Security Configuration

### Weak Secret Detection (15+ patterns)
```
default, change, secret, example, test, demo, gula_default,
changeme, password, 12345, abcdef, admin, qwerty, letmein,
welcome, pass, 00000, 11111
```

### Required Secrets (hard fail in production)
| Secret | Config Key | Validation |
|--------|-----------|------------|
| SECRET_KEY | `SECRET_KEY` | Present + not weak |
| REFRESH_TOKEN_SECRET | `REFRESH_TOKEN_SECRET` | Present + not weak |
| ENCRYPTION_KEY | `ENCRYPTION_KEY` | Present + not weak + Fernet-valid |
| NID_HMAC_KEY | `NID_HMAC_KEY` | Present + not weak |

---

## 12. Service Accounts

- API key format: `gula_{ulid}_{random_hex}`
- Keys bcrypt-hashed before storage
- Support roles, scopes, expiry dates
- `last_used_at` tracking

---

## 13. Security Testing

| Tool | Scope | Findings |
|------|-------|----------|
| Bandit | SAST | 0 High, 2 Medium |
| Gitleaks | Secret scanning | 0 leaks (CI) |
| Safety | CVE scan | Dependency check |
| Hadolint | Dockerfile lint | Config compliance |
| Semgrep | Custom rules | Configured |
| OWASP ZAP | DAST | Configured |

---

## 14. Critical Security Findings

| Finding | Evidence | Risk |
|---------|----------|------|
| **Firebase bypasses backend security** | frontend-v2 talks directly to Firestore | **CRITICAL** |
| **Emergency break-glass is audited but uncontrolled** | `consent_dep.py` allows doctors to bypass consent | **HIGH** |
| **HS256 (HMAC) — no RS256/ES256** | JWT uses symmetric key | **HIGH** — key distribution risk |
| **No JWT kid header** | No key rotation support | **MEDIUM** |
| **Rate limit bypass in test mode** | `ENV=test` skips rate limiting | **LOW** — test only |
| **No evidence of secrets rotation** | No automated rotation in CI/CD | **HIGH** |
| **OAuth2 uses HS256 for id_tokens** | JWKS endpoint empty for HMAC | **MEDIUM** — OIDC compliance gap |
| **Redis password from env** | REDIS_PASSWORD in plaintext env | **MEDIUM** |
