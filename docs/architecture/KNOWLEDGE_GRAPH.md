# GULA Engineering Knowledge Graph

## Repository Map

```
gula-platform (monorepo root)
├── backend/           → Platform-Core (FastAPI monolith)
│   └── app/           → Main application code
│       ├── main.py    → App entrypoint, middleware, background loops
│       ├── config.py  → Environment config loading
│       ├── database.py → SQLAlchemy engine, pool, circuit escalation
│       ├── models/    → 17+ SQLAlchemy ORM models
│       ├── routes/    → 36+ API route modules
│       ├── services/  → Business logic layer
│       ├── core/      → Infrastructure (events, logging, self-healing)
│       ├── security/  → Auth, encryption, RBAC, rate limiting
│       ├── tasks/     → Background task framework
│       └── ...        → 22+ domain engine directories
├── services/          → Microservices (future decomposition)
│   ├── ai/            → AI microservice
│   ├── device_bridge/ → LabLink-Core (ASTM/HL7 device integration)
│   ├── lab/           → Lab microservice
│   ├── order/         → Order microservice
│   ├── patient/       → Patient microservice
│   ├── result/        → Result microservice
│   ├── sample/        → Sample microservice
│   ├── notification/  → Notification microservice
│   ├── autonomous_manager/ → Self-healing platform
│   └── shared/        → [BRIDGED TO shared/]
├── shared/            → ★ CANONICAL SHARED LIBRARY ★
├── nhop-platform/     → National Health Oversight Platform
├── frontend-v2/       → React + Firebase SPA (citizen/doctor/lab/ministry)
├── client/            → Lightweight tRPC + React SPA
├── frontend/          → Static HTML PWA (offline-capable)
├── ai/                → Clinical AI modules (top-level)
├── edge_agent/        → Edge computing agent
├── docs/              → Documentation (architecture, SNDHS, deployment)
├── scripts/           → Operations and maintenance scripts
└── config/            → Infrastructure config (nginx, prometheus, grafana)
```

## Dependency Graph

```
frontend-v2 ────► backend/app (REST API)
     │                    │
     │                    ├──► shared/ (via import)
     │                    ├──► PostgreSQL 16
     │                    └──► Redis 7
     │
client ─────────► backend/app (tRPC/REST)
     │
nhop-platform ──► backend/app (shared DB)
     │
services/* ─────► shared/ (via import)
     │
device_bridge ──► backend/app (HTTP API via gula_client.py)
     │
shared/ ────────► (canonical, no internal deps)
```

## Module Dependency Map

```
shared/auth/        → shared/security/
shared/config/      → (standalone)
shared/events/      → shared/logging/
shared/audit/       → shared/events/
shared/metrics/     → (standalone)
shared/cache/       → (optional redis)
shared/retry/       → shared/logging/
shared/health/      → (standalone)
shared/security/    → (standalone)
shared/rbac/        → (standalone)
shared/qr/          → (qrcode library)
shared/barcode/     → (python-barcode)
shared/pdf/         → shared/qr/ (optional)
shared/storage/     → (boto3, optional)
shared/notifications/ → (firebase-admin, optional)
shared/observability/ → shared/logging/
shared/device/      → (standalone)
shared/workflow/    → (standalone)
shared/policies/    → (standalone)
shared/validators/  → (standalone)
shared/middleware/  → shared/logging/
shared/schemas/     → (standalone)
shared/models/      → (SQLAlchemy)
shared/utilities/   → (standalone)
shared/design_system/ → (standalone)
```

## API Endpoint Map

| Route Group | Prefix | Source | Description |
|-------------|--------|--------|-------------|
| Auth | `/api/v1/auth/*` | `routes/login.py` | Login, logout, refresh |
| Register | `/api/v1/register` | `routes/register.py` | Lab registration |
| Patients | `/api/v1/patients/*` | `routes/patients.py` | Patient CRUD |
| Orders | `/api/v1/orders/*` | `routes/results.py` | Lab orders |
| Results | `/api/v1/results/*` | `routes/results.py` | Lab results |
| Samples | `/api/v1/samples/*` | `routes/samples.py` | Sample tracking |
| Labs | `/api/v1/labs/*` | `routes/labs.py` | Lab management |
| Dashboard | `/api/v1/dashboard/*` | `routes/dashboard.py` | Analytics |
| Stats | `/api/v1/stats/*` | `routes/stats.py` | Statistics |
| Metrics | `/metrics` | `routes/metrics.py` | Prometheus |
| Health | `/health*` | `main.py` | Health checks |
| QR | `/api/v1/qr/*` | `routes/qr.py` | QR generation |
| Patient Card | `/api/v1/patient-card/*` | `routes/patient_card.py` | Digital cards |
| AI | `/api/v1/ai/*` | `routes/ai.py` | Clinical AI |
| Edge | `/api/v1/edge/*` | `routes/edge.py` | Edge platform |
| Policy/Rules | `/api/v1/policies/*` | `policies/router.py` | Policy engine |
| Workflows | `/api/v1/workflows/*` | `workflows/router.py` | Workflow engine |
| Notifications | `/api/v1/notifications/*` | `routes/notifications.py` | Notifications |
| Compliance | `/api/v1/compliance/*` | `routes/compliance.py` | Regulatory |
| Integrations | `/api/v1/integrations/*` | `routes/integrations.py` | External |
| Skills | `/api/v1/skills/*` | `routes/skills.py` | Skill platform |

## Database Dependency Graph

```
PostgreSQL 16
├── audit_logs ──── (SHA-256 chain, immutable trigger)
├── patients ────── (encrypted national_id, SNDHS fields)
├── lab_orders ──── (version column for optimistic locking)
├── lab_results ─── (HMAC tokens for public sharing)
├── outbox_events ─ (transactional outbox pattern)
├── labs ────────── (tenant root)
├── lab_users ───── (RBAC, perm_version column)
├── samples ─────── (barcode tokens)
├── quality_controls
├── claims ──────── (insurance billing)
├── consents ────── (citizen data consent)
├── test_types ──── (reference ranges)
├── subscriptions ─ (feature flags, tier management)
├── edge_* ──────── (edge AI platform)
├── ai_interactions
├── policies ────── (policy engine)
├── rules ───────── (rule engine)
├── workflows ───── (workflow engine)
├── forms ───────── (dynamic forms)
├── approvals ───── (approval chains)
├── constraints ─── (constraint engine)
└── skill_* ─────── (skill platform)
```

## Test Coverage Map

| Package | Test Files | Coverage |
|---------|-----------|----------|
| `tests/` (backend) | 28 test modules | 92% critical modules |
| `services/device_bridge/tests/` | 12 test modules | Unit + integration |
| `nhop-platform/tests/` | 3 test modules | API + outbreak |
| `frontend-v2/src/lib/__tests__/` | 2 test modules | Unit |
| `shared/` | (new) | Targeting ≥95% |

## Security Layer Map

```
Security Layer
├── Network: nginx (TLS termination) → api-gateway → backend
├── Auth: JWT (HS256) + refresh tokens
├── RBAC: 9 roles × 13 permissions
├── Rate Limiting: token bucket per IP/user
├── Intrusion Detection: time-windowed IP tracking
├── Encryption: Fernet (at rest), bcrypt (passwords), HMAC (NID)
├── Security Headers: CSP, HSTS, X-Frame-Options, X-Content-Type-Options
├── Circuit Breaker: prevents cascade failures
└── Audit: SHA-256 hash chain (immutable)
```
