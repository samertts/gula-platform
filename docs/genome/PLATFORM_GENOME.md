# GULA Platform — Platform Genome

> **Version:** 2.1.0 | **Last Updated:** 2026-07-17 | **Classification:** CONFIDENTIAL
> The complete genetic blueprint of the GULA Platform — 10 chromosomes, gene expression map, genetic traits, mutation history, and genome health score.

---

## Chromosome 1: Backend Core (DNA Sequence)

### Gene 1.1 — main.py (The Nucleus)
```
Lifespan → StartupGuard → warmup → Kernel → Routes → serve → shutdown → dispose
```

**Middleware Stack (5' → 3'):**
1. `MaxBodySizeMiddleware` — 413 if > MAX_REQUEST_BODY_MB (default 10)
2. `RequestIDMiddleware` — UUID assignment + log context binding
3. `DocsAuthMiddleware` — JWT-protected /docs in production
4. `CORSMiddleware` — configured origins + mobile app schemes
5. `RequestTimingMiddleware` — access log + X-Response-Time header
6. `SecurityHeadersMiddleware` — CSP, HSTS, X-Frame-Options, Permissions-Policy
7. `GZipMiddleware` — compress responses >= 1000 bytes
8. `ReadinessMiddleware` — 503 until system_ready=True
9. `DegradedModeMiddleware` — blocks writes in L2/L3 degradation
10. `KernelMiddleware` — kernel context per-request
11. `ConcurrencyLimitMiddleware` — backpressure (default 200, clinical writes exempt)

**Global Error Handler:** Returns bilingual (Arabic/English) JSON. In production: hides stack traces, returns 503 if system not ready.

### Gene 1.2 — config.py (The Genetic Code)
```
ENV → RUNTIME_MODE → SECRET_KEY → JWT → ENCRYPTION_KEY → DATABASE_URL → REDIS_URL → 
SNDHS_FLAGS → FINANCIAL_FLAGS → KERNEL_FLAGS → ADAPTER_MODES → AI_PROVIDERS
```

**Runtime Modes:** api | worker | test | cli
**Secret Strength Check:** 16 weak patterns detected → hard fail in production
**Feature Gates:** 4 env-var controlled toggles (SNDHS_VISITS, SNDHS_NATIONAL_ID, FINANCIAL_ENGINE, ADS)

### Gene 1.3 — database.py (The Mitochondria — Energy Provider)
```
Engine → Pool (5+10 per worker × 2 workers = 40) → SessionLocal → get_db()
                                      ↓
                           SlidingWindow (300s)
                                      ↓
                    Circuit Escalation: L1 → L2 → L3
```

**Connection Budget:** `2 workers × (5 pool + 10 overflow) = 40` (under Postgres 100 default)

**Error Escalation Thresholds:**
| Level | Event | Threshold | Action |
|-------|-------|-----------|--------|
| L1_SLOW | DB timeout >5/5min | TIMEOUT_L1=5 | Prefer cache |
| L2_CIRCUIT | DB refused >20/5min | CIRCUIT_OPEN=20 | Open breaker, block writes |
| L3_DEGRADE | DB refused >50/5min | SYSTEM_DEGRADE=50 | Critical-only mode |

### Gene 1.4 — worker.py (The Immune System)
```
OutboxWorker → RecoveryWorker → HealthWatchdog → AdaptiveConcurrency → AutoRepair → TaskWorker
```

Each loop runs in `_resilient_loop` with exponential backoff (5s → 120s max).

---

## Chromosome 2: API Layer (Routes as Genes)

