# PI-004 — Architecture Report

## Deployment Platform Architecture

**Version:** 2.1.0
**Date:** July 2026

---

## 1. Platform Architecture Overview

The GULA Deployment Platform comprises the infrastructure, middleware, and operational tooling that hosts the national health platform. The architecture follows a layered, defense-in-depth model with three distinct deployment profiles:

1. **MVP (Docker Compose)** — Single-node deployment for initial rollout
2. **Standard (ECS Fargate)** — Managed container orchestration for production
3. **Advanced (EKS)** — Kubernetes-based for future scale-out

---

## 2. Component Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          INTERNET (TLS 1.3)                            │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌──────────────────────┐    ┌──────────────────────────────────────┐  │
│  │    CloudFront CDN     │    │         API Gateway (nginx)          │  │
│  │  - Static app hosting │    │  - TLS termination                  │  │
│  │  - Edge caching       │    │  - Rate limiting                    │  │
│  │  - WAF (SQLi, XSS)   │    │  - JWT validation                   │  │
│  │  - S3 origin          │    │  - Request routing                  │  │
│  └──────────┬───────────┘    └──────────────┬───────────────────────┘  │
│             │                               │                          │
│  ┌──────────▼───────────────────────────────▼───────────────────────┐  │
│  │                  Application Layer                                │  │
│  │                                                                   │  │
│  │  ┌──────────────────┐  ┌──────────────────┐  ┌────────────────┐  │  │
│  │  │  gula-backend     │  │  gula-worker      │  │  device-bridge │  │
│  │  │  (FastAPI)        │  │  (Background)     │  │  (ASTM/HL7)   │  │
│  │  │  Gunicorn + UVic  │  │  Outbox pattern   │  │  Instrument    │  │
│  │  │  Web: 3 workers   │  │  Queue consumer   │  │  integration   │  │
│  │  └──────────────────┘  └──────────────────┘  └────────────────┘  │  │
│  │                         X (if not applicable)                     │  │
│  └───────────────────────────────────────────────────────────────────┘  │
│                                    │                                    │
│  ┌───────────────────────────────┐ │ ┌───────────────────────────────┐ │
│  │        Data Layer             │ │ │        Cache Layer            │ │
│  │  ┌───────────────────────┐   │ │ │  ┌───────────────────────┐   │ │
│  │  │  PostgreSQL 16 HA     │   │ │ │  │  Redis 7 Cluster      │   │ │
│  │  │  - Primary (RW)       │   │ │ │  │  - Auth sessions      │   │ │
│  │  │  - Read Replica (RO)  │   │ │ │  │  - Rate limit counters│   │ │
│  │  │  - Streaming repl.    │   │ │ │  │  - Job queue (RQ)     │   │ │
│  │  │  - Point-in-time recov│   │ │ │  │  - Cache (LRU)        │   │ │
│  │  └───────────────────────┘   │ │ │  └───────────────────────┘   │ │
│  └───────────────────────────────┘ └─────────────────────────────────┘ │
│                                    │                                    │
│  ┌───────────────────────────────────────────────────────────────────┐  │
│  │                    Message Queue                                  │  │
│  │  ┌───────────────────────┐                                        │  │
│  │  │  RabbitMQ              │                                        │  │
│  │  │  - Outbox events       │                                        │  │
│  │  │  - Notification queue  │                                        │  │
│  │  │  - Report generation   │                                        │  │
│  │  │  - Dead letter         │                                        │  │
│  │  └───────────────────────┘                                        │  │
│  └───────────────────────────────────────────────────────────────────┘  │
│                                                                         │
│  ┌───────────────────────────────────────────────────────────────────┐  │
│  │                    Monitoring & Observability                     │  │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌────────────────────┐   │  │
│  │  │Prometheus│ │  Grafana │ │  Loki    │ │  Alertmanager      │   │  │
│  │  │Metrics   │ │Dashboards│ │  Logs    │ │  Alerts → Telegram   │   │  │
│  │  └──────────┘ └──────────┘ └──────────┘ └────────────────────┘   │  │
│  └───────────────────────────────────────────────────────────────────┘  │
│                                                                         │
│  ┌───────────────────────────────────────────────────────────────────┐  │
│  │                    Infrastructure Layer                           │  │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌────────┐ │  │
│  │  │  VPC     │ │  Subnets │ │  NAT GW  │ │  ALB/NLB │ │  S3    │ │  │
│  │  │  Network │ │  Public/ │ │  Egress  │ │  Load    │ │Object  │ │  │
│  │  │  Isolation│ │  Private │ │  Access  │ │  Balancer│ │Storage │ │  │
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────┘ └────────┘ │  │
│  └───────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 3. HAProxy Load Balancer (Scale Deployment)

When `make scale` is used, HAProxy sits in front of multiple backend replicas:

```
              ┌──────────────┐
              │    HAProxy    │
              │  :80 / :443   │
              │  Stats: :8404 │
              └──────┬───────┘
         ┌───────────┼───────────┐
         ▼           ▼           ▼
   ┌──────────┐ ┌──────────┐ ┌──────────┐
   │Backend 1 │ │Backend 2 │ │Backend N │
   │:8000     │ │:8000     │ │:8000     │
   └──────────┘ └──────────┘ └──────────┘
         │           │           │
         └───────────┼───────────┘
                     ▼
              ┌──────────────┐
              │  PostgreSQL  │
              │  (RW Primary) │
              └──────────────┘
```

**HAProxy configuration highlights:**
- Round-robin load balancing across N backends
- Health checks every 5s against `/health/ready`
- Stats endpoint at `:8404/stats` (password protected)
- Max connections: 10,000
- Connection queue: 1,000

