# GULA PLATFORM — ARCHITECTURE MASTER PLAN

**Status:** VERIFIED (from audit) + PROPOSED (future state)
**Date:** 2026-07-17

---

## CURRENT ARCHITECTURE SCORE

| Criterion | Score (1-10) | Notes |
|-----------|-------------|-------|
| Clean Architecture | 6/10 | Core/domain separation exists but 60+ subdirectories blur boundaries |
| Domain-Driven Design | 5/10 | Domain modules exist but inconsistent granularity |
| SOLID Principles | 7/10 | Dependency injection via FastAPI, OCP violated in monolithic routes |
| Hexagonal Architecture | 4/10 | No port/adapter pattern — direct DB access in routes |
| CQRS | 3/10 | Read/write separation only in read-replica (basic) |
| Event-Driven | 6/10 | Outbox pattern exists, but no event store or CQRS events |
| Offline-First | 7/10 | Edge agent, device bridge queue, offline sync exist |
| Plugin Architecture | 3/10 | No plugin system, all code compiled together |
| Module Boundaries | 4/10 | 60+ subdirectories with no enforced boundaries |
| Future Scalability | 5/10 | Monolith will hit limits, microservices not ready |
| Replaceability | 4/10 | No modular replacement strategy for components |

**Overall Architecture Score: 4.9/10**

---

## ARCHITECTURAL ISSUES (Verified)

### Issue 1: No Enforced Module Boundaries
**Evidence:** 60+ subdirectories in `backend/app/` with no dependency rules between them. `routes/` imports directly from `models/`, `services/`, `database.py`, and `config.py`.

**Impact:**
- Circular imports possible
- No team-scale development (merge conflicts)
- Refactoring breaks unexpected dependents

**Solution:** Enforce layer rules:
```
routes/ → services/ → models/ (dependency direction)
routes/ → config/ (read only)
services/ → database.py (via DI, not direct import)
```

### Issue 2: Monolith Scope Explosion
**Evidence:** Code for 19+ distinct platform domains exists in a single Python package.

**Impact:**
- Import time increases
- Memory footprint grows
- Deployment includes unused code
- Testing is slower

**Solution:** Split into namespaced packages:
```
gula-core/ (LIMS, auth, patients, orders, results)
gula-clinical/ (clinical engine, interpretations)
gula-nhdw/ (national health data warehouse)
gula-nursing/ (nursing platform)
gula-pharmacy/ (pharmacy platform)
gula-radiology/ (radiology platform)
gula-ems/ (emergency services)
...
```

### Issue 3: Microservices Not Production-Ready
**Evidence:** 8 microservices at `services/` are single-file CRUD stubs with no tests, deprecated FastAPI patterns, inline pip dependencies, and dead shared bridge code.

**Impact:**
- Cannot be deployed independently
- Would fail under production load
- No monitoring or observability
- Security issues (direct hardcoded dependencies)

**Solution:**
- Migrate to lifespan context manager
- Add tests (unit + integration)
- Use proper dependency management (pyproject.toml)
- Remove dead services/shared/ bridge

### Issue 4: No Plugin Architecture
**Evidence:** All code is compiled into a single Python process. No way to add capabilities without modifying core code.

**Impact:**
- Every new feature requires full deployment
- Third-party developers cannot extend
- Cannot isolate failures

**Solution:** Implement plugin system using Python entry points or import hooks:
```
gula.plugin.ai = "gula-ai-interpretation"
gula.plugin.connector = "my-custom-connector"
gula.plugin.workflow = "hospital-workflow"
```

### Issue 5: Database Access Pattern Inconsistency
**Evidence:** Core monolith uses SQLAlchemy ORM. Microservices use raw asyncpg. Some modules may use direct SQL.

**Impact:**
- Inconsistent query patterns
- Duplicate business logic
- Migration changes affect both layers

**Solution:** Standardize on SQLAlchemy 2.0 ORM for all database access.

---

## TARGET ARCHITECTURE

