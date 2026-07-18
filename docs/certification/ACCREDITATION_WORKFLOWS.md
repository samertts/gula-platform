# GULA Accreditation Workflows

## Overview

This document defines the end-to-end accreditation workflows for the GULA
Certification Platform. Each workflow maps the complete lifecycle from trigger
through completion, detailing stakeholders, documents, decision points, SLAs,
and automation opportunities.

### Workflow Principles

1. **Traceability**: Every action is logged with timestamp and actor
2. **Evidence-Based**: All decisions require documented evidence
3. **Right to Appeal**: Every adverse decision has an appeals path
4. **Scalable**: Workflows designed for 10 to 10,000 certifications
5. **Arabic-First**: All workflow communications in Arabic (with English parallel)
6. **Continuous Improvement**: Workflows evolve based on operational data

---

## 1. Initial Accreditation Workflow

### Trigger

Organization or individual submits application for initial certification via
the GULA Certification Portal.

### Workflow Steps

```
Step 1: Application Submission
────────────────────────────
Trigger: User completes and submits application form
Actor: Applicant (organization admin or individual)
System: Certification Portal
Documents:
  - Application form (digital)
  - Organization registration documents
  - Staff list and qualifications
  - Previous certifications (if any)
  - Lab license from MoH
SLAs:
  - Form completion: 30 minutes average
  - Document upload: Within 7 days of application start
Automation:
  - Form validation (required fields, format checks)
  - Automatic document classification (AI-based)
  - Fee calculation based on organization size

Decision Point DP-1: Application Complete?
├── Yes → Continue to Step 2
└── No  → Return to applicant with deficiency list
          SLA: 3 business days to review

Step 2: Document Review
────────────────────
Actor: Certification Officer
System: Document Management System
Activities:
  - Verify document authenticity
  - Cross-check against eligibility criteria
  - Identify missing or insufficient documents
  - Score document completeness
Documents:
  - Application review checklist
  - Document verification report
SLAs:
  - Initial review: 5 business days
  - Complex review (large org): 10 business days
Automation:
  - Document authenticity verification (OCR, digital signature check)
  - Automatic eligibility scoring
  - Document deficiency letter generation

Decision Point DP-2: Documents Acceptable?
├── Yes → Continue to Step 3
├── Minor Issues → Request additional documents (SLA: 5 days to respond)
└── Major Issues → Reject application with full explanation
                   SLA: 3 business days for rejection notice

Step 3: Pre-Assessment
────────────────────
Actor: Lead Auditor
System: Assessment Management System
Activities:
  - Review self-assessment questionnaire
  - Conduct pre-assessment interview (remote)
  - Determine audit scope and duration
  - Assign audit team
  - Schedule on-site audit
Documents:
  - Self-assessment questionnaire
  - Pre-assessment report
  - Audit plan (scope, team, schedule)
SLAs:
  - Pre-assessment review: 5 business days
  - Audit plan delivery: 3 business days after review
Automation:
  - Self-assessment scoring
  - Audit team recommendation (based on sector, size)
  - Calendar scheduling with conflict detection
  - Automated notification to auditee

Decision Point DP-3: Ready for Audit?
├── Yes → Continue to Step 4
└── No  → Remediation period (30 days max)
          Then reassess

Step 4: On-Site Audit
────────────────────
Actor: Audit Team (Lead Auditor + Team Members)
System: Audit Management System + Mobile Audit App
Activities:
  - Opening meeting
  - Facility tour
  - Document review (in detail)
  - Staff interviews
  - System demonstration
  - Process observation
  - Closing meeting
Duration:
  - Small lab (1-5 staff): 1-2 days
  - Medium lab (6-20 staff): 2-3 days
  - Large lab (21+ staff): 3-5 days
  - Hospital-wide: 4-5 days
Documents:
  - Opening meeting slides
  - Audit evidence collection forms
  - Staff interview records
  - Non-conformance reports (NCRs)
  - Audit report (draft)
SLAs:
  - Draft report delivery: 5 business days after audit
  - Final report: After management review
Automation:
  - Digital evidence capture (photo, video, document)
  - Real-time NCR creation
  - Audit checklist auto-population
  - Report generation (templates)

Step 5: Remediation
────────────────────
Actor: Applicant
System: Corrective Action Management
Activities:
  - Respond to NCRs with root cause analysis
  - Submit corrective action plans (CAP)
  - Implement corrections
  - Submit evidence of correction
  - Verification of closure
Documents:
  - Root cause analysis (per NCR)
  - Corrective action plan
  - Evidence of correction
  - CAP closure verification
SLAs:
  - Critical NCR closure: 5 business days
  - Major NCR closure: 15 business days
  - Minor NCR closure: 30 business days
  - Verification: 5 business days after submission
Automation:
  - CAP template generation
  - Deadline tracking with automated reminders
  - Evidence submission portal
  - Automatic escalation if overdue

Decision Point DP-4: All NCRs Closed?
├── Yes → Continue to Step 6
├── Major Open → Deferred (re-audit required)
│                SLA: Re-audit within 30 days
└── Critical Open → Denied (full reapplication after 90 days)
                    SLA: Denial notice within 3 business days

Step 6: Certification Decision
────────────────────
Actor: Certification Committee (independent)
System: Decision Management System
Activities:
  - Review audit report and findings
  - Verify all NCRs closed
  - Confirm audit team qualifications
  - Make certification decision
  - Determine certification level
Documents:
  - Audit report (final)
  - NCR closure verification
  - Certification decision form
  - Certificate (if approved)
SLAs:
  - Committee review: 10 business days
  - Decision notification: 2 business days after decision
Automation:
  - Decision recommendation (based on scoring algorithm)
  - Certificate generation
  - Blockchain anchoring
  - Notification to applicant

Decision Point DP-5: Certification Decision?
├── Certified → Continue to Step 7
├── Conditionally Certified → Issue with conditions
│                              Re-check in 90 days
└── Denied → Full explanation + appeal instructions
             Reapplication allowed after 90 days

Step 7: Certificate Issuance
────────────────────
Actor: System (automated)
System: Certificate Management System
Activities:
  - Generate certificate document
  - Anchor to blockchain
  - Issue to digital wallet
  - Notify stakeholders
  - Publish to certification directory
Documents:
  - Digital certificate (PDF)
  - Certificate metadata (JSON-LD)
  - Public directory entry
SLAs:
  - Certificate generation: < 1 hour after decision
  - Blockchain anchoring: < 1 hour (waiting for confirmations)
  - Digital wallet delivery: < 24 hours
Automation:
  - Full automation from decision to delivery

Step 8: Surveillance Setup
────────────────────
Actor: Certification Officer
System: Surveillance Management
Activities:
  - Configure continuous monitoring
  - Schedule periodic surveillance
  - Set up automated data feeds
  - Configure alert thresholds
Documents:
  - Surveillance plan
  - Monitoring configuration
  - Reporting schedule
SLAs:
  - Surveillance setup: 5 business days after issuance
Automation:
  - Monitoring configuration based on certification type
  - Calendar scheduling for periodic surveillance
  - Notification configuration
```

