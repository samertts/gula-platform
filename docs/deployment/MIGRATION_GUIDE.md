# GULA Platform — Migration Guide

**Applies to:** v2.5.0
**Last Updated:** 2026-07-23

## Table of Contents

1. [Overview](#1-overview)
2. [Database Migration (Schema Changes)](#2-database-migration-schema-changes)
3. [Application Upgrade](#3-application-upgrade)
4. [Data Migration](#4-data-migration)
5. [SNDHS Phase 1 Migration](#5-sndhs-phase-1-migration-detailed)
6. [Financial Engine Phase A Migration](#6-financial-engine-phase-a-migration)
7. [Deployment Migration](#7-deployment-migration)
8. [Rollback Procedures](#8-rollback-procedures)
9. [Backward Compatibility](#9-backward-compatibility)
10. [Related Documents](#10-related-documents)

---

## 1. Overview

This guide covers all migration scenarios for the GULA Platform. It documents the database schema evolution strategy, application upgrade paths, data backfill procedures, and rollback protocols. Every migration in this codebase is designed to be safe, additive, and reversible.

### Scope

| Migration Type | Risk | Downtime | Reversible |
|---------------|------|----------|------------|
| Schema (additive columns/tables) | Low | None | Yes |
| Schema (constraints/indexes) | Low | None (CONCURRENTLY) | Yes |
| Application code (patch) | Low | None | Yes |
| Application code (minor) | Medium | <5s | Yes |
| Application code (major) | Medium | <15min | Yes |
| Data backfill | Low | None | Yes (idempotent) |
| SNDHS Phase 1 | Low | None | Yes (soft + hard) |
| Financial Phase A | Low | None | Yes |

### Migration States

The platform uses a **linear single-head** Alembic migration history. At any point `alembic current` reports exactly one revision. All 50 migrations form a single chain from the base schema (`20250322_0000`) to the current head.

---

## 2. Database Migration (Schema Changes)

### 2.1 Migration Framework

All schema changes use **Alembic** with SQLAlchemy as the ORM. Migrations live in `backend/migrations/versions/`.

```bash
# Run pending migrations
cd backend && alembic upgrade head

# Or via Docker
docker compose run --rm gula-backend alembic upgrade head

# Check current revision
docker compose run --rm gula-backend alembic current

# Check whether all migrations are applied
docker compose run --rm gula-backend alembic check
```

### 2.2 Migration Policy (MANDATORY)

Violating these rules causes `NoSuchTableError` on fresh deploys or silent schema drift.

| Rule | Why |
|------|-----|
| **Never modify an existing migration** | Existing DBs have already run it |
| **All schema changes = new revision** | `alembic revision --autogenerate -m "describe"` |
| **`20250322_0000_create_base_schema.py` is immutable** | It is the bootstrap snapshot |
| **Every migration must be idempotent** | Use `_has_column()`, `_table_exists()`, `_index_exists()` guards |
| **New columns must be nullable or have a `server_default`** | Non-nullable columns break existing rows |
| **Test on a clean DB before PR** | The CI migration-gate does this; do it locally first |

### 2.3 Creating a New Migration

```bash
cd backend && alembic revision --autogenerate -m "add_foo_column"
```

Always review the generated migration to verify:
- Idempotency guards (`_has_column`, `_table_exists`, `_index_exists`)
- New columns are nullable or have `server_default`
- `CREATE INDEX CONCURRENTLY` is used for indexes on populated tables

### 2.4 Testing Migrations

```bash
# Test on clean DB (mirrors CI migration-gate)
docker compose down -v && docker compose up -d postgres
docker compose run --rm gula-backend alembic upgrade head

# Round-trip test (CI also enforces this)
docker compose run --rm gula-backend alembic downgrade -1
docker compose run --rm gula-backend alembic upgrade head
```

### 2.5 Migration Chain (50 Migrations)

| Category | Date Range | Count | Files |
|----------|-----------|-------|-------|
| Base schema | 2025-03-22 | 1 | `20250322_0000_create_base_schema.py` |
| Core features | 2025-03-22 to 2025-03-29 | 10 | `20250322_0001` through `20260329_0012` |
| Claims, MPI, Consent, Edge | 2026-04 | 4 | `20260407_0001`, `20260413_0001`, `20260417_0001`, `20260428_0001` |
| Stats perf indexes | 2026-05-03 | 1 | `20260503_0001` |
| SNDHS Phase 1 | 2026-05-05 | 6 | `20260505_0001` through `20260505_0006` |
| Financial Phase A | 2026-05-06 | 1 | `20260506_0001` |
| AI safety/interactions | 2026-05-11 | 2 | `20260511_0001`, `20260511_0002` |
| National platforms | 2026-07-14 to 2026-07-16 | 16 | `20260714_0001` through `20260716_0016` |
| AI platform | 2026-07-19 | 1 | `20260719_0001` |
| Gap closure indexes | 2026-07-20 | 1 | `20260720_0001` |
| Authorization | 2026-07-22 | 1 | `20260722_0001` |

### 2.6 Migration During Deployment

The recommended order is **migrations-first, then code deploy**:

```bash
# Step 1: Run migrations (old code is backward-compatible with new schema)
docker compose run --rm gula-backend alembic upgrade head

# Step 2: Verify migration
docker compose run --rm gula-backend alembic current

# Step 3: Deploy new application code
docker compose up -d --no-deps gula-backend

# Step 4: Post-deployment verification
curl -s http://localhost:8080/health/deep | jq .
```

---

## 3. Application Upgrade

### 3.1 Version Numbering

The platform follows semantic versioning: `v<major>.<minor>.<patch>`.

**Current version:** 2.5.0 (`backend/app/config.py`)

| Bump | When | Downtime | Example |
|------|------|----------|---------|
| Major | Breaking changes, DB migrations requiring downtime | <15min | 2.5.0 → 3.0.0 |
| Minor | New features, backward-compatible | <5s | 2.4.0 → 2.5.0 |
| Patch | Bug fixes, security patches | None | 2.5.0 → 2.5.1 |

### 3.2 Recent Release History

| Version | Date | Highlights |
|---------|------|------------|
| 2.5.0 | 2026-07-23 | Current release |
| 2.3.2 | 2026-07-16 | National Notification Platform Tests |
| 2.3.1 | 2026-07-16 | Identity Governance Persistence Tests |
| 2.3.0 | 2026-07-16 | Missions 025-028 (Hospital, Nursing, Pharmacy, Radiology platforms) |
| 2.2.0 | 2026-07-16 | Sprint-001: Missions 017-024, 037-039 |
| 2.1.0 | 2026-07-14 | Engineering Program M4.x |
| 1.0.0 | 2026-07-14 | Foundation Complete |

### 3.3 Upgrade Steps

```bash
# 1. Pull latest code
git pull origin main

# 2. Run database migrations first
docker compose run --rm gula-backend alembic upgrade head

# 3. Rebuild and restart
docker compose up -d --build

# 4. Verify health
make health-deep
```

### 3.4 Zero-Downtime Strategy (Blue/Green)

The platform supports blue-green deployment for zero-downtime upgrades:

```bash
# Step 1: Deploy the green environment
docker compose -f docker-compose.green.yml up -d

# Step 2: Run smoke tests against green
./scripts/smoke-test.sh --target green

# Step 3: Switch traffic from blue to green
cp config/nginx/green.conf config/nginx/active.conf
docker compose exec api-gateway nginx -s reload

# Step 4: Monitor green for 15 minutes
watch -n 5 'curl -s https://api.gula.health/health/deep | jq .grade'

# Step 5: Decommission blue environment
docker compose -f docker-compose.blue.yml down
```

An automated workflow exists at `.github/workflows/blue-green-deploy.yml`.

### 3.5 Canary Deployment

For risk-sensitive upgrades, a canary deployment routes a small percentage of traffic to the new version:

```bash
# Deploy canary (10% traffic)
kubectl apply -f k8s/deployment-canary.yaml

# Gradually increase traffic
kubectl patch canary gula-backend --type merge \
  -p '{"spec":{"canary":{"weight":25}}}'

# Promote to stable
kubectl patch canary gula-backend --type merge \
  -p '{"spec":{"canary":{"weight":100}}}'
```

### 3.6 Rollback Procedure

```bash
# Docker Compose: roll back to previous tag
docker compose up -d --no-deps gula-backend=<previous-tag>

# If DB migration was rolled back, run downgrade
docker compose run --rm gula-backend alembic downgrade -1
```

### 3.7 Full System Rollback

```bash
# Step 1: Stop all services
docker compose down

# Step 2: Restore .env
cp .env.backup .env

# Step 3: Restore database from backup
make backup  # or scripts/restore-test.sh latest

# Step 4: Start with previous image
GULA_IMAGE_TAG=<previous-tag> docker compose up -d

# Step 5: Verify
make health && make health-deep
```

---

## 4. Data Migration

### 4.1 SNDHS Phase 1 Backfill

The SNDHS Phase 1 backfill script (`scripts/sndhs_phase1_backfill.py`) creates one visit per `(patient, calendar-day)` for every existing `lab_order`. It is **idempotent and concurrent-safe** (uses `FOR UPDATE SKIP LOCKED`).

```bash
# Dry run first
docker compose exec gula-backend python scripts/sndhs_phase1_backfill.py --dry-run

# Run backfill (1000 rows per batch, 50ms sleep)
docker compose exec gula-backend python scripts/sndhs_phase1_backfill.py

# Tune for large tables
docker compose exec gula-backend \
  python scripts/sndhs_phase1_backfill.py --batch-size 500 --max-batches 200 --sleep-ms 100
```

Re-run until the final log line is:
```
sndhs_phase1_check OK total_orders=N linked=N visits_created=N elapsed=Ts
```

Verify zero remaining unlinked rows:
```sql
SELECT count(*) AS unlinked FROM lab_orders WHERE visit_id IS NULL;
```

### 4.2 National ID Encryption Migration

`patients.national_id` is encrypted at rest using `NID_HMAC_KEY`. When populating this field:

- Always encrypt using the application-layer encryption service
- Never store plaintext national IDs
- The HMAC key must be stable — changing it breaks existing lookups

**Dual-read rule:** Any code that reads `national_id` or `sndhs_health_id` must gracefully handle `None` — existing rows pre-backfill will have null values.

### 4.3 Data Preservation Guidelines

- All schema changes must be **additive** — never remove or modify existing columns
- New columns must be **nullable** or have a `server_default`
- Backfill scripts must be **idempotent** (safe to re-run)
- Use `FOR UPDATE SKIP LOCKED` for concurrent-safe batch processing
- Always take a full backup before any data migration: `make backup`

---

## 5. SNDHS Phase 1 Migration (Detailed)

> **Source:** `docs/sndhs/phase1/RUNBOOK.md`
> **Risk:** Low · **Downtime:** Zero · **Reversible:** Yes (every step has a documented rollback)

### 5.1 Overview

SNDHS Phase 1 introduces the visit-centric, national-ID-aware foundations on top of the running GULA platform. All new columns are nullable, new tables are additive, constraints land only after a verified backfill, and new code paths sit behind two feature flags (`SNDHS_ENABLE_VISITS`, `SNDHS_ENABLE_NATIONAL_ID`) that default to `false`.

### 5.2 Files Added

| File | Purpose |
|------|---------|
| `backend/migrations/versions/20260505_0001_sndhs_phase1_extend_patients.py` | Add `national_id`, `sndhs_health_id`, `identity_level`, `consent_flags` to `patients` |
| `backend/migrations/versions/20260505_0002_sndhs_phase1_index_national_id.py` | Index on `patients.national_id` |
| `backend/migrations/versions/20260505_0003_sndhs_phase1_visits_table.py` | Create `visits` table |
| `backend/migrations/versions/20260505_0004_sndhs_phase1_lab_orders_visit_id.py` | Add `visit_id` to `lab_orders` |
| `backend/migrations/versions/20260505_0005_sndhs_phase1_audit_logs_v2.py` | Create `sndhs_audit_logs` (enhanced audit v2) |
| `backend/migrations/versions/20260505_0006_sndhs_phase1_constraints.py` | FK constraint + unique index (after backfill) |
| `backend/app/core/sndhs_flags.py` | Feature flag reader module |
| `scripts/sndhs_phase1_backfill.py` | Idempotent batched backfill |
| `scripts/sndhs_phase1_rollback.sql` | SQL rollback script |
| `scripts/sndhs_phase1_disable_flags.sh` | Emergency flag flip |

### 5.3 Pre-requisites

1. `make health-deep` shows **GREEN**
2. Backups are current: `make backup`
3. `git pull` the latest code: `git fetch origin && git checkout main`

### 5.4 Migration Order

Apply migrations 0001–0005 first (all are non-blocking — add columns/tables/indexes only):

```bash
docker compose exec gula-backend alembic upgrade 20260505_0005
```

Verify:
```sql
SELECT column_name FROM information_schema.columns
WHERE table_name = 'patients'
  AND column_name IN ('national_id','sndhs_health_id','identity_level','consent_flags');
SELECT to_regclass('public.visits') AS visits,
       to_regclass('public.sndhs_audit_logs') AS sndhs_audit_logs;
SELECT column_name FROM information_schema.columns
WHERE table_name = 'lab_orders' AND column_name = 'visit_id';
```

### 5.5 Backfill Process

Run the backfill **before** applying step F (constraints):

```bash
# Dry run
docker compose exec gula-backend python scripts/sndhs_phase1_backfill.py --dry-run

# Live run
docker compose exec gula-backend python scripts/sndhs_phase1_backfill.py
```

Re-run until zero unlinked rows remain.

### 5.6 Apply Constraints (Step F)

Only after backfill reports zero unlinked rows:

```bash
docker compose exec gula-backend alembic upgrade head
```

This migration:
1. Adds `fk_lab_orders_visit_id` as `NOT VALID`, then validates online
2. Creates `ux_patients_national_id_notnull` as `CREATE INDEX CONCURRENTLY`

### 5.7 Feature Flag Activation

Enable flags in `.env`:

```dotenv
SNDHS_ENABLE_NATIONAL_ID=true
SNDHS_ENABLE_VISITS=true
```

Restart the backend: `docker compose restart gula-backend`

### 5.8 Verification

```bash
make health-deep
make scenario-test USERS=10 ROUNDS=1
```

The platform's existing scenario test must remain GREEN after each step.

### 5.9 Rollback

**Soft rollback (preferred):** Disable flags only (non-destructive, reversible):

```bash
bash scripts/sndhs_phase1_disable_flags.sh
```

**Hard rollback (schema undo):**

```bash
# Undo step F through step A, one at a time
docker compose exec gula-backend alembic downgrade 20260505_0005
docker compose exec gula-backend alembic downgrade 20260505_0004
docker compose exec gula-backend alembic downgrade 20260505_0003
docker compose exec gula-backend alembic downgrade 20260505_0002
docker compose exec gula-backend alembic downgrade 20260505_0001
docker compose exec gula-backend alembic downgrade 20260503_0001
```

SQL fallback (if Alembic is unavailable):

```bash
docker compose exec -T gula-postgres \
  psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -v ON_ERROR_STOP=1 \
  < scripts/sndhs_phase1_rollback.sql
docker compose exec gula-backend alembic stamp 20260503_0001
```

---

## 6. Financial Engine Phase A Migration

### 6.1 Overview

Financial Engine Phase A is **schema-only** — it creates the data model without activating any runtime behaviour. Routes and services are deferred to Phase B+.

- **Migration file:** `backend/migrations/versions/20260506_0001_financial_engine_phase_a.py`
- **Revises:** `20260505_0006` (head of SNDHS chain)
- **Feature gate:** `ENABLE_FINANCIAL_ENGINE` (default: `false`)
- **Sub-feature gate:** `ENABLE_ADS` (default: `false`)

### 6.2 Tables Created (9 tables)

| Table | Purpose |
|-------|---------|
| `fin_providers` | Billable entity (lab / clinic / doctor / institution) |
| `fin_subscriptions` | Provider plan + status + expiry |
| `fin_transactions` | Pricing-engine ledger (per-test fees, ad spend, refunds) |
| `fin_ads_campaigns` | Sponsored-listing bids and daily caps |
| `fin_ads_clicks` | Raw click stream for CPC accounting + fraud scoring |
| `fin_ads_conversions` | Attributed orders for CPA accounting |
| `fin_fraud_logs` | Provider-level integrity flags |
| `fin_market_benchmarks` | Per-test-type market reference (price + TAT) |
| `fin_clinical_behavior` | Doctor-level over-testing / deviation profile |

### 6.3 Migration Safety Properties

- All columns are nullable (except primary keys)
- No foreign-key constraints (added in a later phase after backfill)
- No long locks: every table is brand-new and empty
- Every operation is idempotent (guarded by `_has_table` / `_index_exists`)
- Downgrade drops the nine tables in reverse dependency-free order

### 6.4 Activation

No activation needed for Phase A. The tables sit empty until the engine is turned on:

```dotenv
ENABLE_FINANCIAL_ENGINE=false   # Keep OFF until Phase B+ code is shipped
ENABLE_ADS=false                # Keep OFF until Phase B+
```

### 6.5 Rollback

```bash
docker compose run --rm gula-backend alembic downgrade 20260505_0006
```

---

## 7. Deployment Migration

### 7.1 Docker Compose Update

When upgrading between releases, the Docker Compose configuration may change:

```bash
# Pull latest docker-compose.yml changes
git pull origin main

# Rebuild images with new Dockerfile/requirements
docker compose up -d --build

# Or use Makefile target
make restart
```

### 7.2 Environment Variable Changes

New env vars are added with each release. Always update `.env` from `.env.example`:

```bash
# Update env template
cp .env.example .env

# Regenerate secrets if needed (back up old .env first)
make secrets-gen
```

Key env vars that may need migration:

| Variable | Default | When to Change |
|----------|---------|----------------|
| `SNDHS_ENABLE_VISITS` | `false` | After SNDHS Phase 1 backfill + verification |
| `SNDHS_ENABLE_NATIONAL_ID` | `false` | After SNDHS Phase 1 backfill + verification |
| `ENABLE_FINANCIAL_ENGINE` | `false` | Phase B+ only |
| `ENABLE_ADS` | `false` | Phase B+ only |
| `RUNTIME_MODE` | `api` | `worker` for background task process |
| `FEATURE_BACKGROUND_TASKS` | `true` | Set `false` to disable background workers |

### 7.3 Configuration Migration

- `.env.example` — template (tracked in git)
- `.env` — real secrets (gitignored)
- `.env.production` — production template (no real secrets)

Always back up `.env` before modifying: `cp .env .env.backup`

### 7.4 CI Pipeline Migration Gate

The CI pipeline enforces migration integrity on every push (`.github/workflows/ci.yml`):

1. **syntax-gate** — `py_compile` all files + `flake8 --select=E9,F821`
2. **data-preservation-gate** — Data Preservation Constitution quality gate
3. **migration-check** — `alembic upgrade head` on fresh postgres:17, verify required tables, `downgrade -1 && upgrade head`
4. **lint** — `ruff check` + eslint
5. **test** — `pytest tests/` against postgres + redis
6. **security-scan** — `safety` + `bandit -ll -ii`
7. **build-and-push** — matrix of 8 images to GHCR, Trivy scan

Locally: `make ci` replicates syntax-gate + lint + docker build.

---

## 8. Rollback Procedures

### 8.1 Rollback Decision Matrix

| Issue Type | Rollback? | Alternative |
|-----------|-----------|-------------|
| Code error (API returns 500) | YES | Hotfix if quick |
| Migration error | YES | Fix forward if possible |
| Configuration error | YES | Fix config, restart |
| Performance regression | YES | Scale up, then fix |
| Security vulnerability | YES | Emergency hotfix |
| Data inconsistency | NO | Data repair procedure |
| Partial functionality | Maybe | Feature flag disable |

**Never roll back a database migration that removes columns or data. Always prefer a "fix forward" approach for data-affecting changes.**

### 8.2 Application Rollback

```bash
# Check current image
docker compose images gula-backend

# Roll back to previous tag
docker compose up -d --no-deps --force-recreate gula-backend=<previous-tag>

# Verify
curl -f http://localhost:8080/health/ready
```

### 8.3 Database Rollback

```bash
# Check current migration
docker compose run --rm gula-backend alembic current

# Rollback one migration
docker compose run --rm gula-backend alembic downgrade -1

# Rollback to specific revision
docker compose run --rm gula-backend alembic downgrade <revision_id>

# Rollback all the way
docker compose run --rm gula-backend alembic downgrade base
```

### 8.4 Full Recovery from Backup

```bash
# Step 1: Stop all services
docker compose down

# Step 2: Restore .env
cp .env.backup .env

# Step 3: Restore database
gunzip -c ./backups/gula_<timestamp>.sql.gz | docker compose exec -T postgres psql -U gula

# Step 4: Start services with previous image tag
GULA_IMAGE_TAG=<previous-tag> docker compose up -d

# Step 5: Verify
make health && make health-deep
```

### 8.5 Emergency Kill Switch

```bash
make kill-switch-on    # DigitalOcean-level traffic block
make kill-switch-off
```

---

## 9. Backward Compatibility

### 9.1 API Backward Compatibility

- All API changes are **additive only** — existing endpoints never change their request/response shape
- New fields in responses have sensible defaults for old clients
- Endpoint deprecation follows a **two-release notice** period
- The `X-API-Version` header enables versioned behaviour for breaking changes

### 9.2 Schema Backward Compatibility

- **Dual-read rule:** Any code reading `national_id` or `sndhs_health_id` must handle `None`
- New columns always nullable or with `server_default`
- Old code runs against new schema without errors (migrations-first deploy pattern)
- Feature flags gate new code paths — old code paths remain unchanged

### 9.3 Deprecation Policy

1. Mark as deprecated in documentation and release notes
2. Keep deprecated feature active for **2 minor releases** (or 90 days)
3. Log warnings when deprecated endpoints are called
4. Remove after the deprecation period with a MAJOR version bump

### 9.4 Breaking Change Notification

Breaking changes are communicated via:
- **CHANGELOG.md** — documented under "Breaking Changes" section
- **Release notes** — published with every release tag
- **GitHub Releases** — detailed migration instructions included

### 9.5 Post-Deployment Verification Checklist

After every migration:

- [ ] `curl -f http://localhost:8080/health` returns 200
- [ ] `curl -f http://localhost:8080/health/ready` returns 200
- [ ] `curl -f http://localhost:8080/health/deep` returns grade GREEN
- [ ] `docker compose run --rm gula-backend alembic current` matches expected revision
- [ ] No CRITICAL or ERROR logs in last 5 minutes
- [ ] All required tables exist (`labs`, `lab_users`, `patients`, `lab_orders`, `lab_results`, `outbox_events`, `audit_logs`)
- [ ] Authentication endpoints respond correctly
- [ ] Tenant isolation verified

---

## 10. Related Documents

| Document | Path | Purpose |
|----------|------|---------|
| Deployment Guide | `docs/production/DEPLOYMENT_GUIDE.md` | Full deployment procedures |
| Production Guide | `docs/production/PRODUCTION_GUIDE.md` | Production operations, scaling, HA |
| SNDHS Phase 1 Runbook | `docs/sndhs/phase1/RUNBOOK.md` | Detailed SNDHS migration steps |
| Disaster Recovery Guide | `docs/production/DISASTER_RECOVERY_GUIDE.md` | DR procedures and runbooks |
| CLAUDE.md | `CLAUDE.md` | Migration policy, development workflow |
| CHANGELOG.md | `CHANGELOG.md` | Release history and breaking changes |
| MASTER SYSTEM ATLAS | `MASTER_SYSTEM_ATLAS.md` | Comprehensive system inventory |
| ADR-002 Monolith-First | `docs/adr/ADR-002-monolith-first.md` | Architecture decision for monolith approach |
| ADR-010 SNDHS | `docs/adr/ADR-010-SNDHS.md` | SNDHS integration architecture decision |
| SNDHS Architecture | `docs/sndhs/` | 22-file SNDHS architecture & deployment spec |

### ADRs Related to Migration

| ADR | Subject |
|-----|---------|
| ADR-002 | Monolith-first deployment strategy |
| ADR-005 | PostgreSQL + Redis stack |
| ADR-009 | Self-healing infrastructure |
| ADR-010 | SNDHS government integration |
| ADR-015 | Disaster recovery |
| ADR-024 | Platform constitution |
