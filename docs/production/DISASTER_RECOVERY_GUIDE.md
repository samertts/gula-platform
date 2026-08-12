# GULA Platform — Disaster Recovery Guide v1.0

**Version:** 1.0
**Date:** 2026-07-15
**Status:** FINAL
**Classification:** CONFIDENTIAL — Operations Team Only

---

## 1. DR Strategy

### Overview

GULA uses an **active-passive multi-region** disaster recovery strategy:

| Region | Role | Location | Status |
|--------|------|----------|--------|
| ME | Primary | Middle East (Bahrain/Iraq) | Active |
| EU | DR | Frankfurt, Germany | Standby |

### Recovery Objectives

| Metric | Target | Measurement |
|--------|--------|-------------|
| RPO (Recovery Point Objective) | 5 seconds | WAL shipping lag |
| RTO (Recovery Time Objective) | 5 minutes | Time from failover decision to fully operational |
| Availability SLA | 99.99% | Uptime per calendar month |
| Max data loss | 5 seconds of transactions | Controlled by synchronous replication |

### DR Architecture

```
┌──────────────────────────────────────────────┐
│          Cloudflare Global Load Balancer       │
│  Primary: api.gula.health → ME Region         │
│  Failover: api.gula.health → EU Region        │
└──────────────────────┬───────────────────────┘
                       │
          ┌────────────┴────────────┐
          ▼                         ▼
┌─────────────────┐      ┌─────────────────┐
│   ME Region      │      │   EU Region      │
│   (Active)       │      │   (Passive)      │
│                  │      │                  │
│  PostgreSQL P    │◄────►│  PostgreSQL DR   │
│  (WAL streaming) │ WAL  │  (replica)       │
│                  │      │                  │
│  Redis Master    │─────►│  Redis Replica   │
│                  │ async│                  │
│  RabbitMQ P      │─────►│  RabbitMQ M      │
│                  │      │                  │
│  MinIO P         │─────►│  MinIO DR        │
│                  │ sync │                  │
│  Backend Active  │      │  Backend Standby │
└─────────────────┘      └─────────────────┘
```

---

## 2. Replication Setup

### PostgreSQL WAL Streaming

```bash
# On DR region: set up streaming replication
pg_basebackup -h postgres-primary.me.gula.internal \
  -D /var/lib/postgresql/data \
  -S replication_slot_gula_dr \
  -X stream -P -v

# Configure DR standby (postgresql.auto.conf)
cat >> /var/lib/postgresql/data/postgresql.auto.conf << EOF
primary_conninfo = 'host=postgres-primary.me.gula.internal port=5432 user=replicator password=REPL_PASS application_name=gula_dr'
primary_slot_name = 'replication_slot_gula_dr'
hot_standby = on
EOF

# Create standby signal
touch /var/lib/postgresql/data/standby.signal
```

### Redis Async Replication

```conf
# DR Redis configuration
replicaof postgres-primary.me.gula.internal 6379
replica-read-only yes
replica-lazy-flush no
replica-serve-stale-data yes
```

### MinIO Bucket Replication

```bash
# Configure bucket replication on primary MinIO
mc admin replicate add me-minio eu-minio \
  --replicate existing-objects \
  --replicate delete-marker \
  --replicate delete \
  --sync
```

### RabbitMQ Shovel / Federation

```bash
# Configure shovel plugin on primary
rabbitmq-plugins enable rabbitmq_shovel rabbitmq_shovel_management

# Add shovel to forward messages to DR
rabbitmqctl set_parameter shovel gula-dr-shovel \
  '{"src-queue": "gula.events",
    "dest-uri": "amqp://user:pass@eu-rabbitmq:5672",
    "dest-queue": "gula.events.dr"}'
```

---

## 3. Failover Scenarios

### 3.1 Pod/Container Failure

**Symptoms:**
- Health check returns 503 on affected pod
- Container in `CrashLoopBackOff` or `Error` state
- Error rate increases

