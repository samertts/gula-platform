# GULA Platform — Security Atlas

**Classification:** CONFIDENTIAL
**Date:** 2026-07-18
**Overall Security Rating:** 7.8/10 (B+)

---

## 1. Security Score Summary

| Domain | Score | Assessment |
|--------|-------|------------|
| Architecture & Threat Modeling | 85% | Strong foundation |
| Authentication | 80% | Good, gaps in lifecycle management |
| Session Management | 65% | Redis-dependent, fails open |
| Access Control | 90% | Excellent (RBAC + ABAC + tenant isolation) |
| Validation & Encoding | 75% | Good, gaps in output encoding |
| Stored Cryptography | 70% | No key rotation |
| Error Handling & Logging | 85% | Hash-chain audit, structured logging |
| Data Protection | 80% | Encryption at rest for national IDs |
| Communications | 75% | mTLS not implemented |
| **Overall** | **78%** | **7.8/10** |

---

## 2. Defense-in-Depth Architecture (4 Layers)

### Layer 1: Edge (Cloudflare)
- WAF with 9 custom + managed rules
- DDoS protection
- Bot detection (Workers)
- DNS + CDN
- Rate limiting

### Layer 2: Network (Nginx)
- TLS 1.2/1.3 with Let's Encrypt
- ModSecurity WAF (SQLi, XSS)
- Rate limiting (5 zones: auth=10/min, public=30/min, user=60/min, admin=20/min)
- API Gateway Nginx (127.0.0.1:8080)

### Layer 3: Application (FastAPI Middleware)
- JWT authentication (HS256, 30min TTL)
- RBAC (9 roles × 16 permissions)
- ABAC (attribute-based access control)
- MFA (TOTP + WebAuthn/FIDO2/Passkeys)
- OAuth2/OIDC provider + PKCE
- SAML 2.0 SSO
- Rate limiting in middleware
- Circuit breakers (DB + Redis)
- Startup guard blocks until ready

### Layer 4: Data
- Fernet AES-256 encryption at rest (national IDs)
- HMAC-signed national IDs + patient card tokens
- Hash-chain audit (SHA-256 with PG trigger, 100-entry HMAC checkpoints)
- Tenant isolation (lab_id filter on every patient-data query)
- Optimistic locking (version column on LabOrder + LabResult)

---

## 3. Authentication Methods

| Method | Status | Implementation |
|--------|--------|---------------|
| Password (bcrypt) | ✅ | Timing-safe login, minimum strength |
| JWT (HS256) | ✅ | 30min access, 30d refresh, jti blacklisting |
| OAuth2/OIDC | ✅ | Authorization code + PKCE |
| SAML 2.0 | ✅ | SSO integration |
| MFA (TOTP) | ✅ | Time-based one-time passwords |
| WebAuthn/FIDO2 | ✅ | Passkeys, hardware tokens |
| Service Accounts | ✅ | API key authentication |
| Password Reset | ⚠️ | No rate limit on reset endpoint |

---

## 4. RBAC Roles (9)

| Role | Level | Scope |
|------|-------|-------|
| master_admin | 100 | All permissions |
| ministry_admin | 90 | Read + platform management |
| province_admin | 80 | Province-scoped |
| admin / lab_admin | 50 | Full lab management |
| doctor | 40 | Read-only clinical |
| staff / lab_staff | 20 | Read/write orders/results |
| technician | 20 | Order/result read/write |
| citizen | 10 | Own data only |

**Permissions:** 16 string permissions (patients:read/write/delete, orders:read/write, results:read/write, staff:manage, lab:read/manage, dashboard:read, audit:read, platform:manage_labs/users/view_stats, system:admin)

---

## 5. Encryption Keys (Required, Hard Fail if Missing/Weak)

| Secret | Purpose | Rotation |
|--------|---------|----------|
| SECRET_KEY | JWT signing | ❌ Never rotated |
| REFRESH_TOKEN_SECRET | Refresh token signing | ❌ Never rotated |
| ENCRYPTION_KEY | Fernet (national IDs) | ❌ Never rotated |
| NID_HMAC_KEY | National ID HMAC | ❌ Never rotated |
| NID_HMAC_KEY_PREV | Key rotation (optional) | N/A |

---

## 6. Audit Hash Chain

| Property | Value |
|----------|-------|
| Algorithm | SHA-256(prev_hash + JSON(entry)) |
| Genesis | "0" × 64 |
| Integrity | PG trigger prevents UPDATE/DELETE |
| Checkpoints | HMAC every 100 entries (audit_anchors_{YYYY-MM}.log) |
| Coverage | All CREATE/UPDATE/DELETE, login/logout, permission changes, break-glass, AI decisions |

---

## 7. Critical Security Findings

| Finding | Risk Score | Priority |
|---------|-----------|----------|
| **Firebase security bypass** — frontend-v2 writes directly to Firestore, bypassing RBAC, ABAC, audit, rate limiting, encryption | 25/25 | P0 |
| **No LICENSE file** — Legal ambiguity for all users/contributors | 25/25 | P0 |
| **HS256 JWT** — Symmetric key distribution risk; no key rotation | 12/25 | P1 |
| **No automated secrets rotation** — All keys unchanged since deployment | 15/25 | P1 |
| **Rate limiting fails open** — Redis down = no rate limits | 12/25 | P1 |
| **Session revocation fails open** — Redis down = revoked tokens accepted | 12/25 | P2 |
| **No CSRF protection** — Browser clients vulnerable | 8/25 | P2 |
| **OAuth2 no key rotation** — Long-lived signing keys | 12/25 | P2 |
| **External AI provider PHI exposure** — Patient data to OpenAI/Google | 16/25 | P1 |
| **Emergency break-glass audit-only** — No access controls | 12/25 | P2 |
| **Push notification VAPID not configured** | 4/25 | P3 |

---

## 8. Security Testing

| Tool | Purpose | Status |
|------|---------|--------|
| Bandit | SAST — Python security analysis | ✅ 0 High, 2 Medium |
| Gitleaks | Secret detection in CI | ✅ 0 leaks |
| Safety | CVE scan of dependencies | ✅ CI-gated |
| Hadolint | Dockerfile linting | ✅ CI-gated |
| Trivy | Container vulnerability scan | ✅ CI-gated |
| Semgrep | Custom security rules | ✅ CI-gated |
| OWASP ZAP | DAST — dynamic application testing | ⚠️ Configured |
| npm audit | Frontend dependency scan | ❌ Not in CI |
| Frontend tests | XSS/DOM security testing | ❌ Missing |

---

## 9. Security Compliance

| Standard | Status |
|----------|--------|
| OWASP ASVS Level 2 | ⚠️ PARTIAL (78%) |
| OWASP Top 10 (2021) | ⚠️ PARTIAL |
| Zero Trust Architecture | ⚠️ PARTIAL (no mTLS) |
| C2M2 | ⚠️ PARTIAL |
| ISO 27001 | ❌ In progress |
| HIPAA | ❌ Not assessed |
| GDPR | ❌ Not assessed |
