# PI-004: National Deployment, Operations & Resilience Platform

## Disaster Recovery Guide

**Version:** 1.0.0
**App Version:** 2.1.0
**Date:** 2026-07-16

---

### 1. Recovery Objectives

| Metric | Target | Measurement Method |
|--------|--------|-------------------|
| **RPO** (Recovery Point Objective) | ≤5s | WAL streaming lag + `scripts/dr-test.sh` |
| **RTO** (Recovery Time Objective) | ≤5m | Automatic failover via Patroni (`config/postgres-ha/failover.sh`) |
| **DR Test Frequency** | Quarterly | `scripts/dr-test.sh` |
| **Backup Verification** | Daily | `scripts/backup-verification.sh` |

Reference: `config/dr/cross-region-replication.yml:59-60`

---

### 2. Backup Strategy

#### 2.1 Automated Backups

Three-layer backup strategy:

| Layer | Frequency | Retention | Tool | Config |
|-------|-----------|-----------|------|--------|
| **Continuous WAL Archiving** | Real-time | 60 days | pgBackRest + S3 | `config/postgres-ha/backup-config.sh` |
| **Full Database** | Daily at 02:00 | 30 days | pgBackRest | `config/postgres-ha/backup-config.sh:291` |
| **Hourly Incremental** | Every hour | 7 days | pgBackRest | `config/postgres-ha/backup-config.sh:293` |
| **Monthly Snapshot** | 1st of month | 12 months | pgBackRest | `config/postgres-ha/backup-config.sh:295` |
| **pg_dump (cron)** | Daily + Hourly | 30 days daily, 2 days hourly | Docker cron container | `docker-compose.full.yml:752-773` |

#### 2.2 pgBackRest Configuration (`config/postgres-ha/backup-config.sh`)

```bash
# Install and configure
S3_KEY=your_key S3_KEY_SECRET=your_secret ./config/postgres-ha/backup-config.sh install

# Manual full backup
./config/postgres-ha/backup-config.sh full

# Verify backup integrity
./config/postgres-ha/backup-config.sh verify
```

Key configuration:
- **Dual repository:** Local staging (`/var/lib/pgbackrest`) + S3 remote
- **Compression:** Zstandard (zst), level 6
- **Parallelism:** 4 processes (matches vCPU count)
- **Buffer:** 512K buffer, 1024M hard max
- **S3 endpoint:** Configurable (AWS S3 or MinIO)

#### 2.3 Docker Backup Container (`docker-compose.full.yml:752-773`)

```yaml
backup-cron:
  image: postgres:14.11-alpine
  command: >
    -c "mkdir -p /backups/daily /backups/hourly /backups/logs &&
    echo '0 2 * * * pg_dump ... | gzip > /backups/daily/gula_full_$$(date +\%Y\%m\%d).sql.gz
    && find ... -mtime +30 -delete' > /etc/crontabs/root &&
    echo '0 * * * * pg_dump ... | gzip > /backups/hourly/gula_hourly_$$(date +\%Y\%m\%d).sql.gz
    && find ... -mtime +2 -delete' >> /etc/crontabs/root &&
    crond -f -l 2"
```

#### 2.4 Backup Scripts

| Script | Purpose |
|--------|---------|
| `scripts/backup.sh` | Manual backup trigger |
| `scripts/continuous-backup.sh` | Continuous backup daemon |
| `scripts/backup-verification.sh` | Verify latest backup integrity |
| `scripts/manage-snapshots.sh` | Snapshot lifecycle management |

---

### 3. Point-in-Time Recovery (PITR)

#### 3.1 PITR Configuration (`config/postgres-ha/pitr-config.sh`)

```bash
# Configure WAL archiving
./config/postgres-ha/pitr-config.sh apply

# Check status
./config/postgres-ha/pitr-config.sh status
```

