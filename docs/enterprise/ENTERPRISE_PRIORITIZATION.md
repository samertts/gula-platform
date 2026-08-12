# GULA Platform — Enterprise Prioritization Matrix

**Classification:** INTERNAL — Technical Review Board
**Date:** 2026-07-18
**Derived from:** DISCOVERY_VALIDATION.md (71 findings), ARCHITECTURE_GAP_ANALYSIS.md (77 gaps), DISCOVERY_CONSOLIDATION.md, IMPROVEMENT_BACKLOG.md (45 items), TECHNICAL_DEBT_REGISTRY.md (647 items)
**Total Backlog Items:** 840+ | **Total Estimated Effort:** ~1,964 hours (~12.5 person-months)

---

## 1. Enterprise-Wide Priority Map

| Priority | Definition | SLA | Count | Total Est. Effort |
|----------|-----------|-----|-------|-------------------|
| P0 (Critical) | Blocks deployment, data loss, security breach, legal liability | 24h | 5 | 68h |
| P1 (High) | Constitutional mandates, patient safety, regulatory exposure, platform-critical | 7d | 27 | 186h |
| P2 (Medium) | Best practice violations, tech debt accumulation, major feature gaps | 30d | 478 | 1,322h |
| P3 (Low) | Cosmetic, documentation, naming, low-impact improvements | 90d | 330 | 388h |

### Priority Distribution by Source

| Source | P0 | P1 | P2 | P3 | Total |
|--------|----|----|----|----|-------|
| DISCOVERY_VALIDATION | 5 | 14 | 26 | 26 | 71 |
| ARCHITECTURE_GAP_ANALYSIS | 9* | 30* | 32* | 6* | 77 |
| TECHNICAL_DEBT_REGISTRY | 4 | 13 | 448 | 182 | 647 |
| IMPROVEMENT_BACKLOG | — | — | 25 | 20 | 45 |

*\* Severity (Critical/High/Medium/Low) mapped to P0/P1/P2/P3 respectively*

---

## 2. Architecture — Ranked Backlog

**Scope:** Layer violations, circular dependencies, missing layers, monolith structure, module boundaries, ADRs, dual systems

| Rank | Issue | Priority | Effort (h) | Impact | Dependencies | Recommended Action |
|------|-------|----------|-----------|--------|-------------|-------------------|
| AR-01 | **No Dedicated Domain Layer** — 70+ top-level packages scatter domain logic; business logic mixed with infrastructure. Routes import models directly. | P0 | 120 | Architecture extraction to microservices blocked; testing hindered; constitutional violation | None | Refactor each bounded context to follow domain/application/infrastructure pattern per enterprise_architecture.md |
| AR-02 | **No CQRS Implementation** — Read/write separation only in basic read-replica. Commands return data. Queries may mutate state. | P0 | 80 | Writes compete with reads; violates constitutional mandate | AR-01 | Implement command/query separation for high-volume domains (results, orders) with dedicated read models |
| AR-03 | **Circular Dependencies (7 cycles)** — database→self_healing→database, main→routes.metrics→main, kernel cycles, national domain cycles | P1 | 56 | Import-time crashes; refactoring blocked; violates Q5 zero-circular mandate | None | Break each cycle with dependency inversion; add ARCH-002 gate to CI |
| AR-04 | **Layer Violations (26 instances)** — Domain importing from FastAPI, services importing databases directly, routes importing models | P1 | 52 | Architecture drift; framework coupling; constitutional violation | AR-01 | Enforce ARCH-001 layer boundary via automated gate; fix all 26 violations |
| AR-05 | **Cross-Domain Leakage (365 instances)** — Bounded context imports across domain boundaries | P2 | 1,095 | Module coupling prevents independent development; refactoring risk | AR-01, AR-04 | Establish bounded context boundaries; enforce via import-lint in CI |
| AR-06 | **No ADR for Key Decisions (5 missing)** — No ADR for layer restructuring, UUID migration, mTLS exception, FHIR strategy, SBOM decision | P1 | 9 | Inconsistent architecture understanding; migration path unclear; constitutional violation | None | Create 5 ADRs documenting decisions, rationale, and migration timeline |
| AR-07 | **Monster Route Files** — ehr.py (73KB, 1,192 lines), compliance.py (47KB), clinical.py (41KB) violate clean-architecture principles | P2 | 24 | Maintainability burden; merge conflict risk; violates single-responsibility | None | Split each monster file into sub-modules by bounded context |
| AR-08 | **No Hexagonal (Port/Adapter) Architecture** — Direct DB access from routes; no repository interfaces abstracting infrastructure | P1 | 60 | Cannot swap databases; testing requires real DB; infrastructure changes break business logic | AR-01 | Introduce repository interfaces in domain layer; implement adapters in infrastructure |
| AR-09 | **No Plugin Architecture** — All code compiles into single Python process; no extension mechanism | P2 | 40 | Every feature requires full deployment; third-party devs cannot extend | AR-01 | Implement Python entry-point-based plugin system with sandboxed execution |
| AR-10 | **Dual DI Containers / Dual Systems** — Kernel reimplements Core with two circuit breakers, two feature flag systems, two DI containers | P2 | 30 | Maintenance burden; inconsistent behavior; confusion about which system to extend | None | Consolidate into single DI container and single circuit breaker system |
| AR-11 | **No Kernel/Module Boundary Enforcement** — 70 top-level packages with inconsistent naming; imports cross boundaries freely | P1 | 20 | No team-scale development possible; merge conflicts increase | AR-01 | Enforce strict import rules via automated gate (ARCH-001/ARCH-002) |
| AR-12 | **Monolith scope explosion** — 60+ subdirectories, 221 app modules with 200+ national platform tables with no routes | P2 | 40 | Operational cognitive load; unclear operational status | AR-07 | Categorize all modules as active/deprecated/stub; remove or stub dead code |
| AR-13 | **Architecture layer naming conflict** — CLAUDE.md 3-layer vs Constitution 4-layer; no ADR for transition | P2 | 8 | Team follows wrong pattern; migration path unclear | AR-06 | Create ADR; update all documentation to 4-layer; implement migration plan |
| AR-14 | **Microservice stubs (6 of 9)** — services/lab, order, patient, result, sample, notification are empty stubs | P3 | 40 | Waste developer attention; architecture direction ambiguity | None | Either implement stubs or remove them; update documentation |
| AR-15 | **Backend dual structure** — backend/services/ and backend/core/ (both with api/ subdirs) duplicate backend/app/ equivalents | P3 | 16 | Developer confusion; dead code hazard | None | Remove duplicate directories; consolidate into backend/app/ |
| AR-16 | **No Event Store** — Outbox pattern exists but no event sourcing or replay capability | P2 | 30 | Cannot replay historical events; lost audit resolution | None | Add event store table (PostgreSQL JSONB) with replay API |
| AR-17 | **Large Files (67 instances > 200 lines)** — Functions and files exceed recommended size limits | P3 | 134 | Maintainability burden; code review difficulty | AR-07 | Refactor large files; set CI gate on file size |
| AR-18 | **Naming Violations (50 instances)** — Inconsistent naming patterns across codebase | P3 | 25 | Developer confusion; reduced readability | None | Standardize naming conventions; add linting rules |
| AR-19 | **Forbidden Imports (52 instances)** — Framework imports in domain layer, cross-domain imports | P2 | 53 | Architecture drift; violates modularity rules | AR-01 | Fix all forbidden imports; add CI gate |

---

## 3. Security — Ranked Backlog

**Scope:** mTLS, JWT, secrets rotation, encryption, RBAC gaps, rate limiting, frontend security, CSRF, OAuth2

