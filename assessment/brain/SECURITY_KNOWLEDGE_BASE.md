# Security Knowledge Base — GULA Platform v2.1.0

> **Generated:** 2026-07-14
> **Scope:** Entire monorepo (backend monolith, shared library, 8 microservices, 2 frontends, device bridge, edge agent)
> **Framework Mapping:** CVEs → CWEs → OWASP Top 10 → OWASP LLM Top 10 → MITRE ATT&CK → MITRE ATLAS → NIST SSDF → SLSA

---

## 1. CVE Registry

### 1.1 Python Dependencies

| CVE ID | Package | Affected Version | Fixed In | CVSS | Severity | Status | Remediation Date | Notes |
|--------|---------|------------------|----------|------|----------|--------|------------------|-------|
| CVE-2024-33663 | python-jose | <=3.3.0 | 3.4.0 | 6.8 | MEDIUM | ❌ **Unpatched** | TBD | Algorithm confusion attack — backend uses `>=3.3.0`, shared uses `>=3.3.0`. Upgrade to `>=3.4.0`. |
| CVE-2024-33664 | python-jose | <=3.3.0 | 3.4.0 | 5.3 | MEDIUM | ❌ **Unpatched** | TBD | JWT bomb DoS — same fix version as above. |
| CVE-2024-29370 | python-jose | 3.3.0 | 3.4.0 | 5.3 | MEDIUM | ❌ **Unpatched** | TBD | JWE denial of service. |
| CVE-2024-42512 | reportlab | <4.2.1 | 4.2.1 | 9.8 | CRITICAL | ⚠️ **Verify** | TBD | Sandbox escape allowing RCE. GULA has `>=4.1.0` — must upgrade to `>=4.2.1`. |
| CVE-2024-1135 | gunicorn | <22.0.0 | 22.0.0 | 6.1 | MEDIUM | ⚠️ **Verify** | TBD | HTTP response splitting. GULA has `>=21.2.0` — needs upgrade to `>=22.0.0`. |
| CVE-2024-39398 | psycopg2-binary | <2.9.10 | 2.9.10 | 5.9 | MEDIUM | ⚠️ **Verify** | TBD | DoS via malformed data. GULA has `>=2.9.9` — check if 2.9.10 resolved. |
| CVE-2024-24762 | fastapi | <0.109.1 | 0.109.1 | 7.5 | HIGH | ✅ **Not affected** | — | ReDoS via path parameters. GULA has `>=0.110.0`. |
| CVE-2021-32677 | fastapi | <0.65.2 | 0.65.2 | 6.1 | MEDIUM | ✅ **Not affected** | — | CSRF via `OAuth2PasswordRequestForm`. |
| CVE-2026-48710 | starlette (fastapi dep) | <1.0.1 | 1.0.1 | 4.3 | MEDIUM | ⚠️ **Monitor** | — | BadHost header injection. Need to verify transitive dep. |
| CVE-2024-3772 | pydantic | 2.0.0–2.4.0 | 2.4.0 | 5.3 | MODERATE | ✅ **Not affected** | — | ReDoS. GULA has `>=2.7.0`. |
| CVE-2021-29510 | pydantic | <1.8.2 | 1.8.2 | 5.3 | MODERATE | ✅ **Not affected** | — | Infinite loop. |
| CVE-2019-7548 | sqlalchemy | 1.2.17 | 1.3.0 | 7.5 | HIGH | ✅ **Not affected** | — | SQLi in group_by. GULA has `>=2.0.30`. |
| CVE-2019-7164 | sqlalchemy | <1.3.0 | 1.3.0 | 7.5 | HIGH | ✅ **Not affected** | — | SQLi. |
| CVE-2026-39892 | cryptography | 45.0.0–46.0.6 | 46.0.7 | 5.5 | MEDIUM | ✅ **Not affected** | — | Buffer overflow. GULA has `>=42.0.0` (<45.0.0). |
| CVE-2026-26007 | cryptography | <46.0.5 | 46.0.5 | 5.3 | MEDIUM | ✅ **Not affected** | — | ECDH info disclosure. |
| CVE-2026-34073 | cryptography | <46.0.6 | 46.0.6 | 5.5 | MEDIUM | ✅ **Not affected** | — | DNS validation. |
| CVE-2024-26130 | cryptography | 41.0.0–42.0.4 | 42.0.5 | 7.5 | HIGH | ✅ **Not affected** | — | NULL deref DoS. GULA has `>=42.0.0` — verify exact pinned. |
| CVE-2023-50447 | Pillow | <10.2.0 | 10.2.0 | 7.5 | HIGH | ✅ **Not affected** | — | Heap buffer overflow. GULA has `>=10.4.0`. |
| CVE-2024-22195 | jinja2 | <3.1.3 | 3.1.3 | 5.3 | MEDIUM | ✅ **Not affected** | — | Sandbox escape via `\|attr` filter. GULA has `>=3.1.4`. |
| CVE-2023-33733 | reportlab | <4.0 | 4.0 | 9.1 | CRITICAL | ✅ **Not affected** | — | RCE via code injection. GULA has `>=4.1.0`. |

### 1.2 JavaScript Dependencies

| CVE ID | Package | Affected Version | Fixed In | CVSS | Severity | Status | Notes |
|--------|---------|------------------|----------|------|----------|--------|-------|
| CVE-2022-23529 | jsonwebtoken | <9.0.1 | 9.0.1 | 7.6 | HIGH | ✅ **Not affected** | Unrestricted key type. GULA has `^9.0.3`. |
| CVE-2024-39338 | axios | <1.7.4 | 1.7.4 | 6.5 | MEDIUM | ✅ **Not affected** | SSRF. Resolutions enforce `>=1.8.2`. |
| Various | lodash | <4.17.21 | 4.17.21 | 7.4 | HIGH | ✅ **Not affected** | Prototype pollution. GULA has `4.17.21`. |

### 1.3 Docker Images

