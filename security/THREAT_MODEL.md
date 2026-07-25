# GSF Threat Model — STRIDE Analysis

**Document ID**: GSF-TM-001  
**Version**: 1.0.0  
**Effective Date**: 2026-07-25  
**Classification**: Confidential — GULA Security Team  

---

## 1. System Description

The GULA National Healthcare Platform connects healthcare providers, laboratories,
pharmacies, and patients across all Iraqi governorates. The system processes
Protected Health Information (PHI), laboratory results, prescriptions, and
administrative data through a multi-tenant architecture deployed on Kubernetes
with on-premises and cloud hybrid infrastructure.

### Key System Components

| Component | Technology | Security Module |
|-----------|------------|----------------|
| API Gateway | FastAPI / Kong | GSF-008, GSF-009 |
| Identity Provider | Custom / Keycloak | GSF-001, GSF-004 |
| FHIR Gateway | FastAPI / HAPI FHIR | GSF-017 |
| Authentication Service | Custom | GSF-004 |
| Authorization Service | OPA / Rego | GSF-005 |
| Audit Service | Custom / ELK | GSF-006 |
| Secrets Store | Vault / AWS SM | GSF-002 |
| Crypto Service | cryptography | GSF-003 |
| Database | PostgreSQL (Citus) | GSF-010 |
| Message Bus | Kafka | GSF-019 |
| Container Runtime | Docker / containerd | GSF-011 |
| Orchestrator | Kubernetes | GSF-012 |
| Object Store | MinIO / S3 | GSF-010 |
| Monitoring | Prometheus / Grafana | GSF-019 |
| SIEM | ELK / Wazuh | GSF-019 |

---

## 2. Threat Actors

| Actor | Description | Skill Level | Motivation | Access |
|-------|-------------|-------------|------------|--------|
| **Nation-State (APT)** | State-sponsored cyber warfare unit targeting Iraqi healthcare infrastructure | Advanced/Expert | Geopolitical destabilization, intelligence gathering | External, persistent |
| **Cybercriminal** | Organized crime targeting PHI for ransom or sale | Intermediate/Advanced | Financial gain | External |
| **Insider (Privileged)** | System administrator, DBA, or clinician with legitimate access | Intermediate | Financial gain, curiosity, coercion | Internal, authorized |
| **Insider (Standard)** | Healthcare worker with basic access | Low/Intermediate | Curiosity, error | Internal, limited |
| **External Attacker** | Opportunistic hacker scanning for vulnerabilities | Low/Intermediate | Reputation, curiosity | External |
| **Terrorist Organization** | Targeted attack on national healthcare infrastructure | Intermediate/Advanced | Disruption, terror | External |
| **Competitor** | Foreign healthcare IT provider | Intermediate | Industrial espionage | External |
| **Third-party Vendor** | Software/hardware vendor with integration access | Varies | Accidental, financial | Limited network |

---

## 3. Asset Inventory

| Asset ID | Asset | Classification | Owner | Storage Location |
|----------|-------|---------------|-------|-----------------|
| A-001 | Patient PHI (Full medical records) | Restricted | Clinical | DB (encrypted) |
| A-002 | Patient demographics (name, NIN, DOB) | Restricted | Clinical | DB (encrypted) |
| A-003 | Laboratory results | Restricted | Clinical | DB (encrypted) |
| A-004 | Prescriptions and medication history | Restricted | Clinical | DB (encrypted) |
| A-005 | Authentication credentials (password hashes) | Restricted | Security | DB (hashed/encrypted) |
| A-006 | TOTP/WebAuthn credentials | Restricted | Security | DB (encrypted) |
| A-007 | API keys and service tokens | Restricted | Engineering | Vault/Secrets Store |
| A-008 | TLS/SSL private keys | Restricted | Security | Vault/Secrets Store |
| A-009 | Database credentials | Restricted | Engineering | Vault/Secrets Store |
| A-010 | Audit logs | Confidential | Security | Log Store |
| A-011 | Access control policies (Rego) | Confidential | Security | OPA bundle server |
| A-012 | Source code | Confidential | Engineering | GitHub |
| A-013 | CI/CD pipeline configuration | Confidential | Engineering | GitHub Actions |
| A-014 | Infrastructure configuration (Terraform) | Confidential | Engineering | Terraform state |
| A-015 | Container images | Internal | Engineering | Container Registry |
| A-016 | Session tokens (JWTs) | Restricted | Security | Memory/Redis |
| A-017 | Encryption keys (DEK, KEK) | Restricted | Security | Vault/Hardware HSM |
| A-018 | Consent directives | Restricted | Clinical | DB (encrypted) |
| A-019 | Security labels | Confidential | Clinical | DB |
| A-020 | Network configuration and firewall rules | Confidential | Engineering | Infrastructure as Code |

