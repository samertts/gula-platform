# GULA PLATFORM — SECURITY MASTER REPORT

**Classification:** CONFIDENTIAL
**Date:** 2026-07-17
**Scope:** OWASP ASVS Level 2, OWASP Top 10 (2021), API Security, Zero Trust, C2M2

---

## EXECUTIVE SUMMARY

GULA implements a **defense-in-depth** architecture across 4 layers: Cloudflare Edge → nginx WAF → FastAPI middleware → DB/Redis circuit breakers. The security model includes JWT auth, RBAC (9 roles), ABAC, Fernet encryption, rate limiting, hash-chained audit logs, and tenant isolation.

**Overall Security Rating: B+** (Strong foundation, known gaps in OAuth2 lifecycle, CSRF, VAPID, and license clarity)

---

## FINDINGS BY OWASP ASVS LEVEL

### V1: Architecture, Design and Threat Modeling (Score: 85%)

| Control | Status | Evidence |
|---------|--------|----------|
| 1.1 Secure software lifecycle | ✅ | CI/CD quality gates, pre-commit hooks |
| 1.2 Authentication architecture | ✅ | JWT + OAuth2 + SAML + MFA |
| 1.3 Session management | ⚠️ | Redis-backed blacklist (fails open) |
| 1.4 Access control | ✅ | RBAC + ABAC + lab_id filtering |
| 1.5 Input/output validation | ✅ | Pydantic v2 + middleware validation |
| 1.6 Cryptographic architecture | ✅ | Fernet, bcrypt, SHA-256 chain |
| 1.7 Error handling | ✅ | Global exception handler, no stack leaks |
| 1.8 Data protection | ⚠️ | National ID encrypted, but no key rotation |
| 1.9 Communications security | ✅ | mTLS options, TLS 1.2+ |

### V2: Authentication (Score: 80%)

| Control | Status | Evidence |
|---------|--------|----------|
| 2.1 Password security | ✅ | bcrypt, minimum strength, timing-safe login |
| 2.2 General authenticator | ✅ | JWT access (30min) + refresh (30d) |
| 2.3 Authenticator lifecycle | ⚠️ | No forced rotation policy |
| 2.4 Credential storage | ✅ | bcrypt hashes, Fernet-encrypted national IDs |
| 2.5 Credential recovery | ⚠️ | Password reset exists, no rate limit on reset endpoint |
| 2.6 Look-up secrets | ✅ | OAuth2 client secrets hashed |
| 2.7 Out-of-band | ❌ | No OOB verification for sensitive operations |
| 2.8 One-time verifier | ✅ | TOTP via MFA, backup codes |

### V3: Session Management (Score: 65%)

| Control | Status | Evidence |
|---------|--------|----------|
| 3.1 Fundamental | ✅ | JWT with jti, expiry |
| 3.2 Session binding | ✅ | Token bound to user_id + lab_id |
| 3.3 Session termination | ⚠️ | Redis blacklist for logout; fails open if Redis down |
| 3.4 Cookie-based sessions | N/A | Token-based auth (Bearer header) |

### V4: Access Control (Score: 90%)

| Control | Status | Evidence |
|---------|--------|----------|
| 4.1 General | ✅ | RBAC enforced at dependency level |
| 4.2 Operation-level | ✅ | require_role() decorator |
| 4.3 Other controls | ✅ | Tenant isolation via lab_id filtering |

### V5: Validation, Sanitization and Encoding (Score: 75%)

| Control | Status | Evidence |
|---------|--------|----------|
| 5.1 Input validation | ✅ | Pydantic models, max body size (10MB) |
| 5.2 Sanitization | ✅ | CSP headers, output encoding |
| 5.3 Output encoding | ⚠️ | Arabic content verified, XSS protection via CSP |
| 5.4 Mail/Messaging | ❌ | No verification of email/SMS input sanitization |
| 5.5 Deserialization | ✅ | Pydantic v2 strict mode |

### V6: Stored Cryptography (Score: 70%)

| Control | Status | Evidence |
|---------|--------|----------|
| 6.1 Data classification | ✅ | PHI/PII identified, national ID encrypted |
| 6.2 Algorithm selection | ✅ | SHA-256, bcrypt, Fernet (AES-128-CBC) |
| 6.3 Key management | ⚠️ | **No automated key rotation** |
| 6.4 Random values | ✅ | secrets module used appropriately |

### V7: Error Handling and Logging (Score: 85%)

| Control | Status | Evidence |
|---------|--------|----------|
| 7.1 Error handling | ✅ | Generic messages in production |
| 7.2 Logging | ✅ | Structured JSON, request correlation |
| 7.3 Log protection | ✅ | Append-only audit trigger |
| 7.4 Audit events | ✅ | Hash-chained audit log |

### V8: Data Protection (Score: 80%)