| CVE ID | Image | Severity | Status | Notes |
|--------|-------|----------|--------|-------|
| N/A | nginx:1.25-alpine | MEDIUM | ⚠️ **Outdated** | nginx 1.25 series is EOL. Upgrade to `nginx:1.26-alpine` or `nginx:1.27-alpine`. |
| Various | python:3.11-slim / 3.12-slim | VARIES | ✅ **Monitor** | Regularly rebuild to pick up OS patch updates. |

### 1.4 Critical Vulnerability Summary

| Severity | Count | Action Required |
|----------|-------|----------------|
| CRITICAL (CVSS >=9) | 1 (reportlab sandbox escape) | Verify reportlab >=4.2.1 |
| HIGH (CVSS 7–8.9) | 3 direct active | Upgrade python-jose to >=3.4.0; upgrade gunicorn to >=22.0.0 |
| MEDIUM (CVSS 4–6.9) | 7+ active | Standard patching cadence |

---

## 2. CWE Mapping

### 2.1 CWE Registry

| CWE ID | Name | Where It Applies | Current Mitigation | Gaps | Priority |
|--------|------|------------------|-------------------|------|----------|
| CWE-89 | SQL Injection | All SQLAlchemy ORM queries across routes/ and services/ | Full ORM usage with parameterized queries; no raw SQL concatenation with user input; Pydantic validation on all request models | No automated SQL injection testing in CI; no SQLAlchemy event-based query inspection | LOW |
| CWE-79 | Cross-Site Scripting | Any user-supplied text rendered in JSON API responses | CSP restricted to `self`; API returns JSON only (no HTML rendering); httpOnly cookies; `X-XSS-Protection` header | `'unsafe-inline'` in CSP `script-src` neutralizes XSS protection for inline scripts; no HTML output encoding (JSON-only mitigates most); no input sanitization for user text in dashboards (frontend concern) | HIGH |
| CWE-352 | Cross-Site Request Forgery | All unsafe-method endpoints (POST/PUT/DELETE/PATCH) | `SameSite=Strict` on cookies; httpOnly cookies; `X-Frame-Options: DENY` prevents clickjacking | **No CSRF token mechanism** — SameSite is insufficient for all browsers (Safari, older Chrome, embedded browsers) | HIGH |
| CWE-918 | Server-Side Request Forgery | External API calls to MOI NID, Insurance, Residency APIs; AI model calls to Ollama | None — no SSRF protection found | No URL validation/allowlisting; no private IP block; no DNS rebinding protection | CRITICAL |
| CWE-639 | Insecure Direct Object Reference | Patient/order/result endpoints | ABAC via `require_own_lab()` ensures lab_id tenant isolation | No attribute-based access for resource-level ownership beyond lab_id (acceptable given architecture) | LOW |
| CWE-306 | Missing Authentication | JWT-protected endpoints | JWT (HS256) access + refresh tokens; Redis-backed JTI blacklist; cookie + Bearer header extraction | DocsAuthMiddleware guards docs endpoints; no unauthenticated data access paths identified | LOW |
| CWE-862 | Missing Authorization | Role/permission-gated endpoints | RBAC with 9 roles × extended permissions; `require_permission()`, `require_role()` dependencies; permission versioning for instant revocation | Permission caching/stale detection (acceptable for O(1) lookup) | LOW |
| CWE-326 | Inadequate Encryption Strength | National ID encryption | Fernet (AES-128-CBC + HMAC-SHA256); HMAC-sign-then-encrypt pattern | No key rotation mechanism; no key-version tagging on ciphertexts; 128-bit key (adequate but 256-bit preferred) | MEDIUM |
| CWE-798 | Use of Hardcoded Credentials | `config.py` secret validation | `_is_weak_secret()` detection rejects common weak patterns; hard `sys.exit(1)` for missing/weak secrets in production | `SUPABASE_SERVICE_KEY`, `MOI_NID_API_KEY`, `FCM_SERVER_KEY`, `APNS_KEY`, `CF_API_TOKEN` have no weak-pattern validation; env-file-based secrets are static until manually rotated | MEDIUM |
| CWE-287 | Improper Authentication | Login flow | bcrypt password hashing with dummy-hash timing-safe login; JWT dual-secret architecture | No MFA/2FA; no account-lockout after N failed attempts; no password complexity policy at API layer | HIGH |
| CWE-613 | Insufficient Session Expiration | Refresh token flow | JWT access tokens (30-min expiry); refresh tokens (30-day expiry); Redis JTI blacklist; permission version bump safety net | No refresh token rotation (old token remains valid after refresh); no absolute session timeout; no concurrent session limit; no geolocation/IP-based session validation | MEDIUM |
| CWE-532 | Information Exposure Through Log Files | Structured JSON logging throughout | Request ID correlation via `RequestIDMiddleware`; failed-login HMAC-email hashing | **No centralized PII redaction** — user emails, IPs, and details fields could contain PII logged verbatim | HIGH |
| CWE-20 | Improper Input Validation | All Pydantic request models | Full Pydantic input validation on all request models | No automated fuzz testing; no property-based testing | LOW |
| CWE-400 | Uncontrolled Resource Consumption | Rate limiting | Redis-backed multi-tier rate limiting (public 30/min, user 60/min, auth 10/min, admin 20/min); dual-key strategy; dynamic IP hard-block on 5× threshold | Fixed-window algorithm (burst at window edge); no per-route granular limits beyond generic tiers | LOW |
| CWE-778 | Insufficient Logging | Security event monitoring | Audit hash chain; failed-login logging; health watchdog alerts on grade transitions; Sentry integration | No brute-force account lockout (only IP-level); no anomaly detection for unusual access patterns; no SIEM integration; no automated incident response | HIGH |
| CWE-269 | Improper Privilege Management | RBAC/ABAC | 9 roles; `assert_lab_within_limit()` for subscription caps; province-level admin scoping | None identified — RBAC is comprehensive | LOW |