---

## 4. Trust Boundaries

```
TB-1: Internet → WAF/API Gateway
TB-2: Public DMZ → Application Services
TB-3: Application Services → Data Layer
TB-4: Inter-service communication (mesh)
TB-5: Application Layer → Monitoring/Logging
TB-6: CI/CD Pipeline → Production
TB-7: Admin Access → Infrastructure
TB-8: Third-party Integration → API Gateway
TB-9: On-premises → Cloud (hybrid deployments)
TB-10: Client Device → Web/Mobile Application
```

---

## 5. STRIDE Analysis

### 5.1 Identity Module (GSF-001)

| Threat | Type | Risk | Mitigation | CWE |
|--------|------|------|------------|-----|
| Attacker creates fraudulent identity via NIN forgery | S | High | National ID verification via biometric, government API validation | CWE-290 |
| Tenant isolation bypass in multi-tenant identity store | S | Critical | Row-level security (RLS), tenant context enforced in all queries | CWE-282 |
| Privilege escalation via manipulated identity attributes | T | High | Signed attribute tokens, input validation, attribute immutability | CWE-287 |
| Identity enumeration via timing attack on lookups | I | Medium | Constant-time comparison, generic error messages | CWE-203 |
| Denial of service on identity resolution endpoint | D | Medium | Rate limiting, caching, resource quotas | CWE-770 |
| Elevation via identity provider misconfiguration | E | High | Automated configuration scanning, least privilege defaults | CWE-16 |

### 5.2 Secrets Module (GSF-002)

| Threat | Type | Risk | Mitigation | CWE |
|--------|------|------|------------|-----|
| Secret extraction from Vault via compromised tokens | S | Critical | Short-lived tokens, Just-In-Time access, audit logging | CWE-798 |
| Secret leak in application logs | I | High | Secret pattern detection in log pipeline, structured logging filters | CWE-532 |
| Secret rotation failure causing service outage | D | Medium | Pre-rotation validation, canary deployments, rollback | — |
| Man-in-the-middle on Vault API calls | T | High | mTLS encryption, certificate pinning | CWE-295 |
| Secrets cached in persistent storage unencrypted | I | High | Memory-only caching, encrypted swap prevention | CWE-312 |

### 5.3 Crypto Module (GSF-003)

| Threat | Type | Risk | Mitigation | CWE |
|--------|------|------|------------|-----|
| Weak key generation via insufficient entropy | S | Critical | CSPRNG enforcement (os.urandom), entropy monitoring | CWE-338 |
| Cryptographic key leak via memory dump | I | High | Secure memory (mlock/madvise), key wrapping | CWE-316 |
| Algorithm confusion attack (downgrade to weak crypto) | T | High | Algorithm whitelist, version pinning, explicit params | CWE-327 |
| Side-channel attack on encryption operations | I | Medium | Constant-time implementations, process isolation | CWE-385 |
| Nonce reuse in AEAD encryption | S | Critical | Counter-based nonce generation, atomic increment | CWE-1240 |

### 5.4 Authentication Module (GSF-004)

| Threat | Type | Risk | Mitigation | CWE |
|--------|------|------|------------|-----|
| Credential stuffing / brute force on login | S | High | Rate limiting, account lockout, CAPTCHA | CWE-307 |
| MFA bypass via TOTP token interception | T | High | TOTP over HTTPS only, short TOTP window (30s), WebAuthn as primary | CWE-304 |
| Session hijacking via JWT token theft | T | Critical | JWT binding to client fingerprint, short expiry, refresh rotation | CWE-613 |
| OAuth2 authorization code interception | T | High | PKCE enforced, state parameter validation | CWE-603 |
| SAML assertion replay | T | High | One-time use assertions, timestamp validation, NotOnOrAfter | CWE-287 |
| WebAuthn credential bypass via lack of origin validation | S | Critical | Strict origin validation, RP ID enforcement | CWE-601 |

