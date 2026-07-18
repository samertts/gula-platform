# GULA Platform — Enterprise Risk Register

**Classification:** CONFIDENTIAL
**Date:** 2026-07-18
**Risk Scoring:** Likelihood (1-5) × Impact (1-5) = Risk Score (1-25)

---

## Risk Scoring Definitions

| Dimension | 1 | 2 | 3 | 4 | 5 |
|-----------|---|---|---|---|---|
| Likelihood | Rare | Unlikely | Possible | Likely | Almost Certain |
| Impact | Negligible | Minor | Moderate | Major | Catastrophic |

---

## Critical Risks (Score 20-25)

| Risk ID | Category | Risk Description | L | I | Score | Mitigation | Owner |
|---------|----------|-----------------|---|---|-------|-----------|-------|
| R-001 | Security | Firebase bypasses backend security — frontend-v2 writes directly to Firestore, bypassing RBAC, ABAC, audit, rate limiting, encryption | 5 | 5 | **25** | Lockdown Firestore to admin-only; proxy all data requests through backend API | Security Lead |
| R-002 | Legal | No LICENSE file — zero legal clarity for users and contributors | 5 | 5 | **25** | Add AGPL v3 LICENSE file | Legal |
| R-003 | Legal | Contradictory license claims — MIT vs Proprietary metadata creates legal ambiguity | 5 | 5 | **25** | Resolve to single license throughout repository | Legal |
| R-004 | Organizational | No legal entity — cannot sign contracts, accept payments, or limit liability | 5 | 5 | **25** | Incorporate entity in Iraq or UAE | Founder |
| R-005 | Security | Patient data exposure via Firebase — PHI flows through Firestore outside backend security controls | 4 | 5 | **20** | Immediate Firestore lockdown; full data flow audit | Security Lead |
| R-006 | Infrastructure | No backup restore testing — backups configured but never verified for integrity | 4 | 5 | **20** | Weekly automated restore testing with integrity verification | DevOps |
| R-007 | Compliance | AI provider regulatory violations — Executive Orders 3&4 mandate Ollama-only; Gemini + Groq in production code | 5 | 4 | **20** | Remove external AI providers or formally update EOs with privacy guardrails | AI Team Lead |
| R-008 | Financial | No revenue — platform is pre-revenue/pre-commercial | 4 | 5 | **20** | Start Enterprise Edition sales immediately; incorporate legal entity | Founder/CEO |
| R-009 | Operational | Single person dependency — founder/BDFL has most context; no succession plan | 4 | 5 | **20** | Documentation, knowledge transfer, code review requirements, hiring | Founder |

---

## High Risks (Score 15-19)

| Risk ID | Category | Risk Description | L | I | Score | Mitigation | Owner |
|---------|----------|-----------------|---|---|-------|-----------|-------|
| R-010 | Technical | Schema/ORM drift — 70% of tables have no ORM model; risk of silent schema divergence | 4 | 4 | **16** | Auto-generate ORM models from migrations | Backend Team |
| R-011 | Operational | DR/Backup not tested — DR scripts exist but no regular drills | 4 | 4 | **16** | Monthly DR drills, automated restore testing | DevOps |
| R-012 | Business | Open source competitor emerges — fork or new project | 4 | 4 | **16** | Maintain technical lead, community, ecosystem | Product |
| R-013 | Financial | Development cost exceeds revenue — 40-person team burn rate without revenue | 4 | 4 | **16** | Seed funding, phased hiring, efficient operations | Founder/CEO |
| R-014 | Operational | No dedicated DevOps/SRE — operations handled ad-hoc | 4 | 4 | **16** | Hire DevOps engineer, create runbooks | Founder |
| R-015 | Security | External AI provider PHI exposure — patient data sent to OpenAI, Google, DeepSeek | 3 | 5 | **15** | Remove external providers; enforce local-only AI | AI Team Lead |
| R-016 | Technical | No automated secret rotation — all keys unchanged since deployment | 3 | 5 | **15** | Implement rotation endpoints, automated 90-day rotation | Security Lead |
| R-017 | Infrastructure | Single PostgreSQL instance — no HA in production; any PG failure = complete outage | 3 | 5 | **15** | Deploy Patroni + PgBouncer + read replicas | DevOps |
| R-018 | Operational | Documentation outdated — 60+ sub-platforms undocumented; 36 vs 53+ route count | 5 | 3 | **15** | Automated documentation generation, update CLAUDE.md | Platform Engineering |
| R-019 | Technical | Version tracking inconsistency — 2.1.0 / 2.2.0 / 2.3.2 across repo | 4 | 3 | **12** | Unify to single version source; config.py as source of truth | DevOps |

---

## Medium Risks (Score 10-14)

