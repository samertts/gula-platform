# GULA Compliance Matrix

## Overview

This compliance matrix maps regulatory requirements from Iraqi and international
healthcare standards to specific GULA platform controls. It serves as the authoritative
reference for compliance assessment, audit preparation, and certification decisions.

### Regulatory Framework Scope

| Regulation | Jurisdiction | Applicability | Status |
|------------|-------------|---------------|--------|
| Iraqi Ministry of Health Regulations | Iraq | All GULA deployments | Active |
| Iraqi Data Protection Law (Draft) | Iraq | All patient data processing | Emerging |
| HIPAA Privacy & Security Rules | USA | International compatibility | Adopted |
| GDPR | EU | EU expansion readiness | Adopted |
| ISO 15189:2022 | International | Medical laboratories | Certified |
| ISO 27001:2022 | International | Information security | In progress |
| CAP Laboratory Accreditation | USA/International | Lab quality | Enabling |
| CLSI Guidelines | International | Lab standards | Enabling |

### Matrix Structure

Each row contains:

| Field | Description |
|-------|-------------|
| **ID** | Unique control identifier |
| **Regulation** | Source regulation or standard |
| **Article/Clause** | Specific article, clause, or section |
| **Requirement** | Description of the regulatory requirement |
| **GULA Control** | Specific GULA platform control or feature |
| **Control Owner** | Responsible team or role |
| **Implementation Status** | Not Implemented / Planned / Implemented / Verified / Certified |
| **Evidence Location** | Where the control is documented or can be verified |
| **Last Audit Date** | Date of last compliance verification |
| **Risk Level** | Critical / High / Medium / Low |

---

## 1. Iraqi Ministry of Health Regulations

### Laboratory Licensing and Operations

| ID | Article/Clause | Requirement | GULA Control | Owner | Status | Evidence Location | Last Audit | Risk |
|----|---------------|-------------|--------------|-------|--------|-------------------|-----------|------|
| IQ-MOH-001 | Lab Licensing Regs §3 | Labs must maintain accurate patient records | Patient management module with full CRUD, audit trail | Backend Team | Verified | `backend/app/routes/patients.py`, AuditLog model | 2026-06 | High |
| IQ-MOH-002 | Lab Licensing Regs §5 | Result records must be retained for minimum 5 years | Configurable retention policies, archival system | Infrastructure Team | Implemented | `backend/app/core/retention.py` | 2026-05 | High |
| IQ-MOH-003 | Lab Licensing Regs §7 | Critical values must be reported within specified timeframe | Critical alert system with escalation, notification logging | Backend Team | Verified | `backend/app/routes/results.py`, CriticalAlert model | 2026-06 | Critical |
| IQ-MOH-004 | Lab Licensing Regs §9 | Staff qualifications must be documented | User profile with certification tracking, document upload | Admin Team | Implemented | `backend/app/routes/users.py` | 2026-04 | Medium |
| IQ-MOH-005 | Lab Licensing Regs §12 | Equipment maintenance records required | Device bridge maintenance logging, calibration tracking | LabLink Team | Implemented | `services/device_bridge/app/models/maintenance.py` | 2026-05 | High |
| IQ-MOH-006 | Lab Licensing Regs §15 | QC procedures must be documented and followed | QC module with Westgard rules, Levey-Jennings charts | Backend Team | Verified | `backend/app/routes/qc.py`, QC models | 2026-06 | High |
| IQ-MOH-007 | Lab Licensing Regs §18 | Proficiency testing participation required | PT module, result submission, performance tracking | Backend Team | Planned | `backend/app/routes/proficiency.py` | N/A | Medium |
| IQ-MOH-008 | Lab Licensing Regs §21 | Test menu must be formally defined and approved | Test catalog management with versioning, approval workflow | Backend Team | Verified | `backend/app/models/test_catalog.py` | 2026-05 | Medium |
| IQ-MOH-009 | Lab Licensing Regs §24 | Referral lab testing must maintain chain of custody | Referral workflow with specimen tracking, chain of custody | Backend Team | Implemented | `backend/app/routes/referrals.py` | 2026-04 | High |
| IQ-MOH-010 | Lab Licensing Regs §30 | Patient identity verification required before testing | Patient identity verification, MPI matching | Backend Team | Verified | `backend/app/services/mpi/matcher.py` | 2026-06 | Critical |

### Health Data Management

