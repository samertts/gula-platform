# STABILIZATION PHASE H & I — READ-ONLY ASSESSMENT

**Repository:** `/home/samertts/workspace/projects/gula-integration` · **Branch:** `integration/gula-unification-v1` @ `2827c1ff1032918aa2541aa0b47bb7f2e5d6cac0` (unchanged)
**Date:** 2026-11-17 · **Work items:** W-056 (Phase H, REMED-H) / W-057 (Phase I, REMED-I)
**Scope:** **READ-ONLY.** No code, config, DB, test, fixture, migration or deployment change. No test command, SQL/DDL, Alembic, git write operation, or access to `gula-platform` / operational DB. No real patient data. Only this file was added.
**Verdict:** `GOVERNANCE/FINAL_DECISION.md` remains **HOLD** — md5 `effdfeaf10234678d83b2668c4489552` re-verified unchanged. **D-020 and D-021 remain PENDING.** No approval, certification or release status is inferred.
**Evidence basis:** governance documents listed in §2 plus bounded read-only verification (`ls`/`wc`/`grep`/`ast` scan) of source paths and router registration. Evidence types below are those **cited by the existing documents**; no test was re-executed by this assessment. **No new E-ID or F-ID is created**; proposed items are labelled `PROPOSED-F:` for the parent registry owner.

---

## 1. Phase H — engine integration audit + National Capability Registry feasibility

### 1.1 Inventory reconciliation (39 engines)

Source: `AUTONOMOUS_ENGINES_INVENTORY.md` §3–§6, `AUTONOMOUS_ENGINES_VERIFICATION.md` §3/§7, `AUTONOMOUS_ENGINES_FINDINGS.md` §2, and GECS `FINDINGS_REGISTRY.md` F-066…F-072 (read).

| Status | Count | Reconciliation result |
|---|---:|---|
| INTEGRATION_VERIFIED | 9 | Confirmed from per-engine rows (B01, B02, B04, B05, B06, B10, C07, D02, D05) |
| UNIT_VERIFIED | 15 | Confirmed (A02, A03, A04, A05, A09, A11, B03, B12, C02, C03, C04, C06, D01, D03, D04) |
| PARTIAL_VERIFIED | 2 | Confirmed (A01, C05) |
| SOURCE_PRESENT | 11 | Confirmed (A06, A07, A08, A10, B07, B08, B11, C01, C08, C09, D06) |
| DORMANT | 1 | ENG-A12 generated scaffold (F-071) |
| UNVERIFIABLE | 1 | ENG-B09 national CDS (F-068) |
| RUNTIME_VERIFIED | 0 | Explicitly not claimed |
| PRODUCTION_VERIFIED | 0 | Explicitly not claimed |
| **Total** | **39** | A 12 · B 12 · C 9 · D 6; 9+15+2+11+1+1 = 39 |

**Discrepancy statement:** no discrepancy found between the reconciled totals in the inventory (§6) and the per-engine status mapping in the verification report (§3) — both are 9/15/2/11/1/1 with 0 runtime/production. The inventory's §6 note honestly records an older, superseded 8/16 summary line; this assessment does not revive it.

**Currency caveat (honest, not a re-score):** the working tree contains concurrent uncommitted P0 remediation (GECS `MASTER_CONTROL.md` §1/§2, `WORK_REGISTRY.md` W-049…W-052 IN_PROGRESS). On-disk LOC therefore differ from the inventory's HEAD-era figures: `kernel/rules_runtime.py` 355 vs 299, `national/services/cds_engine.py` 1084 vs 983, `health_data/mdm/service.py` 160 vs 132, `matching.py` 325 vs 318, `gateways/lab_device_gateway.py` 226 vs 219, `services/offline_sync_service.py` 390 vs ~260, `certification/engine.py` 126 vs 117. Statuses are carried from the documents unchanged; none was re-executed or upgraded here.

### 1.2 Integration-gap analysis (on-disk sample, read-only)

All line numbers below are **current working-tree** values and may differ by 1–3 lines from the governance documents because of the concurrent edits noted above. No wiring was added, removed or enabled.

