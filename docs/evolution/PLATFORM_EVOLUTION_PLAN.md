# GULA Platform Evolution Plan

> Version: 1.0 | Status: Draft | Last Updated: 2026-07-17
> Applies to: GULA Platform v2.1.0 (monolith + 8 microservices)

---

## 1. Evolution Principles

### P1 — Stable Core, Volatile Edges
The monolith (`backend/app/`) is the system of record. New capabilities must be built as optional extensions before they can replace core paths. Never extract from the monolith until extraction is proven safe via feature-flag gating.

### P2 — Data Integrity Above All
No evolutionary step may risk patient data loss, corruption, or temporary unavailability during normal operation. Every migration must support rollback. The `outbox_events` table guarantees delivery; any extraction must preserve this guarantee.

### P3 — Tenant Isolation at Every Layer
All patient-data queries MUST filter by `lab_id = current_user.lab_id`. Tenant isolation must survive service splits, CQRS views, and event bus routing. Never introduce a shared-nothing service that bypasses lab-level scoping.

### P4 — Strangler Fig Pattern
When extracting a module from the monolith, the strangler fig pattern is mandatory: build the new service alongside, route traffic incrementally via feature flags, monitor parity, and only delete the monolith code when zero traffic reaches it.

### P5 — Async-First Communication
Synchronous HTTP between monolith and extracted services is a temporary bridge. All new inter-service communication must be event-driven via Redis Streams or RabbitMQ. The `outbox_events` pattern (already in use) is the template for all async boundaries.

### P6 — Observability Before Extraction
Before any service is extracted, it must have: structured JSON logging (already in place via `logging_config.py`), OpenTelemetry tracing, Prometheus metrics, and at least one health check endpoint. No service ships without these three pillars.

### P7 — Feature-Flag Every Break
Every extraction, merge, or API change must be behind a per-tenant feature flag (`backend/app/core/feature_flags.py`). Rollout is gradual: 1 lab → 10 labs → 50% → 100%. Kill switches are not optional.

### P8 — Preserve the Health Chain
The five health endpoints (`/health`, `/health/live`, `/health/ready`, `/health/status`, `/health/deep`) must continue to function through every evolutionary phase. The self-healing system (`core/self_healing.py`, `core/auto_repair.py`) must never be bypassed.

### P9 — Test the Migration Path
Every extraction must include: (a) integration tests where both monolith and extracted service run simultaneously, (b) a chaos scenario that kills the extracted service to verify fallback, (c) a rollback test. This is enforced by CI.

### P10 — People Follow Architecture
Team topology must match the target architecture before the architecture is implemented. The current 3-person team determines extraction velocity. Conway's Law is a constraint, not an outcome.

---

## 2. Current State Assessment

### 2.1 Monolith Health
- **Lines of code**: ~45,000 Python in `backend/app/`
- **Routes**: 36 route modules in `routes/`
- **Models**: 17 SQLAlchemy ORM models
- **Middleware**: 11 stacked middleware (order-critical)
- **Background loops**: 3 (adaptive concurrency, health alert, self-healing)
- **Self-healing**: 3 layers (circuit breaker, auto-repair, adaptive concurrency)
- **Test coverage**: 28 test modules, but unit coverage of services/ is <40%
- **Health system**: 5 endpoints, multi-layer checks

### 2.2 Microservice Maturity
| Service | Status | Maturity |
|---------|--------|----------|
| device_bridge (LabLink-Core) | Production | Mature — ASTM/HL7 parsing, real devices |
| lab | Stub | Schema only, no routes |
| order | Stub | Schema only, no routes |
| patient | Stub | Schema only, no routes |
| result | Stub | Schema only, no routes |
| sample | Stub | Schema only, no routes |
| notification | Stub | Schema only, no routes |
| ai | Stub | Schema only, no routes |
| autonomous_manager | Stub | Dockerfile only |

### 2.3 Key Strengths
- Robust middleware stack with clear ordering
- Proven self-healing and degraded-mode operation
- Strong security invariants (JWT, RBAC, tenant isolation, audit chain)
- SNDHS Phase 1 integration underway
- Comprehensive CI pipeline (6 jobs + migrations check)
- Well-structured startup guard (`startup_guard.py`)

### 2.4 Key Weaknesses
- Monolith has high coupling between routes and models
- No OpenAPI schema governance — breaking changes possible without notice
- Test coverage is strong on integration paths, weak on business logic
- 7 stubs exist with no clear migration plan
- Financial Engine Phase A schema has no routes — technical debt
- No event catalog or schema registry

