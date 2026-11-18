# Workstream Charters (WS-01 … WS-07)

**Document:** 03 · **Program:** National Integration · **Date:** 2026-11-18
**Status:** `IMPLEMENTED` (charters approved for execution within this program's authority).

---

Authorization boundary for every charter below: synthetic data only; no route activation in `factory.py`/`main.py`; no migration against an operational DB; no test deletion or weakening; no production claim. File ownership is **disjoint** — an agent may not edit a file owned by another workstream without an explicit hand-off record in `status_registry.json`.

## WS-01 — Identity & MPI

- **Owns:** `backend/app/identity/**`, `backend/app/services/mpi/**`, `backend/app/services/identity_matching.py`, `backend/app/health_core/identity/**`, `backend/tests/**/test_*mpi*`, `test_*identity*`.
- **Goal:** close synthetically-safe MPI defects; prepare MP-001 / ODR-002 / ODR-003 packages; preserve AUD-01…16 evidence.
- **Acceptance:** no false merge, no lost reference, no raw NID at rest, adversarial review; `REJECT` status unchanged until owner signs superseding package.
- **Allowed now:** synthetic regression tests, doc packages, no DB UNIQUE change.
- **Status:** `BLOCKED` for owner decisions; `TESTED` for synthetic MPI suite (127 passed, prior cycle).

## WS-02 — Security & audit

- **Owns:** `backend/app/security/**`, `backend/app/audit/**`, `backend/app/health_core/authorization/**`, `backend/tests/**/test_*authorization*`, `test_*audit*`.
- **Goal:** preserve S-01…S-13 remediations; fail-closed authorization; audit actor attribution (ADR-D package).
- **Acceptance:** no unguarded non-public endpoint; audit hash-chain intact; no assertion weakened.
- **Allowed now:** synthetic tests, ADR-D package, no D-020 sign-off claim.
- **Status:** `TESTED` (68 authorization + 26 reliability-audit tests); `BLOCKED` for D-020 certification.

## WS-03 — FHIR R4 interoperability

- **Owns:** `backend/app/health_core/fhir/**`, `backend/app/capabilities/fhir_interoperability/**`, `backend/app/national/fhir/**`, `backend/app/fhir/**`, related `backend/tests/**/test_*fhir*`.
- **Goal:** OperationOutcome adapter correctness, round-trip validation, no identifier leakage in diagnostics (I-2).
- **Acceptance:** local adapter tests pass; HTTP endpoint claim stays `NOT IMPLEMENTED` (no sandbox endpoint).
- **Status:** `TESTED` (local adapter only; HTTP endpoint `NOT IMPLEMENTED`).

## WS-04 — Terminology

- **Owns:** `backend/app/health_core/terminology/**`, `backend/app/national/reference/**`, related tests.
- **Goal:** ICD-10/LOINC/UCUM validation, provenance, honest treatment of offline licensed datasets.
- **Acceptance:** no invented SNOMED CT license; LOINC check-digit validation stays `NOT IMPLEMENTED` until an authoritative release is available (no offline result is claimed).
- **Status:** `TESTED` (15 provenance + 23 validator tests); licensed datasets `BLOCKED`.

## WS-05 — Reliability & offline-first

- **Owns:** `backend/app/health_core/reliability/**`, offline sync engine tests, WAL/audit/retry modules in Health Core.
- **Goal:** preserve F-02/F-03/F-05 fixes; honest in-memory boundary; conflict quarantine.
- **Acceptance:** no false durability claim; no CRDT claim; WAL anchors tested.
- **Status:** `TESTED` (26 reliability tests); durable/keyed external anchor `BLOCKED` (persistence owner).

## WS-06 — Client integration

- **Owns:** `backend/app/health_core/client_integration/**`, client manifest/contract tests, frontend contract documents (read-only on `frontend-v3/` runtime code unless separately authorized).
- **Goal:** fail-closed manifest validation (`NO_OBSERVATION_FOR_PLATFORM`), Arabic RTL/a11y guards.
- **Acceptance:** all real client platforms remain `BLOCKED/NOT IMPLEMENTED`; no demo counted as E2E.
- **Status:** `TESTED` (30 client tests); platform adapters `BLOCKED` (Xcode absent, Expo layer not authorized).

## WS-07 — National domains & journeys

- **Owns:** `backend/app/domain_platform/**`, `backend/app/national/**` (read-only for migrations), `GOVERNANCE/NATIONAL_SERVICE_*` (read-only source), journey tests.
- **Goal:** 11-domain isolation preserved; national inventory/contracts carried forward; W1–W3 waves sequenced per `NATIONAL_INTEGRATION_ROADMAP.md`.
- **Acceptance:** no dormant router activation; ADR-A/C decisions recorded before migration work; no DB change.
- **Status:** `INTEGRATED` (11/11 domain certification, isolation PASS — prior cycle); national waves `BLOCKED` pending ADR-A/C/D.

## Conflict-resolution rule

If a required change spans two workstreams (e.g. FHIR terminology validation across WS-03/WS-04), the lead performs it with both owners recorded, and the change requires two independent reviewers. Such a change is marked `INTEGRATED` only after both owners sign in the registry.