| Risk ID | Category | Risk Description | L | I | Score | Mitigation | Owner |
|---------|----------|-----------------|---|---|-------|-----------|-------|
| R-020 | Quality | Low route test coverage (35%) — most route modules untested | 4 | 3 | **12** | Prioritize route test coverage to 60%+ | Quality Engineering |
| R-021 | Quality | Low service test coverage (30%) — core business logic under-tested | 4 | 3 | **12** | Add integration tests for critical service paths | Quality Engineering |
| R-022 | Quality | Zero edge/interop test coverage — edge platform untested | 3 | 4 | **12** | Add edge platform smoke tests | Quality Engineering |
| R-023 | Quality | 6 microservice stubs with 0 tests — cannot deploy as microservices | 3 | 4 | **12** | Implement or remove stubs; add tests | Platform Engineering |
| R-024 | Security | JWT uses HS256 — symmetric key distribution risk; no key rotation | 3 | 4 | **12** | Migrate to RS256/ES256 with JWKS endpoint | Security Lead |
| R-025 | Security | Rate limiting fails open — Redis unavailability bypasses all rate limits | 3 | 4 | **12** | Add local in-memory fallback with reduced capacity | Backend Team |
| R-026 | Security | Session revocation fails open — Redis down = revoked tokens accepted | 3 | 4 | **12** | Short JWT expiry (5min), local blacklist cache | Backend Team |
| R-027 | Infrastructure | No staging environment — changes deployed directly to production | 4 | 3 | **12** | Create staging environment mirroring production | DevOps |
| R-028 | Infrastructure | Terraform targets AWS, deployment on DigitalOcean — IaC mismatch | 4 | 3 | **12** | Re-target Terraform for DO or migrate to AWS | DevOps |
| R-029 | Quality | No E2E tests — no Playwright/Cypress for critical user journeys | 3 | 4 | **12** | Implement Playwright for 10-20 critical workflows | Quality Engineering |
| R-030 | Security | CSRF protection missing — browser clients vulnerable to cross-site requests | 2 | 4 | **8** | Add Double Submit Cookie middleware | Backend Team |
| R-031 | Business | Government adoption stalls — bureaucracy, budget cycles | 4 | 3 | **12** | Cultivate multiple gov contracts simultaneously | Business Development |
| R-032 | Compliance | Clinical CDS schema-only — no code executes CDS rules | 3 | 3 | **9** | Implement CDS rules engine | Clinical Engineering |

---

## Low Risks (Score 1-9)

| Risk ID | Category | Risk Description | L | I | Score | Mitigation | Owner |
|---------|----------|-----------------|---|---|-------|-----------|-------|
| R-033 | Technical | No DICOM server — radiology workflows incomplete | 2 | 3 | **6** | Deploy Orthanc/DCM4CHEE | Backend Team |
| R-034 | Quality | No load test baseline — performance regression undetectable | 3 | 2 | **6** | Capture and baseline k6 results | Quality Engineering |
| R-035 | Legal | GDPR non-compliance — EU user data without proper safeguards | 3 | 4 | **12** | GDPR compliance project (Phase 2) | Legal |
| R-036 | Legal | HIPAA violation — US patient data without BAAs | 2 | 5 | **10** | HIPAA compliance assessment (Phase 3) | Legal |
| R-037 | Technical | Massive schema churn (17 migrations in 1 day) — 200+ tables, no code | 4 | 3 | **12** | Freeze schema expansion until code catches up | Backend Team Lead |
| R-038 | Organizational | No board/advisors — no strategic guidance or governance | 4 | 3 | **12** | Form advisory board (technical + business + clinical) | Founder |
| R-039 | Security | No frontend security testing — XSS, DOM-based risks unknown | 3 | 4 | **12** | Add npm audit, ESLint security plugin, ZAP scan | Frontend Lead |
| R-040 | Community | Low contribution volume — community doesn't engage | 4 | 3 | **12** | Good first issues, contributing guides, mentorship | Community Manager |

---

## Top 10 Risks by Score

| Rank | ID | Risk | Score | Category |
|------|----|------|-------|----------|
| 1 | R-001 | Firebase security bypass | **25** | Security |
| 2 | R-002 | No LICENSE file | **25** | Legal |
| 3 | R-003 | Contradictory license claims | **25** | Legal |
| 4 | R-004 | No legal entity | **25** | Organizational |
| 5 | R-005 | Patient data exposure via Firebase | **20** | Security |
| 6 | R-006 | No backup restore testing | **20** | Infrastructure |
| 7 | R-007 | AI provider regulatory violations | **20** | Compliance |
| 8 | R-008 | No revenue | **20** | Financial |
| 9 | R-009 | Single person dependency | **20** | Operational |
| 10 | R-010 | Schema/ORM drift | **16** | Technical |

---

## Risk Distribution

| Severity | Count | Score Range |
|----------|-------|-------------|
| Critical | 9 | 20-25 |
| High | 9 | 15-19 |
| Medium | 14 | 10-14 |
| Low | 8 | 1-9 |
| **Total** | **40** | — |