### Initial Accreditation SLA Summary

| Phase | SLA (Business Days) |
|-------|---------------------|
| Application submission & review | 10 |
| Document review | 10 |
| Pre-assessment | 8 |
| On-site audit | 5 (event) + 5 (report) |
| Remediation | 5-30 (variable) |
| Certification decision | 12 |
| Certificate issuance | 2 |
| **Total (best case)** | **~52 business days (~10 weeks)** |
| **Total (with remediation)** | **~82 business days (~16 weeks)** |

---

## 2. Renewal Accreditation Workflow

### Trigger

Existing certificate approaching expiry (90-day window before expiry).

### Workflow Summary

The renewal workflow is a streamlined version of the initial accreditation,
leveraging existing data and continuous monitoring.

```
Step 1: Renewal Notification
────────────────────────────
Trigger: 90 days before certificate expiry
Actor: System (automated)
Documents:
  - Renewal notification with instructions
  - Current certificate details
  - Surveillance summary
  - CME/CPD record (for individual)
Automation:
  - Full automation

Step 2: Simplified Application
────────────────────────────
Actor: Applicant
Documents:
  - Renewal application (pre-populated)
  - Changes since last certification (delta report)
  - Updated supporting documents (if changed)
  - CME/CPD evidence (for individuals)
SLAs:
  - Application submission: 30 days before expiry
  - Review: 5 business days
Automation:
  - Pre-populated application from existing data
  - Change detection from GULA platform analytics
  - Automatic CME record import

Decision Point RP-1: Significant Changes?
├── No significant change → Fast-track (Steps 3-5 skipped)
│                          Go to Decision Point RP-2
└── Significant change → Full renewal process
                         Continue to Step 3

Step 3: Document Review (if needed)
────────────────────
Similar to initial accreditation Step 2 but reduced scope
SLA: 3 business days (vs 10 for initial)

Step 4: Audit (if needed)
────────────────────
Scope: Changes only + verification of continuous compliance
Duration: 1 day (remote preferred)
SLA: Report within 3 business days

Step 5: Certification Decision
────────────────────
Actor: Certification Officer (not committee, for renewals)
SLA: 5 business days

Decision Point RP-2: Renewal Decision?
├── Approved → Certificate reissued with new expiry date
├── Conditional → Conditions with 60-day deadline
└── Denied → Full explanation + appeal + standard initial path for re-entry

Step 6: Certificate Reissuance
────────────────────
Identical to initial Step 7
```

