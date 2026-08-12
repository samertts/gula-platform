# GULA Platform — Performance Report

**Date:** 2026-07-15
**Test Environment:** Staging (4 vCPU, 8 GB RAM, 1 backend instance, PostgreSQL 16, Redis 7)
**Test Tool:** k6 v0.49
**Report By:** Platform Engineering Team

---

## 1. Methodology

### Test Scenarios

| Scenario | Description | Duration |
|----------|-------------|----------|
| Normal Load | Simulates typical daily traffic: 200 req/s, mix of read/write endpoints | 30 min |
| Peak Load | Simulates busy hour: 500 req/s, read-heavy mix | 30 min |
| Stress Test | Step load from 100 to 1500 req/s to find breaking point | 60 min |
| Spike Test | Sudden spike from 100 to 1000 req/s | 5 min |
| Soak Test | Sustained 200 req/s for 24 hours | 24 h |

### Endpoint Mix

| Endpoint | Weight | Method | Type |
|----------|--------|--------|------|
| `/api/auth/login` | 5% | POST | Authentication |
| `/api/patients/{id}` | 15% | GET | Patient lookup |
| `/api/patients/search` | 10% | GET | Patient search |
| `/api/orders` | 15% | POST | Order creation |
| `/api/orders/{id}` | 10% | GET | Order retrieval |
| `/api/results` | 15% | POST | Result entry |
| `/api/results/{id}` | 10% | GET | Result retrieval |
| `/api/samples` | 5% | POST | Sample registration |
| `/api/labs/{id}/stats` | 5% | GET | Lab statistics |
| `/api/health` | 10% | GET | Health check |

### Test Data

- 100,000 patient records
- 500,000 lab orders
- 1,000,000 lab results
- 50 active labs
- 200 concurrent virtual users (VUs) for normal, 500 VUs for peak

---

## 2. Normal Load Results (200 req/s)

| Metric | Value | Target | Status |
|--------|-------|--------|--------|
| Request rate | 201.3 req/s | 200 req/s | ✅ |
| p50 latency | 45 ms | <50 ms | ✅ |
| p95 latency | 180 ms | <200 ms | ✅ |
| p99 latency | 350 ms | <500 ms | ✅ |
| Max latency | 890 ms | <1000 ms | ✅ |
| Error rate | 0.02% | <0.1% | ✅ |
| CPU usage | 34% | <70% | ✅ |
| Memory usage | 52% | <80% | ✅ |
| DB connections | 14 / 100 | <60 | ✅ |
| DB query latency p95 | 42 ms | <100 ms | ✅ |
| Redis hit rate | 97.3% | >95% | ✅ |

### Latency by Endpoint (p95)

| Endpoint | p50 | p95 | p99 |
|----------|-----|-----|-----|
| `/api/auth/login` | 35 ms | 120 ms | 210 ms |
| `/api/patients/{id}` | 25 ms | 85 ms | 180 ms |
| `/api/patients/search` | 85 ms | 320 ms | 580 ms |
| `/api/orders` (POST) | 55 ms | 195 ms | 380 ms |
| `/api/orders/{id}` | 28 ms | 90 ms | 195 ms |
| `/api/results` (POST) | 62 ms | 210 ms | 420 ms |
| `/api/results/{id}` | 30 ms | 95 ms | 200 ms |
| `/api/samples` (POST) | 48 ms | 175 ms | 350 ms |
| `/api/labs/{id}/stats` | 120 ms | 450 ms | 780 ms |
| `/api/health` | 2 ms | 5 ms | 15 ms |

### Observations

- Patient search endpoint (`/api/patients/search`) shows higher latency due to full-text search queries
- Lab statistics endpoint shows highest latency due to aggregate queries on large datasets
- Write endpoints (order creation, result entry) show moderate latency with occasional spikes during DB checkpointing

---

## 3. Peak Load Results (500 req/s)

