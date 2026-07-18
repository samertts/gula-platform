# GULA Platform — Enterprise Transformation Roadmap

**Classification:** INTERNAL — Board/C-Suite/Technical Review Board
**Date:** 2026-07-18
**Horizon:** 36 Months (2026 Q3 → 2029 Q2)
**Derived from:** ENTERPRISE_PRIORITIZATION.md (840 items), TECHNICAL_DEBT_MASTER_REGISTER_v2.md (46 items, 7,280h), ARCHITECTURE_GAP_ANALYSIS.md (77 gaps), DISCOVERY_VALIDATION.md (71 findings), EXECUTIVE_SUMMARY.md, IMPROVEMENT_BACKLOG.md (45 items), PLATFORM_EVOLUTION_PLAN.md, FUTURE_ARCHITECTURE.md, ROADMAP_2050.md

---

## 1. Executive Summary

### Current State

| Dimension | Score | Grade |
|-----------|-------|-------|
| **Quality Index** | **673/1000** | **D (BRONZE)** |
| Architecture Compliance | 7/100 | F |
| Security Posture | 85/100 | B |
| CI/CD Maturity | 88/100 | B |
| Healthcare Compliance | 72/100 | C |
| Test Coverage | 54% | F |
| Quality Gate Status | **NOT CERTIFIED** | — |

### Target State (Month 36)

| Dimension | Score | Grade |
|-----------|-------|-------|
| **Quality Index** | **900+/1000** | **PLATINUM** |
| Architecture Compliance | 80+/100 | A |
| Security Posture | 95+/100 | A |
| CI/CD Maturity | 95+/100 | A |
| Healthcare Compliance | 90+/100 | A |
| Test Coverage | 80+% | B+ |
| Quality Gate Status | **CERTIFIED GOLD** | — |

### Investment Summary

| Category | Estimated Effort |
|----------|-----------------|
| Total engineering effort | ~6,969 hours |
| Estimated cost (at $150/h) | ~$1,045,350 |
| Annual tech debt interest (current) | ~$340,000/year |
| Team size required | 8-12 engineers across 36 months |
| Phases | 6 horizons across 3 years |

### Core Principles

1. **Safety first** — clinical safety and data integrity are never compromised for speed
2. **Strangler fig** — never rewrite; extract and redirect incrementally
3. **Feature-flag every break** — every extraction, merge, or API change is behind per-tenant flags
4. **Observability before extraction** — no service ships without structured logging, tracing, and metrics
5. **Test the migration path** — every extraction includes integration tests, chaos scenarios, and rollback tests

---

## 2. Horizon Map

| Horizon | Period | Focus | Investment | Key Metrics | Certification Milestone |
|---------|--------|-------|-----------|-------------|------------------------|
| **H1** | Days 1-30 | Quick Wins & Foundation | ~200h | QG PASS, Arch 30+, P0=0, Security 88+ | BRONZE → SILVER (entry) |
| **H2** | Days 31-90 | Critical Fixes & Stabilization | ~600h | Arch 50+, Coverage 60%, QI 700+, Test fix 268 | SILVER CERTIFIED |
| **H3** | Months 4-6 | Architecture Modernization | ~1,200h | GOLD cert, QI 800+, Domain layer started, CQRS in design | GOLD CERTIFIED |
| **H4** | Months 7-12 | Clinical Safety & AI | ~1,500h | Arch 70+, AI gov in place, FHIR 20+ resources, Clinical safety suite | GOLD+ |
| **H5** | Months 13-24 | National Readiness | ~2,000h | FHIR complete, SNDHS Phase 2 live, National ID active, MoH cert | PLATINUM (entry) |
| **H6** | Months 25-36 | Platform Evolution | ~1,500h | PLATINUM cert, ecosystem live, 3+ countries, AI mesh | PLATINUM CERTIFIED |
| **Total** | **36 months** | | **~7,000h** | QI 900+, Arch 80+, Coverage 80+, Security 95+ | |

---

## 3. Detailed Phase Plans

### H1 — Quick Wins & Foundation (Days 1-30)

**Objective:** Eliminate all P0 items, establish legal foundation, fix critical security holes, and build the quality infrastructure needed for all subsequent phases.

**Items:**

| # | Item | Source ID | Effort (h) | Impact |
|---|------|-----------|-----------|--------|
| 1 | Establish legal entity (incorporation, bank account, legal counsel) | CO-01, G01, MTD-P0 | 80 | Unblocks all commercial activity |
| 2 | Add AGPL v3 LICENSE file; resolve MIT vs Proprietary metadata contradiction | CO-02, S02, MTD-P0 | 8 | Legal clarity for contributions and IP |
| 3 | Lockdown Firebase: route all frontend-v2 data through backend API (interim) | SE-01, S01, MTD-001 | 80 | Eliminates catastrophic PHI exposure |
| 4 | Remove external AI providers (Gemini, Groq) or formally update Executive Orders | AI-09, C03, MTD-017 | 16 | Regulatory compliance; data sovereignty |
| 5 | Add SBOM generation (CycloneDX) to CI pipeline | SE-06, CO-06, MTD-016 | 8 | Supply chain visibility |
| 6 | Add Gitleaks secret scanning to CI pipeline | SE-07, MTD-016 | 4 | Prevent credential leaks |
| 7 | Add ARCH-001/002/003 quality gates to CI (layer boundary, circular deps, naming) | DX-03, AR-04, 7.1 | 16 | Automated architecture compliance |
| 8 | Add pre-commit hook (flake8 E9/F821) | DX-06, QW-002 | 4 | Catch errors before CI |
| 9 | Write 5 missing ADRs (layer restructuring, UUID, mTLS, FHIR, SBOM) | AR-06, MTD-043, A07 | 9 | Architecture rationale documented |
| 10 | Canonicalize version to single source (config.py = 2.1.0) | MTD-046, C01 | 8 | Version clarity |
| 11 | Fix Pydantic V2 deprecation warnings (class Config → ConfigDict) | MTD-045 | 20 | Clean warnings |
| 12 | Add security.txt for vulnerability disclosure | SE-20 | 1 | Responsible disclosure channel |
| 13 | Add database indexes for slow query patterns | PF-04, QW-003 | 8 | Performance quick win |
| 14 | Add `make quality` shortcut for fast developer feedback | DX-07, QW-009 | 4 | Developer velocity |
| 15 | Add migration round-trip verification to PR CI | QW-010, DX-08 | 8 | Prevent broken migrations |
| 16 | Fix x-content-type-options security header format | SE-16 | 2 | Minor security fix |
| 17 | Add README to undocumented modules (ai/, firewall/, edge/, gateways/) | DO-01, QW-001 | 8 | Developer onboarding |
| 18 | Add system_ready INFO log message on startup | QW-008 | 4 | Operational visibility |
| 19 | Add pytest-randomly to detect test order dependencies | QW-007 | 4 | Test reliability |
| 20 | Implement backup restore testing (automated script) | IN-02, OP-01, MTD-003 | 40 | DR validation |
| 21 | Update CLAUDE.md with accurate route (53+) and model (60+) counts | DO-05, MTD-036 | 8 | Documentation accuracy |
| 22 | Fix MySQL references in docs to PostgreSQL | DO-10 | 2 | Documentation accuracy |

**Dependencies:** None (foundation phase)

**Exit Criteria:**
- [ ] P0 count = 0 (all resolved or in active remediation)
- [ ] Legal entity incorporated and LICENSE file committed
- [ ] Firebase interim lockdown deployed to production
- [ ] All external AI providers removed or governed by updated EOs
- [ ] SBOM + Gitleaks running in CI on every PR
- [ ] Architecture gates enforced in CI (block PRs on violations)
- [ ] Backup restore testing automated and passing
- [ ] All 5 ADRs written and reviewed
- [ ] All 22 items complete

**Risk:**
- Legal incorporation takes longer than expected → parallel-track with technical work
- Firebase lockdown reveals undocumented frontend dependencies → extend interim window
- Team capacity insufficient for 22 items → prioritize items 1-8 as mandatory, rest as stretch

**Resources:** 4-5 engineers (1 backend, 1 security, 1 DevOps, 1 legal/compliance, 1 platform)

---

### H2 — Critical Fixes & Stabilization (Days 31-90)

**Objective:** Resolve all P0/P1 items, stabilize infrastructure, harden security, close critical test coverage gaps, and achieve SILVER certification.

