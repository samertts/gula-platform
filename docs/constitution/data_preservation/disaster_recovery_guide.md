# Disaster Recovery Guide

**Part of the GULA Data Preservation Constitution (Rule 7)**
**Version:** 1.0.0
**Last Updated:** 2026-07-22

---

## 1. DISASTER CLASSIFICATION

| Level | Name | Description | Example | RTO Target |
|-------|------|-------------|---------|-----------|
| L1 | Minor | Single component failure, no data loss | Pod crash, connection spike | 5 min |
| L2 | Significant | Multiple components, partial service degradation | DB primary failover, cache loss | 30 min |
| L3 | Major | Full service degradation, potential data loss | Server failure, storage corruption | 2 hours |
| L4 | Critical | Regional disaster, data at risk | Datacenter outage, fire, flood | 4 hours |
| L5 | Catastrophic | Complete infrastructure loss | Region destroyed, off-site needed | 24 hours |

---

## 2. INCIDENT RESPONSE

### 2.1 Detection

| Signal | Likely Cause | Severity |
|--------|-------------|----------|
| Health check fails | Component down | L1+ |
| AlertManager firing | Threshold exceeded | L1+ |
| User reports issue | Various | L1+ |
| Monitoring silent | Monitoring system down | L2+ |
| All endpoints timeout | Network/infrastructure | L3+ |

### 2.2 Initial Response

```
1. DETECT — Automated alert or manual report
2. ASSESS — Determine severity level (L1-L5)
3. DECLARE — Declare incident in #incidents channel
4. RESPOND — Select response team based on severity
5. COMMUNICATE — Stakeholder status every 30 min
6. RESOLVE — Execute recovery procedure
7. VERIFY — Confirm service health
8. POSTMORTEM — Root cause analysis within 72 hours
```

### 2.3 Response Team

| Role | Responsibility |
|------|---------------|
| Incident Commander | Coordinates response, makes decisions |
| Technical Lead | Executes recovery procedures |
| Communications Lead | Stakeholder updates |
| Scribe | Logs all actions and timestamps |

---

## 3. RECOVERY PROCEDURES

### 3.1 L1 — Component Failure

**Symptoms:** Single pod down, health check alert, auto-restart cycle.

```bash
# 1. Check component status
docker ps | grep gula-backend
systemctl status gula-backend

# 2. View recent logs
docker logs --tail 100 gula-backend

# 3. Restart if not auto-recovering
docker restart gula-backend
# or: systemctl restart gula-backend

# 4. Verify recovery
curl -f http://localhost:8000/health/ready

# 5. Run data integrity check
python scripts/check_data_integrity.py
```

### 3.2 L2 — DB Primary Failure

**Symptoms:** Application errors connecting to database, Patroni alert.

```bash
# 1. Verify primary is down
patronictl list

# 2. If primary failed, Patroni auto-promotes replica
# Wait 30s for automatic failover

# 3. Check new primary
patronictl list

# 4. Verify data integrity on new primary
psql -U postgres -d labdb -c "
  SELECT COUNT(*) FROM patients;
  SELECT COUNT(*) FROM lab_orders;
  SELECT COUNT(*) FROM lab_results;
"

# 5. If auto-failover did NOT happen:
patronictl failover --master gula-cluster --candidate <replica-name>

# 6. Restart application to reconnect
docker restart gula-backend

# 7. Run health check
curl -f http://localhost:8000/health/deep
```

### 3.3 L3 — Server Failure

**Symptoms:** Server unreachable, SSH timeout, all alerts firing.

```bash
# 1. Attempt SSH with fallback
ssh -o ConnectTimeout=10 user@server-ip || \
  echo "Server unreachable — proceed to DR"

# 2. If unreachable, initiate DR procedures
# Promote DR replica (see L4 procedures)

# 3. Once server is back, assess data state
# Check if PostgreSQL data directory is intact
ls -la /var/lib/postgresql/data/

# 4. If data intact, start services
systemctl start postgresql
systemctl start gula-backend

# 5. Verify and validate
curl -f http://localhost:8000/health/ready
```

### 3.4 L4 — Full DR Procedure

**Symptoms:** Entire datacenter unreachable, regional outage.

See ADR-015 and `scripts/dr_recovery.sh` for detailed procedures.

