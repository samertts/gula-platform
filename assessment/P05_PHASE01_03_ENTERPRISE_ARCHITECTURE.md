# GULA ENTERPRISE ENGINEERING PROGRAM

## PROGRAM-05: Enterprise Architecture Evolution

**Version:** 1.0 | **Status:** COMPLETE | **Date:** 2026-07-18

---

## Architecture Principles

| # | Principle | Description |
|---|-----------|-------------|
| 1 | **Domain Driven** | Every capability belongs to exactly one bounded context |
| 2 | **API First** | Every module communicates through well-defined contracts |
| 3 | **Event First** | State changes publish events; consumers react asynchronously |
| 4 | **Security by Design** | Zero Trust at every layer; default deny |
| 5 | **Healthcare Native** | FHIR, HL7, ISO 15189 are intrinsic, not bolted-on |
| 6 | **AI Native** | AI is a platform capability, not a separate service |
| 7 | **Offline First** | Edge nodes operate disconnected; sync when connected |
| 8 | **Configuration First** | Behavior is configured, not coded |
| 9 | **Multi Tenant** | Logical and physical isolation per deployment tier |
| 10 | **Sovereign** | Data residency, national identity, regulatory compliance built-in |

---

# PHASE 01: ENTERPRISE TARGET ARCHITECTURE

## Enterprise Vision

GULA evolves from a **monolithic LIMS application** into a **composable healthcare platform** where every business capability is a pluggable module within a governed enterprise kernel.

## Enterprise Layer Model

```
┌────────────────────────────────────────────────────────────────┐
│  PRESENTATION LAYER                                            │
│  Citizen Portal | Ministry Cmd Ctr | Doctor Dashboard | Lab WB │
├────────────────────────────────────────────────────────────────┤
│  API GATEWAY LAYER                                             │
│  Rate Limit | Auth | Routing | Versioning | Audit | CORS      │
├────────────────────────────────────────────────────────────────┤
│  APPLICATION LAYER (per bounded context)                       │
│  Orders Service | Results Service | Patients Service | ...    │
├────────────────────────────────────────────────────────────────┤
│  DOMAIN LAYER                                                  │
│  Entities | Value Objects | Aggregates | Domain Events        │
│  Domain Services | Repository Interfaces | Specifications     │
├────────────────────────────────────────────────────────────────┤
│  CORE / KERNEL LAYER                                          │
│  Event Bus | Cmd Bus | Query Bus | Workflow | Config          │
│  Identity | AuthZ | Audit | Scheduler | Notification Engine   │
├────────────────────────────────────────────────────────────────┤
│  INFRASTRUCTURE LAYER                                          │
│  PostgreSQL+pgvector | Redis Cluster | MinIO/S3 | RabbitMQ    │
├────────────────────────────────────────────────────────────────┤
│  OBSERVABILITY LAYER                                           │
│  Prometheus | Grafana | OpenTelemetry | Loki | Tempo          │
└────────────────────────────────────────────────────────────────┘
```

## Enterprise Capability Map

**Primary:** Laboratory Management | Order Processing | Result Management | Patient Management | Quality Control | Analyzer Integration | Blood Bank | Pathology | Radiology | Pharmacy | Clinical Decision | Public Health

**Supporting:** IAM | Audit | Notifications | Workflow Engine | Scheduling | Reporting | Inventory | Equipment Mgmt | Billing | Document Mgmt | Terminology | Research

**Shared:** Configuration | Feature Flags | Multi-tenancy | Search | AI Inference | Knowledge Graph | Integration Bus | FHIR Gateway | HL7 Gateway

## Bounded Context Map

```
Identity & Access ──▶ Organization ──▶ Laboratory ──▶ Patient (MPI)
      │                    │               │               │
      ▼                    ▼               ▼               ▼
  Personnel            Equipment        Orders ──▶ Specimens ──▶ Results
      │                    │               │                     │
      ▼                    ▼               ▼                     ▼
  Workflow              Inventory       Quality              Public Health
      │                                                    │
      ▼                                                    ▼
Notifications ──▶ Clinical ──▶ AI Platform ──▶ Healthcare (FHIR)
```

---

# PHASE 02: PLATFORM CORE ARCHITECTURE

## Kernel Boot Sequence

```
1. Kernel.boot()
   ├─ Load Configuration (env → file → vault)
   ├─ Validate Configuration (secrets present, weak checks)
   ├─ Initialize Logging
   ├─ Initialize HealthManager
   ├─ Initialize ServiceRegistry
   ├─ Register Core Services (event bus, command bus, audit, identity)
   ├─ Discover and Register Modules
   │   ├─ Load module manifests
   │   ├─ Resolve dependencies (topological sort)
   │   ├─ Initialize each module
   │   └─ Register module services
   ├─ Seed Reference Data
   ├─ Start Background Workers
   └─ Signal READY (system_ready = True)
```

## Standard Module Structure

```
module-name/
├── __init__.py           # Module manifest, router registration
├── manifest.json         # Metadata, version, dependencies
├── domain/
│   ├── entities.py       # Rich domain entities with behavior
│   ├── value_objects.py  # Immutable value objects
│   ├── aggregates.py     # Aggregate roots with consistency boundaries
│   ├── events.py         # Domain events
│   ├── services.py       # Domain services (stateless)
│   └── repository.py     # Repository interfaces (abstract)
├── application/
│   ├── commands.py       # Command definitions
│   ├── queries.py        # Query definitions
│   ├── handlers.py       # Command/Query handlers
│   └── services.py       # Application services (orchestration)
├── infrastructure/
│   ├── repositories.py   # SQLAlchemy implementations
│   ├── models.py         # ORM models (SQLAlchemy mappers)
│   ├── migrations/       # Alembic migration scripts
│   └── adapters.py       # External service adapters
├── api/
│   ├── routes.py         # FastAPI route definitions (thin)
│   ├── schemas.py        # Pydantic request/response schemas
│   └── dependencies.py   # FastAPI DI
├── tests/
│   ├── test_domain.py
│   ├── test_application.py
│   └── test_api.py
└── README.md
```

