# Runbook: Disk Full

**Severity:** SEV1 (writes fail) / SEV2 (warning)
**Response Time:** <15 minutes
**Last Updated:** 2026-07-15

---

## Symptoms

- PostgreSQL stops responding or crashes: "No space left on device"
- Write operations fail with disk errors
- Backups fail with insufficient space
- `df -h` shows <10% free space
- Monitoring alert: `DiskSpaceLow` or `DiskSpaceCritical`
- Database circuit breaker opens (disk full prevents writes)

## Quick Checks

```bash
# 1. Check disk usage
df -h

# 2. Check container disk usage
docker system df

# 3. Find large files/directories
du -sh /var/lib/* | sort -rh | head -10
du -sh /var/log/* | sort -rh | head -10

# 4. Check Docker overlay size
du -sh /var/lib/docker/overlay2/* | sort -rh | head -10

# 5. Check database size
docker compose exec postgres psql -U gula -c "
SELECT pg_size_pretty(pg_database_size('gula'));"
```

## Possible Causes & Fixes

### Cause 1: WAL Accumulation

**Symptoms:** `/var/lib/postgresql/data/pg_wal/` is very large (>10GB)

**Check:**
```bash
du -sh /var/lib/postgresql/data/pg_wal/
ls -la /var/lib/postgresql/data/pg_wal/ | wc -l
```

**Fix:**
```bash
# 1. Check replication slots (inactive slots prevent WAL cleanup)
docker compose exec postgres psql -U gula -c "
SELECT slot_name, slot_type, active, pg_size_pretty(pg_wal_lsn_diff(pg_current_wal_lsn(), restart_lsn))
FROM pg_replication_slots;"

# 2. Remove inactive replication slots
docker compose exec postgres psql -U gula -c "
SELECT pg_drop_replication_slot(slot_name)
FROM pg_replication_slots
WHERE NOT active;"

# 3. Force WAL checkpoint
docker compose exec postgres psql -U gula -c "CHECKPOINT;"

# 4. If WAL still too large, manual cleanup (CAUTION: data loss risk)
# Only do this if you have a recent backup
docker compose exec postgres psql -U gula -c "SELECT pg_switch_wal();"
# Then remove old WAL files manually if needed
```

### Cause 2: Log Accumulation

**Symptoms:** `/var/log/` or Docker log files are large

**Check:**
```bash
du -sh /var/log/
ls -la /var/log/*.log | sort -k5 -rn | head -10

# Docker logs
docker inspect gula-backend --format '{{.LogPath}}' | xargs du -sh
```

**Fix:**
```bash
# 1. Truncate Docker container logs
truncate -s 0 $(docker inspect gula-backend --format '{{.LogPath}}')
truncate -s 0 $(docker inspect postgres --format '{{.LogPath}}')

# 2. Configure Docker log rotation (permanent fix)
# In docker-compose.yml:
services:
  gula-backend:
    logging:
      driver: json-file
      options:
        max-size: "50m"
        max-file: "5"

# 3. Clean system logs
sudo journalctl --vacuum-size=500M
sudo logrotate -f /etc/logrotate.conf
```

### Cause 3: Database Bloat

**Symptoms:** Database size larger than expected, dead tuples accumulating

**Check:**
```bash
docker compose exec postgres psql -U gula -c "
SELECT relname,
       n_dead_tup,
       n_live_tup,
       round(n_dead_tup::float / NULLIF(n_live_tup + n_dead_tup, 0) * 100, 2) as dead_pct
FROM pg_stat_user_tables
ORDER BY dead_pct DESC LIMIT 20;"
```

**Fix:**
```bash
# 1. VACUUM tables with high dead tuple percentage
docker compose exec postgres psql -U gula -c "VACUUM (VERBOSE, ANALYZE) gula;"

# 2. VACUUM FULL for heavily bloated tables (locks table)
docker compose exec postgres psql -U gula -c "VACUUM FULL VERBOSE patients;"

# 3. REINDEX if needed
docker compose exec postgres psql -U gula -c "REINDEX DATABASE gula;"

# 4. Ensure autovacuum is running properly
docker compose exec postgres psql -U gula -c "SHOW autovacuum;"
```

### Cause 4: Docker Overlay / Unused Images

**Symptoms:** Docker system df shows large images, containers, or build cache

**Check:**
```bash
docker system df
docker image ls
docker container ls -a
docker volume ls
```

**Fix:**
```bash
# 1. Remove unused containers
docker container prune -f

# 2. Remove unused images
docker image prune -af

# 3. Remove unused volumes
docker volume prune -f

# 4. Remove unused build cache
docker builder prune -af

# 5. Full cleanup
docker system prune -af --volumes
```

### Cause 5: Backup Storage Full

**Symptoms:** Backup directory is full, recent backups fail

**Check:**
```bash
du -sh /backups/*
```

**Fix:**
```bash
# 1. Remove old backups (retain last 7 daily)
find /backups/daily -name "*.sql.gz" -mtime +7 -delete

# 2. Remove old weekly backups (retain last 4 weeks)
find /backups/weekly -name "*.sql.gz" -mtime +28 -delete

# 3. Compress old backup logs
find /backups -name "*.log" -mtime +3 -exec gzip {} \;

# 4. Move old backups to cold storage
aws s3 mv /backups/monthly/ s3://gula-backups-archive/monthly/ --recursive
```

### Cause 6: Temporary Data

**Symptoms:** `/tmp` or temp directories are large

**Check:**
```bash
du -sh /tmp/*
du -sh /var/tmp/*
```

**Fix:**
```bash
# Clean temporary files
find /tmp -type f -atime +1 -delete
find /var/tmp -type f -atime +1 -delete

# Clean PostgreSQL temp files
docker compose exec postgres psql -U gula -c "SELECT pg_temp_cleanup();"
```

## Resolution Verification

```bash
# 1. Check free space
df -h
# Free space should be >20%

# 2. Verify PostgreSQL is running
docker compose exec postgres pg_isready -U gula

# 3. Verify writes work
curl -sf http://localhost:8000/test/write

# 4. Check circuit breaker is closed
curl -s http://localhost:8000/health/deep | jq .circuit_breakers

# 5. Run backup (to verify enough space)
./scripts/backup.sh --quick
```

## Escalation

| Time | Action |
|------|--------|
| 0 min | Begin cleanup |
| 10 min | If cannot free >20% quickly, escalate |
| 15 min | If PostgreSQL is down, page DBA and declare SEV1 |

## Prevention

- [ ] Set disk monitoring alerts at 70%, 80%, 90%
- [ ] Configure log rotation (Docker, system, application)
- [ ] Set WAL archive and retention limits
- [ ] Schedule weekly VACUUM maintenance
- [ ] Set Docker system prune cron job: `0 3 * * 0 docker system prune -af`
- [ ] Monitor database growth trends monthly
- [ ] Configure backup retention limits
