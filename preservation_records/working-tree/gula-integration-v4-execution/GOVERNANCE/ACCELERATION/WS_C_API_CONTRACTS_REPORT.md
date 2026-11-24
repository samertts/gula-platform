# WORKSTREAM C — API & INTEGRATION CONTRACTS REPORT

**Program:** GULA Accelerated Parallel Health Core Development Program
**Workstream:** C (API and Integration Contracts)
**Date:** 2026-11-18
**Repository:** `/home/samertts/workspace/projects/gula-integration`
**Contract family:** `1.0.0-alpha1` · status `LOCAL_SYNTHETIC_ONLY`
**Classification:** SYNTHETIC / CONTRACT-ONLY / NOT PRODUCTION-EXPOSED

> **Nothing in this workstream is exposed.** No FastAPI router, endpoint, route or
> production registration was created or modified. `app/factory.py`, `app/main.py`,
> all MPI files, `GOVERNANCE/FINAL_DECISION.md` (HOLD) and every other governance
> document were left untouched. No database, migration, DDL, real patient data or
> real identifier is involved. No commit, push, merge, rebase or PR was performed.

---

## 1. Files created (14 new files; zero modified files)

### Contracts package — `backend/app/health_core/contracts/`

| File | Purpose |
|---|---|
| `__init__.py` | Public re-exports of the whole contract family. |
| `version.py` | `HEALTH_CORE_CONTRACT_VERSION = "1.0.0-alpha1"`, `CONTRACT_STATUS`, `COMPATIBLE_MAJOR`, `contract_major()`, `is_compatible_version()`. |
| `catalogue.py` | `ContractDomain` (11), `ContractOperation` (22), `DOMAIN_OPERATIONS` grouping. |
| `models.py` | Strict Pydantic v2 request/response models for all 11 domains, `SyntheticRef` / `ArabicSafeText` / `CodeValue` annotated types, `DOMAIN_SCHEMAS`. |
| `errors.py` | `HealthCoreErrorResponse`, `ERROR_CATALOGUE`, `error_response_from()` mapping every shared error. |
| `authorization.py` | `Role`, `Permission`, `AuthorizationBoundary`, `AUTHORIZATION_BOUNDARIES`, `boundary_for()`. |
| `events.py` | `EventDefinition`, `EVENT_CATALOGUE`, `EventContractViolation`, `validate_domain_event()`. |
| `idempotency.py` | Header/TTL/constants, `ReplaySemantics`, `IDEMPOTENCY_SEMANTICS`, `new_idempotency_key()`, `validate_idempotency_key()`, `IdempotencyScope`. |

### Tests — `backend/tests/health_core/`

| File | Scope |
|---|---|
| `test_contracts_schemas.py` | Valid/invalid synthetic payloads for all 11 domains, Arabic text, immutability, serialisation. |
| `test_contracts_errors.py` | Every shared error code maps to the stable client shape. |
| `test_contracts_authorization.py` | Every operation has a non-public boundary with permission + role. |
| `test_contracts_events.py` | Every `EventType` has a definition; sample events validate; deviations rejected. |
| `test_contracts_idempotency.py` | Key shape, replay/conflict documentation, tenant-bound scope. |
| `test_contracts_version.py` | Version constant/compatibility + AST proof that no FastAPI router/route exists. |

No existing file was edited, deleted, moved or staged. All 463 pre-existing uncommitted
entries were preserved (no `git add/reset/clean`, no branch operations).

---

## 2. Contract catalogue

### 2.1 Operations & schemas (11 domains × create/read)

| # | Domain | Operation (create / read) | Request model | Response model |
|---|---|---|---|---|
| 1 | Practitioner | `practitioner.create` / `practitioner.read` | `PractitionerCreateRequest` | `PractitionerResponse` |
| 2 | Organization | `organization.create` / `organization.read` | `OrganizationCreateRequest` | `OrganizationResponse` |
| 3 | Facility | `facility.create` / `facility.read` | `FacilityCreateRequest` | `FacilityResponse` |
| 4 | Medical Record | `medical_record.create` / `medical_record.read` | `MedicalRecordCreateRequest` | `MedicalRecordResponse` |
| 5 | Encounter | `encounter.create` / `encounter.read` | `EncounterCreateRequest` | `EncounterResponse` |
| 6 | Diagnosis | `diagnosis.create` / `diagnosis.read` | `DiagnosisCreateRequest` | `DiagnosisResponse` |
| 7 | Observation | `observation.create` / `observation.read` | `ObservationCreateRequest` | `ObservationResponse` |
| 8 | Lab Order | `lab_order.create` / `lab_order.read` | `LabOrderCreateRequest` | `LabOrderResponse` |
| 9 | Specimen | `specimen.create` / `specimen.read` | `SpecimenCreateRequest` | `SpecimenResponse` |
| 10 | Lab Result | `lab_result.create` / `lab_result.read` | `LabResultCreateRequest` | `LabResultResponse` |
| 11 | Result Verification | `result_verification.create` / `result_verification.read` | `ResultVerificationCreateRequest` | `ResultVerificationResponse` |