---

## 3. Evolution Vectors

### 3.1 Architecture Vector

```
Monolith (v2.1) → Modular Monolith (v2.5) → Domain Services (v3.0) → Service Mesh (v4.0)
```

| Phase | Architecture | Splits | Communication |
|-------|-------------|--------|---------------|
| Now | Monolith with internal packages | 0 | In-process function calls |
| Phase 1 (2027 Q1) | Modular monolith with domain boundaries | 0 | Well-defined Python packages with internal interfaces |
| Phase 2 (2027 Q3) | Extracted services behind gateway | 2-3 | HTTP + Redis Streams for critical paths |
| Phase 3 (2028) | Domain services with CQRS | 5-7 | Async events + REST for queries |
| Phase 4 (2029) | Service mesh with istio | 12+ | gRPC + Event Bus + Kafka |
| Phase 5 (2030+) | Multi-region mesh | 20+ | Service mesh + data mesh |

### 3.2 Technology Vector

```
Python 3.11 + FastAPI sync → Python 3.13+ async-native → Rust/WASM extensions
```

| Component | Current | 2027 | 2028 | 2029+ |
|-----------|---------|------|------|-------|
| Python | 3.11 | 3.13 | 3.14 | 3.15+ |
| FastAPI | sync endpoints | async-native endpoints | async-native + background workers | Fully async |
| DB Pool | SQLAlchemy 2.0 (3×6+12) | Same + PgBouncer | PgBouncer + read replicas | Write-heavy sharding |
| Redis | 7.2 (single) | 7.4 + sentinel | Redis Cluster | Redis + Kafka |
| Container | Docker Compose | Compose + K8s (dev) | K8s (prod) | Multi-region K8s |
| Observability | Prometheus + Grafana | + OpenTelemetry | + Loki + Tempo | Full observability mesh |
| API Gateway | nginx | nginx + Kong | Kong + Istio | Istio service mesh |

### 3.3 Healthcare Vector

```
Iraqi LIMS → National EHR → Health Information Exchange → Global Health Standards
```

| Capability | Current | 2027 | 2028 | 2029-2030 |
|-----------|---------|------|------|-----------|
| Lab types | Private labs | + Hospital labs | + Reference labs | + All clinical settings |
| Data standards | Proprietary | + HL7 v2.5 | + FHIR R4 | + openEHR, ISO 13606 |
| National integration | SNDHS Phase 1 | + Visit tracking | + National ID | + Full HIE |
| International | None | Arabic region | MENA | Global (WHO) |
| Telemedicine | None | Basic referral | Integrated | Full telehealth platform |

### 3.4 AI Vector

```
Clinical Decision Support → Autonomous Agents → Population Health AI
```

| Capability | Current | 2027 | 2028 | 2029+ |
|-----------|---------|------|------|-------|
| CDS | Basic rules in `ai/` | ML models for critical values | Deep learning on lab patterns | Multi-modal AI |
| Automation | None | Result validation AI | Auto-approve normal results | Autonomous lab operations |
| Population health | None | Basic analytics | Predictive outbreaks | Real-time population monitoring |
| Edge AI | None | Model inference on edge_agent | Federated learning | Edge AI mesh |
| LLM | None | Arabic clinical LLM | Multi-lingual | Domain-specific foundation model |

### 3.5 Security Vector

```
RBAC (v2.1) → ABAC (v3.0) → Zero Trust (v4.0) → Continuous Adaptive Trust (v5.0)
```

| Layer | Current | 2027 | 2028 | 2029+ |
|-------|---------|------|------|-------|
| Auth | JWT + refresh tokens | + OAuth 2.0 / OIDC | + FIDO2 WebAuthn | Passwordless |
| Authorization | RBAC (9 roles, 13 permissions) | + Attribute-based | + Policy-based (OPA) | Continuous trust scoring |
| Network | Docker network | + mTLS between services | + Istio mTLS | Zero Trust mesh |
| Data | AES-256 at rest | + TDE | + Homomorphic encryption for analytics | Fully encrypted computing |
| Audit | V2 audit chain | + Real-time alerting | + AI anomaly detection | Predictive threat detection |
| Standards | ISO 27001-aligned | + HIPAA | + NIST 800-53 | + Iraqi eHealth law |