---

## 4. Kubernetes Architecture (Advanced)

```
┌──────────────────────────────────────────────────────────┐
│                      EKS Cluster                         │
│                                                          │
│  ┌──────────────────────────────────────────────────────┐│
│  │                gula-namespace                         ││
│  │                                                      ││
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐          ││
│  │  │backend   │  │worker    │  │device-   │          ││
│  │  │Deploy    │  │Deploy    │  │bridge    │          ││
│  │  │HPA: 2-10 │  │HPA: 1-5  │  │Deploy    │          ││
│  │  └──────────┘  └──────────┘  └──────────┘          ││
│  │                                                      ││
│  │  ┌──────────┐  ┌──────────┐  ┌──────────────────┐   ││
│  │  │PostgreSQL│  │Redis     │  │Ingress (nginx)   │   ││
│  │  │Operator  │  │Operator  │  │TLS: cert-manager  │   ││
│  │  │(Crunchy) │  │(Redis HW)│  │WAF: modsecurity   │   ││
│  │  └──────────┘  └──────────┘  └──────────────────┘   ││
│  └──────────────────────────────────────────────────────┘│
│                                                          │
│  ┌──────────────────────────────────────────────────────┐│
│  │               monitoring-namespace                    ││
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────┐ ││
│  │  │Prometheus│  │Grafana   │  │Loki      │  │ELK   │ ││
│  │  │Operator  │  │Operator  │  │Stack     │  │Stck  │ ││
│  │  └──────────┘  └──────────┘  └──────────┘  └──────┘ ││
│  └──────────────────────────────────────────────────────┘│
└──────────────────────────────────────────────────────────┘
```

---

## 5. CI/CD Pipeline Architecture

```
Developer Push → GitHub
    │
    ▼
GitHub Actions
    │
    ├── syntax-gate (py_compile + flake8) ← 30s
    ├── migration-check (alembic on clean DB) ← 60s
    ├── smoke-test (curl health endpoints) ← 30s
    ├── backend-test (pytest 28 modules) ← 5min
    ├── security-scan (safety, bandit, hadolint, gitleaks) ← 2min
    │
    ├── build-and-push (8 images to GHCR) ← 8min
    │   ├── gula-backend:${SHA}
    │   ├── gula-worker:${SHA}
    │   ├── device-bridge:${SHA}
    │   ├── service-lab:${SHA}
    │   ├── service-order:${SHA}
    │   ├── service-patient:${SHA}
    │   ├── service-result:${SHA}
    │   └── service-sample:${SHA}
    │
    ├── deploy-staging (Helm upgrade) ← 2min
    ├── e2e-tests (Playwright) ← 10min
    │
    └── deploy-production (blue/green) ← 5min
```

---

## 6. Database Architecture

### 6.1 Connection Management

```
                     gula-backend (3 workers)
                    /        |        \
              Pool 1      Pool 2      Pool 3
           (size: 6)   (size: 6)   (size: 6)
           max_overflow: 12  (per worker)
                    \        |        /
                 ┌─────────────────────┐
                 │  PostgreSQL 16       │
                 │  max_connections: 100│
                 │  shared_buffers: 4GB │
                 │  effective_cache: 8GB│
                 └─────────────────────┘
```

### 6.2 Key Database Metrics

| Metric | Value | Warning | Critical |
|--------|-------|---------|----------|
| Connections | 25-45 | > 70 | > 90 |
| Active queries | 5-15 | > 30 | > 50 |
| Cache hit ratio | 98% | < 95% | < 90% |
| Replication lag | < 100ms | > 1s | > 5s |
| Long queries (> 1s) | < 5/min | > 20/min | > 50/min |
| Dead tuples | < 10% | > 20% | > 30% |
| Transaction ID wraparound | < 100M | > 1B | > 2B |

---

## 7. Service Mesh Architecture (Future)

```
┌──────────────────────────────────────────────┐
│                  Istio Service Mesh           │
│                                              │
│  ┌─────────┐   ┌─────────┐   ┌─────────┐   │
│  │backend-v1│   │backend-v2│   │worker   │   │
│  │(current) │   │(canary)  │   │         │   │
│  └────┬─────┘   └────┬─────┘   └────┬─────┘   │
│       │              │              │         │
│  ┌────▼──────────────▼──────────────▼──────┐  │
│  │         VirtualService                  │  │
│  │  weight: backend-v1=95, backend-v2=5   │  │
│  └─────────────────────────────────────────┘  │
│                                              │
│  Features:                                    │
│  - Traffic splitting (canary)                 │
│  - Circuit breaking                           │
│  - Retry + timeout policies                   │
│  - Mutual TLS (mTLS) between services         │
│  - Distributed tracing (Jaeger)               │
└──────────────────────────────────────────────┘
```

---

## 8. Self-Healing Architecture

The platform implements three layers of self-healing:

1. **Circuit Breaker** (`backend/app/core/self_healing.py`): Opens on DB/Redis failures, prevents cascading failures, auto-closes after recovery
2. **Auto-Repair Engine** (`backend/app/core/auto_repair.py`): GC collection, pool recycle, connection retry with exponential backoff
3. **Adaptive Concurrency** (`backend/app/main.py`): Halves max concurrent requests on slow DB queries; restores after fast queries

```
Request → DegradedModeMiddleware → Circuit Breaker
                                    ├── CLOSED → Normal processing
                                    ├── OPEN → Reject writes, allow reads
                                    └── HALF_OPEN → Probe recovery
                                                ↓
                                        Auto-Repair Engine
                                    └── Full recovery → Reset breaker
```
