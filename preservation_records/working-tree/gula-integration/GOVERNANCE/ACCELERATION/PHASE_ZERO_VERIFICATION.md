# Phase Zero — Current-State Verification & Parallel File Ownership Map

**Report ID:** HC-PZ-001
**Date:** 2026-11-18
**Repository:** `gula-integration` · branch `integration/gula-unification-v1` · HEAD `2827c1ff1032918aa2541aa0b47bb7f2e5d6cac0`
**Authoritative inputs:** `GOVERNANCE/HEALTH_CORE/HEALTH_CORE_READINESS_ASSESSMENT.md`, `GOVERNANCE/PROGRAM_STATUS/MPI_AND_HEALTH_CORE_FINAL_STATUS.md`, `GOVERNANCE/IDENTITY_REMEDIATION/MPI_FINAL_INDEPENDENT_AUDIT.md`, `GOVERNANCE/FINAL_DECISION.md` (read-only).
**Data:** synthetic only.

---

## 1. State verification (performed before any code was written)

| Check | Observed | Expected | Result |
|---|---|---|---|
| Branch | `integration/gula-unification-v1` | same | PASS |
| HEAD | `2827c1ff1032918aa2541aa0b47bb7f2e5d6cac0` | same | PASS |
| `FINAL_DECISION.md` md5 | `effdfeaf10234678d83b2668c4489552` | same | PASS — `HOLD` intact |
| MPI findings verdict | `REJECT` | `REJECT` | PASS |
| Working tree (default porcelain) | 258 entries | 258 | PASS |
| Working tree (`-uall`) | 463 entries | 463 | PASS |
| Deletions | 0 | 0 | PASS |
| `gula-platform` | `remediate-security-001` @ `f478676b…`, status 0 | untouched | PASS |
| Toolchain | Python 3.12.13, pytest 9.1.1, ruff 0.16.10, mypy 2.4.1 | available | PASS |

Baseline snapshots: `/tmp/opencode/healthcore-accel/{STATUS_BASELINE.txt,HEAD_BASELINE.txt,FINAL_DECISION_MD5_BASELINE.txt}`.

---

## 2. The exact 10 eligible domains (readiness-derived, not name-derived)

| # | Domain | Classification | Eligibility decision |
|---:|---|---|---|
| 1 | Practitioner | `SAFE TO DEVELOP` | Implement |
| 2 | Organization / Facility | `SAFE TO DEVELOP` | Implement |
| 3 | Medical Record (non-identity-linkage components) | `SAFE WITH ISOLATION` | Implement behind port |
| 4 | Encounter | `SAFE WITH ISOLATION` | Implement behind port |
| 5 | Diagnosis | `SAFE WITH ISOLATION` | Implement behind port |
| 6 | Clinical Observations | `SAFE WITH ISOLATION` | Implement behind port |
| 7 | Lab Orders | `SAFE WITH ISOLATION` | Implement behind port |
| 8 | Specimens | `SAFE WITH ISOLATION` | Implement behind port |
| 9 | Lab Results | `SAFE WITH ISOLATION` | Implement behind port, synthetic only |
| 10 | Result Verification | `SAFE WITH ISOLATION` | Implement behind port, synthetic only |

**Explicitly excluded:** Patient Master Record (`BLOCKED BY OWNER DECISION`) and Patient Timeline cross-lab/canonical aggregation (`BLOCKED BY MPI`). A single-synthetic-patient in-memory timeline is permitted as a synthetic aggregation of one fixture patient only and is explicitly NOT the blocked cross-lab timeline.

---

## 3. Actual code inventory (inspected, not inferred)

### 3.1 Existing capability scaffolding — inspected and deliberately NOT modified

`backend/app/capabilities/clinical_foundation/` (29 files / 554 lines) and `backend/app/capabilities/encounter_management/` (39 files / 737 lines) are **machine-generated template scaffolding**:

- Every command/query/event is an **empty dataclass** (`data: dict = {}`, `event_id: str = ""`); routes return fixed stub dicts; policy rule lists are empty; no authorization is enforced.
- Both `capability.json` manifests are **invalid JSON** (trailing comma + single-quoted arrays).
- Both `__init__.py` files use **broken bare imports** (`from clinical_foundation.capability import …`), so importing the package fails.
- `Encounter_management` dataclass **cannot be defined** (`non-default argument 'encounter_id' follows default argument`).
- `SQLAlchemyEncounter_managementRepository` targets a non-ORM dataclass; no table or migration exists.
- **Neither package is wired into the live app**: `factory.py` includes only `fhir_interoperability` and `search_service` capability routers; no capability autodiscovery exists. Their in-tree tests (3 each) are not collected by `backend/pytest.ini` (`testpaths = tests`).
- They contain **zero** MPI/citizen/canonical/patient-id references.

**Decision:** Do not repair or fill these tracked, other-program-owned scaffolds inside this program. Doing so would risk activating deferred modules and would require touching broken tracked files unrelated to the eligible-domain implementations. Reuse only their **vocabulary** (`encounter.created`, `diagnosis.recorded`, `vitals.recorded`, `note.added`) in the new package's shared event enum.

### 3.2 Existing user-modified files — hard exclusion zone

- `backend/app/health_data/mdm/matching.py`, `backend/app/health_data/mdm/service.py` (modified)
- `backend/app/models/__init__.py` (modified), `backend/app/models/communication_experience.py` (untracked)
- 71 entries under `backend/tests/` (modified/untracked)
- 249 pre-existing uncommitted entries elsewhere