**Items:**

| # | Item | Source ID | Effort (h) | Impact |
|---|------|-----------|-----------|--------|
| 1 | Deploy PostgreSQL HA with Patroni + pgBouncer | IN-01, OP-03, MTD-002 | 120 | Eliminates DB SPOF |
| 2 | Migrate JWT signing from HS256 to RS256 with JWKS endpoint | SE-03, MTD-007 | 24 | Asymmetric trust; key rotation enabled |
| 3 | Add kid header to JWT; implement JWKS endpoint | SE-13, MTD-007 | 4 | Key rotation support |
| 4 | Implement panic value escalation engine with multi-channel notifications | HC-01, MTD-009 | 40 | Patient safety (IQ-MOH-003) |
| 5 | Fix 268 test fixture errors; enforce fixture isolation | TE-03, MTD-010 | 40 | CI reliability |
| 6 | Add integration tests for critical route modules (orders, results, samples) | TE-01, MTD-010 | 40 | Safety net for refactoring |
| 7 | Add service-level tests for clinical_service, interpretation, ehr_service | TE-02, MTD-010 | 40 | Business logic coverage |
| 8 | Implement rate limiting fail-close with local fallback | SE-05, MTD-010 | 16 | Security hardening |
| 9 | Create staging environment mirroring production | IN-03, OP-02, MTD-008 | 80 | Pre-prod validation |
| 10 | Implement automated secrets rotation pipeline (90-day cycle) | SE-04, MTD-015 | 40 | Credential security |
| 11 | Resolve circular dependencies (7 cycles) | AR-03 | 56 | Import-time crash prevention |
| 12 | Implement CSRF protection middleware | SE-10 | 8 | Web security |
| 13 | Fix 26 layer violations (domain importing FastAPI, services importing DB) | AR-04 | 52 | Architecture boundary enforcement |
| 14 | Add clinical safety E2E test suite (order→collect→result→release→alert) | TE-10, ST-005 | 40 | Clinical workflow validation |
| 15 | Implement result auto-validation engine (Phase 1: Westgard rules) | HC-03, MTD-020 | 50 | Manual validation bottleneck relief |
| 16 | Populate LOINC codes for all test catalog entries | HC-09, MTD-018 | 40 | Terminology standardization |
| 17 | Add OpenAPI diff-based changelog generation in CI | DO-02, 3.4 | 8 | API consumer communication |
| 18 | Add frontend security testing (npm audit, ESLint security, ZAP scan) | SE-12 | 16 | Client-side vulnerability detection |
| 19 | Complete SNDHS Phase 1 integration tests | MT-002 | 40 | SNDHS data integrity |
| 20 | Improve test coverage threshold enforcement in CI (70% overall, 90% critical) | TE-07 | 4 | Quality gate |

**Dependencies:** H1 complete (legal foundation, CI gates, SBOM/secrets scanning)

**Exit Criteria:**
- [ ] All P0 items resolved; all P1 items in active remediation
- [ ] PostgreSQL HA deployed and verified with automated failover
- [ ] JWT migrated to RS256 with JWKS endpoint
- [ ] Test coverage ≥ 60% (routes + services combined)
- [ ] 268 fixture errors resolved; pytest-randomly passes
- [ ] Panic value escalation engine live in production
- [ ] Staging environment operational
- [ ] Architecture gates passing; circular dependencies = 0
- [ ] Quality Index ≥ 700

**Risk:**
- PG HA migration causes downtime → schedule maintenance window; practice rollback
- Test coverage improvement slower than estimated → prioritize clinical and security routes
- Secrets rotation pipeline breaks auth → implement staggered rollout with canary
- Firewall migration for staging environment delayed → use namespace isolation on same cluster

**Resources:** 5-7 engineers (2 backend, 1 DevOps, 1 QA, 1 security, 1 clinical, 1 platform)

---

### H3 — Architecture Modernization (Months 4-6)

**Objective:** Achieve GOLD certification by extracting the domain layer, implementing CQRS, enforcing hexagonal architecture, and resolving the highest-leverage architecture debt.

**Items:**

| # | Item | Source ID | Effort (h) | Impact |
|---|------|-----------|-----------|--------|
| 1 | Extract main.py (1,948 lines) into modular initialization components | MTD-013 | 40 | Single-file bottleneck relief |
| 2 | Begin domain layer refactoring: establish bounded context map | MTD-012, AR-01 | 120 | Foundation for all architecture work |
| 3 | Implement CQRS for high-volume domains (results, orders) — command side | AR-02, MTD-029 | 80 | Read/write separation |
| 4 | Introduce repository interfaces in domain layer (hexagonal ports) | AR-08 | 60 | DB swap capability |
| 5 | Consolidate dual circuit breaker + dual feature flag + dual DI systems | AR-10, MTD-014 | 160 | Eliminate duplicate infrastructure |
| 6 | Fix 365 cross-domain leakage instances (bounded context enforcement) | AR-05 | 160 | Module coupling reduction |
| 7 | Implement audit_logs time-based partitioning | PF-07, MTD-033 | 16 | Query performance |
| 8 | Squash 47 alembic migrations into single base | PF-05, MTD-025 | 40 | Migration performance |
| 9 | Implement event store table (PostgreSQL JSONB) with replay API | AR-16 | 30 | Event sourcing foundation |
| 10 | Implement predictive adaptive concurrency (moving average response time) | PF-01, MTD-023, MT-001 | 40 | Performance stability |
| 11 | Fix circuit breaker gaps: persistence, half-open timeout, admin API | PF-08, MTD-024, ST-004 | 40 | Self-healing reliability |
| 12 | Enforce ARCH-001/002/003 gates with blocking CI jobs (confirm compliance) | DX-03, 7.1 | 8 | Automated governance |
| 13 | Split monster route files: ehr.py (73KB), compliance.py (47KB), clinical.py (41KB) | AR-07 | 24 | Maintainability |
| 14 | Implement webhook registry with retry, signing, delivery logging | OP-09, MTD-035 | 30 | Integration capability |
| 15 | Deploy OpenTelemetry instrumentation for all route handlers and DB calls | IN-10, MTD-030 | 40 | Distributed tracing |
| 16 | Extend constitution enforcer with missing checks (SBOM, migration, naming) | DX-05, 6.6 | 16 | Automated constitutional compliance |
| 17 | Implement property-based testing for domain logic (order state machine, critical values) | MT-003 | 40 | Edge case coverage |
| 18 | Add no-SQLite-in-tests enforcement; migrate tests to PostgreSQL testcontainer | MTD-032 | 40 | Production-like testing |
| 19 | Create ADR for 4-layer architecture transition; update all docs | AR-13 | 8 | Architecture clarity |
| 20 | Establish data governance framework: catalog, lineage, quality metrics, stewardship | CO-16, 7.5 | 40 | Data quality foundation |
| 21 | Implement clinical safety management system per IEC 62304 (Phase 1: hazard analysis) | CO-17, 7.6 | 40 | Clinical safety governance |

**Dependencies:** H2 complete (test coverage adequate for safe refactoring, CI gates in place)

**Exit Criteria:**
- [ ] Domain layer established for at least 3 bounded contexts (orders, results, samples)
- [ ] CQRS implemented for results domain (commands return IDs, not data)
- [ ] Dual systems consolidated into single circuit breaker, feature flags, DI
- [ ] Zero circular dependencies; all architecture gates passing
- [ ] main.py extracted into modular components
- [ ] Quality Index ≥ 800
- [ ] GOLD certification achieved
- [ ] Architecture Compliance ≥ 60/100
- [ ] Event store operational with replay API

**Risk:**
- Domain refactoring breaks working production code → strangler fig pattern; feature-flag all new paths
- CQRS complexity exceeds team capacity → implement read models first; defer full CQRS
- Migration squash loses git blame history → mark old migrations as superseded; don't delete
- Dual system consolidation causes regression → comprehensive integration test suite required before
- Team cognitive load from parallel refactoring → phase items; no more than 3 major refactors concurrently

**Resources:** 6-8 engineers (3 backend, 1 DevOps, 1 QA, 1 platform architect, 1 data engineer, 1 clinical safety)

---

### H4 — Clinical Safety & AI (Months 7-12)

**Objective:** Implement full AI governance framework, build clinical safety suite, expand FHIR coverage, and harden the platform for production-critical clinical use.