### 5.5 Authorization Module (GSF-005)

| Threat | Type | Risk | Mitigation | CWE |
|--------|------|------|------------|-----|
| Policy engine denial due to malformed Rego input | D | High | Input validation, schema enforcement, Rego sandboxing | CWE-20 |
| Permission escalation via RBAC role confusion | E | Critical | Role hierarchy validation, separation of duties | CWE-276 |
| ABAC attribute manipulation to gain unauthorized access | T | High | Attribute signing, context validation, request verification | CWE-285 |
| Policy cache poisoning leading to stale authorizations | T | Medium | Cache TTL limits, cache invalidation on policy change | — |

### 5.6 Audit Module (GSF-006)

| Threat | Type | Risk | Mitigation | CWE |
|--------|------|------|------------|-----|
| Audit log tampering by privileged insider | T | Critical | Hash chain verification, append-only storage, WORM | CWE-779 |
| Audit log flooding to hide malicious activity | D | Medium | Rate alerting, anomaly detection on log volume | CWE-400 |
| Audit log leak exposing sensitive data | I | High | Log sanitization, access controls on log store, encryption at rest | CWE-532 |
| Missing audit events due to asynchronous log loss | S | Medium | Write-ahead log, delivery acknowledgments, circuit breaker | — |

### 5.7 FHIR Module (GSF-017)

| Threat | Type | Risk | Mitigation | CWE |
|--------|------|------|------------|-----|
| Unauthorized PHI access via FHIR search across compartments | S | Critical | Compartment-based authorization, CHC enforcement | CWE-282 |
| Consent directive bypass through REST API manipulation | T | High | Consent evaluation on every operation, default deny | CWE-285 |
| FHIR security label tampering (meta.security) | T | High | Server-enforced labels, client-submitted labels validated | CWE-345 |
| SMART-on-FHIR scope escalation | E | High | Scope validation at token issuance and introspection | CWE-282 |
| Bulk data export exposing all patient records | I | Critical | Bulk export restricted to authorized clients, audit every export | CWE-200 |

### 5.8 Infrastructure Modules (GSF-009 through GSF-016)

| Threat | Type | Risk | Mitigation | CWE |
|--------|------|------|------------|-----|
| Container escape via kernel vulnerability | S | Critical | seccomp profiles, AppArmor, read-only root FS, non-root user | CWE-1188 |
| Kubernetes RBAC misconfiguration allowing cluster compromise | E | Critical | Automated RBAC analysis, least privilege, audit review | CWE-276 |
| Unsecured etcd exposing all cluster secrets | I | Critical | etcd encryption at rest, TLS authentication, network isolation | CWE-313 |
| Supply chain attack via compromised base image | S | Critical | Image signing (Cosign), vulnerability scanning, minimal base images | CWE-1104 |
| Terraform state file exposure revealing infrastructure | I | High | Remote state with encryption, access control, state locking | CWE-200 |
| CI/CD pipeline credential theft | S | High | OIDC-based auth (no static creds), short-lived tokens | CWE-798 |

### 5.9 Privacy Module (GSF-018)

| Threat | Type | Risk | Mitigation | CWE |
|--------|------|------|------------|-----|
| Re-identification of anonymized patient data | I | High | k-anonymity (k=10), l-diversity, differential privacy | CWE-200 |
| Consent revocation not propagated to all data processors | S | High | Event-driven consent propagation, audit trail of propagation | — |
| Privacy policy bypass via direct database query | T | Critical | Column-level encryption, database firewall, query interception | CWE-285 |

### 5.10 Threat Detection (GSF-019)

| Threat | Type | Risk | Mitigation |
|--------|------|------|------------|
| Alert fatigue causing missed genuine threats | D | High | ML-based alert prioritization, correlation rules, suppression |
| Adversarial ML attack on anomaly detection model | T | Medium | Adversarial training, model monitoring, ensemble methods |
| SIEM data exfiltration via query injection | I | Medium | Parameterized queries, read-only SIEM access, audit of queries |

