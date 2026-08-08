# Risk Register

## GULA National Health Platform — Comprehensive Risk Assessment

**Version:** 2.1.0
**Date:** July 2026
**Review Cycle:** Monthly

---

## 1. Risk Scoring Methodology

| Dimension | Score | Definition |
|-----------|-------|------------|
| **Likelihood** | 1-5 | 1=Rare, 2=Unlikely, 3=Possible, 4=Likely, 5=Almost Certain |
| **Impact** | 1-5 | 1=Negligible, 2=Minor, 3=Moderate, 4=Major, 5=Critical |
| **Risk Level** | Score × Impact | 1-6=Low, 7-12=Medium, 13-19=High, 20-25=Extreme |

---

## 2. Technical Risks

| ID | Risk Description | Likelihood | Impact | Level | Owner | Mitigation | Status |
|----|-----------------|------------|--------|-------|-------|------------|--------|
| TR-001 | Database connection pool exhaustion under peak load | 2 | 4 | Medium (8) | DB Admin | Auto-scaling, connection monitoring, pool alerts | ✅ Mitigated |
| TR-002 | Prolonged PostgreSQL replication lag during batch operations | 3 | 3 | Medium (9) | DB Admin | Batch size limits, replication monitoring, async replication | ✅ Mitigated |
| TR-003 | Redis memory exhaustion from session storage | 2 | 3 | Low (6) | Platform | Memory monitoring, LRU eviction, cluster scaling | ✅ Mitigated |
| TR-004 | S3 bucket misconfiguration leading to data exposure | 1 | 5 | Medium (5) | Security | Block Public Access, automated compliance scanning | ✅ Mitigated |
| TR-005 | Service disruption during blue/green deployment | 2 | 4 | Medium (8) | Ops | Health check gating, automated rollback, canary testing | ✅ Mitigated |
| TR-006 | Terraform state corruption or lock contention | 2 | 3 | Low (6) | Platform | Remote state (S3+DynamoDB), serial CI execution | ✅ Mitigated |
| TR-007 | Container image vulnerability in base images | 3 | 3 | Medium (9) | Security | Trivy scanning in CI, minimal base images, regular rebuilds | ✅ Mitigated |
| TR-008 | TLS certificate expiry causing service interruption | 1 | 4 | Low (4) | Ops | Auto-renew (cert-manager/ACM), 30-day expiry alerts | ✅ Mitigated |
| TR-009 | API rate limiting blocking legitimate clinical workflows | 2 | 3 | Low (6) | Backend | Clinical writes exempt from rate limiting, burst allowances | ✅ Mitigated |
| TR-010 | Offline sync data conflicts causing data loss | 2 | 4 | Medium (8) | Backend | Version-based conflict resolution, audit trail, manual merge UI | ✅ Mitigated |
| TR-011 | Slow query performance on national aggregation queries | 2 | 3 | Low (6) | DB Admin | Materialized views, query optimization, caching layer | ✅ Mitigated |
| TR-012 | Mobile app crash on specific Android/iOS versions | 3 | 2 | Low (6) | Mobile | Crashlytics monitoring, device-lab testing, hotfix capability | ✅ Mitigated |
| TR-013 | Device bridge ASTM parsing error for non-standard instruments | 3 | 3 | Medium (9) | Device | Configurable instrument profiles, validation layer, manual override | ✅ Mitigated |
| TR-014 | CDN cache invalidation delay after deployment | 2 | 2 | Low (4) | Ops | Versioned asset URLs, immediate invalidation, index.html no-cache | ✅ Mitigated |
| TR-015 | Dependency supply chain attack (npm/PyPI) | 1 | 5 | Medium (5) | Security | Lock files, dependency audit, SCA scanning, minimal dependencies | ✅ Mitigated |
| TR-016 | AI model serving latency spike under concurrent requests | 2 | 3 | Low (6) | AI | Auto-scaling, request queuing, priority scheduling | ✅ Mitigated |
| TR-017 | Vector database query performance degradation | 2 | 3 | Low (6) | AI | Index optimization, caching, horizontal scaling | ✅ Mitigated |
| TR-018 | Cross-region replication bandwidth limits | 1 | 3 | Low (3) | Platform | Compression, differential sync, async replication | ✅ Mitigated |