**Impact:** Partial capacity loss, no data loss

**Automated Response:**
- K8s: Pod auto-restarted by ReplicaSet
- Docker: Restart policy restarts container
- Health check: Removed from load balancer

**Manual Action:** None required (auto-healed)

**RTO:** <30 seconds

---

### 3.2 Node Failure

**Symptoms:**
- Node heartbeat lost in monitoring
- Multiple pods become unavailable
- Node status shows `NotReady`

**Impact:** Significant capacity loss, potential partial data loss (in-memory queue)

**Automated Response:**
- K8s: Pods rescheduled to healthy nodes
- Patroni: Replica promotion if primary node fails
- Redis: Sentinel failover if master node fails

**Manual Action:**

```bash
# 1. Verify node is truly down
kubectl get nodes
kubectl describe node <failed-node>

# 2. Cordon failed node (if still reachable)
kubectl cordon <failed-node>

# 3. Verify pods are rescheduling
kubectl get pods -n gula-platform -o wide

# 4. Check Patroni status
patronictl -c /etc/patroni/patroni.yml list

# 5. Verify cluster health
kubectl get nodes
kubectl get pods -n gula-platform
```

**RTO:** <2 minutes

---

### 3.3 Database Primary Failure

**Symptoms:**
- `DegradedModeMiddleware` active (writes rejected, reads work)
- Circuit breaker opens for database
- Patroni alert: "Leader changed"
- `pg_isready` returns failure on primary
- Replication lag spikes on replicas

**Impact:** Write operations unavailable, read operations continue

**Automated Response:**
- Patroni: Automatic replica promotion within 30 seconds
- Circuit breaker: Opens to reject writes, periodic retry

**Manual Action:**

```bash
# 1. Confirm Patroni failover status
patronictl -c /etc/patroni/patroni.yml list
patronictl -c /etc/patroni/patroni.yml history

# 2. Verify new primary is healthy
pg_isready -h <new-primary-ip>
docker compose exec postgres psql -U gula -c "SELECT pg_is_in_recovery();"
# Should return 'f' (false = not in recovery = primary)

# 3. Verify data integrity
docker compose exec postgres psql -U gula -c "
SELECT count(*) FROM labs;
SELECT count(*) FROM patients;
SELECT count(*) FROM lab_orders;
SELECT count(*) FROM lab_results;"

# 4. Rebuild failed old primary as new replica
# On the failed node:
pg_rewind --target-pgdata /var/lib/postgresql/data \
  --source-server="host=<new-primary> port=5432 user=postgres"

# 5. Update connection strings if needed
docker compose up -d --no-deps gula-backend

# 6. Verify circuit breaker has closed
curl -s https://api.gula.health/health/deep | jq .circuit_breakers

# 7. Verify writes work
curl -X POST https://api.gula.health/test/write
```

**RTO:** <30 seconds (Patroni auto-failover)

---

### 3.4 Cache Failure

**Symptoms:**
- Redis circuit breaker opens
- Cache miss rate spikes to 100%
- Response latency increases (DB takes the load)
- Redis `PING` fails

**Impact:** Performance degradation (DB handles full load), no data loss

**Automated Response:**
- Redis Sentinel: Slave promotion within 10 seconds
- Backend: Falls back to DB queries with degraded performance

**Manual Action:**

```bash
# 1. Check Sentinel status
redis-cli -h redis-sentinel -p 26379 SENTINEL masters
redis-cli -h redis-sentinel -p 26379 SENTINEL replicas gula-master

# 2. Verify new master
redis-cli -h <new-master-ip> -a $REDIS_PASSWORD PING
redis-cli -h <new-master-ip> -a $REDIS_PASSWORD INFO replication

# 3. Verify backend is connecting to new master
docker compose logs --tail=20 gula-backend | grep redis

# 4. Warm cache
curl -X POST https://api.gula.health/admin/cache/warm \
  -H "Authorization: Bearer $GULA_ADMIN_TOKEN"

# 5. Monitor cache hit ratio
# Grafana: Redis Hit Rate panel → should return to >95%
```