```
┌─────────────────────────────────────────────────────────┐
│                    USER INTERFACES                        │
│  frontend-v2  │  frontend  │  client  │  mobile  │ API  │
│  (React+PWA)  │  (HTML/JS) │  (tRPC)  │  (future)│ REST │
└──────────────────────┬──────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────┐
│                 API GATEWAY (nginx)                       │
│  Auth → Rate Limit → Route → Transform → Cache           │
│  + Cloudflare Edge (WAF, DDoS, bot detection)            │
└──────────────────────┬──────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────┐
│              APPLICATION LAYER                            │
│  ┌────────────────────────────────────────────────────┐  │
│  │              SOVEREIGN AI PLATFORM                  │  │
│  │  AI Gateway → Model Router → Safety → RAG → Agent  │  │
│  └────────────────────────────────────────────────────┘  │
│  ┌────────────────────────────────────────────────────┐  │
│  │           SOVEREIGN CONNECTOR GATEWAY               │  │
│  │  Policy → Token → Connector Runtime → Audit         │  │
│  └────────────────────────────────────────────────────┘  │
│  ┌────────────────────────────────────────────────────┐  │
│  │              GULA CORE (Monolith)                   │  │
│  │  Routes → Services → Domain → Models               │  │
│  │  LIMS │ Clinical │ National │ EMR │ Admin          │  │
│  └────────────────────────────────────────────────────┘  │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐       │
│  │  Plugin  │ │  Plugin │ │  Plugin  │ │  Plugin │       │
│  │  System  │ │  System │ │  System  │ │  System │       │
│  └─────────┘ └─────────┘ └─────────┘ └─────────┘       │
└──────────────────────┬──────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────┐
│              INFRASTRUCTURE LAYER                         │
│  PostgreSQL 16 │ Redis 7 │ RabbitMQ │ Kafka │ MinIO     │
│  ClickHouse │ Prometheus │ Grafana │ Loki │ Jaeger     │
└──────────────────────────────────────────────────────────┘
```

---

## FUTURE-PROOFING PRINCIPLES

### 1. Domain Boundaries
Each domain module (`lims/`, `clinical/`, `hospital/`, etc.) must:
- Have its own `routes/`, `services/`, `models/` subdirectory
- Import only from `shared/` or `core/` — never from other domains
- Be independently testable
- Declare dependencies explicitly

### 2. Dependency Rule
```yaml
allowed_imports:
  routes: [services, config, security]
  services: [domain, models, config, core]
  domain: [models]  # Pure business logic
  models: []  # ORM only
  core: [config]  # Infrastructure
```

### 3. Evolution Path
| Stage | Architecture | Timeline |
|-------|-------------|----------|
| **1** | Well-structured monolith | Month 1-6 |
| **2** | Modular monolith (namespaced packages) | Month 6-12 |
| **3** | Plugin system for extensions | Month 12-18 |
| **4** | Extract high-volume services (results, AI) | Month 18-24 |
| **5** | Full microservice architecture (selective) | Month 24-36 |

### 4. Technology Decisions for Longevity
| Decision | Choice | Rationale |
|----------|--------|-----------|
| Backend | Python 3.12+ / FastAPI | Industry standard, async, wide ecosystem |
| ORM | SQLAlchemy 2.0 | Mature, async, migration support |
| API | REST (primary) + gRPC (internal) | REST for external, gRPC for performance |
| Events | RabbitMQ | Reliable, well-understood |
| Streams | Kafka | High-throughput, replay, long retention |
| AI | Ollama + cloud routing | Offline-first, vendor independent |
| Queue | RabbitMQ + Redis | Transactional outbox pattern |
| Cache | Redis (multi-level) | L1 in-memory + L2 Redis |
| Storage | S3-compatible (MinIO) | Standard, portable |
| Identity | OAuth2 + OIDC + SAML | Standards-based, not proprietary |
| Deployment | Docker (now) → K8s (future) | Evolutionary, not revolutionary |
