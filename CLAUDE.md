# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## GULA Platform — Medical Laboratory SaaS (Monorepo)

Arabic-first healthcare platform for Iraqi medical laboratories. This is a **monorepo**
that consolidates three previously separate GitHub repositories:

| Former Repo | Location in monorepo | Role |
|-------------|----------------------|------|
| `samertts/gula-platform` | `backend/`, `services/`, `nhop-platform/`, `ai/` | Core platform (source of truth) |
| `samertts/LabLink-Core` | `services/device_bridge/` | Lab instrument integration (ASTM/HL7) |
| `samertts/Front-end-` | `frontend-v2/` | Rich React + Firebase UI |

Production stack is a FastAPI monolith (`backend/app/`) backed by PostgreSQL 17 + Redis 7;
a parallel microservices tree (`services/`) exists for future decomposition but is not the
primary deployment target. **App version: 2.5.0** (`config.py`).

## Core Principles (NON-NEGOTIABLE)

1. **Stability first** — never break working code to add features
2. **Data integrity above all** — no change may risk patient data loss
3. **Fix before feature** — bugs and security issues take priority
4. **Test then commit** — always run `python -m py_compile app/main.py` before committing

## Common Commands

All development is orchestrated through the `Makefile` at the repo root. `make help`
lists every target. The key ones:

```bash
# Local stack
make up                # docker compose up -d + wait for /health/ready
make down              # stop and remove containers
make restart           # rebuild images + restart + deep health check
make ps                # container status table
make logs-backend      # tail backend logs (also: logs-db, logs-redis)
make shell             # bash into gula-backend container

# Health & diagnostics
make health            # quick liveness (containers + HTTP 200 check)
make health-deep       # full diagnostic: grade (GREEN/YELLOW/RED), latency, memory
make status            # ps + health-deep combined

# Development
make lint              # pyflakes + flake8 (E9, F821 — errors only)
make test              # cd backend && pytest tests/ -v
make ci                # syntax-gate + lint + docker build (full CI locally)
make secrets-gen       # generate strong random SECRET_KEY/ENCRYPTION_KEY/etc.

# Testing
make scenario-test     # end-to-end load test (USERS=10 ROUNDS=1)
make integrity-test    # concurrent order-validation integrity test (WORKERS=100)
make chaos             # full chaos suite from tests/chaos/
make chaos-<name>      # single chaos scenario

# Single test — use pytest directly
cd backend && python -m pytest tests/test_security.py -v
cd backend && python -m pytest tests/test_security.py::test_jwt_reject_expired -v

# Database
make db-shell          # psql inside gula-postgres
make redis-cli         # redis-cli (auto-reads REDIS_PASSWORD from .env)
make backup            # pg_dump → ./backups/gula_<ts>.sql.gz

# Monitoring (opt-in profile)
make monitoring        # start prometheus + grafana (internal only — SSH tunnel to reach)
make monitoring-down
make metrics-token     # write METRICS_BEARER_TOKEN → config/prometheus/metrics_token

# Scaling
make scale REPLICAS=5  # HAProxy + N backend replicas (stats at :8404/stats)

# DigitalOcean operations
scripts/repair-droplet.sh    # comprehensive droplet repair (destructive — use with care)
scripts/diagnose-droplet.sh  # read-only diagnostics (safe to run anytime)
```

## Architecture

### Request Lifecycle

Internet → host nginx (TLS) → `api-gateway` (Docker nginx on 127.0.0.1:8080) →
`gula-backend` (FastAPI, gunicorn + uvicorn workers, `expose: 8000`) →
PostgreSQL 16 (+ Redis 7).

The backend never exposes a public port itself. All traffic enters through the gateway.

### Middleware Stack (order matters — see `backend/app/factory.py`)

Requests flow through these layers in registration order (last registered runs first):

