# Architecture Decision Records — National Platform Runtime

## ADR-RUNTIME-001: Modular Bounded Contexts as Python Packages

**Status:** Accepted
**Context:** The National Platform Runtime needs 9 distinct engines that can be developed, tested, and deployed independently while sharing common infrastructure.
**Decision:** Each engine is a standalone Python package under `backend/app/national/` with its own domain, application, infrastructure, and API layers. All modules share the same `NationalBase` declarative base and reuse existing Kernel services.
**Consequence:** Each module can be tested independently. No module imports from another runtime module — only from the frozen Kernel and infrastructure layers.

## ADR-RUNTIME-002: Event-Driven Inter-Module Communication

**Status:** Accepted
**Context:** Modules must react to state changes in other modules without direct coupling (e.g., workflow completion triggers notifications, task completion triggers workflows).
**Decision:** All modules publish domain events to the Kernel EventBus. Modules subscribe to relevant events through the event bus dispatcher. No direct inter-module imports.
**Consequence:** Modules remain decoupled. New modules can react to existing events without modifying event publishers.

## ADR-RUNTIME-003: Dual-Layer Task Execution

**Status:** Accepted
**Context:** The platform needs both low-level task execution (Redis-backed queue with retry/DLQ) and high-level task management (assignment, SLA, escalation).
**Decision:** Two layers: (1) Existing `tasks/` module provides the execution substrate (queue, registry, worker, retry). (2) New `task_engine/` and `background_platform/` provide management and scheduling on top. The execution layer never references the management layer.
**Consequence:** Tasks work without the management layer. Management adds value without modifying the execution substrate.

## ADR-RUNTIME-004: Workflow Definitions as Data, Not Code

**Status:** Accepted
**Context:** Clinical workflows must be modifiable by domain experts without deploying code. They must support versioning and parallel execution of multiple versions.
**Decision:** Workflow definitions are stored as JSON in PostgreSQL (steps, transitions, handlers). The workflow runtime interprets these definitions at execution time. Step handlers are registered Python functions referenced by name.
**Consequence:** Workflows can be modified via API without deployments. Multiple workflow versions can run simultaneously. New step handlers require code deployment but workflow topology changes do not.

## ADR-RUNTIME-005: Pluggable Notification Channel Adapters

**Status:** Accepted
**Context:** The notification platform must support multiple channels (Email, SMS, Push, WhatsApp, Telegram, Government Gateway) with different delivery characteristics and provider dependencies.
**Decision:** Each channel has an abstract `NotificationChannelAdapter` interface. Adapters are registered in a channel registry. The notification service selects channels based on user preferences and notification category. External provider implementations are stub adapters that abstract the underlying API.
**Consequence:** Adding a new channel requires only implementing the adapter interface and registering it. Production deployments plug in real provider implementations behind the same interface.

## ADR-RUNTIME-006: Document Hash Chain Integrity

**Status:** Accepted
**Context:** Healthcare documents must have tamper-evident integrity. Electronic signatures must be verifiable independently of the platform.
**Decision:** Every document version stores SHA-256 hash of content. Signatures chain the document hash with signer identity and timestamp. QR codes encode a verification URL that includes the document hash for client-side verification.
**Consequence:** Document integrity is verifiable without accessing the database. QR code scanning enables field verification by patients and auditors.

## ADR-RUNTIME-007: Unified Search with Pluggable Backends

**Status:** Accepted
**Context:** Different deployment scenarios need different search backends (PostgreSQL FTS for small deployments, Elasticsearch/OpenSearch for national scale). The API must be backend-agnostic.
**Decision:** `IndexAdapter` abstract interface with implementations for PostgreSQL FTS, Elasticsearch, FHIR, and in-memory. The search service delegates to the configured adapter. FHIR search parameters are mapped to adapter-specific queries.
**Consequence:** Deployments choose their search backend via configuration. The unified search API remains consistent across all backends.