22 operations total. All models use `model_config = ConfigDict(extra="forbid", frozen=True,
str_strip_whitespace=True, ...)` and `Field(...)` on every field. Every response carries
`ref`, `tenant_id`, `contract_version` and `contract_status`. All references are opaque
`SYN-` values validated via the shared `reject_national_identifier` / `is_synthetic_id`
helpers (imported, never redefined); empty, digit-only, long-alphanumeric and non-`SYN-`
values are rejected. Free-text fields preserve Arabic/unicode verbatim.

### 2.2 Error contract

| Shared error (`code`) | status | retryable | Client mapping |
|---|---|---|---|
| `HealthCoreError` (`HEALTH_CORE_ERROR`) | 400 | false | `HealthCoreErrorResponse` |
| `InvalidSyntheticReferenceError` (`INVALID_SYNTHETIC_REFERENCE`) | 400 | false | `HealthCoreErrorResponse` |
| `UnknownPatientError` (`UNKNOWN_PATIENT`) | 404 | false | `HealthCoreErrorResponse` |
| `TenantMismatchError` (`TENANT_MISMATCH`) | 403 | false | `HealthCoreErrorResponse` |
| `DuplicateEntityError` (`DUPLICATE_ENTITY`) | 409 | false | `HealthCoreErrorResponse` |
| `InvalidStateTransitionError` (`INVALID_STATE_TRANSITION`) | 409 | false | `HealthCoreErrorResponse` |
| `ForbiddenSyntheticOperationError` (`FORBIDDEN_SYNTHETIC_OPERATION`) | 403 | false | `HealthCoreErrorResponse` |

Stable client shape: `code`, `message`, `status_code`, `retryable`, `details`, `request_id`,
`timestamp`, `detail` (legacy alias of `message`), `detail_ar`. `ERROR_CATALOGUE` is derived
from the shared classes themselves, so a new shared error cannot be silently omitted.

### 2.3 Authorization contract

22/22 operations declare exactly one `AuthorizationBoundary`; **0 public operations**.
Permissions use the reference-data style `health_core:<resource>.<action>` with a
`describe()` helper; minimum roles are `viewer` (reads), `clinician` (clinical creates),
`lab_technician` (lab-order/specimen/result/verification creates). Every boundary is
tenant-scoped.

### 2.4 Event contract

22/22 shared `EventType` values have an `EventDefinition` (aggregate type + required
payload keys). Event names are imported from `app.health_core.common` — lowercase
`<entity>.<action>` dotted convention. `validate_domain_event()` enforces registered
type, matching aggregate, required payload keys and synthetic `SYN-` ids. No broker or
publisher exists.

### 2.5 Idempotency contract

| Element | Value |
|---|---|
| Header | `Idempotency-Key` |
| Key shape | `SYN-IDK-<12 hex>` (opaque, via shared `new_synthetic_id`) |
| Scope | per `(tenant, key, operation)`; never global |
| TTL | 86 400 s (24 h) |
| New key | process once (`create_new`) |
| Same key + same operation/payload in TTL | replay stored response (`replay_stored_response`) |
| Same key + different operation/payload in TTL | conflict → `DUPLICATE_ENTITY` / 409 (`conflict`) |

---

## 3. Test result (exact)

Command (as specified):

```
cd /home/samertts/workspace/projects/gula-integration/backend && \
ENV=test RUNTIME_MODE=test PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=.:.. \
/tmp/opencode/mpi-venv/bin/python -m pytest tests/health_core/test_contracts_*.py -q --tb=short
```

**Result: `185 passed, 1 warning in ~1.03s`** (warning is a pre-existing Starlette
`TestClient`/httpx deprecation notice, unrelated to this workstream).

Additional verification:
- With pre-existing `test_sandbox_guards.py` (4) + `test_identity_port.py` (10):
  **199 passed** — the static AST guards confirm no forbidden MPI/DB imports and no
  production route activation in the whole `app/health_core` tree including contracts.
