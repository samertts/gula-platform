# GULA Platform Ecosystem — Module Architecture

**Version:** 2.1.0  
**Status:** DRAFT  
**Last Updated:** 2026-07-17

---

## 1. Core Platform

### 1.1 gula-backend (Monolith)

**Location:** `backend/app/`  
**Entry Point:** `backend/app/main.py` (1948 lines)  
**Runtime:** FastAPI + Gunicorn + uvicorn workers  
**Port:** 8000 (internal, behind api-gateway)  
**Health:** `/health`, `/health/ready`, `/health/deep`, `/health/status`

The monolith contains all Core Platform capabilities. It runs behind:
- **api-gateway** (Docker nginx on 127.0.0.1:8080) — TLS termination, routing, rate limiting
- **HAProxy** (optional, for scale mode) — load balancing across N backend replicas

**Middleware Stack** (in order, defined in `main.py`):
1. `MaxBodySizeMiddleware` — 413 above MAX_REQUEST_BODY_MB (default 10)
2. `RequestIDMiddleware` — X-Request-ID assignment + log context
3. `DocsAuthMiddleware` — guards /docs, /redoc, /openapi.json in production
4. `CORSMiddleware`
5. `RequestTimingMiddleware` — access log + X-Response-Time
6. `SecurityHeadersMiddleware` — CSP, HSTS, X-Frame-Options
7. `GZipMiddleware`
8. `ReadinessMiddleware` — 503 until system_ready
9. `DegradedModeMiddleware` — rejects writes when DB circuit is open
10. `ConcurrencyLimitMiddleware` — in-flight cap (exempts clinical writes)

### 1.2 gula-worker

**Location:** `backend/app/worker.py`  
**Purpose:** Background task processing (outbox pattern, scheduled jobs, AI inference)  
**Runtime Mode:** `RUNTIME_MODE=worker`  
**Feature Gate:** `FEATURE_BACKGROUND_TASKS=true`

### 1.3 API Gateway