### Expression Pattern
All routes register via `app.include_router()` in `main.py`. Registration order:
1. Core routes (login, register, setup, metrics, patients, results, test_results, dashboard, labs, samples)
2. Feature routes (qr, id_scan, identity, notifications, ehr, security, device_results)
3. Advanced lab (quality_control, critical_alerts, batch)
4. Admin, Mobile, Compliance, Tiers, Citizen Portal, Claims
5. Legacy (national_identity, insurance)
6. AI (ai, optimizer, ai_telemetry)
7. Clinical (clinical, clinical_orders, clinical_documentation, clinical_quality)
8. Kernel management
9. Governance + National LIMS
10. National Platform Runtime (19 modules: rules, background, workflow, task, notification, document, scheduling, search, observability)
11. National Data Platform
12. Platform Foundation, Contracts, Integration Connectors
13. Hospital, NHDW, Nursing, Pharmacy, Radiology, Simulation
14. Command Intelligence, Knowledge Graph, Roadmap Engine, Health Data Lake
15. Enterprise Control Plane, Runtime Kernel Extensions
16. National Integration Platform, Citizen Platform, AI Fabric, Research Platform
17. Certification, Ecosystem, Intelligence
18. EMS, Blood Bank, Critical Care, Biomedical Engineering, Public Health
19. Command Center, Pilot Platform, Lifecycle Platform, Trust Platform

**Total Routers Registered:** 100+ distinct routers from 80+ route modules

---

## Chromosome 3: Data Layer (Models & Migrations)

### Schema Evolution (47 migrations in chronological order)

```
2025-03-22: Foundation (6 migrations) — Bootstrap, roles, indexes, states
2026-03-24: Phase 2 (5 migrations) — Patient, lab metadata, audit v1, production indexes
2026-03-29: Phase 2 (2 migrations) — Subscription tiers, optimistic lock
2026-04-07/28: Feature (4 migrations) — Claims, MPI, Consent, Edge
2026-05-03/06: Analytics (2 migrations) — Stats, Financial Engine Phase A
2026-05-05: SNDHS Phase 1 (6 migrations) — Patient fields, visits, audit v2
2026-05-11: AI Dataset (2 migrations) — AI interactions, safety columns
2026-07-14/16: National Platform (18 migrations) — LIMS, NHDW, Nursing, Pharmacy,
  Radiology, EMS, Blood Bank, Critical Care, Biomedical, Public Health, Command Center,
  Pilot, Lifecycle, Trust, Governance, Auth, Canonical Patient
```

### Model Inheritance Tree
```
Base (declarative_base)
├── Lab models: Lab, LabUser, LabOrder, LabResult, Patient, Sample, TestType, TestResult
├── Security models: User, MFADevice, OAuth2Client, OAuth2Token, ServiceAccount
├── Business models: QualityControl, Claim, Subscription, FeatureFlag, Organization
├── Audit: AuditLog, OutboxEvent
├── Clinical: Consent, AIInteraction, AIFeedback
├── Edge: EdgeDevice, EdgeEvent, EdgeModel, EdgeTask, EdgeTelemetry, EdgePolicy
├── MPI: CanonicalPatient
│
HospitalBase
├── HospitalMaster, Building, Floor, Unit, Room, Bed, Clinic, Department, etc.

NHDWBase
├── Admission, Discharge, Transfer, TelemedicineSession, ShiftReport, etc.

NationalBase
├── Nursing: NursingNote, NursingTask, NursingShift, etc.
├── Pharmacy: Prescription, DispenseRecord, DrugCatalog, StockLevel, etc.

RadiologyBase
├── RadiologyExam, DICOMStudy, RadiologyReport, WorklistEntry, etc.

NationalDataBase
├── CanonicalPatient, CanonicalObservation, CanonicalEncounter (MDM)
├── GoldenRecord, DuplicateRecord, MergeAction (MDM)
├── StoredEvent, EventSnapshot (Event Store)
├── DataCatalogEntry, ConsentDirective, DataLineageEntry (Governance)
├── FactLabResult, FactPatientVisit, DimPatient (Warehouse)
├── VectorEmbedding, TrainingDataset, KnowledgeGraphNode (AI Data)
```

---

## Chromosome 4: Security & Identity

### Authentication Layers
```
REST API → JWT (HS256, 30min default) → Refresh Token (30 days)
OAuth2 → Authorization Code + PKCE → Client Credentials (M2M)
SAML2 → SP-Initiated SSO → IdP Assertion
MFA → TOTP | WebAuthn/FIDO2 | Backup Codes
Risk-Based → Device Trust + Behavioral Scoring → Step-up Auth
```

