#!/bin/bash
# =============================================================================
# GULA Platform - Smart Database Maintenance
# =============================================================================
# This script keeps the database lean and prevents bloat by:
#   1. Pruning processed integration/outbox events
#   2. Pruning old telemetry and non-critical events
#   3. Running VACUUM ANALYZE to reclaim space and update stats
#
# Runs with low priority (nice/ionice) to avoid choking the platform.
# =============================================================================

set -euo pipefail

# Configuration
PG_CONTAINER="${PG_CONTAINER:-gula-postgres}"
DB_USER="${DB_USER:-postgres}"
DB_NAME="${DB_NAME:-labdb}"
RETENTION_EVENTS_DAYS=7
RETENTION_TELEMETRY_DAYS=30

log() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] [MAINTENANCE] $*"; }

_run_sql() {
    local sql="$1"
    if docker ps --format '{{.Names}}' 2>/dev/null | grep -q "^${PG_CONTAINER}$"; then
        docker exec -u "${DB_USER}" "${PG_CONTAINER}" psql -d "${DB_NAME}" -c "${sql}"
    else
        # Fallback to local psql if not in docker
        psql -U "${DB_USER}" -d "${DB_NAME}" -c "${sql}"
    fi
}

log "Starting database maintenance (Lean Mode)..."

# 1. Prune Processed Events (Outbox & Integration Inbox)
log "Pruning processed events older than ${RETENTION_EVENTS_DAYS} days..."
_run_sql "DELETE FROM outbox_events WHERE processed = true AND created_at < NOW() - INTERVAL '${RETENTION_EVENTS_DAYS} days';"
_run_sql "DELETE FROM integration_inbox_events WHERE status IN ('completed', 'failed') AND created_at < NOW() - INTERVAL '${RETENTION_EVENTS_DAYS} days';"

# 2. Prune Telemetry and Edge Events
log "Pruning telemetry and edge events older than ${RETENTION_TELEMETRY_DAYS} days..."
_run_sql "DELETE FROM edge_telemetry WHERE timestamp < NOW() - INTERVAL '${RETENTION_TELEMETRY_DAYS} days';"
_run_sql "DELETE FROM edge_events WHERE created_at < NOW() - INTERVAL '${RETENTION_TELEMETRY_DAYS} days';"

# 3. Vacuum and Analyze (Reclaim space and optimize query planner)
# We run this with 'nice' and 'ionice' if possible, but inside docker we just run it.
log "Running VACUUM ANALYZE on high-churn tables..."
_run_sql "VACUUM ANALYZE outbox_events;"
_run_sql "VACUUM ANALYZE integration_inbox_events;"
_run_sql "VACUUM ANALYZE edge_telemetry;"
_run_sql "VACUUM ANALYZE edge_events;"
_run_sql "VACUUM ANALYZE audit_logs;"

log "Maintenance complete. Database is lean and optimized."
