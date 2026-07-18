# Discovery Validation Report

**PROGRAM-02** | GULA Platform
**Date:** 2026-07-18 | **Status:** COMPLETE

Validates every major finding from PROGRAM-02 discovery phases against evidence across 11 source documents. Each finding is assigned confidence, impact, risk level, and priority.

## Source Documents

| ID | Document | Size |
|----|----------|------|
| S01 | `reports/discovery/13_GAP_ANALYSIS.md` | 5KB |
| S02 | `reports/discovery/14_CONTRADICTIONS.md` | 4KB |
| S03 | `reports/discovery/17_RISK_REGISTER.md` | 5KB |
| S04 | `reports/discovery/19_RECOMMENDATIONS.md` | 9KB |
| S05 | `docs/constitution/CONSTITUTION-VALIDATION-REPORT.md` | 6KB |
| S06 | `docs/engineering/TECHNICAL_DEBT_REGISTER.md` | 21KB |
| S07 | `docs/engineering/RISK-REGISTER.md` | 6KB |
| S08 | `docs/security/security_baseline.md` | 9KB |
| S09 | `reports/SECURITY_MASTER_REPORT.md` | 13KB |
| S10 | `reports/RISK_REGISTER.md` | 12KB |
| S11 | `reports/ARCHITECTURE_SNAPSHOT.md` | 10KB |

## Scoring Rubric

| Dimension | Range | Definition |
|-----------|-------|------------|
| Confidence | 1-5 | 5=verified by 3+ independent sources; 4=verified by 2 sources; 3=single source with corroboration; 2=single source; 1=unverified claim |
| Impact | 1-10 | 10=enterprise-wide outage/legal; 7-9=platform-critical; 4-6=feature-impacting; 1-3=cosmetic |
| Risk Level | Critical/High/Medium/Low | Cross-product of likelihood × severity |
| Priority | P0(24h)/P1(7d)/P2(30d)/P3(90d) | P0=immediate remediation; P1=this sprint; P2=this quarter; P3=next quarter |

---

## 1. Architecture Findings

| # | Finding | Evidence | Confidence | Impact | Business Value | Clinical Impact | Security Impact | Risk Level | Priority | Owner |
|---|---------|----------|-----------|--------|---------------|----------------|----------------|-----------|----------|-------|
| A01 | **Monolith scope explosion** — 60+ subdirectories, 221 app modules with unclear operational status; 200+ national platform tables with no routes | S01:13, S02:35-37, S10:24, S11:150 | 5 | 8 | 7 | 3 | 4 | High | P2 | Platform Engineering |
| A02 | **Route count documentation gap** — CLAUDE.md claims 36 routes; actual is 53+ routes; 46 routes in ARCHITECTURE_SNAPSHOT | S02:20-24, S11:68, S02:104 | 5 | 6 | 5 | 3 | 3 | Medium | P3 | Backend Team |
| A03 | **Architecture layer naming conflict** — CLAUDE.md uses 3-layer (routes→services→models); Platform Constitution mandates 4-layer (routes→services→domain→infrastructure); no ADR for the transition | S05:33-39 | 5 | 7 | 6 | 2 | 2 | Medium | P2 | Platform Engineering |
| A04 | **FHIR strategy ambiguity** — Engineering Constitution §14.1 mandates FHIR on all endpoints; Platform Constitution §3.3 says content-type on every endpoint; actual implementation is separate /fhir/ route | S05:46-52 | 5 | 6 | 7 | 5 | 2 | Medium | P2 | Backend Team Lead |
| A05 | **mTLS mandate vs HTTP comms** — Platform Constitution §4.3 mandates mTLS for all inter-service communication; docker-compose.yml uses plain HTTP; no ADR documenting the decision | S05:53-58 | 5 | 8 | 5 | 2 | 8 | High | P2 | Platform Engineering |
| A06 | **Monster route files** — ehr.py (73KB), compliance.py (47KB), clinical.py (41KB) violate clean-architecture principles | S02:36, S03:50-51, S04:105-108 | 5 | 5 | 4 | 3 | 2 | Medium | P3 | Backend Team |
| A07 | **No ADR for key architectural decisions** — No ADR for layer restructuring (G1), UUID migration (G2), mTLS exception (G4), FHIR strategy (G5), SBOM (G6) | S05:96-117 | 5 | 7 | 6 | 2 | 4 | High | P2 | Platform Engineering |
| A08 | **Docker Compose at production scale** — Not designed for production orchestration; single PG instance; no built-in HA | S10:116-117, S03:15-16, S01:85-87 | 5 | 8 | 7 | 5 | 5 | Critical | P1 | DevOps |
| A09 | **Microservice stubs vs monolith confusion** — 7 stubs in services/ create architecture direction ambiguity; 6/9 are stubs with 0 tests | S06:31-61, S03:34-35 | 5 | 4 | 3 | 1 | 1 | Low | P3 | Platform Engineering |
| A10 | **Backend dual structure** — backend/services/ and backend/core/ (both with api/ subdirs) duplicate backend/app/ equivalents | S06:65-91, S01:66-68 | 5 | 3 | 3 | 1 | 1 | Low | P3 | Backend Team Lead |