| Rank | Issue | Priority | Effort (h) | Impact | Dependencies | Recommended Action |
|------|-------|----------|-----------|--------|-------------|-------------------|
| SE-01 | **Firebase security bypass** — frontend-v2 writes directly to Firestore, bypassing RBAC, ABAC, audit logging, rate limiting, encryption | P0 | 160 | **Critical data exposure** — all backend security controls bypassed; patient data at risk | None | Option A (lockdown): 2 weeks — proxy all Firestore access through backend. Option B (migration): 3 months — migrate off Firebase |
| SE-02 | **mTLS Not Implemented** — Constitution mandates mutual TLS between all services; current deployment uses plain HTTP between device-bridge and backend | P0 | 40 | Inter-service communication unencrypted and unauthenticated; MITM attack vector | None | Implement mTLS with internal CA for all inter-service communication; automate cert lifecycle |
| SE-03 | **JWT uses HS256 (symmetric key)** — Key distribution risk across services; no key rotation possible | P1 | 24 | Symmetric key must be shared across all services; key compromise allows token forgery | None | Migrate JWT signing to RS256/ES256 with JWKS endpoint; keep HS256 for internal-only tokens |
| SE-04 | **No automated secrets rotation** — SECRET_KEY, ENCRYPTION_KEY, NID_HMAC_KEY, REFRESH_TOKEN_SECRET never rotated | P1 | 40 | Credential aging increases breach risk; constitutional mandate (§4.5) requires 90-day rotation | None | Implement automated secret rotation pipeline with key versioning, staggered rollout, and rollback |
| SE-05 | **Rate limiting fails open** — When Redis is unavailable, rate limiting silently permits all requests | P1 | 16 | All rate limits bypassed during Redis outage; abuse/DoS potential | None | Implement fail-close with local fallback rate limiting (in-memory sliding window) |
| SE-06 | **No SBOM in CI** — Constitution mandates SBOM on every build; CI pipeline has no SBOM step | P1 | 8 | Supply chain security blind spot; regulatory non-compliance | None | Add CycloneDX SBOM generation to CI; validate against vulnerability DB |
| SE-07 | **No Secrets Scanning in CI** — No automated secret scanning (Gitleaks) in CI pipeline | P1 | 4 | Secrets may be committed; no automated detection; credential leak risk | None | Add Gitleaks step to CI; block PR if secrets detected |
| SE-08 | **External AI provider data sovereignty risk** — ai/ calls OpenAI, DeepSeek, Gemini; PHI could be exposed | P1 | 40 | Patient data sent to US-based providers; EO violation; regulatory risk | None | Route all AI through local Ollama-only; implement PHI scrubber for any external calls |
| SE-09 | **Session revocation fails open** — JWT blacklist in Redis; revoked tokens accepted during Redis outages | P2 | 16 | Revoked sessions remain active during outages; security policy bypass | SE-05 | Implement local JWT revocation cache with periodic Redis sync |
| SE-10 | **CSRF protection missing** — No CSRF tokens for browser-based API clients | P2 | 8 | Cross-site request forgery vulnerability; browser-based attacks possible | None | Add CSRF middleware; implement double-submit cookie pattern |
| SE-11 | **OAuth2 no key rotation** — Long-lived signing keys without rotation or key overlap period | P2 | 16 | Key compromise undetected; no rotation mechanism; OIDC compliance gap | SE-03 | Implement key rotation with overlap period; add kid header support |
| SE-12 | **No frontend security testing** — XSS, CSRF, DOM-based risks unknown; no frontend security scan | P2 | 16 | Client-side vulnerabilities undetected; supply chain risk | None | Add npm audit, ESLint security plugin, and ZAP/OWASP scan to frontend CI |
| SE-13 | **JWT kid Header Missing** — No key ID header; key rotation impossible without invalidating all tokens | P1 | 4 | Cannot identify signing key; key rotation blocked | SE-03 | Add kid header to JWT; implement JWKS endpoint for public key distribution |
| SE-14 | **Secrets in .env on disk** — Developer workstation risk; gitignored but physically present | P3 | 8 | Developer credential risk; accidental commit exposure | None | Add .env to .gitignore; implement env var injection via CI/CD only |
| SE-15 | **Weak secret detection incomplete** — _WEAK_PATTERNS list may miss modern weak passwords | P3 | 4 | Weak secrets may pass validation; insufficient entropy measurement | None | Add entropy measurement; expand _WEAK_PATTERNS with modern patterns |
| SE-16 | **Security headers minor issues** — x-content-type-options value incorrect format | P3 | 2 | Minor security header misconfiguration | None | Fix header value format |
| SE-17 | **Rate Limit Exemption for Clinical Writes** — /results, /orders, /samples, /critical-alerts exempt from concurrency limit | P2 | 8 | Abuse potential for patient-safety endpoints | None | Implement separate rate limiting for clinical endpoints with higher but bounded threshold |
| SE-18 | **No Security Incident Response Plan** — Runbooks exist for 7 scenarios but no overall plan | P2 | 16 | Incident response uncoordinated; roles and escalation unclear | None | Compose security incident response plan with roles, communication plan, and post-mortem process |
| SE-19 | **No Runtime Application Self-Protection (RASP)** — Constitution §4.10 mandates RASP | P2 | 40 | Application-layer attacks undetected at runtime | None | Evaluate RASP solutions; implement for high-risk endpoints handling PHI |
| SE-20 | **No Security.txt** — No well-known security.txt file for responsible disclosure | P3 | 1 | No channel for vulnerability disclosure | None | Create `.well-known/security.txt` with disclosure policy |

---

## 4. AI — Ranked Backlog

**Scope:** Explainability, hallucination detection, model validation, RAG, MCP, AI governance, duplicate engines

| Rank | Issue | Priority | Effort (h) | Impact | Dependencies | Recommended Action |
|------|-------|----------|-----------|--------|-------------|-------------------|
| AI-01 | **No Explainability Output** — Constitution mandates every AI output include explanation of how result was reached | P0 | 80 | Clinical AI cannot be used safely; regulatory risk; patient safety concern | None | Add explainability layer: feature attribution, confidence scores, reference sources to all AI outputs |
| AI-02 | **No Hallucination Detection** — Constitution mandates factual consistency verification and source grounding | P0 | 80 | AI may produce clinically dangerous false information; no automated hallucination guard | AI-03 (RAG) | Implement hallucination detection with factual consistency checker, source grounding, confidence threshold gating |
| AI-03 | **No RAG System / Vector Database** — No pgvector/Qdrant/Weaviate; AI cannot reference clinical documents | P1 | 60 | AI feature accuracy limited; clinical AI cannot cite sources; hallucination risk elevated | None | Deploy pgvector extension and embedding pipeline; implement RAG for clinical guidelines |
| AI-04 | **No Model Registry** — Constitution mandates model registry with version, provenance, validation results | P1 | 40 | AI model lineage untracked; cannot determine which model version produced which result | None | Build model registry with version control, provenance tracking, validation status |
| AI-05 | **No Prompt Registry** — Constitution mandates immutable, versioned prompt registry with change review | P1 | 30 | Prompt changes untracked; behavior changes invisible; prompt drift | None | Implement prompt registry with version control, diff review, approval workflow |
| AI-06 | **No Bias Detection/Monitoring** — Constitution mandates demographic parity, equal opportunity, disparate impact analysis | P1 | 40 | AI may produce biased clinical recommendations; ethical concern | AI-07 (Audit) | Implement bias detection pipeline with demographic analysis and continuous monitoring |
| AI-07 | **No AI Audit Trail** — Constitution mandates every AI interaction logged with input, output, confidence, model version | P1 | 24 | No traceability for AI decisions; regulatory audit impossible | AI-04 (Registry) | Implement AI audit logging with immutable chain, input/output capture, model version tracking |
| AI-08 | **No Model Validation Pipeline** — Constitution mandates accuracy, bias, adversarial, and edge case testing before deployment | P1 | 60 | Models deployed without validation; performance regressions undetected; clinical safety risk | AI-04 | Build model validation pipeline with automated test suite, A/B testing, gated promotion |
| AI-09 | **Executive Order Violations** — EO 3 & 4 mandate local Ollama-only; Gemini + Groq integrations exist in production code | P1 | 16 | Regulatory compliance violation; patient data sovereignty risk | None | Remove external AI providers or formally update EOs with privacy guardrails |
| AI-10 | **Duplicate AI Engines** — routes/ai.py (multi-provider) vs services/ai/main.py (Ollama-only) | P2 | 20 | Code duplication; split logic; maintenance burden | None | Consolidate into single AI service; deprecate routes/ai.py for direct API |
| AI-11 | **No MCP Servers** — No Model Context Protocol; AI tool access limited | P2 | 40 | AI agent capabilities limited; cannot execute DB queries or trigger workflows autonomously | None | Implement MCP servers for database access, API integration, and data analysis |
| AI-12 | **No Model Monitoring / Drift Detection** — No continuous performance monitoring, data drift, concept drift detection | P2 | 30 | Model performance degrades silently; population changes cause drift | AI-04 | Implement model monitoring with data drift detection, performance dashboards, auto-alerting |
| AI-13 | **Auto-interpretation partially implemented** — Clinical result interpretation exists but incomplete | P3 | 40 | Not all result types covered; inconsistent diagnostic support | AI-03 | Extend auto-interpretation to cover all test types; add confidence scoring |
| AI-14 | **No critical result prediction** — No ML model for predicting panic/critical values before results final | P3 | 30 | Missed opportunity for early warning; reactive vs proactive | AI-03, AI-12 | Implement predictive model for critical value forecasting using historical patterns |