### 2.2 CWE Gap Analysis

**Immediate priority gaps (CWE score > 0, no mitigation):**
- **CWE-918 (SSRF):** Zero mitigation. CRITICAL risk for a platform calling government APIs.
- **CWE-352 (CSRF):** Zero mitigation beyond SameSite cookies. HIGH risk for medical data mutations.

**Partial mitigation gaps:**
- **CWE-79 (XSS):** CSP weakened by `'unsafe-inline'`. JSON-only API reduces surface but does not eliminate risk.
- **CWE-326 (Encryption):** Fernet is strong but key rotation is impossible without version tagging.
- **CWE-798 (Secrets):** Env files are static. No external secrets backend.
- **CWE-532 (Logging):** PII flows through logs unchecked.

---

## 3. OWASP Top 10 (2021) Mapping

### A01: Broken Access Control
- **Status:** ✅ **Mitigated**
- **Implementation:** RBAC with 9 roles × extended permissions; ABAC via `require_own_lab()` for tenant isolation; `require_permission()` FastAPI dependency with O(1) lookup; `require_role()` for role gating; `require_feature_for_lab()` with per-tenant feature flags; `assert_lab_within_limit()` for subscription caps; permission versioning (`bump_perm_version`) for instant revocation; province-level admin scoping
- **Gaps:** No attribute-based access for resource-level ownership beyond lab_id (acceptable)
- **Files:** `backend/app/security/rbac.py`, `dependencies.py`

### A02: Cryptographic Failures
- **Status:** ⚠️ **Partial**
- **Implementation:** Fernet (AES-128-CBC + HMAC-SHA256) for NID encryption; HMAC-sign-then-encrypt pattern; TLS termination at nginx api-gateway; HSTS with `includeSubDomains`; secure cookie flags (httpOnly, SameSite, Secure)
- **Gaps:** No key rotation mechanism; no key-version tagging on ciphertexts; no HSTS `preload` directive; no OCSP stapling in nginx; no TLS version enforcement in app code
- **Files:** `backend/app/security/encryption.py`, `shared/security/encryption.py`, `backend/app/main.py` (middleware)

### A03: Injection
- **Status:** ✅ **Mitigated**
- **Implementation:** Full SQLAlchemy ORM with parameterized queries; no raw SQL concatenation; Pydantic input validation on all request models; `text()` calls use fixed queries only
- **Gaps:** No automated SQL injection testing in CI; no fuzz testing
- **Files:** All ORM model and route files

### A04: Insecure Design
- **Status:** ⚠️ **Partial**
- **Implementation:** AI safety pattern ("Suggest → Human Approve → System Enforce"); frozen `AISuggestion` dataclass; `AIGuardrailViolation` exception; sandbox with explicit operation whitelist; all sandbox handlers read-only
- **Gaps:** No AI output validation layer to detect hallucinations; no adversarial prompt detection; no context window limits; 32/35 routes bypass service layer (architecture violation)
- **Files:** `backend/app/ai/`, various route files

### A05: Security Misconfiguration
- **Status:** ⚠️ **Partial**
- **Implementation:** Explicit CORS origin whitelist; restricted HTTP methods; `SecurityHeadersMiddleware` sets 7+ security headers; `MaxBodySizeMiddleware` (10MB); `ReadinessMiddleware` blocks until system ready; `DegradedModeMiddleware` in circuit-breaker mode
- **Gaps:** CSP `'unsafe-inline'` in script-src weakens XSS protection; no CSP `report-uri`/`report-to`; no `Cross-Origin-Embedder-Policy`; nginx 1.25-alpine is EOL
- **Files:** `backend/app/main.py:390-428`

### A06: Vulnerable and Outdated Components
- **Status:** ⚠️ **Partial**
- **Implementation:** SBOM generated; security scanning in CI (bandit, safety)
- **Gaps:** **3 active CVEs** (python-jose algorithm confusion, reportlab sandbox, gunicorn splitting); 8 microservice Dockerfiles have zero version pins; 7 Dockerfiles install packages without version constraints; nginx 1.25 EOL; no `pip-audit` or `npm audit` in CI; no automated dependency scanning
- **Files:** SBOM.md, 8 microservice Dockerfiles

### A07: Identification and Authentication Failures
- **Status:** ⚠️ **Partial**
- **Implementation:** JWT (HS256) dual-secret architecture; bcrypt with dummy-hash timing-safe login; Redis-backed JTI blacklist; token type discrimination; permission version safety net; multi-factor cookie extraction (cookie + Bearer)
- **Gaps:** **No MFA/2FA**; no account-lockout after N failed attempts (only IP-level rate limiting); no password complexity policy at API layer; no refresh token rotation (old token remains valid after rotation)
- **Files:** `backend/app/security/auth.py`, `backend/app/routes/login.py`

### A08: Software and Data Integrity Failures
- **Status:** ✅ **Mitigated**
- **Implementation:** SHA-256 hash-chained audit log; HMAC-signed anchor files on disk; genesis hash chain root; `verify_audit_chain()` endpoint; dual-key anchor HMAC for key rotation; `outbox_events` table for at-least-once delivery
- **Gaps:** No periodic chain verification as background task; anchor files to container-local filesystem (lost on restart unless volume-mounted)
- **Files:** `backend/app/services/audit_service.py`, `backend/app/models/audit_log.py`

### A09: Security Logging and Monitoring Failures
- **Status:** ⚠️ **Partial**
- **Implementation:** Structured JSON logging; request ID correlation; Sentry integration; health alert watchdog (GREEN/YELLOW/RED scoring); rate-limit dynamic IP block; circuit breaker for DB/Redis; `RequestTimingMiddleware` access logs
- **Gaps:** **No centralized PII redaction**; no SIEM integration; no anomaly detection (geo-velocity, multi-IP patterns); no IDS/IPS; no automated incident response
- **Files:** `backend/app/core/logging_config.py`, `backend/app/main.py`