### 3.6 Infrastructure Vector

```
Docker Compose → K8s → Multi-region → Edge Mesh
```

| Aspect | Current | 2027 | 2028 | 2029-2030 |
|--------|---------|------|------|-----------|
| Orchestration | Docker Compose | K8s (dev/staging) | K8s (production) | Multi-cluster K8s |
| Regions | 1 (Baghdad) | 2 (Baghdad + Erbil) | 3 (+ Basra) | 6+ regional |
| Edge | 1 edge_agent prototype | 50 labs | 500 labs | 5000+ labs |
| HA | Docker healthcheck | + HAProxy (make scale) | + PDB + HPA | Multi-region active-active |
| IaC | docker-compose.yml + Terraform | + Helm charts | + Crossplane | GitOps (ArgoCD) |
| CDN | Cloudflare basic | + Workers | + Durable Objects | Edge computing |

### 3.7 Government/Regulatory Vector

```
Single Country → Multi-country → International Standards
```

| Aspect | Current | 2027 | 2028-2029 | 2030+ |
|--------|---------|------|-----------|-------|
| Countries | Iraq | + Kurdistan Region | + MENA (3-5 countries) | Global |
| Health ID | Iraqi national ID | + SNDHS health ID | + Country-specific IDs | + WHO Global Patient ID |
| Regulations | Iraqi MoH | + Iraqi eHealth law | + GDPR, local DP laws | WHO standards |
| Language | Arabic + English | + Kurdish | + Farsi, Turkish | Multi-lingual (10+) |
| Currency | IQD | IQD + USD | Multi-currency | Global payments |

---

## 4. Modules to Split (with Timeline)

### S1 — Authentication Service
- **Priority**: Critical
- **Timeline**: Phase 1 (2027 Q1-Q2)
- **Reason**: Every service needs auth; monolith-bound auth blocks extraction
- **Strategy**: Extract `security/` package into standalone auth service with OAuth 2.0
- **Dependencies**: None (foundational)
- **Risk**: JWT secret rotation must be synchronized across all services
- **Size**: ~3,000 lines (security/auth.py, jwt_guard.py, rbac.py, totp.py, api_key.py)

### S2 — Device Bridge Integration API
- **Priority**: Critical
- **Timeline**: Phase 1 (2027 Q1-Q2)
- **Reason**: device_bridge (LabLink-Core) already exists as `services/device_bridge/` and is mature
- **Strategy**: Move result ingestion endpoints from monolith to device_bridge; monolith calls device_bridge via HTTP
- **Dependencies**: S1 (auth) for service-to-service auth
- **Risk**: ASTM/HL7 parsing errors must not block result submission

### S3 — Notification Service
- **Priority**: High
- **Timeline**: Phase 1 (2027 Q2-Q3)
- **Reason**: Email/SMS/push notification logic is mixed into business routes
- **Strategy**: Extract `notifications/` into standalone service with outbox pattern
- **Dependencies**: S1 (auth)
- **Risk**: Critical alert delivery must have <5s latency

### S4 — Sample Management Service
- **Priority**: High
- **Timeline**: Phase 2 (2027 Q3-Q4)
- **Reason**: Sample lifecycle (collection → processing → storage → disposal) is well-bounded
- **Strategy**: Extract `routes/samples.py`, `models/sample.py`, sample-related services
- **Dependencies**: S1, S2
- **Risk**: Sample barcode scanning must remain low-latency

### S5 — Results Service
- **Priority**: High
- **Timeline**: Phase 2 (2027 Q4 - 2028 Q1)
- **Reason**: Result validation, interpretation, and reporting is the most complex domain
- **Strategy**: Strangler fig — new results go through new service first; old results migrate gradually
- **Dependencies**: S1, S2, S4
- **Risk**: Optimistic lock (`version` column) must work across service boundaries

### S6 — Orders Service
- **Priority**: Medium
- **Timeline**: Phase 2 (2028 Q1-Q2)
- **Reason**: Lab order lifecycle has complex state machine in `domain/order_state.py`
- **Strategy**: Extract state machine + routes into orders service
- **Dependencies**: S1, S4, S5
- **Risk**: Order state transitions must be atomic