| Control | Status | Evidence |
|---------|--------|----------|
| 8.1 Sensitivity | ✅ | PHI/PII classification exists |
| 8.2 Encryption at rest | ✅ | Fernet for national IDs |
| 8.3 Encryption in transit | ✅ | TLS 1.2+ enforced at gateway |
| 8.4 Secrets management | ⚠️ | .env file on disk (gitignored but present) |

### V9: Communications (Score: 75%)

| Control | Status | Evidence |
|---------|--------|----------|
| 9.1 TLS | ✅ | TLS 1.2+ with strong ciphers |
| 9.2 mTLS | ⚠️ | Options exist but not enforced |
| 9.3 Certificate management | ⚠️ | Let's Encrypt auto-renew, no cert rotation policy |

---

## OWASP TOP 10 (2021) ASSESSMENT

| Risk | Status | Mitigation |
|------|--------|-----------|
| A01: Broken Access Control | ✅ | RBAC + ABAC + lab_id filtering |
| A02: Cryptographic Failures | ⚠️ | No key rotation, but encryption exists |
| A03: Injection | ✅ | Pydantic, parameterized queries (SQLAlchemy) |
| A04: Insecure Design | ⚠️ | Rate limit fails open without Redis |
| A05: Security Misconfiguration | ⚠️ | License ambiguity, version inconsistency |
| A06: Vulnerable Components | ✅ | Dependabot configured, weekly scans |
| A07: Auth Failures | ⚠️ | Session revocation fails open |
| A08: Data Integrity | ✅ | Audit chain hash, optimistic locking |
| A09: Logging Failures | ✅ | Structured logging, append-only audit |
| A10: SSRF | ⚠️ | Outbound requests exist but no explicit SSRF protection |

---

## CRITICAL FINDINGS (P0-P1)

### P0: No LICENSE File
**Problem:** Zero license clarity. Contributors, users, and deployers have no legal basis for using the code.
**Evidence:** No LICENSE file at repo root. Contradictory metadata (MIT vs Proprietary).
**Risk:** Legal exposure for both project and users.
**Remediation:** Select license, add LICENSE file, update all metadata.

### P0: Version Inconsistency
**Problem:** 3 different versions deployed simultaneously.
**Evidence:** config.py=2.1.0, pyproject.toml=2.2.0, setup.py=2.1.0
**Risk:** CI artifacts version mismatch, deployment confusion.
**Remediation:** Centralize version in config.py, reference from build files.

### P1: No Automated Key Rotation
**Problem:** OAuth2, JWT signing keys, encryption keys never rotated.
**Evidence:** No rotation endpoints, no rotation schedule, rotate-keys.sh exists but is manual.
**Risk:** Compromised key = compromised all tokens and encrypted data.
**Remediation:** Implement key rotation endpoints, KMS integration, rotation policy (90d JWT, 180d encryption).

### P1: Rate Limiting Fails Open
**Problem:** When Redis is unavailable, rate limiting silently permits all requests.
**Evidence:** `rate_limit.py` depends entirely on Redis availability.
**Risk:** Brute-force attacks during Redis outages.
**Remediation:** Add local in-memory fallback rate limiter with reduced capacity.

### P1: CSRF Protection Missing
**Problem:** No CSRF tokens for browser-based API clients.
**Evidence:** Middleware stack lacks CSRF middleware.
**Risk:** Cross-site request forgery on state-changing operations.
**Remediation:** Add Double Submit Cookie pattern or SameSite=Strict on session cookies.

---

## HIGH FINDINGS (P2)

### P2: OAuth2 Key Rotation
Same as P1 - repeating for emphasis in OAuth2 context.

### P2: Session Revocation Fails Open
**Problem:** JWT blacklist in Redis — if Redis is unavailable, revoked tokens are accepted.
**Evidence:** `auth.py` `is_token_blacklisted()` queries Redis.
**Risk:** Stolen tokens remain valid during Redis outages.
**Remediation:** Add short JWT expiry (5min for sensitive operations), local blacklist cache.

### P2: Push Notification VAPID Keys Not Configured
**Problem:** Service worker registers push notifications but VAPID keys are not in any env file.
**Evidence:** `frontend/sw.js` line 85 registers push; no VAPID env var.
**Risk:** Push notifications non-functional.
**Remediation:** Generate VAPID keys, add to .env.example.

### P2: External AI Provider Calls
**Problem:** Top-level `ai/` directory contains code calling OpenAI, DeepSeek, Gemini directly.
**Evidence:** `ai/ai_service.py` (193 lines), `ai/ai_agent.py` (28 lines).
**Risk:** Data sovereignty violation, PHI exposure to external providers.
**Remediation:** Remove or gate behind explicit configuration, add data sovereignty checks.

