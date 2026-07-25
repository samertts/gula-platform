# Security Policy — GULA National Healthcare Platform

**Document ID**: GSF-POL-001  
**Version**: 1.0.0  
**Effective Date**: 2026-07-25  
**Classification**: Internal — GULA Platform Engineering  

---

## 1. Scope

This security policy applies to all components of the GULA National Healthcare
Platform, including:

- **GULA Security Framework (GSF)** — All modules GSF-001 through GSF-020
- **GULA Backend Services** — FastAPI-based microservices
- **GULA Frontend** — Web and mobile applications
- **GULA FHIR Gateway** — FHIR R4 API gateway
- **GULA Infrastructure** — Kubernetes clusters, databases, networks
- **GULA CI/CD Pipeline** — Build, test, and deployment infrastructure
- **GULA Identity Platform** — Authentication and authorization services
- **GULA Analyzer Integration** — Medical device integration layer
- **GULA Data Lake** — Analytical data storage and processing
- **Third-party Integrations** — All connected healthcare systems

This policy covers all environments: development, staging, production, and
disaster recovery.

---

## 2. Roles and Responsibilities

| Role | Responsibility |
|------|---------------|
| Chief Information Security Officer (CISO) | Overall security ownership, policy approval |
| GSF Security Lead | GSF module security, vulnerability management |
| Platform Engineering Lead | Infrastructure security, CI/CD security |
| Application Security Lead | Code security, SAST/DAST, dependency scanning |
| Compliance Officer | Regulatory compliance, audit coordination |
| Privacy Officer | Data protection, consent management |
| Incident Response Lead | Security incident handling |
| SOC Team | 24/7 monitoring and threat detection |
| All Developers | Secure coding practices, responsible disclosure |

### RACI Matrix

| Activity | CISO | GSF Lead | Eng Lead | AppSec | Compliance |
|----------|------|----------|----------|-------|------------|
| Policy definition | A/R | C | C | C | C |
| Threat modeling | I | R | C | C | I |
| Code review (security) | I | C | C | R | I |
| Vulnerability remediation | I | A | R | C | I |
| Incident response | A | C | R | C | I |
| Compliance reporting | A | C | C | I | R |
| Security training | A | R | R | C | I |

R=Responsible, A=Accountable, C=Consulted, I=Informed

---

## 3. Security Requirements

### 3.1 Cryptographic Standards

| Requirement | Standard |
|-------------|----------|
| Symmetric encryption | AES-256-GCM (minimum) |
| Asymmetric encryption | Ed25519, ECDSA P-384, RSA-3072 |
| Key exchange | X25519 |
| Hash functions | SHA-256, SHA-384, SHA-512 |
| Password hashing | Argon2id (recommended), bcrypt (minimum) |
| TLS version | TLS 1.3 (minimum), TLS 1.2 (fallback) |
| Certificate type | X.509 v3 with SHA-256 signatures |
| Random number generation | CSPRNG (os.urandom / getrandom) |

### 3.2 Authentication Requirements

- Multi-factor authentication (MFA) required for all clinical users
- MFA required for all administrative access
- Step-up authentication for PHI access
- Session timeout: 15 minutes idle (clinical), 30 minutes (administrative)
- Maximum failed login attempts: 5 before account lockout (30 minutes)
- Password policy: minimum 12 characters, complexity enforced
- Password history: 10 previous passwords remembered
- WebAuthn/passkeys preferred over passwords

### 3.3 Authorization Requirements

- Fine-grained RBAC with minimum 20 distinct roles
- ABAC for patient data access (contextual, relationship-based)
- Break-glass procedure for emergency access with immediate audit
- Principle of least privilege enforced at all levels
- Regular access reviews: monthly (privileged), quarterly (standard)

### 3.4 Audit Requirements

- All security-relevant events logged immutably
- Audit logs retained: minimum 7 years (clinical), 3 years (system)
- Audit logs tamper-evident with hash chain verification
- Real-time audit log monitoring and alerting
- Audit logs backed up off-site within 24 hours

### 3.5 Data Protection Requirements

- PHI encrypted at rest (AES-256-GCM)
- PHI encrypted in transit (TLS 1.3)
- Database column-level encryption for sensitive fields
- Dynamic data masking for non-privileged access
- Data classification: Public, Internal, Confidential, Restricted (PHI)
- Data loss prevention (DLP) for PHI egress

---

## 4. Vulnerability Management

### 4.1 Vulnerability Assessment