### S7 — Financial Service (Phase B)
- **Priority**: Medium
- **Timeline**: Phase 2 (2028 Q2-Q3)
- **Reason**: Financial Engine Phase A schema is ready; Phase B routes must not live in monolith
- **Strategy**: Build new FastAPI service in `services/financial/` with `ENABLE_FINANCIAL_ENGINE` flag
- **Dependencies**: S1, S3 (notifications for billing)
- **Risk**: Financial reconciliation errors have regulatory impact

### S8 — AI Service
- **Priority**: Medium
- **Timeline**: Phase 3 (2028 Q3-Q4)
- **Reason**: Clinical AI inference should scale independently from API
- **Strategy**: Extract `backend/app/ai/` and `backend/app/routes/ai.py` into dedicated serving infrastructure
- **Dependencies**: S1, S5
- **Risk**: Model versioning must be backward-compatible with stored results

### S9 — Patient Service / MPI
- **Priority**: Medium
- **Timeline**: Phase 3 (2029 Q1-Q2)
- **Reason**: Master Patient Index (`services/mpi/`) with SNDHS national ID integration
- **Strategy**: Extract patient routes, models, and MPI logic
- **Dependencies**: S1, S6
- **Risk**: Patient deduplication must survive service split

### S10 — Edge Synchronization Service
- **Priority**: Medium
- **Timeline**: Phase 3 (2029 Q2-Q3)
- **Reason**: Edge agent sync logic is intertwined with core API
- **Strategy**: Extract `routes/edge.py` and `edge/` into sync service
- **Dependencies**: S1, S5, S6
- **Risk**: Offline sync conflict resolution must be deterministic

### S11 — Audit Service
- **Priority**: Low
- **Timeline**: Phase 4 (2029 Q3-Q4)
- **Reason**: Audit log is append-only and highly decoupled; natural candidate for extraction
- **Strategy**: Extract audit chain into append-only service with its own DB
- **Dependencies**: S1
- **Risk**: Audit chain integrity must be preserved during migration

### S12 — Stats & Analytics Service
- **Priority**: Low
- **Timeline**: Phase 4 (2029 Q4 - 2030 Q1)
- **Reason**: Aggregation queries are heavy; isolating them protects transactional paths
- **Strategy**: Extract `routes/stats.py` into read-optimized service with materialized views
- **Dependencies**: S1, S5, S6, S4
- **Risk**: Real-time stats must remain real-time post-split

---

## 5. Modules to Merge (with Timeline)

### M1 — Merge NHOP into GULA Monolith (or Mesh)
- **Priority**: High
- **Timeline**: Phase 1 (2027 Q2-Q3)
- **Rationale**: `nhop-platform/` is a separate FastAPI on port 8100 that owns the national citizen registry. GULA needs patient data; NHOP needs lab data. A split causes sync problems.
- **Strategy**: Evaluate full merge vs. async event bridge. If national ID requirements diverge, keep separate but add event bus.
- **Risk**: Merging violates separation of concerns; keeping separate causes data staleness.

### M2 — Merge `backend/services/api/` and `backend/core/api/` stubs
- **Priority**: Low
- **Timeline**: Phase 1 (2027 Q1)
- **Rationale**: These directories contain experimental stubs that duplicate monolith routes. They are explicitly warned against in CLAUDE.md.
- **Strategy**: Delete stubs; document in ADR that monolith is the source of truth.
- **Risk**: None (no production code depends on them).

### M3 — Merge frontend-v2 and client apps
- **Priority**: Medium
- **Timeline**: Phase 2 (2028 Q1)
- **Rationale**: `frontend-v2` (Firebase-backed React) and `client/` (tRPC React SPA) overlap significantly. Two frontends confuse users.
- **Strategy**: Keep `frontend-v2` as the citizen/doctor/lab portal. Migrate `client/` features into it. Decommission `client/`.
- **Risk**: tRPC features may not map cleanly to Firebase.

### M4 — Merge edge_agent capabilities into device_bridge
- **Priority**: Medium
- **Timeline**: Phase 2 (2028 Q2)
- **Rationale**: `edge_agent/` handles offline/remote lab sites; `device_bridge` handles instrument integration. Both deal with lab hardware and offline scenarios.
- **Strategy**: Extend device_bridge with edge agent capabilities; deprecate standalone `edge_agent/`.
- **Risk**: Device bridge is mature; adding edge capabilities must not destabilize it.