### A10: Server-Side Request Forgery (SSRF)
- **Status:** ❌ **Gap**
- **Implementation:** None — no SSRF protection found anywhere in the codebase
- **Gaps:** **No URL validation or allowlisting** for external API calls (MOI NID, Insurance, Residency, AI Ollama). If an attacker can influence adapter mode or URL, they could SSRF internal services.
- **Files:** N/A — mitigation needs to be created in `shared/security/ssrf.py`

---

## 4. OWASP LLM Top 10 Mapping

### LLM01: Prompt Injection
- **Status:** ⚠️ **Partial**
- **Mitigation:** AI sandbox with explicit operation whitelist (`_REGISTRY`); all sandbox handlers are read-only; kernel plugin loader blocks dangerous operations
- **Gaps:** No adversarial prompt detection at API boundary; no input sanitization for AI prompts; no rate limiting on AI calls per lab
- **Files:** `backend/app/ai/sandbox.py`, `backend/app/ai/guardrails.py`

### LLM02: Insecure Output Handling
- **Status:** ⚠️ **Partial**
- **Mitigation:** `AISuggestion` dataclass is frozen with `is_approved=False` at creation; `requires_doctor_review` flag on flagged outputs; clinical operations are rules-based (deterministic)
- **Gaps:** No AI model output validation layer to detect hallucinations; no schema enforcement on AI output keys; no output sanitization before display
- **Files:** `backend/app/ai/guardrails.py`

### LLM03: Training Data Poisoning
- **Status:** ✅ **Not Applicable**
- **Rationale:** GULA does not train custom models. AI features use pre-trained models (Gemini API via `google-generativeai`) and rules-based clinical interpretation. No fine-tuning pipeline exists.

### LLM04: Model Denial of Service
- **Status:** ❌ **Gap**
- **Mitigation:** None specific to AI
- **Gaps:** No rate limiting on AI calls; no context window limits; no request size limits for AI prompts; no timeout configuration on AI model calls; no cost-aware throttling
- **Files:** `backend/app/routes/ai.py`

### LLM05: Supply Chain Vulnerabilities
- **Status:** ⚠️ **Partial**
- **Mitigation:** SBOM generated for all dependencies; `google-generativeai` pinned via shared library
- **Gaps:** No pinning of AI SDK versions (`google-generativeai` uses `>=0.8.0`); no model provenance verification; no integrity checks for model responses
- **Files:** `shared/pyproject.toml`

### LLM06: Sensitive Information Disclosure
- **Status:** ⚠️ **Partial**
- **Mitigation:** AI sandbox operations are read-only (no DB writes); `_ABSOLUTELY_BLOCKED` set prevents 10 categories of operations
- **Gaps:** Patient data could theoretically be included in AI prompts if not properly filtered; no PII redaction layer before AI calls; no training data extraction prevention
- **Files:** `backend/app/ai/sandbox.py`, `backend/app/ai/guardrails.py`

### LLM07: Insecure Plugin Design
- **Status:** ⚠️ **Partial**
- **Mitigation:** Kernel plugin loader blocks dangerous operations; explicit operation whitelist
- **Gaps:** No plugin sandboxing beyond operation whitelist; no plugin isolation at process level
- **Files:** `backend/app/kernel/`

### LLM08: Excessive Agency
- **Status:** ✅ **Mitigated**
- **Mitigation:** "AI = Suggest, Human = Approve, System = Enforce" — fundamental safety pattern; immutable `AISuggestion` dataclass (always `is_approved=False` at creation); `AIGuardrailViolation` exception (must not be silently caught); all sandbox handlers are read-only
- **Files:** `backend/app/ai/guardrails.py`

### LLM09: Overreliance
- **Status:** ⚠️ **Partial**
- **Mitigation:** `requires_doctor_review` flag on flagged outputs; clinical operations are rules-based (deterministic, not ML)
- **Gaps:** No confidence scoring on AI suggestions; no explicit disclaimer in API responses; no audit trail specific to AI-suggested actions
- **Files:** `backend/app/ai/`

### LLM10: Model Theft
- **Status:** ✅ **Not Applicable**
- **Rationale:** GULA does not host proprietary models. Uses Gemini API (Google-managed). No model weights stored in repository. Model queries go through authenticated API calls.

---

## 5. MITRE ATT&CK Mapping

### T1078: Valid Accounts
- **Relevance:** JWT token compromise; lab user account misuse
- **Current Defenses:** JWT dual-secret (access + refresh); bcrypt password hashing; timing-safe login (dummy hash prevents user enumeration); Redis JTI blacklist for revocation; permission version bump as DB-level safety net
- **Gaps:** No MFA; no account lockout; no concurrent session limits; no geolocation validation
- **Detection:** Rate-limit triggers on login attempts; audit logs record auth events
- **Priority:** HIGH

### T1190: Exploit Public-Facing Application
- **Relevance:** FastAPI HTTP endpoints exposed through nginx api-gateway; ~202 endpoints across 36 route modules
- **Current Defenses:** 11-layer middleware stack (body size, CORS, security headers, readiness, degraded mode, concurrency limiting); Pydantic input validation on all endpoints; rate limiting (multi-tier); CSP + HSTS + X-Frame-Options
- **Gaps:** SSRF guard missing; CSRF protection missing; CSP `'unsafe-inline'` weakens XSS protection
- **Detection:** `RequestTimingMiddleware` access logs; Sentry error tracking; health alert watchdog
- **Priority:** CRITICAL

### T1133: External Remote Services
- **Relevance:** Device bridge (ASTM/HL7) accepts data from lab instruments; edge agent communicates with labs; nhop-platform national registry integration
- **Current Defenses:** Device bridge uses HMAC-signed device tokens; gula_client.py validates responses; all external services use HTTPS
- **Gaps:** No mTLS between services; no device certificate validation documented; no network segmentation for device bridge
- **Priority:** MEDIUM

