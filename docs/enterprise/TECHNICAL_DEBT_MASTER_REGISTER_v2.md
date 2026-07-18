# GULA Platform — Technical Debt Master Register v2

**Classification:** INTERNAL — Technical Review Board
**Version:** 2.0
**Date:** 2026-07-18
**Sources Consolidated:** 8 documents (see §4)
**Total Unique Items (merged, deduped):** 46
**Total Estimated Hours:** 7,280 (~182 weeks at 40h/wk)
**Annual Interest (est.):** ~$340,000/year (compounding delay cost)

---

## 1. Executive Summary

### Totals

| Metric | Value |
|--------|-------|
| Total unique items | 46 |
| Total estimated hours | 7,280 |
| Total estimated cost (at $150/h) | $1,092,000 |
| Annual technical debt interest (est.) | $340,000 |
| Items with Critical Clinical Risk | 8 |
| Items with Critical Business Risk | 14 |

### Items by Category

| Category | Count | Total Hours | High/Critical Risk |
|----------|-------|-------------|-------------------|
| Architecture | 7 | 2,560 | 5 |
| Security | 6 | 1,040 | 4 |
| Infrastructure | 5 | 880 | 3 |
| Performance | 3 | 400 | 1 |
| Healthcare | 6 | 720 | 4 |
| AI | 5 | 840 | 3 |
| Testing | 5 | 560 | 3 |
| Documentation | 3 | 80 | 0 |
| Operations | 4 | 160 | 1 |
| Developer Experience | 2 | 40 | 0 |

### Items by Priority

| Priority | Count | Definition |
|----------|-------|------------|
| **P0** | 5 | Blocking — deployment, data loss, security breach |
| **P1** | 12 | Critical — patient safety, regulatory, constitutional |
| **P2** | 18 | Major — best practices, tech debt accumulation |
| **P3** | 11 | Minor — cosmetic, naming, documentation |

### Items by Clinical Risk Level

| Risk Level | Count |
|------------|-------|
| Critical | 8 |
| High | 10 |
| Medium | 14 |
| Low | 14 |

### Items by Business Risk Level

| Risk Level | Count |
|------------|-------|
| Critical | 14 |
| High | 15 |
| Medium | 12 |
| Low | 5 |

---

## 2. Master Register

**Cost estimation basis:** $150/h (senior engineer blended rate, Iraq-adjusted)
**ROI:** Low = <1.5x risk reduction vs cost; Medium = 1.5-3x; High = >3x
**Resolution Order:** Sorted by priority (P0→P3), then clinical risk, then business risk, then effort (low-effort high-impact first)

