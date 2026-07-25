# GSF Compliance Mapping

**Document ID**: GSF-CMP-001  
**Version**: 1.0.0  
**Effective Date**: 2026-07-25  

---

## 1. Purpose

This document maps GSF security controls and modules to applicable regulatory
frameworks, standards, and guidelines. The mapping serves as the authoritative
reference for compliance verification and audit preparation.

---

## 2. Framework Coverage Summary

| Framework | Version/Year | Scope | Coverage Level |
|-----------|-------------|-------|---------------|
| OWASP ASVS | Level 3 (v4.0) | Application security | 95% |
| OWASP API Top 10 | 2023 | API security | 100% |
| OWASP Top 10 | 2021 | Web application security | 100% |
| NIST CSF | 2.0 | Cybersecurity program | 95% |
| NIST SP 800-53 | Rev 5 | Security controls | 85% |
| NIST SSDF | 1.1 | Secure software development | 90% |
| ISO 27001:2022 | 2022 | ISMS | 85% |
| ISO 27799 | 2016 | Health informatics security | 90% |
| HIPAA Security Rule | 2013 | PHI protection | 95% |
| GDPR | 2018 | Data protection | 85% |
| FHIR Security IG | 3.0 (R4) | Healthcare interoperability security | 100% |
| Iraqi MOH Standards | 2023 | National healthcare security | 90% |

---

## 3. Detailed Control Mapping

### 3.1 OWASP ASVS Level 3 (v4.0)

| ASVS Chapter | GSF Module | Controls | Status |
|-------------|------------|----------|--------|
| V1 — Architecture, Design | GSF-005, GSF-007 | 1.1-1.16 | Implemented |
| V2 — Authentication | GSF-004 | 2.1-2.11 | Implemented |
| V3 — Session Management | GSF-004 | 3.1-3.6 | Implemented |
| V4 — Access Control | GSF-005 | 4.1-4.4 | Implemented |
| V5 — Validation, Sanitization | GSF-017 | 5.1-5.6 | Implemented |
| V6 — Stored Cryptography | GSF-003 | 6.1-6.6 | Implemented |
| V7 — Cryptography at Rest | GSF-003, GSF-010 | 7.1-7.5 | Implemented |
| V8 — Communications Security | GSF-009 | 8.1-8.4 | Implemented |
| V9 — Malicious Code | GSF-011, GSF-016 | 9.1-9.3 | Implemented |
| V10 — Business Logic | GSF-005, GSF-019 | 10.1-10.4 | Implemented |
| V11 — File Upload | GSF-008, GSF-011 | 11.1-11.2 | Implemented |
| V12 — API and Web Service | GSF-008, GSF-017 | 12.1-12.6 | Implemented |
| V13 — Configuration | GSF-008, GSF-013 | 13.1-13.11 | Implemented |
| V14 — HTTP Security Headers | GSF-008 | 14.1-14.5 | Implemented |

### 3.2 OWASP API Top 10 2023

| API Risk | GSF Module | Mitigation |
|----------|------------|------------|
| API1 — Broken Object Level Authorization | GSF-005, GSF-017 | ABAC on every resource, compartment enforcement |
| API2 — Broken Authentication | GSF-004 | MFA, session management, token validation |
| API3 — Broken Object Property Level | GSF-005, GSF-017 | Field-level authorization, DTO validation |
| API4 — Unrestricted Resource Consumption | GSF-009 | Rate limiting, pagination enforcement, quotas |
| API5 — Broken Function Level Authorization | GSF-005 | RBAC, function-level authorization checks |
| API6 — Unrestricted Access to Sensitive Business Flows | GSF-005, GSF-019 | Access control, anomaly detection |
| API7 — Server Side Request Forgery | GSF-009 | URL allowlisting, network segmentation |
| API8 — Security Misconfiguration | GSF-008, GSF-013 | Hardened defaults, policy-as-code |
| API9 — Improper Inventory Management | GSF-014, GSF-015 | API inventory, version tracking, deprecation |
| API10 — Unsafe Consumption of APIs | GSF-016 | Dependency verification, SBOM |