---

## 5. Healthcare — Ranked Backlog

**Scope:** FHIR coverage, HL7 v2, DICOM, clinical terminology, CDS, clinical workflows, IHE, lab standards

| Rank | Issue | Priority | Effort (h) | Impact | Dependencies | Recommended Action |
|------|-------|----------|-----------|--------|-------------|-------------------|
| HC-01 | **Panic Value Escalation** — No automated escalation workflow for critical lab results exceeding panic thresholds | P1 | 40 | Patient safety risk; regulatory non-compliance (IQ-MOH-003); delayed critical result notification | None | Implement escalation engine with configurable thresholds, multi-channel notifications, escalation timer |
| HC-02 | **Missing Critical Clinical Features** — No barcode/RFID sample tracking, delta check, panic value escalation, result auto-validation | P1 | 160 | Core clinical safety gaps; patient safety risk; operational inefficiency | None | Implement all four features as integrated clinical safety suite |
| HC-03 | **Result Auto-Validation** — No automated result validation against QC rules, delta checks, or reference ranges | P1 | 50 | Manual validation bottleneck; delayed result release; inconsistent criteria | None | Build auto-validation engine with configurable rules (Westgard, delta check, reference range, critical flags) |
| HC-04 | **Delta Check (Patient Trend)** — No automated comparison of current results against patient historical trends | P1 | 30 | Clinically significant changes may go unnoticed; patient safety risk | None | Implement delta check engine that flags significant deviations from patient baselines |
| HC-05 | **Barcode/RFID Sample Tracking** — No barcode/RFID-based sample chain of custody tracking | P1 | 40 | Sample misidentification risk; no automated chain of custody | None | Add barcode generation at order entry and scanning at every sample touchpoint |
| HC-06 | **FHIR Coverage Insufficient** — Only 6 FHIR resources implemented out of 100+ in R4/R5 | P2 | 120 | Interoperability limited; cannot exchange data with other HIE/HIS systems | None | Implement FHIR core resources (Patient, Observation, DiagnosticReport, ServiceRequest, Specimen, Practitioner, Organization, Encounter) |
| HC-07 | **HL7 v2.x Limited to ASTM** — Only ASTM protocol; no ADT, ORM, ORU, MFN, SIU message support | P2 | 80 | Hospital system integration blocked; incompatible with HIS/EMR | None | Implement HL7 v2.x parser for ADT, ORM, ORU, MFN, SIU message types |
| HC-08 | **DICOM Server Missing** — Radiology schema has DICOM fields but no server, no image storage, no WADO | P2 | 60 | Cannot store or retrieve medical images; no PACS integration | None | Deploy DICOM server (Orthanc/DCM4CHEE) with WADO-RS and STOW-RS |
| HC-09 | **Clinical Terminology Tables Empty** — LOINC, SNOMED CT, ICD-10/11 models exist but no data populated | P2 | 40 | Test results cannot be standardized; interoperability blocked; regulatory requirement | None | Populate LOINC, SNOMED CT, ICD-10/11 codes; build mapping service with auto-suggest |
| HC-10 | **Clinical Decision Support is Schema-Only** — CDS rules exist in DB tables but no code executes them | P2 | 60 | Clinical decision support non-functional; wasted schema investment | HC-03 | Implement CDS rule engine that evaluates rules on result entry and order creation |
| HC-11 | **Instrument Bidirectional Interface** — Device bridge sends results to platform but lacks command/control back to instruments | P2 | 40 | Cannot send worklists to instruments; operators must manually enter orders | None | Implement HL7 ORM (order) messages and bidirectional instrument control |
| HC-12 | **Physician Portal** — No dedicated physician-facing interface for result review, patient management, or order entry | P2 | 120 | Low adoption by referring physicians; manual result delivery | None | Build physician portal with result dashboard, trend charts, order entry, patient list |
| HC-13 | **Patient Mobile App** — No patient-facing mobile application for result access, appointment booking, or notifications | P2 | 160 | Patient engagement limited; no self-service result access; competitive disadvantage | None | Develop patient mobile app with result viewing, appointment booking, secure messaging |
| HC-14 | **IHE Cross-Enterprise Workflows Missing** — No support for Integrating the Healthcare Enterprise profiles | P3 | 60 | Cannot interoperate with other healthcare enterprises using IHE profiles | HC-06 | Implement IHE profiles for lab (LTW, LDA), patient identity (PIX/PDQ), document sharing (XDS) |
| HC-15 | **openEHR Not Implemented** — No archetype-based EHR support for structured clinical data | P3 | 40 | Future-proofing gap; not immediately required | None | Monitor openEHR adoption in Iraqi national EHR strategy; defer implementation |
| HC-16 | **Appointment/Scheduling Missing** — No patient appointment scheduling, phlebotomy visit scheduling, or resource allocation | P2 | 80 | Patients cannot book lab visits; walk-in only model limits capacity | None | Implement scheduling engine with calendar management, resource allocation, patient self-service |
| HC-17 | **Inventory Management Missing** — No reagent lot tracking, stock level monitoring, or automated reorder | P2 | 60 | Labs risk stockouts or expired reagents; no audit trail for reagent lots | None | Build inventory module with lot tracking, expiry alerts, consumable usage per test |
| HC-18 | **Vaccine Inventory Cold Chain** — Schema exists but no routes or business logic for cold chain monitoring | P2 | 30 | Cannot support national vaccination programs; temperature excursions undetected | None | Implement cold chain routes with temperature monitoring, excursion alerting, lot tracking |

---

## 6. Infrastructure — Ranked Backlog

**Scope:** HA, DR, scaling, monitoring, staging, Terraform, database versioning, APM