### Renewal SLA Summary

| Scenario | SLA |
|----------|-----|
| Fast-track (no changes) | 10 business days |
| With changes (remote audit) | 20 business days |
| With changes (on-site audit) | 30 business days |

### Renewal Fee Structure

| Category | Fee | Notes |
|----------|-----|-------|
| No changes | 50% of initial fee | Minimal review |
| Minor changes | 75% of initial fee | Remote audit |
| Major changes | 100% of initial fee | Full audit |

---

## 3. Surprise Audit Workflow

### Trigger

Random selection (10% of active certificates) OR specific trigger event.

### Trigger Events

| Event | Description | Priority |
|-------|-------------|----------|
| Patient safety incident | Report of harm related to GULA usage | Critical |
| Data breach | Security incident involving patient data | Critical |
| Staff complaint | Multiple complaints about quality | High |
| Whistleblower report | Internal report of non-compliance | High |
| Random selection | Automated random sampling | Normal |
| Media attention | Negative press about organization | Variable |
| MOI/MoH request | Official government request | High |

### Workflow

```
Step 1: Audit Trigger
────────────────────
Trigger: Random selection OR event
Actor: System OR Certification Officer
Decision: Audit scope and urgency determined

Step 2: Notice Period
────────────────────
Type:
  - Unannounced: No notice (0 hours)
  - Short notice: 24-48 hours
  - Standard: 2 weeks (for random selection)

Step 3: Audit Execution
────────────────────
Scope:
  - Full scope: All certification requirements
  - Focused scope: Specific area of concern
  - Triage scope: Quick assessment (half-day)
Duration: 0.5-2 days depending on scope

Step 4: Findings
────────────────────
Same NCR process as initial accreditation
Escalated SLAs:
  - Critical NCR response: 24 hours
  - Major NCR response: 5 business days
  - Minor NCR response: 10 business days

Step 5: Decision
────────────────────
Possible outcomes:
  - No change (certificate maintained)
  - Level downgrade (e.g., Gold → Silver)
  - Conditional certification
  - Suspension (immediate, pending investigation)
  - Revocation (for critical findings)
```

---

## 4. Remediation Workflow

### Trigger

Non-conformance report (NCR) issued during any audit.

### Workflow

