# GULA Platform — Architecture Map
**Date:** 2026-07-17

---

## 1. System Architecture Overview

```
                          ┌─────────────────────────────────────────┐
                          │           INTERNET (HTTPS)              │
                          └────────────────┬────────────────────────┘
                                           │ TLS 1.2/1.3
                                   ┌───────▼────────┐
                                   │  Host Nginx    │
                                   │  (SSL Term.)   │
                                   │  Rate Limit     │
                                   │  WAF (ModSec)  │
                                   └───────┬────────┘
                                           │
                                   ┌───────▼────────┐
                                   │  API Gateway    │
                                   │  (Docker Nginx) │
                                   │  127.0.0.1:8080 │
                                   └───┬────────┬────┘
                                       │        │
                          ┌────────────▼──┐  ┌──▼────────────┐
                          │  gula-backend │  │   Frontend    │
                          │  FastAPI:8000 │  │  Nginx:80     │
                          │  Gunicorn     │  │  (static)     │
                          │  Uvicorn      │  └───────────────┘
                          └───────┬───────┘
                                  │
                    ┌─────────────┼──────────────┐
                    │             │               │
            ┌───────▼──────┐ ┌───▼────┐  ┌──────▼────────┐
            │ PostgreSQL 16│ │ Redis 7│  │  Outbox →     │
            │ (Primary)    │ │(Cache, │  │  Event Bus    │
            │              │ │ Rate   │  │  (in-process) │
            │              │ │ Limit) │  └───────────────┘
            └──────────────┘ └────────┘
```

## 2. Request Lifecycle

```
Client Request
  → Host Nginx (SSL termination, rate limit 10r/s general, 30r/s API)
    → API Gateway Nginx (127.0.0.1:8080, rate limit 100r/min per IP)
      → MaxBodySizeMiddleware (413 >10MB)
        → RequestIDMiddleware (X-Request-ID UUID)
          → DocsAuthMiddleware (JWT-guard /docs in production)
            → CORSMiddleware
              → RequestTimingMiddleware (X-Response-Time)
                → SecurityHeadersMiddleware (CSP, HSTS)
                  → GZipMiddleware (>1KB)
                    → ReadinessMiddleware (503 until startup complete)
                      → DegradedModeMiddleware (L2=read-only, L3=critical-only)
                        → KernelMiddleware
                          → ConcurrencyLimitMiddleware (max 200, clinical exempt)
                            → Route Handler
                              → Auth Dependency (JWT decode + perm check)
                                → Permission Check (RBAC + ABAC + Feature Flag)
                                  → Business Logic (Service Layer)
                                    → DB Query (lab_id tenant filter)
                                      → Audit Log (hash chain)
                                        → Response
```

## 3. Component Dependency Map

```
┌──────────────────────────────────────────────────────────────────┐
│                    gula-backend (Monolith)                        │
│                                                                  │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────────┐ │
│  │  Routes  │→ │ Services │→ │  Models  │→ │   Database       │ │
│  │  (53+)   │  │  (34+)   │  │  (60+)   │  │  (250+ tables)   │ │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └──────────────────┘ │
│       │              │             │                              │
│       │         ┌────▼────┐  ┌────▼────┐                         │
│       │         │Security │  │  Core   │                         │
│       │         │(15 mods)│  │(15 mods)│                         │
│       │         └────┬────┘  └────┬────┘                         │
│       │              │             │                              │
│  ┌────▼──────────────▼─────────────▼────┐                        │
│  │         shared/ (Canonical Lib)      │                        │
│  │   auth, rbac, security, audit,       │                        │
│  │   circuit_breaker, messaging         │                        │
│  └──────────────────────────────────────┘                        │
│                                                                  │
│  External Dependencies: PostgreSQL, Redis, Ollama, Gemini, Groq  │
└──────────────────────────────────────────────────────────────────┘
```

## 4. Middleware Stack (11 layers, `main.py` lines 210-380)

