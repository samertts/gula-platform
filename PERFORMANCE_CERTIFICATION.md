# Performance Certification Report

**Date:** 2026-07-22

## Frontend Production Build

| Metric | Value |
|--------|-------|
| Build time | 1.42s |
| Modules transformed | 1,748 |
| Total chunks | 31 |
| Main bundle | 451.90 kB (142.60 kB gzip) |
| UI components | 88.86 kB (26.02 kB gzip) |
| CSS | 36.59 kB (7.47 kB gzip) |

## Code Splitting (All 29 Routes)

| Chunk | Size | Gzip |
|-------|------|------|
| DashboardPage | 2.21 kB | 0.89 kB |
| PatientsPage | 1.56 kB | 0.82 kB |
| OrdersPage | 1.70 kB | 0.88 kB |
| ResultsPage | 1.71 kB | 0.88 kB |
| SamplesPage | 1.56 kB | 0.88 kB |
| LabsPage | 1.54 kB | 0.83 kB |
| LoginPage | 1.82 kB | 0.88 kB |
| FhirPage | 20.22 kB | 4.32 kB |
| EhrPage | 10.70 kB | 2.94 kB |
| AiPlatformPage | 14.01 kB | 3.57 kB |
| HospitalPage | 13.86 kB | 3.39 kB |
| Other pages (19) | 1-7 kB | < 3 kB each |

## Optimization Features

| Feature | Status |
|---------|--------|
| Lazy loading (React.lazy) | ✅ All 29 routes |
| Suspense boundaries | ✅ Per-route |
| Tree shaking | ✅ Vite default |
| CSS minification | ✅ PostCSS |
| Image optimization | ✅ Vite asset pipeline |
| Font subsetting | ✅ Variable fonts |
| Bundle analysis | ✅ PERFORMANCE.md |

## Caching

| Layer | Strategy |
|-------|----------|
| Browser | `stale-while-revalidate` (health endpoints) |
| API | `no-store` (patient data) |
| React Query | 30s stale time, cache invalidation on mutations |
| Redis | Session cache, rate limit counters, JWT blacklist |

## Backend Performance

| Metric | Value |
|--------|-------|
| Workers | 3 (default), scalable to N |
| Concurrency | 50 req/worker (adaptive) |
| DB pool | 18 conn (3 × 6), scalable |
| Response time | <300ms normal, >300ms triggers concurrency throttle |

## Status: PASS ✅