---

## 2. Security Findings

| # | Finding | Evidence | Confidence | Impact | Business Value | Clinical Impact | Security Impact | Risk Level | Priority | Owner |
|---|---------|----------|-----------|--------|---------------|----------------|----------------|-----------|----------|-------|
| S01 | **Firebase security bypass** — frontend-v2 writes directly to Firestore, bypassing RBAC, ABAC, audit logging, rate limiting, encryption | S03:17-20, S02:65-68, S03:17 | 5 | 10 | 9 | 9 | 10 | Critical | P0 | Security Lead |
| S02 | **No LICENSE file** — Zero license clarity; MIT vs Proprietary metadata contradiction creates legal ambiguity for users and contributors | S09:129-133, S10:149-150, S10:39-41 | 5 | 9 | 8 | 2 | 3 | Critical | P0 | Legal |
| S03 | **JWT uses HS256 (symmetric key)** — Key distribution risk across services; no key rotation possible | S01:27-28, S03:35-38, S08:31 | 5 | 8 | 6 | 5 | 8 | High | P1 | Security Lead |
| S04 | **No automated secrets rotation** — SECRET_KEY, ENCRYPTION_KEY, NID_HMAC_KEY, REFRESH_TOKEN_SECRET never rotated; rotate-keys.sh exists but is manual | S01:19, S03:36-38, S09:141-146, S10:25 | 5 | 9 | 8 | 7 | 9 | Critical | P1 | DevOps |
| S05 | **Rate limiting fails open** — When Redis is unavailable, rate limiting silently permits all requests | S09:147-152, S10:26-27, S09:117 | 5 | 8 | 5 | 4 | 8 | High | P1 | Backend Team |
| S06 | **Session revocation fails open** — JWT blacklist in Redis; revoked tokens accepted during Redis outages | S09:166-170, S10:41-42 | 5 | 7 | 4 | 4 | 7 | High | P2 | Backend Team |
| S07 | **CSRF protection missing** — No CSRF tokens for browser-based API clients; middleware stack lacks CSRF middleware | S09:153-158, S10:30-31 | 5 | 6 | 4 | 3 | 6 | Medium | P2 | Backend Team |
| S08 | **OAuth2 no key rotation** — Long-lived signing keys without rotation or key overlap period | S09:163-165, S10:42-43 | 4 | 7 | 5 | 4 | 7 | High | P2 | Security Lead |
| S09 | **Secrets in .env on disk** — Developer workstation risk; gitignored but physically present | S09:224, S10:44 | 4 | 4 | 3 | 3 | 4 | Medium | P3 | DevOps |
| S10 | **No frontend security testing** — XSS, CSRF, DOM-based risks unknown; no frontend security scan pipeline | S01:31, S03:38-39 | 4 | 6 | 5 | 4 | 6 | Medium | P2 | Frontend Lead |
| S11 | **Weak secret detection incomplete** — _WEAK_PATTERNS list may miss modern weak passwords; no entropy measurement | S09:194-199, S10:45-46 | 4 | 4 | 3 | 2 | 4 | Low | P3 | Security Lead |
| S12 | **Security headers minor issues** — x-content-type-options value incorrect format | S09:226, S10:47 | 4 | 2 | 1 | 1 | 2 | Low | P3 | Backend Team |
| S13 | **External AI provider data sovereignty risk** — top-level ai/ directory calls OpenAI, DeepSeek, Gemini directly; PHI could be exposed to external providers | S09:178-183, S02:42-48 | 5 | 8 | 6 | 7 | 8 | Critical | P1 | AI Team Lead |