| Rank | Issue | Priority | Effort (h) | Impact | Dependencies | Recommended Action |
|------|-------|----------|-----------|--------|-------------|-------------------|
| IN-01 | **Single PostgreSQL instance in production** — No HA, no failover, no replication; any PG failure = complete platform outage | P1 | 120 | **Single point of failure**; any PG failure = complete platform outage; data loss risk | None | Deploy Patroni-based PostgreSQL HA with 1 primary + 1-2 replicas; configure pgBouncer |
| IN-02 | **No Automated Backup Restore Testing** — Backups configured but zero evidence of restore testing; RTO unknown | P1 | 40 | Backup may be corrupt; recovery time unknown; DR plan untested | None | Implement automated restore test that spins up temp DB, restores latest backup, validates data integrity |
| IN-03 | **No Staging Environment** — Changes deployed directly to production; no pre-production validation | P1 | 80 | Changes tested only in development; production-like validation impossible; deployment risk high | None | Create staging environment mirroring production config, data volume, and network topology |
| IN-04 | **Terraform targets AWS, deployment on DigitalOcean** — Infrastructure-as-Code entirely mismatched from actual deployment | P2 | 40 | IaC useless for current deployment; manual infrastructure management | None | Option A: Retarget Terraform for DigitalOcean. Option B: Migrate infrastructure to AWS |
| IN-05 | **No Synthetic Monitoring** — Production behavior unknown between health check intervals | P2 | 20 | Outage detection delayed; no proactive availability tracking; SLA measurement impossible | None | Deploy synthetic monitoring (Checkly/Playwright) for 5-10 critical user paths; alert on failure |
| IN-06 | **No APM (Application Performance Monitoring)** — No distributed tracing; performance issues hard to diagnose | P2 | 40 | Performance bottlenecks undetected; no code-level latency breakdown | None | Integrate APM agent (OpenTelemetry SDK) for end-to-end distributed tracing |
| IN-07 | **No Chaos Engineering in Production** — Failure modes untested; resilience unknown | P3 | 40 | Failure response unvalidated; resilience posture unknown | IN-01 | Run chaos experiments monthly: PG failover, Redis outage, network partition |
| IN-08 | **Database Version Inconsistency** — CLAUDE.md claims PG16; full.yml uses postgres:14.11-alpine | P3 | 8 | Version drift; potential compatibility issues | None | Standardize on PG16 across all compose files and documentation |
| IN-09 | **Push Notification VAPID Not Configured** — Service worker registers push but VAPID keys missing from env | P3 | 4 | Push notifications non-functional | None | Generate VAPID keys; add to env configuration |
| IN-10 | **No Distributed Tracing Implementation** — Constitution mandates OpenTelemetry; current tracing is only RequestID middleware | P2 | 40 | End-to-end latency analysis impossible; constitutional violation | None | Implement OpenTelemetry instrumentation for all route handlers, DB calls, external API calls |
| IN-11 | **No Business Metrics Dashboards** — No dashboards for orders/hour, active labs, result TAT, test volume by type | P2 | 20 | Business performance invisible; no data-driven operations decisions | None | Build business metrics dashboard (Grafana) with Prometheus exporters for order volume, TAT, active users |
| IN-12 | **No Clinical Alerting** — No alerting for TAT breach for critical tests, instrument downtime affecting patient results | P2 | 24 | Clinically significant delays unreported; patient safety risk | IN-11 | Implement clinical alerting with severity levels, escalation policies, multi-channel delivery |
| IN-13 | **No Automated Recovery Testing** — Constitutional mandate for monthly automated recovery testing not implemented | P2 | 16 | RTO/RPO targets untested; recovery procedure may fail when needed | IN-02 | Implement automated recovery test script validating DB restore, app health, data integrity |

---

## 7. Performance — Ranked Backlog

**Scope:** Query optimization, caching, N+1 queries, adaptive concurrency, load testing, slow queries

| Rank | Issue | Priority | Effort (h) | Impact | Dependencies | Recommended Action |
|------|-------|----------|-----------|--------|-------------|-------------------|
| PF-01 | **Adaptive Concurrency Reactive** — _adaptive_concurrency_loop degrades after detection, not before; no prediction; oscillates | P2 | 40 | Performance oscillations under load; suboptimal throughput; delayed degradation response | None | Implement predictive concurrency adjustment based on queue depth trends and latency forecasting |
| PF-02 | **No Load Test Baseline** — k6 scripts exist but no baseline results captured; performance regression undetectable | P2 | 24 | Performance regression goes undetected; no capacity planning data | None | Run k6 baseline against key endpoints; store results as artifact; compare on each PR |
| PF-03 | **No Performance Regression Test Harness** — No automated baseline comparison in CI | P2 | 40 | Performance regressions caught in production; no CI gate | PF-02 | Create test harness recording p50/p95/p99 for 10 key endpoints; CI warns on >20% regression |
| PF-04 | **Missing Database Indexes** — Frequently queried columns on audit_logs, outbox_events, lab_results lack indexes | P2 | 8 | Slow queries cause timeouts and poor UX | None | Add indexes: audit_logs.resource_type, outbox_events.status, lab_results.order_id via new migration |
| PF-05 | **47 Migration Revisions** — Slow alembic upgrade; risk at step 23/47; complex dependency chain | P3 | 40 | Slow CI migration-gate; deployment risk; complex rollback chain | None | Squash migrations into single base; mark old migrations as superseded |
| PF-06 | **No VACUUM/ANALYZE Automation** — PostgreSQL autovacuum may not keep up with write-heavy workloads | P3 | 8 | Table bloat; query plan degradation; performance drift | None | Configure aggressive autovacuum for high-write tables; add monitoring alert for bloat ratio |
| PF-07 | **No Partition Management for audit_logs** — Single table for all audit entries will grow unbounded | P2 | 16 | Query performance degradation on large audit_logs table; maintenance difficulty | None | Implement time-based partitioning on audit_logs; create partition management job |
| PF-08 | **Circuit Breaker Thundering Herd Risk** — No persistence, no half-open timeout; all clients retry simultaneously after circuit half-opens | P2 | 16 | Recovery failure from coordinated retry storm; alert fatigue | None | Add randomized retry backoff, circuit half-open timeout, and persistence |

---

## 8. Testing — Ranked Backlog

**Scope:** Coverage gaps, integration tests, E2E tests, chaos testing, frontend tests, fixture issues

| Rank | Issue | Priority | Effort (h) | Impact | Dependencies | Recommended Action |
|------|-------|----------|-----------|--------|-------------|-------------------|
| TE-01 | **Route Test Coverage 35%** — Most route modules untested; ehr.py (73KB), compliance.py (47KB) effectively uncovered | P1 | 80 | Defects reach production; regression risk on changes; no safety net for refactoring | None | Add integration tests for all 53+ route modules; prioritize clinical and security routes |
| TE-02 | **Service Test Coverage 30%** — Core business logic (interpretation, clinical_service, ehr_service) under-tested | P1 | 80 | Business logic defects undetected; patient safety risk for clinical service | None | Add unit tests for all 34+ service files; focus on clinical, interpretation, and outbox services |
| TE-03 | **268 Test Fixture Errors** — Fixture isolation issues undermine CI reliability and developer trust | P1 | 40 | Flaky CI undermines confidence; developer time wasted debugging fixture issues | None | Fix fixture isolation; add pytest-randomly to detect order dependencies; enforce isolation rules |
| TE-04 | **Zero Edge/Interop Test Coverage** — Edge platform and interoperability components completely untested | P2 | 40 | Edge deployment failures undetected; integration gaps invisible | None | Add edge platform integration tests; test offline sync and reconnect scenarios |
| TE-05 | **Zero Frontend Tests** — frontend-v2 has no test framework; quality unknown | P2 | 60 | Frontend quality unknown; regression risk on UI changes; no automated UI validation | None | Add Jest/React Testing Library; add Playwright E2E for critical workflows |
| TE-06 | **Zero E2E Tests** — No Cypress/Playwright; integration failures undetected | P2 | 80 | Cross-service integration risk; user journey regression undetected; no release validation | TE-05 | Implement Playwright test suite for 10-20 critical user journeys; run in CI on every PR |
| TE-07 | **No Coverage Threshold in CI** — Tests can degrade over time without enforcement | P2 | 4 | Coverage silently erodes; no quality gate for new code | TE-01, TE-02 | Set coverage thresholds in CI (70% overall, 90% critical modules); block PRs below threshold |
| TE-08 | **6 Microservice Stubs with 0 Tests** — Cannot deploy as microservices; significant effort to implement | P3 | 40 | Microservice architecture non-viable; investment waste if stubs remain | None | Either implement and test microservices, or remove stubs and update docs |
| TE-09 | **No Load Test Baseline** — k6 scripts exist but no baseline; performance regression undetectable | P3 | 16 | Performance drift invisible; capacity decisions based on guesswork | None | Run k6 baseline; store results in repo; compare on PRs |
| TE-10 | **No Clinical Safety E2E Test Suite** — No end-to-end tests covering complete clinical workflow | P1 | 40 | Patient safety risk; integration gaps cause incidents; manual verification only | None | Write E2E test covering patient registration → order → sample → result → validation → release → alert |