WAL archiving configuration:
- **WAL level:** replica (required for streaming replication)
- **Archive command:** `aws s3 cp %p s3://gula-wal-archive/wal/%f` (or MinIO via `mc`)
- **Archive timeout:** 60s
- **WAL segment size:** 64MB
- **Bucket:** `gula-wal-archive` in `me-central-1`

#### 3.2 PITR Restore

```bash
# PITR to specific timestamp
FORCE_PITR=true ./config/postgres-ha/pitr-config.sh pitr "2026-06-01 14:30:00+03"

# Or via pgBackRest directly
sudo -u postgres pgbackrest --stanza=gula \
  --type=time "--target=2026-06-01 14:30:00+03" \
  --target-action=promote --delta restore
```

#### 3.3 PITR Script

`scripts/pitr-recover.sh` provides a streamlined interface:

```bash
./scripts/pitr-recover.sh --target-time "2026-06-01 14:30:00" --target-action promote
```

---

### 4. Cross-Region Replication

#### 4.1 Topology (`config/dr/cross-region-replication.yml`)

```
Primary Region (me-central1)          DR Region (eu-west1)
  Baghdad, Iraq                         Frankfurt, Germany
  DigitalOcean (fra1)                   DigitalOcean (fra1-alt)
  Priority: 100                         Priority: 50
  Active: true                          Active: false
```

#### 4.2 PostgreSQL Replication

- **Mode:** Streaming synchronous replication
- **Replication slots:** 5
- **WAL keep size:** 1024MB
- **Max WAL senders:** 10
- **Standby timeout:** 30s
- **DR promotion:** Automatic

Patroni standby cluster configuration (`config/postgres-ha/patroni.yml:197-208`):

```yaml
standby_cluster:
  host: "{{ DR_PRIMARY_HOST }}"
  port: 5432
  primary_slot_name: gula_dr
  create_replica_methods:
    - pgbackrest
    - basebackup
```

#### 4.3 Redis Replication

Cross-region replication is **disabled** for Redis (ephemeral cache). Sentinel HA within region only.

#### 4.4 RabbitMQ Replication (`config/dr/cross-region-replication.yml:32-38`)

- **Mode:** Shovel (dynamic)
- **Ack mode:** on-confirm
- **Reconnect delay:** 5s
- **Queue pattern:** `*.events`
- **HA mode:** all

#### 4.5 MinIO Replication (`config/dr/cross-region-replication.yml:40-48`)

- **Mode:** Bucket replication
- **Sync:** Async
- **Versioning:** Enabled
- **Rules:** Source `gula-reports` → Target `gula-reports-dr`

#### 4.6 DNS Failover (`config/dr/cross-region-replication.yml:50-57`)

- **Provider:** Cloudflare
- **Failover TTL:** 60s
- **Health checks:** `/health` endpoint, 30s interval, 5s timeout, 3 unhealthy threshold

---

### 5. Failover Procedures

#### 5.1 Patroni Automatic Failover (`config/postgres-ha/failover.sh`)

The automated failover script performs:

1. **Discover Patroni API** — find first responsive member
2. **Identify current leader** — via `/_cluster` endpoint
3. **Assess leader health** — if healthy, exit (no failover needed)
4. **Evaluate replica candidates** — pick best (least lag, healthy)
5. **Execute failover** — POST to Patroni `/failover`
6. **Wait for election** — poll every 2s, max 60s
7. **Verify new leader** — test read/write via psql or Patroni health
8. **Update application config** — update DATABASE_URL in `.env` and Consul
9. **Send alert** — webhook notification

```bash
# Manual failover
./config/postgres-ha/failover.sh

# Dry run
DRY_RUN=true ./config/postgres-ha/failover.sh

# Standalone PG failover script (non-Patroni environments)
./scripts/pg_failover.sh
```

#### 5.2 DR Failover (`scripts/dr-failover.sh`)

Cross-region failover for the full platform:

```bash
./scripts/dr-failover.sh --region eu-west1 --confirm
```

#### 5.3 DR Failback (`scripts/dr-failback.sh`)

Return to primary region after DR event:

```bash
./scripts/dr-failback.sh --region me-central1 --confirm
```

#### 5.4 DR Recovery (`scripts/dr_recovery.sh`)

Comprehensive DR recovery:

```bash
./scripts/dr_recovery.sh --full
```

#### 5.5 Validation (`scripts/validate-restore.sh`)

```bash
./scripts/validate-restore.sh --backup latest
./scripts/validate-restore.sh --pitr "2026-06-01T14:30:00Z"
```

#### 5.6 DR Testing (`scripts/dr-test.sh`)

```bash
./scripts/dr-test.sh          # Run DR test suite
make dr-test                  # Same, via Makefile
make dr-validate              # Validate DR configuration
```

---

### 6. RPO/RTO Validation

#### 6.1 Measuring RPO

```bash
# Check WAL archive lag
./config/postgres-ha/pitr-config.sh status

# Replication lag from psql
SELECT now() - pg_last_xact_replay_timestamp() AS replication_lag;
```

#### 6.2 Measuring RTO

```bash
# Time failover with DR test
time ./scripts/dr-test.sh --measure-rto
```

Target RTO: 5 minutes (from detection to full read/write capability).

#### 6.3 Validation Scripts

| Script | Validates | Frequency |
|--------|-----------|-----------|
| `scripts/backup-verification.sh` | Backup integrity | Daily |
| `scripts/validate-restore.sh` | Restore from backup | Weekly |
| `scripts/dr-test.sh` | Full DR scenario | Quarterly |
| `scripts/restore-test.sh` | Restore procedure | Monthly |

---

### 7. Business Continuity Procedures

#### 7.1 Continuity Tiers

| Tier | Scenario | Action | RTO |
|------|----------|--------|-----|
| 1 | Single container crash | Docker auto-restart, health check | <30s |
| 2 | Host failure (droplet) | Auto-failover to replica node | <5m |
| 3 | Database corruption | PITR to previous consistent state | <30m |
| 4 | Regional outage | Cross-region DR failover | <15m |
| 5 | Full site disaster | geo-replicated backup restore | <4h |

#### 7.2 Continuity Scripts

```bash
# Production freeze
./scripts/production-freeze.sh

# Emergency fix
./scripts/emergency-fix.sh

# Fix server
./scripts/fix-server.sh

# Change master password
./scripts/change-master-password.sh
```

#### 7.3 Read-Only Mode

When the DB circuit breaker opens:
- **L2_READ_ONLY:** Write endpoints return 503, reads still work, DB probed every 10s for recovery
- **L3_CRITICAL_ONLY:** Only health, auth, kill-switch, and metrics paths reachable

Automatic recovery: circuit breaker closes once DB health is restored for 3 consecutive checks.

---

### 8. Backup Verification Schedule

| Time | Action | Script |
|------|--------|--------|
| Every hour | Incremental backup | `backup-config.sh incr` |
| Daily 02:00 | Full backup | `backup-config.sh full` |
| Daily 06:00 | Verify latest backup | `backup-config.sh verify` |
| 1st of month 03:00 | Monthly snapshot | `backup-config.sh monthly` |
| Weekly | Restore validation test | `scripts/validate-restore.sh` |
| Monthly | DR failover drill | `scripts/dr-test.sh` |
| Quarterly | Full DR exercise | `scripts/dr-failover.sh` |

---

**References:** `config/dr/cross-region-replication.yml`, `config/postgres-ha/backup-config.sh`, `config/postgres-ha/pitr-config.sh`, `config/postgres-ha/failover.sh`, `config/postgres-ha/patroni.yml`, `scripts/dr-failover.sh`, `scripts/dr-failback.sh`, `scripts/dr_recovery.sh`, `scripts/dr-test.sh`, `scripts/backup.sh`, `scripts/continuous-backup.sh`, `scripts/backup-verification.sh`, `scripts/pitr-recover.sh`, `scripts/validate-restore.sh`, `scripts/manage-snapshots.sh`, `docker-compose.full.yml`