### M5 — Merge AI stubs across monolith, services, and top-level
- **Priority**: Low
- **Timeline**: Phase 3 (2028 Q4)
- **Rationale**: AI code exists in `backend/app/ai/`, `services/ai/`, and top-level `ai/`. This fragmentation prevents model sharing.
- **Strategy**: Consolidate into `services/ai/` as the single AI service. Monolith calls it via gRPC/gRPC or event bus.
- **Dependencies**: S8 (AI Service extraction)

---

## 6. Modules to Retire (with Timeline)

### R1 — Static HTML PWA (`frontend/`)
- **Timeline**: Phase 1 (2027 Q2)
- **Reason**: Offline-capable PWA was MVP-only. `frontend-v2` and `client/` supersede it.
- **Strategy**: Archive `frontend/` directory. No code deletion until all users migrated.
- **Risk**: None (not actively used based on frontend-v2 being the rich target).

### R2 — `backend/services/` and `backend/core/` API stubs
- **Timeline**: Phase 1 (2027 Q1)
- **See**: M2 above. Delete with ADR documentation.

### R3 — Standalone `ai/` (top-level)
- **Timeline**: Phase 3 (2028 Q4)
- **Reason**: Superseded by `services/ai/` consolidation (M5).
- **Strategy**: Migrate any unique models to `services/ai/`; delete top-level `ai/`.

### R4 — `services/autonomous_manager/`
- **Timeline**: Phase 3 (2029 Q1)
- **Reason**: Autonomous operations concept was pre-mature. Functionality should live in the self-healing system (`core/self_healing.py`, `core/auto_repair.py`).
- **Strategy**: Fold autonomous manager concepts into monolith self-healing; delete stub.

### R5 — Legacy Frontend Firebase Config (Phase A remaining)
- **Timeline**: Phase 4 (2029 Q3)
- **Reason**: Firebase Auth was used in early `frontend-v2`. As we move to OAuth 2.0/OIDC (Phase 2+), Firebase Auth should be deprecated.
- **Strategy**: Keep Firestore for data if needed; migrate auth to OIDC provider.

### R6 — `render.yaml`
- **Timeline**: Phase 2 (2028 Q1)
- **Reason**: Render PaaS was an early alternative. K8s is now the target.
- **Strategy**: Remove render.yaml from root. Keep in git history for reference.

### R7 — Old `scripts/repair-droplet.sh`
- **Timeline**: Phase 1 (2027 Q2)
- **Reason**: Destructive script flagged as "never run autonomously" in CLAUDE.md. As we move to K8s, droplet repair is irrelevant.
- **Strategy**: Replace with `scripts/diagnose-cluster.sh` for K8s diagnostics.

---

## 7. New Platform Capabilities (with Priority)

### C1 — OpenAPI Schema Governance (Priority: Critical)
- **Description**: All API changes must go through schema review; breaking changes must be versioned.
- **Implementation**: Add OpenAPI diff to CI (openapi-diff or spectral). Schemas become the contract.
- **Timeline**: 2027 Q1

### C2 — Event Catalog / Schema Registry (Priority: Critical)
- **Description**: All domain events published to the event bus must be registered, versioned, and documented.
- **Implementation**: AsyncAPI spec + Schema Registry (Redpanda or Apicurio).
- **Timeline**: 2027 Q2

### C3 — Service Health Dashboard (Priority: High)
- **Description**: Real-time view of all service health, latency, error rates, and SLO compliance.
- **Implementation**: Grafana dashboard with synthetic monitoring. Extend current `make health-deep`.
- **Timeline**: 2027 Q2

### C4 — FHIR R4 Compliance Layer (Priority: High)
- **Description**: All patient, lab, and result data accessible via FHIR R4 APIs.
- **Implementation**: Translation layer in `services/fhir/` that maps GULA models to FHIR resources.
- **Dependencies**: S5 (Results), S9 (Patient)
- **Timeline**: 2028 Q1

### C5 — National Health ID Resolution (Priority: High)
- **Description**: Resolve patients across labs via national ID. Full SNDHS integration.
- **Implementation**: Extend MPI with national ID matching. Use `NID_HMAC_KEY` for encrypted lookup.
- **Dependencies**: S9 (Patient/MPI)
- **Timeline**: 2027 Q3

### C6 — Multi-Language Support (Kurdish, Farsi, Turkish) (Priority: High)
- **Description**: UI and reports in Kurdish (Sorani/Kurmanji), Farsi, and Turkish.
- **Implementation**: i18n infrastructure in `frontend-v2`. Arabic-first remains default.
- **Timeline**: 2028 Q2