## Module Registration (Decorator Pattern)

```python
@module(
    name="orders",
    version="2.1.0",
    dependencies=["identity", "patients", "laboratory"],
    events_published=["OrderCreated", "OrderValidated", "OrderCompleted"],
    events_subscribed=["PatientMerged", "LabDeactivated"],
)
class OrdersModule:
    ...
```

## CQRS Architecture

**Command Bus Pipeline:** Validation → Authorization → Audit → Transaction → Execute → Publish Event

**Query Bus Pipeline:** Validation → Authorization → Cache → Execute → Return DTO

## Platform Core Services

| Service | Responsibility |
|---------|---------------|
| Event Bus | Publish/Subscribe, topic routing, retry, DLQ, replay |
| Command Bus | Command dispatch, pipeline behaviors, handler resolution |
| Query Bus | Query dispatch, caching, read model optimization |
| Workflow Engine | State machine execution, approval flows, escalation timers |
| Rule Engine | Business/clinical/security/workflow rule evaluation |
| Configuration Service | Multi-source config (env→file→vault→DB), profile mgmt, hot reload |
| Notification Engine | Template rendering, multi-channel delivery (email/SMS/push/Telegram) |
| Scheduler | Cron-based task scheduling, SLA timers, retries |
| Audit Engine | Hash-chained immutable audit, HMAC anchors, chain verification |
| Search Service | Global text search, clinical search, semantic search via RAG |

---

# PHASE 03: DOMAIN ARCHITECTURE

## Enterprise Domain Catalog (30 domains)

| # | Domain | Type | Event Sourced |
|---|--------|------|:---:|
| 1 | **Identity** | Core | Yes |
| 2 | **Organizations** | Supporting | Yes |
| 3 | **Laboratory** | Core | Yes |
| 4 | **Patients** | Core | Yes |
| 5 | **Personnel** | Generic | No |
| 6 | **Specimens** | Core | Yes |
| 7 | **Orders** | Core | Yes |
| 8 | **Results** | Core | Yes |
| 9 | **Equipment** | Supporting | Yes |
| 10 | **Inventory** | Generic | Yes |
| 11 | **Quality** | Core | Yes |
| 12 | **Blood Bank** | Core | Yes |
| 13 | **Pathology** | Core | Yes |
| 14 | **Radiology** | Supporting | Yes |
| 15 | **Pharmacy** | Supporting | Yes |
| 16 | **Clinical** | Core | Yes |
| 17 | **Billing** | Generic | Yes |
| 18 | **Scheduling** | Generic | Yes |
| 19 | **Workflow** | Shared | Yes |
| 20 | **Notifications** | Shared | Yes |
| 21 | **Audit** | Shared | Yes |
| 22 | **Reporting** | Supporting | No |
| 23 | **Analytics** | Supporting | No |
| 24 | **AI** | Core | Yes |
| 25 | **Knowledge** | Supporting | No |
| 26 | **Public Health** | Core | Yes |
| 27 | **Research** | Supporting | Yes |
| 28 | **Integration** | Shared | Yes |
| 29 | **Configuration** | Shared | No |
| 30 | **Governance** | Supporting | Yes |

## Domain Dependency Rules

| Method | Allowed | When |
|--------|---------|------|
| Synchronous (REST/gRPC) | Yes | Commands/queries requiring immediate response |
| Asynchronous (Events) | Yes | State changes, notifications, long-running processes |
| Direct DB Access | **NEVER** | Violates bounded context isolation |
| Circular Dependencies | **NEVER** | Enforced by dependency graph validation at boot |

## Key Architecture Decisions

| ADR | Decision | Rationale |
|-----|----------|-----------|
| 001 | Modules communicate through events or service contracts | Prevents coupling; enables independent deployment |
| 002 | Each module has its own DB schema (schema-per-module) | Database-level isolation; independently evolvable |
| 003 | Cross-module queries go through Query Bus | Read models optimized independently of write models |
| 004 | All state mutations go through Command Bus | Consistent validation, authorization, audit pipeline |
| 005 | Domain events published via outbox pattern | Atomicity: event published iff transaction commits |
| 006 | Audit is a platform kernel service, not per-module | Immutable chain integrity requires single sequence |
| 007 | AI is a platform capability, not a standalone module | Every module consumes AI; AI has no domain logic |
| 008 | Offline/edge uses CQRS with local event store | CRDT-based conflict resolution for disconnected ops |
| 009 | Multi-tenancy: schema-per-tenant premium, shared standard | Cost vs. isolation tradeoff |
| 010 | FHIR is canonical API for external interoperability | Single standard across all healthcare domains |

---

## Migration Strategy (Current → Target)

The monolith `backend/app/` is refactored into modules incrementally:

1. **Extract Kernel** → `kernel/` with bootloader, service registry, config, health
2. **Extract Domain Exceptions** → Remove FastAPI imports from domain layer
3. **Module-by-module extraction** → Move each domain into its own module directory with standard structure
4. **Add event layer** → Introduce event bus for inter-module communication
5. **Add CQRS layer** → Command/Query buses with pipeline behaviors
6. **Add schema-per-module** → Alembic migrations create module-specific schemas
7. **Remove cross-module direct DB access** → All inter-module queries go through Query Bus
8. **Consolidate duplicated infrastructure** → Remove kernel mini-framework, keep one event bus