**RTO:** <10 seconds (Sentinel auto-failover)

---

### 3.5 Queue Failure

**Symptoms:**
- RabbitMQ management UI unreachable
- Messages not being consumed
- Worker processes idle
- Monitoring alerts for queue depth

**Impact:** Async operations delayed, eventual consistency delayed

**Automated Response:**
- RabbitMQ mirrored queue: automatic failover to replica
- Workers: reconnect to available node

**Manual Action:**

```bash
# 1. Check cluster status
rabbitmqctl cluster_status

# 2. If a node is down, check mirrored queue state
rabbitmqctl list_queues name messages consumers state

# 3. Promote a mirror to master if needed
rabbitmqctl sync_queue gula.events

# 4. If all nodes down, restart
docker compose restart rabbitmq

# 5. Verify message flow
rabbitmqctl list_queues name messages messages_ready messages_unacknowledged
```

**RTO:** <5 seconds (mirrored queue failover)

---

### 3.6 Region Failure

**Symptoms:**
- All endpoints in ME region are unreachable
- Cloudflare health checks fail
- DR alert triggered
- Complete platform outage in primary region

**Impact:** Complete platform unavailability if DR not activated

**Automated Response:**
- Cloudflare: Detects health check failure, triggers failover notification
- **NOT** automatic DNS failover (manual to prevent split-brain)

**Manual Action — FAILOVER PROCEDURE:**

```bash
# STEP 1: Verify ME region is unreachable (3 independent checks)
curl -m 5 https://api.gula.health/health || true
curl -m 5 https://me-monitor.gula.internal/health || true
ping -c 3 postgres-primary.me.gula.internal || true

# If all 3 fail → proceed with failover

# STEP 2: Promote DR PostgreSQL to primary (within EU region)
# On DR postgres server:
psql -c "SELECT pg_promote();"

# Verify:
psql -c "SELECT pg_is_in_recovery();"
# Should return 'f' (false = not in recovery)

# STEP 3: Activate DR Redis as writable
redis-cli -h eu-redis SLAVEOF NO ONE

# STEP 4: Activate DR RabbitMQ
# On each DR RabbitMQ node:
rabbitmqctl stop_app
rabbitmqctl reset
rabbitmqctl start_app
rabbitmqctl set_policy ha-all ".*" '{"ha-mode":"all","ha-sync-mode":"automatic"}'

# STEP 5: Scale up DR backend replicas (from 1 standby to 3+ active)
docker compose up -d --scale gula-backend=3

# STEP 6: Update Cloudflare DNS
# Change api.gula.health A record to point to EU load balancer IP
# Via Cloudflare API:
curl -X PUT "https://api.cloudflare.com/client/v4/zones/$ZONE_ID/dns_records/$RECORD_ID" \
  -H "Authorization: Bearer $CLOUDFLARE_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"type":"A","name":"api","content":"<EU-LB-IP>","ttl":60,"proxied":true}'

# STEP 7: Verify failover
curl -s https://api.gula.health/health | jq .
curl -s https://api.gula.health/health/deep | jq .

# STEP 8: Test write path
curl -X POST https://api.gula.health/test/write

# STEP 9: Announce to stakeholders
# (Use communication template in INCIDENT_RESPONSE_GUIDE.md)
```

**RTO:** <5 minutes (manual failover)

---

## 4. Failback Procedure

### Prerequisites

Before failing back to the primary (ME) region:
1. Root cause of the original failure is fixed
2. ME region is stable and tested
3. Data catch-up is complete and verified
4. Business approval obtained

### Failback Steps

