# Health Core Readiness Assessment

**Report ID:** HC-RA-001
**Date:** 2026-11-18
**Repository:** `gula-integration` · branch `integration/gula-unification-v1` · HEAD `2827c1ff1032918aa2541aa0b47bb7f2e5d6cac0`
**Trigger:** Phase 5 gate — decide whether it is safe to start Health Core development, without starting it.
**Authoritative inputs:** `GOVERNANCE/FINAL_DECISION.md` (md5 `effdfeaf10234678d83b2668c4489552`, `HOLD`), `MPI_FINAL_INDEPENDENT_AUDIT.md` (verdict `REJECT`).
**Data:** synthetic only; no real patient data; no secrets.

---

## 1. Scope and method

This assessment classifies the 12 named Health Core domains into one of four states: `SAFE TO DEVELOP`, `SAFE WITH ISOLATION`, `BLOCKED BY MPI`, `BLOCKED BY OWNER DECISION`. It is based on a **read-only inspection of the actual repository**, not on assumptions:

| Evidence inspected | Finding |
|---|---|
| `backend/app/models/patient.py` | Real `Patient` is **lab-scoped** (`lab_id` FK, `health_id`, `national_id_hash`). LIMS patient identity ≠ canonical national identity. |
| `backend/app/models/test_result.py` | Test results carry `citizen_id` with a **direct FK to MPI `citizens.id`** (`ForeignKey("citizens.id", ondelete="RESTRICT")`, index `ix_test_results_citizen_lab`). Results/verification are directly coupled to canonical identity. |
| `backend/app/models/lab_order.py`, `lab_result.py` | Orders reference lab-scoped `patient_id` + `lab_id`; results are lab-scoped. No direct MPI FK on the order path. |
| `backend/app/models/organization.py` | `Organization` and `Facility` are **independent of MPI**. |
| `backend/app/capabilities/clinical_foundation/`, `encounter_management/` | Dormant scaffolding: commands/queries/events are mostly **empty dataclasses** (e.g. `get_patient_timeline.py` is a 12-line filter DTO); **not wired** into `factory.py`/`main.py`. Greenfield, not live. |
| `backend/app/health_data/canonical/models.py` | FHIR-like canonical **dataclasses** (`PatientCanonical`, `EncounterCanonical`, `ObservationCanonical`) with `patient_id` / `patient_canonical_id` / `national_id_hash` fields — useful contracts, not a live patient-identity service. |
| `GOVERNANCE/FINAL_DECISION.md` | `HOLD — do not release to production`; security not certified; `MIG-EXISTING` not met (ownership ADR-B, rollback decision, 51-row snapshot, **NR-011** blocks `alembic check`). |
| `MPI_FINAL_INDEPENDENT_AUDIT.md` | MPI verdict `REJECT`; AUD-02 (HIGH) PARTIAL, AUD-07/AUD-16 owner-blocked. |

**Interpretation:** "Health Core" is a forward-looking program label (no existing `Health Core` artifact in the repo). The relevant question is which domains can be *developed now* under strict isolation versus which depend on an MPI identity path that is currently unacceptable. **Development permission is not release permission:** `HOLD` remains, so no domain may be activated in production regardless of its classification.

---

## 2. Classification of the 12 domains

| # | Domain | Classification | Primary reason | Secondary blockers |
|---:|---|---|---|---|
| 1 | **Patient Master Record** | `BLOCKED BY OWNER DECISION` | Its core is canonical identity/link storage; MP-001 (DB `UNIQUE` on links), ODR-002 (payload-change semantics, D-MPI-5) and ODR-004 (canonical hardening, D-MPI-6) are **not decided/executed**. | MPI `REJECT` (REJECT_MATCH/CREATE_NEW identity path, AUD-02 PARTIAL); ODR-001 taxonomy. |
| 2 | **Medical Record** | `SAFE WITH ISOLATION` | Longitudinal record can be keyed to a synthetic lab-scoped patient via an interface; no real canonical link needed. | None at development time; production activation blocked by `HOLD`. |
| 3 | **Encounter** | `SAFE WITH ISOLATION` | Existing capability is dormant scaffolding (not routed, empty DTOs); develop against a patient-reference interface with synthetic fixtures. | Needs patient-reference contract before integration. |
| 4 | **Practitioner** | `SAFE TO DEVELOP` | No MPI dependency; practitioner identity comes from `LabUser`/professional registry. No patient data involved. | Production activation blocked by `HOLD`. |
| 5 | **Organization / Facility** | `SAFE TO DEVELOP` | `Organization`/`Facility` models are MPI-independent reference data. | Production activation blocked by `HOLD`. |
| 6 | **Diagnosis** | `SAFE WITH ISOLATION` | Clinical coding (ICD) can be developed against an encounter/patient interface with synthetic fixtures. | Terminology source selection; integration needs encounter contract. |
| 7 | **Clinical Observations** | `SAFE WITH ISOLATION` | `ObservationCanonical` dataclass already provides a contract; synthetic patients only. | Terminology/unit normalization owner choice. |
| 8 | **Lab Orders** | `SAFE WITH ISOLATION` | `LabOrder` uses lab-scoped `patient_id`; no direct MPI FK. Develop with synthetic lab patients. | Integration to canonical identity deferred until MPI accepted. |
| 9 | **Specimens** | `SAFE WITH ISOLATION` | Specimen/barcode workflow (see `sample_tracking/`) can be keyed to synthetic order/sample IDs. | Link to real patient/order chain deferred. |
| 10 | **Lab Results** | `SAFE WITH ISOLATION` | `TestResult` has a **direct MPI `citizen_id` FK** — develop only with synthetic citizen fixtures and a patient-identity interface; never a real link. | Real result writes blocked until MPI accepted + AUD-02 closed. |
| 11 | **Result Verification** | `SAFE WITH ISOLATION` | Verification provenance uses reviewer identity (available without MPI); the result being verified must be synthetic. | Audit taxonomy ODR-001 for ledger event types; real links blocked. |
| 12 | **Patient Timeline** | `BLOCKED BY MPI` | Its purpose is cross-service/cross-lab aggregation of **one** patient's record — correctness requires canonical identity. With MPI `REJECT`, aggregation can group different people (wrong-patient risk). AUD-07 also means corrected identities cannot be re-resolved. | MP-001, ODR-002; no real-data timeline until MPI re-audited to ACCEPT. |

