# GSF Attack Surface Analysis

**Document ID**: GSF-AS-001  
**Version**: 1.0.0  
**Effective Date**: 2026-07-25  

---

## 1. Methodology

This attack surface analysis follows the NIST SP 800-115 methodology and OWASP
Attack Surface Analysis approach. Each attack vector is categorized by:

- Attack vector description
- Attack vector type (network, application, supply chain, physical)
- Likelihood (1-5)
- Impact (1-5)
- GSF module providing mitigation
- Attack surface reduction strategy

---

## 2. Network Attack Surface

### 2.1 External Network

| Attack Vector | Likelihood | Impact | Mitigation (GSF Module) | Reduction Strategy |
|---------------|------------|--------|----------------------|-------------------|
| API Gateway: unauthenticated endpoints | 4 | 4 | GSF-001, GSF-004 | Default-deny, require authentication on all endpoints |
| API Gateway: DDoS/volumetric attacks | 3 | 3 | GSF-009 | Rate limiting, CDN/WAF, autoscaling |
| API Gateway: TLS termination attacks | 2 | 4 | GSF-003, GSF-009 | TLS 1.3 minimum, HSTS, certificate pinning |
| API Gateway: HTTP request smuggling | 3 | 4 | GSF-008 | HTTP/2 preferred, proper header validation |
| DNS: DNS spoofing/cache poisoning | 2 | 3 | GSF-009 | DNSSEC, DNS over HTTPS |
| Email: Phishing targeting clinical staff | 5 | 3 | GSF-019 | SPF/DKIM/DMARC, email filtering, training |
| SMTP: Email spoofing for social engineering | 3 | 2 | GSF-019 | DMARC enforcement, BIMI |

### 2.2 Internal Network

| Attack Vector | Likelihood | Impact | Mitigation (GSF Module) | Reduction Strategy |
|---------------|------------|--------|----------------------|-------------------|
| Inter-service traffic interception | 2 | 5 | GSF-009 | mTLS mesh, service mesh (Istio/Linkerd) |
| ARP spoofing/internal MITM | 2 | 4 | GSF-009 | Network segmentation, MAC binding, DHCP snooping |
| Kubernetes API server exposure | 2 | 5 | GSF-012 | API server audit, RBAC, network policies, OIDC |
| etcd data exposure | 1 | 5 | GSF-012 | etcd encryption, network isolation, TLS |
| Database direct network access | 2 | 5 | GSF-009, GSF-010 | Network policies, database firewall, proxy only |
| Internal port scanning | 3 | 2 | GSF-009 | Network policies, IDS, minimal exposed ports |
| Lateral movement after initial compromise | 3 | 5 | GSF-009, GSF-005 | Microsegmentation, mTLS, JIT access |

### 2.3 External Integrations

| Attack Vector | Likelihood | Impact | Mitigation (GSF Module) | Reduction Strategy |
|---------------|------------|--------|----------------------|-------------------|
| Third-party API integration (Ministry systems) | 3 | 4 | GSF-004, GSF-009 | API tokens, mTLS, rate limiting, audit |
| Medical device integration (analyzers) | 3 | 5 | GSF-009, GSF-017 | Network segmentation, device auth, input validation |
| Vendor VPN access | 2 | 4 | GSF-009 | JIT VPN, MFA, session recording, time-limited |
| Health Information Exchange (HIE) | 2 | 4 | GSF-017 | IHE ATNA, audit trails, consent verification |

---

## 3. Application Attack Surface

### 3.1 Frontend (Web)

| Attack Vector | Likelihood | Impact | Mitigation (GSF Module) |
|---------------|------------|--------|------------------------|
| XSS (Cross-Site Scripting) | 3 | 4 | CSP (GSF-008), input sanitization, XSS filters |
| CSRF (Cross-Site Request Forgery) | 3 | 3 | CSRF tokens, SameSite cookies, CORS (GSF-008) |
| Clickjacking | 2 | 3 | X-Frame-Options: DENY, CSP frame-ancestors (GSF-008) |
| DOM manipulation/DOMPurify bypass | 2 | 3 | Strict CSP, trusted types (GSF-008) |
| Session fixation | 2 | 3 | Regenerate session on auth, secure cookies (GSF-004) |
| Local storage of sensitive data | 3 | 4 | No sensitive data in localStorage, httpOnly cookies (GSF-008) |
| Formjacking (Magecart-style) | 2 | 5 | CSP, SRI (GSF-008), subresource integrity |

### 3.2 Backend (API)