### C7 — SMS/WhatsApp Notification Integration (Priority: High)
- **Description**: Patient and doctor notifications via SMS and WhatsApp.
- **Implementation**: Extend notification service with Twilio/360dialog integration.
- **Dependencies**: S3 (Notification Service)
- **Timeline**: 2027 Q3

### C8 — Payment Gateway Integration (Priority: Medium)
- **Description**: In-app payments for lab tests, subscriptions, and national health plan billing.
- **Implementation**: Integrate with Iraqi payment gateways (AsiaCell, ZainCash) and international (Stripe).
- **Dependencies**: S7 (Financial Service)
- **Timeline**: 2028 Q3

### C9 — Telemedicine / Referral Platform (Priority: Medium)
- **Description**: Doctors can refer patients between labs; patients can get second opinions.
- **Implementation**: New bounded context in services mesh. FHIR-based referral resources.
- **Timeline**: 2029 Q1

### C10 — Population Health Dashboard (Priority: Medium)
- **Description**: Anonymized, aggregate view of lab results across regions for epidemiological monitoring.
- **Implementation**: Read-optimized analytics service with dbt + materialized views.
- **Dependencies**: S12 (Stats & Analytics)
- **Timeline**: 2029 Q2

### C11 — Genomic Data Support (Priority: Low)
- **Description**: Store, retrieve, and analyze genomic test results alongside traditional lab results.
- **Implementation**: New FHIR resource support (GenomicReport, MolecularSequence). Large-file storage (S3/MinIO).
- **Timeline**: 2030 Q1

### C12 — Clinical Trial Support (Priority: Low)
- **Description**: Manage patient enrollment, sample tracking, and data collection for clinical trials.
- **Implementation**: New bounded context with CDISC/ODM compliance.
- **Timeline**: 2030 Q2

### C13 — Wearable/IoT Device Integration (Priority: Low)
- **Description**: Integrate continuous glucose monitors, blood pressure cuffs, and other patient-worn devices.
- **Implementation**: Extend device_bridge for Bluetooth/BLE/API-based consumer devices.
- **Timeline**: 2030 Q3

### C14 — Healthcare Provider Marketplace (Priority: Low)
- **Description**: Patients can find, compare, and book lab tests across providers.
- **Implementation**: New marketplace bounded context. Lab rating, pricing transparency.
- **Timeline**: 2031+

### C15 — Autonomous Lab Operations (Priority: Low)
- **Description**: AI-driven lab operations: auto-ordering of reagents, predictive maintenance, staff scheduling.
- **Implementation**: Extend AI mesh with operations models.
- **Timeline**: 2031+

### C16 — Blockchain-Based Credentialing (Priority: Low)
- **Description**: Immutable, verifiable records of lab certifications, staff credentials, and quality control.
- **Implementation**: Selected integration via SSI/verifiable credentials (not full blockchain).
- **Timeline**: 2031+

---

## 8. Evolution Timeline

### Phase 1: Foundation (2027)
**Theme**: Modular monolith + extraction of foundational services

| Quarter | Milestones | Decisions |
|---------|-----------|-----------|
| Q1 | Auth Service extraction (S1); OpenAPI governance (C1); Merge backend stubs (M2); Delete frontend/ (R1) | D1: Auth approach (OAuth provider vs. build) |
| Q2 | Device Bridge integration (S2); Notification Service (S3); Event Catalog (C2); Merge NHOP decision (M1) | D2: NHOP merge vs. event bridge; Event bus technology |
| Q3 | Sample Management (S4); National ID resolution (C5); SMS/WhatsApp (C7) | D3: Service mesh technology (Istio vs Linkerd vs none) |
| Q4 | Results Service extraction begins (S5); Service health dashboard (C3) | D4: CQRS for results (yes/no) |

### Phase 2: Extraction (2028)
**Theme**: Critical domain services split; FHIR compliance; K8s migration

| Quarter | Milestones | Decisions |
|---------|-----------|-----------|
| Q1 | Results Service complete (S5); FHIR R4 layer (C4); K8s dev/staging; Merge frontends (M3) | D5: FHIR server (HAPI vs. custom); K8s distribution |
| Q2 | Orders Service (S6); edge_agent merge into device_bridge (M4); Multi-language (C6) | D6: FHIR storage strategy |
| Q3 | Financial Service Phase B (S7); Payment gateway (C8); K8s production pilot | D7: Payment processor(s) |
| Q4 | Merge AI stubs (M5); 50 labs running on K8s | D8: AI inference infrastructure |

