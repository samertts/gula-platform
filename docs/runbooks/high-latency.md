# Runbook: High Latency

**Severity:** SEV2 (SEV1 if sustained >1h)
**Response Time:** <30 minutes
**Last Updated:** 2026-07-15

---

## Symptoms

- API response time p95 > 500ms (alert threshold)
- API response time p99 > 1s (alert threshold)
- Users report system feels slow
- Grafana latency panels show elevated values
- `/health/deep` shows increased component latencies
- Nginx upstream response time increases

## Quick Checks

```bash
# 1. Check current latency (from /health/deep)
curl -s http://localhost:8000/health/deep | jq '.latency'

# 2. Check slow queries in PostgreSQL
docker compose exec postgres psql -U gula -c "
SELECT query, calls, mean_exec_time, rows, shared_blks_hit::float / NULLIF(shared_blks_hit + shared_blks_read, 0)::float AS hit_ratio
FROM pg_stat_statements
ORDER BY mean_exec_time DESC LIMIT 10;"

# 3. Check connection count
docker compose exec postgres psql -U gula -c "
SELECT count(*) as connections,
       count(*) FILTER (WHERE state = 'active') as active,
       count(*) FILTER (WHERE wait_event IS NOT NULL) as waiting
FROM pg_stat_activity;"

# 4. Check Redis latency
docker compose exec redis redis-cli -a $REDIS_PASSWORD --latency -h redis

# 5. Check system resources
top -bn1 | head -20
free -h
df -h
```

## Possible Causes & Fixes

### Cause 1: N+1 Database Queries

**Symptoms:** High number of database queries per request, many similar queries in slow log

**Check:**
```bash
# Look for repeated similar queries
docker compose exec postgres psql -U gula -c "
SELECT query, calls
FROM pg_stat_statements
WHERE query ~ 'LEFT JOIN\|SELECT.*FROM'
ORDER BY calls DESC LIMIT 20;"
```

**Fix:**
```python
# Add eager loading / joins in Python code
# Before (N+1):
orders = session.query(Order).filter_by(lab_id=lab_id).all()
for order in orders:
    print(order.patient.name)  # Each access queries DB

# After (eager):
orders = session.query(Order).options(
    joinedload(Order.patient)
).filter_by(lab_id=lab_id).all()
for order in orders:
    print(order.patient.name)  # No extra query
```

### Cause 2: Missing Database Index

**Symptoms:** Sequential scans on large tables, high `shared_blks_read`

**Check:**
```bash
# Find sequential scans
docker compose exec postgres psql -U gula -c "
SELECT relname, seq_scan, seq_tup_read, idx_scan
FROM pg_stat_user_tables
ORDER BY seq_tup_read DESC LIMIT 20;"

# Find queries doing full table scans
docker compose exec postgres psql -U gula -c "
SELECT query, calls, rows, total_exec_time
FROM pg_stat_statements
WHERE query ~ 'WHERE'
ORDER BY total_exec_time DESC LIMIT 10;"
```

**Fix:**
```bash
# Create migration with index
docker compose run --rm gula-backend alembic revision --autogenerate -m "add_index_for_slow_query"

# Add index to migration file:
# op.create_index('idx_orders_lab_id_created', 'lab_orders', ['lab_id', 'created_at'])

# Run migration
docker compose run --rm gula-backend alembic upgrade head
```

### Cause 3: Connection Pool Exhaustion

**Symptoms:** Backend logs show connection wait timeouts, active connections near limit

**Check:**
```bash
docker compose exec postgres psql -U gula -c "
SELECT count(*) as total,
       count(*) FILTER (WHERE state = 'active') as active,
       count(*) FILTER (WHERE wait_event_type = 'Lock') as waiting_on_lock
FROM pg_stat_activity;"
```

**Fix:**