---

## 3. Healthcare Findings

| # | Finding | Evidence | Confidence | Impact | Business Value | Clinical Impact | Security Impact | Risk Level | Priority | Owner |
|---|---------|----------|-----------|--------|---------------|----------------|----------------|-----------|----------|-------|
| H01 | **FHIR coverage minimal** — Only 6 FHIR resource types implemented out of 100+ in R4/R5; limits national interoperability | S01:70-71, S04:159-163 | 5 | 7 | 8 | 6 | 2 | Medium | P2 | Backend Team Lead |
| H02 | **HL7 v2.x limited to ASTM** — Only ASTM protocol; no ADT, ORM, ORU, MFN, SIU message support; hospital system integration blocked | S01:15, S01:73, S04:124-128 | 5 | 8 | 8 | 7 | 2 | High | P2 | Device Bridge Team |
| H03 | **DICOM server missing** — Radiology schema has DICOM fields but no server, no image storage, no WADO | S01:14, S01:73, S04:171-174 | 5 | 8 | 7 | 7 | 2 | High | P2 | Backend Team |
| H04 | **Clinical terminology tables empty** — LOINC, SNOMED CT, ICD-10/11 models exist but no data populated | S01:74-76, S03:53-55 | 5 | 6 | 6 | 6 | 1 | Medium | P2 | Data Engineering |
| H05 | **Clinical Decision Support is schema-only** — CDS rules exist in DB tables but no code executes them | S03:41-42, S04:183-186 | 5 | 7 | 6 | 8 | 2 | High | P2 | Clinical Engineering |
| H06 | **Missing critical clinical features** — No barcode/RFID sample tracking, no delta check (patient trend), no panic value escalation, no result auto-validation | S01:97-110 | 4 | 9 | 9 | 9 | 3 | Critical | P1 | Product Engineering |
| H07 | **IHE cross-enterprise workflows missing** — No support for Integrating the Healthcare Enterprise profiles | S01:77 | 4 | 5 | 5 | 4 | 1 | Low | P3 | Platform Engineering |
| H08 | **Bidirectional instrument interface missing** — Device bridge sends results to platform but lacks command/control back to instruments | S01:104 | 4 | 6 | 6 | 5 | 1 | Medium | P2 | Device Bridge Team |
| H09 | **openEHR not implemented** — No archetype-based EHR support for structured clinical data | S01:79 | 3 | 4 | 4 | 3 | 1 | Low | P3 | Platform Engineering |

---

## 4. AI Findings

| # | Finding | Evidence | Confidence | Impact | Business Value | Clinical Impact | Security Impact | Risk Level | Priority | Owner |
|---|---------|----------|-----------|--------|---------------|----------------|----------------|-----------|----------|-------|
| AI01 | **Executive Order violations** — EO 3 & 4 mandate local Ollama-only AI; Gemini + Groq integrations exist in production code | S02:42-48, S03:42-43, S04:49-55 | 5 | 9 | 7 | 8 | 8 | Critical | P1 | AI Team Lead |
| AI02 | **Duplicate AI engines** — routes/ai.py (multi-provider) vs services/ai/main.py (Ollama-only); code duplication, split logic | S02:34-35, S04:96-99 | 5 | 6 | 5 | 5 | 3 | High | P2 | AI Team Lead |
| AI03 | **No RAG system** — No vector database (pgvector/Qdrant), no embeddings pipeline; AI cannot reference clinical documents or perform semantic search | S01:16, S04:163-166 | 5 | 7 | 7 | 6 | 1 | Medium | P2 | AI Team |
| AI04 | **No MCP servers** — No Model Context Protocol; AI tool access limited | S01:17, S01:118 | 4 | 4 | 4 | 3 | 1 | Low | P3 | AI Team |
| AI05 | **External AI provider PHI exposure** — ai/ai_service.py and ai/ai_agent.py call OpenAI, DeepSeek, Gemini; patient data could be sent to US-based providers | S09:178-183, S10:27 | 5 | 8 | 6 | 7 | 8 | Critical | P1 | AI Team Lead |
| AI06 | **Auto-interpretation partially implemented** — Clinical result interpretation exists but incomplete; not all result types covered | S01:119 | 3 | 6 | 6 | 5 | 4 | Medium | P3 | AI Team |
| AI07 | **No critical result prediction** — No ML model for predicting panic/critical values before results are final | S01:120 | 3 | 5 | 5 | 5 | 2 | Low | P3 | AI Team |