1. `MaxBodySizeMiddleware` — 413 above `MAX_REQUEST_BODY_MB` (default 10)
2. `RequestIDMiddleware` — assigns `X-Request-ID` + binds to log ctx + DB correlation vars
3. `DocsAuthMiddleware` — guards `/docs`, `/redoc`, `/openapi.json` in production (admin JWT; production-only)
4. `CORSMiddleware`
5. `RequestTimingMiddleware` — per-request access log, `X-Response-Time` header
6. `SecurityHeadersMiddleware` — CSP, HSTS, X-Frame-Options, etc.
7. `GZipMiddleware`
8. `DegradedModeMiddleware` (from `core/self_healing.py`) — rejects writes when DB circuit is open
9. `ReadinessMiddleware` — 503 on all non-whitelisted paths until `system_ready` is True
10. `KernelMiddleware` — attaches kernel context to every request
11. `ConcurrencyLimitMiddleware` — per-worker in-flight cap (`MAX_CONCURRENT_REQUESTS`, default 50).
    Clinical writes (`/results`, `/orders`, `/samples`, `/critical-alerts`) are **exempt** —
    patient-safety operations must never be shed.

### FastAPI App Initialization

The app uses the **lifespan context manager** pattern (not the deprecated `@app.on_event()`):

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    # startup logic
    yield
    # shutdown logic

