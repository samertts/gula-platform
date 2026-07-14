# Architecture Decision Records — GULA Platform

**Contract Tag:** `integration-contracts-v1.0` | **Date:** 2026-07-14

| ADR | Title | Status |
|---|---|---|
| 001 | Monolith-first with Microservice Decomposition Path | Accepted |
| 002 | FHIR R4 as Canonical Interoperability Standard | Accepted |
| 003 | Transactional Outbox for Event Delivery | Accepted |
| 004 | HMAC Patient Card Tokens | Accepted |
| 005 | National ID Encryption at Rest | Accepted |
| 006 | Circuit Breaker Self-Healing | Accepted |
| 007 | CQRS with Capability-based Modules | Accepted |
| 008 | SDK-first Public Contract Philosophy | Accepted |
| 009 | Arabic-first Bilingual Platform | Accepted |
| 010 | Offline-first Edge Architecture | Accepted |

---

## ADR-001: Monolith-first with Microservice Decomposition Path

**Status:** Accepted

### Context

The GULA Platform must serve Iraqi medical laboratories with varying scale — from small private clinics to nationwide government deployments. The team needed an architecture that would:
1. Ship rapidly with a small team
2. Support eventual decomposition as scale demands
3. Avoid premature distributed systems complexity

### Decision

Adopt a **monolith-first** architecture:
- **Production deployment:** Single FastAPI monolith (`backend/app/`) with gunicorn + uvicorn workers
- **Microservice tree:** A parallel `services/` directory contains independently deployable services for future decomposition (lab, order, patient, result, sample, notification, ai, autonomous_manager)
- **Shared library:** `shared/` package contains canonical domain logic used by both monolith and future services
- **Capability Registry:** The engineering kernel maintains a registry of 52+ capabilities across 9 domains, enabling incremental extraction

### Consequences

**Positive:**
- Rapid development velocity (300+ Python files, 7 weeks to production)
- Single deployment unit simplifies operations
- All business logic in one codebase enables effective refactoring
- Shared library prevents duplication when services are extracted

**Negative:**
- Cannot independently scale individual domains
- Single deployment unit requires coordination for any change
- Future extraction will require API gateway routing changes

### Decision Rationale

The primary deployment target is Docker Compose on a single DigitalOcean droplet. At this scale, the operational cost of microservices (service mesh, observability, distributed tracing, data consistency) far outweighs the benefits. The parallel service tree ensures the decomposition path is prepared.

---

## ADR-002: FHIR R4 as Canonical Interoperability Standard

**Status:** Accepted

### Context

The platform must interoperate with:
- Iraqi Ministry of Health national systems
- Hospital information systems (HIS)
- Electronic medical records (EMR)
- Future national health data exchange

### Decision

Adopt **FHIR R4** as the canonical interoperability standard:
- 10 FHIR resource types implemented: Patient, Practitioner, Organization, Encounter, Observation, DiagnosticReport, Specimen, ServiceRequest, Device, Bundle
- Two endpoint families: Government Compliance (`/compliance/fhir`) and LIMS (`/lims`)
- National data layer for cross-institution exchange
- 8 custom FHIR profiles with complete field mapping rules
- LOINC, SNOMED CT, UCUM terminology bindings
- CapabilityStatement served at `/compliance/fhir/metadata`

### Consequences

**Positive:**
- Industry standard with broad tooling support
- Clear migration path for EMR/HIS integration
- CapabilityStatement provides discoverable contract
- FHIR search and pagination standards reduce custom API surface

**Negative:**
- FHIR is a large standard; we implement a subset
- Custom profiles require consumer awareness
- Some Iraqi-specific concepts (national ID, governorate hierarchy) require extension

---

## ADR-003: Transactional Outbox for Event Delivery

**Status:** Accepted

### Context

The platform generates domain events (specimen lifecycle, order state changes, critical results) that must be delivered to:
- Internal services (workflows, notifications)
- External systems (webhooks, HIS, Ministry of Health)

Dual-write (DB + message broker) risks inconsistency.

### Decision

Implement the **transactional outbox pattern**:
- Events are written to the `outbox_events` table within the same DB transaction as the business operation
- A background worker polls for pending events and publishes them
- At-least-once delivery with exponential backoff (max 5 attempts)
- Dead letter queue for events that exceed max attempts
- Support for event replay, snapshots, and recovery

