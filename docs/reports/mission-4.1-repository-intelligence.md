# MISSION 4.1 — Repository Intelligence Report

**Date**: 2026-07-14
**Executor**: Autonomous Security Program
**Repository**: gula-platform (monorepo)
**Version**: v2.1.0-engineering-factory
**Status**: COMPLETE

---

## 1. Repository Overview

| Attribute | Value |
|-----------|-------|
| **Remote** | `git@github.com:samertts/gula-platform.git` |
| **Current Branch** | `main` (ahead of origin/main by 3 commits) |
| **Total Commits** | ~536+ |
| **Total Tags** | 1 (`v2.1.0-engineering-factory`) |
| **Total Files** | 3,057 |
| **Total Directories** | 460 |
| **Repository Size** | 45 MB (excluding .git, .venv, caches) |
| **Github Branches** | 60+ (main + 57 feature branches + 3 codex branches) |
| **Uncommitted Changes** | 251 modified files (1,683 insertions, 2,012 deletions) |
| **Stashed Work** | None |

### 1.1 All Branches

```
main (local + origin)
origin/claude/*              (52 branches — Claude-generated features)
origin/codex/*               (3 branches — Codex-generated fixes)
origin/fix/*                 (1 branch — manual fix)
```

### 1.2 Git History Themes

1. **Phase 1 (Initial)**: Project bootstrap, MVP lab platform
2. **Phase 2 (Hardening)**: Security, auth, RBAC, rate limiting, audit trails
3. **Phase 3 (Production)**: Self-healing, chaos testing, DIVE, monitoring
4. **Phase 4 (Deployment)**: Docker, nginx, DigitalOcean, Render, K8s
5. **Phase 5 (Sovereign)**: SNDHS-lite, NHOP, national health infrastructure
6. **Phase 6 (Engineering)**: Engineering factory, kernel, generators, constitution
7. **Phase 7 (Current)**: Production validation, kernel certification

---

## 2. Language Breakdown

| Language | File Count | Percentage |
|----------|-----------|------------|
| Python | 898 | 29.4% |
| HTML | 463 | 15.1% |
| Markdown | 198 | 6.5% |
| JavaScript/TypeScript | 141 | 4.6% |
| Shell Script | 87 | 2.8% |
| YAML | 58 | 1.9% |
| CSS | 5 | 0.2% |
| SQL | 14 | 0.5% |
| JSON | 23 | 0.8% |
| Other | 1,170 | 38.2% |

---

## 3. Component Catalog

### 3.1 Core Platform — `backend/app/`

| Component | Files | Description |
|-----------|-------|-------------|
| **Routes** | 37 | 36 route modules + `__init__` |
| **Models** | 19 | 17 SQLAlchemy ORM models |
| **Services** | 33 | Business logic layer + MPI (6 modules) |
| **Security** | 11 | Auth, RBAC, encryption, JWT, rate limiting |
| **Core** | 16 | Self-healing, auto-repair, startup guard, feature flags |
| **Kernel** | 69 | Plugin engine, module loader, event bus, validation |
| **Engineering** | 40 | Generators, CI gates, testing, documentation |
| **AI** | 5 | Guardrails, sandbox, approval, optimizer |
| **Financial** | 3 | Phase A — schema only |
| **Edge** | 10 | Edge platform control plane |
| **Domain** | 2 | Order state machine |
| **Tasks** | ~5 | Background task queue |

### 3.2 Shared Library — `shared/`

