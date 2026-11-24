# A05 — Interoperability Audit

**Program:** PROGRAM-GULA-PARALLEL-001 (GULA National Healthcare Platform, Iraq)  
**Agent:** A05 — Clinical Data & Interoperability Auditor  
**Wave:** A (Discovery / AUDIT ONLY)  
**Date:** 2026-11-19  
**Status:** COMPLETE — read-only; no source, config, git, service, database, migration or test-execution changes were made. Companion to `CLINICAL_WORKFLOW_AUDIT.md`.

---

## 0. Governance and constraints observed

| Rule | Compliance evidence |
|---|---|
| Read-only on all source/config | File reads, path globs, content searches and read-only `git status --porcelain -- <paths>` only. |
| Write only to owned paths | Writes limited to the two A05-owned reports under `docs/parallel-program/clinical/`. |
| No git state changes | No add/stage/commit/checkout/stash/merge/worktree/reset/clean operation. |
| No tests/migrations/DB execution | No pytest, Alembic, app startup or DB query was executed. |
| 378 protected paths | Untracked Health Core and MPI reliability files are cited as evidence only. |
| Evidence-based | Route inventories and exact `path:line` citations; speculative claims are absent or labelled. |

**Constitution check:** no commercial interoperability product is proposed. Findings and safe directions reuse the existing FastAPI/SQLAlchemy/PostgreSQL stack and existing open FHIR libraries already in the repository. No vendor-specific protocol coupling is introduced by this report.

---

## 1. Scope, inventory and method

### 1.1 Files reviewed (included in the ≈70-file A05 evidence set)

**Registered FHIR/interoperability surfaces:**
- `backend/app/routes/ehr_fhir.py` (registered at `backend/app/factory.py:538`, `:570`, `:579`)
- `backend/app/fhir/{_capabilities.py,_reference.py,_validation_report.py,terminology.py}`
- `backend/app/capabilities/fhir_interoperability/routes.py` (registered at `backend/app/factory.py:656-658`; explicitly simulation-oriented)
- `backend/app/integration/fhir_r4_exchange.py`, `backend/app/health_core/fhir/**` (synthetic adapter; not production-wired)

**MPI/identity interoperability:**
- `backend/app/services/mpi/{matcher.py,models.py,blocking.py,resolver.py,canonical_service.py,reliability.py,api.py,schemas.py}`
- `backend/app/services/patient_service.py`, `backend/app/routes/canonical_patient.py`

**Tests read (not executed):**
- `backend/tests/test_fhir_comprehensive.py`, `backend/tests/test_fhir_r4_exchange.py`, `backend/tests/test_fhir_interoperability.py`, `backend/tests/test_fhir_interoperability_hardening.py`, `backend/tests/unit/test_fhir_http_endpoints.py`
- `backend/tests/health_core/test_fhir_roundtrip.py`, `backend/tests/health_core/test_fhir_validation.py`
- `backend/tests/test_mpi_reliability.py`, `backend/tests/test_mpi_hash_chain_integrity.py`, `backend/tests/test_mpi_audit0416_integrity.py`

### 1.2 Verified runtime boundaries

| Surface | Evidence | Audit treatment |
|---|---|---|
| `ehr_fhir` router | `backend/app/routes/ehr_fhir.py:44-48` (`prefix="/fhir"`); registered via `backend/app/factory.py:538`, `:570`, `:579`. | Production discovery/write surface. A05-006 and A05-007 apply. |
| `fhir_interoperability` router | `backend/app/factory.py:656-658`; capability metadata at `backend/app/capabilities/fhir_interoperability/routes.py:47-49`; HL7 conversion payload includes `"simulationOnly": True` at `:83`. | Simulation/conversion surface, not evidence of a full production FHIR server. |
| `fhir_http` router | `backend/tests/unit/test_fhir_http_endpoints.py:619-623` asserts the string `fhir_http` is absent from `app/factory.py` and `app/main.py`; `backend/app/factory.py` contains no registration. | Deliberately unregistered. Its rich tests are **not** counted as production implementation evidence (§3). |
| Health Core FHIR adapter | `backend/tests/health_core/test_quality_review_static.py:118-130` asserts no Health Core import in startup files. | Synthetic contract only; not reported as production-active. |
| MPI advisory locks | `backend/app/services/mpi/reliability.py:72-77` returns `False` for non-PostgreSQL dialects. | Implementation present; in-checkout concurrency proof absent (A05-008). |