| Order | Middleware | File | Purpose |
|-------|-----------|------|---------|
| 1 | `MaxBodySizeMiddleware` | `main.py` | Reject bodies >10MB (413) |
| 2 | `RequestIDMiddleware` | `main.py` | UUID per request + log context |
| 3 | `DocsAuthMiddleware` | `main.py` | JWT-guard /docs in production |
| 4 | `CORSMiddleware` | FastAPI | CORS from env var |
| 5 | `RequestTimingMiddleware` | `main.py` | Access log + latency header |
| 6 | `SecurityHeadersMiddleware` | `main.py` | CSP, HSTS, XFO, etc. |
| 7 | `GZipMiddleware` | FastAPI | Compress >1KB responses |
| 8 | `ReadinessMiddleware` | `main.py` | 503 until system_ready |
| 9 | `DegradedModeMiddleware` | `self_healing.py` | Circuit breaker enforcement |
| 10 | `KernelMiddleware` | `main.py` | Kernel context attachment |
| 11 | `ConcurrencyLimitMiddleware` | `main.py` | Backpressure (clinical exempt) |

## 5. Self-Healing Architecture (3 Layers)

```
                    ┌───────────────────────────┐
                    │  Health Alert Loop        │
                    │  (60s interval)           │
                    │  GREEN/YELLOW/RED scoring │
                    │  Webhook on transitions   │
                    └─────────────┬─────────────┘
                                  │
    ┌─────────────────────────────┼─────────────────────────────┐
    │                             │                             │
┌───▼──────────┐          ┌──────▼──────┐          ┌───────────▼───┐
│ Circuit      │          │ Auto-Repair │          │ Adaptive      │
│ Breaker      │          │ Engine      │          │ Concurrency   │
│              │          │             │          │               │
│ DB: 3 fails  │          │ Memory GC   │          │ Halves cap on │
│ Redis: 5     │          │ Pool Recycle│          │ 2 slow DB     │
│              │          │ Circuit     │          │ reads >300ms  │
│ L1 Cache     │          │ Probe       │          │ Restores on 3 │
│ L2 Read-only │          │ Redis       │          │ fast <150ms   │
│ L3 Critical  │          │ Reconnect   │          │               │
└──────────────┘          └─────────────┘          └───────────────┘
```

## 6. Health Endpoints

| Path | Purpose | Bypasses Middleware |
|------|---------|---------------------|
| `/health` | Liveness | All 3 guards |
| `/health/live` | Same | All 3 guards |
| `/health/ready` | Readiness (Docker) | All 3 guards |
| `/health/status` | Startup diagnostic | All 3 guards |
| `/health/deep` | Grade + latencies | All 3 guards |
| `/health/kernel` | Kernel health | All 3 guards |

## 7. Data Flow: Lab Result Ingestion

```
Lab Analyzer (Sysmex, Roche, Mindray)
  → ASTM Protocol (serial/TCP)
    → services/device_bridge/ (ASTM parser + adapter)
      → normalizer (vendor→canonical)
        → test mapper (code→test_type)
          → patient matcher (barcode/ID)
            → smart router (online/offline)
              → gula_client.py (HTTP POST)
                → backend/app/routes/device_results.py
                  → Auth + Validation
                    → LabResult model (optimistic lock)
                      → Audit log (hash chain)
                        → Clinical Engine (interpretation)
                          → Outbox event
                            → Notification (WhatsApp/SMS)
                              → Response
```

## 8. Authentication Flow

```
Login (POST /auth/login)
  → rate_limit_auth (10/min)
    → timing-safe verification (dummy bcrypt hash)
      → JWT generation (HS256, 30min TTL)
        → Refresh token (30 day TTL)
          → Redis perm_version cache
            └─ Response: {access_token, refresh_token, user}

Subsequent Requests
  → Authorization: Bearer <JWT>
    → get_current_user():
      1. Decode JWT (python-jose)
      2. Check Redis blacklist (jti)
      3. Load LabUser from DB
      4. Compare perm_version (Redis → DB fallback)
      5. Check lab is active
      6. Set context vars (user_id, lab_id)
    → require_permission() RBAC check
    → require_own_lab() tenant isolation
    → require_feature() subscription tier
    → Route handler
```

