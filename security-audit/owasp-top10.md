# OWASP Top 10 (2021) Compliance Assessment

## A01:2021 – Broken Access Control

**Status:** Partially Implemented

**Existing Controls:** ✅
- Hierarchical RBAC with 30+ roles
- ABAC engine with attribute-based conditions
- Purpose-of-use enforcement
- Break-glass emergency access system
- Consent enforcement
- VIP protection
- Minor protection rules

**Gaps:** ❌
- No object-level access control enforcement at API gateway level
- Missing authorization checks in some microservice routes
- No tenant isolation audit testing

**Risk Level:** Medium

---

## A02:2021 – Cryptographic Failures

**Status:** Partially Implemented

**Existing Controls:** ✅
- Fernet (AES-256) encryption for sensitive fields
- bcrypt password hashing (cost factor 12)
- JWT with HS256
- National ID HMAC hashing
- Separate encryption and signing keys

**Gaps:** ❌
- No database encryption at rest
- TLS not enforced in Terraform ALB configuration
- Environment key files stored in plaintext
- No key rotation policy documented

**Risk Level:** Critical

---

## A03:2021 – Injection

**Status:** Mostly Mitigated

**Existing Controls:** ✅
- SQLAlchemy ORM (parameterized queries)
- Pydantic input validation
- No raw SQL in production code
- FastAPI automatic request parsing

**Gaps:** ❌
- Possible SQL injection vector detected in `backend/app/engineering/testing/performance.py:88`
- Possible SQL injection in `backend/app/insurance/api/payments.py:536`
- XML parsing without XXE protection in some modules

**Risk Level:** Medium

---

## A04:2021 – Insecure Design

**Status:** Needs Improvement

**Existing Controls:** ✅
- Application factory pattern
- Startup guard validation
- Feature flags for new functionality
- Degraded mode support

**Gaps:** ❌
- No threat modeling artifacts found
- No security design review documentation
- Rate limiting implemented but not at gateway level

**Risk Level:** Medium

---

## A05:2021 – Security Misconfiguration

**Status:** Needs Improvement

**Existing Controls:** ✅
- Security headers middleware
- CORS configuration
- Environment-specific configuration
- API docs disabled in production (configurable)

**Gaps:** ❌
- CSP allows `unsafe-inline` and `unsafe-eval`
- K8s pods run as root by default
- Terraform security groups allow unrestricted egress
- ConfigMap stores sensitive data
- Debug endpoints exposed in some routes

**Risk Level:** Critical

---

## A06:2021 – Vulnerable and Outdated Components

**Status:** Partially Mitigated

**Existing Controls:** ✅
- Trivy scans show no critical/high CVEs
- Dependencies use pinned versions
- Python dependencies in requirements.txt

**Gaps:** ❌
- No automated dependency scanning in CI/CD
- No SBOM generation
- `mysql2` npm dependency unnecessary (MySQL driver for PostgreSQL-only platform)
- No regular update policy
- `node_modules` included in Docker build context

**Risk Level:** High

---

## A07:2021 – Identification and Authentication Failures

**Status:** Partially Implemented

**Existing Controls:** ✅
- bcrypt password hashing
- JWT with configurable expiry
- Token blacklisting via Redis
- Timing-safe login with dummy hash
- Account lockout via rate limiting
- OAuth2 with PKCE
- SAML SSO
- WebAuthn/FIDO2
- TOTP MFA

**Gaps:** ❌
- No MFA enforcement for privileged users
- No password complexity requirements enforced
- No credential rotation policy
- No breached password detection

**Risk Level:** High

---

## A08:2021 – Software and Data Integrity Failures

**Status:** Not Implemented

**Existing Controls:** ✅
- Signed git commits via githooks
- Pre-commit hooks

**Gaps:** ❌
- No container image signing
- No SBOM generation in CI/CD
- No dependency verification (no lockfile signing)
- No CI/CD pipeline integrity verification

**Risk Level:** Critical

---

## A09:2021 – Security Logging and Monitoring Failures

**Status:** Partially Implemented

**Existing Controls:** ✅
- Comprehensive audit logging
- Structured logging with request IDs
- Prometheus + Grafana + Alertmanager
- Sentry integration
- Health alerting via webhooks

**Gaps:** ❌
- No centralized SIEM integration in production
- Audit logs not stored immutably
- No automated log analysis for threats
- Alerting configured but not tested for security events

**Risk Level:** Medium

---

## A10:2021 – Server-Side Request Forgery (SSRF)

**Status:** Partially Mitigated

**Existing Controls:** ✅
- URL validation in external connectors
- Rate limiting on outbound requests

**Gaps:** ❌
- No explicit SSRF protection at network level
- No URL allowlist for outbound connections
- `httpx` client used without timeout configuration in some places

**Risk Level:** Medium