| Component | Modules | Description |
|-----------|---------|-------------|
| Architecture | 3 | Knowledge graph, validator |
| Audit | 2 | Audit service |
| Auth | 3 | JWT, passwords |
| Cache | 3 | Cache backends |
| Config | 3 | Config loader |
| Design System | 4 | Components, RTL, tokens |
| Device | 3 | ASTM adapter |
| Domain | 8 | Healthcare, Billing, Events |
| Events | 3 | Event bus |
| Generators | 4 | Docs, migrations, modules |
| Identity | 4 | Domain, events, service |
| Logging | 3 | Config |
| Metrics | 3 | Collector |
| Middleware | 2 | Base middleware |
| Models | 2 | Base model |
| Notifications | 3 | Sender, template |
| PDF | 3 | Generator |
| RBAC | 3 | Permissions |
| Security | 3 | Encryption, HMAC |
| SDK | 4 | Client, models |
| Storage | 3 | Backends |
| Workflow | 2 | Engine |
| DI Container | 6 | Dependency injection |
| Other | ~12 | Barcode, booking, CLI, licensing, payments, QR, retry, search, subscriptions, tracing, validators |

### 3.3 Frontends

| Component | Files | Description |
|-----------|-------|-------------|
| **frontend-v2/** | ~100+ TSX/TS | React + Firebase — citizen, doctor, lab, ministry portals |
| **frontend/** | ~300+ | Static HTML PWA (offline-capable) |
| **client/** | ~30 TSX/TS | tRPC + React SPA |

### 3.4 Microservices — `services/`

| Service | Files | Status |
|---------|-------|--------|
| device_bridge (LabLink-Core) | 40 | Production — ASTM/HL7 device integration |
| ai | 1 stub | Stub only |
| autonomous_manager | 1 stub | Stub only |
| lab | 1 stub | Stub only |
| notification | 1 stub | Stub only |
| order | 1 stub | Stub only |
| patient | 1 stub | Stub only |
| result | 1 stub | Stub only |
| sample | 1 stub | Stub only |
| shared | 4 modules | Shared microservice library |

### 3.5 National Platform — `nhop-platform/`

| Component | Modules | Description |
|-----------|---------|-------------|
| API v1 | 5 | Citizens, doctor, notifications, outbreak, test_results |
| Models | ~10 | Citizen, DiseaseCase, Lab, Notification, TestResult, etc. |
| Services | ~8 | Audit, duplicates, health_id, outbreak, smart_analysis |
| Tests | 4 | Test modules |

### 3.6 AI — `ai/` (top-level)

| Module | Description |
|--------|-------------|
| ai_agent.py | AI agent framework |
| ai_service.py | AI service layer |
| ali_reza_engine.py | Medical AI engine |
| anomaly_detection.py | Anomaly detection |
| clinical/ | Clinical decision support (4 modules) |
| lab_business_ai/ | Lab business AI (5 modules) |
| outbreak/ | Outbreak detection |
| population/ | Population health AI (6 modules) |
| preventive/ | Preventive medicine AI (5 modules) |

---

## 4. API Catalog — `backend/app/routes/`

| Endpoint Route | Module | Purpose |
|----------------|--------|---------|
| /admin | admin.py | Admin operations |
| /ai | ai.py | Clinical AI endpoints |
| /ai/telemetry | ai_telemetry.py | AI telemetry |
| /batch | batch.py | Batch processing |
| /citizen | citizen_portal.py | Citizen portal |
| /claims | claims.py | Insurance claims |
| /compliance | compliance.py | Regulatory compliance |
| /consent | consent.py | Patient consent management |
| /critical-alerts | critical_alerts.py | Critical lab alerts |
| /dashboard | dashboard.py | Dashboard data |
| /device-results | device_results.py | Device result ingestion |
| /edge | edge.py | Edge platform |
| /ehr | ehr.py | EHR integration |
| /id-scan | id_scan.py | National ID scanning |
| /identity | identity.py | Identity management |
| /insurance | insurance.py | Insurance integration |
| /integrations | integrations.py | Third-party integrations |
| /labs | labs.py | Lab management |
| /login | login.py | Authentication |
| /metrics | metrics.py | Prometheus metrics |
| /mobile | mobile.py | Mobile API |
| /national-identity | national_identity.py | National identity |
| /notifications | notifications.py | Notifications |
| /optimizer | optimizer.py | System optimizer |
| /patient-card | patient_card.py | Digital QR patient cards |
| /patients | patients.py | Patient management |
| /qr | qr.py | QR code generation |
| /quality-control | quality_control.py | QC management |
| /register | register.py | Registration |
| /results | results.py | Lab results |
| /samples | samples.py | Sample tracking |
| /security | security.py | Security endpoints |
| /setup | setup.py | Platform setup |
| /stats | stats.py | Statistics & trends |
| /test-results | test_results.py | Public test results |
| /tiers | tiers.py | Subscription tiers |

---

## 5. Entity Catalog (Database Models)

**`backend/app/models/`**

| Entity | Table | Purpose |
|--------|-------|---------|
| Patient | patients | Patient records |
| Lab | labs | Laboratory facilities |
| LabOrder | lab_orders | Test orders |
| LabResult | lab_results | Test results |
| LabUser | lab_users | Laboratory staff |
| Sample | samples | Biological samples |
| AuditLog | audit_logs | Immutable audit trail |
| Outbox | outbox_events | Event outbox |
| Consent | consent_records | Patient consent |
| Claim | claims | Insurance claims |
| Subscription | subscription_tiers | Tier subscriptions |
| QualityControl | quality_control | QC records |
| TestType | test_types | Available tests |
| TestResult | test_results | External test results |
| EdgeDevice | edge_devices | Edge devices |
| AiInteraction | ai_interactions | AI usage records |
| User | users | System users |

**`nhop-platform/app/models/`**

| Entity | Purpose |
|--------|---------|
| Citizen | National citizen registry |
| Lab | NHOP lab records |
| LabTest | Available lab tests |
| TestOrder | National test orders |
| TestResult | National test results |
| AntibioticSensitivity | Antibiotic susceptibility |
| DiseaseCase | Reportable diseases |
| Notification | National notifications |
| AuditLog | NHOP audit trail |

---

## 6. Architecture Graph

```
Internet
  │
  ▼
host nginx (TLS) ──► api-gateway (Docker nginx :8080)
                          │
                          ▼
                    gula-backend (FastAPI + gunicorn + uvicorn :8000)
                          │
                    ┌─────┴─────┐
                    ▼           ▼
              PostgreSQL 16   Redis 7
              
Optional services:
  device_bridge ──► ASTM/HL7 lab instruments ──► gula-backend
  nhop-platform  ──► National citizens registry (port 8100)
  edge_agent     ──► Offline edge computing
  frontend-v2    ──► React + Firebase (separate deployment)
```

### Middleware Stack (in order)

1. `MaxBodySizeMiddleware`
2. `RequestIDMiddleware`
3. `DocsAuthMiddleware`
4. `CORSMiddleware`
5. `RequestTimingMiddleware`
6. `SecurityHeadersMiddleware`
7. `GZipMiddleware`
8. `ReadinessMiddleware`
9. `DegradedModeMiddleware`
10. `ConcurrencyLimitMiddleware`

---

## 7. Dependency Graph

### Python Dependencies (Production)

| Package | Purpose | Category |
|---------|---------|----------|
| fastapi | Web framework | API |
| uvicorn | ASGI server | Runtime |
| gunicorn | WSGI server | Runtime |
| sqlalchemy | ORM | Database |
| alembic | Migrations | Database |
| psycopg2-binary | PostgreSQL driver | Database |
| pydantic | Validation | Core |
| redis | Cache/queue | Infrastructure |
| python-jose | JWT | Security |
| cryptography | Encryption | Security |
| passlib+bcrypt | Password hashing | Security |
| python-multipart | File upload | API |
| orjson | JSON perf | Performance |
| qrcode + Pillow | QR generation | Feature |
| reportlab | PDF generation | Feature |
| jinja2 | Templates | Feature |
| arabic-reshaper | Arabic text | Feature |
| httpx | HTTP client | Integration |
| sentry-sdk | Error tracking | Monitoring |

### Python Dependencies (Dev/Test)

| Package | Purpose |
|---------|---------|
| pytest | Test runner |
| pytest-asyncio | Async test support |

### Node.js Dependencies (client/)

| Package | Purpose |
|---------|---------|
| express | Web framework |
| @trpc/server, @trpc/client, @trpc/react-query | tRPC |
| react, react-dom | UI framework |
| @tanstack/react-query | Data fetching |
| tailwindcss | CSS framework |
| zod | Validation |
| recharts | Charts |

### Node.js Dependencies (frontend-v2/)

Leverages Firebase + Gemini SDK + various React components (build via Vite).

---

## 8. Reusable Components

### Detected Reusable Libraries

| Component | Location | Reusability |
|-----------|----------|-------------|
| **shared/** library | `shared/` | HIGH — Canonical shared library with 55+ modules |
| **services/shared/** | `services/shared/` | MEDIUM — Microservice library (4 modules, overlaps with shared/) |
| **Kernel** | `backend/app/kernel/` | HIGH — Plugin engine, event bus, tenant isolation |
| **Engineering Factory** | `backend/app/engineering/` | HIGH — Generators, CI gates, code analysis |
| **Shared Auth** | `shared/auth/` | HIGH — JWT, password utilities |
| **Shared Security** | `shared/security/` | HIGH — Encryption, HMAC |
| **DI Container** | `shared/di_container/` | HIGH — Dependency injection framework |
| **Workflow Engine** | `shared/workflow/` | MEDIUM — Workflow automation |

---

## 9. Detected Duplicates & Dead Code

### Duplicated Code

| Pattern | Locations | Risk |
|---------|-----------|------|
| AI code duplicated | `ai/` (top-level) vs `backend/app/ai/` (monolith) | HIGH — Two AI codebases doing overlapping work |
| Shared library duplicated | `shared/` vs `services/shared/` | MEDIUM — `services/shared/` has 4 modules that overlap with `shared/` |
| Model definitions duplicated | `nhop-platform/app/models/` partially overlaps `backend/app/models/` | MEDIUM — Lab/test models appear in both |
| Identity code split | `backend/app/services/identity*` vs `shared/identity/` | MEDIUM |

### Dead Code / Abandoned Modules

| Module | Evidence | Action |
|--------|----------|--------|
| `backend/services/` (multi) | 8 of 9 services are stubs (only `main.py`) | Remove or implement |
| `backend/core/api/` | `main.py` only — experimental | Remove |
| `backend/gateway/` | `api_gateway.py`, `device_gateway.py` — experimental | Remove or consolidate |
| `backend/search/` | `search_service.py` — not wired into monolith | Remove or integrate |
| `backend/cache/` | `cache.py` — not wired | Remove or integrate |
| `backend/mutants/` | Testing artifacts | Remove |
| `archive/` | Legacy code, experimental modules | Archive or delete |
| `services/ai/`, `lab/`, etc. | 7 stub microservices with only `main.py` | Implement or remove |
| `backend/services/health_exchange/` | Experimental health data exchange | Evaluate |
| `backend/services/identity_engine/` | Duplicate identity logic | Consolidate |
| `backend/services/health_record_engine/` | Experimental health records | Evaluate |
| `backend/services/lab_service/` etc. | Stub services | Clean up |

---

## 10. Technical Debt Register

| ID | Issue | SeverITY | Location | Impact |
|----|-------|----------|----------|--------|
| T1 | Stub microservices in monorepo | HIGH | `services/*/main.py` (7 stubs) | Confusion, maintenance burden |
| T2 | Duplicate AI codebases | HIGH | `ai/` vs `backend/app/ai/` | Inconsistency, wasted effort |
| T3 | Duplicate shared libraries | MEDIUM | `shared/` vs `services/shared/` | Divergent code |
| T4 | Uncommitted changes (251 files) | HIGH | Working tree | Risk of lost work, merge conflicts |
| T5 | Archive directory not pruned | LOW | `archive/` | Bloat, confusion |
| T6 | Experimental services in production tree | MEDIUM | `backend/services/*` | Confusion about deployment target |
| T7 | Stub microservice main.py files with identical patterns | MEDIUM | `services/*/main.py` | Maintenance burden |
| T8 | Two frontend codebases (frontend/ + frontend-v2/) | MEDIUM | `frontend/`, `frontend-v2/` | Split attention |
| T9 | Client app (client/) third frontend | LOW | `client/` | Three frontends is confusing |
| T10 | `backend/tests/` has 130+ test files, some with low coverage | MEDIUM | `backend/tests/` | Coverage gaps |
| T11 | Outdated `.coverage` file tracked in git | LOW | `.coverage` | Should be gitignored |

---

## 11. Recommendations

### Immediate (Mission 4.1 Output)
1. Remove stub microservices (`services/ai`, `lab`, `notification`, `order`, `patient`, `result`, `sample`)
2. Consolidate AI code into `backend/app/ai/`
3. Consolidate `services/shared/` into `shared/` or remove
4. Clean up `backend/services/` experimental modules
5. Archive or delete `archive/` directory
6. Add `.coverage` to `.gitignore`

### For Subsequent Missions
7. M4.2: Full dependency SBOM and CVE scanning
8. M4.3: Safe dependency upgrade plan
9. M4.4: Supply chain security audit
10. M4.5: Full security hardening validation
11. M4.6: Dependency Guardian service
12. M4.7: Security Knowledge Base population
13. M4.8: Architecture Guardian rules
14. M4.9: Engineering Constitution enforcement

---

## 12. Repository Knowledge Graph (Summary)

```
gula-platform (v2.1.0-engineering-factory)
│
├── backend/                    [PRODUCTION MONOLITH]
│   ├── app/
│   │   ├── main.py            (1368 lines) — FastAPI entry
│   │   ├── config.py           — Env config
│   │   ├── database.py         — SQLAlchemy engine
│   │   ├── routes/ (37)        — API endpoints
│   │   ├── models/ (19)        — ORM entities
│   │   ├── services/ (33)      — Business logic
│   │   ├── security/ (11)      — Auth & security
│   │   ├── core/ (16)          — Infrastructure
│   │   ├── kernel/ (69)        — Plugin engine
│   │   ├── engineering/ (40)   — Code generation
│   │   ├── ai/ (5)             — Clinical AI
│   │   ├── edge/ (10)          — Edge platform
│   │   ├── financial/ (3)      — Phase A
│   │   └── tasks/              — Background workers
│   ├── tests/ (130+)           — Test suite
│   └── migrations/ (27)        — Alembic migrations
│
├── shared/ (55+ modules)       [CANONICAL LIBRARY]
│
├── services/                   [MICROSERVICES]
│   ├── device_bridge/ (40)     — ASTM/HL7 (LIVING)
│   └── 7 stubs                 — Empty shells
│
├── frontend-v2/ (~100 files)   [REACT + FIREBASE UI]
├── frontend/ (~300 files)      [STATIC HTML PWA]
├── client/ (~30 files)         [tRPC + REACT SPA]
│
├── ai/ (~30 files)             [TOP-LEVEL AI — DUPLICATE]
├── nhop-platform/ (~50 files)  [NATIONAL HEALTH OVERSIGHT]
├── edge_agent/ (~10 files)     [EDGE COMPUTING]
│
├── docs/                       [DOCUMENTATION]
│   ├── adr/ (12)               — Architecture Decision Records
│   ├── sndhs/ (22 files)       — National Health Data System
│   ├── sovereign/ (10 phases)  — Sovereign infrastructure
│   └── architecture/           — Architecture docs
│
├── scripts/ (87)               [OPERATION SCRIPTS]
├── config/                     [INFRASTRUCTURE CONFIG]
├── k8s/                        [KUBERNETES MANIFESTS]
└── archive/                    [LEGACY CODE]
```

---

**Report generated by Mission 4.1 — Repository Intelligence**
**Next**: Mission 4.2 — Dependency Intelligence