---

## 5. Infrastructure Findings

| # | Finding | Evidence | Confidence | Impact | Business Value | Clinical Impact | Security Impact | Risk Level | Priority | Owner |
|---|---------|----------|-----------|--------|---------------|----------------|----------------|-----------|----------|-------|
| I01 | **Single PostgreSQL instance in production** — No HA, no failover, no replication; any PG failure = complete platform outage | S03:43-44, S04:40-47, S07:86-88 | 5 | 9 | 9 | 8 | 5 | Critical | P1 | DevOps |
| I02 | **No staging environment** — Changes deployed directly to production; no pre-production validation | S01:18, S03:44-45, S04:72-75 | 5 | 8 | 7 | 6 | 3 | High | P1 | DevOps |
| I03 | **No automated backup restore testing** — Backups configured but zero evidence of restore testing; RTO unknown | S01:19, S03:19-20, S04:34-39, S10:117-120 | 5 | 9 | 8 | 8 | 5 | Critical | P1 | DevOps |
| I04 | **Terraform targets AWS, deployment on DigitalOcean** — Infrastructure-as-Code is entirely mismatched from actual deployment target | S02:76, S03:40-41 | 5 | 7 | 6 | 3 | 4 | High | P2 | DevOps |
| I05 | **Database version inconsistency** — CLAUDE.md claims PG16; full.yml uses postgres:14.11-alpine; MVP docker-compose.yml uses PG16 | S02:55, S02:77 | 5 | 4 | 3 | 2 | 2 | Low | P3 | DevOps |
| I06 | **No synthetic monitoring** — Production behavior unknown between health check intervals | S01:91, S03:56-57, S04:112-115 | 5 | 6 | 5 | 4 | 3 | Medium | P2 | DevOps |
| I07 | **No APM (Application Performance Monitoring)** — No distributed tracing; performance issues hard to diagnose | S01:92 | 4 | 5 | 4 | 3 | 2 | Medium | P3 | DevOps |
| I08 | **No chaos engineering in production** — Failure modes untested; resilience unknown | S01:90 | 4 | 5 | 4 | 4 | 3 | Medium | P3 | Platform Engineering |
| I09 | **Push notification VAPID not configured** — Service worker registers push but VAPID keys missing from env | S09:172-177, S10:45 | 5 | 3 | 3 | 1 | 1 | Low | P3 | Frontend Lead |

---

## 6. Data/Integration Findings

