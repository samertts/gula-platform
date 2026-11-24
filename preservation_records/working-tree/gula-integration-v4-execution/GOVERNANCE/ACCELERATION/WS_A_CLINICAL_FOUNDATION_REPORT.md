# Workstream A — Clinical Foundation Report

**Program:** GULA Accelerated Parallel Health Core Development Program
**Workstream:** WS A (Clinical Foundation)
**Date:** 2026-11-18
**Status:** IMPLEMENTED AND VERIFIED IN SYNTHETIC SANDBOX — **NOT PRODUCTION-ACTIVATED**
**Governing decision:** `GOVERNANCE/FINAL_DECISION.md` remains **HOLD**; MPI verdict remains **REJECT**.
This report is development evidence only. It is not a clinical-readiness, release or safety claim.

---

## 1. Files created (all inside the three WS-A writable paths)

### Production source — `backend/app/health_core/clinical/` (8 files)

| File | Purpose |
|---|---|
| `__init__.py` | Public API of the clinical workstream; re-exports entities, services, ports, adapters and errors. |
| `errors.py` | `ClinicalValidationError`, `UnknownClinicalEntityError` — structured extensions of the shared `HealthCoreError` contract. |
| `validation.py` | Synthetic-reference, label, ICD-style, LOINC-style, UCUM-style unit, finite-number and UTC-timestamp validation. |
| `entities.py` | Frozen, slotted domain entities and enums for all six domains, plus the encounter legal-transition table. |
| `ports.py` | `EventSink` and generic `ClinicalRepository[T]` Protocols (interfaces declared before adapters). |
| `repositories.py` | `InMemoryEventLog` and `InMemoryRepository[T]` — process-local adapters with operation fingerprints. |
| `services.py` | Idempotent services and the encounter/diagnosis state machines (1006 lines). |
| `context.py` | `ClinicalContext` composition root wiring all six services to one identity port, event log and in-memory repositories. |

### Tests — `backend/tests/health_core/` (5 NEW files, existing files untouched)

| File | Tests |
|---|---|
| `test_clinical_practitioner.py` | 8 |
| `test_clinical_organization.py` | 7 |
| `test_clinical_encounter.py` | 10 |
| `test_clinical_diagnosis_observation.py` | 10 |
| `test_clinical_medical_record.py` | 6 |
| **Total** | **41** |

### Report

| File | Purpose |
|---|---|
| `GOVERNANCE/ACCELERATION/WS_A_CLINICAL_FOUNDATION_REPORT.md` | This report. |

**No other path was created or modified by WS A.** In particular `backend/app/factory.py`,
`backend/app/main.py`, `backend/tests/health_core/conftest.py`, `GOVERNANCE/FINAL_DECISION.md`,
all MPI files and all other workstreams' files were left untouched.

---

## 2. Domain-by-domain implementation summary

Every domain is keyed exclusively to an opaque `SYN-PAT-…` `PatientRef` obtained from
`PatientIdentityPort`. Unknown patients raise `UnknownPatientError`; cross-tenant access raises
`TenantMismatchError`; no patient is ever implicitly created.

### 2.1 Practitioner (`PractitionerRegistry`)
- In-memory, tenant-scoped synthetic practitioner registry.
- Role is a `PractitionerRole` enum (physician, nurse, lab technician, radiologist, pharmacist).
- Qualification is a validated, non-identifying synthetic label; `active: bool` is recorded at
  registration and reflected in the emitted `PRACTITIONER_REGISTERED` payload.
- `active_for_tenant()` returns only active practitioners; inactive practitioners are still
  retrievable by id but are refused as encounter authors.
- Duplicate idempotency key with a different argument set raises `DuplicateEntityError`; an
  identical replay returns the original entity and emits no second event.

### 2.2 Organization / Facility (`OrganizationRegistry`)
- Synthetic `Organization` containers and `Facility` entities with `FacilityType` validation.
- A facility must reference an existing, active organisation in the **same** tenant;
  `require_facility()` additionally verifies the exact parent organisation when supplied.
- `FACILITY_REGISTERED` events carry `AggregateType.FACILITY`, the facility id and tenant id.
- Organisation creation emits no event: the shared `AggregateType`/`EventType` vocabulary has no
  organisation aggregate or `organization.registered` value, and no misleading label was invented.

