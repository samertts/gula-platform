# GULA Security Baseline

**Version:** 1.0  
**Status:** RATIFIED  

---

## 1. Security Posture

GULA operates with a **defense-in-depth, Zero Trust** security model. Security is implemented at every layer: network, application, data, identity, and infrastructure.

## 2. Current Security Maturity

| Domain | Score | Status |
|--------|-------|--------|
| Identity & Access Management | 4.5/5 | JWT + RBAC + ABAC + refresh rotation + permission versioning |
| Encryption | 4.5/5 | AES-256 at rest, TLS in transit, Fernet for PII, HMAC for cards |
| Secrets Management | 5/5 | Hard fail on missing/weak secrets, rotation scripts, KMS |
| Network Security | 5/5 | Two-layer nginx, WAF, IDS (Snort), SIEM (Wazuh + Elastic) |
| Application Security | 4.5/5 | Input validation, rate limiting, security headers, CSP |
| Audit & Logging | 5/5 | Immutable hash-chain audit, correlation IDs, structured logging |
| Vulnerability Management | 4.5/5 | SAST (Bandit + Semgrep), SCA (Safety), DAST (ZAP), container scan (Trivy) |
| Incident Response | 4/5 | Alert webhook, PagerDuty + Slack + Email, kill switch, degradation modes |
| Compliance | 3.5/5 | ISO 27001 patterns, HIPAA-aware IaC, OWASP Top 10; no formal certification |
| Supply Chain Security | 4/5 | SBOM, license scanning, dependency review, dependabot |
| Runtime Protection | 5/5 | AppArmor, seccomp, no-new-privileges, container security contexts |
| **Overall** | **4.5/5** | Enterprise-grade with gaps in formal compliance certification |

## 3. Identity & Access Control

### 3.1 Authentication
- **Primary:** JWT (HS256) with 15-minute access token TTL
- **Refresh:** 7-day refresh token with rotation
- **Blacklist:** Token invalidation via Redis
- **MFA:** TOTP support implemented
- **OAuth2:** Provider implemented (Google, etc.)
- **SAML:** SSO support implemented
- **Passkeys:** Not yet implemented

### 3.2 Authorization
- **RBAC:** 9 roles with 13 granular permissions
- **ABAC:** Attribute-based access for tenant isolation
- **Permission Version:** Fast-path invalidation via Redis (O(1) check)
- **Service Accounts:** API key + JWT support
- **Tenant Isolation:** `lab_id` filter on all patient-data queries

### 3.3 Required Controls
- All endpoints require authentication unless explicitly whitelisted
- All patient data access requires tenant-scoped authorization
- Privilege escalation requires MFA re-verification
- Service account tokens must be rotated every 90 days
- Failed authentication attempts trigger rate limiting + alerting

## 4. Data Protection

### 4.1 Encryption Standards
| Data State | Standard | Implementation |
|-----------|----------|---------------|
| At Rest (Database) | AES-256 | Fernet (cryptography.fernet) |
| At Rest (National ID) | AES-256 | Fernet (NID_HMAC_KEY) |
| In Transit (External) | TLS 1.3 | nginx SSL termination |
| In Transit (Internal) | mTLS | Linkerd service mesh |
| Patient Cards | HMAC-SHA256 | Token verification |

### 4.2 Data Classification
| Classification | Examples | Controls |
|---------------|----------|----------|
| Public | Marketing materials, API docs | No controls |
| Internal | Code, configuration, non-PHI metrics | Access control, no public exposure |
| Confidential | Patient names, lab results, clinical notes | Encryption, tenant isolation, audit |
| Restricted | National IDs, mental health records, genetic data | Field-level encryption, strict access |
| Highly Restricted | Encryption keys, secrets, credentials | Vault, rotation, limited access |

### 4.3 Data Retention
| Data Type | Retention | Deletion |
|-----------|-----------|----------|
| Clinical Records | 10 years | Secure deletion, audit logged |
| Audit Logs | 7 years | Immutable (append-only) |
| Security Logs | 1 year | Secure deletion |
| AI Interactions | 90 days | Anonymized retention |
| Backups | 30 days daily, 12 weeks weekly, 12 months monthly | SHA-256 verification before deletion |

## 5. Network Security

### 5.1 Perimeter
- Two-layer nginx architecture (host + Docker)
- TLS 1.3 termination at host nginx
- WAF with SQL injection, XSS, path traversal, command injection blocking
- Rate limiting at 6 zones (API, auth, upload, health, public, connection)
- IP blocklist with dynamic updates

### 5.2 Internal
- All containers expose only to internal Docker network
- API gateway binds to `127.0.0.1:8080` only
- Service mesh (Linkerd) for mTLS between services
- Network policies for Kubernetes deployment

### 5.3 Detection
- Snort IDS with custom rules
- Fail2ban for brute force protection
- Intrusion detection in application layer
- SIEM integration (Wazuh + Elastic)

## 6. Application Security

### 6.1 Input Validation
- All inputs validated at API layer (Pydantic models)
- SQL injection protection (parameterized queries)
- XSS protection (output encoding)
- Payload size limits (10MB default)
- Content-Type validation

