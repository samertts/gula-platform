# GULA PLATFORM — MASTER SYSTEM ATLAS

> **Generated:** 2026-07-17
> **Version:** 2.1.0 (codebase), v2.3.2 (changelog)
> **Audit Type:** Comprehensive system inspection (MISSION-026)
> **Status:** Complete

---

## TABLE OF CONTENTS

1. [Repository Atlas](#1-repository-atlas)
2. [Architecture Atlas](#2-architecture-atlas)
3. [Healthcare Atlas](#3-healthcare-atlas)
4. [Application Atlas](#4-application-atlas)
5. [Database Atlas](#5-database-atlas)
6. [API Atlas](#6-api-atlas)
7. [Security Atlas](#7-security-atlas)
8. [Infrastructure Atlas](#8-infrastructure-atlas)
9. [AI Atlas](#9-ai-atlas)
10. [Documentation Atlas](#10-documentation-atlas)
11. [Compliance Atlas](#11-compliance-atlas)
12. [Testing Atlas](#12-testing-atlas)
13. [Future Roadmap Atlas](#13-future-roadmap-atlas)
14. [Risk Atlas](#14-risk-atlas)
15. [Technical Debt Atlas](#15-technical-debt-atlas)
16. [Missing Components Atlas](#16-missing-components-atlas)
17. [Recommendations Atlas](#17-recommendations-atlas)
18. [Final Report](#18-final-report)

---

## 1. REPOSITORY ATLAS

### 1.1 Repository Overview

| Metric | Value |
|--------|-------|
| Repository root | `/home/samertts/workspace/projects/gula-platform` |
| Git commits | 467 |
| Git branches | 1 active (`main`) + 27 remote (claude/*, codex/*, fix/*) |
| Git tags | `deployment-platform-v1.0` |
| Total files (excl. cache, venv, archives) | **3,709** |
| Total directories (same exclusions) | **1,421** |
| Primary language | Python (60.5%) |
| Secondary languages | HTML (12.7%), Markdown (11.3%), TSX (10.2%), TypeScript (6.1%) |
| Monorepo | Yes — 3 merged repositories |

### 1.2 File Count by Type

| File Type | Count | Percentage |
|-----------|-------|------------|
| Python (`.py`) | 2,243 | 60.5% |
| HTML (`.html`) | 472 | 12.7% |
| Markdown (`.md`) | 420 | 11.3% |
| TSX (`.tsx`) | 380 | 10.2% |
| TypeScript (`.ts`) | 225 | 6.1% |
| YAML (`.yml`/`.yaml`) | 144 | 3.9% |
| Shell scripts (`.sh`) | 118 | 3.2% |
| JSON (non-node_modules) | 96 | 2.6% |
| Terraform (`.tf`/`.tfvars`) | 62 | 1.7% |
| JavaScript (`.js`) | 44 | 1.2% |
| Dart (`.dart`) | 21 | 0.6% |
| Kotlin (`.kt`/`.kts`) | 20 | 0.5% |
| Dockerfiles | 14 | 0.4% |
| SQL (`.sql`) | 14 | 0.4% |
| CSS/SCSS | 9 | 0.2% |
| TOML (`.toml`) | 5 | 0.1% |
| SVG | 2 | 0.05% |

### 1.3 Top-Level Directory Structure

```
gula-platform/
├── ai/                          # AI modules (top-level)
├── architecture/                # Architecture documentation
├── archive/                     # Deprecated/experimental code
├── assessment/                  # Assessment reports & tools
├── backend/                     # Core monolith (FastAPI)
│   ├── app/                     # Application code (1,561 Python files)
│   ├── migrations/              # Alembic migrations (46 files)
│   ├── tests/                   # Backend tests (100+ files)
│   ├── core/                    # Service stubs
│   ├── services/                # Microservice stubs
│   └── cache/                   # Cache layer
├── cli/                         # CLI tools
├── client/                      # tRPC + React SPA
├── cloudflare/                  # Cloudflare config
├── config/                      # Infrastructure configs (34 subdirectories)
├── contracts/                   # API contracts, SDKs, standards
├── data/                        # Data files
├── database/                    # DB scripts
├── digitalocean/                # DigitalOcean deployment config
├── docs/                        # All documentation (27 subdirectories)
├── docker/                      # Docker files
├── edge_agent/                  # Offline edge computing agent
├── frontend/                    # Static HTML PWA
├── frontend-v2/                 # React 19 + Firebase SPA
├── helm/                        # Helm chart
├── hospital_desktop/            # Desktop application
├── k6/                          # Load testing scripts
├── k8s/                         # Kubernetes manifests
├── nhop-platform/               # National Health Oversight Platform
├── packages/                    # Shared packages
│   └── uap/                     # Unified Application Platform
├── platform/                    # Multi-app platform
│   ├── ai/                      # AI governance (TypeScript)
│   ├── apps/                    # 8 application modules
│   ├── ui/                      # Design system
│   └── update/                  # Update system
├── reports/                     # Generated reports
├── sample_tracking/             # Sample tracking desktop
├── scripts/                     # Operations scripts (118 files)
├── services/                    # Microservices (decomposed)
│   ├── ai/                      # AI microservice
│   ├── autonomous_manager/      # Autonomous manager
│   ├── device_bridge/           # LabLink-Core (Lab instrument integration)
│   ├── lab/                     # Lab microservice
│   ├── notification/            # Notification microservice
│   ├── order/                   # Order microservice
│   ├── patient/                 # Patient microservice
│   ├── result/                  # Result microservice
│   ├── sample/                  # Sample microservice
│   └── shared/                  # Shared microservice library
├── shared/                      # Canonical shared library (100+ files)
├── supabase/                    # Supabase config
├── terraform/                   # Terraform (5 environments, 12 modules)
└── tests/                       # Top-level tests (chaos, load, stress, etc.)
```

### 1.4 Package Managers & Dependency Files

| File | Purpose |
|------|---------|
| `requirements.txt` | Backend Python production deps |
| `requirements-dev.txt` | Backend Python dev/test deps |
| `requirements-lock.txt` | Pinned Python dependencies |
| `pyproject.toml` | Python project metadata |
| `setup.py` | Legacy setup |
| `package.json` (root) | tRPC SPA + Express server |
| `pnpm-workspace.yaml` | pnpm workspace config |
| `packages/uap/package.json` | UAP shared library |
| `platform/*/package.json` | 8 platform applications |
| `contracts/sdk/typescript/package.json` | TypeScript SDK |
| `services/device_bridge/pyproject.toml` | Device bridge Python project |
| `shared/pyproject.toml` | Shared library Python project |

---

## 2. ARCHITECTURE ATLAS

### 2.1 Architecture Style

| Dimension | Finding | Evidence |
|-----------|---------|----------|
| **Primary style** | Monolith-first with microservices decomposition path | `backend/app/` is the production monolith; `services/` contains 8 microservice stubs |
| **ADR-002** | Monolith-first explicitly chosen | `docs/adr/ADR-002-monolith-first.md` |
| **Layered architecture** | Yes — routes → services → domain → models | All route/service/domain modules organized accordingly |
| **DDD patterns** | Partial — bounded contexts in capabilities, domain entities, events | `backend/app/capabilities/` has commands/queries/events subpackages |
| **CQRS** | Partial — command/query separation in capabilities | 10 capability modules have `commands/` and `queries/` subdirectories |
| **Event-driven** | Yes — event bus, outbox pattern, dead letter queue, inbox | `backend/app/kernel/event_bus/` (10 files) |
| **Hexagonal/Ports & Adapters** | Partial — integration module uses application/domain/infrastructure + ports/adapters | `backend/app/integration/` |
| **Plugin architecture** | Yes — kernel has plugin manager, marketplace, sandbox, hot-reload | `backend/app/kernel/plugin/` (8 files) |
| **Clean Architecture** | Partial — some modules follow domain/application/infrastructure/api split | `biomedical/`, `blood_bank/`, `command_center/`, `critical_care/`, `ems/`, `public_health/` |

### 2.2 Module Counts by Layer

| Layer | Submodules | File Count |
|-------|-----------|------------|
| **Routes** (API layer) | 1 directory | 52 files |
| **Models** (Data layer) | 1 directory + 5 subdirectories | 25 + 20+ EHR/hospital models |
| **Services** (Business logic) | 3 directories | 15+ files |
| **Core** (Infrastructure) | 1 directory | 15 modules |
| **Security** | 1 directory | 15 files |
| **Kernel** (Platform engine) | 10 subpackages | 100 files |
| **Capabilities** (Bounded contexts) | 10 modules | 60+ files (commands/queries/events/tests) |
| **Engineering** (Code generation) | 15 subpackages | 52 files |
| **Integration** (External systems) | 10 subpackages | 50+ files |
| **National** (Government layer) | 15+ subpackages | 150+ files |
| **Healthcare domains** | 15 modules | ~180 files |
| **AI Fabric** | 1 module | 25 files |
| **Shared library** | 35 subpackages | 100+ files |
| **Total backend app** | 66 directories | **1,561 Python files** |

### 2.3 Request Lifecycle

```
Internet → Host nginx (TLS) → api-gateway (Docker nginx :8080) → 
  gula-backend (FastAPI, Gunicorn+Uvicorn, :8000) → PostgreSQL 16 + Redis 7
```

**Middleware stack (11 layers in order):**
1. `MaxBodySizeMiddleware` — 413 above 10 MB
2. `RequestIDMiddleware` — X-Request-ID correlation
3. `DocsAuthMiddleware` — guards /docs /redoc in production
4. `CORSMiddleware`
5. `RequestTimingMiddleware` — access log + X-Response-Time
6. `SecurityHeadersMiddleware` — CSP, HSTS, X-Frame-Options
7. `GZipMiddleware`
8. `ReadinessMiddleware` — 503 until `system_ready`
9. `DegradedModeMiddleware` — circuit breaker rejection
10. `KernelMiddleware` — kernel context
11. `ConcurrencyLimitMiddleware` — in-flight cap (clinical writes exempt)

### 2.4 Self-Healing System (3 Layers)

| Layer | Mechanism | File |
|-------|-----------|------|
| **Circuit Breaker** | Tracks consecutive failures, opens/closes circuit | `core/self_healing.py` |
| **Auto-Repair Engine** | GC, pool recycle, reconnects | `core/auto_repair.py` |
| **Adaptive Concurrency** | Halves in-flight on slow DB, restores on fast | `main.py::_adaptive_concurrency_loop` |

### 2.5 Runtime Modes

| Mode | Purpose | Background Tasks |
|------|---------|------------------|
| `api` | FastAPI HTTP server | No |
| `worker` | Background worker (outbox, recovery, repair) | Yes |
| `test` | Pytest runtime | Never |
| `cli` | One-shot scripts | No |

### 2.6 Dependency Graph (High Level)

```
frontend-v2/ ──HTTP──→ api-gateway ──→ gula-backend ──→ PostgreSQL
client/      ──HTTP──→ api-gateway ──→ gula-backend ──→ Redis 7
platform/apps/ ──HTTP──→ api-gateway ──→ gula-backend ──→ (Firebase for auth)

services/device_bridge/ ──ASTM/HL7──→ Lab instruments
services/device_bridge/ ──HTTP──→ gula-backend (via gula_client.py)

edge_agent/ ──sync──→ gula-backend

nhop-platform/ ──HTTP──→ gula-backend (integration)
```

### 2.7 Circular Dependencies

| Source | Target | Risk Level |
|--------|--------|------------|
| `backend/app/models/` imports `backend/app/database` | Low — expected (models need Base) |
| `backend/app/core/startup_guard` imports `backend/app/database` | Low — expected |
| `shared/` imports several `backend/app/` modules | **MEDIUM** — `shared/` should be dependency-free |
| `backend/app/config.py` references `shared.config.loader` | Low — import-time only |

---

## 3. HEALTHCARE ATLAS

### 3.1 Healthcare Capabilities Coverage

| Healthcare Domain | Backend Module | Route Files | Models | Status |
|-------------------|---------------|-------------|--------|--------|
| **Laboratory (LIMS)** | `backend/app/lims/` (15 files) | `routes/results.py`, `routes/samples.py`, `routes/test_results.py` | `LabOrder`, `LabResult`, `Sample`, `TestType`, `QualityControl` | **Complete** |
| **Clinical** | `backend/app/clinical/` (12 files) | `routes/clinical.py`, `routes/clinical_orders.py`, `routes/clinical_documentation.py`, `routes/clinical_quality.py` | CDS models, knowledge, quality, terminology | **Complete** |
| **Radiology** | `backend/app/radiology/` (9 files) | `routes/radiology.py` (in platform) | PACS, imaging, device integration | **Present** |
| **Nursing** | `backend/app/nursing/` (8 files) | `routes/nursing.py` (in platform) | Medication admin, coordination | **Present** |
| **Pharmacy** | `backend/app/pharmacy/` (9 files) | `routes/pharmacy.py` (in platform) | Dispensing, inventory, clinical checks | **Present** |
| **Hospital** | `backend/app/hospital/` (3 files) | `routes/hospital.py` | Bed, bed assignment, building, campus, clinic, cost center | **Present** |
| **Blood Bank** | `backend/app/blood_bank/` (13 files) | API routes | Donor, transfusion, compatibility, inventory | **Present** |
| **Biomedical Engineering** | `backend/app/biomedical/` (12 files) | API routes | Equipment maintenance, calibration, inventory | **Present** |
| **Critical Care** | `backend/app/critical_care/` (12 files) | API routes | ICU, monitoring, alerts | **Present** |
| **EMS (Emergency)** | `backend/app/ems/` (12 files) | API routes | Dispatch, ambulance, triage | **Present** |
| **Public Health** | `backend/app/public_health/` (12 files) | API routes | Surveillance, epidemiology, reporting | **Present** |
| **Care Continuum** | `backend/app/care_continuum/` (12 files) | Route modules | Care journey, chronic disease, immunization, maternal health, referral, primary care | **Present** |
| **EHR** | `backend/app/ehr/` (15 files) | `routes/ehr.py`, `routes/ehr_fhir.py` | Allergies, attachments, care plans, clinical notes, medications, immunizations, family history | **Present** |
| **Citizen Portal** | `backend/app/citizen_platform/` (22 files) | Route modules | PHR, appointments, telemedicine, emergency, family, offline | **Present** |
| **Research** | `backend/app/research_platform/` (19 files) | Route modules | Data science, epidemiology, GIS, registries, precision health | **Present** |
| **National Health** | `backend/app/national/` (150+ files) | Multiple route modules | Identity, FHIR, security, observability, workflows, rules, search, scheduling | **Present** |
| **NHOP** | `nhop-platform/` (36 files) | API v1 routes | Citizen registry, outbreak detection, test results | **Present** |

### 3.2 Medical Specialties Covered

| Specialty | Coverage | Evidence |
|-----------|----------|----------|
| Clinical Pathology | **Complete** | LIMS, lab orders, results, quality control |
| Hematology | **Present** | Blood bank module, lab results |
| Microbiology | **Present** | Lab results, public health surveillance |
| Clinical Chemistry | **Present** | Lab results, test types |
| Immunology | **Present** | Lab results |
| Radiology/Imaging | **Present** | Radiology module, PACS, DICOM viewer (Cornerstone.js) |
| Emergency Medicine | **Present** | EMS module, triage, critical alerts |
| Critical Care | **Present** | Critical care module, ICU |
| Cardiology | **Partial** | EHR clinical notes, no dedicated cardiology module |
| Neurology | **Partial** | EHR clinical notes, no dedicated neurology module |
| Obstetrics/Gynecology | **Partial** | Maternal health in care_continuum |
| Pediatrics | **Partial** | Family health in citizen platform |
| Oncology | **Partial** | Research platform, no dedicated oncology module |
| Ophthalmology | **Missing** | No dedicated module |
| Dermatology | **Missing** | No dedicated module |
| Psychiatry | **Missing** | No dedicated module |
| Orthopedics | **Missing** | No dedicated module |
| Anesthesiology | **Missing** | No dedicated module |
| Surgery | **Missing** | No surgical module |
| Dentistry | **Missing** | No dental module |
| Nutrition/Dietetics | **Missing** | No module |
| Physical Therapy | **Missing** | No module |

### 3.3 Medical Standards Implementation

| Standard | Implementation | Status |
|----------|---------------|--------|
| **ASTM** | `backend/app/lims/integration/astm.py`, `services/device_bridge/app/parsers/astm_basic.py`, `contracts/astm/protocol.json` | **Present** |
| **HL7 v2** | `backend/app/lims/integration/hl7.py`, `services/device_bridge/app/parsers/`, `contracts/hl7/protocol.json` | **Present** |
| **FHIR R4** | `backend/app/capabilities/fhir_interoperability/`, `backend/app/certification/dimensions/fhir_compliance.py`, `backend/app/contracts/fhir.py`, `backend/app/integration/gateway/fhir_gateway.py`, `contracts/fhir/` | **Present** |
| **LOINC** | **NOT FOUND** — no LOINC code systems, mappings, or references | **Missing** |
| **SNOMED CT** | **NOT FOUND** — no SNOMED CT code systems or mappings | **Missing** |
| **ICD-10** | **NOT FOUND** — no ICD-10 code systems | **Missing** |
| **DICOM** | `@cornerstonejs/core` in radiology app package.json | **Present** (frontend only) |

### 3.4 Key Finding: LOINC/SNOMED/ICD-10 Gap

**Evidence:** grep for LOINC, SNOMED, ICD-10 across 25 model files returned zero results. grep across routes returned zero for LOINC/SNOMED. No terminology mapping tables exist in migrations or models.

This means the platform can store lab results but **cannot semantically code them** with standard medical terminology — a critical gap for:

- Interoperability with other healthcare systems
- National health data aggregation
- Clinical decision support
- Regulatory compliance
- International data exchange

---

## 4. APPLICATION ATLAS

### 4.1 Application Inventory

| Application | Location | Framework | Status |
|------------|----------|-----------|--------|
| **Backend API** | `backend/app/` | FastAPI (Python 3.11) | **Production** |
| **Citizen Portal** | `frontend-v2/` | React 19 + Firebase + Vite | **Production** |
| **Doctor Workspace** | `frontend-v2/` (views/doctor) | React 19 + Firebase + Vite | **Production** |
| **Lab Dashboard** | `frontend-v2/` (views/lab) | React 19 + Firebase + Vite | **Production** |
| **Ministry Command Centre** | `frontend-v2/` (views/ministry) | React 19 + Firebase + Vite | **Production** |
| **Admin Panel** | `frontend-v2/` (views/admin) | React 19 + Firebase + Vite | **Production** |
| **Research Portal** | `frontend-v2/` (views/research) | React 19 + Firebase + Vite | **Development** |
| **Static PWA** | `frontend/` | Vanilla HTML/CSS/JS | **Production** |
| **tRPC SPA** | `client/` | React 18 + tRPC + Vite | **Development** |
| **Citizen App** | `platform/apps/citizen/` | React 19 PWA + Firebase + Workbox | **Development** |
| **Doctor App** | `platform/apps/doctor/` | React 19 PWA + Workbox | **Development** |
| **Hospital App** | `platform/apps/hospital/` | React 19 PWA + Workbox | **Development** |
| **Laboratory App** | `platform/apps/laboratory/` | React 19 PWA + QR scanning | **Development** |
| **Ministry App** | `platform/apps/ministry/` | React 19 + Recharts + PDF export | **Development** |
| **Nurse App** | `platform/apps/nurse/` | React 19 PWA + Workbox | **Development** |
| **Pharmacy App** | `platform/apps/pharmacy/` | React 18 + QR scanning | **Development** |
| **Radiology App** | `platform/apps/radiology/` | React 18 + Cornerstone.js DICOM | **Development** |
| **Hospital Desktop** | `hospital_desktop/` | Python desktop app | **Development** |
| **Sample Tracking** | `sample_tracking/` | Python desktop app | **Development** |
| **Edge Agent** | `edge_agent/` | Python CLI agent | **Development** |
| **National Platform (NHOP)** | `nhop-platform/` | FastAPI (separate app, port 8100) | **Production** |
| **CLI Tools** | `contracts/sdk/cli/`, `cli/` | Python CLI | **Development** |
| **TypeScript SDK** | `contracts/sdk/typescript/` | TypeScript + Axios | **Development** |
| **Dart SDK** | `contracts/sdk/dart/` | Dart | **Development** |
| **Kotlin SDK** | `contracts/sdk/kotlin/` | Kotlin | **Development** |
| **Python SDK** | `contracts/sdk/python/` | Python | **Development** |
| **Device Bridge** | `services/device_bridge/` | Python (LabLink-Core) | **Production** |
| **AI Services (micro)** | `services/ai/` | Python FastAPI | **Development** |
| **Autonomous Manager** | `services/autonomous_manager/` | Python | **Development** |
| **Lab Service (micro)** | `services/lab/` | Python FastAPI | **Stub** |
| **Order Service (micro)** | `services/order/` | Python FastAPI | **Stub** |
| **Patient Service (micro)** | `services/patient/` | Python FastAPI | **Stub** |
| **Result Service (micro)** | `services/result/` | Python FastAPI | **Stub** |
| **Sample Service (micro)** | `services/sample/` | Python FastAPI | **Stub** |
| **Notification Service (micro)** | `services/notification/` | Python FastAPI | **Stub** |

### 4.2 Missing Applications

| Application | Status | Why Missing |
|------------|--------|-------------|
| **Radiology PACS Viewer** | **Partial** | Only in platform/radiology app (development) — no production PACS |
| **Blood Bank Management** | **Partial** | Backend module exists but no frontend application |
| **Ambulance/EMS Dispatch** | **Partial** | Backend module exists but no frontend dispatch UI |
| **HR System** | **Missing** | No HR module anywhere in codebase |
| **Finance/Billing (Phase B+)** | **Planned** | Financial engine schema-only, routes deferred to Phase B+ |
| **Training/Learning** | **Missing** | No training module |
| **Maintenance/Facilities** | **Missing** | No maintenance module (biomedical covers equipment only) |
| **Ward Management** | **Missing** | No dedicated ward management module |
| **Operating Theatre/Surgery** | **Missing** | No surgical module |
| **Patient Billing** | **Missing** | Financial schema exists but no patient billing |
| **Insurance Claims (Phase B+)** | **Partial** | Claims model exists, routes in development |
| **Telemedicine** | **Partial** | `citizen_platform/telemedicine.py` exists but limited |
| **Population Health** | **Partial** | Research platform covers some aspects |

---

## 5. DATABASE ATLAS

### 5.1 Core Models

| Model | Table | Purpose |
|-------|-------|---------|
| `Lab` | `labs` | Laboratory organization |
| `LabUser` | `lab_users` | User accounts per lab |
| `Patient` | `patients` | Patient records |
| `LabOrder` | `lab_orders` | Test orders |
| `LabResult` | `lab_results` | Test results (with optimistic locking via version) |
| `Sample` | `samples` | Physical samples |
| `TestType` | `test_types` | Defined test types |
| `User` | `users` | System users |
| `AuditLog` | `audit_logs` | Immutable audit trail |
| `OutboxEvent` | `outbox_events` | Transactional outbox |
| `Subscription` | `subscriptions` | Tenant subscription tiers |
| `FeatureFlag` | `feature_flags` | Per-tenant feature flags |
| `QualityControl` | `quality_control` | QC data |
| `Consent` | `consent` | Patient consent records |
| `EdgeDevice`, `EdgeTask`, `EdgePolicy` | `edge_*` | Edge computing devices |

### 5.2 Extended Models

| Model Group | Tables | Purpose |
|-------------|--------|---------|
| **Claims** | `claims`, `claim_items` | Insurance claims |
| **MPI/Citizen** | `citizens`, `identity_claims`, `merge_audit` | Master Patient Index |
| **Canonical** | `canonical_patients`, `patient_links`, `citizen_links` | Unified patient registry |
| **OAuth2** | `oauth2_clients`, `oauth2_tokens` | OAuth2 provider |
| **Service Accounts** | `service_accounts` | API service accounts |
| **MFA** | `mfa_devices` | Multi-factor auth |
| **Organization** | `organizations`, `facilities`, `appointments` | Multi-org hierarchy |
| **AI** | `ai_interactions`, `ai_feedback`, `ai_retrieval_refs` | AI audit trail |
| **Med Term** | `medical_terminology_normalized` | Terminology normalization |
| **EHR** | Clinical notes, allergies, medications, immunizations, etc. | Electronic Health Record |
| **Hospital** | Beds, bed assignments, buildings, campuses, clinics, cost centers | Hospital operations |
| **Care Continuum** | Care journeys, chronic diseases, immunizations, maternal health, referrals, primary care, public health | Longitudinal care |
| **National Data** | Canonical documents, encounters, medications, observations, procedures | National health data |
| **Warehouse** | Dimension tables (date, facility, patient, provider), fact tables (diagnosis, lab result, patient visit) | Data warehouse |
| **Event Store** | Stored events, event snapshots, retention policies | Event sourcing |
| **Governance** | Data catalog, lineage, quality, classification, stewardship | Data governance |
| **MDM** | Golden records, duplicate records, source systems, provider/location/terminology/device registries | Master data management |
| **SNDHS** | Visits, lab_orders.visit_id, national_id, sndhs_health_id | Government integration |

### 5.3 Migration Summary

| Category | Migration Files | Date Range |
|----------|----------------|------------|
| Base schema | 1 | 2025-03-22 |
| Core features | 10 | 2025-03-22 to 2025-03-29 |
| Claims, MPI, Consent, Edge | 4 | 2026-04 |
| SNDHS Phase 1 | 6 | 2026-05-05 |
| Financial Phase A | 1 | 2026-05-06 |
| AI safety/interactions | 2 | 2026-05-11 |
| National platforms | 16 | 2026-07-14 to 2026-07-16 |
| Governance/security/auth | 3 | 2026-07-16 |
| Canonical patient | 1 | 2026-07-16 |
| **Total** | **46** | **2025-03-22 to 2026-07-16** |

### 5.4 Database Technology Stack

| Component | Technology | Configuration |
|-----------|------------|---------------|
| Primary database | PostgreSQL 16 | `config/postgres/postgresql.conf` |
| Connection pooling | SQLAlchemy pool (WEB_CONCURRENCY × (DB_POOL_SIZE + DB_MAX_OVERFLOW) < max_connections) | `database.py` |
| Cache | Redis 7 | `config/redis/redis.conf` |
| Failover | Patroni (config only) | `config/postgres-ha/patroni.yml` |
| Connection pooler | PgBouncer (config only) | `config/pgbouncer/` |
| Read replicas | Supported via `READ_REPLICA_URL` | `config.py` |
| HA Redis | Sentinel + Cluster (configs only) | `config/redis-sentinel/`, `config/redis-cluster/` |

### 5.5 Key Database Design Observations

| Observation | Details |
|-------------|---------|
| **Idempotent migrations** | All migrations use `_table_exists()`, `_has_column()`, `_index_exists()` guards |
| **Optimistic locking** | `LabResult` uses `version` column for concurrency control |
| **Audit hash chain** | `AuditLog` has immutable chain with linked hashes |
| **Tenant isolation** | All patient-data queries filter by `lab_id` |
| **Encryption at rest** | `patients.national_id` encrypted with `NID_HMAC_KEY` |
| **No partitioning** | No table partitioning found in any migration |
| **No views** | No SQL views found |
| **No triggers** | No database triggers found (logic is in app layer) |
| **No stored procedures** | All logic in application layer |

---

## 6. API ATLAS

### 6.1 Route Modules

**52 route files** in `backend/app/routes/`:

| Route File | Prefix/Path | Purpose |
|-----------|-------------|---------|
| `login.py` | `/login` | Authentication |
| `register.py` | `/register` | User registration |
| `labs.py` | `/labs` | Lab management |
| `patients.py` | `/patients` | Patient CRUD |
| `results.py` | `/results` | Test results |
| `test_results.py` | `/test-results` | Test result management |
| `samples.py` | `/samples` | Sample tracking |
| `dashboard.py` | `/dashboard` | Lab dashboard |
| `stats.py` | `/stats` | Statistics & trends |
| `ai.py` | `/ai` | Clinical AI |
| `ai_telemetry.py` | `/ai/telemetry` | AI monitoring |
| `admin.py` | `/admin` | Admin operations |
| `security.py` | `/security` | Security settings |
| `qr.py` | `/qr` | QR code operations |
| `id_scan.py` | `/id-scan` | ID scanning |
| `identity.py` | `/identity` | Identity management |
| `patient_card.py` | `/patient-card` | Patient digital cards |
| `ehr.py` | `/ehr` | Electronic Health Records |
| `ehr_fhir.py` | `/ehr/fhir` | FHIR EHR endpoints |
| `clinical.py` | `/clinical` | Clinical operations |
| `clinical_orders.py` | `/clinical/orders` | Clinical orders |
| `clinical_documentation.py` | `/clinical/documentation` | Clinical documentation |
| `clinical_quality.py` | `/clinical/quality` | Clinical quality |
| `care_continuum.py` | `/care-continuum` | Care continuum |
| `hospital.py` | `/hospital` | Hospital operations |
| `compliance.py` | `/compliance` | Regulatory compliance |
| `consent.py` | `/consent` | Patient consent |
| `critical_alerts.py` | `/critical-alerts` | Critical lab alerts |
| `batch.py` | `/batch` | Batch operations |
| `device_results.py` | `/device-results` | Device result ingestion |
| `quality_control.py` | `/quality-control` | QC management |
| `mobile.py` | `/mobile` | Mobile API |
| `notifications.py` | `/notifications` | Notifications |
| `metrics.py` | `/metrics` | Prometheus metrics |
| `tiers.py` | `/tiers` | Subscription tiers |
| `citizen_portal.py` | `/citizen` | Citizen portal API |
| `claims.py` | `/claims` | Insurance claims |
| `national_identity.py` | `/national/identity` | National identity |
| `insurance.py` | `/insurance` | Insurance integration |
| `national_data.py` | `/national/data` | National health data |
| `national_streaming.py` | `/national/streaming` | National data streaming |
| `optimizer.py` | `/optimizer` | System optimizer |
| `integrations.py` | `/integrations` | External integrations |
| `edge.py` | `/edge` | Edge platform |
| `mfa.py` | `/mfa` | Multi-factor auth |
| `password_reset.py` | `/password-reset` | Password reset |
| `oauth2.py` | `/oauth2` | OAuth2 provider |
| `saml.py` | `/saml` | SAML SSO |
| `service_accounts.py` | `/service-accounts` | API keys/service accounts |
| `setup.py` | `/setup` | Initial setup |
| `canonical_patient.py` | `/canonical-patient` | Unified patient lookup |

### 6.2 Additional Route Registrations

**79 total `app.include_router()` calls** in `main.py` covering:
- National platform (notification, document, scheduling, search, observability, background, workflow, task)
- Kernel routes
- Governance + analytics
- LIMS
- Rules, workflows, tasks
- Platform routes
- Contracts
- Connectors
- Hospital
- NHDW
- Nursing, pharmacy, radiology
- Simulation, command intelligence, knowledge graph
- Roadmap, health data, control plane, runtime kernel
- Citizen platform, AI fabric

### 6.3 Health Endpoints

| Path | Purpose |
|------|---------|
| `/health` | Liveness |
| `/health/live` | Liveness (alias) |
| `/health/ready` | Readiness (Docker healthcheck) |
| `/health/status` | Diagnostics |
| `/health/deep` | Grade + latency + memory |

### 6.4 SDK Clients

| SDK | Language | Location |
|-----|----------|----------|
| CLI | Python | `contracts/sdk/cli/` |
| Client | Dart | `contracts/sdk/dart/` |
| Client | Kotlin | `contracts/sdk/kotlin/` |
| Client | Python | `contracts/sdk/python/` |
| Client | TypeScript | `contracts/sdk/typescript/` |

### 6.5 API Documentation

| Format | Location | Status |
|--------|----------|--------|
| OpenAPI 3.0 | Auto-generated by FastAPI | **Active** |
| AsyncAPI | `contracts/export/asyncapi.json` | **Draft** |
| OpenAPI export | `contracts/export/openapi.json` | **Draft** |
| FHIR Capability Statement | `contracts/fhir/capability-statement.json` | **Present** |

---

## 7. SECURITY ATLAS

### 7.1 Authentication

| Mechanism | Implementation | Status |
|-----------|---------------|--------|
| JWT (HS256) | `security/auth.py` - `python-jose` | **Production** |
| Refresh token rotation | Token rotation with blacklist | **Production** |
| Password hashing | bcrypt (cost factor 12) via `passlib` | **Production** |
| Token revocation | Redis-backed blacklist | **Production** |
| MFA | `security/mfa_service.py` + `routes/mfa.py` | **Production** |
| OAuth2 provider | `security/oauth2_provider.py` + `routes/oauth2.py` | **Production** |
| SAML SSO | `security/saml_service.py` + `routes/saml.py` | **Production** |
| WebAuthn | `shared/auth/webauthn.py` | **Development** |
| Biometric | `frontend-v2/src/components/BiometricStatus.tsx` | **Frontend only** |

### 7.2 Authorization

| Model | Implementation | Status |
|-------|---------------|--------|
| RBAC | 9 roles: platform_admin, lab_admin, doctor, technician, receptionist, pharmacist, nurse, viewer, edge_agent | **Production** |
| ABAC | `security/abac.py` — Attribute-Based Access Control | **Development** |
| Permissions | 13+ granular permissions per role | **Production** |
| Tenant isolation | `lab_id` filter on all patient-data queries | **Production** |
| Break glass | `governance/repositories/break_glass_repository.py` | **Development** |
| Consent-based | `security/consent_dep.py` | **Development** |

### 7.3 Encryption

| Asset | Method | Key |
|-------|--------|-----|
| National IDs | AES-256 at rest | `NID_HMAC_KEY` (32-byte hex, env var) |
| Data at rest | Fernet (AES-128-CBC + HMAC) | `ENCRYPTION_KEY` (Fernet key, env var) |
| Passwords | bcrypt (one-way hash) | Cost factor 12 |
| JWT tokens | HS256 | `SECRET_KEY` (env var) |
| Patient card tokens | HMAC-signed | `SECRET_KEY` |
| Device communication | HMAC | `DEVICE_HMAC_KEY` |
| Transport | TLS | Host nginx termination |

### 7.4 Audit

| Feature | Implementation | File |
|---------|---------------|------|
| Hash-chain audit | Immutable linked hashes | `models/audit_log.py` |
| All mutations logged | user_id, lab_id, timestamp, action, resource | `audit/audit_log.py` |
| Audit integrity verification | Endpoint to verify chain | `routes/security.py` |
| SNDHS audit v2 | Enhanced with SNDHS correlation fields | Migration `20260505_0005` |

### 7.5 Security Infrastructure

| Component | Implementation | Status |
|-----------|---------------|--------|
| Rate limiting | Redis-backed, per-user, per-endpoint | `security/rate_limit.py` |
| Intrusion detection | Anomaly detection module | `security/intrusion_detection.py` |
| API firewall | Request filtering | `firewall/api_firewall.py` |
| Security headers | CSP, HSTS, X-Frame-Options, X-Content-Type-Options | `main.py` middleware |
| CORS | Production origins only | `main.py` middleware |
| Secrets management | Environment variables, no hardcoded secrets | `config.py` |
| Weak secret detection | `_is_weak_secret()` in config.py | `config.py` |
| Security scanning | Bandit, Gitleaks, Hadolint, Trivy | CI pipeline |

### 7.6 Security Gaps

| Gap | Risk | Evidence |
|-----|------|----------|
| **ABAC not fully implemented** | Medium | `security/abac.py` exists but routes not migrated |
| **No PKI** | Medium | No certificate management for internal services |
| **No key rotation** | Medium | No automated key rotation mechanism |
| **No Zero Trust architecture** | Medium | `config/zero-trust/` has configs only, not enforced |
| **Bandit medium findings** | Low | `0.0.0.0` bindings in dev mode integration config |
| **268 test fixture errors** | Low | Tenant isolation matrix tests have fixture issues (test infrastructure) |
| **No penetration testing results** | Medium | No pen-test evidence found |
| **SAML/OAuth2 not fully tested** | Medium | Route modules exist but limited security tests |

---

## 8. INFRASTRUCTURE ATLAS

### 8.1 Deployment Platforms

| Platform | Config File | Status |
|----------|-------------|--------|
| Docker Compose (MVP) | `docker-compose.yml` | **Primary** |
| Docker Compose (Full) | `docker-compose.full.yml` | Available |
| Docker Compose (Scale) | `docker-compose.scale.yml` | Available |
| Kubernetes | `k8s/` (base + 4 overlays) | Available |
| Helm | `helm/gula-platform/` (35 templates) | Available |
| DigitalOcean App Platform | `digitalocean/app.yaml` | Available |
| Render | `render.yaml` | Available |
| Supabase | `supabase/` | Available |
| Cloudflare | `cloudflare/` (workers, DNS) | Available |
| Terraform | `terraform/` (5 environments) | Available |

### 8.2 Container Infrastructure

| Service | Image Base | Resource Limits |
|---------|-----------|-----------------|
| `postgres` | postgres:16-alpine | 896MB RAM, 1 CPU |
| `redis` | redis:7-alpine | 320MB RAM, 0.5 CPU |
| `gula-backend` | Local/GHCR | 1.5GB RAM, 1.5 CPU |
| `api-gateway` | nginx:alpine | Default |
| `device-bridge` | Python (optional) | Default |

### 8.3 CI/CD Pipeline

**6 GitHub Actions workflows:**

| Workflow | Trigger | Steps |
|----------|---------|-------|
| `ci.yml` | Push/PR to all branches | Syntax gate → Migration check → OpenAPI contract → Backend test → Security scan → Smoke test → Build & push (8 images) |
| `deploy.yml` | Push to main + manual | SSH deploy to DigitalOcean, health check, rollback on failure |
| `blue-green-deploy.yml` | CI success on main | Blue/green slot swap on K8s, smoke test, traffic switch |
| `canary-deploy.yml` | Manual | Gradual traffic shifting |
| `auto-rollback.yml` | CI failure | Automatic rollback to previous commit |
| `quality-gate.yml` | Manual | Quality gate enforcement |

### 8.4 Monitoring Stack

| Component | Configuration | Status |
|-----------|---------------|--------|
| Prometheus | `config/prometheus/prometheus.yml` + alerting rules | **Configured** |
| Grafana | `config/grafana/` (provisioned dashboards + datasources) | **Configured** |
| Loki | `config/loki/loki-config.yml` | **Configured** |
| Promtail | `config/promtail/promtail-config.yml` | **Configured** |
| Tempo (Tracing) | `config/tempo/tempo-config.yml` | **Configured** |
| Jaeger | `config/jaeger/` | **Configured** |
| OpenTelemetry | `config/opentelemetry/otel-collector-config.yml` | **Configured** |
| Alertmanager | `config/alertmanager/alertmanager.yml` | **Configured** |
| Sentry | Optional via `SENTRY_DSN` env var | **Configured** |

### 8.5 Security Infrastructure

| Component | Configuration | Status |
|-----------|---------------|--------|
| SIEM (Elastic) | `config/siem/elastic-security-config.yml` | **Configured** |
| Wazuh agent | `config/siem/wazuh-agent-config.yml` | **Configured** |
| IDS (Snort) | `config/ids/snort-rules/` | **Configured** |
| Cert-manager | `config/cert-manager/` | **Configured** |
| Vault | `config/vault/` | **Configured** |
| Runtime protection | `config/runtime-protection/` | **Configured** |
| Zero Trust | `config/zero-trust/` | **Configured** |

### 8.6 Backup & DR

| Component | Configuration | Status |
|-----------|---------------|--------|
| Database backup | `pg_dump` → `./backups/` via `make backup` | **Configured** |
| Cross-region replication | `config/dr/cross-region-replication.yml` | **Configured** |
| Multi-region topology | `config/multi-region/topology.yaml` | **Planned** |
| HA Postgres | Patroni configuration | **Configured** |
| HA Redis | Sentinel + Cluster configurations | **Configured** |
| HA RabbitMQ | Cluster configuration | **Configured** |
| MinIO HA | `config/minio-ha/` | **Configured** |

### 8.7 Terraform Environments

| Environment | Directory | Purpose |
|-------------|-----------|---------|
| Dev | `terraform/environments/dev/` | Development |
| Staging | `terraform/environments/staging/` | Pre-production |
| Pilot | `terraform/environments/pilot/` | Pilot deployment |
| Production | `terraform/environments/prod/` | Production |
| Disaster Recovery | `terraform/environments/dr/` | DR site |

### 8.8 Infrastructure Gaps

| Gap | Risk | Evidence |
|-----|------|----------|
| **K8s not primary** | Medium | Docker Compose is primary; K8s configs exist but untested in production |
| **Monitoring not live** | Medium | Prometheus/Grafana/Loki/Tempo configs exist but are "opt-in profile" |
| **No CDN configured** | Low | Cloudflare config exists but not fully integrated |
| **DR not tested** | High | DR runbooks and configs exist but no evidence of DR testing |
| **Manual backup only** | Medium | `make backup` is manual; no automated backup schedule |

---

## 9. AI ATLAS

### 9.1 AI Components

| Component | Location | Purpose | Status |
|-----------|----------|---------|--------|
| **AI Fabric** | `backend/app/ai_fabric/` (25 files) | AI agent platform, RAG, governance, observability | **Development** |
| **Clinical AI** | `ai/clinical/clinical_ai/` (5 files) | Clinical decision support, rules engine | **Development** |
| **Population AI** | `ai/population/population_ai/` (6 files) | Population health analytics, trends, prevalence | **Development** |
| **Preventive AI** | `ai/preventive/preventive_ai/` (6 files) | Preventive health analysis | **Development** |
| **Outbreak Detection** | `ai/outbreak/` (1 file) | Disease outbreak detection | **Development** |
| **Lab Business AI** | `ai/lab_business_ai/` (5 files) | Demand prediction, lab activity, top tests | **Development** |
| **Anomaly Detection** | `ai/anomaly_detection.py` | System anomaly detection | **Development** |
| **AI Service (micro)** | `services/ai/main.py` | AI microservice | **Stub** |
| **AI Governance (TS)** | `platform/ai/` (4 files) | Bias detector, explainability, model/prompt registries | **Development** |
| **Knowledge Graph** | `backend/app/knowledge_graph/` (12 files) | Enterprise knowledge graph, service catalog, FHIR catalog | **Development** |
| **AI Routes** | `routes/ai.py` | AI API endpoints | **Development** |
| **AI Telemetry** | `routes/ai_telemetry.py` | AI usage monitoring | **Development** |
| **Sentry Integration** | `main.py` via sentry-sdk | Error tracking for AI | **Production** |

### 9.2 AI Agents

| Agent | File | Purpose |
|-------|------|---------|
| Citizen Agent | `ai_fabric/agents/citizen_agent.py` | Patient-facing AI |
| Clinical Agent | `ai_fabric/agents/clinical_agent.py` | Clinical decision support |
| Engineering Agent | `ai_fabric/agents/engineering_agent.py` | Developer/DevOps AI |
| Laboratory Agent | `ai_fabric/agents/laboratory_agent.py` | Lab operations AI |
| Security Agent | `ai_fabric/agents/security_agent.py` | Security monitoring AI |
| Agent Registry | `ai_fabric/agents/registry.py` | Agent management |

### 9.3 AI Data & Models

| Component | Purpose | Status |
|-----------|---------|--------|
| `AIInteraction` model | Store all AI interactions for audit | **Production** |
| `AIFeedback` model | User feedback on AI outputs | **Production** |
| `AIRetrievalRef` model | RAG retrieval references | **Production** |
| `MedicalTerminologyNormalized` | Normalized medical terms | **Production** |
| National AI data models | Training datasets, synthetic data, vector embeddings, feature store, knowledge graph edges | **Schema only** |
| Vector embeddings | `VectorEmbedding` model | **Schema only** |

### 9.4 AI Gaps

| Gap | Risk | Evidence |
|-----|------|----------|
| **No LLM integration in production** | High | AI fabric routes exist but no active LLM provider integration |
| **No vector database** | High | Vector embeddings schema exists but no vector DB (Qdrant/Pinecone/Weaviate) |
| **No RAG pipeline in production** | High | RAG module exists (`ai_fabric/rag.py`) but no active pipeline |
| **No model serving infrastructure** | High | No model registry or serving infrastructure |
| **No prompt management** | Medium | Prompt registry exists in `platform/ai/` but not integrated |
| **No AI safety testing** | Medium | Hallucination columns exist in schema but no safety testing |
| **No clinical AI validation** | Critical | No FDA/CE/WHO clinical AI validation |
| **No bias auditing** | Medium | Bias detector exists in `platform/ai/` but not active |
| **Gemini/Groq API keys in env** | Medium | API key config exists but no production integration |

---

## 10. DOCUMENTATION ATLAS

### 10.1 Architecture Decision Records

**26 ADRs** in `docs/adr/`:

| ADR | Title | Status |
|-----|-------|--------|
| 001 | Engineering Constitution | **Active** |
| 002 | Monolith-First | **Active** |
| 003 | Multi-Tenant Isolation | **Active** |
| 004 | Skill Platform | **Active** |
| 005 | PostgreSQL + Redis Stack | **Active** |
| 006 | Clinical AI Integration | **Active** |
| 007 | Device Bridge (ASTM/HL7) | **Active** |
| 008 | Patient Card System | **Active** |
| 009 | Self-Healing Infrastructure | **Active** |
| 010 | SNDHS Government Integration | **Active** |
| 011 | Notification Platform | **Active** |
| 012 | Engineering Automation | **Active** |
| 012 | Identity Platform | **Active** |
| 013 | Production Platform | **Active** |
| 014 | Observability Stack | **Active** |
| 015 | Disaster Recovery | **Active** |
| 016 | National EHR | **Active** |
| 017 | National Data Platform | **Active** |
| 018 | National Operations | **Active** |
| 019 | National Ecosystem | **Active** |
| 020 | Citizen Super App | **Active** |
| 021 | National Intelligence | **Active** |
| 022 | Doctor Workspace | **Active** |
| 023 | Laboratory Desktop | **Active** |
| 024 | Platform Constitution | **Active** |

### 10.2 Documentation by Category

| Category | File Count | Coverage |
|----------|-----------|----------|
| Architecture | 5 | Core architecture, entity catalog, knowledge graph, identity, security |
| Database | 1 | Entity deduplication plan |
| AI | 2 | AI architecture, Iraqi healthcare intelligence |
| Operations | 2 | Production launch, zero-downtime upgrades |
| Production | 9 | Deployment, DR, incident response, scaling, security ops, release notes |
| Runbooks | 7 | Backend down, DB down, disk full, high latency, security incident, cert expiry, failed deploy |
| SNDHS | 17 | Full spec (architecture, DB, API, state machines, offline sync, security, events, etc.) |
| National | 11 | ADR, API catalog, architecture, clinical model, FHIR coverage, SBOM, security, workflows |
| Sovereign (10 phases) | 50+ | Interoperability, infrastructure, regulatory, health data, epidemiology, AI governance, health economics, crisis continuity, legal, ecosystem |
| Nursing | 3 | ADR, architecture |
| Pharmacy | 3 | ADR, architecture |
| Radiology | 3 | ADR, architecture |
| Hospital Workspace | 4 | ADR, architecture, deployment, operations |
| Engineering | 7 | Architecture decisions, digital constitution, government readiness, assessment, blueprint, quality gates, risk register, technical debt |
| Platform Freeze Reports | 18 | PI-003, PI-004, PI-005 (architecture, deployment, performance, security, etc.) |
| Templates | 7 | ADR, assessment, decision log, government compliance, risk, technical debt |

### 10.3 Documentation Gaps

| Gap | Risk | Evidence |
|-----|------|----------|
| **No API reference docs** | High | No generated API docs (only FastAPI /docs) |
| **No user manuals** | High | No end-user documentation for any application |
| **No developer getting-started guide** | Medium | `CLAUDE.md` serves as developer guide but no comprehensive onboarding |
| **No testing guide** | Medium | `TESTING.md` exists but not referenced in CONTRIBUTING |
| **No deployment runbook** | Medium | Production docs exist but no step-by-step deployment guide |
| **No clinical safety documentation** | High | No clinical safety case or hazard analysis |
| **No privacy impact assessment** | High | No PIA for patient data processing |
| **No disaster recovery test plan** | Medium | DR docs exist but no DR test plan |

---

## 11. COMPLIANCE ATLAS

### 11.1 Healthcare Standards Compliance

| Standard | Implementation | Verification | Status |
|----------|---------------|--------------|--------|
| **HL7 v2** | ASTM/HL7 parsers in device bridge and LIMS | `contracts/hl7/protocol.json` | **Implementing** |
| **FHIR R4** | FHIR interoperability capability, FHIR gateway, FHIR compliance checker | `contracts/fhir/capability-statement.json`, `contracts/fhir/profiles.json` | **Implementing** |
| **ASTM E1381** | Device bridge ASTM parser | `contracts/astm/protocol.json` | **Implementing** |
| **LOINC** | **NOT FOUND** | No LOINC codes, mappings, or references anywhere | **Not Implemented** |
| **SNOMED CT** | **NOT FOUND** | No SNOMED CT codes or references | **Not Implemented** |
| **ICD-10** | **NOT FOUND** | No ICD-10 codes or references | **Not Implemented** |
| **DICOM** | Cornerstone.js in radiology app | Only in frontend package.json | **Partial** |

### 11.2 Regulatory Compliance

| Framework | Implementation | Verification | Status |
|-----------|---------------|--------------|--------|
| **HIPAA** | **NOT FOUND** | No HIPAA-specific controls or documentation | **Not Addressed** |
| **ISO 27001** | **NOT FOUND** | No ISO 27001 certification evidence | **Not Addressed** |
| **ISO 27799** (Health informatics security) | **NOT FOUND** | No evidence | **Not Addressed** |
| **ISO 15189** (Medical laboratories) | **NOT FOUND** | No evidence of lab accreditation readiness | **Not Addressed** |
| **CLSI** (Clinical lab standards) | **NOT FOUND** | No evidence | **Not Addressed** |
| **WHO** guidelines | **NOT FOUND** | No evidence | **Not Addressed** |
| **CAP** (College of American Pathologists) | **NOT FOUND** | No evidence | **Not Addressed** |
| **Iraqi MoH** regulations | **Partial** | SNDHS integration suggests MoH alignment | **Assumed** |
| **GCC/regional** regulations | **NOT FOUND** | No GCC-specific compliance documentation | **Not Addressed** |

### 11.3 Compliance Observations

| Observation | Details |
|-------------|---------|
| **No compliance/regulatory module** | `routes/compliance.py` exists but no evidence of regulatory reporting |
| **Clinical terminology gap** | No LOINC/SNOMED/ICD-10 is a critical gap for any healthcare system |
| **No audit certification** | Audit hash chain is technically strong but no ISO 27001 certification |
| **No privacy framework** | No GDPR/HIPAA/Iraqi privacy law compliance documentation |
| **No consent management framework** | Consent model exists but no regulatory consent framework |
| **Good security practices** | Security controls (encryption, RBAC, audit) would satisfy many requirements but lack certification |

---

## 12. TESTING ATLAS

### 12.1 Test Inventory

| Test Location | File Count | Type | Status |
|---------------|-----------|------|--------|
| `backend/tests/` | 100+ files | Unit + Integration + Security | **Active** |
| `backend/app/capabilities/*/tests/` | 20 files | Unit + Integration per capability | **Active** |
| `backend/app/national/tests/` | 24 files | Unit, security, FHIR validation, performance, integration, identity merge, offline, recovery | **Active** |
| `nhop-platform/tests/` | 5 files | Doctor API, outbreak API, outbreak detection | **Active** |
| `services/device_bridge/tests/` | 12 files | Adapters, device manager, onboarding, parsers, pipeline, sync | **Active** |
| `tests/chaos/` | 3 files (2 yaml + 1 sh) | Chaos engineering scenarios | **Configured** |
| `tests/load/` | 2 files | Locust + scenario load tests | **Configured** |
| `tests/stress/` | 1 file + 1 yaml | Stress testing | **Configured** |
| `tests/spike/` | 1 file | Spike testing | **Configured** |
| `tests/soak/` | 1 file | Soak testing | **Configured** |
| `tests/recovery/` | 1 file | Recovery testing | **Configured** |
| `tests/integration/` | 1 file | Integration integrity tests | **Configured** |
| `contracts/compatibility/` | 4 test files | API, DTO, FHIR contract tests | **Active** |
| `client/src/lib/__tests__/` | Unknown | Frontend tests | **Minimal** |

### 12.2 Test Category Breakdown

| Category | Count | Description |
|----------|-------|-------------|
| **Kernel tests** | 35 | Event bus, plugin system, runtime, DI, outbox, scheduler, locks |
| **Security tests** | 39+ | JWT, auth, RBAC, encryption, tenant isolation, SQL injection |
| **Identity tests** | 10+ | Identity governance, matching, merge |
| **Clinical safety tests** | 1 | `test_clinical_safety.py` |
| **Comprehensive integration** | 1 | `test_comprehensive.py` |
| **Feature flag tests** | 1 | `test_feature_flags.py` |
| **Performance tests** | 2 | `test_performance_budgets.py`, performance baseline tests |
| **Chaos tests** | 2 | `test_chaos_survival.py`, `test_chaos_engineering.py` |
| **Stress tests** | 2 | `test_stress.py` (backend) + top-level stress |
| **Disaster recovery tests** | 1 | `test_disaster_recovery.py` |
| **Compliance tests** | 1 | `test_compliance_integrity.py` |
| **Migration tests** | 2 | `test_migrations.py`, `test_migration_resilience.py` |
| **Device bridge tests** | 12 | ASTM parsing, HL7, sync, auth |

### 12.3 Testing Framework

| Tool | Purpose | Configuration |
|------|---------|---------------|
| pytest | Python test runner | `backend/pytest.ini` |
| pytest-asyncio | Async test support | requirements-dev.txt |
| pytest-cov | Coverage | `.coveragerc` |
| factory_boy | Test fixtures | `engineering/testing/factories.py` |
| k6 | Load testing | `k6/` directory |
| Locust | Load testing | `tests/load/locustfile.py` |
| Chaos Mesh | Chaos engineering | `tests/chaos/chaos-mesh-experiment.yaml` |
| Vitest | Frontend testing | `vitest` in package.json |

### 12.4 Testing Gaps

| Gap | Risk | Evidence |
|-----|------|----------|
| **No E2E tests** | High | No Playwright/Cypress/Selenium anywhere |
| **No frontend tests** | High | Minimal test files in frontend-v2, client, platform/apps |
| **No contract tests for all APIs** | Medium | Contract tests only for core routes |
| **No performance baseline** | Medium | Performance tests exist but no established baseline |
| **Coverage unknown** | Medium | Coverage config exists but no published coverage targets |
| **No mutation testing** | Low | `mutants/` directory exists but no integrated mutation testing |
| **No accessibility tests** | Medium | No a11y testing |
| **No mobile testing** | Medium | No mobile-specific tests |

---

## 13. FUTURE ROADMAP ATLAS

### 13.1 Planned Features (from docs/code)

| Feature | Target Phase | Evidence |
|---------|-------------|----------|
| Financial Engine Phase B+ | Future | Schema only, ENABLE_FINANCIAL_ENGINE=false |
| Insurance claims integration | Phase B+ | Claims routes exist but gated |
| National EHR (Phase 2) | Future | ADR-016, national architecture docs |
| National Intelligence (Phase 3) | Future | ADR-021 |
| Citizen Super App | Future | ADR-020, platform/apps/citizen |
| SNDHS Phase 2 | Future | Phase 1 complete, RUNBOOK.md exists |
| Multi-region deployment | Future | Configs exist, not active |
| Sovereign phases 16-25 | Future | 10 sovereign phase docs covering interoperability, regulatory, AI governance, health economics, etc. |
| AI clinical validation | Future | AI fabric exists but no validation |
| Offline-first edge | Future | edge_agent/ exists but early stage |
| Microservices decomposition | Future | services/ stubs exist, monolith is primary |

### 13.2 Architecture Roadmap (from docs)

| Phase | Focus | Status |
|-------|-------|--------|
| Foundation (PI-001 to PI-006) | Core platform, LIMS, lab operations | **Complete** (frozen) |
| National Phase 1 | SNDHS integration, identity, FHIR | **Complete** |
| National Phase 2 | EHR, data platform, operations | **In Progress** |
| National Phase 3 | Ecosystem, intelligence, citizen super app | **Planned** |
| Sovereign Phase 16-25 | Interoperability, regulatory, health economics, crisis continuity, legal, ecosystem | **Planned** |

---

## 14. RISK ATLAS

### 14.1 Critical Risks

| Risk | Severity | Likelihood | Impact | Mitigation |
|------|----------|------------|--------|------------|
| **No LOINC/SNOMED/ICD-10** | **Critical** | **Certain** | Cannot code lab results semantically; cannot exchange data with other health systems | Requires terminology service implementation |
| **No clinical AI validation** | **Critical** | **High** | Clinical AI could give unsafe recommendations without validation | Requires clinical safety case |
| **No patient data privacy framework** | **Critical** | **High** | No documented privacy compliance (GDPR/HIPAA/Iraqi law) | Requires privacy impact assessment |
| **No DR testing** | **High** | **High** | DR plan exists but never tested; failover would likely fail | Requires DR drill |
| **No E2E tests** | **High** | **Certain** | Cannot verify system works end-to-end after changes | Requires E2E test suite |
| **Monorepo complexity** | **Medium** | **Certain** | 3,700+ files, 66 app subdirs, unclear ownership | Requires module boundaries and ownership |
| **Circular shared library dependency** | **Medium** | **Confirmed** | `shared/` imports `backend/app/` modules | Requires dependency inversion |

### 14.2 High Risks

| Risk | Severity | Evidence |
|------|----------|----------|
| **SAML/OAuth2 limited testing** | High | Route modules exist but security tests are limited |
| **No user manuals** | High | No end-user documentation for any application |
| **No performance baseline** | High | Cannot measure regression |
| **Microservices stubs may diverge** | Medium | services/ stubs may get out of sync with monolith |
| **68 empty/placeholder directories** | Medium | Many modules have `__init__.py` only |
| **Kubernetes configs not tested** | Medium | k8s/ and helm/ configs exist but Docker Compose is primary |
| **Monitoring stack not active** | Medium | Prometheus/Grafana configured but not running by default |

### 14.3 Security Risks

| Risk | Severity | Evidence |
|------|----------|----------|
| **Medium Bandit findings unaddressed** | Low | 0.0.0.0 bindings in dev integration config |
| **268 tenant isolation test failures** | Low | Test infrastructure issue, not production |
| **Secrets in env files** | Medium | `.env` is gitignored but `.env.production` tracked |
| **No PKI** | Medium | Service-to-service auth relies on shared secrets |

---

## 15. TECHNICAL DEBT ATLAS

### 15.1 Known Technical Debt

| Item | Impact | Evidence |
|------|--------|----------|
| **F821 bugs fixed** | Resolved | 125 undefined-name errors resolved (changelog v2.2.0) |
| **Ruff style warnings** | Low | 898 style/naming warnings remaining |
| **B904 exception chaining** | Medium | 220 exception-chaining warnings requiring human review |
| **Empty `__init__.py` files** | Low | `routes/__init__.py` and many others are empty |
| **Deprecated patterns** | Medium | `passlib/bcrypt` deprecation warning |
| **Mutants directory** | Low | `backend/mutants/` exists with test mutants |
| **archive/ directory** | Medium | 50+ files in archive/ need cleanup |
| **mypy cache in tree** | Low | `.mypy_cache/` should be in .gitignore |
| **Duplication across frontends** | High | 3 frontends (frontend-v2, frontend, client) + 8 platform apps = significant overlap |
| **Firebase + tRPC auth split** | Medium | Firebase used in frontend-v2, JWT in backend; two auth systems |

### 15.2 Code Quality

| Metric | Value | Evidence |
|--------|-------|----------|
| Syntax gate | **PASS** (0 errors) | 1,532 Python modules scanned |
| Flake8 errors (E9, F821) | **0** | CI gate |
| Ruff warnings | 898 (style/naming) | Non-blocking |
| Bandit HIGH | **0** | Security scan |
| Bandit MEDIUM | 2 | Integration dev config only |
| Pre-commit hooks | Configured | `.pre-commit-config.yaml` |

---

## 16. MISSING COMPONENTS ATLAS

### 16.1 Missing Backend Modules

| Module | Impact | Notes |
|--------|--------|-------|
| **Terminology service** | Critical | No LOINC, SNOMED CT, ICD-10 support |
| **Medical coding engine** | Critical | No auto-coding of lab results |
| **Clinical decision support engine** | High | CDS models exist but no rules engine |
| **Health Insurance/Billing** | Medium | Financial engine is schema-only (Phase A) |
| **HR/Payroll** | Medium | No HR module |
| **Training/LMS** | Medium | No training module |
| **Facilities management** | Medium | No facilities module |
| **Surgical/OR management** | Medium | No surgical module |

### 16.2 Missing Frontend Applications

| Application | Impact | Notes |
|-------------|--------|-------|
| **Blood Bank UI** | High | Backend exists, no frontend |
| **EMS Dispatch UI** | High | Backend exists, no frontend |
| **Public Health Dashboard** | High | Backend exists, no frontend |
| **Biomedical Engineering UI** | Medium | Backend exists, no frontend |
| **Critical Care Monitoring UI** | Medium | Backend exists, no frontend |
| **Care Continuum UI** | Medium | Backend exists, no frontend |
| **Research Platform UI** | Medium | Partially in frontend-v2 |

### 16.3 Missing Infrastructure

| Component | Impact | Notes |
|-----------|--------|-------|
| **Automated backups** | High | Backups are manual only |
| **DR testing** | High | No DR drill evidence |
| **Load balancer in production** | Medium | HAProxy config exists but not default |
| **CDN** | Medium | Cloudflare configured but not fully integrated |
| **Service mesh (Linkerd)** | Medium | K8s configs exist, not active |
| **Container registry automation** | Low | GHCR configured |
| **Chaos engineering automation** | Low | Chaos Mesh configured |

### 16.4 Missing Documentation

| Document | Impact | Notes |
|----------|--------|-------|
| User manuals (all apps) | Critical | No end-user documentation |
| API reference docs | High | Only FastAPI auto-generated |
| Clinical safety case | Critical | Required for healthcare certification |
| Privacy impact assessment | High | Required for patient data |
| Disaster recovery test report | High | No evidence of DR testing |
| Penetration test report | High | No pen-test evidence |
| Compliance certification docs | High | No ISO/HIPAA/other certification |

### 16.5 Missing Security Components

| Component | Impact | Notes |
|-----------|--------|-------|
| **PKI infrastructure** | Medium | No internal CA or certificate management |
| **Key rotation automation** | Medium | No automated key rotation |
| **Zero Trust enforcement** | Medium | Configs exist, not active |
| **WAF in production** | Medium | Configs exist, not active |
| **SIEM active deployment** | Medium | Configs exist, not active |
| **Container image signing** | Medium | Not implemented |

---

## 17. RECOMMENDATIONS ATLAS

### 17.1 Critical (Must Fix Before Production)

| Priority | Recommendation | Rationale |
|----------|---------------|-----------|
| **P0** | Implement LOINC coding for all lab tests | Without LOINC, lab results cannot be exchanged with any other healthcare system |
| **P0** | Implement SNOMED CT for clinical findings | Required for semantic interoperability |
| **P0** | Implement ICD-10 for diagnoses | Required for national health reporting |
| **P0** | Create clinical safety case | Required for clinical AI and any healthcare certification |
| **P0** | Conduct privacy impact assessment | Required for patient data processing compliance |
| **P0** | Implement E2E testing | Cannot verify system integrity without E2E tests |

### 17.2 High (Should Fix Before National Deployment)

| Priority | Recommendation | Rationale |
|----------|---------------|-----------|
| **P1** | Conduct DR drill and document results | DR plan exists but never tested |
| **P1** | Create user manuals for all applications | Zero end-user documentation found |
| **P1** | Implement automated backups | Current backup is manual only |
| **P1** | Resolve shared library circular dependency | `shared/` should not import `backend/` |
| **P1** | Complete ABAC implementation | ABAC module exists but not integrated |
| **P1** | Establish performance baseline | Cannot detect regressions without baseline |
| **P1** | Add frontend tests | All frontends have minimal/no tests |

### 17.3 Medium (Should Address in Next Sprint)

| Priority | Recommendation | Rationale |
|----------|---------------|-----------|
| **P2** | Clean up archive/ directory | 50+ files of dead code |
| **P2** | Remove duplicate `.mypy_cache` from tree | Should be in .gitignore |
| **P2** | Resolve 898 ruff style warnings | Code quality improvement |
| **P2** | Resolve 220 B904 warnings | Exception chaining |
| **P2** | Add LOINC/SNOMED/ICD-10 seed data to test types | Foundation for terminology service |
| **P2** | Implement health data streaming pipeline | National streaming routes exist but pipeline not active |
| **P2** | Document API contracts | OpenAPI spec generated but no formal API documentation |

### 17.4 Low (Nice to Have)

| Priority | Recommendation | Rationale |
|----------|---------------|-----------|
| **P3** | Consolidate frontends (3→1) | Significant duplication between frontend-v2, client, and platform/apps |
| **P3** | Implement PKI | Service-to-service auth improvement |
| **P3** | Activate SIEM | Security monitoring |
| **P3** | Automate key rotation | Security hygiene |
| **P3** | Add mutation testing | Test quality |
| **P3** | Implement accessibility testing | Inclusive design |

---

## 18. FINAL REPORT

### 18.1 Summary Statistics

| Metric | Value |
|--------|-------|
| **Total Files** | 3,709 |
| **Total Directories** | 1,421 |
| **Total Python Files** | 2,243 |
| **Total Frontend Files (TS/TSX/JS)** | 649 |
| **Total HTML Files** | 472 |
| **Total Documentation Files (MD)** | 420 |
| **Total Configuration Files (YAML)** | 144 |
| **Total Shell Scripts** | 118 |
| **Total JSON Files** | 96 |
| **Total Terraform Files** | 62 |
| **Total Dockerfiles** | 14 |

### 18.2 Module Counts

| Category | Count |
|----------|-------|
| **Total Backend App Subdirectories** | 66 |
| **Total Route Modules** | 52 |
| **Total Route Registrations** | 79 |
| **Total Model Modules** | 25 (+ EHR, hospital, care_continuum models) |
| **Total Database Migrations** | 46 |
| **Total Security Modules** | 15 |
| **Total Kernel Modules** | 100 |
| **Total Engineering Modules** | 52 |
| **Total Applications** | 28 |
| **Total GitHub Workflows** | 6 |
| **Total Architecture Decision Records** | 26 |

### 18.3 Healthcare Coverage

| Category | Finding |
|----------|---------|
| **Laboratory Specialties Covered** | 5 (clinical pathology, hematology, microbiology, chemistry, immunology) |
| **Medical Specialties Covered** | 17 (of ~30+) |
| **Medical Specialties Missing** | 13+ (ophthalmology, dermatology, psychiatry, orthopedics, anesthesiology, surgery, dentistry, nutrition, physical therapy, cardiology, neurology, oncology, OB/GYN dedicated) |
| **Pharmacy Specialties Missing** | No pharmacy specialties (general pharmacy module only) |
| **Nursing Specialties Missing** | No nursing specialties (general nursing module only) |
| **Radiology Specialties Missing** | General radiology only (no MRI/CT/Ultrasound/Nuclear Medicine subspecialties) |
| **Healthcare Standards Implemented** | ASTM, HL7 v2, FHIR R4 |
| **Healthcare Standards Missing** | LOINC, SNOMED CT, ICD-10, DICOM (full), HIPAA |

### 18.4 Architecture Score

| Dimension | Score (0-10) | Assessment |
|-----------|-------------|------------|
| **Modularity** | 7/10 | Well-modularized monolith with bounded contexts, some circular deps |
| **Pattern adherence** | 6/10 | Mixed patterns (DDD partial, CQRS partial, Clean Architecture partial) |
| **Dependency management** | 5/10 | `shared/` circular dependency, archive/ contains dead code |
| **Scalability** | 7/10 | Horizontal scaling via HAProxy, read replicas, K8s configs |
| **Maintainability** | 6/10 | Large monorepo, 3x frontends, limited tests |

### 18.5 Security Score

| Dimension | Score (0-10) | Assessment |
|-----------|-------------|------------|
| **Authentication** | 8/10 | JWT, MFA, OAuth2, SAML, WebAuthn in dev |
| **Authorization** | 7/10 | RBAC production, ABAC not integrated |
| **Encryption** | 7/10 | Encryption at rest, Fernet keys, no PKI |
| **Audit** | 8/10 | Immutable hash chain, full context |
| **Infrastructure security** | 5/10 | SIEM/IDS/Zero Trust configured but not active |

### 18.6 Clinical Score

| Dimension | Score (0-10) | Assessment |
|-----------|-------------|------------|
| **Healthcare domain coverage** | 6/10 | 17 domains covered, many missing |
| **Medical terminology** | 2/10 | No LOINC, SNOMED CT, ICD-10 |
| **Clinical AI readiness** | 3/10 | AI fabric exists but no validation |
| **Compliance readiness** | 3/10 | No certifications, no formal compliance program |
| **Patient safety** | 4/10 | No clinical safety case, limited CDS |

### 18.7 Infrastructure Score

| Dimension | Score (0-10) | Assessment |
|-----------|-------------|------------|
| **Deployment automation** | 8/10 | CI/CD with blue/green, canary, auto-rollback |
| **Monitoring** | 6/10 | Full monitoring stack configured but not live |
| **Backup/DR** | 4/10 | Manual backups, DR not tested |
| **Scalability** | 7/10 | Multiple scaling strategies configured |
| **Infrastructure as Code** | 8/10 | Terraform, K8s, Helm, Docker Compose |

### 18.8 AI Score

| Dimension | Score (0-10) | Assessment |
|-----------|-------------|------------|
| **AI architecture** | 5/10 | Well-designed fabric but not production-ready |
| **Model integration** | 2/10 | No active LLM integration |
| **Data infrastructure** | 4/10 | Vector embeddings schema exists but no vector DB |
| **AI governance** | 5/10 | Governance framework exists but not active |
| **Clinical AI safety** | 1/10 | No validation, no safety testing |

### 18.9 Documentation Score

| Dimension | Score (0-10) | Assessment |
|-----------|-------------|------------|
| **Architecture docs** | 8/10 | 26 ADRs, architecture docs, sovereign docs |
| **API docs** | 4/10 | Auto-generated only, no formal API documentation |
| **User manuals** | 0/10 | No end-user documentation |
| **Operations docs** | 7/10 | Runbooks, deployment guides, production docs |
| **Developer docs** | 6/10 | CLAUDE.md, but no comprehensive onboarding |

### 18.10 Overall Scores

| Score | Value |
|-------|-------|
| **Production Readiness** | **7/10** — Core lab platform is production-ready; national and AI features need work |
| **National Readiness** | **5/10** — SNDHS Phase 1 complete, but LOINC/SNOMED/ICD-10 missing; no compliance certification |
| **Global Readiness** | **3/10** — Arabic-first with no i18n/i10n framework; missing international standards; no multi-language support beyond Arabic/English |
| **Architecture** | **6.2/10** |
| **Security** | **7.0/10** |
| **Clinical** | **3.7/10** |
| **Infrastructure** | **6.8/10** |
| **AI** | **3.4/10** |
| **Documentation** | **5.0/10** |

### 18.11 Key Findings Summary

1. **Massive codebase**: 3,709 files, 1,421 directories, 66 backend subdirectories
2. **Well-architected monolith**: Monolith-first with microservices decomposition path, self-healing, circuit breakers, event bus
3. **Strong security foundations**: JWT auth, RBAC, encryption at rest, immutable audit, MFA, OAuth2, SAML
4. **Comprehensive healthcare domain model**: 17 healthcare domains with backend modules
5. **CRITICAL GAP — No medical terminology**: LOINC, SNOMED CT, and ICD-10 are completely absent
6. **CRITICAL GAP — No clinical safety**: No clinical safety case, no AI validation
7. **CRITICAL GAP — No compliance certification**: No HIPAA/ISO/certification evidence
8. **No end-user documentation**: Zero user manuals across all 28 applications
9. **No E2E tests**: Cannot verify end-to-end system integrity
10. **3 frontends + 8 platform apps**: Significant duplication across frontend implementations
11. **AI fabric not production-ready**: Well-designed architecture but no active LLM integration
12. **DR not tested**: DR plan exists but never validated
13. **Monitoring not live**: Full observability stack configured but not deployed by default

---

*End of MASTER SYSTEM ATLAS — MISSION-026 Complete*