### T1110: Brute Force
- **Relevance:** Login endpoint `/auth/login`; token refresh endpoint
- **Current Defenses:** Rate limiting (auth tier: 10 requests/min); bcrypt password hashing (computationally expensive); timing-safe login (dummy hash prevents timing attacks)
- **Gaps:** No user-level account lockout (only IP-level rate limiting); no anomaly detection for distributed brute force (attack from multiple IPs against single user)
- **Detection:** Rate-limit 429 responses; failed-login audit logging with email HMAC
- **Priority:** HIGH

### T1562: Impair Defenses
- **Relevance:** Audit log tampering; log clearing; rate limit bypass
- **Current Defenses:** SHA-256 hash-chained audit log (tamper-evident); HMAC-signed anchor files on disk; dual-key anchor HMAC for key rotation; `verify_audit_chain()` endpoint
- **Gaps:** No external SIEM; no immutable log storage; anchor files on container-local filesystem (lost on restart)
- **Detection:** Periodic chain verification (recommended — not implemented)
- **Priority:** MEDIUM

### T1498: Network Denial of Service
- **Relevance:** API endpoints; login; AI model calls
- **Current Defenses:** Rate limiting (Redis-backed, shared across workers); dynamic IP hard-block on 5× threshold; `ConcurrencyLimitMiddleware` (max 50 concurrent requests per worker, clinical writes exempt); `MaxBodySizeMiddleware` (10MB limit); health alert watchdog
- **Gaps:** Fixed-window rate limiting allows burst; no per-route granular limits; no WAF/CDN-level DDoS protection documented
- **Detection:** Rate-limit 429 responses; health watchdog grade transitions; circuit breaker trips
- **Priority:** MEDIUM

### T1059: Command and Scripting Interpreter
- **Relevance:** AI sandbox; reportlab PDF generation; jinja2 templating
- **Current Defenses:** AI sandbox uses explicit operation whitelist; no `exec()`/`eval()` in production code; no `os.system()` in production routes; `subprocess` only in test/engineering tooling
- **Gaps:** Reportlab sandbox escape (CVE-2024-42512) is unverified; jinja2 sandbox escape patched (CVE-2024-22195 — not affected)
- **Detection:** AI guardrail violations logged; Sentry error tracking
- **Priority:** MEDIUM

### T1204: User Execution
- **Relevance:** File upload (ID scan); QR code scanning (patient cards)
- **Current Defenses:** File upload: 2MB size limit; strict content-type validation (image/jpeg, png, webp, bmp); minimum size check (1000 bytes); processed in executor (non-blocking)
- **Gaps:** No virus scanning; no EXIF stripping; no file-storage quarantine period
- **Priority:** MEDIUM

---

## 6. MITRE ATLAS Mapping (AI-Specific)

### AML.T0000: Introduction of Compromised Artifact
- **Relevance:** AI model dependencies (google-generativeai SDK)
- **Status:** ⚠️ Partial — SBOM covers AI SDK but no model provenance checks
- **Mitigation:** Pin SDK version in shared library

### AML.T0001: LLM Prompt Injection (direct)
- **Relevance:** AI interpretation endpoints; clinical suggestion generation
- **Status:** ⚠️ Partial — sandbox whitelist provides some protection but no adversarial prompt detection
- **Mitigation:** AI sandbox with read-only handlers; blocked operations list

### AML.T0002: LLM Prompt Injection (indirect)
- **Relevance:** Patient data embedded in AI prompts; lab results as context
- **Status:** ❌ Gap — no input sanitization layer before AI calls
- **Mitigation needed:** PII redaction layer; prompt template sanitization

### AML.T0019: Denial of Service (ML Model)
- **Relevance:** AI API endpoints; Ollama model calls
- **Status:** ❌ Gap — no rate limiting or cost-aware throttling on AI calls
- **Mitigation needed:** Per-lab AI rate limits; request size limits; timeout configuration

### AML.T0024: Information Leakage via Model Output
- **Relevance:** AI-suggested clinical interpretations
- **Status:** ⚠️ Partial — output validation checks structure but not content
- **Mitigation:** `requires_doctor_review` flag; manual review process

### AML.T0050: Model Inversion Attack
- **Relevance:** Patient data used in AI query context
- **Status:** ✅ Not applicable — GULA doesn't host models, uses external API
- **Rationale:** Gemini API handles model isolation

### AML.T0051: Membership Inference
- **Relevance:** Training data extraction from model responses
- **Status:** ✅ Not applicable — GULA does not train on patient data

### AML.T0053: Unsafe Plugin / Agent Execution
- **Relevance:** AI plugins through kernel system
- **Status:** ⚠️ Partial — operation whitelist exists but plugin isolation is limited
- **Mitigation:** Kernel plugin loader blocks dangerous operations

---

## 7. NIST SSDF Mapping

### PO: Prepare the Organization

| Practice | Implementation | Status |
|----------|---------------|--------|
| PO.1: Identify security requirements | CLAUDE.md documents security invariants; config.py validates secrets at startup; middleware stack defined | ✅ Complete |
| PO.2: SBOM management | SBOM generated manually (not CI-automated); CycloneDX v1.6 files exist | ⚠️ Partial |
| PO.3: Risk assessment | Security Hardening Report (20 dimensions) completed; scoring framework exists | ✅ Complete |

### PS: Protect the Software

| Practice | Implementation | Status |
|----------|---------------|--------|
| PS.1: Protect all forms of code | Git repository; private (no public access); CLAUDE.md non-negotiables | ✅ Complete |
| PS.2: Protect secrets | `_is_weak_secret()` detection; hard fail on missing secrets; `make secrets-gen` | ⚠️ Partial — no external secrets backend |
| PS.3: Control access to build/CI | GitHub Actions with CI pipeline; blue-green deployment | ✅ Complete |
| PS.4: Secure build environment | Docker-based builds; `make ci` replicates CI locally | ✅ Complete |
| PS.5: Protect integrity of source code | Signed commits not enforced; code review expected | ⚠️ Partial |
| PS.6: Protect integrity of third-party packages | SBOM tracks deps; bandit/linting in CI; 3 unpinned CVEs active | ❌ Gap |

