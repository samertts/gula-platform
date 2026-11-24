# CROSS-SERVICE INTEGRATION MATRIX

**Repository:** `gula-integration` · **Branch / HEAD:** `integration/gula-unification-v1` @ `2827c1ff1032918aa2541aa0b47bb7f2e5d6cac0` (unchanged) · **Date:** 2026-11-17
**Work item:** W-072 (NAT-I) · **Change control:** CC-010 · **Evidence:** E-064 (new read-only scan) · **Related findings:** F-082, F-083, F-084 (all remain OPEN).

---

## 0. Scope and non-claims

Read-only verification of cross-service coupling and of the three residuals confirmed in the prior stabilization cycle. **No service code, ownership, contract, router or database was changed.** Router presence and import presence are **not** proof of governed integration. This matrix is an evidence record, not a release/safety certification. `FINAL_DECISION.md` stays **HOLD**; D-020/D-021 stay **PENDING**.

---

## 1. Re-verified residuals (E-064 — all still present)

| Finding | Observed on disk (current tree) | Impact | Status |
|---|---|---|---|
| **F-083** pharmacy → EHR direct write | `app/pharmacy/services.py:14` imports `MedicationDispense` from `app.ehr.models.medication`; `:962` constructs it; `:992` `self.db.add(dispense)` against EHR-owned `ehr_medication_dispenses`. Contract §4 assigns `ehr_*` to EHR under R-DB-1 single-writer / "never a direct write"; contract §6 row 04 records the missing pharmacy dispense event. | Cross-service write bypasses the EHR service/event boundary; ownership + tenant/facility authz + audit + idempotency of the write are not governed by a documented contract. | **OPEN — ownership/event-boundary decision required (ADR-D/ADR-B). No change here.** |
| **F-084** bootstrap → LIMS direct write | `app/core/bootstrap/departments.py:33` imports `app.lims.models.Department`; `:50-52` queries it; `:56-65` creates and `:65` `db.add`s it. | May be an authorized provisioning path. Must be classified as governed bootstrap or cross-service write before any remediation. | **OPEN — classification pending. No defect asserted, no change here.** |
| **F-082** kernel runtime extension registration has no call site | `app/kernel/runtime_integration.py:14` `init_runtime_extensions()` and `:35` `register_runtime_routes()` are defined; the **only** occurrences under `backend/app/**` are their definitions. `runtime_routes.py` reads `rules_runtime`/`policy_runtime` components that this initializer would register. | Possible unpopulated runtime surfaces; source observation only, **not** a runtime observation; not a duplicate of F-066 (missing tests). | **OPEN — architecture review; no code change authorized.** |

---

## 2. Bounded cross-service import scan (E-064)

A fresh AST scan over `backend/app/**/*.py` with a bounded 20-service set found **48 import sites across 19 distinct source→target pairs**. All `models`-segment and cross-service imports are counted; **only the two writes above were confirmed as direct writes**; the other pairs are **NOT VERIFIED as writes** (they include reads, FHIR mapping, and pure helpers) and are **not** asserted as defects.

| Source → Target pairs (19) |
|---|
| biomedical → national · blood_bank → national · care_continuum → national · care_continuum → public_health · critical_care → national · ehr → identity · ems → national · identity → national · national → ehr · national → hospital · national → identity · national → insurance · national → lims · nursing → ehr · nursing → radiology · pharmacy → billing · pharmacy → ehr · public_health → national · radiology → identity |

**Method note (honest, non-comparable denominators):** the prior Phase I scan (`STABILIZATION_PHASE_H_I_ASSESSMENT.md` §2) reported 70 import sites / 25 pairs using a different service taxonomy. E-064 uses a fixed 20-package set and AST `Import`/`ImportFrom` resolution; the two figures measure different corpora and are **never summed, substituted or treated as a regression**. Both agree that cross-service coupling is non-zero and that the two confirmed direct writes are the actionable cases.

---

## 3. Governance requirements per cross-service write (assessment template)

For **each** cross-service write, the following must be documented before the integration is considered governed. Status below is the honest current reading for the two confirmed writes; no new contract was authored here.

| Requirement | F-083 (pharmacy→EHR) | F-084 (bootstrap→LIMS) |
|---|---|---|
| Authoritative data owner | EHR (`ehr_*`, R-DB-1) — **documented** | LIMS (`lims_*`) — documented |
| Documented service contract | **Missing** (dispense event absent, contract §6 row 04) | **Classification pending** |
| Authorization check | Not verified at the write boundary | Bootstrap context — not verified |
| Tenant / facility check | Not verified at the write boundary | Not verified |
| Transaction strategy | Local `db.add` — no explicit cross-service strategy | Local `db.add` — provisioning |
| Idempotency | Not verified | Not verified |
| Audit | Not verified for this write | Not verified for this write |
| Failure recovery | Not verified | Not verified |
| Version compatibility | Unversioned (contracts §3.7 DRAFT/absent) | Unversioned |

**Decision required (not taken here):** move the pharmacy dispense write behind an EHR service boundary or versioned event (ADR-D/ADR-B scope), and classify the bootstrap department creation as governed provisioning or a cross-service write. No broad data-ownership or contract change is made automatically, per §9 of the program directive.

---

## 4. Event architecture and data-flow reading (carried, not re-certified)

Per `NATIONAL_SERVICE_CONTRACTS.md` §3.9/§3.10 and `STABILIZATION_PHASE_H_I_ASSESSMENT.md`: event naming uses four incompatible conventions (DRAFT), versioning is effectively absent, tenancy is UNSTABLE, and 7 services have no immutable audit writes. The event/outbox primitives exist (`ENG-A05`, ENG-B10) but are **unit/integration-scoped**, not runtime-observed. Cross-service consistency, replay safety, ordering and dead-letter handling therefore remain **NOT VERIFIED** at national integration level. No additional event bus was created; the existing event/outbox family was not modified.

---

## 5. Verdict and rollback

**Verdict: PARTIAL (assessment), integration NOT VERIFIED.** Two confirmed direct writes and one wiring gap are re-verified and remain OPEN; 19 cross-service import pairs are indexed with an honest "not verified as writes" boundary. No ungoverned write was remediated automatically because each requires an ownership/contract decision (ADR-D/ADR-B) outside this change control. `FINAL_DECISION.md` stays **HOLD**.

**Rollback (CC-010):** delete this document and the E-064 log. No application, contract, event or DB object was created or changed by this work item.