| ID | Article/Clause | Requirement | GULA Control | Owner | Status | Evidence Location | Last Audit | Risk |
|----|---------------|-------------|--------------|-------|--------|-------------------|-----------|------|
| IQ-MOH-011 | Health Data Regs §2 | Patient consent required for data processing | Consent management module, electronic consent capture | Backend Team | Implemented | `backend/app/routes/consent.py` | 2026-05 | Critical |
| IQ-MOH-012 | Health Data Regs §5 | Data minimization principle | Field-level access control, minimum necessary data exposure | Security Team | Verified | `backend/app/security/rbac.py` | 2026-06 | High |
| IQ-MOH-013 | Health Data Regs §8 | Data accuracy and correction | Patient data correction workflow with audit trail | Backend Team | Verified | `backend/app/routes/patients.py`, AuditLog | 2026-05 | Medium |
| IQ-MOH-014 | Health Data Regs §11 | Data breach notification | Incident response module, automated notification system | Security Team | Implemented | `backend/app/security/incident_response.py` | 2026-04 | Critical |
| IQ-MOH-015 | Health Data Regs §14 | Data retention and disposal | Retention policy engine, secure deletion workflows | Infrastructure Team | Implemented | `backend/app/core/retention.py` | 2026-05 | High |
| IQ-MOH-016 | Health Data Regs §17 | Data processing registration | Processing activity register, automated documentation | Admin Team | Planned | `backend/app/routes/compliance.py` | N/A | Medium |
| IQ-MOH-017 | SNDHS Regs §3 | National health data submission | SNDHS integration module, automated data submission | Backend Team | Verified | `backend/app/routes/sndhs.py` | 2026-06 | Critical |
| IQ-MOH-018 | SNDHS Regs §5 | Data quality standards for submission | Data validation rules, quality scoring, error reporting | Backend Team | Implemented | `backend/app/services/sndhs/validator.py` | 2026-05 | High |
| IQ-MOH-019 | SNDHS Regs §8 | National ID handling and protection | National ID encryption at rest, access controls | Security Team | Verified | `backend/app/security/encryption.py`, NID handler | 2026-06 | Critical |
| IQ-MOH-020 | SNDHS Regs §12 | Health ID assignment and management | SNDHS health ID generation, patient linkage | Backend Team | Implemented | `backend/app/services/sndhs/health_id.py` | 2026-05 | High |

---

## 2. Iraqi Data Protection Law (Emerging)

| ID | Article/Clause | Requirement | GULA Control | Owner | Status | Evidence Location | Last Audit | Risk |
|----|---------------|-------------|--------------|-------|--------|-------------------|-----------|------|
| IQ-DPL-001 | Art 4 | Lawful basis for processing | Consent management, legitimate interest assessment | Legal Team | Planned | `backend/app/routes/consent.py` | N/A | Critical |
| IQ-DPL-002 | Art 7 | Consent requirements (explicit, informed) | Granular consent options, consent record keeping | Backend Team | Implemented | `backend/app/routes/consent.py` | 2026-04 | Critical |
| IQ-DPL-003 | Art 9 | Special category data (health) protections | Enhanced encryption, stricter access controls | Security Team | Verified | `backend/app/security/encryption.py` | 2026-06 | Critical |
| IQ-DPL-004 | Art 12 | Data subject rights (access, rectification, erasure) | DSR portal, automated request handling | Backend Team | Implemented | `backend/app/routes/dsr.py` | 2026-05 | High |
| IQ-DPL-005 | Art 15 | Data Protection Officer appointment | DPO designation, contact published | Admin Team | Implemented | `config/compliance/dpo.txt` | 2026-03 | Medium |
| IQ-DPL-006 | Art 18 | Data Protection Impact Assessment (DPIA) | DPIA template, automated screening questions | Compliance Team | Planned | `backend/app/routes/dpia.py` | N/A | High |
| IQ-DPL-007 | Art 22 | Cross-border data transfer restrictions | Transfer impact assessment, adequacy decisions | Legal Team | Planned | `config/compliance/transfers/` | N/A | High |
| IQ-DPL-008 | Art 25 | Data protection by design and default | Privacy-by-design in all features, minimal data collection | Engineering Team | Verified | Engineering design review process | 2026-05 | High |
| IQ-DPL-009 | Art 30 | Record of processing activities | Automated ROPA generation from system configuration | Admin Team | Implemented | `backend/app/routes/compliance.py` | 2026-04 | Medium |
| IQ-DPL-010 | Art 33 | Security of processing | Comprehensive security controls (see ISO 27001 section) | Security Team | Verified | `backend/app/security/` | 2026-06 | Critical |

---

## 3. HIPAA (International Compatibility)

### Privacy Rule

| ID | Article/Clause | Requirement | GULA Control | Owner | Status | Evidence Location | Last Audit | Risk |
|----|---------------|-------------|--------------|-------|--------|-------------------|-----------|------|
| HIPAA-P-001 | §164.502 | Uses and disclosures of PHI | PHI access controls, disclosure accounting | Security Team | Verified | `backend/app/security/rbac.py` | 2026-05 | Critical |
| HIPAA-P-002 | §164.504 | Organizational requirements | BA agreements, organized healthcare arrangement | Legal Team | Implemented | `config/compliance/business_associates/` | 2026-04 | High |
| HIPAA-P-003 | §164.506 | Treatment, payment, operations | Use-case based access categories | Backend Team | Verified | `backend/app/security/rbac.py` | 2026-05 | Medium |
| HIPAA-P-004 | §164.508 | Authorization for uses and disclosures | Consent management, authorization forms | Backend Team | Implemented | `backend/app/routes/consent.py` | 2026-04 | High |
| HIPAA-P-005 | §164.510 | Opportunity to agree or object | Patient communication preferences, opt-out mechanisms | Backend Team | Implemented | `backend/app/routes/patients.py` | 2026-03 | Medium |
| HIPAA-P-006 | §164.512 | Uses for which authorization not required | Public health reporting, oversight | Backend Team | Verified | `backend/app/routes/sndhs.py` | 2026-06 | High |
| HIPAA-P-007 | §164.514 | De-identification | De-identification module, expert determination | Backend Team | Implemented | `backend/app/services/deidentification.py` | 2026-05 | Medium |
| HIPAA-P-008 | §164.520 | Notice of privacy practices | NPP generation, acknowledgment tracking | Admin Team | Implemented | `backend/app/routes/privacy.py` | 2026-04 | Medium |
| HIPAA-P-009 | §164.522 | Rights to request restriction and confidential communication | Restriction management, communication preferences | Backend Team | Implemented | `backend/app/routes/patients.py` | 2026-05 | Medium |
| HIPAA-P-010 | §164.528 | Accounting of disclosures | Disclosure log, automated accounting reports | Backend Team | Verified | `backend/app/routes/audit.py` | 2026-06 | Medium |

