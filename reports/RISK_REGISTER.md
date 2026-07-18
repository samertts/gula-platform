# GULA PLATFORM — COMPLETE RISK REGISTER

**Status:** VERIFIED (from audit evidence) + PROPOSED (mitigations)
**Date:** 2026-07-17

---

## RISK SCORING METHODOLOGY

| Dimension | Score | Definition |
|-----------|-------|------------|
| Likelihood | 1-5 | 1=Rare, 2=Unlikely, 3=Possible, 4=Likely, 5=Almost Certain |
| Impact | 1-5 | 1=Negligible, 2=Minor, 3=Moderate, 4=Major, 5=Catastrophic |
| Risk Score | L×I | 1-25 |

---

## TECHNICAL RISKS

| ID | Risk | Likelihood | Impact | Score | Mitigation |
|----|------|-----------|--------|-------|------------|
| T-01 | **Database schema/ORM drift** — 70% of tables have no ORM model | 4 | 4 | **16** | Add ORM models for all tables, auto-generation from migrations |
| T-02 | **Microservices not production-ready** — 8 single-file stubs, no tests, deprecated patterns | 4 | 3 | **12** | Refactor using lifespan pattern, add tests, proper packaging |
| T-03 | **Monolith scope explosion** — 60+ subdirectories with unclear operational status | 4 | 3 | **12** | Document each module's status (stub/prototype/production), enforce modular boundaries |
| T-04 | **No automated secret rotation** — Keys unchanged after initial deployment | 3 | 5 | **15** | Implement rotation endpoints, automated 90-day rotation |
| T-05 | **Rate limiting fails open** — Redis unavailability bypasses rate limiting | 3 | 4 | **12** | Add local in-memory fallback with reduced capacity |
| T-06 | **External AI provider calls in codebase** — ai/ai_service.py and ai_agent.py | 3 | 4 | **12** | Remove or gate behind explicit configuration |
| T-07 | **Integration connectors untested** — 20+ connectors with 0 tests | 4 | 3 | **12** | Add smoke tests for all connectors |
| T-08 | **services/shared/ dead code** — Not imported, maintenance burden | 5 | 1 | **5** | Remove deprecated bridge files |
| T-09 | **No CSRF protection** — Browser clients vulnerable to CSRF | 2 | 4 | **8** | Add Double Submit Cookie middleware |
| T-10 | **No coverage threshold in CI** — Tests can degrade over time | 4 | 2 | **8** | Enforce 80% minimum coverage |

---

## SECURITY RISKS

| ID | Risk | Likelihood | Impact | Score | Mitigation |
|----|------|-----------|--------|-------|------------|
| S-01 | **No LICENSE file** — Unclear legal status for all users and contributors | 5 | 5 | **25** | **IMMEDIATE:** Add AGPL v3 LICENSE file |
| S-02 | **Contradictory license claims** — MIT vs Proprietary creates legal ambiguity | 5 | 5 | **25** | **IMMEDIATE:** Resolve to single license |
| S-03 | **Session revocation fails open** — Redis down = revoked tokens accepted | 3 | 4 | **12** | Short JWT expiry (5min), local blacklist cache |
| S-04 | **OAuth2 no key rotation** — Long-lived signing keys without rotation | 3 | 4 | **12** | Automated key rotation with key overlap period |
| S-05 | **Secrets in .env on disk** — Developer workstation risk | 3 | 3 | **9** | Pre-commit hook warning, education |
| S-06 | **Push notification VAPID not configured** — Feature non-functional | 4 | 1 | **4** | Generate VAPID keys, add to config |
| S-07 | **Weak secret pattern detection incomplete** — May miss modern weak secrets | 2 | 3 | **6** | Add entropy measurement, expand pattern list |
| S-08 | **Security headers minor issue** — x-content-type-options value incorrect | 4 | 1 | **4** | Fix header value format |

---

## FINANCIAL RISKS