| # | Finding | Evidence | Confidence | Impact | Business Value | Clinical Impact | Security Impact | Risk Level | Priority | Owner |
|---|---------|----------|-----------|--------|---------------|----------------|----------------|-----------|----------|-------|
| D01 | **Schema/ORM drift** — 70% of tables have no SQLAlchemy ORM model; risk of silent schema divergence | S10:22-23, S01:55 | 5 | 8 | 7 | 6 | 3 | Critical | P1 | Backend Team |
| D02 | **20+ integration connectors untested** — No smoke tests for connector implementations; integration points blind | S09:206-211, S10:28 | 5 | 7 | 6 | 5 | 5 | High | P2 | Integration Team |
| D03 | **Device bridge protocol monoculture** — Only ASTM/HL7; DICOM, LIS2-A, POCT1-A unsupported; driver dev is bottleneck for onboarding | S06:275-303, S01:15 | 5 | 7 | 7 | 6 | 1 | Medium | P2 | Device Bridge Team |
| D04 | **Massive schema churn** — 17 migrations added on 2026-07-16 with 200+ tables and no corresponding routes; schema drift risk | S02:57-58, S03:37-38, S04:91-95 | 5 | 7 | 6 | 4 | 2 | High | P2 | Backend Team Lead |
| D05 | **47 migration revisions** — Slow alembic upgrade; risk at step 23/47; complex dependency chain between revisions | S06:94-122 | 5 | 5 | 4 | 3 | 1 | Medium | P3 | Backend Team Lead |
| D06 | **No data retention policy enforcement** — National Trust Platform mandates clinical records 25y, lab results 10y, audit logs 7y; no automated enforcement | S05:89-92 | 5 | 7 | 6 | 5 | 4 | High | P2 | Platform Engineering |
| D07 | **services/shared/ dead code** — 3 deprecated bridge files never imported; creates maintenance burden and confusion | S09:212-217, S10:29 | 5 | 2 | 2 | 1 | 1 | Low | P3 | Backend Team |
| D08 | **Old MySQL reference in docs** — INFRASTRUCTURE_GUIDE.md mentions MySQL; codebase uses PostgreSQL exclusively | S02:56, S04:143-145 | 5 | 1 | 1 | 1 | 1 | Low | P3 | Backend Team |

---

## 7. Testing/Quality Findings

| # | Finding | Evidence | Confidence | Impact | Business Value | Clinical Impact | Security Impact | Risk Level | Priority | Owner |
|---|---------|----------|-----------|--------|---------------|----------------|----------------|-----------|----------|-------|
| T01 | **Route test coverage 35%** — Most route modules untested; ehr.py (73KB), compliance.py (47KB) effectively uncovered | S01:55, S03:31-32, S04:63-66 | 5 | 8 | 7 | 7 | 4 | High | P1 | Quality Engineering |
| T02 | **Service test coverage 30%** — Core business logic (interpretation, clinical_service, ehr_service) under-tested | S01:56, S03:33-34, S04:67-71 | 5 | 8 | 7 | 8 | 4 | High | P1 | Quality Engineering |
| T03 | **Zero edge/interop test coverage** — Edge platform and interoperability components completely untested | S01:57, S03:34-35, S04:86-90 | 5 | 7 | 6 | 5 | 4 | High | P2 | Quality Engineering |
| T04 | **Zero frontend tests** — frontend-v2 has no test framework; quality unknown | S01:10, S01:58 | 5 | 7 | 6 | 4 | 3 | High | P2 | Frontend Lead |
| T05 | **Zero E2E tests** — No Cypress/Playwright; integration failures undetected | S01:11, S03:39-40, S01:59 | 5 | 8 | 7 | 7 | 3 | High | P2 | Quality Engineering |
| T06 | **268 test fixture errors** — Fixture isolation issues undermine CI reliability and developer trust | S07:62-68, S05:86-88 | 5 | 6 | 5 | 4 | 2 | High | P1 | Quality Engineering |
| T07 | **No coverage threshold in CI** — Tests can degrade over time without enforcement | S09:200-205, S10:31 | 5 | 5 | 4 | 3 | 2 | Medium | P2 | DevOps |
| T08 | **6 microservice stubs with 0 tests** — Cannot deploy as microservices; significant effort to implement | S03:34-35, S02:112, S10:24 | 5 | 5 | 4 | 2 | 1 | Medium | P3 | Platform Engineering |
| T09 | **No load test baseline** — k6 scripts exist but no baseline results captured; performance regression undetectable | S01:44, S04:108-111 | 5 | 5 | 4 | 3 | 1 | Medium | P3 | Quality Engineering |

---

## 8. Governance/Compliance Findings