### 2.3 Encounter (`EncounterService`)
- Full lifecycle state machine:
  `planned → in_progress → admitted → discharged`, plus `transferred` and `cancelled`.
- Legal edges are declared in `LEGAL_ENCOUNTER_TRANSITIONS`; every illegal edge raises
  `InvalidStateTransitionError` with `from_status`/`to_status` details and leaves state untouched.
- Every accepted transition increments `version`, produces a new frozen `Encounter` and emits an
  immutable `DomainEvent` with `AggregateType.ENCOUNTER` and the correct tenant.
- Encounters validate the patient through the identity port, an active practitioner in the same
  tenant, and an active facility in the same tenant.
- Clinical notes are keyed, idempotent, author-validated, tenant/patient scoped and emit
  `NOTE_ADDED` on the encounter aggregate.
- Transitions and note creation are idempotent via `SYN-TRN-` / `SYN-NOT-` keys.

### 2.4 Diagnosis (`DiagnosisService`)
- `record()` validates an ICD-style pattern (`^[A-TV-Z][0-9]{2}(\.[0-9A-Z]{1,4})?$`), a short
  description and a `Severity` enum; codes are normalised to upper case.
- Each problem links to exactly one synthetic encounter **of the same synthetic patient**; a
  cross-patient encounter raises `ForbiddenSyntheticOperationError`.
- `resolve()` moves `active → resolved`, sets `resolved_at`, increments `version`, and emits a
  `DIAGNOSIS_RECORDED` transition event with `payload["transition"] = "resolve"`.
- `list_for_encounter()` and `list_for_patient()` are deterministic (asserted-at, then id).

### 2.5 Clinical Observations (`ObservationService`)
- `record()` validates a LOINC-style code (`^[0-9]{4,6}-[0-9]$`), a UCUM-style unit, a finite
  numeric value and a timezone-aware `recorded_at` (normalised to UTC).
- Code-specific unit constraints are enforced for heart rate, temperature, blood pressure and
  oxygen saturation; structural validation only (no LOINC check-digit recomputation).
- `query()` filters by patient, optional encounter and optional code, and always orders by
  `recorded_at` then observation id.
- Every successful recording emits `OBSERVATION_RECORDED` with `AggregateType.OBSERVATION`.

### 2.6 Medical Record — non-identity-linkage components (`MedicalRecordService`)
- `RecordScope` explicitly declares one tenant and one or more patient references;
  `assert_single_patient()` raises `ForbiddenSyntheticOperationError` for zero, duplicate or
  multiple distinct patient references.
- `aggregate()` gathers encounters, diagnoses, observations and notes for **one** synthetic
  patient only; `open()` does the same and emits `MEDICAL_RECORD_OPENED` with
  `AggregateType.MEDICAL_RECORD`, the patient ref as aggregate id and item counts in the payload.
- No identity resolution, canonical-patient lookup, NHID, MPI call or cross-patient join exists.

---

## 3. Public API

### Composition root

```python
ClinicalContext(identity: PatientIdentityPort,
                events: EventSink = InMemoryEventLog()) -> ClinicalContext
ClinicalContext.event_history() -> tuple[DomainEvent, ...]
# services exposed as: .practitioners, .organizations, .encounters,
#                     .diagnoses, .observations, .medical_records
```

### Services (all keyword-only after `self`)

