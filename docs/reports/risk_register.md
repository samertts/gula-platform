# GULA Risk Register

**Version:** 1.0  
**Date:** 2026-07-18  
**Classification:** INTERNAL  

---

## Risk Assessment Matrix

| Likelihood \ Impact | Minimal | Moderate | Significant | Severe |
|--------------------|---------|----------|-------------|--------|
| Almost Certain | Medium | High | **Critical** | **Critical** |
| Likely | Medium | High | **Critical** | **Critical** |
| Possible | Low | Medium | High | High |
| Unlikely | Low | Low | Medium | High |

---

## Architecture Risks

| ID | Risk | Likelihood | Impact | Level | Mitigation | Owner |
|----|------|-----------|--------|-------|-----------|-------|
| AR-01 | Architectural drift makes future changes prohibitively expensive | Likely | Significant | **Critical** | Establish Architecture Board, enforce module boundaries, consolidate to 15-25 modules | Architecture |
| AR-02 | Dual Kernel/legacy systems diverge beyond reconciliation | Possible | Severe | High | Define migration plan to unified architecture; deprecate one system | Architecture |
| AR-03 | main.py continues growing beyond 2,000 lines | Almost Certain | Moderate | High | Extract lifecycle, middleware, routing modules | Architecture |
| AR-04 | New developers struggle with 70 top-level package layout | Likely | Moderate | High | Consolidate module structure, improve documentation | Engineering |
| AR-05 | Memory growth in kernel/background tasks over long uptime | Possible | Significant | High | Implement memory monitoring, auto-restart thresholds | Engineering |
| AR-06 | Import-time failures in 50+ route modules cause hard crashes | Likely | Moderate | High | Implement graceful import error handling, startup verification | Engineering |

## Security Risks

| ID | Risk | Likelihood | Impact | Level | Mitigation | Owner |
|----|------|-----------|--------|-------|-----------|-------|
| SR-01 | Patient data breach through misconfigured tenant isolation | Unlikely | Severe | High | Enforce `lab_id` filter in all queries; audit trails; pen testing | Security |
| SR-02 | AI prompt injection leads to unauthorized clinical action | Possible | Significant | High | Guardrails, sandbox, blocked operations, output validation | AI |
| SR-03 | Supply chain attack through compromised dependency | Possible | Significant | High | Dependabot, SBOM, CVE scanning, lockfiles, review process | Security |
| SR-04 | Secrets leaked through logs or error messages | Unlikely | Moderate | Low | Secrets scrubbing in logging, error response sanitization | Security |
| SR-05 | JWT token theft leads to unauthorized access | Possible | Significant | High | Short TTL (15 min), refresh rotation, blacklist, anomaly detection | Security |
| SR-06 | Rate limiting bypass through distributed attack | Possible | Moderate | Medium | Multiple rate limit layers (nginx + app), IP blocklist, WAF | Security |
| SR-07 | Inadequate RBAC configuration leads to privilege escalation | Unlikely | Significant | Medium | Permission version O(1) check, regular ACL audits | Security |

## AI Risks

| ID | Risk | Likelihood | Impact | Level | Mitigation | Owner |
|----|------|-----------|--------|-------|-----------|-------|
| AR-01 | AI hallucination leads to clinical misdiagnosis | Possible | Severe | **Critical** | Guardrails, human review, sandbox, evaluation framework | AI |
| AR-02 | Provider API outage breaks clinical AI features | Likely | Significant | High | Multi-provider failover, local-first priority, offline fallback | AI |
| AR-03 | PII leakage through AI model output | Possible | Severe | High | PII protection (8 types), output validation, audit | AI |
| AR-04 | AI cost overrun from uncontrolled token usage | Likely | Moderate | High | Budget tracking, cost-optimized routing, caching, rate limiting | Operations |
| AR-05 | Model bias leads to unequal care | Unlikely | Significant | Medium | Bias evaluation framework, diverse demographic testing | AI |
| AR-06 | Vector store (in-memory) data loss on restart | Almost Certain | Moderate | Medium | Connect pgvector/Qdrant for persistent storage | AI |

## Healthcare Risks

| ID | Risk | Likelihood | Impact | Level | Mitigation | Owner |
|----|------|-----------|--------|-------|-----------|-------|
| HR-01 | Critical value alert not delivered due to system failure | Unlikely | Severe | High | Multiple alert channels, acknowledgment workflow, escalation chain | Healthcare |
| HR-02 | Patient data access by wrong lab (tenant isolation failure) | Unlikely | Severe | High | `lab_id` filter on all queries, audit trails, cross-lab access tests | Security |
| HR-03 | FHIR interoperability failure with national systems | Possible | Significant | High | FHIR compliance testing, contract enforcement | Interop |
| HR-04 | Result data loss due to optimistic lock failure | Unlikely | Significant | Medium | Optimistic lock with retry, version conflict resolution | Engineering |
| HR-05 | Terminology mapping error leads to incorrect clinical decision | Possible | Significant | High | Clinical Board review of mappings, validation testing | Healthcare |
| HR-06 | Offline sync conflict leads to data inconsistency | Possible | Moderate | Medium | Conflict resolution strategy, last-write-wins with logging | Edge |