| # | Finding | Evidence | Confidence | Impact | Business Value | Clinical Impact | Security Impact | Risk Level | Priority | Owner |
|---|---------|----------|-----------|--------|---------------|----------------|----------------|-----------|----------|-------|
| G01 | **No legal entity** — Project has no incorporated entity for contracts, payments, or liability separation | S10:127-128 | 5 | 9 | 9 | 3 | 3 | Critical | P0 | Founder |
| G02 | **License contradiction** — No LICENSE file; MIT vs Proprietary metadata creates legal ambiguity; contributor rights unclear | S10:39-41, S09:129-133, S10:149-150 | 5 | 9 | 8 | 3 | 3 | Critical | P0 | Legal |
| G03 | **ISO 15189 incomplete** — Medical lab quality certification only partially implemented | S01:131, S04:179-181 | 4 | 7 | 8 | 6 | 2 | High | P2 | Compliance Lead |
| G04 | **ISO 27001 incomplete** — Info security certification partially implemented; formal audit not started | S01:132, S08:24 | 4 | 7 | 7 | 3 | 4 | High | P2 | Security Lead |
| G05 | **Iraqi MoH certification partial** — National health certification requirements not fully met | S01:133 | 4 | 7 | 8 | 6 | 2 | High | P2 | Compliance Lead |
| G06 | **Coverage target conflict across documents** — Platform Constitution mandates ≥95%; Digital Constitution §6.2 says 70%; actual is 54% | S05:20-26 | 5 | 5 | 4 | 3 | 1 | Medium | P2 | Platform Engineering |
| G07 | **No SBOM in CI** — Platform Constitution §4.6 mandates SBOM on every build; CI pipeline has no SBOM step | S05:62-64 | 5 | 5 | 4 | 2 | 3 | Medium | P2 | DevOps |
| G08 | **No circular dependency check in CI** — Platform Constitution Q5 mandates 0 circular dependencies; no automated check | S05:81-84 | 5 | 4 | 3 | 2 | 2 | Low | P3 | Backend Team |
| G09 | **Constitution enforcer gaps** — scripts/constitution_enforcer.py (20 rules) lacks SBOM check, migration policy check, naming convention check; not in CI | S05:102-108 | 5 | 5 | 4 | 2 | 2 | Medium | P2 | Platform Engineering |
| G10 | **Duplicate files** — ENGINEERING_CONSTITUTION.md and engineering_constitution.md in same dir; quality_gates.md and QUALITY-GATES.md | S05:65-70 | 5 | 2 | 1 | 1 | 1 | Low | P3 | Platform Engineering |
| G11 | **DIGITAL-CONSTITUTION.md not formally deprecated** — Dated 2026-07-08, superseded by Platform Constitution 2026-07-16; may cause confusion | S05:71-76 | 4 | 3 | 2 | 1 | 1 | Low | P3 | Platform Engineering |

---

## 9. Technical Debt Findings

| # | Finding | Evidence | Confidence | Impact | Effort (days) | Interest Rate | Risk Level | Priority | Owner |
|---|---------|----------|-----------|--------|---------------|---------------|-----------|----------|-------|
| TD01 | **7 microservice stubs** — services/lab, order, patient, result, sample, notification, ai are empty stubs; waste developer attention | S06:31-61 | 5 | 4 | 5 | 2%/mo | Low | P3 | Platform Engineering |
| TD02 | **Backend dual structure** — backend/services/ and backend/core/ duplicate backend/app/ equivalents; developer confusion | S06:65-91 | 5 | 3 | 3 | 1%/mo | Low | P3 | Backend Team Lead |
| TD03 | **47 migration revisions** — Slow alembic upgrade; complex dependency chain; CI migration-gate lengthens | S06:94-122 | 5 | 5 | 5 | 3%/mo | Medium | P3 | Backend Team Lead |
| TD04 | **Adaptive concurrency reactive** — _adaptive_concurrency_loop degrades after detection, not before; no prediction; oscillates | S06:126-153 | 5 | 6 | 10 | 2%/mo | Medium | P2 | Platform Engineering |
| TD05 | **Circuit breaker coverage gaps** — No persistence, thundering herd risk, no admin override, no half-open timeout, alert fatigue | S06:157-193 | 5 | 7 | 15 | 3%/mo | High | P2 | Platform Engineering |
| TD06 | **Test coverage gaps** — 28 modules for 53+ routes; edge cases, E2E, performance, security regression uncovered | S06:196-231 | 5 | 7 | 20 | 5%/mo | High | P2 | Quality Engineering |
| TD07 | **Frontend fragmentation** — 3 frontends (static PWA, React+Firebase, tRPC+React) with 3x maintenance burden | S06:234-271 | 5 | 6 | 40 | 2%/mo | Medium | P3 | Product Engineering |
| TD08 | **Device bridge protocol monoculture** — ASTM-only; DICOM, LIS2-A, POCT1-A unsupported; custom integration bottleneck | S06:275-303 | 5 | 5 | 20 | 2%/mo | Medium | P3 | Device Bridge Team |
| TD09 | **Documentation depth gaps** — No onboarding guide, no DR runbook, no clinical workflow docs, no performance baseline, no threat model | S06:306-341 | 5 | 4 | 15 | 1%/mo | Low | P3 | Platform Engineering |
| TD10 | **Arabic-first translation gaps** — Incomplete translations, clinical term inconsistency, RTL edge cases, machine-translated clinical content | S06:345-378 | 5 | 8 | 15 | 5%/mo | High | P1 | Product Engineering |