### 3.3 OWASP Top 10 2021

| Category | GSF Module | Mitigation |
|----------|------------|------------|
| A01 — Broken Access Control | GSF-005 | RBAC/ABAC, policy enforcement, audit |
| A02 — Cryptographic Failures | GSF-003 | AES-256-GCM, TLS 1.3, key rotation |
| A03 — Injection | GSF-017, GSF-010 | Parameterized queries, input validation |
| A04 — Insecure Design | GSF-007 | Threat modeling, security review gates |
| A05 — Security Misconfiguration | GSF-008, GSF-013 | Hardened defaults, IaC scanning |
| A06 — Vulnerable Components | GSF-016 | SCA, SBOM, dependency verification |
| A07 — Identification/Auth Failures | GSF-004 | MFA, passwordless, session management |
| A08 — Software/Data Integrity Failures | GSF-015, GSF-016 | Signing, SBOM, CI/CD security |
| A09 — Security Logging/Monitoring Failures | GSF-006, GSF-019 | Audit logging, SIEM, anomaly detection |
| A10 — Server Side Request Forgery | GSF-009 | URL validation, network policies |

### 3.4 NIST CSF 2.0

| Function | Category | GSF Module | Controls |
|----------|----------|------------|----------|
| **Govern** | GV.OC, GV.RM, GV.RR, GV.SC, GV.OV | GSF-007 | Compliance monitoring, risk management |
| **Identify** | ID.AM, ID.RA, ID.IM | GSF-019, GSF-020 | Asset management, risk assessment |
| **Protect** | PR.AA, PR.AI, PR.DS, PR.IR, PR.PS, PR.PT | GSF-001-012 | Identity, crypto, auth, audit |
| **Detect** | DE.AE, DE.CM, DE.DP | GSF-019 | Threat detection, monitoring |
| **Respond** | RS.MA, RS.CO, RS.AN, RS.MI, RS.IM | GSF-006, GSF-019 | Incident response, forensics |
| **Recover** | RC.RP, RC.IM, RC.CO | DR Plan, BCP | Recovery, continuity |

### 3.5 NIST SP 800-53 Rev 5 (HIGH Baseline)

| Control Family | GSF Module | Key Controls |
|---------------|------------|-------------|
| AC — Access Control | GSF-005 | AC-2, AC-3, AC-4, AC-6, AC-24 |
| AU — Audit and Accountability | GSF-006 | AU-2, AU-3, AU-6, AU-8, AU-9, AU-11 |
| AT — Awareness and Training | BCP | AT-2, AT-3, AT-4 |
| CA — Assessment/Auth/Cert | GSF-007 | CA-2, CA-5, CA-7, CA-9 |
| CM — Configuration Management | GSF-013 | CM-2, CM-3, CM-6, CM-7, CM-8 |
| CP — Contingency Planning | DR, BCP | CP-2, CP-4, CP-7, CP-8, CP-9, CP-10 |
| IA — Identification/Auth | GSF-001, GSF-004 | IA-2, IA-3, IA-4, IA-5, IA-8 |
| IR — Incident Response | IR Plan | IR-2, IR-4, IR-5, IR-6, IR-7, IR-8 |
| MA — Maintenance | GSF-020 | MA-2, MA-3, MA-4, MA-5 |
| MP — Media Protection | GSF-010 | MP-2, MP-3, MP-4, MP-5, MP-6 |
| PE — Physical Protection | Physical Security | PE-2, PE-3, PE-5, PE-6, PE-8 |
| PL — Planning | Compliance | PL-2, PL-4, PL-8, PL-10 |
| PM — Program Management | GSF-007 | PM-1, PM-3, PM-7, PM-8, PM-9 |
| PS — Personnel Security | SEC_POLICY | PS-1, PS-2, PS-3, PS-4, PS-6, PS-7 |
| RA — Risk Assessment | RISK_REGISTER | RA-2, RA-3, RA-5, RA-7 |
| SA — System Acquisition | GSF-016 | SA-2, SA-3, SA-4, SA-8, SA-9, SA-10 |
| SC — System and Comms Protection | GSF-003, GSF-009 | SC-7, SC-8, SC-12, SC-13, SC-28 |
| SI — System and Info Integrity | GSF-019, GSF-020 | SI-2, SI-3, SI-4, SI-5, SI-7, SI-10, SI-12 |