### 1.3 Protection status

- **USER WORK / PROTECTED:** `backend/app/services/mpi/reliability.py` (untracked), `backend/app/health_core/**` (untracked). Cited only.
- Clean in the queried set: `backend/app/routes/ehr_fhir.py`, `backend/app/fhir/_capabilities.py`, `backend/app/fhir/_reference.py`, `backend/tests/test_fhir_comprehensive.py`.
- A05 made no changes to any source, test or config file.

### 1.4 Executive summary

The registered FHIR surface advertises more than it implements and does not honour FHIR transaction atomicity. The CapabilityStatement claims R4, SMART-on-FHIR and 18 implemented resources, but there are no `ehr_fhir` read/search routes for five claimed resource types and internal status tables disagree about `Procedure`, `Bundle` and `Provenance` (A05-006, P1). Separately, `POST /fhir` accepts `type: "transaction"` but processes entries in a loop, swallows per-entry `HTTPException`s and performs a single `commit()`; there is no rollback or all-or-nothing behaviour, and existing tests cover only empty/basic batches (A05-007, P0). MPI has PostgreSQL advisory-lock primitives, but SQLite fixtures are explicit no-ops and the in-repository tests do not prove concurrency (A05-008, P2).

**Counts (this report):** 3 findings — **P0: 1 · P1: 1 · P2: 1**. Combined with the clinical report: **8 findings — P0: 3 · P1: 3 · P2: 2**.

---

## 2. Findings

---

### A05-006 — P1 — FHIR CapabilityStatement overclaims resources, interactions and security conformance

- **Evidence:**
  - `backend/app/fhir/_capabilities.py:5-16` — active CapabilityStatement, software version `2.1.0`, `fhirVersion: "4.0.1"`.
  - `backend/app/fhir/_capabilities.py:23-36` — advertises `SMART-on-FHIR`, OAuth2/JWT bearer compatibility and tenant isolation via `lab_id` claims.
  - `backend/app/fhir/_capabilities.py:148-182` — advertises `DiagnosticReport`, `Specimen`, `ServiceRequest`, `Organization`, `Practitioner` and `Provenance` read/search interactions.
  - `backend/app/fhir/_capabilities.py:195-214` — `IMPLEMENTED_RESOURCES` lists 18 types, including the five above.
  - `backend/app/routes/ehr_fhir.py:112-122` — the registered `/fhir/metadata` route returns this statement directly.
  - Exhaustive `@router.` inventory of `backend/app/routes/ehr_fhir.py` shows read/search routes for `Patient` (`:128`), `Encounter` (`:178`), `Condition` (`:243`, `:319`), `Observation` (`:357`, `:419`), `Provenance` (`:502`), `MedicationRequest` (`:590`, `:656`), `MedicationStatement` (`:686`), `CarePlan` (`:745`), `Procedure` (`:804`, `:830`), `AllergyIntolerance` (`:875`, `:928`), `Immunization` (`:958`, `:1024`), `DocumentReference` (`:1054`, `:1102`), `Composition` (`:1135`, `:1197`) and `Bundle` (`:1243`). **No route exists for `DiagnosticReport`, `Specimen`, `ServiceRequest`, `Organization` or `Practitioner` read/search.**
  - `backend/app/fhir/_capabilities.py:233-249` — the endpoint summary also omits those five resources while claiming 18 implemented resources.
  - `backend/app/fhir/_reference.py:20-25` — internal status table marks `Procedure` and `Bundle` as `stub` and `Provenance` as `planned`, contradicting the CapabilityStatement and the actual routes.
  - Registered surface: `backend/app/factory.py:538`, `:570`, `:579` includes `ehr_fhir`; this is not an unregistered demo.