**Items:**

| # | Item | Source ID | Effort (h) | Impact |
|---|------|-----------|-----------|--------|
| 1 | Implement AI explainability layer: feature attribution, confidence scores, source references | AI-01, MTD-005, 11.5 | 80 | Clinical AI safety |
| 2 | Implement hallucination detection: factual consistency checker, source grounding, confidence gating | AI-02, MTD-005, 11.6 | 80 | Prevent false clinical information |
| 3 | Build model registry: version control, provenance, validation status | AI-04, MTD-005, 11.3 | 40 | AI model lineage |
| 4 | Implement prompt registry: version control, diff review, approval workflow | AI-05, MTD-005, 11.4 | 30 | Prompt governance |
| 5 | Implement bias detection pipeline: demographic parity, equal opportunity monitoring | AI-06, 11.7 | 40 | Ethical AI |
| 6 | Implement AI audit trail: immutable chain, input/output capture, model version tracking | AI-07, 11.8 | 24 | AI traceability |
| 7 | Build model validation pipeline: automated tests, A/B testing, gated promotion | AI-08, 11.9 | 60 | Model quality assurance |
| 8 | Implement model monitoring / drift detection: data drift, concept drift, auto-alerting | AI-12, 11.10 | 30 | Production model health |
| 9 | Deploy RAG system with pgvector and embedding pipeline | AI-03, MTD-021, 11.1 | 60 | Clinical reference retrieval |
| 10 | Implement MCP servers for database, API, and data analysis tool access | AI-11, 11.2 | 40 | AI agent capabilities |
| 11 | Consolidate dual AI engines: deprecate routes/ai.py; unify on services/ai | AI-10, MTD-026 | 20 | AI codebase consolidation |
| 12 | Complete FHIR core resources: Patient, Observation, DiagnosticReport, ServiceRequest, Specimen, Practitioner, Organization, Encounter | HC-06, MTD-006 | 120 | Interoperability |
| 13 | Implement HL7 v2.x parser: ADT, ORM, ORU, MFN, SIU message types | HC-07 | 80 | Hospital system integration |
| 14 | Implement delta check engine for patient trend analysis | HC-04, MTD-020 | 30 | Clinical safety |
| 15 | Implement barcode/RFID sample tracking (chain of custody) | HC-05, 4.4 | 40 | Sample safety |
| 16 | Implement result auto-validation Phase 2: delta checks, reference ranges, critical flags | HC-03, MTD-020 | 50 | Automated validation |
| 17 | Implement instrument bidirectional interface (HL7 ORM order messages) | HC-11, MTD-019 | 40 | Device workflow |
| 18 | Implement IHE profiles: LTW (lab), PIX/PDQ (patient identity) | HC-14 | 30 | Cross-enterprise workflows |
| 19 | Implement administrative API for platform management and tenant provisioning | OP-08, 3.3 | 40 | Operational self-service |
| 20 | Implement data retention policy enforcement (25y clinical, 10y results, 7y audit) | OP-07, CO-13, D06 | 20 | Regulatory compliance |
| 21 | Complete ISO 15189 gap analysis; implement missing controls | CO-07, 10.1 | 60 | Lab accreditation |
| 22 | Conduct IEC 62304 clinical safety hazard analysis for all AI features | CO-17 | 40 | Clinical safety governance |

**Dependencies:** H3 complete (domain layer in place, event store operational, architecture gates passing)

**Exit Criteria:**
- [ ] All 10 AI governance components operational (explainability, hallucination, model registry, prompt registry, bias, audit, validation, monitoring, RAG, MCP)
- [ ] AI consolidated into single service with full audit trail
- [ ] FHIR core 8 resources implemented and tested
- [ ] HL7 v2.x parser supporting 5 message types
- [ ] Clinical safety suite live: delta check, barcode tracking, auto-validation, panic escalation
- [ ] ISO 15189 gap analysis complete
- [ ] Quality Index ≥ 850
- [ ] Architecture Compliance ≥ 70/100
- [ ] Healthcare Compliance ≥ 80/100

**Risk:**
- AI hallucination detection is imperfect → shadow-mode all AI outputs for 30 days; always require human confirmation
- FHIR implementation scope too large → prioritize Patient, Observation, DiagnosticReport first; defer remaining
- HL7 v2 parser fails on real hospital messages → extensive field testing with partner hospitals before production
- Clinical safety hazard analysis reveals unknown risks → document and mitigate before releasing AI features
- Model validation pipeline delays AI deployment → manual validation gate as interim measure

**Resources:** 8-10 engineers (2 AI/ML, 3 backend, 1 clinical informatics, 1 security, 1 QA, 1 compliance, 1 DevOps)

---

### H5 — National Readiness (Months 13-24)

**Objective:** Achieve PLATINUM-level readiness for national-scale deployment: complete FHIR R4 compliance, SNDHS Phase 2 live, national ID fully enabled, multi-country architecture foundation, and MoH certification.

**Items:**

| # | Item | Source ID | Effort (h) | Impact |
|---|------|-----------|-----------|--------|
| 1 | Complete FHIR R4 full compliance (all relevant resources for lab domain) | HC-06, MTD-006 | 120 | National interoperability |
| 2 | Enable SNDHS Phase 2: result submission to SNDHS, patient lookup | SNDHS Phase progression | 160 | National health data exchange |
| 3 | Enable SNDHS_ENABLE_VISITS and SNDHS_ENABLE_NATIONAL_ID flags after backfill | SNDHS Phase 1 flags | 40 | Full SNDHS integration |
| 4 | Run SNDHS Phase 1 backfill for existing data | scripts/sndhs_phase1_backfill.py | 40 | Data completeness |
| 5 | Implement E2E test suite for clinical workflows (Playwright, 20 journeys) | TE-06, MTD-011 | 160 | Quality assurance |
| 6 | Add frontend tests (Jest + React Testing Library + Playwright) | TE-05, MTD-011 | 80 | Frontend quality |
| 7 | Implement FHIR-based patient identity cross-referencing (PIX/PDQ) | HC-14 | 40 | Patient matching |
| 8 | Implement clinical terminology population: SNOMED CT, ICD-10/11 | HC-09, MTD-018 | 80 | Terminology standardization |
| 9 | Deploy DICOM server (Orthanc/DCM4CHEE) with WADO-RS and STOW-RS | HC-08 | 60 | Medical imaging |
| 10 | Implement CDS rule engine (evaluate on result entry and order creation) | HC-10 | 60 | Clinical decision support |
| 11 | Build physician portal with result dashboard, trend charts, order entry | HC-12, 4.6 | 120 | Referring physician adoption |
| 12 | Build patient mobile app (result viewing, appointment booking, messaging) | HC-13, 4.7 | 160 | Patient engagement |
| 13 | Complete ISO 15189 full compliance framework | CO-07 | 60 | Lab accreditation |
| 14 | Complete ISO 27001 certification (SoA, internal audit, management review) | CO-08, 10.2 | 80 | Security certification |
| 15 | Prepare for Iraqi MoH formal certification submission | CO-09, 10.3 | 60 | Market access |
| 16 | Implement frontend consolidation: deprecate client/; migrate features to frontend-v2 | MTD-027 | 200 | Frontend unification |
| 17 | Implement outbox pattern monitoring: queue depth, latency, failure rate | OP-05, ST-006 | 16 | Event delivery reliability |
| 18 | Implement business metrics dashboard (Grafana): orders/hour, TAT, active labs | IN-11, 9.3 | 20 | Operational visibility |
| 19 | Implement clinical alerting: TAT breach, instrument downtime, critical delays | IN-12, 9.5 | 24 | Clinical operations |
| 20 | Implement automated recovery testing (monthly constitutional mandate) | IN-13, 9.6 | 16 | DR validation |
| 21 | Implement service health dashboard with SLO compliance tracking | C3 (Evolution Plan) | 40 | Service visibility |
| 22 | Implement SMS/WhatsApp notification integration (Twilio/360dialog) | C7 (Evolution Plan) | 40 | Patient communication |
| 23 | Implement synthetic monitoring for 5-10 critical user paths | IN-05, MTD-038 | 40 | Proactive availability |
| 24 | Implement chaos engineering in CI: monthly automated failure scenarios | IN-07, MTD-039 | 40 | Resilience validation |
| 25 | Implement performance regression test harness in CI | PF-03, MTD-031, ST-003 | 40 | Performance quality gate |
| 26 | Create staging K8s environment; begin K8s production pilot | PLATFORM_EVOLUTION Phase 2 | 80 | Orchestration migration |
| 27 | Implement proficiency testing module (IQ-MOH-007) | CO-18, 10.4 | 20 | Lab licensing compliance |
| 28 | Implement processing activity register (IQ-MOH-016 / ROPA) | OP-11, 10.5 | 16 | Data protection compliance |
| 29 | Implement DPIA workflow (IQ-DPL-006) | OP-12, 10.6 | 16 | Privacy impact assessments |
| 30 | Implement cross-border data transfer impact assessment (IQ-DPL-007) | CO-19, 10.7 | 16 | International compliance |

