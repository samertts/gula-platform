---
id: BACKEND-000001
type: backend
title: "Backend Knowledge Bridge"
version: "1.0"
created: "2026-08-04"
status: verified
confidence: 90%
tags: [backend, fastapi, python, services, bridge]
---

# Backend Knowledge — Bridge Reference

## Stack
- Python 3.12 + FastAPI
- SQLAlchemy (async)
- Alembic (migrations)
- pytest (testing)

## Structure
```
backend/
├── app/
│   ├── routes/         # Thin route handlers (7 services extracted)
│   ├── services/       # Business logic (10 services)
│   ├── models/         # SQLAlchemy models
│   ├── capabilities/   # Bounded contexts (10+)
│   ├── security/       # Auth, Redis, middleware
│   ├── tasks/          # Background task queue
│   └── factory.py      # App factory (106 routes)
├── tests/
│   ├── unit/           # 150 unit tests
│   ├── comprehensive/  # 103 integration tests
│   └── conftest.py     # Test fixtures
└── migrations/         # 50 Alembic migrations (281 tables)
```

## Service Extraction (71% route reduction)
| Service | Before | After | Reduction |
|---|---|---|---|
| lab_service | 312 | 94 | -70% |
| sample_service | 294 | 72 | -76% |
| admin_service | 1046 | 493 | -53% |
| quality_control | 416 | 97 | -77% |
| metrics_service | 400 | 29 | -93% |
| test_results | 735 | 138 | -81% |
| stats_service | 448 | 70 | -84% |

## Test Counts
- Unit: 150 tests (10 service files)
- Comprehensive: 103 tests
- Total: 399 tests, 0 failures

## Key Patterns
- Lazy Redis (_LazyCache) — no I/O at import time
- Lazy TaskQueue (_LazyTaskQueue) — no Redis at import time
- App factory pattern — `create_app()` works on SQLite
- Service layer — business logic extracted from routes

## Related
- `.ai/core/testing/README.md` — Test procedures
- `.ai/core/skills/SKILL-000003` — Fix pytest imports
- `.ai/core/skills/SKILL-000004` — Fix ruff naming
