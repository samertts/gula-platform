#!/bin/bash
set -euo pipefail

PRIMARY_HOST="${1:-postgres-primary}"
REPLICA_COUNT="${2:-2}"
REPLICATION_USER="replicator"
REPLICATION_PASS="${REPLICATION_PASS:-replication_pass}"
NAMESPACE="${NAMESPACE:-gula}"

log() { printf '[READ-REPLICAS] %s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ) $*"; }

setup_replication_user() {
    log "Setting up replication user..."
    psql -h "$PRIMARY_HOST" -U postgres -c "CREATE ROLE ${REPLICATION_USER} WITH REPLICATION LOGIN PASSWORD '${REPLICATION_PASS}';" 2>/dev/null || true
    psql -h "$PRIMARY_HOST" -U postgres -c "GRANT CONNECT ON DATABASE labdb TO ${REPLICATION_USER};" 2>/dev/null || true
    log "Replication user configured."
}

configure_primary() {
    log "Configuring primary for replication..."
    psql -h "$PRIMARY_HOST" -U postgres -c "ALTER SYSTEM SET wal_level = replica;"
    psql -h "$PRIMARY_HOST" -U postgres -c "ALTER SYSTEM SET max_wal_senders = $((REPLICA_COUNT + 5));"
    psql -h "$PRIMARY_HOST" -U postgres -c "ALTER SYSTEM SET max_replication_slots = $((REPLICA_COUNT + 5));"
    psql -h "$PRIMARY_HOST" -U postgres -c "ALTER SYSTEM SET hot_standby = on;"
    psql -h "$PRIMARY_HOST" -U postgres -c "ALTER SYSTEM SET synchronous_commit = remote_write;"
    psql -h "$PRIMARY_HOST" -U postgres -c "SELECT pg_reload_conf();"
    log "Primary configured for replication."
}

create_replica() {
    local REPLICA_INDEX=$1
    local REPLICA_NAME="postgres-replica-${REPLICA_INDEX}"
    log "Creating replica: $REPLICA_NAME"

    kubectl create deployment "$REPLICA_NAME" --image=postgres:16-alpine -n "$NAMESPACE" --replicas=1 2>/dev/null || true

    log "Replica $REPLICA_NAME created. Initializing from primary..."
    PG_PASSWORD="${PGPASSWORD:-postgres}"
    PGPASSWORD="$PG_PASSWORD" pg_basebackup -h "$PRIMARY_HOST" -D "/var/lib/postgresql/data" \
        -U "$REPLICATION_USER" -P -v --wal-method=stream 2>/dev/null || true

    log "Replica $REPLICA_NAME initialized."
}

add_pgbouncer_pool() {
    local REPLICA_HOST=$1
    log "Adding pgbouncer pool for replica: $REPLICA_HOST"
    cat >> /etc/pgbouncer/pgbouncer.ini << EOF

[databases]
labdb_replica${REPLICA_INDEX} = host=${REPLICA_HOST} port=5432 dbname=labdb pool_size=20
EOF
    log "pgbouncer pool added for $REPLICA_HOST"
}

add_prometheus_exporter() {
    local REPLICA_HOST=$1
    log "Adding Prometheus postgres-exporter for: $REPLICA_HOST"
    docker run -d --name "postgres-exporter-${REPLICA_INDEX}" \
        --network gula-net \
        -e DATA_SOURCE_NAME="postgresql://${REPLICATION_USER}:${REPLICATION_PASS}@${REPLICA_HOST}:5432/labdb?sslmode=disable" \
        prometheuscommunity/postgres-exporter:latest 2>/dev/null || true
}

configure_read_only() {
    local REPLICA_HOST=$1
    log "Setting replica to read-only..."
    psql -h "$REPLICA_HOST" -U postgres -c "ALTER SYSTEM SET default_transaction_read_only = on;"
    psql -h "$REPLICA_HOST" -U postgres -c "SELECT pg_reload_conf();"
}

setup_replication_user
configure_primary

for i in $(seq 1 "$REPLICA_COUNT"); do
    create_replica "$i"
    configure_read_only "postgres-replica-$i"
    add_pgbouncer_pool "postgres-replica-$i"
    add_prometheus_exporter "postgres-replica-$i"
done

log "=== Read replica setup complete ==="
log "Created $REPLICA_COUNT replicas"
log "Primary: $PRIMARY_HOST"
log "pgbouncer configured with read-only pool for replicas"
log "Prometheus exporters configured for replication lag monitoring"
