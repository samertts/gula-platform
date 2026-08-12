# Runbook: Database Down

**Severity:** SEV1
**Response Time:** <15 minutes
**Last Updated:** 2026-07-15

---

## Symptoms

- `/health` returns 503 (backend running, DB not responding)
- `/health/deep` shows grade YELLOW or RED, database component RED
- Circuit breaker opens for database (`DegradedModeMiddleware` active)
- `pg_isready` returns failure
- Backend logs: "DB connection failed" or "could not connect to server"
- Users see 503 errors on write operations (reads may still work via replica)
- Monitoring alert: `PostgresDown` or `DBConnectionFailed`

## Quick Checks

```bash
# 1. Check database container
docker compose ps postgres

# 2. Check PostgreSQL is accepting connections
docker compose exec postgres pg_isready -U gula

# 3. Check Patroni cluster status
docker compose exec postgres patronictl list

# 4. Check logs
docker compose logs --tail=100 postgres | grep -i "error\|fatal\|panic\|shutdown"

# 5. Check disk space
df -h /var/lib/postgresql/data
```

## Possible Causes & Fixes

### Cause 1: Disk Full

**Symptoms:** PostgreSQL stops with "No space left on device", write operations fail

**Check:**
```bash
df -h
du -sh /var/lib/postgresql/data/
du -sh /var/lib/postgresql/data/pg_wal/
```

**Fix:**
```bash
# 1. Remove old WAL files (if archive is configured)
docker compose exec postgres psql -U gula -c "SELECT pg_switch_wal();"
docker compose exec postgres psql -U gula -c "SELECT pg_replication_slot_advance('replication_slot', pg_current_wal_lsn());"

# 2. Force WAL cleanup
docker compose exec postgres psql -U gula -c "CHECKPOINT;"

# 3. Truncate if needed (emergency)
docker compose exec postgres psql -U gula -c "SELECT pg_drop_replication_slot('replication_slot');"

# 4. Free up space (find and remove old log files)
find /var/lib/postgresql/data -name "*.log" -mtime +7 -delete

# 5. Restart PostgreSQL
docker compose restart postgres

# 6. Set up disk alert at 80% to prevent recurrence
```

### Cause 2: Out of Memory

**Symptoms:** PostgreSQL OOM killed, kernel logs show OOM killer

**Check:**
```bash
dmesg | grep -i "oom\|killed\|postgres"
docker inspect postgres --format '{{.State.ExitCode}}'
```

**Fix:**
```yaml
# Increase memory limit in docker-compose.yml
services:
  postgres:
    deploy:
      resources:
        limits:
          memory: 4G  # Increase from current
    shm_size: '2gb'  # Increase shared memory
```

```bash
# Tune PostgreSQL memory settings
# Adjust in postgresql.conf or via environment
# shared_buffers = 1GB (25% of available RAM)
# effective_cache_size = 3GB

docker compose up -d --no-deps postgres
```

### Cause 3: Configuration Error

**Symptoms:** PostgreSQL fails to start, logs show config errors

**Check:**
```bash
docker compose logs --tail=50 postgres | grep -i "configuration\|config\|failed\|error"
```

**Fix:**
```bash
# Verify PostgreSQL config
docker compose exec postgres psql -U gula -c "SHOW ALL;" | grep -i "max_connections\|shared_buffers\|wal_level"

# Check for syntax errors in config
docker compose exec postgres postgres --check-config

# Restore default config if corrupted
docker compose down postgres
docker compose up -d postgres
```

### Cause 4: Replication Slot / WAL Bottleneck

**Symptoms:** WAL disk fills, replication lag grows, standby cannot catch up

**Check:**
```bash
docker compose exec postgres psql -U gula -c "
SELECT slot_name, slot_type, active, restart_lsn, confirmed_flush_lsn
FROM pg_replication_slots;"

# Check WAL directory size
du -sh /var/lib/postgresql/data/pg_wal/
```

**Fix:**
```bash
# Remove inactive replication slots
docker compose exec postgres psql -U gula -c "
SELECT pg_drop_replication_slot(slot_name)
FROM pg_replication_slots
WHERE NOT active;"

# Restart PostgreSQL to clean WAL
docker compose restart postgres
```

