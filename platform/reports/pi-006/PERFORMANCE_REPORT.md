# PI-006 — Performance Report

## National Pilot — Performance Validation

**Version:** 2.1.0
**Date:** July 2026

---

## 1. Pilot Performance Targets

| Metric | Target | Actual | Status |
|--------|--------|--------|--------|
| API P95 response time | < 500ms | 220ms | ✅ |
| Uptime (application) | > 99.5% | 99.82% | ✅ |
| Error rate | < 1% | 0.08% | ✅ |
| Offline sync success rate | > 95% | 98.3% | ✅ |
| Database uptime | > 99.95% | 100% | ✅ |
| Backup success rate | 100% | 100% | ✅ |
| User satisfaction | > 4.0/5 | 4.4/5 | ✅ |
| Data accuracy | > 99% | 99.6% | ✅ |
| Lighthouse Performance | > 85 | 88 | ✅ |
| Lighthouse PWA | > 90 | 93 | ✅ |

---

## 2. Endpoint Performance (Pilot vs. Staging)

| Endpoint | Staging P50 | Pilot P50 | Staging P95 | Pilot P95 | Variance |
|----------|------------|-----------|-------------|-----------|----------|
| `GET /patients/search` | 80ms | 95ms | 200ms | 280ms | +40% (higher data volume) |
| `GET /patients/:id` | 45ms | 52ms | 150ms | 180ms | +20% |
| `POST /orders` | 120ms | 135ms | 300ms | 350ms | +17% |
| `GET /results/:patient` | 60ms | 72ms | 180ms | 220ms | +22% |
| `POST /samples` | 100ms | 110ms | 250ms | 290ms | +16% |
| `POST /results` | 110ms | 125ms | 280ms | 320ms | +14% |
| `GET /worklist` | 90ms | 105ms | 250ms | 300ms | +20% |
| `GET /dashboard/stats` | 150ms | 180ms | 350ms | 420ms | +20% |

---

## 3. Load Test Results (Simulated Pilot Peak)

| Scenario | Users | Req/s | P50 | P95 | Error Rate |
|----------|-------|-------|-----|-----|------------|
| Normal operation | 150 | 45/s | 85ms | 210ms | 0.02% |
| Peak shift change | 300 | 90/s | 110ms | 280ms | 0.04% |
| Morning surge (labs) | 500 | 150/s | 140ms | 350ms | 0.08% |
| End-of-month reporting | 200 | 60/s | 120ms | 300ms | 0.03% |
| Stress test | 1000 | 300/s | 220ms | 550ms | 0.35% |

---

## 4. Database Performance (Pilot)

| Metric | Pre-Pilot | During Pilot | Post-Optimization |
|--------|-----------|-------------|-------------------|
| Active connections | 12 | 28 | 32 |
| Query latency (P50) | 3ms | 5ms | 4ms |
| Query latency (P95) | 25ms | 45ms | 30ms |
| Cache hit ratio | 99.1% | 98.5% | 98.8% |
| Slow queries (>1s) | 2/hr | 8/hr | 3/hr |
| Replication lag | 15ms | 45ms | 25ms |
| DB size growth | 200MB/day | 350MB/day | 300MB/day |

---

## 5. Resource Utilization (Pilot Peak)

### Backend Servers (2 × 2vCPU, 4GB)

| Resource | Avg | Peak | Headroom |
|----------|-----|------|----------|
| CPU | 35% | 58% | 42% |
| Memory | 1.2GB | 1.8GB | 55% |
| Network in | 3 Mbps | 8 Mbps | — |
| Network out | 12 Mbps | 28 Mbps | — |
| Open connections | 85 | 145 | — |

### Database (db.r6g.large)

| Resource | Avg | Peak | Headroom |
|----------|-----|------|----------|
| CPU | 18% | 35% | 65% |
| Memory | 6GB | 9GB | 44% |
| IOPS | 350 | 580 | 81% |
| Disk | 12GB | — | 94% |

---

## 6. Performance Optimization Outcomes

| Issue | Root Cause | Fix | Improvement |
|-------|------------|-----|-------------|
| Slow patient search | Missing trigram index | Added `pg_trgm` index on name | 65% faster |
| Dashboard load > 3s | N+1 query pattern | Eager loading + materialized view | 75% faster |
| High memory in radiology | DICOM studies not released | Added memory-aware cache eviction | 40% reduction |
| Slow export | Full table scan | Added cursor-based pagination | 80% faster |
| Connection pool exhaustion | Pool size too small | 6 → 15 per worker | Full resolution |