**Dependencies:** H4 complete (AI governance, clinical safety, FHIR 8 resources, HL7 v2 parser)

**Exit Criteria:**
- [ ] FHIR R4 complete for lab domain resources (20+ resource types)
- [ ] SNDHS Phase 2 operational: results submitted and patients resolved via national ID
- [ ] SNDHS flags enabled on production data after backfill validation
- [ ] ISO 15189 framework complete; ISO 27001 certification in progress
- [ ] MoH certification gap analysis complete; remediation plan approved
- [ ] E2E test suite for 20 critical clinical journeys passing in CI
- [ ] Physician portal and patient mobile app beta-ready
- [ ] Frontend consolidated from 3 to 2 (frontend-v2 + PWA); client/ deprecated
- [ ] All regulatory compliance items (IQ-MOH, IQ-DPL) implemented
- [ ] Quality Index ≥ 870
- [ ] Architecture Compliance ≥ 75/100
- [ ] Test Coverage ≥ 70%
- [ ] Healthcare Compliance ≥ 85/100

**Risk:**
- SNDHS Phase 2 API is unstable or undocumented → build integration with retry and degraded mode; engage MoH technical team early
- National ID backfill reveals data quality issues → implement data cleansing pipeline before flag enablement
- ISO 27001 audit reveals major gaps → prioritize remediation before formal audit; engage external auditor early
- Patient mobile app development scope too large → MVP with result viewing only; defer appointment booking and messaging
- Physician portal adoption lower than expected → co-design with 3-5 pilot physicians before general release
- Frontend consolidation causes user disruption → maintain both frontends during transition period; feature-flag new UI

**Resources:** 10-12 engineers (3 backend, 2 frontend, 1 mobile, 1 DevOps, 1 QA, 1 clinical informatics, 1 compliance, 1 AI, 1 security)

---

### H6 — Platform Evolution (Months 25-36)

**Objective:** Achieve full PLATINUM certification, establish platform ecosystem, expand to multiple countries, deploy AI mesh, and complete the transformation to a domain-driven service-oriented architecture.

**Items:**

| # | Item | Source ID | Effort (h) | Impact |
|---|------|-----------|-----------|--------|
| 1 | Extract Auth Service (standalone OAuth 2.0/OIDC service) | S1 (Evolution Plan) | 120 | Foundation for all service extraction |
| 2 | Extract Device Bridge Integration API | S2 (Evolution Plan) | 80 | Service boundary |
| 3 | Extract Notification Service | S3 (Evolution Plan) | 80 | Scalable notifications |
| 4 | Extract Sample Management Service | S4 (Evolution Plan) | 100 | Domain service |
| 5 | Extract Results Service (strangler fig: new results → new service) | S5 (Evolution Plan) | 160 | High-complexity extraction |
| 6 | Extract Orders Service (state machine + routes) | S6 (Evolution Plan) | 120 | Order domain service |
| 7 | Build Financial Engine Phase B (invoicing, payment tracking, insurance claims) | S7 (Evolution Plan), 2.1 | 120 | Revenue operations |
| 8 | Extract AI Service (dedicated inference infrastructure) | S8 (Evolution Plan) | 80 | Independent AI scaling |
| 9 | Extract Patient/MPI Service | S9 (Evolution Plan) | 100 | Patient registry service |
| 10 | Extract Edge Synchronization Service | S10 (Evolution Plan) | 80 | Edge scalability |
| 11 | Implement gRPC endpoints for high-volume domains (results ingestion, batch) | DX-10, 3.6 | 40 | Internal performance |
| 12 | Implement FHIR R4 compliance layer (translation service) | C4 (Evolution Plan) | 80 | National HIE readiness |
| 13 | Implement multi-language support (Kurdish, Farsi, Turkish) | C6 (Evolution Plan) | 80 | Regional expansion |
| 14 | Implement payment gateway integration (AsiaCell, ZainCash, Stripe) | C8 (Evolution Plan) | 60 | Revenue enablement |
| 15 | Implement telemedicine / referral platform | C9 (Evolution Plan) | 120 | Clinical network |
| 16 | Implement population health dashboard (anonymized, aggregate) | C10 (Evolution Plan) | 80 | Epidemiological monitoring |
| 17 | Implement AI mesh: orchestrator, edge inference, model registry integration | 9.1 (Future Architecture) | 120 | AI platform |
| 18 | Consolidate AI codebase: merge top-level ai/ + backend/app/ai/ + services/ai/ | M5, R3 (Evolution Plan) | 40 | AI unification |
| 19 | Implement OpenAPI SDK generation for Python, TypeScript, Java | DO-06, MTD-037 | 80 | Developer ecosystem |
| 20 | Build public API catalog with search, auth requirements, rate limits | DO-07, 3.5 | 40 | Developer portal |
| 21 | Implement event catalog / schema registry (AsyncAPI + Redpanda/Apicurio) | C2 (Evolution Plan) | 60 | Event governance |
| 22 | Merge NHOP into GULA mesh or add event bridge | M1 (Evolution Plan) | 60 | Platform unification |
| 23 | Retire static HTML PWA (frontend/) — archive directory | R1 (Evolution Plan) | 20 | Cleanup |
| 24 | Retire services/autonomous_manager/ stub | R4 (Evolution Plan) | 20 | Cleanup |
| 25 | Implement K8s production migration (multi-region pilot) | IN-10, OP-10 | 160 | Orchestration upgrade |
| 26 | Implement mTLS with internal CA for all inter-service communication | SE-02, MTD-004 | 240 | Zero Trust foundation |
| 27 | Complete Firebase full migration: proxy all access through backend | SE-01, MTD-001 | 160 | Eliminate bypass risk |
| 28 | Achieve Iraqi MoH formal certification | CO-09 | 60 | Market validation |
| 29 | Complete WHO digital health standards alignment | ROADMAP_2050 Phase 2 | 80 | International readiness |
| 30 | Implement clinical trial support module | C12 (Evolution Plan) | 80 | Research capability |

**Dependencies:** H5 complete (national readiness, certifications in progress, SNDHS Phase 2 live)

**Exit Criteria:**
- [ ] 12+ domain services operational behind service mesh
- [ ] mTLS enforced between all inter-service communication
- [ ] Firebase fully migrated: zero direct Firestore access from frontend
- [ ] FHIR R4 compliance layer operational for all core lab resources
- [ ] Multi-language support (Arabic + Kurdish + Farsi + Turkish)
- [ ] Payment gateway live in at least 1 country
- [ ] AI mesh with edge inference deployed in 50+ labs
- [ ] Public API catalog and SDK generation automated in CI
- [ ] MoH certification achieved
- [ ] K8s production with multi-region pilot (2 regions)
- [ ] Quality Index ≥ 900
- [ ] Architecture Compliance ≥ 80/100
- [ ] Test Coverage ≥ 80%
- [ ] Security Score ≥ 95%
- [ ] Debt Resolution ≥ 90%
- [ ] PLATINUM certification achieved

**Risk:**
- Service extraction breaks tenant isolation → comprehensive isolation test suite; feature-flag every extraction
- mTLS rollout breaks existing service communication → maintain HTTP fallback for legacy services during transition
- Payment gateway integration faces regulatory hurdles → engage Iraqi Central Bank and licensed payment partners early
- K8s operational complexity overwhelms team → stay on Docker Compose + HAProxy if team not ready; use managed K8s
- Multi-language support scope underestimated → prioritize Kurdish (most common second language); defer Farsi and Turkish
- Firebase migration disrupts existing frontend-v2 users → maintain backward compatibility during transition; feature-flag new proxy path
- mTLS 480h estimate is large → phase over 2 quarters; prioritize PHI-transmitting services first