**Location:** `config/nginx/gateway.conf` (Docker nginx)  
**Responsibilities:**
- TLS termination (Let's Encrypt via host nginx)
- Path-based routing to backend / microservices
- Rate limiting (per-IP, per-lab)
- Request logging
- Static file serving (frontend builds)

### 1.4 Identity & Access

| Component | Location | Description |
|-----------|----------|-------------|
| Authentication | `backend/app/security/auth.py` | JWT encode/decode, `get_current_user`, OAuth2 password flow |
| Authorization | `backend/app/security/rbac.py` | 9 roles: super_admin, admin, lab_owner, lab_manager, technician, doctor, nurse, receptionist, viewer |
| Session Management | `backend/app/security/sessions.py` | Redis-backed, permission version bump for JWT invalidation |
| MFA | `backend/app/routes/mfa.py` | TOTP-based multi-factor authentication |
| OAuth2 | `backend/app/routes/oauth2.py` | OAuth2 client/server for third-party integrations |
| SAML | `backend/app/routes/saml.py` | SAML SSO for enterprise/government |
| Service Accounts | `backend/app/routes/service_accounts.py` | API keys for machine-to-machine auth |

### 1.5 Audit System

**Location:** `backend/app/models/audit_log.py`  
**Mechanism:** SHA-256 hash chain, HMAC-anchored file system checkpoints  
**Chain Verification:** `backend/app/audit/` (chain traversal and integrity check)  
**V2 Extension** (SNDHS): `backend/migrations/versions/20260505_0005_sndhs_phase1_audit_logs_v2.py`

### 1.6 Event Bus

**Location:** `backend/app/kernel/event_bus/`  
**Components:**

| Component | File | Purpose |
|-----------|------|---------|
| EventBus | `bus.py` | Central pub/sub hub |
| Dispatcher | `dispatcher.py` | Event routing to subscribers |
| Store | `store.py` | Event persistence |
| Outbox | `outbox.py` | Transactional outbox for guaranteed delivery |
| Inbox | `inbox.py` | Idempotent message consumption |
| Dead Letter Queue | `dead_letter_queue.py` | Failed event storage |
| Retry Queue | `retry_queue.py` | Retry logic with backoff |
| Replay | `replay.py` | Event re-processing |
| Snapshot | `snapshot.py` | State snapshots for recovery |
| Recovery | `recovery.py` | Crash recovery |
| Versioning | `versioning.py` | Event schema evolution |

---

## 2. Clinical Domain Modules

### 2.1 LIMS Pack

**Built-in** — This is the original GULA product.

| Component | Location | Description |
|-----------|----------|-------------|
| Patient Management | `backend/app/routes/patients.py` | CRUD, search, family, duplicate detection |
| Order Management | `backend/app/routes/orders.py` (reference) | State machine with optimistic locking |
| Sample Tracking | `backend/app/routes/samples.py` | Barcode, collection, status workflow |
| Result Management | `backend/app/routes/results.py` | Per-test results, normal ranges, flags |
| Quality Control | `backend/app/routes/quality_control.py` | Westgard rules, Levey-Jennings |
| Test Types | `backend/app/routes/test_results.py` | Test catalog management |
| Critical Alerts | `backend/app/routes/critical_alerts.py` | Alert statistics, notification dispatch |
| Device Integration | `services/device_bridge/` | ASTM/HL7 via LabLink-Core |
| QR Patient Cards | `backend/app/routes/patient_card.py` | HMAC-signed tokens, Arabic HTML |
| Master Patient Index | `backend/app/services/mpi/` | Probabilistic matching, blocking keys |

**Models:**
- `backend/app/models/patient.py` — `Patient` (with national_id, phone, name, lab_id)
- `backend/app/models/lab_order.py` — `LabOrder` (state machine, version for optimistic locking)
- `backend/app/models/sample.py` — `Sample` (barcode, type, status, storage)
- `backend/app/models/lab_result.py` — `LabResult` (per-test, normal ranges, flags)
- `backend/app/models/test_result.py` — `TestResult` (individual test in panel)
- `backend/app/models/test_type.py` — `TestType` (test catalog)
- `backend/app/models/quality_control.py` — `QualityControl` (Westgard, Levey-Jennings)

**State Machine:** `backend/app/domain/order_state.py` — LabOrder states:
```
pending → collected → in_progress → reviewed → completed → reported
                                                         ↓ (rejection)
                                                     rejected
```

### 2.2 EHR Pack

**Built-in** at `backend/app/ehr/`

| Component | Description |
|-----------|-------------|
| EHR Routes | `backend/app/routes/ehr.py` — patient health records |
| FHIR Endpoints | `backend/app/routes/ehr_fhir.py` — FHIR R4 patient resources |
| Clinical Summaries | Trend data, latest value per test type |
| Citizen Access | `backend/app/routes/citizen_portal.py` — patient-accessible records |
| Care Continuum | `backend/app/routes/care_continuum.py` — longitudinal care history |
| Clinical Docs | `backend/app/routes/clinical_documentation.py` — clinical notes |

### 2.3 Radiology Pack

**Planned** — Not yet implemented.

**Expected Components:**
- Imaging study ordering
- DICOM image storage and retrieval
- PACS integration via `AdapterBase`
- AI-powered reading assistant
- Structured reporting templates
- Modality worklist management

**Extends:** Patient Management + Storage Service + Workflow Engine

### 2.4 Pharmacy Pack

**Stub** at `backend/app/pharmacy/`

**Expected Components:**
- Prescription management
- Dispensing workflow
- Inventory management
- Drug-drug interaction checking (via AI Fabric)
- Narcotics control
- Billing integration

### 2.5 Nursing Pack

**Stub** at `backend/app/nursing/`

**Expected Components:**
- Medication administration records
- Care plan management
- Shift handover
- Vital signs recording
- Nursing notes
- Task scheduling

### 2.6 Blood Bank Pack

**Stub** at `backend/app/blood_bank/`

**Expected Components:**
- Donor management
- Blood collection and processing
- Cross-match workflow
- Inventory management
- Transfusion tracking
- Adverse reaction reporting

### 2.7 Critical Care Pack

**Existing** at `backend/app/critical_care/`

**Components:**
- ICU patient monitoring integration
- Real-time alerting
- Clinical decision support
- Ventilator/dialysis machine integration
- APACHE/SOFA scoring

### 2.8 Public Health Pack

**Via AI Fabric** at `backend/app/ai_fabric/public_health.py`

| Component | Description |
|-----------|-------------|
| Disease Surveillance | `DiseaseSurveillance` — case tracking and reporting |
| Outbreak Detection | `OutbreakDetector` — statistical anomaly detection |
| Population Health | `PopulationHealthAnalytics` — cohort analytics |

### 2.9 EMS Pack

**Planned**

**Expected Components:**
- Dispatch management
- Pre-hospital care records
- Ambulance tracking
- Hospital handover
- Telemedicine integration

---

## 3. Government & National Modules

### 3.1 SNDHS Pack

**Location:** `backend/app/national/`, `backend/app/national_data/`  
**Feature Gate:** `SNDHS_ENABLE_VISITS`, `SNDHS_ENABLE_NATIONAL_ID` (default: false)  
**Migration Files:** 6 Alembic revisions in `backend/migrations/versions/`
**Backfill Script:** `scripts/sndhs_phase1_backfill.py`
**Rollback:** `scripts/sndhs_phase1_rollback.sql` + `scripts/sndhs_phase1_disable_flags.sh`
**Docs:** `docs/sndhs/` (22 files)

**Components:**
- Visit tracking (`visits` table + `lab_orders.visit_id`)
- National ID / Health ID on patients (encrypted at rest)
- Enhanced audit log (v2 with SNDHS correlation fields)
- National identity lookup: `backend/app/routes/national_identity.py`
- National data routes: `backend/app/routes/national_data.py`
- FHIR-compatible patient resources for government reporting

### 3.2 National Oversight Pack (NHOP)

**Location:** `nhop-platform/` (separate FastAPI app, port 8100)  
**Purpose:** National Health Oversight — aggregates data across all GULA instances  
**Data:** Ministry-level dashboards, population health statistics, compliance monitoring  
**Relationship:** GULA owns per-lab LIMS; NHOP owns national citizen registry view

### 3.3 Compliance Pack

**Location:** `backend/app/routes/compliance.py`  
**Components:**
- Regulatory reporting
- FHIR-compatible patient resources
- Audit log export for government inspection
- Consent management verification

### 3.4 Audit Pack

**Location:** `backend/app/audit/`  
**Components:**
- Hash chain traversal and verification
- Checkpoint management
- Immutable log export
- Chain integrity monitoring

---

## 4. AI & Intelligence Modules

### 4.1 AI Fabric (Core AI Runtime)

**Location:** `backend/app/ai_fabric/`

| Layer | Component | File |
|-------|-----------|------|
| **Gateway** | AIGateway — multi-provider router | `gateway.py` |
| **Local AI** | LocalAIEngine — on-premise inference | `local_ai.py` |
| **Models** | ModelRegistry — provider registration | `local_ai.py` |
| **RAG** | RAGEngine, VectorStore, SemanticSearch | `rag.py` |
| **KG** | KnowledgeGraphService | `knowledge_graph.py` |
| **Security** | AIFirewall — prompt injection defense | `security.py` |
| **Governance** | AIGovernance — audit, bias detection | `governance.py` |
| **Observability** | AIObserver — metrics, tracing | `observability.py` |

### 4.2 Clinical AI Pack

**Location:** `backend/app/ai_fabric/clinical.py`

| Component | Description |
|-----------|-------------|
| ClinicalDecisionSupport | Multi-test pattern detection (sepsis, DKA, renal failure) |
| ClinicalSummarizer | Patient history summarization |
| DrugInteractionDetector | Drug-drug interaction checking |

### 4.3 Lab Intelligence Pack (SAMIR Engine)

**Location:** `backend/app/ai_fabric/laboratory_intelligence.py`

| Component | Description |
|-----------|-------------|
| CriticalResultDetector | Real-time critical value detection |
| DeltaChecker | Significant change detection |
| QCAnalyzer | Westgard rule engine |
| WorkloadPredictor | Lab workload forecasting |

### 4.4 Ali Reza Pack (Arabic Clinical AI)

**Location:** `backend/app/ai/`  
**Purpose:** Arabic-language clinical AI — NER, classification, ICD-10 coding in Arabic

### 4.5 Population Health Pack

**Location:** `backend/app/ai_fabric/public_health.py`

| Component | Description |
|-----------|-------------|
| DiseaseSurveillance | Regional disease monitoring |
| OutbreakDetector | Statistical outbreak detection |
| PopulationHealthAnalytics | Cohort analysis, risk stratification |

### 4.6 Predictive Analytics Pack

**Via AI Fabric + Analytics Routes:**
- Workload prediction
- Result trend analysis
- Patient flow forecasting
- Inventory demand prediction

**Routes:** `backend/app/routes/ai.py`, `backend/app/routes/ai_telemetry.py`

---

## 5. Integration Modules

### 5.1 Device Bridge Pack (LabLink-Core)

**Location:** `services/device_bridge/`  
**Status:** **Mature** — actively used in production  
**Protocols:** ASTM (E1381, E1394), HL7 v2.x  
**Supported Devices:** Sysmex, Roche, Mindray, Beckman Coulter, Abbott, and generic ASTM  
**Architecture:**

```
Physical Device → Serial/TCP → Device Bridge → gula_client → gula-backend API
```

**Gula Client:** `services/device_bridge/app/integration/gula_client.py`
**Bridge Routes:** `backend/app/routes/device_results.py`

**Deployment:** `docker compose --profile device-bridge up device-bridge`

### 5.2 FHIR Gateway Pack

**Location:** `backend/app/routes/ehr_fhir.py`, `backend/app/interoperability/`  
**Standards:**
- FHIR R4 resources (Patient, Observation, DiagnosticReport, etc.)
- HL7 v2.x message parsing and generation
- LOINC coding of lab tests
- ICD-10/11 (diagnosis), SNOMED CT (optional)

### 5.3 National ID Gateway Pack

**Location:** `backend/app/routes/national_identity.py`, `backend/app/routes/id_scan.py`  
**Components:**
- Iraqi National ID card OCR scanning (OpenCV + Tesseract)
- National ID lookup and verification
- Encrypted national ID storage with hashed lookup for deduplication

### 5.4 Insurance Gateway Pack

**Location:** `backend/app/routes/insurance.py`, `backend/app/routes/claims.py`  
**Components:**
- Insurance claim submission (draft → validated → submitted → accepted/rejected → paid)
- Prior authorization workflows
- Eligibility verification

**Models:** `backend/app/models/claim.py`

### 5.5 EHR Integration Pack

**Location:** `backend/app/ehr/`, `backend/app/routes/ehr.py`  
**Extends:** Patient management with longitudinal health records  
**FHIR Routes:** `backend/app/routes/ehr_fhir.py`  
**Citizen Portal:** `backend/app/routes/citizen_portal.py`

---

## 6. Infrastructure Modules

### 6.1 Monitoring Pack

**Location:** `config/prometheus/`, `config/grafana/`  
**Deployment:** `docker compose -f docker-compose.yml -f docker-compose.full.yml up prometheus grafana`  
**Components:**
- Prometheus scrape config + alerting rules
- Grafana provisioned dashboards (backend, Redis, PostgreSQL)
- Metrics endpoint: `/metrics/prom` (Bearer token protected)

### 6.2 Logging Pack

**Location:** `config/loki/` (planned)  
**Current:** Structured JSON logging via `backend/app/core/logging_config.py`  
**Log Aggregation:** Planned — Loki + Promtail

### 6.3 Tracing Pack

**Location:** `config/jaeger/` (planned)  
**Current:** In-process tracing via `ObservabilityAPI.emit_trace()`  
**Distributed Tracing:** Planned — OpenTelemetry + Jaeger

### 6.4 Backup/DR Pack

**Location:** `scripts/backup.sh`  
**Backup:** `make backup` → pg_dump → `./backups/gula_<ts>.sql.gz`  
**DR Strategy:** PostgreSQL streaming replication, S3 backups

### 6.5 Security Pack

**Location:** `backend/app/firewall/`, `backend/app/security/`  
**Components:**
- Rate limiting (Redis + in-memory fallback)
- Intrusion detection (time-windowed IP attack detection)
- WAF (host nginx)
- Secrets management (env vars, no hardcoded fallbacks)

---

## 7. Developer & Extension Modules

### 7.1 SDK Pack

**Runtime SDK:** `backend/app/kernel/runtime_sdk.py` (277 lines)

```
RuntimeSDK
├── plugins — PluginRuntimeAPI (hooks, state, events)
├── modules — ModuleRuntimeAPI (registration, lifecycle)
├── workflows — WorkflowRuntimeAPI (steps, sagas)
└── observability — ObservabilityAPI (metrics, traces, logs)
```

**AI SDK:** `backend/app/ai_fabric/sdk.py` (217 lines)

```
UnifiedAISDK
├── gateway — AIGateway (multi-provider inference)
├── rag — RAGEngine (retrieval augmented generation)
├── knowledge_graph — KnowledgeGraphService
├── clinical — ClinicalDecisionSupport
├── surveillance — DiseaseSurveillance
├── outbreak — OutbreakDetector
└── agents — AgentRegistry (custom AI agents)
```

### 7.2 Plugin SDK

**Location:** `backend/app/kernel/plugin/`
**Key Files:**
- `loader.py` — dynamic Python module loading
- `sandbox.py` — runtime security restrictions
- `manager.py` — lifecycle management
- `registry.py` — plugin registry
- `marketplace.py` — marketplace interface
- `version_manager.py` — version validation
- `permissions.py` — permission checking
- `dependencies.py` — dependency resolution
- `hot_reload.py` — hot-reload support

### 7.3 Connector SDK

**Location:** `backend/app/interoperability/adapter_base.py`  
**Contract:** Any external system integration MUST extend `AdapterBase`

```python
class MyLabSystemAdapter(AdapterBase):
    name = "my_lab_system"
    domain = TrustDomain(name="my_lab", capabilities={"read_patient", "write_result"})

    async def health(self) -> AdapterHealth:
        ...

    async def call_outbound(self, operation, payload, context) -> AdapterResult:
        ...
```

### 7.4 API Marketplace

**Location:** `backend/app/kernel/plugin/marketplace.py`  
**Interface:** `PluginMarketplaceInterface` — search, list, get available plugins  
**Integration:** Connects to `gula-marketplace` microservice for production

### 7.5 Dev Tools Pack

**Make Targets:**
- `make ci` — syntax-gate + lint + docker build
- `make lint` — pyflakes + flake8 (E9, F821)
- `make test` — pytest tests/
- `make health-deep` — full diagnostic
- `make shell` — bash into backend container

**Validation Tools:**
- `backend/app/kernel/validation/architecture.py` — architectural rule checking
- `backend/app/kernel/validation/dependencies.py` — dependency validation
- `backend/app/kernel/validation/security.py` — security validation
- `backend/app/kernel/validation/performance.py` — performance validation
- `backend/app/kernel/validation/stress.py` — stress testing

---

## 8. Module Dependency Graph

```
                                    ┌─────────────────────┐
                                    │     Event Bus       │
                                    │  (kernel/event_bus) │
                                    └─────────┬───────────┘
                                              │
                    ┌─────────────────────────┼─────────────────────┐
                    │                         │                     │
            ┌───────▼───────┐       ┌─────────▼─────────┐  ┌───────▼───────┐
            │  Auth + RBAC  │       │  Audit Logging    │  │   Feature     │
            │(security/auth)│       │  (models/audit)    │  │   Flags       │
            └───────┬───────┘       └─────────┬─────────┘  │(kernel/flags) │
                    │                         │             └───────┬───────┘
                    └──────────┬──────────────┘                     │
                               │                                    │
                    ┌──────────▼──────────┐                         │
                    │  Patient Management  │◄────────────────────────┘
                    │  (models + routes)   │
                    └──────────┬──────────┘
                               │
              ┌────────────────┼────────────────┐
              │                │                │
     ┌────────▼───────┐ ┌─────▼──────┐ ┌───────▼────────┐
     │ Order Mgmt     │ │ Sample     │ │ Master Patient │
     │ (state machine)│ │ Tracking   │ │ Index (MPI)    │
     └────────┬───────┘ └─────┬──────┘ └────────────────┘
              │               │
              ▼               ▼
     ┌──────────────────────────────────┐
     │        Result Management         │
     │  (per-test, normal ranges, PDF)  │
     └──────┬───────────────────┬───────┘
            │                   │
     ┌──────▼──────┐      ┌─────▼──────────┐
     │ Critical    │      │ Clinical Intel │
     │ Alerting    │      │ (AI Fabric)    │
     └─────────────┘      └─────┬──────────┘
                                │
                    ┌───────────┼───────────┐
                    │           │           │
            ┌───────▼───┐ ┌────▼────┐ ┌────▼───────┐
            │  SNDHS    │ │  NHOP   │ │ Population │
            │  Pack     │ │  Pack   │ │ Health Pack│
            └───────────┘ └─────────┘ └────────────┘
```

---

## 9. Module Lifecycle

### 9.1 Design Phase
- Define capability in `CapabilityDescriptor` format
- Identify dependencies on existing capabilities
- Design data model (SQLAlchemy tables or JSONB extensions)
- Define API surface (FastAPI routes)
- Design extension points for other packs
- Write ADR (Architecture Decision Record) at `docs/adr/`

### 9.2 Development Phase
- Create pack directory structure
- Implement models, services, routes
- Write Alembic migrations (idempotent, reversible)
- Build UI components (if applicable)
- Write i18n translations (Arabic + English minimum)
- Register capabilities in `CapabilityRegistry`

### 9.3 Testing Phase
- Unit tests: `tests/test_<pack>_unit.py`
- Integration tests: `tests/test_<pack>_integration.py`
- Migration round-trip test: `alembic downgrade -1 && alembic upgrade head`
- Tenant isolation test: verify `lab_id` filtering
- Audit coverage test: verify all mutations log
- Security scan: bandit, safety, gitleaks
- Performance benchmark: p99 latency, memory usage

### 9.4 Certification Phase
1. Automated security scan passes
2. Compatibility check against kernel API
3. Migration idempotency verified
4. Tenant isolation audit passes
5. Documentation complete (API, deployment, examples)
6. Clinical safety review (for clinical packs)
7. Board approves → certifies

### 9.5 Publish Phase
- Pack versioned and tagged in registry
- Pack.json manifest created
- Marketplace listing published
- Release notes generated
- Changelog updated

### 9.6 Install Phase
- Customer discovers via marketplace
- License key generated (if paid)
- Pack downloaded and verified
- Runtime validates dependencies and permissions
- Alembic migrations applied
- Pack initialized and registered with kernel
- Health check endpoint registered

### 9.7 Maintenance Phase
- Bug fixes released as PATCH versions
- Feature additions as MINOR versions
- Breaking changes as MAJOR versions (with migration path)
- Security patches expedited
- Deprecation notices published 2 MAJOR versions before removal

### 9.8 Retire Phase
- Capability status set to DEPRECATED
- Deprecation warning in logs
- Removal scheduled after deprecation period
- Data migration scripts provided
- Capability status set to RETIRED
- Pack uninstalled from customer instances

---

## Appendix A: Route Inventory

All 53 route modules in `backend/app/routes/`:

| Route File | Description | REST Path Prefix |
|------------|-------------|------------------|
| `login.py` | Authentication | `/login` |
| `labs.py` | Lab management | `/labs` |
| `patients.py` | Patient CRUD | `/patients` |
| `results.py` | Lab results | `/results` |
| `orders.py` | Lab orders | `/orders` |
| `samples.py` | Specimen tracking | `/samples` |
| `admin.py` | Admin console | `/admin` |
| `ai.py` | AI/ML routes | `/ai` |
| `ai_telemetry.py` | AI system telemetry | `/ai/telemetry` |
| `batch.py` | Batch operations | `/batch` |
| `canonical_patient.py` | Enterprise patient ID | `/canonical-patient` |
| `care_continuum.py` | Longitudinal care | `/care-continuum` |
| `citizen_portal.py` | Patient portal | `/citizen` |
| `claims.py` | Insurance billing | `/claims` |
| `clinical.py` | Clinical intelligence | `/clinical` |
| `clinical_documentation.py` | Clinical notes | `/clinical-docs` |
| `clinical_orders.py` | Clinical (non-lab) orders | `/clinical-orders` |
| `clinical_quality.py` | Clinical quality metrics | `/clinical-quality` |
| `compliance.py` | Regulatory compliance | `/compliance` |
| `consent.py` | Patient consent | `/consent` |
| `critical_alerts.py` | Critical results | `/critical-alerts` |
| `dashboard.py` | Statistics dashboards | `/dashboard` |
| `device_results.py` | Device integration | `/device-results` |
| `edge.py` | Edge platform | `/edge` |
| `ehr.py` | EHR routes | `/ehr` |
| `ehr_fhir.py` | FHIR-compatible EHR | `/ehr/fhir` |
| `hospital.py` | Hospital management | `/hospital` |
| `id_scan.py` | ID card scanning | `/id-scan` |
| `identity.py` | Identity management | `/identity` |
| `insurance.py` | Insurance integration | `/insurance` |
| `integrations.py` | External integrations | `/integrations` |
| `metrics.py` | Platform metrics | `/metrics` |
| `mfa.py` | Multi-factor auth | `/mfa` |
| `mobile.py` | Mobile API endpoints | `/mobile` |
| `national_data.py` | National health data | `/national-data` |
| `national_identity.py` | National ID | `/national-identity` |
| `national_streaming.py` | National data streaming | `/national-streaming` |
| `notifications.py` | Notifications | `/notifications` |
| `oauth2.py` | OAuth2 server | `/oauth2` |
| `optimizer.py` | Lab optimizer | `/optimizer` |
| `password_reset.py` | Password management | `/password-reset` |
| `patient_card.py` | QR patient cards | `/patient-card` |
| `qr.py` | QR code utilities | `/qr` |
| `quality_control.py` | QC management | `/quality-control` |
| `register.py` | Lab registration | `/register` |
| `saml.py` | SAML SSO | `/saml` |
| `security.py` | Security settings | `/security` |
| `service_accounts.py` | API service accounts | `/service-accounts` |
| `setup.py` | Initial setup | `/setup` |
| `stats.py` | Statistics & trends | `/stats` |
| `test_results.py` | Test type results | `/test-results` |
| `tiers.py` | Subscription tiers | `/tiers` |

## Appendix B: Model Inventory

All 26 model files in `backend/app/models/`:
`lab.py`, `lab_user.py`, `patient.py`, `user.py`, `lab_order.py`, `lab_result.py`, `sample.py`,
`test_result.py`, `test_type.py`, `quality_control.py`, `audit_log.py`, `outbox.py`,
`ai_interaction.py`, `canonical_patient.py`, `claim.py`, `consent.py`, `edge.py`,
`mfa_device.py`, `oauth2_client.py`, `oauth2_token.py`, `organization.py`,
`service_account.py`, `subscription.py`, `base.py` (declarative base).