| Engine(s) | On-disk verification | Integration reading |
|---|---|---|
| ENG-A01 canonical workflow | `backend/app/workflows/engine.py` (237 lines) present; `identity/api/router.py:13` import, `:59` `include_router(workflows_routes.router)` | Mounted via identity router; `PARTIAL_VERIFIED` retained |
| ENG-A02/A03/A04/A05 kernel | `kernel/runtime/bootloader.py:30` `_phase_initialize_background()`, `:131` `EventBus(self.kernel)`, `:135` method; gates at `kernel/integration.py:27-28` | Boot paths present in source; not runtime-observed |
| ENG-A07/A08 rules + policy runtime | `kernel/runtime_routes.py:52-57,215-217` reads components `rules_runtime`/`policy_runtime`; HTTP router mounted at `factory.py:763-764`. **But** `kernel/runtime_integration.py:14` `init_runtime_extensions()` and `:35` `register_runtime_routes()` have **no call site anywhere under `backend/`** (grep returned only their definitions); `warmup_kernel()` at `kernel/integration.py:93-104` does not call them | Route present, component-registration initializer unreferenced → source-present wiring gap (see PROPOSED-F:H1). F-066 (no dedicated tests) is separate and unchanged |
| ENG-A10 national expression | `factory.py:692` imports `rules_router`, `:693` includes it | Route mounted; no dedicated tests (F-066) |
| ENG-A12 generated scaffold | `capabilities/workflow_engine/` exists (34 files, 541 Python LOC); `application/service.py`, `routes.py`, `capability.py`, `domain/entities.py` present. Reference scan found only 5 `app.capabilities.workflow_engine` hits, all inside its own directory | **DORMANT confirmed; stays dormant (F-071). Never activate** |
| ENG-B09 national CDS | `national/api/routes/__init__.py:4` imports `cds_router`, `:22` adds it to `national_router`; `factory.py` contains **no** `national_router` and **no** `cds_router` reference (verified) | **Unmounted confirmed; stays unmounted (F-068, D-021 PENDING). Do not enable** |
| ENG-B10 outbox worker | `core/startup.py:270,272`; `worker.py:86,100` | Wired in source; background loop not runtime-observed |
| ENG-B11/B12 search + doc-intel | `factory.py:661` `search_service_router`, `:713` `search_router`, `:707` `document_router` | Both search routers mounted in current tree (docs cite only one line); no status change |
| ENG-C07 / D01–D05 / D06 | `factory.py:779` `certification_router`, `:790` `ems_router`, `:793` `doc_intel_router`, `:796` `blood_bank_router`, `:799` `critical_care_router`, `:802` `biomedical_router`, `:805` `public_health_router`, `:690` `lims` | Routers present; router presence ≠ service readiness; no engine activated |

Source-only engines with no evidence of execution in the cited batches (A06, B07, B08, B11, C01, C08, C09, D06) remain `SOURCE_PRESENT`; their paths exist on disk for the sampled set (`mdm/service.py`, `matching.py`, `gateways/lab_device_gateway.py`, `certification/engine.py`, `capabilities/search_service/search.py` all verified present).

### 1.3 National Capability Registry feasibility

**Recommendation: GO-FOR-DESIGN of a reference-only capability index; NO-GO for any executing registry or new engine.**

Rationale:
- The authoritative facts already exist in `AUTONOMOUS_ENGINES_INVENTORY.md` (39 engines + status taxonomy), `AUTONOMOUS_ENGINES_DEPENDENCY_MAP.md` (entry points, consumers, hotspots), `NATIONAL_SERVICE_INVENTORY.md` §6 and `NATIONAL_SERVICE_CONTRACTS.md` §4. A static index would improve discoverability and duplicate prevention **without** adding a runtime component.
- Feasible design envelope: a generated/checked-in **document or static JSON/Markdown index** with engine ID → canonical path → status → entry point → owning domain → consumer list → linked F-ID, with no process, no dispatch, no health check, no routing and no per-request lookup. It must not become a routing authority or a single point of failure; the app must continue to work if the index is absent.
- **Non-negotiable constraints:** NO new engine is built; **ENG-A12 stays dormant**; **ENG-B09 stays unmounted**; no service activation, mount, refactor, dependency addition or clinical behavior change; no SPOF introduced; index is advisory only.
- This is a feasibility recommendation only. Building the index (even as documentation tooling) requires its own authorization and change record; it is **not** performed by this assessment.

### 1.4 W-056 status

**PARTIAL** — inventory totals and a bounded wiring sample (including ENG-A12 dormancy and ENG-B09 non-mount) were verified read-only and a reference-only registry design recommendation is recorded; no runtime verification, no index implementation, no new E-ID and no full 39-engine re-audit was performed.

---

## 2. Phase I — 18 national service readiness review (additive only)

Source: `NATIONAL_SERVICE_INVENTORY.md` §3/§16 (all 18 rows retained verbatim), `NATIONAL_SERVICE_CONTRACTS.md` §6/§11, `NATIONAL_INTEGRATION_ROADMAP.md` §2–§4. **No verdict was changed and no service was activated.**

