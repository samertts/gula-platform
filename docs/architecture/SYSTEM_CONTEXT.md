# GULA Platform — System Context

**Version:** 1.0 | **Last Updated:** 2026-07-23

## Table of Contents

1. [System Context Overview](#1-system-context-overview)
2. [Actors / Personas](#2-actors--personas)
3. [External Systems](#3-external-systems)
4. [Subsystems](#4-subsystems)
5. [Services](#5-services)
6. [Data Flows](#6-data-flows)
7. [Trust Boundaries](#7-trust-boundaries)
8. [National Architecture](#8-national-architecture)
9. [Context Diagram (ASCII)](#9-context-diagram-ascii)

---

## 1. System Context Overview

**GULA Platform** (منصة غولا الصحية) is an Arabic-first, multi-tenant healthcare platform for Iraqi medical laboratories. It is a monorepo that consolidates three previously separate GitHub repositories into a unified codebase:

| Former Repository | Location in Monorepo | Role |
|---|---|---|
| `samertts/gula-platform` | `backend/`, `services/`, `nhop-platform/`, `ai/` | Core platform (source of truth) |
| `samertts/LabLink-Core` | `services/device_bridge/` | Lab instrument integration (ASTM/HL7) |
| `samertts/Front-end-` | `frontend-v2/` | Rich React + Firebase UI |

The production deployment follows a **monolith-first** architecture: a single FastAPI monolith (`backend/app/`) running under Gunicorn + Uvicorn workers, backed by PostgreSQL 16 and Redis 7. All traffic enters through a host nginx (TLS termination) → Docker nginx api-gateway → backend pipeline. A parallel microservices tree (`services/`) exists for future decomposition but is not the current production target.

**App Version:** 2.5.0 | **Platform Name (Arabic):** منصة غولا الصحية

### Architecture Principles (Canonical)

1. **Single Source of Truth** — Every concern has exactly one canonical implementation in `shared/`
2. **Repository Consolidation** — All code is unified from six historic repositories
3. **Layered Design** — Presentation → Application → Domain → Infrastructure
4. **Arabic-First** — RTL support at every layer
5. **Event-Driven** — Asynchronous communication via canonical EventBus
6. **Tenant-Isolated** — Every query scoped by `lab_id`
7. **Audit-Everywhere** — Every mutation logged through SHA-256 hash-chain AuditService

**Key ADRs:** [ADR-002 Monolith First](../adr/ADR-002-monolith-first.md), [ADR-003 Multi-Tenant Isolation](../adr/ADR-003-multi-tenant-isolation.md), [ADR-005 PostgreSQL/Redis Stack](../adr/ADR-005-postgresql-redis-stack.md), [ADR-009 Self-Healing Infrastructure](../adr/ADR-009-self-healing-infrastructure.md)

### Deployment Architecture

```
Internet → host nginx (TLS, Let's Encrypt) → api-gateway (Docker nginx, 127.0.0.1:8080)
    → gula-backend (FastAPI, gunicorn + uvicorn, 127.0.0.1:8000)
    → PostgreSQL 16 + Redis 7
```

The backend never exposes a public port. All traffic enters through the gateway. Rate limiting is applied at the api-gateway layer (100 req/min per IP, 10 req/min on auth endpoints).

### Component Architecture (within monolith)

```
backend/app/
├── main.py              # App init, middleware, lifespan, health endpoints
├── config.py            # Env vars, secrets validation, app version
├── database.py          # SQLAlchemy engine + pool + contextvars
├── factory.py           # Application factory, middleware stack, route registration
├── routes/              # 56 route modules (500+ endpoints)
├── models/              # 28 model files (~160+ ORM models)
├── services/            # Business logic layer (36 modules)
├── core/                # Infrastructure (19 modules)
├── security/            # Auth, JWT, RBAC, rate limiting (15 modules)
├── kernel/              # Kernel runtime (plugin system, event bus)
├── tasks/               # Background tasks (outbox pattern)
├── audit/               # Audit logging (SHA-256 hash chain)
├── notifications/       # Notification service
├── integration/         # Integration platform (ESB, CDC, HL7/FHIR)
├── gateways/            # External service adapters
├── financial/           # Financial Engine (Phase A schema only)
├── national/            # National health platform
├── nhdw/                # National Health Data Warehouse
└── 15+ sub-packages     # LIMS, radiology, pharmacy, nursing, EMS, etc.
```

---

## 2. Actors / Personas

| Actor | Description | Primary Interactions | Authenticated |
|---|---|---|---|
| **Lab Technician** | Laboratory staff who receive samples, run tests on instruments, and enter results. | `POST /results`, `POST /samples`, `GET /orders`, Device Bridge (ASTM), result validation screens | JWT (HS256) + RBAC |
| **Lab Director** | Manages lab operations, reviews QC data, configures test panels, oversees staff. | `PUT /labs`, `GET /stats`, quality control dashboards, staff management, subscription tiers | JWT + RBAC |
| **Clinician / Doctor** | Orders lab tests for patients, reviews results, receives critical alerts. Clinical workspace across national healthcare network. | `POST /orders`, `GET /results`, critical alerts, patient clinical history, ePrescription | JWT + RBAC |
| **Patient / Citizen** | Receives lab results, manages digital patient card, views personal health record via citizen portal or mobile app. | QR code scanning, patient card retrieval, result viewing (`frontend-v2` citizen portal, mobile app) | JWT (limited) or HMAC token (card) |
| **Ministry Official** | National/regional health authority accessing population health statistics, disease surveillance, compliance audits via Command Centre. | `GET /stats`, `GET /compliance`, national data warehouse queries, NHOP registry management | JWT + RBAC (elevated) |
| **System Administrator** | Manages tenants, labs, users, feature flags, system configuration, deployment, and monitoring. | `GET /admin/*`, `POST /setup`, Prometheus/Grafana monitoring, kill-switch operations | JWT + admin RBAC |
| **Integration Partner** | External systems (insurance companies, government agencies, national ID systems) consuming or providing data via API or webhook. | `POST /integrations`, OAuth2/OIDC flows, webhook callbacks, FHIR/HL7 exchange | OAuth2 / API keys |
| **Nurse** | Collects specimens, performs bedside tests, manages patient admissions and visit tracking. | `POST /samples`, patient identification, visit registration, critical alert response | JWT + RBAC |
| **Pharmacist** | Dispenses medications, checks drug interactions, manages inventory. | Pharmacy platform routes, drug catalog, dispensing queue, inventory management | JWT + RBAC |
| **Radiologist** | Reviews imaging studies, produces radiology reports, manages DICOM studies. | Radiology platform routes, DICOM study management, AI-assisted analysis, report generation | JWT + RBAC |

---

## 3. External Systems

### 3.1 Data Stores

| System | Version | Purpose | Integration Point |
|---|---|---|---|
| **PostgreSQL 16** | 16.x | Primary database — all transactional data, patient records, lab orders, audit logs, outbox events. SQLAlchemy async engine with connection pooling. | `backend/app/database.py` — pool config: `WEB_CONCURRENCY × (DB_POOL_SIZE + DB_MAX_OVERFLOW)` = 3 × (6 + 12) = 54 connections |
| **Redis 7** | 7.x | Cache (L1 in-memory + L2 Redis), session store, rate limiting, message broker fallback. Optional — in-memory fallback when `REDIS_URL` is absent. | `backend/app/security/redis_client.py` — multi-level cache coordinator in `core/cache_manager.py` |
| **Supabase** | Managed | Optional managed Postgres integration for projects migrating from Supabase. Not authoritative — `DATABASE_URL` is the runtime source of truth. | `config.py:SUPABASE_URL`, `supabase/setup.sql` |

### 3.2 Integration Systems

| System | Purpose | Integration Point |
|---|---|---|
| **Device Bridge (LabLink-Core)** | ASTM/HL7 lab instrument integration — reads from physical devices (Sysmex, Roche, Mindray, generic), normalises results, forwards to backend. | `services/device_bridge/` — `POST /ingest` → backend API via `app/integration/gula_client.py`. Supports Serial/TCP connectors, offline buffering, smart routing. |
| **AI Providers — Google Gemini** | Clinical AI — lab result interpretation, chat assistance, predictive analytics. Gemini 2.0 Flash models. | `backend/app/gateways/google_ai.py` — `GEMINI_API_KEY`, `gemini-2.0-flash` models for clinical and chat. Free tier: 1,500 req/day. |
| **AI Providers — Groq** | Alternative LLM inference provider for clinical AI (LLaMA/Mixtral models). | `config.py:GROQ_API_KEY` |
| **AI Providers — Ollama** | Self-hosted LLM inference for on-premises AI processing. | `config.py:OLLAMA_BASE_URL` |
| **MoI National ID (NID)** | Iraqi Ministry of Interior — national identity verification. Encrypted at rest with Fernet + HMAC. | `backend/app/gateways/national_identity_gateway.py` — `MOI_NID_API_URL`, `MOI_NID_API_KEY`. Adapter modes: `stub` (default), `live`, `shadow`. |
| **NHI Insurance** | National Health Insurance — eligibility and claims verification. | `backend/app/gateways/insurance_gateway.py` — `INSURANCE_API_URL`, `INSURANCE_API_KEY`. Adapter modes. |
| **MoI Residency** | Ministry of Interior — residency status verification. | `backend/app/gateways/residency_gateway.py` — `RESIDENCY_API_URL`, `RESIDENCY_API_KEY`. Adapter modes. |

### 3.3 Edge & Infrastructure

| System | Purpose | Integration Point |
|---|---|---|
| **Cloudflare** | DNS (dns-records.yaml), WAF (waf-rules.json), CDN, R2 object storage (gula-reports bucket), Edge Workers (worker.js). | `cloudflare/` — `CF_API_TOKEN`, `CF_ACCOUNT_ID`, `CF_ZONE_ID`, `CF_R2_BUCKET` |
| **Sentry** | Optional error tracking and performance monitoring. FastAPI+SQLAlchemy integrations. | `config.py:SENTRY_DSN` — `traces_sample_rate: 0.05` |
| **Firebase Cloud Messaging** | Optional push notifications for mobile apps. Only remaining Firebase dependency. | `config.py:FCM_SERVER_KEY` — no data dependency |
| **Prometheus + Grafana** | Monitoring stack (opt-in profile). Prometheus scrape config + Grafana dashboards provisioned in `config/`. | `docker-compose.full.yml`, `config/prometheus/`, `config/grafana/`. Internal only — SSH tunnel to reach. |
| **DigitalOcean** | Primary cloud provider. Droplet-based deployment via `scripts/deploy.sh`. | `digitalocean/`, `config.py:DIGITALOCEAN_APP_ID` |

### 3.4 Other External Integrations

| System | Purpose | Details |
|---|---|---|
| **SAML Identity Providers** | Enterprise SSO integration for Ministry/Government authentication. | `backend/app/routes/saml.py` |
| **OAuth2 Providers** | Third-party OAuth2 sign-in (Google, etc.) | `backend/app/routes/oauth2.py` |
| **Apple Push Notifications** | Push notifications for iOS mobile app. | `config.py:APNS_KEY` |
| **HAProxy** | Load balancer for horizontal scaling (multiple backend replicas). | `config/haproxy/haproxy.cfg` — stats at `:8404/stats` |

---

## 4. Subsystems

| Subsystem | Location | Technology | Description |
|---|---|---|---|
| **Backend Monolith** | `backend/app/` | FastAPI (Python 3.11+), Gunicorn + Uvicorn | Production deployment target. All routes (56 modules, 500+ endpoints), models (28 files, ~160 ORM models), business logic (36 services), and core infrastructure. Port 8000, never exposed publicly. |
| **frontend-v2** | `frontend-v2/` | React SPA + Vite | Rich multi-portal application: citizen portal, Ministry Command Centre, predictive analytics, doctor/lab dashboards. Firebase removed — all data flows through backend API. |
| **frontend (PWA)** | `frontend/` | Static HTML + service worker | Lightweight offline-capable progressive web app. Static pages for login, registration, result lookup, and tier information. |
| **client (tRPC)** | `client/` | tRPC + React SPA | Lightweight typed RPC client connected to `gula-backend`. |
| **NHOP** | `nhop-platform/` | FastAPI (Python), port 8100 | National Health Oversight Platform — companion service that owns the national citizen registry. GULA owns the per-lab LIMS view. Runs as a separate Docker container. |
| **edge_agent** | `edge_agent/` | Python | Off-site/offline edge computing agent for remote lab sites. Buffers data when disconnected, syncs when connectivity is restored. Configurable via `config.example.toml`. |
| **Mobile — Android** | `mobile/android/` | Kotlin (Gradle) | Native Android application for patients and healthcare workers. |
| **Mobile — iOS** | `mobile/ios/` | Swift (Xcode) | Native iOS application with widgets, intents, and UI tests. |
| **AI Modules** | `ai/` | Python | Top-level clinical AI modules — lab brain, population health, outbreak detection, preventive engine, Ali Reza engine. Separate from `backend/app/ai/` (monolith-side AI). |
| **Cloudflare** | `cloudflare/` | Workers + WAF + DNS | Edge infrastructure: DNS records (dns-records.yaml), WAF rules (waf-rules.json), R2 bucket spec (r2-bucket-spec.json), Worker script (worker.js), wrangler config. |

---

## 5. Services

All located under `services/`. These represent the future microservice decomposition; the monolith is currently the source of truth for business logic.

| Service | Directory | Purpose | Status |
|---|---|---|---|
| **device_bridge** | `services/device_bridge/` | LabLink-Core: ASTM/HL7 instrument integration. Physical device connectivity (Sysmex, Roche, Mindray, generic), ASTM protocol engine, patient matching, test mapping, edge buffering, smart routing. | **Production** (docker compose --profile device-bridge) |
| **lab** | `services/lab/` | Lab management microservice (future decomposition). | Future |
| **order** | `services/order/` | Order management microservice (future decomposition). | Future |
| **patient** | `services/patient/` | Patient management microservice (future decomposition). | Future |
| **result** | `services/result/` | Result management microservice (future decomposition). | Future |
| **sample** | `services/sample/` | Sample management microservice (future decomposition). | Future |
| **notification** | `services/notification/` | Notification microservice (future decomposition). | Future |
| **ai** | `services/ai/` | Clinical AI microservice (future decomposition). | Future |
| **autonomous_manager** | `services/autonomous_manager/` | Autonomous system management (future decomposition). | Future |
| **shared** | `services/shared/` | Shared libraries used across microservices. | Bridged to `shared/` |

All microservices are shipped as Docker images via CI matrix (7 images + 1 backend = 8 total in build-and-push job). `latest` tag only on `main` branch.

---

## 6. Data Flows

### 6.1 Request Lifecycle

```
Internet
    │
    ▼
host nginx (TLS termination, Let's Encrypt certs)
    │
    ▼
api-gateway (Docker nginx on 127.0.0.1:8080)
    ├── Rate limiting (100 req/min per IP, 10 req/min auth)
    ├── Security headers (CSP, HSTS, X-Frame-Options)
    └── Depends on backend health check
    │
    ▼
gula-backend (FastAPI — middleware stack order, outermost first)

  Layer 1:  ConcurrencyLimitMiddleware   (in-flight cap 50, clinical writes exempt)
  Layer 2:  KernelMiddleware             (kernel context attachment)
  Layer 3:  ReadinessMiddleware          (503 if system_ready is False)
  Layer 4:  DegradedModeMiddleware       (rejects writes if DB circuit open)
  Layer 5:  GZipMiddleware               (compress responses ≥ 1000 bytes)
  Layer 6:  SecurityHeadersMiddleware    (CSP, HSTS, X-Frame-Options, X-Content-Type-Options)
  Layer 7:  RequestTimingMiddleware      (access log, X-Response-Time header)
  Layer 8:  CORSMiddleware               (configured origins, methods, headers)
  Layer 9:  DocsAuthMiddleware           (guards /docs /redoc in production, admin JWT)
  Layer 10: RequestIDMiddleware          (X-Request-ID, log ctx, DB correlation vars)
  Layer 11: MaxBodySizeMiddleware        (413 above 10 MB default)
    │
    ▼
Route handler → Service layer → DB/Redis/External API
    │
    └──→ Audit Log (SHA-256 hash chain)
```

### 6.2 Authentication Flow

```
Client                          Backend                         DB/Redis
  │                               │                               │
  │  POST /login                  │                               │
  │  {email, password}            │                               │
  ├──────────────────────────────►│                               │
  │                               │── verify credentials ────────►│
  │                               │◄──── user + lab_id ──────────┤
  │                               │                               │
  │                               │── check RBAC permissions ────►│
  │                               │◄──── role permissions ───────┤
  │                               │                               │
  │                               │  create_access_token()        │
  │                               │  (HS256, sub, lab_id, role,   │
  │                               │   exp=30min, iat)             │
  │                               │  create_refresh_token()       │
  │                               │  (exp=30 days)                │
  │                               │                               │
  │  {access_token, refresh_token}│                               │
  │◄──────────────────────────────┤                               │
  │                               │                               │
  │  GET /orders                  │                               │
  │  Authorization: Bearer <jwt>  │                               │
  ├──────────────────────────────►│                               │
  │                               │── decode_jwt()                │
  │                               │── validate exp + iat          │
  │                               │── check lab_id isolation      │
  │                               │── RBAC has_permission()       │
  │                               │── query (lab_id filter) ─────►│
  │                               │◄──── results ────────────────┤
  │◄──── 200 OK ─────────────────┤                               │
```

**Key invariants:**
- JWT signed with HS256 using `SECRET_KEY` (no hardcoded fallback in production)
- Refresh token signed with independent `REFRESH_TOKEN_SECRET`
- All patient-data queries filter by `lab_id = current_user.lab_id`
- Rate limiting: 10 req/min on `/login`
- MFA available via `/mfa/*` routes
- OAuth2 and SAML also available for enterprise SSO

### 6.3 Lab Order Processing

```
Clinician (frontend-v2)           Backend                          DB              Audit
      │                              │                            │                │
      │  POST /orders                │                            │                │
      │  {patient_id, tests,         │                            │                │
      │   priority, clinical_info}   │                            │                │
      ├─────────────────────────────►│                            │                │
      │                              │── validate patient exists  │                │
      │                              │── validate test codes      │                │
      │                              │── apply order state        │                │
      │                              │   machine (order_state.py) │                │
      │                              │── compute price/tier       │                │
      │                              │                            │                │
      │                              │── INSERT lab_order ───────►│                │
      │                              │                            │                │
      │                              │── write audit entry ──────►│── AuditLog ───►│
      │                              │   (action="order_created", │                │
      │                              │    user_id, lab_id,        │                │
      │                            │   order_id, hash_chain)    │                │
      │                              │                            │                │
      │                              │── create OutboxEvent ─────►│── outbox ─────►│
      │                              │   (topic="order.created",  │                │
      │                              │    payload, idempotency)   │                │
      │                              │                            │                │
      │  {order_id, status}          │                            │                │
      │◄─────────────────────────────┤                            │                │
```

Order states (from `backend/app/domain/order_state.py`):
`PENDING → ACCEPTED → COLLECTED → IN_PROGRESS → COMPLETED → VERIFIED → REPORTED`
With transition guards and validation at each step.

### 6.4 Result Entry (Device Integration)

```
Physical Instrument (Sysmex/Roche/Mindray)
    │
    │  Serial or TCP connection (ASTM protocol)
    ▼
Device Bridge (services/device_bridge/)
    ├── SerialConnector / TCPConnector (ENQ/ACK/EOT handshake)
    ├── ASTM Buffer (STX/ETX framing, checksum validation)
    ├── ASTM Parser (H/P/R/L record parsing)
    ├── Vendor-specific adapter (SysmexAdapter/RocheAdapter/MindrayAdapter)
    ├── PatientMatcher (ASTM patient ID → GULA patient ID)
    └── TestMappingEngine (Hb/HGB → HEMOGLOBIN)
    │
    │  HTTPS POST /ingest (x-api-key auth)
    ▼
gula-backend
    ├── Validate device API key
    ├── Validate result data against order
    ├── Apply LabResult optimistic lock (version column)
    ├── Calculate reference ranges
    ├── Flag critical values
    │
    ├── INSERT/UPDATE lab_result ────► PostgreSQL
    ├── Write audit log ─────────────► AuditLog (hash chain)
    ├── Create outbox event ─────────► OutboxEvent
    └── Trigger notification ───────► FCM / Telegram
```

### 6.5 Self-Healing Flow

The system has 3 layers of self-healing:

1. **Circuit Breaker** (`core/self_healing.py`):
   - Tracks consecutive failures per service (DB, Redis)
   - States: CLOSED → OPEN (on threshold) → HALF_OPEN (recovery probe)
   - Degradation levels: NONE → L1_CACHE_HEAVY → L2_READ_ONLY → L3_CRITICAL_ONLY

2. **Auto-Repair Engine** (`core/auto_repair.py`):
   - GC pressure reduction
   - Database pool recycle
   - Connection re-establishment

3. **Adaptive Concurrency** (`main.py::_adaptive_concurrency_loop`):
   - Halves `_MAX_CONCURRENT` after 2 slow DB readings (>300ms)
   - Restores after 3 fast readings (<150ms)

### 6.6 Health Watchdog

A `_health_alert_loop` runs every 60 seconds scoring the system GREEN/YELLOW/RED. It fires `ALERT_WEBHOOK_URL` (Telegram/Discord/Slack) on transitions and sends 5-minute RED reminders.

### 6.7 Startup Guard

`core/startup_guard.py` blocks readiness until: config validated, DB reachable, migrations checked, critical data seeded. Until passing, `system_ready = False` and all paths except health whitelist return 503.

---

## 7. Trust Boundaries

```
                      Trust Boundary 1: Internet ←→ TLS
┌────────────────────────────────────────────────────────────────┐
│  INTERNET                                                        │
│  (Patients, Clinicians, Ministry, Integration Partners)         │
└──────────────────────────┬─────────────────────────────────────┘
                           │  HTTPS (TLS 1.2/1.3)
                           │  Cloudflare WAF filtering
                           ▼
┌────────────────────────────────────────────────────────────────┐
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  HOST NGINX (TLS Termination)                             │  │
│  │  - Let's Encrypt certificate                             │  │
│  │  - TLS termination (decrypts to internal network)         │  │
│  └──────────────────────┬───────────────────────────────────┘  │
│                          │                                      │
│         Trust Boundary 2: Host nginx ←→ api-gateway           │
│                          │  (localhost: loopback)               │
│                          ▼                                      │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  API GATEWAY (Docker nginx on 127.0.0.1:8080)             │  │
│  │  - Rate limiting (100 req/min IP, 10 req/min auth)       │  │
│  │  - Security headers (CSP, HSTS, X-Frame-Options)         │  │
│  │  - deny public port exposure                             │  │
│  └──────────────────────┬───────────────────────────────────┘  │
│                          │                                      │
│         Trust Boundary 3: api-gateway ←→ gula-backend         │
│                          │  (localhost: loopback, port 8000)    │
│                          ▼                                      │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  GULA BACKEND (FastAPI monolith)                          │  │
│  │  - JWT authentication (HS256)                            │  │
│  │  - RBAC authorization (9 roles × 16 permissions)         │  │
│  │  - ABAC for fine-grained access control                  │  │
│  │  - Tenant isolation (lab_id filter on all queries)       │  │
│  │  - Audit log (SHA-256 hash chain, all mutations)         │  │
│  │  - Rate limiting per endpoint                            │  │
│  │  - MFA / OAuth2 / SAML                                   │  │
│  │  - Circuit breaker (degraded mode on failure)            │  │
│  └──────┬──────────────────────────────┬────────────────────┘  │
│         │                              │                        │
│  Trust Boundary 4a:    │    Trust Boundary 4b:                 │
│  Backend ←→ DB         │    Backend ←→ Redis                  │
│  (password auth)       │    (password auth)                    │
│         ▼              │         ▼                             │
│  ┌────────────┐        │  ┌────────────┐                      │
│  │ PostgreSQL │        │  │  Redis 7   │                      │
│  │    16      │        │  │ (optional) │                      │
│  └────────────┘        │  └────────────┘                      │
│                         │                                      │
│  Trust Boundary 5: gula-backend ←→ External Systems           │
│  - JWT or API key for NHOP                                    │
│  - API key (x-api-key) for Device Bridge                      │
│  - GEMINI_API_KEY for Google AI                               │
│  - GROQ_API_KEY for Groq                                      │
│  - MOI_NID_API_KEY for National ID API                        │
│  - INSURANCE_API_KEY for Insurance API                        │
│  - CF_API_TOKEN for Cloudflare control plane                  │
└────────────────────────────────────────────────────────────────┘
```

### Security Invariants (never violate)

1. All patient-data queries filter by `lab_id = current_user.lab_id`
2. All mutations write to audit log (SHA-256 hash chain)
3. Phone lookups use exact match — never `LIKE` with user input
4. `/metrics/prom` requires `Bearer METRICS_BEARER_TOKEN` in production
5. `system_ready` stays False until DB is confirmed reachable
6. Optimistic lock (`version` column) on every `LabResult` mutation
7. Secrets have no hardcoded fallbacks — absence → hard fail on startup
8. `patients.national_id` encrypted at rest (Fernet + HMAC)
9. Patient card HMAC tokens verified before data returned
10. National ID stored encrypted, never plaintext

---

## 8. National Architecture

### SNDHS-lite Integration (Phase 1)

The platform integrates with the **Iraqi National Health Data System (SNDHS)** through phased deployment:

| Component | Status | Details |
|---|---|---|
| `patients.national_id` | Feature-flagged | Encrypted, indexed national ID field. Off by default (`SNDHS_ENABLE_NATIONAL_ID`). |
| `patients.sndhs_health_id` | Feature-flagged | SNDHS-assigned health ID. Same flag as national ID. |
| `visits` table | Feature-flagged | Clinical episode tracking. Off by default (`SNDHS_ENABLE_VISITS`). |
| `lab_orders.visit_id` | Feature-flagged | Links orders to clinical visits. |
| Enhanced audit log (v2) | Feature-flagged | Immutable chain with SNDHS correlation fields. |
| NHOP (National Health Oversight Platform) | Active | Separate FastAPI app on port 8100. Owns national citizen registry. GULA owns per-lab LIMS view. |

**Migration files (all in `backend/migrations/versions/`):**
- `20260505_0001_sndhs_phase1_extend_patients.py`
- `20260505_0002_sndhs_phase1_index_national_id.py`
- `20260505_0003_sndhs_phase1_visits_table.py`
- `20260505_0004_sndhs_phase1_lab_orders_visit_id.py`
- `20260505_0005_sndhs_phase1_audit_logs_v2.py`
- `20260505_0006_sndhs_phase1_constraints.py`

**Deployment procedure:**
1. Run `scripts/sndhs_phase1_backfill.py` before enabling flags on existing data
2. Set `SNDHS_ENABLE_VISITS=true` and/or `SNDHS_ENABLE_NATIONAL_ID=true`
3. Rollback via `scripts/sndhs_phase1_rollback.sql` + `scripts/sndhs_phase1_disable_flags.sh`

**Key ADR:** [ADR-010 SNDHS-lite Government Integration](../adr/ADR-010-sndhs-government-integration.md)
**Full specification:** `docs/sndhs/` (22 files covering architecture, DB, API, offline sync, security, governance)

### Government API Adapters

External government APIs are accessed through the adapter pattern (`backend/app/gateways/`):

| Adapter | File | Endpoint | Mode |
|---|---|---|---|
| National ID (MoI) | `national_identity_gateway.py` | `MOI_NID_API_URL` | stub / live / shadow |
| Insurance (NHI) | `insurance_gateway.py` | `INSURANCE_API_URL` | stub / live / shadow |
| Residency (MoI) | `residency_gateway.py` | `RESIDENCY_API_URL` | stub / live / shadow |
| Cloudflare | `cloudflare_gateway.py` | `CF_API_TOKEN` | stub / live / shadow |

Adapter modes:
- **stub** (default) — returns mock data, no external call
- **live** — makes real API calls
- **shadow** — makes real API calls but returns stub data (for testing)

### National Platform Components

The monolith contains extensive national health platform modules:

| Module | Location | Purpose |
|---|---|---|
| National Health Data Warehouse | `backend/app/nhdw/` | DW models (DimPatient, DimFacility, FactLabResult, etc.) |
| National Data Platform | `backend/app/national_data/` | Canonical records, MDM, governance, event store |
| National Health Platform | `backend/app/national/` | Rules engine, workflow runtime, notification platform, scheduling, search |
| Command Centre | `backend/app/command_center/` | National health command centre for Ministry oversight |
| Public Health | `backend/app/public_health/` | Disease surveillance, population health monitoring |
| National Citizen Registry | `nhop-platform/` | Companion FastAPI service on port 8100 |

### Tenant Model

Multi-level hierarchy (Ministry → Governorate → Facility → Department):

```
Ministry of Health (National Tenant)
    ├── Baghdad Health Directorate
    │   ├── Baghdad Teaching Hospital
    │   │   ├── Hematology Lab
    │   │   └── Biochemistry Lab
    │   └── Al-Karkh PHC
    ├── Basra Health Directorate
    │   ├── Basra General Hospital
    │   └── ...
    ├── Nineveh Health Directorate
    └── ... (18 governorates total)
```

---

## 9. Context Diagram (ASCII)

```
                                                             ┌──────────────────────┐
                                                             │    CLOUDFLARE EDGE   │
                                                             │  DNS ─ WAF ─ CDN ─   │
                                                             │  R2 (gula-reports)   │
                                                             └──────────┬───────────┘
                                                                        │
┌──────────────────────────────────────────────────────────────────────┐│
│                         INTERNET / EXTERNAL                           ││
│                                                                       ││
│  ┌──────────┐  ┌───────────┐  ┌────────────┐  ┌────────────────┐    ││
│  │ Patients │  │ Clinicians│  │  Ministry  │  │  Integration   │    ││
│  │ (Citizen │  │ (Doctors/ │  │  Officials │  │  Partners      │    ││
│  │  Portal) │  │  Nurses)  │  │  (NHOP)    │  │ (Insurance/Gov)│    ││
│  └─────┬────┘  └─────┬─────┘  └──────┬─────┘  └───────┬────────┘    ││
│        │             │               │                │             ││
│        │      ┌──────▼──────┐        │                │             ││
│        │      │Lab Technici.│        │                │             ││
│        │      └──────┬──────┘        │                │             ││
│        │             │               │                │             ││
│        │      ┌──────▼──────┐        │                │             ││
│        │      │Lab Directors│        │                │             ││
│        │      └─────────────┘        │                │             ││
└────────┼─────────────────────────────┼────────────────┼─────────────┘│
         │                             │                │              │
         └──────────┬──────────────────┴────────────────┘              │
                    │                        ▲                          │
                    │  HTTPS (TLS 1.3)       │  Cloudflare Workers      │
                    ▼                        │                          │
         ┌───────────────────────────────────────────────────────────┐  │
         │                   HOST NGINX                              │  │
         │        TLS Termination — Let's Encrypt Certbot            │  │
         └────────────────────────┬──────────────────────────────────┘  │
                                 │                                      │
                                 ▼                                      │
         ┌───────────────────────────────────────────────────────────┐  │
         │                  API GATEWAY (Docker nginx)               │  │
         │                  127.0.0.1:8080                            │  │
         │  Rate Limit: 100 req/min/IP │ Auth: 10 req/min            │  │
         │  Security Headers: CSP, HSTS, X-Frame-Options             │  │
         └────────────────────────┬──────────────────────────────────┘  │
                                 │                                      │
                                 ▼                                      │
         ┌────────────────────────────────────────────────────────────┐ │
         │                GULA BACKEND (FastAPI Monolith)              │ │
         │            Gunicorn + Uvicorn — 127.0.0.1:8000              │ │
         │                                                            │ │
         │  ┌────────────── MIDDLEWARE STACK ───────────────┐         │ │
         │  │ 1. ConcurrencyLimitMiddleware (cap=50)        │         │ │
         │  │ 2. KernelMiddleware                           │         │ │
         │  │ 3. ReadinessMiddleware (503 if !ready)       │         │ │
         │  │ 4. DegradedModeMiddleware (circuit breaker)   │         │ │
         │  │ 5. GZipMiddleware                             │         │ │
         │  │ 6. SecurityHeadersMiddleware                  │         │ │
         │  │ 7. RequestTimingMiddleware                    │         │ │
         │  │ 8. CORSMiddleware                             │         │ │
         │  │ 9. DocsAuthMiddleware (production only)       │         │ │
         │  │10. RequestIDMiddleware                        │         │ │
         │  │11. MaxBodySizeMiddleware (10 MB)             │         │ │
         │  └──────────────────────────────────────────────┘         │ │
         │                                                            │ │
         │  ┌────────── ROUTES (56 modules, 500+ endpoints) ───────┐ │ │
         │  │ auth, labs, orders, results, patients, samples,       │ │ │
         │  │ stats, ai, compliance, patient_card, edge,            │ │ │
         │  │ identity, insurance, qr, notifications, security,     │ │ │
         │  │ clinical, ehr, radiology, pharmacy, nursing, ems,     │ │ │
         │  │ blood_bank, critical_care, public_health, ...         │ │ │
         │  └──────────────────────────────────────────────────────┘ │ │
         │                                                            │ │
         │  ┌────── DOMAIN ──────┐ ┌─────── SERVICES (36) ─────────┐│ │
         │  │ order_state        │ │ mpi, audit, outbox,            ││ │
         │  │ machine, entities  │ │ governance, notifications,     ││ │
         │  └────────────────────┘ │ reference, patient_card, ...  ││ │
         │                         └───────────────────────────────┘│ │
         │                                                            │ │
         │  ┌─────────── CORE INFRASTRUCTURE ───────────────────────┐│ │
         │  │ self_healing, auto_repair, startup_guard,             ││ │
         │  │ feature_flags, sndhs_flags, policy_engine,            ││ │
         │  │ circuit breaker, logging_config, kernel               ││ │
         │  └──────────────────────────────────────────────────────┘│ │
         │                                                            │ │
         │  ┌─ SUBSYSTEMS ──────────────────────────────────────────┐│ │
         │  │ audit/ │ tasks/ │ integration/ │ gateways/            ││ │
         │  │ national/ │ nhdw/ │ financial/ │ kernel/              ││ │
         │  │ radiology/ │ pharmacy/ │ nursing/ │ lims/             ││ │
         │  │ ems/ │ blood_bank/ │ critical_care/ │ public_health/ ││ │
         │  │ command_center/ │ hospital/ │ governance/ │ trust/   ││ │
         │  └──────────────────────────────────────────────────────┘│ │
         └──────────┬─────────────────────────────────────────────┬──┘ │
                    │                                             │     │
                    │                                             │     │
    ┌───────────────┼──────────────────┐            ┌────────────┼─────┘
    │               │                  │            │            │
    ▼               ▼                  ▼            ▼            │
┌─────────┐  ┌──────────┐  ┌──────────────────┐  ┌────────────┐  │
│Postgres │  │ Redis 7  │  │  DEVICE BRIDGE   │  │ NHOP       │  │
│  16     │  │ Cache    │  │  (LabLink-Core)  │  │ FastAPI    │  │
│         │  │ Sessions │  │  ASTM / HL7      │  │ :8100      │  │
│SQLAlch. │  │ RateLim  │  │  127.0.0.1:8700  │  │ Registry   │  │
│  async  │  │ L1+L2    │  └────────┬─────────┘  └────────────┘  │
└─────────┘  └──────────┘           │                              │
                                    ▼                              │
                            ┌──────────────────┐                   │
                            │ Lab Instruments   │                   │
                            │ (Serial/TCP)     │                   │
                            │ Sysmex │ Roche   │                   │
                            │ Mindray│ Generic  │                   │
                            └──────────────────┘                   │
                                                                    │
┌───────────────────────────────────────────────────────────────────┘
│
│  ┌────────────────────────────────────────────────────────────────┐
│  │                    EXTERNAL SYSTEMS                              │
│  │                                                                │
│  │  ┌──────────────┐  ┌──────────────┐  ┌────────────────────┐   │
│  │  │ AI PROVIDERS  │  │  GOVERNMENT  │  │  INFRASTRUCTURE    │   │
│  │  │              │  │              │  │                    │   │
│  │  │ Google Gemini│  │ MoI NID API  │  │  Sentry (errors)   │   │
│  │  │ (Gemini 2.0) │  │ Insurance API│  │  FCM (push notif)  │   │
│  │  │ Groq (LLaMA) │  │ Residency API│  │  APNS (iOS push)   │   │
│  │  │ Ollama (self)│  │ SNDHS Health │  │  Prometheus/Grafana│   │
│  │  └──────────────┘  └──────────────┘  │  HAProxy (scale)   │   │
│  │                                       └────────────────────┘   │
│  └────────────────────────────────────────────────────────────────┘
│
│  ┌────────────────────────────────────────────────────────────────┐
│  │                    FRONTEND SUBSYSTEMS                          │
│  │                                                                │
│  │  ┌──────────────┐  ┌──────────┐  ┌───────────┐  ┌──────────┐ │
│  │  │ frontend-v2  │  │ frontend  │  │  client   │  │  edge_   │ │
│  │  │ React SPA    │  │ PWA (HTML)│  │ tRPC SPA  │  │  agent   │ │
│  │  │ (Citizen/    │  │ (Offline) │  │ (Light)   │  │ (Offline)│ │
│  │  │  Doctor/     │  │           │  │           │  │           │ │
│  │  │  Ministry)   │  │           │  │           │  │           │ │
│  │  └──────────────┘  └──────────┘  └───────────┘  └──────────┘ │
│  │                                                                │
│  │  ┌──────────────┐  ┌──────────────┐                           │
│  │  │ Mobile Android│  │  Mobile iOS  │                           │
│  │  │ (Kotlin)     │  │  (Swift)     │                           │
│  │  └──────────────┘  └──────────────┘                           │
│  └────────────────────────────────────────────────────────────────┘
│
│  ┌────────────────────────────────────────────────────────────────┐
│  │              FUTURE MICROSERVICES (services/)                   │
│  │                                                                │
│  │  ┌─────┐ ┌──────┐ ┌───────┐ ┌──────┐ ┌──────┐ ┌────────┐    │
│  │  │ lab │ │ order│ │patient│ │result│ │sample│ │ notif. │    │
│  │  └─────┘ └──────┘ └───────┘ └──────┘ └──────┘ └────────┘    │
│  │  ┌──────┐ ┌──────────────────┐ ┌──────────┐                   │
│  │  │  ai  │ │autonomous_manager│ │  shared  │                   │
│  │  └──────┘ └──────────────────┘ └──────────┘                   │
│  └────────────────────────────────────────────────────────────────┘
```

---

## References

| Document | Location | Content |
|---|---|---|
| Architecture Overview | `ARCHITECTURE.md` | Deployment architecture, middleware stack, component architecture |
| Developer Guide | `CLAUDE.md` | Request lifecycle, middleware order, monolith vs microservices, feature flags |
| Canonical Architecture | `docs/architecture/CANONICAL_ARCHITECTURE.md` | Layer architecture, canonical component map, security invariants |
| ADR Index | `docs/adr/README.md` | 23 architecture decision records |
| Deployment Guide | `DEPLOYMENT_PLATFORMS.md` | Deployment targets (Docker Compose, Kubernetes, DigitalOcean, Render, Supabase) |
| Production Deployment | `PRODUCTION_DEPLOYMENT.md` | Production deployment procedures |
| Operations Guide | `OPERATIONS.md` | Operations procedures, kill switch, scaling |
| SNDHS Spec | `docs/sndhs/` | 22-file SNDHS architecture & deployment specification |
| SNDHS Runbook | `docs/sndhs/phase1/RUNBOOK.md` | SNDHS Phase 1 production deployment guide |
| Identity Architecture | `IDENTITY_ARCHITECTURE.md` | Full identity architecture with layer diagram |
| Security Model | `SECURITY_MODEL.md` | Controls by layer |
| Tenant Model | `TENANT_MODEL.md` | Multi-level tenant hierarchy |
| Self-Audit Agent | `scripts/self_audit_agent.py` | Claude-powered codebase self-audit |
| Enterprise Certification | `ENTERPRISE_PRODUCTION_CERTIFICATION_REPORT.md` | Enterprise governance certification |