```bash
# STEP 1: Restore ME as a standby of EU (catch up on missed data)
# On ME postgres:
pg_basebackup -h <eu-primary-ip> \
  -D /var/lib/postgresql/data \
  -S replication_slot_gula_fallback \
  -X stream -P -v

# STEP 2: Wait for replication to catch up
psql -h <eu-primary-ip> -c "SELECT * FROM pg_stat_replication;"
# Wait for write_lag to approach 0

# STEP 3: Verify data parity
# Compare row counts between EU (current primary) and ME (catching up)
python3 scripts/compare-row-counts.py \
  --source=postgresql://user:pass@eu/gula \
  --target=postgresql://user:pass@me/gula

# STEP 4: Schedule maintenance window
# Notify stakeholders: "Scheduled failback to ME region at 02:00 UTC"

# STEP 5: During maintenance window:
# 5a. Stop writes on EU
docker compose scale gula-backend=0

# 5b. Final WAL sync (wait for 0 replica lag)
psql -h <eu-primary-ip> -c "SELECT pg_switch_wal();"

# 5c. Promote ME to primary
psql -h <me-ip> -c "SELECT pg_promote();"

# 5d. Point DR (EU) to follow ME
# 5e. Update Cloudflare DNS back to ME IP
curl -X PUT "https://api.cloudflare.com/client/v4/zones/$ZONE_ID/dns_records/$RECORD_ID" \
  -H "Authorization: Bearer $CLOUDFLARE_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"type":"A","name":"api","content":"<ME-LB-IP>","ttl":60,"proxied":true}'

# STEP 6: Verify failback
curl -s https://api.gula.health/health | jq .
curl -s https://api.gula.health/health/deep | jq .

# STEP 7: Run full verification suite
./scripts/smoke-test.sh
```

**Failback RTO:** <15 minutes

---

## 5. Data Integrity Verification After Recovery

### Automated Data Checks

```bash
# Row count comparison
python3 scripts/compare-row-counts.py \
  --source=postgresql://user:pass@primary/gula \
  --target=postgresql://user:pass@dr/gula

# Checksum verification
python3 scripts/verify-table-checksums.py --db-url=postgresql://user:pass@gula

# Audit log chain verification
python3 scripts/verify-audit-chain.py --db-url=postgresql://user:pass@gula
```

### Manual Data Checks

```sql
-- Check for orphan records
SELECT count(*) FROM lab_results r
LEFT JOIN lab_orders o ON r.order_id = o.id
WHERE o.id IS NULL;

-- Check referential integrity
SELECT count(*) FROM lab_orders o
LEFT JOIN patients p ON o.patient_id = p.id
WHERE p.id IS NULL;

-- Check tenant isolation
SELECT lab_id, count(*) FROM patients GROUP BY lab_id;

-- Verify latest data
SELECT max(created_at) FROM audit_logs;
SELECT max(created_at) FROM lab_results;
SELECT max(created_at) FROM lab_orders;

-- Check sequence sanity
SELECT 'patients', max(id) FROM patients
UNION ALL
SELECT 'lab_orders', max(id) FROM lab_orders;
```

### Verification Sign-off

After all checks pass, complete the sign-off:

```bash
# Generate recovery report
python3 scripts/generate-dr-report.py \
  --event="failover" \
  --from="me" \
  --to="eu" \
  --start="2026-07-15T14:30:00Z" \
  --end="2026-07-15T14:35:00Z" \
  --status="completed" \
  --data-loss="0 rows" \
  --rto="4m30s"
```

---

## 6. Quarterly DR Test Procedure

### Schedule

| Quarter | Month | Type | Scope |
|---------|-------|------|-------|
| Q1 | January | Tabletop | Documentation review |
| Q2 | April | Partial test | Database failover only |
| Q3 | July | Full failover | Complete region failover |
| Q4 | October | Chaos test | Random failure injection |

### Test Plan Template

