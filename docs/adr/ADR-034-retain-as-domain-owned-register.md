# ADR-034: Retain-as-Domain-Owned Register (authorization, audit, document, search, notifications, barcode/QR)

**Status:** Accepted
**Date:** 2026-08-08
**Deciders:** Engineering Lead, Platform Architect, CTO
**Supersedes:** (none — finalizes the retain register for the PROGRAM-01 final closure)
**Related:** ADR-028, ADR-029, ADR-030, ADR-024

---

## Context

The structural migration phase (ADR-028) reduces the acknowledged Shared Core
reimplementation findings in
`.ai/core/architecture/constitution_baseline.json` to canonical providers
(`SHARED_CORE_CATALOG` in `backend/app/domain_platform/shared_core.py`).

PROGRAM-01 FINAL CLOSURE (Wave 5 orders 22 + 24) freezes every remaining
finding with an explicit **`Retain as Domain-Owned`** (or **`False Positive`**)
state. These are legitimate domain-scoped implementations or interface
contracts that are NOT Shared Core violations: re-pointing them to the
canonical provider would either (a) lose domain-owned behavior, (b) remove
live functionality in favor of a stub, (c) change stored data (barcode
format), or (d) replace an authoritative facade with itself.

The gate's `_is_canonical` exemption keeps the canonical provider paths
allowed; every retained path carries an explicit state in the baseline JSON so
the scan acknowledges it and blocks any NEW duplicate signal.

## Decision

Register the following findings as **frozen** with an explicit state in
`.ai/core/architecture/constitution_baseline.json` (Wave 5 orders 22 + 24,
ADR-034):

### Retain as Domain-Owned

| # | Path | Capability | Why retained |
|---|---|---|---|
| 4 | `document_intelligence/application/interfaces.py` — `AuditService(ABC)` | audit | Interface contract, not an implementation |
| 8 | `national/task_engine/domain/repository.py` — `TaskAuditLogRepository(ABC)` | audit | Domain contract |
| 10 | `services/authorization_service.py` — `AuthorizationAuditService` (decision-log, own schema) | audit | Canonical lacks decision/policy/risk fields |
| 12 | `document_intelligence/domain/repository.py` — `DocumentRepository(ABC)` | document_engine | Interface only |
| 13 | `document_intelligence/infrastructure/repository.py` — `SqlDocumentRepository` (real) | document_engine | Canonical is a stub (NotImplementedError) |
| 14 | `national/document_platform/application/interfaces.py` — `PDFGenerator(ABC)` | document_engine | Interface only, zero concrete impls |
| 15 | `national/document_platform/domain/repository.py` — `DocumentRepository(ABC)` | document_engine | Interface only |
| 16 | `national/document_platform/infrastructure/repository.py` — `SQLAlchemyDocumentRepository` (real) | document_engine | Canonical is a stub; live repo is real |
| 19 | `citizen_platform/identity.py` — `HealthIdentityService` (national-id verify) | identity | Different stack; citizen-portal national-id verification |
| 21 | `services/authorization_service.py` — `IdentityService.get_identity_context` | identity | Analogous but legacy lab-UI scoped |
| 23 | `citizen_platform/notifications.py` — `CitizenNotificationService` (in-memory inbox) | notifications | Canonical delivers but has no persistence; this has neither (data-loss risk) |
| 29 | `control_plane/policy/enforcer.py` — `PolicyEnforcer` | authorization | Component-governance policy, NOT user access control |
| 30 | `services/authorization_service.py` — `PermissionService/RoleService/PolicyService` (DB-backed) | authorization | Parallel ABAC for the legacy lab UI path (strategic path: NIAM) |
| 31 | `document_intelligence/backup_dr.py` — `BackupScheduler` (async DR loop) | scheduler | Real DR utility, test-covered; dormant |
| 34 | `document_intelligence/application/interfaces.py` — `SearchService(ABC)` | search_engine | Interface only |
| 37 | `national/fhir/search.py` — `FHIRSearchEngine` (in-memory) | search_engine | National-layer FHIR logic; re-exported public API |
| 40 | `models/sample.py` — `generate_barcode` (column default, live LIMS) | barcode_engine | Different format/length — re-point changes stored barcode values (data impact) |
| 41 | `national/document_platform/application/service.py` — `generate_qr` (doc-verify token) | qr_engine | Document verification token, not image QR |
| 45 | `document_intelligence/application/interfaces.py` — `generate_pdf` (abstract) | document_engine | Abstract only, zero concrete impls |

### False Positive (retained, no duplicate)

| # | Path | Capability | Why retained |
|---|---|---|---|
| 26 | `platform/notifications.py` — `NotificationService` (facade) | notifications | IS the canonical facade — delegates, no duplication |
| 48 | `kernel/runtime_sdk.py` — `publish_event` (facade over kernel bus) | events | Facade, not a reimplementation |

**Behavioral equivalence:** freezing changes no behavior. Every retained
implementation keeps running exactly as before. The state fields are added to
the baseline JSON; the gate continues to block any NEW duplicate signal in
these capabilities.

## Alternatives Considered

### A. Migrate all retained findings to canonical providers

Rejected individually and collectively. The retained findings are either
interfaces (no implementation to migrate), live implementations whose
canonical counterpart is an inactive stub (`document_engine` repositories,
`search_engine`), data-impacting (`barcode_engine` format change), or
domain-owned logic that the canonical provider explicitly does not cover
(`authorization` legacy path, `audit` decision-log, `notifications` inbox
persistence). See the classification §2 for per-finding analysis.

### B. Leave the retained findings actionable

Rejected. PROGRAM-01 final closure must leave **zero actionable** findings.
Retained findings have no safe migration today; freezing them with an explicit
state is the correct governance (same reasoning as ADR-030 alternative C).

### C. Delete the retained interfaces/repositories

Rejected. ADR-028 requires evidence-based, reversible actions; dormant
interfaces are strategic contracts for the national layer. Deleting them would
break imports and remove documented domain APIs.

## Consequences

**Positive**

- The register ends PROGRAM-01 with **0 actionable** findings: 25 frozen
  (19 Domain-Owned + 1 Strategic Exception + 3 kernel-domain + 2 False
  Positive) + 2 resolved (encryption).
- The gate remains deterministic: any NEW signal in the covered capabilities
  outside the acknowledged paths fails the PR.
- Domain-owned interfaces and live repositories are formally protected from
  unsafe consolidation.

**Negative**

- These implementations remain outside `shared/`; future canonical
  consolidation (e.g., activating a real `capabilities/document_management`
  provider) requires dedicated ADRs.
- `barcode_engine` format unification remains deferred (data-impacting).

**Neutral**

- No code, schema, API, or behavior changes.

## References

- ADR-028 — Structural Migration Rules (`docs/adr/ADR-028-structural-migration.md`)
- ADR-029 — Canonical Provider Promotion (`docs/adr/ADR-029-canonical-provider-promotion.md`)
- ADR-030 — Kernel Domain Register (`docs/adr/ADR-030-kernel-domain-register.md`)
- `backend/app/domain_platform/shared_core.py` — `SHARED_CORE_CATALOG`
- `docs/baselines/ARCHITECTURAL_MIGRATION_CLASSIFICATION.md` — §2, §3 (orders 22 + 24), Wave 5 table
