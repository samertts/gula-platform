---
id: RUNBOOK-000004
type: runbook
title: "High Latency Investigation"
version: "1.0"
created: "2026-08-04"
status: verified
confidence: 90%
tags: [performance, latency, investigation, monitoring]
source: docs/runbooks/high-latency.md
---

# RUNBOOK-000004: High Latency Investigation

**Severity:** SEV2
**Response Time:** <30 minutes
**Source:** `docs/runbooks/high-latency.md`

## Quick Diagnosis
```bash
# 1. Check response times
curl -w "time_total: %{time_total}s\n" -o /dev/null -s http://localhost:8000/health

# 2. Check Docker stats
docker stats --no-stream

# 3. Check database slow queries
docker compose exec postgres psql -U gula -c "SELECT pid, now() - pg_stat_activity.query_start AS duration, query FROM pg_stat_activity WHERE state != 'idle' AND now() - pg_stat_activity.query_start > interval '5 seconds';"
```

## Common Causes
1. Database slow queries (missing indexes)
2. Redis connection pool exhausted
3. Memory pressure (OOM)
4. Network latency
5. Cold start (first request)

## Resolution Steps

### Step 1: Identify bottleneck
```bash
# Check which tier is slow
# Frontend: curl frontend
# Backend: curl backend directly
# Database: pg_isready + slow query check
```

### Step 2: Database optimization
```bash
# Check indexes
docker compose exec postgres psql -U gula -d gula -c "\di+"

# Analyze slow query
EXPLAIN ANALYZE <query>;
```

### Step 3: Cache check
```bash
# Redis hit rate
docker compose exec redis redis-cli INFO stats | grep -i "keyspace_hits\|keyspace_misses"
```

## Full Reference
See `docs/runbooks/high-latency.md` for complete runbook.