```python
PractitionerRegistry(events: EventSink, practitioners: ClinicalRepository[Practitioner] | None = None)
  .register(*, tenant_id: str, idempotency_key: str, role: PractitionerRole | str,
            qualification: str, active: bool = True) -> Practitioner
  .get(*, tenant_id: str, practitioner_id: str) -> Practitioner
  .active_for_tenant(tenant_id: str) -> tuple[Practitioner, ...]

OrganizationRegistry(events: EventSink,
                     organizations: ClinicalRepository[Organization] | None = None,
                     facilities: ClinicalRepository[Facility] | None = None)
  .register_organization(*, tenant_id: str, idempotency_key: str, label: str) -> Organization
  .register_facility(*, tenant_id: str, idempotency_key: str, organization_id: str,
                     label: str, facility_type: FacilityType | str) -> Facility
  .get_organization(*, tenant_id: str, organization_id: str) -> Organization
  .get_facility(*, tenant_id: str, facility_id: str) -> Facility
  .require_facility(*, tenant_id: str, facility_id: str,
                    organization_id: str | None = None) -> Facility
  .facilities_for_organization(*, tenant_id: str, organization_id: str) -> tuple[Facility, ...]

EncounterService(identity: PatientIdentityPort, practitioners: PractitionerRegistry,
                 organizations: OrganizationRegistry, events: EventSink,
                 encounters=None, notes=None, transitions=None)
  .create(*, tenant_id: str, idempotency_key: str, patient_ref: str,
          practitioner_id: str, facility_id: str, reason: str) -> Encounter
  .transition(*, tenant_id: str, encounter_id: str,
              to_status: EncounterStatus | str, idempotency_key: str) -> Encounter
  .add_note(*, tenant_id: str, encounter_id: str, idempotency_key: str,
            author_practitioner_id: str, text: str) -> ClinicalNote
  .get_encounter(*, tenant_id: str, encounter_id: str) -> Encounter
  .list_for_patient(*, tenant_id: str, patient_ref: str) -> tuple[Encounter, ...]
  .notes_for_encounter(*, tenant_id: str, encounter_id: str) -> tuple[ClinicalNote, ...]
  .notes_for_patient(*, tenant_id: str, patient_ref: str) -> tuple[ClinicalNote, ...]

DiagnosisService(identity: PatientIdentityPort, encounters: EncounterService,
                 events: EventSink, diagnoses=None, transitions=None)
  .record(*, tenant_id: str, idempotency_key: str, patient_ref: str, encounter_id: str,
          code: str, description: str, severity: Severity | str) -> Diagnosis
  .resolve(*, tenant_id: str, diagnosis_id: str, idempotency_key: str) -> Diagnosis
  .get_diagnosis(*, tenant_id: str, diagnosis_id: str) -> Diagnosis
  .list_for_encounter(*, tenant_id: str, encounter_id: str) -> tuple[Diagnosis, ...]
  .list_for_patient(*, tenant_id: str, patient_ref: str) -> tuple[Diagnosis, ...]

ObservationService(identity: PatientIdentityPort, encounters: EncounterService,
                   events: EventSink, observations=None)
  .record(*, tenant_id: str, idempotency_key: str, patient_ref: str, encounter_id: str,
          code: str, display: str, value: float, unit: str,
          recorded_at: datetime) -> Observation
  .query(*, tenant_id: str, patient_ref: str, encounter_id: str | None = None,
         code: str | None = None) -> tuple[Observation, ...]

MedicalRecordService(identity: PatientIdentityPort, encounters: EncounterService,
                     diagnoses: DiagnosisService, observations: ObservationService,
                     events: EventSink)
  .aggregate(*, scope: RecordScope) -> MedicalRecordView
  .open(*, scope: RecordScope) -> MedicalRecordView

RecordScope(tenant_id: str, patient_refs: tuple[str, ...])
  .assert_single_patient() -> str
```

### Interfaces and adapters

```python
class EventSink(Protocol):
    def append(self, event: DomainEvent) -> None: ...
    def all(self) -> tuple[DomainEvent, ...]: ...

class ClinicalRepository[T](Protocol):  # PEP 695 in adapters; TypeVar Protocol in ports.py
    def add_if_absent(self, key: str, entity: T, fingerprint: str) -> tuple[T, bool]: ...
    def fingerprint_of(self, key: str) -> str | None: ...
    def get(self, key: str) -> T | None: ...
    def save(self, key: str, entity: T) -> T: ...
    def all(self) -> tuple[T, ...]: ...

InMemoryEventLog()  # append / all / count
InMemoryRepository[T]()  # add_if_absent / fingerprint_of / get / save / all / count
```

### Validation helpers (`app.health_core.clinical.validation`)