app = FastAPI(lifespan=lifespan)
```

Never reintroduce `@app.on_event("startup")` / `@app.on_event("shutdown")` — they are
removed and will raise a deprecation warning in newer FastAPI versions.

### Self-Healing (3 Layers)

1. **Circuit Breaker** (`backend/app/core/self_healing.py`) — isolates failing DB/Redis; flips to degraded mode
2. **Auto-Repair Engine** (`backend/app/core/auto_repair.py`) — GC, pool recycle, reconnects
3. **Adaptive Concurrency** (`backend/app/main.py::_adaptive_concurrency_loop`) — halves `_MAX_CONCURRENT` on 2 slow DB readings (>300ms); restores after 3 fast (<150ms)

A separate `_health_alert_loop` watchdog scores the system GREEN/YELLOW/RED every
60s and fires `ALERT_WEBHOOK_URL` (Telegram/Discord/Slack) on transitions and on
5-minute RED reminders.

### Startup Guard (`backend/app/core/startup_guard.py`)

Blocks readiness until: config validated, DB reachable, migrations checked, critical
data seeded. Until it passes, `system_ready = False` and the `ReadinessMiddleware`
returns 503 for every path except the health-check whitelist. Never set
`system_ready = True` from elsewhere.

### Health Endpoints

| Path | Purpose |
|------|---------|
| `/health` | liveness only (process alive) |
| `/health/live` | same as above |
| `/health/ready` | readiness (used by Docker healthcheck + api-gateway `depends_on`) |
| `/health/status` | diagnostic — always visible, explains WHY startup failed |
| `/health/deep` | grade + component latencies + memory — used by `make health-deep` |

All five are in `_ALWAYS_ALLOWED_PATHS` — they bypass readiness, degraded-mode, and
concurrency middlewares.

### Monolith vs. Microservices

- **`backend/app/`** is the production monolith. All routes, models, services live here.
  This is what runs in Docker as `gula-backend`.
- **`services/`** (top-level) contains independent services:
  - `services/device_bridge/` — **LabLink-Core**: ASTM/HL7 lab instrument integration.
    Reads from physical devices (Sysmex, Roche, Mindray, generic), normalises results,
    and forwards to `gula-backend` via `app/integration/gula_client.py`.
    Start with: `docker compose --profile device-bridge up device-bridge`
  - `services/lab`, `order`, `patient`, `result`, `sample`, `notification`, `ai`,
    `autonomous_manager` — future-decomposed microservices shipped as images via CI matrix;
    monolith is still the source of truth for business logic.
- **`frontend-v2/`** — Rich React SPA (formerly `samertts/Front-end-`).
  Contains citizen portal, Ministry Command Centre, predictive analytics, doctor/lab
  dashboards. Firebase dependency removed — all data flows through backend API only.
  Run: `cd frontend-v2 && npm install && npm run dev`
- **`client/`** — Lightweight tRPC + React SPA connected to `gula-backend`.
- **`frontend/`** — Static HTML PWA (offline-capable).
- **`nhop-platform/`** — National Health Oversight Platform (separate FastAPI app on port 8100).
  Owns the national citizen registry; GULA owns the per-lab LIMS view.
- **`edge_agent/`** — Off-site/offline edge computing agent for remote lab sites.
- **`ai/`** — Clinical AI modules (top-level; separate from `backend/app/ai/`).
- **`backend/services/`** and **`backend/core/`** (both with `api/` subdirs) are
  experimental stubs — avoid committing business logic there.

### Database Connection Pool

Formula: `WEB_CONCURRENCY × (DB_POOL_SIZE + DB_MAX_OVERFLOW) < postgres.max_connections`.
Defaults (3 × (6 + 12) = 54) fit inside Postgres's default 100. If you change any
of the three knobs, recheck the budget.

`backend/app/database.py` maintains per-request `contextvars` (`request_id`,
`endpoint`, `user_id`, `lab_id`) so every DB error log is correlated. Set by
middleware — do not read them directly, use `check_db_connection_detail`.

## Backend App Structure (`backend/app/`)

```
backend/app/
├── main.py                  # FastAPI app init, middleware, lifespan, route registration
├── config.py                # Env var loading, hard-fail on weak/missing secrets
├── database.py              # SQLAlchemy engine + pool + request-correlation contextvars
├── worker.py                # Background worker entry point
├── routes/                  # 55 route modules (500+ endpoints)
│   ├── patient_card.py      # QR-backed digital patient cards
│   ├── stats.py             # Statistics & trends API
│   ├── edge.py              # Edge platform endpoints
│   ├── ai.py                # Clinical intelligence
│   ├── compliance.py        # Regulatory compliance
│   └── ...                  # auth, labs, orders, results, samples, etc.
├── models/                  # 28 model files (~160+ ORM models)
├── services/                # Business logic layer (36 modules)
│   ├── mpi/                 # Master Patient Index
│   ├── governance/          # Identity governance
│   └── reference/           # Reference data
├── domain/
│   └── order_state.py       # Lab-order state machine
├── core/                    # Core infrastructure (19 modules)
│   ├── feature_flags.py     # Per-tenant feature matrix
│   ├── sndhs_flags.py       # SNDHS-lite deployment flags
│   ├── startup_guard.py     # system_ready flag + startup validation
│   ├── self_healing.py      # Circuit breaker, DegradedModeMiddleware
│   ├── auto_repair.py       # Auto-repair engine
│   ├── policy_engine.py     # Policy enforcement
│   └── logging_config.py    # Structured JSON logging
├── security/                # Auth, encryption, rate limiting, RBAC (15 modules)
├── ai/                      # Clinical AI integration (monolith-side)
├── edge/                    # Edge platform support
├── financial/               # Financial Engine (schema + routes + services)
├── audit/                   # Audit logging
├── notifications/           # Notification service
├── firewall/                # Rate limiting & firewall
├── gateways/                # External service adapters (Cloudflare, Google AI, insurance, national ID, etc.)
├── legal/                   # Legal/compliance models
├── tasks/                   # Background tasks (Outbox pattern)
├── integration/             # Integration platform (ESB, CDC, HL7/FHIR, connectors)
├── kernel/                  # Kernel runtime (plugin, event bus, background, config, features)
├── national/                # National health platform (rules engine, workflow, scheduling, etc.)
├── nhdw/                    # National Health Data Warehouse
├── nursing/                 # Nursing platform
├── pharmacy/                # Pharmacy platform
├── radiology/               # Radiology platform
├── lims/                    # LIMS workflows
├── hospital/                # Hospital management
├── ems/                     # Emergency Medical Services
├── blood_bank/              # Blood bank & transfusion
├── critical_care/           # Critical care platform
├── biomedical/              # Biomedical engineering
├── public_health/           # Public health & disease surveillance
├── command_center/          # National health command center
├── governance/              # Governance models & policies
├── trust/                   # Trust platform
└── 15+ additional sub-packages (care_continuum, ehr, clinical, document_intelligence, etc.)
```

## Feature Flags

Two flag systems operate in parallel:

1. **Per-tenant** (`backend/app/core/feature_flags.py`) — enables/disables features per lab.
2. **Deployment-wide** (`backend/app/core/sndhs_flags.py`) — global rollout toggles for
   SNDHS-lite and Financial Engine, controlled via environment variables:

| Env var | Default | Controls |
|---------|---------|----------|
| `SNDHS_ENABLE_VISITS` | `false` | Visit tracking (`visits` table + `lab_orders.visit_id`) |
| `SNDHS_ENABLE_NATIONAL_ID` | `false` | National ID / health ID fields on patients |
| `ENABLE_FINANCIAL_ENGINE` | `false` | Financial Engine routes (Phase B+ only) |
| `ENABLE_ADS` | `false` | Advertising/campaign features |
| `FEATURE_BACKGROUND_TASKS` | `true` | Background worker startup |
| `RUNTIME_MODE` | `api` | Execution context: `api` / `worker` / `test` / `cli` |

Never enable `SNDHS_ENABLE_VISITS` or `SNDHS_ENABLE_NATIONAL_ID` without reading
`docs/sndhs/phase1/RUNBOOK.md` — they require data backfill and schema verification first.

## SNDHS-lite Integration (Phase 1)

The National Health Data System integration adds:

- **`patients.national_id`** — Iraqi national ID (encrypted, indexed)
- **`patients.sndhs_health_id`** — SNDHS-assigned health ID
- **`visits` table** — Clinical episode tracking
- **`lab_orders.visit_id`** — Links orders to visits
- **Enhanced audit log (v2)** — Immutable chain with additional SNDHS correlation fields

**Dual-read rule:** Any code that reads `national_id` or `sndhs_health_id` must gracefully
handle `None` — existing rows pre-backfill will have null values. Do not assume these
fields are populated.

**Migration files (all in `backend/migrations/versions/`):**
- `20260505_0001_sndhs_phase1_extend_patients.py`
- `20260505_0002_sndhs_phase1_index_national_id.py`
- `20260505_0003_sndhs_phase1_visits_table.py`
- `20260505_0004_sndhs_phase1_lab_orders_visit_id.py`
- `20260505_0005_sndhs_phase1_audit_logs_v2.py`
- `20260505_0006_sndhs_phase1_constraints.py`

**Backfill:** Run `scripts/sndhs_phase1_backfill.py` before enabling flags on existing data.
**Rollback:** `scripts/sndhs_phase1_rollback.sql` + `scripts/sndhs_phase1_disable_flags.sh`.
**Full spec:** `docs/sndhs/` (22 files covering architecture, DB, API, offline sync, security, governance).

## Financial Engine (Phase A)

Phase A is **schema-only** — the data model is bootstrapped but routes and services are deferred
to Phase B+. Do not add business logic to `backend/app/financial/` without explicit approval.

- Migration: `backend/migrations/versions/20260505_0001_financial_engine_phase_a.py`
- Tables created: `fin_campaigns`, `fin_conversions`, `fin_fraud_flags`, etc.
- Feature gates `ENABLE_FINANCIAL_ENGINE` and `ENABLE_ADS` default to **off**.

## Patient Card System

Digital, QR-backed patient cards with clinical history:

- **Routes:** `backend/app/routes/patient_card.py`
- Card tokens are HMAC-signed — never bypass signature verification
- Returns Arabic-first printable HTML format
- Full longitudinal history endpoint respects `lab_id` tenant isolation
- Scanning endpoint validates token before revealing any patient data

## Migration Policy (MANDATORY — never violate)

Violations cause `NoSuchTableError` on fresh deploys or silent schema drift.

| Rule | Why |
|------|-----|
| **Never modify an existing migration** | Existing DBs have already run it |
| **All schema changes = new revision** | `alembic revision --autogenerate -m "describe"` |
| **`20250322_0000_create_base_schema.py` is immutable** | It is the bootstrap snapshot |
| **Every migration must be idempotent** | Use `_has_column()`, `_table_exists()`, `_index_exists()` guards |
| **New columns must be nullable or have a `server_default`** | Non-nullable columns break existing rows |
| **Test on a clean DB before PR** | The CI migration-gate does this; do it locally first |

```bash
# Create a migration
cd backend && alembic revision --autogenerate -m "add_foo_column"