```
NCR Issued
    │
    ▼
Step 1: Acknowledge Receipt
────────────────────
Actor: Applicant
SLA: 2 business days
Output: Receipt acknowledgment
Automation: Automated acknowledgment request

Step 2: Root Cause Analysis (RCA)
────────────────────
Actor: Applicant quality team
Methods:
  - 5 Whys
  - Fishbone diagram
  - FMEA (for critical findings)
SLA:
  - Critical: 24 hours
  - Major: 5 business days
  - Minor: 10 business days
Documents: RCA report
Automation: RCA template generator

Step 3: Corrective Action Plan (CAP)
────────────────────
Actor: Applicant
Contents:
  - Root cause statement
  - Corrective action description
  - Implementation timeline
  - Success criteria
  - Responsible person
SLA:
  - Critical: 48 hours
  - Major: 10 business days
  - Minor: 15 business days
Documents: CAP form (standardized)

Decision Point REM-1: CAP Acceptable?
├── Yes → Implement
└── No  → Return for revision (SLA: 5 days)

Step 4: Implementation
────────────────────
Actor: Applicant
Activities:
  - Execute corrective actions
  - Collect evidence of implementation
  - Update documentation
  - Train staff if needed
SLA: Per CAP timeline (5-30 days)
Documents: Implementation evidence

Step 5: Verification of Effectiveness (VoE)
────────────────────
Actor: Audit Team
Methods:
  - Document review (standard)
  - Remote verification (for minors)
  - On-site verification (for critical/major)
SLA:
  - Critical: 3 business days after implementation
  - Major: 10 business days
  - Minor: 15 business days

Decision Point REM-2: CAP Effective?
├── Yes → NCR Closed
├── Partially → Revised CAP required (SLA: 10 days)
└── No → Escalation (see Escalation Workflow)
```

---

## 5. Escalation Workflow

### Trigger

Conditions that require escalation beyond standard certification process.

### Escalation Triggers

| Trigger | From | To |
|---------|------|----|
| Unresolved critical NCR | Audit team | Certification Manager |
| Repeated major NCRs | Audit team | Certification Manager |
| Fraud or misrepresentation discovered | Any | Certification Board |
| Patient harm reported | Any | Emergency Committee |
| Legal/regulatory action | External notification | Certification Board |
| Appeal of decision | Applicant | Appeals Panel |

### Escalation Levels

```
Level 1: Certification Manager Review
─────────────────────────
Scope: Single unresolved issue
Authority: Extend deadlines, require re-audit
SLA: 5 business days for decision

Level 2: Certification Board Review
─────────────────────────
Scope: Pattern of issues, policy questions
Authority: Modify certification conditions, downgrade level
SLA: 10 business days for decision

Level 3: Emergency Committee
─────────────────────────
Scope: Patient safety, legal issues, public health
Authority: Immediate suspension, mandatory reporting
SLA: 24-48 hours for decision
```

### Escalation Workflow

```
Trigger Event
    │
    ▼
Level 1: Certification Manager
    ├── Resolved → Close escalation
    └── Not resolved → Level 2
    
Level 2: Certification Board
    ├── Resolved → Decision communicated
    └── Not resolved → Level 3 or external authority
    
Level 3: Emergency Committee
    ├── Immediate action taken
    ├── Mandatory reporting (if applicable)
    └── Long-term resolution plan
```

---

## 6. Revocation Workflow

### Trigger

Conditions warranting certificate revocation.

### Revocable Offenses

| Offense | Severity | Action |
|---------|----------|--------|
| Patient data breach | Critical | Immediate suspension + investigation |
| Fraudulent certification application | Critical | Revocation + 5-year ban |
| Deliberate misrepresentation of GULA compliance | Critical | Revocation |
| Failure to remediate critical NCR | High | Revocation after escalation |
| Non-payment of certification fees | Medium | Suspension → Revocation (60 days) |
| Voluntary surrender | Low | Immediate revocation |

### Due Process Workflow