**Category summary:** `SAFE TO DEVELOP` 2 · `SAFE WITH ISOLATION` 8 · `BLOCKED BY MPI` 1 · `BLOCKED BY OWNER DECISION` 1.

---

## 3. Mandatory guardrails for every allowed domain

Every `SAFE TO DEVELOP` / `SAFE WITH ISOLATION` domain **must** comply with all of the following (from the mandate); violating any one converts it to blocked:

1. **Synthetic fixtures only** — no real patient data, no real NID, no production database rows.
2. **No real patient links** — do not create `PatientLink`/`CitizenLink`/MPI claims against real people.
3. **No NHID or MPI bypass** — do not invent a canonicalization path, do not call MPI write endpoints with synthetic identities in a way that would create durable real-looking records; use explicit interface stubs.
4. **Clear interfaces and contracts** — depend on an abstract patient/identity provider (`PatientIdentityPort`) whose only implementation during this phase is an in-memory synthetic adapter; keep a single seam to swap in the real MPI adapter **only after** MPI is accepted.
5. **No migrations or DDL** — use existing tables only where they are synthetic-safe, or in-memory/dummy repositories; do not add schema.
6. **No production path activation** — do not wire new routes into the live factory/router, do not enable features, do not seed production-like data.
7. **No clinical-readiness claim** — mark all output as development/synthetic; never label a module clinically usable or releasable.
8. **No scope expansion** — work stays inside the domain's own module; do not "fix" MPI, NHID, or unrelated Identity defects (the NR-011 baseline failure is out of scope and documented elsewhere).

---

## 4. What this means for the transition decision

**Answer to "is it safe to start Health Core development?": PARTIALLY — yes only for the 10 non-MPI-dependent domains, under the guardrails in §3; no for Patient Master Record, Patient Timeline, and no production activation for any domain.**

- The two `SAFE TO DEVELOP` domains (Practitioner; Organization/Facility) can begin immediately with synthetic reference data.
- The eight `SAFE WITH ISOLATION` domains can be designed and implemented behind interfaces with synthetic fixtures, but must not create real patient links, must not touch NHID/MPI, and must not be activated.
- The three blocked domains require, in order: (a) owner decisions MP-001 + ODR-001…004, (b) execution and independent re-verification of those decisions, (c) MPI re-audit from `REJECT` to at least `CONDITIONAL ACCEPT`, and (d) lifting of `FINAL_DECISION` `HOLD` by the Program Director. None of these is performed in this phase.

**Fastest safe first patient journey:** a synthetic-only vertical slice (synthetic Practitioner + Facility → synthetic Encounter → synthetic Diagnosis/Observation → synthetic Lab Order → synthetic Specimen → synthetic Lab Result → synthetic Verification → synthetic Timeline within a single synthetic patient), with **no canonical identity creation and no MPI writes**. It demonstrates workflow shape, not clinical validity, and cannot be promoted until all gates above are cleared. See Phase 6 plan in `MPI_AND_HEALTH_CORE_FINAL_STATUS.md`.

---

## 5. Integrity attestations

- `FINAL_DECISION.md` md5 `effdfeaf10234678d83b2668c4489552` — unchanged; `HOLD` intact.
- MPI verdict `REJECT` — unchanged.
- `/home/samertts/workspace/projects/gula-platform` — untouched.
- No commit/push/merge/rebase/PR/deploy; no `git reset`/`clean`/`add .`/`add -A`; no migration/DDL/schema change; no NHID canonicalization change; no unmerge.
- No Health Core implementation was started; this is assessment and classification only.
- Synthetic data only; no real patient data; no secrets.

**End of report.**
