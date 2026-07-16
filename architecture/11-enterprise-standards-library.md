# GULA Platform — Enterprise Standards Library

Version: 1.0 — 2026-07-15
Status: **DRAFT** — Architecture Review Board approval pending

---

## Table of Contents

1. [Naming Conventions](#1-naming-conventions)
2. [Repository Structure Standards](#2-repository-structure-standards)
3. [Folder Structure per Module](#3-folder-structure-per-module)
4. [Package Naming](#4-package-naming)
5. [Module Structure](#5-module-structure)
6. [Service Design Standards](#6-service-design-standards)
7. [Event Design Standards](#7-event-design-standards)
8. [Command/Query Design Standards](#8-commandquery-design-standards)
9. [DTO Design Standards](#9-dto-design-standards)
10. [FHIR Resource Mapping Standards](#10-fhir-resource-mapping-standards)
11. [REST API Standards](#11-rest-api-standards)
12. [GraphQL API Standards](#12-graphql-api-standards)
13. [gRPC API Standards](#13-grpc-api-standards)
14. [Database Design Standards](#14-database-design-standards)
15. [Versioning Strategy](#15-versioning-strategy)
16. [Logging Standards](#16-logging-standards)
17. [Tracing Standards](#17-tracing-standards)
18. [Configuration Standards](#18-configuration-standards)
19. [Secrets Management Standards](#19-secrets-management-standards)
20. [Caching Standards](#20-caching-standards)
21. [Monitoring Standards](#21-monitoring-standards)
22. [Testing Standards](#22-testing-standards)
23. [Documentation Standards](#23-documentation-standards)

---

## 1. Naming Conventions

### 1.1 Python (Backend)

| Element | Convention | Example |
|---------|-----------|---------|
| Modules | snake_case | `outbox_service.py` |
| Classes | PascalCase | `OutboxService`, `LabOrder` |
| Functions/Methods | snake_case | `resolve_lab_features()`, `create_order()` |
| Variables | snake_case | `lab_id`, `feature_flags` |
| Constants | UPPER_SNAKE_CASE | `MAX_ATTEMPTS`, `_DEFAULT_BASE_DELAY` |
| Private members | `_` prefix | `_TRANSITIONS`, `_get_state()` |
| Dunder methods | `__dunder__` | `__init__`, `__str__` |
| Type variables | PascalCase | `T`, `ResultType` |
| Enums | PascalCase + UPPER values | `class CircuitState(Enum): OPEN = "open"` |
| Dataclasses | PascalCase | `@dataclass class ServiceDescriptor` |
| Abstract classes | ABC suffix or `ABC` | `IdentityProvider` (ABC) |
| Exceptions | PascalCase + Error suffix | `InvalidTransitionError` |

### 1.2 TypeScript/JavaScript (Frontend)

| Element | Convention | Example |
|---------|-----------|---------|
| Files | camelCase | `authService.ts`, `patientCard.tsx` |
| Components | PascalCase | `PatientCard`, `LabDashboard` |
| Functions | camelCase | `fetchPatients()`, `submitOrder()` |
| Variables | camelCase | `labId`, `isAuthenticated` |
| Constants | UPPER_SNAKE_CASE | `MAX_RETRY_COUNT` |
| Interfaces | PascalCase + I prefix optional | `PatientData`, `ILabConfig` |
| Types | PascalCase | `LabTier`, `OrderStatus` |
| Hooks | camelCase + `use` prefix | `useAuth()`, `useFeatureFlags()` |
| Props | PascalCase + Props suffix | `PatientCardProps` |
| Enums | PascalCase | `enum OrderStatus { Pending, Completed }` |

### 1.3 SQL

| Element | Convention | Example |
|---------|-----------|---------|
| Table names | snake_case (plural) | `lab_orders`, `audit_logs` |
| Column names | snake_case | `created_at`, `lab_id` |
| Primary keys | `id` | `id INTEGER PRIMARY KEY` |
| Foreign keys | `{table}_id` | `lab_id`, `patient_id` |
| Indexes | `ix_{table}_{column}` | `ix_lab_orders_status` |
| Unique constraints | `uq_{table}_{column}` | `uq_patients_national_id` |
| Check constraints | `ck_{table}_{rule}` | `ck_lab_results_version` |
| Functions | UPPER_SNAKE_CASE | `RESOLVE_CITIZEN_MERGE()` |
| Migrations | `{date}_{description}` | `20260505_0001_sndhs_phase1_extend_patients` |

### 1.4 Infrastructure

| Element | Convention | Example |
|---------|-----------|---------|
| Docker images | `gula-{service}` | `gula-backend`, `gula-worker` |
| Docker containers | `gula-{service}` | `gula-postgres`, `gula-redis` |
| Environment variables | UPPER_SNAKE_CASE | `DATABASE_URL`, `SECRET_KEY` |
| Kubernetes namespaces | kebab-case | `gula-platform`, `gula-monitoring` |
| DNS records | kebab-case | `api.gula.health`, `lab.gula.health` |

---

## 2. Repository Structure Standards

### 2.1 Monorepo Layout

```
gula-platform/
├── backend/                  # Python FastAPI backend (monolith)
│   ├── app/                  # Application code
│   │   ├── main.py           # FastAPI app entry point
│   │   ├── config.py         # Configuration loading
│   │   ├── database.py       # DB engine + pool
│   │   ├── worker.py         # Background worker
│   │   ├── routes/           # API route modules
│   │   ├── models/           # SQLAlchemy ORM models
│   │   ├── services/         # Business logic services
│   │   ├── domain/           # Domain logic (DDD)
│   │   ├── core/             # Core infrastructure
│   │   ├── security/         # Auth, RBAC, ABAC, encryption
│   │   ├── kernel/           # Platform kernel
│   │   ├── platform/         # Platform capabilities
│   │   ├── clinical/         # Clinical domain
│   │   ├── lims/             # LIMS domain
│   │   ├── national/         # National/citizen domain
│   │   ├── ehr/              # EHR domain
│   │   ├── edge/             # Edge platform
│   │   ├── ai/               # Clinical AI
│   │   ├── financial/        # Financial engine
│   │   ├── integration/      # Integration (DDD structured)
│   │   ├── interoperability/ # HL7/FHIR interop
│   │   ├── gateways/         # External API gateways
│   │   ├── notifications/    # Notification service
│   │   ├── audit/            # Audit logging
│   │   ├── tasks/            # Background tasks
│   │   └── firewall/         # API firewall
│   ├── tests/                # Test suite
│   ├── migrations/           # Alembic migrations
│   └── alembic.ini           # Alembic configuration
├── services/                 # Future microservices
│   ├── device_bridge/        # LabLink-Core (ASTM/HL7)
│   ├── lab/                  # Future: Lab service
│   ├── order/                # Future: Order service
│   └── ...                   # Other future services
├── shared/                   # Shared library
│   ├── auth/                 # Authentication shared code
│   ├── models/               # Shared SQLAlchemy mixins
│   ├── rbac/                 # RBAC shared definitions
│   ├── events/               # Event type constants
│   ├── logging/              # Structured logging
│   ├── security/             # Encryption, HMAC
│   ├── ai/                   # AI provider/client
│   ├── cache/                # Cache abstractions
│   ├── di_container/         # DI container
│   ├── domain/               # Domain abstractions
│   ├── design_system/        # Shared design system
│   └── ...                   # Other shared modules
├── frontend-v2/              # React + Firebase SPA
├── client/                   # tRPC + React client
├── frontend/                 # Static HTML PWA
├── edge_agent/               # Offline edge agent
├── nhop-platform/            # National Health Oversight Platform
├── ai/                       # AI modules (top-level)
├── architecture/             # Architecture docs
├── docs/                     # Documentation
├── scripts/                  # Operational scripts
├── config/                   # Infrastructure config
│   ├── haproxy/              # Load balancer config
│   ├── prometheus/           # Prometheus config
│   └── grafana/              # Grafana dashboards
├── k8s/                      # Kubernetes manifests
├── cloudflare/               # Cloudflare config
├── digitalocean/             # DigitalOcean config
└── supabase/                 # Supabase integration
```

### 2.2 Module Boundaries

- **Kernel** (`backend/app/kernel/`) must never depend on business modules
- **Business modules** depend on Kernel but not on each other
- **Shared** (`shared/`) must remain framework-independent
- **No circular dependencies** are allowed
- **Every module must expose clear interfaces**

---

## 3. Folder Structure per Module

### 3.1 DDD-Aligned Module Structure

Every domain module follows this structure where applicable:

```
module/
├── __init__.py               # Module exports
├── domain/                   # Domain layer
│   ├── entities.py           # Domain entities
│   ├── value_objects.py      # Value objects
│   ├── events.py             # Domain events
│   ├── repositories.py       # Repository interfaces
│   └── services.py           # Domain services
├── application/              # Application layer
│   ├── commands/             # Command handlers
│   ├── queries/              # Query handlers
│   ├── event_handlers/       # Event handlers
│   └── dto.py                # Data transfer objects
├── infrastructure/           # Infrastructure layer
│   ├── repository_impl.py    # Repository implementations
│   ├── db_models.py          # ORM models (if separate)
│   └── external_services.py  # External integrations
├── presentation/             # API layer
│   ├── routes.py             # Route definitions
│   └── schemas.py            # Request/response schemas
└── tests/                    # Module-specific tests
```

### 3.2 Current Module Examples

- `backend/app/ehr/` — Follows this structure (commands/, queries/, events/, models/, routes/, services/)
- `backend/app/integration/` — Follows this structure (application/, domain/, infrastructure/, presentation/)
- `backend/app/national/` — Has domain/, services/, api/, events/, repositories/, security/
- `backend/app/national/observability/` — Follows this structure (api/, application/, domain/, infrastructure/)

---

## 4. Package Naming

### 4.1 Convention

Packages follow the pattern: `{domain}.{component}`

| Package | Convention | Example |
|---------|-----------|---------|
| Core domain | `app.{domain}` | `app.lims`, `app.national` |
| Component | `app.{domain}.{component}` | `app.national.domain`, `app.national.services` |
| Sub-component | `app.{domain}.{component}.{sub}` | `app.national.security.abac` |
| Shared | `shared.{domain}` | `shared.auth`, `shared.encryption` |
| Tests | `tests.{domain}` | `tests.test_security`, `tests.test_patient_card` |

### 4.2 Examples from Codebase

- `backend.app.routes.patients`
- `backend.app.services.outbox_service`
- `backend.app.core.self_healing`
- `backend.app.security.rbac`
- `backend.app.national.domain.citizen`
- `backend.app.national.security.abac`
- `backend.app.kernel.event_bus.bus`
- `shared.di_container.engine`

---

## 5. Module Structure

### 5.1 Capability-Based, Self-Contained

Each module is a self-contained capability:

- **Has its own domain logic** — entities, value objects, events
- **Has its own application services** — commands, queries, handlers
- **Has its own API surface** — routes, schemas
- **Has its own tests** — unit + integration
- **Declares its dependencies** — other modules, external services
- **Exports a clear interface** — what it provides, what it needs
- **CQRS-ready** — separates commands from queries

### 5.2 Module Manifest

Each module should have a manifest or metadata:

```python
# Example module metadata (from backend/app/kernel/module/metadata.py)
@dataclass
class ModuleMetadata:
    name: str
    version: str
    description: str
    dependencies: list[str]
    capabilities: list[str]
    status: ModuleStatus
```

### 5.3 Module Discovery

Modules are auto-discovered via `backend/app/kernel/module/discovery.py` and loaded by `backend/app/kernel/module/loader.py` with dependency resolution by `backend/app/kernel/module/resolver.py`.

---

## 6. Service Design Standards

### 6.1 Principles

- **Stateless** — No instance state; all state in DB/Redis
- **Idempotent** — Same input always produces same result
- **Observable** — OpenTelemetry traced, structured logged
- **Thin** — Orchestrates domain objects, doesn't implement domain logic
- **Dependency injected** — Constructor injection via `shared/di_container/`

### 6.2 Service Pattern

```python
class OrderService:
    def __init__(self, db: Session, event_bus: EventBus):
        self._db = db
        self._event_bus = event_bus

    def create_order(self, lab_id: int, patient_id: int, ...) -> Order:
        # 1. Validate business rules (domain)
        # 2. Persist (infrastructure)
        # 3. Publish event (infrastructure)
        # 4. Return DTO
```

### 6.3 Code References

- `backend/app/services/order_service.py` — Order service
- `backend/app/services/patient_service.py` — Patient service
- `backend/app/services/outbox_service.py` — Outbox service
- `backend/app/national/services/citizen_service.py` — Citizen service
- `backend/app/ehr/services/` — EHR services

---

## 7. Event Design Standards

### 7.1 CloudEvents 1.0 Compliance

All events follow the CloudEvents 1.0 specification:

| Attribute | Description | Required |
|-----------|-------------|----------|
| `id` | Unique event ID (ULID) | Yes |
| `source` | Event origin (e.g., `/lims/orders`) | Yes |
| `specversion` | `1.0` | Yes |
| `type` | Event type (e.g., `order.created`) | Yes |
| `datacontenttype` | `application/json` | Yes |
| `data` | Event payload | Yes |
| `time` | ISO 8601 timestamp | Yes |
| `subject` | Entity ID | No |
| `traceparent` | W3C trace context | No |

### 7.2 Event Naming

Pattern: `{domain}.{entity}.{action}` in past tense

| Event | Example |
|-------|---------|
| Order created | `order.created` |
| Result validated | `result.validated` |
| Patient merged | `patient.merged` |
| Citizen registered | `citizen.registered` |
| Lab configured | `lab.configured` |

### 7.3 Event Schema

Events must have a typed, versioned schema:

```python
# From shared/events/constants.py
@dataclass
class DomainEvent:
    event_id: str          # ULID
    event_type: str        # "order.created"
    event_version: int     # 1
    aggregate_type: str    # "order"
    aggregate_id: str      # Order ULID
    data: dict             # Event payload
    metadata: dict         # Correlation, trace, audit
    timestamp: str         # ISO 8601
```

### 7.4 Event Versioning

- Events are versioned with integer version numbers
- Breaking changes → new event version (e.g., `order.created.v2`)
- Consumers must declare which versions they support
- Event bus supports version translation (`backend/app/kernel/event_bus/versioning.py`)

### 7.5 Code References

- `backend/app/lims/events.py` — LIMS events
- `backend/app/national/events/` — National events (8 event modules)
- `backend/app/ehr/events/` — EHR events
- `backend/app/kernel/event_bus/events.py` — Kernel events
- `shared/events/constants.py` — Event type constants
- `backend/app/models/outbox.py` — Outbox event model
- `backend/app/kernel/event_bus/versioning.py` — Event versioning

---

## 8. Command/Query Design Standards

### 8.1 CQRS Pattern

Commands and queries are separated at the application layer:

```python
# Command (mutates state)
class CreateOrderCommand:
    lab_id: int
    patient_id: int
    test_type_ids: list[int]
    doctor_id: int | None = None

# Query (returns data)
class GetOrderQuery:
    order_id: int
    include_results: bool = False
```

### 8.2 Handler Pattern

```python
class CreateOrderHandler:
    def __init__(self, db: Session, event_bus: EventBus):
        ...

    def handle(self, command: CreateOrderCommand) -> OrderDTO:
        # Validate command
        # Execute domain logic
        # Persist
        # Publish events
        # Return DTO
```

### 8.3 Code References

- `backend/app/ehr/commands/` — EHR command handlers
- `backend/app/ehr/queries/` — EHR query handlers
- `backend/app/ehr/services/` — EHR service layer

---

## 9. DTO Design Standards

### 9.1 Pydantic v2

All DTOs use Pydantic v2 models:

```python
from pydantic import BaseModel, Field

class OrderCreateRequest(BaseModel):
    patient_id: int = Field(..., gt=0)
    test_type_ids: list[int] = Field(..., min_length=1)
    priority: str = Field(default="routine")
    notes: str | None = None

class OrderResponse(BaseModel):
    id: int
    status: str
    created_at: datetime
    patient: PatientSummary
    test_types: list[TestTypeSummary]
```

### 9.2 Request/Response Separation

- **Request schemas** — Input validation, never reused as responses
- **Response schemas** — Output formatting, never reused as inputs
- **Separate schemas per endpoint** — Not shared across different use cases

### 9.3 Code References

- `backend/app/national/api/` — National API schemas
- `backend/app/services/mpi/schemas.py` — MPI schemas
- `backend/app/ehr/routes/` — EHR route schemas
- `shared/schemas/pagination.py` — Shared pagination schema
- `shared/schemas/response.py` — Shared response schema

---

## 10. FHIR Resource Mapping Standards

### 10.1 R4/R5 Mapping

FHIR resources are mapped in:

| FHIR Resource | GULA Entity | Location |
|---------------|-------------|----------|
| Patient | `Citizen` + `Patient` | `backend/app/national/fhir/patient.py` |
| Practitioner | `Practitioner` | `backend/app/national/fhir/practitioner.py` |
| Organization | `Lab` + `Organization` | `backend/app/national/fhir/organization.py` |
| Observation | `LabResult` | `backend/app/national/fhir/observation.py` |
| Encounter | `Encounter` + `Visit` | `backend/app/national/fhir/encounter.py` |
| Bundle | Bulk operations | `backend/app/national/fhir/bundle.py` |
| Search | FHIR search API | `backend/app/national/fhir/search.py` |

### 10.2 Mapping Rules

- One GULA entity may map to multiple FHIR resources
- FHIR extensions used for GULA-specific fields
- Must support both R4 and R5 output
- Search parameters follow FHIR R4 search API spec
- Terminology server integration via `backend/app/national/fhir/terminology.py`

### 10.3 Code References

- `backend/app/national/fhir/` — FHIR resource mapping (10 modules)
- `backend/app/lims/fhir_mappers.py` — LIMS-to-FHIR mapping
- `backend/app/interoperability/` — HL7/FHIR interop layer
- `backend/app/ehr/` — EHR FHIR support

---

## 11. REST API Standards

### 11.1 URL Structure

```
/api/{version}/{resource}[/{id}][/{sub-resource}][?{query}]
```

Examples:
- `/api/v1/patients/{patient_id}`
- `/api/v1/patients/{patient_id}/orders`
- `/api/v1/orders?status=pending&lab_id=42`

### 11.2 Versioning

- Version in URL path: `/api/v1/`, `/api/v2/`
- Internal routes (not versioned): `/health`, `/metrics`
- Versioning via `backend/app/routes/` module organization

### 11.3 RESTful Resource Naming

| Operation | HTTP Method | URL Pattern |
|-----------|-------------|-------------|
| List | GET | `/api/v1/patients` |
| Create | POST | `/api/v1/patients` |
| Read | GET | `/api/v1/patients/{id}` |
| Update | PUT | `/api/v1/patients/{id}` |
| Partial Update | PATCH | `/api/v1/patients/{id}` |
| Delete | DELETE | `/api/v1/patients/{id}` |

### 11.4 Pagination

```json
{
    "data": [...],
    "pagination": {
        "page": 1,
        "per_page": 50,
        "total": 1000,
        "total_pages": 20,
        "next": "/api/v1/patients?page=2",
        "prev": null
    }
}
```

From `shared/schemas/pagination.py` — shared pagination schema.

### 11.5 Error Format

```json
{
    "error": "validation_error",
    "detail": "Invalid patient ID",
    "detail_ar": "معرف المريض غير صالح",
    "errors": [
        {
            "field": "patient_id",
            "message": "must be a positive integer",
            "message_ar": "يجب أن يكون رقمًا صحيحًا موجبًا"
        }
    ]
}
```

### 11.6 HTTP Status Codes

| Code | Usage |
|------|-------|
| 200 | Success (GET, PUT, PATCH) |
| 201 | Created (POST) |
| 204 | No Content (DELETE) |
| 400 | Bad Request (validation) |
| 401 | Unauthorized (no auth) |
| 403 | Forbidden (no permission) |
| 404 | Not Found |
| 409 | Conflict (state conflict) |
| 413 | Payload Too Large |
| 422 | Unprocessable Entity |
| 423 | Locked (immutable resource) |
| 429 | Too Many Requests |
| 500 | Internal Server Error |
| 503 | Service Unavailable |

### 11.7 HATEOAS

Responses include related resource links:

```json
{
    "data": {
        "id": 42,
        "status": "completed"
    },
    "_links": {
        "self": "/api/v1/orders/42",
        "patient": "/api/v1/patients/7",
        "results": "/api/v1/orders/42/results",
        "validate": {
            "href": "/api/v1/orders/42/validate",
            "method": "POST"
        }
    }
}
```

### 11.8 Arabic Language Support

- All error responses include `{field}_ar` for Arabic translations
- Content negotiation via `Accept-Language` header
- Arabic-first design enforced across all API responses

### 11.9 Code References

- `shared/schemas/pagination.py` — Pagination schema
- `shared/schemas/response.py` — Standard response schema
- `backend/app/routes/` — All REST route implementations

---

## 12. GraphQL API Standards

### 12.1 Schema-First

GraphQL APIs (where used) follow schema-first design:

```graphql
type Patient {
    id: ID!
    name: String!
    dateOfBirth: Date
    orders: [Order!]
}

type Query {
    patient(id: ID!): Patient
    patients(labId: ID!, page: Int, perPage: Int): PatientConnection!
}

type Mutation {
    createPatient(input: PatientInput!): Patient!
}
```

### 12.2 Resolvers

- Resolvers are thin — delegate to services
- DataLoader pattern for N+1 prevention
- Authentication via context (JWT validation)

### 12.3 Code References

GraphQL is primarily used in the frontend layer; backend may expose GraphQL via:
- `backend/app/routes/` — Future: GraphQL endpoint

---

## 13. gRPC API Standards

### 13.1 Proto-First

gRPC APIs (where used) are defined with proto files:

```protobuf
service CitizenService {
    rpc GetCitizen (GetCitizenRequest) returns (Citizen);
    rpc ResolveIdentity (ResolveIdentityRequest) returns (IdentityResponse);
    rpc StreamUpdates (StreamRequest) returns (stream CitizenUpdate);
}
```

### 13.2 Streaming

- Server-side streaming for bulk operations
- Bidirectional streaming for real-time device data
- Unary RPCs for standard CRUD

### 13.3 Code References

- `services/device_bridge/` — Potential gRPC for device communication
- Future: gRPC gateway for device bridge → backend

---

## 14. Database Design Standards

### 14.1 Primary Keys

- All tables use auto-incrementing integer primary keys (legacy) OR ULIDs (new tables)
- New tables should use ULID for distributed ID generation
- Composite primary keys avoided; use surrogate keys

### 14.2 ULID Usage

From `backend/app/national/domain/citizen.py:10`:

```python
class Citizen(BaseEntity):
    __tablename__ = "national_citizens"
    # Uses ULID via inherited id field from BaseEntity
```

### 14.3 Tenant Isolation

- Every lab-scoped table has a `lab_id` column with foreign key to `labs.id`
- Every query must filter by `current_user.lab_id`
- Tenant mixin: `shared/models/base.py::TenantMixin`

### 14.4 Audit Columns

Every table should have (via mixins):

| Column | Type | Purpose |
|--------|------|---------|
| `created_at` | `DateTime(timezone=True)` | Creation timestamp |
| `updated_at` | `DateTime(timezone=True)` | Last update timestamp |
| `created_by` | `Integer` | User ID who created |
| `updated_by` | `Integer` | User ID who last updated |
| `deleted_at` | `DateTime(timezone=True)` | Soft delete timestamp |

### 14.5 Soft Delete

- Records are soft-deleted via `deleted_at` column
- Queries filter `WHERE deleted_at IS NULL`
- Referential integrity maintained for active records
- Soft delete mixin: `shared/models/base.py::SoftDeleteMixin`

### 14.6 Optimistic Locking

- `version` column (integer) for concurrency control
- Checked on every `LabResult` mutation
- Incremented on each update
- Optimistic lock mixin: `shared/models/base.py::OptimisticLockMixin`

### 14.7 Indexing Standards

- Index all foreign keys
- Index all columns used in WHERE, JOIN, ORDER BY
- Composite indexes for multi-column query patterns
- Partial indexes for filtered queries (e.g., `WHERE deleted_at IS NULL`)
- GiST indexes for full-text search where needed

### 14.8 Code References

- `shared/models/base.py` — Shared model mixins (AuditMixin, SoftDeleteMixin, TenantMixin, TimestampMixin, OptimisticLockMixin)
- `backend/app/models/base.py` — Backend model re-exports
- `backend/app/database.py` — Engine and session configuration
- `backend/app/national/domain/citizen.py` — ULID-based entity example

---

## 15. Versioning Strategy

### 15.1 Semantic Versioning (APIs)

Format: `MAJOR.MINOR.PATCH`

- **MAJOR** — Breaking API changes (incompatible)
- **MINOR** — Backward-compatible additions
- **PATCH** — Backward-compatible bug fixes

### 15.2 Calendar Versioning (Releases)

Format: `YYYY.MM.RELEASE`

- `2026.07.1` — July 2026, first release

### 15.3 App Version

Current: `2.1.0` (from `backend/app/config.py:65`)

### 15.4 Breaking Change Policy

- Breaking changes require deprecation notice for at least one release cycle
- Deprecated endpoints return `Sunset` header
- Migration guide published with each breaking change
- Old API version maintained for minimum 3 months after deprecation

---

## 16. Logging Standards

### 16.1 Structured JSON Logging

All logs are structured JSON via `shared/logging/`:

```json
{
    "timestamp": "2026-07-15T10:30:00.123Z",
    "level": "INFO",
    "logger": "gula.orders",
    "message": "Order created successfully",
    "request_id": "req_abc123",
    "user_id": 42,
    "lab_id": 7,
    "order_id": 1234,
    "duration_ms": 45,
    "trace_id": "0af7651916cd43dd8448eb211c80319c"
}
```

### 16.2 Correlation IDs

- Every request gets a unique `X-Request-ID` via `RequestIDMiddleware`
- Correlation ID flows through all downstream calls
- Database queries logged with same correlation context

### 16.3 Log Levels

| Level | Usage |
|-------|-------|
| `DEBUG` | Development-only details |
| `INFO` | Normal operations (request start/end, state transitions) |
| `WARNING` | Degraded behavior (retries, fallbacks) |
| `ERROR` | Failures requiring investigation |
| `CRITICAL` | System-threatening failures (alert ops) |

### 16.4 Log Categories

| Logger | Scope |
|--------|-------|
| `gula` | Root logger |
| `gula.orders` | Order service |
| `gula.results` | Results service |
| `gula.auth` | Authentication |
| `gula.database` | Database operations |
| `gula.self_healing` | Self-healing system |
| `gula.outbox` | Outbox publisher |
| `gula.external_api` | Gateway calls |
| `gula.features` | Feature flags |
| `gula.config` | Configuration |

### 16.5 Code References

- `backend/app/core/logging_config.py` — Logging configuration
- `shared/logging/config.py` — Shared logging setup
- `shared/logging/__init__.py` — Logging exports

---

## 17. Tracing Standards

### 17.1 OpenTelemetry

- Distributed tracing via OpenTelemetry
- W3C Trace Context propagation (`traceparent` header)
- Automatic instrumentation for FastAPI, SQLAlchemy, HTTPX

### 17.2 Trace Context

Every request carries:

- `trace_id` — 16-byte random identifier (entire trace)
- `span_id` — 8-byte random identifier (single operation)
- `trace_flags` — Sampling decision

### 17.3 Span Naming

| Operation | Span Name |
|-----------|-----------|
| HTTP Request | `{method} {path}` |
| Database Query | `db.{operation}.{table}` |
| Gateway Call | `gateway.{name}.{action}` |
| Background Job | `worker.{job_name}` |

### 17.4 Code References

- `shared/observability/tracer.py` — OpenTelemetry tracer setup
- `backend/app/main.py` — Sentry tracing integration (optional)

---

## 18. Configuration Standards

### 18.1 Environment-Based Configuration

All configuration is environment-based via env vars:

- `.env.example` — Template, tracked in git
- `.env` — Real secrets, gitignored
- `.env.production` — Production template, tracked (no real secrets)

### 18.2 Hierarchical Config

```
Environment variables (highest)
    ↓
.env file (development)
    ↓
Defaults in config.py
```

### 18.3 Configuration Validation

From `backend/app/config.py`:

- Missing secrets → hard fail on startup
- Weak secrets → rejected via `_is_weak_secret()` check
- Invalid RUNTIME_MODE → `sys.exit(1)`
- All env vars validated and typed before use

### 18.4 Configuration Categories

| Category | Example Vars | Location |
|----------|-------------|----------|
| App | `APP_NAME`, `APP_VERSION`, `BASE_URL` | `config.py` |
| Database | `DATABASE_URL`, `READ_REPLICA_URL` | `config.py` |
| Security | `SECRET_KEY`, `ENCRYPTION_KEY` | `config.py` |
| JWT | `JWT_ALGORITHM`, `JWT_EXPIRE_MINUTES` | `config.py` |
| Redis | `REDIS_URL`, `REDIS_PASSWORD` | `config.py` |
| Features | `SNDHS_ENABLE_*`, `ENABLE_FINANCIAL_ENGINE` | `config.py` |
| AI | `GEMINI_API_KEY`, `AI_MODEL` | `config.py` |
| External | `GOV_NID_MODE`, `TELEGRAM_BOT_TOKEN` | `config.py` |
| Observability | `SENTRY_DSN`, `ALERT_WEBHOOK_URL` | `config.py` |

### 18.5 Code References

- `backend/app/config.py` — Main configuration module
- `backend/app/kernel/config/` — Kernel configuration
- `shared/config/loader.py` — Config loader
- `.env.example` — Environment template
- `docker-compose.yml` — Container environment variables

---

## 19. Secrets Management Standards

### 19.1 Principles

- **Never hardcoded** — No default passwords, tokens, or keys in code
- **Never logged** — Secrets redacted from all log output
- **Encrypted at rest** — Database encryption for PII/PHI
- **Rotated regularly** — Key rotation policy enforced
- **Audited** — Access to secrets logged

### 19.2 Required Secrets

From `backend/app/config.py`:

| Secret | Purpose | Weakness Check |
|--------|---------|---------------|
| `SECRET_KEY` | JWT signing | Yes (`_is_weak_secret`) |
| `ENCRYPTION_KEY` | PII encryption | Yes |
| `NID_HMAC_KEY` | National ID hashing | Yes |
| `REFRESH_TOKEN_SECRET` | Refresh token signing | Yes |
| `DEVICE_HMAC_KEY` | Device authentication | Yes |

### 19.3 Key Generation

From `Makefile: secrets-gen`:

```bash
make secrets-gen
# Outputs strong random values for all secrets
```

### 19.4 Environment Rules

- `.env` is gitignored — never commit secrets
- `.env.example` has placeholder values — never real secrets
- `.env.production` has variable names only — populated by deployment tooling

### 19.5 Code References

- `backend/app/config.py:80-100` — Weak secret detection
- `Makefile` — `secrets-gen` target
- `.env.example` — Environment template
- `shared/security/encryption.py` — Encryption utilities

---

## 20. Caching Standards

### 20.1 Multi-Tier Caching

| Tier | Technology | Use Case | TTL |
|------|-----------|----------|-----|
| L1 (Application) | In-process dict | Hot data, feature flags | Seconds |
| L2 (Distributed) | Redis | Session, rate limits, API cache | Minutes |
| L3 (Edge) | Cloudflare CDN | Static assets, public data | Hours |

### 20.2 Cache-Aside Pattern (Default)

```
Read:  Check cache → if miss → read DB → write cache → return
Write: Write DB → invalidate cache
```

### 20.3 Cache Key Convention

```
{domain}:{entity}:{id}:{field}
```

Examples:
- `lab:42:features`
- `patient:7:summary`
- `order:1234:results`
- `rate_limit:42:api:orders`

### 20.4 Invalidation Strategy

- Write-through cache invalidation on mutation
- TTL-based expiry for all cached items
- Manual cache clear for admin operations
- Cache warming for critical data on startup

### 20.5 Code References

- `backend/app/core/cache_manager.py` — Cache management
- `backend/app/security/redis_client.py` — Redis client
- `shared/cache/backends.py` — Cache backend abstractions
- `shared/cache/__init__.py` — Cache exports

---

## 21. Monitoring Standards

### 21.1 RED Metrics (Services)

| Metric | Description | Source |
|--------|-------------|--------|
| Rate | Requests per second | RequestTimingMiddleware |
| Errors | Failed requests per second | App logs + middleware |
| Duration | Request latency (P50/P95/P99) | RequestTimingMiddleware |

### 21.2 USE Metrics (Resources)

| Metric | Description | Source |
|--------|-------------|--------|
| Utilization | CPU, memory, connection pool % | `get_pool_status()` |
| Saturation | Queue depth, pressure | Circuit breaker, concurrency |
| Errors | Resource errors | System metrics |

### 21.3 SLOs/SLIs

| Metric | Target | Measurement |
|--------|--------|-------------|
| API Availability | ≥ 99.9% | Uptime / total time |
| API Latency (P95) | < 500ms | RequestTimingMiddleware |
| DB Query Time (P95) | < 100ms | Database instrumentation |
| Error Rate | < 0.1% | Failed requests / total |
| Circuit Breaker | Never OPEN > 5 min | Self-healing metrics |

### 21.4 Health Scoring

From `backend/app/core/self_healing.py` — `_health_alert_loop`:

| Grade | Score | Meaning |
|-------|-------|---------|
| GREEN | All healthy | Normal operation |
| YELLOW | Degraded but functional | Warning |
| RED | Critical failure | Immediate attention |

### 21.5 Code References

- `backend/app/routes/metrics.py` — Prometheus metrics endpoint
- `backend/app/core/self_healing.py` — Health scoring and alerting
- `config/prometheus/` — Prometheus scrape configs
- `config/grafana/` — Grafana dashboards
- `shared/metrics/collector.py` — Metrics collection utilities

---

## 22. Testing Standards

### 22.1 Test Pyramid

```
        ╱─────╲
       ╱  E2E  ╲       ← 5% (critical paths)
      ╱─────────╲
     ╱  Contract ╲     ← 10% (API, integration points)
    ╱─────────────╲
   ╱  Integration  ╲    ← 25% (service, DB, external)
  ╱─────────────────╲
 ╱    Unit Tests      ╲  ← 60% (domain, logic, edge cases)
╱───────────────────────╲
```

### 22.2 Coverage Targets

| Type | Target | Location |
|------|--------|----------|
| Line coverage | ≥ 80% | `backend/tests/` |
| Branch coverage | ≥ 70% | `backend/tests/` |
| Mutation testing | ≥ 60% | `backend/tests/` |

### 22.3 Test Types

| Type | Framework | What It Covers |
|------|-----------|----------------|
| Unit | pytest | Domain logic, services, utilities |
| Integration | pytest + test DB | Routes, database, APIs |
| E2E | pytest + full stack | Critical user journeys |
| Contract | pytest + PACT | API contracts (future) |
| Chaos | pytest + Chaos Toolkit | Resilience patterns |

### 22.4 Test Structure

Tests mirror the source tree:

```
backend/tests/
├── test_security.py          # Auth, JWT, RBAC, encryption
├── test_comprehensive.py     # Full integration across major routes
├── test_stress.py            # Stress and load tests
├── test_patient_card.py      # QR card system
├── test_mpi_matcher.py       # MPI deduplication
├── test_outbox_service.py    # Outbox pattern
├── test_feature_flags.py     # Feature flag system
├── test_edge_platform.py     # Edge synchronization
├── test_stability_assertions.py  # Data integrity
├── test_system_improvements.py   # Clinical interpretation
├── chaos/                    # Chaos testing suite
└── ...                       # Additional test modules
```

### 22.5 Running Tests

```bash
make test            # pytest tests/ -v
make ci              # syntax-gate + lint + docker build
make scenario-test   # End-to-end load test
make integrity-test  # Concurrent order validation
make chaos           # Full chaos suite
```

### 22.6 Code References

- `backend/tests/` — 28 test modules
- `Makefile` — Test targets
- `.github/workflows/ci.yml` — CI pipeline with testing stages
- `tests/chaos/` — Chaos testing suite

---

## 23. Documentation Standards

### 23.1 ADR Required

Every significant architecture decision must have an ADR (Architecture Decision Record):

- Format: `docs/adr/{YYYYMMDD}-{title}.md`
- Template: `docs/templates/adr-template.md`
- Statuses: PROPOSED → ACCEPTED → DEPRECATED → SUPERSEDED

### 23.2 OpenAPI First

- All REST APIs documented via OpenAPI (auto-generated by FastAPI + Pydantic)
- `/docs` and `/redoc` endpoints for human-readable docs
- Production docs protected by `DocsAuthMiddleware`

### 23.3 README Per Module

Every module directory should have:
- `README.md` explaining purpose, API surface, and code examples
- Architecture references linking to broader docs

### 23.4 Documentation Standards

| Document | Location | Required |
|----------|----------|----------|
| ADR | `docs/adr/{id}-{title}.md` | For architecture decisions |
| API Docs | Auto-generated via OpenAPI | Yes |
| README | Per-module `README.md` | Yes |
| Architecture | `architecture/` | Centralized architecture docs |
| Runbook | `docs/runbooks/` | Operational procedures |
| Changelog | `CHANGELOG.md` | Release notes |
| Migration Guide | `docs/migration-*.md` | Breaking changes |

### 23.5 Code References

- `docs/adr/` — Architecture Decision Records
- `docs/templates/adr-template.md` — ADR template
- `docs/runbooks/` — Operational runbooks
- `backend/app/lims/README.md` — Example module README
- `backend/app/national/ADR.md` — National layer ADR
- `backend/app/national/CHANGELOG.md` — National layer changelog

---

## Document Version History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-07-15 | Architecture Team | Initial enterprise standards library |

**Review Cycle**: This document must be reviewed and updated quarterly or when significant architectural changes occur.