```python
require_synthetic_ref(value: str, *, field: str, prefix: str | None = None) -> str
require_label(value: str, *, field: str, max_length: int = 120) -> str
require_icd_code(value: str, *, field: str = "code") -> str
require_loinc_code(value: str, *, field: str = "code") -> str
require_unit(code: str, value: str, *, field: str = "unit") -> str
require_finite_number(value: object, *, field: str) -> float
require_utc_timestamp(value: datetime, *, field: str) -> str
utc_now_iso() -> str
```

---

## 4. Verification evidence

### Required command (exact)

```
cd /home/samertts/workspace/projects/gula-integration/backend
ENV=test RUNTIME_MODE=test PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=.:.. \
  /tmp/opencode/mpi-venv/bin/python -m pytest tests/health_core/test_clinical_*.py -q --tb=short
```

**Result:** `41 passed, 1 warning in 0.81s` — 0 failed, 0 skipped, 0 errors.
The single warning is a pre-existing `StarletteDeprecationWarning` from an unrelated installed
`fastapi/testclient.py`; no warning originates in WS-A code.

### Static sandbox guards (existing file, not modified)

```
ENV=test RUNTIME_MODE=test PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=.:.. \
  /tmp/opencode/mpi-venv/bin/python -m pytest tests/health_core/test_sandbox_guards.py -q --tb=short
```

**Result:** `4 passed, 1 warning in 0.90s`. This proves (by AST inspection across *every* file under
`app/health_core`, including the new package) that there are no forbidden MPI/DB/network imports,
no forbidden identity-link or DB-session names, and no `health_core` reference in `factory.py` or
`main.py`.

### Lint / format / typing (WS-A paths only)

```
/tmp/opencode/mpi-venv/bin/python -m ruff check app/health_core/clinical/ tests/health_core/test_clinical_*.py
  -> All checks passed!
/tmp/opencode/mpi-venv/bin/python -m ruff format --check app/health_core/clinical/ tests/health_core/test_clinical_*.py
  -> 13 files already formatted
MYPYPATH=.:.. /tmp/opencode/mpi-venv/bin/python -m mypy --strict --no-incremental \
  --python-version 3.12 --config-file /dev/null --follow-imports=silent app/health_core/clinical/
  -> Success: no issues found in 8 source files
```

`--follow-imports=silent` is used only because a pre-existing file outside WS-A's writable scope
(`app/domain/order_state.py:63,81`) has untyped parameters; following it produces 2 errors that
are not in WS-A code. No WS-A file has a type error.

### Cross-workstream observation (not WS-A scope)

A wider run of the whole `tests/health_core/` directory collected 349 tests: 342 passed, 5 failed
and 2 errors. All 7 non-passing cases belong to other workstreams' concurrently added files
(`test_integration_arabic_rtl_a11y.py`, `test_integration_auth_boundaries.py`,
`test_integration_conflicts.py`, `test_integration_offline.py`, `test_lab_identity_tenant.py`).
All 41 WS-A tests and all 4 sandbox-guard tests passed in that same run. WS A did not modify any
of those files and makes no claim about them.

---

## 5. Classification per domain

| Domain | Classification | Basis |
|---|---|---|
| Practitioner | **VERIFIED** | 8 tests: registration, qualification/role validation, active status, tenant isolation, event emission, idempotent replay and key conflict. |
| Organization / Facility | **PARTIALLY VERIFIED** | All required behavior verified (hierarchy, same-tenant enforcement, facility event, idempotency, 7 tests). "Partially" reflects only that the shared `EventType`/`AggregateType` vocabulary has no organisation event/aggregate; organisation creation emits no event. |
| Encounter | **PARTIALLY VERIFIED** | Lifecycle legality, versions, notes, tenant+patient scoping, idempotency and event ordering verified (10 tests). "Partially" reflects only that the shared vocabulary has no `encounter.started`, so `planned → in_progress` emits `ENCOUNTER_CREATED` with an explicit `transition` payload. |
| Diagnosis | **PARTIALLY VERIFIED** | ICD-style validation, severity, single-encounter link, resolve, ordering and idempotency verified (tests in the 10-test diagnosis/observation file). "Partially" reflects only that the shared vocabulary has no `diagnosis.resolved`, so resolve emits `DIAGNOSIS_RECORDED` with `payload["transition"] = "resolve"`. |
| Clinical Observations | **VERIFIED** | 10 tests covering LOINC structure, UCUM units and code-specific unit constraints, finite values, UTC timestamp normalisation, recorded-at ordering, query filters, tenant/patient scoping and event emission. |
| Medical Record (non-identity components) | **VERIFIED** | 6 tests: aggregate of all four data types for one patient, `MEDICAL_RECORD_OPENED` event, multi-patient refusal, cross-tenant refusal, unknown-patient refusal, empty-scope refusal. |