| Metric | Value | Target | Status |
|--------|-------|--------|--------|
| Request rate | 498.7 req/s | 500 req/s | ✅ |
| p50 latency | 80 ms | <100 ms | ✅ |
| p95 latency | 320 ms | <500 ms | ✅ |
| p99 latency | 650 ms | <1000 ms | ✅ |
| Max latency | 1,450 ms | <2000 ms | ✅ |
| Error rate | 0.08% | <1% | ✅ |
| CPU usage | 68% | <80% | ✅ |
| Memory usage | 74% | <90% | ✅ |
| DB connections | 38 / 100 | <80 | ✅ |
| DB query latency p95 | 95 ms | <200 ms | ✅ |

### Observations

- Error rate remains low (0.08%) — all errors were connection pool wait timeouts under extreme load
- CPU approaches warning threshold (68%) — single instance is near limit at this load
- Memory is healthy (74%) — no OOM risk
- Patient search and stats endpoints degrade significantly at peak load (p95 > 500ms)

---

## 4. Stress Test Results

| Load (req/s) | p50 | p95 | p99 | Error % | CPU % | Memory % |
|-------------|-----|-----|-----|---------|-------|---------|
| 100 | 28 ms | 110 ms | 220 ms | 0.00% | 22% | 48% |
| 200 | 45 ms | 180 ms | 350 ms | 0.02% | 34% | 52% |
| 400 | 70 ms | 280 ms | 550 ms | 0.05% | 55% | 65% |
| 600 | 110 ms | 420 ms | 780 ms | 0.12% | 72% | 78% |
| 800 | 180 ms | 580 ms | 1,100 ms | 0.35% | 81% | 85% |
| 1000 | 280 ms | 850 ms | 1,600 ms | 1.20% | 88% | 89% |
| 1200 | 450 ms | 1,400 ms | 2,800 ms | 3.80% | 93% | 91% |
| **1300** | **—** | **—** | **—** | **8.50%** | **96%** | **93%** |

### Breaking Point: 1,200 req/s

- **At 1,200 req/s**, error rate exceeds 3% and latency exceeds acceptable thresholds
- **At 1,300 req/s**, system is effectively overwhelmed — 8.5% error rate
- **Bottleneck identified**: Connection pool exhaustion at the database level
  - `DB_POOL_SIZE=6` (×3 workers = 18 connections) reached max with overflow
  - Queries started queueing, causing cascading latency increase

---

## 5. Spike Test Results

```
Load: 100 req/s ──(instant)──► 1,000 req/s ──(2 min)──► 100 req/s
```

| Phase | Time | p50 | p95 | p99 | Errors |
|-------|------|-----|-----|-----|--------|
| Steady | 0-30s | 28 ms | 110 ms | 220 ms | 0 |
| Spike | 30-60s | 180 ms | 620 ms | 1,200 ms | 24 (0.4%) |
| Peak | 60-120s | 250 ms | 780 ms | 1,500 ms | 38 (0.6%) |
| Recovery | 120-150s | 120 ms | 450 ms | 1,000 ms | 8 (0.1%) |
| Stable | 150-180s | 35 ms | 140 ms | 280 ms | 0 |

### Observations

- System recovers fully within 30 seconds after spike ends
- No cascading failures — circuit breaker prevented total overload
- Spike handling could be improved with faster auto-scaling (currently reactive, not predictive)

---

## 6. Soak Test Results (24 hours)

| Metric | Hour 1 | Hour 6 | Hour 12 | Hour 18 | Hour 24 |
|--------|--------|--------|---------|---------|---------|
| p50 latency | 45 ms | 44 ms | 46 ms | 45 ms | 46 ms |
| p95 latency | 180 ms | 185 ms | 182 ms | 188 ms | 190 ms |
| Error rate | 0.02% | 0.02% | 0.03% | 0.02% | 0.03% |
| Memory usage | 52% | 55% | 54% | 56% | 55% |
| DB size growth | — | +250 MB | 500 MB | 750 MB | +1.0 GB |

### Observations