**No workstream may modify, delete, or overwrite any of these.**

### 3.3 New isolated implementation surface

A new package `backend/app/health_core/` + test package `backend/tests/health_core/` was created before parallel work began. It is **not imported by `factory.py` or `main.py`** — a static test enforces this. It contains the only permitted identity seam:

- `app.health_core.identity.PatientIdentityPort` — abstract protocol (`register_patient`, `resolve_patient`, `find_patient`).
- `app.health_core.identity.SyntheticPatientRegistry` — the ONLY implementation: in-memory, tenant-scoped, no DB/MPI/network.
- `app.health_core.identity.PatientRef` — opaque `SYN-` reference with no NID/name/phone/DOB.
- `app.health_core.common` — `HealthCoreError` hierarchy (stable `code`/`status_code`/`retryable`), `DomainEvent`, `EventType`/`AggregateType` shared vocabulary, synthetic-id primitives and real-identifier rejection.
- `backend/tests/health_core/test_sandbox_guards.py` — AST-based guard that scans **every** file any workstream adds under `app/health_core` for forbidden MPI/DB/network imports and names. Foundation: 14 tests passing, ruff clean.

---

## 4. Parallel file ownership & conflict map (disjoint by construction)

| Owner | Writable paths (and ONLY these) | Reads (no writes) | Conflict risk |
|---|---|---|---|
| **Lead (coordinator)** | `backend/app/health_core/__init__.py`, `backend/app/health_core/common/**`, `backend/app/health_core/identity/**`, `backend/tests/health_core/__init__.py`, `backend/tests/health_core/conftest.py`, `backend/tests/health_core/test_identity_port.py`, `backend/tests/health_core/test_sandbox_guards.py`, `GOVERNANCE/ACCELERATION/PHASE_ZERO_VERIFICATION.md`, `GOVERNANCE/ACCELERATION/ACCELERATED_EXECUTION_REPORT.md` | all | none — other agents forbidden from these paths |
| **WS-A Clinical** | `backend/app/health_core/clinical/**`, `backend/tests/health_core/test_clinical_*.py`, `GOVERNANCE/ACCELERATION/WS_A_CLINICAL_FOUNDATION_REPORT.md` | `common/**`, `identity/**`, dormant capability dirs (read only) | none |
| **WS-B Laboratory** | `backend/app/health_core/lab/**`, `backend/tests/health_core/test_lab_*.py`, `GOVERNANCE/ACCELERATION/WS_B_LAB_WORKFLOW_REPORT.md` | `common/**`, `identity/**`, existing LIMS models (read only) | none |
| **WS-C Contracts** | `backend/app/health_core/contracts/**`, `backend/tests/health_core/test_contracts_*.py`, `GOVERNANCE/ACCELERATION/WS_C_API_CONTRACTS_REPORT.md` | `common/**`, `identity/**`, `clinical/**`, `lab/**` (read only) | none |
| **WS-D Integration** | `backend/app/health_core/integration/**`, `backend/tests/health_core/test_integration_*.py`, `GOVERNANCE/ACCELERATION/WS_D_APP_INTEGRATION_REPORT.md` | `common/**`, `identity/**`, client app dirs (read only) | none |
| **WS-E Quality** | `GOVERNANCE/ACCELERATION/QUALITY_ARCHITECTURE_REVIEW.md`, `backend/tests/health_core/test_quality_review_static.py` | everything (read only) | none — reviews after implementation lands |

**Enforcement:** every agent prompt states its exact writable set and an explicit forbidden list. `git status` is compared to the saved baseline after integration to prove no unauthorized file was touched.

---

## 5. Shared interface contract (stable for all workstreams)

```python
from app.health_core.common import (
    AggregateType, EventType, DomainEvent, new_event,
    HealthCoreError, UnknownPatientError, TenantMismatchError,
    DuplicateEntityError, InvalidStateTransitionError,
    new_synthetic_id, is_synthetic_id, reject_national_identifier,
)
from app.health_core.identity import PatientIdentityPort, PatientRef, SyntheticPatientRegistry

patient: PatientRef = registry.register_patient(tenant_id="SYN-LAB-0001", label="fixture")
event = new_event(event_type=EventType.ENCOUNTER_CREATED, aggregate_type=AggregateType.ENCOUNTER,
                  aggregate_id="SYN-ENC-…", tenant_id=patient.tenant_id, payload={...})
```

Rules: depend on `PatientIdentityPort` (never on MPI/NHID); emit `EventType` members (never ad-hoc strings); all aggregate ids from `new_synthetic_id`; all errors from the shared hierarchy; no `app.factory`/`app.main` import; no SQLAlchemy/DB import.

---

## 6. Integration gates (applied after parallel work lands)

1. Each workstream's scoped pytest passes with synthetic fixtures.
2. Cross-module conformance tests pass (WS-C contracts over WS-A/WS-B outputs).
3. `test_sandbox_guards.py` passes over the entire expanded package.
4. ruff clean on `backend/app/health_core` + `backend/tests/health_core`.
5. mypy reports no errors attributable to `app.health_core` (pre-existing `app.domain.order_state` errors are baseline and out of scope).
6. Zero changes to forbidden/user-modified paths, protected artifacts, or `factory.py`/`main.py`.
7. No schema/migration/DDL, no commit/push.

**End of Phase Zero verification.**
