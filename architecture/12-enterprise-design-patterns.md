# GULA Platform — Enterprise Design Patterns Catalog

Version: 1.0 — 2026-07-15
Status: **DRAFT** — Architecture Review Board approval pending

---

## Table of Contents

1. [Repository Pattern](#1-repository-pattern)
2. [Unit of Work](#2-unit-of-work)
3. [Specification Pattern](#3-specification-pattern)
4. [CQRS](#4-cqrs)
5. [Event Sourcing](#5-event-sourcing)
6. [Outbox Pattern](#6-outbox-pattern)
7. [Saga Pattern](#7-saga-pattern)
8. [Circuit Breaker](#8-circuit-breaker)
9. [Retry Pattern](#9-retry-pattern)
10. [Bulkhead Pattern](#10-bulkhead-pattern)
11. [Idempotency Pattern](#11-idempotency-pattern)
12. [Caching Patterns](#12-caching-patterns)
13. [Feature Flags](#13-feature-flags)
14. [Plugin Pattern](#14-plugin-pattern)
15. [Adapter Pattern](#15-adapter-pattern)
16. [Strategy Pattern](#16-strategy-pattern)
17. [Factory Pattern](#17-factory-pattern)

---

## 1. Repository Pattern

### 1.1 Intent

Provide a collection-like interface for accessing domain objects while hiding storage details. Centralizes query logic and provides a single point for caching, audit, and tenant isolation.

### 1.2 Structure

```
Interface: Repository[T]
├── get(id) → T
├── find(specification) → list[T]
├── add(entity) → T
├── update(entity) → T
├── delete(entity) → None
└── count(specification) → int
```

### 1.3 When to Use

- When you need to abstract database access
- When you need centralized caching, audit, or logging for DB operations
- When you need to switch storage backends
- When your domain logic needs a collection-like interface

### 1.4 When Not to Use

- Simple CRUD with no business logic
- When a simple ORM query is sufficient
- When the abstraction adds unnecessary complexity

### 1.5 Existing Code

- `backend/app/national/repositories/citizen_repository.py` — Citizen repository
- `backend/app/national/repositories/base.py` — Base repository with tenant isolation
- `backend/app/national/domain/` — Repository interfaces per domain entity

### 1.6 Implementation

```python
# From backend/app/national/repositories/base.py
class BaseRepository[T]:
    def __init__(self, db: Session):
        self._db = db

    def get(self, id: Any) -> T | None:
        return self._db.query(self._model).filter(self._model.id == id).first()

    def find(self, spec: Specification) -> list[T]:
        query = self._db.query(self._model)
        query = spec.apply(query)
        return query.all()

    def add(self, entity: T) -> T:
        self._db.add(entity)
        self._db.flush()
        return entity

    def update(self, entity: T) -> T:
        self._db.merge(entity)
        self._db.flush()
        return entity

    def delete(self, entity: T) -> None:
        self._db.delete(entity)
        self._db.flush()
```

---

## 2. Unit of Work

### 2.1 Intent

Maintain a list of objects affected by a business transaction and coordinate the writing out of changes, ensuring atomicity and consistency.

### 2.2 Structure

```
UnitOfWork
├── begin() → transaction
├── commit() → None
├── rollback() → None
└── repositories → dict[str, Repository]
```

### 2.3 When to Use

- When multiple repositories need to participate in a single transaction
- When you need atomic commits across aggregates
- When you want to defer persistence to the end of a business operation

### 2.4 When Not to Use

- Single-repository operations
- Read-only operations
- When SQLAlchemy's built-in session management is sufficient

### 2.5 Existing Code

- `backend/app/database.py` — SQLAlchemy session management
- SQLAlchemy's Unit of Work is built into the Session object — all `db.commit()` and `db.rollback()` calls follow this pattern.
- `backend/app/services/outbox_service.py` — Writes outbox events in same transaction as business operation (line 7: "INSIDE an existing DB transaction")

---

## 3. Specification Pattern

### 3.1 Intent

Encapsulate a business rule as a composable, reusable, and testable object. Allows building complex queries from simple building blocks.

### 3.2 Structure

```
Specification
├── is_satisfied_by(entity) → bool
├── apply(query) → Query
└── and(spec) → Specification (composite)
└── or(spec) → Specification (composite)
└── not() → Specification (negation)
```

### 3.3 When to Use

- Complex query filtering that crosses entity boundaries
- When the same business rule applies in multiple places
- When you need composable filters

### 3.4 When Not to Use

- Simple WHERE clauses
- When a single query suffices
- Small-scale applications with minimal query logic

### 3.5 Existing Code

- `backend/app/national/domain/identity_resolution.py` — Identity resolution with search criteria
- `backend/app/services/mpi/blocking.py` — MPI blocking keys for candidate search
- `backend/app/services/mpi/matcher.py` — MPI matching with composable criteria

---

## 4. CQRS

### 4.1 Intent

Separate read and write operations into different models, allowing independent optimization of queries and commands. Commands mutate state; queries return data without side effects.

### 4.2 Structure

```
         ┌──────────────┐
         │   Client     │
         └──┬───────┬───┘
            │       │
      ┌─────▼──┐ ┌──▼──────┐
      │Command │ │ Query   │
      │ Bus    │ │ Bus     │
      └─────┬──┘ └──┬──────┘
            │        │
      ┌─────▼──┐ ┌──▼──────┐
      │Command │ │ Query   │
      │Handler │ │ Handler │
      └─────┬──┘ └──┬──────┘
            │        │
      ┌─────▼──┐ ┌──▼──────┐
      │ Write  │ │  Read   │
      │ Model  │ │  Model  │
      └────────┘ └─────────┘
```

### 4.3 When to Use

- When reads and writes have different performance requirements
- When complex business logic needs clean separation from query logic
- When multiple read models serve different use cases
- When you want to optimize for different access patterns

### 4.4 When Not to Use

- Simple CRUD applications
- When the overhead of separation exceeds the benefit
- Single-developer, small-scale projects

### 4.5 Existing Code

- `backend/app/ehr/commands/` — EHR command handlers
- `backend/app/ehr/queries/` — EHR query handlers
- `backend/app/ehr/events/` — EHR event handlers (eventual consistency between command and query models)
- `backend/app/national/services/citizen_service.py` — Application service layer
- `backend/app/kernel/types.py:52-70` — CapabilityCommand and CapabilityQuery type definitions

### 4.6 Implementation Pattern

```python
# Command
class CreateCitizenCommand:
    first_name: str
    father_name: str
    last_name: str
    date_of_birth: date
    gender: Gender

class CreateCitizenHandler:
    def __init__(self, repository: CitizenRepository, event_bus: EventBus):
        self._repository = repository
        self._event_bus = event_bus

    def handle(self, cmd: CreateCitizenCommand) -> CitizenDTO:
        citizen = Citizen.create(cmd.first_name, cmd.father_name, ...)
        citizen = self._repository.add(citizen)
        self._event_bus.publish(CitizenCreatedEvent(citizen.id))
        return CitizenDTO.from_entity(citizen)

# Query
class GetCitizenQuery:
    citizen_id: str

class GetCitizenHandler:
    def __init__(self, repository: CitizenRepository):
        self._repository = repository

    def handle(self, query: GetCitizenQuery) -> CitizenDTO | None:
        citizen = self._repository.get(query.citizen_id)
        return CitizenDTO.from_entity(citizen) if citizen else None
```

---

## 5. Event Sourcing

### 5.1 Intent

Store the state of an aggregate as a sequence of events. Each event represents a state change. The current state is derived by replaying all events in order.

### 5.2 Structure

```
Aggregate
├── apply_event(event) → None (builds state)
├── load_from_history(events) → Aggregate
└── uncommitted_events → list[Event]

EventStore
├── save(aggregate_id, events) → None
├── load(aggregate_id) → list[Event]
└── replay(since) → stream[Event]
```

### 5.3 When to Use

- When you need a complete audit trail of every state change
- When you need temporal queries (state at any point in time)
- When event-driven integration is required
- When you need to detect and resolve conflicts
- For identity resolution history (MPI merge audit)

### 5.4 When Not to Use

- Simple CRUD with no audit requirements
- High-frequency updates (event store write amplification)
- When current state is all that matters
- When team is not familiar with event sourcing complexity

### 5.5 Existing Code

- `backend/app/kernel/event_bus/snapshot.py` — Event snapshots
- `backend/app/kernel/event_bus/replay.py` — Event replay
- `backend/app/kernel/event_bus/store.py` — Event store
- `backend/app/models/audit_log.py` — Append-only audit log with hash chain (audit trail pattern)
- `backend/app/national/domain/merge_record.py` — MPI merge audit (event-sourced identity decisions)
- `backend/app/national/security/audit.py` — National audit events

---

## 6. Outbox Pattern

### 6.1 Intent

Ensure reliable event delivery by writing events to a database table within the same transaction as the business operation. A background worker reads pending events and publishes them to the event bus or message broker.

### 6.2 Structure

```
Business Transaction
├── Write business data (DB)
└── Write outbox event (DB) ← same transaction
        ↓
OutboxWorker (background)
├── Read pending events
├── Publish to event bus
├── Mark as done
└── Retry on failure (max 5 attempts)
```

### 6.3 When to Use

- When you need guaranteed event delivery
- When the message broker might be unavailable
- When you need at-least-once delivery guarantees
- When events must be atomic with business data

### 6.4 When Not to Use

- In-memory event bus is sufficient
- When exactly-once delivery is required (use idempotent consumers)
- When events are not business-critical

### 6.5 Existing Code

- `backend/app/models/outbox.py` — OutboxEvent model (status lifecycle: pending → processing → done/failed)
- `backend/app/services/outbox_service.py` — Writer and worker implementation
- `backend/app/services/outbox_service.py:7-26` — "Transactional Outbox Service" full implementation
- `backend/app/kernel/event_bus/outbox.py` — Kernel-level outbox
- `backend/app/kernel/event_bus/inbox.py` — Inbox pattern for event consumption
- `backend/app/kernel/event_bus/dead_letter_queue.py` — Failed event handling
- `backend/app/kernel/event_bus/retry_queue.py` — Retry logic

### 6.6 Implementation

```python
# From backend/app/services/outbox_service.py
# Writer (called inside business transaction)
def emit_to_outbox(
    db: Session,
    event_type: str,
    aggregate_type: str,
    aggregate_id: int,
    payload: dict,
) -> OutboxEvent:
    event = OutboxEvent(
        event_type=event_type,
        aggregate_type=aggregate_type,
        aggregate_id=aggregate_id,
        payload=json.dumps(payload, default=str),
        status="pending",
    )
    db.add(event)
    return event

# Worker
class OutboxWorker:
    @staticmethod
    async def run_once() -> int:
        events = db.query(OutboxEvent).filter(
            OutboxEvent.status == "pending",
            OutboxEvent.attempts < MAX_ATTEMPTS,
        ).limit(_BATCH_SIZE).with_for_update(skip_locked=True).all()

        for event in events:
            try:
                event.status = "processing"
                db.flush()
                await dispatch_event(event)
                event.status = "done"
                event.processed_at = datetime.now(UTC)
            except Exception as exc:
                event.attempts += 1
                event.last_error = str(exc)
                event.status = "failed" if event.attempts >= MAX_ATTEMPTS else "pending"
        db.commit()
```

---

## 7. Saga Pattern

### 7.1 Intent

Manage distributed transactions across multiple services through a sequence of local transactions with compensating actions for rollback. Two flavors: choreography (event-driven) and orchestration (central coordinator).

### 7.2 Structure

**Choreography:**
```
Service A → emits event → Service B → emits event → Service C
  ↑                        ↑                          │
  └── compensating event ←─┴── compensating event ←──┘ (on failure)
```

**Orchestration:**
```
Saga Coordinator
├── Step 1: Execute Service A
├── Step 2: Execute Service B
├── Step 3: Execute Service C
└── On failure: Execute compensating actions (reverse order)
```

### 7.3 When to Use

- When a business transaction spans multiple services
- When you need eventual consistency with rollback capability
- When 2PC (two-phase commit) is not feasible

### 7.4 When Not to Use

- Single-service transactions
- When strong consistency is required (use distributed transactions instead)
- When compensating actions are not possible

### 7.5 Existing Code

- `backend/app/lims/workflows.py` — LIMS workflow orchestration
- `backend/app/national/workflows/` — National workflows
- `backend/app/national/workflow_runtime/` — Workflow runtime engine
- `backend/app/kernel/background/` — Background job orchestration
- `shared/workflow/engine.py` — Workflow engine

---

## 8. Circuit Breaker

### 8.1 Intent

Prevent cascading failures by detecting when a dependency is unhealthy and temporarily stopping calls to it. Automatically retry after a recovery timeout.

### 8.2 Structure

```
                  ┌─────────┐
    request  ────▶│ CLOSED  │────▶ success (counter reset)
                  └────┬────┘
                       │ failure > threshold
                       ▼
                  ┌─────────┐
                  │  OPEN   │────▶ reject immediately
                  └────┬────┘
                       │ timeout elapsed
                       ▼
                  ┌───────────┐
                  │ HALF_OPEN │────▶ probe one request
                  └─────┬─────┘
                   ┌────┴────┐
                   ▼         ▼
               success    failure
                  │          │
                  ▼          ▼
              CLOSED       OPEN
```

### 8.3 When to Use

- For all external service calls
- For database connections (DB circuit breaker)
- For notification services
- For any dependency that could fail or become slow

### 8.4 When Not to Use

- Local, in-process operations that never fail
- When the failure is expected and handled at the application level
- Idempotent operations where retry is safe without circuit breaking

### 8.5 Existing Code

- `backend/app/core/self_healing.py:49-90` — CircuitBreaker class (CLOSED/OPEN/HALF_OPEN)
- `backend/app/gateways/base.py` — ExternalGateway base with circuit breaker
- `backend/app/notifications/service.py:25-28` — Notification circuit breaker
- `shared/circuit_breaker.py` — Shared circuit breaker
- `backend/app/core/self_healing.py` — Full self-healing system (458 lines)

### 8.6 Implementation

```python
# From backend/app/core/self_healing.py
class CircuitBreaker:
    def __init__(self, name: str, failure_threshold: int = 3, recovery_timeout: float = 30.0):
        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._last_failure_time: float | None = None

    def record_failure(self) -> None:
        self._failure_count += 1
        self._last_failure_time = time.monotonic()
        if self._failure_count >= self.failure_threshold:
            self._state = CircuitState.OPEN

    def record_success(self) -> None:
        self._failure_count = 0
        self._state = CircuitState.CLOSED

    def allow_request(self) -> bool:
        current = self._get_state()
        return current != CircuitState.OPEN  # Half-open allows one request
```

---

## 9. Retry Pattern

### 9.1 Intent

Handle transient failures by retrying failed operations with configurable backoff, jitter, and maximum attempts.

### 9.2 Structure

```
attempt 0: delay = base_delay
attempt 1: delay = base_delay × backoff ^ 1
attempt 2: delay = base_delay × backoff ^ 2 (capped at max_delay)
...
attempt N: fail permanently
```

### 9.3 When to Use

- Network operations (HTTP calls, API requests)
- Database deadlocks or transient errors
- External service calls
- File system operations

### 9.4 When Not to Use

- Business logic errors (invalid input, authorization failures)
- Non-idempotent operations without idempotency key
- When retry would make the system worse (retry storm)

### 9.5 Existing Code

- `backend/app/core/resilience.py` — Full retry implementation (276 lines)
- `backend/app/core/resilience.py:42-60` — `retry()` decorator with exponential backoff
- `backend/app/gateways/base.py` — ExternalGateway with configurable retry
- `shared/retry/decorators.py` — Shared retry decorators

### 9.6 Implementation

```python
# From backend/app/core/resilience.py
def retry(
    max_attempts: int = 3,
    base_delay: float = 0.5,
    max_delay: float = 30.0,
    backoff: float = 2.0,
    exceptions: tuple = (Exception,),
):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < max_attempts - 1:
                        delay = min(base_delay * (backoff ** attempt), max_delay)
                        jitter = random.uniform(0, delay * 0.1)  # 10% jitter
                        time.sleep(delay + jitter)
            raise last_exception  # type: ignore
        return wrapper
    return decorator
```

---

## 10. Bulkhead Pattern

### 10.1 Intent

Isolate system resources so that a failure in one component doesn't cascade. Limit the number of concurrent calls to each service or resource.

### 10.2 Structure

```
Request Queue
├── Clinical writes (exempt from shedding)
├── Read operations (concurrency limited)
├── AI calls (concurrency limited)
├── External API calls (concurrency limited)
└── Background jobs (separate worker pool)
```

### 10.3 When to Use

- When multiple clients share the same resources
- When one slow consumer can degrade the whole system
- When you need to guarantee availability for critical operations
- When connection pools are limited

### 10.4 When Not to Use

- Single-user systems
- When the overhead of isolation exceeds the benefit
- Small systems with low concurrency

### 10.5 Existing Code

- `backend/app/main.py:ConcurrencyLimitMiddleware` — In-flight request cap per worker
- `backend/app/main.py` — Clinical writes exempt from concurrency shedding
- `backend/app/kernel/background/worker_pool.py` — Worker pool implementation
- `backend/app/gateways/base.py` — Per-gateway rate limiting

---

## 11. Idempotency Pattern

### 11.1 Intent

Allow clients to safely retry requests without causing duplicate processing. The server detects duplicate requests and returns the original response.

### 11.2 Structure

```
Client sends: Idempotency-Key: <uuid>

Server:
├── Check idempotency_keys table for key
├── If exists → return cached response (200)
├── If new → process request, store response (201)
└── Keys scoped per lab, expire after 24h
```

### 11.3 When to Use

- POST endpoints that create resources
- Payment processing
- Any operation that must be exactly-once
- Clinical order and result creation

### 11.4 When Not to Use

- GET requests (idempotent by definition)
- PUT/DELETE (idempotent by definition)
- Operations with no side effects

### 11.5 Existing Code

- `backend/app/core/idempotency.py` — Full idempotency middleware (190 lines)
- `backend/app/models/` — Idempotency keys table
- Supported endpoints: POST `/api/orders`, POST `/api/results`, POST `/api/results/{id}/validate`, POST `/api/samples`

### 11.6 Implementation

```python
# From backend/app/core/idempotency.py
def idempotency_check(request: Request, db: Session = Depends(get_db)):
    key = request.headers.get("Idempotency-Key")
    if not key:
        return IdempotencyResult(is_duplicate=False)

    lab_id = get_current_lab_id(request)
    existing = db.query(IdempotencyRecord).filter(
        IdempotencyRecord.key == key,
        IdempotencyRecord.lab_id == lab_id,
    ).first()

    if existing and not existing.is_expired():
        return IdempotencyResult(
            is_duplicate=True,
            cached_response=existing.response_data,
        )

    return IdempotencyResult(is_duplicate=False)
```

---

## 12. Caching Patterns

### 12.1 Intent

Improve performance and reduce database load by temporarily storing frequently accessed data in a faster storage tier.

### 12.2 Cache-Aside (Default GULA Pattern)

```
Read:  Check cache → if miss → read DB → write cache → return
Write: Write DB → invalidate cache → return
```

### 12.3 Read-Through

```
Cache is authoritative: Read through cache → cache reads DB on miss
Used for: Reference data, configuration
```

### 12.4 Write-Through

```
Write to cache first → cache writes to DB synchronously
Used for: Session data, rate limit counters
```

### 12.5 Write-Behind

```
Write to cache first → cache asynchronously writes to DB
Used for: High-volume metrics, audit log (future)
```

### 12.6 When to Use

- Frequently accessed, rarely modified data
- Expensive computation results
- API responses for dashboard/read endpoints
- Reference data (test types, lab configurations)

### 12.7 When Not to Use

- Data that changes on every write (use write-through)
- Clinical data that requires immediate consistency
- Large datasets that would evict useful cache entries

### 12.8 Existing Code

- `backend/app/core/cache_manager.py` — Cache management layer
- `backend/app/security/redis_client.py` — Redis client implementation
- `shared/cache/backends.py` — Cache backend abstractions
- `backend/app/gateways/base.py` — Gateway-level caching with freshness tracking

---

## 13. Feature Flags

### 13.1 Intent

Enable or disable functionality at runtime without deploying new code. Support per-tenant configuration, percentage rollouts, and kill switches.

### 13.2 Structure

```
Feature Resolution:
├── Tier base features (starter/growth/enterprise)
├── Deployment mode overrides (single/multi_branch/government)
├── Security level overrides (standard/high_security/air_gapped)
├── Per-lab FeatureFlag overrides (add/remove features)
└── Expiry check on per-lab flags
```

### 13.3 When to Use

- Per-tenant feature gating
- Gradual feature rollout
- A/B testing
- Kill switch for problematic features
- Deployment-mode-specific features

### 13.4 When Not to Use

- Security features (use RBAC/ABAC instead)
- User-specific permissions
- Temporary branches (use feature branches instead)

### 13.5 Existing Code

- `backend/app/core/feature_flags.py` — Full feature flag system (340 lines)
- `backend/app/models/subscription.py` — FeatureFlag model + LabSubscription
- `backend/app/kernel/features/flags.py` — Kernel-level feature flags
- `backend/app/kernel/features/kill_switch.py` — Feature kill switch
- `backend/app/kernel/features/experimental.py` — Experimental features
- `backend/app/kernel/features/capabilities.py` — Capability-based features
- `backend/app/kernel/features/tenant_features.py` — Tenant-scoped features
- `shared/feature_flags.py` — Shared feature flag utilities

### 13.6 Implementation

```python
# From backend/app/core/feature_flags.py
def resolve_lab_features(lab_id: int, db) -> frozenset[str]:
    # 1. Load subscription → tier, deployment, security
    # 2. Get tier base features
    # 3. Apply deployment overrides
    # 4. Apply security overrides
    # 5. Apply per-lab FeatureFlag overrides
    # 6. Return resolved feature set

def require_feature(feature: str, lab_id: int, db):
    features = resolve_lab_features(lab_id, db)
    if feature not in features:
        raise HTTPException(status_code=403, detail={
            "error": "feature_not_available",
            "message_ar": "هذه الميزة غير متاحة في خطتك الحالية",
        })
```

---

## 14. Plugin Pattern

### 14.1 Intent

Allow third-party code to extend the platform without modifying core code. Plugins are sandboxed, permissioned, versioned, and hot-reloadable.

### 14.2 Structure

```
Plugin Manager
├── Loader — dynamic module loading
├── Sandbox — isolated execution
├── Permissions — plugin capabilities
├── Registry — plugin catalog
├── Version Manager — compatibility
├── Hot-Reload — watch for changes
└── Marketplace — distribution
```

### 14.3 When to Use

- Extensible platform that third parties integrate with
- When different tenants need different capabilities
- When features should be developed independently

### 14.4 When Not to Use

- Small, single-tenant applications
- When security isolation is too complex
- When all features are known ahead of time

### 14.5 Existing Code

- `backend/app/kernel/plugin/` — Complete plugin system
- `backend/app/kernel/plugin/loader.py` — Dynamic plugin loading
- `backend/app/kernel/plugin/sandbox.py` — Sandboxed execution
- `backend/app/kernel/plugin/permissions.py` — Plugin permissions
- `backend/app/kernel/plugin/manager.py` — Lifecycle management
- `backend/app/kernel/plugin/registry.py` — Plugin registry
- `backend/app/kernel/plugin/hot_reload.py` — Hot-reload
- `backend/app/kernel/plugin/version_manager.py` — Version compatibility
- `backend/app/kernel/plugin/marketplace.py` — Plugin marketplace
- `backend/app/kernel/plugin/dependencies.py` — Plugin dependency resolution

---

## 15. Adapter Pattern

### 15.1 Intent

Convert the interface of a class into another interface clients expect. Allows incompatible interfaces to work together, isolating the platform from external system dependencies.

### 15.2 Structure

```
Client (Business Code)
    │
    ├── Gateway Interface (abstraction)
    │       ├── Gateway Adapter A (e.g., NID production)
    │       ├── Gateway Adapter B (e.g., NID stub)
    │       └── Gateway Adapter C (e.g., NID v2)
    │
    └── External System
```

### 15.3 When to Use

- External API integration
- When multiple providers offer the same service
- When stubbing out external dependencies for testing
- When protocols need abstraction (ASTM, HL7, FHIR)

### 15.4 When Not to Use

- Simple wrappers that add no value
- When you control both sides of the interface
- When the abstraction is unlikely to change

### 15.5 Existing Code

- `backend/app/gateways/base.py` — ExternalGateway base class (571 lines)
- `backend/app/gateways/national_identity_gateway.py` — NID adapter
- `backend/app/gateways/insurance_gateway.py` — Insurance adapter
- `backend/app/gateways/residency_gateway.py` — Residency adapter
- `backend/app/gateways/cloudflare_gateway.py` — Cloudflare adapter
- `backend/app/interoperability/adapter_base.py` — HL7/FHIR adapter base
- `shared/device/adapters.py` — Device protocol adapters

---

## 16. Strategy Pattern

### 16.1 Intent

Define a family of algorithms, encapsulate each one, and make them interchangeable. Strategy lets the algorithm vary independently from clients that use it.

### 16.2 Structure

```
Context
├── set_strategy(strategy)
└── execute_strategy(data) → Result

Strategy (Interface)
├── ConcreteStrategyA
├── ConcreteStrategyB
└── ConcreteStrategyC
```

### 16.3 When to Use

- When multiple algorithms exist for the same task
- When algorithms should be interchangeable at runtime
- When you want to isolate algorithm implementation from usage

### 16.4 When Not to Use

- When the number of algorithms is small and fixed
- When strategies add unnecessary indirection
- When conditional logic is simpler

### 16.5 Existing Code

- `backend/app/identity_matching.py` — Identity matching strategies
- `backend/app/services/mpi/matcher.py` — MPI matching strategy selection
- `backend/app/core/self_healing.py` — Degradation level strategies
- `backend/app/national/security/purpose_of_use.py` — Purpose-based access strategies
- `backend/app/gateways/base.py` — Stub vs live mode strategy

---

## 17. Factory Pattern

### 17.1 Intent

Define an interface for creating an object, but let subclasses decide which class to instantiate. Used for registry-based, config-driven object creation.

### 17.2 Structure

```
Factory
├── create(type, config) → Object
└── register(type, builder) → None

Registry
├── builder_map: dict[str, Builder]
├── register(name, builder)
└── create(name, *args) → Object
```

### 17.3 When to Use

- When object creation is complex
- When the concrete type is determined at runtime
- When you want to centralize creation logic
- When new types are registered by plugins

### 17.4 When Not to Use

- Simple object creation with `__init__`
- When the type is known at compile time
- When the factory adds no benefit over direct construction

### 17.5 Existing Code

- `backend/app/kernel/module/discovery.py` — Module discovery factory
- `backend/app/kernel/module/loader.py` — Module loading factory
- `backend/app/kernel/plugin/registry.py` — Plugin registry factory
- `backend/app/kernel/plugin/loader.py` — Plugin loading factory
- `shared/di_container/engine.py` — DI container factory
- `backend/app/kernel/capabilities_registry_populator.py` — Capability registration

---

## Document Version History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-07-15 | Architecture Team | Initial enterprise design patterns catalog |

**Review Cycle**: This document must be reviewed and updated quarterly or when significant architectural changes occur.