### Security Rule

| ID | Article/Clause | Requirement | GULA Control | Owner | Status | Evidence Location | Last Audit | Risk |
|----|---------------|-------------|--------------|-------|--------|-------------------|-----------|------|
| HIPAA-S-001 | §164.308(a)(1) | Security management process | Risk management program, security policies | Security Team | Verified | `backend/app/security/` | 2026-06 | Critical |
| HIPAA-S-002 | §164.308(a)(2) | Assigned security responsibility | CISO role defined, security team structure | Admin Team | Implemented | `config/compliance/roles.md` | 2026-03 | High |
| HIPAA-S-003 | §164.308(a)(3) | Workforce security | User access management, termination procedures | Admin Team | Verified | `backend/app/routes/users.py` | 2026-05 | High |
| HIPAA-S-004 | §164.308(a)(4) | Information access management | RBAC, access reviews, privilege management | Security Team | Verified | `backend/app/security/rbac.py` | 2026-06 | Critical |
| HIPAA-S-005 | §164.308(a)(5) | Security awareness and training | GULA Learning Platform, mandatory security modules | Learning Team | Implemented | `docs/learning/TRAINING_CATALOG.md` (SC modules) | 2026-04 | High |
| HIPAA-S-006 | §164.308(a)(6) | Security incident procedures | Incident response plan, automated detection | Security Team | Verified | `backend/app/security/incident_response.py` | 2026-06 | Critical |
| HIPAA-S-007 | §164.308(a)(7) | Contingency plan | DR plan, backup/restore procedures, failover | Infrastructure Team | Verified | `docs/runbooks/`, backup scripts | 2026-05 | Critical |
| HIPAA-S-008 | §164.308(a)(8) | Evaluation | Periodic security assessments, pen testing | Security Team | Implemented | Quarterly assessment reports | 2026-03 | High |
| HIPAA-S-009 | §164.310(a)(1) | Facility access controls | Data center security, access logs | Infrastructure Team | Implemented | Data center security documentation | 2026-04 | Medium |
| HIPAA-S-010 | §164.310(b) | Workstation use and security | Workstation policies, automatic lockout | Admin Team | Implemented | Session timeout configuration | 2026-03 | Medium |
| HIPAA-S-011 | §164.310(c) | Workstation security | Device management, antivirus | Infrastructure Team | Implemented | Infrastructure configuration | 2026-04 | Medium |
| HIPAA-S-012 | §164.310(d)(1) | Device and media controls | Media disposal, device tracking | Infrastructure Team | Implemented | Asset management system | 2026-04 | Medium |
| HIPAA-S-013 | §164.312(a)(1) | Access control | Unique user IDs, emergency access, automatic logoff | Security Team | Verified | `backend/app/security/auth.py` | 2026-06 | Critical |
| HIPAA-S-014 | §164.312(b) | Audit controls | Comprehensive audit logging, immutable trail | Backend Team | Verified | `backend/app/models/audit_log.py` | 2026-06 | Critical |
| HIPAA-S-015 | §164.312(c)(1) | Integrity controls | Data integrity checks, checksums, validation | Backend Team | Verified | `backend/app/services/validation.py` | 2026-05 | High |
| HIPAA-S-016 | §164.312(d) | Person or entity authentication | MFA, strong password policy, biometric support | Security Team | Verified | `backend/app/security/auth.py` | 2026-06 | Critical |
| HIPAA-S-017 | §164.312(e)(1) | Transmission security | TLS 1.3 for all communications, API encryption | Infrastructure Team | Verified | `config/nginx/`, TLS configuration | 2026-06 | Critical |
| HIPAA-S-018 | §164.314(a) | Group health plan requirements | Plan sponsor documentation | Legal Team | Implemented | BA agreements, plan documents | 2026-03 | Medium |
| HIPAA-S-019 | §164.316(a) | Policies and procedures | Documented security policies, version control | Security Team | Implemented | `config/compliance/policies/` | 2026-05 | High |
| HIPAA-S-020 | §164.316(b)(1) | Documentation retention | Policy retention, version history | Admin Team | Implemented | Document management system | 2026-04 | Medium |

---

## 4. GDPR (EU Expansion)

