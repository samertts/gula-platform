# CLAUDE.md — GULA Platform Primary AI Operating Manual

> **Version:** 3.0 — Ratified under PROGRAM-012 / PROGRAM-012A
> **Mandate:** This is the **first file every AI model and developer must read** when
> working on this repository. It is the single authoritative entry point for project
> philosophy, architecture, standards, governance, and knowledge navigation.
> **Supreme Authority:** `AI_OPERATING_CONSTITUTION.md` (CONST-000001) supersedes all
> rules below. If any conflict exists, the constitution wins.
> **Read chain:** `AI_OPERATING_CONSTITUTION.md` → `CLAUDE.md` → `AGENTS.md` (auto-loaded instructions + anchored state)
> → `docs/brain/PROJECT_BRAIN.md` (live knowledge index) → domain docs.
> **Companion governance:** `docs/ai/AI_GOVERNANCE.md` (operations),
> `docs/constitution/32_AI_EXECUTION_CONSTITUTION.md` (law),
> `docs/ai/RISK_REGISTER.md`, `docs/ai/MASTER_ROADMAP.md`.

## Table of Contents

1. [Mission & Non-Negotiable Principles](#1-mission--non-negotiable-principles)
2. [AI Governance — Deterministic Session Protocol](#2-ai-governance)
3. [Knowledge Navigation (Project Brain)](#3-knowledge-navigation)
4. [Repository Shape (30-Second Map)](#4-repository-shape)
5. [Common Commands](#5-common-commands)
6. [Architecture](#6-architecture)
7. [Feature Flags & SNDHS](#7-feature-flags--sndhs)
8. [Migration Policy (MANDATORY)](#8-migration-policy)
9. [Security Invariants (Never Violate)](#9-security-invariants)
10. [Autonomous Task Boundaries](#10-autonomous-task-boundaries)
11. [CI Pipeline](#11-ci-pipeline)
12. [Testing](#12-testing)
13. [Deployment Targets & Env Conventions](#13-deployment-targets--env-conventions)
14. [Certification Suites](#14-certification-suites)
15. [Key Files](#15-key-files)
16. [Decision History & Programs](#16-decision-history--programs)

---

## 1. Mission & Non-Negotiable Principles

Arabic-first healthcare platform for Iraqi medical laboratories. This is a **monorepo**
consolidating three previous repositories:

| Former Repo | Location | Role |
|-------------|----------|------|
| `samertts/gula-platform` | `backend/`, `services/`, `archive/legacy/nhop-platform/`, `ai/` | Core platform (source of truth) |
| `samertts/LabLink-Core` | `services/device_bridge/` | Lab instrument integration (ASTM/HL7) |
| `samertts/Front-end-` | `archive/frontend-v2/` | Rich React + Firebase UI |

Production stack: **FastAPI monolith** (`backend/app/`, Python 3.12) backed by
PostgreSQL 16/17 + Redis 7; **App version 2.5.0** (`config.py`).

Core principles (NON-NEGOTIABLE — see `docs/constitution/01-04`):
1. **Stability first** — never break working code to add features
2. **Data integrity above all** — no change may risk patient data loss
3. **Fix before feature** — bugs and security issues take priority
4. **Test then commit** — verification before every commit
5. **National scale** — every decision must support deployment across all Iraqi
   governorates (Ministry → Health Directorates → Hospitals → Laboratories hierarchy)
6. **Dormant modules are strategic assets** — never remove them; improve without
   activating unfinished functionality

## 2. AI Governance

### 2.1 The Permanent Constitution (PROGRAM-CONSTITUTION-001)

| Article | Mandate |
|---------|---------|
| Free First | Search for FREE solution before any paid alternative |
| Open Source First | Open Source preferred over proprietary |
| Self-Hosted First | Self-hosted before hosted SaaS |
| Reuse Before Build | Never duplicate existing functionality |
| Zero Paid Dependency | Paid software requires documented exception |
| No Vendor Lock-In | Every component MUST be replaceable |
| Local AI First | Self-hosted inference (Ollama) before commercial APIs |
| Free Security First | OpenSSL, Let's Encrypt, WireGuard before commercial |

Enforced by: `governance/` engines + `scripts/constitution_enforcer.py` +
CI `constitution-compliance.yml`. Full policy:
`docs/constitution/COST_GOVERNANCE.md`, `docs/architecture/FREE_FIRST_POLICY.md`.

### 2.2 Deterministic Session Protocol (MANDATORY for every AI session)

1. **Read**: CLAUDE.md → AGENTS.md → `docs/brain/PROJECT_BRAIN.md` → domain docs.
2. **Plan**: atomic tasks; estimate risk, dependencies, affected modules, tests, rollback.
3. **Impact analysis**: files, APIs, tests, docs, DB objects, Android/Frontend surfaces.
4. **Implement** in small steps; never batch unrelated changes.
5. **Validate**: `make validate` — hard gates must pass before commit.
6. **Regression review**: `make validate` compares against
   `reports/validation/baseline.json`; **any regression blocks the commit**.
7. **Self-review**: correctness, architecture, security, naming, backward compatibility.
8. **Safe commit**: conventional commits, atomic, risk level in body for HIGH/CRITICAL.
9. **Knowledge update**: `make brain` on structural changes (new modules/endpoints/migrations).
10. **Report**: honest results — never fabricate, never skip verification.

Full protocol, severity model, rejection rules (R1–R10) and repair rules (P1–P5):
`docs/constitution/32_AI_EXECUTION_CONSTITUTION.md` and `docs/ai/AI_GOVERNANCE.md`.

### 2.3 Validation & Regression Gates

```bash
make validate              # fast scope: ruff + tsc + eslint + brain freshness + tech-debt
make validate SCOPE=full   # adds unit tests, architecture compliance, scorecard, constitution
python3 scripts/enterprise_validation_engine.py --update-baseline  # after intentional improvement
```

- Hard gates (block commit): ruff errors, TypeScript errors, ESLint errors, unit tests,
  brain freshness. Advisory: architecture compliance, scorecard, constitution.
- Reports: `reports/validation/validation_report.{json,md}` + `baseline.json`.
- Multi-AI consensus: conflicting implementations are never merged automatically
  (Constitution 32.6).

## 3. Knowledge Navigation

**`docs/brain/PROJECT_BRAIN.md`** is the live Project Brain — a generated knowledge
index of structure, modules, routes, services, migrations, tests, CI, docs, programs
and environments. It is authoritative for counts and inventories; this file is
authoritative for behavior and invariants.

| Need | Go to |
|------|-------|
| Live knowledge index (counts, modules, programs) | `docs/brain/PROJECT_BRAIN.md` |
| Auto-loaded agent instructions + anchored state | `AGENTS.md` |
| Constitution (32 articles) | `docs/constitution/` |
| Architecture | `ARCHITECTURE.md`, `docs/architecture/` |
| ADRs | `architecture/`, `docs/adr/` |
| Security | `security/`, `docs/security/` |
| Permissions & roles | `PERMISSION_CATALOG.md`, `ROLE_CATALOG.md`, `PERMISSION_MATRIX.csv` |
| Roadmaps | `ROADMAP.md`, `docs/ai/MASTER_ROADMAP.md` |
| Risks | `security/RISK_REGISTER.md`, `docs/ai/RISK_REGISTER.md` |
| Release history | `CHANGELOG.md`, `docs/reports/`, `reports/` |

## 4. Repository Shape

```
gula-platform/
├── backend/app/          # PRODUCTION monolith (FastAPI, Python 3.12) — source of truth
│   ├── routes/           # thin route modules → delegate to services/
│   ├── services/         # business logic (extracted per PROGRAM-BACKEND-001)
│   ├── models/           # SQLAlchemy ORM models
│   ├── core/             # startup_guard, self_healing, auto_repair, feature flags
│   ├── security/         # auth, RBAC/ABAC, encryption, rate limiting
│   ├── kernel/           # plugin system, event bus, runtime
│   ├── national/         # national health platform modules
│   └── 15+ bounded contexts (ehr, pharmacy, radiology, lims, hospital, ...)
├── backend/migrations/   # Alembic — IMMUTABLE once merged
├── shared/               # shared engineering library (security, fhir, etc.)
├── governance/           # constitution-as-code engines (Free/OSS-First, ADR, procurement)
├── security/             # security framework docs + modules
├── frontend-v3/          # CURRENT frontend (React, Arabic-first RTL)
├── archive/frontend-v2/  # legacy rich React SPA (archived, ADR-028)
├── archive/legacy/frontend/  # static HTML PWA (archived, ADR-028)
├── client/               # tRPC + React SPA
├── mobile/               # Android (Flutter?)
├── services/             # device_bridge (ASTM/HL7) + future microservice stubs
├── ai/                   # clinical AI modules (top-level)
├── archive/legacy/nhop-platform/  # National Health Oversight Platform (archived, ADR-028)
├── edge_agent/           # off-site/offline edge computing agent
├── scripts/              # 80+ operational + governance scripts
├── docs/                 # constitution, architecture, sndhs, brain, ai governance, ...
├── config/               # prometheus, grafana, haproxy, ...
├── k8s/ helm/ terraform/ # infrastructure as code
└── reports/              # certification & validation reports
```

Experimental stubs to avoid committing business logic: `backend/services/`,
`backend/core/` (both have `api/` subdirs). `backend/app/financial/` is Phase A
schema-only — no business logic without approval.

## 5. Common Commands

All development is orchestrated through the **Makefile** at the repo root
(`make help` lists every target):

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

# Development
make lint              # pyflakes + flake8 (E9, F821 — errors only)
make test              # cd backend && pytest tests/ -v
make ci                # syntax-gate + lint + docker build (full CI locally)

# Governance (PROGRAM-012)
make brain             # regenerate docs/brain/PROJECT_BRAIN.md (run on structural changes)
make validate          # enterprise validation engine (fast scope)
make validate SCOPE=full  # + unit tests, architecture compliance, scorecard, constitution
make compliance        # architecture compliance engine (L1-L7)
make scorecard         # repository scorecard (10 axes, 0-100)
make certify           # run certification tools
make self-audit        # Claude-powered self-audit (report only)

# Testing (single test — use pytest directly)
cd backend && python -m pytest tests/test_security.py -v
cd backend && python -m pytest tests/test_security.py::test_jwt_reject_expired -v

# Database
make db-shell          # psql inside gula-postgres
make redis-cli         # redis-cli (auto-reads REDIS_PASSWORD from .env)
make backup            # pg_dump → ./backups/gula_<ts>.sql.gz

# Monitoring (opt-in profile)
make monitoring        # prometheus + grafana (internal only — SSH tunnel)
make metrics-token     # write METRICS_BEARER_TOKEN → config/prometheus/metrics_token

# Scaling
make scale REPLICAS=5  # HAProxy + N backend replicas (stats at :8404/stats)

# Secrets & admin
make secrets-gen       # strong random SECRET_KEY/ENCRYPTION_KEY/etc.
make kill-switch-on/off  # DigitalOcean-level traffic block

# DigitalOcean operations
scripts/repair-droplet.sh    # comprehensive droplet repair (DESTRUCTIVE — use with care)
scripts/diagnose-droplet.sh  # read-only diagnostics (safe to run anytime)
```

## 6. Architecture

### Request Lifecycle

Internet → host nginx (TLS) → `api-gateway` (Docker nginx on 127.0.0.1:8080) →
`gula-backend` (FastAPI, gunicorn + uvicorn workers, `expose: 8000`) →
PostgreSQL + Redis. The backend never exposes a public port itself.

### Middleware Stack (order matters — see `backend/app/factory.py`)

1. `MaxBodySizeMiddleware` — 413 above `MAX_REQUEST_BODY_MB` (default 10)
2. `RequestIDMiddleware` — `X-Request-ID` + log ctx + DB correlation vars
3. `DocsAuthMiddleware` — guards `/docs`, `/redoc`, `/openapi.json` in production
4. `CORSMiddleware`
5. `RequestTimingMiddleware` — access log + `X-Response-Time`
6. `SecurityHeadersMiddleware` — CSP, HSTS, X-Frame-Options
7. `GZipMiddleware`
8. `DegradedModeMiddleware` — rejects writes when DB circuit is open
9. `ReadinessMiddleware` — 503 on non-whitelisted paths until `system_ready`
10. `KernelMiddleware` — kernel context per request
11. `ConcurrencyLimitMiddleware` — per-worker cap (default 50); **clinical writes
    (`/results`, `/orders`, `/samples`, `/critical-alerts`) are exempt** — patient
    safety is never shed.

### Startup & Self-Healing

- **Lifespan pattern** (never `@app.on_event()` — deprecated).
- **Startup Guard** (`backend/app/core/startup_guard.py`): blocks readiness until
  config validated, DB reachable, migrations checked, critical data seeded. Never set
  `system_ready = True` from elsewhere.
- **Self-healing** (`core/self_healing.py` + `core/auto_repair.py`): circuit breaker,
  auto-repair (GC, pool recycle), adaptive concurrency. A `_health_alert_loop`
  watchdog grades GREEN/YELLOW/RED every 60s → `ALERT_WEBHOOK_URL`.

### Health Endpoints

| Path | Purpose |
|------|---------|
| `/health`, `/health/live` | liveness |
| `/health/ready` | readiness (Docker healthcheck + api-gateway `depends_on`) |
| `/health/status` | diagnostic — explains WHY startup failed |
| `/health/deep` | grade + latencies + memory (`make health-deep`) |

All five bypass readiness/degraded/concurrency middlewares.

### Database Connection Pool

`WEB_CONCURRENCY × (DB_POOL_SIZE + DB_MAX_OVERFLOW) < postgres.max_connections`.
Defaults (3 × (6+12) = 54) fit inside Postgres's default 100. Recheck on knob changes.

## 7. Feature Flags & SNDHS

Two flag systems: per-tenant (`core/feature_flags.py`) and deployment-wide
(`core/sndhs_flags.py`):

| Env var | Default | Controls |
|---------|---------|----------|
| `SNDHS_ENABLE_VISITS` | `false` | Visit tracking |
| `SNDHS_ENABLE_NATIONAL_ID` | `false` | National ID / health ID fields |
| `ENABLE_FINANCIAL_ENGINE` | `false` | Financial Engine routes (Phase B+ only) |
| `ENABLE_ADS` | `false` | Advertising/campaign features |
| `FEATURE_BACKGROUND_TASKS` | `true` | Background worker startup |
| `RUNTIME_MODE` | `api` | `api` / `worker` / `test` / `cli` |

**Never enable `SNDHS_ENABLE_VISITS`/`SNDHS_ENABLE_NATIONAL_ID` without reading
`docs/sndhs/phase1/RUNBOOK.md`** (requires backfill + schema verification).

**Dual-read rule:** any code reading `national_id`/`sndhs_health_id` must handle `None`
(pre-backfill rows). Backfill: `scripts/sndhs_phase1_backfill.py`. Rollback:
`scripts/sndhs_phase1_rollback.sql` + `scripts/sndhs_phase1_disable_flags.sh`.

## 8. Migration Policy (MANDATORY)

Violations cause `NoSuchTableError` on fresh deploys or silent schema drift.

| Rule | Why |
|------|-----|
| **Never modify an existing migration** | Existing DBs have already run it |
| **All schema changes = new revision** | `alembic revision --autogenerate -m "describe"` |
| **`20250322_0000_create_base_schema.py` is immutable** | Bootstrap snapshot |
| **Every migration must be idempotent** | `_has_column()`, `_table_exists()`, `_index_exists()` guards |
| **New columns nullable or with `server_default`** | Non-nullable breaks existing rows |
| **Test on a clean DB before PR** | CI migration-gate does this; do it locally first |

```bash
cd backend && alembic revision --autogenerate -m "add_foo_column"
docker compose down -v && docker compose up -d postgres
docker compose run --rm gula-backend alembic upgrade head
docker compose run --rm gula-backend alembic downgrade -1   # round-trip
docker compose run --rm gula-backend alembic upgrade head
```

## 9. Security Invariants

1. All patient-data queries MUST filter by `lab_id = current_user.lab_id` (tenant isolation)
2. All mutations MUST write to the audit log (`AuditLog` + hash chain)
3. Phone lookups MUST use exact match — never `LIKE` with user input
4. `/metrics/prom` MUST require `Bearer METRICS_BEARER_TOKEN` in production
5. `system_ready` MUST stay False until DB confirmed reachable
6. Optimistic lock (`version` column) MUST be checked on every `LabResult` mutation
7. Secrets (`SECRET_KEY`, `ENCRYPTION_KEY`, `NID_HMAC_KEY`, `REFRESH_TOKEN_SECRET`,
   `DEVICE_HMAC_KEY`) have **no hardcoded fallbacks** — absence/weakness → startup hard fail
8. `patients.national_id` MUST be encrypted at rest — never plaintext
9. Patient card HMAC tokens MUST be verified before returning any patient data

## 10. Autonomous Task Boundaries

**Always safe:** fix lint errors; add missing indexes (as new migrations); fix log
typos; add tests for untested logic; update `.env.example`.

**Requires human approval:** JWT/auth logic; billing/subscription logic; DB schema
changes; API response-shape changes (breaks mobile clients); CI pipeline changes;
enabling SNDHS flags on production; `backend/app/financial/` changes.

**Never autonomously:** delete/truncate DB tables; change secret defaults; push to
`main`; remove/reduce audit coverage; disable rate limiting/security headers; modify
`20250322_0000_create_base_schema.py`; run `scripts/repair-droplet.sh`.

## 11. CI Pipeline

Primary: `.github/workflows/ci.yml` — `syntax-gate` (py_compile + import-walk +
E9/F821) → `data-preservation-gate` → `migration-check` (fresh PG, round-trip) →
`lint` (ruff + eslint) → `test` (pytest vs PG+Redis) → `security-scan` (safety,
bandit) → `build-and-push` (8 images, Trivy).

Other workflows: blue-green-deploy, canary-deploy, deploy, auto-rollback,
frontend-e2e (Playwright), frontend-pwa, nightly, preview-deploy, release,
quality-gate, scorecard, **constitution-compliance** (governance rules), and
**ai-governance** (brain freshness + validation gate).

Locally: `make ci` replicates syntax-gate + lint + docker build.

## 12. Testing

- **Backend:** 399 tests pass (150 unit + 146 service + 103 comprehensive) — run
  `make test` or `cd backend && python -m pytest tests/ -q`.
- **Frontend-v3:** 54 unit tests (Vitest) + Playwright E2E (28 tests, 7 suites).
- **Unit test files** for extracted services live in `backend/tests/unit/` (10 files).
- Key suites: `test_comprehensive.py` (integration), `test_security.py` (JWT/auth),
  `test_tenant_isolation_matrix.py`, `test_clinical_safety.py`, `test_kernel/` (38 files).
- Full inventory: `docs/brain/PROJECT_BRAIN.md` §2.1.
- **Every bug fixed → regression test. Every feature → tests** (Constitution 32).

## 13. Deployment Targets & Env Conventions

| Target | Config | Notes |
|--------|--------|-------|
| Docker Compose (primary) | `docker-compose.yml` | postgres + redis + backend + api-gateway |
| Full infra | `docker-compose.full.yml` | + Prometheus, Grafana, HAProxy, Loki, RabbitMQ |
| Kubernetes | `k8s/` | future scale-out (not primary) |
| DigitalOcean | `digitalocean/` | `scripts/deploy.sh` |
| Render | `render.yaml` | PaaS alternative |
| Cloudflare | `cloudflare/` | edge workers / CDN |
| National | `archive/legacy/nhop-platform/`, `docs/sndhs/` | governorate deployment |

Env files: `.env.example` (template, tracked), `.env` (secrets, gitignored),
`.env.production` (no real secrets). `make secrets-gen` prints strong values.
Docker requires `shared/` volume mount (`-v /path/to/shared:/app/shared:ro`) and
`REDIS_URL` with password.

## 14. Certification Suites

| Tool | Output |
|------|--------|
| `scripts/enterprise_governance_certification.py --output-dir ./governance_report` | NATIONAL_CERTIFICATION_REPORT.md (7 levels) |
| `scripts/identity_enterprise_certification.py --output-dir ./identity_report` | 8 files, 194 criteria |
| `backend/app/certification/` (live engine) | `/certification` API, dimension evaluators |
| `scripts/certification_check.py` | certification decision |
| `scripts/enterprise_validation_engine.py` | reports/validation/*.json/md |

## 15. Key Files

Full inventory in `docs/brain/PROJECT_BRAIN.md`. Critical ones:

| File | Purpose |
|------|---------|
| `backend/app/main.py` | App init, lifespan, middleware, route registration |
| `backend/app/factory.py` | Route registration (line 440+) |
| `backend/app/config.py` | Env loading + hard-fail on weak secrets; SNDHS/Financial flags |
| `backend/app/database.py` | SQLAlchemy engine, pool, correlation contextvars |
| `backend/app/core/startup_guard.py` | `system_ready` + startup validation |
| `backend/app/core/self_healing.py` | Circuit breaker, DegradedModeMiddleware |
| `backend/app/security/rbac.py` | Roles × permissions |
| `backend/app/security/auth.py` | JWT encode/decode, `get_current_user` |
| `backend/app/services/*` | 10 extracted services (lab, sample, admin, quality_control, metrics, mobile, test_result, stats, dashboard, outbox) |
| `backend/migrations/versions/` | 50 Alembic migrations — immutable once merged |
| `scripts/project_brain.py` | Project Brain generator (make brain) |
| `scripts/enterprise_validation_engine.py` | Validation + regression gate (make validate) |
| `scripts/constitution_enforcer.py` | 25-rule constitution enforcement |
| `scripts/zero_drift_engine.py` | Frontend↔backend consistency (auto-heals) |
| `scripts/self_audit_agent.py` | Claude-powered self-audit |
| `docs/brain/PROJECT_BRAIN.md` | Live knowledge index |
| `docs/ai/AI_GOVERNANCE.md` | AI governance operating procedures |

## 16. Decision History & Programs

- **PROGRAM-012/012A (2026-07-31)** — AI Governance, Project Brain, Execution Layer:
  constitution Article 32, validation engine, regression gate, brain, governance docs.
  See `docs/ai/MASTER_ROADMAP.md`.
- **PROGRAM-CONSTITUTION-001** — Permanent constitution (Free/OSS/Self-Hosted First).
- **PROGRAM-BACKEND-001** — Service extraction: 10 services, −71% route line count,
  150 unit tests.
- **ADRs**: `architecture/`, `docs/adr/` — every architectural change requires an ADR
  (Constitution 27).
- **Changelog**: `CHANGELOG.md` (release history).
- **Program reports**: repo root (`PROGRAM-*.md`, `MISSION-*.md`) + `docs/reports/`.

**Every architectural decision → ADR. Every public feature → documentation.
Every deployment change → deployment docs.** (Documentation Policy)
