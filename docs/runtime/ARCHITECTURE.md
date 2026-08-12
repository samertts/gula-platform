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

## New Platform Components (v2.3.0)

### Identity Platform (PI-001 WP2.5)

```
Identity Platform
├── Identity Persistence (Phase 1) — gov_identity_records, gov_break_glass_accesses, gov_merge_proposals
├── Offline Sync Engine (Phase 4) — CRDT vector clocks, conflict resolution, EncryptedSyncStore
├── Device Trust Service      — Fingerprinting, trust escalation, auto-deactivation
└── Risk-Based Auth           — Context scoring, impossible travel, adaptive responses
```

All four components reuse existing Kernel (event_bus), database.py (SessionLocal),
and security/auth.py patterns. Zero new database tables — all persistence reuses
existing `gov_identity_records` et al.

### Security Platform (PI-001 WP3)

- **Device Trust Service**: Provides fingerprint-based device identification (CPU, GPU, RAM,
  OS, display, user-agent hashes) with trust level lifecycle management
- **Risk-Based Authentication**: Real-time risk scoring using request context (geo, device,
  behavior) with Haversine distance for impossible travel detection and Tor/VPN/datacenter
  IP classification via heuristic rules

### Clinical Core (PI-002)

- **Offline Sync Engine**: Enables clinical data synchronization in disconnected environments
  using vector clock-based conflict detection. Supports four merge strategies: LWW, timestamp,
  CRDT, and manual review. Data encrypted at rest via `EncryptedSyncStore`.

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
- 3 Identity/Security/Clinical Core services (886 LOC total)
- 49 new tests covering offline sync, device trust, risk-based auth
- 137 Python source files (National Platform Runtime)
- 0 breaking changes to existing modules
- 0 undefined name errors (pyflakes)
- 0 syntax errors
- 0 flake8 E9/F821 errors
