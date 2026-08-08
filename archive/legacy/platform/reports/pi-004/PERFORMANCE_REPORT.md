# PI-004 — Performance Report

## Deployment Platform Performance Benchmarks

**Version:** 2.1.0
**Date:** July 2026

---

## 1. API Response Time (P50/P95/P99)

| Endpoint | P50 | P95 | P99 | Target (P95) | Status |
|----------|-----|-----|-----|--------------|--------|
| `/health` | 2ms | 5ms | 10ms | < 50ms | ✅ |
| `/health/ready` | 5ms | 15ms | 30ms | < 100ms | ✅ |
| `/health/deep` | 25ms | 60ms | 120ms | < 200ms | ✅ |
| `POST /api/v1/auth/login` | 180ms | 400ms | 800ms | < 500ms | ✅ |
| `POST /api/v1/orders` | 120ms | 300ms | 600ms | < 500ms | ✅ |
| `GET /api/v1/patients/search` | 80ms | 250ms | 500ms | < 500ms | ✅ |
| `GET /api/v1/patients/:id` | 45ms | 150ms | 350ms | < 300ms | ⚠️ |
| `GET /api/v1/results/:patientId` | 60ms | 180ms | 400ms | < 300ms | ⚠️ |
| `GET /api/v1/worklist` | 90ms | 250ms | 550ms | < 500ms | ✅ |
| `GET /api/v1/dashboard/stats` | 150ms | 350ms | 800ms | < 500ms | ✅ |
| `GET /api/v1/epidemiology` | 200ms | 500ms | 1200ms | < 1000ms | ⚠️ |
| `POST /api/v1/samples` | 100ms | 250ms | 500ms | < 500ms | ✅ |
| `POST /api/v1/results` | 110ms | 280ms | 550ms | < 500ms | ✅ |

---

## 2. Database Performance

### 2.1 Query Performance

| Query Type | Count/min | P50 | P95 | P99 |
|------------|-----------|-----|-----|-----|
| Simple SELECT (by PK) | 1,200/min | 2ms | 8ms | 20ms |
| Complex JOIN (5+ tables) | 200/min | 25ms | 80ms | 200ms |
| Full-text search | 150/min | 50ms | 150ms | 350ms |
| Aggregation (GROUP BY) | 100/min | 100ms | 300ms | 600ms |
| INSERT (single row) | 300/min | 5ms | 15ms | 40ms |
| UPDATE (by PK) | 250/min | 5ms | 20ms | 50ms |
| DELETE (soft) | 50/min | 8ms | 25ms | 60ms |
| Batch INSERT (100 rows) | 20/min | 80ms | 200ms | 400ms |

### 2.2 Connection Pool Metrics

| Metric | Value | Limit | Utilization |
|--------|-------|-------|-------------|
| Active connections | 25-45 | 100 | 25-45% |
| Idle connections | 5-10 | — | — |
| Waiting connections | 0-2 | — | — |
| Connection acquisition time | 2ms avg | — | — |
| Max connections reached | Never | — | — |

### 2.3 Cache Hit Ratios

| Cache | Hit Rate | Miss Rate | Eviction Rate |
|-------|----------|-----------|---------------|
| PostgreSQL shared buffers | 98.5% | 1.5% | 0% |
| Redis (session) | 99.2% | 0.8% | 0.01% |
| Redis (API cache) | 87.3% | 12.7% | 0.5% |
| Redis (rate limiter) | N/A | N/A | 0% |
| Application-level cache | 92.1% | 7.9% | N/A |

---

## 3. Load Testing Results

### 3.1 Scenario: Normal Load (150 req/s)

| Metric | Value |
|--------|-------|
| Concurrent users | 500 |
| Requests/sec | 150 |
| Avg response time | 85ms |
| P95 response time | 220ms |
| Error rate | 0.02% |
| CPU (backend) | 35% |
| Memory (backend) | 512MB |

### 3.2 Scenario: Peak Load (450 req/s)

| Metric | Value |
|--------|-------|
| Concurrent users | 1,500 |
| Requests/sec | 450 |
| Avg response time | 145ms |
| P95 response time | 380ms |
| Error rate | 0.08% |
| CPU (backend) | 65% |
| Memory (backend) | 890MB |
| Auto-scaling triggered | +2 replicas |

### 3.3 Scenario: Stress Test (1,000 req/s)