| Attack Vector | Likelihood | Impact | Mitigation (GSF Module) |
|---------------|------------|--------|------------------------|
| SQL injection | 3 | 5 | ORM, parameterized queries, WAF, DAST (GSF-017) |
| NoSQL injection (MongoDB/Redis) | 2 | 4 | Input validation, query sanitization |
| Mass assignment / parameter tampering | 3 | 4 | DTO validation, allow-lists (GSF-005) |
| Insecure deserialization | 2 | 5 | Schema validation, type checking, safe parsers |
| Path traversal | 2 | 4 | Input validation, chroot/jail, minimal file access |
| SSRF (Server-Side Request Forgery) | 3 | 5 | URL allowlist, network isolation, disable redirects |
| Command injection | 2 | 5 | No shell execution, subprocess with args list |
| XXE (XML External Entity) | 1 | 4 | Disable XXE, prefer JSON |
| IDOR (Insecure Direct Object Reference) | 4 | 5 | ABAC enforcement on every resource access (GSF-005) |
| Rate limiting bypass | 3 | 3 | Distributed rate limiting, Redis-based (GSF-009) |
| File upload vulnerabilities | 2 | 4 | File type validation, AV scanning, sandbox (GSF-011) |

### 3.3 FHIR API (Specific)

| Attack Vector | Likelihood | Impact | Mitigation (GSF Module) |
|---------------|------------|--------|------------------------|
| Unauthorized cross-compartment search | 3 | 5 | Compartment-based authorization (GSF-017) |
| FHIR search parameter injection | 3 | 4 | Parameter validation, query complexity limits (GSF-017) |
| _include/_revinclude abuse | 2 | 3 | Include depth limits, resource type restrictions (GSF-017) |
| Bulk data export abuse | 2 | 5 | Additional auth, audit, rate limits (GSF-017) |
| Consent directive bypass via REST | 3 | 5 | Consent evaluation on every operation, _security parameter (GSF-017) |
| Security label manipulation (meta.security) | 2 | 4 | Server-enforced labels, label validation (GSF-017) |

### 3.4 Authentication Attack Surface

| Attack Vector | Likelihood | Impact | Mitigation (GSF Module) |
|---------------|------------|--------|------------------------|
| Brute force / credential stuffing | 4 | 3 | Rate limiting, account lockout, CAPTCHA (GSF-004) |
| Password spraying | 3 | 3 | MFA, passwordless auth, anomaly detection (GSF-004, GSF-019) |
| Session hijacking (JWT theft) | 3 | 5 | Token binding, short expiry, refresh rotation (GSF-004) |
| OAuth2 authorization code interception | 2 | 4 | PKCE enforced, state validation (GSF-004) |
| SAML assertion manipulation | 2 | 4 | Signature validation, assertion encryption (GSF-004) |
| MFA fatigue / push bombing | 3 | 3 | Number matching, rate limit MFA requests (GSF-004) |
| WebAuthn credential theft | 1 | 4 | Hardware-backed credentials, origin validation (GSF-004) |

### 3.5 Authorization Attack Surface

| Attack Vector | Likelihood | Impact | Mitigation (GSF Module) |
|---------------|------------|--------|------------------------|
| RBAC privilege escalation | 2 | 5 | Role hierarchy validation, separation of duties (GSF-005) |
| ABAC attribute manipulation | 3 | 4 | Attribute signing, context validation (GSF-005) |
| Policy engine bypass (direct DB access) | 2 | 5 | Database firewall, column encryption, triggers (GSF-010) |
| Cache poisoning of authorization decisions | 1 | 4 | Short cache TTL, invalidation on policy change (GSF-005) |
| Default deny failures (fail-open) | 2 | 5 | Fail-closed by default, testing (GSF-005) |

---

## 4. Supply Chain Attack Surface

| Attack Vector | Likelihood | Impact | Mitigation (GSF Module) |
|---------------|------------|--------|------------------------|
| Compromised PyPI/npm dependency | 3 | 5 | SCA scanning, dependency pinning, SBOM (GSF-016) |
| Compromised base container image | 3 | 5 | Minimal images, image scanning, Cosign signing (GSF-011) |
| Typosquatting dependency attack | 2 | 3 | Dependency review, allowlisted registries (GSF-016) |
| Compromised CI/CD pipeline | 2 | 5 | Pipeline integrity verification, OIDC (GSF-015) |
| Malicious Terraform module | 2 | 4 | Module registry verification, policy-as-code (GSF-013) |
| Compromised GitHub Actions | 2 | 5 | Pin actions to SHA, minimal permissions (GSF-014, GSF-015) |
| Counterfeit hardware in on-prem deployment | 1 | 4 | Hardware attestation, TPM, vendor verification |
| Watering hole attack on development environments | 2 | 3 | Dev/prod separation, VPN, MFA |

---

## 5. Physical Attack Surface