| ID | Risk | Likelihood | Impact | Score | Mitigation |
|----|------|-----------|--------|-------|------------|
| F-01 | **No revenue** — Platform is in pre-revenue/pre-commercial phase | 4 | 5 | **20** | Start Enterprise Edition sales immediately |
| F-02 | **Over-reliance on government contracts** — Revenue concentration | 3 | 4 | **12** | Diversify into SaaS, marketplace, training |
| F-03 | **Underpricing** — Current $199/mo starter may be too low for value | 2 | 3 | **6** | Market research, value-based pricing |
| F-04 | **Development cost exceeds revenue** — 40-person team burn rate | 4 | 4 | **16** | Seed funding, phased hiring, efficient operations |
| F-05 | **Currency fluctuation (IQD/USD)** — Iraqi market exposure | 3 | 3 | **9** | USD pricing, local hedging |

---

## OPERATIONAL RISKS

| ID | Risk | Likelihood | Impact | Score | Mitigation |
|----|------|-----------|--------|-------|------------|
| O-01 | **Single person dependency** — Founder/BDFL has most context | 4 | 5 | **20** | Documentation, knowledge transfer, code review requirements |
| O-02 | **No dedicated DevOps/SRE** — Operations handled ad-hoc | 4 | 4 | **16** | Hire DevOps engineer, create runbooks |
| O-03 | **Documentation outdated** — 60+ sub-platforms undocumented | 5 | 3 | **15** | Automated documentation generation, ADRs |
| O-04 | **No incident response process** — No PagerDuty/Opsgenie equivalent | 3 | 4 | **12** | Define IR process, implement alerting |
| O-05 | **Backup/DR not regularly tested** — Scripts exist but untested | 4 | 4 | **16** | Monthly DR drill, automated restore testing |

---

## CLINICAL RISKS

| ID | Risk | Likelihood | Impact | Score | Mitigation |
|----|------|-----------|--------|-------|------------|
| C-01 | **AI hallucination in clinical context** — Misinterpretation of lab results | 2 | 5 | **10** | Confidence scoring, human-in-the-loop, disclaimers |
| C-02 | **Data integrity failure** — Result corruption or loss | 1 | 5 | **5** | Optimistic locking, audit chain, transaction outbox |
| C-03 | **Tenant isolation breach** — One lab sees another lab's patient data | 1 | 5 | **5** | Verified: lab_id filtering on all queries |
| C-04 | **Clinical workflow gap** — Missing critical workflow step | 3 | 3 | **9** | Clinical workflow audit, subject matter expert review |
| C-05 | **Regulatory non-compliance** — Non-compliance with local health regulations | 2 | 4 | **8** | Country-specific compliance modules, legal review |

---

## LEGAL RISKS

| ID | Risk | Likelihood | Impact | Score | Mitigation |
|----|------|-----------|--------|-------|------------|
| L-01 | **License ambiguity** — No LICENSE file, contradictory metadata | 5 | 5 | **25** | **IMMEDIATE:** Add AGPL v3, fix metadata |
| L-02 | **Copyright infringement** — Third-party code without proper attribution | 3 | 4 | **12** | Dependency audit, SBOM generation |
| L-03 | **Trademark infringement** — Domain squatting, fake GULA versions | 3 | 3 | **9** | Register trademark proactively |
| L-04 | **Export control violation** — Healthcare technology in sanctioned countries | 2 | 5 | **10** | Export classification, compliance screening |
| L-05 | **GDPR non-compliance** — EU user data without proper safeguards | 3 | 4 | **12** | GDPR compliance project (Phase 2) |
| L-06 | **HIPAA violation** — US patient data without BAAs | 2 | 5 | **10** | HIPAA compliance assessment (Phase 3) |

---

## BUSINESS RISKS

| ID | Risk | Likelihood | Impact | Score | Mitigation |
|----|------|-----------|--------|-------|------------|
| B-01 | **Open source competitor emerges** — Fork or new project | 4 | 4 | **16** | Maintain technical lead, community, ecosystem |
| B-02 | **Government adoption stalls** — Bureaucracy, budget cycles | 4 | 3 | **12** | Cultivate multiple gov contracts simultaneously |
| B-03 | **Talent retention** — Key engineers leave | 3 | 4 | **12** | Competitive comp, equity, remote options, mission |
| B-04 | **Market timing** — Too early or too late for market | 3 | 3 | **9** | Validate with early customers, iterate quickly |
| B-05 | **Partner dependency** — Over-reliance on implementation partners | 2 | 3 | **6** | Build internal services team, multiple partners |

---

## INFRASTRUCTURE RISKS