- **Affected components:** `/fhir/metadata`, FHIR clients that drive discovery from CapabilityStatement, national EHR/LAB integration contracts, conformance documentation.
- **Root cause:** Capability metadata is hand-maintained and not generated or gated against the actual route map. Two FHIR metadata tables disagree, and no test asserts advertised-resource/route parity.
- **Safe-fix possible?** Technically yes (generate or gate the resource list from a single verified map, downgrade claims to actual interactions, reconcile `_reference.py`), but **not in Wave A**: it changes a public interoperability contract.
- **Approval required?** **Yes.** Interoperability/contract owner + A07; A09 must add a route-parity regression test. SMART-on-FHIR wording must be removed or independently proven before external publication.
- **SCOPE_REQUEST:** SR-A05-06.

---

### A05-007 — P0 — FHIR `transaction` bundles are not atomic; partial writes are committed

- **Evidence:**
  - `backend/app/routes/ehr_fhir.py:1437-1445` — `POST /fhir` accepts both `batch` and `transaction`.
  - `backend/app/routes/ehr_fhir.py:1446-1497` — entries are processed one-by-one in a loop; each entry may create/update/delete clinical resources and returns a per-entry status code.
  - `backend/app/routes/ehr_fhir.py:1498-1499` — `HTTPException` is caught per entry and converted into a response status; processing continues.
  - `backend/app/routes/ehr_fhir.py:1505-1507` — for `transaction`, the handler calls `db.commit()` once after the loop. There is no `rollback()`, savepoint, pre-validation pass or all-or-nothing gate anywhere in the handler.
  - `backend/tests/test_fhir_comprehensive.py:115-133` — the only batch/transaction tests cover an empty `batch` response and an unsupported bundle type; there is no test that a failing transaction entry rolls back earlier writes.
- **Affected components:** `POST /fhir` transaction bundles, all create/update/delete FHIR entry points used inside a bundle (`backend/app/routes/ehr_fhir.py:1366-1431`), clinical record integrity, tenant-scoped writes.
- **Root cause:** Batch and transaction semantics were conflated. The implementation offers per-entry isolation for both and commits all successful entries for `transaction`, which violates FHIR transaction atomicity.
- **Safe-fix possible?** **No in Wave A.** A correct fix requires an owner-approved contract (pre-validation, single transaction boundary, rollback on any failure, defined response Bundle) plus regression tests. It touches API behaviour and DB transaction control.
- **Approval required?** **Yes.** Interoperability owner + A07 (transactions/API contract) + A09 (rollback tests). P0 halt: no external partner should be told that `transaction` is atomic.
- **SCOPE_REQUEST:** SR-A05-07.

---

### A05-008 — P2 — MPI PostgreSQL concurrency controls are implemented but not proven inside the checkout

- **Evidence:**
  - `backend/app/services/mpi/reliability.py:3-12` — the module states its controls are PostgreSQL-native and that SQLite lock acquisition is a documented no-op; the “real concurrency proof” is described as out-of-repository.
  - `backend/app/services/mpi/reliability.py:72-77` — `_acquire_xact_lock()` returns `False` unless `bind.dialect.name == "postgresql"`.
  - `backend/app/services/mpi/canonical_service.py:191`, `:237` and `backend/app/services/mpi/resolver.py:520`, `:728`, `:817`, `:900` call the advisory-lock helpers.
  - `backend/tests/test_mpi_reliability.py:44-47` — asserts the SQLite no-op (`acquire_audit_chain_lock(db) is False`).
  - `backend/tests/test_mpi_hash_chain_integrity.py:9-11` — explicitly says all tests run on SQLite, emit no `FOR UPDATE`, and make **no PostgreSQL concurrency claim**.
  - `backend/tests/test_mpi_audit0416_integrity.py:112-122` — a single-process test cannot force the concurrent-NID interleaving; it uses a structural source pin and refers to an out-of-repository PostgreSQL harness.
  - Repository-wide search for `pg_advisory_xact_lock` found the production helper and test/source assertions only; no executable PostgreSQL MPI concurrency harness exists in this checkout.