```
Incident Detected
    │
    ▼
Step 1: Preliminary Investigation
────────────────────
Actor: Certification Officer
Duration: 5 business days
Output: Investigation report with recommendation
Confidential: Yes

Step 2: Show Cause Notice
────────────────────
Actor: Certification Manager
Contents:
  - Nature of alleged violation
  - Evidence summary
  - Required response (show cause why revocation should not occur)
  - Response deadline (15 business days)
Notification: Registered email + courier

Step 3: Holder Response
────────────────────
Actor: Certificate holder
Contents:
  - Response to allegations
  - Mitigating circumstances
  - Corrective action already taken
  - Any supporting evidence
SLA: 15 business days from notice

Step 4: Review and Decision
────────────────────
Actor: Certification Board (or Emergency Committee)
Activities:
  - Review investigation report
  - Consider holder response
  - Deliberate (confidential)
  - Make decision
SLA: 10 business days after response deadline

Decision Point REV-1: Revocation Decision?
├── Revoke → Immediate effect
│            All stakeholders notified
│            Public directory updated
│            Digital wallet updated
│            Blockchain status updated
│
├── Suspension → Temporary (30-90 days)
│                Conditions for reinstatement defined
│                Monitoring period
│
├── Lesser Penalty → Fine, warning, conditions
└── No Action → Case closed, holder notified

Step 5: Appeal Notification
────────────────────
Actor: Certification Officer
Contents:
  - Decision details
  - Appeal rights and process
  - Appeal deadline (30 days)
SLA: 3 business days after decision

Step 6: Implementation
────────────────────
Actor: System (automated)
Actions:
  - Update certificate status in database
  - Register revocation on blockchain
  - Update verification API
  - Notify digital wallets
  - Update public directory
  - Notify internal systems (EventBus)
SLA: < 2 hours
```

---

## 7. Cross-Border Accreditation Workflow

### Purpose

Enable recognition of GULA certifications across international borders and
mutual recognition agreements with other certification bodies.

### Recognition Models

| Model | Description | Complexity |
|-------|-------------|------------|
| **Unilateral** | GULA recognizes foreign certification | Low |
| **Bilateral** | Mutual recognition agreement | Medium |
| **Multilateral** | Multi-party accreditation network | High |
| **Endorsement** | Foreign certification endorsed by GULA | Medium |
| **Bridging** | Gap assessment + supplementary certification | Medium |

### Workflow

```
Request for Cross-Border Recognition
    │
    ▼
Step 1: Equivalency Assessment
────────────────────
Actor: Certification Board + Technical Committee
Activities:
  - Compare certification requirements
  - Identify gaps and overlaps
  - Assess assessment rigor
  - Review issuing body credentials
Duration: 20 business days
Documents:
  - Foreign certification standard
  - Equivalency mapping matrix
  - Issuing body assessment

Decision Point CB-1: Equivalent?
├── Full → Automatic recognition
├── Partial → Bridging certification required
└── None → Standard initial certification path

Step 2: Bridging Certification (if needed)
────────────────────
Actor: Applicant
Scope:
  - Arabic terminology assessment
  - Iraqi regulatory module
  - GULA platform orientation
  - Country-specific compliance module
Duration: 1-2 weeks

Step 3: Cross-Border Certification Issuance
────────────────────
Additional fields in certificate:
  - Original certification reference
  - Recognition basis (treaty, agreement, assessment)
  - Jurisdictional scope
  - Issuing body details

Step 4: Ongoing Monitoring
────────────────────
Integration with:
  - Foreign issuing body's surveillance system
  - Shared revocation registry
  - Periodic joint audits (annually)
```

---

## 8. Integration with National Authorities

### Ministry of Health (MoH) Integration

| Interaction | Trigger | Data Shared |
|-------------|---------|-------------|
| Certification notification | New organizational certification issued | Organization name, certification level, scope |
| Revocation notification | Certificate revoked | Organization name, reason, date |
| Regulatory reporting | Quarterly | Aggregate certification statistics |
| Audit participation | Per agreement | MoH observer on certification audits |
| Standards alignment | Annual | Certification criteria review |

