# Architecture Decision Records — National Healthcare Domain

## ADR-001: Separate Declarative Base for National Domain

**Status:** Accepted  
**Context:** The existing application uses a single `declarative_base()` in `database.py`. Adding ~47 new models with class names that may overlap (e.g., `Patient`, `Consent`) causes `InvalidRequestError: Multiple classes found for path "X"`.  
**Decision:** Create a separate `NationalBase = declarative_base()` in `backend/app/national/base.py`. All national domain models inherit from this base. Foundation mixins (TimestampMixin, etc.) work correctly because they only define `Column(...)` at class level.  
**Consequence:** Models from `models/` and `models/national/` live in independent registries. The national domain can have class names like `Patient` without conflicting. Foundation tables (`patients`, `citizens`) remain untouched.

## ADR-002: Health Number as Public Identifier

**Status:** Accepted  
**Context:** Iraqi National ID is legally sensitive and must never be stored in plaintext or exposed publicly. The system needs a public-facing identifier for patient portals, lab reports, QR codes, and barcodes.  
**Decision:** Introduce the **Health Number** as the sole public healthcare identifier. Format: `IQ` + 8 digits (e.g., `IQ12345678`). Stored in `national_citizens.health_number` — unique, indexed, visible everywhere. National ID is stored as an HMAC-SHA256 hash (`national_id_hash`) and never exposed.  
**Consequence:** All external references use health number. National ID is used only for deduplication and government reporting.

## ADR-003: Single Citizen Model for All Identity Types

**Status:** Accepted  
**Context:** The platform must support Iraqi citizens, newborns, foreigners, residents, visitors, and unknown patients. Previously, each identity type had a separate disconnected representation.  
**Decision:** The `Citizen` model in `national_citizens` table stores all identity types with an `identity_status` discriminator (`active`, `merged`, `deceased`, `inactive`, `suspended`, `pending_verification`). Type-specific models (Newborn, Foreigner, Visitor) reference `Citizen.citizen_id` and store type-specific attributes.  
**Consequence:** One canonical identity table for all 48M citizens. Type-specific details are in child tables joined by FK.

## ADR-004: FHIR R4 as Canonical Interoperability Format

**Status:** Accepted  
**Context:** The platform needs a standard healthcare data exchange format. HL7 v2 is used by lab instruments; FHIR R4 is the modern standard for APIs.  
**Decision:** All external healthcare data exchange MUST use FHIR R4. The national FHIR layer provides mappers from internal models → FHIR resources. HL7 v2 is handled exclusively at the device bridge layer (`services/device_bridge/`).  
**Consequence:** All APIs that serve healthcare data return FHIR-compatible JSON. Internal consumers use mappers that produce FHIR resources.

## ADR-005: Event-Driven Workflows with Compensation

**Status:** Accepted  
**Context:** Healthcare workflows must be reliable, auditable, and support compensation (rollback) when steps fail.  
**Decision:** Each workflow is a state machine with typed steps. On failure, the workflow engine calls `compensate()` which reverses completed steps in reverse order. Events are emitted at each state transition via `shared.events.EventBus`.  
**Consequence:** Workflows are self-documenting (step names in code), auditable (events for each step), and resilient (compensation handles partial failures).

## ADR-006: ABAC + RBAC for Healthcare Security

**Status:** Accepted  
**Context:** Healthcare data requires fine-grained access control beyond simple roles: patient consent, purpose of use, minimum necessary access, break glass, VIP protection, minor protection.  
**Decision:** Implement layered security: RBAC for role-permission checks (fast path), ABAC for contextual decisions (sensitive records, VIP, minors, emergency), and dedicated services for consent enforcement, break glass, and audit trail.  
**Consequence:** All access decisions go through ABAC engine first, with RBAC as a fast pre-check. Break glass triggers immediate audit notification and 24-hour review requirement.