Evidence-type key: **C** = contract row; **ST** = isolated synthetic unit test cited in engine evidence E-046…E-052; **IT** = isolated synthetic TestClient/DB-fixture integration test cited; **S** = source/API/model-only; **A** = enum/column/analytics signal only.

| # | Service | Inventory verdict | Contract (§6) | Evidence type cited | Additive note |
|---:|---|---|---|---|---|
| 01 | Laboratory | IMPLEMENTED | DRAFT | C + IT/ST (QC 26, LIMS auth 8, test-result 19) | 6 public token/phone ops still R-09; strict schema failures open |
| 02 | Hospital | PARTIAL | BLOCKED | C + S (4 thin test files) | 13 of 14 tables unmigrated (§15.3); no hospital/critical-care audit |
| 03 | Primary healthcare | CROSS_CUTTING / PARTIAL | BLOCKED | S + synthetic workflow cross-ref (E-048/050) | `cc_*` 0 % migrated, 0 audit, 0 dedicated tests |
| 04 | Pharmacy & medication | IMPLEMENTED | DRAFT | C + S (3 test files) | Explicit authz + dispense event missing; see PROPOSED-F:I1 |
| 05 | Radiology & imaging | IMPLEMENTED | DRAFT | C + IT (FHIR/R4 E-047, HL7 E-051) | 1 unmigrated table; critical-finding event missing |
| 06 | Emergency & ambulance | IMPLEMENTED | DRAFT | C + S (2 test files) | Typed schemas + test depth thin |
| 07 | Blood bank | PARTIAL | BLOCKED | C + S (8 test files) | No immutable audit; router `system:admin` |
| 08 | Immunization | CROSS_CUTTING / PARTIAL | BLOCKED | S (FHIR mapper source, 0 tests) | `cc_*`/`ehr_*` 0 %; mapper untested end-to-end |
| 09 | Public health & surveillance | PARTIAL | DRAFT/BLOCKED | C + S (2 test files) | No audit; admin-only router |
| 10 | Dental | NOT_IMPLEMENTED | NOT IMPLEMENTED | A (enum values verified at `biomedical/domain/enums.py:17`, `insurance/domain/enums.py:64,149`) | 0 ops, 0 tables; new build / funding-gated (W7) |
| 11 | Maternal & child health | CROSS_CUTTING / PARTIAL | BLOCKED | S (0 tests) | `cc_maternal` 0 % migrated, no audit |
| 12 | Chronic disease mgmt | PARTIAL | BLOCKED | C + S (1 test) + synthetic CDS (E-047, `app/ai/healthcare_cds.py`) | National CDS remains unverifiable (F-068); `cc_*` 0 % |
| 13 | Rehabilitation / physio | NOT_IMPLEMENTED | NOT IMPLEMENTED | A (`physiotherapist` string at `identity/professional_registry/models.py:15`; JSON column) | 0 ops, 0 tables |
| 14 | Mental health | DATA/ANALYTICS ONLY | DATA/ANALYTICS ONLY | A (enums/JSON columns/read-only analytics) | 0 ops, 0 dedicated tables |
| 15 | Referral & continuity | CROSS_CUTTING / PARTIAL | BLOCKED | S + synthetic workflow cross-ref (E-048/050) | 0 % migrated; F-007 coverage hole open; strongest unblock candidate (J7) |
| 16 | Insurance & claims | UNSERVED / BLOCKED (§15.1 correction) | UNSERVED / BLOCKED | S (84 coded endpoints unserved; 1 test) | Two claims implementations; ADR-G/ADR-I pending; **NOT 62 live ops** |
| 17 | Home healthcare | CROSS_CUTTING / PARTIAL | BLOCKED | S (0 tests) | `cc_*` 2 tables, 0 % migrated, no audit |
| 18 | Medical equipment | PARTIAL | DRAFT | C + S (1 test) | No immutable audit for maintenance/calibration |

**Path verification (sample):** all 18 corresponding service directories under `backend/app/` exist for the coded services (`lims`, `hospital`, `nursing`, `critical_care`, `care_continuum`, `pharmacy`, `radiology`, `ems`, `blood_bank`, `public_health`, `nhdw`, `chronic_care`, `biomedical`, `devices`, `insurance`, `billing`, `payments`, `ehr`); dental/rehabilitation/mental health have no service package, consistent with their A-only status. No verdict was recomputed from API/model existence.