### Authorization Matrix
```
RBAC (9 roles × 13 permissions)
  ├── patient, lab_technician, lab_supervisor, lab_admin
  ├── doctor, admin, master_admin, ministry_officer, system
  └── Hierarchical resolution (lab_admin ≥ lab_supervisor ≥ lab_technician)

ABAC (Attribute-based)
  ├── User attributes (role, lab_id, department)
  ├── Resource attributes (lab_id, sensitivity, type)
  └── Environment (time, location, device trust)

Consent Layer
  └── Patient Consent Directive → blocks data access without consent

Tenant Isolation
  └── All queries: WHERE lab_id = current_user.lab_id
```

### Cryptographic Assets
| Secret | Env Var | Algorithm | Criticality |
|--------|---------|-----------|-------------|
| JWT Signing | SECRET_KEY | HS256 | CRITICAL |
| Refresh Token | REFRESH_TOKEN_SECRET | HS256 | CRITICAL |
| PII Encryption | ENCRYPTION_KEY | Fernet (AES-128-CBC) | CRITICAL |
| National ID HMAC | NID_HMAC_KEY | HMAC-SHA256 | CRITICAL |
| Device HMAC | DEVICE_HMAC_KEY | HMAC-SHA256 | HIGH |

---

## Chromosome 5: Business Logic (Services & Domain)

### Order State Machine
```
                    ┌──────────────┐
                    │   pending    │
                    └──────┬───────┘
                           │
              ┌────────────┼────────────┐
              ▼            ▼            │
      ┌──────────────┐ ┌──────────────┐ │
      │  completed   │ │  cancelled   │ │
      └──────┬───────┘ └──────────────┘ │
             │            ▲             │
             ▼            └─────────────┘
      ┌──────────────┐
      │  validated   │  ← terminal
      └──────────────┘
```

### Service Layer Pattern
```
Route → Service → Repository (SQLAlchemy) → Database
          │
          ├── Audit Service (immutable log)
          ├── Outbox Service (guaranteed delivery)
          └── Event Bus (decoupled notifications)
```

### Core Service Chain for Lab Result
```
POST /results → results.py → order_service → audit_service → 
  outbox_service → critical_alerts (if critical) → notifications (push/FCM)
```

---

## Chromosome 6: Intelligence (AI & Clinical)

### AI Architecture
```
┌─────────────────────────────────────────────────────┐
│                   AI Providers                        │
│  Gemini (clinical)  │  Groq  │  Ollama  │  Rules     │
└──────────┬───────────────────────────────────────────┘
           │
┌──────────▼───────────────────────────────────────────┐
│              AI Guardrails (guardrails.py)             │
│  Hallucination detection │ Clinical safety │ Approval │
└──────────┬───────────────────────────────────────────┘
           │
┌──────────▼───────────────────────────────────────────┐
│              Clinical AI Services                      │
│  ali_reza_engine │ samir_engine │ interpretation      │
│  clinical_intelligence │ anomaly_detection             │
└──────────┬───────────────────────────────────────────┘
           │
┌──────────▼───────────────────────────────────────────┐
│              AI Sandbox (sandbox.py)                   │
│  Isolated execution │ Resource limits │ Audit trail   │
└──────────────────────────────────────────────────────┘
```

### AI Interaction Dataset Pipeline
```
AI Request → AIInteraction record → Feedback loop →
  MedicalTerminologyNormalized → Training Dataset → Knowledge Graph
```

---

## Chromosome 7: Frontend (All 3 Frontends)

```
┌────────────────────────────────────────────────────────┐
│                    frontend-v2/                         │
│  React + Firebase + Vite + TypeScript                  │
│  ├── Citizen Portal (patient self-service)             │
│  ├── Ministry Command Centre (national dashboard)      │
│  ├── Doctor Workspace (clinical orders, results)       │
│  ├── Lab Dashboard (operations, QC, analytics)         │
│  └── Predictive Analytics (AI-powered trends)          │
├────────────────────────────────────────────────────────┤
│                    client/                              │
│  React + tRPC + Vite + TypeScript                      │
│  └── Lightweight SPA (backend tRPC)                    │
├────────────────────────────────────────────────────────┤
│                    frontend/                            │
│  Static HTML + Service Worker + PWA Manifest           │
│  ├── Offline result viewing                            │
│  ├── Login / Register / Tier display                   │
│  └── Service worker caching                            │
└────────────────────────────────────────────────────────┘
```