### PW: Produce Well-Secured Software

| Practice | Implementation | Status |
|----------|---------------|--------|
| PW.1: Design security in | 11-layer middleware; RBAC/ABAC; self-healing; hash-chained audit | ✅ Complete |
| PW.2: Review design for security | Security Hardening Report; architecture review | ✅ Complete |
| PW.3: Reuse trusted software | Shared library for auth, encryption, logging | ✅ Complete |
| PW.4: Verify third-party software | SBOM generated; safety/bandit scanning in CI | ⚠️ Partial |
| PW.5: Reuse secure coding practices | Pydantic validation everywhere; ORM parameterized queries | ✅ Complete |
| PW.6: Integrate security into build | syntax-gate + lint + security-scan in CI; `make ci` | ✅ Complete |
| PW.7: Verify security of software | 124 tests; penetration testing not mentioned | ⚠️ Partial |
| PW.8: Configure for deployment | Production config in `.env.production`; HSTS in production only | ✅ Complete |

### RV: Respond to Vulnerabilities

| Practice | Implementation | Status |
|----------|---------------|--------|
| RV.1: Identify vulnerabilities | CVE tracking in SBOM; security-scan CI job | ✅ Complete |
| RV.2: Analyze vulnerabilities | CVE severity rating; impact analysis in SBOM | ✅ Complete |
| RV.3: Fix vulnerabilities | 3 active CVEs unpatched; no automated patch enforcement | ❌ Gap |
| RV.4: Disclose vulnerabilities | No vulnerability disclosure program documented | ❌ Gap |

### RC: Recover from Incidents

| Practice | Implementation | Status |
|----------|---------------|--------|
| RC.1: Incident response plan | Health alert watchdog; circuit breaker; self-healing engine | ⚠️ Partial — no formal IR plan documented |
| RC.2: Continue operations | Degraded mode; circuit breaker isolation; backup/restore (`make backup`) | ✅ Complete |

---

## 8. SLSA Compliance

### SLSA Build Level Assessment

| Requirement | Level | Status | Notes |
|-------------|-------|--------|-------|
| Provenance exists | L1 | ✅ | CI pipeline generates artifacts |
| Provenance is authenticated | L2 | ⚠️ | GitHub Actions provides provenance but no attestations |
| Provenance is non-forgeable | L3 | ❌ | No signed provenance attestations |
| Build as code | L1 | ✅ | Docker Compose + CI/CD YAML |
| Isolated build | L2 | ✅ | Docker containers for builds |
| Hermetic build | L3 | ❌ | Dependencies fetched from network during build |
| Reproducible build | L4 | ❌ | No reproducibility guarantee |
| Dependency graph | L2 | ⚠️ | SBOM generated but not CI-integrated; CycloneDX files exist |

**Current SLSA Level: ~L1** — Basic provenance exists but lacks attestation, hermetic sealing, and reproducibility.

### Gaps to Next Level

| Gap | Effort | Impact |
|-----|--------|--------|
| Add `pip-audit` + `npm audit` to CI | 1 hour | Dependency integrity verification |
| Generate SBOM in CI pipeline | 2 hours | Automated dependency tracking |
| Add signed attestations (cosign) | 4 hours | Non-forgeable provenance (L3) |
| Pin all Dockerfile dependencies | 2 hours | Hermetic build step (L3) |
| Make builds deterministic | 8 hours | Reproducible builds (L4) |

---

## 9. Remediation History

| # | Date | Fix Description | Related CVE/CWE | Files Changed | Verification Method | Fixed By |
|---|------|----------------|-----------------|---------------|---------------------|----------|
| 1 | 2026-07-14 | Auth hardening: JWT dual-secret (access + refresh); dummy-hash timing-safe login | CWE-287, CWE-306 | `auth.py`, `login.py` | pytest security tests | Assessment |
| 2 | 2026-07-14 | AI guardrails: sandbox whitelist; read-only handlers; blocked operations | CWE-284, CWE-829 | `ai/guardrails.py`, `ai/sandbox.py` | Unit tests; scenario tests | Assessment |
| 3 | 2026-07-14 | Audit trail: SHA-256 hash chain; HMAC-signed anchor files; verify endpoint | CWE-778, CWE-353 | `audit_service.py`, `audit_log.py` | Chain verification tests | Assessment |
| 4 | 2026-07-14 | Rate limiting: Redis-backed multi-tier; dual-key strategy; dynamic IP block | CWE-400, T1498 | `rate_limit.py` | pytest tests; chaos tests | Assessment |
| 5 | 2026-07-14 | RBAC/ABAC: 9 roles; permission versioning; tenant isolation | CWE-862, CWE-639 | `rbac.py`, `dependencies.py` | pytest tests | Assessment |
| 6 | 2026-07-14 | File upload: size limits; content-type validation; minimum size check | CWE-20, T1204 | `id_scan.py` | pytest tests | Assessment |
| 7 | 2026-07-14 | Secrets: `_is_weak_secret()` detection; hard fail on missing/weak secrets | CWE-798 | `config.py` | Startup validation tests | Assessment |

### Open Remediation Items