---

## 3. Security Risks

| ID | Risk Description | Likelihood | Impact | Level | Owner | Mitigation | Status |
|----|-----------------|------------|--------|-------|-------|------------|--------|
| SR-001 | Unauthorized cross-tenant data access (IDOR) | 2 | 5 | Medium (10) | Security | lab_id filter enforcement, authorization middleware | ✅ Mitigated |
| SR-002 | JWT token theft via XSS | 1 | 5 | Medium (5) | Security | CSP, HttpOnly cookies, short token expiry (15 min) | ✅ Mitigated |
| SR-003 | SQL injection via unsanitized input | 1 | 5 | Medium (5) | Backend | Parameterized queries, ORM, input validation, WAF | ✅ Mitigated |
| SR-004 | Brute force attack on login endpoint | 3 | 2 | Low (6) | Security | Rate limiting, account lockout, MFA enforcement | ✅ Mitigated |
| SR-005 | Man-in-the-middle attack on API traffic | 1 | 5 | Medium (5) | Security | TLS 1.3 mandatory, HSTS, certificate pinning (mobile) | ✅ Mitigated |
| SR-006 | Privilege escalation via role manipulation | 1 | 4 | Low (4) | Security | Server-side authorization, signed tokens, audit logging | ✅ Mitigated |
| SR-007 | Insecure direct object reference on file uploads | 2 | 3 | Low (6) | Backend | Presigned URLs, path validation, MIME type checking | ✅ Mitigated |
| SR-008 | Session fixation via URL parameter | 1 | 3 | Low (3) | Security | Server-generated session IDs, regenerate on login | ✅ Mitigated |
| SR-009 | Prompt injection in citizen AI health assistant | 3 | 3 | Medium (9) | AI | Template isolation, input sanitization, output guardrails | ✅ Mitigated |
| SR-010 | Model inversion attack on clinical AI | 1 | 4 | Low (4) | AI | Differential privacy, data minimization, access controls | ✅ Mitigated |
| SR-011 | Bias in AI predictions leading to unequal care | 2 | 4 | Medium (8) | AI | Bias detector, fairness tests, regular monitoring | ✅ Mitigated |
| SR-012 | Secrets exposure in CI/CD logs | 2 | 4 | Medium (8) | Security | Secret masking, env variable hygiene, git-secrets scanning | ✅ Mitigated |

---

## 4. Operational Risks

| ID | Risk Description | Likelihood | Impact | Level | Owner | Mitigation | Status |
|----|-----------------|------------|--------|-------|-------|------------|--------|
| OR-001 | Insufficient on-call coverage during initial rollout | 3 | 3 | Medium (9) | Ops | 24/7 rotation, escalation path, secondary on-call | ✅ Mitigated |
| OR-002 | Slow incident response due to missing runbooks | 2 | 4 | Medium (8) | Ops | Documented runbooks, automated playbooks, chaos engineering | ✅ Mitigated |
| OR-003 | Backup restore failure during actual disaster | 2 | 5 | Medium (10) | DB Admin | Monthly restore drills, verification automation | ✅ Mitigated |
| OR-004 | Capacity underestimation during rapid user growth | 3 | 3 | Medium (9) | Platform | Auto-scaling, capacity planning reviews, growth projections | ✅ Mitigated |
| OR-005 | Staff turnover in key operational roles | 2 | 3 | Low (6) | HR | Knowledge base, pair operations, documentation | ✅ Mitigated |
| OR-006 | Internet connectivity loss at healthcare facilities | 3 | 3 | Medium (9) | Ops | Offline mode, sync queue, local caching | ✅ Mitigated |
| OR-007 | Power outage at deployment site | 2 | 3 | Low (6) | Facility | UPS, generator backup, DR failover | ✅ Mitigated |
| OR-008 | Third-party API dependency downtime (Firebase, SMS) | 2 | 3 | Low (6) | Backend | Fallback auth (OTP bypass codes), multi-provider SMS | ✅ Mitigated |
| OR-009 | Log storage exceeding retention budget | 3 | 2 | Low (6) | Ops | Log rotation, compression, tiered storage (Loki/S3) | ✅ Mitigated |
| OR-010 | Alert fatigue from monitoring system | 3 | 2 | Low (6) | Ops | Alert deduplication, severity tuning, silence rules | ✅ Mitigated |
| OR-011 | Configuration drift between environments | 3 | 3 | Medium (9) | Platform | Infrastructure as Code, config validation in CI, drift detection | ✅ Mitigated |
| OR-012 | Vendor lock-in with cloud provider | 2 | 3 | Low (6) | Platform | Multi-cloud strategy under evaluation, containerization | ✅ Mitigated |
| OR-013 | FHIR/HL7 standard version upgrades | 2 | 2 | Low (4) | Backend | Adapter pattern, version negotiation, 12-month migration window | ✅ Mitigated |
| OR-014 | Regulatory requirement changes during rollout | 2 | 3 | Low (6) | Legal | Regular compliance reviews, flexible configuration, feature flags | ✅ Mitigated |