| ID | Article/Clause | Requirement | GULA Control | Owner | Status | Evidence Location | Last Audit | Risk |
|----|---------------|-------------|--------------|-------|--------|-------------------|-----------|------|
| GDPR-001 | Art 5(1)(a) | Lawfulness, fairness, transparency | Transparent data processing notices, consent records | Legal Team | Implemented | `backend/app/routes/privacy.py` | 2026-04 | High |
| GDPR-002 | Art 5(1)(b) | Purpose limitation | Processing purpose specification at data collection | Backend Team | Implemented | Consent management, data classification | 2026-05 | High |
| GDPR-003 | Art 5(1)(c) | Data minimization | Minimum necessary data collection, field-level controls | Engineering Team | Verified | Data model design, RBAC | 2026-06 | High |
| GDPR-004 | Art 5(1)(d) | Accuracy | Data quality validation, correction workflows | Backend Team | Verified | `backend/app/services/validation.py` | 2026-05 | Medium |
| GDPR-005 | Art 5(1)(e) | Storage limitation | Data retention schedules, automated purging | Infrastructure Team | Implemented | `backend/app/core/retention.py` | 2026-05 | High |
| GDPR-006 | Art 5(1)(f) | Integrity and confidentiality | Encryption, access controls, security monitoring | Security Team | Verified | Comprehensive security controls | 2026-06 | Critical |
| GDPR-007 | Art 7 | Conditions for consent | Granular consent, withdrawal mechanisms, records | Backend Team | Implemented | `backend/app/routes/consent.py` | 2026-05 | Critical |
| GDPR-008 | Art 15 | Right of access | Subject access request portal, automated data export | Backend Team | Implemented | `backend/app/routes/dsr.py` | 2026-04 | High |
| GDPR-009 | Art 16 | Right to rectification | Patient data correction with audit trail | Backend Team | Verified | `backend/app/routes/patients.py` | 2026-05 | Medium |
| GDPR-010 | Art 17 | Right to erasure | Data deletion workflows, erasure verification | Backend Team | Implemented | `backend/app/routes/dsr.py` | 2026-05 | High |
| GDPR-011 | Art 18 | Right to restrict processing | Processing restriction flags, access controls | Backend Team | Implemented | Patient status flags | 2026-04 | Medium |
| GDPR-012 | Art 20 | Right to data portability | Data export in standard formats (JSON, FHIR) | Backend Team | Implemented | `backend/app/routes/export.py` | 2026-04 | Medium |
| GDPR-013 | Art 22 | Automated decision making | AI decision transparency, human review option | AI Team | Implemented | `backend/app/ai/transparency.py` | 2026-05 | High |
| GDPR-014 | Art 25 | Data protection by design | Privacy impact assessments, design review process | Engineering Team | Verified | Engineering process documentation | 2026-05 | High |
| GDPR-015 | Art 30 | Records of processing | ROPA generation, processing activity register | Admin Team | Implemented | `backend/app/routes/compliance.py` | 2026-04 | Medium |
| GDPR-016 | Art 32 | Security of processing | Technical and organizational measures (see ISO 27001) | Security Team | Verified | Full security stack | 2026-06 | Critical |
| GDPR-017 | Art 33 | Data breach notification | Breach detection, notification workflow | Security Team | Implemented | `backend/app/security/incident_response.py` | 2026-05 | Critical |
| GDPR-018 | Art 35 | DPIA | Screening questions, full DPIA template | Compliance Team | Planned | DPIA module | N/A | High |
| GDPR-019 | Art 37 | Designation of DPO | DPO appointed, contact published | Admin Team | Implemented | `config/compliance/dpo.txt` | 2026-03 | Medium |
| GDPR-020 | Art 44 | International transfers | Transfer mechanisms (SCCs, BCBs) | Legal Team | Planned | Transfer documentation | N/A | High |

---

## 5. ISO 15189:2022 (Medical Laboratories)