### 6.2 Security Headers (Applied to All Responses)
```
X-Frame-Options: DENY
X-XSS-Protection: 1; mode=block
X-Content-Type-Options: nosniff
Referrer-Policy: strict-origin-when-cross-origin
Permissions-Policy: camera=(), microphone=(), geolocation=(), payment=(), usb=(), bluetooth=(), serial=()
Cross-Origin-Opener-Policy: same-origin
Cross-Origin-Resource-Policy: same-site
Content-Security-Policy: default-src 'self'
Strict-Transport-Security: max-age=31536000; includeSubDomains
```

### 6.3 API Security
- Rate limiting on all endpoints
- Authentication on all non-public endpoints
- Authorization on all data-access operations
- Audit logging on all mutations
- Idempotency key support for critical operations

## 7. Secrets Management

### 7.1 Secrets Inventory
| Secret | Source | Rotation | Fallback |
|--------|--------|----------|----------|
| SECRET_KEY | Environment | 90 days | Hard fail |
| ENCRYPTION_KEY | Environment | 90 days | Hard fail |
| NID_HMAC_KEY | Environment | 90 days | Hard fail |
| REFRESH_TOKEN_SECRET | Environment | 90 days | Hard fail |
| DEVICE_HMAC_KEY | Environment | 90 days | Hard fail |
| METRICS_BEARER_TOKEN | Environment | 90 days | Hard fail |
| DATABASE_URL | Environment | On credential change | Hard fail |
| REDIS_PASSWORD | Environment | 90 days | Hard fail |

### 7.2 Rules
- No hardcoded secrets in code
- No default/fallback values in production
- Weak secret detection at startup
- Secrets rotation scripts available
- Production secrets never in version control
- Vault configured for dynamic secrets (production)

## 8. Audit & Logging

### 8.1 Audit Requirements
- All data mutations must be logged to `audit_logs` table
- Audit log must be immutable (append-only)
- Audit entries must include: `user_id`, `lab_id`, `action`, `resource_type`, `resource_id`, `timestamp`, `request_id`
- Audit hash chain for tamper detection
- Audit anchor file on Docker volume (outside database)

### 8.2 Security Event Logging
- All authentication attempts (success + failure)
- All authorization failures
- All privilege changes
- All configuration changes
- All patient data access
- All API key operations
- All secrets rotation

## 9. Vulnerability Management

### 9.1 Scanning Pipeline
| Scan Type | Frequency | Tool | Threshold |
|-----------|-----------|------|-----------|
| SAST | Every PR | Bandit + Semgrep | No HIGH/CRITICAL |
| SCA | Every PR | Safety | No known CVEs |
| Container | Every build | Hadolint + Trivy | No HIGH/CRITICAL |
| Secret | Every PR | Gitleaks | No secrets |
| DAST | Weekly | OWASP ZAP | No HIGH/CRITICAL |
| IaC | Weekly | Checkov | No HIGH/CRITICAL |
| License | Monthly | Custom | No restricted licenses |
| Penetration Test | Annually | External team | No CRITICAL findings |

### 9.2 Remediation SLAs
| Severity | Response | Fix |
|----------|----------|-----|
| CRITICAL | 1 hour | 24 hours |
| HIGH | 4 hours | 72 hours |
| MEDIUM | 24 hours | 14 days |
| LOW | 72 hours | 30 days |

## 10. Incident Response

### 10.1 Response Tiers
| Tier | Severity | Response Team | Escalation |
|------|----------|---------------|------------|
| 1 | Minor (single user impact) | On-call Engineer | Engineering Lead |
| 2 | Moderate (feature degraded) | Engineering Team | Architecture Board |
| 3 | Major (platform degraded) | Full Engineering | Executive Committee |
| 4 | Critical (data breach, outage) | Full Team + External | Executive + Legal |

### 10.2 Response Procedures

See `docs/playbooks/incident_response.md` for detailed procedures.

## 11. Compliance Roadmap

| Standard | Target Date | Status |
|----------|-------------|--------|
| OWASP Top 10 | Current | ✓ Implemented |
| OWASP ASVS Level 2 | 2026 Q4 | In progress |
| ISO 27001 | 2027 Q2 | Planned |
| HIPAA | 2027 Q2 | Planned (where applicable) |
| SOC 2 Type II | 2027 Q4 | Planned |
| FHIR R4 Security | Current | ✓ Implemented |
| NIST Cybersecurity Framework | 2027 Q2 | Planned |

## 12. Zero Trust Architecture

GULA follows the NIST SP 800-207 Zero Trust Architecture:

- **Never trust, always verify:** Every request authenticated and authorized
- **Least privilege:** Minimum access required for each role
- **Assume breach:** Network segmentation, encryption, continuous monitoring
- **Micro-segmentation:** Service mesh (Linkerd) for internal mTLS
- **Continuous verification:** Permission version checked on every request
- **Data-centric security:** Encryption at rest and in transit

---

*This Security Baseline is mandatory. All exceptions require Security Board approval.*
