# SNDHS-lite Phase 1 — Deployment Runbook

> **Owner:** Platform engineering · **Risk:** low · **Downtime:** zero ·
> **Reversible:** yes (every step has a documented rollback).

This phase introduces the visit-centric, national-ID-aware foundations
on top of the running GULA platform. Nothing existing is broken; new
columns are nullable, new tables are additive, constraints land only
after a verified backfill, and the new code paths sit behind two
deployment-wide feature flags that default to `false`.

## 0. Files added in this phase

```
backend/migrations/versions/20260505_0001_sndhs_phase1_extend_patients.py
backend/migrations/versions/20260505_0002_sndhs_phase1_index_national_id.py
backend/migrations/versions/20260505_0003_sndhs_phase1_visits_table.py
backend/migrations/versions/20260505_0004_sndhs_phase1_lab_orders_visit_id.py
backend/migrations/versions/20260505_0005_sndhs_phase1_audit_logs_v2.py
backend/migrations/versions/20260505_0006_sndhs_phase1_constraints.py
backend/app/core/sndhs_flags.py
backend/app/config.py                  # +2 flag readers
scripts/sndhs_phase1_backfill.py       # idempotent batched backfill
scripts/sndhs_phase1_rollback.sql      # belt-and-braces SQL rollback
scripts/sndhs_phase1_disable_flags.sh  # emergency flag flip
```

## 1. Pre-flight (≤ 5 min)

1. `make health-deep` shows GREEN.
2. Backups are current:
   ```bash
   make backup
   ```
3. `git pull` the branch on the host:
   ```bash
   git fetch origin && git checkout claude/sndhs-core-architecture-QzKHF
   ```

## 2. Apply migrations A–E (NON-BLOCKING)

Steps 0001–0005 only add columns/tables/indexes — none of them takes a
long lock. Two of them run `CREATE INDEX CONCURRENTLY` and therefore
each operate outside a transaction (Alembic's
`autocommit_block` handles that).

```bash
docker compose exec gula-backend alembic upgrade 20260505_0005
```

Expected output: five "Running upgrade ... -> ..." lines. No table
locks longer than the standard `ADD COLUMN` metadata lock.

Verify:

```bash
docker compose exec gula-postgres psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "
  SELECT column_name FROM information_schema.columns
  WHERE table_name = 'patients'
    AND column_name IN ('national_id','sndhs_health_id','identity_level','consent_flags');
  SELECT to_regclass('public.visits') AS visits,
         to_regclass('public.sndhs_audit_logs') AS sndhs_audit_logs;
  SELECT column_name FROM information_schema.columns
  WHERE table_name = 'lab_orders' AND column_name = 'visit_id';
"
```

All four patients columns must appear; both `to_regclass` results must
be non-null; `lab_orders.visit_id` must appear.

## 3. Run the backfill

The backfill is **idempotent and concurrent-safe** (it uses
`FOR UPDATE SKIP LOCKED`). Start with a dry run:

```bash
docker compose exec gula-backend python scripts/sndhs_phase1_backfill.py --dry-run
```

Then run for real, in waves if the table is large:

```bash
# Default: 1000 rows per batch, 50 ms sleep. Tune per cluster load.
docker compose exec gula-backend python scripts/sndhs_phase1_backfill.py

# Optional: cap per pass to avoid replication-lag spikes.
docker compose exec gula-backend \
  python scripts/sndhs_phase1_backfill.py --batch-size 500 --max-batches 200 --sleep-ms 100
```

Re-run the script until the final log line is:

```
sndhs_phase1_check OK total_orders=N linked=N visits_created=N elapsed=Ts
```

If it ends with a `WARNING ... unlinked rows`, simply re-run.

Verify zero remaining:

```bash
docker compose exec gula-postgres psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "
  SELECT count(*) AS unlinked FROM lab_orders WHERE visit_id IS NULL;
"
# Expect: 0
```

## 4. Apply step F (constraints)

Only after step 3 reports zero unlinked rows. Step F double-checks the
pre-conditions and aborts loudly otherwise.

```bash
docker compose exec gula-backend alembic upgrade head
```

The migration will:

1. `ALTER TABLE lab_orders ADD CONSTRAINT fk_lab_orders_visit_id ... NOT VALID`
2. `ALTER TABLE lab_orders VALIDATE CONSTRAINT fk_lab_orders_visit_id` (online).
3. `CREATE UNIQUE INDEX CONCURRENTLY ux_patients_national_id_notnull ... WHERE national_id IS NOT NULL` (online).

Verify:

```bash
docker compose exec gula-postgres psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "
  SELECT conname, contype FROM pg_constraint
  WHERE conrelid = 'lab_orders'::regclass AND conname = 'fk_lab_orders_visit_id';
  SELECT indexname FROM pg_indexes
  WHERE tablename = 'patients' AND indexname = 'ux_patients_national_id_notnull';
"
```

## 5. Enable the feature flags (canary)

Edit `.env` (or the deployment env source):

```dotenv
SNDHS_ENABLE_NATIONAL_ID=true
SNDHS_ENABLE_VISITS=true
```

Restart the backend:

```bash
docker compose restart gula-backend
```

Verify:

```bash
curl -fsS http://127.0.0.1:8000/health/status | jq '.sndhs // .'
# (when wired into status output it will show
#  {"visits_enabled":true,"national_id_enabled":true})
```

The canonical reader is `backend/app/core/sndhs_flags.status_snapshot()`.
New endpoints that depend on the flags use the FastAPI dependencies
`require_visits()` / `require_national_id()` and respond `503
SNDHS_FEATURE_DISABLED` when off — old endpoints continue unchanged.

## 6. Smoke-test the new surface

```bash
make health-deep
make scenario-test USERS=10 ROUNDS=1
```

The platform's existing scenario test drives the legacy endpoints and
must remain GREEN after each phase step.

## 7. Rollback

Roll back in REVERSE order. There are two rollback paths.

### 7a. Soft rollback (preferred) — disable flags only

If a regression appears that is isolated to the new flag-gated
behaviour, flip the flags off without touching schema:

```bash
bash scripts/sndhs_phase1_disable_flags.sh
```

This is non-destructive and reversible at any time.

### 7b. Hard rollback — undo schema

Required only if a schema-level issue is discovered. Always run 7a
first.

Option 1 — Alembic (preferred):

```bash
# Drop step F.
docker compose exec gula-backend alembic downgrade 20260505_0005
# Drop step E (sndhs_audit_logs).
docker compose exec gula-backend alembic downgrade 20260505_0004
# Drop step D (lab_orders.visit_id).
docker compose exec gula-backend alembic downgrade 20260505_0003
# Drop step C (visits).
docker compose exec gula-backend alembic downgrade 20260505_0002
# Drop step B (national_id index).
docker compose exec gula-backend alembic downgrade 20260505_0001
# Drop step A (patients columns).
docker compose exec gula-backend alembic downgrade 20260503_0001
```

Option 2 — SQL fallback if Alembic is unavailable:

```bash
docker compose exec -T gula-postgres \
  psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -v ON_ERROR_STOP=1 \
  < scripts/sndhs_phase1_rollback.sql
# Then, if Alembic is still installed, stamp it back to the prior head:
docker compose exec gula-backend alembic stamp 20260503_0001
```

The SQL script:
- never modifies any pre-existing row,
- only drops Phase-1 columns/tables/indexes/constraints,
- handles `CREATE INDEX CONCURRENTLY` cleanup correctly (each
  `DROP INDEX CONCURRENTLY` runs outside a transaction).

## 8. Operational notes

- **Existing endpoints continue to work** while flags are off. The
  legacy `health_id`, `national_id_hash`, and integer `audit_logs.id`
  surfaces are untouched.
- **`sndhs_audit_logs` is append-only** at the database level; do not
  attempt UPDATE/DELETE — the trigger raises `P0001`.
- The backfill creates **one visit per (patient, calendar-day)**.
  This is the simplest legally defensible mapping; later phases can
  refine visit boundaries (e.g. by encounter) without breaking
  consumers (visits stay UUID; orders keep their stable visit_id).
- The feature flags are environment-driven; the in-process override
  helpers (`enable_visits()`, `disable_visits()`, …) are reserved for
  the admin control surface and emit audit events when wired up.

## 9. Hard constraints (verify after Phase 1 lands)

| Constraint | Verification |
|------------|--------------|
| No long table locks | `pg_stat_activity` during step F shows no `AccessExclusiveLock` lasting > 1 s |
| `CREATE INDEX CONCURRENTLY` used | `ix_patients_national_id`, `ix_lab_orders_visit_id`, `ux_patients_national_id_notnull` all built without blocking writers |
| New columns nullable | `information_schema.columns` shows `is_nullable = YES` for all four patients additions |
| Constraints only after backfill | `unlinked = 0` before step F runs (the migration aborts otherwise) |
| Rollback for every step | Each migration's `downgrade()` is documented and exercised in CI on a clean DB |
| Old code keeps working | `make scenario-test` GREEN at every milestone |