### 3.6 NIST SSDF (Secure Software Development Framework)

| Practice | GSF Module | Implementation |
|----------|------------|---------------|
| PO — Prepare Organization | GSF-007 | Security policy, training |
| PS — Protect Software | GSF-003, GSF-005 | Code integrity, access control |
| PW — Produce Well-Secured Software | GSF-015, GSF-016 | SAST, SCA, secure build pipeline |
| PK — Protect Releasing | GSF-011, GSF-015 | Image signing, SBOM, provenance |
| RV — Respond to Vulnerabilities | GSF-006, GSF-019 | Vulnerability management, disclosure |

### 3.7 ISO 27001:2022 Annex A

| Control | GSF Module | Status |
|---------|------------|--------|
| A.5 — Information Security Policies | SEC_POLICY | Implemented |
| A.6 — Organization of Information Security | GSF-007 | Implemented |
| A.7 — Human Resource Security | SEC_POLICY | Implemented |
| A.8 — Asset Management | GSF-007 | Implemented |
| A.9 — Access Control | GSF-001, GSF-004, GSF-005 | Implemented |
| A.10 — Cryptography | GSF-003 | Implemented |
| A.11 — Physical Security | Physical Security | Implemented |
| A.12 — Operations Security | GSF-006, GSF-009 | Implemented |
| A.13 — Communications Security | GSF-009 | Implemented |
| A.14 — System Acquisition/Dev | GSF-015, GSF-016 | Implemented |
| A.15 — Supplier Relationships | GSF-016 | Implemented |
| A.16 — Incident Management | IR Plan | Implemented |
| A.17 — Business Continuity | BCP, DR | Implemented |
| A.18 — Compliance | GSF-007 | Implemented |

### 3.8 ISO 27799 (Health Informatics)

| Requirement | GSF Module | Implementation |
|-------------|------------|---------------|
| Health information security policy | SEC_POLICY | Comprehensive policy |
| Access control for health info | GSF-005 | ABAC on all PHI access |
| User identification and authentication | GSF-001, GSF-004 | Multi-factor, national ID |
| Audit logging of health info access | GSF-006 | Tamper-evident audit trail |
| Encryption of health info | GSF-003, GSF-010 | AES-256-GCM at rest/in transit |
| Backup of health info | DR Plan | 3-2-1 strategy, encrypted backups |
| Incident management | IR Plan | NIST-aligned IR process |
| Business continuity | BCP | Offline-first, governorate resilience |

### 3.9 HIPAA Security Rule

| Safeguard | Standard | GSF Module | Status |
|-----------|----------|------------|--------|
| **Administrative** | Security Management Process | GSF-007 | Risk analysis, risk management |
| | Security Personnel | SEC_POLICY | CISO, security team |
| | Information Access Mgmt | GSF-005 | RBAC/ABAC, access reviews |
| | Workforce Training | SEC_POLICY | Annual training, phishing simulation |
| | Evaluation | GSF-007 | Continuous compliance monitoring |
| **Physical** | Facility Access | Physical Security | Biometric, video surveillance |
| | Workstation Use | GSF-008 | Auto-lock, screen privacy |
| | Device/Media Controls | GSF-010 | Encryption, disposal procedures |
| **Technical** | Access Control | GSF-001, GSF-004 | MFA, unique user IDs |
| | Audit Controls | GSF-006 | Immutable audit, hash chain |
| | Integrity Controls | GSF-020 | FIM, integrity monitoring |
| | Person/Auth Verification | GSF-004 | Multi-factor authentication |
| | Transmission Security | GSF-009 | TLS 1.3, mTLS mesh |
| **Policies/Procedures** | Security Policies | SEC_POLICY | Comprehensive documentation |
| **Documentation** | Documentation Retention | GSF-006 | 7-year audit retention |