### Consequences

**Positive:**
- Atomic writes guarantee consistency between business state and events
- No distributed transaction or two-phase commit needed
- Replay capability enables recovery scenarios
- Full audit trail of all events

**Negative:**
- Poll-based delivery adds latency (10s poll interval)
- Requires `outbox_events` table management (purge after 30 days)
- Worker process must be running for event delivery

---

## ADR-004: HMAC Patient Card Tokens

**Status:** Accepted

### Context

Patient cards contain QR codes that link to clinical data. Scanning a QR code must:
- Authenticate the card as genuine (issued by the platform)
- Prevent enumeration attacks (random guessing)
- Require zero configuration for the scanning actor

### Decision

Use **HMAC-SHA256 signed tokens** for patient card QR codes:
- Token = `base64(patient_id + timestamp)` + `:` + `HMAC(patient_id + timestamp, NID_HMAC_KEY)`
- Token is embedded in the QR code
- Scanning endpoint verifies HMAC before revealing any patient data
- Key is server-only, never exposed

### Consequences

**Positive:**
- Stateless verification (no DB lookup for token validation)
- Tamper-proof: token modification invalidates HMAC
- No shared secret distribution needed
- Lightweight: single HMAC operation

**Negative:**
- Key rotation requires regenerating all cards
- Token reveals patient_id (obfuscated but not encrypted)
- No built-in expiry (can be extended with TTL in token payload)

---

## ADR-005: National ID Encryption at Rest

**Status:** Accepted

### Context

Iraqi national IDs (`national_id`) are sensitive personally identifiable information (PII). The platform must store them for:
- Patient identity verification
- Health data deduplication (MPI)
- SNDHS-lite national reporting

### Decision

National IDs are **never stored in plaintext**:
- Storage: HMAC-SHA256 hash of the national ID
- Retrieval: exact-match only (never LIKE or partial match)
- FHIR output: only first 16 characters of the hash are exposed
- Encryption key (`NID_HMAC_KEY`) must be strong (rejected by `_is_weak_secret()`)
- Dual-read rule: code reading national_id must handle `None` (pre-backfill rows)

### Consequences

**Positive:**
- National ID is never exposed in cleartext
- Hash prevents data breach exposure
- Exact-match query preserves search capability

**Negative:**
- Cannot retrieve original national ID (by design)
- Hash collision (extremely unlikely with SHA256)
- Data migration requires access to original IDs

---

## ADR-006: Circuit Breaker Self-Healing

**Status:** Accepted

### Context

The platform must remain available during infrastructure degradation. Database failures, connection pool exhaustion, and Redis outages should not cause complete system failure.

### Decision

Implement a **3-layer self-healing system**:

1. **Circuit Breaker** (`core/self_healing.py`):
   - Monitors DB and Redis health
   - Opens circuit on repeated failures
   - Flips to degraded mode (read-only, rejecting writes)

2. **Auto-Repair Engine** (`core/auto_repair.py`):
   - Garbage collection triggers
   - Connection pool recycling
   - Automatic reconnection attempts

3. **Adaptive Concurrency** (`main.py`):
   - Halves `MAX_CONCURRENT` on 2 slow DB readings (>300ms)
   - Restores after 3 fast readings (<150ms)

Plus a **health watchdog** that scores the system GREEN/YELLOW/RED every 60 seconds and fires alert webhooks on transitions.

### Consequences

**Positive:**
- Graceful degradation instead of hard failure
- Automatic recovery without human intervention
- Clinical write paths are always exempt from shedding

**Negative:**
- Degraded mode is still a degraded experience
- Circuit breaker adds complexity to health monitoring
- False positives possible during transient latency spikes

---

## ADR-007: CQRS with Capability-based Modules

**Status:** Accepted

### Context

The platform spans multiple domains (laboratory, identity, financial, governance) with different read/write patterns. A monolithic model leads to coupling. Developers need clear boundaries.

### Decision

Adopt **CQRS (Command Query Responsibility Segregation)** at the module level:
- Each domain has separate command (write) and query (read) paths
- Capability Registry (`kernel/capability_registry.py`) catalogs 52+ capabilities across 9 domains
- Each capability defines: events, commands, queries, entities, DTOs, policies, permissions, API endpoints
- Capability generator produces 20+ artifacts per capability
- Bidirectional sync between CapabilityRegistry ↔ FeatureFlagManager

