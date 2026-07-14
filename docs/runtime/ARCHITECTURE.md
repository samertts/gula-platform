# National Health Platform Runtime — Architecture Report

## Overview

The National Platform Runtime is the execution layer for the Iraq National Health Platform. It provides 9 domain engines that together power all clinical, administrative, and operational workflows across the national healthcare system.

## Architecture Principles

- **Zero breaking changes** — all existing Foundation, Governance, LIMS, and Integration Contracts remain frozen
- **Zero duplicated code** — every module reuses existing Kernel, EventBus, Tasks, Notifications, Security, and Domain models
- **Clean Architecture** — each module follows domain → application → infrastructure → API layering
- **CQRS/Event-Driven** — commands, queries, events for every bounded context
- **Government-scale** — horizontal scaling, multi-region ready, offline-first compatible

## Module Architecture

```
National Platform Runtime
├── Rules Engine         — Expression evaluation, simulation, versioning, 8 categories
├── Background Platform  — Job scheduling, cron, dependencies, distributed execution
├── Workflow Runtime     — Saga orchestration, long-running, approvals, compensation
├── Task Engine          — Assignments, queues, SLA, escalation, delegation, KPIs
├── Notification Platform— Email, SMS, Push, WebSocket, WhatsApp, Telegram, Gov Gateway
├── Document Platform    — Versioning, e-signatures, QR verification, PDF, retention
├── Scheduling Platform  — Appointments, resources, calendars, conflict detection
├── Search Platform      — Unified FHIR/full-text search, facets, saved searches
└── Observability        — Metrics, tracing, health checks, alerts, OpenTelemetry
```

## Reuse of Existing Infrastructure

| Existing Module | Reused By | Integration Pattern |
|----------------|-----------|-------------------|
| Kernel (event_bus) | All 9 modules | Event publishing/subscription |
| Kernel (background) | Background Platform, Workflow Runtime | Cron scheduling, task queue |
| tasks/ | Background Platform, Workflow Runtime, Notification Platform | Async task execution |
| notifications/ | Notification Platform | Telegram adapter, service base |
| national/base.py | All 9 modules | NationalBase, BaseEntity |
| national/enums.py | All 9 modules | Shared enum values |
| national/exceptions.py | All 9 modules | NationalDomainError base |
| national/security/ | All 9 modules | ABAC/RBAC authorization |
| core/self_healing | All modules via kernel | Circuit breaker, degraded mode |
| database.py | All modules | SessionLocal, connection pool |
| shared/models | All modules | TimestampMixin, SoftDeleteMixin |

## Bounded Contexts

Each of the 9 modules is a fully isolated bounded context with:
- Domain entities and value objects
- Domain events
- Application services (use cases)
- Infrastructure (SQLAlchemy models + repositories)
- REST API (FastAPI routers)

## Data Flow

```
Request → API Gateway → Kernel Middleware → Route Handler
    → Application Service → Domain Logic
        → Events → EventBus → Other Modules
        → Tasks → TaskQueue → Async Workers
        → DB → Repository → PostgreSQL
```

## Key Metrics

- 9 National Platform Runtime modules
- 137 Python source files
- 0 breaking changes to existing modules
- 0 undefined name errors (pyflakes)
- 0 syntax errors
- 0 flake8 E9/F821 errors