- **Affected components:** MPI audit-chain tail lock, canonical-link check/insert serialization, NID reconciliation, provenance/concurrency evidence.
- **Root cause:** Production correctness depends on PostgreSQL transaction-scoped advisory locks, while the available test fixture deliberately cannot exercise them. Structural pins prove code presence, not runtime serialization.
- **Safe-fix possible?** **No in Wave A.** Adding or running a real PostgreSQL harness requires an approved disposable test environment and owner sign-off; no DB execution is authorized in this wave.
- **Approval required?** **Yes.** A07 (DB behaviour), A09 (harness), A04/A05 (identity/provenance evidence), orchestrator. Until then, describe MPI concurrency as **PG-dependent and not proven in-checkout**, not as “concurrency safe”.
- **SCOPE_REQUEST:** SR-A05-08.

---

## 3. Boundaries and verified non-findings

1. **`fhir_http` is not production.** `backend/tests/unit/test_fhir_http_endpoints.py:619-623` asserts no `fhir_http` reference in `app/factory.py` or `app/main.py`; `backend/app/factory.py` registers `ehr_fhir` (`:570`, `:579`) and `fhir_interoperability` (`:656-658`) instead. Its ETag/versioning tests were reviewed but are **not** counted as evidence for the registered FHIR API.
2. **Health Core FHIR adapter is synthetic.** Static startup guards (`backend/tests/health_core/test_quality_review_static.py:118-130`) assert `factory.py`/`main.py` do not import it. Its nine resource types and round-trip tests do not change the CapabilityStatement findings.
3. **`fhir_interoperability` is explicitly simulation-oriented.** `backend/app/capabilities/fhir_interoperability/routes.py:83` returns `simulationOnly: True`; `backend/tests/test_fhir_interoperability.py:94-101` pins this. It should not be presented as a second conformant production FHIR server.
4. **No vendor lock-in introduced.** No new broker, EHR vendor SDK, cloud FHIR service or commercial terminology service is recommended.
5. **No DB/contract change made.** The transaction and metadata findings are report-only; no route, model, migration or test file was edited.

---

## 4. SCOPE_REQUESTs

| ID | Request | Owner / approval needed |
|---|---|---|
| SR-A05-06 | Make `/fhir/metadata` truthful: generate or gate claims from the registered route map, reconcile `_reference.py`, and prove or remove SMART-on-FHIR wording. | Interoperability owner; A07; A09. |
| SR-A05-07 | Define and implement atomic `transaction` semantics (pre-validation, rollback on any failed entry, response Bundle contract) before external use. | Interoperability owner; A07; A09. P0 halt. |
| SR-A05-08 | Supply an approved disposable PostgreSQL MPI concurrency harness; preserve current honest “not proven in-checkout” wording until it exists. | A07; A09; A04/A05; orchestrator. |

---

## 5. Orchestrator handoff

- A05-007 is the interoperability P0 and should be consolidated into the master register with a halt on external `transaction` claims.
- A05-006 is a public-contract accuracy issue; it should not be silently “fixed” by deleting claims without owner approval because partners may already depend on the advertised list.
- A05-008 is an evidence-boundary correction, not evidence that MPI is unsafe.
- A05 remains reviewer for Wave C; no clinical, FHIR, DB or API behaviour may be changed by this agent in Wave A.
