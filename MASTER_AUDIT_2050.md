# GULA GRAND MASTER AUDIT 2050

> **نسخة شاملة: كل شيء في GULA**
>
> *Comprehensive Knowledge Base: Every component, every decision, every risk — mapped, verified, versioned.*

```
╔══════════════════════════════════════════════════════════════════════════════╗
║                   GULA PLATFORM — NATIONAL CRITICAL INFRASTRUCTURE          ║
║                                                                              ║
║  System-of-Systems for the Republic of Iraq's National Digital Health        ║
║  Transformation. Monolith-first, event-driven, AI-augmented, sovereign.      ║
║                                                                              ║
║  Version: 2.1.0       |       Audit Date: July 17, 2026                     ║
║  Audit Scope: 50 Areas | 1000+ Files | 1505+ Tests | 25 ADRs               ║
╚══════════════════════════════════════════════════════════════════════════════╝
```

---

## TABLE OF CONTENTS

1.  [Repository](#1-repository)
2.  [Architecture](#2-architecture)
3.  [Backend](#3-backend)
4.  [Frontend](#4-frontend)
5.  [Database](#5-database)
6.  [APIs](#6-apis)
7.  [AI](#7-ai)
8.  [Security](#8-security)
9.  [Healthcare](#9-healthcare)
10. [Public Health](#10-public-health)
11. [Laboratory](#11-laboratory)
12. [Radiology](#12-radiology)
13. [Pharmacy](#13-pharmacy)
14. [Dentistry](#14-dentistry)
15. [Nursing](#15-nursing)
16. [Hospital](#16-hospital)
17. [Citizen](#17-citizen)
18. [Ministry](#18-ministry)
19. [Government](#19-government)
20. [Infrastructure](#20-infrastructure)
21. [Kubernetes](#21-kubernetes)
22. [Docker](#22-docker)
23. [Terraform](#23-terraform)
24. [CI/CD](#24-cicd)
25. [GitHub](#25-github)
26. [Documentation](#26-documentation)
27. [Testing](#27-testing)
28. [Benchmark](#28-benchmark)
29. [Disaster Recovery](#29-disaster-recovery)
30. [Compliance](#30-compliance)
31. [Accessibility](#31-accessibility)
32. [Localization](#32-localization)
33. [Offline](#33-offline)
34. [Synchronization](#34-synchronization)
35. [Scalability](#35-scalability)
36. [Reliability](#36-reliability)
37. [Performance](#37-performance)
38. [Clinical Safety](#38-clinical-safety)
39. [Privacy](#39-privacy)
40. [Digital Identity](#40-digital-identity)
41. [Digital Wallet](#41-digital-wallet)
42. [Knowledge Graph](#42-knowledge-graph)
43. [Digital Twin](#43-digital-twin)
44. [Integration](#44-integration)
45. [SDK](#45-sdk)
46. [Plugin System](#46-plugin-system)
47. [Marketplace](#47-marketplace)
48. [Developer Platform](#48-developer-platform)
49. [Future Readiness](#49-future-readiness)
50. [Sustainability](#50-sustainability)

---

## 1. Repository

### Identity

| Property | Value |
|----------|-------|
| **Name** | `gula-platform` |
| **Path** | `/home/samertts/workspace/projects/gula-platform` |
| **Type** | Monorepo (consolidated from 3 former repos) |
| **App Version** | `2.1.0` |
| **Primary Stack** | Python 3.11+ (FastAPI), TypeScript (React 19), PostgreSQL 16, Redis 7 |
| **License** | Proprietary — Ministry of Health Iraq Compliant |
| **Root Authority** | `CLAUDE.md` (Engineering Constitution) |
| **Git History** | 50+ commits, multiple merged PRs across foundation/production/national missions |
| **Deployments** | Docker Compose (primary), Kubernetes (kustomize + helm), DigitalOcean, Render |

### Repository Structure

```
gula-platform/
├── backend/                    # FastAPI monolith (production target)
│   ├── app/                    # Application core (70+ modules)
│   │   ├── main.py            # App init, middleware stack, lifespan, 100+ route registrations
│   │   ├── config.py          # Env var loading, hard-fail on weak/missing secrets
│   │   ├── database.py        # SQLAlchemy engine, pool, circuit escalation, sliding window
│   │   ├── routes/            # 53 route modules (auth, patients, results, labs, etc.)
│   │   ├── models/            # 26+ core ORM models + 30+ domain-specific models
│   │   ├── core/              # 18 infrastructure modules (self-healing, startup-guard, etc.)
│   │   ├── security/          # 16 security modules (auth, RBAC, ABAC, encryption, etc.)
│   │   ├── services/          # Business logic (MPI, interpretation, outbox, etc.)
│   │   ├── ai/                # Clinical AI sandbox + gateway + guardrails
│   │   ├── ai_fabric/         # National AI & Intelligence Fabric (12+ modules)
│   │   ├── clinical/          # Clinical terminology, CDS, quality
│   │   ├── radiology/         # Radiology IS + PACS + AI analysis
│   │   ├── pharmacy/          # Pharmacy information platform
│   │   ├── nursing/           # Nursing & care coordination
│   │   ├── nhdw/              # National Hospital Desktop Workspace
│   │   ├── hospital/          # Hospital information system
│   │   ├── citizen_platform/  # Citizen digital health
│   │   ├── national/          # National platform runtime (19 modules)
│   │   ├── national_data/     # National data platform (MDM, warehouse, event store)
│   │   ├── governance/        # National governance layer
│   │   ├── lims/              # National LIMS layer
│   │   ├── ems/               # EMS & disaster response
│   │   ├── blood_bank/        # Blood bank & transfusion
│   │   ├── critical_care/     # Critical care (ICU)
│   │   ├── biomedical/        # Biomedical engineering
│   │   ├── public_health/     # Public health & disease surveillance
│   │   ├── command_center/    # Health command & crisis center
│   │   ├── pilot_platform/    # Pilot deployment & readiness
│   │   ├── lifecycle_platform/# Platform lifecycle & governance
│   │   ├── trust/             # National trust platform
│   │   ├── knowledge_graph/   # Platform knowledge graph
│   │   ├── roadmap/           # Master roadmap engine
│   │   ├── simulation/        # Digital twin platform
│   │   ├── command_intelligence/ # Command intelligence
│   │   ├── control_plane/     # Enterprise control plane
│   │   ├── certification/     # Certification & engineering metrics
│   │   ├── research_platform/ # Research & analytics
│   │   ├── integration/       # Integration connectors & platform
│   │   ├── contracts/         # Platform contracts
│   │   ├── platform/          # Platform foundation modules
│   │   ├── kernel/            # Permanent runtime foundation
│   │   ├── edge/              # Edge AI platform
│   │   ├── financial/         # Financial Engine (Phase A — schema only)
│   │   ├── firewall/          # Rate limiting & firewall
│   │   ├── gateways/          # API gateways & adapter modes
│   │   ├── audit/             # Audit logging
│   │   ├── notifications/     # Notification service
│   │   ├── workflows/         # Workflow engine
│   │   └── tasks/             # Background task processing
│   ├── migrations/            # 47+ Alembic migration files
│   ├── tests/                 # 44 test files + kernel/ + integration/ + identity/ + etc.
│   ├── gateway/               # Service gateway (device_gateway, api_gateway)
│   ├── Dockerfile             # Multi-stage Python build
│   └── alembic.ini            # DB migration configuration
│
├── frontend-v2/               # React 19 + Firebase rich SPA (primary frontend)
│   ├── src/
│   │   ├── App.tsx            # App shell, routing, keyboard shortcuts
│   │   ├── main.tsx           # Bootstrap, telemetry init
│   │   ├── firebase.ts        # Firebase auth + firestore + offline persistence
│   │   ├── translations.ts    # 5 languages (EN/AR/KU/TR/SY), 650+ keys
│   │   ├── contexts/          # Auth, Language, Notification providers
│   │   ├── types/             # Full domain type definitions
│   │   ├── services/          # SyncService, AuditService, WorkflowEngine, AI services
│   │   ├── lib/               # Utilities, telemetry, command registry, hooks
│   │   └── views/             # 28 views across 8 wings
│   └── components/            # 36+ reusable components
│
├── services/                  # Microservices (future decomposition targets)
│   ├── device_bridge/         # LabLink-Core: ASTM/HL7 instrument integration
│   ├── lab/                   # Lab service stub
│   ├── patient/               # Patient service stub
│   ├── order/                 # Order service stub
│   ├── result/                # Result service stub
│   ├── sample/                # Sample service stub
│   ├── notification/          # Notification consumer stub
│   ├── ai/                    # AI service (Ollama-only, hard-locked)
│   ├── autonomous_manager/    # Self-healing container orchestration
│   └── shared/                # Deprecated shared library (re-exports from root shared/)
│
├── shared/                    # Canonical shared library (40+ modules)
│   ├── circuit_breaker.py     # Three-state breaker (CLOSED/OPEN/HALF_OPEN)
│   ├── messaging.py           # RabbitMQ wrapper
│   ├── events/                # EventBus, constants
│   ├── audit/                 # Hash-chained audit service
│   ├── auth/                  # JWT encode/decode, password hashing, MFA, WebAuthn
│   ├── security/              # Encryption, HMAC
│   ├── cache/                 # Redis + in-memory backends
│   ├── retry/                 # Retry decorators, bulkhead, safe_call
│   └── notifications/         # Push, email, SMS, WhatsApp
│
├── client/                    # Lightweight tRPC + React SPA
├── frontend/                  # Static HTML PWA (offline-capable)
├── ai/                        # Standalone AI modules
├── edge_agent/                # Offline edge computing agent
├── nhop-platform/             # National Health Oversight Platform
├── hospital_desktop/          # Desktop application for hospital
├── cli/                       # CLI tooling
├── platform/                  # Platform UI + reports
├── packages/uap/              # Universal Application Platform
│
├── docs/                      # Documentation
│   ├── adr/                   # 25 ADR files
│   ├── engineering/           # Constitution, blueprint, risk register, quality gates
│   ├── national/              # National-scale docs (architecture, API, FHIR, security)
│   ├── production/            # Ops guides (DR, incident response, scaling)
│   ├── sovereign/             # Sovereign infrastructure docs (phases 16-25)
│   ├── sndhs/                 # SNDHS-lite Phase 1 spec (22 files)
│   └── runbooks/              # 6 incident runbooks
│
├── config/                    # Infrastructure configuration
│   ├── prometheus/            # Prometheus rules + scrape config
│   ├── grafana/               # Provisioned dashboards
│   ├── haproxy/               # Load balancer config
│   ├── postgres/              # Init scripts, partitions, audit
│   ├── opentelemetry/         # OTel collector config
│   ├── security/              # SAST, DAST, container scan, IaC scan configs
│   ├── quality-gates/         # 9 quality gate scripts
│   └── ...                    # 20+ config directories
│
├── k8s/                       # Kubernetes manifests (base + overlays)
│   ├── base/                  # 30+ resource manifests
│   └── overlays/              # dev, prod, region-me, region-eu
│
├── helm/                      # Helm chart for gula-platform
├── terraform/                 # Terraform IaC (12 modules, 5 environments)
├── tests/                     # Operational tests (chaos, load, stress, recovery)
│   ├── chaos/                 # Bash + Chaos Mesh experiments
│   ├── load/                  # k6, Locust, custom Python
│   └── integration/           # Integrity test (100+ workers)
│
├── scripts/                   # Operations scripts (backfill, monitor, self-audit)
├── assessment/                # Assessment reports (architecture, security, etc.)
├── architecture/              # Master architecture docs (24 documents)
├── contracts/                 # API contracts (OpenAPI, AsyncAPI, FHIR, ASTM, HL7)
├── database/                  # SQL schemas
├── .github/                   # CI/CD workflows + Dependabot
│
├── Makefile                   # Build orchestration (80+ targets)
├── docker-compose.yml         # MVP stack
├── docker-compose.full.yml    # Enterprise stack
├── docker-compose.scale.yml   # Scaled stack
├── Dockerfile                 # Root Dockerfile (Node.js)
├── nginx.conf                 # API gateway config
└── pyproject.toml             # Python project config
```

**Merge Provenance:**
- `samertts/gula-platform` -> `backend/`, `services/`, `nhop-platform/`, `ai/` (core platform)
- `samertts/LabLink-Core` -> `services/device_bridge/` (instrument integration)
- `samertts/Front-end-` -> `frontend-v2/` (React + Firebase)

### Key Repository Stats

| Metric | Value |
|--------|-------|
| Total source files | 1000+ |
| Python modules in backend/app/ | 70+ directories, hundreds of files |
| TypeScript/React in frontend-v2 | 36 components, 28 views |
| Test files (backend) | 44 standalone + 3 subdirectory groups |
| Migration files | 47+ |
| ADR files | 25 + 8 national ADRs |
| Assessment reports | 20+ |
| Architecture documents | 24 |
| CI/CD workflows | 6 |
| Dockerfiles | 10+ |
| Makefile targets | 80+ |

---

## 2. Architecture

### System Architecture Overview

```
+------------------------------------------------------------------+
|                        CLIENT LAYER                                 |
|  +----------+  +----------+  +----------+  +--------------------+  |
|  |frontend  |  |frontend  |  | client/  |  | Mobile (Android/   |  |
|  |-v2/      |  |(Static   |  | (tRPC    |  | iOS via Firebase   |  |
|  |(React 19 |  | HTML PWA)|  | +React)  |  | Auth + REST API)   |  |
|  +----+-----+  +----+-----+  +----+-----+  +---------+----------+  |
+-------|-------------|-------------|--------------------|-----------+
|       |             |             |                    |             |
+-------|-------------|-------------|--------------------|-----------+
|                        API GATEWAY (nginx, TLS, rate-limit)           |
+------------------------------------------------------------------+
|                        BACKEND LAYER (FastAPI Monolith)               |
|                                                                       |
|  +----------------------------------------------+                    |
|  |               MIDDLEWARE STACK                |                    |
|  | MaxBodySize -> RequestID -> DocsAuth -> CORS |                    |
|  | Timing -> SecurityHeaders -> GZip ->         |                    |
|  | Readiness -> DegradedMode -> Kernel ->       |                    |
|  | ConcurrencyLimit                              |                    |
|  +----------------------------------------------+                    |
|                                                                       |
|  +----------+  +-----------+  +------------------+                    |
|  | ROUTES   |  | MODELS    |  | SERVICES         |                    |
|  | (53 mod- |  | (26+ ORM  |  | (interpretation, |                    |
|  |  ules)   |  | +30+ dom- |  | outbox, MPI,     |                    |
|  |          |  | ain)      |  | clinical_intell.) |                    |
|  +----------+  +-----------+  +------------------+                    |
|                                                                       |
|  +----------+  +-----------+  +------------------+                    |
|  | SECURITY |  | CORE      |  | KERNEL (runtime  |                    |
|  | (JWT,    |  | (self-    |  | foundation,      |                    |
|  | RBAC,    |  | healing,  |  | plugin system,   |                    |
|  | ABAC,    |  | startup,  |  | event bus,       |                    |
|  | OAuth2,  |  | policy,   |  | feature flags)   |                    |
|  | SAML,    |  | kill_sw.) |  |                  |                    |
|  | MFA)     |  |           |  |                  |                    |
|  +----------+  +-----------+  +------------------+                    |
|                                                                       |
|  +-------------------------------------------------------------+     |
|  | NATIONAL PLATFORM (governance, LIMS, national_data, public  |     |
|  | health, ems, blood_bank, critical_care, biomedical, command |     |
|  | center, pilot, lifecycle, trust, knowledge_graph, ai_fabric)|     |
|  +-------------------------------------------------------------+     |
|                                                                       |
|  +-------------------------------------------------------------+     |
|  | DOMAIN PLATFORMS (radiology, pharmacy, nursing, hospital,    |     |
|  | nhdw, citizen_platform, clinical, ehr, care_continuum, etc.)|     |
|  +-------------------------------------------------------------+     |
+------------------------------------------------------------------+
                          |
              +-----------+-----------+
              |                       |
              v                       v
    +-------------------+   +------------------+
    |  PostgreSQL 16     |   |  Redis 7          |
    |  (primary +        |   |  (cache, rate     |
    |   replica WAL)     |   |  limiting,        |
    +-------------------+   |  sentinel HA)      |
              |             +------------------+
              v
    +-------------------+
    |   ClickHouse       |
    |   (analytics)      |
    +-------------------+
```

### Architecture Decisions (Top 10)

| # | Decision | Rationale | Status |
|---|----------|-----------|--------|
| ADR-002 | **Monolith-first** | Single deployable before decomposition | **Active** |
| ADR-005 | **PostgreSQL 16 + Redis 7** | Mature, well-understood, sufficient for national scale | **Active** |
| ADR-003 | **Multi-tenant via lab_id** | Every query filtered by lab_id | **Active** |
| ADR-009 | **Self-healing infrastructure** | Circuit breakers, auto-repair, adaptive concurrency | **Active** |
| ADR-012 | **Layered identity** | Three tiers: app-level, national MPI, government | **Active** |
| ADR-014 | **OpenTelemetry observability** | Prometheus + Grafana + Loki + Tempo + OTel | **Active** |
| ADR-015 | **Active-passive multi-region DR** | ME primary, EU DR, RPO 5s, RTO 5min | **Active** |
| ADR-016 | **National EHR on separate base** | FHIR R4 compatible, declarative, layered | **Active** |
| ADR-024 | **Platform Constitution** | Supreme authority over all modules | **Active** |

### Design Patterns

| Pattern | Location | Implementation |
|---------|----------|---------------|
| **Monolith-first** | `backend/app/` | Single FastAPI app, routes registered in main.py |
| **Event-driven** | `shared/events/`, `shared/messaging/` | EventBus + RabbitMQ |
| **Transactional Outbox** | `backend/app/services/outbox_service.py` | Guaranteed event delivery |
| **Circuit Breaker** | `backend/app/core/self_healing.py` | Three-state, auto-recovery |
| **CQRS (partial)** | `database.py` | Read-replica engine for read queries |
| **Strategy** | `services/device_bridge/adapters/` | Vendor-specific instrument adapters |
| **Dependency Injection** | FastAPI `Depends()` | Auth, DB session, rate limiting |
| **Factory** | `backend/tests/conftest.py` | Test fixture factories |
| **Lifespan** | `main.py` | `asynccontextmanager` pattern |
| **Outbox** | `outbox_service.py` | Transactional outbox for events |
| **Saga (implied)** | `domain/order_state.py` | Compensating actions on failure |

---

## 3. Backend

### FastAPI Application (`backend/app/main.py`)

**1948 lines** — single entry point for all HTTP requests.

#### Middleware Stack (order matters)

| # | Middleware | Purpose | Defined At |
|---|-----------|---------|------------|
| 1 | `MaxBodySizeMiddleware` | 413 on >10MB request bodies | Line 349 |
| 2 | `RequestIDMiddleware` | X-Request-ID + DB correlation | Line 373 |
| 3 | `DocsAuthMiddleware` | JWT-gate on /docs, /redoc in prod | Line 409 |
| 4 | `CORSMiddleware` | Allow-list origins + headers | Line 466 |
| 5 | `RequestTimingMiddleware` | Access-log + X-Response-Time | Line 488 |
| 6 | `SecurityHeadersMiddleware` | CSP, HSTS, X-Frame-Options | Line 517 |
| 7 | `GZipMiddleware` | Compress responses >1KB | Line 556 |
| 8 | `ReadinessMiddleware` | 503 until system_ready flag | Line 575 |
| 9 | `DegradedModeMiddleware` | Reject writes when DB circuit open | Line 604 |
| 10 | `KernelMiddleware` | Attach kernel context to requests | Line 610 |
| 11 | `ConcurrencyLimitMiddleware` | Backpressure shed (clinical exempt) | Line 643 |

#### Background Workers

| Worker | Interval | Function |
|--------|----------|----------|
| `OutboxWorker` | Continuous | Process `OutboxEvent` queue |
| `RecoveryWorker` | Every 30s | Probe + auto-heal degraded components |
| `_health_alert_loop` | 60s (10s RED) | Grade system GREEN/YELLOW/RED |
| `AdaptiveConcurrency` | Every 30s | Halve/restore MAX_CONCURRENT |
| `AutoRepair` | Periodic | GC, pool recycle, reconnects |
| `EdgeMaintenance` | Every 30s | Reap stale tasks, mark offline devices |

#### Config (`backend/app/config.py` - 326 lines)

| Setting | Default | Hard Fail? |
|---------|---------|------------|
| `SECRET_KEY` | random (dev) | **Yes** in production |
| `REFRESH_TOKEN_SECRET` | random (dev) | **Yes** in production |
| `ENCRYPTION_KEY` | None (dev) | **Yes** in production |
| `NID_HMAC_KEY` | falls back to ENCRYPTION_KEY | **Yes** in production |
| `DATABASE_URL` | postgresql://postgres@localhost/gula | **Yes** in production |
| `REDIS_URL` | empty (in-memory fallback) | No |
| `JWT_ALGORITHM` | HS256 | - |
| `JWT_EXPIRE_MINUTES` | 30 | - |
| `REFRESH_TOKEN_EXPIRE_DAYS` | 30 | - |
| `MAX_REQUEST_BODY_MB` | 10 | - |
| `DB_POOL_SIZE` | 5 per worker | - |
| `DB_MAX_OVERFLOW` | 10 per worker | - |
| `WEB_CONCURRENCY` | 2 | - |
| `KERNEL_KILL_SWITCH` | false | - |

Weak-secret detection against 20 patterns (`default`, `change`, `secret`, `test`, etc.) - triggers `sys.exit(1)` in production.

#### Critical Backend Files

| File | Purpose | Lines |
|------|---------|-------|
| `app/main.py` | App init, middleware, lifespan, routes, background workers | 1948 |
| `app/config.py` | Env var loading, secrets validation, feature flags | 326 |
| `app/database.py` | Engine, pool, sliding window, circuit escalation, read replica | 533 |
| `app/core/self_healing.py` | Circuit breaker, DegradedModeMiddleware, SystemHealth | ~400 |
| `app/core/startup_guard.py` | system_ready flag, startup validation | ~200 |
| `app/core/auto_repair.py` | GC, pool recycle, reconnects | ~200 |
| `app/core/policy_engine.py` | 17 action types, risk levels, frequency guards | ~250 |
| `app/core/kill_switch.py` | Emergency stop for autonomous actions | ~150 |
| `app/core/idempotency.py` | Idempotency key middleware, ON CONFLICT protection | ~200 |
| `app/core/feature_flags.py` | Per-tenant feature matrix | ~200 |
| `app/security/auth.py` | JWT encode/decode, refresh tokens, blacklist | ~400 |
| `app/security/rbac.py` | 9 roles, 13 permissions, role hierarchy | ~300 |
| `app/security/abac.py` | Attribute-based access control with conditions | ~200 |
| `app/security/encryption.py` | Fernet symmetric encryption | ~100 |
| `app/security/rate_limit.py` | 4-tier rate limiting, dynamic IP blocking | ~300 |
| `app/services/outbox_service.py` | OutboxWorker, event emission, MAX_ATTEMPTS | ~330 |
| `app/services/mpi/matcher.py` | Fellegi-Sunter, Jaro-Winkler, Arabic normalization | ~315 |
| `app/ai/sandbox.py` | AI sandbox: suggest_interpretation, guardrails | ~350 |
| `app/domain/order_state.py` | Order state machine | ~150 |

---

## 4. Frontend

### Overview

The primary frontend is `frontend-v2/` - a React 19 SPA with Firebase backend. **36 components** across **28 views** serving **8 organizational wings**.

| Wing | Views | Purpose |
|------|-------|---------|
| General | Dashboard, Landing/Auth, Settings, Appointments, LabResults, Records, ImagingLab, LabIntelligence | Cross-cutting |
| Citizen | CitizenDashboard, Health, Assistant, Family, Medications, History, SmartResults, Registration, IdentityVerification, Consent, SecurityAudit | Patient portal |
| Lab | LabDashboard, WorkQueue, DeviceMonitoring, DeviceManagement, Inventory, SampleTracking, QC | LIMS operations |
| Doctor | DoctorIntelligence, PatientProfile | Clinical workspace |
| Admin | AuditLog, Infrastructure, IntegrationHub, SystemsArchitecture | System administration |
| Ministry | MinistryDashboard, NationalHealthGrid, EpidemiologicalIntelligence, DataSovereigntyAudit | National oversight |
| Researcher | ResearcherDashboard | Population health |

### Key Technologies

| Technology | Purpose |
|------------|---------|
| React 19 | UI framework |
| React Router 7 | Client-side routing |
| Firebase 11 | Auth + Firestore (real-time + offline) |
| Tailwind CSS v4 | Utility-first styling |
| `motion` (framer-motion) | Animations |
| Vite 6 | Build tool |
| Recharts | Charts |
| `@google/genai` | Gemini AI integration |
| PostHog + Sentry | Telemetry (lazy-loaded) |
| `cmdk` | Command palette |
| `sonner` | Toast notifications |
| `vite-plugin-pwa` | PWA support |

### Architecture Patterns

- **Provider hierarchy**: `AuthProvider -> LanguageProvider -> NotificationProvider -> Toaster -> AppContent`
- **Offline-first**: `SyncService` queues mutations in `localStorage`, processes on `window.online`
- **Real-time**: Heavy `onSnapshot` usage for live subscriptions from Firestore
- **Keyboard-first**: Cmd+K command palette, vim-style navigation chords (g+d, g+p, etc.)
- **Wing isolation**: `ROLE_WING_MAP` gates UI surface; tests enforce isolation
- **Permission guards**: `PermissionGuard` wraps admin/ministry routes

### Security Specifications

"The Dirty Dozen" attack payloads documented in `security_spec.md`:
1. Self-Promotion (role escalation)
2. Patient Hijacking (ownerId manipulation)
3. Ghost Records (non-existent patients)
4. Data Injection (2MB strings)
5. ID Poisoning (path traversal)
6. Orphaned Writes (incomplete records)
7. Privilege Escalation (anonymous read)
8. Relational Leak (cross-user patient listing)
9. Terminal State Bypass (appointment time travel)
10. Identity Spoofing (ownerId mismatch)
11. PII Scraping (unfiltered user queries)
12. Future Timestamping (year 2099)

---

## 5. Database

### Stack

| Component | Technology | Configuration |
|-----------|------------|---------------|
| **Primary** | PostgreSQL 16 | Docker: `postgres:16-alpine` |
| **Replica** | PostgreSQL 16 (streaming) | Configurable via docker-compose.full.yml |
| **Cache** | Redis 7 | Docker: `redis:7-alpine` |
| **Analytics** | ClickHouse | docker-compose.full.yml |
| **Object Store** | MinIO (S3-compatible) | docker-compose.full.yml |
| **Connection Pool** | SQLAlchemy + optional PgBouncer | config/postgres-pool/ |

### Connection Pool Formula

```
Total DB connections = WEB_CONCURRENCY x (DB_POOL_SIZE + DB_MAX_OVERFLOW)
Default:             2 x (5 + 10) = 30 total (well under PG default 100)
```

### Migration Policy (MANDATORY - never violate)

| Rule | Enforcement |
|------|-------------|
| Never modify existing migration | CI migration-check verifies |
| All schema changes = new revision | `alembic revision --autogenerate` |
| `20250322_0000_create_base_schema.py` immutable | CI blocks changes |
| Every migration must be idempotent | `_has_column()`, `_table_exists()` guards |
| New columns nullable or `server_default` | CI migration-check round-trip |
| Test on clean DB before PR | Makefile: `make migration-check` |

### Core ORM Models

| Model | Table | Purpose |
|-------|-------|---------|
| Lab | `labs` | Laboratory entities |
| LabUser | `lab_users` | Lab staff/users |
| Patient | `patients` | Patient records (national_id encrypted) |
| LabOrder | `lab_orders` | Test orders |
| LabResult | `lab_results` | Test results (optimistic-lock via version) |
| Sample | `samples` | Specimen tracking |
| TestType | `test_types` | Reference ranges |
| AuditLog | `audit_logs` | Hash-chained audit |
| OutboxEvent | `outbox_events` | Transactional outbox |
| QualityControl | `quality_control` | QC records |
| User | `users` | Platform users |

### Domain-Specific Models (30+ additional)

| Domain | Key Models |
|--------|-----------|
| LIMS | Instrument, InstrumentModel, Reagent, Consumable, Lot, Supplier, Storage, Transportation, Workstation, Section, Panel, SpecimenCatalog, ReferenceRangeDef, EquipmentLog, Calibration, Maintenance, TemperatureLog, IQC, EQA, DeltaCheckRule, AutoValidationRule, LabReport, ReportAttachment, Result, ResultValidation, ResultRelease, ElectronicSignature, ChainOfCustody, QCProgram |
| Radiology | DICOMStudy, DICOMStorage, ModalityDevice, Protocol, WorklistEntry, MPPS, RadiologyAppointment, RadiologyOrder, RadiologyExam, RadiologySeries, RadiologyImage, ImageAnnotation, ImageMeasurement, ImageShare, RadiologyReport, ReportTemplate, CriticalFinding, AIAnalysisJob |
| Pharmacy | DrugCatalog, DrugBatch, DrugSupplier, Store, Warehouse, StockLevel, StockMovement, Prescription, PrescriptionItem, DispenseQueue, DispenseRecord, DrugReturn, InventoryTransfer, InventoryTransferItem, InventoryForecast, DrugInteractionRule, ContraindicationRule, AllergyRule, DoseGuideline, ClinicalGuideline, Recall, WasteRecord, DrugMonitoring |
| Nursing | NursingNote, NursingShift, NursingTask, PatientAssignment, ShiftHandover, CarePlan, ClinicalChecklist, Delegation, EscalationRecord, FallRiskAssessment, FluidBalance, NursingCarePlan, NutritionAssessment, PainAssessment, PressureInjuryAssessment |
| NHDW | Admission, Discharge, Transfer, WardRound, CarePlan, ClinicalTask, QueueEntry, TelemedicineSession, ResourceSchedule, ShiftReport, DashboardConfiguration, WaitingListEntry, HospitalMessage, HospitalAlert |
| Hospital | HospitalMaster, Campus, Building, Floor, Unit, Room, Bed, BedAssignment, Clinic, HospitalDepartment, OperationTheater, MedicalEquipment, CostCenter |
| MDM | GoldenRecord, DuplicateRecord, MergeAction, SourceSystem, DeviceRegistry, LocationRegistry, ProviderRegistry, TerminologyRegistry |
| Warehouse | DimPatient, DimDate, DimFacility, DimProvider, DimDiagnosis, FactDiagnosis, FactLabResult, FactPatientVisit |
| EMS | EmergencyIncidentModel, DispatchAssignmentModel, AmbulanceModel, CrewShiftModel, TriageAssessmentModel, ePCRModel, MassCasualtyIncidentModel, ShelterModel |
| Blood Bank | BloodDonorModel, BloodDonationModel, BloodComponentModel, BloodInventoryModel, BloodRequestModel, CrossmatchModel, TransfusionModel |
| Critical Care | ICUAdmissionModel, ICUBedModel, VitalSignsRecordModel, EarlyWarningScoreModel, VentilatorSettingModel |

### Database Schema Files

| File | Purpose |
|------|---------|
| `database/schema.sql` | Main schema |
| `database/auth_schema.sql` | Auth tables |
| `data/db/init.sql` | Seed data |
| `data/db/global_test_library.sql` | Global test library |
| `config/postgres/init.sql` | Docker init |
| `config/postgres/audit.sql` | Audit triggers |
| `config/postgres/partitions.sql` | Table partitioning |

---

## 6. APIs

### API Design

| Aspect | Implementation |
|--------|---------------|
| **Protocol** | HTTP/REST |
| **Documentation** | Swagger UI at `/docs`, ReDoc at `/redoc` (JWT-gated in production) |
| **Auth** | Bearer JWT tokens (access + refresh) |
| **Format** | JSON (UTF-8) with Arabic support |
| **Versioning** | `X-API-Version` header (APP_VERSION) |
| **CORS** | Whitelist-based |

### API Endpoint Catalog (200+ endpoints)

| Prefix | Module | Auth Required | Description |
|--------|--------|---------------|-------------|
| `/health*` | system | No | Health probes |
| `/login` | login | No | JWT authentication |
| `/register` | register | No | User/lab registration |
| `/setup` | setup | Admin | Initial system setup |
| `/test-types` | test_results | No (cached) | Reference ranges |
| `/patients` | patients | Yes | CRUD |
| `/results` | results | Yes | Lab results |
| `/labs` | labs | Yes | Lab management |
| `/samples` | samples | Yes | Sample tracking |
| `/dashboard` | dashboard | Yes | Aggregated stats |
| `/orders` | orders | Yes | Test orders |
| `/critical-alerts` | critical_alerts | Yes | Critical value alerts |
| `/quality-control` | quality_control | Yes | QC (Westgard rules) |
| `/admin/*` | admin | Yes (master_admin) | System admin |
| `/mobile/*` | mobile | Yes | Mobile API |
| `/compliance/*` | compliance | Yes (ministry) | Compliance reports |
| `/tiers/*` | tiers | Yes (admin) | Subscription tiers |
| `/citizen/*` | citizen_portal | Yes (citizen) | Patient portal |
| `/stats/*` | stats | Yes | Time-series analytics |
| `/mpi/*` | mpi | Yes | Master Patient Index |
| `/consent/*` | consent | Yes | Consent management |
| `/mfa/*` | mfa | Yes | Multi-factor auth |
| `/oauth2/*` | oauth2 | Yes | OAuth2/OpenID Connect |
| `/saml/*` | saml | Yes | SAML2 SP |
| `/edge/*` | edge | Yes (device) | Edge AI platform |
| `/patient-card/*` | patient_card | Yes (HMAC) | Digital patient cards |
| `/care-continuum/*` | care_continuum | Yes | Referrals, chronic disease |
| `/ai/*` | ai | Yes (rate-limited) | Clinical AI |
| `/hospital/*` | hospital | Yes | Hospital IS |
| `/nhdw/*` | nhdw | Yes | Hospital desktop |
| `/nursing/*` | nursing | Yes | Nursing platform |
| `/pharmacy/*` | pharmacy | Yes | Pharmacy platform |
| `/radiology/*` | radiology | Yes | Radiology + PACS |
| `/simulation/*` | simulation | Yes | Digital twin |
| `/governance/*` | governance | Yes (ministry) | National governance |
| `/national-data/*` | national_data | Yes | Data platform |
| `/ecosystem/*` | ecosystem | Yes (partner) | Partner ecosystem |
| `/intelligence/*` | intelligence | Yes (ministry) | National intelligence |
| `/ems/*` | ems | Yes | EMS + disaster response |
| `/blood-bank/*` | blood_bank | Yes | Blood bank |
| `/critical-care/*` | critical_care | Yes | ICU |
| `/biomedical/*` | biomedical | Yes | Biomedical engineering |
| `/public-health/*` | public_health | Yes | Disease surveillance |
| `/command-center/*` | command_center | Yes (crisis) | Health command center |
| `/pilot/*` | pilot_platform | Yes (admin) | Pilot deployments |
| `/lifecycle/*` | lifecycle_platform | Yes (admin) | Platform lifecycle |
| `/trust/*` | trust | Yes | Trust services |
| `/kernel/*` | kernel | Yes (admin) | Kernel management |
| `/knowledge-graph/*` | knowledge_graph | Yes | Knowledge graph |
| `/roadmap/*` | roadmap | Yes | Platform roadmap |

### API Contract Files

| File | Format | Purpose |
|------|--------|---------|
| `contracts/export/openapi.json` | OpenAPI 3.0 | HTTP API contract |
| `contracts/export/asyncapi.json` | AsyncAPI | Event contract |
| `contracts/export/fhir.json` | FHIR R4 | FHIR capability statement |
| `contracts/astm/protocol.json` | ASTM | Device protocol spec |
| `contracts/hl7/protocol.json` | HL7 v2 | HL7 protocol spec |
| `contracts/dto/catalog.json` | JSON | Data transfer objects |
| `contracts/events/catalog.json` | JSON | Event catalog |
| `contracts/fhir/profiles.json` | FHIR | FHIR profiles |

---

## 7. AI

### Three-Layer AI Architecture

| Layer | Location | Role | Provider Priority |
|-------|----------|------|-------------------|
| **1. Clinical Routes** | `backend/app/routes/ai.py` | Production AI inference | Ollama -> Gemini -> Groq -> none |
| **2. AI Fabric** | `backend/app/ai_fabric/` | National AI gateway | 8 providers, failover, cost optimizer |
| **3. AI Microservice** | `services/ai/main.py` | Locked to Ollama only | Hard-constrained by Executive Orders 3, 4 |

### AI Providers (Layer 2 AI Fabric)

| Provider | Models | Cost (1K in/out) | Priority |
|----------|--------|------------------|----------|
| Ollama (default) | llama3.2:1b, llama3.1:8b, mistral:7b | Free | 1 |
| Gemini | gemini-2.0-flash, gemini-2.0-pro | $0.0005/$0.0015 | 2 |
| vLLM | gula-medical-7b | Free | 3 |
| OpenAI | gpt-4o, gpt-4o-mini | $0.0025/$0.01 | 4 |
| Anthropic | claude-3-opus, claude-3-sonnet | $0.003/$0.015 | 5 |
| Groq | llama-3.1-8b-instant | Free | 6 |
| DeepSeek | deepseek-chat, deepseek-coder | $0.0005/$0.002 | 7 |
| OpenRouter | (configurable) | $0.001/$0.003 | 8 |

### AI Safety: AI = Suggest, Human = Approve, System = Enforce

```
User Request
    |
    v
PromptInjectionProtector <- 12 regex patterns
    |
    v
ai_suggest() -> AISuggestion (immutable, typed)
    |
    +-- Absolutely Blocked (10 ops) -> AIGuardrailViolation
    +-- Suggestable (7 ops) -> PendingApproval
    +-- Auto-approve (DISPLAY_ONLY)
            |
            v
    ApprovalStore
    +-- PENDING (30min TTL)
    +-- APPROVED (by human)
    +-- REJECTED
    +-- EXPIRED
            |
            v
    AISandbox.execute()
    +-- Whitelist check (dual-gate)
    +-- Audit log
    +-- Read-only execution
            |
            v
    OutputValidator -> PIIProtector -> Response
```

### Absolutely Blocked AI Operations

```
validate_order, cancel_order, modify_result, delete_patient,
create_lab_user, change_role, approve_result, write_audit_log,
export_patient_data, send_critical_alert
```

### Allowable AI Suggestions

```
suggest_interpretation, analyze_order, suggest_normal_range,
flag_anomaly, suggest_reorder, summarize_history, translate_report
```

### AI Agents (5 registered)

| Agent | Domain | Tools |
|-------|--------|-------|
| ClinicalAgent | Clinical, CDS | suggest_interpretation, analyze_clinical_pattern, suggest_reorder |
| LaboratoryAgent | Lab, QC | delta_check, qc_analysis, workload_forecast |
| SecurityAgent | Security | detect_intrusion, analyze_access_pattern, check_prompt_injection |
| EngineeringAgent | Engineering | audit_architecture, check_dependency, suggest_refactor |
| CitizenAgent | Citizen | answer_health_query, explain_result, schedule_reminder |

### AI Constitution (7 Articles)

| Article | Severity | Enforceable |
|---------|----------|-------------|
| ART-001: Patient Safety First | Critical | Yes |
| ART-002: Data Privacy | Critical | Yes |
| ART-003: Human Oversight | High | Yes |
| ART-004: Transparency | High | Yes |
| ART-005: Fairness | High | Yes |
| ART-006: Accountability | Medium | Yes |
| ART-007: Conservatism | Medium | No |

### AI Dataset Collection

| Table | Purpose | Anonymized |
|-------|---------|------------|
| `ai_interactions` | Every user-AI exchange | Yes |
| `ai_retrieval_refs` | RAG audit trail | Yes |
| `ai_feedback` | User feedback (5 signals) | Yes |
| `ai_unresolved_questions` | "Couldn't answer" log | Yes |
| `medical_terminology_normalized` | Curated medical vocabulary | Reference data |

---

## 8. Security

### Security Architecture (Defense in Depth)

```
Layer 1: Cloudflare Edge (CDN, WAF, DDoS, geo-restriction)
Layer 2: Network Perimeter (nginx gateway, rate limiting, IP blocking)
Layer 3: Zero Trust (Linkerd mTLS, service mesh policies)
Layer 4: Application (JWT, RBAC, ABAC, consent, MFA, encryption)
Layer 5: Data (encryption at rest, audit hash chain, tenant isolation)
```

### Authentication Systems

| System | Status | Details |
|--------|--------|---------|
| **JWT Access Tokens** | Active | HS256, 30min default TTL |
| **JWT Refresh Tokens** | Active | HS256, 30-day TTL, blacklist rotation |
| **OAuth2 / OpenID Connect** | Active | Auth code + PKCE, client_credentials, refresh_token |
| **SAML 2.0 SP** | Partial | Response parsing, no full IdP loop |
| **MFA / WebAuthn / FIDO2** | Active | TOTP + WebAuthn + backup codes |
| **Password Auth** | Active | bcrypt, strength validation, reset flow |
| **Service Accounts** | Active | `gula_` prefixed API keys, bcrypt hashed |

### Authorization Model

| System | Scope | Mechanism |
|--------|-------|-----------|
| **RBAC** | Platform-wide | 9 roles + 13 permissions, hierarchy 10-100 |
| **ABAC** | Fine-grained | Attribute conditions (subject, resource, environment) |
| **Consent** | Data sharing | 4-tier: owner -> lab -> break-glass -> explicit |
| **Tenant Isolation** | All patient data | `lab_id = current_user.lab_id` on every query |
| **Permission Version** | Session invalidation | `perm_ver` in JWT, Redis incremented on role change |
| **Province Scoping** | National-level | `province_admin` scoped by province_id |

### Rate Limiting

| Tier | Key | Limit |
|------|-----|-------|
| Auth | IP | 10 req/min |
| Public | IP | 30 req/min |
| User | User + IP | 60 req/min |
| Admin | User + IP | 20 req/min |
| Dynamic Block | IP | >5x limit -> 1 hour block |

### Security Invariants (non-negotiable)

1. All patient-data queries MUST filter by `lab_id = current_user.lab_id`
2. All mutations MUST write to the audit log
3. Phone lookups MUST use exact match - never LIKE with user input
4. `/metrics/prom` MUST require `Bearer METRICS_BEARER_TOKEN`
5. `system_ready` MUST stay False until DB confirmed reachable
6. `version` column MUST be checked on every `LabResult` mutation
7. Secrets have no hardcoded fallbacks
8. `patients.national_id` MUST be encrypted at rest
9. Patient card HMAC tokens MUST be verified before data returned

### Security Test Coverage (107+ dedicated tests)

| Area | Tests | Key Patterns Tested |
|------|-------|---------------------|
| JWT | 26+ | Expiry, type confusion, algorithm "none", tampering |
| RBAC | 20+ | Permission mapping, header override, mass assignment |
| ABAC | 8 | Allow/deny, conditions, priority |
| Consent | 8 | All 5 rules + expiration + break-glass |
| Rate limit | 10 | Allow/block thresholds, IP extraction |
| MFA | 15 | TOTP setup/verify, WebAuthn, device mgmt |
| Risk auth | 16 | 11 factors, 4 outcomes, decision logging |
| Idempotency | 10 | Duplicate detection, TTL, lab scoping |

---

## 9. Healthcare

### Healthcare Domains Covered

| Domain | Implementation | Status |
|--------|---------------|--------|
| Clinical Notes | `backend/app/clinical/` | Active |
| Clinical Orders | `backend/app/routes/clinical_orders.py` | Active |
| Clinical Documentation | `backend/app/routes/clinical_documentation.py` | Active |
| Clinical Quality | `backend/app/routes/clinical_quality.py` | Active |
| Clinical Decision Support | `backend/app/clinical/cds/` | Active |
| Terminology (ICD10/11, SNOMED, LOINC) | `backend/app/clinical/terminology/` | Active |
| Care Continuum | `backend/app/routes/care_continuum.py` | Active |
| EHR (FHIR R4 compatible) | `backend/app/ehr/` | Active |
| Patient Card (QR) | `backend/app/routes/patient_card.py` | Active |

### FHIR R4 Coverage

14 FHIR resources implemented: Patient, Encounter, Condition, Observation, DiagnosticReport, ServiceRequest, MedicationRequest, MedicationStatement, CarePlan, Procedure, AllergyIntolerance, Immunization, DocumentReference, Composition, Bundle

---

## 10. Public Health

### Public Health Platform (`backend/app/public_health/`)

**MISSION-032:** National Public Health & Disease Surveillance Platform

### Capabilities

| Capability | Models/Modules | Status |
|------------|---------------|--------|
| Disease Case Management | `DiseaseCaseModel` | Active |
| Outbreak Detection | `OutbreakAlertModel`, `OutbreakDetector` | Active |
| Surveillance Signals | `SurveillanceSignalModel` | Active |
| Immunization Records | `ImmunizationRecordModel` | Active |
| Public Health Reports | `PublicHealthReportModel` | Active |
| Environmental Health | `EnvironmentalHealthModel` | Active |
| Predictive Outbreak (Frontend) | `PredictiveOutbreak.tsx` | Active |

### Z-Score Alerting

| Z-Score | Alert Level |
|---------|-------------|
| z >= 5 | CRITICAL |
| z >= 3 | OUTBREAK |
| z >= 2 | WARNING |

---

## 11. Laboratory

### LIMS Domain

**Primary Production Path:** `backend/app/lims/` + `backend/app/models/` + `backend/app/routes/results.py`

**Full LIMS Model Coverage (42 tables):** Orders, Results, Samples, Specimens, Panels, Instruments, QC (IQC, EQA, Westgard), Reagents, Calibration, Transportation, Workflow, Chain of Custody, Reports

### Device Bridge (`services/device_bridge/`)

| Aspect | Detail |
|--------|--------|
| **Protocols** | ASTM (full ENQ/ACK/EOT), HL7 v2 |
| **Vendors** | Sysmex, Roche, Mindray, Generic |
| **Connectors** | Serial (pyserial), TCP (raw sockets) |
| **Architecture** | 14 sub-packages, vendor adapters (Strategy pattern) |
| **Modes** | local_only, hybrid, cloud_only |
| **Offline** | EdgeAgentBuffer + SyncEngine with version reconciliation |
| **Port** | 8200 (Docker, profile: device-bridge) |

### QC / Westgard Rules

| Rule | Description |
|------|-------------|
| 1-2s | 1 control > 2 SD from mean |
| 1-3s | 1 control > 3 SD (reject) |
| 2-2s | 2 consecutive > 2 SD same side |
| R-4s | 2 consecutive > 4 SD difference |
| 4-1s | 4 consecutive > 1 SD same side |
| 10x | 10 consecutive same side of mean |

---

## 12. Radiology

### Radiology Information System & PACS (`backend/app/radiology/`)

**MISSION-028:** National Radiology Information System & PACS

### Modules

| Module | Purpose |
|--------|---------|
| `models.py` | 18 ORM models (DICOM, exams, reports, appointments) |
| `routes.py` | Full CRUD + workflows |
| `dicom.py` | DICOM storage + metadata extraction |
| `ai.py` | AI Analysis Jobs, model registry (9 models), triage, human approval |

### AI Models Registered (9)

| Model | Modality | Criticality |
|-------|----------|-------------|
| chest-xray-abnormality | XR | Actionable |
| chest-xray-critical | XR | Critical Red |
| ct-brain-hemorrhage | CT | Critical Red |
| ct-pulmonary-embolism | CT | Critical |
| mri-brain-tumor | MRI | Actionable (Beta) |
| mammography-density | MG | Non-critical |
| chest-xray-quality | XR | Non-critical |
| ct-pneumothorax | CT | Critical Red |
| us-renal-stone | US | Actionable |

---

## 13. Pharmacy

### Pharmacy Information Platform (`backend/app/pharmacy/`)

**MISSION-027:** National Pharmacy Information Platform

### Capabilities

| Module | Models | Status |
|--------|--------|--------|
| Drug Catalog | `DrugCatalog`, `DrugBatch` | Active |
| Inventory | `StockLevel`, `StockMovement`, `Store`, `Warehouse` | Active |
| Prescriptions | `Prescription`, `PrescriptionItem` | Active |
| Dispensing | `DispenseQueue`, `DispenseRecord` | Active |
| Returns/Waste | `DrugReturn`, `WasteRecord` | Active |
| Interactions | `DrugInteractionRule`, `ContraindicationRule`, `AllergyRule` | Active |
| Dosing | `DoseGuideline`, `DrugMonitoring` | Active |
| Recalls | `Recall` | Active |
| Forecasting | `InventoryForecast` | Active |

---

## 14. Dentistry

**Status: Not yet implemented** as a dedicated module.

Dental services would be covered under general clinical documentation, orders, and encounter models. No separate `dentistry/` module exists in the codebase. Dentistry is acknowledged in the global healthcare discovery docs (`docs/discovery/GLOBAL_MEDICAL_SPECIALTIES.md`) but no dedicated routing, models, or clinical logic exists in production code.

---

## 15. Nursing

### Nursing & Care Coordination Platform (`backend/app/nursing/`)

**MISSION-026:** National Nursing & Care Coordination Platform

### Capabilities

| Module | Models | Status |
|--------|--------|--------|
| Nursing Notes | `NursingNote` | Active |
| Shifts | `NursingShift`, `ShiftHandover` | Active |
| Tasks | `NursingTask` | Active |
| Patient Assignment | `PatientAssignment` | Active |
| Care Plans | `NursingCarePlan` | Active |
| Checklists | `ClinicalChecklist`, `DailyChecklistModel` | Active |
| Delegation | `Delegation` | Active |
| Escalations | `EscalationRecord` | Active |
| Assessments | `FallRiskAssessment`, `PainAssessment`, `NutritionAssessment`, `PressureInjuryAssessment` | Active |

---

## 16. Hospital

### Hospital Information System (`backend/app/hospital/` + `backend/app/nhdw/`)

**MISSION-025:** National Hospital Desktop Workspace (NHDW)

**Hospital Models:** HospitalMaster, Campus, Building, Floor, Unit, Room, Bed, BedAssignment, Clinic, HospitalDepartment, OperationTheater, MedicalEquipment, CostCenter

**NHDW Models:** Admission, Discharge, Transfer, WardRound, CarePlan, ClinicalTask, QueueEntry, TelemedicineSession, ResourceSchedule, ShiftReport, DashboardConfiguration, WaitingListEntry, HospitalMessage, HospitalAlert

### Hospital Workspace Docs

| Document | Purpose |
|----------|---------|
| `docs/hospital-workspace/ARCHITECTURE.md` | Architecture |
| `docs/hospital-workspace/ADR.md` | Design decisions |
| `docs/hospital-workspace/OPERATIONS.md` | Operations |
| `docs/hospital-workspace/DEPLOYMENT.md` | Deployment |

---

## 17. Citizen

### Citizen Digital Health Platform (`backend/app/citizen_platform/`)

**MISSION-019:** National Citizen Super App

### Citizen-Facing Features

| Feature | Implementation | Purpose |
|---------|---------------|---------|
| Dashboard | `CitizenDashboard.tsx` | Health overview |
| Health Profile | `CitizenHealth.tsx` | Medical history |
| AI Assistant | `CitizenAssistant.tsx` | Symptom checker, health queries |
| Family Management | `FamilyManagement.tsx` | Dependents/guardians |
| Medication Center | `MedicationCenter.tsx` | Current meds, reminders |
| Medical History | `MedicalHistoryView.tsx` | Longitudinal record |
| Smart Results | `SmartResultsView.tsx` | Interpreted results |
| Registration | `PatientRegistration.tsx` | Self-registration |
| Identity Verification | `IdentityVerificationView.tsx` | National ID verification |
| Consent Management | `ConsentManagementView.tsx` | Data sharing preferences |
| Security Audit | `SecurityAuditView.tsx` | Access history |

### Arabic-First Design

All patient-facing content in Arabic by default. Clinical terminology in Iraqi-Arabic dialect. AI explanations in Arabic with medical disclaimers.

---

## 18. Ministry

### Ministry Command Centre / National Oversight

### Ministry Views (frontend-v2)

| View | Purpose |
|------|---------|
| MinistryDashboard | High-level national health metrics |
| NationalHealthGrid | Real-time national health status |
| EpidemiologicalIntelligence | Disease surveillance + outbreak detection |
| DataSovereigntyAudit | Privacy and compliance monitoring |
| CrisisResponsePipeline | Emergency management |
| MinistryCommandCenter | National oversight command center |

### Governance Layer (`backend/app/governance/`)

| Module | Purpose |
|--------|---------|
| `routes/` | Governance API endpoints |
| `analytics/` | National health analytics |
| `policies/` | Policy enforcement |
| `audit/` | National audit aggregation |

---

## 19. Government

### Government Integration

### SNDHS-lite Phase 1

| Feature | Status | Details |
|---------|--------|---------|
| National ID collection | Complete | Encrypted at rest (AES-256) |
| Health ID assignment | Complete | SNDHS-assigned |
| Visit tracking | Complete | Flag-gated (`SNDHS_ENABLE_VISITS`) |
| Enhanced audit log v2 | Complete | Additional SNDHS correlation fields |
| Backfill script | Complete | `scripts/sndhs_phase1_backfill.py` |
| Rollback script | Complete | `scripts/sndhs_phase1_rollback.sql` |
| Migration files | Complete | 6 migration files |
| Spec docs | Complete | 22 files in `docs/sndhs/` |

### Government Adapters (`backend/app/gateways/mode.py`)

| Adapter | Modes | Endpoint |
|---------|-------|----------|
| MoI NID (National ID) | stub/live/shadow | `MOI_NID_API_URL` |
| Insurance (NHI) | stub/live/shadow | `INSURANCE_API_URL` |
| Residency (MoI) | stub/live/shadow | `RESIDENCY_API_URL` |
| Cloudflare | stub/live/shadow | `CF_API_TOKEN` |

---

## 20. Infrastructure

### Infrastructure Stack

| Component | Technology | HA Strategy |
|-----------|------------|-------------|
| **Reverse Proxy** | nginx (api-gateway) | Multi-replica behind HAProxy |
| **Load Balancer** | HAProxy | leastconn, slow-start |
| **Application** | FastAPI (gunicorn + uvicorn) | Multi-worker, HPA |
| **Database** | PostgreSQL 16 | Patroni HA, streaming replication, PgBouncer |
| **Cache** | Redis 7 | Sentinel HA, cluster mode |
| **Messaging** | RabbitMQ | Clustered, mirrored queues |
| **Streaming** | Kafka (dev) | - |
| **Analytics** | ClickHouse | - |
| **Object Store** | MinIO | Distributed, erasure coding |
| **Monitoring** | Prometheus + Grafana | Federation, VictoriaMetrics |
| **Logging** | Loki + Promtail | - |
| **Tracing** | Tempo + OTel Collector | - |
| **Alerting** | Alertmanager | PagerDuty, Slack, Email |
| **Secrets** | Vault (planned) | - |

### Observability Stack

| Tool | Config Path | Purpose |
|------|-------------|---------|
| Prometheus | `config/prometheus/` | Metrics, 30+ alert rules |
| Grafana | `config/grafana/` | Provisioned dashboards |
| Loki | `config/loki/` | Log aggregation (168h) |
| Tempo | `config/tempo/` | Distributed tracing (48h) |
| OTel Collector | `config/opentelemetry/` | Trace/metric/log pipeline |
| Alertmanager | `config/alertmanager/` | Severity-based routing |

### Prometheus Alert Rules (3 rule files, 35+ alerts)

- **SLO Recording**: Availability, DB health, Redis health, queue pressure
- **Availability**: BackendDown (crit), DatabaseDown (crit), RedisDown (warn)
- **Performance**: DatabaseSlow/verySlow, RedisSlow
- **Capacity**: HighConcurrency, HighMemory, OrderBacklog
- **Infrastructure**: DiskSpaceWarning/Critical, HighSystemMemory, HighCPU
- **Database**: PostgresConnectionsHigh, 7 DB error-type alerts
- **SLO Burn Rate**: 99.99% availability target, burn rate tracking

---

## 21. Kubernetes

### Deployment Structure

**Namespace:** `gula` with Linkerd auto-injection

**Base manifests** (`k8s/base/`): 30+ resources covering backend, frontend, gateway, postgres, redis, rabbitmq, 7 microservices, mesh (Linkerd)

**Overlays** (`k8s/overlays/`):
- `dev/` - 1 replica per service, API docs enabled
- `prod/` - 5 backend replicas, 3 frontend, HPA (5-8)
- `region-me/` - Middle East labels + topology spread
- `region-eu/` - Europe labels + topology spread

### Scaling Configuration

| Deployment | Min | Max | Metric |
|-----------|-----|-----|--------|
| gula-backend (prod) | 5 | 8 | CPU 70%, Mem 80% |
| Microservices (7) | 2 | 6 | CPU 70% |
| notification/AI | 1 | 3 | CPU 70% |

### Security Context

- All pods: `runAsNonRoot: true`, dropped capabilities
- Init containers: wait-for-postgres, wait-for-redis, wait-for-rabbitmq
- Health probes: liveness + readiness on `/health`
- Image pull: `ghcr-credentials` secret

### Helm Chart (`helm/gula-platform/`)

- 9 dependency charts (Bitnami: postgresql, redis, rabbitmq, minio; Prometheus, Grafana, Loki, Tempo, Linkerd2)
- Comprehensive values.yaml (1326 lines)
- Patroni HA, Redis Sentinel (3 replicas, quorum 2), RabbitMQ cluster (3 nodes), MinIO distributed (4 nodes, 100Gi each)

---

## 22. Docker

### Primary Stack (`docker-compose.yml`)

| Service | Image | Ports | Role |
|---------|-------|-------|------|
| postgres | `postgres:16-alpine` | Internal 5432 | Primary DB |
| redis | `redis:7-alpine` | Internal 6379 | Cache |
| gula-backend | Local/GHCR | Internal 8000 | FastAPI |
| gula-worker | Local/GHCR | Internal | Background |
| frontend | `nginx:1.25-alpine` | Internal 80 | Static files |
| api-gateway | `nginx:1.25-alpine` | `127.0.0.1:8080` | Reverse proxy |

### Full Stack (`docker-compose.full.yml`)

PostgreSQL primary + replica + PgBouncer, Redis + replica + Sentinel, RabbitMQ + Zookeeper + Kafka, Ollama + AI service, MinIO, Keycloak + Vault (optional), Prometheus + Grafana + Loki + Jaeger + OTel, 8 microservices, backup-cron

### Security

- `no-new-privileges: true` on all services
- Only `api-gateway:8080` bound to `127.0.0.1`
- Env var validation (`:?variable must be set`)
- Non-root application user (`appuser`)
- Resource limits (memory + CPU)

---

## 23. Terraform

**Location:** `terraform/`

### Structure

```
terraform/
├── modules/                    # 12 reusable modules
│   ├── vpc/, eks/, rds/, elasticache/
│   ├── rabbitmq/, ecr/, s3/, iam/
│   ├── monitoring/, networking/, security/, dr/
├── environments/
│   ├── prod/                   # Full production
│   ├── staging/                # Pre-production
│   ├── dr/                     # Disaster recovery (reduced)
│   ├── dev/                    # Development
│   └── management/             # CI/CD runner
```

### AWS Resources (Production)

| Resource | Specification |
|----------|---------------|
| VPC | 3 AZs, NAT gateways per AZ, VPC endpoints |
| EKS | System (3-5 m5.xlarge), App (5-20 m5.xlarge), Spot (5-20 c5.xlarge) |
| RDS | `db.r6g.xlarge`, 500GB, auto-scaling to 2TB, Multi-AZ |
| ElastiCache | `cache.r6g.xlarge`, 3 nodes, cluster mode |
| ALB | Cross-zone, WAF, CloudFront CDN |
| Route53 | Health checks, failover routing, 60s TTL |

---

## 24. CI/CD

### CI Pipeline (`.github/workflows/ci.yml`)

```
Syntax Gate -> Migration Check -> OpenAPI Contract
    |               |
    +---------------+---> Smoke Test -> Backend Test -> Security Scan
                                |
                                +---> Build & Push (8 images) -> Image Summary
```

| Job | Time | Blocks? | Tools |
|-----|------|---------|-------|
| `syntax-gate` | <30s | Yes | py_compile, flake8 (E9, F821) |
| `migration-check` | ~60s | No | alembic upgrade head + round-trip |
| `openapi-contract` | ~30s | No | Export OpenAPI, validate endpoints |
| `smoke-test` | ~60s | No | uvicorn boot + curl health |
| `backend-test` | ~5min | No | pytest tests/ (PG + Redis) |
| `security-scan` | ~2min | No | safety, bandit, hadolint, gitleaks |
| `build-and-push` | ~10min | Yes | Buildx + GHCR, Trivy scan |

### Deploy Pipeline

- SSH into server, pull code, preserve `.env`, auto-generate missing secrets
- Pull pre-built GHCR images, `docker compose up`
- Health check with 3-minute retry window, **auto-rollback** on failure

### Blue-Green / Canary Deploy

- K8s-based: active/passive slot switching via service selector + Linkerd TrafficSplit
- Canary: progressive traffic (10% -> 25% -> 50% -> 100%)

### Quality Gates (9 parallel)

Architecture, Performance, Security, Database, API, FHIR, Scalability, Accessibility, Offline

---

## 25. GitHub

### Configuration

| File | Purpose |
|------|---------|
| `.github/dependabot.yml` | Weekly dependency updates |
| `.github/workflows/ci.yml` | CI pipeline |
| `.github/workflows/deploy.yml` | Production deployment |
| `.github/workflows/blue-green-deploy.yml` | Blue-green deployment |
| `.github/workflows/canary-deploy.yml` | Canary deployment |
| `.github/workflows/auto-rollback.yml` | Automatic rollback |
| `.github/workflows/quality-gate.yml` | Quality gate checks |

---

## 26. Documentation

### Documentation Inventory

| Category | Location | Content |
|----------|----------|---------|
| **Engineering Constitution** | `CLAUDE.md` | Root authority, core principles |
| **ADRs** | `docs/adr/` | 25 ADRs (ADR-001 through ADR-025) |
| **National Health Domain** | `docs/national/` | EHR, API catalog, FHIR, clinical model, security, workflows |
| **Production Operations** | `docs/production/` | 8 guides (DR, incident, scaling, etc.) |
| **Sovereign Infrastructure** | `docs/sovereign/` | 10 docs for phases 16-25 |
| **SNDHS Phase 1** | `docs/sndhs/` | 22 files covering full spec |
| **Engineering Foundation** | `docs/engineering/` | Blueprint, decisions, debt, risk, quality gates |
| **Runbooks** | `docs/runbooks/` | 7 incident runbooks |
| **Architecture** | `architecture/` | 24 files (master, domain, service, data flow, security) |
| **Contracts** | `contracts/` | OpenAPI, AsyncAPI, FHIR, ASTM, HL7 |

### Key Missing Documents

- No dedicated Dentistry module documentation
- No Digital Wallet documentation
- Plugin System has ADR but no developer guide
- Marketplace concept undocumented
- SDK specification not found
- No postmortems directory

---

## 27. Testing

### Test Inventory

| Area | Files | Tests |
|------|-------|-------|
| **Backend (pytest)** | 44 standalone + 4 subdirectory groups | 1505+ |
| **Kernel** | `tests/kernel/` (45 files) | Comprehensive |
| **Kernel Hardening** | `tests/kernel_hardening/` (7 files) | Chaos, stress, security |
| **Integration** | `tests/integration/` | Connector registry, SDK |
| **Identity** | `tests/identity/` (3 files) | Domain, governance, service |
| **Chaos** | `tests/chaos/` | Infrastructure chaos |
| **Load/Stress** | `tests/load/` | k6, Locust, custom Python |
| **Contracts** | `contracts/compatibility/` | API contract compliance |

### Top Test Files by Complexity

| File | Lines | Purpose |
|------|-------|---------|
| `test_comprehensive.py` | 860 | Full integration |
| `test_governance.py` | 910 | National Governance Layer |
| `test_system_improvements.py` | 716 | Interpretation engine |
| `test_national_notification_platform.py` | 712 | Notification platform |
| `test_control_layer.py` | 536 | PolicyEngine, DecisionGuard, RiskEngine |
| `test_resilience.py` | 488 | Beta-launch resilience |
| `test_hard_scenarios.py` | 482 | 5 production break scenarios |
| `test_tenant_isolation_matrix.py` | 480 | Parametric isolation sweep |
| `test_stress.py` | 481 | Concurrency + race conditions |
| `test_compliance_integrity.py` | 465 | Audit chain, FHIR R4 |

### Assessment Grades

| Dimension | Grade | Key Finding |
|-----------|-------|-------------|
| Architecture | B | Clean monolith layering |
| Backend | B | Well-organized FastAPI |
| Frontend | C | Two frontends, coverage gap |
| Security | B | No critical findings |
| Database | B | Sound migration policy |
| Testing | C+ | 54% coverage, fixture issues |
| Performance | C | Framework exists, baselines needed |
| Compliance | C | SNDHS Phase 1, framework partial |
| Deployment | B | Docker Compose + CI/CD |
| Documentation | C+ | Engineering docs strong, gaps elsewhere |
| Operations | C | Monitoring stack, runbooks partial |
| Governance | B | Constitution + ADR process |

### Known Technical Debt

| ID | Issue | Score | Impact |
|----|-------|-------|--------|
| D-001 | 268 test fixture errors | 20 Critical | CI reliability |
| D-002 | 1413 mypy strict errors | 15 Critical | No static typing |
| D-003 | Route coverage ~35% | 16 Critical | Regression risk |
| D-004 | 50 RUSTSEC advisories | 16 Critical | Security debt |
| D-005 | Lock file inconsistency | 12 High | Build reproducibility |

---

## 28. Benchmark

### Benchmark Files

| File | Location | Purpose |
|------|----------|---------|
| `benchmarks.py` | `contracts/quality/` | Performance benchmarks |
| `benchmark-results.json` | `contracts/quality/` | Stored results |
| `benchmark-report.md` | `contracts/quality/` | Benchmark report |
| `test_performance_budgets.py` | `backend/tests/` | Query-count budgets, N+1 detection |
| `test_stress.py` | `backend/tests/` | Stress test benchmarks |

### SLO Targets

| SLO | Target |
|-----|--------|
| Availability | 99.99% |
| p99 Latency | <500ms |
| Error Budget Burn | 5%/hour (critical) |
| RPO | 5 seconds |
| RTO | 5 minutes |

### Performance Testing

| Test | Tool | Scenario |
|------|------|----------|
| Load | k6, Locust | Full lab workflow |
| Stress | Custom Python | Ramp: 1u -> 500u -> recovery |
| Soak | Custom script | Long-duration stability |
| Spike | Custom script | Sudden traffic spikes |
| Database | `test_performance_budgets.py` | N+1 detection, query budgets |

---

## 29. Disaster Recovery

### DR Strategy: Active-Passive Multi-Region

| Region | Location | Role | Provider |
|--------|----------|------|----------|
| Primary | Baghdad (me-central1) | Active | DigitalOcean |
| DR | Frankfurt (eu-west1) | Standby | DigitalOcean (alt) |

### Replication

| Component | Method | RPO |
|-----------|--------|-----|
| PostgreSQL | Synchronous streaming | 5s |
| Redis | Sentinel-based (no cross-region) | Ephemeral |
| RabbitMQ | Shovel (async) | Near real-time |
| MinIO | Bucket replication (async) | Near real-time |
| WAL | pgBackrest to S3 | 5min |

### Backup Strategy

| Frequency | Method | Retention |
|-----------|--------|-----------|
| Hourly | Incremental pg_dump | 2 days |
| Daily | Full pg_dump compressed | 30 days |
| AWS | Automated backups | 35 days, cross-region |
| WAL | pgBackrest to S3 | PITR capable |

### DR Runbooks

| Runbook | File |
|---------|------|
| Backend Down | `docs/runbooks/backend-down.md` |
| Database Down | `docs/runbooks/database-down.md` |
| Disk Full | `docs/runbooks/disk-full.md` |
| Failed Deployment | `docs/runbooks/failed-deployment.md` |
| High Latency | `docs/runbooks/high-latency.md` |
| Security Incident | `docs/runbooks/security-incident.md` |
| Certificate Expiry | `docs/runbooks/certificate-expiry.md` |

---

## 30. Compliance

### Regulatory Framework

| Framework | Status | Implementation |
|-----------|--------|---------------|
| **Iraqi Data Protection Law** | In progress | Encryption, consent, audit |
| **Ministry of Health Guidelines** | In progress | Clinical guardrails, tenant isolation |
| **SNDHS-lite Phase 1** | Complete | 22 spec docs, backfill, rollback |
| **FHIR R4** | Active | 14 resource types |
| **HL7 v2.x** | Active | Device bridge |
| **ISO 15189** (Medical Labs) | Planned | QC, EQA, IQC |
| **ISO 27001** (Info Security) | Base | Encryption, RBAC, audit |
| **ISO 27799** (Health Informatics) | Base | Patient data protection |
| **NIST SP 800-53** | Base | Security controls |
| **CLSI Standards** | Partial | Westgard rules, reference ranges |

### Compliance Documents

| Document | Location |
|----------|----------|
| Compliance Framework | `architecture/14-compliance-framework.md` |
| Government Readiness | `docs/engineering/GOVERNMENT-READINESS.md` |
| Digital Constitution | `docs/engineering/DIGITAL-CONSTITUTION.md` |
| Platform Constitution | `docs/constitution/PLATFORM-CONSTITUTION.md` |
| Sovereign Invariants | `docs/sovereign/SOVEREIGN_INVARIANTS.md` |
| Standards Mapping | `docs/sovereign/STANDARDS_MAPPING_MATRIX.md` |

### Compliance Tests

| Test File | Coverage |
|-----------|----------|
| `test_compliance_integrity.py` | Audit chain, FHIR R4, DHIS2 |
| `test_governance.py` | 12 phases of governance |
| `test_consent.py` | Consent layer compliance |
| `test_tenant_isolation_matrix.py` | Tenant isolation sweep |

---

## 31. Accessibility

**Status:** Partial

### Features

- Arabic-first UI with full RTL support
- Keyboard navigation (Cmd+K, vim-style chords, Home/End/Up/Down/Escape)
- Screen reader support (semantic HTML, ARIA labels - partial)
- High contrast (Tailwind theme)
- Font support: Outfit (Arabic), Inter (Latin), JetBrains Mono (code)

### Quality Gate

- `config/quality-gates/accessibility` - WCAG compliance check (Node.js)
- Part of quality gate pipeline on PR to main

### Gaps

- No dedicated accessibility audit document
- WCAG 2.1 AA compliance not formally verified
- Screen reader testing not documented

---

## 32. Localization

### Language Support

| Language | Code | Direction | Coverage |
|----------|------|-----------|----------|
| English | `EN` | LTR | **Full** (650+ keys) |
| Arabic | `AR` | RTL | **Full** (650+ keys, medical terminology adapted) |
| Kurdish | `KU` | RTL | Partial (keys defined, strings placeholder) |
| Turkmen | `TR` | RTL | Partial (keys defined, strings placeholder) |
| Syriac | `SY` | RTL | Partial (keys defined, strings placeholder) |

### Translation Architecture

- Single `translations.ts` file with `Translation` interface (650+ keys)
- Type-safe `Record<Language, Translation>` mapping
- `LanguageContext` manages state, sets `dir` and `lang` on `<html>`
- Components access via `useLanguage().t` (e.g., `t.dashboard`)
- RTL-aware layout utilities

### AI Language Support

- Clinical interpretations in Arabic, English, Iraqi-Arabic
- AI system instructions are Arabic-first
- Medical disclaimer always in Arabic
- Fallback chain preserves language context

---

## 33. Offline

### Offline Capabilities

| Component | Offline Strategy | Implementation |
|-----------|-----------------|----------------|
| **Frontend** | Firestore IndexedDB | `enableIndexedDbPersistence()` |
| **Frontend Mutations** | Offline queue | `SyncService` (localStorage, auto-process) |
| **Frontend Optimistic** | Optimistic updates | `useOptimisticAction()` |
| **Device Bridge** | Edge agent buffer | `EdgeAgentBuffer` + `SyncEngine` |
| **Device Bridge Modes** | local_only, hybrid, cloud_only | Per-device policy |
| **Identity** | Offline sync engine | CRDT-compatible vector clocks |
| **AI** | Local inference (Ollama) | Full offline AI operation |

### Offline Data Flow (Device Bridge)

```
Physical Device -> Serial/TCP -> EdgeAgentBuffer (local queue)
    |                              |
    | (cloud_only/hybrid)     (local_only/hybrid)
    |                              |
GulaClient -> Monolith        SyncEngine -> batch sync -> GulaClient -> Monolith
```

---

## 34. Synchronization

### Sync Mechanisms

| System | Protocol | Conflict Resolution |
|--------|----------|---------------------|
| **Frontend <-> Firestore** | Real-time onSnapshot | Last-write-wins |
| **Device Bridge <-> Monolith** | HTTP REST | Version-based, MAX_ATTEMPTS |
| **Offline Identity** | CRDT vectors | Vector clocks + encrypted store |
| **DB Replication** | WAL streaming (sync) | PostgreSQL built-in |
| **Cache** | Redis replication (async) | Sentinel failover |
| **Events** | RabbitMQ (persistent) | Durable queues |
| **Analytics** | ClickHouse HTTP + Kafka | JSONEachRow |
| **DR** | WAL shipping + async bucket | 5s RPO target |

### Sync Conflicts Handled

- **Identity merge**: Fellegi-Sunter scoring -> proposal -> human approval
- **Optimistic locking**: `version` column on LabResult and LabOrder
- **Idempotency**: `Idempotency-Key` header with 24h TTL
- **State machine**: Order state machine prevents invalid transitions
- **Outbox**: Exactly-once delivery via transactional outbox

---

## 35. Scalability

### Horizontal Scaling Mechanisms

| Mechanism | Configuration | Limits |
|-----------|--------------|--------|
| **Docker Compose** | `BACKEND_REPLICAS` (default 3) | HAProxy leastconn |
| **Kubernetes HPA** | 2-10 pods (prod: 5-8) | CPU 70%, Memory 80% |
| **Microservices HPA** | 2-6 pods per service | CPU 70% |
| **Database** | Read replicas + PgBouncer | Default 54 connections |
| **Cache** | Redis Cluster (6 shards) | 3 primary + 3 replica |
| **DigitalOcean** | 1-3 instances | CPU 75% threshold |

### Concurrency Budget

```
WEB_CONCURRENCY x (DB_POOL_SIZE + DB_MAX_OVERFLOW) < postgres.max_connections
Default: 3 x (6 + 12) = 54 < 100 (PostgreSQL default)
```

### Adaptive Concurrency

- Polls DB latency every 30s
- 2 slow readings (>300ms): halve `_MAX_CONCURRENT`
- 3 fast readings (<150ms): restore original
- Clinical writes always exempt

---

## 36. Reliability

### Reliability Architecture

| Layer | Mechanism | MTTR Target |
|-------|-----------|-------------|
| **Application** | Circuit breaker (DB/Redis) | 30s auto-recovery |
| **Application** | DegradedModeMiddleware | Instant (next request) |
| **Application** | ReadinessMiddleware | Replica creation |
| **Application** | ConcurrencyLimitMiddleware | Instant (503) |
| **Background** | Auto-repair (GC, pool recycle) | 30s-60s |
| **Background** | RecoveryWorker | 30s probe cycle |
| **Infrastructure** | Docker healthcheck | 30s interval |
| **Infrastructure** | K8s liveness/readiness | 30s, restart on failure |
| **Database** | Patroni HA | <30s failover |
| **Cache** | Redis Sentinel | <10s failover |
| **Load Balancer** | HAProxy health checks | 2s interval |
| **DNS** | Route53 failover | 60s TTL |

### Self-Healing Hierarchy (3 layers)

1. **Circuit Breaker** - isolates failing DB/Redis, flips to degraded mode
2. **Auto-Repair Engine** - GC, pool recycle, reconnects
3. **Adaptive Concurrency** - halves MAX_CONCURRENT on slow DB

### Degradation Levels

| Level | Effect | Trigger |
|-------|--------|---------|
| `NONE` | Normal operations | - |
| `L1_CACHE_HEAVY` | Reads prefer cache, writes warn | DB timeouts >5/5min |
| `L2_READ_ONLY` | All mutations rejected | DB refused >20/5min |
| `L3_CRITICAL_ONLY` | Health/auth/kill-switch only | DB refused >50/5min |

### Autonomous Manager

- Monitors 10 services every 15s
- 3 consecutive failures on critical -> `docker restart`
- 60s cooldown, non-critical logged only

---

## 37. Performance

### Performance Budgets

| Operation | Budget | Enforcement |
|-----------|--------|-------------|
| DB query count per endpoint | Configurable | `test_performance_budgets.py` |
| DB query latency (p95) | <200ms (GREEN), >500ms (YELLOW) | Health alert loop |
| Redis latency (p95) | <50ms (GREEN), >100ms (YELLOW) | Health alert loop |
| API response >2000ms | Warning log | RequestTimingMiddleware |
| API p99 latency | <500ms (SLO) | Prometheus rules |
| Memory per process | <600MB GREEN, >800MB YELLOW | Health alert loop |

### Query Optimization

| Optimization | Location | Impact |
|-------------|----------|--------|
| Connection pooling | `database.py` | Reduces connection overhead |
| Read replicas | `READ_REPLICA_URL` | Distributes read load |
| Statement timeout (30s) | `database.py` | Prevents runaway queries |
| work_mem (16MB) | `database.py` | Limits sort/hash memory |
| L1/L2 caching | `core/cache_manager.py` | Multi-level cache |

---

## 38. Clinical Safety

### Clinical Safety Principles

1. **AI = Suggest. Human = Approve. System = Enforce.**
2. AI may never write to clinical state
3. Clinical write operations exempt from concurrency shedding
4. Critical values always require alerts
5. Validated orders are immutable
6. State machine prevents medical safety violations
7. Technicians cannot validate orders
8. Break-glass requires mandatory audit trail
9. Tenant isolation prevents cross-lab contamination

### Critical Thresholds (Essential Analytes)

| Analyte | Unit | Low | High |
|---------|------|-----|------|
| Glucose | mg/dL | 70 | 140 |
| Potassium | mmol/L | 3.5 | 5.2 |
| Sodium | mmol/L | 135 | 145 |
| Calcium | mg/dL | 8.5 | 10.5 |
| Hemoglobin | g/dL | 12.0 | 16.0 |
| WBC | x10^3/uL | 4.0 | 11.0 |
| Platelets | x10^3/uL | 150 | 450 |
| Troponin | ng/mL | - | 0.04 |
| INR | ratio | - | 1.2 (4.0 critical) |
| Lactate | mmol/L | - | 2.0 |

### Clinical Safety Tests (`test_clinical_safety.py`)

- CriticalThresholdsIntegrity: All essential analytes present, valid bounds
- CheckCriticalBoundaries: At-threshold, below, normal, above
- CriticalAlertMessages: Bilingual messages
- ClinicalSignoffAuthority: Technician blocked, admin can validate
- AIClinicalBoundary: 10 blocked operations
- OptimisticLocking: version columns exist
- StateMachineMedicalSafety: No backward transitions

---

## 39. Privacy

### Privacy Architecture

| Protection | Implementation |
|------------|---------------|
| Patient names | Encrypted at rest via Fernet |
| National IDs | Encrypted at rest (AES-256-CBC + HMAC-SHA256) |
| Phone numbers | Exact match only, no LIKE |
| AI datasets | No PII columns |
| Logging | Structured JSON, PII stripped |
| Telemetry | Property blacklist, no PII sent |
| Audit | Hash chain prevents tampering |

### Data Classification

| Classification | Examples | Protection |
|---------------|----------|------------|
| Public | Test types, reference ranges | No restrictions |
| Internal | Lab names, aggregated stats | Auth required |
| Confidential | Patient demographics | Encryption + tenant isolation |
| Restricted | National IDs, diagnoses | Encryption + ABAC + consent |
| Sensitive | Mental health, HIV, genetics | Explicit consent + separate encryption |

### Retention

| Data Type | Retention |
|-----------|-----------|
| Clinical records | 25 years |
| Lab results | 10 years |
| Audit logs | 7 years |
| Session data | 24 hours |

---

## 40. Digital Identity

### Identity Architecture (3 Tiers)

```
Tier 3: Government Identity (MoI NID, national ID, biometric)
    |
Tier 2: National MPI (citizens table, 48M scale, Fellegi-Sunter)
    |
Tier 1: Application Identity (JWT tokens, lab users, patients)
```

### Master Patient Index (`backend/app/services/mpi/`)

| Component | Technology |
|-----------|------------|
| Matching Algorithm | Fellegi-Sunter scoring |
| String Similarity | Jaro-Winkler distance |
| Name Normalization | Arabic/English normalization |
| Deterministic Match | NID hash exact match (score 1.0) |
| Probabilistic Match | Phone, DOB, name, gender, family ID |
| Auto-Merge | >= 0.90 |
| Review | >= 0.70 |

### Identity Models

| Table | Purpose |
|-------|---------|
| `citizens` | Canonical national identity (48M scale) |
| `canonical_patients` | Unified LIMS view |
| `identity_claims` | Lab-to-citizen bridging |
| `mpi_merge_audit` | Merge audit trail |
| `gov_identity_records` | Government identity records |
| `gov_break_glass_accesses` | Emergency access log |
| `consents` | Data sharing permissions |

---

## 41. Digital Wallet

**Status:** Not yet implemented.

Digital Wallet is listed as a future vision item. No dedicated implementation exists in the current codebase.

**Related existing capabilities:**
- Patient Card (QR-backed, HMAC-signed)
- National ID Card (frontend component)
- Consent Management
- Identity Verification
- Digital Twin platform
- Knowledge Graph

---

## 42. Knowledge Graph

### Platform Knowledge Graph (`backend/app/knowledge_graph/`)

**MISSION-017B**

### Capabilities

| Feature | Status |
|---------|--------|
| Knowledge Graph Nodes | Active |
| Knowledge Graph Edges | Active |
| Graph Routes | Active |
| Vector Embeddings | Active |
| Cross-Entity Navigation | Active |

### Models

- `KnowledgeGraphNode` - Graph vertices with type, properties, embeddings
- `KnowledgeGraphEdge` - Graph edges with relationship type, weight

### Architecture Docs

| Document | Location |
|----------|----------|
| Knowledge Graph | `docs/architecture/KNOWLEDGE_GRAPH.md` |
| Entity Catalog | `docs/architecture/ENTITY_CATALOG.md` |
| Knowledge Integration | `architecture/23-knowledge-integration.md` |

---

## 43. Digital Twin

### Digital Twin Platform (`backend/app/simulation/`)

**MISSION-027**

### Capabilities

| Feature | Status |
|---------|--------|
| Digital Twin Routes | Active |
| Simulation Engine | Active |
| Predictive Modeling | Active |
| Population Health Simulation | Frontend: `DigitalTwinSimulation.tsx` |

### Frontend Components

| Component | Purpose |
|-----------|---------|
| `DigitalTwin.tsx` | Individual digital twin visualization |
| `DigitalTwinSimulation.tsx` | What-if simulation interface |

---

## 44. Integration

### Integration Architecture

| Integration Type | Systems | Protocol |
|-----------------|---------|----------|
| **Lab Instruments** | Sysmex, Roche, Mindray, Generic | ASTM/HL7 |
| **Government** | MoI NID, NHI Insurance, MoI Residency | REST (stub/live/shadow) |
| **Cloudflare** | R2 Storage, CDN, Control Plane | REST API |
| **Supabase** | PostgreSQL (migration path) | Standard PG |
| **Firebase** | Auth + Firestore | Google SDK |
| **External AI** | Gemini, Groq, OpenAI, Anthropic | HTTP/gRPC |
| **SAML IdP** | Government/enterprise IdP | SAML 2.0 |
| **OAuth2 IdP** | Keycloak, Google, etc. | OAuth2/OpenID Connect |

### Adapter Mode System

Modes: `stub` (mock), `live` (real API), `shadow` (dual-write, compare)
Per-adapter overrides: NID, INSURANCE, RESIDENCY, CLOUDFLARE

---

## 45. SDK

**Status:** Not yet implemented as a standalone deliverable.

Closest equivalents:
- **Shared Library** (`shared/`) - 40+ reusable Python modules
- **Contracts** (`contracts/`) - API contracts for SDK consumers
- **Ecosystem Platform** - Partner agreement, credential, rate limit management
- **CLI** (`cli/`) - CLI tooling

SDK generation from OpenAPI spec is possible via standard tools but no packaged SDK exists.

---

## 46. Plugin System

### Kernel Plugin System (ADR-004)

**Status:** Architecture defined, not yet implemented in production.

| Concept | Description |
|---------|-------------|
| Plugin identity | UUID4 + manifest + version |
| Lifecycle | registered -> enabled -> disabled -> removed |
| Isolation | Subprocess with resource limits |
| API | gRPC or REST with signed requests |
| Permissions | Declarative permission manifest |

### Related Capabilities

- `KERNEL_ENABLE_PLUGINS` flag in config
- Agent system in `ai_fabric/agents/` provides plugin-like extensibility
- Ecosystem partner framework

---

## 47. Marketplace

**Status:** Vision only. No implementation exists.

### Related Implementations

- **Subscription Tiers** - Lab subscription tiers, upgrade requests
- **Financial Engine** - Phase A schema only
- **Ecosystem Partner Management** - Certificates, credentials, rate limits
- **Feature Flags** - Per-tenant feature enable/disable

### Feature Flags

`ENABLE_FINANCIAL_ENGINE` and `ENABLE_ADS` - both default to **false**.

---

## 48. Developer Platform

### Developer Platform Components

| Component | Status | Purpose |
|-----------|--------|---------|
| **API Documentation** | Active | Swagger UI, ReDoc |
| **OpenAPI Export** | Active | CI pipeline |
| **AsyncAPI Export** | Active | Event catalog |
| **Contracts** | Active | OpenAPI, FHIR, ASTM, HL7 |
| **CLI** | Active | Generators, validators |
| **Engineering Factory** | Active | Engineering process docs |
| **SDK** | Not yet | No packaged SDK |
| **Plugin SDK** | Not yet | No plugin development kit |
| **Developer Portal** | Not yet | No developer portal |

---

## 49. Future Readiness

### Roadmap

| Phase | Focus | Status |
|-------|-------|--------|
| Foundation (v1.0) | Core lab platform | **Complete** |
| Production (v1.1) | National deployment | **Complete** |
| National (v2.0) | SNDHS, EHR, Governance | **In progress (v2.1.0)** |
| Intelligence (v3.0) | AI fabric, knowledge graph | Partial |
| Ecosystem (v4.0) | Marketplace, SDK, plugins | Vision |

### Future Features Identified

| Feature | Readiness |
|---------|-----------|
| **Digital Wallet** | Not started |
| **Marketplace** | Not started |
| **Plugin System** | Architecture defined |
| **SDK** | Not started |
| **Dentistry Module** | Not started |
| **Telemedicine** | Model exists (`TelemedicineSession`) |
| **KIOSK Mode** | Not started |
| **Wearable Integration** | Not started |
| **Post-Quantum Cryptography** | Roadmap |
| **Fully Decoupled Microservices** | Scaffolds exist |

---

## 50. Sustainability

### Software Sustainability

| Dimension | Assessment | Actions |
|-----------|-----------|---------|
| **Code Maintainability** | Moderate | 1413 mypy errors, 268 test fixture issues |
| **Documentation Coverage** | Good | Extensive engineering docs |
| **Test Coverage** | C+ (54%) | Below target |
| **Dependency Management** | Moderate | 50 RUSTSEC advisories |
| **Technical Debt** | High | D-001 through D-005 (Score 79) |

### Operational Sustainability

| Aspect | Status | Notes |
|--------|--------|-------|
| **Monitoring** | Good | Prometheus/Grafana/Loki/Tempo |
| **Alerting** | Good | Severity-based routing (PD, Slack, Email) |
| **Incident Response** | Good | 7 runbooks, SEV1-4 classification |
| **Backup** | Good | Hourly/daily/WAL, 30-day retention |
| **DR** | Good | Active-passive multi-region |
| **Capacity Planning** | Moderate | HPA, budgets, baselines needed |
| **Cost Management** | Basic | No cost analysis tools integrated |

### Environmental Sustainability

- Infrastructure hosted on cloud providers (DigitalOcean, AWS)
- No specific green IT or carbon footprint tracking
- Efficient via containerization and auto-scaling

```
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║  GULA - منصة غولا الصحية الذكية للمختبرات                                    ║
║  Smart Health Platform for Medical Laboratories in Iraq                      ║
║  Version 2.1.0 | Republic of Iraq - Ministry of Health Compliant             ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
```