| Activity | Frequency | Tooling |
|----------|-----------|---------|
| SAST (Static Analysis) | Every commit | Semgrep, Ruff, Bandit |
| DAST (Dynamic Analysis) | Weekly | OWASP ZAP, Burp Suite |
| SCA (Dependency Scan) | Every commit | Trivy, Dependabot, pip-audit |
| Container scanning | Every build | Trivy, Grype |
| Infrastructure scanning | Daily | Trivy, ScoutSuite, Prowler |
| Penetration testing | Quarterly | External pentest team |
| Bug bounty | Continuous | National CERT program |
| Red team exercises | Annually | External red team |

### 4.2 Vulnerability Severity

| Severity | CVSS 4.0 | SLA to Fix |
|----------|----------|------------|
| Critical | 9.0–10.0 | 24 hours |
| High | 7.0–8.9 | 7 days |
| Medium | 4.0–6.9 | 30 days |
| Low | 0.1–3.9 | 90 days |

---

## 5. Incident Response

Refer to [INCIDENT_RESPONSE.md](INCIDENT_RESPONSE.md) for the complete
Incident Response Plan. Key requirements:

- Detection-to-triage: 15 minutes (critical), 1 hour (high)
- Containment: 1 hour (critical), 4 hours (high)
- Eradication: 24 hours (critical), 7 days (high)
- Notification to regulatory authorities: 72 hours (Iraqi law/HIPAA/GDPR)
- Post-mortem report: 5 business days after containment

---

## 6. Compliance Requirements

Refer to [COMPLIANCE.md](COMPLIANCE.md) for detailed compliance mapping.
Minimum compliance baseline:

- **OWASP ASVS Level 3** — All application security controls
- **NIST CSF 2.0** — Framework core functions (Identify, Protect, Detect,
  Respond, Recover)
- **NIST SP 800-53 Rev 5** — All HIGH baseline controls
- **ISO 27001:2022** — Annex A controls
- **ISO 27799** — Health informatics security management
- **HIPAA Security Rule** — Administrative, physical, technical safeguards
- **GDPR** — Data protection requirements for EU patients
- **FHIR Security IG** — Implementation Guide v3.0
- **Iraqi MOH Security Standards** — National healthcare security requirements

---

## 7. Physical Security

For on-premises deployments in Iraqi governorates:

- Access control: biometric + smart card for data center access
- Video surveillance: 24/7 with 90-day retention
- Environmental controls: redundant cooling, fire suppression
- Power: dual redundant UPS + generator (minimum 72 hours)
- Network: physical network segregation, Faraday cages for sensitive zones

---

## 8. Supply Chain Security

- All third-party dependencies verified against known vulnerabilities (SCA)
- Software Bill of Materials (SBOM) generated for every build
- Container images signed with Cosign and verified before deployment
- SLSA Level 3 build compliance for critical services
- Vendor security assessment for all integration partners

---

## 9. Training and Awareness

| Training | Audience | Frequency |
|----------|----------|-----------|
| Security awareness | All staff | Annually |
| Secure coding | Developers | Quarterly |
| Incident response | Operations | Semi-annually |
| Compliance training | All staff | Annually |
| Phishing simulation | All staff | Monthly |
| Healthcare privacy | Clinical teams | Annually |

---

## 10. Policy Review and Enforcement

- This policy is reviewed quarterly by the CISO and Security Lead
- Exceptions require documented risk acceptance signed by CISO
- Violations are subject to disciplinary action up to termination
- Automated policy enforcement via GSF modules where possible

---

## 11. References

| Reference | Source |
|-----------|--------|
| [NIST SP 800-61 Rev 2](https://csrc.nist.gov/publications/detail/sp/800-61/rev-2/final) | Computer Security Incident Handling Guide |
| [NIST SP 800-53 Rev 5](https://csrc.nist.gov/publications/detail/sp/800-53/rev-5/final) | Security and Privacy Controls |
| [OWASP ASVS v4.0](https://owasp.org/www-project-application-security-verification-standard/) | Application Security Verification Standard |
| [FHIR Security IG](https://hl7.org/fhir/security.html) | FHIR Security Implementation Guide |
| [ISO 27799](https://www.iso.org/standard/74281.html) | Health informatics security management |
| Iraq MOH Circular 47/2023 | National healthcare cybersecurity requirements |

---

**Document History**

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0.0 | 2026-07-25 | GULA Security Team | Initial policy |