### Professional Body Integration

| Body | Purpose | Mechanism |
|------|---------|-----------|
| Iraqi Medical Association | Doctor certification recognition | API data exchange |
| Iraqi Nurses Union | Nursing certification alignment | Shared standards |
| Iraqi Association of Medical Lab Scientists | Lab certification endorsement | Joint certification pathways |
| Pharmacists Syndicate | Pharmacy certification | Credential verification |

### Data Exchange Protocol

```json
{
  "exchange_type": "certification_notification",
  "authority_id": "iraq-moh-001",
  "timestamp": "2026-07-01T10:00:00Z",
  "certificates": [
    {
      "certificate_number": "ORG-02-2026-0015",
      "organization_name_ar": "مختبر بغداد المركزي",
      "organization_name_en": "Baghdad Central Laboratory",
      "certification_type": "GULA-Compliant Lab",
      "level": "platinum",
      "issued_at": "2026-06-01",
      "expires_at": "2027-06-01",
      "status": "active",
      "scope": "Clinical chemistry, hematology, microbiology",
      "verification_url": "https://verify.gula-platform.com/cert/ORG-02-2026-0015"
    }
  ],
  "signature": {
    "algorithm": "HMAC-SHA256",
    "value": "..."
  }
}
```

### Automation Opportunities

Across all workflows, the following automation is available:

| Automation | Implementation | Workflow |
|------------|----------------|----------|
| Application pre-fill | Data from GULA core | All application steps |
| Document classification | AI document classifier | Document review |
| Eligibility scoring | Rules engine | DP-1, DP-2 |
| Audit scheduling | Calendar optimization | Step 3 (all workflows) |
| Evidence capture | Mobile app with OCR | On-site audit |
| Report generation | Template engine | Post-audit reporting |
| CAP tracking | Automated deadline monitoring | Remediation |
| Decision recommendation | Scoring algorithm | Certification decision |
| Certificate generation | Template + blockchain | Issuance |
| Surveillance monitoring | Data pipeline from GULA | Surveillance |
| Renewal detection | Expiry monitoring | Renewal trigger |
| Risk-based selection | Random + risk scoring | Surprise audit trigger |
| Escalation detection | Rule-based alerts | Escalation trigger |
| Revocation implementation | API orchestration | Revocation Step 6 |

---

## Appendix: Workflow State Machine

```
State: DRAFT → SUBMITTED → UNDER_REVIEW → PRE_ASSESSMENT → 
       AUDIT_SCHEDULED → AUDIT_IN_PROGRESS → AUDIT_COMPLETED →
       REMEDIATION → DECISION_PENDING → ISSUED → ACTIVE →
       SURVEILLANCE → [RENEWAL → ACTIVE] OR [EXPIRED] OR [REVOKED]
```

## Appendix: Document Templates

| Document | Template ID | Language |
|----------|-------------|----------|
| Audit Plan | `TMPL-AUDIT-PLAN-001` | AR/EN |
| Non-Conformance Report | `TMPL-NCR-001` | AR/EN |
| Corrective Action Plan | `TMPL-CAP-001` | AR/EN |
| Audit Report | `TMPL-AUDIT-REPORT-001` | AR/EN |
| Certification Decision | `TMPL-DECISION-001` | AR/EN |
| Show Cause Notice | `TMPL-SHOW-CAUSE-001` | AR/EN |
| Certificate | `TMPL-CERT-{TYPE}-{LEVEL}` | AR/EN |
| Renewal Application | `TMPL-RENEWAL-001` | AR/EN |

## Appendix: SLA Escalation

If any step exceeds its SLA, automatic escalation occurs:

| Overrun | Action | Notify |
|---------|--------|--------|
| +25% of SLA | Reminder | Responsible person |
| +50% of SLA | Warning | Responsible person + manager |
| +75% of SLA | Escalation | Certification Manager |
| +100% of SLA | Critical alert | Director of Certification |