**Resources:** 10-14 engineers (4 backend, 2 frontend, 1 mobile, 2 DevOps/SRE, 1 QA, 1 security, 1 AI/ML, 1 clinical informatics, 1 compliance)

---

## 4. Quick Wins (H1 — Days 1-30)

20 high-impact, low-effort items that can be executed immediately:

| # | Item | Effort (h) | Turnaround | Quality Index Impact | Owner Recommendation |
|---|------|-----------|-----------|---------------------|---------------------|
| 1 | Add AGPL v3 LICENSE file | 8 | 1 day | +5 (legal clarity) | Legal/Founder |
| 2 | Add SBOM generation to CI | 8 | 1 day | +3 (supply chain) | DevOps |
| 3 | Add Gitleaks secret scanning to CI | 4 | 0.5 day | +4 (security) | DevOps |
| 4 | Add pre-commit hook (flake8) | 4 | 0.5 day | +2 (code quality) | Platform Engineering |
| 5 | Write 5 missing ADRs | 9 | 2 days | +5 (architecture clarity) | Backend Lead |
| 6 | Canonicalize version to single source | 8 | 1 day | +2 (documentation) | DevOps |
| 7 | Fix Pydantic V2 deprecation warnings | 20 | 3 days | +3 (clean code) | Backend Team |
| 8 | Add security.txt | 1 | 0.5 day | +1 (security) | Security Lead |
| 9 | Add database indexes for slow queries | 8 | 1 day | +8 (performance) | Backend Lead |
| 10 | Add `make quality` shortcut | 4 | 0.5 day | +2 (developer velocity) | Platform Engineering |
| 11 | Add migration round-trip verification to CI | 8 | 1 day | +5 (deployment safety) | Backend Lead |
| 12 | Fix x-content-type-options header | 2 | 0.5 day | +1 (security) | Backend Team |
| 13 | Add README to 4 undocumented modules | 8 | 1 day | +3 (documentation) | Quality Engineering |
| 14 | Add system_ready startup log | 4 | 0.5 day | +1 (operations) | Backend Lead |
| 15 | Add pytest-randomly | 4 | 0.5 day | +4 (test reliability) | Quality Engineering |
| 16 | Add backup restore testing automation | 40 | 5 days | +15 (DR validation) | DevOps |
| 17 | Update CLAUDE.md with accurate counts | 8 | 1 day | +3 (documentation) | Platform Engineering |
| 18 | Fix MySQL references to PostgreSQL | 2 | 0.5 day | +1 (documentation) | Backend Team |
| 19 | Remove external AI providers | 16 | 2 days | +10 (regulatory compliance) | AI Lead |
| 20 | Lockdown Firebase (interim) | 80 | 10 days | +20 (security) | Security Lead |
| **Total** | **~200h** | **—** | **+100 potential QI gain** | **—** |

---

## 5. Critical Fixes (H2 — Days 31-90)

### P0/P1 Items That Must Be Resolved

| Priority | Item | Effort (h) | Risk if Deferred |
|----------|------|-----------|-----------------|
| P0 | PostgreSQL HA (Patroni) | 120 | Single PG failure = complete platform outage |
| P0 | JWT RS256 migration + JWKS | 28 | Key compromise allows token forgery |
| P0 | Panic value escalation | 40 | Patient death from delayed critical result notification |
| P0 | Firebase security bypass (lockdown) | 80 | Catastrophic PHI exposure |
| P1 | 268 fixture errors | 40 | CI unreliability; false confidence |
| P1 | Route test coverage (critical paths) | 40 | Production regressions undetected |
| P1 | Service test coverage (clinical logic) | 40 | Business logic defects in production |
| P1 | Rate limiting fail-close | 16 | All rate limits bypassed during Redis outage |
| P1 | Staging environment | 80 | Deployment risk without pre-prod validation |
| P1 | Secrets rotation pipeline | 40 | Credential aging; breach risk |
| P1 | Circular dependencies (7 cycles) | 56 | Import-time crashes |
| P1 | Layer violations (26 instances) | 52 | Architecture drift; framework coupling |
| P1 | CSRF protection | 8 | Cross-site request forgery vulnerability |

### Layer Violations Remediation (H2 Focus)

| Violation Type | Count | Remediation Approach |
|---------------|-------|---------------------|
| Domain importing from FastAPI | ~8 | Extract framework dependency; use dependency injection |
| Services importing DB directly | ~10 | Introduce repository interfaces |
| Routes importing models | ~8 | Route should only import service interfaces |
| Cross-domain imports (H3) | 365 | Establish bounded contexts; enforce with import-lint in CI |

### Coverage Improvement Targets

| Area | Current | H2 Target | Method |
|------|---------|-----------|--------|
| Route test coverage | 35% | 60% | Integration tests for 20 uncovered route modules |
| Service test coverage | 30% | 60% | Unit tests for 15 uncovered service files |
| Clinical workflow E2E | 0% | 1 pathway | Playwright: order→collect→result→release→alert |
| Edge/interop coverage | 0% | 20% | Basic smoke tests for edge connectors |
| Frontend coverage | 0% | 20% | Jest + React Testing Library for core components |

### Infrastructure Hardening

| Component | Current State | H2 Target State |
|-----------|--------------|-----------------|
| PostgreSQL | Single instance, no HA | Patroni cluster (1 primary + 1 replica) + pgBouncer |
| Backup validation | Unverified | Automated weekly restore test with integrity validation |
| Secrets rotation | Manual, never done | Automated 90-day rotation pipeline with staggered rollout |
| Staging environment | None | Docker Compose staging mirroring production topology |
| CI architecture gates | None | ARCH-001/002/003 blocking gates operational |

---

## 6. Architecture Modernization (H3 — Months 4-6)

### Domain Layer Extraction

| Bounded Context | Current Location | Target Structure | Effort (h) |
|----------------|-----------------|------------------|-----------|
| Orders | routes/orders.py + models/order.py | domain/order/ + application/order/ + infrastructure/order/ | 120 |
| Results | routes/results.py + models/result.py | domain/result/ + application/result/ + infrastructure/result/ | 120 |
| Samples | routes/samples.py + models/sample.py | domain/sample/ + application/sample/ + infrastructure/sample/ | 80 |
| Patients | routes/patients.py + services/mpi/ | domain/patient/ + application/patient/ + infrastructure/patient/ | 80 |

### CQRS/Event Sourcing Implementation

| Domain | Command Side | Query Side | Timeline |
|--------|-------------|------------|----------|
| Results | Write-optimized (current monolith DB) | Materialized views for result history | H3 Phase 1 |
| Orders | Write-optimized (current monolith DB) | Order status materialized view | H3 Phase 2 |
| Audit | Append-only event store | Search-optimized audit index | H4 |

### Layer Compliance Gates (from QUALITY_GATE_RULES.md)

| Gate | Rule | Enforcement |
|------|------|-------------|
| ARCH-001 | Layer boundaries: domain may not import FastAPI/SQLAlchemy | Import lint check in CI |
| ARCH-002 | Zero circular dependencies | Tarjan's SCC algorithm in CI |
| ARCH-003 | Naming conventions: packages follow domain/application/infrastructure | Naming lint in CI |
| ARCH-004 | No cross-domain imports outside bounded context | Import graph analysis in CI |

### Performance Optimization Targets

| Metric | Current (p50/p95) | H3 Target (p50/p95) |
|--------|-------------------|---------------------|
| Result submission | 120ms / 450ms | 80ms / 250ms |
| Order creation | 100ms / 350ms | 70ms / 200ms |
| Patient lookup | 80ms / 300ms | 50ms / 150ms |
| Dashboard load | 500ms / 2s | 200ms / 800ms |
| API response (overall) | 100ms / 500ms | 80ms / 300ms |

---

## 7. Clinical Safety & AI (H4 — Months 7-12)

### Clinical Safety Program

| Component | Standard | Effort (h) | Priority |
|-----------|----------|-----------|----------|
| Hazard analysis for all clinical features | IEC 62304 | 40 | P1 |
| Clinical risk management file | ISO 14971 | 40 | P1 |
| Software safety classification | IEC 62304 §5 | 20 | P1 |
| Clinical validation protocol | CLSI guidelines | 30 | P1 |
| Post-market surveillance plan | ISO 13485 | 20 | P2 |
| Clinical safety case report | — | 30 | P2 |