| ID | Risk | Likelihood | Impact | Score | Mitigation |
|----|------|-----------|--------|-------|------------|
| I-01 | **Single cloud provider dependency** — All infra on one provider | 3 | 4 | **12** | Multi-cloud strategy, Kubernetes portability |
| I-02 | **Docker Compose at production scale** — Not designed for production orchestration | 4 | 3 | **12** | Migration to Kubernetes (in progress) |
| I-03 | **Disaster recovery not tested** — DR scripts but no regular drills | 4 | 4 | **16** | Monthly DR drills, automated restore testing |
| I-04 | **No traffic shadowing** — Canary deployments exist but no traffic shadow | 3 | 2 | **6** | Add traffic shadow for pre-production validation |
| I-05 | **Database backup verification missing** — Backups taken but not verified | 4 | 4 | **16** | Automated restore testing after every backup |

---

## ORGANIZATIONAL RISKS

| ID | Risk | Likelihood | Impact | Score | Mitigation |
|----|------|-----------|--------|-------|------------|
| G-01 | **No formal entity** — Project has no legal entity for contracts/payments | 5 | 5 | **25** | **CRITICAL:** Incorporate entity in Iraq or UAE |
| G-02 | **Single point of failure** — Founder/lead has all context | 4 | 5 | **20** | Documentation, delegation, team redundancy |
| G-03 | **No board/advisors** — No strategic guidance or governance | 4 | 3 | **12** | Form advisory board (technical + business + clinical) |
| G-04 | **Decision process unclear** — Ad-hoc decision making | 3 | 3 | **9** | RACI matrix, ADR process, decision log |

---

## COMMUNITY RISKS

| ID | Risk | Likelihood | Impact | Score | Mitigation |
|----|------|-----------|--------|-------|------------|
| M-01 | **Toxic community** — Negative culture drives away contributors | 2 | 3 | **6** | Code of Conduct, active moderation |
| M-02 | **Low contribution volume** — Community doesn't engage | 4 | 3 | **12** | Good first issues, contributing guides, mentorship |
| M-03 | **Burnout of maintainers** — Core team overwhelmed | 3 | 4 | **12** | Multiple maintainers, automated processes, clear boundaries |
| M-04 | **Fork fragmentation** — Community splits across multiple forks | 2 | 3 | **6** | Strong brand, trademark enforcement, federation |

---

## TOP 10 RISKS BY SCORE

| Rank | ID | Risk | Score | Category |
|------|----|------|-------|----------|
| 1 | S-01 | No LICENSE file | **25** | Security/Legal |
| 2 | S-02 | Contradictory license claims | **25** | Security/Legal |
| 3 | G-01 | No legal entity | **25** | Organizational |
| 4 | F-01 | No revenue | **20** | Financial |
| 5 | O-01 | Single person dependency | **20** | Operational |
| 6 | T-01 | Schema/ORM drift | **16** | Technical |
| 7 | O-05 | Backup/DR not tested | **16** | Operational |
| 8 | I-05 | Backup verification missing | **16** | Infrastructure |
| 9 | I-03 | DR not tested | **16** | Infrastructure |
| 10 | B-01 | Open source competitor | **16** | Business |

---

## RISK TREATMENT PLAN

| Priority | Risk | Treatment | Cost | Timeline |
|----------|------|-----------|------|----------|
| **P0** | No LICENSE file | Avoid: Add AGPL v3 | $0 | Week 1 |
| **P0** | Contradictory license | Fix: Unify metadata | $0 | Week 1 |
| **P0** | No legal entity | Transfer: Incorporate | $2-5K | Month 1 |
| **P1** | Schema/ORM drift | Reduce: Auto-generate ORM | $10-20K | Month 2-3 |
| **P1** | No revenue | Accept/Mitigate: Start sales | $0 | Immediate |
| **P1** | Single person dependency | Reduce: Documentation, hiring | $50-100K | Month 3-6 |
| **P1** | DR/Backup not tested | Reduce: Monthly drills | $5-10K | Month 1 |
| **P2** | Microservices not ready | Reduce: Refactor | $20-40K | Month 3-6 |
| **P2** | OAuth2 key rotation | Reduce: Implement rotation | $10-20K | Month 2-3 |
| **P2** | Rate limit fails open | Reduce: Local fallback | $5-10K | Month 1-2 |
| **P3** | All other risks | Monitor/Accept | Per item | Ongoing |