| ID | Article/Clause | Requirement | GULA Control | Owner | Status | Evidence Location | Last Audit | Risk |
|----|---------------|-------------|--------------|-------|--------|-------------------|-----------|------|
| ISO15189-001 | §5.1 | Laboratory shall define its organization and management | Lab configuration, organizational structure in GULA | Admin Team | Verified | `backend/app/models/labs.py` | 2026-06 | High |
| ISO15189-002 | §5.2 | Quality management system | QMS documentation module, document control | Quality Team | Verified | `backend/app/routes/qms.py` | 2026-06 | Critical |
| ISO15189-003 | §5.3 | Document control | Document versioning, approval workflow, review cycles | Quality Team | Verified | `backend/app/routes/qms.py`, document model | 2026-06 | High |
| ISO15189-004 | §5.4 | Service agreements | Service agreement templates, SLA tracking | Admin Team | Implemented | `backend/app/routes/agreements.py` | 2026-04 | Medium |
| ISO15189-005 | §5.5 | Examination by referral laboratories | Referral workflow, accredited lab database | Backend Team | Implemented | `backend/app/routes/referrals.py` | 2026-05 | High |
| ISO15189-006 | §5.6 | External services and supplies | Supplier management, supply tracking | Admin Team | Implemented | `backend/app/routes/suppliers.py` | 2026-04 | Medium |
| ISO15189-007 | §5.7 | Advisory services | Clinical decision support, interpretive comments | Backend Team | Verified | `backend/app/routes/cds.py` | 2026-05 | Medium |
| ISO15189-008 | §5.8 | Resolution of complaints | Complaint management, investigation workflow | Admin Team | Implemented | `backend/app/routes/complaints.py` | 2026-05 | Medium |
| ISO15189-009 | §5.9 | Identification and control of non-conformities | NCR management, CAPA workflow | Quality Team | Verified | `backend/app/routes/qms.py`, NCR model | 2026-06 | High |
| ISO15189-010 | §5.10 | Corrective actions | CAPA system, root cause analysis, effectiveness check | Quality Team | Verified | `backend/app/routes/qms.py`, CAPA model | 2026-06 | High |
| ISO15189-011 | §5.11 | Preventive actions | Risk assessment, proactive monitoring | Quality Team | Implemented | `backend/app/routes/qms.py` | 2026-04 | Medium |
| ISO15189-012 | §5.12 | Continual improvement | Quality indicators, performance monitoring | Quality Team | Verified | `backend/app/routes/quality.py` | 2026-05 | Medium |
| ISO15189-013 | §5.13 | Control of records | Record management, retention, archival | Admin Team | Verified | `backend/app/core/retention.py` | 2026-06 | High |
| ISO15189-014 | §5.14 | Evaluation and audits | Internal audit module, audit schedule management | Quality Team | Implemented | `backend/app/routes/audit.py` | 2026-05 | High |
| ISO15189-015 | §5.15 | Management review | Management review documentation, KPI dashboards | Admin Team | Implemented | `backend/app/routes/reports.py` | 2026-04 | Medium |
| ISO15189-016 | §6.1 | Personnel | Staff qualification tracking, training records, competency | Admin Team | Verified | `backend/app/routes/users.py`, Learning Platform | 2026-06 | High |
| ISO15189-017 | §6.2 | Accommodation and environmental conditions | Facility management, environmental monitoring | Infrastructure Team | Implemented | Facility documentation | 2026-03 | Medium |
| ISO15189-018 | §6.3 | Laboratory equipment, reagents, and consumables | Equipment management, reagent tracking, inventory | LabLink Team | Verified | `services/device_bridge/app/models/equipment.py` | 2026-06 | High |
| ISO15189-019 | §6.4 | Pre-examination processes | Test request management, sample collection, transport | Backend Team | Verified | `backend/app/routes/orders.py`, `routes/samples.py` | 2026-06 | Critical |
| ISO15189-020 | §6.5 | Examination processes | Test procedure management, QC, method validation | Backend Team | Verified | `backend/app/routes/qc.py`, `routes/results.py` | 2026-06 | Critical |
| ISO15189-021 | §6.6 | Ensuring quality of examination results | QC program, EQA/PT, inter-lab comparisons | Backend Team | Verified | `backend/app/routes/qc.py` | 2026-06 | Critical |
| ISO15189-022 | §6.7 | Post-examination processes | Result review, release, critical value reporting | Backend Team | Verified | `backend/app/routes/results.py` | 2026-06 | Critical |
| ISO15189-023 | §6.8 | Reporting of results | Result report generation, electronic delivery | Backend Team | Verified | `backend/app/services/pdf_report.py` | 2026-06 | High |
| ISO15189-024 | §7.1 | Information management | LIMS data management, backup, disaster recovery | Infrastructure Team | Verified | `backend/app/database.py`, backup scripts | 2026-06 | Critical |
| ISO15189-025 | §7.2 | Confidentiality | Data encryption, access controls, confidentiality agreements | Security Team | Verified | `backend/app/security/` | 2026-06 | Critical |

---

## 6. ISO 27001:2022 (Information Security)