---

## 10. Contradictions (Resolved)

| # | Contradiction | Source A | Source B | Resolution | Evidence | Confidence | Impact | Risk Level | Priority | Owner |
|---|---------------|----------|----------|------------|----------|-----------|--------|-----------|----------|-------|
| C01 | **Version inconsistency** | config.py: 2.1.0 | CHANGELOG: 2.3.2 | Unify to single version source; recommend config.py as source of truth, auto-generate CHANGELOG reference | S02:8-15, S05:40-44, S09:135-139 | 5 | 6 | High | P1 | DevOps |
| C02 | **Route/model count documentation gap** | CLAUDE.md: 36 routes, 17 models | Actual: 53+ routes, 60+ models | Update all documentation to reflect actual counts; implement automated doc generation | S02:20-24, S02:104-108 | 5 | 7 | High | P2 | Platform Engineering |
| C03 | **AI provider policy violation** | Executive Orders 3&4: Ollama-only | routes/ai.py uses Gemini + Groq | Either remove external providers or formally update EOs with privacy guardrails | S02:42-48, S03:42-43, S04:49-55 | 5 | 9 | Critical | P1 | AI Team Lead |
| C04 | **PostgreSQL version conflict** | CLAUDE.md: PG16 | full.yml: postgres:14.11-alpine | Standardize on PG16 across all compose files; align documentation | S02:55, S02:77-79 | 5 | 4 | Low | P3 | DevOps |
| C05 | **Microservices readiness claim** | CLAUDE.md: "independent services" | 6/9 are stubs with 0 tests | Either implement services or remove stubs; update documentation | S02:34-35, S02:110 | 5 | 5 | Medium | P2 | Platform Engineering |
| C06 | **Coverage target conflict** | Platform Constitution: ≥95% | Digital Constitution: 70%; actual: 54% | Align all documents to single target (recommend: 70% overall, 90% critical modules) | S05:20-26 | 5 | 5 | Medium | P2 | Platform Engineering |
| C07 | **UUID PK mandate vs Integer PKs** | Engineering Constitution §2.4: UUID PKs | Most models use Integer/BigInteger PKs | Create migration to UUID PKs or file ADR to keep Integer PKs | S05:27-32 | 5 | 6 | High | P2 | Backend Team Lead |
| C08 | **mTLS mandate vs HTTP reality** | Platform Constitution §4.3: mTLS for all inter-service | docker-compose.yml: plain HTTP | File ADR documenting why mTLS is not used in current deployment; add roadmap for mTLS enablement | S05:53-58 | 5 | 8 | High | P2 | Platform Engineering |
| C09 | **FHIR strategy contradiction** | Engineering Constitution §14.1: FHIR on all endpoints | Actual: separate /fhir/ route only | File ADR documenting FHIR deployment model; decide on content-type vs separate route | S05:46-52 | 5 | 6 | Medium | P2 | Backend Team Lead |
| C10 | **RBAC role/permission count mismatch** | CLAUDE.md: 9 roles × 13 permissions | Actual: 10 roles × 16 permissions | Update documentation to reflect actual RBAC implementation | S02:65-66, S02:113 | 5 | 3 | Low | P3 | Security Lead |
| C11 | **Test count documentation gap** | CLAUDE.md: 28 test modules | Actual: 77+ test files | Update documentation; test count is understated (positive finding) | S02:86-88, S02:113 | 5 | 2 | Low | P3 | Quality Engineering |
| C12 | **Business plan vs reality** | BUSINESS_PLAN.md: $100-10,000+/mo, 50 customers Y1 | No payment processing, no customer evidence | Validate business model; implement billing or adjust projections | S02:93-100 | 4 | 7 | High | P2 | Product Management |
| C13 | **Deployment target mismatch** | Terraform targets AWS (RDS, EKS, ElastiCache) | Actual deployment: Docker Compose on DigitalOcean | Re-target Terraform for DO or migrate infrastructure to AWS | S02:76-77, S03:40-41 | 5 | 7 | High | P2 | DevOps |

