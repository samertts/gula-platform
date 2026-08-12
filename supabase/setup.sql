-- =============================================================================
-- GULA Platform — Supabase one-time bootstrap
-- =============================================================================
-- Run this ONCE in the Supabase SQL editor (Project → SQL → New query)
-- BEFORE the first `alembic upgrade head` runs.
--
-- Idempotent: safe to re-run. Does not touch application tables — those are
-- created and owned by Alembic migrations under backend/migrations/versions/.
-- =============================================================================

-- ── 1. Required extensions ──────────────────────────────────────────────────
CREATE EXTENSION IF NOT EXISTS pgcrypto;          -- gen_random_uuid(), digest()
CREATE EXTENSION IF NOT EXISTS pg_trgm;           -- trigram indexes for search
CREATE EXTENSION IF NOT EXISTS pg_stat_statements; -- query metrics for /health/deep
CREATE EXTENSION IF NOT EXISTS btree_gin;         -- composite indexes on jsonb

-- ── 2. Lock down default privileges ─────────────────────────────────────────
-- Supabase exposes `anon` and `authenticated` roles via PostgREST. We do NOT
-- use PostgREST — all access goes through the FastAPI backend with the
-- application role. Revoke everything by default to prevent accidental
-- data exposure if Supabase Auth is ever enabled later.
REVOKE ALL ON SCHEMA public FROM anon, authenticated;
ALTER DEFAULT PRIVILEGES IN SCHEMA public
    REVOKE ALL ON TABLES FROM anon, authenticated;
ALTER DEFAULT PRIVILEGES IN SCHEMA public
    REVOKE ALL ON SEQUENCES FROM anon, authenticated;
ALTER DEFAULT PRIVILEGES IN SCHEMA public
    REVOKE ALL ON FUNCTIONS FROM anon, authenticated;

-- ── 3. Conservative runtime defaults at the database level ──────────────────
-- Per-session SET statements in app/database.py override these where needed.
ALTER DATABASE postgres SET statement_timeout                  = '30s';
ALTER DATABASE postgres SET idle_in_transaction_session_timeout = '60s';
ALTER DATABASE postgres SET lock_timeout                        = '5s';
ALTER DATABASE postgres SET log_min_duration_statement          = 1000; -- log >1s queries

-- ── 4. Enable row-level audit hooks (no-op until backend creates the tables)
--     The actual audit_logs table + triggers are created by Alembic
--     migration 20250322_0002_perf_indexes_audit_protection.py.
--     This block just confirms the necessary functions are available.
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_proc WHERE proname = 'gen_random_uuid'
    ) THEN
        RAISE EXCEPTION 'pgcrypto extension failed to install';
    END IF;
END $$;

-- ── 5. Optional: dedicated application role (recommended for production) ────
-- The default `postgres` superuser has more privileges than the app needs.
-- Uncomment and edit the password before running, then update DATABASE_URL
-- to use `gula_app` instead of `postgres`.
--
-- DO $$
-- BEGIN
--     IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'gula_app') THEN
--         CREATE ROLE gula_app LOGIN PASSWORD 'CHANGE_ME_STRONG_PASSWORD'
--             NOSUPERUSER NOCREATEROLE NOCREATEDB;
--     END IF;
-- END $$;
--
-- GRANT CONNECT ON DATABASE postgres TO gula_app;
-- GRANT USAGE  ON SCHEMA public TO gula_app;
-- GRANT ALL PRIVILEGES ON ALL TABLES    IN SCHEMA public TO gula_app;
-- GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO gula_app;
-- ALTER DEFAULT PRIVILEGES IN SCHEMA public
--     GRANT ALL ON TABLES    TO gula_app;
-- ALTER DEFAULT PRIVILEGES IN SCHEMA public
--     GRANT ALL ON SEQUENCES TO gula_app;

-- ── 6. Tag the project so we can detect "fresh DB" state from the backend ──
CREATE TABLE IF NOT EXISTS gula_supabase_bootstrap (
    id          INT PRIMARY KEY DEFAULT 1,
    bootstrapped_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    sql_version TEXT NOT NULL DEFAULT '1.0',
    notes       TEXT,
    CONSTRAINT single_row CHECK (id = 1)
);

INSERT INTO gula_supabase_bootstrap (id, sql_version, notes)
VALUES (1, '1.0', 'Initial bootstrap — extensions + privileges + defaults')
ON CONFLICT (id) DO UPDATE
SET bootstrapped_at = NOW(),
    sql_version     = EXCLUDED.sql_version,
    notes           = EXCLUDED.notes;

-- ── 7. Sanity check ─────────────────────────────────────────────────────────
DO $$
DECLARE
    n_ext   INT;
    expected_ext TEXT[] := ARRAY['pgcrypto', 'pg_trgm', 'pg_stat_statements', 'btree_gin'];
    e TEXT;
BEGIN
    FOREACH e IN ARRAY expected_ext LOOP
        SELECT COUNT(*) INTO n_ext FROM pg_extension WHERE extname = e;
        IF n_ext = 0 THEN
            RAISE EXCEPTION 'Missing required extension: %', e;
        END IF;
    END LOOP;
    RAISE NOTICE '✓ GULA Supabase bootstrap complete — % extensions verified',
                 array_length(expected_ext, 1);
END $$;
