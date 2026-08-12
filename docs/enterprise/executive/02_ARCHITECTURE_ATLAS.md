# GULA Platform — Architecture Atlas

**Classification:** CONFIDENTIAL
**Date:** 2026-07-18

---

## 1. Architecture Overview

GULA is deployed as a **FastAPI monolith** (v2.1.0) on **Python 3.11+** with **Gunicorn + Uvicorn** workers, backed by **PostgreSQL 16** and **Redis 7**. The architecture follows a layered design with 11 middleware layers, 4-level degradation, and 3-layer self-healing.

### Request Lifecycle

```
Internet → Host Nginx (TLS 1.2/1.3, WAF ModSec, rate limit)
  → API Gateway Nginx (127.0.0.1:8080)
    → FastAPI Middleware Stack (11 layers)
      → Route Handler (53+ modules)
        → Service Layer (34+ modules)
          → Data Layer (SQLAlchemy 2.0 + Alembic)
            → PostgreSQL 16 + Redis 7
```

---

## 2. Middleware Stack (Ordered)

| # | Middleware | Purpose | Bypassed |
|---|-----------|---------|----------|
| 1 | MaxBodySizeMiddleware | 413 above MAX_REQUEST_BODY_MB (default 10) | No |
| 2 | RequestIDMiddleware | UUID X-Request-ID + log context + DB correlation | No |
| 3 | DocsAuthMiddleware | JWT-guard /docs, /redoc, /openapi.json in production | No |
| 4 | CORSMiddleware | Cross-origin resource sharing | No |
| 5 | RequestTimingMiddleware | Per-request access log, X-Response-Time header | No |
| 6 | SecurityHeadersMiddleware | CSP, HSTS, X-Frame-Options, XSS-Protection, Referrer-Policy, Permissions-Policy, COOP | No |
| 7 | GZipMiddleware | Compression for responses >1KB | No |
| 8 | ReadinessMiddleware | 503 until system_ready is True | Health paths |
| 9 | DegradedModeMiddleware | Circuit breaker: L1=cache, L2=read-only, L3=critical-only | Health paths |
| 10 | KernelMiddleware | Kernel integration | No |
| 11 | ConcurrencyLimitMiddleware | Max 200 in-flight requests; clinical writes exempt | Health paths |

---

## 3. Self-Healing Layers

| Layer | Component | Trigger | Action |
|-------|-----------|---------|--------|
| **Circuit Breaker** | DB circuit | 3 consecutive DB failures | L1→cache, L2→read-only, L3→critical-only, L4→degraded |
| **Circuit Breaker** | Redis circuit | 5 consecutive Redis failures | Falls back to DB-only with in-memory cache |
| **Auto-Repair** | auto_repair.py | Scheduled (30s loop) | GC collection, pool recycle, circuit probe, Redis reconnect |
| **Adaptive Concurrency** | _adaptive_concurrency_loop | 2 slow DB readings >300ms | Halve _MAX_CONCURRENT; restore after 3 fast <150ms |
| **Health Alert Loop** | _health_alert_loop | 60s interval | Score GREEN/YELLOW/RED; webhook on transitions + 5min RED reminders |

---

## 4. Route Modules (53+)

| Category | Count | Key Modules (with LOC) |
|----------|-------|----------------------|
| **Core LIMS** | 16 | admin (37,893), login (7,330), register (21,530), labs (7,308), patients (8,732), results (11,594), test_results (24,384), samples (6,349), dashboard (6,327), stats (14,945), patient_card (11,396), quality_control (10,802), critical_alerts (1,118), device_results (3,993), batch (3,950), qr (2,736) |
| **Clinical** | 8 | clinical (40,609), clinical_orders (9,855), clinical_documentation (11,846), clinical_quality (2,909), ehr (73,097), ehr_fhir (37,334), care_continuum (33,957), hospital (26,515) |
| **AI** | 2 | ai (39,938), ai_telemetry (19,846) |
| **Security** | 9 | identity (2,673), national_identity (755), mfa (4,486), password_reset (2,723), oauth2 (12,106), saml (2,147), service_accounts (3,462), consent (6,661), security (1,968) |
| **National** | 6 | national_data (34,607), national_streaming (9,502), compliance (47,295), citizen_portal (17,175), claims (6,316), insurance (550) |
| **Other** | 8+ | edge (32,912), metrics (12,801), mobile (13,349), notifications (4,632), tiers (21,577), integrations (4,425), setup (1,021), optimizer (3,069), canonical_patient (7,890) |

---

## 5. Service Layer (34+ modules)

| Largest Services | LOC | Purpose |
|-----------------|-----|---------|
| interpretation.py | 1,100+ | Clinical test result interpretation (Arabic/English) |
| clinical_service.py | 1,336 | Clinical workflow orchestration |
| ehr_service.py | 1,324 | EHR data management |
| care_continuum_service.py | 1,084 | Longitudinal patient care tracking |

---

## 6. Data Flow: Lab Result Ingestion

```
Lab Analyzer (ASTM serial/TCP)
  → device_bridge
    → normalizer → test mapper → patient matcher → smart router
      → gula_client.py (HTTP POST)
        → device_results route
          → auth + validation → LabResult (optimistic lock)
            → audit → clinical engine → outbox → notification (WhatsApp/SMS)
```

---

## 7. Feature Flags (2 Parallel Systems)

| System | Scope | Mechanism |
|--------|-------|-----------|
| Per-tenant (feature_flags.py) | Per-lab feature enablement | DB-backed + Redis-cached |
| Deployment-wide (sndhs_flags.py) | Global toggles | Environment variables |

| Flag | Default | Controls |
|------|---------|----------|
| SNDHS_ENABLE_VISITS | false | Visit tracking |
| SNDHS_ENABLE_NATIONAL_ID | false | National ID fields |
| ENABLE_FINANCIAL_ENGINE | false | Financial Engine routes |
| ENABLE_ADS | false | Advertising/campaign features |
| FEATURE_BACKGROUND_TASKS | true | Background worker startup |

---

## 8. Background Worker (6 Resilient Loops)

| Loop | Interval | Purpose |
|------|----------|---------|
| OutboxWorker | 10s | Dispatch events (FOR UPDATE SKIP LOCKED) |
| RecoveryWorker | 30s | Probe failed services |
| _health_alert_loop | 60s | System scoring + alert dispatch |
| _adaptive_concurrency_loop | dynamic | Worker cap adjustment |
| auto_repair.run | 30s | GC, pool recycle, reconnect |
| TaskWorker | discrete | Clinical tasks |

---

## 9. Architecture Compliance Score

| Metric | Score | Grade |
|--------|-------|-------|
| **Certification Level** | BRONZE | — |
| **Quality Index** | 673/1000 | D |
| **Architecture Compliance** | 7/100 | F |
| **Layer Violations** | 26 | FAIL |
| **Circular Dependencies** | 7 | FAIL |
| **Forbidden Imports (domain→framework)** | 52 | FAIL |
| **Cross-Domain Leakages** | 365 | FAIL |

### Missing Architectural Layers

| Layer | Status |
|-------|--------|
| Dedicated Domain Layer | ❌ Missing |
| CQRS | ❌ Missing |
| Hexagonal (Port/Adapter) | ❌ Missing |
| Plugin Architecture | ❌ Missing |
| Event Store | ❌ Missing |
| Service Mesh | ❌ Missing |
| API Gateway Service Mesh | ❌ Missing |