No domain is **BLOCKED** or **NOT IMPLEMENTED**. Every "PARTIALLY VERIFIED" label is a vocabulary
limitation in the shared foundation, not an unimplemented requirement; no new event type was
fabricated and no shared file was modified.

---

## 6. Security and isolation notes

- **Identity seam:** the only patient dependency is `PatientIdentityPort`; construction of any
  patient-scoped service requires an identity port, and every operation resolves the patient with
  `tenant_id` + `patient_ref`. There is no MPI/NHID/canonical-patient adapter in this package.
- **Synthetic-only identifiers:** all keys and patient refs must be `SYN-` prefixed opaque values;
  `reject_national_identifier()` rejects digit-only and long alphanumeric real-looking values.
  No field holds a name, DOB, phone, national number or any other real-world identifier.
- **Tenant isolation:** every read, create, transition and aggregate checks the entity's tenant
  against the caller's tenant; mismatches raise `TenantMismatchError` (403-shaped). Facility→
  organisation and encounter→facility links are same-tenant only.
- **No cross-patient aggregation:** `RecordScope` refuses zero, multiple or duplicate patient refs
  with `ForbiddenSyntheticOperationError` (403-shaped) before any data is gathered.
- **Immutable evidence:** events are frozen `DomainEvent` objects created by the shared `new_event`;
  the log is append-only and returns immutable tuples. Entities are frozen and slotted; state
  changes create new versions.
- **Idempotency:** entity ids are caller-supplied synthetic idempotency keys; an identical replay
  returns the original entity with no new event, while a conflicting reuse raises
  `DuplicateEntityError` (409-shaped) with no state change.
- **No persistence / no activation:** no SQLAlchemy, no `app.database`, no session, no migration,
  no DDL, no filesystem write, no HTTP client, no socket, no route registration and no broker
  publish exists in the package. State dies with the in-memory object. This was confirmed by the
  existing AST guard tests (4 passed).

---

## 7. Residual limitations

1. **Event vocabulary gaps** (shared, unmodified): no `organization.registered`,
   no `encounter.started`, no `diagnosis.resolved`, no `practitioner.deactivated`. No misleading
   shared event type was invented. The reuse mapping for the two state-change gaps is explicit in
   `services.py::TRANSITION_EVENTS` and in event payloads (`transition`, `from_status`,
   `to_status`).
2. **Terminology validation is structural only**: ICD codes are pattern-checked, not validated
   against a terminology release; LOINC check digits are not recomputed; UCUM units are an
   allow-list, not a full UCUM parser. This is intentional for synthetic development.
3. **In-memory only**: repositories and events are process-local and non-durable. This is a
   deliberate safety property, not a persistence implementation.
4. **No authorization layer**: WS A enforces tenant/patient scoping, not RBAC/ABAC policy. Any
   future boundary must add authorization before this code could be considered for use.
5. **No clinical-safety claim**: severity, diagnosis and observation values are synthetic
   fixtures; no thresholding, alerting, interpretation or clinical decision support is provided.
6. **Wider suite**: 5 failures and 2 errors exist in concurrently added non-WS-A test files, as
   recorded in §4. WS A neither caused nor repaired them.

---

## 8. Explicit non-activation statement

**Nothing in this workstream is production-activated.** No production route, feature flag,
startup hook, `app/factory.py` or `app/main.py` change was made. No migration, DDL, schema change,
production database access, real patient record, real NID, secret or MPI write was introduced.
The package is an isolated synthetic development surface only. It must not be described as
clinically usable, releasable or production ready while `GOVERNANCE/FINAL_DECISION.md` remains
**HOLD** and the MPI verdict remains **REJECT**.