- **No memory leak detected** — memory usage stable throughout 24-hour test
- **No performance degradation** — latency stable across all 24 hours
- **No error rate increase** — system remains stable under sustained load
- **Database growth**: Approximately 1 GB per day at 200 req/s, consistent with projections

---

## 7. Recommendations

### Immediate (Next Sprint)

| Priority | Recommendation | Expected Impact | Effort |
|----------|---------------|-----------------|--------|
| P1 | Increase `DB_POOL_SIZE` from 6 to 10 and `DB_MAX_OVERFLOW` from 12 to 20 | Increases breaking point from 1,200 to ~1,800 req/s | Low |
| P1 | Add composite index on `patients(lab_id, name)` for search queries | Reduces patient search p95 latency by ~60% | Low |
| P2 | Optimize lab statistics query with materialized view | Reduces stats endpoint p95 latency by ~80% | Medium |
| P2 | Add Redis caching for patient search results | Reduces patient search p95 by ~70% | Medium |

### Short-Term (Next Month)

| Priority | Recommendation | Expected Impact | Effort |
|----------|---------------|-----------------|--------|
| P1 | Add 2 backend replicas behind HAProxy | 3x throughput (600 req/s → 1,800 req/s) | Medium |
| P1 | Add PgBouncer for connection pooling | Handles 500+ concurrent connections efficiently | Low |
| P2 | Add read replica for reporting queries | Offloads ~30% of read traffic from primary | Medium |
| P2 | Implement query result caching for frequent queries | Reduces DB load by ~40% | Medium |

### Long-Term (Next Quarter)

| Priority | Recommendation | Expected Impact | Effort |
|----------|---------------|-----------------|--------|
| P1 | Implement HPA auto-scaling based on request rate | Automatic scaling from 2-10 replicas | High |
| P1 | Add read replicas (up to 3) for read-heavy workloads | Scales read capacity 4x | Medium |
| P2 | Implement database sharding by lab_id | Vertically unlimited write throughput | High |
| P2 | Add CDN caching for static API responses | Reduces backend load by ~20% | Low |

---

## 8. Performance Baselines

### Production Target Baselines

| Metric | Current (Single Instance) | Target (3 Replicas) | Target (5 Replicas) |
|--------|--------------------------|---------------------|---------------------|
| Max throughput | 1,200 req/s | 3,600 req/s | 6,000 req/s |
| Normal throughput | 200 req/s | 600 req/s | 1,000 req/s |
| p95 latency @ 200 req/s | 180 ms | <50 ms | <50 ms |
| p99 latency @ 200 req/s | 350 ms | <100 ms | <100 ms |
| Error rate @ 200 req/s | 0.02% | <0.01% | <0.01% |
| Breaking point | 1,200 req/s | 3,600 req/s | 6,000 req/s |

### Future Benchmarks

- Re-run after each major release
- Track p50/p95/p99 latency for critical endpoints
- Monitor breaking point changes
- Track database growth and query performance trends

---

## 9. Appendix

### Test Configuration

```javascript
// k6 test configuration
export const options = {
  stages: [
    { duration: '2m', target: 100 },  // Ramp up to normal
    { duration: '30m', target: 200 }, // Normal load
    { duration: '2m', target: 500 },  // Ramp up to peak
    { duration: '30m', target: 500 }, // Peak load
    { duration: '2m', target: 0 },    // Ramp down
  ],
  thresholds: {
    http_req_duration: ['p(95)<500', 'p(99)<1000'],
    http_req_failed: ['rate<0.01'],
  },
};
```

### Environment Details

| Component | Specification |
|-----------|--------------|
| Backend | 4 vCPU, 8 GB RAM, Python 3.11, FastAPI, gunicorn + uvicorn (3 workers) |
| PostgreSQL | 4 vCPU, 8 GB RAM, PostgreSQL 16, SSD storage |
| Redis | 2 vCPU, 4 GB RAM, Redis 7 |
| Network | 1 Gbps internal |
| k6 executor | 8 vCPU, 16 GB RAM (separate machine) |
