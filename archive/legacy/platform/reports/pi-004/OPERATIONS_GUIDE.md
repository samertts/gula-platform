# PI-004 — Operations Guide

## National Platform — Day-to-Day Operations

**Version:** 2.1.0
**Date:** July 2026

---

## 1. Monitoring Stack

### 1.1 Components

| Component | Version | Port | Purpose |
|-----------|---------|------|---------|
| Prometheus | 2.53.x | 9090 | Metrics collection & alerting |
| Grafana | 11.x | 3000 | Dashboard & visualization |
| Loki | 3.x | 3100 | Log aggregation |
| Promtail | 3.x | 9080 | Log shipping |
| Alertmanager | 0.27.x | 9093 | Alert routing & deduplication |
| node_exporter | 1.8.x | 9100 | Host metrics |
| cAdvisor | 0.49.x | 8080 | Container metrics |
| PostgreSQL exporter | 0.15.x | 9187 | DB metrics |

### 1.2 Key Dashboards

| Dashboard | Description | Refresh |
|-----------|-------------|---------|
| **GULA Overview** | System health, request rate, error rate, latency | 15s |
| **Database Performance** | Connection pool, query times, slow queries | 30s |
| **Redis** | Memory usage, hit rate, command rate | 30s |
| **Application** | Per-endpoint latency, error breakdown | 15s |
| **Business KPIs** | Orders, results, active patients, lab throughput | 60s |
| **Infrastructure** | CPU, memory, disk, network per host | 15s |
| **Container Health** | Restarts, resource usage, OOM kills | 15s |

---

## 2. Logging (Loki)

### 2.1 Log Structure

All backend logs are structured JSON:

```json
{
  "timestamp": "2026-07-16T10:30:00Z",
  "level": "info",
  "request_id": "req_abc123",
  "endpoint": "POST /api/v1/orders",
  "method": "POST",
  "path": "/api/v1/orders",
  "status_code": 201,
  "duration_ms": 142,
  "user_id": "user_xyz",
  "lab_id": "lab_001",
  "message": "Order created successfully",
  "error": null
}
```

### 2.2 Log Levels

| Level | Description | Action Required |
|-------|-------------|-----------------|
| `debug` | Detailed diagnostic info | No |
| `info` | Normal operations | No |
| `warning` | Anomalous but handled | Review daily |
| `error` | Recoverable failure | Immediate investigation |
| `critical` | System degradation | Page on-call |

### 2.3 Log Queries (Examples)

```logql
# Error rate in last 15 minutes
rate({app="gula-backend"} |= `"level": "error"` [5m])

# Slow requests (>1s)
{app="gula-backend"} | json | duration_ms > 1000

# Specific user activity
{app="gula-backend"} | json | user_id = "user_xyz"

# Database connection issues
{app="gula-backend"} |= "database"
```

---

## 3. Alerting (Alertmanager)

### 3.1 Alert Rules

| Alert Name | Condition | Severity | Response Time |
|------------|-----------|----------|---------------|
| `HighErrorRate` | 5xx > 1% for 5m | critical | 5 minutes |
| `HighLatency` | P99 > 2s for 5m | warning | 15 minutes |
| `DatabaseDown` | PG connection failed | critical | Immediate |
| `RedisDown` | Redis connection failed | critical | Immediate |
| `HighMemoryUsage` | Memory > 85% for 10m | warning | 30 minutes |
| `HighDiskUsage` | Disk > 90% | critical | 1 hour |
| `CircuitBreakerOpen` | DB circuit open | critical | Immediate |
| `ConnectionPoolExhausted` | Pool at 100% | critical | Immediate |
| `CertificateExpiring` | TLS cert < 30 days | warning | 7 days |
| `BackupFailed` | Backup job failed | critical | 1 hour |

### 3.2 Notification Channels

| Channel | Purpose | Routing |
|---------|---------|---------|
| Telegram | Engineering on-call | critical + warning |
| Discord | All engineering | critical, warning, info |
| Email (PagerDuty) | Management escalation | critical (unacknowledged > 15m) |
| SMS | Emergency only | critical (DB/Redis down) |

### 3.3 On-Call Rotation

- **Primary:** 1 engineer (8am–8pm Baghdad time)
- **Secondary:** 1 engineer (8pm–8am)
- **Escalation:** Engineering lead
- **Schedule:** Weekly rotation, published in ops calendar

---

## 4. Incident Response

### 4.1 Severity Levels

| Level | Description | Example | SLA |
|-------|-------------|---------|-----|
| SEV-1 | Service unavailable, data loss risk | Database down | 15min respond, 2hr fix |
| SEV-2 | Feature degradation, non-critical | Slow queries | 30min respond, 4hr fix |
| SEV-3 | Minor issue, workaround exists | UI bug | 4hr respond, 24hr fix |
| SEV-4 | Cosmetic, no user impact | Wrong label | Next sprint |

### 4.2 Incident Response Process

```
1. DETECT — Monitoring alert or user report
2. TRIAGE — Assign severity, notify channel
3. RESPOND — Primary on-call investigates
4. MITIGATE — Apply fix or workaround
5. RESOLVE — Service restored
6. POST-MORTEM — Within 48 hours
```

### 4.3 Post-Mortem Template

