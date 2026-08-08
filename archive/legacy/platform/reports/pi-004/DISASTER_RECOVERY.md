# PI-004 — Disaster Recovery Guide

## National Platform — Business Continuity & Disaster Recovery

**Version:** 2.1.0
**Date:** July 2026

---

## 1. Recovery Objectives

| Metric | Target | Measurement |
|--------|--------|-------------|
| **RPO** (Recovery Point Objective) | 1 hour | Maximum data loss in an outage |
| **RTO** (Recovery Time Objective) | 4 hours | Time to restore full service |
| **RTO (Critical)** | 30 minutes | Time to restore read-only access |
| **RTO (Full)** | 4 hours | Time to restore read-write access |
| **MTPD** (Maximum Tolerable Period of Disruption) | 8 hours | Maximum acceptable downtime |
| **MTD** (Maximum Tolerable Data Loss) | 1 hour | Tolerable data loss window |

---

## 2. Backup Strategy

### 2.1 Daily Backup (Automatic)

```
Schedule: 02:00 Baghdad time (UTC+3)
Tool: pg_dump with custom format (-Fc)
Encryption: AES-256-GCM (encrypted backup)
Destination: S3 bucket gula-backups (server-side encryption)

File name: gula_<date>_<time>.sql.gz.enc
Retention: 30 days on S3 Standard
           90 days on S3 Glacier-Instant
           365 days on S3 Glacier-Deep Archive
```

### 2.2 Weekly Backup (Full + Archive)

```
Schedule: Sunday 02:00 Baghdad time
Tool: pg_dump with directory format (-Fd)
Additional: Configuration files, environment templates
Retention: 12 weeks (quarterly → 1 year)
```

### 2.3 Monthly Backup (Long-Term Archive)

```
Schedule: First day of month, 02:00
Tool: pg_dump custom format + pg_dumpall (global objects)
Retention: 7 years (regulatory compliance)
Storage: S3 Glacier-Deep Archive + offline tape
```

### 2.4 Continuous WAL Archiving

```
PostgreSQL archive_mode = on
archive_command: cp %p /wal_archive/%f
WAL shipping to S3 every 5 minutes
Retention: 7 days (enables PITR within 7-day window)
```

---

## 3. Point-in-Time Recovery (PITR)

### 3.1 Recovery Window

| Window | Accuracy | Available |
|--------|----------|-----------|
| Last 24 hours | ±5 minutes | Yes |
| Last 7 days | ±1 minute | Yes (via WAL) |
| Last 30 days | ±1 day | Yes (daily dumps) |

### 3.2 PITR Procedure

```bash
# Step 1: Provision new DB instance
docker compose -f docker-compose.dr.yml up -d postgres

# Step 2: Restore base backup
docker compose exec -T postgres \
  pg_restore --dbname=gula --clean --if-exists \
  s3://gula-backups/daily/gula_2026-07-15_020001.sql.gz

# Step 3: Apply WAL to target time
docker compose exec postgres \
  pg_ctl -D /var/lib/postgresql/data promote

# Step 4: Validate data integrity
docker compose exec postgres \
  psql -U gula -c "SELECT count(*) FROM patients;"
docker compose exec postgres \
  psql -U gula -c "SELECT count(*) FROM lab_orders;"

# Step 5: Redirect traffic
# Update DNS or load balancer to point to DR instance
```

---

## 4. Cross-Region Failover

### 4.1 Architecture

```
Primary Region (Middle East — Bahrain/AUH)
├── PostgreSQL Primary (Read/Write)
├── Redis Primary
├── Application servers
├── S3 primary bucket
└── CloudFront primary distribution

DR Region (Europe — Frankfurt)
├── PostgreSQL Replica (Read-only, streaming replication)
├── Redis Replica
├── Standby application servers (scale 0)
├── S3 replica bucket (cross-region replication)
└── CloudFront DR distribution (disabled)
```

### 4.2 Failover Trigger Criteria

| Condition | Threshold | Action |
|-----------|-----------|--------|
| Primary region unreachable | 5 min | Automatic failover |
| DB primary unhealthy | 2 consecutive health checks fail | Promote replica |
| Application layer down | All backends unhealthy for 5 min | DNS switch |
| Planned maintenance | Scheduled + announced | Manual failover |

### 4.3 Failover Procedure

```bash
# Step 1: Promote DR PostgreSQL to primary
psql -h dr-postgres.gula.internal -c "SELECT pg_promote();"

# Step 2: Scale up DR applications
docker compose -f docker-compose.dr.yml up -d gula-backend
kubectl scale deployment gula-backend --replicas=5 -n gula

# Step 3: Activate DR CloudFront distribution
aws cloudfront update-distribution --id DR_DIST_ID --enabled

# Step 4: Switch DNS
# Update Route53 weighted record: 0% primary → 100% DR

# Step 5: Verify
curl https://api.gula.health/health/deep
# Expected: status "GREEN", region "eu-frankfurt"

# Step 6: Update monitoring
# Switch Prometheus remote_write to DR
```

