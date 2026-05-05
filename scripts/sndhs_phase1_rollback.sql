-- ============================================================================
-- SNDHS-lite Phase 1 — production-safe rollback (PostgreSQL).
--
-- This script reverses Phase-1 schema additions in dependency order
-- without touching any existing data.
--
-- Use only when a controlled rollback is required. The preferred
-- rollback is `alembic downgrade <prior-revision>`; this script is the
-- belt-and-braces fallback when alembic is unavailable.
--
-- The script is structured as discrete, idempotent blocks. Each block
-- is safe to re-run. NO destructive operations against existing data.
-- The original `audit_logs`, `patients`, and `lab_orders` rows are
-- never modified — only Phase-1 columns / tables are touched.
--
-- Usage:
--     psql "$DATABASE_URL" -v ON_ERROR_STOP=1 -f scripts/sndhs_phase1_rollback.sql
--
-- Recommended ordering:
--   1) flip feature flags off (operator: SNDHS_ENABLE_*=false + restart)
--   2) wait one drain cycle
--   3) run this script
--   4) `alembic stamp <prior-revision>` if the alembic head needs to
--      match the rolled-back state (only if alembic is still present).
-- ============================================================================

\set ON_ERROR_STOP on

BEGIN;

-- ── Step F-rollback: drop FK + partial UNIQUE ───────────────────────────────
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM pg_constraint c
        JOIN   pg_class t ON t.oid = c.conrelid
        WHERE  t.relname = 'lab_orders' AND c.conname = 'fk_lab_orders_visit_id'
    ) THEN
        EXECUTE 'ALTER TABLE lab_orders DROP CONSTRAINT fk_lab_orders_visit_id';
    END IF;
END $$;

COMMIT;

-- DROP INDEX CONCURRENTLY must run outside a transaction.
DROP INDEX CONCURRENTLY IF EXISTS ux_patients_national_id_notnull;

BEGIN;

-- ── Step E-rollback: append-only audit table ────────────────────────────────
DROP TRIGGER IF EXISTS trg_sndhs_audit_logs_no_delete  ON sndhs_audit_logs;
DROP TRIGGER IF EXISTS trg_sndhs_audit_logs_no_update  ON sndhs_audit_logs;
DROP FUNCTION IF EXISTS sndhs_audit_logs_no_mutation();

DROP INDEX IF EXISTS ix_sndhs_audit_logs_created_at;
DROP INDEX IF EXISTS ix_sndhs_audit_logs_purpose;
DROP INDEX IF EXISTS ix_sndhs_audit_logs_action;
DROP INDEX IF EXISTS ix_sndhs_audit_logs_entity;
DROP INDEX IF EXISTS ix_sndhs_audit_logs_user_id;
DROP TABLE IF EXISTS sndhs_audit_logs;

COMMIT;

-- ── Step D-rollback: lab_orders.visit_id ────────────────────────────────────
DROP INDEX CONCURRENTLY IF EXISTS ix_lab_orders_visit_id;

BEGIN;
ALTER TABLE lab_orders DROP COLUMN IF EXISTS visit_id;
COMMIT;

-- ── Step C-rollback: visits table ───────────────────────────────────────────
BEGIN;
DROP INDEX IF EXISTS ix_visits_created_at;
DROP INDEX IF EXISTS ix_visits_status;
DROP INDEX IF EXISTS ix_visits_patient_id;
DROP TABLE IF EXISTS visits;
COMMIT;

-- ── Step B-rollback: patients.national_id index ─────────────────────────────
DROP INDEX CONCURRENTLY IF EXISTS ix_patients_national_id;

-- ── Step A-rollback: patients added columns ─────────────────────────────────
BEGIN;
ALTER TABLE patients DROP COLUMN IF EXISTS consent_flags;
ALTER TABLE patients DROP COLUMN IF EXISTS identity_level;
ALTER TABLE patients DROP COLUMN IF EXISTS sndhs_health_id;
ALTER TABLE patients DROP COLUMN IF EXISTS national_id;
COMMIT;

-- Done. Phase 1 schema additions have been reversed.