```bash
# ──────────────────────────────────────────────────
# PHASE 1: ASSESS (5 min)
# ──────────────────────────────────────────────────

# Confirm from 3 independent sources
curl -f http://10.0.1.1/health  # Primary health endpoint
curl -f http://10.0.2.1/health  # Secondary check
# Third check: external monitoring (e.g., Pingdom)

# ──────────────────────────────────────────────────
# PHASE 2: DECIDE (5 min)
# ──────────────────────────────────────────────────

# Incident Commander authorizes failover
# Reasons: primary unreachable for >5 min, no recovery expected

# ──────────────────────────────────────────────────
# PHASE 3: PROMOTE DR DATABASE (5 min)
# ──────────────────────────────────────────────────

# SSH to DR server
ssh dr-admin@dr-server

# Promote PostgreSQL standby to primary
psql -U postgres -c "SELECT pg_promote();"

# Verify promotion
psql -U postgres -c "SELECT pg_is_in_recovery();"
# Expected: false (not in recovery = primary)

# ──────────────────────────────────────────────────
# PHASE 4: ACTIVATE DR SERVICES (10 min)
# ──────────────────────────────────────────────────

# Redis
redis-cli -h dr-redis SLAVEOF NO ONE

# Scale backend
docker compose -f docker-compose.yml up -d --scale gula-backend=3

# ──────────────────────────────────────────────────
# PHASE 5: SWITCH TRAFFIC (5 min)
# ──────────────────────────────────────────────────

# Update DNS / load balancer to point to DR region
# Cloudflare: change DNS records

# ──────────────────────────────────────────────────
# PHASE 6: VERIFY (10 min)
# ──────────────────────────────────────────────────

# Full health check
curl -f http://dr-loadbalancer/health/deep

# Data integrity check
python scripts/check_data_integrity.py

# Write test
curl -X POST http://dr-loadbalancer/test-types -H "Content-Type: application/json" -d '{
  "name": "DR Test"
}'

# Verify read
curl http://dr-loadbalancer/patients?limit=1

# ──────────────────────────────────────────────────
# PHASE 7: ANNOUNCE (5 min)
# ──────────────────────────────────────────────────

# Update status page
# Notify stakeholders
# Log incident
```

### 3.5 L5 — Catastrophic Disaster

**Symptoms:** Primary and DR regions both lost.

```bash
# 1. Provision new infrastructure from IaC
terraform apply -auto-approve

# 2. Restore latest off-site backup
# Download from S3-compatible storage
aws s3 cp s3://gula-backups/prod/latest/database.dump /backups/

# 3. Restore database
createdb -U postgres labdb
pg_restore -U postgres -d labdb -j 4 /backups/database.dump

# 4. Replay WAL archives (if available)
# Set restore_command and recovery_target_time

# 5. Deploy application
docker compose up -d

# 6. Restore file storage from off-site backup
aws s3 sync s3://gula-files-backups/prod/ /data/files/

# 7. Verify and validate
python scripts/check_data_integrity.py
curl -f http://localhost:8000/health/deep
```

---

## 4. DATA INTEGRITY VERIFICATION

After every recovery, run:

```bash
python scripts/check_data_integrity.py
```

This script verifies:

- All required tables exist and are populated
- Foreign key constraints are valid
- No orphaned records
- Sequence values are consistent
- Audit log hash chain is intact
- Row counts match expected ranges

See `scripts/check_data_integrity.py` for the full implementation.

---

## 5. FAILBACK PROCEDURE

After the primary region is restored, failback must be executed carefully:

1. **Fix root cause** — Primary region issue is fully resolved
2. **Sync data** — DR region (now primary) replicates back to restored primary
3. **Verify parity** — Row counts, checksums, and FK integrity match
4. **Schedule maintenance** — Announce 30-minute maintenance window
5. **During maintenance:**
   - Stop writes on DR
   - Sync remaining data
   - Promote original primary
   - Switch DNS traffic
6. **Verify** — Full health check and data integrity
7. **Resume** — Announce service restored

---

## 6. POSTMORTEM REQUIREMENTS

Within 72 hours of any L3+ incident:

1. Timeline of events
2. Root cause analysis
3. Data loss assessment (if any)
4. Recovery procedure effectiveness
5. Improvements to prevent recurrence
6. Updates to this guide

---

## 7. TESTING SCHEDULE

| Test | Frequency | Type | Success Criteria |
|-----|-----------|------|-----------------|
| Backup verification | Weekly | Automated | Restore to temp DB, validate |
| Migration rollback | Per migration | Automated | upgrade → downgrade → upgrade |
| Single table restore | Monthly | Automated | pg_restore -t, verify data |
| Full database restore | Monthly | Automated | Full restore, integrity check |
| Component failover | Monthly | Manual | Kill component, verify recovery |
| DB failover | Quarterly | Manual | Patroni failover, verify writes |
| DR region failover | Quarterly | Manual | Full DR activation, data check |
| Chaos engineering | Quarterly | Automated | Random failures, measure recovery |

---

## 8. COMMUNICATION

| Stakeholder | Channel | Frequency During Incident |
|-------------|---------|-------------------------|
| Internal team | Slack #incidents | Continuous |
| Engineering Lead | Phone | On escalation |
| Lab administrators | Email + Dashboard banner | Every 30 min |
| Clinical staff | In-app notification | Every 60 min |
| Regulatory body | Email | Within 24 hours (if data loss) |

---

## 9. REFERENCES

- ADR-015: Disaster Recovery Strategy — Full DR architecture and decision record
- `docs/constitution/data_preservation/backup_strategy.md` — Backup procedures
- `docs/constitution/data_preservation/restore_strategy.md` — Restore procedures
- `scripts/dr_recovery.sh` — DR recovery automation
- `scripts/pg_failover.sh` — PostgreSQL failover script
- `scripts/dr-failover.sh` — Full DR failover
- `scripts/dr-failback.sh` — DR failback
- `scripts/dr-test.sh` — DR test automation
- `scripts/backup.sh` — Backup automation
- `scripts/check_data_integrity.py` — Data integrity verification