### Phase 3: Expansion (2029)
**Theme**: AI mesh, multi-country, zero trust

| Quarter | Milestones | Decisions |
|---------|-----------|-----------|
| Q1 | AI Service (S8); Telemedicine (C9); Retire autonomous_manager (R4) | D9: AI model serving framework |
| Q2 | Patient/MPI Service (S9); Edge Sync (S10); MENA region 1 | D10: Country-specific ID strategy |
| Q3 | Audit Service (S11); Zero Trust pilot; Retire Firebase Auth (R5) | D11: Zero Trust vendor/technology |
| Q4 | Population Health Dashboard (C10); 500 labs; 2 regions | D12: Data mesh vs. monolithic warehouse |

### Phase 4: Health Information Exchange (2030)
**Theme**: National HIE, full interoperability, international

| Quarter | Milestones | Decisions |
|---------|-----------|-----------|
| Q1 | Stats Service (S12); Genomic support (C11); 3 regions | D13: Genomic storage strategy |
| Q2 | Clinical Trial support (C12); IoT devices (C13); WHO standards alignment | D14: International standard prioritization |
| Q3 | Full HIE with SNDHS; Multi-country (3+); Legacy cleanup | D15: HIE topology (centralized vs. federated) |
| Q4 | International health ID pilot; 1000+ labs | D16: Global patient identity |

### Phase 5+: Autonomous Platform (2031+)
**Theme**: AI-native, global, autonomous

- Healthcare Provider Marketplace (C14)
- Autonomous Lab Operations (C15)
- Blockchain credentialing (C16)
- 5000+ labs across 10+ countries
- Multi-region active-active
- Edge AI mesh with federated learning
- Full Zero Trust with continuous adaptive trust scoring

---

## 9. Risk Register for Evolution

| # | Risk | Likelihood | Impact | Mitigation |
|---|------|-----------|--------|------------|
| R01 | Service extraction breaks tenant isolation | Medium | Critical | Automated tenant isolation tests run in CI for every extraction PR |
| R02 | Event bus becomes single point of failure | Medium | Critical | Redis sentinel/cluster; fallback to direct DB reads in degraded mode |
| R03 | Performance regression from HTTP overhead | High | High | Measure p50/p95/p99 before/after each extraction; keep hot paths in monolith |
| R04 | Developer productivity drop during transition | High | High | Maintain feature flag parity; allow monolith development during extraction |
| R05 | Data consistency issues across services | Medium | Critical | Saga pattern with compensating transactions; outbox pattern for all writes |
| R06 | FHIR compliance timeline slips | Medium | Medium | Build FHIR layer incrementally; support partial FHIR in Phase 2 |
| R07 | K8s operational complexity overwhelms team | High | Medium | Stay on Docker Compose until team is ready; use managed K8s (EKS/AKS) |
| R08 | National ID integration breaks privacy | Low | Critical | Encryption at rest (`ENCRYPTION_KEY`); `NID_HMAC_KEY` for lookups; audit all access |
| R09 | AI model quality issues cause misdiagnosis | Medium | Critical | Always have human-in-the-loop; confidence thresholds; shadow mode for new models |
| R10 | Payment integration regulatory failure | Low | High | Engage Iraqi Central Bank early; use licensed payment partners |
| R11 | Multi-region data residency conflicts | Medium | High | Per-region data isolation; GDPR compliance by design; Iraqi eHealth law alignment |
| R12 | Service mesh adds 5-15ms latency per hop | Medium | Medium | Benchmark before enabling; keep critical paths (result submission) on direct calls |
| R13 | Test environment doesn't match production | High | Medium | K8s dev/staging mirror production; chaos engineering in staging |
| R14 | Key personnel departure during transition | Medium | High | Document all extraction procedures in ADRs; cross-train all team members |
| R15 | Vendor lock-in (K8s distribution, event bus, FHIR server) | Medium | Medium | Evaluate 2+ vendors before each D# decision; prefer open standards |
| R16 | Feature flag technical debt accumulates | High | Low | Quarterly feature flag cleanup; auto-expire flags after 6 months |
| R17 | Legacy data migration fails | Low | Critical | Full backup before every migration; rollback script required; test on staging DB copy |

---

## 10. Decision Gates