```markdown
## Incident Post-Mortem

**Date:** 2026-07-16
**Duration:** XX minutes
**Severity:** SEV-X
**Impact:** X users affected, X requests lost

### Timeline
- HH:MM — Detection
- HH:MM — Triage
- HH:MM — Mitigation started
- HH:MM — Resolution

### Root Cause
[Detailed explanation]

### Resolution
[What was done to fix]

### Action Items
- [ ] Add monitoring for [signal]
- [ ] Automate [manual step]
- [ ] Update runbook for [scenario]
```

---

## 5. Capacity Planning

### 5.1 Current Baseline

| Resource | Current | Peak | Headroom |
|----------|---------|------|----------|
| Requests/sec | 150 | 450 | 67% |
| DB connections | 25/100 | 45/100 | 55% |
| Redis memory | 2GB/4GB | 3.2GB/4GB | 20% |
| CPU (backend) | 30% | 65% | 35% |
| Memory (backend) | 512MB/1GB | 780MB/1GB | 22% |
| Disk (DB) | 45GB/200GB | — | 77% |

### 5.2 Growth Projections

| Quarter | Users | Facilities | Orders/day | DB Size |
|---------|-------|------------|------------|---------|
| Q3 2026 | 50,000 | 15 | 5,000 | 50GB |
| Q4 2026 | 200,000 | 50 | 20,000 | 80GB |
| Q1 2027 | 500,000 | 100 | 50,000 | 150GB |
| Q2 2027 | 1,000,000 | 200 | 100,000 | 250GB |

### 5.3 Scaling Triggers

| Signal | Action |
|--------|--------|
| CPU > 70% for 1 hour | Add 1 backend replica |
| Memory > 80% for 30min | Increase instance size |
| DB connections > 80 | Increase pool + max_connections |
| Disk > 80% | Add storage or archive old data |
| Request queue > 100 | Add workers |
| Redis evictions > 0/s | Increase Redis memory |

---

## 6. Backup Verification

### 6.1 Backup Schedule

| Backup Type | Frequency | Retention | Storage |
|-------------|-----------|-----------|---------|
| Full DB dump | Daily (02:00 Baghdad) | 30 days | S3 (gula-backups/) |
| WAL archiving | Continuous | 7 days | Same bucket |
| Transaction logs | Every 5 minutes | 24 hours | Same bucket |
| Configuration snapshots | Weekly | 90 days | GitHub + S3 |
| Application logs | Daily | 90 days | Loki/S3 |

### 6.2 Verification Process

```bash
# Automated verification (runs daily at 03:00)
./scripts/verify-backup.sh

# Manual restore drill (monthly)
1. Restore latest backup to staging DB
2. Run `pg_comparison` against production checksums
3. Verify all tables present and have expected row counts
4. Test a sample query path: patient → order → result
5. Document results in ops log
```

### 6.3 Backup Commands

```bash
# Manual backup
make backup   # → ./backups/gula_2026-07-16_020001.sql.gz

# Restore to staging
gunzip < ./backups/gula_2026-07-16_020001.sql.gz | \
  docker compose exec -T postgres psql -U gula -d gula_staging

# Point-in-time recovery (PITR)
docker compose exec postgres \
  pg_restore --dbname=gula --clean --if-exists \
  /backups/gula_2026-07-16_020001.dump
```

---

## 7. Health Checks

### 7.1 Endpoints

| Endpoint | Purpose | Check Interval |
|----------|---------|----------------|
| `/health` | Liveness (process alive) | 10s |
| `/health/live` | Same as above | 10s |
| `/health/ready` | Readiness (DB, Redis, migrations) | 30s |
| `/health/deep` | Full diagnostic with component latencies | 60s |
| `/health/status` | Human-readable startup failure reason | On-demand |

### 7.2 Docker Healthchecks

```yaml
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:8000/health/live"]
  interval: 30s
  timeout: 10s
  retries: 3
  start_period: 40s
```

### 7.3 K8s Probes

```yaml
livenessProbe:
  httpGet: { path: /health/live, port: 8000 }
  initialDelaySeconds: 30
  periodSeconds: 15
readinessProbe:
  httpGet: { path: /health/ready, port: 8000 }
  initialDelaySeconds: 30
  periodSeconds: 20
startupProbe:
  httpGet: { path: /health/ready, port: 8000 }
  initialDelaySeconds: 5
  periodSeconds: 5
  failureThreshold: 30
```

---

## 8. Routine Operations

### 8.1 Daily Checklist

- [ ] Check alerts dashboard (last 24h)
- [ ] Verify backup completion
- [ ] Review error rates across all endpoints
- [ ] Check disk usage on DB server
- [ ] Confirm all containers running
- [ ] Review slow query log

### 8.2 Weekly Checklist

- [ ] Review capacity metrics (CPU, memory, disk trends)
- [ ] Audit user access and roles
- [ ] Review security scan results
- [ ] Update on-call rotation
- [ ] Apply security patches (if any)

### 8.3 Monthly Checklist

- [ ] Full disaster recovery drill
- [ ] Backup restoration test
- [ ] Performance benchmark run
- [ ] Dependency vulnerability scan
- [ ] Certificate expiry review
- [ ] Incident post-mortem review
