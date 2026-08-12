# GULA Platform — Operations Guide v1.0

**Version:** 1.0
**Date:** 2026-07-15
**Status:** FINAL

---

## 1. Daily Operations

### Morning Checklist

- [ ] Check `/health` endpoint returns 200
- [ ] Check `/health/deep` — verify grade is GREEN
- [ ] Review Slack alerts from past 12 hours
- [ ] Check backup status (last successful + age)
- [ ] Monitor disk space on all volumes (`df -h`)
- [ ] Review container status (`docker compose ps`)
- [ ] Check database connections (`SELECT count(*) FROM pg_stat_activity`)
- [ ] Review error rate in Grafana
- [ ] Check queue depths in RabbitMQ

### Operational Commands

```bash
# Quick health check
curl -s https://api.gula.health/health
curl -s https://api.gula.health/health/deep | jq .

# Container status
docker compose ps

# Logs (last 5 minutes, errors only)
docker compose logs --since=5m --tail=100 gula-backend | grep -iE "error|critical|exception|traceback"

# Disk usage
df -h

# Database connection count
docker compose exec postgres psql -U gula -c "SELECT count(*) FROM pg_stat_activity;"

# Redis memory usage
docker compose exec redis redis-cli -a $REDIS_PASSWORD INFO memory | grep used_memory_human

# Queue depth
docker compose exec rabbitmq rabbitmqctl list_queues -p gula name messages consumers ready
```

### Alert Triage

| Alert | Severity | First Action | Escalate If |
|-------|----------|-------------|-------------|
| `BackendDown` | CRITICAL | Check backend logs | Not resolved in 2min |
| `ErrorRateSpike` | CRITICAL | Check recent rollouts | Lasts >5min |
| `HighLatency` | WARNING | Check slow queries | Lasts >30min |
| `DiskSpaceLow` | WARNING | Clean disk | <10% free |
| `DBConnHigh` | WARNING | Check pool config | >90% usage |
| `ReplicationLag` | WARNING | Check replica health | >60s lag |
| `CertExpiry` | WARNING | Renew certificate | <7 days |

---

## 2. Weekly Operations

### Weekly Checklist

- [ ] Review performance trends (Grafana: last 7 days)
- [ ] Check for CVEs in dependencies
  - `pip-audit -r backend/requirements.txt`
  - `npm audit --prefix frontend-v2`
- [ ] Rotate audit logs if needed
- [ ] Verify DR readiness (test failover procedure)
- [ ] Review error budget consumption
- [ ] Check TLS certificate expiry dates
- [ ] Review IAM audit logs for anomalies
- [ ] Analyze slow query log (`pg_stat_statements`)
- [ ] Verify monitoring and alerting are functioning
- [ ] Review backup integrity (test restore on staging)

### Weekly Commands

```bash
# Dependency audit
pip-audit -r backend/requirements.txt
npm audit --prefix frontend-v2

# Certificate check
openssl s_client -connect api.gula.health:443 -servername api.gula.health </dev/null 2>/dev/null | openssl x509 -noout -enddate

# Slow query analysis
docker compose exec postgres psql -U gula -c "
SELECT query,
       calls,
       mean_exec_time,
       rows,
       shared_blks_hit::float / (shared_blks_hit + shared_blks_read)::float AS cache_hit_ratio
FROM pg_stat_statements
WHERE calls > 100
ORDER BY mean_exec_time DESC LIMIT 20;"

# Backup integrity check
ls -la /backups/
./scripts/backup-verification.sh --latest

# Performance trends (Grafana API)
curl -s -H "Authorization: Bearer $GRAFANA_TOKEN" \
  "https://grafana.gula.internal/api/dashboards/uid/platform-overview"
```

---

## 3. Monthly Operations

### Monthly Checklist

- [ ] Capacity review (resource usage trends)
- [ ] Performance benchmarking (compare to baseline)
- [ ] Security review (vulnerability scan results)
- [ ] Dependency updates (minor/patch versions)
- [ ] Audit log review and archive
- [ ] Review and update incident response procedures
- [ ] Test backup restoration on staging environment
- [ ] Review cost analysis and optimize
- [ ] Update runbooks for any new findings
- [ ] Team training / knowledge sharing session

### Monthly Capacity Review