### Cause 5: Corrupted Data / Index

**Symptoms:** PostgreSQL crashes with PANIC, query errors, "relation not valid"

**Check:**
```bash
docker compose logs --tail=100 postgres | grep -i "PANIC\|corrupt\|invalid page\|checksum"
```

**Fix:**
```bash
# 1. Attempt recovery mode
docker compose exec postgres postgres --single -D /var/lib/postgresql/data postgres

# 2. Rebuild corrupted indexes
docker compose exec postgres psql -U gula -c "REINDEX DATABASE gula;"

# 3. If recovery fails, restore from backup
# See Disaster Recovery Guide for PITR procedure

# 4. As last resort, promote replica if available
docker compose exec postgres patronictl failover --master postgres-1 --candidate postgres-2
```

### Cause 6: Connection Pool Exhaustion

**Symptoms:** New connections refused, active queries waiting, high connection count

**Check:**
```bash
docker compose exec postgres psql -U gula -c "
SELECT count(*) as total_connections,
       count(*) FILTER (WHERE state = 'active') as active,
       count(*) FILTER (WHERE state = 'idle') as idle,
       count(*) FILTER (WHERE state = 'idle in transaction') as idle_in_transaction
FROM pg_stat_activity;"
```

**Fix:**
```bash
# 1. Terminate idle connections
docker compose exec postgres psql -U gula -c "
SELECT pg_terminate_backend(pid)
FROM pg_stat_activity
WHERE state = 'idle'
AND pid <> pg_backend_pid();"

# 2. Terminate idle transactions (dangerous)
docker compose exec postgres psql -U gula -c "
SELECT pg_terminate_backend(pid)
FROM pg_stat_activity
WHERE state = 'idle in transaction'
AND age(now(), state_change) > interval '5 minutes'
AND pid <> pg_backend_pid();"

# 3. Increase max_connections
# Update postgresql.conf or docker-compose environment
echo "max_connections=200" >> /var/lib/postgresql/data/postgresql.conf
docker compose restart postgres
```

## Patroni Failover Procedure

If Patroni failover did not happen automatically:

```bash
# 1. Check cluster state
docker compose exec postgres patronictl list

# 2. Check history
docker compose exec postgres patronictl history

# 3. Force failover to specific replica
docker compose exec postgres patronictl failover \
  --master <current-master> \
  --candidate <replica-name> \
  --force

# 4. Verify new master
docker compose exec postgres psql -U gula -c "SELECT pg_is_in_recovery();"
# Should return 'f' (false = not a replica)

# 5. Update backend connection if needed (Patroni handles this automatically)
docker compose up -d --no-deps gula-backend
```

## Resolution Verification

```bash
# 1. Container is running
docker compose ps postgres
# Status should be "Up"

# 2. PostgreSQL is accepting connections
docker compose exec postgres pg_isready -U gula
# Should return "accepting connections"

# 3. Can run queries
docker compose exec postgres psql -U gula -c "SELECT 1;"
# Should return "1 row"

# 4. Patroni cluster is healthy
docker compose exec postgres patronictl list
# All members should show "running" status

# 5. Circuit breaker is closed
curl -s http://localhost:8000/health/deep | jq .circuit_breakers

# 6. Backend can write
curl -sf http://localhost:8000/test/write
```

## Escalation

| Time | Action |
|------|--------|
| 0 min | Begin diagnosis |
| 2 min | If disk full or corruption, escalate to DBA |
| 5 min | If Patroni failover hasn't resolved, escalate |
| 10 min | Page Engineering Lead |
| 15 min | Declare SEV1 incident |

### Escalation Contacts

| Role | Contact |
|------|---------|
| DBA on-call | PagerDuty |
| Engineering Lead | [Phone] |
| CTO | [Phone] |

## Prevention

- [ ] Set disk monitoring alert at 80% and 90%
- [ ] Configure resource limits on PostgreSQL container
- [ ] Regular VACUUM and ANALYZE schedule
- [ ] Monitor replication slot health
- [ ] Configure WAL archive and retention
- [ ] Regular failover drills
- [ ] Connection pool limits configured
- [ ] Query timeout configured (statement_timeout)