Option A: Increase pool size
```bash
# In .env:
DB_POOL_SIZE=10
DB_MAX_OVERFLOW=20

# Restart backend
docker compose up -d --no-deps gula-backend
```

Option B: Add PgBouncer
```yaml
# Add to docker-compose.yml
services:
  pgbouncer:
    image: edoburu/pgbouncer:1.21
    environment:
      DB_USER: ${POSTGRES_USER}
      DB_PASSWORD: ${POSTGRES_PASSWORD}
      DB_HOST: postgres
      DB_NAME: ${POSTGRES_DB}
      POOL_MODE: transaction
      MAX_CLIENT_CONN: 500
```

### Cause 4: Resource Contention

**Symptoms:** High CPU, memory pressure, disk I/O wait

**Check:**
```bash
# CPU and memory
top -bn1 | head -20

# Disk I/O
iostat -x 1 5

# Network I/O
nethogs
```

**Fix:**
```bash
# Option A: Scale up resources
docker compose up -d --scale gula-backend=3

# Option B: Increase CPU/memory limits
# docker-compose.override.yml
services:
  gula-backend:
    deploy:
      resources:
        limits:
          cpus: '4'
          memory: 8G

# Option C: Restart workers (releases memory)
docker compose exec gula-backend kill -HUP 1
```

### Cause 5: Slow External API Calls

**Symptoms:** High latency on specific endpoints, external service timeouts

**Check:**
```bash
# Look for external API calls in logs
docker compose logs --tail=100 gula-backend | grep -i "external\|timeout\|http.*call"
```

**Fix:**
```bash
# Add timeout and retry to external calls
# backend/app/services/external_api.py
import httpx

async with httpx.AsyncClient(timeout=5.0) as client:
    try:
        response = await client.get(url)
    except httpx.TimeoutException:
        # Fallback to cached data
        return get_cached_data()

# Add circuit breaker for external services
```

### Cause 6: Cache Miss

**Symptoms:** Redis hit rate drops, DB query rate increases, latency correlates with cache miss pattern

**Check:**
```bash
# Redis hit rate
docker compose exec redis redis-cli -a $REDIS_PASSWORD INFO stats | grep -i "hits\|misses"

# Calculate hit rate: hits / (hits + misses) * 100
```

**Fix:**
```bash
# Warm up cache
curl -X POST http://localhost:8000/admin/cache/warm \
  -H "Authorization: Bearer $GULA_ADMIN_TOKEN"

# Increase cache TTL for frequent queries
# Update cache configuration in backend/app/core/cache.py

# If Redis is memory constrained, increase maxmemory
docker compose exec redis redis-cli -a $REDIS_PASSWORD CONFIG SET maxmemory 4gb
```

## Resolution Verification

```bash
# 1. Check latency returned to baseline
curl -s http://localhost:8000/health/deep | jq '.latency'

# 2. Check p95 latency in Grafana (should be <200ms)
# Navigate to Platform Overview → Latency panel

# 3. Verify no slow queries remain
docker compose exec postgres psql -U gula -c "
SELECT count(*) FROM pg_stat_statements WHERE mean_exec_time > 1000;"

# 4. Check error rate (should be <0.1%)
docker compose logs --since=5m gula-backend | grep -c " 5[0-9][0-9] "

# 5. Run a quick performance test
curl -w "p95: %{time_total}s\n" -o /dev/null -s http://localhost:8000/api/health
```

## Escalation

| Time | Action |
|------|--------|
| 0 min | Begin diagnosis |
| 15 min | If cause not identified, escalate to secondary on-call |
| 30 min | If latency > 1s p95, escalate to Engineering Lead |
| 1h | If sustained, declare SEV1 incident |

## Prevention

- [ ] Monitor slow query log regularly
- [ ] Index review on new queries before deployment
- [ ] Performance regression tests in CI
- [ ] Connection pool monitoring alerts
- [ ] Regular cache hit rate review
- [ ] Auto-scaling configured for traffic spikes