| # | Priority | Fix Description | Related CVE/CWE | Target Date | Assigned |
|---|----------|----------------|-----------------|-------------|----------|
| 1 | CRITICAL | Implement SSRF guard — URL validation, private IP block, allowlist | CWE-918 | TBD | — |
| 2 | HIGH | Add CSRF middleware — Double-Submit Cookie pattern | CWE-352 | TBD | — |
| 3 | HIGH | Remove `'unsafe-inline'` from CSP `script-src` — use nonce/strict-dynamic | CWE-79 | TBD | — |
| 4 | HIGH | Add PII redaction to JSON logging formatter | CWE-532 | TBD | — |
| 5 | HIGH | Implement account lockout after N failed attempts | CWE-287, T1110 | TBD | — |
| 6 | HIGH | Upgrade python-jose to >=3.4.0 | CVE-2024-33663, CVE-2024-33664, CVE-2024-29370 | TBD | — |
| 7 | MEDIUM | Add refresh token rotation | CWE-613 | TBD | — |
| 8 | MEDIUM | Add key-version tagging to encrypted values | CWE-326 | TBD | — |
| 9 | MEDIUM | Add periodic audit-chain verification background task | CWE-778 | TBD | — |
| 10 | MEDIUM | Add EXIF stripping on image uploads | T1204 | TBD | — |
| 11 | MEDIUM | Add brute-force anomaly detection (geo-velocity, multi-IP) | T1110 | TBD | — |
| 12 | MEDIUM | Upgrade gunicorn to >=22.0.0 | CVE-2024-1135 | TBD | — |
| 13 | MEDIUM | Verify reportlab >=4.2.1 | CVE-2024-42512 | TBD | — |
| 14 | MEDIUM | Add CI dependency scanning (pip-audit, npm audit) | SLSA L2 | TBD | — |
| 15 | LOW | Add automated SAST/fuzz testing to CI | CWE-20 | TBD | — |

---

## 10. Continuous Monitoring

### 10.1 What to Monitor

| Category | What to Monitor | Why | Priority |
|----------|----------------|-----|----------|
| **Authentication** | Failed login attempts (per user, per IP); token refresh frequency; account lockout events | Detect brute force, credential stuffing, account takeover | CRITICAL |
| **Authorization** | Permission denial rate; RBAC bypass attempts; lab_id tampering | Detect privilege escalation attempts | HIGH |
| **Rate Limiting** | 429 response rate per tier; IP block events; rate-limit key collision | Detect DoS attacks, misconfigured clients, anomaly | HIGH |
| **Circuit Breaker** | DB/Redis circuit state transitions; degraded mode activations | Detect infrastructure failure; prevent cascading | HIGH |
| **SSRF** | External API call frequency; unexpected URL destinations; private IP resolution attempts | Detect SSRF exploitation | CRITICAL |
| **AI Guardrails** | Blocked operation attempts; guardrail violation rate; sandbox escape attempts | Detect AI misuse or prompt injection | HIGH |
| **Audit Chain** | Chain integrity violations; missed entries; anchor file tampering | Detect audit log manipulation | HIGH |
| **Dependency CVEs** | New CVE disclosures for all 44+ Python + 68+ JS packages | Prevent exploitation of known vulnerabilities | HIGH |
| **Secrets** | Secret age; rotation frequency; env file changes | Prevent stale/compromised secrets | MEDIUM |
| **Session Management** | Active session count; refresh token reuse; JTI blacklist size | Detect session hijacking or token abuse | MEDIUM |
| **File Upload** | Upload volume; content-type mismatch rate; file size distribution | Detect malware delivery or storage abuse | MEDIUM |
| **Resource Usage** | DB connection pool saturation; Redis memory; worker concurrency level | Detect resource exhaustion DoS | MEDIUM |

### 10.2 How to Monitor

| Monitor Method | Implementation | Status |
|---------------|---------------|--------|
| Structured JSON logging | `shared.logging.JSONFormatter`; request ID correlation via middleware | ✅ Active |
| Sentry error tracking | `sentry-sdk[fastapi]` integration; opt-in via `SENTRY_DSN` env var | ✅ Active |
| Health endpoints | `/health`, `/health/live`, `/health/ready`, `/health/status`, `/health/deep` | ✅ Active |
| Health alert watchdog | 60-sec scoring loop (GREEN/YELLOW/RED); webhook alerts on grade transitions | ✅ Active |
| Prometheus metrics | Scrape config in `config/prometheus/`; metrics endpoint (opt-in profile) | ⚠️ Requires `make monitoring` |
| Grafana dashboards | Provisioned dashboards in `config/grafana/` (opt-in profile) | ⚠️ Requires `make monitoring` |
| Audit chain verification | `verify_audit_chain()` endpoint; manual trigger available | ❌ Not automated |
| CI security scanning | `bandit -ll -ii`; safety (CVE); hadolint; gitleaks; `/tmp` write check | ✅ Active |
| SIEM forwarding | No SIEM integration | ❌ Gap |
| Anomaly detection | No automated anomaly detection | ❌ Gap |

### 10.3 Alert Thresholds

| Alert | Threshold | Response | Severity | Channel |
|-------|-----------|----------|----------|---------|
| Multiple failed logins | >5 failures/user in 15 min | Temporary account lockout; notify admin | HIGH | Alert webhook + log |
| Rate limit threshold hit | >3× normal rate on any tier | Investigate source IP; consider permanent block | MEDIUM | Log + periodic review |
| Circuit breaker open | DB/Redis circuit transitions to OPEN | Auto-repair engine kicks in; degraded mode activated | CRITICAL | Alert webhook |
| Health grade change | GREEN → YELLOW or YELLOW → RED | Immediate investigation; auto-repair; page on-call | CRITICAL | Alert webhook |
| Health grade RED >5 min | RED persists for 5+ minutes | Escalate; full incident response | CRITICAL | Alert webhook + SMS |
| Audit chain break | `verify_audit_chain()` finds broken entries | Forensic investigation; data integrity check | CRITICAL | Alert webhook |
| New CVE in critical package | CVE with CVSS >=9 on any CRITICAL-rated package | Emergency patch window | CRITICAL | Email + Slack |
| Permission version mismatch | Bypass attempts via stale permissions | Force token re-issue; investigate | MEDIUM | Log + periodic review |
| Secret age >90 days | `SECRET_KEY`, `ENCRYPTION_KEY` not rotated in 90+ days | Rotate secrets; notify security team | MEDIUM | Periodic review |
| AI guardrail violation | Any attempt to call blocked operation | Log full context; alert admin; no automated action | HIGH | Log + alert |