### P2: Deprecated @app.on_event() in Microservices
**Problem:** All 8 microservices use deprecated startup/shutdown event handlers.
**Evidence:** All `services/*/main.py`.
**Risk:** Will break in future FastAPI versions.
**Remediation:** Migrate to lifespan context manager.

---

## MEDIUM FINDINGS (P3)

### P3: Weak Secret Detection Incomplete
**Problem:** Pattern list may miss modern weak passwords, no entropy check.
**Evidence:** `config.py` `_WEAK_PATTERNS`.
**Risk:** Predictable secrets in non-production environments.
**Remediation:** Add entropy measurement, expand pattern list.

### P3: No Coverage Threshold in CI
**Problem:** Tests pass regardless of coverage level.
**Evidence:** CI workflow lacks coverage threshold enforcement.
**Risk:** Test quality degradation over time.
**Remediation:** Add minimum 80% coverage threshold.

### P3: Integration Connectors Untested
**Problem:** 20+ connectors in `integration/connectors/` have no tests.
**Evidence:** No test files for connector implementations.
**Risk:** Undocumented, untested integration points.
**Remediation:** Add smoke tests for each connector.

### P3: services/shared/ Dead Code
**Problem:** 3 deprecated bridge files never imported.
**Evidence:** Grep shows no imports from services/shared/.
**Risk:** Maintenance burden, confusion.
**Remediation:** Remove dead code.

---

## LOW/INFORMATIONAL (P4)

| Finding | Location | Recommendation |
|---------|----------|---------------|
| .env file on disk | Root | Add to pre-commit hook to warn |
| Root requirements.txt | Root | Remove if unused |
| Security headers minor fix | main.py | Change value from "x-content-type-options: nosniff" to "nosniff" |
| `random` vs `secrets` in tests | tests/ | Verify no crypto uses random |
| No CAA DNS record check | cloudflare/ | Verify CAA allows Let's Encrypt |
| Missing SRI hash for CDN resources | frontend/ | Add subresource integrity |

---

## ZERO TRUST MATURITY ASSESSMENT

| Principle | Status | Notes |
|-----------|--------|-------|
| Verify explicitly | ⚠️ | JWT verified, but no continuous verification |
| Least privilege | ✅ | RBAC scoped by role + lab_id |
| Assume breach | ✅ | Circuit breakers, auto-repair, audit hashing |
| Microsegmentation | ⚠️ | Docker networks separate, but API gateway is single entry |
| No implicit trust | ⚠️ | Internal services trust each other (no mTLS between microservices) |

---

## API SECURITY ASSESSMENT

| Control | Status |
|---------|--------|
| Authentication | JWT Bearer |
| Rate limiting | Yes (Redis-backed) |
| Request validation | Pydantic v2 |
| API versioning | Path-based (/api/v1/) |
| CORS | Configurable, default single origin |
| Content-Type enforcement | Yes |
| Max body size | 10MB |
| Sensitive data in URLs | No (tokens in headers) |
| Idempotency keys | Yes (idempotency_keys table) |
| API documentation | Swagger/ReDoc (guarded in production) |

---

## SECURITY METRICS

| Metric | Value |
|--------|-------|
| Authentication methods | 5 (JWT, OAuth2, SAML, MFA, API Keys) |
| Route modules with auth | 53 (100%) |
| Rate limit zones | 5 (api, auth, upload, health, public) |
| Security headers | 8 (CSP, HSTS, X-Frame, X-Content-Type, Referrer-Policy, Permissions-Policy, X-Request-ID, Cache-Control) |
| Audit log hash chain | SHA-256, append-only DB trigger |
| Encryption at rest | Fernet (national IDs) |
| Password hashing | bcrypt |
| Circuit breakers | 2 (DB, Redis) |
| Degradation levels | 4 (NONE, L1, L2, L3) |
| CI security scans | Safety, Bandit, Hadolint, Gitleaks, Trivy |

---

## REMEDIATION ROADMAP

| Priority | Finding | Timeline | Owner |
|----------|---------|----------|-------|
| P0 | Add LICENSE file | Week 1 | Legal |
| P0 | Unify version | Week 1 | DevOps |
| P1 | Key rotation system | Month 1 | Security |
| P1 | Rate limit fallback | Month 1 | Backend |
| P1 | CSRF protection | Month 1 | Backend |
| P2 | OAuth2 key rotation | Month 2 | Security |
| P2 | Session revocation hardening | Month 2 | Backend |
| P2 | Remove external AI calls | Month 2 | AI Team |
| P2 | Fix microservice lifespan | Month 3 | Backend |
| P3 | Coverage threshold in CI | Month 3 | DevOps |
| P3 | Connector tests | Month 4 | Integration |
| P3 | Remove dead code | Month 4 | Backend |
| P4 | All informational items | Ongoing | Various |