---

## 9. Documentation — Ranked Backlog

**Scope:** Missing READMEs, ADRs, runbooks, API docs, Arabic user manual, on-premise guide

| Rank | Issue | Priority | Effort (h) | Impact | Dependencies | Recommended Action |
|------|-------|----------|-----------|--------|-------------|-------------------|
| DO-01 | **No README per Module** — Constitutional mandate requires README.md for every package/module; many backend modules lack them | P2 | 60 | Developer onboarding friction; module purposes unclear; documentation debt accumulates | None | Add README requirement to PR template; auto-generate baseline READMEs from module metadata |
| DO-02 | **Missing API Changelog / Consumer-Facing Documentation** — API consumers have no changelog for breaking/evolving endpoints | P2 | 8 | API consumers cannot track breaking changes; integration breakage risk on upgrades | None | Auto-generate API changelog from OpenAPI diff in CI; publish to developer portal |
| DO-03 | **Missing Arabic User Manual** — No end-user documentation in Arabic for laboratory staff | P2 | 40 | User adoption barrier; training cost; support burden | None | Create Arabic user manual covering core LIMS workflows; translate key screens and error messages |
| DO-04 | **Missing On-Premise Deployment Guide** — No documentation for on-premise/edge deployment | P2 | 16 | On-premise customers cannot self-deploy; support dependency | None | Create on-premise deployment guide with hardware requirements, network topology, configuration steps |
| DO-05 | **Route/Model Count Documentation Mismatch** — CLAUDE.md claims 36 routes, 17 models; actual is 53+ routes, 60+ models | P2 | 8 | Documentation misleading; team misinformed about system scope | None | Update all documentation to reflect actual counts; implement automated doc generation |
| DO-06 | **No Auto-Generated SDK** — Constitution mandates SDKs for Python, TypeScript, Java, Dart/Flutter; none exist | P2 | 40 | Every integration partner writes custom HTTP clients; adoption barrier | None | Set up openapi-generator workflow in CI to produce and publish SDK packages |
| DO-07 | **No Public API Catalog** — Constitution mandates auto-generated API catalog; not implemented | P2 | 20 | Developers lack centralized API discovery; duplication risk | DO-06 | Build API catalog from OpenAPI specs with search, auth requirements, rate limits |
| DO-08 | **Documentation Depth Gaps** — No onboarding guide, no DR runbook, no clinical workflow docs, no performance baseline, no threat model | P3 | 60 | New team members unproductive; incident response lacks runbooks | None | Create onboarding guide, DR runbook, clinical workflow docs, performance baseline, threat model |
| DO-09 | **Missing Consumer API Changelog** — No changelog for API consumers tracking breaking changes | P2 | 8 | Integration breakage risk; no communication channel for API changes | None | Add OpenAPI diff-based changelog generation to CI; publish to developer portal |
| DO-10 | **Old MySQL Reference in Docs** — INFRASTRUCTURE_GUIDE.md mentions MySQL; codebase uses PostgreSQL exclusively | P3 | 2 | Misleading documentation; operator confusion | None | Fix MySQL references to PostgreSQL |

---

## 10. Developer Experience — Ranked Backlog

**Scope:** CI/CD, tooling, onboarding, linting, type checking, pre-commit hooks

| Rank | Issue | Priority | Effort (h) | Impact | Dependencies | Recommended Action |
|------|-------|----------|-----------|--------|-------------|-------------------|
| DX-01 | **1,413 MyPy Errors** — No static type checking enforcement despite constitutional mandate for strict typing | P1 | 80 | Type-related bugs reach production; refactoring safety reduced; constitutional violation | None | Establish mypy baseline; enforce strict typing on new code; resolve errors per module incrementally |
| DX-02 | **No Circular Dependency Check in CI** — No automated check for circular imports despite constitutional mandate (Q5) | P1 | 8 | Circular imports introduced silently; import-time crashes possible | None | Add ARCH-002 gate to CI using import graph analysis with Tarjan's SCC algorithm |
| DX-03 | **No Automated Architecture Compliance in CI** — No layer boundary, module boundary, or naming convention checks automated | P1 | 16 | Architecture drift undetected; constitutional mandate violations unreported | None | Add ARCH-001, ARCH-002, ARCH-003 gates from QUALITY_GATE_RULES.md to CI as blocking jobs |
| DX-04 | **No Dependency Update Automation** — Dependencies partially pinned; no automated update pipeline (Dependabot/Renovate) | P2 | 4 | Security vulnerabilities from outdated deps; manual update burden | None | Configure Dependabot or Renovate for all repos; pin all transitive deps with hash verification |
| DX-05 | **Constitution Enforcer Gaps** — Existing enforcer (20 rules) lacks SBOM check, migration policy check, naming convention check; not in CI | P2 | 16 | Automated constitutional compliance incomplete; drift risk | None | Extend enforcer with missing checks; integrate into CI as blocking gate |
| DX-06 | **Pre-commit Hook Missing** — No automated lint check before commits; flake8 violations caught only in CI | P2 | 4 | CI pipeline wasted on preventable lint failures; slower feedback loop | None | Add pre-commit hook configuration with flake8 --select=E9,F821 |
| DX-07 | **No Quality Check Makefile Shortcut** — No single `make quality` command for fast developer feedback | P3 | 4 | Developer friction; no quick quality check command | None | Add `make quality` target running lint + type-check + quality scorecard |
| DX-08 | **No Migration Verification in PR CI** — Migration round-trip not tested on every PR | P2 | 8 | Migration failures caught late during release | None | Add CI job running migration round-trip on fresh PostgreSQL for every PR |
| DX-09 | **No API Gateway / Service Mesh** — Single nginx gateway with no service discovery, circuit breaking at network level, traffic splitting | P2 | 60 | Future microservice extraction blocked; canary deployments impossible | None | Add service mesh (Istio/Linkerd) or implement Kong/Envoy as gateway with discovery |
| DX-10 | **No gRPC API Layer** — Future architecture specifies gRPC for internal service communication; not implemented | P3 | 40 | Internal service performance suboptimal; no binary protocol for device bridge | None | Add gRPC endpoints for high-volume domains (results ingestion, batch operations) |

---

## 11. Operations — Ranked Backlog

**Scope:** Runbooks, incident response, backup/restore, monitoring, alerting, DR

