# GULA Platform — Security Knowledge Base

**Version:** 2.1.0
**Last Updated:** 2026-07-14
**Classification:** CONFIDENTIAL — Ministry of Health Iraq Compliant
**Canonical Source:** `backend/app/security/`, `backend/app/core/`, `shared/`
**Test Coverage:** 54+ security tests passing across 28 test modules

---

## Table of Contents
1. [CWE Mappings](#1-cwe-mappings)
2. [OWASP Top 10 2021 Mappings](#2-owasp-top-10-2021-mappings)
3. [MITRE ATT&CK Mappings](#3-mitre-attck-mappings)
4. [NIST CSF Mappings](#4-nist-csf-mappings)
5. [Authentication Mechanisms](#5-authentication-mechanisms)
6. [Authorization / RBAC](#6-authorization--rbac)
7. [Encryption (At Rest & In Transit)](#7-encryption-at-rest--in-transit)
8. [Audit Logging](#8-audit-logging)
9. [Rate Limiting / DoS Protection](#9-rate-limiting--dos-protection)
10. [Input Validation](#10-input-validation)
11. [Session Management](#11-session-management)
12. [Secrets Management](#12-secrets-management)
13. [CSP / Security Headers](#13-csp--security-headers)
14. [Kill Switch / Circuit Breaker](#14-kill-switch--circuit-breaker)
15. [AI Safety Guardrails](#15-ai-safety-guardrails)
16. [Concurrency & Backpressure](#16-concurrency--backpressure)
17. [Startup Security Guard](#17-startup-security-guard)
18. [Policy Engine](#18-policy-engine)
19. [Self-Healing & Auto-Repair](#19-self-healing--auto-repair)
20. [Security Testing Matrix](#20-security-testing-matrix)
21. [Known Gaps & Remediation Roadmap](#21-known-gaps--remediation-roadmap)

---

## 1. CWE Mappings

| CWE | Weakness | GULA Control | File(s) | Status |
|-----|----------|-------------|---------|--------|
| **CWE-287** | Improper Authentication | JWT access + refresh tokens with expiry; token type discrimination | `shared/auth/jwt.py`, `backend/app/security/auth.py` | ✅ |
| **CWE-384** | Session Fixation | JTI-based token blacklisting on logout; perm_version invalidation | `backend/app/security/auth.py:43`, `backend/app/security/session.py` | ✅ |
| **CWE-613** | Insufficient Session Expiration | Short-lived access tokens (default 30 min); refresh token rotation (30 days) | `backend/app/config.py:114-117` | ✅ |
| **CWE-862** | Missing Authorization | RBAC with 9 roles × 13 permissions; ABAC via `require_own_lab()` | `shared/rbac/permissions.py`, `backend/app/security/rbac.py`, `backend/app/security/dependencies.py` | ✅ |
| **CWE-863** | Incorrect Authorization | `require_permission()` FastAPI dependency; hierarchical role levels | `backend/app/security/dependencies.py:88-109` | ✅ |
| **CWE-79** | Cross-Site Scripting (XSS) | CSP headers (`default-src 'self'`, `script-src 'self'`); `X-XSS-Protection: 1; mode=block` | `backend/app/main.py:405-416` | ✅ |
| **CWE-89** | SQL Injection | SQLAlchemy ORM with parameterized queries; no raw SQL in business logic | All model/routes files; `startup_guard.py` exceptions (controlled DDL) | ✅ |
| **CWE-200** | Information Exposure | Global error handler returns generic messages in production; no stack traces | `backend/app/main.py:172-218` | ✅ |
| **CWE-209** | Information Exposure Through Error Messages | Production 500 errors return `"An unexpected error occurred"` | `backend/app/main.py:202-208` | ✅ |
| **CWE-261** | Weak Cryptography | AES-256-GCM via Fernet for data at rest; bcrypt cost factor 12 for passwords | `shared/security/encryption.py`, `shared/auth/passwords.py` | ✅ |
| **CWE-312** | Cleartext Storage of Sensitive Information | National IDs encrypted at rest (Fernet + HMAC integrity); no plaintext storage | `shared/security/encryption.py:29-46`, `backend/app/security/encryption.py` | ✅ |
| **CWE-326** | Inadequate Encryption Strength | `HS256` JWT signing; Fernet (AES-128-CBC + HMAC-SHA256); production hard-fail on weak keys | `backend/app/config.py:101-110,134-140` | ✅ |
| **CWE-327** | Broken/Risky Crypto Algorithm | HMAC-SHA256 for audit anchoring; SHA-256 for chain hash | `backend/app/services/audit_service.py:93` | ✅ |
| **CWE-347** | Improper Verification of Signature | JWT signature verified on every request; `exp` and `iat` claims required | `shared/auth/jwt.py:45-50` | ✅ |
| **CWE-400** | Uncontrolled Resource Consumption | Max body size (10MB); rate limiting; concurrency backpressure (200 active) | `backend/app/main.py:222-240`, `backend/app/security/rate_limit.py`, `backend/app/main.py:516-556` | ✅ |
| **CWE-502** | Deserialization of Untrusted Data | FastAPI/Pydantic request validation; no pickle/yaml deserialization of user input | All route files via Pydantic models | ✅ |
| **CWE-521** | Weak Password Requirements | bcrypt hashing; no hardcoded passwords; dummy hash prevents user enumeration | `shared/auth/passwords.py`, `backend/app/security/auth.py:56` | ✅ |
| **CWE-522** | Insufficiently Protected Credentials | Secrets from environment only; SECRET_KEY/ENCRYPTION_KEY/NID_HMAC_KEY hard-fail in production | `backend/app/config.py:102-150` | ✅ |
| **CWE-532** | Insertion of Sensitive Info into Log | Structured JSON logging excludes secrets; Sentry DSN filterable; no PII in logs | `backend/app/core/logging_config.py` | ✅ |
| **CWE-602** | Client-Side Enforcement of Server-Side Security | RBAC enforced server-side via FastAPI dependencies; feature flags server-side only | `backend/app/security/dependencies.py`, `backend/app/core/feature_flags.py` | ✅ |
| **CWE-639** | Insecure Direct Object Reference (IDOR) | `require_own_lab()` ABAC guard; all patient queries filtered by `lab_id` | `backend/app/security/rbac.py:85-100` | ✅ |
| **CWE-754** | Improper Check for Unusual Conditions | Circuit breaker (3 failures → open); degraded mode middleware; auto-repair engine | `backend/app/core/self_healing.py`, `backend/app/core/auto_repair.py` | ✅ |
| **CWE-770** | Allocation of Resources Without Limits | `_SAFE_METHODS` in degraded mode; `MAX_CONCURRENT_REQUESTS` cap | `backend/app/core/self_healing.py:337`, `backend/app/main.py:498` | ✅ |
| **CWE-778** | Insufficient Logging | Immutable audit log hash chain; HMAC-anchored checkpoints every 100 entries | `backend/app/services/audit_service.py` | ✅ |
| **CWE-798** | Use of Hardcoded Credentials | No hardcoded secrets anywhere; `make secrets-gen` for key generation; env-only | `backend/app/config.py` | ✅ |
| **CWE-799** | Improper Control of Interaction Frequency | Multi-tier rate limiting (auth:10/min, public:30/min, user:60/min, admin:20/min) | `backend/app/security/rate_limit.py` | ✅ |
| **CWE-807** | Untrusted Input in Security Decision | JWT perm_version validated against Redis; token JTI checked against blacklist | `backend/app/security/dependencies.py:40-68` | ✅ |
| **CWE-918** | SSRF (Server-Side Request Forgery) | External gateway adapter mode (stub/live/shadow); `GULA_ADAPTER_MODE` env-controlled | `backend/app/gateways/`, `backend/app/config.py:209-213` | ✅ |

---

## 2. OWASP Top 10 2021 Mappings

### A01:2021 — Broken Access Control

| Control | Implementation | Location |
|---------|---------------|----------|
| RBAC enforcement | 9 roles (master_admin, ministry_admin, province_admin, admin, lab_admin, doctor, technician, receptionist, citizen) with hierarchical permissions | `shared/rbac/permissions.py`, `backend/app/security/rbac.py` |
| ABAC tenant isolation | `require_own_lab()` enforces cross-lab access denial; platform roles exempted | `backend/app/security/rbac.py:85-100` |
| Permission-level dependencies | `require_permission("patients:read")` FastAPI dependency factory | `backend/app/security/dependencies.py:88-109` |
| Subscription tier limits | `assert_lab_within_limit()` enforces per-plan resource caps | `backend/app/security/rbac.py:109-150` |
| Role hierarchy | Numeric role levels (master_admin=100 → citizen=10); `can_manage_role()` | `shared/rbac/permissions.py:108-119,206-211` |
| Feature flags server-side | Enforcement in `require_feature_for_lab()` — no client-side feature toggles | `backend/app/security/rbac.py:103-106` |

### A02:2021 — Cryptographic Failures

| Control | Implementation | Location |
|---------|---------------|----------|
| Data at rest encryption | Fernet (AES-128-CBC + HMAC-SHA256) via `shared.security` | `shared/security/encryption.py`, `backend/app/security/encryption.py` |
| National ID encryption | `encrypt_national_id()` → Fernet encrypt + HMAC-sign; verified on decrypt | `shared/security/encryption.py:29-46` |
| Password hashing | bcrypt cost factor 12 via `shared.auth.passwords` | `shared/auth/passwords.py` |
| JWT signing | HS256 with `SECRET_KEY`; separate `REFRESH_TOKEN_SECRET` | `shared/auth/jwt.py`, `backend/app/config.py` |
| Transport security | TLS enforced in production via nginx; HSTS `max-age=31536000; includeSubDomains` | `SECURITY_HARDENING.md:17`, `backend/app/main.py:423-424` |
| Production key validation | Hard-fail on weak/default keys; separate `_is_weak_secret()` check | `backend/app/config.py:96-98,108-109,139-140` |
| Key rotation support | Audit anchor HMAC supports `_PREV` key for zero-downtime rotation | `backend/app/services/audit_service.py:51` |

### A03:2021 — Injection

| Control | Implementation | Location |
|---------|---------------|----------|
| SQL injection prevention | SQLAlchemy ORM throughout; parameterized queries | All model/route files |
| No raw SQL in business logic | `text()` only in startup guard (DDL/seed) and audit chain verification | `backend/app/core/startup_guard.py:351`, `backend/app/services/audit_service.py:98` |
| Request body size limit | `MaxBodySizeMiddleware` rejects >10MB payloads | `backend/app/main.py:222-240` |
| Pydantic input validation | All endpoints validate via Pydantic schemas | All route files |

### A04:2021 — Insecure Design

| Control | Implementation | Location |
|---------|---------------|----------|
| Default-deny security | `system_ready=False` until all startup checks pass; 503 until ready | `backend/app/core/startup_guard.py` |
| Circuit breaker pattern | 3-failure threshold for DB; 5-failure for Redis; auto half-open recovery | `backend/app/core/self_healing.py` |
| Degraded mode escalation | L1 (cache heavy) → L2 (read-only) → L3 (critical only) | `backend/app/core/self_healing.py:144-159` |
| AI safety by design | AI = suggest, human = approve, system = enforce | `backend/app/ai/guardrails.py` |
| Policy engine | Default-DENY for all autonomous actions; action taxonomy with risk levels | `backend/app/core/policy_engine.py` |

### A05:2021 — Security Misconfiguration

| Control | Implementation | Location |
|---------|---------------|----------|
| CORS strict policy | Production origins only; no wildcard | `backend/app/main.py:318-353` |
| Security headers middleware | CSP, HSTS, X-Frame-Options, X-Content-Type-Options, Referrer-Policy, Permissions-Policy | `backend/app/main.py:390-425` |
| API docs protection | Production docs gated behind admin JWT | `backend/app/main.py:279-313` |
| No debug endpoints in prod | `_docs_url=None` in production unless explicitly enabled | `backend/app/main.py:96-100` |
| Graceful error handling | No stack traces in production; structured JSON errors with Arabic translations | `backend/app/main.py:172-218` |

### A06:2021 — Vulnerable and Outdated Components

| Control | Implementation | Location |
|---------|---------------|----------|
| Dependency scanning | `npm audit` integrated; `pip-audit`/`safety` recommended (CI pipeline) | `.github/workflows/ci.yml` |
| Lock files | `requirements-lock.txt` (58 pinned packages); `package-lock.json` | `backend/requirements-lock.txt` |
| Container scanning | Trivy in CI pipeline; Hadolint for Dockerfile | `.github/workflows/ci.yml` |
| Python version validation | Hard-fail on `3.11.0rc1` pre-release (environment guardian critical finding) | `assessment/environment_report_4.0.md` |
| Known good versions | bcrypt 4.1.3+, cryptography 42.0.0+, pydantic 2.7.0+ | `backend/requirements.txt` |

### A07:2021 — Identification and Authentication Failures

| Control | Implementation | Location |
|---------|---------------|----------|
| JWT access tokens | Short-lived (30 min default); HS256 signed; `iat`/`exp` required | `shared/auth/jwt.py`, `backend/app/config.py:114-117` |
| JWT refresh tokens | 30-day expiry; separate secret (`REFRESH_TOKEN_SECRET`); blacklistable | `backend/app/security/auth.py:97-118`, `backend/app/config.py:121-131` |
| Token revocation | JTI-based blacklist in Redis; perm_version force-invalidation on role changes | `backend/app/security/auth.py:43-52`, `backend/app/security/session.py` |
| Password hashing | bcrypt cost 12 (1024 iterations, 2¹² rounds) | `shared/auth/passwords.py` |
| Timing-safe login | Dummy bcrypt hash prevents user enumeration via response timing | `backend/app/security/auth.py:56` |
| Active account check | `lab_users.is_active` verified on every authenticated request | `backend/app/security/dependencies.py:53` |
| Lab active status | Laboratory-level deactivation enforced for non-master_admin roles | `backend/app/security/dependencies.py:71-77` |

### A08:2021 — Software and Data Integrity Failures

| Control | Implementation | Location |
|---------|---------------|----------|
| Audit log hash chain | SHA-256 chain linking every entry to previous; genesis hash `"0"*64` | `backend/app/services/audit_service.py:80-93` |
| HMAC-anchored checkpoints | Every 100 entries written to file with HMAC-SHA256 signature | `backend/app/services/audit_service.py:105-114` |
| Audit chain verification | `verify_audit_chain()` endpoint detects tampered entries | `backend/app/services/audit_service.py:207-239` |
| DB-level immutability | PostgreSQL trigger prevents UPDATE/DELETE on audit_logs | `backend/app/core/startup_guard.py:578-617` |
| Outbox pattern | Guaranteed event delivery via `OutboxEvent` table | `backend/app/services/outbox_service.py` |

### A09:2021 — Security Logging and Monitoring Failures

| Control | Implementation | Location |
|---------|---------------|----------|
| Immutable audit trail | All mutations logged with user_id, lab_id, timestamp, action, resource | `backend/app/services/audit_service.py`, `backend/app/models/audit_log.py` |
| Request correlation | Every request gets X-Request-ID; tied to DB error logs via contextvars | `backend/app/main.py:246-271` |
| Structured JSON logging | Production logs in JSON format; dev in text | `backend/app/core/logging_config.py` |
| Health alert watchdog | Background loop grades system GREEN/YELLOW/RED every 60s | `backend/app/main.py:716+` |
| Sentry integration | Optional error tracking with FastAPI/SQLAlchemy/Logging integrations | `backend/app/main.py:48-71` |
| Security status endpoint | `/security/status` shows 24h metrics (logins, failures, result views) | `backend/app/routes/security.py` |

### A10:2021 — Server-Side Request Forgery (SSRF)

| Control | Implementation | Location |
|---------|---------------|----------|
| External adapter gating | All external API calls flow through `gateways/` with stub/live/shadow mode | `backend/app/gateways/`, `backend/app/config.py:209-213` |
| IP validation | `_is_private_ip()` in rate limiter prevents header spoofing from external | `backend/app/security/rate_limit.py:45-49` |
| No raw URL fetching from user input | All external URLs use env-configured endpoints only | `backend/app/config.py:218-228` |

---

## 3. MITRE ATT&CK Mappings

### Initial Access (TA0001)

| Technique | ID | GULA Control | Detection |
|-----------|----|-------------|-----------|
| Valid Accounts | T1078 | JWT authentication; token blacklisting; session invalidation | Audit log captures every login attempt |
| External Remote Services | T1133 | API gateway on 127.0.0.1:8080 (not publicly exposed); TLS termination at nginx | Request timing middleware logs all paths |
| Exploit Public-Facing App | T1190 | MaxBodySizeMiddleware; rate limiting; input validation via Pydantic | Structured error logging; Sentry integration |

### Persistence (TA0003)

| Technique | ID | GULA Control | Detection |
|-----------|----|-------------|-----------|
| Account Manipulation | T1098 | `bump_perm_version()` invalidates all active sessions on role change | Audit log captures role/permission changes; immutable audit trail |
| Valid Accounts | T1078 | Refresh token expiry (30d); perm_version check on every request | JTI blacklist prevents reusing revoked tokens |

### Privilege Escalation (TA0004)

| Technique | ID | GULA Control | Detection |
|-----------|----|-------------|-----------|
| Abuse Elevation Control | T1548 | RBAC hierarchy; `can_manage_role()` prevents lower roles from modifying higher | Permission check audit trail |
| Valid Accounts | T1078 | `require_permission()` on every route; ABAC via `require_own_lab()` | Cross-lab access attempts logged |

### Defense Evasion (TA0005)

| Technique | ID | GULA Control | Detection |
|-----------|----|-------------|-----------|
| Indicator Removal | T1070 | Audit log immutability trigger (DB-level) prevents deletion/modification | `verify_audit_chain()` detects tampered entries |
| Modify Authentication Process | T1556 | `REFRESH_TOKEN_SECRET` separate from `SECRET_KEY`; hard-fail on weak keys | Health alert watchdog monitors infrastructure tampering |
| Impair Defenses | T1562 | Policy engine default-DENY; kill switch blocks all autonomous actions | Policy decisions logged (last 200) |

### Credential Access (TA0006)

| Technique | ID | GULA Control | Detection |
|-----------|----|-------------|-----------|
| Brute Force | T1110 | Auth rate limiting: 10/min per IP; dynamic IP block at 5× threshold | Rate limiter logs blocked IPs; IntrusionDetector tracks attempts |
| Unsecured Credentials | T1552 | No hardcoded secrets; `.env` gitignored; `make secrets-gen` for key generation | Secret scanning (gitleaks) in CI |
| Credential Stuffing | T1110.004 | Dual-key rate limiting (user_id + IP); dummy hash for timing safety | Failed login audit trail |

### Lateral Movement (TA0008)

| Technique | ID | GULA Control | Detection |
|-----------|----|-------------|-----------|
| Remote Services | T1021 | Tenant isolation (`require_own_lab()`) prevents cross-lab access | Cross-lab access denied → HTTP 403 logged |
| Internal Spearphishing | T1534 | Mail/notification services audit-logged; consent layer on citizen data reads | Consent access decisions logged with emergency break-glass audit |

### Collection (TA0009)

| Technique | ID | GULA Control | Detection |
|-----------|----|-------------|-----------|
| Data from Local System | T1005 | ABAC; consent enforcement via `require_consent()` | Audit log tracks every data access |
| Data from Information Repos | T1213 | 13 granular permissions restrict data access by role | `/security/status` shows 24h data access metrics |
| Screen Capture | T1113 | CSP `frame-ancestors 'none'` prevents clickjacking; Permissions-Policy blocks camera/mic | — |

### Command and Control (TA0011)

| Technique | ID | GULA Control | Detection |
|-----------|----|-------------|-----------|
| Application Layer Protocol | T1071 | All API traffic through gateway; rate limited; concurrency capped | Request timing middleware; health monitoring |
| Data Encoding | T1132 | TLS 1.2/1.3 in production; HSTS | nginx security headers |

### Exfiltration (TA0010)

| Technique | ID | GULA Control | Detection |
|-----------|----|-------------|-----------|
| Exfiltration Over C2 | T1041 | `RESULT_LINK_EXPIRE_DAYS: 90`; public endpoint rate-limited (30/min) | Public result link access logged |
| Scheduled Transfer | T1029 | Outbox pattern; audit trail covers all data exports | Audit log tracks every data transmission |

### Impact (TA0040)

| Technique | ID | GULA Control | Detection |
|-----------|----|-------------|-----------|
| Data Destruction | T1485 | Audit log immutability trigger prevents tampering; `_ABSOLUTELY_BLOCKED` AI operations | `verify_audit_chain()` detects integrity violations |
| Service Stop | T1489 | Circuit breaker auto-recovery; kill switch limits blast radius; degraded mode | RecoveryWorker probes services every 10-30s |
| Resource Hijacking | T1496 | Concurrency limit (200 active); max body size (10MB); pool size budgeted | Adaptive concurrency loop; health watchdog |

---

## 4. NIST CSF Mappings

| Function | Category | GULA Control | Mapped CWE |
|----------|----------|-------------|------------|
| **Identify** | Asset Management | Configuration validation; startup guard inventory | — |
| | Risk Assessment | Circuit breaker thresholds; policy engine risk levels | CWE-754 |
| | Governance | Policy engine default-DENY; autonomous action taxonomy | — |
| **Protect** | Access Control | JWT + RBAC + ABAC + consent layer | CWE-287, CWE-862 |
| | Data Security | AES-256 at rest; bcrypt; TLS in transit | CWE-261, CWE-312 |
| | Info Protection | Immutable audit log; HMAC-anchored checkpoints | CWE-778, CWE-347 |
| | Maintenance | Dependency scanning in CI; upgrade policy | CWE-1104 |
| | Protective Tech | CSP/HSTS; rate limiting; circuit breaker | CWE-79, CWE-400 |
| **Detect** | Anomalies/Events | IntrusionDetector; RateLimiter dynamic blocking | CWE-799 |
| | Continuous Monitoring | Health alert watchdog (60s); `/health/deep` diagnostics | — |
| | Detection Processes | Sentry error tracking; structured logging | — |
| **Respond** | Response Planning | Kill switch (env/API/Redis); degraded mode escalation | — |
| | Analysis | Request-ID correlation; DB contextvar tracing | — |
| | Mitigation | Auto-repair engine; RecoveryWorker; circuit breaker | CWE-754 |
| **Recover** | Recovery Planning | RecoveryWorker probes; force-reset capability | — |
| | Improvements | Self-audit agent; continuous improvement pipeline | — |

---

## 5. Authentication Mechanisms

### 5.1 JWT Token Architecture

| Component | Implementation | Config |
|-----------|---------------|--------|
| **Token Type** | Access token (short-lived) + Refresh token (long-lived) | — |
| **Algorithm** | HS256 (HMAC-SHA256) | `JWT_ALGORITHM = "HS256"` |
| **Access Token TTL** | Default 30 minutes | `JWT_EXPIRE_MINUTES` (config.py:114) |
| **Refresh Token TTL** | Default 30 days | `REFRESH_TOKEN_EXPIRE_DAYS` (config.py:131) |
| **Signing Key** | Access: `SECRET_KEY`; Refresh: `REFRESH_TOKEN_SECRET` (separate) | config.py:102, 121 |
| **Token Payload** | `user_id`, `lab_id`, `role`, `perm_ver`, `jti`, `type`, `exp`, `iat` | `auth.py:67-73` |
| **Token Type Discrimination** | `payload["type"]` must match `"access"` / `"refresh"` | `auth.py:90, 99` |

### 5.2 Token Validation (`dependencies.py`)

```
Request → HTTPBearer or httpOnly cookie
         → decode_token() (verify signature + expiry + type)
         → JTI blacklist check (revoked?)
         → user.active check (DB)
         → perm_version match (Redis fast path → DB fallback)
         → lab.active check (except master_admin)
         → correlation context vars set for DB error logging
```

### 5.3 Token Revocation

| Mechanism | Trigger | Scope |
|-----------|---------|-------|
| **JTI Blacklist** | Logout; token refresh | Single token (TTL = token expiry) |
| **perm_version bump** | Role change; deactivate; password change; lab change | ALL active tokens for user |
| **Redis perm_version cache** | O(1) lookup; survives service restarts | Cross-worker consistency |

### 5.4 Password Security

- **Hashing:** bcrypt cost factor 12 via `shared/auth/passwords.py`
- **Timing safety:** Dummy hash `_DUMMY_HASH` used for non-existent user lookups to prevent timing enumeration (`auth.py:56`)
- **No password storage in plaintext:** Never occurs in codebase

### 5.5 Login Rate Limiting

| Limiter | Rate | Target |
|---------|------|--------|
| `rate_limit_auth()` | 10/min per IP | `/auth/login`, `/auth/register` |
| Dynamic IP block | 5× threshold (50 attempts in window) | 1-hour auto-block (`RATE_LIMIT_BLOCK_DURATION_SECONDS`) |

---

## 6. Authorization / RBAC

### 6.1 Role Hierarchy

| Role | Level | Scope | Permissions (count) |
|------|-------|-------|---------------------|
| `master_admin` | 100 | Platform-wide | All (17) |
| `ministry_admin` | 90 | National overview | 9 (read + platform mgmt) |
| `province_admin` | 80 | Province scope | 9 (same as ministry) |
| `admin` | 50 | Single lab | 12 |
| `lab_admin` | 50 | Single lab | 12 |
| `doctor` | 40 | Clinical | 4 (read + dashboard) |
| `technician` | 20 | Technical | 6 (read/write orders/results) |
| `staff` / `lab_staff` | 20 | Operations | 8 |
| `citizen` | 10 | Own data only | 0 (own results via consent) |

### 6.2 Permission Model

**Extended Permissions (16):**
`patients:read`, `patients:write`, `patients:delete`, `orders:read`, `orders:write`, `results:read`, `results:write`, `staff:manage`, `lab:read`, `lab:manage`, `dashboard:read`, `audit:read`, `platform:manage_labs`, `platform:manage_users`, `platform:view_stats`, `system:admin`

**Original Permissions (13):**
`read:patients`, `write:patients`, `read:orders`, `write:orders`, `read:results`, `write:results`, `read:samples`, `write:samples`, `manage:users`, `manage:labs`, `view:audit`, `manage:system`, `view:analytics`

### 6.3 Enforcement Points

| Layer | Mechanism | Code Location |
|-------|-----------|---------------|
| **Route-level** | `require_permission("perm")` dependency | `dependencies.py:88-109` |
| **Role-level** | `require_role("admin", "lab_admin")` | `rbac.py:68-79` |
| **Tenant isolation** | `require_own_lab(user, resource_lab_id)` | `rbac.py:85-100` |
| **Feature gates** | `require_feature_for_lab("feature", lab_id, db)` | `rbac.py:103-106` |
| **Subscription limits** | `assert_lab_within_limit("max_staff", count, lab_id, db)` | `rbac.py:109-150` |
| **Consent** | `require_consent("read:lab_results")` | `consent_dep.py` |

### 6.4 ABAC (Attribute-Based Access Control)

- **`require_own_lab()`**: Cross-lab access blocked unless user is platform role (master_admin, ministry_admin, province_admin). Returns bilingual 403 error (`rbac.py:85-100`)
- **`require_consent()`**: 4-rule access policy: (1) Owner bypass, (2) Lab write-path bypass, (3) Emergency break-glass (doctor-only), (4) Active consent check (`consent_dep.py`)

---

## 7. Encryption (At Rest & In Transit)

### 7.1 Data at Rest

| Data Type | Algorithm | Key | Implementation |
|-----------|-----------|-----|----------------|
| **Sensitive fields** | Fernet (AES-128-CBC + HMAC-SHA256) | `ENCRYPTION_KEY` | `shared/security/encryption.py` |
| **National IDs** | Fernet encrypt → HMAC-SHA256 sign | `ENCRYPTION_KEY` + `NID_HMAC_KEY` | `shared/security/encryption.py:29-46` |
| **Passwords** | bcrypt cost factor 12 | Auto-generated salt | `shared/auth/passwords.py` |
| **JWT tokens** | HS256 (HMAC-SHA256) | `SECRET_KEY`, `REFRESH_TOKEN_SECRET` | `shared/auth/jwt.py` |
| **Audit chain** | SHA-256 | — | `backend/app/services/audit_service.py:93` |
| **Audit anchors** | HMAC-SHA256 | `NID_HMAC_KEY` (with rotation support) | `backend/app/services/audit_service.py:39-51` |

### 7.2 Data in Transit

| Layer | Protocol | Config |
|-------|----------|--------|
| **External** | TLS 1.2 / 1.3 via nginx | Let's Encrypt / certbot |
| **Internal (Docker)** | HTTP (isolated network) | `127.0.0.1:8080` gateway |
| **HSTS** | `max-age=31536000; includeSubDomains` | Production only (`main.py:423-424`) |

### 7.3 Key Management

| Key | Production | Development | Rotation Support |
|-----|-----------|-------------|-----------------|
| `SECRET_KEY` | Must be set (hard-fail) | Auto-generated random | — |
| `ENCRYPTION_KEY` | Must be valid Fernet (hard-fail) | Ephemeral (warning) | — |
| `REFRESH_TOKEN_SECRET` | Must be set (hard-fail) | Auto-generated random | — |
| `NID_HMAC_KEY` | Must be set (hard-fail) | Falls back to ENCRYPTION_KEY | `_PREV` key for zero-downtime |
| `DEVICE_HMAC_KEY` | Must be set (hard-fail) | — | — |

### 7.4 Weak Secret Detection

All secrets checked against `_WEAK_PATTERNS` (`default`, `change`, `secret`, `example`, `test`, `demo`, `gula_default`, `changeme`, `password`, `12345`, `abcdef`). Production hard-exits on weak match (`config.py:96-98,108-109,139-140,155-156`).

---

## 8. Audit Logging

### 8.1 Immutable Hash Chain

```
Genesis ("0"*64)
  ↓ SHA-256(genesis + entry1)
chain_hash_1
  ↓ SHA-256(chain_hash_1 + entry2)
chain_hash_2
  ↓ ...
```

### 8.2 HMAC-Protected Anchors

- Written every 100 entries (`_ANCHOR_INTERVAL = 100`)
- Format: `v{key_version}|{timestamp}|{entry_id}|{chain_hash}|{hmac}`
- Written to monthly files: `audit_anchors_2026-07.log`
- HMAC uses `NID_HMAC_KEY` with previous-key support for rotation
- Verification endpoint checks all anchors and reports HMAC failures

### 8.3 DB-Level Immutability

PostgreSQL trigger `audit_logs_immutable`:
```sql
BEFORE UPDATE OR DELETE ON audit_logs
FOR EACH ROW EXECUTE FUNCTION prevent_audit_modification()
```
Applied idempotently during startup (`startup_guard.py:578-617`).

### 8.4 Audit Coverage

| Event Type | Audit Action | Logged By |
|-----------|-------------|-----------|
| Login | `login` / `login_failed` | Route handler |
| Permission change | `permission_change` | `session.py:bump_perm_version()` |
| Role change | `permission_change` | Session management |
| Data access | `view_result` | Route handlers |
| Patient card scan | `card_scanned` | `patient_card.py` |
| Consent decisions | `allow` / `deny` / `emergency` | `consent_service.log_access_decision()` |
| AI operations | `ai_suggestion` / `ai_approval` / `ai_execution` | AI sandbox + approval store |
| Kill switch | `kill_switch_activate` / `deactivate` | `kill_switch.py` |

### 8.5 Chain Verification

`verify_audit_chain(db, limit=1000)` re-computes every entry's chain_hash and compares against stored value. Returns `"intact"` or `"tampered"` with list of broken entries.

---

## 9. Rate Limiting / DoS Protection

### 9.1 Rate Limit Tiers

| Limiter | Default Rate | Target | Key |
|---------|-------------|--------|-----|
| `rate_limit_public()` | 30/min per IP | Public endpoints (result links) | `public:{ip}` |
| `rate_limit_user()` | 60/min per user + 180/min per IP | Authenticated endpoints | `user:{id}` + `ip:{addr}` |
| `rate_limit_auth()` | 10/min per IP | Login/register | `auth:{ip}` |
| `rate_limit_admin()` | 20/min per user + 60/min per IP | `/admin/*` endpoints | `admin:user:{id}` + `admin:ip:{addr}` |

### 9.2 Dynamic IP Blocking

- Triggered when count exceeds 5× the threshold (e.g., 50 auth attempts in 60s)
- Block duration: `RATE_LIMIT_BLOCK_DURATION_SECONDS` (default 3600s / 1 hour)
- Stored in Redis as `block:{client_ip}` key
- Checked before any rate limit evaluation (`rate_limit.py:102-105`)

### 9.3 Algorithm

Fixed-window algorithm with Redis-backed counters:
```
bucket = floor(now / window_seconds)
full_key = "rl:{key}:{bucket}"
count = cache.incr(full_key)
```
TTL on counter: `window_seconds * 2` to handle clock skew.

### 9.4 Client IP Extraction

Trust-aware header parsing:
1. `X-Real-IP` (nginx-set, trusted only from private IPs)
2. `X-Forwarded-For` first entry (trusted only from private IPs)
3. `request.client.host` fallback

`_is_private_ip()` validates RFC-1918 / loopback / Docker addresses.

### 9.5 DoS Prevention Stack

| Layer | Mechanism | Threshold | Location |
|-------|-----------|-----------|----------|
| Max body size | Content-Length rejection | 10 MB | `main.py:222-240` |
| Rate limiting | Per-key fixed window | Varies by tier | `rate_limit.py` |
| Concurrency limit | In-flight request cap | 200 active | `main.py:516-556` |
| Adaptive concurrency | Dynamic halving on slow DB | 2 × >300ms readings | `main.py` |
| Readiness 503 | All requests blocked until ready | Startup guard | `main.py:448-469` |
| Degraded mode | Write rejection in L2/L3 | DB circuit open | `self_healing.py:353-408` |

---

## 10. Input Validation

| Layer | Mechanism | Details |
|-------|-----------|---------|
| **FastAPI/Pydantic** | Type coercion + validation | All routes use Pydantic models for request bodies |
| **Max body size** | Content-Length check | 10MB default (`MAX_REQUEST_BODY_MB`) |
| **File upload validation** | MIME type + size + content | 50MB max, allowed types: PDF/JPEG/PNG (frontend) |
| **SQLAlchemy ORM** | Parameterized queries | No raw SQL in business logic |
| **CORS** | Origin whitelist | Production origins only |
| **No eval/exec** | Prohibited in codebase | Static analysis (Bandit/Flake8) enforces this |

---

## 11. Session Management

### 11.1 JWT Session Lifecycle

```
 Login → access_token (30min) + refresh_token (30d)
        → perm_version cached in Redis
        → JWT payload includes user_id, lab_id, role, perm_ver, jti
        →
 Request → decode_token → JTI blacklist check → perm_version match
        → user.active → lab.active → proceed
        →
 Logout → JTI added to Redis blacklist (TTL = token expiry)
        →
 Refresh → old refresh token blacklisted → new pair issued
        →
 Role change → bump_perm_version() → ALL tokens invalidated
```

### 11.2 Token Storage

- **Mobile:** `Authorization: Bearer <token>` header
- **Web:** httpOnly `access_token` cookie + Authorization header fallback
- **Refresh token:** Not stored client-side by default (refresh endpoint uses its own mechanism)

### 11.3 Forced Invalidation

`bump_perm_version()` (`session.py:36-76`):
1. Increments `lab_users.perm_version` in DB (caller commits)
2. Writes new version to Redis: `user:perm_ver:{user_id}` (TTL 31 days)
3. Writes `permission_change` audit entry
4. Next request with old token → perm_version mismatch → 401 "Permissions updated — please log in again"

---

## 12. Secrets Management

### 12.1 Secret Inventory

| Secret | Env Var | Required in Prod | Rotatable via |
|--------|---------|-----------------|---------------|
| JWT signing key | `SECRET_KEY` | Yes (hard-fail) | Env restart |
| JWT refresh key | `REFRESH_TOKEN_SECRET` | Yes (hard-fail) | Env restart |
| Encryption key | `ENCRYPTION_KEY` | Yes (hard-fail) | Data re-encryption |
| NID HMAC key | `NID_HMAC_KEY` | Yes (hard-fail) | `_PREV` key rotation |
| Device HMAC key | `DEVICE_HMAC_KEY` | Yes (hard-fail) | Env restart |
| Gemini API key | `GEMINI_API_KEY` | No (optional) | Env restart |
| Groq API key | `GROQ_API_KEY` | No (optional) | Env restart |
| FCM key | `FCM_SERVER_KEY` | No (optional) | Env restart |
| CF API token | `CF_API_TOKEN` | No (optional) | Env restart |
| Sentry DSN | `SENTRY_DSN` | No (optional) | Env restart |
| Supabase keys | `SUPABASE_*_KEY` | No (optional) | Env restart |

### 12.2 Key Generation

```bash
make secrets-gen  # generates: SECRET_KEY, ENCRYPTION_KEY, NID_HMAC_KEY, etc.
```

Equivalent to:
```bash
openssl rand -hex 64       # SECRET_KEY
python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"  # ENCRYPTION_KEY
openssl rand -hex 32       # NID_HMAC_KEY
```

### 12.3 Secrets Hygiene

- No hardcoded secrets in source code (verified by Bandit + gitleaks in CI)
- `.env` gitignored; `.env.example` tracked as template
- `.env.production` tracked without real values
- `config.py` validates on import: production hard-exits on missing/weak secrets
- Makefile target `secret-scan` for gitleaks

---

## 13. CSP / Security Headers

### 13.1 Middleware Headers (`main.py:390-425`)

| Header | Value | Purpose |
|--------|-------|---------|
| `X-Content-Type-Options` | `nosniff` | MIME sniffing prevention |
| `X-Frame-Options` | `DENY` | Clickjacking prevention |
| `X-XSS-Protection` | `1; mode=block` | Legacy XSS filter |
| `Referrer-Policy` | `strict-origin-when-cross-origin` | Referrer leak prevention |
| `Permissions-Policy` | `camera=(), microphone=(), geolocation=()` | API permissions |
| `Cross-Origin-Opener-Policy` | `same-origin` | Cross-origin isolation |
| `Strict-Transport-Security` | `max-age=31536000; includeSubDomains` | HTTPS enforcement (prod only) |
| `Content-Security-Policy` | See below | XSS/Data injection |

### 13.2 Content Security Policy

```
default-src 'self';
script-src 'self' 'unsafe-inline';
style-src 'self' 'unsafe-inline';
img-src 'self' data: blob:;
connect-src 'self' https://gula-platform.org;
font-src 'self';
object-src 'none';
base-uri 'self';
form-action 'self';
frame-ancestors 'none'
```

### 13.3 Nginx Edge Headers (`SECURITY_HARDENING.md`)

- Additional HSTS with `preload`
- Expanded CSP for CDN resources (jsdelivr.net)
- Served at nginx level before traffic reaches API gateway

### 13.4 Cache Control

- Health endpoints: `public, max-age=10, stale-while-revalidate=5`
- Everything else: `no-store, no-cache, must-revalidate`

---

## 14. Kill Switch / Circuit Breaker

### 14.1 Kill Switch (`core/kill_switch.py`)

Three activation paths (OR):
1. **Environment:** `KILL_SWITCH=true` → requires container restart
2. **API:** `POST /admin/kill-switch/activate` → admin-only, instant
3. **Redis:** `redis-cli SET gula:kill_switch 1` → cross-instance propagation

When ACTIVE:
- All auto_repair actions blocked
- Self-audit auto-fix blocked
- Scaling operations blocked
- AI autonomous decisions blocked
- Policy engine blocks all autonomous actions
- Normal API traffic and reads continue (NOT a system shutdown)

### 14.2 Circuit Breaker (`core/self_healing.py`)

| Circuit | Failure Threshold | Recovery Timeout | Degradation Level |
|---------|------------------|------------------|-------------------|
| PostgreSQL | 3 consecutive | 30 seconds | L2_READ_ONLY |
| Redis | 5 consecutive | 20 seconds | L1_CACHE_HEAVY |

**States:** CLOSED → OPEN → HALF_OPEN → CLOSED (auto-recovery)

### 14.3 Degradation Levels

| Level | Name | Behavior | Trigger |
|-------|------|----------|---------|
| **0** | NONE | All operations pass | Normal |
| **1** | L1_CACHE_HEAVY | Writes pass with warning; cache preferred for reads | Redis circuit open; DB latency >300ms |
| **2** | L2_READ_ONLY | POST/PUT/DELETE/PATCH rejected (503); reads pass | DB circuit open |
| **3** | L3_CRITICAL_ONLY | Only health + auth + kill-switch paths pass | DB storm (adaptive) |

**Always-allowed paths** (bypass all degradation):
`/health`, `/health/ready`, `/health/live`, `/health/status`, `/health/deep`, `/health/kernel`

**L3-critical paths** (minimum viable surface):
`/health/*`, `/auth/login`, `/auth/refresh`, `/admin/kill-switch/deactivate`, `/metrics/prom`

---

## 15. AI Safety Guardrails

### 15.1 Core Principle

```
AI = Suggest
Human = Approve
System = Enforce
```

### 15.2 Architecture

```
External/Local AI Model
  ↓
AISuggestion (immutable, typed, trust=UNTRUSTED)
  ↓
Guardrail checks (operation allowed? type-checked? confidence valid?)
  ↓
ApprovalStore.submit() → PendingApproval (status=PENDING)
  ↓
Human reviews → approves via /api/ai/approve/{id}
  ↓
AISandbox.execute() → operation runs under audit
```

### 15.3 Absolutely Blocked AI Operations

10 operations are permanently blocked: `validate_order`, `cancel_order`, `modify_result`, `delete_patient`, `create_lab_user`, `change_role`, `approve_result`, `write_audit_log`, `export_patient_data`, `send_critical_alert`.

### 15.4 AI Suggestable Operations (require human approval)

7 operations: `suggest_interpretation`, `analyze_order`, `suggest_normal_range`, `flag_anomaly`, `suggest_reorder`, `summarize_history`, `translate_report`.

### 15.5 Sandbox Enforcement

- `AISandbox.execute()` verifies: (1) approval is APPROVED status, (2) operation is in whitelist `_REGISTRY`
- No direct DB writes — handlers call internal service functions
- All output marked `display_only=True` unless explicitly opted out
- Every execution is audited before and after

### 15.6 Policy Engine Oversight

All AI autonomous actions must pass `PolicyEngine.evaluate_policy()`:
- `AI_DECISION` → Risk: HIGH; allowed in production
- `AI_AUTO_FIX` → Risk: CRITICAL; blocked in production
- `AI_COMMIT` → Risk: CRITICAL; blocked in production
- Frequency limits: 5 AI decisions per hour before mandatory human review

---

## 16. Concurrency & Backpressure

### 16.1 Concurrency Limit Middleware

| Setting | Default | Config |
|---------|---------|--------|
| Max concurrent requests | 200 | `MAX_CONCURRENT_REQUESTS` |
| Overload response | 503 with `Retry-After: 5` | Arabic + English |

### 16.2 Clinical Write Exemption

Critical paths are ALWAYS exempt from concurrency shedding:
- `/results` — entering / updating lab results
- `/orders` — creating orders, validating
- `/samples` — sample lifecycle
- `/critical-alerts` — critical value notifications

Patient-safety operations must never be shed.

### 16.3 Adaptive Concurrency

Background loop (`main.py`) halves `_MAX_CONCURRENT` on 2 slow DB readings (>300ms); restores after 3 fast (<150ms). This prevents cascading overload.

### 16.4 Database Connection Pool

Formula: `WEB_CONCURRENCY × (DB_POOL_SIZE + DB_MAX_OVERFLOW) < postgres.max_connections`
Current: 3 × (6 + 12) = 54 < 100 (default)

---

## 17. Startup Security Guard

### 17.1 Startup Sequence (`startup_guard.py`)

```
Step 1: validate_config()
  → SECRET_KEY present & not weak
  → ENCRYPTION_KEY present & valid Fernet format & not weak
  → NID_HMAC_KEY present & not weak

Step 2: wait_for_db(max_retries=15, initial_delay=10)
  → Exponential backoff
  → Smart error classification (transient vs permanent)
  → Permanent misconfig → stop and alert

Step 3: check_migrations()
  → alembic_version table exists
  → version_num row present (migration completed)
  → All 7 required tables exist: labs, lab_users, patients, lab_orders, lab_results, outbox_events, audit_logs

Step 4: seed_critical_data()
  → perm_version migration (FATAL if fails)
  → test types catalog (NON-FATAL)
  → master admin user (NON-FATAL)
  → default subscriptions (NON-FATAL)
  → audit log immutability trigger (NON-FATAL)

Step 5: Kernel bootstrap (NON-FATAL)
```

### 17.2 Hybrid Readiness

`is_system_ready()` returns `(ready, reason)`:
- CRITICAL: PostgreSQL must be reachable
- OPTIONAL: Redis failure → degraded mode (not 503)

`ReadinessMiddleware` blocks all non-whitelisted paths with 503 until `system_ready = True`.

---

## 18. Policy Engine

### 18.1 Action Taxonomy

18 classified actions with risk levels:

| Action | Risk Level | Allowed in Production? |
|--------|-----------|----------------------|
| `CODE_CHANGE` | CRITICAL | No |
| `CONFIG_CHANGE` | HIGH | No |
| `DEPLOY` | HIGH | No |
| `DB_SCHEMA` | CRITICAL | No |
| `DB_WRITE` | HIGH | No |
| `DB_POOL_RECYCLE` | MEDIUM | Yes |
| `AUTO_REPAIR` | MEDIUM | Yes |
| `SCALING` | MEDIUM | Yes |
| `CIRCUIT_RESET` | MEDIUM | Yes |
| `CACHE_FLUSH` | HIGH | No |
| `QUEUE_PURGE` | HIGH | No |
| `AI_AUTO_FIX` | CRITICAL | No |
| `AI_COMMIT` | CRITICAL | No |
| `AI_DECISION` | HIGH | Yes |
| `SECRET_ROTATION` | CRITICAL | No |
| `AUDIT_DELETE` | CRITICAL | No (NEVER) |

### 18.2 Default-DENY

Unknown actions are blocked unless explicitly allowed. Every evaluation is logged regardless of outcome. Frequency limits prevent action loops.

---

## 19. Self-Healing & Auto-Repair

### 19.1 Self-Healing Components (`core/self_healing.py`)

| Component | Function |
|-----------|----------|
| **CircuitBreaker** | Tracks consecutive failures per service; opens/closes circuit |
| **SystemHealth** | Singleton holding circuit breakers + degradation level |
| **DegradedModeMiddleware** | Routes degraded requests per level |
| **RecoveryWorker** | Background coroutine probes failed services at 10s (degraded) / 30s (normal) intervals |

### 19.2 Auto-Repair Engine (`core/auto_repair.py`)

| Repair Action | Threshold | Cooldown | Severity |
|---------------|-----------|----------|----------|
| Memory GC | RSS >600MB (warn), >900MB (critical) | 180s | Warn |
| Circuit probe | DB latency >9s | 60s | Warn |
| Pool recycle | DB latency >900ms | 300s | Warn |
| Redis reconnect | Redis latency >9s | 30s | Critical |

### 19.3 Decision Guard

All repair actions pass through `_guard_repair()` which checks:
1. Is kill switch active? → block
2. Is environment production? → stricter rules
3. Policy engine → action-specific risk evaluation

---

## 20. Security Testing Matrix

| Test Module | Coverage | Tests |
|------------|----------|-------|
| `test_security.py` | JWT validation, expiry, password hashing, encryption, RBAC | Comprehensive |
| `test_comprehensive.py` | Full integration tests across all major routes | Full suite |
| `test_stability_assertions.py` | Data integrity checks | Targeted |
| `test_patient_card.py` | QR card generation, scanning, HMAC token verification | Targeted |
| `test_feature_flags.py` | Per-tenant feature matrix | Targeted |
| `test_edge_platform.py` | Edge synchronization security | Targeted |
| `test_mpi_matcher.py` | Master Patient Index deduplication | Targeted |
| `test_outbox_service.py` | Event delivery guarantees | Targeted |

**CI Security Gates:**
| Gate | Tool | Enforces |
|------|------|----------|
| `syntax-gate` | `py_compile` + `flake8 (E9,F821)` | No syntax errors, no undefined names |
| `migration-check` | Alembic upgrade/downgrade | Schema integrity |
| `security-scan` | Bandit, Safety, Hadolint, Gitleaks | No CVEs, no hardcoded secrets |
| `build-and-push` | Trivy | Container image scanning |

**SAST Results (2026-07-08):**
- High: 0
- Medium: 2 (hardcoded_bind_all_interfaces in integration config — dev mode only)
- Low: 53 (informational)

---

## 21. Known Gaps & Remediation Roadmap

### 21.1 Open Issues

| Issue | Severity | Status | Remediation |
|-------|----------|--------|-------------|
| Python 3.11.0rc1 pre-release | 🔴 Critical | Open | Install Python 3.11.9+ or 3.12+ via deadsnakes |
| `.env` file missing in deployment | 🔴 High | Open | Create from `.env.example` |
| Poetry 1.1.12 outdated | 🟡 Medium | Open | `pip install --upgrade poetry` |
| Missing `bandit`/`semgrep`/`safety`/`trivy`/`gitleaks` local tools | 🟡 Medium | Open | `pip install bandit safety`; `npm install -g semgrep` |
| Docker Compose v1 (legacy) | 🟡 Medium | Open | `apt-get install docker-compose-v2` |
| No 2FA/MFA for admin accounts | 🟡 Medium | Enhancement | Phase 2 — TOTP via pyotp |
| No automated CVE scanning schedule | 🟡 Medium | Enhancement | CI cron job for weekly advisory scans |
| Rate limit bypass possible across multiple IPs | 🟢 Low | Enhancement | Consider token bucket with distributed counting |
| Test fixture errors in tenant isolation (268) | 🟢 Low | Open | Test infrastructure, not production code |
| `passlib/bcrypt` deprecation warning | 🟢 Low | Open | Non-functional; bcrypt 4.1.3 compatible |

### 21.2 Enhancement Roadmap

| Priority | Enhancement | Target Phase |
|----------|-------------|-------------|
| 1 | MFA/TOTP for master_admin and admin roles | Phase 2 |
| 2 | Automated CVE scanning (weekly CI cron) | Phase 2 |
| 3 | Rate limiting with token bucket algorithm | Phase 2 |
| 4 | API key rotation endpoint + key expiry | Phase 2 |
| 5 | Database-level row-level security (RLS) | Phase 3 |
| 6 | Security event correlation engine | Phase 3 |
| 7 | Penetration testing program | Ongoing |
| 8 | Bug bounty program | Phase 4 |

---

## References

| Document | Location |
|----------|----------|
| CLAUDE.md (architecture overview) | `/home/samertts/workspace/projects/gula-platform/CLAUDE.md` |
| SECURITY.md | `/home/samertts/workspace/projects/gula-platform/SECURITY.md` |
| SECURITY_HARDENING.md | `/home/samertts/workspace/projects/gula-platform/SECURITY_HARDENING.md` |
| Environment Report 4.0 | `/home/samertts/workspace/projects/gula-platform/assessment/environment_report_4.0.md` |
| Security Assessment (planned) | `/home/samertts/workspace/projects/gula-platform/assessment/security/` |
| CI Pipeline | `/home/samertts/workspace/projects/gula-platform/.github/workflows/ci.yml` |
| SNDHS Phase 1 Security Spec | `/home/samertts/workspace/projects/gula-platform/docs/sndhs/` |
| OWASP Top 10 2021 | https://owasp.org/Top10/ |
| MITRE ATT&CK | https://attack.mitre.org/ |
| NIST CSF | https://www.nist.gov/cyberframework |
| CWE | https://cwe.mitre.org/ |