### 4.4 Automated Failover (Future)

```
- Route53 health checks monitor /health/ready
- Lambda function triggers on health check failure
- Lambda promotes DR DB, scales DR apps, updates DNS
- Notifications sent to on-call via SNS
- ETA: Implemented by Q4 2026
```

---

## 5. Failback Procedure

```bash
# Step 1: Reproduce primary region
# (After root cause resolved)

# Step 2: Set up replication from DR → Primary
pg_basebackup -h dr-postgres -D /data -P -U replicator

# Step 3: Enable streaming replication (DR → Primary)
# Set up primary as replica of DR

# Step 4: Switch roles when DR and Primary are in sync
psql -h dr-postgres -c "SELECT pg_promote();"
# Now original primary is promoted

# Step 5: Reverse DNS
aws route53 change-resource-record-sets --change-batch file://dns-primary.json

# Step 6: Verify
curl https://api.gula.health/health/deep
# Expected: status "GREEN", region "me-bahrain"

# Step 7: Re-establish DR replication
# Set up streaming replication from Primary → DR
```

---

## 6. Recovery Drills Schedule

| Drill Type | Frequency | Scope | Participants |
|------------|-----------|-------|--------------|
| **Tabletop** | Monthly | Walk through DR procedure, no actual failover | Ops team |
| **Backup restore** | Monthly | Restore backup to staging, validate data | DB admin |
| **Read-only failover** | Quarterly | Failover to DR, run read tests, fail back | Ops + QA |
| **Full failover** | Bi-annual | Complete failover, run for 4 hours, fail back | All engineering |
| **PITR drill** | Quarterly | Perform point-in-time recovery to specific minute | DB admin |
| **Chaos engineering** | Bi-annual | Inject failures, observe self-healing | Platform team |

### 6.1 Drill Schedule 2026

| Month | Drill | Date |
|-------|-------|------|
| August | Backup restore | 1st Saturday |
| September | Read-only failover | 2nd Saturday |
| October | PITR drill | 1st Saturday |
| November | Tabletop scenario | 3rd Wednesday |
| December | Full failover | 2nd Saturday |

---

## 7. Data Integrity Verification

### 7.1 Post-Recovery Checks

```sql
-- Check row counts match expected
SELECT 'patients', count(*) FROM patients
UNION ALL
SELECT 'lab_orders', count(*) FROM lab_orders
UNION ALL
SELECT 'lab_results', count(*) FROM lab_results;

-- Verify audit log chain integrity
-- (Each entry's hash must match previous entry)
WITH hash_chain AS (
  SELECT id, lag(hash) OVER (ORDER BY timestamp) as prev_hash
  FROM audit_logs
)
SELECT count(*) as broken_links
FROM hash_chain
WHERE prev_hash IS NOT NULL
  AND prev_hash != (
    SELECT hash FROM audit_logs a2 WHERE a2.id = hash_chain.id
  );

-- Check foreign key integrity
SELECT 'orphan_results', count(*)
FROM lab_results r LEFT JOIN lab_orders o ON r.order_id = o.id
WHERE o.id IS NULL;
```

### 7.2 Application-Level Verification

```bash
# Run integrity test suite
cd backend && python -m pytest tests/test_integrity.py -v

# Verify business continuity
curl -X POST https://api.gula.health/api/v1/integrity/check \
  -H "Authorization: Bearer $ADMIN_TOKEN"

# Expected output:
# {
#   "status": "pass",
#   "checks": {
#     "database_reachable": true,
#     "patient_count_matches": true,
#     "order_result_consistency": true,
#     "audit_chain_intact": true,
#     "replication_lag": "0s"
#   }
# }
```

---

## 8. Communication Plan

| Stakeholder | Notification | Channel | Timeline |
|-------------|-------------|---------|----------|
| Ops team | Incident alert | PagerDuty + Telegram | Immediate |
| Engineering | Outage notification | Slack #ops | 5 minutes |
| Support team | User-facing issue | Slack #support | 10 minutes |
| Ministry IT | Status update | Email + phone | 30 minutes |
| All users | Service status | Status page | 1 hour |
| Public | Major outage | Website banner | 2 hours |
| Media (if widespread) | Press statement | PR department | 4 hours |

**Status page:** `https://status.gula.health` — hosted externally (e.g., Statuspage.io)