### AI Governance Framework

| Component | Constitution § | Status | H4 Target |
|-----------|---------------|--------|-----------|
| Explainability layer | §5.2 | NOT IMPLEMENTED | Every AI output includes explanation |
| Hallucination detection | §5.7 | NOT IMPLEMENTED | Factual consistency checker + confidence gating |
| Model registry | §5.4 | NOT IMPLEMENTED | Version, provenance, validation status |
| Prompt registry | §5.3 | NOT IMPLEMENTED | Versioned, immutable, approval workflow |
| Bias detection | §5.8 | NOT IMPLEMENTED | Demographic parity + equal opportunity monitoring |
| AI audit trail | §5.9 | NOT IMPLEMENTED | Immutable chain with input/output capture |
| Model validation pipeline | §5.5 | NOT IMPLEMENTED | Automated test suite + A/B testing + gated promotion |
| Model monitoring / drift | §5.6 | NOT IMPLEMENTED | Data drift, concept drift, auto-alerting |
| RAG system | §5.1 | NOT IMPLEMENTED | pgvector + embedding pipeline |
| MCP servers | — | NOT IMPLEMENTED | DB access, API integration, data analysis |

### Model Validation Pipeline Architecture

```
Model Candidate → Validation Suite → Shadow Deployment → A/B Test → Production → Monitoring
     │                 │                  │                   │           │           │
     └─ Versioned ────└─ Accuracy ───────└─ Shadow 30d ──────└─ 10% ────└─ Canary ──└─ Drift
        in registry       Bias check       no user impact        traffic    rollout     detection
                          Edge cases                                                                 
```

### Clinical Safety Suite Components

| Component | Description | Effort (h) | H4 Deliverable |
|-----------|-------------|-----------|----------------|
| Panic value escalation | Configurable thresholds, multi-channel notifications, escalation timer | 40 | H2 |
| Result auto-validation | Westgard rules, delta checks, reference ranges, critical flags | 100 | H2-H4 |
| Delta check engine | Automated comparison of current vs historical patient results | 30 | H4 |
| Barcode/RFID tracking | Chain of custody from order entry to disposal | 40 | H4 |
| Critical alerting | TAT breach, instrument downtime, clinically significant delays | 24 | H5 |

---

## 8. National Readiness (H5 — Months 13-24)

### FHIR R4 Full Compliance Plan

| Phase | Resources | Timeline | Effort (h) |
|-------|-----------|----------|-----------|
| Phase 1 | Patient, Observation, DiagnosticReport | H4 (months 7-9) | 40 |
| Phase 2 | ServiceRequest, Specimen, Practitioner, Organization, Encounter | H4 (months 10-12) | 80 |
| Phase 3 | Condition, Medication, ImagingStudy, DocumentReference | H5 (months 13-16) | 60 |
| Phase 4 | Bundle, Subscription, AuditEvent, Provenance | H5 (months 17-20) | 60 |
| Phase 5 | Full R4 compliance verification + FHIRcast | H5 (months 21-24) | 40 |

### SNDHS Production Enablement

| Step | Action | Dependencies | Effort (h) | Timeline |
|------|--------|-------------|-----------|----------|
| 1 | Run data backfill for national_id and visit_id | Migration files applied | 40 | H5 month 13 |
| 2 | Verify backfill integrity with data quality checks | Step 1 complete | 20 | H5 month 13 |
| 3 | Enable SNDHS_ENABLE_NATIONAL_ID flag for 1 lab (pilot) | Steps 1-2 complete | 8 | H5 month 14 |
| 4 | Monitor pilot for 2 weeks; fix issues | Step 3 live | 40 | H5 month 14-15 |
| 5 | Roll out to 10 labs; enable SNDHS_ENABLE_VISITS | Pilot successful | 16 | H5 month 15 |
| 6 | Full production rollout (all labs) | Steps 4-5 complete | 24 | H5 month 16 |
| 7 | Implement SNDHS Phase 2: result submission and patient lookup | Full rollout | 160 | H5 months 17-20 |

### National ID / Visits Enablement

| Component | Migration | Impact | Rollback Plan |
|-----------|-----------|--------|---------------|
| patients.national_id | Encrypted column; HMAC blind index | All patient queries must handle NULL | Disable flag; NULL-safe reads |
| patients.sndhs_health_id | SNDHS-assigned health ID | Dual-read for pre-backfill rows | Disable flag |
| visits table | New table + lab_orders.visit_id FK | Order creation requires visit context when flag enabled | Drop FK; set visit_id to NULL |
| audit_logs v2 | Enhanced audit chain | SNDHS correlation fields in all audit entries | Use v1 fallback |

### Interoperability Standards Roadmap

| Standard | Current State | H5 Target | Effort (h) |
|----------|--------------|-----------|-----------|
| FHIR R4 | 6 resources | 20+ resources (full lab domain) | 240 |
| HL7 v2.x | ASTM only | ADT, ORM, ORU, MFN, SIU | 80 |
| LOINC | Schema only | Full population + mapping service | 40 |
| SNOMED CT | Schema only | Population + mapper from local codes | 40 |
| ICD-10/11 | Schema only | Auto-coding from clinical findings | 40 |
| DICOM | Schema only | Orthanc server + WADO-RS/STOW-RS | 60 |
| IHE | Not implemented | LTW, LDA, PIX/PDQ | 30 |

---

## 9. Platform Evolution (H6 — Months 25-36)

### Service Extraction Sequence

```
Year 1 (Months 1-12)       Year 2 (Months 13-24)       Year 3 (Months 25-36)
─────────────────────       ──────────────────────      ──────────────────────
Monolith (BRONZE)          Modular Monolith (GOLD)     Service Mesh (PLATINUM)
                                                             │
                                                       ┌─────┼─────┬─────┬─────┐
                                                       │     │     │     │     │
                                                     Auth  Device Notif Sample
                                                     Svc   Bridge Svc   Svc
                                                       │     │     │     │
                                                     Result Orders Fin.  AI
                                                     Svc    Svc   Svc   Svc
                                                       │     │     │
                                                     Patient Edge  Audit
                                                     Svc   Sync   Svc
                                                       Svc
```

### Service Extraction Dependencies

```
Auth Service ─────────────────────────────────────────────────────────────────
    │
    ├── Device Bridge API ────────────────────────────────────────────────────
    ├── Notification Service ──────────────────────────────────────────────────
    │
    ├── Sample Management ────────────┐
    │                                 ├── Results Service ────┐
    │                                 │                       ├── Orders Service
    │                                 │                       │
    │                                 ├── Patient/MPI ────────┤
    │                                 │                       ├── Edge Sync ──────► Audit Svc
    │                                 │                       │
    │                                 └── Financial Engine ───┘
    │
    └── AI Service ───────────────────────────────────────────────────────────► Stats Svc
```

### Ecosystem Platform Components

| Component | Description | Target Labs | Timeline |
|-----------|-------------|-------------|----------|
| Developer SDK | Auto-generated Python/TypeScript/Java SDK from OpenAPI | 50+ labs integrating | H6 month 25 |
| API Catalog | Searchable catalog of all APIs with auth requirements, rate limits | All developers | H6 month 26 |
| Webhook System | Event-driven integration for EMRs, HIS, and third-party apps | 20+ hospital integrations | H6 month 27 |
| Connector Marketplace | Community-contributed device drivers, protocol adapters, FHIR mappings | 50+ connectors | H6 month 30 |
| Partner Program | Certification, support tiers, revenue share for implementation partners | 10+ partners | H6 month 33 |
| Plugin Architecture | Python entry-point-based plugins for custom lab workflows | Enterprise customers | H6 month 34 |
| App Marketplace | Third-party apps built on GULA platform API | 20+ apps | H6 month 36 |

### National Intelligence Platform

| Capability | Description | Data Sources | Timeline |
|-----------|-------------|-------------|----------|
| Population Health Dashboard | Anonymized disease prevalence, test volume trends, regional health indicators | All labs (aggregate) | H6 month 28 |
| Outbreak Detection | Real-time anomaly detection for notifiable diseases | Result data + geographic | H6 month 30 |
| Public Health Reporting | Automated reporting to MoH, WHO compliance | Configurable data sets | H6 month 32 |
| Cross-Region Analytics | Multi-country aggregate health intelligence | Multiple country deployments | H6 month 34 |
| AI Population Models | Predictive models for disease spread, resource needs | Historical + real-time data | H6 month 36 |

