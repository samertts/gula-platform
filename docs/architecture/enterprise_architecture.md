# GULA Enterprise Architecture

**Version:** 1.0  
**Status:** RATIFIED  
**Classification:** INTERNAL  

---

## 1. Architecture Vision

GULA follows a **Modular Monolith with Service Decomposition Path** architecture. The primary deployment target is a modular FastAPI monolith organized by bounded context. Services are identified for future extraction when scalability requirements demand it, but monolith-first is the default strategy.

## 2. Architecture Principles

### Principle 1: Modular Monolith First
Modules are strongly-separated within a single deployment unit. Extraction to independent services happens only when scalability, team autonomy, or deployment independence demands it.

**Rationale:** Monoliths are simpler to develop, test, deploy, and operate. Premature microservices add latency, complexity, and operational overhead.

### Principle 2: Bounded Contexts
Every module represents a bounded context with explicit relationships to other contexts. Shared Kernel is minimized. Context mapping is documented.

**Rationale:** DDD bounded contexts prevent architectural drift by maintaining clear ownership and interfaces.

### Principle 3: Stable Interfaces
Interfaces between modules are more stable than implementations. Interfaces evolve through versioning, not breaking changes.

**Rationale:** Stable interfaces enable independent module evolution and eventual service extraction.

### Principle 4: Domain-Driven Design
Business logic lives in domain layer. Application layer orchestrates. Infrastructure layer implements interfaces.

**Rationale:** DDD ensures business logic is not coupled to frameworks, databases, or external services.

### Principle 5: CQRS for Write-Heavy Domains
Read and write models are separated for domains with high write volume or complex read requirements (LIMS, orders, results).

**Rationale:** CQRS enables optimized read performance without compromising write consistency.

### Principle 6: Event-Driven for Cross-Domain Communication
Domains communicate through events, not direct API calls. The event outbox pattern ensures reliable delivery.

**Rationale:** Event-driven communication decouples domains and enables eventual consistency without distributed transactions.

### Principle 7: Failure Isolation
Every module must handle failures of its dependencies gracefully. Circuit breakers, fallbacks, and degraded modes are mandatory.

**Rationale:** Failure in one module must not cascade to others.

### Principle 8: Observability is Infrastructure
Health, metrics, logs, and traces are part of every module's contract, not an afterthought.

**Rationale:** Without observability, no module can be operated at production scale.

## 3. Architecture Layers

```
┌─────────────────────────────────────────────────────────────┐
│                     API Gateway (nginx)                      │
│              Rate Limiting | TLS | WAF | Routing             │
├─────────────────────────────────────────────────────────────┤
│                        API Layer                             │
│              FastAPI Routes | Middleware Stack                │
├───────────────────┬──────────────────┬──────────────────────┤
│   Application     │    Application   │    Application       │
│   Services        │    Services      │    Services          │
├───────────────────┴──────────────────┴──────────────────────┤
│                      Domain Layer                            │
│           Entities | Value Objects | Aggregates              │
│           Domain Services | Domain Events                   │
│           Repository Interfaces | Policies                   │
├─────────────────────────────────────────────────────────────┤
│                    Infrastructure Layer                      │
│      Database | Cache | Message Queue | External APIs       │
│      Repository Implementations | Event Publishers          │
├─────────────────────────────────────────────────────────────┤
│                      Platform Core                           │
│   Kernel | Config | DI | Health | Circuit Breaker | Audit   │
└─────────────────────────────────────────────────────────────┘
```

## 4. Request Lifecycle

```
Internet → Host nginx (TLS) → API Gateway (nginx on 127.0.0.1:8080)
  → MaxBodySizeMiddleware → RequestIDMiddleware → DocsAuthMiddleware
  → CORSMiddleware → RequestTimingMiddleware → SecurityHeadersMiddleware
  → GZipMiddleware → ReadinessMiddleware → DegradedModeMiddleware
  → KernelMiddleware → ConcurrencyLimitMiddleware → Route Handler
  → Service Layer → Domain Layer → Infrastructure Layer → Response
```

## 5. Core vs Capabilities vs Modules

| Layer | Purpose | Examples |
|-------|---------|----------|
| **Platform Core** | Infrastructure shared by all capabilities | Kernel, Config, Security, Database, Audit, Self-healing |
| **Capabilities** | Business-neutral technical capabilities | FHIR interop, Workflow engine, Storage, Search |
| **Domain Modules** | Business-specific bounded contexts | LIMS, EHR, Radiology, Pharmacy, Blood Bank |
| **National Modules** | Country/region-specific functionality | SNDHS, NHDW, Citizen Platform, National ID |

## 6. Module Structure (Required Pattern)

Every module must follow this structure:

```
module_name/
├── __init__.py           # Public API (what other modules can import)
├── contracts.py          # Interface definitions (ports)
├── domain/               # Business logic (no external dependencies)
│   ├── entities.py
│   ├── value_objects.py
│   ├── aggregates.py
│   ├── events.py
│   ├── services.py       # Domain services
│   └── repositories.py   # Repository interfaces
├── application/          # Application services (orchestration)
│   ├── commands.py       # CQRS commands
│   ├── queries.py        # CQRS queries
│   └── handlers.py       # Command/query handlers
├── infrastructure/       # External dependency implementations
│   ├── database/
│   ├── cache/
│   ├── api/              # External API clients
│   └── messaging/
├── routes.py             # API endpoints (thin layer)
├── models.py             # SQLAlchemy models (if any)
├── services.py           # Application services
├── tasks.py              # Background tasks
├── exceptions.py         # Module-specific exceptions
├── health.py             # Health checks
├── permissions.py        # Permissions
├── config.py             # Module configuration
└── tests/                # Module tests
    ├── test_domain.py
    ├── test_application.py
    └── test_routes.py
```

## 7. Dependency Rules

1. **Domain layer** depends on NOTHING external (no FastAPI, no SQLAlchemy, no Redis)
2. **Application layer** depends on Domain layer only
3. **Infrastructure layer** implements Application layer interfaces
4. **Routes layer** depends on Application layer only
5. **Platform Core** has no dependencies on capability or domain modules
6. **Modules** may depend on Platform Core and Contracts, never on other module internals
7. **Circular dependencies** between modules are forbidden

## 8. Current Architecture Assessment

| Aspect | Score | Finding |
|--------|-------|---------|
| Domain Isolation | B- | `domain/order_state.py` is textbook clean; 70 top-level packages scatter domain logic |
| Layer Separation | B- | Routes import models, services import databases — no interface boundaries in legacy path |
| Module Boundaries | C | 70 top-level packages with inconsistent naming; kernel/module boundary not cleanly enforced |
| main.py Cohesion | D | 1,948-line main.js doing model registration, middleware, route registration, health, background tasks |
| Dependency Injection | C+ | Two DI systems: legacy import-time coupling vs Kernel DI container |
| Dual Systems | D | Two circuit breakers, two feature flag systems, two DI containers — Kernel reimplements Core |
| Event System | B | Event outbox pattern implemented; cross-domain events partially connected |
| Testability | B- | conftest.py is excellent; module-level globals hinder isolation |

## 9. Migration Target

The target architecture is a **Capability-Based Modular Monolith** with:

- 15-25 top-level modules (reduced from 70)
- All modules following the standardized structure above
- Single DI system (Kernel DI container with legacy migration path)
- Clean domain isolation in all modules
- Routes <= 200 lines each (extract business logic to services)
- main.py <= 500 lines (extract to lifecycle, config, middleware, routing modules)

---

*This document defines the enterprise architecture for GULA. All architectural decisions must conform to these principles.*
