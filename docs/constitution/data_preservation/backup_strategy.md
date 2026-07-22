# Backup Strategy

**Part of the GULA Data Preservation Constitution (Rule 7)**
**Version:** 1.0.0
**Last Updated:** 2026-07-22

---

## 1. OBJECTIVES

- **RPO (Recovery Point Objective):** ≤ 1 hour — maximum acceptable data loss
- **RTO (Recovery Time Objective):** ≤ 4 hours — time to restore full service
- **Backup Integrity:** 100% — every backup must be verifiably restorable
- **Retention:** Daily backups for 30 days, weekly for 12 months, monthly for 7 years

---

## 2. BACKUP SCHEDULE

| Frequency | Type | Target | Retention | Timing |
|-----------|------|--------|-----------|--------|
| Continuous | WAL archiving | PostgreSQL WAL | 7 days | Real-time |
| Hourly | pg_dump (custom format) | Full database | 24 hours | :00 each hour |
| Daily | pg_dump (custom format) | Full database | 30 days | 02:00 UTC |
| Weekly | pg_dump (custom + directory) | Full database | 12 months | Sunday 02:00 UTC |
| Monthly | pg_dump (directory + compress) | Full database | 7 years | 1st of month 02:00 UTC |
| Pre-migration | pg_dump (custom format) | Full database | Until migration confirmed stable | Before every migration |

---

## 3. BACKUP TYPES

### 3.1 Logical Backup (pg_dump)

```bash
# Custom format (compressed, parallel)
pg_dump -U postgres -Fc -j 4 -f /backups/daily/gula_$(date +%Y%m%d_%H%M%S).dump labdb

# Directory format (parallel restore)
pg_dump -U postgres -Fd -j 4 -f /backups/daily/gula_dir_$(date +%Y%m%d_%H%M%S) labdb
```

### 3.2 Physical Backup (pg_basebackup)

```bash
# Used for point-in-time recovery
pg_basebackup -U replicator -D /backups/physical/$(date +%Y%m%d_%H%M%S) -X stream -P
```

### 3.3 WAL Archiving

```postgresql
-- postgresql.conf
archive_mode = on
archive_command = 'cp %p /backups/wal/%f'
archive_timeout = 60  -- force archive every 60s
```

### 3.4 Filesystem Backup (Redis, Config)

| Component | Method | Frequency |
|-----------|--------|-----------|
| Redis RDB | `SAVE` or `BGSAVE` + copy | Hourly |
| Redis AOF | File copy | Continuous |
| Application config | `tar -czf` | Daily |
| Uploaded files | `rsync` to backup storage | Hourly |
| Edge device config | API snapshot | Daily |

---

## 4. BACKUP VERIFICATION

Every backup MUST be verified:

```bash
# Step 1: Check file exists and has size > 0
if [ -f "$BACKUP_FILE" ] && [ $(stat -c%s "$BACKUP_FILE") -gt 1000000 ]; then
    echo "Backup file exists and has valid size"
fi

# Step 2: SHA-256 checksum
sha256sum "$BACKUP_FILE" > "$BACKUP_FILE.sha256"

# Step 3: Test restore to temp database
createdb gula_backup_test
pg_restore -d gula_backup_test "$BACKUP_FILE" 2>&1 || echo "Restore test failed"

# Step 4: Row count validation
psql -d gula_backup_test -c "SELECT COUNT(*) FROM patients"
psql -d gula_backup_test -c "SELECT COUNT(*) FROM lab_orders"
psql -d gula_backup_test -c "SELECT COUNT(*) FROM lab_results"

# Step 5: Integrity check
psql -d gula_backup_test -c "SELECT count(*) FROM (
    SELECT conname FROM pg_constraint WHERE contype = 'f' AND NOT convalidated
) fk_issues"

# Step 6: Cleanup
dropdb gula_backup_test
```

---

## 5. BACKUP STORAGE

| Location | Format | Encryption | Access |
|----------|--------|------------|--------|
| Local disk (`/backups/daily/`) | Custom dump + WAL | At rest | Root only |
| Network mount (`/mnt/backup/`) | Custom dump | AES-256 | Backup user |
| Off-site (S3-compatible) | Encrypted dump | AES-256 + TLS | Restricted IAM |
| Tape (monthly archive) | Directory dump | AES-256 | Physical security |

### Retention Policy

```bash
# Cleanup daily backups older than 30 days
find /backups/daily -name "*.dump" -mtime +30 -delete

# Cleanup hourly backups older than 24 hours
find /backups/hourly -name "*.dump" -mmin +1440 -delete

# Monthly backups retained for 7 years (manual archival)
```

### Off-Site Requirements

- At least 2 copies of every backup
- At least 1 copy off-site (different physical location)
- Encrypted at rest and in transit
- Test restore from off-site copy quarterly

---

## 6. BACKUP MONITORING

| Metric | Alert Threshold | Action |
|--------|----------------|--------|
| Backup age | > 65 minutes (hourly) | PagerDuty critical alert |
| Backup size | < 50% of expected | Investigate data loss |
| Restore test | Failure | Immediate investigation |
| Disk space | < 20% free | Add storage or prune |
| WAL archive lag | > 10 minutes | Check archive_command |

---

## 7. PRE-MIGRATION BACKUP PROCEDURE

Before every schema migration (automated by `scripts/backup.sh`):

```
1. Trigger full pg_dump (custom format)
2. Compute and store SHA-256 checksum
3. Restore to temporary database
4. Validate row counts on 5 core tables
5. Record rollback point in migration log
6. ONLY THEN proceed with migration
7. If migration fails, restore from backup immediately
```

See `scripts/backup.sh` and `scripts/backup-verification.sh` for implementation.

---

## 8. EMERGENCY BACKUP

If the primary backup system fails:

1. **WAL archiving continues** — lowest overhead, continuous protection
2. **Replica promotion** — promote streaming replica to new primary
3. **pg_dump from replica** — run backup against read replica
4. **Emergency pg_dump** with reduced concurrency (`-j 1`)

---

## 9. REFERENCES

- `docs/constitution/data_preservation/restore_strategy.md` — Restore procedures
- `docs/constitution/data_preservation/disaster_recovery_guide.md` — DR runbook
- `scripts/backup.sh` — Automated backup script
- `scripts/backup-verification.sh` — Backup verification script
- ADR-015: Disaster Recovery Strategy
- ADR-005: PostgreSQL Redis Stack