| Rank | Issue | Priority | Effort (h) | Impact | Dependencies | Recommended Action |
|------|-------|----------|-----------|--------|-------------|-------------------|
| OP-01 | **No Backup Restore Testing** — Backups exist but restore is never tested; RTO unknown | P1 | 40 | **Critical DR risk** — backup may be corrupt; no recovery validation | None | Implement automated restore test script; run weekly; report results |
| OP-02 | **No Staging Environment** — No pre-production validation; changes deployed to prod directly | P1 | 80 | Production incidents from untested changes; no release validation | None | Create staging environment; enforce deploy-to-staging-before-production gate |
| OP-03 | **Single PostgreSQL Instance** — No HA; any DB failure = complete platform outage | P1 | 120 | **SPOF** — database failure = complete platform outage | None | Deploy Patroni HA with pgBouncer connection pooling |
| OP-04 | **Circuit Breaker Coverage Gaps** — No persistence, thundering herd risk, no admin override, no half-open timeout, alert fatigue | P2 | 40 | Ineffective circuit breaking during incidents; operator blind | None | Implement circuit breaker admin API; add persistence; fix half-open timeout |
| OP-05 | **No Outbox Pattern Monitoring** — Queue depth, processing latency, failure rate, retry count unmonitored | P2 | 16 | Outbox backlog undetected; event loss risk; processing delays invisible | None | Add monitoring for outbox processing health; alert on backlog or sustained failures |
| OP-06 | **Security Incident Response Plan Incomplete** — Runbooks for 7 scenarios but no overall plan | P2 | 16 | Uncoordinated incident response; roles and escalation unclear | None | Compose incident response plan with roles, communication plan, escalation matrix |
| OP-07 | **No Data Retention Policy Enforcement** — Clinical records 25y, lab results 10y, audit logs 7y mandated; no automated enforcement | P2 | 20 | Regulatory non-compliance; storage bloat; privacy risk | None | Implement automated data lifecycle management; schedule archival/deletion jobs |
| OP-08 | **No Admin API** — No separate admin API for platform management, tenant provisioning, or system configuration | P2 | 40 | Platform operations require direct DB access; no self-service tenant management | None | Create admin API with scoped permissions for platform operations and tenant provisioning |
| OP-09 | **No Webhook System** — No outbound webhook delivery for events (result ready, critical alert, order status change) | P2 | 30 | Hospitals cannot integrate GULA events into their systems | None | Implement webhook registry with retry, secret signing, and delivery logging |
| OP-10 | **Docker Compose at Production Scale** — Not designed for production orchestration; single PG instance; no HA | P1 | 60 | Production reliability risk; no orchestration; manual scaling | None | Migrate to K8s or Docker Swarm for production orchestrations; keep compose for dev |
| OP-11 | **Processing Activity Registration Missing** — IQ-MOH-016 mandates ROPA generation; not implemented | P2 | 16 | Regulatory non-compliance with data protection law | None | Implement automated processing activity register from system configuration and data flow maps |
| OP-12 | **Data Protection Impact Assessment Missing** — IQ-DPL-006 DPIA template and screening not implemented | P2 | 16 | Cannot conduct DPIAs for new features; regulatory risk for high-risk processing | None | Implement DPIA workflow with automated screening, template generation, review tracking |

---

## 12. Compliance — Ranked Backlog

**Scope:** Constitutional violations, regulatory gaps, ISO certification, Iraqi MoH certification, data governance

| Rank | Issue | Priority | Effort (h) | Impact | Dependencies | Recommended Action |
|------|-------|----------|-----------|--------|-------------|-------------------|
| CO-01 | **No Legal Entity** — Project has no incorporated entity for contracts, payments, or liability separation | P0 | 80 | **Blocks all commercial activity**; no contracts, no payments, no liability protection | None | Incorporate legal entity (Iraq or UAE); set up corporate bank account; engage legal counsel |
| CO-02 | **No LICENSE File / License Contradiction** — No LICENSE file; MIT vs Proprietary metadata creates legal ambiguity | P0 | 8 | **Legal risk** — contributor rights unclear; users have no license; IP protection uncertain | CO-01 | Choose license (recommend: AGPL v3 + commercial option); add LICENSE file; update all metadata |
| CO-03 | **Coverage Target Conflict** — Platform Constitution ≥95%, Digital Constitution 70%, actual 54% | P1 | 4 | Team confusion about targets; governance authority dilution | None | Align all documents to single target (recommend: 70% overall, 90% critical modules) |
| CO-04 | **UUID PK Mandate vs Integer PKs** — Constitution §2.4 mandates UUID; most models use Integer/BigInteger | P1 | 40 | Constitutional violation; migration to UUID on large tables is high-risk | None | Create ADR: either commit to UUID migration with plan or document decision to retain Integer PKs |
| CO-05 | **mTLS Mandate vs HTTP Reality** — Constitution §4.3 mandates mTLS; deployment uses plain HTTP | P1 | 8 | Critical constitutional violation; security gap; compliance audit finding | None | File ADR documenting current HTTP rationale, risk assessment, mTLS implementation timeline |
| CO-06 | **SBOM Mandate vs No SBOM in CI** — Constitution §4.6 mandates SBOM every build; CI pipeline has no SBOM step | P1 | 8 | Supply chain security blind spot; constitutional violation; regulatory non-compliance | None | Add SBOM generation to CI; validate against vulnerability DB |
| CO-07 | **ISO 15189 (Medical Labs) Partial** — Quality control module exists but full compliance framework incomplete | P2 | 120 | Labs cannot achieve/cite accreditation; competitive disadvantage; regulatory risk | None | Map all ISO 15189 clauses to GULA controls; implement missing controls; conduct gap assessment |
| CO-08 | **ISO 27001 (Information Security) In Progress** — Security controls present but formal certification not complete | P2 | 80 | Cannot claim certified ISMS; enterprise customers require ISO 27001 | None | Complete ISO 27001 certification; implement SoA, internal audit, management review |
| CO-09 | **Iraqi MoH Certification Partial** — SNDHS integration exists but full MoH certification framework not mapped | P2 | 60 | Deployment in Iraqi public health sector may be blocked | None | Complete MoH certification gap analysis; implement missing controls; submit for formal certification |
| CO-10 | **Failed Tests Contradiction** — 268 test errors and 3 failures; Quality Gate Q12 mandates zero failed tests | P1 | 40 | Test suite fragility undermines CI reliability; false sense of security | None | Fix or disable 268 fixture errors; resolve 3 chaos ordering failures; enforce zero-failure policy |
| CO-11 | **No README per Module** — Constitutional Q5 mandates README for every package; many lack | P2 | 16 | Developer onboarding friction; constitutional violation | None | Add README requirement to PR template; auto-generate baseline READMEs |
| CO-12 | **No Circular Dependency Check in CI** — Constitutional Q5 mandates zero circular deps; no automated check | P1 | 8 | Circular deps introduced silently; constitutional violation | None | Add ARCH-002 gate to CI using import graph analysis |
| CO-13 | **Retention Policy Enforcement Missing** — Clinical 25y, results 10y, audit 7y; no automated enforcement | P2 | 20 | Regulatory non-compliance; storage bloat; privacy risk | None | Implement automated data lifecycle management |
| CO-14 | **Duplicate Governance Files** — ENGINEERING_CONSTITUTION.md and engineering_constitution.md; quality_gates.md and QUALITY-GATES.md | P3 | 4 | Confusion about authoritative version; maintenance burden | None | Deduplicate files; keep authoritative version with canonical naming |
| CO-15 | **DIGITAL-CONSTITUTION.md Not Formally Deprecated** — Superseded document still present with conflicting rules | P3 | 4 | Developers may reference superseded document; governance authority dilution | None | Add deprecation notice header; redirect readers to PLATFORM-CONSTITUTION.md |
| CO-16 | **No Data Governance Framework** — No formal data classification, data lineage, data quality metrics, or data stewardship | P2 | 40 | Data quality unmeasured; no ownership assignments; regulatory risk | None | Establish data governance program with catalog, lineage tracking, quality metrics, stewardship roles |
| CO-17 | **No Clinical Safety Governance** — No formal clinical safety framework (IEC 62304, ISO 14971) for SaMD | P2 | 40 | Regulatory risk for clinical decision support; liability for patient harm from software errors | None | Implement clinical safety management system per IEC 62304; conduct hazard analysis |
| CO-18 | **Proficiency Testing (IQ-MOH-007) Planned Only** — PT module, result submission, performance tracking not implemented | P2 | 20 | Labs cannot demonstrate PT compliance; regulatory risk for lab licensing | None | Implement proficiency testing module with result submission, peer comparison, performance scoring |
| CO-19 | **Cross-Border Data Transfer (IQ-DPL-007) Planned Only** — Transfer impact assessment and adequacy decisions not implemented | P2 | 16 | International expansion blocked; cloud deployment legally uncertain | None | Implement transfer impact assessment framework; document adequacy decisions for target jurisdictions |
| CO-20 | **Constitution Enforcer Not in CI** — 20 rules exist but not integrated into CI pipeline | P2 | 8 | Constitutional enforcement depends on manual review; drift risk | None | Integrate constitution enforcer into CI as blocking gate |

