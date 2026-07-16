# GULA Platform — Architecture Snapshot

**Date:** 2026-07-15 12:45 UTC
**Version:** 2.1.0

---

## 1. System Architecture Diagram

```
                         ┌─────────────────────────────────┐
                         │         Internet / Users         │
                         └──────────────┬──────────────────┘
                                        │
                                   [TLS/HTTPS]
                                        │
                         ┌──────────────▼──────────────────┐
                         │     Host nginx (TLS term.)       │
                         └──────────────┬──────────────────┘
                                        │
                         ┌──────────────▼──────────────────┐
                         │    api-gateway (Docker nginx)    │
                         │        127.0.0.1:8080            │
                         └──────────────┬──────────────────┘
                                        │
               ┌────────────────────────┼────────────────────────┐
               │                        │                        │
    ┌──────────▼──────────┐  ┌──────────▼──────────┐  ┌─────────▼─────────┐
    │    gula-backend      │  │      Prometheus      │  │      HAProxy      │
    │  (FastAPI, port 8000)│  │    (monitoring)      │  │  (load balancer)  │
    │  gunicorn + uvicorn  │  └─────────────────────┘  └───────────────────┘
    │  3 workers default   │
    └──────────┬───────────┘
               │
     ┌─────────┼─────────────┐
     │         │             │
┌────▼────┐ ┌──▼───┐  ┌─────▼─────┐
│PostgreSQL│ │Redis │  │   Sentry  │
│   16     │ │  7   │  │  (opt.)   │
└─────────┘ └──────┘  └───────────┘
```

## 2. Middleware Stack (request order)

```
1. MaxBodySizeMiddleware      → 413 above MAX_REQUEST_BODY_MB
2. RequestIDMiddleware         → X-Request-ID + log context
3. DocsAuthMiddleware         → guards /docs in production
4. CORSMiddleware             → configured origins
5. RequestTimingMiddleware    → access log + X-Response-Time
6. SecurityHeadersMiddleware  → CSP, HSTS, X-Frame-Options
7. GZipMiddleware            → compression
8. ReadinessMiddleware       → 503 until system_ready
9. DegradedModeMiddleware    → blocks writes in degraded mode
10. KernelMiddleware         → kernel context
11. ConcurrencyLimitMiddleware → backpressure
```

## 3. Module Dependency Graph

```
┌─────────────────────────────────────────────────────────────────┐
│                      gula-backend (FastAPI)                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌────────────────┐  │
│  │  Routes  │  │  Models  │  │ Services │  │  Core Infra    │  │
│  │  (46)    │  │  (20)    │  │  (31)    │  │  (16 modules)  │  │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └───────┬────────┘  │
│       │              │              │                │           │
│       ▼              ▼              ▼                ▼           │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌────────────────┐  │
│  │ Security │  │  Audit   │  │  Domain  │  │  Self-Healing  │  │
│  │  (12)    │  │  (1)     │  │  (1)     │  │  (3 layers)    │  │
│  └──────────┘  └──────────┘  └──────────┘  └────────────────┘  │
│                                                                  │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌────────────────┐  │
│  │ National │  │ Platform │  │   LIMS   │  │  Integration   │  │
│  │ Runtime  │  │ Modules  │  │  (39)    │  │  Connectors    │  │
│  └──────────┘  └──────────┘  └──────────┘  └────────────────┘  │
│                                                                  │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌────────────────┐  │
│  │Governance│  │Clinical  │  │ Hospital │  │  Knowledge     │  │
│  │ Layer    │  │ Core     │  │   HIS    │  │  Graph         │  │
│  └──────────┘  └──────────┘  └──────────┘  └────────────────┘  │
│                                                                  │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌────────────────┐  │
│  │Financial │  │   Edge   │  │    AI    │  │  Notification  │  │
│  │(Phase A) │  │ Platform │  │  Safety  │  │  Service       │  │
│  └──────────┘  └──────────┘  └──────────┘  └────────────────┘  │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## 4. Data Flow

```
Client → nginx → api-gateway → FastAPI middleware stack
                                         │
                                         ▼
                                   Route handler
                                         │
                              ┌──────────┼──────────┐
                              │          │          │
                              ▼          ▼          ▼
                         Service     Model     External API
                         Layer       Layer     (guarded)
                              │          │
                              ▼          ▼
                         PostgreSQL    Redis
                          (source     (cache/
                            of truth)   sessions)
```

## 5. Security Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Security Architecture                    │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  Authentication: JWT (access + refresh tokens)               │
│  Authorization: RBAC (9 roles) + ABAC (attribute-based)      │
│  Encryption: Fernet at rest, TLS in transit                  │
│  Rate Limiting: Per-IP + per-user sliding window             │
│  Circuit Breaker: DB + Redis health monitoring               │
│  Audit Logging: Immutable hash chain                         │
│  Consent Management: Grant/revoke/check + break-glass        │
│  Intrusion Detection: Pattern-based + threshold-based        │
│  Session Management: JWT blacklist + refresh token rotation  │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

## 6. Component Versions

| Component | Version |
|-----------|---------|
| Platform | 2.1.0 |
| Python | 3.10+ |
| FastAPI | latest |
| PostgreSQL | 16 |
| Redis | 7 |
| nginx (gateway) | 1.25-alpine |
| Gunicorn | latest |
| Uvicorn | latest |
| Prometheus | latest |
| Grafana | latest |
| HAProxy | latest |
| App modules | 221 |
| Routes | 0 |
| Models | 20 |
| Services | 31 |
| Core modules | 16 |
| Security modules | 12 |
| Tests | 117 test files |
| Total commits | 466 |

---

*Snapshot generated by GULA Production Freeze Agent on 2026-07-15 12:45 UTC*