### Gate G1 — Auth Service Extraction
**Proceed if**: Auth service passes parity tests (all monolith auth flows work through new service with <5% latency increase)
**Pivot if**: OAuth 2.0 integration reveals Iraqi national auth requirements not met → Build custom OIDC provider
**Stop if**: Security audit finds vulnerabilities in new service → Fix before proceeding

### Gate G2 — K8s Migration
**Proceed if**: Dev team can deploy, debug, and roll back on K8s without external help
**Pivot if**: Team cannot handle K8s complexity → Use managed K8s (EKS AKS) or stay on Compose + HAProxy
**Stop if**: Cost > 2× Docker Compose with no reliability improvement → Re-evaluate ROI

### Gate G3 — FHIR R4 Rollout
**Proceed if**: 10+ labs successfully use FHIR endpoints for at least one workflow (order or result)
**Pivot if**: Labs find FHIR too complex → Maintain proprietary endpoints alongside FHIR; make FHIR optional
**Stop if**: Performance of FHIR translation layer > 200ms p95 → Optimize or use native FHIR storage

### Gate G4 — First Service Mesh Enablement
**Proceed if**: Istio/Linkeder pilot on 2 services shows <5ms p50 latency increase and no stability issues
**Pivot if**: Latency impact > 10ms → Skip mesh; use direct gRPC with mTLS only
**Stop if**: Team cannot debug mesh issues → Train team first

### Gate G5 — Multi-Region Deployment
**Proceed if**: Cross-region replication latency <100ms p95 and conflict resolution handles all edge cases
**Pivot if**: Iraqi internet infrastructure causes >200ms latency → Use active-passive instead of active-active
**Stop if**: Data sovereignty requirements not met → Defer; engage legal

### Gate G6 — Zero Trust Architecture
**Proceed if**: All services support mTLS and policy-based access (OPA/CASB) without breaking existing flows
**Pivot if**: Legacy devices (ASTM/HL7) cannot support mTLS → Use device bridge as TLS termination point
**Stop if**: Performance impact > 15% on any SLO → Deploy gradually by service priority

### Gate G7 — Multi-Country Expansion
**Proceed if**: Legal review confirms compliance in target country; at least 5 labs committed
**Pivot if**: Regulatory burden > 6 months per country → Use partner licensing model instead of direct operation
**Stop if**: Any country imposes sanctions or data exit restrictions → Re-evaluate country selection

### Gate G8 — AI Autonomous Operations
**Proceed if**: AI model achieves 99.5%+ accuracy on lab result validation with <0.1% false negative rate for critical values
**Pivot if**: False negative rate > 0.5% → Keep human-in-the-loop mandatory
**Stop if**: Regulatory body prohibits autonomous lab operations → Limit AI to decision support only

---

## Appendix A: Key Metrics for Evolution Tracking

| Metric | Current | Phase 1 Target | Phase 2 Target | Phase 3 Target |
|--------|---------|---------------|---------------|---------------|
| Monolith LOC | ~45,000 | 42,000 (-3K) | 35,000 (-10K) | 20,000 (-25K) |
| Services | 1 mature + 7 stubs | 4 mature | 7 mature | 12 mature |
| API response p50 | <100ms | <100ms | <120ms | <150ms |
| API response p99 | <500ms | <500ms | <600ms | <800ms |
| Test coverage | 28 modules | 35 modules | 45 modules | 60 modules |
| Labs served | ~100 | 200 | 500 | 5000 |
| Countries | 1 | 1 | 1-3 | 3-10 |
| Uptime (monthly) | 99.5% | 99.9% | 99.95% | 99.99% |
| Deploy frequency | Weekly | Semi-weekly | Daily | On-demand |
| MTTR | ~2h | <1h | <30min | <15min |

## Appendix B: Evolution Decision Log

| ADR# | Title | Date | Phase | Status |
|------|-------|------|-------|--------|
| ADR-XXX | Auth Service Extraction Strategy | 2027 Q1 | Phase 1 | Pending |
| ADR-XXX | Event Bus Technology Selection | 2027 Q2 | Phase 1 | Pending |
| ADR-XXX | K8s Distribution Decision | 2028 Q1 | Phase 2 | Pending |
| ADR-XXX | FHIR Server Implementation | 2028 Q1 | Phase 2 | Pending |
| ADR-XXX | Data Mesh Architecture Decision | 2029 Q4 | Phase 3 | Pending |

---

*This document is living. Update after each Phase gate review.*