**Duplicate-service check (contract doc + on-disk verification):** already-documented cases remain open — `national_facilities` has two ORM declarations (`models/clinical_scope.py:136`, `national/domain/facility.py:9`, both verified); `insurance/api/*` (8 modules, 84 endpoints) has no import from app/tests while `factory.py:601-605` mounts `routes/claims.py` + `routes/insurance.py` (verified); dual lab surfaces (`lims/` plus `services/*_service.py`) and patient-record ownership ambiguity (`national/`, `ehr/`, `national_data/`) are recorded in inventory §7 and contract §5. **These are carried-forward findings, not newly minted F-IDs.**

**Ungoverned cross-service write scan:** read-only AST scan of `backend/app/**/*.py` found **70 import sites across 25 distinct source→target service-package pairs**; **46** import-site module paths contain a `models` segment. Most inspected uses are reads (e.g. `national/fhir/care_plan.py:5` EHR→FHIR mapping, `national/api/routes/interop.py:24` LIMS `LabReport` query, `nursing/services.py:684,717` EHR medication reads, `devices/service.py:1112` pure baseline functions). Two **confirmed direct writes** are recorded below; other pairs are `NOT VERIFIED` as writes and are not asserted as defects.

### 2.1 Findings (proposed only — parent registry owns F-IDs)

**PROPOSED-F:H1 — kernel runtime extension registration has no call site.** `kernel/runtime_integration.py:14` `init_runtime_extensions()` and `:35` `register_runtime_routes()` are defined, and the runtime HTTP router is mounted (`factory.py:763-764`), but no caller exists anywhere under `backend/`; `warmup_kernel()` (`kernel/integration.py:93-104`) does not register these extensions. `runtime_routes.py:52-57,215-217` therefore reads `rules_runtime`/`policy_runtime` components that this initializer would register. Impact: possible unpopulated runtime surfaces; **not** a runtime observation and **not** a duplicate of F-066 (missing tests). Needs architecture review; **no code change authorized here.**

**PROPOSED-F:I1 — pharmacy POS writes an EHR-owned table directly.** `pharmacy/services.py:14` imports `MedicationDispense` from `app.ehr.models.medication`; `:962` constructs it and `:992` executes `self.db.add(dispense)` against `ehr_medication_dispenses` (`ehr/models/medication.py:120-121`). Contract §4 assigns `ehr_*` to EHR with R-DB-1 single-writer and "never a direct write"; contract §6 row 04 already records the pharmacy dispense event as missing. Needs ownership/event-boundary decision (ADR-D/ADR-B scope); **no change made here.**

**PROPOSED-F:I2 — core bootstrap writes a LIMS-owned table (classification required).** `core/bootstrap/departments.py:33` imports `app.lims.models.Department`, `:56-65` creates and `db.add`s it. This may be an authorized provisioning path; classify as governed bootstrap or cross-service write before any remediation. **No defect asserted, no change made here.**

### 2.2 W-057 status

**PARTIAL** — all 18 rows and their evidence types were reviewed additively, duplicate-service cases were cross-checked against the contracts and verified on disk, and a bounded cross-service import/write scan was performed; no service verdict changed, no tests were run, no new E-ID/F-ID was claimed, and readiness is not re-certified.

---

## 3. Risks, residual gaps and non-claims

- **Integration gaps remain open:** ENG-A12 dormant, ENG-B09 unmounted, kernel runtime registration unreferenced (PROPOSED-F:H1), and F-066…F-072 stay at their recorded status/severity. No engine was activated, enabled or refactored.
- **Readiness gaps remain open:** 407/833 ORM tables migrated, `cc_*`/`ehr_*`/`ins_*` at 0 %, 7 services without immutable audit, offline-first NOT SATISFIED (F-028 in-memory queue + F-069 first-wins `CRDT_MERGE`), and insurance UNSERVED/BLOCKED. Router presence is not service readiness.
- **Evidence currency risk:** working-tree LOC and factory line numbers have drifted during concurrent P0 remediation; an engine re-baseline is needed **after** that work settles, not during this read-only phase.
- **Authority gap:** D-020 (security) and D-021 (clinical safety) remain PENDING; ADR-A…ADR-J remain PENDING; W-056/W-057 do not authorize any repair, mount, test addition or contract change.
- **Process gap:** this assessment produces no new E-ID and ran no tests; all verification statements here are source/document observations only.

**Explicit non-claim:** this document makes **no production-readiness, clinical-safety, runtime-verified, migration-compatibility or release claim** for any engine, service or journey. `FINAL_DECISION.md` remains **HOLD**; D-020/D-021 remain **PENDING**; HOLD must not become GO on the strength of this assessment.