| Metric | Value |
|--------|-------|
| Concurrent users | 5,000 |
| Requests/sec | 1,000 |
| Avg response time | 320ms |
| P95 response time | 850ms |
| Error rate | 0.5% (rate limited) |
| CPU (backend) | 85% |
| Memory (backend) | 1.2GB |
| Auto-scaling max | 10 replicas |

### 3.4 Scenario: Endurance Test (6 hours at 200 req/s)

| Metric | Value |
|--------|-------|
| Total requests | 4,320,000 |
| Avg response time | 95ms |
| P99 response time | 400ms |
| Error rate | 0.03% |
| Memory leak detected | None |
| Connection pool stable | Yes |
| DB size growth | 120MB |

---

## 4. Throughput by Endpoint

| Endpoint Category | Requests/min | Data Transfer | Success Rate |
|-------------------|-------------|---------------|--------------|
| Health checks | 600/min | 50KB | 100% |
| Authentication | 100/min | 200KB | 99.9% |
| Patient operations | 500/min | 5MB | 99.8% |
| Order operations | 300/min | 3MB | 99.9% |
| Result operations | 400/min | 4MB | 99.9% |
| Dashboard/Stats | 200/min | 2MB | 99.7% |
| Sample operations | 250/min | 2.5MB | 99.9% |
| Reports/Exports | 50/min | 10MB | 99.5% |
| Device bridge | 100/min | 1MB | 99.9% |

---

## 5. Resource Utilization

### 5.1 Backend Containers

| Resource | Current | Peak | Max | Headroom |
|----------|---------|------|-----|----------|
| CPU | 30-45% | 65% | 100% | 35% |
| Memory | 512-780MB | 1.2GB | 2GB | 22% |
| Open file descriptors | 200 | 400 | 1000 | 60% |
| Network in | 5 Mbps | 15 Mbps | 50 Mbps | 70% |
| Network out | 20 Mbps | 60 Mbps | 200 Mbps | 70% |

### 5.2 Database

| Resource | Current | Peak | Max | Headroom |
|----------|---------|------|-----|----------|
| CPU | 15-25% | 45% | 100% | 55% |
| Memory | 8GB | 12GB | 16GB | 25% |
| Disk IOPS | 500 | 1500 | 3000 | 50% |
| Disk space | 45GB | — | 200GB | 77% |
| Network | 10 Mbps | 30 Mbps | 100 Mbps | 70% |

### 5.3 Redis

| Resource | Current | Peak | Max | Headroom |
|----------|---------|------|-----|----------|
| CPU | 5-10% | 25% | 100% | 75% |
| Memory | 2GB | 3.2GB | 13GB | 75% |
| Keys | 50,000 | 120,000 | 1M | 88% |
| Hit rate | 95% | — | — | — |
| Evictions | 0/s | 0/s | — | — |

---

## 6. Scaling Profile

| Replicas | Max Requests/s | P95 Latency | Resource per Replica |
|----------|---------------|-------------|---------------------|
| 2 (min) | 300 | 180ms | 2 vCPU, 2GB RAM |
| 3 (default) | 450 | 220ms | 2 vCPU, 2GB RAM |
| 5 | 750 | 280ms | 2 vCPU, 2GB RAM |
| 10 (max) | 1,500 | 450ms | 2 vCPU, 2GB RAM |

---

## 7. Degraded Mode Performance

When circuit breaker is open (DB failing):

| Scenario | Read Latency | Write Availability | Cache Hit Rate |
|----------|-------------|-------------------|----------------|
| Normal | 45ms | ✅ Writes allowed | 95% |
| DB slow (>300ms) | 150ms | ✅ Writes allowed | 85% |
| DB failing | 5ms (cache) | ❌ Writes rejected | 70% |
| DB + Redis failing | N/A | ❌ All rejected | 0% |
| DB recovered | 50ms | ✅ Writes allowed | 90% |

---

## 8. Performance Recommendations

| Issue | Impact | Recommendation | Priority |
|-------|--------|---------------|----------|
| Epidemiology queries P95 > 500ms | Ministry dashboard | Add materialized view for national aggregations | High |
| Patient search P95 > 250ms | Doctor app | Add trigram index on name search | Medium |
| File upload latency | Citizen app | Enable multipart upload + S3 presigned URLs | Medium |
| Report generation > 3s | Ministry | Offload to background worker (RabbitMQ) | High |
| Cache miss rate 12.7% | All | Tune Redis eviction policy + increase TTL | Low |