## Infrastructure Risks

| ID | Risk | Likelihood | Impact | Level | Mitigation | Owner |
|----|------|-----------|--------|-------|-----------|-------|
| IR-01 | Database failure causes full platform outage | Possible | Severe | High | Circuit breaker, degraded mode, read replicas, DR failover | Infrastructure |
| IR-02 | Container resource exhaustion under peak load | Possible | Significant | High | Resource limits, HPA, adaptive concurrency, concurrency limit middleware | Infrastructure |
| IR-03 | Backup corruption leads to unrecoverable data loss | Unlikely | Severe | High | SHA-256 verification, restore testing, cross-region replication | Infrastructure |
| IR-04 | CDN/edge service outage breaks frontend delivery | Possible | Moderate | Medium | Multi-CDN strategy, offline PWA fallback | Infrastructure |
| IR-05 | Deployment failure causes extended downtime | Possible | Significant | High | Blue-green deployment, auto-rollback, smoke tests | DevOps |

## Operational Risks

| ID | Risk | Likelihood | Impact | Level | Mitigation | Owner |
|----|------|-----------|--------|-------|-----------|-------|
| OR-01 | Insufficient on-call coverage for 24/7 healthcare | Likely | Significant | High | Define on-call rotation, escalation paths, runbooks | Operations |
| OR-02 | Runbook not updated after infrastructure change | Likely | Moderate | High | Documentation gate in change process, quarterly audits | Operations |
| OR-03 | Database migration fails in production | Possible | Significant | High | Migration round-trip CI testing, rollback plan, deploy lock | Engineering |
| OR-04 | Insufficient monitoring of new features | Likely | Moderate | Medium | Observability gate in PR review, auto-generated dashboards | Observability |

## Compliance Risks

| ID | Risk | Likelihood | Impact | Level | Mitigation | Owner |
|----|------|-----------|--------|-------|-----------|-------|
| CR-01 | Non-compliance with Iraqi health data regulations | Possible | Severe | High | Legal review, compliance baseline, audit trails | Legal |
| CR-02 | Patient consent not properly managed for data sharing | Possible | Significant | High | Consent management system, consent audit | Healthcare |
| CR-03 | Data retention policy not enforced | Possible | Moderate | Medium | Automated retention enforcement, periodic audits | Data Governance |
| CR-04 | No formal ISO certification (27001, 15189) | Likely | Moderate | Medium | Compliance roadmap, gap analysis, certification plan | Compliance |

## Business Risks

| ID | Risk | Likelihood | Impact | Level | Mitigation | Owner |
|----|------|-----------|--------|-------|-----------|-------|
| BR-01 | Single-customer dependency (one large lab) | Possible | Significant | High | Diversify customer base, marketplace strategy | Product |
| BR-02 | No monetization strategy for AI capabilities | Likely | Moderate | Medium | Subscription tiers, usage-based AI pricing | Product |
| BR-03 | Open source competitor emerges | Possible | Moderate | Medium | Maintain quality lead, community building, sovereign positioning | Product |
| BR-04 | Talent retention in specialized domains (AI, healthcare) | Likely | Moderate | Medium | Knowledge documentation, training programs, succession planning | Operations |

## Top 10 Risks by Criticality

| Rank | ID | Risk | Level | Mitigation |
|------|----|------|-------|-----------|
| 1 | HR-01 | Critical alert delivery failure | Critical | Multi-channel alerts, ack workflow, escalation |
| 2 | AR-01 | AI hallucination in clinical context | Critical | Guardrails, HITL, sandbox, evaluation |
| 3 | AR-01 | Architectural drift | Critical | Board, enforcement, consolidation |
| 4 | HR-02 | Tenant isolation failure | Critical | Lab_id filter, audit, cross-lab tests |
| 5 | IR-01 | Database failure outage | Critical | Circuit breaker, degraded mode, DR |
| 6 | AR-02 | AI Provider outage | High | Multi-provider failover, local-first |
| 7 | AR-03 | PII leakage through AI | High | PII protection, output validation |
| 8 | OR-01 | Insufficient 24/7 coverage | High | On-call rotation, runbooks, escalation |
| 9 | CR-01 | Regulatory non-compliance | High | Legal review, compliance program |
| 10 | IR-03 | Backup corruption | High | Verification, restore testing, replication |

---

*This risk register is a living document. Risks should be reviewed and updated quarterly by the Architecture Board.*