---

## 13. Data/Integration — Ranked Backlog

**Scope:** Schema/ORM drift, integration connectors, device bridge protocols, data retention, migration health

| Rank | Issue | Priority | Effort (h) | Impact | Dependencies | Recommended Action |
|------|-------|----------|-----------|--------|-------------|-------------------|
| DI-01 | **Schema/ORM Drift** — 70% of tables have no SQLAlchemy ORM model; risk of silent schema divergence | P1 | 80 | Schema evolves without code awareness; ORM mismatch; migration complexity | None | Generate ORM models for unmodeled tables; enforce model-per-table in migration policy |
| DI-02 | **Massive Schema Churn** — 17 migrations added on 2026-07-16 with 200+ tables and no corresponding routes | P2 | 40 | Schema drift risk; dead tables; wasted migration effort | DI-01 | Freeze schema-only migrations until routes exist; audit 200+ new tables for necessity |
| DI-03 | **20+ Integration Connectors Untested** — No smoke tests for connector implementations | P2 | 40 | Integration points blind; connector failures undetected | None | Add smoke tests for all 20+ integration connectors; run in CI |
| DI-04 | **Device Bridge Protocol Monoculture** — Only ASTM/HL7; DICOM, LIS2-A, POCT1-A unsupported | P2 | 80 | Driver dev is bottleneck for onboarding new instruments | None | Implement DICOM, LIS2-A, POCT1-A parsers; create driver SDK for third-party device integrators |
| DI-05 | **No Webhook System** — No outbound webhook delivery for events | P2 | 30 | Hospitals cannot integrate GULA events into their systems | None | Implement webhook registry with retry, secret signing, delivery logging |
| DI-06 | **No Data Retention Policy Enforcement** — No automated enforcement of retention mandates | P2 | 20 | Regulatory non-compliance; storage bloat | None | Implement automated data lifecycle management |
| DI-07 | **47 Migration Revisions** — Slow alembic upgrade; complex dependency chain | P3 | 40 | Slow CI; deployment risk; complex rollback | None | Squash migrations into single base migration |
| DI-08 | **services/shared/ Dead Code** — 3 deprecated bridge files never imported | P3 | 8 | Maintenance burden; developer confusion | None | Remove deprecated bridge files |
| DI-09 | **Old MySQL Reference in Docs** — INFRASTRUCTURE_GUIDE.md mentions MySQL | P3 | 2 | Misleading documentation | None | Fix MySQL references to PostgreSQL |

---

## 14. Quick Wins (< 1 Week, High Impact)

| # | Issue | Category | Effort | Impact | Dependencies | Recommended Action |
|---|-------|----------|--------|--------|-------------|-------------------|
| QW-01 | Add database indexes for slow query patterns (audit_logs, outbox_events, lab_results) | Performance | 1 day | 8/10 | DB access, Alembic migration | Create migration for missing indexes |
| QW-02 | Add migration round-trip verification to PR CI | Developer Experience | 1 day | 8/10 | GitHub Actions, PostgreSQL service container | CI job: fresh PG → alembic upgrade → downgrade → upgrade |
| QW-03 | Add flake8 pre-commit hook | Developer Experience | 0.5 day | 7/10 | None | Add pre-commit hook configuration |
| QW-04 | Add secrets scanning (Gitleaks) to CI | Security | 0.5 day | 7/10 | None | Add Gitleaks step to CI; block on detection |
| QW-05 | Create 5 missing ADRs (layer restructuring, UUID, mTLS, FHIR, SBOM) | Architecture | 2 days | 8/10 | None | Create ADRs documenting decisions and rationale |
| QW-06 | Add Arabic translation CI gate | Developer Experience | 1 day | 9/10 | Frontend translation files | CI fails if new i18n keys lack Arabic translations |
| QW-07 | Add coverage threshold enforcement in CI | Testing | 0.5 day | 6/10 | Coverage tool configured | Set minimum coverage thresholds; block PRs below threshold |
| QW-08 | Add system_ready log message on startup | Operations | 0.5 day | 4/10 | None | Log startup duration and component health when system_ready=True |
| QW-09 | Add Slack release notification | Operations | 0.5 day | 5/10 | Slack webhook URL | Release tag push triggers Slack message with version and changelog |
| QW-10 | Add pytest-randomly for order-independent tests | Testing | 0.5 day | 6/10 | None | Install pytest-randomly; run random order tests in CI |
| QW-11 | Add README to undocumented modules (ai/, firewall/, edge/, gateways/) | Documentation | 1 day | 6/10 | None | Write short READMEs explaining purpose, key classes, relationships |
| QW-12 | Fix security headers (x-content-type-options) | Security | 0.5 day | 2/10 | None | Correct header value format |
| QW-13 | Add security.txt for vulnerability disclosure | Security | 0.5 day | 2/10 | None | Create `.well-known/security.txt` |
| QW-14 | Add health check timeout configuration via env vars | Infrastructure | 0.5 day | 4/10 | None | Move hardcoded HEALTHCHECK params to env vars |
| QW-15 | Resolve DB version inconsistency (PG16 vs PG14) | Infrastructure | 1 day | 4/10 | None | Standardize on PG16 across all compose files |
| QW-16 | Configure Dependabot/Renovate for dependency updates | Developer Experience | 0.5 day | 6/10 | None | Enable auto-updates for pip/npm; pin all transitive deps |
| QW-17 | Add deprecation notice to DIGITAL-CONSTITUTION.md | Compliance | 0.5 day | 3/10 | None | Add deprecation header; redirect to PLATFORM-CONSTITUTION.md |
| QW-18 | Remove duplicate governance files (ENGINEERING_CONSTITUTION.md, quality_gates.md) | Compliance | 0.5 day | 2/10 | None | Keep authoritative version; remove or symlink duplicates |
| QW-19 | Generate VAPID keys for push notifications | Infrastructure | 0.5 day | 3/10 | None | Generate keys; add to env configuration |
| QW-20 | Add `make quality` shortcut for developer feedback | Developer Experience | 0.5 day | 5/10 | None | Create make target running lint + quality scorecard |

---

## 15. Strategic Initiatives (3+ Months, Transformative)