---

## 10. Investment Summary

| Horizon | Engineering (h) | Engineering Cost ($150/h) | Infrastructure ($) | External/Compliance ($) | Total ($) |
|---------|----------------|--------------------------|-------------------|----------------------|-----------|
| **H1** (Days 1-30) | ~200 | $30,000 | $5,000 | $15,000 (legal incorporation) | $50,000 |
| **H2** (Days 31-90) | ~600 | $90,000 | $25,000 (PG HA infra, staging) | $10,000 (security audit) | $125,000 |
| **H3** (Months 4-6) | ~1,200 | $180,000 | $15,000 (event store, tracing) | $5,000 | $200,000 |
| **H4** (Months 7-12) | ~1,500 | $225,000 | $30,000 (pgvector, RAG infra, DICOM) | $40,000 (IEC 62304, ISO 15189) | $295,000 |
| **H5** (Months 13-24) | ~2,000 | $300,000 | $100,000 (K8s infra, staging prod, SNDHS) | $80,000 (ISO 27001, MoH cert) | $480,000 |
| **H6** (Months 25-36) | ~1,500 | $225,000 | $150,000 (service mesh, multi-region) | $100,000 (mTLS CA, WHO alignment) | $475,000 |
| **Total** | **~7,000h** | **$1,050,000** | **$325,000** | **$250,000** | **$1,625,000** |

### Ramp Schedule

| Period | Engineers | Monthly Burn | Cumulative |
|--------|-----------|-------------|------------|
| Months 1-3 (H1-H2) | 4-5 | $40,000 | $120,000 |
| Months 4-6 (H3) | 6-8 | $65,000 | $315,000 |
| Months 7-12 (H4) | 8-10 | $85,000 | $825,000 |
| Months 13-24 (H5) | 10-12 | $105,000 | $2,085,000 |
| Months 25-36 (H6) | 10-14 | $120,000 | $3,525,000 |

### Funding Strategy

| Source | Amount | Timeline | Purpose |
|--------|--------|----------|---------|
| Seed round | $2M | Month 1-3 | H1-H4 (first 12 months) |
| Early enterprise revenue | $250K-$500K | Months 6-12 | Partial H5 funding |
| Grant (World Bank / EU / Gates) | $500K-$5M | Months 6-18 | National readiness, SNDHS, AI safety |
| Series A | $10M | Months 12-18 | H5-H6 + regional expansion |
| Government contracts | $500K+/year | Months 18+ | Ongoing revenue |

---

## 11. Success Metrics Dashboard

### Quality Index Progression

| Milestone | Current | H1 | H2 | H3 | H4 | H5 | H6 |
|-----------|---------|----|----|----|----|----|----|
| **Quality Index** | **673** | 700 | 750 | 800 | 850 | 870 | 900+ |
| Architecture Compliance | 7/100 | 30 | 50 | 60 | 70 | 75 | 80+ |
| Test Coverage | 54% | 56% | 60% | 65% | 70% | 75% | 80+% |
| Security Score | 85% | 88% | 90% | 92% | 93% | 94% | 95+% |
| Healthcare Compliance | 72% | 72% | 75% | 78% | 82% | 87% | 90+% |
| CI/CD Maturity | 88% | 90% | 92% | 94% | 95% | 95% | 95+% |
| Debt Resolution % | 0% | 10% | 25% | 40% | 55% | 70% | 90+% |
| P0 Count | 5 | 0 | 0 | 0 | 0 | 0 | 0 |
| P1 Count | 27 | 20 | 5 | 2 | 0 | 0 | 0 |
| Certification | BRONZE | BRONZE | SILVER | GOLD | GOLD+ | PLATINUM (entry) | PLATINUM |

### Operational Metrics

| Metric | Current | H1 | H2 | H3 | H4 | H5 | H6 |
|--------|---------|----|----|----|----|----|----|
| Uptime (monthly) | 99.5% | 99.5% | 99.7% | 99.8% | 99.9% | 99.95% | 99.99% |
| API p50 response | 100ms | 100ms | 95ms | 80ms | 80ms | 75ms | 70ms |
| API p99 response | 500ms | 500ms | 450ms | 300ms | 300ms | 250ms | 200ms |
| Deploy frequency | Weekly | Weekly | Semi-weekly | Semi-weekly | Daily | Daily | On-demand |
| MTTR | ~2h | <2h | <1h | <1h | <30min | <30min | <15min |
| Labs served | ~100 | ~100 | ~120 | ~150 | ~200 | ~500 | ~1,000+ |
| Test suite speed | ~15min | ~15min | ~12min | ~10min | ~8min | ~6min | ~5min |
| Migration revisions | 47 | 48 | 48 | 1 (squashed) | 2 | 5 | 10 |
| Circular dependencies | 7 | 7 | 7 | 0 | 0 | 0 | 0 |
| Layer violations | 26 | 26 | 26 | 10 | 0 | 0 | 0 |
| MyPy strict errors | 1,413 | 1,413 | 1,200 | 800 | 400 | 100 | 0 |

### Certification Milestones

| Certificate | Current Target | Target Date | Dependencies |
|-------------|---------------|-------------|-------------|
| SILVER Certification | QI 700+ | Day 90 | H1 + H2 complete |
| GOLD Certification | QI 800+, Arch 60+, Coverage 60% | Month 6 | H3 complete |
| GOLD+ Certification | QI 850+, Arch 70+, AI governance in place | Month 12 | H4 complete |
| PLATINUM (entry) | QI 870+, Arch 75+, Coverage 70%, SNDHS live | Month 24 | H5 complete |
| PLATINUM Certified | QI 900+, Arch 80+, Coverage 80+, Security 95+ | Month 36 | H6 complete |
| ISO 15189 | Complete gap analysis | Month 12 | H4 |
| ISO 27001 | Certification in progress | Month 18 | H5 |
| Iraqi MoH | Formal certification | Month 24 | H5 |
| FHIR R4 | Full compliance | Month 20 | H5 |

---

## 12. Risk Register

| # | Risk | Likelihood | Impact | Mitigation | Horizon |
|---|------|-----------|--------|------------|---------|
| R01 | Legal incorporation takes > 30 days | Medium | High | Parallel-track technical work; engage legal counsel before Day 1 | H1 |
| R02 | Firebase lockdown reveals undocumented dependencies | Medium | High | Maintain interim access; audit all frontend data access patterns before lockdown | H1 |
| R03 | PG HA migration causes production downtime | Medium | Critical | Maintenance window; practice failover/rollback 3x before production cutover | H2 |
| R04 | Test coverage improvement slower than estimated | High | Medium | Target critical clinical/security paths first; defer non-critical coverage | H2 |
| R05 | Domain refactoring breaks production code | Medium | Critical | Strangler fig pattern; feature-flag all new paths; comprehensive test suite required | H3 |
| R06 | CQRS complexity exceeds team capacity | Medium | High | Implement read models first (materialized views); defer full CQRS to H4 | H3 |
| R07 | AI hallucination detection insufficient | Medium | Critical | Shadow-mode all AI outputs for 30 days; always require human confirmation | H4 |
| R08 | FHIR implementation scope too large | High | Medium | Priority order: Patient > Observation > DiagnosticReport > rest | H4 |
| R09 | SNDHS Phase 2 API unstable or undocumented | High | High | Build with retry and degraded mode; engage MoH technical team 3 months before integration | H5 |
| R10 | National ID backfill reveals data quality issues | Medium | High | Implement data cleansing pipeline before flag enablement; run backfill on staging first | H5 |
| R11 | ISO 27001 audit reveals major gaps | Medium | High | Engage external auditor 6 months before audit; prioritize remediation | H5 |
| R12 | Service extraction breaks tenant isolation | Medium | Critical | Automated isolation test suite; feature-flag every extraction | H6 |
| R13 | mTLS rollout breaks service communication | Medium | Critical | Maintain HTTP fallback during transition; phase by service criticality | H6 |
| R14 | K8s complexity exceeds team capability | High | Medium | Stay on Docker Compose + HAProxy fallback; use managed K8s (EKS/AKS) if needed | H6 |
| R15 | Key personnel departure during transition | Medium | High | Document all procedures in ADRs; cross-train all team members; maintain bus factor ≥ 2 | All |