# Test on clean DB (mirrors CI migration-gate)
docker compose down -v && docker compose up -d postgres
docker compose run --rm gula-backend alembic upgrade head

# Round-trip test (CI also enforces this)
docker compose run --rm gula-backend alembic downgrade -1
docker compose run --rm gula-backend alembic upgrade head
```

## Security Invariants (never violate)

1. All patient-data queries MUST filter by `lab_id = current_user.lab_id` (tenant isolation)
2. All mutations MUST write to the audit log (`AuditLog` model + hash chain)
3. Phone lookups MUST use exact match — never `LIKE` with user input
4. `/metrics/prom` MUST require `Bearer METRICS_BEARER_TOKEN` in production
5. `system_ready` MUST stay False until DB is confirmed reachable
6. Optimistic lock (`version` column) MUST be checked on every `LabResult` mutation
7. Secrets (`SECRET_KEY`, `ENCRYPTION_KEY`, `NID_HMAC_KEY`, `REFRESH_TOKEN_SECRET`,
   `DEVICE_HMAC_KEY`) have no hardcoded fallbacks — absence → hard fail on startup.
   Weak-pattern detection (`_is_weak_secret` in `config.py`) also fails startup.
8. `patients.national_id` MUST be encrypted at rest — never store plaintext national IDs
9. Patient card HMAC tokens MUST be verified before any patient data is returned

## Autonomous Task Boundaries

### Always safe
- Fix pyflakes/flake8 errors
- Add missing indexes (as new migrations)
- Fix typos in log messages
- Add test cases for untested business logic
- Update `.env.example` with new variables
- Read-only diagnostics (`scripts/diagnose-droplet.sh`)

### Requires human approval
- Changes to JWT/auth logic (`app/security/auth.py`, `jwt_guard.py`)
- Changes to billing/subscription-tier logic (`models/subscription.py`, `routes/tiers.py`)
- DB schema changes (any new migration that adds/removes/alters columns)
- API response-shape changes (breaks mobile clients)
- CI pipeline modifications (`.github/workflows/`)
- Enabling `SNDHS_ENABLE_VISITS` or `SNDHS_ENABLE_NATIONAL_ID` on production data
- Any changes to `backend/app/financial/`

### Never autonomously
- Delete or truncate DB tables
- Change defaults for `SECRET_KEY`, `ENCRYPTION_KEY`, `NID_HMAC_KEY`
- Push to `main`
- Remove or reduce audit-log coverage
- Disable rate limiting or security headers
- Modify `20250322_0000_create_base_schema.py`
- Run `scripts/repair-droplet.sh` (destructive — DigitalOcean droplet repair)

## CI Pipeline (`.github/workflows/ci.yml`)

Runs on every push. Jobs in dependency order:

1. **`syntax-gate`** (< 30s, blocks everything) — `py_compile` every file in `app/`
   and `migrations/`, then import-walk with `unittest.mock` stubs to catch
   NameError/AttributeError/SystemExit at module level. Then `flake8 --select=E9,F821`.
2. **`data-preservation-gate`** — runs Data Preservation Constitution quality gate
   (exit code: 0=pass, 1=warning, 2=block merge).
3. **`migration-check`** — `alembic upgrade head` on a fresh postgres:17-alpine,
   verifies required tables (`labs`, `lab_users`, `patients`, `lab_orders`,
   `lab_results`, `outbox_events`, `audit_logs`), then `downgrade -1 && upgrade head`.
4. **`lint`** — `ruff check` on backend + eslint on frontend.
5. **`test`** — `pytest tests/` against postgres:17-alpine + redis:7-alpine.
6. **`security-scan`** — `safety` (CVE scan), `bandit -ll -ii`.
7. **`build-and-push`** — matrix of 8 images (backend + 7 microservices) to GHCR,
   Trivy scan. `latest` tag only on `main`.

Additional workflows:
- **`blue-green-deploy.yml`** — Zero-downtime blue/green deployment
- **`canary-deploy.yml`** — Canary deployment with configurable percentage
- **`deploy.yml`** — Standard deployment pipeline
- **`auto-rollback.yml`** — Automatic rollback on health check failure
- **`frontend-e2e.yml`** — Playwright E2E tests (28 tests, 7 suites)
- **`frontend-pwa.yml`** — PWA compliance tests
- **`nightly.yml`** — Nightly full test suite
- **`preview-deploy.yml`** — Preview deployments for PRs
- **`release.yml`** — Release workflow
- **`quality-gate.yml`** — Quality gate enforcement

Locally, `make ci` replicates syntax-gate + lint + docker build — the fastest
feedback loop before pushing.

## Testing

**85+ test files** (2,148+ tests) in `backend/tests/`. Key ones:

| File | What it covers |
|------|----------------|
| `test_comprehensive.py` | Full integration tests across all major routes |
| `test_stress.py` | Stress & performance under load |
| `test_system_improvements.py` | Clinical interpretation, intelligence APIs, stats |
| `test_security.py` | JWT, auth, encryption invariants |
| `test_patient_card.py` | QR card generation, scanning, HMAC tokens |
| `test_mpi_matcher.py` | Master Patient Index deduplication |
| `test_outbox_service.py` | Event outbox guaranteed delivery |
| `test_feature_flags.py` | Per-tenant feature matrix |
| `test_edge_platform.py` | Edge site synchronization |
| `test_stability_assertions.py` | Data integrity checks |
| `test_abac.py` | Attribute-Based Access Control |
| `test_ai_platform.py` | AI platform orchestration |
| `test_clinical_safety.py` | Clinical safety invariants |
| `test_tenant_isolation_matrix.py` | Multi-tenant isolation |
| `test_chaos_survival.py` | Chaos engineering resilience |
| `test_migration_resilience.py` | Migration round-trip integrity |
| `test_kernel/` (38 files) | Kernel runtime tests |
| `test_kernel_hardening/` (7 files) | Kernel hardening + chaos |

## Key Files

| File | Purpose |
|------|---------|
| `backend/app/main.py` | FastAPI app, lifespan, middleware stack, background loops, route registration |
| `backend/app/config.py` | Env var loading + hard-fail on missing/weak secrets; SNDHS/Financial flags |
| `backend/app/database.py` | SQLAlchemy engine, pool, request-correlation contextvars |
| `backend/app/core/self_healing.py` | Circuit breaker, `DegradedModeMiddleware` |
| `backend/app/core/auto_repair.py` | Auto-repair engine (GC, pool recycle) |
| `backend/app/core/startup_guard.py` | `system_ready` flag + startup validation |
| `backend/app/core/feature_flags.py` | Per-tenant feature matrix |
| `backend/app/core/sndhs_flags.py` | SNDHS-lite deployment-wide toggles |
| `backend/app/security/rbac.py` | 10 roles × 16 permissions |
| `backend/app/security/auth.py` | JWT encode/decode, `get_current_user` |
| `backend/app/domain/order_state.py` | Lab-order state machine |
| `backend/app/services/outbox_service.py` | Guaranteed event delivery (outbox pattern) |
| `backend/app/services/audit_service.py` | SHA-256 hash-chain audit logging |
| `backend/app/routes/patient_card.py` | Digital QR-backed patient cards |
| `backend/app/routes/stats.py` | Statistics & trends API |
| `backend/app/routes/authorization.py` | RBAC/ABAC authorization routes |
| `backend/app/financial/` | Financial Engine skeleton (Phase A — schema only) |
| `backend/app/integration/` | Integration platform (ESB, CDC, HL7/FHIR) |
| `backend/app/kernel/` | Kernel runtime (plugin system, event bus) |
| `backend/migrations/versions/` | Alembic migrations — immutable once merged |
| `cloudflare/` | Cloudflare DNS, WAF, Worker, R2 config |
| `terraform/` | Terraform IaC (12 modules, 5 environments) |
| `scripts/self_audit_agent.py` | Claude-powered self-audit |
| `scripts/sndhs_phase1_backfill.py` | SNDHS Phase 1 data backfill |
| `scripts/diagnose-droplet.sh` | Read-only DigitalOcean diagnostics |
| `scripts/repair-droplet.sh` | DigitalOcean droplet repair (destructive) |
| `config/haproxy/haproxy.cfg` | Load balancer for `make scale` |
| `config/prometheus/` | Scrape config + alerting rules |
| `config/grafana/` | Provisioned dashboards |
| `services/device_bridge/` | LabLink-Core — ASTM/HL7 device integration |
| `services/device_bridge/app/integration/gula_client.py` | Device bridge → GULA API client |
| `frontend-v2/src/` | Rich React + Firebase frontend (citizen/doctor/lab/ministry portals) |
| `nhop-platform/` | National citizen registry companion service |
| `docs/sndhs/` | 22-file SNDHS architecture & deployment spec |
| `docs/sndhs/phase1/RUNBOOK.md` | SNDHS Phase 1 production deployment guide |

## Self-Audit Workflow

A Claude agent that scans the codebase and optionally applies safe fixes:

```bash
ANTHROPIC_API_KEY=... python3 scripts/self_audit_agent.py              # report only
ANTHROPIC_API_KEY=... python3 scripts/self_audit_agent.py --fix        # auto-apply safe fixes
ANTHROPIC_API_KEY=... python3 scripts/self_audit_agent.py --watch 3600 # hourly

