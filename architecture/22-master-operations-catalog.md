# GULA Platform — Master Operations Catalog

Version: 1.0 — 2026-07-15
Status: **DRAFT** — Architecture Review Board approval pending

---

## Table of Contents

1. [Operational Procedures](#1-operational-procedures)
2. [Runbooks for Common Scenarios](#2-runbooks-for-common-scenarios)
3. [Incident Response Procedures](#3-incident-response-procedures)
4. [Backup and Restore Procedures](#4-backup-and-restore-procedures)
5. [Disaster Recovery Plans](#5-disaster-recovery-plans)
6. [Monitoring Dashboards](#6-monitoring-dashboards)
7. [Alert Configurations](#7-alert-configurations)
8. [On-Call Schedules](#8-on-call-schedules)
9. [Escalation Paths](#9-escalation-paths)

---

## 1. Operational Procedures

### 1.1 Deployment Procedures

| Procedure | Command/Script | Frequency | Owner |
|-----------|---------------|-----------|-------|
| Standard deploy | `docker compose up -d --build` | Per release | DevOps Team |
| Blue-green deploy | `.github/workflows/blue-green-deploy.yml` | Major releases | DevOps Team |
| Scale up | `make scale REPLICAS=5` | As needed | DevOps Team |
| Rollback | `docker compose down && docker compose up -d <previous-tag>` | Emergency | DevOps Team |
| Health check | `make health` | Post-deploy | DevOps Team |
| Deep health check | `make health-deep` | Post-deploy | DevOps Team |

### 1.2 Database Procedures

| Procedure | Command/Script | Frequency | Owner |
|-----------|---------------|-----------|-------|
| Backup | `make backup` | Daily | DevOps Team |
| Migration | `alembic upgrade head` | Per schema change | Backend Team |
| Migration test | `alembic downgrade -1 && alembic upgrade head` | Per migration | Backend Team |
| Seed data | Custom seed script | First deploy | Backend Team |
| DB shell | `make db-shell` | As needed | DevOps Team |
| Redis CLI | `make redis-cli` | As needed | DevOps Team |
| Connection pool check | `backend/app/database.py:get_pool_status()` | As needed | DevOps Team |

### 1.3 Monitoring Procedures

| Procedure | Command/Script | Frequency | Owner |
|-----------|---------------|-----------|-------|
| Health check | `make health` | Every deploy | DevOps Team |
| Deep health | `make health-deep` | Every deploy + hourly | DevOps Team |
| Status summary | `make status` | Daily | DevOps Team |
| Container status | `make ps` | As needed | DevOps Team |
| Logs tail | `make logs-backend` | Debugging | Dev Team |
| Metrics | `curl /metrics/prom` | Monitoring | DevOps Team |

### 1.4 Security Procedures

| Procedure | Command/Script | Frequency | Owner |
|-----------|---------------|-----------|-------|
| Secret generation | `make secrets-gen` | Initial/new secrets | Security Team |
| CVE scan | CI pipeline (`safety`, `trivy`) | Per commit | Security Team |
| Secret scan | CI pipeline (`gitleaks`) | Per commit | Security Team |
| Lint | `make lint` | Per commit | Dev Team |
| Kill switch on | `make kill-switch-on` | Emergency | Security Team |
| Kill switch off | `make kill-switch-off` | After resolution | Security Team |

### 1.5 Maintenance Procedures

| Procedure | Command/Script | Frequency | Owner |
|-----------|---------------|-----------|-------|
| Docker prune | `docker system prune -f` | Weekly | DevOps Team |
| Log rotation | Docker log config | Auto | Platform |
| DB vacuum | `VACUUM ANALYZE` | Weekly (scheduled) | DevOps Team |
| DB reindex | `REINDEX` | Monthly | DevOps Team |
| Certificate renewal | Let's Encrypt auto-renew | Every 90 days | Platform |

### 1.6 Makefile Targets Reference

| Target | Purpose |
|--------|---------|
| `make up` | Start all containers + wait for ready |
| `make down` | Stop and remove containers |
| `make restart` | Rebuild images + restart + deep health check |
| `make ps` | Container status table |
| `make logs-backend` | Tail backend logs |
| `make shell` | Bash into gula-backend container |
| `make health` | Quick liveness (containers + HTTP 200) |
| `make health-deep` | Full diagnostic (grade, latency, memory) |
| `make status` | ps + health-deep combined |
| `make backup` | pg_dump → backups/ |
| `make db-shell` | psql inside gula-postgres |
| `make redis-cli` | redis-cli (auto-reads password) |
| `make lint` | pyflakes + flake8 |
| `make test` | pytest tests/ -v |
| `make ci` | syntax-gate + lint + docker build |
| `make secrets-gen` | Generate strong random secrets |
| `make scale REPLICAS=5` | Scale backend behind HAProxy |

---

## 2. Runbooks for Common Scenarios

### 2.1 R01 — Container Not Starting

**Symptoms**: `docker ps` shows missing container; `make health` shows unhealthy.

**Steps**:
1. `docker logs gula-backend` — Check for error messages
2. `docker compose ps` — Verify all services listed
3. Check `.env` exists and all required vars are set
4. `docker compose logs gula-backend | grep ERROR` — Look for startup errors
5. Common fixes:
   - `DATABASE_URL` not set → Add to `.env`
   - Port conflict → Check `docker compose port` mappings
   - Migration error → `docker compose run --rm gula-backend alembic upgrade head`
6. `docker compose restart gula-backend` — Retry startup
7. If persists: `docker compose down && docker compose up -d`

### 2.2 R02 — Database Connection Failure

**Symptoms**: Backend logs show "could not connect to PostgreSQL"; `/health/deep` shows DB status RED.

**Steps**:
1. `docker compose logs gula-postgres | tail -50` — Check Postgres logs
2. `docker compose exec gula-postgres pg_isready` — Test Postgres health
3. `docker compose restart gula-postgres` — Restart if unresponsive
4. Check disk space: `docker compose exec gula-postgres df -h`
5. Check connection count: `docker compose exec gula-postgres psql -c "SELECT count(*) FROM pg_stat_activity;"`
6. If pool exhausted: `SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE state = 'idle';`
7. Circuit breaker auto-opens — wait 30s for recovery
8. If persistent: failover to standby (see DR plan)

### 2.3 R03 — Redis Failure

**Symptoms**: Rate limiting stops working; session errors; `cache.*` errors in logs.

**Steps**:
1. `docker compose logs gula-redis | tail -50` — Check Redis logs
2. `make redis-cli PING` — Should return PONG
3. `docker compose restart gula-redis` — Restart
4. Check `REDIS_URL` in `.env` — Verify host, port, password
5. If Redis is down: auth still works (JWT validation does not need Redis)
6. Rate limiting degrades gracefully — no false blocking
7. Cache miss rate increases but system remains functional

### 2.4 R04 — High Memory / OOM

**Symptoms**: Container exits with code 137; slow response times; swap usage.

**Steps**:
1. `make health-deep` — Check memory stats per container
2. `docker stats` — Real-time resource usage
3. Check `MAX_CONCURRENT_REQUESTS` setting in config
4. Adaptive concurrency should auto-reduce — verify in logs
5. If worker memory > 512MB: reduce `WEB_CONCURRENCY`
6. Restart the backend container to free memory
7. Monitor GC pressure: `auto_repair.py` should handle this
8. If recurring: increase container memory limit in `docker-compose.yml`

### 2.5 R05 — Circuit Breaker Open

**Symptoms**: `/health/status` shows circuit OPEN for a service; partial 503 errors.

**Steps**:
1. `make health-deep` — Identify which circuit breaker is OPEN
2. Check the failing service (DB, Redis, AI, gateway)
3. Fix the root cause (e.g., restart failing database)
4. Recovery worker auto-probes every 30s — wait for auto-recovery
5. If urgent: restart backend to reset circuit breakers
6. After recovery: verify system is GREEN on next health check

### 2.6 R06 — Outbox Events Stuck

**Symptoms**: Outbox events stuck in "pending" status; downstream services not receiving updates.

**Steps**:
1. `make shell` — Enter backend container
2. `python -c "from app.models.outbox import OutboxEvent; print('Events pending:', db.query(OutboxEvent).filter(OutboxEvent.status == 'pending').count())"`
3. Check `OutboxWorker` is running: verify `FEATURE_BACKGROUND_TASKS=true` in `.env`
4. Check logs: `make logs-backend | grep outbox`
5. Manually trigger: `python -c "from app.services.outbox_service import OutboxWorker; await OutboxWorker.run_once()"`
6. If stuck on specific events: check `last_error` field for details
7. Dead letter queue auto-handles failed events after 5 attempts

### 2.7 R07 — Performance Degradation

**Symptoms**: High latency; P95 above 1s; alerting triggered.

**Steps**:
1. `make health-deep` — Check latency, memory, DB pool status
2. Check `RequestTimingMiddleware` logs for slow endpoints
3. Check DB query performance: slow queries in database logs
4. Common fixes:
   - Missing index → review query plan → add index (new migration)
   - Cache miss → warm cache or adjust TTL
   - Connection pool exhaustion → increase pool size
   - High concurrency → adaptive concurrency should auto-adjust
5. If AI or gateway calls are slow: circuit breaker should isolate
6. Alert ops team if degradation persists

### 2.8 R08 — Security Incident

**Symptoms**: Intrusion detection alert; unauthorized access detected; data breach suspected.

**Steps**:
1. **IMMEDIATE**: `make kill-switch-on` — Block all non-critical traffic
2. Triage: `make logs-backend | grep -i "security\|intrusion\|unauthorized"` 
3. Identify: Check audit logs for anomalous patterns
4. Contain: Revoke affected tokens via JWT blacklist
5. Investigate: Review access logs, audit trail, and application logs
6. Remediate: Deploy security fix (see emergency release process)
7. Recover: `make kill-switch-off` after verification
8. Post-mortem: Root cause analysis within 48h

---

## 3. Incident Response Procedures

### 3.1 Incident Classification

| Severity | Description | Response Time | Examples |
|----------|-------------|---------------|----------|
| **P0** | Critical — platform down, data loss, security breach | Immediate (15 min) | Complete outage, data corruption, breach |
| **P1** | High — major feature unavailable, degraded performance | 30 min | Orders not processing, sync broken |
| **P2** | Medium — non-critical feature unavailable | 2 hours | Reporting slow, UI issue |
| **P3** | Low — cosmetic issue, minor annoyance | 1 week | Typo in UI, minor optimization |
| **P4** | Info — monitoring, enhancement | Next sprint | Feature request, tech debt |

### 3.2 Incident Response Flow

```
Incident Reported (alert / user report / monitoring)
    ↓
1. Triage (5 min) — Assess severity, declare incident, notify team
2. Contain (15 min) — Stop the bleeding (kill switch, traffic diversion)
3. Diagnose (30 min) — Root cause analysis
4. Fix (1 hour) — Implement and deploy fix
5. Verify (30 min) — Confirm fix, monitoring stable
6. Post-mortem (48h) — Incident report, action items
```

### 3.3 Communication

| Channel | Who | When |
|---------|-----|------|
| Incident Slack/Discord | All responders | Immediate |
| Status page | All users | P0/P1 declared |
| Management update | Product owner | Every 30 min during P0 |
| Telegram alert | On-call engineer | Monitoring system |
| Post-incident report | Engineering team | 48h post-resolution |

---

## 4. Backup and Restore Procedures

### 4.1 Backup Strategy

| Component | Method | Frequency | Retention | Location |
|-----------|--------|-----------|-----------|----------|
| PostgreSQL | `pg_dump` via `make backup` | Daily | 30 days (daily) + 12 months (monthly) | `./backups/` + cloud storage |
| PostgreSQL (WAL) | WAL archiving (if enabled) | Continuous | 7 days | Cloud storage |
| Redis | RDB snapshots | Every 15 min | 24 hours | Docker volume |
| Configuration | `.env.production` + `docker-compose.yml` | Per change | Git history | Repository |
| Uploaded files | Object storage (Cloudflare R2) | Mirror | Same as source | Cloudflare R2 |

### 4.2 Backup Commands

```bash
# Full database backup
make backup  # Creates ./backups/gula_YYYYMMDD_HHMMSS.sql.gz

# Manual backup
docker compose exec gula-postgres pg_dump -U gula -d gula | gzip > backups/gula_$(date +%Y%m%d).sql.gz

# WAL archiving (production)
# Configure postgresql.conf: archive_mode = on, archive_command = ...
```

### 4.3 Restore Procedure

```bash
# Step 1: Stop the application
docker compose down gula-backend

# Step 2: Restore database (destroys existing data)
gunzip -c backups/gula_20260714.sql.gz | docker compose exec -T gula-postgres psql -U gula -d gula

# Step 3: Restart the application
docker compose up -d

# Step 4: Run pending migrations
docker compose run --rm gula-backend alembic upgrade head

# Step 5: Verify
make health-deep
```

### 4.4 Recovery Testing

- Monthly restore drill: Restore backup to staging environment and verify data integrity
- Quarterly DR test: Simulate complete region failure, restore to alternate location

---

## 5. Disaster Recovery Plans

### 5.1 Disaster Scenarios

| Scenario | RTO | RPO | Strategy |
|----------|-----|-----|----------|
| Database corruption | 30 min | 24h | Restore from backup |
| Application failure | 15 min | N/A | Restart container / scale |
| Region failure | 4 hours | 24h | Deploy to alternate region |
| Cloud provider outage | 4 hours | 24h | Failover to alternate provider |
| Data center fire | 24 hours | 24h | Full restore from cloud backup |
| Ransomware / crypto | 4 hours | 24h | Immutable backup restore |

### 5.2 High Availability Architecture

```
┌──────────────────────────────────────────────────────────┐
│                   Primary Region                          │
│  ┌──────────┐   ┌──────────┐   ┌───────────────────────┐ │
│  │ HAProxy  │──▶│ Backend  │──▶│ PostgreSQL + Redis     │ │
│  │ (:8080)  │   │ Replicas │   │ (Primary)              │ │
│  └──────────┘   └──────────┘   └───────────────────────┘ │
└──────────────────────────────────────────────────────────┘
                                │
                                │ WAL streaming / async replication
                                ▼
┌──────────────────────────────────────────────────────────┐
│                   Standby Region                          │
│  ┌──────────┐   ┌──────────┐   ┌───────────────────────┐ │
│  │ HAProxy  │──▶│ Backend  │──▶│ PostgreSQL (Standby)   │ │
│  │ (:8080)  │   │ Replicas │   │ + Redis (Replica)      │ │
│  └──────────┘   └──────────┘   └───────────────────────┘ │
└──────────────────────────────────────────────────────────┘
```

### 5.3 DR Procedure

```
1. Primary failure detected → Monitoring alerts on-call
2. Assess impact → P0 declared if full region failure
3. Promote standby → Flip DNS to standby region
4. Scale standby → Increase replica count to handle load
5. Verify → Full health check + integrity test
6. Monitor → Watch for issues during failover
7. Post-recovery → Fail back to primary when available
```

---

## 6. Monitoring Dashboards

### 6.1 Grafana Dashboards

| Dashboard | Panels | Data Source | File |
|-----------|--------|-------------|------|
| **Platform Overview** | Uptime, latency, error rate, request rate | Prometheus | `config/grafana/platform-overview.json` |
| **Database** | Connection pool, query latency, slow queries | Prometheus + PostgreSQL | `config/grafana/database.json` |
| **Redis** | Cache hit rate, memory usage, command rate | Prometheus | `config/grafana/redis.json` |
| **Health** | System grade, component status, circuit breaker | App health endpoint | `config/grafana/health.json` |
| **Business** | Orders/hour, results/hour, active labs | PostgreSQL | `config/grafana/business.json` |
| **Security** | Auth attempts, rate limit hits, audit volume | Prometheus | `config/grafana/security.json` |
| **Performance** | P50/P95/P99 latency, throughput, error budget | Prometheus | `config/grafana/performance.json` |

### 6.2 Key Metrics

All dashboards display at minimum:

| Metric | Source | Display |
|--------|--------|---------|
| Uptime | Health endpoint | Percentage + 9s |
| Request rate | RequestTimingMiddleware | req/s |
| Error rate | Middleware + Sentry | % of requests |
| Latency | RequestTimingMiddleware | P50/P95/P99 |
| DB pool usage | `database.py:get_pool_status()` | % utilized |
| Active requests | ConcurrencyLimitMiddleware | Count |
| Circuit breaker state | Self-healing | OPEN/CLOSED/HALF_OPEN |
| System grade | Health alert loop | GREEN/YELLOW/RED |

---

## 7. Alert Configurations

### 7.1 Alert Rules

| Rule | Condition | Severity | Notification |
|------|-----------|----------|-------------|
| **System RED** | Health grade = RED for > 5 minutes | P0 | Telegram + Slack + On-call |
| **System YELLOW** | Health grade = YELLOW for > 15 minutes | P1 | Telegram + Slack |
| **High latency** | P95 latency > 1s for > 5 minutes | P1 | Telegram + Slack |
| **Error rate spike** | Error rate > 5% for > 5 minutes | P1 | Telegram + Slack |
| **Circuit breaker OPEN** | Any circuit OPEN for > 2 minutes | P1 | Telegram + Slack |
| **DB pool exhaustion** | Pool utilization > 80% | P2 | Slack |
| **OOM** | Container OOM killed | P0 | Telegram + Slack |
| **Certificate expiry** | TLS cert expires in < 14 days | P2 | Email + Slack |
| **Backup failure** | Daily backup did not complete | P1 | Slack |
| **CVE detected** | Critical CVE in dependencies | P1 | Slack |

### 7.2 Alert Destinations

| Destination | P0 | P1 | P2 | P3 |
|-------------|----|----|----|----|
| Telegram (on-call) | ✅ Immediate | ✅ Immediate | ❌ | ❌ |
| Slack (#alerts) | ✅ | ✅ | ✅ | ❌ |
| Email (ops team) | ✅ | ✅ | ✅ | ✅ |
| SMS (on-call) | ✅ | ❌ | ❌ | ❌ |

### 7.3 Alert Configuration Files

- `config/prometheus/alerting-rules.yml` — Prometheus alert rules
- `backend/app/core/self_healing.py:_health_alert_loop` — Application-level alerting
- `ALERT_WEBHOOK_URL` env var — Telegram/Discord/Slack webhook

---

## 8. On-Call Schedules

### 8.1 Team Structure

| Role | Responsibility |
|------|----------------|
| **Primary On-Call** | First responder for all P0/P1 incidents |
| **Secondary On-Call** | Backup to primary, handles P2 escalations |
| **Backend Support** | Application-level debugging and fixes |
| **Database Support** | Database performance and recovery |
| **Security Support** | Security incidents and vulnerability response |

### 8.2 Schedule

- **Primary**: Rotating weekly, Mon-Mon
- **Secondary**: Rotating weekly, offset from primary
- **Major holidays**: Extended coverage with additional support

### 8.3 Availability Requirements

- Response time: 15 min for P0, 30 min for P1
- Coverage: 24/7/365
- Handoff: Weekly on Monday 09:00 UTC

---

## 9. Escalation Paths

### 9.1 Technical Escalation

```
Engineer (Primary On-Call)
    ↓ (unresolved after 30 min)
Senior Engineer (Secondary On-Call)
    ↓ (unresolved after 1 hour)
Tech Lead
    ↓ (unresolved after 2 hours)
Architecture Review Board
    ↓ (unresolved after 4 hours)
CTO / Engineering Director
```

### 9.2 Security Escalation

```
On-Call Engineer → Security Incident Triage
    ↓ (confirmed security incident)
Security Lead
    ↓ (breach confirmed)
Security Team + Legal Counsel
    ↓ (regulatory notification required)
CEO / Board
```

### 9.3 Clinical Safety Escalation

```
On-Call Engineer → Patient Safety Assessment
    ↓ (potential patient impact)
Clinical Safety Officer
    ↓ (confirmed clinical risk)
Medical Director
    ↓ (widespread impact)
Ministry of Health Liaison
```

### 9.4 Customer Escalation

```
Customer Support → Technical Support
    ↓ (unresolved)
Engineering Team
    ↓ (SLA breach)
Account Manager
    ↓ (critical account)
Product Owner / CEO
```

---

## Document Version History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-07-15 | Architecture Team | Initial master operations catalog |

**Review Cycle**: This document must be reviewed and updated quarterly or when operational procedures change.