| Attack Vector | Likelihood | Impact | Mitigation (GSF Module) |
|---------------|------------|--------|------------------------|
| Unauthorized data center access | 1 | 5 | Biometric + smart card, video surveillance, mantrap (on-prem) |
| Server tampering / hard drive theft | 1 | 5 | Full disk encryption, TPM, chassis intrusion detection |
| Stolen laptop/device with credentials | 3 | 4 | Full disk encryption, remote wipe, MDM |
| USB drop attack | 3 | 2 | USB blocking, endpoint protection, training |
| Shoulder surfing in clinical settings | 3 | 2 | Screen privacy filters, auto-lock, training |
| Social engineering at facility entrance | 2 | 2 | Visitor policy, escorted access, training |

---

## 6. Healthcare-Specific Attack Vectors

| Attack Vector | Likelihood | Impact | Mitigation (GSF Module) |
|---------------|------------|--------|------------------------|
| Ransomware targeting hospital operations | 3 | 5 | Offline backups, network segmentation, EDR (GSF-009, GSF-020) |
| PHI exfiltration via FHIR API | 2 | 5 | Rate limiting, anomaly detection, DLP (GSF-017, GSF-019) |
| Medical device ransomware | 2 | 5 | Analyzer network isolation, device inventory (GSF-009) |
| Lab result manipulation | 1 | 5 | Integrity monitoring, FHIR Provenance (GSF-017, GSF-020) |
| Patient identity theft for insurance fraud | 3 | 4 | Multi-factor identity proofing, audit (GSF-001) |
| Prescription fraud | 2 | 4 | E-prescribing controls, audit, anomaly detection (GSF-019) |
| Insider PII sale on dark web | 2 | 5 | DLP, UBA, audit, access reviews (GSF-006, GSF-019) |
| IoT/connected device compromise | 3 | 4 | Network segmentation, device auth (GSF-009) |
| Offline mode data integrity bypass | 3 | 4 | Local hashing, sync verification, tamper detection (GSF-020) |

---

## 7. Attack Surface Reduction Strategies

### 7.1 Network Reduction

| Strategy | Implementation | Reduction |
|----------|---------------|-----------|
| Default-deny network policies | Kubernetes NetworkPolicy deny-all default | 40% |
| mTLS for all inter-service traffic | Istio/Linkerd with mTLS strict mode | 35% |
| API Gateway as single entry point | Kong/APISIX with WAF | 25% |
| Remove public-facing non-API services | Internal-only services on cluster-internal IPs | 20% |
| Database proxy with auth | pgBouncer + mTLS + credential rotation | 15% |

### 7.2 Application Reduction

| Strategy | Implementation | Reduction |
|----------|---------------|-----------|
| Input validation on all API endpoints | Pydantic models, schema validation | 60% |
| ABAC on every resource access | OPA Rego enforcement point | 55% |
| MFA enforcement for all clinical users | WebAuthn + TOTP | 40% |
| CSP with strict policy | CSP Level 2 with nonces | 30% |
| Deprecate unused API endpoints | API versioning, endpoint inventory | 25% |

### 7.3 Supply Chain Reduction

| Strategy | Implementation | Reduction |
|----------|---------------|-----------|
| Minimal base images | distroless, scratch-based | 60% |
| SBOM verification in CI/CD | SPDX generation, policy enforcement | 50% |
| Dependency pinning and locking | pip freeze, renovate bot | 40% |
| Image signing and verification | Cosign, admission controller | 35% |
| Action pinning in CI/CD | GitHub Actions SHA pinning | 30% |

---

## 8. Attack Surface Metrics

| Metric | Current Value | Target | Measurement |
|--------|---------------|--------|-------------|
| External-facing endpoints | 12 | < 8 | Network scan |
| Open ports per service | 3 | < 2 | Port scan |
| API endpoints (total) | 850 | < 500 | Swagger/OpenAPI |
| API endpoints without auth | 0 | 0 | Automated scan |
| External dependencies | 215 | < 150 | SCA tool |
| Base image size | 180MB | < 50MB | Container scan |
| CVEs in production (critical) | 0 | 0 | Trivy scan |
| CVEs in production (high) | 3 | 0 | Trivy scan |
| Days since last pentest | 45 | < 90 | Schedule |
| Phishing susceptibility rate | 8% | < 3% | Simulation |

---

## 9. Continuous Attack Surface Management

- **Weekly**: External network scan, dependency CVE scan
- **Monthly**: Full attack surface review, penetration test (automated)
- **Quarterly**: Manual penetration test, red team exercise
- **Per Release**: Attack surface delta analysis, new feature threat modeling

---

**Document History**

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0.0 | 2026-07-25 | GULA Security Team | Initial attack surface analysis |