### Consequences

**Positive:**
- Clear domain boundaries prevent coupling
- Feature flags gate capability rollout per-tenant
- Generated code ensures consistency
- Impact analysis via dependency graph

**Negative:**
- Overhead of maintaining capability descriptors
- Generated code requires regeneration on changes
- Some domains (e.g., financial) are schema-only pending business requirements

---

## ADR-008: SDK-first Public Contract Philosophy

**Status:** Accepted

### Context

External developers (lab software vendors, Ministry of Health integrators, mobile developers) need a stable, well-documented API surface.

### Decision

Adopt **SDK-first contract philosophy**:
- All public contracts defined in `contracts/`:
  - `contracts/dto/catalog.json` — 146+ DTO schemas with field-level constraints
  - `contracts/events/catalog.json` — 85+ event definitions with retry policies
  - `contracts/fhir/` — CapabilityStatement + FHIR profiles
  - `contracts/hl7/protocol.json` — HL7 v2.5.1 complete protocol contract
  - `contracts/astm/protocol.json` — ASTM E1381/E1394 complete protocol contract
- SDKs generated from canonical definitions:
  - Python SDK (`contracts/sdk/python/`) with full type hints
  - TypeScript SDK (`contracts/sdk/typescript/`) with TypeScript types
- 28 enums shared across both SDKs
- Contracts are the source of truth; backend implementations must match

### Consequences

**Positive:**
- SDK users get compile-time type checking
- Contracts force API design discipline
- Documentation is auto-generated from contracts
- Version bumps are explicit and traceable

**Negative:**
- SDK generation must be kept in sync with backend
- Python SDK needs separate packaging pipeline
- Some consumers (curl, Postman) don't benefit from SDK

---

## ADR-009: Arabic-first Bilingual Platform

**Status:** Accepted

### Context

GULA serves Iraqi medical laboratories where:
- Primary language is Arabic
- Regulatory and national reporting requires Arabic
- FHIR standard is English-based
- Some lab staff prefer English UI

### Decision

Design as an **Arabic-first, bilingual platform**:
- API error responses include both `detail` (English) and `detail_ar` (Arabic)
- FHIR resources include `title_ar`, `description_ar` alongside English fields
- Patient names stored with Arabic character support (UTF-8)
- PDF reports generated with `arabic-reshaper` + `python-bidi` for correct Arabic rendering
- QR card system generates Arabic-first printable HTML
- Citizen portal responses use Arabic field aliases (e.g., `اسم_التحليل` for `test_name_ar`)

### Consequences

**Positive:**
- Native experience for Iraqi end users
- Compliance with Ministry of Health Arabic requirements
- Flexibility for international users

**Negative:**
- Extra field per bilingual response (increased payload size)
- Arabic rendering requires specialized libraries (arabic-reshaper, python-bidi)
- FHIR standard fields remain English; Arabic in `text` and custom extensions

---

## ADR-010: Offline-first Edge Architecture

**Status:** Accepted

### Context

Iraqi medical laboratories face:
- Unreliable internet connectivity in remote governorates
- Need for continuous operations during network outages
- Laboratory instruments that cannot queue data indefinitely

### Decision

Adopt an **offline-first edge architecture**:
- **Edge Agent** (`edge_agent/`): Runs on a local device (Raspberry Pi or mini PC) at the lab site
- **Device Bridge** (`services/device_bridge/`): Connects to instruments via serial/TCP, buffers results locally
- **Sync protocol:**
  - Results buffered to local SQLite when network is unavailable
  - Push to GULA backend when connectivity resumes
  - Conflict resolution (last-write-wins, server authoritative)
- **Device trust model:** Public key registration, trust scoring, heartbeat monitoring
- **Edge SDK** includes `SyncQueue`, `SyncEngine`, `ConflictResolver` for mobile apps

### Consequences

**Positive:**
- Labs operate continuously during network outages
- No data loss from instrument transmissions
- Backpressure absorbed by edge buffer, not instruments

**Negative:**
- Edge agent requires local hardware and maintenance
- Sync conflict resolution may lose client-side state
- Trust management adds operational overhead
- Requires monitoring for offline devices that never reconnect