```bash
# CPU usage analysis (last 30 days in PromQL)
avg(rate(container_cpu_usage_seconds_total{container="gula-backend"}[5m])) by (pod)

# Memory trend
avg(container_memory_usage_bytes{container="gula-backend"}) by (pod)

# Database growth
docker compose exec postgres psql -U gula -c "
SELECT pg_size_pretty(pg_database_size('gula')),
       pg_size_pretty(sum(pg_total_relation_size(relid))) as total_table_size,
       pg_size_pretty(sum(pg_indexes_size(relid))) as total_index_size
FROM pg_stat_user_tables;"

# Request growth rate
# Grafana: rate(http_requests_total[30d])
```

### Monthly Security Review

```bash
# SAST scan
bandit -r backend/app/ -f json | jq '.results | length'  # new findings count

# DAST scan (OWASP ZAP)
zap-cli quick-scan --self-contained \
  --spider https://api.staging.gula.health \
  --active-scan https://api.staging.gula.health

# Dependency scan
safety check -r backend/requirements.txt --json

# Secret scan
gitleaks detect --source . --verbose

# Container scan
trivy image ghcr.io/gula-platform/backend:latest

# IaC scan
checkov -d k8s/
```

### Monthly Performance Benchmark

Run k6 load test against staging:

```bash
# Install k6
brew install k6  # or apt/dnf

# Run normal load test
k6 run tests/load/normal.js \
  -e BASE_URL=https://api.staging.gula.health \
  --out json=reports/load-test-$(date +%Y%m%d).json

# Run peak load test
k6 run tests/load/peak.js \
  -e BASE_URL=https://api.staging.gula.health \
  --out json=reports/peak-test-$(date +%Y%m%d).json

# Compare with baseline
python3 scripts/compare-benchmarks.py \
  --baseline docs/reports/performance-report.md \
  --current reports/load-test-$(date +%Y%m%d).json
```

---

## 4. Quarterly Operations

### Quarterly Checklist

- [ ] Full disaster recovery test (failover to DR)
- [ ] Chaos engineering exercise
- [ ] Full security audit (external penetration test)
- [ ] Access review (all user accounts and permissions)
- [ ] Database performance tuning
- [ ] Cost optimization review
- [ ] Update architecture documentation
- [ ] Review and update SLAs/SLOs
- [ ] Capacity planning for next quarter
- [ ] Training / certification for operations team

### Disaster Recovery Test

See [Disaster Recovery Guide](DISASTER_RECOVERY_GUIDE.md) for full DR test procedure.

### Chaos Engineering

```bash
# Run chaos suite
make chaos

# Individual chaos scenarios
make chaos-db-failover
make chaos-cache-failover
make chaos-network-partition
make chaos-pod-kill
make chaos-cpu-stress
make chaos-memory-stress
```

### Quarterly Security Audit

```bash
# Full penetration test
# (Engage external pentesting firm — run quarterly)

# Internal security scan
python3 -m pytest tests/test_security.py -v

# Access review
docker compose exec postgres psql -U gula -c "
SELECT u.email, u.role, u.lab_id, u.last_login, u.is_active
FROM lab_users u
ORDER BY u.last_login DESC NULLS LAST;"

# Audit log review
docker compose exec postgres psql -U gula -c "
SELECT action, actor_id, resource_type, resource_id, created_at
FROM audit_logs
WHERE created_at > NOW() - INTERVAL '7 days'
ORDER BY created_at DESC
LIMIT 100;"
```

---

## 5. Dashboard Interpretation

### Platform Overview Dashboard

| Panel | What to Look For | Good | Warning | Critical |
|-------|-----------------|------|---------|----------|
| Request Rate | Sudden drop/growth | Stable trend | >2x normal | >5x normal |
| Error Rate | Spike in 5xx | <0.1% | >0.5% | >2% |
| Latency (p50/p95/p99) | Increasing trend | <50/200/500ms | >100/300/700ms | >200/500/1000ms |
| Active Users | Normal pattern | Daily pattern | Abnormal pattern | No traffic |
| Health Grade | GREEN | GREEN | YELLOW | RED |

### Database Dashboard

| Panel | What to Look For | Good | Warning | Critical |
|-------|-----------------|------|---------|----------|
| Connection Count | Spikes or steady growth | Within pool limit | >80% of max | >95% of max |
| Query Latency | Slow query identification | p95 < 100ms | p95 > 200ms | p95 > 500ms |
| Cache Hit Ratio | % of queries served from cache | >99% | >95% | <90% |
| Replication Lag | Growing lag | <1s | >5s | >30s |
| Disk I/O | Read/write throughput | <50% device max | >70% | >90% |
| Deadlocks | Should be 0 | 0 | >0 in 5min | Consistent >0 |

