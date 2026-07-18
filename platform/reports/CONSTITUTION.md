# GULA Constitution

## National Health Platform — Guiding Principles & Governance Framework

**Version:** 2.1.0
**Date:** July 2026

---

## Preamble

The GULA National Health Platform is built to serve the people of Iraq — citizens, healthcare providers, and the Ministry of Health — with a secure, reliable, and accessible digital health infrastructure. This Constitution establishes the non-negotiable principles and governance framework that guide every decision in the platform's development, deployment, and operation.

---

## Article 1: Core Principles

### 1.1 Patient Safety First
No feature, performance optimization, or cost-saving measure shall compromise patient safety. Clinical safety is always the highest priority.

### 1.2 Data Integrity Above All
Patient data must never be lost, corrupted, or exposed. All systems must maintain data integrity through encryption, validation, audit trails, and redundant storage.

### 1.3 Stability Before Features
Working code must never be broken to add new features. All changes must pass quality gates and regression tests before deployment.

### 1.4 Arabic-First
The platform is built for Arabic-speaking users. The default language is Arabic. All user interfaces, documentation, and communications prioritize Arabic while supporting English and other Iraqi languages.

### 1.5 Universal Access
The platform must be accessible to all Iraqis regardless of technical literacy, disability, or connectivity. Offline capability, accessibility (WCAG 2.1 AA), and simple interfaces are non-negotiable.

---

## Article 2: Tenant Isolation

### 2.1 Lab-Level Data Isolation
Every patient data query MUST filter by `lab_id = current_user.lab_id`. This is the fundamental security invariant — never bypass it.

### 2.2 Cross-Tenant Access
Cross-tenant data access is strictly prohibited unless explicitly authorized through Ministry-level functions with full audit logging.

### 2.3 Audit Trail
Every data access and modification must be recorded in the immutable audit log with the actor's identity, timestamp, and the specific data accessed.

---

## Article 3: Security Invariants

### 3.1 Encryption
- **At rest:** All patient data encrypted with AES-256. National IDs use column-level AES-256-GCM encryption.
- **In transit:** All traffic uses TLS 1.3 minimum. Internal service communication uses mTLS.
- **Keys:** Managed through KMS with automatic rotation. No hardcoded keys or secrets.

### 3.2 Authentication
- Support for JWT (RS256, 15-min access tokens), OAuth2, SAML 2.0, OTP, and biometric authentication.
- MFA is mandatory for clinical staff accounts.
- Token refresh uses rotation — each refresh token can be used exactly once.

### 3.3 Authorization
Role-based access control with 10 distinct roles and tenant-level attribute enforcement. No user may access data outside their authorized scope.

### 3.4 Vulnerability Management
- Critical CVEs: Fix within 48 hours
- High CVEs: Fix within 7 days
- Medium CVEs: Fix within 30 days
- Automated scanning in CI pipeline for every commit

---

## Article 4: Clinical Safety

### 4.1 Human-in-the-Loop
No automated AI decision affecting patient care may be final without human review. The system must block critical actions until a qualified human approves, modifies, or rejects.

### 4.2 Explainability
Every AI prediction must be explainable in natural language (Arabic + English). The explanation must include the factors influencing the decision and a confidence assessment.

### 4.3 Bias Monitoring
All AI models must be continuously monitored for demographic, selection, and algorithmic bias. Models showing significant bias must be automatically held from production.

### 4.4 Alert Fatigue
Clinical alerts must be severity-graded. Only critical alerts may interrupt clinical workflow. Non-critical alerts must be non-disruptive.

---

## Article 5: Operations & Reliability

### 5.1 Availability Target
The platform shall maintain 99.5% availability during business hours (7am–11pm Baghdad time) and 99.0% availability outside business hours.

### 5.2 Data Recovery
- RPO: 1 hour maximum data loss
- RTO: 4 hours to full recovery, 30 minutes to read-only access

### 5.3 Backup Requirements
- Daily full backups with 30-day retention
- Continuous WAL archiving for point-in-time recovery
- Monthly off-site backup storage
- Quarterly restore drills

### 5.4 Incident Response
- SEV-1 (Service Down): 15-minute response, 2-hour resolution
- SEV-2 (Degraded): 30-minute response, 4-hour resolution
- SEV-3 (Minor): 4-hour response, 24-hour resolution
- Post-mortem required within 48 hours for SEV-1 and SEV-2

---

## Article 6: Development Standards

### 6.1 Code Quality
- All code must pass TypeScript strict mode compilation
- All code must pass linting with zero errors
- Test coverage must be >= 95% for new code
- No TODO, FIXME, or hardcoded secrets in production code

### 6.2 Migration Policy
- Never modify an existing migration
- Every schema change requires a new Alembic revision
- Every migration must be idempotent
- New columns must be nullable or have server_default

### 6.3 CI/CD Pipeline
Every commit must pass:
1. Syntax compilation (`py_compile` for Python, `tsc` for TypeScript)
2. Linting (flake8/flake8 for Python, ESLint for TypeScript)
3. Security scanning (SAST, secret detection, dependency audit)
4. Unit and integration tests
5. Build and container image creation

### 6.4 Code Review
All code changes require a pull request with at least two approvals before merging. Security-critical changes require Security Lead approval.

---

## Article 7: Data Governance

### 7.1 Data Classification

| Classification | Examples | Requirements |
|---------------|----------|--------------|
| **Critical** | National ID, health records, genetic data | Column-level encryption, strict access control, full audit |
| **Sensitive** | Names, contact info, demographic data | Encryption at rest, access logging |
| **Internal** | Lab names, test codes, operational data | Standard access control |
| **Public** | Facility names, service information | No restrictions |

### 7.2 Data Retention
- Patient records: Indefinite (active), 10 years after last activity (archive)
- Audit logs: 2 years (hot), 7 years (cold), then deleted
- Session data: Auto-deleted after 7 days
- Backups: 30 days (hot), 365 days (cold)

### 7.3 Consent
Patient data may only be accessed for purposes to which the patient has explicitly consented. Consent can be revoked at any time.

---

## Article 8: Amendment Process

### 8.1 Proposal
Any team member may propose an amendment to this Constitution through a written proposal to the Steering Committee.

### 8.2 Review
The Steering Committee will review the proposal within 30 days, consulting with relevant domain leads.

### 8.3 Approval
Amendments require:
- Simple majority for non-principle changes
- Two-thirds majority for changes to Articles 1-4 (Core Principles, Tenant Isolation, Security, Clinical Safety)
- 100% consent from all domain leads for changes to Article 1 (Patient Safety, Data Integrity)

### 8.4 Effective Date
Approved amendments take effect 14 days after approval, allowing time for communication and implementation.

---

*This Constitution was adopted by the GULA Steering Committee on July 16, 2026.*