---

## Chromosome 8: Integration (Device Bridge & National)

### Device Bridge (LabLink-Core)
```
Physical Lab Instrument (Sysmex, Roche, Mindray, etc.)
  │
  └── ASTM/HL7 Protocol ──→ Device Bridge
                              │
                    ┌─────────┼─────────┐
                    ▼         ▼         ▼
              Parsers    Pipeline   Adapters
              (ASTM)   (matching,  (vendor-specific)
                        mapping,
                       normalizing)
                    │         │         │
                    └─────────┼─────────┘
                              ▼
                    Integration Client
                    (gula_client.py)
                              │
                              ▼
                    gula-backend API
                    (/device-results)
```

### National Integration (SNDHS Phase 1)
```
gula-backend ←→ nhop-platform (citizen registry)
      │
      ├── Iraqi MoI NID API (stub/live/shadow)
      ├── NHI Insurance API (stub/live/shadow)
      ├── MoI Residency API (stub/live/shadow)
      └── Cloudflare (R2, WAF, Workers)
```

---

## Chromosome 9: Infrastructure (Deployment & CI/CD)

### Deployment Topology
```
Internet
  │
  ├── Cloudflare (DNS, WAF, CDN, R2)
  │     │
  │     └── DigitalOcean Droplet / DO App Platform
  │           │
  │           └── host nginx (TLS termination)
  │                 │
  │                 └── Docker Network (gula-net)
  │                       │
  │               ┌───────┼───────────┐
  │               ▼       ▼           ▼
  │         api-gateway  postgres:16  redis:7
  │         (nginx)      (database)   (cache)
  │               │
  │        ┌──────┴──────┐
  │        ▼              ▼
  │   gula-backend    gula-worker
  │   (FastAPI)       (background)
```

### Container Architecture (MVP docker-compose.yml)
| Service | Image | Port | Dependencies |
|---------|-------|------|--------------|
| postgres | postgres:16-alpine | 5432 (internal) | — |
| redis | redis:7-alpine | 6379 (internal) | — |
| gula-backend | gula-backend:latest | 8000 (internal) | postgres, redis |
| api-gateway | nginx:alpine | 80/443 | gula-backend |

### CI/CD Pipeline (6 Gates)
```
Push → syntax-gate (<30s) → migration-check → smoke-test →
  backend-test → security-scan → build-and-push (8 images to GHCR)
```

---

## Chromosome 10: Self-Healing & Resilience

### Three-Layer Defense System

**Layer 1 — Circuit Breaker (self_healing.py)**
```
Normal → Failure Count → Circuit OPEN (L2_READ_ONLY) → Recovery Probe →
  Half-Open → Success → Circuit CLOSED
```

**Layer 2 — Auto-Repair Engine (auto_repair.py)**
```
Periodic Cycle:
  1. Run GC (generational collection)
  2. Recycle connection pool
  3. Reconnect Redis if down
  4. Persist sliding window to Redis
  5. Check and repair health.check()
```

**Layer 3 — Adaptive Concurrency (main.py)**
```
DB Query Latency Monitor:
  >300ms average → halve _MAX_CONCURRENT
  <150ms average × 3 consecutive → restore _MAX_CONCURRENT
```

### Health Alert Watchdog
```
Every 60s (10s in RED):
  Check DB, Redis, Memory, Queue Backlog, Degraded Mode
  Grade: GREEN | YELLOW | RED
  On Transition: ALERT_WEBHOOK_URL (Telegram/Discord/Slack)
  RED Reminder: Every 5 minutes
```

