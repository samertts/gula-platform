# GULA National Trust, Compliance & Privacy Platform

**Version:** 1.0.0 (Frozen)
**Date:** 2026-07-16
**Classification:** SUPREME — National Trust Platform Constitution
**Supersedes:** All prior privacy and compliance policies

---

## Preamble

This document establishes the National Trust Platform for the GULA National Digital
Health Platform. It governs privacy, compliance, data sovereignty, digital trust,
national policies, audit compliance, legal compliance, clinical compliance, AI
governance, digital evidence, and long-term preservation.

Every module, application, API, database, event, FHIR resource, SDK, security
policy, and AI model MUST comply with this platform. The foundation remains frozen.

---

## Article I: Trust Principles

### Section 1.1 — National Trust Foundations

| Principle | Mandate |
|-----------|---------|
| Patient Trust | Patients own their data. The platform is a custodian, not an owner. |
| Transparency | Every data access is visible to the patient. No hidden processing. |
| Accountability | Every action is attributed to a verified identity. |
| Sovereignty | Iraqi health data remains in Iraq under Iraqi law. |
| Integrity | Data cannot be modified without detection and audit trail. |

### Section 1.2 — Trust Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Citizen Trust Layer                       │
│  Privacy Dashboard | Consent Dashboard | Access History     │
├─────────────────────────────────────────────────────────────┤
│                    Trust Services Layer                      │
│  Digital Signature | Timestamping | Evidence Preservation   │
├─────────────────────────────────────────────────────────────┤
│                    Compliance Layer                          │
│  Policy Engine | Evidence Collection | Audit Trail          │
├─────────────────────────────────────────────────────────────┤
│                    Sovereignty Layer                         │
│  Data Residency | Encryption | National Key Management      │
├─────────────────────────────────────────────────────────────┤
│                    Privacy Layer                             │
│  Consent | Masking | Anonymization | Pseudonymization       │
├─────────────────────────────────────────────────────────────┤
│                    Data Layer                                │
│  Encrypted Storage | Immutable Audit | FHIR Resources       │
└─────────────────────────────────────────────────────────────┘
```

---

## Article II: Repository Trust Audit

### Section 2.1 — Audit Requirements

Every repository, application, API, database, event, FHIR resource, SDK,
security policy, and AI model MUST be audited against:

| Audit Dimension | Coverage | Frequency |
|-----------------|----------|-----------|
| Trust Compliance | All components | Quarterly |
| Privacy Compliance | All data-handling components | Monthly |
| Risk Assessment | All external-facing components | Monthly |
| Security Posture | All components | Weekly |
| AI Trust | All AI features | Per-release |

### Section 2.2 — Trust Report

Generated quarterly, containing:
- Trust score per component (0-100)
- Compliance gaps with remediation plans
- Risk register updates
- Incident summary

### Section 2.3 — Compliance Report

Generated monthly, containing:
- Regulatory compliance status
- Audit finding summary
- Corrective action tracking
- Evidence collection status

### Section 2.4 — Risk Report

Generated monthly, containing:
- Risk inventory and scores
- Risk treatment plans
- Residual risk acceptance
- Emerging risk identification

---

## Article III: Privacy Platform

### Section 3.1 — Consent Management

| Consent Type | Requirements | Implementation |
|-------------|--------------|----------------|
| Collection | Explicit, informed, specific | Pre-collection consent dialog |
| Processing | Purpose-limited | Purpose attribute on consent |
| Sharing | Named recipients only | Consent reference on share |
| Withdrawal | Right to withdraw at any time | One-click withdrawal |
| Minor | Guardian consent required | Dual-consent workflow |

### Section 3.2 — Purpose Of Use

Every data access MUST declare a Purpose of Use. Purposes are:
- Treatment
- Payment
- Operations
- Public Health
- Research (with separate consent)
- National Reporting (mandated by law)

### Section 3.3 — Minimum Necessary Access

Every API and service MUST enforce minimum necessary access:
- Only the minimum data fields needed for the purpose
- Only the minimum records needed for the operation
- Only for the minimum time needed for the task

### Section 3.4 — Sensitive Record Protection

Sensitive records (genetic data, mental health, HIV status, reproductive health):
- Explicit consent required for every access
- Separate encryption keys
- Enhanced audit logging
- Breach notification within 24 hours

### Section 3.5 — Minor Protection

- Minors (<18) require guardian consent
- Minor data access logged with guardian ID
- Minor right to privacy on reaching majority
- Transition process at age of majority

### Section 3.6 — Guardian Policies

Guardians have access to minor records but NOT to:
- Sexual health records (after age 14)
- Mental health records (after age 16)
- Reproductive health records (after age 14)

### Section 3.7 — Data Masking

| Field | Masking Rule | Example |
|-------|-------------|---------|
| National ID | Show last 4 digits | `****-****-1234` |
| Phone number | Show last 4 digits | `+964-***-****-5678` |
| Email | Show domain only | `***@example.com` |
| Name (non-clinical) | First name + last initial | `Ahmed A.` |

### Section 3.8 — Data Anonymization

Anonymization MUST remove:
- Direct identifiers (name, ID, phone, email)
- Quasi-identifiers (DOB transformed to age group, zip to region)
- Clinical free text (de-identified using NLP)
- Dates transformed to relative offsets

### Section 3.9 — Pseudonymization

Pseudonymization uses:
- Deterministic pseudonyms for same-patient linking
- Reversible only with special key
- Key stored separately from pseudonymized data
- Key access logged and audited

### Section 3.10 — Retention Policies

| Data Category | Retention | Deletion |
|--------------|-----------|----------|
| Clinical records | 25 years from last visit | Anonymize after retention |
| Lab results | 10 years | Anonymize after retention |
| Audit logs | 7 years | Archive after retention |
| Consent records | Duration of consent + 2 years | Delete after retention |
| Session data | 24 hours | Auto-delete |
| Backup | 30 days (incremental), 1 year (monthly) | Secure deletion |

---

## Article IV: Digital Sovereignty

### Section 4.1 — National Data Ownership

- All patient data is owned by the Republic of Iraq
- The platform operates under license from the Ministry of Health
- No data may be transferred, sold, or used outside of authorized purposes
- Data ownership is inalienable

### Section 4.2 — Data Residency

- All patient data stored on servers physically located in Iraq
- No replication to foreign jurisdictions
- Backup stored in Iraq only
- Disaster recovery within Iraqi borders
- Cloud providers must have in-country data centers

### Section 4.3 — Cross-Border Transfer

Cross-border data transfer is PROHIBITED except:
- Explicit patient consent for international treatment
- Ministry of Health authorization
- International health emergency (WHO mandate)
- All transfers logged and audited

### Section 4.4 — Key Ownership

- Encryption keys owned and managed by the Republic of Iraq
- Key generation, rotation, and destruction follows national policy
- Key escrow with Ministry of Health
- Foreign key management not permitted

### Section 4.5 — National Encryption Policies

- All encryption uses NIST-approved algorithms
- Key sizes meet or exceed national standards
- Post-quantum cryptography roadmap maintained
- Encryption implementation validated by national authority

### Section 4.6 — National Backup Policies

- Backup must be stored in at least 2 Iraqi data centers
- Monthly restore testing mandatory
- Backup encryption key separate from production keys
- Backup integrity verified on every restore test

---

## Article V: Compliance Framework

### Section 5.1 — Configurable Compliance Framework

The compliance framework supports dynamic mapping to:
- Iraqi national health regulations
- International standards where adopted (ISO 27001, HIPAA, GDPR elements)
- Ministry of Health directives
- Regional health authority policies

### Section 5.2 — Evidence Collection

| Evidence Type | Collection Method | Retention |
|--------------|-------------------|-----------|
| Access logs | Automated from middleware | 7 years |
| Consent records | From consent service | Consent + 2 years |
| Audit trail | Immutable hash chain | 7 years |
| Policy reviews | Manual + system verification | 5 years |
| Training records | HR system integration | 3 years |
| Risk assessments | Automated quarterly | 5 years |

### Section 5.3 — Compliance Dashboards

- Real-time compliance status
- Evidence collection completeness
- Open corrective actions
- Risk heat map
- Audit readiness score

### Section 5.4 — Corrective Actions

- Auto-generated from compliance gaps
- Assigned with severity and deadline
- Tracked to resolution
- Escalated on deadline miss
- Verified by re-audit

### Section 5.5 — Continuous Compliance

- Automated compliance checks on every deployment
- Policy-as-code enforcement
- Drift detection and alerting
- Quarterly compliance certification

---

## Article VI: Trust Services

### Section 6.1 — Digital Signature

- Qualified electronic signatures per national law
- Signature verification with certificate chain
- Signature timestamp binding
- Long-term signature preservation

### Section 6.2 — Timestamping

- RFC 3161 compliant timestamping
- Trusted timestamp authority
- Audit-proof timestamp binding
- Timestamp verification on every evidence export

### Section 6.3 — Evidence Preservation

- Evidence stored in tamper-evident format
- Hash chain preserves integrity
- Periodic integrity verification
- Evidence export with full provenance

### Section 6.4 — Certificate Lifecycle

| Stage | Action | System |
|-------|--------|--------|
| Issuance | Certificate Authority validates identity | PKI system |
| Deployment | Certificate distributed securely | Vault |
| Monitoring | Expiry detection, 30-day warning | Monitoring |
| Renewal | Automated renewal before expiry | Cert-manager |
| Revocation | Immediate on compromise | CRL/OCSP |
| Expiration | Auto-renew or alert | Monitoring |

### Section 6.5 — Identity Verification Hooks

- Integration with national identity system
- Biometric verification (optional)
- Document verification
- Liveness detection
- Continuous authentication monitoring

### Section 6.6 — Document Integrity

- Document hash stored on creation
- Hash verified on every access
- Tamper detection alerting
- Forensic verification exportable

---

## Article VII: AI Trust

### Section 7.1 — AI Transparency

- Every AI interaction clearly labeled as AI-generated
- Confidence scores displayed for all AI predictions
- Model limitations communicated explicitly
- Human oversight option always available

### Section 7.2 — AI Explainability

- SHAP/LIME explanations for model predictions
- Natural language explanations for clinical recommendations
- Decision tree visualization for rule-based systems
- Explanation stored in audit trail

### Section 7.3 — Human Approval

| AI Decision Type | Approval Required | Mechanism |
|-----------------|-------------------|-----------|
| Clinical recommendation | YES | Approval workflow |
| Test interpretation | YES | Clinical review |
| Alert prioritization | YES | Manual override available |
| Scheduling suggestion | NO (opt-out) | Auto-implemented |
| Population health insight | NO | Dashboard display |

### Section 7.4 — Model Audit

- Model version, training data, and validation results recorded
- Performance metrics tracked over time
- Data drift and concept drift monitored
- Model retirement criteria defined

### Section 7.5 — Prompt Audit

- All prompts versioned and immutable
- Prompt changes require review
- Prompt injection attempts logged
- Prompt effectiveness monitored

### Section 7.6 — Bias Monitoring

- Demographic parity by age, gender, region
- Equal opportunity for all population groups
- Disparate impact analysis quarterly
- Bias mitigation action plans

### Section 7.7 — Safety Validation

- Hallucination detection on all generative outputs
- Safety guardrails on all AI endpoints
- Red-teaming before model deployment
- Continuous harm monitoring

---

## Article VIII: National Audit

### Section 8.1 — Immutable Audit

- Every data mutation recorded in hash chain
- Chain: `hash(n-1) + event + timestamp + hash(n)`
- Verification: recompute chain and compare
- Tampering detected immediately

### Section 8.2 — Forensic Logs

- Full request/response capture for sensitive operations
- Network-level logging for intrusion detection
- System call logging for privileged operations
- Logs preserved for 7 years

### Section 8.3 — Chain Of Custody

| Event | Recorded Fields |
|-------|-----------------|
| Data creation | Who, when, what, source |
| Data access | Who, when, why, what fields |
| Data modification | Who, when, before state, after state |
| Data deletion | Who, when, what, authorization |
| Data export | Who, when, what, destination |

### Section 8.4 — Evidence Export

Export format: signed JSON with:
- Evidence payload
- Hash chain position
- Digital signature
- Timestamp certificate
- Chain of custody

### Section 8.5 — Integrity Verification

- Automatic chain verification every hour
- Discrepancy alert within 5 minutes
- Full chain audit every 24 hours
- Forensic-grade verification on demand

---

## Article IX: Long-Term Preservation

### Section 9.1 — Medical Record Preservation

- Records preserved for legal minimum + safety margin
- Format: FHIR (canonical) + PDF/A (human-readable)
- Periodic format migration for readability
- Full-text search index preserved

### Section 9.2 — Archive Policies

| Archive Type | Trigger | Storage | Access |
|-------------|---------|---------|--------|
| Active | Current data | Primary DB | Full |
| Warm | 1-5 years old | Compressed DB | Limited |
| Cold | 5-25 years old | Encrypted archive | Audit only |
| Deep | 25+ years | Offline storage | National archive |

### Section 9.3 — Migration Policies

- Format migration before technology obsolescence
- Migration tested on sample before full run
- Migration logged and audited
- Original format preserved alongside new format

### Section 9.4 — Checksum Validation

- Every archived record has checksum
- Periodic re-validation (annually)
- Checksum algorithm updated as standards evolve
- Failed checksum triggers immediate investigation

### Section 9.5 — Integrity Monitoring

- Automated daily integrity check
- Bit-rot detection on storage media
- Replication consistency verification
- Recovery drill every quarter

---

## Article X: Citizen Trust

### Section 10.1 — Privacy Dashboard

Citizens can view:
- What data is collected
- How data is used
- Who has accessed their data
- Consent status per purpose
- Retention status per record

### Section 10.2 — Consent Dashboard

- View all active consents
- Modify consent scope (with clinical override for safety)
- Withdraw consent (with clinical review)
- Consent history

### Section 10.3 — Access History

Complete access history with:
- Who accessed the record
- When they accessed it
- What purpose they declared
- What data they viewed
- Duration of access

### Section 10.4 — Who Accessed My Record

- Real-time notification on access
- Monthly access summary report
- Suspicious access alerting
- Access report exportable

### Section 10.5 — Notification Center

- Consent expiry warnings
- Data breach notifications
- New purpose notifications
- Policy change notifications
- Access summary notifications

---

## Article XI: Developer Platform

### Section 11.1 — Compliance SDK

Auto-generated SDK for:
- Consent checking
- Purpose validation
- Privacy masking
- Audit logging
- Encryption helpers

### Section 11.2 — Policy Engine

Generic policy engine supporting:
- Rules-based access control
- Attribute-based policies
- Temporal policies
- Contextual policies
- Policy versioning

### Section 11.3 — REST APIs

| API | Purpose | Auth |
|-----|---------|------|
| `/api/v1/consent` | Consent management | Bearer + ABAC |
| `/api/v1/privacy` | Privacy operations | Bearer + ABAC |
| `/api/v1/audit` | Audit queries | Bearer + admin |
| `/api/v1/trust` | Trust services | mTLS |
| `/api/v1/compliance` | Compliance reporting | Bearer + admin |

### Section 11.4 — OpenAPI

All trust platform APIs have OpenAPI 3.1 specs:
- Available at `/docs`
- Versioned
- Include security schemas
- Include example requests/responses

### Section 11.5 — CLI

Trust platform CLI for:
- Compliance check
- Evidence export
- Audit query
- Consent management
- Encryption operations

### Section 11.6 — Architecture

```
backend/app/
├── legal/           # Consent models (existing)
├── audit/           # Audit logging (existing)
├── services/
│   ├── consent_service.py
│   ├── audit_service.py
├── governance/      # Governance platform (existing)
├── trust/           # Trust platform (NEW)
│   ├── base.py
│   ├── models.py
│   ├── services.py
│   ├── routes.py
│   ├── policies/
│   ├── compliance/
│   └── sovereignty/
├── core/
│   ├── policy_engine.py  # (existing)
│   ├── decision_guard.py # (existing)
│   └── risk_engine.py    # (existing)
```

### Section 11.7 — Documentation

- Trust Guide: `docs/trust/TRUST-GUIDE.md`
- Privacy Guide: `docs/trust/PRIVACY-GUIDE.md`
- Compliance Guide: `docs/trust/COMPLIANCE-GUIDE.md`
- Sovereignty Guide: `docs/trust/SOVERIEGNTY-GUIDE.md`

---

## Quality Gates

| Gate | Check | Threshold |
|------|-------|-----------|
| Architecture validation | Layer compliance | 0 violations |
| Security validation | OWASP Top 10 | 0 findings |
| Privacy validation | Data minimization | 0 violations |
| Compliance validation | Regulatory coverage | 100% |
| Performance validation | P95 under 500ms | Pass |
| FHIR validation | Resource compliance | 0 errors |
| Ruff | All rules | 0 errors |
| MyPy strict | Type coverage | 0 errors |
| Pytest | All tests pass | 0 failures |
| Coverage | Line coverage | >=95% |
| Bandit | SAST scan | 0 High/Medium |
| Semgrep | Custom rules | 0 findings |
| SBOM | Dependency scan | 0 Critical/High |

---

## Signatories

This National Trust Platform is adopted and frozen as the supreme authority for
privacy, compliance, trust, and data sovereignty for the GULA National Digital
Health Platform.

**Date:** 2026-07-16
**Version:** 1.0.0 — FROZEN

---

## References

- `docs/constitution/PLATFORM-CONSTITUTION.md` — Platform Constitution
- `docs/trust/` — Trust platform documentation
- `backend/app/legal/` — Legal and consent models
- `backend/app/audit/` — Audit system
- `backend/app/core/policy_engine.py` — Policy enforcement
- `backend/app/governance/` — Governance platform
- `config/zero-trust/` — Zero trust configuration