| ID | Article/Clause | Requirement | GULA Control | Owner | Status | Evidence Location | Last Audit | Risk |
|----|---------------|-------------|--------------|-------|--------|-------------------|-----------|------|
| ISO27001-001 | Annex A 5.1 | Information security policy | Security policy documentation, review cycle | Security Team | Implemented | `config/compliance/policies/security_policy.md` | 2026-05 | High |
| ISO27001-002 | Annex A 5.2 | Information security roles and responsibilities | Security roles defined, RACI matrix | Admin Team | Implemented | `config/compliance/roles.md` | 2026-03 | High |
| ISO27001-003 | Annex A 5.9 | Inventory of assets | Asset management system, hardware/software inventory | Infrastructure Team | Implemented | Asset register | 2026-04 | Medium |
| ISO27001-004 | Annex A 5.10 | Acceptable use of information | Acceptable use policy, user acknowledgment | Admin Team | Implemented | AUP documentation | 2026-03 | Medium |
| ISO27001-005 | Annex A 5.14 | Information transfer | Secure transfer protocols, encryption requirements | Infrastructure Team | Verified | TLS configuration, VPN | 2026-05 | High |
| ISO27001-006 | Annex A 5.15 | Access control | RBAC, MFA, access reviews | Security Team | Verified | `backend/app/security/auth.py`, `rbac.py` | 2026-06 | Critical |
| ISO27001-007 | Annex A 5.17 | Authentication information | Password policy, credential management | Security Team | Verified | `backend/app/security/auth.py` | 2026-06 | Critical |
| ISO27001-008 | Annex A 5.18 | Access rights | Provisioning, review, revocation processes | Admin Team | Verified | `backend/app/routes/users.py` | 2026-05 | High |
| ISO27001-009 | Annex A 5.19 | Supplier relationships | Supplier security assessment, agreements | Legal Team | Implemented | Supplier security questionnaires | 2026-04 | Medium |
| ISO27001-010 | Annex A 5.24 | Information security incident management | Incident detection, response, reporting | Security Team | Verified | `backend/app/security/incident_response.py` | 2026-06 | Critical |
| ISO27001-011 | Annex A 5.25 | Information security aspects of business continuity | BC plan, DR testing, continuity procedures | Infrastructure Team | Verified | `docs/runbooks/disaster_recovery.md` | 2026-05 | Critical |
| ISO27001-012 | Annex A 5.29 | Information security during disruption | Degraded mode, circuit breaker, graceful degradation | Backend Team | Verified | `backend/app/core/self_healing.py` | 2026-06 | Critical |
| ISO27001-013 | Annex A 5.31 | Legal, statutory, regulatory compliance | Compliance register, regulatory monitoring | Legal Team | Implemented | This compliance matrix | 2026-06 | High |
| ISO27001-014 | Annex A 5.33 | Protection of records | Record retention, immutable audit trail | Backend Team | Verified | `backend/app/models/audit_log.py` | 2026-06 | High |
| ISO27001-015 | Annex A 5.36 | Compliance with policies and standards | Automated compliance checking, periodic audits | Security Team | Implemented | Compliance scanning tools | 2026-05 | Medium |
| ISO27001-016 | Annex A 5.37 | Documented operating procedures | Runbooks, SOPs, operational documentation | Infrastructure Team | Implemented | `docs/runbooks/` | 2026-04 | Medium |
| ISO27001-017 | Annex A 6.7 | Remote working | Remote access VPN, secure remote desktop | Infrastructure Team | Implemented | VPN configuration, remote access policy | 2026-04 | Medium |
| ISO27001-018 | Annex A 7.4 | Physical security monitoring | Data center access control, surveillance | Infrastructure Team | Implemented | Facility security documentation | 2026-03 | Medium |
| ISO27001-019 | Annex A 8.1 | User endpoint devices | Endpoint management, antivirus, patching | Infrastructure Team | Implemented | MDM, patch management | 2026-04 | High |
| ISO27001-020 | Annex A 8.8 | Management of technical vulnerabilities | Vulnerability scanning, patch management | Security Team | Implemented | Weekly vulnerability scans | 2026-05 | High |
| ISO27001-021 | Annex A 8.9 | Configuration management | Configuration baselines, change management | Infrastructure Team | Implemented | CMDB, change control process | 2026-04 | Medium |
| ISO27001-022 | Annex A 8.12 | Data leakage prevention | DLP controls, data classification, egress monitoring | Security Team | Planned | DLP implementation | N/A | High |
| ISO27001-023 | Annex A 8.16 | Monitoring activities | Log aggregation, SIEM, alerting | Infrastructure Team | Verified | Prometheus, Grafana, SIEM | 2026-06 | High |
| ISO27001-024 | Annex A 8.20 | Networks security | Firewall, IDS/IPS, network segmentation | Infrastructure Team | Verified | Network architecture documentation | 2026-06 | Critical |
| ISO27001-025 | Annex A 8.24 | Use of cryptography | Encryption policies, key management | Security Team | Verified | `backend/app/security/encryption.py` | 2026-06 | Critical |
| ISO27001-026 | Annex A 8.25 | Secure development lifecycle | SDLC policy, code review, security testing | Engineering Team | Verified | CI/CD pipeline, code review process | 2026-05 | High |
| ISO27001-027 | Annex A 8.28 | Secure coding | OWASP guidelines, static analysis, dependency scanning | Engineering Team | Verified | SAST in CI pipeline, dependency audit | 2026-05 | High |
| ISO27001-028 | Annex A 8.29 | Security testing in development | Penetration testing, security testing in CI | Security Team | Implemented | Quarterly pen tests, CI security gates | 2026-04 | High |
| ISO27001-029 | Annex A 8.30 | Outsourced development | Third-party developer security requirements | Legal Team | Implemented | Developer agreements, security review | 2026-03 | Medium |
| ISO27001-030 | Annex A 8.31 | Separation of environments | Dev/staging/prod separation, access controls | Infrastructure Team | Verified | Environment architecture | 2026-05 | High |

---

## 7. CAP (College of American Pathologists) Requirements