| # | ID | Category | Priority | Description | Source Files | Est. Hrs | Cost ($) | ROI | Business Risk | Clinical Risk | Resolution Order |
|---|----|----------|----------|-------------|-------------|--------|---------|-----|-------------|--------------|-----------------|
| 1 | MTD-001 | Security | P0 | **Firestore security bypass** — frontend-v2 talks directly to Firestore, bypassing backend auth, RBAC, and audit. Catastrophic PHI exposure if Firestore misconfigured or compromised. Any authenticated frontend user can query any document. | `reports/discovery/18_TECHNICAL_DEBT.md:SD04`; `docs/enterprise/DISCOVERY_CONSOLIDATION.md:§11`; `docs/enterprise/ARCHITECTURE_GAP_ANALYSIS.md:§12` | 240 | 36,000 | High | Critical | Critical | 1 |
| 2 | MTD-002 | Infrastructure | P0 | **Single PostgreSQL instance, no HA** — Production runs a single Postgres 16 container. No replication, no failover, no Patroni. Loss of this container = complete platform outage + potential data loss. RTO measured in hours of manual recovery. | `reports/discovery/18_TECHNICAL_DEBT.md:DB04`; `docs/reports/technical_debt_register.md:§Critical`; `docs/enterprise/DISCOVERY_CONSOLIDATION.md:§11` | 240 | 36,000 | High | Critical | Critical | 2 |
| 3 | MTD-003 | Infrastructure | P0 | **No automated backup restore testing** — `make backup` runs nightly but restore is never validated. Backups may be corrupt, incomplete, or incompatible with current schema. DR plan would fail during actual disaster. RPO/RTO targets undefined. | `reports/discovery/18_TECHNICAL_DEBT.md:ID02`; `docs/enterprise/ARCHITECTURE_GAP_ANALYSIS.md:8.3`; `docs/enterprise/DISCOVERY_CONSOLIDATION.md:§11` | 80 | 12,000 | High | Critical | Critical | 3 |
| 4 | MTD-004 | Security | P0 | **mTLS not implemented** — PLATFORM-CONSTITUTION §4.3 mandates mutual TLS between all services. Actual deployment uses HTTP between device-bridge, backend, and internal services. Man-in-the-middle attack vector on unencrypted inter-service PHI transit. | `docs/enterprise/ARCHITECTURE_GAP_ANALYSIS.md:12.3`; `docs/technical-debt/REGISTRY.md:TD-3888`; `docs/enterprise/DISCOVERY_CONSOLIDATION.md:§12(C6)` | 480 | 72,000 | Medium | Critical | Critical | 4 |
| 5 | MTD-005 | Healthcare | P0 | **No AI governance or explainability** — PLATFORM-CONSTITUTION §5.2-5.9 mandates explainability, hallucination detection, bias detection, model registry, prompt registry, and AI audit trail. None implemented. Clinical AI features exist without any safety guardrails — direct patient safety risk for AI-assisted diagnosis. | `docs/enterprise/ARCHITECTURE_GAP_ANALYSIS.md:§11`; `docs/enterprise/DISCOVERY_CONSOLIDATION.md:§11` | 480 | 72,000 | High | Critical | Critical | 5 |
| 6 | MTD-006 | Healthcare | P0 | **FHIR coverage severely insufficient** — Only 6 FHIR R4/R5 resources implemented vs 100+ in spec. No Patient, Observation, DiagnosticReport, ServiceRequest resources via proper FHIR API. Cannot exchange data with HIS/EMR, Ministry of Health, or national systems. Blocks SNDHS Phase 2 and MoH certification. | `docs/enterprise/ARCHITECTURE_GAP_ANALYSIS.md:5.1`; `docs/reports/technical_debt_register.md:TD-H03`; `docs/enterprise/DISCOVERY_CONSOLIDATION.md:§14` | 480 | 72,000 | High | Critical | High | 6 |
| 7 | MTD-007 | Security | P1 | **HS256 JWT (symmetric key) with no kid header** — Symmetric HMAC requires sharing secret across all services. Key rotation impossible without invalidating all tokens simultaneously. No asymmetric trust model for multi-service architecture. No JWKS endpoint for public key distribution. | `reports/discovery/18_TECHNICAL_DEBT.md:SD01,SD02`; `docs/enterprise/ARCHITECTURE_GAP_ANALYSIS.md:12.1,12.2` | 80 | 12,000 | High | Critical | High | 7 |
| 8 | MTD-008 | Infrastructure | P1 | **No staging environment** — K8s overlays only have dev/prod. No pre-production environment that mirrors production configuration, data volume, or network topology. Changes deploy to prod without realistic pre-release validation. | `reports/discovery/18_TECHNICAL_DEBT.md:ID01`; `docs/enterprise/ARCHITECTURE_GAP_ANALYSIS.md:8.4`; `docs/enterprise/DISCOVERY_CONSOLIDATION.md:§11` | 160 | 24,000 | High | Critical | High | 8 |
| 9 | MTD-009 | Healthcare | P1 | **Panic value escalation not automated** — Critical lab results exceeding panic thresholds have no automated escalation workflow. IQ-MOH-003 mandates critical values reported within specified timeframe. Current process relies on manual notification. Patient safety risk for delayed critical result communication. | `docs/enterprise/ARCHITECTURE_GAP_ANALYSIS.md:4.1,9.5` | 120 | 18,000 | High | High | Critical | 9 |
| 10 | MTD-010 | Testing | P1 | **Route test coverage at 35%, services at 30%** — 53+ route modules at 35% coverage; 34+ service modules at 30%. Critical paths (orders, results, samples) inadequately tested. Regression risk for every production change. Q12 quality gate (zero failed tests) violated by 268 fixture errors not fixed. | `docs/reports/technical_debt_register.md:TD-H01,TD-H02`; `docs/engineering/TECHNICAL-DEBT.md:D-001,D-003`; `reports/discovery/18_TECHNICAL_DEBT.md:CQ01,CQ02`; `docs/engineering/TECHNICAL_DEBT_REGISTER.md:TD-006` | 240 | 36,000 | High | High | High | 10 |
| 11 | MTD-011 | Testing | P1 | **No E2E or frontend tests** — Zero end-to-end tests for clinical workflows. Zero frontend tests in frontend-v2. Full-stack user journeys never validated automatically. UI regression risk for every change. No automated validation of critical clinical workflows (order→collect→result→release→alert). | `reports/discovery/18_TECHNICAL_DEBT.md:CQ04,CQ05`; `docs/enterprise/ARCHITECTURE_GAP_ANALYSIS.md:8.5,8.6`; `docs/reports/technical_debt_register.md:TD-H10,TD-M10` | 320 | 48,000 | High | High | High | 11 |
| 12 | MTD-012 | Architecture | P1 | **No dedicated domain layer — 70+ top-level packages** — Business logic mixed with infrastructure. No domain/entity/value-object/repository pattern. Routes import models directly, bypassing services. Domain layer (`domain/order_state.py`) imports from FastAPI framework. Cannot extract microservices. Constitutional C3 (layer naming) violated. | `docs/enterprise/ARCHITECTURE_GAP_ANALYSIS.md:1.1,1.3,1.8`; `docs/reports/technical_debt_register.md:TD-C02,TD-C07,TD-M01`; `docs/technical-debt/REGISTRY.md:TD-3289` | 640 | 96,000 | Medium | Critical | High | 12 |
| 13 | MTD-013 | Architecture | P1 | **main.py at 1,948 lines — single-file bottleneck** — FastAPI app initialization, middleware stack, background loops (adaptive concurrency, health alert), route registration all in one file. Hard to test, reason about, or modify. Every change risks breaking startup sequence. | `docs/reports/technical_debt_register.md:TD-C01` | 40 | 6,000 | High | High | Medium | 13 |
| 14 | MTD-014 | Architecture | P1 | **Two circuit breaker + two feature flag + two DI systems** — Kernel reimplements Core: dual circuit breakers (`core/self_healing.py` + `kernel/gateway/circuit_breaker.py`), dual feature flags (`core/feature_flags.py` + `kernel/features/`), dual DI containers (legacy import-time + Kernel DI). Inconsistent behavior. Maintenance divergence. Which system to extend is unclear. | `docs/reports/technical_debt_register.md:TD-C04,TD-C05,TD-C06`; `docs/enterprise/ARCHITECTURE_GAP_ANALYSIS.md:1.7` | 480 | 72,000 | Medium | High | Medium | 14 |
| 15 | MTD-015 | Infrastructure | P1 | **No automated secrets rotation** — SECRET_KEY, ENCRYPTION_KEY, NID_HMAC_KEY, REFRESH_TOKEN_SECRET, DEVICE_HMAC_KEY never rotated. Constitutional mandate (§4.5) requires 90-day rotation. Credential aging increases breach risk. Manual rotation almost never happens. No key versioning or staggered rollout capability. | `reports/discovery/18_TECHNICAL_DEBT.md:SD03,ID03`; `docs/enterprise/ARCHITECTURE_GAP_ANALYSIS.md:8.2` | 80 | 12,000 | High | Critical | High | 15 |
| 16 | MTD-016 | Security | P1 | **No SBOM in CI + no secrets scanning in CI** — Constitutional mandates SBOM on every build (§4.6) and secrets scanning (§4.7). CI has neither. Software composition unknown. Supply chain vulnerabilities undetected. Secrets may be committed without detection. Gitleaks configured but not in CI pipeline. | `docs/enterprise/ARCHITECTURE_GAP_ANALYSIS.md:8.1,12.4,12.5`; `docs/enterprise/DISCOVERY_CONSOLIDATION.md:§12(C7)`; `docs/technical-debt/REGISTRY.md:TD-3889` | 40 | 6,000 | High | High | Medium | 16 |
| 17 | MTD-017 | Security | P1 | **AI provider compliance risk** — Gemini/Groq integrations potentially violate Executive Orders 3 & 4 for healthcare AI. No data processing agreement (DPA) verification. No AI model deployment in Iraqi jurisdiction. Patient data may transit to non-compliant jurisdictions. | `docs/enterprise/DISCOVERY_CONSOLIDATION.md:§13(Critical)` | 80 | 12,000 | High | Critical | High | 17 |
| 18 | MTD-018 | Healthcare | P1 | **LOINC/SNOMED CT/ICD codes — model only, not populated** — Terminology models exist but no code population, mapping, or validation. Test results cannot be standardized for interoperability. LOINC mapping for test catalog incomplete. Regulatory requirement for lab certification (IQ-MOH) unmet. | `docs/enterprise/ARCHITECTURE_GAP_ANALYSIS.md:5.4,5.5,5.6`; `docs/enterprise/DISCOVERY_CONSOLIDATION.md:§14` | 240 | 36,000 | Medium | High | Medium | 18 |
| 19 | MTD-019 | Healthcare | P1 | **Instrument bidirectional interface missing — ASTM-only monoculture** — Device bridge only supports ASTM receive. No HL7 ORM (order) messages to send worklists to instruments. No DICOM support for imaging/pathology. Operators manually enter orders on analyzers. New lab onboarding bottleneck. | `docs/engineering/TECHNICAL_DEBT_REGISTER.md:TD-008`; `docs/enterprise/ARCHITECTURE_GAP_ANALYSIS.md:4.5,5.2,5.3`; `docs/enterprise/DISCOVERY_CONSOLIDATION.md:§14` | 480 | 72,000 | Medium | High | High | 19 |
| 20 | MTD-020 | Healthcare | P1 | **Result auto-validation + delta check not implemented** — No automated result validation against QC rules, Westgard rules, delta checks, or reference ranges. Manual validation bottleneck delays result release. Clinically significant changes from patient baselines go undetected. Patient safety risk for serial monitoring. | `docs/enterprise/ARCHITECTURE_GAP_ANALYSIS.md:4.2,4.3` | 240 | 36,000 | Medium | High | Critical | 20 |
| 21 | MTD-021 | AI | P2 | **No RAG system / vector database** — No pgvector, Qdrant, or Weaviate deployment. AI features cannot retrieve reference documents, clinical guidelines, or lab protocols. Hallucination risk elevated. Document Q&A impossible. Constitution §5 mandates RAG for clinical AI features. | `docs/enterprise/ARCHITECTURE_GAP_ANALYSIS.md:11.1`; `docs/reports/technical_debt_register.md:TD-H04` | 160 | 24,000 | Medium | High | High | 21 |
| 22 | MTD-022 | AI | P2 | **1413 mypy strict type errors** — No static type checking enforced despite constitutional mandate (Q10). Entire `backend/app/` has 1,413 strict mypy errors. Type-related bugs reach production. Refactoring safety severely reduced. Exemption in quality gates needs removal. | `docs/engineering/TECHNICAL-DEBT.md:D-002`; `docs/enterprise/ARCHITECTURE_GAP_ANALYSIS.md:8.8` | 240 | 36,000 | Medium | Medium | Medium | 22 |
| 23 | MTD-023 | Performance | P2 | **Adaptive concurrency is reactive, not predictive** — `_adaptive_concurrency_loop` halves `_MAX_CONCURRENT` only after detecting 2 slow DB readings. No predictive component. Oscillates between degrade/recover. No coordination with circuit breaker. No per-endpoint-type pools. | `docs/engineering/TECHNICAL_DEBT_REGISTER.md:TD-004`; `docs/engineering/IMPROVEMENT_BACKLOG.md:MT-001` | 80 | 12,000 | Medium | Medium | Medium | 23 |
| 24 | MTD-024 | Performance | P2 | **Circuit breaker coverage gaps** — Graduated states not implemented. No persistence (state lost on restart). Thundering herd on recovery. No admin API for manual override. No downstream dependency health checks. No coordination with adaptive concurrency. | `docs/engineering/TECHNICAL_DEBT_REGISTER.md:TD-005`; `docs/engineering/IMPROVEMENT_BACKLOG.md:ST-004` | 120 | 18,000 | Medium | High | High | 24 |
| 25 | MTD-025 | Performance | P2 | **Migration volume — 47 alembic revisions** — Slow `alembic upgrade head`. Failure risk at step 23/47. Complex dependency chain. CI migration-gate takes longer with each new migration. Cannot easily understand current schema without reading all 47 migrations. | `docs/engineering/TECHNICAL_DEBT_REGISTER.md:TD-003`; `reports/discovery/18_TECHNICAL_DEBT.md:DB02`; `docs/engineering/IMPROVEMENT_BACKLOG.md:ST-002` | 80 | 12,000 | Medium | Medium | Low | 25 |
| 26 | MTD-026 | Architecture | P2 | **Dual AI engine + stub agents** — `services/ai` (Ollama-only) vs `routes/ai.py` (multi-provider) creates fragmentation. `ai_fabric/agents/*.py` registers 5 agents but all are stub-level with no real LLM integration. `Kernel runtime cannot reference app/runtime` — dead code path. | `reports/discovery/18_TECHNICAL_DEBT.md:AD02`; `docs/reports/technical_debt_register.md:TD-H06,TD-H07`; `docs/technical-debug/REGISTRY.md:TD-3341+` | 160 | 24,000 | Low | Medium | High | 26 |
| 27 | MTD-027 | Architecture | P2 | **Frontend fragmentation — 3 parallel frontends** — `frontend/` (static PWA), `frontend-v2/` (React/Firebase), `client/` (tRPC+React). Each has different stack, deployment, auth model. 3x maintenance burden. Inconsistent UX. Split developer expertise. New features must be implemented in 1-3 places. | `docs/engineering/TECHNICAL_DEBT_REGISTER.md:TD-007`; `docs/engineering/TECHNICAL-DEBT.md:D-004`; `reports/discovery/18_TECHNICAL_DEBT.md:AD03` | 800 | 120,000 | Low | Medium | Medium | 27 |
| 28 | MTD-028 | Architecture | P2 | **7 microservice stubs + backend dual structure** — `services/{lab,order,patient,result,sample,notification,ai}` are stub skeletons with only Dockerfile + main.py + health endpoint. `backend/services/` and `backend/core/` (with `api/` subdirs) are experimental stubs. Waste developer attention. Create architecture confusion. | `docs/engineering/TECHNICAL_DEBT_REGISTER.md:TD-001,TD-002`; `docs/engineering/TECHNICAL-DEBT.md:D-009`; `reports/discovery/18_TECHNICAL_DEBT.md:AD04` | 80 | 12,000 | Medium | Low | Low | 28 |
| 29 | MTD-029 | Architecture | P2 | **CQRS not implemented — no event store** — Constitutional mandate (BLOCKER). Commands return data instead of void/ID. Queries may mutate state. No optimized read models for dashboards. No event store for replay/history. Outbox pattern exists but no event sourcing. | `docs/enterprise/ARCHITECTURE_GAP_ANALYSIS.md:1.2,1.5` | 640 | 96,000 | Low | Medium | Medium | 29 |
| 30 | MTD-030 | Operations | P2 | **No distributed tracing / APM** — `X-Request-ID` middleware exists but no OpenTelemetry spans. No code-level latency breakdown. No end-to-end trace context for async tasks. Debugging distributed issues requires manual correlation. Incident MTTR significantly higher than with tracing. | `docs/enterprise/ARCHITECTURE_GAP_ANALYSIS.md:9.1,9.4`; `docs/engineering/IMPROVEMENT_BACKLOG.md:ST-008,LT-009`; `reports/discovery/18_TECHNICAL_DEBT.md:ID06` | 120 | 18,000 | Medium | Medium | Medium | 30 |
| 31 | MTD-031 | Testing | P2 | **No performance regression testing in CI** — Load test scripts exist (k6 + Locust) but no baseline comparison. No CI gate for performance regression. Performance degradation reaches production undetected. No historical trend data for capacity planning. | `docs/engineering/IMPROVEMENT_BACKLOG.md:ST-003`; `docs/reports/technical_debt_register.md:TD-M06,TD-L04` | 120 | 18,000 | Medium | Medium | Low | 31 |
| 32 | MTD-032 | Testing | P2 | **SQLite for tests, not PostgreSQL** — Test suite uses SQLite instead of PG. PG-specific features (JSONB, array columns, full-text search, partition pruning) not tested. Schema drift between test and production environments. | `docs/reports/technical_debt_register.md:TD-M09` | 80 | 12,000 | Medium | Medium | Medium | 32 |
| 33 | MTD-033 | Infrastructure | P2 | **No audit_logs partition management** — `audit_logs` table grows unbounded. No partitioning by month. Query performance degrades over time. No archival automation for retention compliance (7-year healthcare requirement). Single table will reach millions of rows. | `reports/discovery/18_TECHNICAL_DEBT.md:DB05`; `docs/engineering/IMPROVEMENT_BACKLOG.md:LT-002` | 80 | 12,000 | Medium | Medium | Low | 33 |
| 34 | MTD-034 | Operations | P2 | **SNDHS-lite dual-read complexity** — `national_id` and `sndhs_health_id` may be None for pre-backfill rows. Every code path must handle None gracefully. Backfill not run. No enforcement after backfill. Flag-gated code paths create testing matrix explosion. | `docs/engineering/TECHNICAL-DEBT.md:D-010`; `docs/engineering/IMPROVEMENT_BACKLOG.md:MT-002` | 80 | 12,000 | Medium | Medium | High | 34 |
| 35 | MTD-035 | Operations | P2 | **No webhook system** — No outbound webhook delivery for clinical events (result ready, critical alert, order status change). Hospitals/EMRs cannot integrate GULA events into their systems. Real-time notification depends on polling or manual processes. | `docs/enterprise/ARCHITECTURE_GAP_ANALYSIS.md:3.2` | 120 | 18,000 | Medium | Medium | Medium | 35 |
| 36 | MTD-036 | Developer Experience | P2 | **Documentation stale: route count 36 vs 53+, model count 17 vs 60+** — CLAUDE.md reports 36 routes and 17 models. Actual count: 53+ routes and 60+ models. New developers given wrong codebase size. API consumers cannot discover actual endpoints. | `reports/discovery/18_TECHNICAL_DEBT.md:DD01,DD02` | 16 | 2,400 | Medium | Low | Low | 36 |
| 37 | MTD-037 | Developer Experience | P2 | **No auto-generated SDK, no API changelog, no API catalog** — Constitution mandates SDKs for Python/TypeScript/Java/Dart (§7.5) and API catalog (§7.4). None exist. Every integration partner writes custom HTTP clients. API consumers have no changelog for breaking changes. | `docs/enterprise/ARCHITECTURE_GAP_ANALYSIS.md:3.1,3.4,3.5` | 240 | 36,000 | Low | Medium | Low | 37 |
| 38 | MTD-038 | Operations | P3 | **No synthetic monitoring** — No synthetic transaction monitoring for critical user journeys (login, order entry, result release). Outage detection delayed until user reports. No proactive availability tracking. SLA measurement impossible. | `reports/discovery/18_TECHNICAL_DEBT.md:ID04`; `docs/enterprise/ARCHITECTURE_GAP_ANALYSIS.md:9.2` | 80 | 12,000 | Low | Medium | Medium | 38 |
| 39 | MTD-039 | Testing | P3 | **No chaos engineering in CI** — `tests/chaos/` and chaos-mesh experiments exist but not automated in CI. Self-healing mechanisms (circuit breaker, degraded mode, auto-repair) not regularly validated. Production failures may reveal untested recovery paths. | `docs/engineering/IMPROVEMENT_BACKLOG.md:MT-007`; `docs/enterprise/ARCHITECTURE_GAP_ANALYSIS.md:8.9` | 80 | 12,000 | Medium | Medium | High | 39 |
| 40 | MTD-040 | AI | P3 | **Vector store in-memory only** — RAG state lost on restart. Not production-ready. No embeddings pipeline. No pgvector connection. AI cannot maintain context across sessions. `ai_fabric/rag.py` uses in-memory storage only. | `docs/reports/technical_debt_register.md:TD-H04`; `docs/enterprise/ARCHITECTURE_GAP_ANALYSIS.md:11.1` | 160 | 24,000 | Medium | Medium | Medium | 40 |
| 41 | MTD-041 | AI | P3 | **Dual AI engine + stub agents** — `services/ai` (Ollama-only) vs `routes/ai.py` (multi-provider) creates fragmentation. `ai_fabric/agents/*.py` registers 5 agents but all are stub-level with no real LLM integration. `kern references non-existent `app/runtime`. | `reports/discovery/18_TECHNICAL_DEBT.md:AD02`; `docs/reports/technical_debt_register.md:TD-H06,TD-H07` | 160 | 24,000 | Low | Medium | High | 41 |
| 42 | MTD-042 | Documentation | P3 | **Missing Arabic user manual + on-premise deployment guide** — Arabic-first platform lacks Arabic user manual. On-premise deployment guide missing. Deployment friction for labs wanting self-hosted option. User onboarding for Arabic-speaking lab technicians relies on English documentation. | `reports/discovery/18_TECHNICAL_DEBT.md:DD05,DD06` | 120 | 18,000 | Low | Low | Low | 42 |
| 43 | MTD-043 | Documentation | P3 | **Missing ADRs for 6 critical architecture decisions** — No ADR for: layer restructuring, UUID migration, mTLS decision, FHIR strategy, SBOM decision. Architecture rationale undocumented. Team cannot understand why decisions were made. Risk of reverting to wrong approach. | `docs/enterprise/ARCHITECTURE_GAP_ANALYSIS.md:§6`; `docs/enterprise/DISCOVERY_CONSOLIDATION.md:§12(G1-G6)` | 16 | 2,400 | Low | Low | Low | 43 |
| 44 | MTD-044 | Operations | P3 | **National platform schema-only — 200+ tables with no code** — `backend/app/national*/` has 200+ database tables defined but zero route handlers, services, or business logic. Dead schema creates migration overhead. Every migration must account for these unused tables. Unknown maintenance cost. | `reports/discovery/18_TECHNICAL_DEBT.md:AD07`; `docs/enterprise/DISCOVERY_CONSOLIDATION.md:§11` | 160 | 24,000 | Low | Low | Low | 44 |
| 45 | MTD-045 | Developer Experience | P3 | **Pydantic V2 + passlib/bcrypt + Starlette deprecation warnings** — `class Config` pattern deprecated (should use `ConfigDict`). passlib 1.7.4 with bcrypt 4.1.3 produces deprecation warning. `HTTP_422_UNPROCESSABLE_ENTITY` deprecated (use `HTTP_422_UNPROCESSABLE_CONTENT`). Warning noise masks real issues. | `docs/engineering/TECHNICAL-DEBT.md:D-005,D-006,D-007` | 20 | 3,000 | Low | Low | Low | 45 |
| 46 | MTD-046 | Documentation | P3 | **Version divergence (2.1.0 vs 2.2.0 vs 2.3.2)** — config.py=2.1.0, CHANGELOG.md=2.3.2, pyproject.toml=2.2.0, Helm appVersion=2.1.0. Tracking confusion. Which version is production? Cannot reliably determine deployed version from any single source. | `reports/discovery/18_TECHNICAL_DEBT.md:DB01`; `docs/enterprise/DISCOVERY_CONSOLIDATION.md:§1` | 8 | 1,200 | Low | Low | Low | 46 |

---

## 3. Category Breakdown

### Architecture (7 items, 2,560 hours)

| ID | Priority | Description | Hrs | Clinical Risk |
|----|----------|-------------|-----|---------------|
| MTD-012 | P1 | No domain layer — 70+ top-level packages | 640 | High |
| MTD-013 | P1 | main.py at 1,948 lines | 40 | Medium |
| MTD-014 | P1 | Dual circuit breaker + feature flag + DI systems | 480 | Medium |
| MTD-026 | P2 | Dual AI engine + stub agents | 160 | High |
| MTD-027 | P2 | Frontend fragmentation — 3 parallel frontends | 800 | Medium |
| MTD-028 | P2 | 7 microservice stubs + backend dual structure | 80 | Low |
| MTD-029 | P2 | CQRS not implemented — no event store | 640 | Medium |

**High-risk items:** MTD-012 (no domain layer); MTD-026 (AI fragmentation with clinical risk); MTD-027 (frontend fragmentation spreads auth bypass risk)

**Top 3 recommendations:**
1. Extract main.py into modular initialization (MTD-013, 40h, quick win)
2. Consolidate dual circuit breaker + feature flag systems (MTD-014 phase 1, 80h)
3. Begin domain layer refactoring with bounded context mapping (MTD-012, 640h phased over 4 quarters)

### Security (6 items, 1,040 hours)

| ID | Priority | Description | Hrs | Clinical Risk |
|----|----------|-------------|-----|---------------|
| MTD-001 | P0 | Firestore security bypass | 240 | Critical |
| MTD-004 | P0 | mTLS not implemented | 480 | Critical |
| MTD-007 | P1 | HS256 JWT no kid header | 80 | High |
| MTD-016 | P1 | No SBOM + no secrets scanning in CI | 40 | Medium |
| MTD-017 | P1 | AI provider compliance risk | 80 | High |

**High-risk items:** MTD-001 (catastrophic PHI exposure); MTD-004 (inter-service MITM); MTD-017 (AI provider regulatory)

**Top 3 recommendations:**
1. Lock down Firebase security — route all frontend traffic through backend API (MTD-001, 240h)
2. Implement RS256 JWT with JWKS endpoint and kid header (MTD-007, 80h)
3. Add SBOM generation + Gitleaks scanning to CI pipeline (MTD-016, 40h, quick win)

### Infrastructure (5 items, 880 hours)

| ID | Priority | Description | Hrs | Clinical Risk |
|----|----------|-------------|-----|---------------|
| MTD-002 | P0 | Single PostgreSQL instance, no HA | 240 | Critical |
| MTD-003 | P0 | No automated backup restore testing | 80 | Critical |
| MTD-008 | P1 | No staging environment | 160 | High |
| MTD-015 | P1 | No automated secrets rotation | 80 | High |
| MTD-033 | P2 | No audit_logs partition management | 80 | Low |

**High-risk items:** MTD-002 (platform SPOF); MTD-003 (DR plan untested); MTD-008 (no pre-prod validation)

**Top 3 recommendations:**
1. Deploy Patroni-based PostgreSQL HA with automated failover (MTD-002, 240h)
2. Implement automated restore testing — spin up temp DB, restore latest backup, validate integrity (MTD-003, 80h)
3. Create staging environment that mirrors production (MTD-008, 160h)

### Performance (3 items, 400 hours)

| ID | Priority | Description | Hrs | Clinical Risk |
|----|----------|-------------|-----|---------------|
| MTD-023 | P2 | Adaptive concurrency is reactive | 80 | Medium |
| MTD-024 | P2 | Circuit breaker coverage gaps | 120 | High |
| MTD-025 | P2 | Migration volume — 47 revisions | 80 | Low |

**Top 3 recommendations:**
1. Implement predictive concurrency with moving average response time (MTD-023, 80h)
2. Add circuit breaker persistence + admin API (MTD-024 phase 1, 40h)
3. Squash migrations to reduce revision count (MTD-025, 80h)

### Healthcare (6 items, 720 hours)

| ID | Priority | Description | Hrs | Clinical Risk |
|----|----------|-------------|-----|---------------|
| MTD-005 | P0 | No AI governance or explainability | 480 | Critical |
| MTD-006 | P0 | FHIR coverage severely insufficient | 480 | High |
| MTD-009 | P1 | Panic value escalation not automated | 120 | Critical |
| MTD-018 | P1 | LOINC/SNOMED/ICD — model only | 240 | Medium |
| MTD-019 | P1 | Instrument bidirectional interface missing | 480 | High |
| MTD-020 | P1 | Result auto-validation + delta check missing | 240 | Critical |

**High-risk items:** MTD-005 (AI safety); MTD-009 (critical result notification); MTD-020 (manual validation risk)

**Top 3 recommendations:**
1. Implement panic value escalation engine with configurable thresholds and multi-channel notifications (MTD-009, 120h)
2. Populate LOINC codes for all test catalog entries (MTD-018 phase 1, 80h)
3. Implement result auto-validation with Westgard rules and delta checks (MTD-020, 240h)

### AI (5 items, 840 hours)

| ID | Priority | Description | Hrs | Clinical Risk |
|----|----------|-------------|-----|---------------|
| MTD-021 | P2 | No RAG system / vector database | 160 | High |
| MTD-040 | P3 | Vector store in-memory only | 160 | Medium |
| MTD-041 | P3 | Dual AI engine + stub agents | 160 | High |

**Top 3 recommendations:**
1. Deploy pgvector and implement embedding pipeline (MTD-021, 160h)
2. Resolve AI provider compliance — DPAs, jurisdiction audit (MTD-017, 80h)
3. Consolidate AI engine into single provider-agnostic interface (MTD-041, 80h)

### Testing (5 items, 560 hours)

| ID | Priority | Description | Hrs | Clinical Risk |
|----|----------|-------------|-----|---------------|
| MTD-010 | P1 | Route/services coverage at 30-35% | 240 | High |
| MTD-011 | P1 | No E2E or frontend tests | 320 | High |
| MTD-031 | P2 | No performance regression testing | 120 | Low |
| MTD-032 | P2 | SQLite for tests, not PostgreSQL | 80 | Medium |
| MTD-039 | P3 | No chaos engineering in CI | 80 | High |

**Top 3 recommendations:**
1. Fix 268 fixture errors and add integration tests for uncovered critical routes (MTD-010 phase 1, 80h)
2. Implement E2E test suite for core clinical workflow: order→collect→result→release→alert (MTD-011 phase 1, 80h)
3. Migrate test suite from SQLite to PostgreSQL (MTD-032, 80h)

### Documentation (3 items, 80 hours)

| ID | Priority | Description | Hrs | Clinical Risk |
|----|----------|-------------|-----|---------------|
| MTD-036 | P2 | Documentation stale: route/model counts | 16 | Low |
| MTD-042 | P3 | Missing Arabic user manual | 120 | Low |
| MTD-043 | P3 | Missing 6 critical ADRs | 16 | Low |

**Top 3 recommendations:**
1. Update CLAUDE.md with accurate route (53+) and model (60+) counts (MTD-036, 8h)
2. Write ADRs for layer restructuring, mTLS, UUID migration, FHIR strategy, SBOM (MTD-043, 16h)
3. Begin Arabic user manual development (MTD-042, 120h)

### Operations (4 items, 160 hours)

| ID | Priority | Description | Hrs | Clinical Risk |
|----|----------|-------------|-----|---------------|
| MTD-030 | P2 | No distributed tracing / APM | 120 | Medium |
| MTD-034 | P2 | SNDHS-lite dual-read complexity | 80 | High |
| MTD-035 | P2 | No webhook system | 120 | Medium |
| MTD-038 | P3 | No synthetic monitoring | 80 | Medium |

**Top 3 recommendations:**
1. Implement OpenTelemetry SDK integration with span exports (MTD-030, 120h)
2. Implement webhook registry with retry, signing, and delivery logging (MTD-035, 120h)
3. Deploy synthetic monitoring for 5-10 critical user paths (MTD-038, 80h)

### Developer Experience (2 items, 40 hours)

| ID | Priority | Description | Hrs | Clinical Risk |
|----|----------|-------------|-----|---------------|
| MTD-037 | P2 | No auto-generated SDK, API changelog, catalog | 240 | Low |
| MTD-045 | P3 | Pydantic V2 + passlib + Starlette deprecation warnings | 20 | Low |
| MTD-046 | P3 | Version divergence (3 sources) | 8 | Low |

**Top 3 recommendations:**
1. Resolve version divergence: canonicalize to config.py=2.1.0 (MTD-046, 8h)
2. Migrate Pydantic V2 `class Config` → `model_config = ConfigDict(...)` (MTD-045, 20h)
3. Set up openapi-generator CI workflow for Python SDK (MTD-037, 80h)

---

## 4. Duplicates Removed

The following duplicates were identified and consolidated from 8 source files into a single item in the master register:

| Master ID | Consolidated From | Dedup Rationale |
|-----------|-------------------|-----------------|
| MTD-001 | SD04 (discovery), §11 (DISCOVERY_CONSOLIDATION), §13 (Critical #1) | Same item, 3 sources |
| MTD-002 | DB04 (discovery), §11 (DISCOVERY_CONSOLIDATION), §13 (Critical #3) | Same item, 3 sources |
| MTD-003 | ID02 (discovery), 8.3 (ARCHITECTURE_GAP), §11 (DISCOVERY), §13 (Critical #2) | Same item, 4 sources |
| MTD-004 | C6 (DISCOVERY), 12.3 (ARCHITECTURE_GAP), TD-3888 (REGISTRY) | Same item, 3 sources |
| MTD-006 | TD-H03 (reports), 5.1 (ARCHITECTURE_GAP), §14 (DISCOVERY) | Same item, 3 sources |
| MTD-007 | SD01+SD02 (discovery), 12.1+12.2 (ARCHITECTURE_GAP) | Same item, 2 sources |
| MTD-008 | ID01 (discovery), 8.4 (ARCHITECTURE_GAP), §11 (DISCOVERY) | Same item, 3 sources |
| MTD-010 | D-001+D-003 (TECHNICAL-DEBT), CQ01+CQ02 (discovery), TD-H01+TD-H02 (reports), TD-006 (TECHNICAL_DEBT_REGISTER) | Same theme, 4 sources |
| MTD-011 | CQ04+CQ05 (discovery), TD-H10+TD-M10 (reports), 8.5+8.6 (ARCHITECTURE_GAP) | Same theme, 3 sources |
| MTD-012 | 1.1+1.3+1.8 (ARCHITECTURE_GAP), TD-C02+TD-C07+TD-M01 (reports), TD-3289 (REGISTRY) | Same theme, 3 sources |
| MTD-014 | TD-C04+TD-C05+TD-C06 (reports), 1.7 (ARCHITECTURE_GAP) | Same item, 2 sources |
| MTD-015 | SD03+ID03 (discovery), 8.2 (ARCHITECTURE_GAP) | Same item, 3 sources |
| MTD-016 | C7 (DISCOVERY), 8.1+12.4+12.5 (ARCHITECTURE_GAP), TD-3889 (REGISTRY) | Same theme, 4 sources |
| MTD-017 | §13 Critical #4 (DISCOVERY_CONSOLIDATION) | Unique to DISCOVERY |
| MTD-019 | TD-008 (TECHNICAL_DEBT_REGISTER), 4.5+5.2+5.3 (ARCHITECTURE_GAP) | Same theme, 2 sources |
| MTD-020 | 4.2+4.3 (ARCHITECTURE_GAP) | Unique to ARCHITECTURE_GAP |
| MTD-021 | TD-H04 (reports), 11.1 (ARCHITECTURE_GAP) | Same item, 2 sources |
| MTD-022 | D-002 (TECHNICAL-DEBT), 8.8 (ARCHITECTURE_GAP) | Same item, 2 sources |
| MTD-023 | TD-004 (TECHNICAL_DEBT_REGISTER), MT-001 (IMPROVEMENT_BACKLOG) | Same item, 2 sources |
| MTD-025 | DB02 (discovery), TD-003 (TECHNICAL_DEBT_REGISTER), ST-002 (IMPROVEMENT_BACKLOG) | Same item, 3 sources |
| MTD-026 | AD02 (discovery), TD-H06+TD-H07 (reports), TD-3341+ (REGISTRY) | Same theme, 3 sources |
| MTD-027 | AD03 (discovery), D-004 (TECHNICAL-DEBT), TD-007 (TECHNICAL_DEBT_REGISTER) | Same item, 3 sources |
| MTD-028 | AD04 (discovery), D-009 (TECHNICAL-DEBT), TD-001+TD-002 (TECHNICAL_DEBT_REGISTER) | Same item, 3 sources |
| MTD-030 | ID06 (discovery), 9.1+9.4 (ARCHITECTURE_GAP), ST-008+LT-009 (IMPROVEMENT_BACKLOG) | Same theme, 4 sources |
| MTD-033 | DB05 (discovery), LT-002 (IMPROVEMENT_BACKLOG) | Same item, 2 sources |
| MTD-034 | D-010 (TECHNICAL-DEBT), MT-002 (IMPROVEMENT_BACKLOG) | Same theme, 2 sources |
| MTD-036 | DD01+DD02 (discovery) | Same item, 1 source |
| MTD-042 | DD05+DD06 (discovery) | Same item, 1 source |
| MTD-043 | G1-G6 (DISCOVERY), §6 (ARCHITECTURE_GAP) | Same theme, 2 sources |
| MTD-045 | D-005+D-006+D-007 (TECHNICAL-DEBT) | Same theme, 1 source |
| MTD-046 | DB01 (discovery), §1 (DISCOVERY_CONSOLIDATION) | Same item, 2 sources |

### Sources Not Individually Listed (Batch-Deduplicated)

- **647 items from `docs/technical-debt/REGISTRY.md`** — These are auto-generated, line-level findings. The 365 "Cross-Domain Leakage" items (ai_fabric imports from ai/kernel, etc.) are captured collectively by MTD-026 and MTD-041. The 67 "Large Files/Functions" items are captured by MTD-013 (main.py) and AD01 (monster route files). The 14 Constitution Contradictions are captured by MTD-004, MTD-012, MTD-016, and MTD-029. The 7 Circular Dependencies are captured by MTD-029. The 52 Forbidden Imports are captured by MTD-012. The 60 Documentation Gaps are captured by MTD-036 and MTD-042. The 50 Naming Violations are captured by MTD-012. The Coverage Deficits (1 item) is captured by MTD-010.

- **45 items from `docs/engineering/IMPROVEMENT_BACKLOG.md`** — These are improvement suggestions, many of which are remediation strategies for specific debt items (MTD-023/MT-001, MTD-010/MT-002, MTD-025/ST-002, etc.). Straightforward improvement items (QW-001-QW-010) without corresponding debt items are below the materiality threshold for this master register.

- **10 items from `docs/engineering/TECHNICAL-DEBT.md`** — All 10 items (D-001 through D-010) have been mapped to master items (MTD-010, MTD-022, MTD-027, MTD-045, MTD-028, MTD-034).

---

## 5. Key Recommendations — Top 10 by Resolution Order

| Rank | ID | Item | Rationale |
|------|----|------|-----------|
| 1 | MTD-001 | Firestore security bypass | **Highest clinical + business risk.** Catastrophic PHI exposure. Firebase direct access bypasses all backend security (auth, RBAC, audit). Estimated 240h to lock down. ROI: High — eliminates a 25/25 risk rating. |
| 2 | MTD-002 | Single PostgreSQL, no HA | **Complete platform SPOF.** Loss of Postgres container = total outage + potential data loss. 240h for Patroni HA with automated failover. Every day without HA is a production incident waiting to happen. |
| 3 | MTD-003 | No backup restore testing | **DR plan untested.** Backups may be corrupt or incompatible. 80h to implement automated restore verification. Low-effort, high-impact — every other DR investment is wasted without validated restores. |
| 4 | MTD-004 | mTLS not implemented | **Constitutional mandate violated (C6).** Inter-service PHI transit unencrypted. 480h for full mTLS with internal CA. Mitigating controls (network isolation) reduce urgency slightly vs MTD-001/002, but constitutional + clinical risk is critical. |
| 5 | MTD-005 | No AI governance/explainability | **Clinical AI safety risk.** AI features exist without any safety guardrails. Constitution §5 mandates explainability, hallucination detection, bias detection. 480h for full implementation. High ROI — eliminates catastrophic clinical AI liability. |
| 6 | MTD-009 | Panic value escalation missing | **Direct patient safety gap.** IQ-MOH-003 requires critical result notification within specified timeframe. No escalation workflow exists. 120h for escalation engine with multi-channel notification. High clinical ROI. |
| 7 | MTD-006 | FHIR coverage insufficient | **Blocks MoH certification and SNDHS Phase 2.** 6/100+ FHIR resources. Cannot exchange data with national health systems. 480h to implement core resources. Strategic blocker for government market access. |
| 8 | MTD-007 | HS256 JWT no kid header | **Security architecture gap.** Cannot rotate keys. No asymmetric trust. 80h to migrate to RS256 with JWKS. Medium effort, eliminates a foundational security weakness that compounds with microservice extraction. |
| 9 | MTD-020 | Result auto-validation + delta check | **Patient safety — manual validation bottleneck.** Results released without automated QC validation. Clinically significant trend changes missed. 240h for auto-validation engine with Westgard rules and delta checks. |
| 10 | MTD-013 | main.py at 1,948 lines | **Highest-leverage architecture quick win.** 40h to extract middleware stack, background loops, and route registration into separate modules. Enables unit testing of startup sequence, reduces merge conflicts, improves developer onboarding. ROI: High for effort required. |

### Escalation Path for P0 Items (MTD-001 through MTD-005)

These 5 items carry Critical risk in both Business and Clinical dimensions. They should be reviewed by the Technical Review Board within 7 days and have dedicated sprint allocation until resolved. Combined estimate: 1,520h (~9.5 engineer-months). Monthly compounding interest on these alone is estimated at $12,000/month.

---

## 6. Quarterly Paydown Roadmap

### Q3 2026 (Jul-Sep) — Core Safety & Security
- MTD-001: Firestore security bypass (phase 1: lockdown) — 80h
- MTD-003: Automated backup restore testing — 80h
- MTD-007: RS256 JWT with JWKS + kid header — 80h
- MTD-009: Panic value escalation engine — 120h
- MTD-010: Fix 268 fixture errors + critical route tests — 80h
- MTD-013: Extract main.py into modular init — 40h
- MTD-016: SBOM + Gitleaks in CI — 40h
- MTD-025: Squash migrations (47→1 base) — 80h
- MTD-034: SNDHS backfill + tests — 80h
- MTD-043: Write 6 missing ADRs — 16h
- MTD-045: Fix Pydantic V2 + deprecation warnings — 20h
- MTD-046: Canonicalize version — 8h
- **Phase total: ~724h (~4.5 engineer-months)**

### Q4 2026 (Oct-Dec) — Infrastructure Hardening
- MTD-002: Deploy PostgreSQL HA (Patroni) — 240h
- MTD-008: Create staging environment — 160h
- MTD-015: Automated secrets rotation pipeline — 80h
- MTD-020: Result auto-validation engine phase 1 — 120h
- MTD-023: Predictive adaptive concurrency — 80h
- MTD-024: Circuit breaker persistence + admin API — 120h
- MTD-030: OpenTelemetry distributed tracing — 120h
- MTD-035: Webhook system — 120h
- **Phase total: ~1,040h (~6.5 engineer-months)**

### Q1 2027 (Jan-Mar) — Architecture & Quality
- MTD-012: Domain layer refactoring (phase 1: bounded context map) — 160h
- MTD-014: Consolidate circuit breaker + feature flags — 160h
- MTD-018: LOINC code population — 80h
- MTD-019: HL7 ORM bidirectional instrument control — 240h
- MTD-021: Deploy pgvector + embedding pipeline — 160h
- MTD-032: Migrate tests from SQLite to PostgreSQL — 80h
- MTD-033: Audit_logs partition management — 80h
- MTD-036: Update CLAUDE.md with accurate counts — 8h
- **Phase total: ~968h (~6 engineer-months)**

### Q2-Q4 2027 — Strategic
- MTD-001: Firestore full migration to backend API — 160h
- MTD-004: mTLS with internal CA — 480h
- MTD-005: AI governance + explainability — 480h
- MTD-006: FHIR core resources (Patient, Observation, DiagnosticReport) — 240h
- MTD-011: E2E test suite for clinical workflows — 320h
- MTD-027: Frontend consolidation (phase 1: deprecate one frontend) — 200h
- MTD-028: Remove/consolidate microservice stubs — 80h
- MTD-029: CQRS + event store — 640h
- MTD-031: Performance regression harness — 120h
- MTD-037: OpenAPI SDK generation — 80h
- MTD-038: Synthetic monitoring — 80h
- MTD-039: Chaos engineering in CI — 80h
- MTD-040: pgvector production RAG — 80h
- MTD-041: Consolidate AI engine — 80h
- MTD-042: Arabic user manual — 120h
- MTD-044: National platform schema cleanup — 160h
- **Phase total: ~3,440h (~21.5 engineer-months)**

---

## 7. Assumptions & Methodology

1. **Cost rate:** $150/h blended senior engineer rate (Iraq-adjusted market rate for full-stack healthcare software engineers)
2. **Effort estimates:** Sourced from source documents where available; estimated from analogous items where not. Actual effort typically 1.5x initial estimate (per engineering convention).
3. **Clinical risk classification:** Based on potential for direct patient harm (Critical = death/serious injury possible; High = clinical impact without immediate harm; Medium = indirect clinical workflow impact; Low = no clinical impact)
4. **Business risk classification:** Based on revenue/regulatory/operational impact (Critical = existential; High = significant revenue or regulatory; Medium = operational friction; Low = cosmetic)
5. **ROI calculation:** Qualitative ratio of risk reduction (sum of business + clinical risk reduction potential) divided by effort cost. High = >3x, Medium = 1.5-3x, Low = <1.5x.
6. **Interest rate:** Estimated at 5-15% of remediation cost per month delayed, based on compounding effect of additional code, dependencies, and knowledge loss. P0 items at the higher end.

---

## 8. Review Cadence

| Frequency | Activity |
|-----------|----------|
| Weekly | Top 5 items reviewed in engineering standup |
| Monthly | Sprint planning picks from resolution order; update estimates |
| Quarterly | Full register grooming; recalculate costs and interest; adjust priorities |
| Per-release | Assess whether any items can be partially resolved in current cycle |
| Annual | Full review of all items; close resolved or obsolete entries |

**Register Owner:** Platform Engineering  
**Next Review:** 2026-08-18  
**Governance:** Technical Review Board approval required for priority changes to P0/P1 items

---

*This register supersedes all previous technical debt documents listed in §4. Source-specific registers should be considered historical references only.*

*Generated from: `docs/technical-debt/REGISTRY.md`, `docs/engineering/TECHNICAL_DEBT_REGISTER.md`, `docs/engineering/IMPROVEMENT_BACKLOG.md`, `docs/engineering/TECHNICAL-DEBT.md`, `docs/reports/technical_debt_register.md`, `reports/discovery/18_TECHNICAL_DEBT.md`, `docs/enterprise/DISCOVERY_CONSOLIDATION.md`, `docs/enterprise/ARCHITECTURE_GAP_ANALYSIS.md`*
