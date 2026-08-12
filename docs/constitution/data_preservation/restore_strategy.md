# Restore Strategy

**Part of the GULA Data Preservation Constitution (Rule 7, 8, 9)**
**Version:** 1.0.0
**Last Updated:** 2026-07-22

---

## 1. OBJECTIVES

- **RTO (Recovery Time Objective):** ≤ 4 hours for full restore
- **RPO (Recovery Point Objective):** ≤ 1 hour (backup schedule), ≤ 5s (WAL streaming)
- **Data Integrity:** 100% — restored data must pass all validation checks
- **Testing:** Full restore test executed at least monthly

---

## 2. RESTORE SCENARIOS

| Scenario | Method | Expected RTO | Data Loss |
|----------|--------|-------------|-----------|
| Single table corrupted | `pg_restore -t <table>` from latest backup | 15 min | < 1 hour |
| Accidental data change | Point-in-time recovery to before change | 30 min | < 5s |
| Schema migration failure | Rollback via `alembic downgrade` | 10 min | None |
| Full database loss | `pg_restore` from latest backup + WAL replay | 2 hours | < 1 hour |
| Server failure | Promote replica or restore to new server | 1 hour | < 5s |
| Region failure | Activate DR region | 15 min (manual) | < 5s |
| Disaster (complete loss) | Restore from off-site backup | 4 hours | < 1 hour |

---

## 3. RESTORE PROCEDURES

### 3.1 Single Table Restore

```bash
# Identify the backup containing the table
ls -la /backups/daily/

# Restore single table
pg_restore -U postgres -d labdb -t patients \
  /backups/daily/gula_20260722_020000.dump

# Verify row count
psql -U postgres -d labdb -c "SELECT COUNT(*) FROM patients"

# Verify FK integrity
psql -U postgres -d labdb -c "
  SELECT conname FROM pg_constraint
  WHERE contype = 'f' AND NOT convalidated
"
```

### 3.2 Point-in-Time Recovery

```bash
# Requirements:
# - Base backup
# - All WAL archives from base backup time to target time
# - postgresql.conf with restore_command

# 1. Restore base backup
pg_restore -U postgres -d labdb \
  /backups/daily/gula_$(date +%Y%m%d)_020000.dump

# 2. Create recovery.conf (PG 16: recovery.signal)
touch /var/lib/postgresql/data/recovery.signal

# 3. Configure restore_command in postgresql.conf
# restore_command = 'cp /backups/wal/%f %p'

# 4. Set recovery target time
# recovery_target_time = '2026-07-22 14:30:00 UTC'

# 5. Start PostgreSQL — it will replay WAL to the target time
systemctl start postgresql

# 6. Verify data
psql -U postgres -d labdb -c "SELECT COUNT(*) FROM lab_orders"

# 7. When ready, promote:
psql -U postgres -c "SELECT pg_wal_replay_resume()"
# or: SELECT pg_promote();
```

### 3.3 Full Database Restore

```bash
# 1. Stop application and drop/create database
systemctl stop gula-backend
dropdb -U postgres labdb
createdb -U postgres labdb

# 2. Restore from custom format backup
pg_restore -U postgres -d labdb -j 4 --verbose \
  /backups/daily/gula_$(date +%Y%m%d)_020000.dump 2>&1 | tee /var/log/restore.log

# 3. Verify restore
psql -U postgres -d labdb -c "
  SELECT COUNT(*) AS total_tables FROM information_schema.tables
  WHERE table_schema = 'public'
"

# 4. Run data integrity checks (see Section 5)

# 5. Start application
systemctl start gula-backend

# 6. Verify application health
curl http://localhost:8000/health/deep
```

### 3.4 Migration Rollback

```bash
# If a migration fails, rollback immediately:
cd backend
alembic downgrade -1

# Verify database is in pre-migration state
psql -U postgres -d labdb -c "SELECT COUNT(*) FROM patients"

# If downgrade fails, restore from pre-migration backup:
pg_restore -U postgres -d labdb \
  /backups/pre_migration_<revision_id>.dump
```

---

## 4. RESTORE VALIDATION

After every restore, validate:

```sql
-- 4.1 Row count validation
SELECT 'patients' AS tbl, COUNT(*) FROM patients
UNION ALL
SELECT 'lab_orders', COUNT(*) FROM lab_orders
UNION ALL
SELECT 'lab_results', COUNT(*) FROM lab_results
UNION ALL
SELECT 'samples', COUNT(*) FROM samples
UNION ALL
SELECT 'audit_logs', COUNT(*) FROM audit_logs;

-- 4.2 FK integrity
SELECT conname, convalidated
FROM pg_constraint
WHERE contype = 'f' AND NOT convalidated;

-- 4.3 Check for orphaned records
SELECT COUNT(*) AS orphaned_lab_results
FROM lab_results r
LEFT JOIN lab_orders o ON r.order_id = o.id
WHERE o.id IS NULL;

SELECT COUNT(*) AS orphaned_samples
FROM samples s
LEFT JOIN lab_orders o ON s.order_id = o.id
WHERE o.id IS NULL;

-- 4.4 Index validation
SELECT tablename, indexname, indexdef
FROM pg_indexes
WHERE tablename IN ('patients', 'lab_orders', 'lab_results', 'audit_logs')
ORDER BY tablename, indexname;

-- 4.5 Sequence consistency
SELECT sequencename, last_value
FROM pg_sequences
ORDER BY sequencename;
```

---

## 5. AUTOMATED RESTORE TESTING

Monthly automated restore test (see `scripts/restore-test.sh`):

```bash
#!/bin/bash
# Monthly restore test procedure

# 1. Provision test database server
docker run -d --name gula_restore_test postgres:16-alpine

# 2. Download latest daily backup
LATEST=$(ls -t /backups/daily/*.dump | head -1)

# 3. Restore to test server
pg_restore -h testhost -U postgres -d labdb -j 4 "$LATEST"

# 4. Run validation queries
psql -h testhost -U postgres -d labdb -c "
  SELECT 'ROW COUNT' AS check_name, COUNT(*) AS result FROM patients
"
psql -h testhost -U postgres -d labdb -c "
  SELECT 'FK INTEGRITY' AS check_name,
    COUNT(*) AS failed_constraints
  FROM pg_constraint
  WHERE contype = 'f' AND NOT convalidated
"

# 5. Run alembic migrations on restored data
cd backend && alembic upgrade head

# 6. Run application smoke tests
curl -f http://testhost:8000/health/ready || exit 1

# 7. Report results
echo "Restore test completed: $(date)"
echo "Backup: $LATEST"
```

---

## 6. RESTORE FAILURE CONTINGENCY

| Failure | Primary Action | Fallback |
|---------|---------------|----------|
| Backup file corrupted | Try previous backup | Use WAL archive for PITR |
| Restore fails mid-way | Drop and retry with single thread | Use directory format backup |
| WAL archive gap | PITR to last available WAL | Accept data loss up to gap |
| No valid backup | Activate DR replica | Rebuild from application logs |
| Hardware failure | Restore to different server | Use DR region |

---

## 7. REFERENCES

- `docs/constitution/data_preservation/backup_strategy.md` — Backup procedures
- `docs/constitution/data_preservation/disaster_recovery_guide.md` — DR runbook
- `scripts/backup.sh` — Backup automation
- `scripts/backup-verification.sh` — Backup verification
- `scripts/restore-test.sh` — Restore test automation
- `scripts/dr_recovery.sh` — DR recovery script
- `scripts/pg_failover.sh` — PostgreSQL failover
- `docs/adr/ADR-015-disaster-recovery.md` — DR Architecture Decision Record