## 9. Database Connection Pool Architecture

```
                 ┌─────────────────────────────────────┐
                 │  SQLAlchemy Engine (Singleton)       │
                 │                                     │
                 │  Pool: QueuePool                     │
                 │  pool_size = 5 (per worker)          │
                 │  max_overflow = 10                    │
                 │  pool_timeout = 10s                   │
                 │  pool_recycle = 1800s                 │
                 │  pool_pre_ping = True                 │
                 │                                     │
                 │  Statement timeout: 30s               │
                 │  work_mem: 128MB                      │
                 │  idle_in_transaction: 30s             │
                 └──────────────────┬──────────────────┘
                                    │
                     ┌──────────────┼──────────────┐
                     │              │              │
              ┌──────▼────┐  ┌─────▼─────┐  ┌─────▼──────┐
              │ Worker 1  │  │ Worker 2  │  │ Worker 3   │
              │ (6 conns) │  │ (6 conns) │  │ (6 conns)  │
              └───────────┘  └───────────┘  └────────────┘
              Total: 18 connections (54 with WEB_CONCURRENCY=3)
              Budget: within PG default max_connections=100
```

## 10. Feature Flag Architecture

```
                 ┌──────────────────────────────────────┐
                 │  Two Parallel Flag Systems           │
                 │                                      │
                 │  1. Per-Tenant (feature_flags.py)    │
                 │     - Tier-based (starter/growth/ent) │
                 │     - Deployment overrides            │
                 │     - Security overrides              │
                 │     - Per-lab FeatureFlag overrides   │
                 │     - DB-backed + Redis-cached        │
                 │                                      │
                 │  2. Deployment-Wide (sndhs_flags.py) │
                 │     - SNDHS_ENABLE_VISITS             │
                 │     - SNDHS_ENABLE_NATIONAL_ID        │
                 │     - ENABLE_FINANCIAL_ENGINE          │
                 │     - ENABLE_ADS                      │
                 │                                      │
                 │  Enforcement: require_feature() dep   │
                 └──────────────────────────────────────┘
```

## 11. Startup Sequence

```
Container Start
  → lifespan startup:
    1. validate_config() — secrets present + not weak
    2. wait_for_db() — exponential backoff, 15 retries
    3. check_migrations() — alembic_version + 7 tables
    4. seed_critical_data() — test types, admin, subscriptions
    5. set_system_ready(True)
    6. Start background workers (health + concurrency loops)
    7. Boot kernel
  → yield (ready to serve)
  → On shutdown: cancel tasks, dispose engine
```

## 12. Microservices Architecture (Future State)

```
                 ┌──────────────────────────────┐
                 │     RabbitMQ (Event Bus)     │
                 │     Exchange: gula.events    │
                 └────┬──────┬──────┬──────┬───┘
                      │      │      │      │
              ┌───────▼┐ ┌──▼───┐ ┌──▼───┐ ┌▼────────┐
              │ lab    │ │order │ │patient│ │ result  │
              │ :8001  │ │:8003 │ │:8002  │ │ :8004   │
              └────────┘ └──────┘ └───────┘ └────┬────┘
                                                  │
                                          ┌───────▼──────┐
                                          │   ClickHouse  │
                                          │   Kafka       │
                                          │   MinIO       │
                                          └───────────────┘
                                  ┌────────┐ ┌─────────┐ ┌──────────┐
                                  │sample  │ │notific. │ │    ai    │
                                  │:8005   │ │:8006    │ │ :9000    │
                                  └────────┘ └─────────┘ └────┬─────┘
                                                               │
                                                        ┌──────▼──────┐
                                                        │   Ollama    │
                                                        │  :11434     │
                                                        └─────────────┘
```

Note: Only `device_bridge` (service-level ASTM/HL7) and `ai` (Ollama gateway) are production-ready. The 7 others are stubs with basic CRUD + RabbitMQ events. The monolith remains the source of truth.
