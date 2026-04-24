# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## GULA Platform — Medical Laboratory SaaS

Arabic-first healthcare platform for Iraqi medical laboratories. Production stack is
a FastAPI monolith (`backend/app/`) backed by PostgreSQL 16 + Redis 7; a parallel
microservices tree (`services/`) exists for future decomposition but is not the
primary deployment target.

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
```

## Architecture

### Request Lifecycle

Internet → host nginx (TLS) → `api-gateway` (Docker nginx on 127.0.0.1:8080) →
`gula-backend` (FastAPI, gunicorn + uvicorn workers, `expose: 8000`) →
PostgreSQL 16 (+ Redis 7).

The backend never exposes a public port itself. All traffic enters through the gateway.

### Middleware Stack (order matters — see `backend/app/main.py`)

Requests flow through these layers in order; each has a specific role:

1. `MaxBodySizeMiddleware` — 413 above `MAX_REQUEST_BODY_MB` (default 10)
2. `RequestIDMiddleware` — assigns `X-Request-ID` + binds to log ctx + DB correlation vars
3. `DocsAuthMiddleware` — guards `/docs`, `/redoc`, `/openapi.json` in production (admin JWT)
4. `CORSMiddleware`
5. `RequestTimingMiddleware` — per-request access log, `X-Response-Time` header
6. `SecurityHeadersMiddleware` — CSP, HSTS, X-Frame-Options, etc.
7. `GZipMiddleware`
8. `ReadinessMiddleware` — 503 on all non-whitelisted paths until `system_ready` is True
9. `DegradedModeMiddleware` (from `core/self_healing.py`) — rejects writes when DB circuit is open
10. `ConcurrencyLimitMiddleware` — per-worker in-flight cap (`MAX_CONCURRENT_REQUESTS`, default 50).
    Clinical writes (`/results`, `/orders`, `/samples`, `/critical-alerts`) are **exempt** —
    patient-safety operations must never be shed.

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
- **`services/`** (top-level) contains future-decomposed microservices (`lab`,
  `order`, `patient`, `result`, `sample`, `notification`, `ai`, `autonomous_manager`).
  They're shipped as images via the CI matrix but the main deployment still uses
  the monolith. Don't duplicate business logic between them — the monolith is
  source of truth for now.
- **`backend/services/`** and **`backend/core/`** (both with `api/` subdirs) are
  experimental stubs — avoid committing business logic there.

### Database Connection Pool

Formula: `WEB_CONCURRENCY × (DB_POOL_SIZE + DB_MAX_OVERFLOW) < postgres.max_connections`.
Defaults (3 × (6 + 12) = 54) fit inside Postgres's default 100. If you change any
of the three knobs, recheck the budget.

`backend/app/database.py` maintains per-request `contextvars` (`request_id`,
`endpoint`, `user_id`, `lab_id`) so every DB error log is correlated. Set by
middleware — do not read them directly, use `check_db_connection_detail`.

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

## Autonomous Task Boundaries

### Always safe
- Fix pyflakes/flake8 errors
- Add missing indexes (as new migrations)
- Fix typos in log messages
- Add test cases for untested business logic
- Update `.env.example` with new variables

### Requires human approval
- Changes to JWT/auth logic (`app/security/auth.py`, `jwt_guard.py`)
- Changes to billing/subscription-tier logic (`models/subscription.py`, `routes/tiers.py`)
- DB schema changes (any new migration that adds/removes/alters columns)
- API response-shape changes (breaks mobile clients)
- CI pipeline modifications (`.github/workflows/`)

### Never autonomously
- Delete or truncate DB tables
- Change defaults for `SECRET_KEY`, `ENCRYPTION_KEY`, `NID_HMAC_KEY`
- Push to `main`
- Remove or reduce audit-log coverage
- Disable rate limiting or security headers
- Modify `20250322_0000_create_base_schema.py`

## CI Pipeline (`.github/workflows/ci.yml`)

Runs on every push. Jobs in dependency order:

1. **`syntax-gate`** (< 30s, blocks everything) — `py_compile` every file in `app/`
   and `migrations/`, then import-walk with `unittest.mock` stubs to catch
   NameError/AttributeError/SystemExit at module level. Then `flake8 --select=E9,F821`.
2. **`migration-check`** — `alembic upgrade head` on a fresh postgres:16-alpine,
   verifies required tables (`labs`, `lab_users`, `patients`, `lab_orders`,
   `lab_results`, `outbox_events`, `audit_logs`), then `downgrade -1 && upgrade head`.
3. **`smoke-test`** — boot uvicorn and curl `/health`, `/health/ready`, `/health/deep`, `/test-types`.
4. **`backend-test`** — `pytest tests/` against postgres:14.11 + redis:7.2.
5. **`security-scan`** — `safety` (CVE scan), `bandit -ll -ii`, `hadolint`, `gitleaks`,
   `/tmp` write check.
6. **`build-and-push`** — matrix of 8 images (backend + 7 microservices) to GHCR,
   Trivy scan. `latest` tag only on `main`.

Locally, `make ci` replicates syntax-gate + lint + docker build — the fastest
feedback loop before pushing.

## Key Files

| File | Purpose |
|------|---------|
| `backend/app/main.py` | FastAPI app, middleware stack, background loops, route registration |
| `backend/app/config.py` | Env var loading + hard-fail on missing/weak secrets |
| `backend/app/database.py` | SQLAlchemy engine, pool, request-correlation contextvars |
| `backend/app/core/self_healing.py` | Circuit breaker, `DegradedModeMiddleware` |
| `backend/app/core/auto_repair.py` | Auto-repair engine (GC, pool recycle) |
| `backend/app/core/startup_guard.py` | `system_ready` flag + startup validation |
| `backend/app/security/rbac.py` | 9 roles × 13 permissions |
| `backend/app/security/auth.py` | JWT encode/decode, `get_current_user` |
| `backend/app/domain/order_state.py` | Lab-order state machine |
| `backend/app/services/outbox_service.py` | Guaranteed event delivery (outbox pattern) |
| `backend/migrations/versions/` | Alembic migrations — immutable once merged |
| `scripts/self_audit_agent.py` | Claude-powered self-audit (see below) |
| `config/haproxy/haproxy.cfg` | Load balancer for `make scale` |
| `config/prometheus/` | Scrape config + alerting rules |
| `config/grafana/` | Provisioned dashboards |

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

## Env File Conventions

- `.env.example` — template, tracked in git; update it whenever you add a new env var
- `.env` — real secrets, gitignored
- `.env.production` — production template, tracked (no real secrets, just variable names + comments)
- `make secrets-gen` — prints a block of strong random values you can paste into `.env`