### 5.11 Integrity Module (GSF-020)

| Threat | Type | Risk | Mitigation |
|--------|------|------|------------|
| FIM database tampering | T | High | FIM database stored off-device with hash chain |
| Runtime integrity bypass (kernel rootkit) | S | Critical | Kernel module signing (LOCKDOWN), IMA/EVM, Secure Boot |
| Configuration drift leading to insecure state | S | Medium | GitOps model with drift detection and automated remediation |

---

## 6. STRIDE Per Component Summary

| Component | S | T | R | I | D | E | Highest |
|-----------|---|---|---|---|---|---|---------|
| API Gateway | M | H | H | H | M | H | H |
| Identity Provider | H | H | H | H | M | H | H |
| FHIR Gateway | H | H | H | C | M | H | C |
| Auth Service | M | H | H | M | M | H | H |
| AuthZ Service | M | H | M | M | H | H | H |
| Audit Service | M | C | M | H | M | M | C |
| Secrets Store | C | H | H | H | M | M | C |
| Crypto Service | M | H | H | H | M | M | H |
| Database | M | H | H | C | M | M | C |
| Message Bus | M | H | M | M | M | M | H |
| Container Runtime | C | H | H | M | M | H | C |
| Kubernetes | C | C | H | H | M | C | C |
| CI/CD Pipeline | H | H | H | H | M | H | H |

C=Critical, H=High, M=Medium, L=Low

---

## 7. Key Mitigation Strategies

| Priority | Strategy | Modules | Threat Addressed |
|----------|----------|---------|-----------------|
| P0 | Enforce mTLS for all service-to-service communication | GSF-009 | S, T (all infrastructure) |
| P0 | Column-level encryption for all PHI columns | GSF-010 | I (data at rest) |
| P0 | Short-lived credentials with automatic rotation | GSF-002, GSF-004 | S (credential theft) |
| P0 | All database queries authorized through GSF-005 | GSF-005, GSF-017 | E (unauthorized access) |
| P1 | Immutable audit with hash chain verification | GSF-006 | T (log tampering) |
| P1 | Pod Security Standards enforcement | GSF-012 | S (container escape) |
| P1 | OPA Gatekeeper for admission control | GSF-012 | E (misconfiguration) |
| P1 | Image signing and verification | GSF-011 | S (supply chain) |
| P2 | Behavioral anomaly detection | GSF-019 | All (detection) |
| P2 | File integrity monitoring | GSF-020 | T (tampering) |
| P2 | Consent directive evaluation on every FHIR operation | GSF-017 | T, E (unauthorized PHI access) |

---

## 8. CVE References

| CVE | Affected | GSF Impact | Mitigation |
|-----|----------|------------|------------|
| CVE-2024-3094 | xz/liblzma (supply chain) | Supply chain integrity | SBOM verification, dependency pinning, GSF-016 |
| CVE-2023-44487 | HTTP/2 rapid reset (DDoS) | Network availability | Rate limiting, connection management, GSF-009 |
| CVE-2023-5363 | OpenSSL RSA decryption | Crypto operations | Upgrade to cryptography >= 49.0.0, GSF-003 |
| CVE-2024-47575 | Kubernetes kubelet auth | Container escape | Pod security standards, GSF-012 |
| CVE-2024-21626 | runc container escape | Container runtime | Seccomp profiles, runtime security, GSF-011 |

---

## 9. Threat Modeling Process

- **Frequency**: Quarterly (full review), Continuous (new features)
- **Methodology**: STRIDE per component + Data Flow Diagram analysis
- **Tooling**: OWASP Threat Dragon, custom GSF threat templates
- **Owners**: GSF Security Lead + Module owners
- **Reviews**: Architecture Review Board

---

## 10. References

- OWASP Threat Modeling Manifesto
- Microsoft STRIDE Methodology
- NIST SP 800-154 (Draft) — Data-Centric Threat Modeling
- CWE Top 25 Most Dangerous Software Weaknesses
- OWASP API Top 10 2023 Attack Vectors
- CSA Cloud Control Matrix — Healthcare Specifics

---

**Document History**

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0.0 | 2026-07-25 | GULA Security Team | Initial threat model |
