-- =============================================================================
-- GULA PLATFORM - PostgreSQL Initialization Script
-- Runs ONCE on a fresh database (Docker entrypoint-initdb.d).
-- Schema is managed entirely by SQLAlchemy create_all + Alembic migrations.
-- This file: extensions only + session-level performance defaults.
-- =============================================================================

-- ---------------------------------------------------------------------------
-- Extensions
-- ---------------------------------------------------------------------------
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";       -- UUID generation
CREATE EXTENSION IF NOT EXISTS "pg_stat_statements"; -- Query performance tracking
CREATE EXTENSION IF NOT EXISTS "btree_gist";       -- GiST index support
CREATE EXTENSION IF NOT EXISTS "pgcrypto";         -- gen_random_bytes, crypt

-- ---------------------------------------------------------------------------
-- Performance defaults (applied at session level via ALTER SYSTEM).
-- These write to postgresql.auto.conf and are loaded on next restart.
-- The values here target a 1-2 GB RAM server.  For larger servers set
-- DB_SHARED_BUFFERS / DB_WORK_MEM env vars and restart.
-- ---------------------------------------------------------------------------

-- Allow platform user to run pg_stat_statements
GRANT pg_read_all_stats TO postgres;

-- Create application role with limited privileges (principle of least privilege)
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'gula_app') THEN
        CREATE ROLE gula_app LOGIN PASSWORD 'change_me_in_production'
            NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT NOREPLICATION;
    END IF;
END
$$;

-- Grant app role access to labdb (schema permissions set after SQLAlchemy creates tables)
DO $$
BEGIN
    -- Grant connect on the database
    IF EXISTS (SELECT FROM pg_database WHERE datname = current_database()) THEN
        EXECUTE format('GRANT CONNECT ON DATABASE %I TO gula_app', current_database());
    END IF;
END
$$;

-- Grant schema usage (tables are created by SQLAlchemy after this script runs)
GRANT USAGE ON SCHEMA public TO gula_app;
ALTER DEFAULT PRIVILEGES IN SCHEMA public
    GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO gula_app;
ALTER DEFAULT PRIVILEGES IN SCHEMA public
    GRANT USAGE, SELECT, UPDATE ON SEQUENCES TO gula_app;

-- ---------------------------------------------------------------------------
-- pg_stat_statements: track all SQL for performance analysis
-- ---------------------------------------------------------------------------
SELECT pg_stat_statements_reset() WHERE EXISTS (
    SELECT 1 FROM pg_extension WHERE extname = 'pg_stat_statements'
);

-- ---------------------------------------------------------------------------
-- Done. Schema created by: backend/alembic upgrade head
-- ---------------------------------------------------------------------------