```markdown
# DR Test Plan — Q3 2026

Date: 2026-07-20
Time: 02:00-04:00 UTC
Scope: Full region failover to EU DR

## Participants
- Test Lead:
- Operations:
- DBA:
- Network Engineer:
- Security:
- Observer:

## Test Steps
1. [ ] Pre-test briefing (15 min)
2. [ ] Verify DR environment is ready (15 min)
3. [ ] Execute failover procedure (30 min)
4. [ ] Verify all services available (15 min)
5. [ ] Run data integrity checks (15 min)
6. [ ] Execute failback procedure (30 min)
7. [ ] Post-test verification (15 min)
8. [ ] Debrief and report (15 min)

## Success Criteria
- [ ] RTO ≤ 5 minutes
- [ ] RPO ≤ 5 seconds
- [ ] All critical endpoints functional
- [ ] No data loss
- [ ] All integrity checks pass

## Rollback Plan
If test fails at any point, stop and fail back immediately.
Contact: [On-call DBA]
```

### Test Execution

```bash
# 1. Pre-test snapshot
./scripts/dr-pre-test-snapshot.sh

# 2. Execute failover
# Follow steps in Section 3.6 (Region Failure)

# 3. Run verification
./scripts/smoke-test.sh --target dr
python3 scripts/verify-table-checksums.py --db-url=postgresql://user:pass@dr/gula

# 4. Execute failback
# Follow steps in Section 4 (Failback)

# 5. Post-test verification
./scripts/smoke-test.sh
python3 scripts/verify-table-checksums.py

# 6. Generate report
python3 scripts/generate-dr-report.py \
  --event="quarterly-test" \
  --type="full-failover" \
  --status="completed" \
  --rto-measured="3m45s" \
  --rpo-measured="2s" \
  --data-loss="0" \
  --issues="None"
```

---

## 7. Communication Plan

### During DR Event

| Time | Action | Owner |
|------|--------|-------|
| T+0 | Incident declared | On-call |
| T+0 | Page on-call team | PagerDuty |
| T+1 | Open incident in Slack #gula-incidents | On-call |
| T+2 | Begin failover procedure | Operations Lead |
| T+3 | Notify engineering team | Slack #gula-eng |
| T+5 | Notify management | Phone/Email |
| T+10 | Notify stakeholders | Email template |
| T+RTO | Service restored | Operations Lead |
| T+RTO+15 | Status update to all channels | Incident Commander |
| T+1h | Detailed incident report | Incident Commander |
| T+24h | Post-mortem meeting | Engineering Lead |

### Stakeholder Communication Template

```
Subject: [GULA] Service Incident — [DATE] — [SEVERITY]

Status: RESOLVED / IN PROGRESS / MONITORING
Severity: SEV1 / SEV2
Duration: [START TIME] — [END TIME] (or "ongoing")
Affected: [List affected features/regions]

What happened:
[Brief description of the incident]

Impact:
[What users experienced, how many affected]

Root Cause:
[What caused the incident]

Resolution:
[How the incident was resolved or is being resolved]

Next Steps:
[Prevention measures, follow-up actions]

Next Update:
[Expected time of next update]
```

---

## 8. DR Configuration Reference

### Environment Variables

| Variable | Primary Value | DR Value |
|----------|--------------|----------|
| `POSTGRES_HOST` | `postgres-primary.me.internal` | `postgres-primary.eu.internal` |
| `POSTGRES_REPLICA_HOST` | `postgres-replica.me.internal` | `postgres-replica.eu.internal` |
| `REDIS_HOST` | `redis-master.me.internal` | `redis-master.eu.internal` |
| `RABBITMQ_HOST` | `rabbitmq.me.internal` | `rabbitmq.eu.internal` |
| `MINIO_ENDPOINT` | `minio.me.internal:9000` | `minio.eu.internal:9000` |

### Monitoring DR Health

```bash
# Check replication status (on DR)
psql -h eu-postgres -c "
SELECT application_name,
       state,
       sync_state,
       write_lag,
       flush_lag,
       replay_lag
FROM pg_stat_replication;"

# Check DR readiness score
curl -s https://dr-monitor.gula.internal/health/ready
```