- Ruff (only the 14 WS-C paths, repo config: line 100, double quotes, `T20` no-print):
  **All checks passed** (4 auto-fixed import-order/Yoda issues; 0 remaining).

Note: a full `tests/health_core/` collection currently errors on
`test_integration_auth_boundaries.py` / `test_integration_offline.py` because a *concurrent*
workstream's `app.health_core.integration` package is still in progress. This is outside
WS-C writable paths and does not affect the WS-C result above.

---

## 4. Alignment with existing national contracts

Read-only documents consulted: `GOVERNANCE/NATIONAL_SERVICE_CONTRACTS.md`,
`GOVERNANCE/CROSS_SERVICE_INTEGRATION_MATRIX.md`,
`GOVERNANCE/NATIONAL_SERVICE_INVENTORY.md`. None was imported from or modified in code.

**(a) Conventions adopted.**
- *Versioning (R-VER-1; §3.7):* explicit SemVer-style version with an alpha prerelease,
  additive-only, major-scoped compatibility (`is_compatible_version`), no path renaming;
  a breaking re-shape would require a new major version and an owner ADR.
- *Events (R-EVT-1; §3.9):* lowercase dotted `<entity>.<action>` event names and a single
  envelope/version field, taken from the shared `EventType`/`DomainEvent` foundation;
  catalogue keyed by event type with required payload keys.
- *Errors (R-ERR-1; §3.3):* canonical envelope field names `code`, `message`, `details`,
  `request_id`, `timestamp`, `detail`/`detail_ar` (plus `status_code`/`retryable` from
  the shared synthetic error), with sanitised details and no raw exception text.
- *Idempotency (R-IDEM-1; §3.5):* `Idempotency-Key` header, per-tenant scope, 24 h TTL,
  replay of stored response, conflict mapped to an existing 409 code.
- *Authorization (R-AUTH-1; §3.2):* explicit per-operation permission string in the
  `<namespace>:<resource>.<action>` reference-data style with a `describe()` helper;
  no operation relies on authentication alone or is implicitly public.
- *Status vocabulary (§2):* classified as DRAFT/UNSERVED-equivalent, never STABLE.

**(b) Intentionally local/synthetic-only.** All 11 alpha contracts — every request/
response model, the error envelope, the 22 authorization boundaries, the 22 event
definitions and the idempotency rules — are LOCAL, SYNTHETIC-ONLY development contracts.
They use only opaque `SYN-` references, no national identifiers, no tenant data and no
FHIR/HL7 national profiles. They **MUST NOT** be presented as national production
service contracts, counted toward the 18-service inventory rows, used to close a §6
`BLOCKED` gate, or used to satisfy any journey J1–J7 hop. They are contract scaffolding
for future owner-authorised work only; promoting any of them requires the relevant ADR
(A–J) and an owner decision.

**(c) Governance docs untouched.** No existing governance document was modified. In
particular `GOVERNANCE/FINAL_DECISION.md` remains **HOLD**, the MPI verdict remains
**REJECT** (no MPI file touched), and `NATIONAL_SERVICE_CONTRACTS.md`,
`CROSS_SERVICE_INTEGRATION_MATRIX.md` and `NATIONAL_SERVICE_INVENTORY.md` are byte-unchanged.

---

## 5. Residual limitations

- Contracts only: there is no runtime validator middleware, no request parsing, no
  handler and no persistence; idempotency/event semantics are documented and tested as
  contracts, not enforced by a live component.
- No OpenAPI/FastAPI surface is generated; these schemas are not wired into `app.openapi()`
  and do not appear in the national operation census.
- Permission/role strings are local to this contract family and are not registered in the
  platform RBAC map; they are declarative only.
- Arabic message (`detail_ar`) has no translation catalogue — mapping currently mirrors
  the safe English message until an owner-approved i18n source exists.
- Synthetic-only data domain: no real identifiers, no FHIR R4 resource models and no HL7
  segments are represented by design.
- Promotion to a national contract is out of scope and gated by the ADRs in §9 of the
  national service contracts document.

---

## 6. Explicit non-exposure statement

**No endpoint is exposed and no router is created.** The contracts package contains only
Pydantic models, enums, dataclasses and pure validation/mapping functions. A dedicated
AST test (`test_contracts_package_creates_no_fastapi_router_or_route`) fails if any
contract module imports `fastapi` or references `APIRouter`/`FastAPI`, and the pre-existing
sandbox guard confirms `factory.py`/`main.py` contain no `health_core` wiring. Nothing in
this workstream is production-exposed, deployable, or reachable from the running app.