### Redis Dashboard

| Panel | What to Look For | Good | Warning | Critical |
|-------|-----------------|------|---------|----------|
| Memory Usage | Growth trend | <70% | >80% | >90% |
| Hit Rate | % of requests served | >99% | >95% | <90% |
| Evictions | Should be 0 | 0 | >0 | >100/s |
| Connected Clients | Stable | Normal level | >80% of max | >95% of max |
| Command Latency | Fast responses | <1ms avg | >5ms avg | >10ms avg |

### RabbitMQ Dashboard

| Panel | What to Look For | Good | Warning | Critical |
|-------|-----------------|------|---------|----------|
| Queue Depth | Trend (should drain) | Close to 0 | Growing >1000 | Growing >10000 |
| Message Rate | Input vs output | Balanced | Input > output for 10min | Input > output for 30min |
| Consumer Count | All queues have consumers | >0 per queue | 0 for any queue | 0 for durable queues |
| Unroutable Messages | Should be 0 | 0 | >0 | >100 |

### Kubernetes Dashboard

| Panel | What to Look For | Good | Warning | Critical |
|-------|-----------------|------|---------|----------|
| Pod Status | All running | All Running | CrashLoopBackOff | Pending/Available < min |
| Node CPU | Cluster load | <60% | >80% | >95% |
| Node Memory | Memory pressure | <70% | >85% | >95% |
| Restart Count | Should be low | <1/day | >3/day in 1h | >5/day |
| OOMKilled | Should be 0 | 0 | >0 | >3 in 1h |

---

## 6. Log Analysis Procedures

### Log Levels

| Level | Meaning | Action |
|-------|---------|--------|
| DEBUG | Detailed diagnostic info | Rarely used in production |
| INFO | Normal operations | Monitor for anomalies |
| WARNING | Potential issue | Investigate if recurring |
| ERROR | Operation failed | Investigate immediately |
| CRITICAL | System failure | Alert + immediate action |

### Common Log Patterns

#### Database Connection Errors

```
ERROR: gula-backend | database.py:123 | DB connection failed: could not connect to server
CRITICAL: gula-backend | self_healing.py:45 | Circuit breaker opened for postgres
```

**Action:**
1. Check if PostgreSQL is running
2. Check network connectivity
3. Check connection pool limits
4. Verify credentials in `.env`

#### Authentication Failures

```
WARNING: auth.py:234 | Failed login attempt for user 'unknown@lab.com' from IP 192.168.1.100
ERROR: auth.py:245 | Invalid JWT token: signature has expired
```

**Action:**
1. If repeated from same IP — rate limiting or block
2. If pattern of brute force — investigate security incident
3. Verify JWT secret hasn't been rotated without warning

#### Slow Queries

```
WARNING: database.py:89 | Slow query (1200ms): SELECT p.*, o.* FROM patients p
LEFT JOIN lab_orders o ON o.patient_id = p.id WHERE p.lab_id = 123
```

**Action:**
1. Run EXPLAIN ANALYZE on the query
2. Check for missing indexes
3. Consider adding composite indexes
4. Review if query optimization is possible

#### Out of Memory

```
CRITICAL: main.py:345 | Worker process terminated due to memory limit
ERROR: gunicorn:1 | Worker 3: memory use 2048MB exceeds limit 1024MB
```

**Action:**
1. Check for memory leaks
2. Increase memory limit
3. Add more workers to distribute load
4. Consider memory profiling

### Log Query Examples (Loki)

```logql
# All errors in last hour
{container="gula-backend"} |= "ERROR" |= `now()-1h`

# 5xx responses
{container="gula-backend"} |= "5[0-9][0-9]"

# Slow queries (>500ms)
{container="gula-backend"} |= "Slow query"

# Authentication failures
{container="gula-backend"} |= "Failed login"

# Circuit breaker events
{container="gula-backend"} |= "Circuit breaker"

# Requests from a specific path
{container="gula-backend"} |= "GET /api/patients"

# Group by error type
sum by (level) (count_over_time({container="gula-backend"} | regexp "^(?P<level>ERROR|WARNING|CRITICAL)" [$__interval]))
```

---

## 7. Backup Verification Procedures

### Daily Verification