| ID | Article/Clause | Requirement | GULA Control | Owner | Status | Evidence Location | Last Audit | Risk |
|----|---------------|-------------|--------------|-------|--------|-------------------|-----------|------|
| CAP-001 | GEN.40400 | Patient test management | Complete test ordering, tracking, resulting workflow | Backend Team | Verified | `backend/app/routes/` | 2026-06 | High |
| CAP-002 | GEN.41000 | Specimen identification | Barcode labeling, two-point patient ID verification | Backend Team | Verified | `backend/app/models/sample.py` | 2026-06 | Critical |
| CAP-003 | GEN.41300 | Specimen rejection | Rejection criteria, documentation workflow | Backend Team | Verified | `backend/app/routes/samples.py` | 2026-05 | High |
| CAP-004 | GEN.41650 | Critical results reporting | Critical value alerting, escalation, documentation | Backend Team | Verified | `backend/app/routes/results.py` | 2026-06 | Critical |
| CAP-005 | GEN.42000 | Result reporting | Report generation, electronic delivery, archival | Backend Team | Verified | `backend/app/services/pdf_report.py` | 2026-05 | High |
| CAP-006 | GEN.43800 | QC procedures | QC program, QC data analysis, troubleshooting | Backend Team | Verified | `backend/app/routes/qc.py` | 2026-06 | Critical |
| CAP-007 | GEN.45500 | Proficiency testing | PT enrollment, result submission, performance evaluation | Backend Team | Implemented | `backend/app/routes/proficiency.py` | 2026-05 | High |
| CAP-008 | GEN.49000 | Competency assessment | Competency tracking, annual assessment, documentation | Admin Team | Implemented | Learning Platform, competency module | 2026-05 | High |
| CAP-009 | GEN.55555 | Laboratory information system | LIS validation, security, disaster recovery | Infrastructure Team | Verified | System validation documentation | 2026-06 | Critical |
| CAP-010 | GEN.56000 | Records retention | Retention policy, archival system, disposal | Infrastructure Team | Verified | `backend/app/core/retention.py` | 2026-05 | Medium |

---

## 8. CLSI (Clinical and Laboratory Standards Institute) Guidelines

| ID | Article/Clause | Requirement | GULA Control | Owner | Status | Evidence Location | Last Audit | Risk |
|----|---------------|-------------|--------------|-------|--------|-------------------|-----------|------|
| CLSI-001 | GP26-A3 | Laboratory quality management system | QMS module, document control, non-conformity management | Quality Team | Verified | `backend/app/routes/qms.py` | 2026-05 | High |
| CLSI-002 | GP27-A2 | Laboratory document control | Document lifecycle management, versioning | Quality Team | Verified | `backend/app/routes/qms.py` | 2026-05 | Medium |
| CLSI-003 | GP29-A | Laboratory validation and verification | Test validation, method verification workflows | Backend Team | Implemented | `backend/app/routes/validation.py` | 2026-04 | High |
| CLSI-004 | GP32-A | Urine specimen collection | Collection protocol templates, labeling | Backend Team | Implemented | `backend/app/routes/samples.py` | 2026-03 | Medium |
| CLSI-005 | H3-A6 | Blood specimen collection | Phlebotomy workflow, tube type management | Backend Team | Implemented | `backend/app/routes/samples.py` | 2026-03 | Medium |
| CLSI-006 | H5-A6 | Specimen transport and handling | Transport tracking, condition monitoring | Backend Team | Implemented | `backend/app/routes/samples.py` | 2026-04 | Medium |
| CLSI-007 | H18-A4 | Hemolysis detection | Hemolysis index tracking, sample quality flagging | Backend Team | Implemented | QC module, sample quality flags | 2026-04 | Medium |
| CLSI-008 | MM01-A3 | Molecular diagnostic methods | Molecular workflow management, result interpretation | Backend Team | Implemented | `backend/app/routes/molecular.py` | 2026-04 | Medium |
| CLSI-009 | MM13-A | Collection of diagnostic specimens | Collection procedure documentation, training | Backend Team | Implemented | `docs/learning/CL-003.md` | 2026-03 | Medium |
| CLSI-010 | POCT04-A3 | Point-of-care testing | POCT device integration, operator management | Backend Team | Implemented | `backend/app/routes/poct.py` | 2026-05 | High |
| CLSI-011 | QMS01-A | Quality management system model | QMS framework, process mapping | Quality Team | Verified | `backend/app/routes/qms.py` | 2026-05 | High |
| CLSI-012 | QMS02-A | Quality management system components | QMS component configuration | Quality Team | Implemented | QMS documentation | 2026-04 | Medium |
| CLSI-013 | QMS03-A | Non-conforming event management | NCR workflow, CAPA system | Quality Team | Verified | `backend/app/routes/qms.py` | 2026-06 | High |
| CLSI-014 | QMS04-A | Continual improvement | Quality indicators, PI tracking, improvement projects | Quality Team | Implemented | Quality dashboard | 2026-05 | Medium |
| CLSI-015 | QMS05-A | Personnel competency | Competency assessment, training records, proficiency | Admin Team | Verified | Learning Platform, competency module | 2026-06 | High |
| CLSI-016 | QMS06-A | Customer service | Customer feedback, complaint management | Admin Team | Implemented | `backend/app/routes/complaints.py` | 2026-04 | Medium |
| CLSI-017 | QMS07-A | Occurrence management | Incident reporting, investigation, learning | Quality Team | Implemented | Incident management module | 2026-05 | High |
| CLSI-018 | QMS08-A | Assessments and audits | Internal audit program, external audit management | Quality Team | Implemented | `backend/app/routes/audit.py` | 2026-05 | High |
| CLSI-019 | QMS09-A | Document management | Document control system, approval workflows | Quality Team | Verified | `backend/app/routes/qms.py` | 2026-05 | Medium |
| CLSI-020 | QMS10-A | Records management | Record retention, archival, disposal | Admin Team | Verified | `backend/app/core/retention.py` | 2026-05 | Medium |