---

## Scoring Summary

### Count by Priority

| Priority | Definition | Count |
|----------|-----------|-------|
| P0 | 24 hours — life/safety critical | 5 |
| P1 | 7 days — platform-critical | 14 |
| P2 | 30 days — this quarter | 26 |
| P3 | 90 days — next quarter | 26 |
| **Total** | | **71** |

### Count by Risk Level

| Risk Level | Count |
|------------|-------|
| Critical | 15 |
| High | 24 |
| Medium | 24 |
| Low | 8 |

### Count by Category

| Category | P0 | P1 | P2 | P3 | Total |
|----------|----|----|----|----|-------|
| 1. Architecture | 0 | 1 | 5 | 4 | 10 |
| 2. Security | 2 | 4 | 4 | 3 | 13 |
| 3. Healthcare | 0 | 1 | 5 | 3 | 9 |
| 4. AI | 0 | 2 | 3 | 2 | 7 |
| 5. Infrastructure | 0 | 3 | 3 | 3 | 9 |
| 6. Data/Integration | 0 | 1 | 4 | 3 | 8 |
| 7. Testing/Quality | 0 | 3 | 4 | 2 | 9 |
| 8. Governance/Compliance | 2 | 0 | 6 | 3 | 11 |
| 9. Technical Debt | 0 | 1 | 3 | 6 | 10 |
| 10. Contradictions (Resolved) | 0 | 1 | 8 | 4 | 13 |

### Top 10 Findings by Severity

| Rank | ID | Finding | Risk Level | Priority |
|------|----|---------|-----------|----------|
| 1 | S01 | Firebase security bypass | Critical | P0 |
| 2 | S02 | No LICENSE file | Critical | P0 |
| 3 | G01 | No legal entity | Critical | P0 |
| 4 | G02 | License contradiction | Critical | P0 |
| 5 | P0 (S09) | External AI PHI exposure | Critical | P1 |
| 6 | C03 | Executive Order AI violation | Critical | P1 |
| 7 | I01 | Single PostgreSQL instance | Critical | P1 |
| 8 | I03 | No backup restore testing | Critical | P1 |
| 9 | D01 | Schema/ORM drift | Critical | P1 |
| 10 | S04 | No automated secrets rotation | Critical | P1 |

---

## Methodology

Each finding was validated against at least one source document (S01-S11). Confidence scores reflect corroboration across independent sources. Impact scores integrate clinical, security, business, and operational dimensions. Priority follows P0-P3 mapping based on risk level and remediation urgency.

### Cross-Reference Key

- S01: `reports/discovery/13_GAP_ANALYSIS.md`
- S02: `reports/discovery/14_CONTRADICTIONS.md`
- S03: `reports/discovery/17_RISK_REGISTER.md`
- S04: `reports/discovery/19_RECOMMENDATIONS.md`
- S05: `docs/constitution/CONSTITUTION-VALIDATION-REPORT.md`
- S06: `docs/engineering/TECHNICAL_DEBT_REGISTER.md`
- S07: `docs/engineering/RISK-REGISTER.md`
- S08: `docs/security/security_baseline.md`
- S09: `reports/SECURITY_MASTER_REPORT.md`
- S10: `reports/RISK_REGISTER.md`
- S11: `reports/ARCHITECTURE_SNAPSHOT.md`

---

*Validation generated by PROGRAM-02 of the GULA Platform Discovery & Hardening program.*
