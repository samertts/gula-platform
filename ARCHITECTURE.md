# GULA Platform — Architecture

## Deployment Architecture (Production)

```
Internet
    │
    ▼
┌──────────────────────────────────────────────────────┐
│  Host nginx (TLS termination)                        │
│  Certbot / Let's Encrypt                             │
└──────────────────────┬───────────────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────────────┐
│  api-gateway (Docker nginx on 127.0.0.1:8080)        │
│  Rate limiting: 100 req/min per IP                    │
│  Auth endpoint: 10 req/min                            │
│  Security headers (CSP, HSTS, X-Frame-Options)        │
└──────────────────────┬───────────────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────────────┐
│  gula-backend (FastAPI monolith)                     │
│  Gunicorn + Uvicorn workers (port 8000)              │
│                                                      │
│  ┌──────────────────────────────────────────────────┐│
│  │ Middleware Stack (order matters):                 ││
│  │ 1. MaxBodySizeMiddleware      (10 MB limit)      ││
│  │ 2. RequestIDMiddleware        (X-Request-ID)     ││
│  │ 3. DocsAuthMiddleware         (admin JWT guard)  ││
│  │ 4. CORSMiddleware                                 ││
│  │ 5. RequestTimingMiddleware    (X-Response-Time)  ││
│  │ 6. SecurityHeadersMiddleware  (CSP/HSTS/etc)     ││
│  │ 7. GZipMiddleware                                 ││
│  │ 8. ReadinessMiddleware        (503 until ready)  ││
│  │ 9. DegradedModeMiddleware     (circuit breaker)  ││
│  │ 10. KernelMiddleware          (kernel context)   ││
│  │ 11. ConcurrencyLimitMiddleware(backpressure)     ││
│  └──────────────────────────────────────────────────┘│
│                                                      │
│  ┌──────────────────────────────────────────────────┐│
│  │ Route Modules (36):                              ││
│  │ auth, labs, orders, results, samples, patients,  ││
│  │ stats, ai, compliance, patient_card, edge, ...   ││
│  └──────────────────────────────────────────────────┘│
└──────────────────────┬───────────────────────────────┘
                       │
          ┌────────────┼────────────┐
          ▼            ▼            ▼
   ┌────────────┐ ┌──────────┐ ┌──────────┐
   │ PostgreSQL │ │  Redis 7 │ │  Device  │
   │   16       │ │  Cache   │ │  Bridge  │
   │            │ │  Session │ │ (ASTM)   │
   │ SQLAlchemy │ │  RateLim │ │          │
   └────────────┘ └──────────┘ └──────────┘
```

## Key Architectural Decisions

### Monolith-First
The production deployment is a **FastAPI monolith** (`backend/app/`). All routes, models, and services live in a single deployable unit. A parallel microservices tree (`services/`) exists for future decomposition but is NOT the production target.

### Middleware Stack
Requests flow through 11 middleware layers in strict order. Each serves a specific purpose — never skip or reorder without understanding the dependency chain.

### Self-Healing System (3 Layers)
1. **Circuit Breaker** — isolates failing DB/Redis; flips to degraded mode
2. **Auto-Repair Engine** — GC, pool recycle, reconnects
3. **Adaptive Concurrency** — halves in-flight cap on slow DB readings

### Health Endpoints
| Path | Purpose |
|------|---------|
| `/health` | Liveness (process alive) |
| `/health/live` | Same as above |
| `/health/ready` | Readiness (Docker healthcheck) |
| `/health/status` | Diagnostics (explains WHY startup failed) |
| `/health/deep` | Grade + latencies + memory |

## Data Flow

```
Request → Auth JWT → RBAC → Route Handler → Service → DB/Redis/External API
                                                         │
                                                         ▼
                                                    Audit Log
                                                    (hash chain)
```

All patient-data queries MUST filter by `lab_id = current_user.lab_id` (tenant isolation).
All mutations MUST write to the audit log.

## Component Architecture (within monolith)

```
backend/app/
├── main.py              # App init, middleware, lifespan
├── config.py            # Env vars, secrets validation
├── database.py          # SQLAlchemy engine + pool
├── routes/              # 36 route modules
├── models/              # 17 SQLAlchemy ORM models
├── services/            # Business logic layer
├── core/                # Infrastructure (15 modules)
│   ├── self_healing.py  # Circuit breaker
│   ├── auto_repair.py   # Auto-repair engine
│   ├── startup_guard.py # System ready flag
│   └── ...
├── security/            # Auth, JWT, RBAC, rate limiting
├── kernel/              # Engineering kernel (DI, plugins, events)
├── notifications/       # Notification service
├── audit/               # Audit logging
├── financial/           # Financial Engine (Phase A schema only)
└── tasks/               # Background tasks (outbox pattern)
```