### Degradation Levels
| Level | Name | DB Writes | DB Reads | AI | Health |
|-------|------|-----------|----------|-----|--------|
| L0 | NORMAL | ✅ | ✅ | ✅ | ✅ |
| L1 | CACHE_HEAVY | ✅ | Cache-first | ⚠️ Limited | ✅ |
| L2 | READ_ONLY | ❌ | ✅ | ❌ | ✅ |
| L3 | CRITICAL_ONLY | ❌ | ❌ | ❌ | Only health/auth |

---

## Gene Expression Map (Feature Flags)

### Deployment-Wide Flags (config.py)
| Flag | Env Var | Default | Gene Expression |
|------|---------|---------|-----------------|
| SNDHS_ENABLE_VISITS | SNDHS_ENABLE_VISITS | false | Controls visits table + lab_orders.visit_id |
| SNDHS_ENABLE_NATIONAL_ID | SNDHS_ENABLE_NATIONAL_ID | false | Controls national_id/health_id fields |
| ENABLE_FINANCIAL_ENGINE | ENABLE_FINANCIAL_ENGINE | false | Controls /financial/* routes + pricing |
| ENABLE_ADS | ENABLE_ADS | false | Controls sponsored listings (requires FINANCIAL) |
| FEATURE_BACKGROUND_TASKS | FEATURE_BACKGROUND_TASKS | true (worker) | Master kill-switch for background loops |
| RUNTIME_MODE | RUNTIME_MODE | api | Execution context: api/worker/test/cli |

### Per-Tenant Flags (feature_flags.py + subscription tiers)
| Flag Group | Examples | Gating |
|------------|----------|--------|
| AI Features | clinical_ai, ai_assistant, ai_interpretation | Tier + Lab flag |
| Clinical | ehr_integration, fhir_api, care_continuum | Tier + Lab flag |
| SNDHS | sndhs_visits, sndhs_national_id | Tier + env flag |
| Financial | billing, ranking, incentives | Tier + env flag |
| Security | mfa_required, saml_sso, oauth2 | Tier |

### Kernel Flags (config.py)
| Flag | Default | Controls |
|------|---------|----------|
| KERNEL_KILL_SWITCH | false | Emergency stop for autonomous kernel |
| KERNEL_DEGRADED | false | Put kernel into degraded mode |
| KERNEL_ENABLE_PLUGINS | true | Plugin system |
| KERNEL_ENABLE_EVENT_BUS | true | Internal event bus |
| KERNEL_ENABLE_BACKGROUND | true | Background task processing |
| KERNEL_ENABLE_FEATURES | true | Feature flag management |
| KERNEL_ENABLE_CONFIG | true | Configuration engine |
| KERNEL_ENABLE_TENANT | true | Multi-tenant engine |
| KERNEL_ENABLE_GATEWAY | true | Internal API gateway |

---

## Genetic Traits (Architectural Characteristics)

### Structural Traits
| Trait | Value | Description |
|-------|-------|-------------|
| Architecture Style | Monolith-first | Production monolith (backend/app/) with decomposed microservice stubs (services/) |
| Database Strategy | Single-writer + Read Replicas | Primary postgres:16 with optional READ_REPLICA_URL for read scaling |
| Caching Strategy | L1 (in-memory) + L2 (Redis) | Two-tier with configurable TTLs |
| Message Pattern | Outbox + Event Bus | Guaranteed delivery via outbox pattern + internal event bus |
| API Protocol | REST (primary) + tRPC (client) | REST for external, tRPC for internal SPA |
| Auth Protocol | JWT + OAuth2 + SAML2 + MFA | Multi-protocol with risk-based step-up |

### Quality Attributes
| Attribute | Target | Measurement |
|-----------|--------|-------------|
| Availability | 99.99% | Docker healthcheck + Prometheus |
| RTO | < 30 min | DR procedures tested |
| RPO | < 5 min | Continuous backup + WAL archiving |
| P99 Latency API | < 500ms | Prometheus + Grafana |
| P99 Latency DB | < 50ms | pg_stat_activity monitoring |
| Max Concurrent | 200 (default) | Adaptive concurrency middleware |
| Connection Pool | 40 (2x20) | 2 workers x (5+15) |

### Security Posture
| Control | Implementation |
|---------|---------------|
| Encryption at Rest | Fernet (national_id, PII fields) |
| Encryption in Transit | TLS (nginx termination) |
| Token-based Auth | JWT HS256 (30min) + Refresh (30d) |
| Multi-Factor | TOTP, WebAuthn, Backup Codes |
| Rate Limiting | Token-bucket (10/min auth, 30/min public) |
| Intrusion Detection | Pattern-based (brute force, credential stuffing) |
| API Firewall | Application-layer filtering |
| Audit Trail | Immutable hash chain (SHA-256) |
| Secret Validation | 16 weak patterns detected at startup |

---

## Mutation History (Migration Chronology)

```
2025-03-22 ── Foundation Bootstrap ────────────────────── [MG-001→006]
  │
2026-03-24 ── Phase 2: Patient/Meta/Audit X ───────────── [MG-007→011]
  │
2026-03-29 ── Phase 2: Tiers/Optimistic Lock ──────────── [MG-012→013]
  │
2026-04-07/28 ── Feature: Claims/MPI/Consent/Edge ─────── [MG-014→017]
  │
2026-05-03/06 ── Analytics + Financial Engine ─────────── [MG-018, MG-025]
  │
2026-05-05 ── SNDHS Phase 1 ────────────────────────────── [MG-019→024]
  │
2026-05-11 ── AI Dataset + Safety ─────────────────────── [MG-026→027]
  │
2026-07-14 ── National LIMS ────────────────────────────── [MG-028]
  │
2026-07-15 ── National Ecosystem Partners ──────────────── [MG-029]
  │
2026-07-16 ── National Platform Mega-Launch ────────────── [MG-030→045]
  │   ├── NHDW (MG-030) ▸ Nursing (MG-031) ▸ Pharmacy (MG-032)
  │   ├── Radiology (MG-033) ▸ EMS (MG-034) ▸ Blood Bank (MG-035)
  │   ├── Critical Care (MG-036) ▸ Biomedical (MG-037)
  │   ├── Public Health (MG-038) ▸ Command Center (MG-039)
  │   ├── Pilot (MG-040) ▸ Lifecycle (MG-041) ▸ Trust (MG-042)
  │   └── Governance (MG-043) ▸ Auth (MG-044) ▸ Canonical (MG-045)
  │
  ▼
2026-07-17 ── CURRENT STATE (v2.1.0, 47 migrations)
```

---

## Genome Health Score

### Current Vital Signs (as of 2026-07-17)

| Metric | Score | Status |
|--------|-------|--------|
| Test Coverage | 59 test files, 28 integration modules | 🟢 HIGH |
| Migration Stability | 47 revisions, all idempotent | 🟢 HIGH |
| Secret Strength | Hard-fail + 16 weak-pattern detection | 🟢 HIGH |
| Circuit Breaker | 3-level with auto-recovery | 🟢 HIGH |
| Feature Flag Hygiene | All new features flag-gated | 🟢 HIGH |
| API Completeness | 51 route modules, 100+ routers | 🟢 HIGH |
| Multi-Tenant Isolation | All queries filter by lab_id | 🟢 HIGH |
| Audit Trail | Immutable hash chain on mutations | 🟢 HIGH |
| Documentation | 26 ADRs, CLAUDE.md, ARCHITECTURE.md | 🟡 MEDIUM |
| CI/CD Pipeline Health | 6 gates, all passing | 🟢 HIGH |
| Dependency Freshness | Regular updates, SBOM generated | 🟡 MEDIUM |
| Disaster Recovery | DR tested, RTO<30min, RPO<5min | 🟢 HIGH |

### Known Genetic Anomalies
| Issue | Impact | Mitigation |
|-------|--------|------------|
| Monolith scalability ceiling | Limits independent scaling of route groups | Microservice stubs ready in services/ |
| Shared database schema | Couples bounded contexts | National Platform modules use separate schemas |
| Runtime mode complexity | 4 modes with different behaviors | Strict mode checking at startup |
| Feature flag sprawl | Per-tenant + env flags in parallel | Clear separation documented in config.py |

---

*End of Platform Genome — 10 chromosomes + expression map + mutation history + health score.*