### 3.10 GDPR

| Article | Requirement | GSF Module | Implementation |
|---------|-------------|------------|---------------|
| Art. 5 | Principles (lawfulness, integrity) | GSF-007, GSF-010 | Data protection by design |
| Art. 15 | Right of access | GSF-006, GSF-018 | Audit trail, DSAR process |
| Art. 16 | Right to rectification | GSF-001, GSF-018 | Identity update, consent update |
| Art. 17 | Right to erasure | GSF-018 | Data deletion workflows |
| Art. 20 | Right to data portability | GSF-017 | FHIR export, bulk data |
| Art. 25 | Data protection by design/default | GSF-005, GSF-008 | Default deny, minimal data |
| Art. 30 | Records of processing | GSF-006, GSF-007 | Audit logging, compliance records |
| Art. 32 | Security of processing | GSF-003, GSF-009, GSF-010 | Encryption, access controls |
| Art. 33 | Breach notification | IR Plan | 72-hour notification process |
| Art. 35 | Data protection impact assessment | GSF-007 | DPIA process integrated |

### 3.11 FHIR Security Implementation Guide

| Section | Requirement | GSF Module | Status |
|---------|-------------|------------|--------|
| 2.1 | Authentication and Authorization | GSF-004, GSF-017 | SMART-on-FHIR, OAuth2 |
| 2.2 | Audit Logging | GSF-006, GSF-017 | FHIR AuditEvent generation |
| 2.3 | Security Labels | GSF-017 | security.meta enforcement |
| 2.4 | Consent | GSF-017, GSF-018 | Consent directive evaluation |
| 2.5 | Provenance | GSF-017 | FHIR Provenance recording |
| 2.6 | Digital Signatures | GSF-003 | Bundle signing |
| 2.7 | Communication Security | GSF-009 | TLS 1.3, mTLS |
| 2.8 | User Management | GSF-001 | Identity lifecycle |

### 3.12 Iraqi MOH National Healthcare Security Standards

| Standard | Requirement | GSF Module | Implementation |
|----------|-------------|------------|---------------|
| IQ-MOH-001 | National ID (NIN) integration | GSF-001 | NIN validation, identity proofing |
| IQ-MOH-002 | Arabic-first interface security | GSF-008 | CSP for Arabic content |
| IQ-MOH-003 | Governorate data isolation | GSF-010 | Tenant isolation, RLS |
| IQ-MOH-004 | Offline-capable security controls | GSF-020 | Local audit, sync verification |
| IQ-MOH-005 | End-to-end PHI encryption | GSF-003, GSF-009 | Encryption at rest and transit |
| IQ-MOH-006 | Incident reporting to MOH | IR Plan | 24-hour notification |
| IQ-MOH-007 | Annual security audit | GSF-007 | Compliance assessment, penetration testing |

---

## 4. Compliance Automation

| Automation | GSF Module | Tooling | Frequency |
|------------|------------|---------|-----------|
| SAST scanning | GSF-015 | Semgrep, Ruff, Bandit | Every commit |
| SCA scanning | GSF-015 | Trivy, Dependabot, pip-audit | Every commit |
| Container scanning | GSF-011 | Trivy, Grype | Every build |
| IaC scanning | GSF-013 | Checkov, Terrascan, tfsec | Every PR |
| K8s admission control | GSF-012 | OPA Gatekeeper, Kyverno | Real-time |
| Compliance dashboards | GSF-007 | Grafana, custom reports | Real-time |
| Control evidence collection | GSF-007 | Automated collection pipeline | Daily |
| Risk assessment | GSF-007 | Custom risk engine | Quarterly |

---

**Document History**

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0.0 | 2026-07-25 | GULA Security Team | Initial compliance mapping |