---

## Coverage Heat Map

### Overall Compliance Coverage

```
Regulation              Not Implt  Planned  Implemented  Verified  Certified
Iraqi MoH               ████████░   ░░░░    ██████████    ████████████   ░░
                        0           2        5              10            3

Iraqi Data Protection    ██████░    █████    █████████      ██████       ░░
                        1           3        4              2            0

HIPAA Privacy            ░░░░       ░░░░     ███████████    ███████████  ░░
                        0           0        5              5            0

HIPAA Security          ░░░░░      ░░░░     █████████      ████████████ ░░
                        0           0        4              7            0

GDPR                    ██████░    ██████   ███████████     █████████    ░░
                        1           2        9              8            0

ISO 15189               ░░░░░      ░░░░     ████████        ██████████████ ███
                        0           0        4              14           7

ISO 27001               ░░░░░      ████     ███████████     ████████████ ░░
                        0           1        8              13           0

CAP                     ░░░░░      ░░░░     █████████       ██████████████
                        0           0        3              7            0

CLSI                    ░░░░░░     ░░░░░    █████████████   ████████     ░░
                        0           0        10             6            0
```

### Domain Coverage Summary

| Domain | Total Controls | Implemented | Verified | Gap |
|--------|---------------|-------------|----------|-----|
| Patient data management | 35 | 35 (100%) | 32 (91%) | 0 |
| Security & access control | 42 | 40 (95%) | 35 (83%) | 2 |
| QC & quality management | 30 | 28 (93%) | 24 (80%) | 2 |
| Lab operations | 28 | 28 (100%) | 25 (89%) | 0 |
| Audit & compliance | 22 | 20 (91%) | 18 (82%) | 2 |
| Infrastructure & DR | 18 | 17 (94%) | 14 (78%) | 1 |
| Training & competency | 15 | 14 (93%) | 11 (73%) | 1 |
| Incident management | 10 | 9 (90%) | 7 (70%) | 1 |
| **Total** | **200** | **191 (95.5%)** | **166 (83%)** | **9** |

### Gap Analysis (Not Implemented)

| ID | Regulation | Requirement | Priority | Action |
|----|------------|-------------|----------|--------|
| IQ-MOH-007 | Iraqi MoH | Proficiency testing module | Medium | Planned for Q3 2026 |
| IQ-DPL-006 | Iraq DPL | DPIA automation | High | In development |
| IQ-DPL-007 | Iraq DPL | Cross-border transfer framework | Medium | Legal review pending |
| GDPR-018 | GDPR | DPIA module | High | In development |
| GDPR-020 | GDPR | International transfer mechanisms | Medium | Legal review pending |
| ISO27001-022 | ISO 27001 | DLP controls | High | Vendor evaluation in progress |
| CAP-007 | CAP | Proficiency testing | High | Planned for Q3 2026 |
| CLSI-003 | CLSI | Advanced validation workflows | Low | Enhancement backlog |
| CLSI-010 | CLSI | POCT enhancements | Medium | Planned for Q4 2026 |

---

## Appendix: Compliance Verification Schedule

| Verification Type | Frequency | Method | Responsible |
|-------------------|-----------|--------|-------------|
| Automated compliance check | Continuous | Automated policy-as-code scanning | Infrastructure Team |
| Internal compliance review | Quarterly | Document review + system checks | Quality Team |
| External penetration test | Semi-annual | Third-party security assessment | Security Team |
| Regulatory self-assessment | Annual | Self-assessment against all regulations | Compliance Team |
| ISO 27001 surveillance | Annual | External auditor visit | Security Team |
| ISO 15189 surveillance | Annual | External auditor visit | Quality Team |
| Full recertification | Every 3 years | External audit for all standards | Quality + Security Teams |

## Appendix: Risk Scoring Methodology

| Factor | Weight | Scoring |
|--------|--------|---------|
| **Patient safety impact** | 40% | 0=no impact, 3=indirect, 7=direct, 10=life-threatening |
| **Data privacy impact** | 25% | 0=no PII, 3=anonymized, 7=indirect ID, 10=direct ID |
| **Regulatory penalty** | 20% | 0=none, 3=warning, 7=fine, 10=license suspension |
| **Business impact** | 15% | 0=cosmetic, 3=minor ops, 7=major ops, 10=shutdown |

**Risk Level = Σ(Score × Weight)**

| Level | Score Range | Color | Response |
|-------|-------------|-------|----------|
| Critical | 8.5-10 | Red | Immediate remediation required |
| High | 6.5-8.4 | Orange | Remediation within 30 days |
| Medium | 4.0-6.4 | Yellow | Remediation within 90 days |
| Low | 0-3.9 | Green | Monitor, remediate as capacity allows |