# Via make
make self-audit        # report-only
make self-audit-fix    # auto-fix
```

## Kill Switch & Admin

```bash
make kill-switch-on    # DigitalOcean-level traffic block
make kill-switch-off
make control-stats     # control-layer stats (requires GULA_ADMIN_TOKEN)
```

## Horizontal Scaling

```bash
# Scale to N backend instances behind HAProxy
docker compose -f docker-compose.yml -f docker-compose.scale.yml up -d --scale gula-backend=5

# Monitor load distribution
open http://localhost:8404/stats
```

## Deployment Targets

| Target | Config location | Notes |
|--------|----------------|-------|
| Docker Compose (primary MVP) | `docker-compose.yml` | postgres + redis + backend + api-gateway |
| Full infra | `docker-compose.full.yml` | + Prometheus, Grafana, HAProxy, Loki, RabbitMQ |
| Kubernetes | `k8s/` (base + overlays) | Not primary — for future scale-out |
| DigitalOcean | `digitalocean/` | Droplet-based; use `scripts/deploy.sh` |
| Render | `render.yaml` | PaaS alternative |
| Supabase | `supabase/` | Managed Postgres integration |
| Cloudflare | `cloudflare/` | Edge workers / CDN |

## Env File Conventions

- `.env.example` — template, tracked in git; update it whenever you add a new env var
- `.env` — real secrets, gitignored
- `.env.production` — production template, tracked (no real secrets, just variable names + comments)
- `make secrets-gen` — prints a block of strong random values you can paste into `.env`

Key env vars added with recent features:

| Variable | Purpose |
|----------|---------|
| `SNDHS_ENABLE_VISITS` | Enable SNDHS visit tracking (default: false) |
| `SNDHS_ENABLE_NATIONAL_ID` | Enable national ID fields on patients (default: false) |
| `ENABLE_FINANCIAL_ENGINE` | Enable Financial Engine routes (default: false) |
| `ENABLE_ADS` | Enable advertising/campaign features (default: false) |
| `RUNTIME_MODE` | Execution context: api / worker / test / cli (default: api) |
| `FEATURE_BACKGROUND_TASKS` | Enable background worker on startup (default: true) |
| `SENTRY_DSN` | Optional Sentry error tracking DSN |

## Firebase Removal

Firebase (firebase, firebase-auth, Firestore) has been fully removed from the
frontend-v2 production codebase:
- `src/firebase.ts` and `src/firebase-auth.ts` deleted (unused — no views imported them)
- `firebase` and `@firebase/eslint-plugin-security-rules` removed from package.json
- All data flows exclusively through `api/client.ts` → backend API

The only remaining Firebase reference is `FCM_SERVER_KEY` in backend `config.py`
(optional Firebase Cloud Messaging for push notifications — not a data dependency).

## Demo Data Generator

`scripts/generate_demo_data.py` generates a complete synthetic national healthcare
ecosystem in an isolated Demo Tenant. Run against a dedicated demo database:

```bash
# Set up demo database
createdb gula_demo
# Run migrations on demo DB
DATABASE_URL=postgresql://gula:gula@localhost:5432/gula_demo alembic upgrade head
# Generate demo data (200+ users, 200 patients, all roles, 18 governorates)
DATABASE_URL=postgresql://gula:gula@localhost:5432/gula_demo python3 scripts/generate_demo_data.py

