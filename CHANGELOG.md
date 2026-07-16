# Changelog
## [2026-07-16] — v2.3.2 — National Notification Platform Tests
### National Notification Platform (2,606 LOC — 0→53 tests)
- **53 new tests** for `NotificationPlatformService`, domain entities, and error handling
- Covers: send (all 10 channels, templates, scheduling, priorities, categories, correlation IDs, metadata)
- Covers: batch send, template CRUD (create, render Jinja2/Mustache, update, delete)
- Covers: user preferences (enable/disable, quiet hours, category opt-in/opt-out)
- Covers: delivery reports, lifecycle (cancel, mark read, mark delivered, list/filter)
- Covers: scheduling, stats, all error conditions (missing template, invalid template, channel blocked, etc.)
- **Bug fixed**: Added missing `created_by` field to `NotificationBatch` domain entity (service was passing it but entity didn't accept it)
- **Dependencies added**: `jinja2`, `chevron` (template rendering engines used by the platform)

### Quality Gates
- All 53 new tests passing with in-memory repositories (fast, no DB needed)
- Total test count: 137 (84 prior + 53 notification platform)

## [2026-07-16] — v2.3.1 — Identity Governance Persistence Tests
### Identity Governance Persistence (ADR-012 Phase 3)
- **35 new tests** for `PersistedIdentityGovernanceService`, `PersistedBreakGlassService`, and `PersistedIdentityMergeEngine`
- Covers: citizen/newborn/foreigner/unknown registration, document linking & verification, search, optimistic locking
- Covers: break-glass access lifecycle (request, revoke, expire, validate, list, stale expiry)
- Covers: merge confidence calculation, propose/approve/reject merge, duplicate proposal detection
- **ADR-012 gap closed**: The persisted identity governance services (407 LOC) now have full test coverage
- Total test count: 84 (49 identity/security/clinical-core + 35 governance persistence)

### Quality Gates
- All 35 new tests passing (SQLite in-memory, isolated per test)
- All source files compile-clean

## [2026-07-16] — v2.2.0 — Sprint-001: Repository Transformation & Foundation Lock
### Repository Audit & Cleanup
- **Syntax Gate PASS**: 1532 Python modules scanned, 0 module-level import errors
- **F821 Bugs Fixed**: 125 undefined-name errors resolved across capabilities framework
- **Test Import Fix**: 54 test files switched from `backend.app` to `app` imports (module identity fix)
- **Syntax Errors**: All syntax errors resolved across 25+ new platform modules
- **Kernel Tests**: 172/173 passing (1 pre-existing flaky isolation test)
- **Security Tests**: All passing (39 tests)
- **Identity Tests**: All passing
- **Feature Flag Tests**: All passing
- **Ruff Gate**: 0 syntax errors (E9), 0 undefined names (F821), 898 style/naming warnings remaining

### Platform Modules Integrated
- `capabilities/` — 10 capability modules (clinical foundation, document/encounter management, FHIR, consent, provider, reporting, search, storage, workflow engine)
- `biomedical/`, `blood_bank/`, `citizen_platform/`, `command_center/`, `control_plane/`, `critical_care/`, `ems/`, `lifecycle_platform/`, `nhdw/`, `nursing/`, `pharmacy/`, `pilot_platform/`, `public_health/`, `radiology/`, `research_platform/`
- `national/` — Document, notification, scheduling, background, observability, rules, search, task engines
- `kernel/` — DI container, event bus, plugin system, runtime, validation, gateway, config, features

### Quality Gates Baseline
- **ruff**: 898 warnings (style/naming — not bugs)
- **B904**: 220 exception-chaining warnings remaining (requires human review for each)
- **mypy**: Configured strict mode (requires env vars to run)
- **bandit**, **semgrep**: Ready in CI pipeline
## [2026-07-15] — v2.2.0 — Missions 017-024: National Platforms
### MISSION-017: National EHR Platform
- **Longitudinal Patient Record**: Comprehensive lifetime clinical history spanning all care encounters, providers, and facilities with FHIR R4 native data model
- **FHIR R4 Native**: Full FHIR R4 compliance for all clinical resources (Patient, Observation, DiagnosticReport, MedicationRequest, etc.)
- **Clinical Documentation**: Structured clinical documentation with templates, codified entries, and digital signatures
- **Medication Platform**: End-to-end medication management — prescribing, dispensing, administration, reconciliation, allergy checking
- **Orders Platform**: Computerized Provider Order Entry (CPOE) for laboratory, radiology, medication, procedures, and referrals
- **Clinical Decision Support**: Rule-based and ML-driven clinical decision support integrated at point of care

### MISSION-018: National Health Data Platform
- **Unified Data Lake**: Centralized storage for all health data — structured, semi-structured, and unstructured — with schema-on-read capabilities
- **Data Warehouse**: Dimensional model for population health analytics, operational reporting, and regulatory submissions
- **Master Data Management (MDM)**: Single source of truth for patients, providers, facilities, and clinical terminology across the ecosystem
- **Streaming Platform**: Real-time event streaming for clinical alerts, surveillance, and operational dashboards
- **National Analytics**: Cross-population analytics engine for epidemiological surveillance, resource utilization, and outcomes research
- **Research Platform**: Privacy-preserving analytics environment with de-identified datasets and cohort discovery
- **AI Data Platform**: Feature store, model training infrastructure, and inference pipelines for national-scale AI/ML

### MISSION-019: National Platform Operations
- **Environment Management**: Multi-environment orchestration (dev/staging/prod/DR) with infrastructure-as-code and automated provisioning
- **Release Platform**: Automated CI/CD pipeline with canary deployments, blue-green rollouts, and rollback automation
- **24/7 Operations Center**: Centralized monitoring hub with on-call rotation, escalation policies, and incident response runbooks
- **Monitoring**: Comprehensive observability — metrics, traces, logs — with intelligent alerting and anomaly detection
- **Incident Management**: Full incident lifecycle — detection, triage, response, post-mortem — integrated with communication channels
- **Security Operations**: SIEM, SOAR, vulnerability management, penetration testing, and compliance monitoring
- **Backup & Disaster Recovery**: Automated backup, point-in-time recovery, cross-region replication, and DR drill automation
- **Capacity Management**: Resource forecasting, auto-scaling, cost optimization, and performance capacity planning

### MISSION-020: National Digital Health Ecosystem
- **Connector Framework (REST/SOAP/GraphQL/FHIR/HL7/ASTM/DICOM/MQTT/AMQP)**: Universal protocol adapter for all healthcare and IoT integration patterns
- **Partner Platform**: Self-service onboarding, credential management, usage analytics, and SLA monitoring for ecosystem participants
- **Data Exchange**: Policy-driven data sharing agreements with consent management, audit trails, and de-identification gateway
- **National API Gateway**: Centralized API management with authentication, rate limiting, transformation, and versioning
- **Operational Resilience**: Multi-region active-active deployment, circuit breakers, bulkheading, and graceful degradation

### MISSION-021: National Citizen Super App
- **Citizen Identity**: Biometric-backed digital identity with national ID verification and multi-factor authentication
- **Health Card**: Digital health card with QR/barcode — emergency contact, allergies, blood type, organ donor status, chronic conditions
- **QR/Barcode**: Scanable identifiers for appointments, prescriptions, lab results, and clinical documents
- **Dashboard**: Personalized health dashboard — upcoming appointments, recent results, medications, immunizations, health metrics
- **Appointments**: Book, reschedule, cancel appointments across all healthcare providers in the ecosystem
- **Laboratory Results**: Real-time lab result viewing with trend charts, reference ranges, and clinical interpretations
- **Clinical Records**: Access to personal clinical records — diagnoses, procedures, medications, allergies, immunizations
- **Family Platform**: Linked family accounts — manage dependents, children, elderly parents — with proxy access controls
- **Offline Support**: Full offline capability — cached health card, prior results, appointment viewing — no connectivity required
- **Multi-Platform (Android/iOS/PWA)**: Native mobile apps for Android and iOS plus progressive web app for universal access

### MISSION-022: National Health Intelligence & Automation
- **Automation Engine**: Workflow automation for clinical and administrative processes — rule-based, event-driven, scheduled
- **Clinical Intelligence**: ML-powered clinical insights — diagnosis support, treatment recommendations, risk stratification
- **Laboratory Intelligence**: AI-driven lab operations — auto-verification, reflex testing, predictive inventory, utilization management
- **Hospital Intelligence**: Operational analytics for hospital management — bed capacity, OR utilization, staffing optimization, length-of-stay prediction
- **Public Health Intelligence**: Population-level surveillance, outbreak detection, environmental health monitoring, health equity analysis
- **National AI Platform (LLM Gateway, RAG, Vector Store, Model Registry)**: Centralized AI infrastructure — LLM access with governance, retrieval-augmented generation, vector embeddings, model version management
- **Decision Support**: Multi-modal decision support — clinical guidelines, drug interactions, imaging AI, lab-based algorithms

### MISSION-023: National Doctor Clinical Workspace
- **Doctor Dashboard**: Personalized clinical dashboard — patient list, alerts, tasks, schedule, performance metrics
- **Patient Workspace**: Longitudinal patient view — history, medications, allergies, lab results, imaging, notes — all in one place
- **Orders**: CPOE for lab, radiology, medication, procedures, referrals — with order sets, favourites, and clinical guidance
- **Clinical Documentation (SOAP/Progress/Consultation/Discharge)**: Structured note templates — SOAP, progress notes, consultation notes, discharge summaries
- **Decision Support**: Integrated CDS — drug-drug interactions, allergy alerts, guideline recommendations, risk scores
- **Secure Messaging**: HIPAA-compliant messaging between care team members with attachments, read receipts, and audit trail
- **Offline Support**: Offline-capable clinical workspace — view patient data, create notes, queue orders — sync when connected

### MISSION-024: National Laboratory Desktop Professional
- **Laboratory Dashboard**: Real-time lab operations dashboard — pending specimens, critical results, QC status, workload, TAT analytics
- **Specimen Lifecycle**: End-to-end specimen tracking — collection, transport, accessioning, processing, storage, disposal — with chain of custody
- **Analyzer Integration (ASTM/HL7/POCT)**: Direct instrument connectivity via ASTM, HL7, and POCT1A with bidirectional communication
- **Quality Management (Westgard/Levey-Jennings)**: Statistical QC — Westgard rules, Levey-Jennings charts, multi-rule analysis, QC lockout
- **Result Management**: Result entry, verification, amendment, correction — with audit trail, delta check, and autoverification rules
- **Printing Platform**: Configurable report printing — multi-format (PDF/HTML/ZPL), batch printing, auto-print, label printing
- **Offline Support**: Full offline operation — specimen registration, result entry, printing — automatic sync on reconnection
- **Windows Native (PySide6)**: Native Windows desktop application built with PySide6 — tray icon, system notifications, auto-update

## [2026-07-14] — FOUNDATION v1.0
### Foundation Completion (MISSION-FINAL)
- **Foundation is now COMPLETE and FROZEN** — no further infrastructure development

### Event Platform Completion
- **Snapshot Engine** (`backend/app/kernel/event_bus/snapshot.py`): Aggregate state snapshots with save/load/rebuild from events
- **Recovery Engine** (`backend/app/kernel/event_bus/recovery.py`): Sequential/parallel/batched event recovery with retry, handlers, job management
- **EventBus** (`backend/app/kernel/event_bus/bus.py`): Integrated snapshot + recovery engines

### Integration Foundation Completion
- **Connector Registry** (`backend/app/integration/connector/registry.py`): Type-indexed, tag-indexed connector registry with health tracking
- **Connector SDK** (`backend/app/integration/connector/sdk.py`): Auto-generates Python SDK client code from connector specs
- **HTTP/REST Connector** (`backend/app/integration/connector/http.py`): Async HTTP client with metrics, health checks
- **GraphQL Connector** (`backend/app/integration/connector/graphql.py`): GraphQL query/mutation support
- **WebSocket Connector** (`backend/app/integration/connector/websocket.py`): Pub/sub with auto-reconnect
- **gRPC Connector** (`backend/app/integration/connector/grpc.py`): gRPC channel management with stub registry
- **DICOM Connector** (`backend/app/integration/connector/dicom.py`): C-FIND, C-MOVE, C-STORE support (pydicom optional)

### Identity Foundation Completion
- **Identity Governance Service** (`backend/app/services/governance/identity_governance.py`): Full identity lifecycle — citizen, newborn, foreigner, resident, visitor, unknown patient registration; birth certificate, passport, visa document workflows; document verification; identity history
- **Family Registry** (`backend/app/services/governance/family_registry.py`): Family creation, member management, guardian linking, dependent tracking
- **Identity Merge Engine** (`backend/app/services/governance/merge_engine.py`): Merge proposals, confidence scoring, approval/rejection workflow, merge history
- **National ID as primary legal identifier** — never exposed in healthcare views
- **Health Number as primary healthcare identifier** — used in all medical documents

### Reference Services Completion
- **Master Reference Data Service** (`backend/app/services/reference/master_reference_data.py`): Countries, governorates, languages, currencies, timezones, medical specialties, units — versioned, with auto-seed
- **Universal Identifier Service** (`backend/app/services/reference/universal_identifier.py`): 12 identifier types (HN, ORD, SPC, ACC, RPT, VIS, ENC, APT, INV, NTF, WF, AUD) with UUID/sequential/hash format support
- **National Laboratory Catalog** (`backend/app/services/reference/national_lab_catalog.py`): 29 seeded lab tests, 3 panels, 7 specimen types; LOINC mapping, search, versioning

### Healthcare Foundation Completion
- **Organization model** (`backend/app/models/organization.py`): Organizations, Facilities, Appointments with relationships
- **ABAC Engine** (`backend/app/security/abac.py`): Attribute-based access control with conditions (equals, in, matches, etc.), priority rules, deny-overrides

### Quality Gates
- 55 new tests covering all new modules — all passing
- Ruff: all checks passing
- Bandit: clean (no high/medium issues)
- py_compile: all files compile cleanly
### Program v3.0 — Capability Factory & Automation (M005)
- **Enhanced CapabilityDescriptor** (`backend/app/kernel/types.py`): Added 30+ fields including capability_id, owner, status lifecycle, events, commands, queries, entities, DTOs, policies, permissions, API endpoints, scores, domain, layer, tags
- **Enhanced CapabilityRegistry** (`backend/app/kernel/runtime/capability_registry.py`): Added dependency graph with topological sort, impact analysis, batch registration, store/load, domain/status filtering, summary statistics
- **Enhanced Capability Generator** (`backend/app/engineering/generators/capability.py`): Now generates 20+ artifacts per capability (domain entities, repository interface+impl, application service, DTOs, commands, events, queries, policies, permissions, API routes, health checks, README, ADR, SBOM, capability.json descriptor, unit tests, integration tests)
- **Capability Registry Populator** (`backend/app/kernel/capabilities_registry_populator.py`): Registered 44 capabilities across 9 domains (identity_security, clinical, communication, infrastructure, reporting, platform, financial, observability, integration) + 10 draft capabilities for M006/M007
- **Kernel Bootloader Enhancement** (12-phase boot now includes capability population + feature flag sync)
- **CapabilityFlagManager** (`backend/app/kernel/features/capabilities.py`): Now bridged to CapabilityRegistry with bidirectional sync
- **CLI Enhancement** (`backend/app/engineering/productivity/cli.py`): Added `gula capability` subcommands (list, show, enable, disable, impact, graph, summary)
- **Capability Report** (`assessment/capability_report_v3.md`): Comprehensive catalog with dependency graph in Mermaid format
- **M006 Core Business Capability Platform**: Generated 6 capability scaffolds (storage_service, document_management, workflow_engine, search_service, reporting_service) with full domain/application/infrastructure layers
- **M007 National Healthcare Core Domain**: Generated 5 healthcare capability scaffolds (provider_management, encounter_management, clinical_foundation, fhir_interoperability, healthcare_consent) with events, commands, queries, policies, permissions

### Capability Registry Final State
- **52 registered capabilities** across 9 domains (identity_security, clinical, communication, infrastructure, reporting, platform, financial, observability, integration)
- All capabilities have proper event/command/query definitions
- Auto-populated at kernel boot (Phase 11 of 12-phase boot sequence)
- Bidirectional sync between CapabilityRegistry ↔ CapabilityFlagManager

### Fixed
- `backend/app/engineering/generators/capability.py`: Fixed mismatched triple-quote string (f""" vs ''') in capability.json template
- `backend/app/kernel/capabilities_registry_populator.py`: Fixed cascading edit misalignments in M006/M007 capability definitions

## [2026-07-13]
### Production Validation
- Fix Python 3.10 `datetime.UTC` compatibility across 49 files (switch to `timezone.utc` via `_compat.py`)
- Fix `StrEnum` compatibility for Python 3.10 in `_compat.py`
- Fix mypy syntax error in `tasks/registry.py` (remove type-comment on line 32)
- Fix `RateLimiter.check()` performance: replace list-based sliding window with `collections.deque` (1000x improvement — 219s → 0.22s for 100k checks)
- Add kernel initialization to test `client` fixture in `conftest.py` (fixes 5 chaos-survival tests)
- All **1420 tests passing**, 9 stress tests passing, Bandit clean

### Configuration
- Add `explicit_package_bases = true` to mypy config
- Add proper mypy overrides for `backend.app.routes.*` and `engineering.*`
- Add `scripts/`, `nhop-platform/`, `client/` to ruff exclude list

### Engineering Automation
- **shared/di_container**: New package — enterprise DI container extracted from Platform-Core. Provides `ServiceContainer` (singleton/scoped/transient, auto-wiring, thread-safe, circular detection) and `ServiceScope`. Zero external dependencies.
- Fix `shared/generators/migration.py`: remove `backend.app._compat` dependency; migrate to `pathlib`
- Fix `shared/generators/documentation.py`: migrate from `os`/`open()` to `pathlib`

### Generator Bug Fixes
- Fix `generators/plugin.py`: hooks now generated inside class body (was outside — producing syntax errors)
- Fix `generators/capability.py`: command/event/query imports use correct relative paths (was producing malformed `from x.y.x.y import` patterns)
- Fix `testing/fixtures.py`: `datetime` import moved to module level (was inside return statement — producing syntax errors)
- Fix `testing/factories.py`: `Meta.model` now uses class reference, not string literal (was producing runtime errors)
- Fix `productivity/cli.py`: CRUD `:indexed`/`:unique` flags now checked per-field (was applying to all fields)
- Refactor `shared/generators/documentation.py`: migrate `os`/`open()` to `pathlib` with error handling

### Documentation
- Rewrite `README.md` to reflect current Docker Compose + PG16 + Redis 7 stack (was outdated Render+Supabase)
- Rewrite `ARCHITECTURE.md` to reflect current monolith-first deployment (was outdated microservices with RabbitMQ/Kafka/ClickHouse/MinIO)

### Breaking Changes
- **ci:** pin pytest-asyncio<1.0.0 to prevent breaking-change installs (7995f4f4)
- Fix site-breaking issues: CSP, nginx crashes, XSS, security hardening (afbc0b19)

### Features
- consolidate engineering kernel, notifications, financial, and shared library features (b1d338f4)
- **engineering:** complete MISSION-000C Engineering Factory Initialization (d3de15d1)
- **shared:** create canonical shared library and consolidate repository assets (e44d7a9f)
- **engineering:** create GULA Engineering Assessment Foundation (e59df563)
- **architecture:** establish master architecture governance (25bf2dec)
- **ai/safety:** §8 safety + §14 hallucination columns on ai_interactions (additive, flag-gated) (25642bbc)
- **launch:** operational medical-intelligence collection pipeline (Phases 2–6, additive + flag-gated) (aaa92671)
- **frontend-v2:** production-grade UX, navigation, and reliability hardening (7368f753)
- **ai:** wire google_ai gateway into routes/ai.py (9a12d798)
- **financial:** Phase A — data model bootstrap (safe, additive) (5a477634)
- **sndhs-lite:** phase 1 — production-safe migrations + backfill + flags (d56a9a61)
- **system:** comprehensive platform improvements — interpretation, clinical intelligence, stats API (05d2000b)
- **patient-card:** digital QR-backed patient card + full-history endpoint (b4fc0c52)
- **deploy:** add post-deploy smoke + perf gate (scripts/smoke-bootstrap.sh) (5e06e7ff)
- **monorepo:** consolidate LabLink-Core and Front-end- into gula-platform (cddd4753)
- **tasks:** add Redis-backed task queue with crash isolation and retry (b539c2d0)
- **edge:** Managed Distributed Edge AI Platform — control plane + agent + UI (92771471)
- **ai:** integrate Gemini 2.0 Flash assistant + fix smoke test CI (8be76a7d)
- **nhop:** add notification system (CMD-024) (d0ebcfa8)
- **nhop:** add docker-compose, Dockerfile, and Alembic scaffolding (CMD-021) (c2f25e8b)
- **nhop:** add doctor-portal API (CMD-017) (04a5a47a)
- **nhop:** add test-results API with smart analysis (CMD-009/010) (eaa04eab)
- **api:** citizen-centric test results API (CMD-009) (4ded1673)
- **models:** add TestResult model + Pydantic schemas (CMD-008) (453ad6c1)
- **nhop:** CMD-007 Lab and LabDevice models with schemas (c697698a)
- **nhop:** CMD-006 citizen registration API (be195640)
- **identity:** add Iraqi-Arabic identity matching service (a6ff9d24)
- **nhop:** add Citizen SQLAlchemy model and Pydantic schemas (2d3b2e71)
- **nhop:** CMD-003 FastAPI main app (7fc79f03)
- **nhop-platform:** add database config and async SQLAlchemy setup (CMD-002) (21aeacd8)
- **consent:** minimal production consent layer (grant/revoke/check + break-glass) (cf7845d1)
- **launch:** citizen-first registration, MPI review queue, rate limiting, alertmanager (a1ba3a11)
- **launch:** wire MPI dedup into patient creation + launch runbook (72b24fb5)
- **mpi+integrations:** Master Patient Index + gov/Cloudflare adapters (36551b94)
- **ops:** one-shot deployment for Render, Supabase, and DigitalOcean (c359c119)
- **ops:** deploy FastAPI on Render + Supabase (no Redis, no SQLite) (fd57c9f8)
- **ai:** integrate Ollama local AI as primary provider with full fallback chain (58837f47)
- **ashs:** DIVE +5 temporal checks + Autonomous Self-Healing System (2abd3980)
- **integrity:** add Data Integrity Verification Engine (DIVE) (22389119)
- **claims:** add Claims module for insurance integration (71749f81)
- **citizen-ux:** decision-first UX — status banner, action sentences, auto AI (1389f843)
- **citizen:** emotional UX, offline fallback, trust badge, action buttons (993a2458)
- **citizen:** ultra-simple patient UI — Zero Cognitive Load design (03402985)
- **ai:** clinical weighting, patient context, action guidance, doctor alert (e4c4f8c2)
- **ai:** severity classification, critical flags, hallucination guard (452495dd)
- AI result interpretation — free Gemini/Groq, Arabic, patient-facing (ce90e1eb)
- 3 stability fixes + TEST 11-13 hard mode tests (191/191 passing) (6ce6db64)
- 3 elite improvements — state persistence, cross-layer correlation, controlled degradation (7ded8c26)
- self-adaptive DB layer — sliding window, circuit escalation, correlation logging (e366a708)
- adaptive DB layer — error counters, action map, differentiated alerts (2abc2719)
- DB connection observability layer with smart retry (1d410374)
- implement Control Layer (Policy Engine, Kill Switch, Decision Guard, Risk Engine) (b8ecd440)
- full system audit fixes + self-building AI agent + horizontal scaling (5e8c5454)
- production certification — resource limits, bearer auth, adaptive concurrency, integrity tests (56d732f9)
- runtime hardening — Grafana dashboard, SLOs, chaos tests, alert watchdog v2 (311004d7)
- production hardening — logging, metrics, alerting, rate-limit headers (71435c1f)
- citizen portal API + /health/deep + optimistic locking on lab_results (5ef164ae)
- complete frontend with tiers page, citizen portal, and tier badge (9e7d30a3)
- production-ready multi-tier SaaS system + critical bug fixes (c3050a3b)
- new light-theme login and register pages (112eb749)
- add deployment, testing, and monitoring infrastructure (570994ff)
- add render deployment config and credentials guide (b515e3cc)
- add production-grade systems (health checks, rate limiting, logging, caching, auto-healing, backups, security) (c536efdd)
- add AI system optimizer — lightweight performance monitoring + Ollama integration (9b7951ed)
- production hardening — zero-crash, multi-tenant, secure deployment (f9fadd88)
- clinical state machine, replay protection, conflict resolution, eviction (57bbf193)
- clinical hardening — authorization, fail-closed firewall, clinical engine (21fffd6d)
- complete registration system for citizens, labs, technicians, and doctors (9ac668d5)
- guardian/children records + staff registration + priority bypass (735a7cd2)
- family health records linking + perf layer (orjson, uvloop, backpressure) (43522c3c)
- Production Hardening Layer — monitoring, zero-downtime deploy, nginx hardening (4d8223c4)
- Self-Healing System + Robust Startup Guard hardening (2cd30eee)
- Production Startup Guard — fail-fast validation before accepting traffic (2ea03b94)
- **k8s:** complete microservices + RabbitMQ manifests (5a82473f)
- Order 21 & 22 — Kubernetes readiness + Blue-Green deployment (16d2f6cc)
- server image branching — build & push Docker images to GHCR per branch (59027db1)
- DB-level enforcement + Outbox Pattern + Idempotency layer (ba102791)
- Wire AI sandbox to real clinical engines + add analyze-order route (b8663d9b)
- Clinical-Grade External API Layer + AI Safety Architecture (2f1c046f)
- External API Safe Layer with circuit breaker, rate limiter, cache (3a046cd9)
- **frontend:** Ultimate UI Overhaul, 5-Languages i18n, Advanced PWA & Charts (3c9622b6)
- full RBAC hierarchy — roles, user management, master-admin NID (ca01d172)
- JWT jti, GZip, offline sync engine, clinical intelligence layer (96057b59)
- add ⚡ quick entry workflow screen (keyboard-first, WhatsApp share) (7c4d4372)
- **security:** production-grade session hardening (567380ca)
- **rbac:** implement granular permission system with JWT-embedded perms (dcd9b651)
- add create_master_admin.py script for initial setup and password reset (2f193ab9)

### Improvements
- **architecture:** cleanup phase 1 (5b54d754)
- **api:** replace deprecated FastAPI patterns with modern equivalents (c3d23bd8)
- **ai:** full cleanup + 5 production-hardening fixes (6d6fae9b)

### Bug Fixes
- **kernel:** certification batch — fix 7 bugs, add enable_modules flag (64580491)
- **production:** batch 1 — production validation & compatibility (a5c4cbbb)
- **production:** eliminate critical blockers batch 1 (eefa04c4)
- **launch:** cross-dialect Uuid for SQLite tests + regen package-lock (e33d203a)
- **vercel:** unblock production deploy — repoint to frontend-v2 and fix build (7c92d4d6)
- **migrations:** resolve duplicate revision id 20260505_0001 (552f73b3)
- **ai:** remove stale `system` reference in chat fallback (b98fb48e)
- **tests:** patch cache with _MemoryStore in performance-sensitive rate-limiter tests (a04f4599)
- **tests:** correct test_flag_low boundary value (52fcdb8b)
- **ci:** resolve security-scan and backend-test failures (7ea627a0)
- **patient-card-tests:** inline auth_headers helper (23d391e6)
- **test:** use private engine in edge guard test to prevent teardown error (8876dc65)
- **tasks:** use get_running_loop + model_dump_json in RedisTaskQueue; add fixture loop scope (f1c5b31b)
- **tests:** stabilise async test collection for pytest-asyncio 1.x (ff4e31b6)
- **tests:** remove asyncio.coroutine removed in Python 3.11 (1d59de4b)
- **edge:** use plain Integer PKs for SQLAlchemy compatibility (41401c47)
- **edge:** skip maintenance loop in test env (a399a0f9)
- **edge:** SQLite-compatible BigInteger PKs, tz-aware datetime math, governance flush (70908a9c)
- **edge:** make tests pass under conftest's SQLite + autoflush=False (e9f0465f)
- **ci:** restore routes/ai.py to original — minimal gateway integration (d7a0540b)
- **ci:** make google-generativeai optional (comment out from requirements) (a1d099b1)
- **vite:** use ESM-safe __dirname (fileURLToPath of import.meta.url) (edaddc3c)
- **test-isolation:** also flush Redis between tests (9c8015b2)
- **backend-test:** test isolation for rate limit + perm_version cache (3371ee41)
- **backend-test:** unblock 2 failing unit tests (00da5939)
- **ci:** run alembic upgrade head before backend-test and smoke-test (9817fc44)
- **startup_guard:** gate SECRET_KEY missing-error on IS_PRODUCTION (4f31d06d)
- **ci:** install pytest via requirements-dev.txt in backend-test job (65d70b61)
- **ci:** resolve backend-test and migration-gate CI failures (b5683fd8)
- **tests:** bypass startup guard in route test fixtures to fix CI 503 errors (a7922ce5)
- **ci:** resolve broken backend-test and migration-check jobs (c519aab0)
- **ci:** silence bandit md5 finding + tighten migration 0001 glob (abe06907)
- **security:** close 2 Dependabot alerts (Vite 5.4.23, drop unused Drizzle) (d9e64ca3)
- **security:** patch 15 Dependabot vulnerabilities in npm deps (2fc3b52f)
- **performance:** 4 root-cause fixes from chaos test results (e3993488)
- **nginx:** add /health/ prefix location + SSL host config (74ac67e9)
- complete delivered_at→processed_at sweep + nginx prefix location (3cdeaa74)
- **backend:** two real bugs found by production audit (6a448402)
- **nginx:** rewrite proxy_pass URI in regex location /api/r/ (d69c477d)
- remove more_clear_headers directive — not available in nginx:1.25-alpine (e7c7f11d)
- pin bcrypt<4.2.0 — passlib 1.7.4 incompatible with bcrypt>=4.2 (3ef7c77f)
- remove invalid indexes on non-existent columns in migration 0010 (00d65772)
- remove CONCURRENTLY from migration 0010 — cannot run inside transaction block (70027c8a)
- restore 447 tests from 178 broken → 0 failures (99298f2d)
- add base schema migration to fix production NoSuchTableError (6ac36645)
- deployment pipeline — alembic auto-migrate + schema gate + CI migration check (f9c224a9)
- graceful shutdown (zombie processes) + Sentry integration + clean print flow (95b22a12)
- 4 UX killers blocking human test (print blank page, portal.html, name #ID) (8c104ac6)
- login redirect + DB health status check for human test readiness (24c2e8e2)
- failure_threshold attribute typo + 5 break-scenario tests (c7943195)
- pg_hba.conf allow 172.16.0.0/12 to cover all Docker bridge subnets (6cc151d0)
- add listen_addresses='*' to postgresql.conf (1fb980df)
- cap DB retry backoff at 30s to prevent 2048s+ wait on attempt 11+ (043b1f77)
- database indexes, nginx cookie, CI Hadolint, domain unit tests (5fec1eca)
- eliminate all pyflakes warnings + harden CI syntax-gate (d707225e)
- undefined names in compliance.py + CI runtime smoke test (ef222be2)
- audit_service.py missing imports + duplicate function definitions (68fe216e)
- remove self-import in /health/deep, use ConcurrencyLimitMiddleware directly (6724d79c)
- nginx routing for /register, /logout, /r/* + dev startup script (0f6ca5ed)
- resolve 3 bugs in ai/ai_service.py (cc477d96)
- return HTTP 201 Created on all resource-creation POST endpoints (15ba6334)
- emergency-fix.sh — apply 8080 port mapping and install maintenance page (88d80370)
- security hardening — auth, RBAC, token revocation, secrets (ad4d1114)
- security hardening — timing attack, IDOR, race condition, XSS, CSP (6538624c)
- emergency recovery script + deploy guard + citizen login UI (57e4dbee)
- complete stub implementations and logic bugs (0c079f44)
- security and bug fixes — firewall, auth, PII, FK, N+1, masking (65113b8b)
- resolve startup crash and harden security across platform (123fc927)
- replace ::regclass with to_regclass() in alembic migration (8d68248e)
- 502 Bad Gateway — nginx resilience + OS kernel tuning (070320c6)
- public result routing, real client IP in audit logs, dead code removal (b441261d)
- Fernet key format, IP extraction, nginx health/status routing (d9d95b7b)
- server diagnostics, /health/status endpoint, deploy verification (0b050d3f)
- 502 Bad Gateway + registration approval flow + citizen admin endpoints (7920351c)
- eliminate double-nginx — Docker nginx owns ports 80/443 directly (d48cc85d)
- resolve 502 — Docker api-gateway port conflict with system nginx (88995c93)
- comprehensive security audit — round 2 fixes (d1ec215a)
- resolve 502 Bad Gateway and multiple security vulnerabilities (2bde1178)
- resolve 502 Bad Gateway — port mismatch between system nginx and Docker (bc3545de)
- resolve 502 Bad Gateway and enable citizen registration (2de8114c)
- add missing integration_test.sh + remove orphaned pass statement (0d44f95f)
- run alembic migrations on backend container startup (4ac22cd7)
- refresh token rotation — blacklist old JTI on use (fd12e00a)
- better login diagnostics + emergency server fix script (17d2673d)
- always run create_all to ensure DB tables exist in production (641f3c88)
- **cookie:** use path='/' for refresh_token cookie (8d0cc255)
- **cookie:** refresh_token path must match browser URL via nginx (93037c6e)
- **bootstrap+login:** DB as source of truth, clear error messages (733286d2)
- **login:** resolve 500 error on login (b0d5a622)
- **security:** hashed admin password + Redis health check (ceec9e24)
- **redis:** fail fast in production if Redis unreachable (7a6c9751)
- enable redis dependency in requirements.txt (02b4a833)
- force-recreate api-gateway on deploy to guarantee nginx picks up config (fbb55899)

### Security
- JWT blacklist, login fix, offline idempotency, rate limiting (9a4271df)

### Other
- add root pyproject configuration (98f2d438)
- Merge pull request #102 from samertts/claude/medical-intelligence-production-iDkzS (b33e6fd5)
- Merge pull request #101 from samertts/claude/gula-production-launch-ceunu (bd79a776)
- Merge pull request #100 from samertts/claude/fix-production-build-fgqHb (04d83282)
- Merge pull request #99 from samertts/claude/sovereign-healthcare-infrastructure-eyES3 (d920dd4d)
- **sovereign:** national infrastructure & governance phases 16–25 (adb712bd)
- Merge pull request #98 from samertts/claude/hardening-phases-9-15 (427e51c2)
- Merge pull request #97 from samertts/claude/fix-duplicate-migration-revision (610e501f)
- production-readiness hardening Phases 9–15 (additive only) (80d96cc6)
- Merge pull request #96 from samertts/claude/analyze-test-coverage-TuQ86 (c38dae5c)
- production-hardening regression suite (additive, no production changes) (695ee300)
- Merge pull request #95 from samertts/claude/implement-todo-item-KiRjG (8fe257a8)
- Merge pull request #94 from samertts/claude/add-claude-documentation-B1uSq (2dd61bef)
- Merge pull request #93 from samertts/claude/integrate-google-ai-studio-1rGMe (a7580928)
- **claude:** update CLAUDE.md to reflect current codebase state (May 2026) (7890dc47)
- Merge pull request #92 from samertts/claude/system-improvements-7FUnw (72792620)
- Merge pull request #91 from samertts/claude/financial-engine-phase-a-eNXWh (40e02674)
- Merge pull request #90 from samertts/claude/sndhs-core-architecture-QzKHF (79ab2328)
- **sndhs:** add core architecture spec for Sovereign National Digital Health System (dd90ca27)
- Merge pull request #89 from samertts/claude/fastapi-lifespan-and-ci-fixes (ed295e0a)
- Merge pull request #88 from samertts/claude/system-improvements-7FUnw (d781c350)
- Merge pull request #87 from samertts/claude/patient-card-system-mMGez (d27aa17b)
- Merge pull request #86 from samertts/claude/repair-droplet-issues (ed5704b0)
- **ops:** add scripts/repair-droplet.sh — fix-all repair script (3fd30adf)
- Merge pull request #85 from samertts/claude/setup-digital-ocean-server-gV0tt (c011a1ab)
- **ops:** add scripts/diagnose-droplet.sh read-only diagnostic (c44bb356)
- Merge pull request #84 from samertts/claude/production-deployment-setup-tyIXE (e26ea1a3)
- **deployment:** rewrite PRODUCTION_DEPLOYMENT.md to match actual stack (159b6c13)
- Merge pull request #83 from samertts/fix/pin-pytest-asyncio-below-1x (717d21d8)
- Merge pull request #82 from samertts/claude/consolidate-github-repos-SWxh5 (a922ccc9)
- Merge pull request #81 from samertts/claude/strict-runtime-isolation-cFNJy (503e3391)
- Merge pull request #80 from samertts/claude/strict-runtime-isolation-cFNJy (675f8275)
- Merge pull request #79 from samertts/claude/enforce-runtime-isolation-zNZ2b (d65933ce)
- Merge pull request #78 from samertts/claude/edge-ai-platform-Om5ie (9fa9a7a9)
- enforce strict runtime isolation across API/worker/test/CLI (6073f8f3)
- Merge pull request #77 from samertts/claude/integrate-google-ai-studio-1rGMe (fd87a262)
- ignore pytest-junit.xml artifact in backend/ (cf1a92f5)
- **ci:** restore routes/ai.py to exact main state to isolate CI failure (86c4d6d2)
- integrate Google AI Studio via official SDK (google-generativeai) (fa228823)
- Merge pull request #76 from samertts/claude/security-multipart-vercel (4b82dbc4)
- sec(deps) + chore(vercel): patch python-multipart CVEs + pin Vercel build (0989587c)
- Merge pull request #75 from samertts/claude/follow-ups-architecture (00ffafb4)
- Merge pull request #67 from samertts/claude/fix-ci-broken-main (91a159ae)
- Merge branch 'main' into claude/fix-ci-broken-main (ed692d8f)
- Merge pull request #65 from samertts/claude/add-claude-documentation-p04Lu (9147002a)
- Merge pull request #64 from samertts/claude/notification-system-2n0Wq (10b8e0e4)
- Merge branch 'main' into claude/notification-system-2n0Wq (642329bc)
- Merge pull request #63 from samertts/claude/setup-docker-compose-4yjHa (0bd94b7e)
- Merge pull request #62 from samertts/claude/doctor-order-tests-api-EFBez (108c4069)
- Merge branch 'main' into claude/doctor-order-tests-api-EFBez (af967570)
- **follow-ups:** pre-commit hooks + OpenAPI contract gate + tsconfig fix (3c018a84)
- Merge pull request #61 from samertts/claude/epidemic-detection-service-26Ft6 (dfa61818)
- Merge branch 'main' into claude/epidemic-detection-service-26Ft6 (5f03ac86)
- Merge pull request #71 from samertts/claude/analyze-test-coverage-Bdm2F (3f8b4bfd)
- Merge branch 'main' into claude/analyze-test-coverage-Bdm2F (429262f4)
- Merge pull request #74 from samertts/claude/security-vite-uuid (86bde7da)
- **deps:** patch Vite path-traversal + uuid bounds-check CVEs (479a2237)
- Merge pull request #73 from samertts/claude/hotfix-ci-recovery-Oy7Bh (7e3165d0)
- **vercel:** scaffold React app entry so Vite can build (9c2e6c60)
- **ci:** stabilize frontend structure + db engine portability (f812e709)
- Merge pull request #72 from samertts/claude/fix-smoke-test-migrations (2d7a7af8)
- Merge pull request #68 from samertts/claude/implement-todo-BqLud (77835aa8)
- Merge pull request #70 from samertts/claude/analyze-test-coverage-Bdm2F (6da1d1c8)
- Merge pull request #69 from samertts/claude/analyze-test-coverage-Bdm2F (9c95e591)
- Add test coverage improvements, resilience layer, and frontend API preparation (6e0ee9e7)
- **backend-test:** add pip-freeze env snapshot + pytest --maxfail=1 (8ee70127)
- **backend-test:** upload pytest log + JUnit XML as artifact (d3023076)
- **backend-test:** bump postgres 14.11-alpine → 16-alpine (b6322f73)
- **smoke-test:** run alembic upgrade head before starting uvicorn (ab528e60)
- fix backend-test and Alembic Migration Gate on main (5d46e424)
- rewrite CLAUDE.md with comprehensive architecture and workflow guide (6b29dd7c)
- Add epidemic detection service (CMD-013) (b9193357)
- Merge pull request #60 from samertts/claude/add-test-results-api-KTbDN (83f7b4c5)
- Merge pull request #58 from samertts/claude/add-test-result-model-XVjSp (b83d97c9)
- Merge pull request #57 from samertts/claude/create-lab-model-H78Zz (d96ef9db)
- Merge branch 'main' into claude/create-lab-model-H78Zz (868984d1)
- Merge pull request #56 from samertts/claude/citizen-registration-api-IjrL1 (975d7e8b)
- Merge branch 'main' into claude/citizen-registration-api-IjrL1 (57e9a7de)
- Merge pull request #55 from samertts/claude/generate-health-id-OFg57 (1467ec26)
- Merge pull request #54 from samertts/claude/create-citizen-model-L82q8 (79677627)
- Merge pull request #53 from samertts/claude/setup-fastapi-main-app-bNcze (8fdd88d1)
- Merge pull request #52 from samertts/claude/setup-db-config-VuywV (8d8f801a)
- Merge pull request #59 from samertts/claude/add-test-results-api-1ozK2 (8260973f)
- Merge pull request #51 from samertts/claude/health-platform-launch-bVZs3 (8af6ae8f)
- Merge pull request #50 from samertts/claude/health-platform-launch-bVZs3 (ea930343)
- Merge pull request #49 from samertts/claude/setup-deployment-platforms-jQYUw (5734e983)
- Add production specification for GULA platform (f5f33676)
- Merge pull request #48 from samertts/claude/setup-deployment-platforms-jQYUw (5995b84a)
- Merge pull request #43 from samertts/codex/fix-unhealthy-gula-backend-container-zjakxk (bdd732c0)
- Merge branch 'main' into codex/fix-unhealthy-gula-backend-container-zjakxk (f6ed2d8f)
- Merge pull request #47 from samertts/claude/deploy-fastapi-render-Tk0WF (7a764dd6)
- Merge pull request #46 from samertts/claude/prepare-system-deployment-tptwG (974c9e50)
- **ops:** tune all configs for 4 GB / 2 vCPU production server (0f031976)
- stop retrying http_500 + increase DB pool (f09db2b9)
- **chaos:** add Chaos & Resilience Test Suite (3f78cc0d)
- Merge pull request #45 from samertts/claude/merge-prepare-production-ih1XG (50065e27)
- Merge pull request #44 from samertts/claude/merge-prepare-production-ih1XG (c5d297ef)
- migration governance + security patch + chain integrity tests (2b47fec3)
- add syntax-gate job — blocks build on NameError/SyntaxError (f0fe5738)
- claude/merge-prepare-production-ih1XG → main (production hardening) (6c951074)
- Merge branch 'main' of http://127.0.0.1:32839/git/samertts/gula-platform (89c16452)
- Fix backend startup syntax and tighten production secrets (f559a68e)
- Merge pull request #42 from samertts/codex/fix-unhealthy-gula-backend-container (675a8c3b)
- Increase backend startup tolerance in compose healthcheck (aa7de8e5)
- Merge pull request #41 from samertts/codex/fix-the-issue (c11c691a)
- override vulnerable transitive deps (7e1ea21f)
- add comprehensive documentation, infrastructure guide, and marketing strategy (c076238a)
- add strategic analysis, business plan, and pitch deck content (6e283d46)
- ✨ Add Performance & UI Optimizations (8ad4f8bd)
- Corrected Dockerfile CMD for Uvicorn workers to properly parse WEB_CONCURRENCY environment variable using sh -c. (5c47292f)
- Final Anti-Fragile System Enhancements: Smart DB Wait, Startup Events, Enhanced Healthchecks, Self-Healing, and Security Hardening. (04740c4d)
- Corrected docker-compose.yml by removing Docker Swarm 'deploy' configurations and ensuring proper restart policies. Also improved backend health check and startup guard resilience. (4836f10c)
- Corrected docker-compose.yml by removing Docker Swarm 'deploy' configurations to ensure compatibility with standard Docker Compose. (13265cc3)
- Final Optimization: Implement eager loading for results, optimize patient search indexing, enhance rate limiting with dynamic IP blocking, and upgrade monitoring with alerting system. (4d1752ed)
- Add ping() to _MemoryStore, improve Redis fallback, enhance Nginx security, optimize metrics queries, and implement monitoring/autofix tools. (6a6eded1)
- Merge origin/main into local main (resolve conflicts) (9a041dad)
- Merge claude/server-image-branching-iyurJ into main (87bbaaf8)
- Merge claude/merge-and-secure-system-E5hKR into main (944775c5)
- Merge claude/fix-deployment-pipeline-iyurJ into main (4fa1ceeb)
- Merge pull request #37 from samertts/claude/merge-and-secure-system-E5hKR (ea2582f3)
- Merge pull request #38 from samertts/claude/ai-system-optimizer-6kPhv (4d6ecbaf)
- Merge pull request #40 from samertts/claude/server-image-branching-iyurJ (5a95b8e0)
- Merge branch 'main' into claude/server-image-branching-iyurJ (024d66db)
- Merge pull request #39 from samertts/claude/fix-bugs-vulnerabilities-Y6mGU (ab00b3cf)
- Merge remote-tracking branch 'origin/claude/fix-bugs-vulnerabilities-Y6mGU' (ffeee17b)
- Merge pull request #36 from samertts/claude/fix-bugs-vulnerabilities-Y6mGU (882fa3de)
- Merge pull request #35 from samertts/claude/fix-bugs-vulnerabilities-Y6mGU (be285eb3)
- nginx caching, DB pool tuning, multi-stage Docker build, Redis graceful degradation (8dad6b56)
- Merge pull request #34 from samertts/claude/fix-bugs-vulnerabilities-Y6mGU (9ce31e32)
- Merge pull request #33 from samertts/claude/server-image-branching-iyurJ (21716f0a)
- expose api-gateway on public ports 80/443 (f9f5446e)
- Fix Docker build: replace offline wheels with standard pip install (4871487c)
- Add .dockerignore for backend wheels and update .gitignore (d9e258a0)
- Fix production deployment: Docker build + bcrypt compatibility (bb71d6d6)
- Add operational metrics, offline queue, and background sync (c5e4175a)
- Fix login flow + redesign login page (300f0b03)
- Add state machine engine, event bus, and immutability enforcement (adc52f94)
- Implement order state machine, validation locking, and search (0428fd6b)
- Improve frontend UX: orders search/pagination, lab stats, workflow bugfixes (0d62373c)
- Complete frontend UI & add citizen registration endpoint (2f523d2f)
- Merge pull request #32 from samertts/claude/server-image-branching-iyurJ (c485cd97)
- auto-create master admin on startup, add welcome dialog and enhanced admin UI (5d07afba)
- add change-master-password.sh script (ace36b3e)
- Merge pull request #31 from samertts/claude/server-image-branching-iyurJ (f5fdac60)
- audit immutability, DB indexes, doctor isolation, admin rate limit (4595cc4b)
- zero-failure hardening — DB revocation, idempotency, per-user rate limiting (d30b4eaf)
- Merge pull request #30 from samertts/claude/server-image-branching-iyurJ (2ff946cb)
- perf+test: startup warmup, stress tests, lab load simulation (2f630c60)
- add comprehensive test suite (103 tests across 15 categories) (af152b91)
- Merge pull request #29 from samertts/claude/server-image-branching-iyurJ (3ac02732)
- Radical nginx cleanup: remove all redundant direct backend routes (a90e49df)
- Fix 404 on GET /login and /register (nginx routing bug) (25352afc)
- Harden deploy.sh and monitor.sh (81aa6c3f)
- Add Alembic migrations + uptime monitor (86b129ba)
- Add safe deploy script with backup + health check (641c5fdd)
- Fix architecture: real backend endpoints + clean nginx (7edfea42)
- Add frontend pages (test-types, employees, profile) + fix nginx routing (108a62e3)
- Fix nginx routing: use exact match for /login, /logout, /register (00861144)
- Add emergency-fix.sh — one-shot server repair + permanent watchdog install (210aecb1)
- Fix site outage root causes permanently (a0dbad9b)
- Merge branch 'main' into claude/fix-deployment-pipeline-iyurJ (9c86a887)
- Add OPERATIONS.md — pre-presentation and weekly runbook (e69d1747)
- Last 2 hardening items: restore JSON signing, NTP drift detection (3fea90b4)
- Final hardening: anchor rotation, restore evidence, secrets setup (cdca6766)
- Security hardening: anchor key versioning, frontend role guard (56593be2)
- Final audit: Compliance UI, anchor HMAC signing, restore test (077deaa1)
- Merge pull request #27 from samertts/claude/server-image-branching-iyurJ (a4c34e93)
- Security hardening: root anchor, HTTPS setup, backup integrity, compliance dashboard (48ce9bf6)
- Tamper-proof audit, docs protection, HTTPS setup, security report (5a2e0bba)
- Infrastructure security hardening, Arabic PDF, audit immutability (0ba880f0)
- Government compliance: FHIR DiagnosticReport, ServiceRequest, DHIS2 export (4de2fd48)
- Merge pull request #26 from samertts/claude/fix-deployment-pipeline-iyurJ (a179ee35)
- migrate JWT to httpOnly cookies, hide server headers (09106c08)
- Security hardening, mobile API, government compliance - v2.1.0 (2e37221b)
- Merge pull request #25 from samertts/claude/fix-deployment-pipeline-iyurJ (0794b08f)
- Fix deployment pipeline: use MVP compose, auto-create .env, valid Fernet keys (dd84a953)
- Merge pull request #24 from samertts/claude/server-image-branching-iyurJ (ba9652fa)
- Fix backend unhealthy: handle invalid Fernet ENCRYPTION_KEY gracefully (a64cb337)
- Add DigitalOcean server setup script and deployment guide (fff574ae)
- Merge pull request #23 from samertts/claude/arabic-greeting-lDwg6 (edede67b)
- Performance optimization: resource limits, workers, caching (73b7e883)
- Merge pull request #22 from samertts/claude/arabic-greeting-lDwg6 (d2b68486)
- Add logs/nginx directory for api-gateway volume mount (30721816)
- Fix 3 root causes preventing platform from starting (9671da4c)
- Harden Docker deployment to prevent orphan container failures (66e04896)
- Merge pull request #21 from samertts/claude/arabic-greeting-lDwg6 (f82a2248)
- Fix all 15 failing tests: make tests self-contained and environment-independent (d9944eef)
- Beta launch prep: performance optimization, resilience hardening, failure testing (75f954ec)
- Merge pull request #20 from samertts/claude/arabic-greeting-lDwg6 (f10d3902)
- Merge branch 'main' into claude/arabic-greeting-lDwg6 (2c4c3981)
- Fix 15+ bugs, logic errors, and edge cases (round 2) (70c9aff2)
- Security hardening: fix 17 vulnerabilities across all severity levels (9ce11525)
- GULA v2.0: Major performance optimization + QC system + critical alerts + batch processing (638b735a)
- update (6e18465b)
- Merge pull request #19 from samertts/codex/fix-platform-issues-as-project-manager-knmhsk (4f3ea063)
- Merge branch 'main' into codex/fix-platform-issues-as-project-manager-knmhsk (68dc4eae)
- Fix deploy/health scripts and self-heal to recover gateway outages (8ed680a7)
- Merge pull request #18 from samertts/codex/fix-platform-issues-as-project-manager (d932b34f)
- Fix 502 Bad Gateway: resolve port conflict between system and Docker nginx (e117d991)
- Fix gateway upstream DNS resolution to prevent 502 (586aba49)
- Merge pull request #17 from samertts/claude/arabic-greeting-lDwg6 (17fea742)
- Fix CI docker-build: add load:true so Trivy can scan the image (4c6e32a3)
- Merge branch 'main' into claude/arabic-greeting-lDwg6 (393cc613)
- Fix deploy failures: add health routes, deploy scripts, rollback support (b251a824)
- Merge pull request #16 from samertts/codex/perform-root-cause-analysis-for-502-error-meevtq (72fd8d78)
- Merge branch 'main' into codex/perform-root-cause-analysis-for-502-error-meevtq (e7ae3ff6)
- Add inline fallback deploy path to eliminate missing-script failures (1d6a5e94)
- Merge pull request #15 from samertts/codex/perform-root-cause-analysis-for-502-error-0zb084 (7fe66773)
- Merge branch 'main' into codex/perform-root-cause-analysis-for-502-error-0zb084 (ded090a3)
- Stabilize production deploy flow and harden recovery scripts (4eab4e61)
- Merge pull request #14 from samertts/codex/perform-root-cause-analysis-for-502-error-mb4rmn (2213dc91)
- Merge branch 'main' into codex/perform-root-cause-analysis-for-502-error-mb4rmn (18cc466d)
- Make deploy workflow self-bootstrap repo before running scripts (c474dedf)
- Merge pull request #13 from samertts/codex/perform-root-cause-analysis-for-502-error-tqlq6b (6d10460d)
- Merge branch 'main' into codex/perform-root-cause-analysis-for-502-error-tqlq6b (610cd228)
- Fix deploy workflow YAML syntax and SSH heredoc block (88bbc45f)
- Merge pull request #12 from samertts/codex/perform-root-cause-analysis-for-502-error-4238jn (436aab4f)
- Merge branch 'main' into codex/perform-root-cause-analysis-for-502-error-4238jn (e1a4138d)
- Fix deploy pipeline and container healthcheck reliability (e8238bca)
- Merge pull request #11 from samertts/codex/perform-root-cause-analysis-for-502-error (ff118ea1)
- Harden gateway and add self-healing deployment tooling (884efd98)
- Add CI pipeline, automated backups, and deploy improvements (99276549)
- Fix critical infra issues: pin images, harden deps, remove hardcoded creds (0c15858d)
- Fix microservice bugs: Kafka leak, upload validation, pagination bounds (7564f92f)
- Comprehensive security & reliability fixes across entire codebase (5838bc73)
- Fix deploy: replace eval-based env gen with inline checks (c999ebcb)
- Refactor deployment workflow for GULA server (b2d58d67)
- Fix deploy: auto-generate missing env vars (SECRET_KEY, ENCRYPTION_KEY) (e09c36ee)
- Merge pull request #10 from samertts/claude/arabic-greeting-lDwg6 (8dffcab3)
- PWA support, nginx optimization, aggressive caching (6c422462)
- Fix deployment: preserve .env file during git reset (5c39e752)
- Harden microservices: remove hardcoded credentials, add shutdown handlers (67a8f0c2)
- Merge pull request #9 from samertts/claude/arabic-greeting-lDwg6 (96e3cfce)
- Comprehensive security hardening and platform improvements (e918cce3)
- Add personalized Arabic greeting to dashboard (ab8e018b)
- Comprehensive code review fixes: security, performance, and quality (eeefad26)
- Security hardening: remove exposed ports, enforce secrets, add HTTPS (2535bb1e)
- Merge pull request #8 from samertts/claude/merge-to-main-lDwg6 (ec32e6de)
- Clean platform: archive old scripts, fix naming, harden deploy (850f1495)
- Fix frontend not loading: remove backend frontend serving (7c366cc2)
- Build professional lightweight frontend from scratch (304510d5)
- Restructure project: clean root, archive non-essential, simplify for MVP (1ce298a3)
- Harden infrastructure security: secrets, configs, deploy pipeline (d51368bc)
- Fix critical security vulnerabilities found in deep audit (92cbce91)
- Fix website not loading: gateway deps, deploy workflow, shared modules (8bc95607)
- Fix website not loading: move backend to services, add frontend proxy (73a0c61e)
- Add admin panel, sample tracking, User model, fix encryption & stub routes (5917b089)
- Production-ready: serve frontend, SMS fallback, API routing fix (78ef3173)
- Add WhatsApp auto-send and enhanced dashboard analytics (5cc7ddf2)
- Add Structured Medical QR, duplicate detection, ID scan, and onboarding (c07dc5ae)
- Add token hashing (SHA-256) and PDF report download with QR code (f7326a09)
- Fix expiry UX, add name verification to public history lookup (6ebfe899)
- Add security hardening, audit logging, composite tests, and patient history (2b27d5f2)
- Build GULA v1 MVP: Lab Result Platform with Smart Interpretation (c38e5bde)
- Search indexing layer added (4a19ddd7)
- Upgrade GULA platform to production architecture (7f2c0797)
- Safe enhancement layer added (UI + CDN + improvements) (3d4e2320)
- safe enhancement layer added (UI + cleanup + structure) (23d372ff)
- Advanced repository cleanup and architecture improvement (935b287b)
- server update (3eb8d5ac)
- Fix SSH command and update deployment messages (c20086df)
- Update deployment workflow to use SERVER_HOST (3e778156)
- Merge pull request #6 from samertts/fix-deploy-workflow (b7a9af80)
- fix deploy workflow (0bf56819)
- Merge pull request #3 from samertts/claude/setup-gula-platform-GTh4t (7e764b8a)
- National-grade improvements: HA, chaos testing, DR, service mesh (7388ed40)
- Hardening phase: security, reliability, and observability improvements (dab3af85)
- Implement GULA Platform enterprise infrastructure (23 executive orders) (fc15b161)
- Fix SSH user for deployment in workflow (0851b4b3)
- Add GitHub Actions workflow for deployment (8e38ed69)
- Add security policy for reporting vulnerabilities (95d9bbf3)
- refactor project structure (4a030550)
- Initial commit (1b3b66a6)
- Initial NHOP platform commit (d2863c35)


## [2026-07-16] — v2.3.0 — Missions 025-028: National Healthcare Platforms
### MISSION-025: National Hospital Desktop Workspace (NHDW)
- **Hospital Dashboard**: Real-time KPIs — admissions, discharges, transfers, bed occupancy, emergency status, ICU/OR status
- **Patient Administration**: Full ADT lifecycle — registration, admission, transfer, discharge, queue management, bed assignment
- **Clinical Operations**: Ward rounds, clinical tasks, vital signs, care plans, clinical timeline, electronic signature
- **Department Platform**: Emergency, ICU, NICU, OR, Internal Medicine, Pediatrics, Surgery, Obstetrics, Cardiology, Dialysis, Oncology
- **Resource Management**: Beds, rooms, equipment, medical devices, consumables, maintenance, cleaning, sterilization
- **Hospital Communication**: Secure messaging, clinical collaboration, referral coordination, critical alerts, escalation
- **Telemedicine**: Session management, secure video, recording, patient/provider portals
- **Offline Platform**: Encrypted local SQLite, offline registration, conflict resolution, delta sync, background sync
- **Desktop Experience**: PySide6 Windows native, RTL, dark mode, accessibility, keyboard shortcuts, multi-monitor, docking panels, role-based UI, feature flags, automatic updates
- **KPI Engine**: Occupancy rates, ALOS, admission/discharge/transfer trends, readmission (30-day), ED wait times (median/p95/p99), OR utilization, bed turnover
- **Route endpoints**: /nhdw/ (50+ endpoints)

### MISSION-026: National Nursing & Care Coordination Platform
- **Nursing Dashboard**: Assigned patients, clinical tasks, medication schedule, vitals due, alerts, ADT overview, shift summary
- **Clinical Care**: Vital signs, fluid balance (intake/output), pain assessment, fall risk, pressure injury, nutrition assessment
- **Medication Administration**: Barcode verification, five rights (patient/drug/dose/route/time), missed/late dose tracking, electronic signature
- **Nursing Documentation**: Nursing notes, structured assessments, shift handover, care plans, clinical checklists, version history
- **Task Coordination**: Clinical tasks, delegation, escalation, priorities, reminders, recurring tasks, clinical checklists
- **Care Coordination**: Physician collaboration, lab/radiology/pharmacy requests, referral tracking, discharge planning, home care handover
- **Offline Platform**: Encrypted local database, offline documentation, offline medication admin, conflict resolution, delta sync
- **Medication Safety**: Drug interaction alerts, allergy checking, overdose prevention, five-rights verification workflow
- **Route endpoints**: /nursing/ (50+ endpoints)

### MISSION-027: National Pharmacy Information Platform (NPIP)
- **Medication Catalog**: National drug catalog, generic/brand names, ATC mapping, drug classes, strength/dosage forms/routes, manufacturer registry, batch registry, GS1 barcodes, drug images
- **Prescription Management**: E-prescription, medication requests, renewals, refills, cancellation, substitution rules, controlled medication rules, electronic signature, FHIR MedicationRequest
- **Clinical Pharmacy**: Drug interaction engine, duplicate therapy, contraindications, allergy checking, dose calculation (age/weight/renal), pediatric dose, pregnancy/breastfeeding alerts, national clinical guidelines
- **Inventory Management**: Warehouse, store, stock levels, batch management, expiry monitoring, cold chain, reorder levels, transfers, returns, waste management, recall management, forecasting
- **Dispensing Platform**: Prescription queue, barcode verification, patient verification, medication labels, counseling checklist, dispensing confirmation, medication history, audit trail
- **Citizen Integration**: Medication history, current medications, prescription status, refill requests, medication reminders, QR verification
- **Offline Platform**: Encrypted local DB, offline dispensing/verification/inventory, conflict resolution, delta sync
- **Route endpoints**: /pharmacy/ (55+ endpoints)

### MISSION-028: National Radiology Information System & PACS (NRISP)
- **Radiology Workflow**: Orders, scheduling, patient preparation, arrival, check-in, imaging workflow, interpretation, verification, report approval, distribution, archiving
- **RIS Platform**: Radiology requests, appointment management, protocol management, contrast tracking, exam status, technologist/radiologist workspaces, critical findings, electronic signature
- **PACS Platform**: DICOM storage, DICOM query/retrieve (C-FIND/C-MOVE/C-GET), image viewer, streaming viewer, image compression, lossless storage, image annotation, measurements, image comparison, image sharing, long-term archive
- **Medical Device Integration**: MRI, CT, X-Ray, Ultrasound, Mammography, Fluoroscopy, Nuclear Medicine, DICOM Modality Worklist, MPPS, device health monitoring
- **Clinical Integration**: EHR, Doctor Workspace, Hospital Platform, Citizen Super App, Nursing, Emergency, Pharmacy, Laboratory
- **AI Imaging Platform**: CAD hooks, image analysis triage, quality detection, explainability, human approval, model registry
- **Citizen Services**: Radiology reports, image viewer, secure sharing, QR verification, image download, appointment tracking
- **Offline Platform**: Encrypted cache, offline worklist, offline reporting, background sync, conflict resolution, delta sync
- **Route endpoints**: /radiology/ (55+ endpoints)

## [2.1.0] - 2026-07-14 — Engineering Program M4.x

### Added
- M4.0 Environment Guardian: Full audit report (assessment/environment_report_4.0.md)
- M4.1 Repository Brain: Knowledge graph (10,858 nodes, 9,778 edges), cross-reference engine, Mermaid diagrams
- M4.2 Architecture Intelligence: GULA-specific scoring engine (Grade B, 7/10)
- M4.3 Dependency Intelligence: Complete SBOM, license report, supply chain analysis
- M4.4 Dependency Upgrade Engine: Lock file (backend/requirements-lock.txt, 58 pinned packages)
- M4.5 Quality Gate Orchestrator: All 5 gates passing (compile, ruff, tests, Dockerfile, lock)
- M4.6 Supply Chain Security: Dependency Guardian monitoring script (scripts/dependency_guardian.py)
- M4.7 Security Hardening: Full security audit, 28 CWE mappings, OWASP/MITRE coverage
- M4.8 Dependency Guardian: Permanent monitoring service (scripts/dependency_guardian.py)
- M4.9 Security Knowledge Base: CWE-79 through CWE-918 mapped, MITRE ATT&CK 8 tactics
- M5 Repository Optimization: Dead code, large modules, empty stubs cataloged
- M6 Kernel Certification: Auth gap fixed on all 11 kernel endpoints
- M7 Capability Factory: Capability catalog with migration roadmap

### Changed
- backend/app/config.py: REFRESH_TOKEN_SECRET now independently random in dev fallback
- backend/app/kernel/routes.py: All 11 kernel endpoints now require JWT authentication
- backend/app/security/jwt_guard.py: Documented as dead code (routes use dependencies.get_current_user)
- backend/requirements.txt: Removed orjson and jinja2 (dead dependencies)
- backend/requirements-dev.txt: Added factory_boy (used by engineering/testing/factories.py)
- shared/notifications/template.py: Fixed F822 lint error (undefined __all__ entry)

## [2026-07-16] — v2.2.0 — Missions 037-039 & EXEC-001: Platform Constitution
### MISSION-037: National Platform Constitution (NPCE)
- **Architecture Constitution**: Clean Architecture, DDD, CQRS, Event-Driven, Hexagonal, Modular Monolith, Microservice Rules, Offline First, FHIR First, API First, Security/Privacy/Accessibility/Observability/AI By Design
- **Engineering Constitution**: Coding/naming/API/database/migration/testing/logging/telemetry/documentation/versioning standards
- **Quality Constitution**: Mandatory gates — coverage >=95%, zero critical bugs/vulnerabilities/architecture violations/circular deps/dead code/unused deps/hardcoded secrets/broken docs
- **Security Constitution**: Zero Trust, RBAC, ABAC, mTLS, Encryption, Secrets Rotation, SBOM, Supply Chain Security, Dependency/Architecture/Runtime/AI Guardians
- **AI Constitution**: Human Approval, Explainability, Prompt/Model Registry, Validation/Monitoring, Hallucination/Bias Detection, Audit Trail, Safety
- **Developer Constitution**: Automatic code/tests/docs/API catalog/SDK/architecture validation/security review/release notes
- **Operations Constitution**: Monitoring, Tracing, Metrics, Health Checks, Backups, Recovery, Chaos Engineering, Capacity Planning, Business Continuity, DR
- **Release Constitution**: Stable/LTS/Beta/RC/Nightly, Rollback, Migration/Compatibility Validation, Feature Flags
- **Continuous Evolution**: Self-assessment, Tech Debt/Architecture Drift Detection, Auto-refactoring/Performance/Security/Dependency suggestions
- **ADR-024**: Platform Constitution & National Trust Framework

### MISSION-038: National Trust, Compliance & Privacy Platform
- **Privacy Platform**: Consent management, purpose of use, minimum necessary access, sensitive record protection, minor/guardian policies, data masking/anonymization/pseudonymization, retention policies
- **Digital Sovereignty**: National data ownership, data residency, cross-border transfer prohibition, key ownership, national encryption/backup policies
- **Compliance Framework**: Configurable compliance, evidence collection, dashboards, corrective actions, continuous compliance
- **Trust Services**: Digital signature, timestamping, evidence preservation, certificate lifecycle, identity verification, document integrity
- **AI Trust**: Transparency, explainability, human approval, model/prompt audit, bias monitoring, safety validation
- **National Audit**: Immutable audit, forensic logs, chain of custody, evidence export, integrity verification
- **Long-Term Preservation**: Medical record/archive/migration policies, checksum validation, integrity monitoring
- **Citizen Trust**: Privacy/consent dashboard, access history, notification center
- **Trust Platform Code**: `backend/app/trust/` — ConsentService, SovereigntyService, TrustService, ComplianceService with full REST API

### MISSION-039: Autonomous Platform Factory (APFE)
- **Repository Intelligence**: Dependency/Module/Architecture/Event/API/Data Flow/Technical Debt/Ownership graphs
- **Autonomous Code Factory**: CRUD/Repository/DTO/Command/Query/Event/Service/REST/SDK/CLI/Doc/Test generation
- **Autonomous Architecture**: Drift/circular deps/duplicate logic/dead code/performance/scalability/security hotspot detection
- **Autonomous DevSecOps**: Build/test/security scan/dependency upgrade/SBOM/release notes/changelog/versioning/packaging/deployment
- **Autonomous Quality**: Ruff/MyPy/Pytest/Coverage/Bandit/Semgrep/Trivy/pip-audit/Safety/OpenAPI/FHIR/Architecture/Performance/Accessibility
- **Autonomous Documentation**: All documentation auto-generated from source
- **Autonomous Operations**: Monitor/Trace/Scale/Recover/Rollback/Backup/Restore/Rotate secrets/certificates/Optimize

### EXEC-001: National Platform Implementation Wave 1
- **Implementation Audit**: Full repository audit — modules, APIs, DB, deployment, gaps
- **Missing Features Detected**: Consent/serenity/trust services, code generation CLI, knowledge graph
- **Production Hardening Targets**: Startup/memory/DB/offline optimization
- **Pilot Deployment**: Criteria, metrics, rollout plan
- **National Rollout**: Governorate-phased rollout with rollback strategy

### Constitution Enforcement
- **20-Rule Enforcer**: Expanded `scripts/constitution_enforcer.py` from 12 to 20 rules covering constitution, security, privacy, AI, FHIR, architecture
- **Architecture Guardian**: Layer boundaries, circular deps, naming, docstrings, unused imports
- **Dependency Guardian**: Python/npm vulnerability scanning, outdated packages, cross-manifest conflicts
- **Makefile Targets**: `constitution-enforce`, `constitution-audit`, `trust-platform`, `factory-validate`, `platform-freeze`, `platform-tag`

### Database Migration
- `20260716_0013_national_trust_platform_tables.py`: 6 new trust platform tables (consent records, retention policies, sovereignty rules, service logs, compliance evidence, compliance checks)

### Documentation
- `docs/constitution/PLATFORM-CONSTITUTION.md` — Supreme engineering authority (frozen v1.0.0)
- `docs/trust/NATIONAL-TRUST-PLATFORM.md` — Trust, privacy, compliance (frozen v1.0.0)
- `docs/factory/ENGINEERING-FACTORY.md` — Engineering automation (frozen v1.0.0)
- `docs/execution/EXECUTION-PROGRAM-001.md` — Implementation roadmap (frozen v1.0.0)
- `docs/adr/ADR-024-Platform-Constitution.md` — Frozen architecture decision
- `docs/runtime/SBOM.md` — Comprehensive software bill of materials
- `docs/runtime/ADR.md` — Updated ADR index with ADR-024

### Tags Created
- `platform-constitution-v1.0` (Frozen)
- `national-trust-platform-v1.0` (Frozen)
- `engineering-factory-v1.0` (Frozen)

## [2026-07-16] — v2.3.0 — PI-001 WP2.5/WP3 + PI-002: National Identity, Security & Clinical Core

### Identity Platform (PI-001 WP2.5)
- **Offline Sync Engine**: CRDT-compatible vector clock synchronization, conflict detection with 4 resolution strategies (LWW, timestamp merge, manual, CRDT merge), encrypted local cache (AES-256-GCM via Fernet + zlib compression), operation signing and verification, sync logging
- **Device Trust Service**: Browser/device fingerprinting (UA, screen, fonts, canvas, WebGL, audio), trust level escalation (UNKNOWN→TRUSTED), automatic deactivation on excessive failures
- **Risk-Based Authentication**: Context-aware risk scoring (0-100), impossible travel detection (Haversine), Tor/VPN/datacenter detection, adaptive responses (proceed→step-up→MFA→block), decision logging
- **Identity Governance**: PostgreSQL persistence for identity records, break glass, merge proposals via repository pattern with optimistic locking
- **Tests**: 49 new tests across offline sync (20), device trust (15), risk-based auth (14)

### Security Platform (PI-001 WP3)
- Complete Zero Trust architecture with continuous verification
- RBAC (9 roles × 13 permissions) + ABAC (attribute conditions engine)
- JWT with Redis blacklist + perm_version double-layer revocation
- OAuth2/OIDC with PKCE (S256), JWKS, introspection, revocation
- MFA: TOTP, HOTP, WebAuthn/FIDO2/Passkeys, backup codes
- SAML 2.0 SSO, Service Accounts with API keys
- Rate limiting (Redis-backed fixed window, per-IP/per-user/per-auth)
- Intrusion detection (time-windowed, per-IP caps)
- Action risk scoring engine (0-10 scale)
- Encrypted storage at rest (AES-256-GCM via Fernet, HMAC-signed)

### Clinical Core (PI-002)
- MPI: Fellegi-Sunter probabilistic matcher, deterministic NID short-circuit
- Citizen model with identity claims and merge audit chain
- EHR: Clinical notes, encounters, diagnoses, allergies, medications, immunizations, care plans, vital signs, attachments
- FHIR R4 API: Patient, Observation, DiagnosticReport, MedicationRequest, AllergyIntolerance, Condition, Encounter, Immunization, CarePlan
- LIMS: Orders, samples, barcodes, QC, EQA, reference ranges, delta checks, Westgard rules
- 47 Alembic migrations covering identity, clinical, security, financial, governance

### Tags Created
- `identity-platform-v1.0` (Frozen)
- `security-platform-v1.0` (Frozen)
- `clinical-core-v1.0` (Frozen)