### 10.4 Response Procedures

#### Procedure 1: SSRF or External API Compromise
1. **Detect:** Alert webhook fires on unexpected URL destination or private IP resolution
2. **Contain:** Immediately rotate any API keys sent to the compromised target; block outbound traffic from the affected service
3. **Investigate:** Review audit logs for data exfiltration; check whether internal services (metadata endpoint, Redis, Postgres) were queried
4. **Remediate:** Apply SSRF guard patch; add URL to blocklist; deploy updated image
5. **Recover:** Restore from backup if data integrity is compromised; verify no persistence
6. **Post-mortem:** Root cause analysis within 72 hours; update SSRF blocklist

#### Procedure 2: Brute Force / Account Takeover
1. **Detect:** Rate-limit 429 rate spikes or account lockout events
2. **Contain:** Identify and block source IPs at nginx level; invalidate all active sessions for affected users via `bump_perm_version()`
3. **Investigate:** Review audit logs for unauthorized access; check JTI blacklist for token reuse
4. **Remediate:** Force password reset for affected accounts; enable additional monitoring
5. **Recover:** Notify affected users; restore access after password change
6. **Post-mortem:** Review rate limiting configuration; consider adding MFA

#### Procedure 3: Dependency CVE (Critical)
1. **Detect:** CI security scan or CVE alert identifies critical vulnerability
2. **Assess:** Determine if GULA's version is affected; check exploitability in current deployment context
3. **Patch:** Update dependency to fixed version; run full test suite (`make ci`)
4. **Deploy:** Apply emergency deploy outside normal window; use blue-green for zero-downtime
5. **Verify:** Confirm CVE no longer detected by scan; run smoke tests
6. **Post-mortem:** Update SBOM; investigate if CVE was exploitable in GULA context

#### Procedure 4: Audit Chain Tamper
1. **Detect:** `verify_audit_chain()` returns broken entries or anchor file verification fails
2. **Contain:** Immediately isolate the affected database; snapshot the current state; block all mutation operations
3. **Investigate:** Determine scope of tampering (which entries, what time period, which user)
4. **Remediate:** Restore from last known-good backup; replay outbox events; repair chain from anchor files
5. **Recover:** Verify chain integrity with independent verification (anchor file HMACs); re-enable mutations
6. **Post-mortem:** Full forensic investigation; update audit service to prevent recurrence

#### Procedure 5: AI Guardrail Violation
1. **Detect:** Guardrail violation logged with full context
2. **Assess:** Determine if violation was adversarial prompt injection or system bug
3. **Contain:** Block the originating lab's AI access; review any output already sent
4. **Investigate:** Review prompt and output history for the lab; check for data leakage
5. **Remediate:** Update prompt filters; add input sanitization; tighten operation whitelist
6. **Recover:** Restore AI access after remediation verified
7. **Post-mortem:** Update AI security posture; add test case for the bypass vector

### 10.5 Monitoring Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         Production                              │
│                                                                 │
│  gula-backend ──► Structured JSON Logs ──► Docker log driver    │
│       │                                                         │
│       ├──► Sentry (error tracking, opt-in via SENTRY_DSN)       │
│       │                                                         │
│       ├──► /health endpoints (5 paths, always visible)          │
│       │       └──► Watchdog (60-sec loop, grade transitions)    │
│       │               └──► Alert webhook (Telegram/Discord/Slack)│
│       │                                                         │
│       ├──► Prometheus (metrics, opt-in profile)                 │
│       │       └──► Grafana dashboards                           │
│       │                                                         │
│       ├──► Audit chain (SHA-256, HMAC anchors, daily verify)   │
│       │                                                         │
│       └──► CI security scan (safety, bandit, hadolint, gitleaks)│
│                                                                 │
│  nginx (api-gateway) ──► Access logs ──► logrotate              │
└─────────────────────────────────────────────────────────────────┘
```

### 10.6 Security Scorecard

| Dimension | Score (0-10) | Trend | Target | Last Assessed |
|-----------|-------------|-------|--------|---------------|
| Authentication | 9/10 | — | 10/10 | 2026-07-14 |
| Authorization | 10/10 | — | 10/10 | 2026-07-14 |
| Secrets Management | 9/10 | — | 10/10 | 2026-07-14 |
| Encryption | 9/10 | — | 10/10 | 2026-07-14 |
| TLS | 6/10 | — | 9/10 | 2026-07-14 |
| Security Headers | 6/10 | — | 9/10 | 2026-07-14 |
| CORS | 10/10 | — | 10/10 | 2026-07-14 |
| Rate Limiting | 9/10 | — | 10/10 | 2026-07-14 |
| SQL Injection | 10/10 | — | 10/10 | 2026-07-14 |
| XSS | 5/10 | — | 9/10 | 2026-07-14 |
| CSRF | 0/10 | — | 9/10 | 2026-07-14 |
| SSRF | 0/10 | — | 10/10 | 2026-07-14 |
| RCE | 10/10 | — | 10/10 | 2026-07-14 |
| Path Traversal | 10/10 | — | 10/10 | 2026-07-14 |
| File Upload | 8/10 | — | 10/10 | 2026-07-14 |
| Audit Trail | 9/10 | — | 10/10 | 2026-07-14 |
| Logging | 5/10 | — | 9/10 | 2026-07-14 |
| AI Guardrails | 9/10 | — | 10/10 | 2026-07-14 |
| Session Management | 8/10 | — | 10/10 | 2026-07-14 |
| Intrusion Detection | 4/10 | — | 9/10 | 2026-07-14 |
| **Overall** | **7.6/10** | — | **9.5/10** | **2026-07-14** |

---

*This Security Knowledge Base should be updated whenever:*
- *A new CVE is discovered affecting any dependency*
- *A new security control is implemented*
- *A security incident occurs (add to Remediation History)*
- *The threat model changes (new integrations, new AI features)*
- *Quarterly (minimum) for continuous monitoring data*