| # | Initiative | Categories | Est. Duration | Est. Effort | Impact | Dependencies | Description |
|---|-----------|-----------|--------------|-------------|--------|-------------|-------------|
| SI-01 | **Clinical Safety Transformation** | Healthcare, AI | 6 months | 640h | **Patient safety critical** | HC-01 through HC-10, AI-01, AI-02 | Implement complete clinical safety suite: panic escalation, auto-validation, delta checks, barcode tracking, CDS engine, AI explainability, hallucination detection. Includes FHIR expansion to 20+ resources and HL7 v2 full message support |
| SI-02 | **Architecture Modernization** | Architecture | 6 months | 800h | Enables team-scale development, microservice extraction | AR-01 through AR-11 | Refactor to Clean Architecture: domain layer extraction, port/adapter pattern, CQRS for high-volume domains, plugin system, module boundary enforcement, circular dependency resolution |
| SI-03 | **Production Infrastructure Hardening** | Infrastructure, Operations | 4 months | 400h | **Eliminates SPOF, enables growth** | IN-01 through IN-08, OP-01 through OP-03 | PostgreSQL HA with Patroni, staging environment, automated DR testing, APM, synthetic monitoring, chaos engineering program, full Prometheus/Grafana/Alertmanager production deployment |
| SI-04 | **Security Posture Overhaul** | Security | 4 months | 400h | **Closes critical security gaps** | SE-01 through SE-20 | Firebase security remediation (lockdown + migration), mTLS implementation, JWT RS256 migration, secrets rotation automation, RASP integration, incident response program, CSRF protection |
| SI-05 | **Quality Engineering Foundation** | Testing, Developer Experience | 5 months | 500h | **Prevents defects, enables refactoring** | TE-01 through TE-10, DX-01 through DX-05 | Achieve 70%+ test coverage (routes + services), E2E test suite (20+ journeys), frontend tests, 1,413 mypy errors resolved, CI architecture gates, performance regression harness |
| SI-06 | **AI Governance & Platform** | AI | 4 months | 400h | Enables safe clinical AI deployment | AI-01 through AI-14 | RAG system with pgvector, model registry, prompt registry, AI audit trail, bias detection, model validation pipeline, drift monitoring, MCP servers. Consolidate duplicate AI engines |
| SI-07 | **Regulatory Certification Program** | Compliance | 6 months | 400h | **Unlocks government/enterprise sales** | CO-01 through CO-20 | Legal entity formation, license resolution, ISO 15189 certification, ISO 27001 certification, Iraqi MoH certification, data governance framework, clinical safety governance (IEC 62304), all IQ-MOH controls |
| SI-08 | **Commercial Platform Enablement** | Healthcare, Infrastructure | 4 months | 360h | **Revenue generation** | HC-12, HC-13, HC-16, HC-17, IN-11 | Physician portal, patient mobile app, appointment scheduling, inventory management, billing/invoicing (Financial Engine Phase B), business metrics dashboards, contract pricing module |
| SI-09 | **Interoperability Expansion** | Healthcare | 5 months | 400h | **Health system integration** | HC-06 through HC-08, HC-14, DI-04 | FHIR expansion (20+ resources), HL7 v2 full message support (ADT/ORM/ORU/MFN/SIU), DICOM server deployment, IHE profile implementation, device bridge protocol expansion (LIS2-A, POCT1-A), webhook system |
| SI-10 | **Schema/Code Alignment** | Data/Integration, Architecture | 3 months | 240h | **Eliminates schema drift, reduces tech debt** | DI-01, DI-02, AD-16 | Generate ORM models for all 200+ unmodeled tables, audit 200+ new national platform tables, consolidate or remove schema-only tables without routes, migration squashing |

---

## Appendix A: Effort Summary by Category

| Category | P0 (h) | P1 (h) | P2 (h) | P3 (h) | Total (h) | Priority Items |
|----------|--------|--------|--------|--------|-----------|----------------|
| Architecture | 200 | 137 | 1,242 | 215 | 1,794 | AR-01, AR-02 (CQRS/Domain Layer) |
| Security | 200 | 136 | 108 | 15 | 459 | SE-01 (Firebase), SE-02 (mTLS) |
| AI | 160 | 254 | 90 | 70 | 574 | AI-01, AI-02 (Explainability/Hallucination) |
| Healthcare | 0 | 320 | 670 | 100 | 1,090 | HC-01 through HC-05 (Clinical Safety) |
| Infrastructure | 0 | 300 | 200 | 52 | 552 | IN-01 (PG HA), IN-03 (Staging) |
| Performance | 0 | 0 | 128 | 48 | 176 | PF-01, PF-02 (Adaptive Concurrency/Baseline) |
| Testing | 0 | 240 | 184 | 56 | 480 | TE-01, TE-02 (Coverage), TE-03 (Fixtures) |
| Documentation | 0 | 0 | 152 | 62 | 214 | DO-01, DO-06 (READMEs/SDKs) |
| Developer Experience | 0 | 104 | 88 | 44 | 236 | DX-01 (MyPy), DX-02 (Circular Dep Check) |
| Operations | 0 | 300 | 218 | 0 | 518 | OP-01 (Backup Testing), OP-03 (PG HA) |
| Compliance | 88 | 100 | 380 | 8 | 576 | CO-01 (Legal Entity), CO-02 (License) |
| Data/Integration | 0 | 80 | 170 | 50 | 300 | DI-01 (Schema/ORM Drift), DI-02 (Schema Churn) |
| **Total** | **648** | **1,971** | **3,630** | **720** | **6,969** | — |

---

## Appendix B: Dependency Graph for Top 20 Items

```
SE-01 [Firebase bypass] → blocks all frontend security
  ├── SE-10 [CSRF] → must be implemented after Firebase lockdown
  └── TE-05 [Frontend tests] → enabled by Firebase remediation

AR-01 [Domain layer] → blocks → AR-02 [CQRS]
  ├── AR-04 [Layer violations] → depends on AR-01
  ├── AR-05 [Cross-domain leakage] → depends on AR-01, AR-04
  ├── AR-08 [Hexagonal architecture] → depends on AR-01
  └── DX-03 [Architecture compliance gates] → enabled by AR-01

IN-01 [PG HA] → reduces risk for → OP-01 [Backup testing]
  └── IN-07 [Chaos engineering] → enabled by IN-01

AI-03 [RAG] → enables → AI-02 [Hallucination detection]
  ├── AI-01 [Explainability] → independent
  └── AI-13 [Auto-interpretation] → enabled by AI-03

HC-01 [Panic escalation] → independent (super high priority)
HC-06 [FHIR expansion] → enables → HC-14 [IHE profiles]

CO-01 [Legal entity] → enables → CO-02 [License resolution]
  └── SI-07 [Regulatory certification] → enabled by CO-01, CO-02
```

---

## Appendix C: Risk-Weighted Priority Matrix

| Quadrant | Urgent & Important (Do Now) | Important Not Urgent (Schedule) |
|----------|---------------------------|-------------------------------|
| **High Impact** | SE-01 (Firebase), IN-01 (PG HA), OP-01 (Backup Testing), CO-01 (Legal Entity), HC-01 (Panic Escalation) | AI-01 (Explainability), AR-01 (Domain Layer), SI-04 (Security Overhaul), SI-01 (Clinical Safety), HC-06 (FHIR) |
| **Low Impact** | QW-01 (Indexes), QW-04 (Gitleaks in CI), QW-06 (Arabic CI Gate) | DO-06 (SDKs), AR-14 (Microservice Stubs), DI-07 (Migration Squash) |

---

*Generated from DISCOVERY_VALIDATION.md (71 findings), ARCHITECTURE_GAP_ANALYSIS.md (77 gaps), DISCOVERY_CONSOLIDATION.md, IMPROVEMENT_BACKLOG.md (45 items), and TECHNICAL_DEBT_REGISTRY.md (647 items). All priority assignments cross-referenced against PLATFORM-CONSTITUTION.md mandates and quality gate requirements.*