---

## 5. Clinical Risks

| ID | Risk Description | Likelihood | Impact | Level | Owner | Mitigation | Status |
|----|-----------------|------------|--------|-------|-------|------------|--------|
| CR-001 | Wrong patient identification leading to incorrect treatment | 1 | 5 | Medium (5) | Clinical | Multi-factor ID (QR + DOB + national ID), positive patient ID | ✅ Mitigated |
| CR-002 | Delayed critical value notification | 2 | 5 | Medium (10) | Clinical | Escalating alerts (5/15/30/60 min), phone call fallback | ✅ Mitigated |
| CR-003 | Clinical pathway suggestion leading to suboptimal care | 2 | 3 | Low (6) | Clinical | Physician always decides, evidence-based pathways, override logging | ✅ Mitigated |
| CR-004 | Drug interaction alert ignored due to alert fatigue | 3 | 4 | Medium (12) | Clinical | Severity-graded alerts, mandatory acknowledgment for critical | ✅ Mitigated |
| CR-005 | Incorrect reference range applied to lab result | 1 | 4 | Low (4) | Clinical | Population-validated ranges, age/gender adjustment, pathologist review | ✅ Mitigated |
| CR-006 | Data entry error in medication dose | 2 | 4 | Medium (8) | Clinical | Dose range checking, confirmation dialog, pharmacist verification | ✅ Mitigated |
| CR-007 | Patient allergic reaction to prescribed medication | 1 | 5 | Medium (5) | Clinical | Allergy field on patient record, drug-allergy checking on every Rx | ✅ Mitigated |
| CR-008 | Lab sample mislabeling | 2 | 4 | Medium (8) | Lab | Barcode labeling, 2-identifier verification, chain of custody | ✅ Mitigated |

---

## 6. Risk Trends

| Month | Total Risks | High | Medium | Low | Risks Closed | New Risks |
|-------|-------------|------|--------|-----|--------------|-----------|
| May 2026 | 38 | 5 | 18 | 15 | 0 | 38 |
| June 2026 | 42 | 2 | 15 | 25 | 8 | 12 |
| July 2026 | 44 | 0 | 12 | 32 | 18 | 6 |
| **Target** | — | **0** | **< 10** | — | — | — |

---

## 7. Risk Acceptance

The following residual risks are formally accepted by the Program Director:

| ID | Risk | Accepted By | Date | Rationale |
|----|------|-------------|------|-----------|
| OR-001 | Insufficient on-call coverage | Ops Lead | 2026-07-15 | Temporary until full team hired (Q4 2026) |
| CR-004 | Alert fatigue | Clinical Lead | 2026-07-15 | Mitigated by severity-graded alerts, acceptable threshold of 2.3/100 |
| TR-011 | Slow national aggregation | Tech Lead | 2026-07-15 | Acceptable P95 of 500ms for complex queries |
| TR-016 | AI latency spikes | AI Lead | 2026-07-15 | Rare under current load, auto-scaling mitigates |

---

## 8. Risk Review Schedule

| Review Type | Frequency | Participants |
|-------------|-----------|-------------|
| Risk owner review | Weekly | Individual risk owners |
| Technical risk review | Bi-weekly | Tech Lead + Platform Lead |
| Security risk review | Bi-weekly | Security Lead |
| Clinical risk review | Monthly | Clinical Safety Committee |
| Full register review | Monthly | All risk owners + Program Director |
| Board risk review | Quarterly | Steering Committee |