# National Digital Twin (10K+ users, 100K+ patients, full FHIR/HL7 export)
DATABASE_URL=postgresql://gula:gula@localhost:5432/gula_demo python3 scripts/generate_demo_data.py --mode twin
```

Demo admin credentials: `admin@demo.gula.iq` / `Demo@ADMIN!`

The generator creates:
- National tenant + 18 governorate sub-tenants
- Organizations (health directorates), facilities (hospitals, PHCs, labs), departments, sections
- Users for every healthcare role (65+ role types, 200+ accounts demo / 10K+ twin)
- Synthetic patients (200+ demo / 100K+ twin), orders, samples, lab results, audit logs
- CSV/Markdown output files (USER_MATRIX.csv, ROLE_MATRIX.csv, DEMO_PASSWORDS.md, etc.)
- **Twin mode only**: FHIR export (Patient/Organization resources), HL7 messages (ORU^R01),
  workflow validation, role validation, performance benchmarks, public health surveillance,
  security report, enterprise readiness certification

All data uses the `DEMO_` prefix and is fully isolated from production.
Never run against a production database.

## Enterprise Governance Certification

`scripts/enterprise_governance_certification.py` performs a comprehensive audit
of every subsystem against enterprise production standards. It generates an
evidence-based certification report with blockers, risks, and recommendations.

```bash
python3 scripts/enterprise_governance_certification.py --output-dir ./governance_report
```

The certification audits:
- Repository integrity, architecture compliance, code quality, security posture
- Authentication (90%+ endpoint auth), RBAC model, tenant isolation
- Audit trail (hash-chain immutable logs), API governance
- Clinical workflows, AI platform governance, integration platform
- Observability (health checks, logging, metrics, circuit breaker)
- Disaster recovery (backup, PITR, failover, DR scripts)
- Documentation coverage, frontend API connectivity

Output: `NATIONAL_CERTIFICATION_REPORT.md` with PASS/WARN/FAIL per check,
blockers list, statistics, and certification classification
(DEVELOPMENT → ALPHA → BETA → RELEASE CANDIDATE → PRODUCTION READY →
ENTERPRISE READY → NATIONAL READY).

## Identity Enterprise Certification

`scripts/identity_enterprise_certification.py` performs a comprehensive audit
of the identity platform against enterprise standards. It verifies that the
Identity Platform is the **single trusted identity provider** for the entire
GULA ecosystem — no subsystem implements its own authentication or authorization.

```bash
python3 scripts/identity_enterprise_certification.py --output-dir ./identity_report
```

The certification checks 194 criteria across 15 categories:
- Identity Models, Authentication (JWT, OAuth2, OIDC, MFA/WebAuthn, API keys)
- Authorization (RBAC + ABAC, tenant isolation, delegation, break-glass)
- Identity Governance (MPI: Fellegi-Sunter probabilistic matching, hash-chained audit)
- Security Controls (secrets, passwords, rate limiting, session management)
- Audit Trail (SHA-256 hash chain, authorization audit, merge audit)
- Frontend integration (AuthContext, token management, 401 handling)

Output: 8 files in `./identity_report/`:
- `IDENTITY_ARCHITECTURE.md` — Full architecture with layer diagram and flow summary
- `ROLE_CATALOG.md` — 9 roles with hierarchy, levels, management rules
- `PERMISSION_CATALOG.md` — 16 extended + 13 legacy permissions by role
- `TENANT_MODEL.md` — Multi-level hierarchy (Ministry → Governorate → Facility → Department)
- `AUTH_FLOW.md` — Login, MFA, OAuth2, OIDC, token lifecycle diagrams
- `SECURITY_MODEL.md` — Controls by layer (transport, password, token, MFA, secrets)
- `AUDIT_MODEL.md` — 7 audit domains, hash-chain integrity, event catalog
- `IDENTITY_CERTIFICATION.md` — Pass/fail report with certification classification

## Self-Audit Workflow
