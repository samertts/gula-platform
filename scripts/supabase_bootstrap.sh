#!/usr/bin/env bash
# =============================================================================
# GULA Platform — Supabase one-shot bootstrap
# =============================================================================
# Usage:
#   DATABASE_URL='postgresql://postgres.xxx:pwd@aws-0-eu-central-1.pooler.supabase.com:6543/postgres?sslmode=require' \
#     ./scripts/supabase_bootstrap.sh
#
# What it does:
#   1. Verifies psql + alembic are available
#   2. Pings the Supabase database
#   3. Runs supabase/setup.sql (extensions, privileges, defaults — idempotent)
#   4. Runs `alembic upgrade head` to materialise the application schema
#   5. Verifies the required tables now exist
# =============================================================================
set -euo pipefail

GREEN='\033[1;32m'; RED='\033[1;31m'; CYAN='\033[1;36m'; YELLOW='\033[1;33m'; NC='\033[0m'
log()  { printf "${CYAN}[supabase]${NC} %s\n" "$*"; }
ok()   { printf "${GREEN}[\xe2\x9c\x93]${NC} %s\n" "$*"; }
warn() { printf "${YELLOW}[!]${NC} %s\n" "$*"; }
err()  { printf "${RED}[\xe2\x9c\x97]${NC} %s\n" "$*" >&2; exit 1; }

# ── Pre-flight ──────────────────────────────────────────────────────────────
[ -n "${DATABASE_URL:-}" ] || err "DATABASE_URL must be set (Supabase pooled URI)."
command -v psql    >/dev/null 2>&1 || err "psql not found. apt-get install postgresql-client"
command -v alembic >/dev/null 2>&1 || err "alembic not found. pip install -r backend/requirements.txt"

case "$DATABASE_URL" in
  *sslmode=require*) ;;
  *) warn "DATABASE_URL is missing 'sslmode=require' — Supabase requires TLS." ;;
esac

case "$DATABASE_URL" in
  *.pooler.supabase.com:6543*) ok "Using pooled connection (port 6543) — recommended." ;;
  *.supabase.com:5432*)        warn "Using direct connection (port 5432). For >1 worker prefer the pooler (6543)." ;;
esac

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"
SETUP_SQL="$ROOT_DIR/supabase/setup.sql"
[ -f "$SETUP_SQL" ] || err "Missing $SETUP_SQL"

# ── 1. Ping the database ────────────────────────────────────────────────────
log "Pinging Supabase..."
psql "$DATABASE_URL" -c "SELECT 'GULA bootstrap ' || now() AS msg;" >/dev/null \
  || err "Could not connect. Check DATABASE_URL, network, and that the project is unpaused."
ok "Database reachable."

# ── 2. Run idempotent bootstrap SQL ─────────────────────────────────────────
log "Applying supabase/setup.sql (extensions, privileges, defaults)..."
psql -v ON_ERROR_STOP=1 "$DATABASE_URL" -f "$SETUP_SQL"
ok "Bootstrap SQL applied."

# ── 3. Run Alembic migrations ───────────────────────────────────────────────
log "Running alembic upgrade head..."
cd "$ROOT_DIR/backend"
alembic upgrade head
ok "Alembic migrations applied."

# ── 4. Verify required tables ───────────────────────────────────────────────
log "Verifying required tables..."
REQUIRED=(labs lab_users patients lab_orders lab_results outbox_events audit_logs alembic_version)
MISSING=()
for t in "${REQUIRED[@]}"; do
    EXISTS=$(psql -tAX "$DATABASE_URL" -c "SELECT to_regclass('public.${t}') IS NOT NULL;")
    if [ "$EXISTS" != "t" ]; then
        MISSING+=("$t")
    fi
done

if [ ${#MISSING[@]} -gt 0 ]; then
    err "Missing tables after migration: ${MISSING[*]}"
fi
ok "All ${#REQUIRED[@]} required tables present."

# ── 5. Show summary ─────────────────────────────────────────────────────────
log "Schema summary:"
psql "$DATABASE_URL" -c "
SELECT 'tables'      AS object_type, COUNT(*) FROM information_schema.tables
WHERE table_schema='public'
UNION ALL SELECT 'indexes', COUNT(*) FROM pg_indexes WHERE schemaname='public'
UNION ALL SELECT 'extensions', COUNT(*) FROM pg_extension
WHERE extname IN ('pgcrypto','pg_trgm','pg_stat_statements','btree_gin');"

ok "Supabase is ready for GULA Platform. Set DATABASE_URL on Render / DO."