```bash
# Check backup completion status
./scripts/backup-verification.sh --daily

# Verify backup file exists and is not empty
ls -la /backups/daily/
du -sh /backups/daily/latest.sql.gz

# Check last successful backup time
stat /backups/daily/latest.sql.gz
```

### Weekly Verification (Restore Test)

```bash
# Restore to staging database
./scripts/restore-test.sh --backup=/backups/daily/latest.sql.gz --target=staging

# Verify data integrity
python3 scripts/verify-restore.py --db-url=postgresql://user:pass@staging/gula

# Run integrity checks
docker compose exec postgres-staging psql -U gula -c "
SELECT count(*) FROM labs;
SELECT count(*) FROM patients;
SELECT count(*) FROM lab_orders;
SELECT count(*) FROM lab_results;
SELECT max(created_at) FROM audit_logs;"

# Compare row counts with production
python3 scripts/compare-row-counts.py --source=production --target=staging
```

### Monthly Verification (Full Recovery Test)

```bash
# Step 1: Spin up clean environment
docker compose -f docker-compose.dr-test.yml up -d

# Step 2: Restore from backup
gunzip -c /backups/monthly/gula_$(date +%Y%m01).sql.gz | \
  docker compose exec -T postgres-dr psql -U gula

# Step 3: Run migrations
docker compose run --rm gula-backend-dr alembic upgrade head

# Step 4: Run smoke tests
./scripts/smoke-test.sh --target dr

# Step 5: Run data integrity tests
python3 -m pytest tests/test_integrity.py -v --db-url=postgresql://user:pass@dr/gula

# Step 6: Verify PITR capability
./scripts/pitr-recover.sh --timestamp="2026-07-14 12:00:00 UTC" --target=dr-pitr
```

### Backup Failure Response

| Failure Type | Action | Priority |
|-------------|--------|----------|
| Backup not created today | Manual trigger: `make backup` | High |
| Backup file empty | Investigate DB/disk, re-run | High |
| Backup corrupted | Restore from previous, investigate | Critical |
| Backup storage full | Expand or rotate old backups | High |
| Verify failure | Investigate data integrity | Critical |

---

## 8. Routine Maintenance

### PostgreSQL Maintenance

```bash
# VACUUM (automatic, but check frequency)
docker compose exec postgres psql -U gula -c "SELECT relname, n_dead_tup, last_vacuum, last_autovacuum FROM pg_stat_user_tables;"

# REINDEX if needed
docker compose exec postgres psql -U gula -c "REINDEX INDEX CONCURRENTLY idx_patients_lab_id;"

# Update statistics
docker compose exec postgres psql -U gula -c "ANALYZE;"
```

### Log Rotation

```bash
# Docker log rotation (configured in docker-compose.yml)
# Verify current settings:
docker inspect gula-backend | jq '.[].HostConfig.LogConfig'

# Manual cleanup of old logs
docker compose logs --tail=0 gula-backend  # Truncate
```

### Cache Warm-up

```bash
# After Redis restart or deployment
# Cache is warmed automatically as queries are made
# To pre-warm critical data:
curl -X POST https://api.gula.health/admin/cache/warm \
  -H "Authorization: Bearer $GULA_ADMIN_TOKEN"
```

### SSL/TLS Certificate Renewal

```bash
# Automatic (certbot timer)
systemctl status certbot.timer

# Manual renewal
certbot renew --force-renewal
nginx -s reload

# Verify new certificate
openssl s_client -connect api.gula.health:443 -servername api.gula.health
```

---

## 9. Emergency Operations

### Emergency Shutdown

```bash
# Graceful shutdown
docker compose down --timeout 30

# Forceful shutdown (if unresponsive)
docker compose down --timeout 0

# Stop specific service
docker compose stop gula-backend
```

### Emergency Restart

```bash
# Restart single service
docker compose restart gula-backend

# Restart all services
docker compose restart

# Force recreate
docker compose up -d --force-recreate

# Full restart (rebuild images)
docker compose up -d --force-recreate --build
```

### Traffic Drain

```bash
# Remove backend from load balancer (HAProxy)
# Disable server in HAProxy config
echo "disable server gula-backend-servers/backend-1" | socat stdio /var/run/haproxy.sock

# Drain connections before maintenance
# (allow in-flight requests to complete, then shut down)
docker compose exec gula-backend kill -USR2 1  # Graceful shutdown
```
