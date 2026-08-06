---
id: PERF-000001
type: performance
title: "Performance Knowledge Bridge"
version: "1.0"
created: "2026-08-04"
status: verified
confidence: 75%
tags: [performance, optimization, caching, bridge]
---

# Performance Knowledge — Bridge Reference

## Documentation
- `docs/performance/query-optimization-guide.md` — Query optimization

## Caching Strategy
- Redis for API responses (TTL-based)
- Redis for session data
- Redis for task queue
- Dashboard stats cached

## Database Performance
- Connection pooling (SQLAlchemy)
- Indexed queries on frequent filters
- UUID primary keys (indexed)
- Soft deletes (no hard deletes)

## Frontend Performance
- Lazy loading (React.lazy)
- Code splitting (Vite)
- Image optimization
- Bundle size monitoring

## Backend Performance
- Async FastAPI endpoints
- Background tasks (queue)
- MinIO for large objects (not DB)
- Rate limiting per role

## Monitoring
- `app/routes/metrics.py` — Prometheus + JSON metrics
- RSS memory tracking
- Database ping health checks
- Uptime monitoring

## Known Bottlenecks
- Auth test setup: 145s → 68s (optimized via SKILL-000006)
- Full test suite: 203s → 108s (optimized)
- mypy times out on full codebase (too many capabilities/ modules)

## Related
- `.ai/core/memory/PROJECT_MEMORY.md` — Performance decisions
- `docs/performance/` — Performance documentation