---

## 13. Decision Gates

### Gate G1 — Proceed to H2 (Day 30)
- [ ] P0 count = 0 (all resolved or in active remediation with owner and deadline)
- [ ] Legal entity incorporated; LICENSE file committed
- [ ] Firebase interim lockdown in production
- [ ] Backup restore testing automated and passing
- [ ] Architecture gates enforcing in CI
- [ ] Quality Index ≥ 700

**Pivot if:** Legal incorporation not complete → continue on technical track; re-assess at Day 45
**Stop if:** Firebase lockdown reveals unrecoverable architecture flaw → convene architecture review board

### Gate G2 — Proceed to H3 (Day 90)
- [ ] All P1 items in active remediation with owners
- [ ] PostgreSQL HA deployed; failover tested
- [ ] JWT migrated to RS256 with JWKS
- [ ] Test coverage ≥ 60% (routes + services)
- [ ] 268 fixture errors resolved
- [ ] Staging environment operational
- [ ] Quality Index ≥ 750

**Pivot if:** Firewall migration for staging not feasible → use namespace isolation on existing infra
**Stop if:** PG HA failover consistently fails → engage PostgreSQL specialist before proceeding

### Gate G3 — Proceed to H4 (Month 6)
- [ ] Domain layer established for 3 bounded contexts
- [ ] CQRS live for results domain
- [ ] Dual systems consolidated
- [ ] Zero circular dependencies
- [ ] main.py modularized
- [ ] Event store operational
- [ ] Quality Index ≥ 800; GOLD certification achieved

**Pivot if:** Domain refactoring progress too slow → reduce scope from 3 contexts to 2; defer samples
**Stop if:** Event store introduces data inconsistency → pause; engage DB architect; fall back to outbox-only

### Gate G4 — Proceed to H5 (Month 12)
- [ ] All 10 AI governance components operational
- [ ] AI consolidated into single service
- [ ] FHIR 8 core resources live in production
- [ ] HL7 v2 parser supporting 5 message types
- [ ] Clinical safety suite live (delta check, barcode, auto-validation, panic)
- [ ] ISO 15189 gap analysis complete
- [ ] Quality Index ≥ 850

**Pivot if:** AI hallucination detection < 99% accuracy → extend shadow mode; defer bias detection to H5
**Stop if:** Clinical safety hazards identified but unmitigated → resolve all critical/high hazards before proceeding

### Gate G5 — Proceed to H6 (Month 24)
- [ ] FHIR R4 complete for 20+ lab domain resources
- [ ] SNDHS Phase 2 operational
- [ ] National ID + visits fully enabled after backfill
- [ ] ISO 27001 certification in progress
- [ ] MoH certification gap analysis complete
- [ ] E2E test suite for 20+ clinical journeys passing
- [ ] Physician portal and patient mobile app beta-ready
- [ ] Frontend consolidated (2 remaining: frontend-v2 + PWA)
- [ ] Quality Index ≥ 870

**Pivot if:** MoH certification timeline slips beyond 12 months → defer formal cert; continue with gap analysis
**Stop if:** SNDHS integration reveals fundamental data model incompatibility → convene national health IT architecture board

### Gate G6 — Transformation Complete (Month 36)
- [ ] 12+ domain services operational behind service mesh
- [ ] mTLS enforced for all inter-service communication
- [ ] Firebase fully migrated; zero direct Firestore access
- [ ] FHIR R4 full compliance
- [ ] Multi-language support (4+ languages)
- [ ] Payment gateway live in 1+ country
- [ ] AI mesh with edge inference in 50+ labs
- [ ] Public API catalog + SDK generation in CI
- [ ] MoH certification achieved
- [ ] K8s production with multi-region pilot
- [ ] Quality Index ≥ 900; PLATINUM certification achieved

---

## 14. Dependencies Map

```
H1 (Days 1-30)                    H2 (Days 31-90)                 H3 (Months 4-6)
───────────────                   ────────────────                ────────────────
Legal Entity ──────────────────►  PG HA ──────────────►           Domain Layer
LICENSE ─────────────────────►   JWT RS256 ──────────►           CQRS
Firebase Lockdown ───────────►   Test Coverage ──────►           Event Store
SBOM + Gitleaks ─────────────►   Panic Escalation ───►           Dual System Consolidation
CI Gates ───────────────────────► Staging ───────────►           Migration Squash
ADRs ─────────────────────────►  Circular Deps Fix ──►           Arch Gates Enforce
Backup Restore Testing ──────►   Layer Violations Fix            Circuit Breaker Fix
                                 Secrets Rotation                Tracing (OpenTelemetry)
                                 CSRF                            

H4 (Months 7-12)                 H5 (Months 13-24)               H6 (Months 25-36)
───────────────                  ────────────────                 ────────────────
AI Governance ──────────────►   FHIR R4 Complete ─────────────►  Auth Service Extraction
RAG System ────────────────►   SNDHS Phase 2 ────────────────►  Service Mesh
Clinical Safety Suite ─────►   ISO 15189/27001 ──────────────►  mTLS
FHIR Core Resources ──────►   E2E Test Suite ────────────────►  Firebase Full Migration
HL7 v2 Parser ─────────────►   Physician Portal ──────────────►  Multi-Region K8s
AI Consolidation ──────────►   Patient Mobile App              Plugin Architecture
Model Validation Pipeline ──►  Frontend Consolidation           SDK Generation
                                Chaos Engineering               Connector Marketplace
                                Synthetic Monitoring            AI Mesh
```

---

## 15. Review Cadence

| Frequency | Activity | Participants |
|-----------|----------|-------------|
| **Daily** | Standup: track top 3 items from current horizon | Engineering team |
| **Weekly** | Horizon progress review; update estimates, flag blockers | Tech Lead, Product Manager |
| **Bi-weekly** | Quality Index recalculation; gate readiness assessment | Platform Engineering |
| **Monthly** | Full horizon review; adjust scope/resources; update risk register | Technical Review Board |
| **Quarterly** | Transformation roadmap grooming; recalculate costs; certify milestones | Leadership + Board |
| **Per release** | Assess items partially resolved; update TRANSFORMATION_ROADMAP.md | Platform Engineering |
| **Annual** | Full roadmap review; close completed horizons; set new targets | Full team + Board |

**Roadmap Owner:** Platform Engineering  
**Next Major Review:** 2026-08-18 (30-day checkpoint)  
**Governance:** Technical Review Board approval required for:
- Horizon scope changes > 20%
- Priority reclassification of P0 items
- Budget reallocation across horizons > 15%
- Decision gate bypass requests

---

## Appendix: Source Cross-Reference

| Source Document | Items Referenced | Horizon(s) |
|----------------|-----------------|------------|
| ENTERPRISE_PRIORITIZATION.md | All 840 backlog items across 13 categories | H1-H6 |
| TECHNICAL_DEBT_MASTER_REGISTER_v2.md | 46 consolidated debt items (MTD-001 to MTD-046) | H1-H6 |
| ARCHITECTURE_GAP_ANALYSIS.md | 77 gaps across 12 categories | H2-H6 |
| DISCOVERY_VALIDATION.md | 71 validated findings (P0-P3) | H1-H6 |
| EXECUTIVE_SUMMARY.md | Top 5 recommendations, 90-day plan | H1-H2 |
| IMPROVEMENT_BACKLOG.md | 45 items (QW, ST, MT categories) | H1-H5 |
| PLATFORM_EVOLUTION_PLAN.md | 12 service splits, 7 merges, 7 retirements, 16 new capabilities | H3-H6 |
| FUTURE_ARCHITECTURE.md | DDD contexts, CQRS, event storming, multi-region, AI mesh | H4-H6 |
| ROADMAP_2050.md | Strategic phases, 2050 vision | H6+ |

---

*This Transformation Roadmap synthesizes 9 source documents totaling 800+ backlog items, 77 architecture gaps, 71 discovery findings, and 46 consolidated technical debt items into a single, timed execution plan spanning 36 months with 6 horizons. It is the definitive reference for all platform transformation activities and supersedes all previous roadmap documents for the 2026-2029 period.*

*Next revision: 2026-08-18 or earlier if any decision gate conditions change materially.*
