# WORKSTREAM E — INDEPENDENT QUALITY & ARCHITECTURE REVIEW

**Report ID:** HC-WSE-001  
**Date:** 2026-11-18 (final recheck after concurrent edits)  
**Repository:** `/home/samertts/workspace/projects/gula-integration`  
**Branch:** `integration/gula-unification-v1`  
**HEAD:** `2827c1ff1032918aa2541aa0b47bb7f2e5d6cac0`  
**Scope reviewed:** `backend/app/health_core/**` (38 Python source files) and `backend/tests/health_core/**` (25 test files, 382 collected tests)  
**Toolchain:** Python 3.12.13 · pytest 9.1.1 · ruff 0.16.10 · mypy 2.4.1  
**Review method:** independent source/AST/constructor/runtime inspection; workstream self-reports were treated as claims, not evidence.  
**Data class:** SYNTHETIC ONLY.

---

## 1. Verdict

**PASS WITH FINDINGS — final synthetic slice is green; NO production-activation or release approval.**

- **Deliverable A (independent tests): PASS** — 18/18 new static/structural tests pass.
- **Full synthetic Health Core suite: PASS** — 382/382 tests pass on the final snapshot.
- **Lint: PASS** — ruff clean across the whole Health Core source + test surface.
- **Types: PASS WITH BASELINE** — mypy reports **zero** `app.health_core` errors; the only 2 errors are the pre-existing `app/domain/order_state.py:63,81` baseline explicitly excluded by Phase Zero gate 5.
- **Protection integrity: PASS** — HOLD file, MPI artifacts, `gula-platform`, HEAD and baseline working-tree entries are intact.
- **Promotion readiness: NOT APPROVED** — findings F-01…F-03 must be resolved before any national/FHIR/production use. This review does **not** lift `GOVERNANCE/FINAL_DECISION.md` HOLD.

A transient red state was observed during concurrent owner edits (§6, F-06). The final recheck is green and is the state this verdict certifies.

---

## 2. Ten-check review table

| # | Check | Result | Independent evidence | Notes / finding |
|---:|---|---|---|---|
| 1 | File ownership and protected artifacts | **PASS** | HEAD unchanged; `FINAL_DECISION.md` md5 `effdfeaf10234678d83b2668c4489552`; MPI doc md5s match baseline; `gula-platform` @ `f478676b…`, status 0; baseline diff has **0 removals** | Pre-report status grew 463 → 533 entries (+70), all expected Health Core / acceleration artifacts; this report adds 1 expected entry |
| 2 | Sandbox isolation — no DB, broker, network or real identity imports | **PASS** | AST scan in `test_no_forbidden_runtime_dependency_roots_are_imported`; 38 modules parse and import acyclically | No SQLAlchemy, Alembic, Redis, Kafka, HTTP clients, sockets, `app.services.mpi`, `app.health_data` or `app.identity` imports |
| 3 | No route/router construction or production activation | **PASS** | `test_no_fastapi_router_construction_or_route_decorators`; `test_factory_and_main_do_not_import_or_reference_health_core` | Zero `APIRouter`, `include_router`, HTTP-method decorators or `health_core` references in `factory.py` / `main.py` |
| 4 | No persistence, schema, DDL or migration surface | **PASS** | `test_no_ddl_or_migration_artifacts_inside_health_core`; source inspection | No migrations directory, DDL tokens, ORM session, filesystem write or durable store; state is in-memory only |
| 5 | Identity seam, tenant scoping and synthetic references | **PASS** | `test_patient_scoping_services_take_the_identity_port_by_constructor`; `test_cross_tenant_patient_resolution_fails_closed`; `test_no_secret_or_real_identifier_literals_in_source` | Every patient-scoped service takes `PatientIdentityPort`; cross-tenant resolution raises `TenantMismatchError`; all refs are opaque `SYN-` values |
| 6 | State machines, immutable records and event vocabulary | **PASS WITH FINDING** | `test_legal_transition_maps_cover_every_state_and_are_terminal`; `test_all_immutable_entities_are_frozen_dataclasses`; `test_event_and_aggregate_enums_are_declared_exactly_once_in_shared_module` | State maps are complete and terminal states are closed; vocabulary is unique, but 4 semantics are reused — **F-01** |
| 7 | Cross-workstream contract conformance | **PASS** | Independent live diagnostic over all real clinical + lab emitted events produced **no BAD lines**; `test_cross_module_conformance.py` 9/9; 27 shared `EventType` values | Initial lab-local constants and payload/aggregate drift were corrected by owners before final recheck; concurrency caveat **F-06** |
| 8 | Idempotency, conflict accounting and offline replay | **PASS** | `test_outbox_ordering_is_deterministic_and_replay_is_idempotent`; `test_conflict_resolution_accounts_for_every_candidate_event`; dedicated suites 13 + 12 passing | Replays are duplicate-marked; every rejected/superseded event has a disposition and audit record |
| 9 | Arabic-first/RTL and client integration declarations | **PASS WITH LIMITATION** | `test_integration_arabic_rtl_a11y.py` 14/14; WS-D surface inspected read-only | Declaration/static coverage only; no real client screen or end-to-end app activation — **F-05** |
| 10 | Toolchain gates and test honesty | **PASS WITH BASELINE** | pytest 382/382; ruff clean; mypy zero Health Core errors (2 baseline errors elsewhere); `test_health_core_test_suite_has_no_skipped_or_xfail_tests`; `test_all_test_functions_contain_an_assertion_or_raising_validator` | One pre-existing Starlette/httpx deprecation warning; no skips, xfails, empty concrete functions or literal `return True` stubs found |

---

## 3. Deliverable A — independent static/structural tests

Created exactly one new test file in the allowed path:

`backend/tests/health_core/test_quality_review_static.py`

It contains **18 real tests**, deliberately independent of the existing denylist-style `test_sandbox_guards.py`. Techniques used: AST walks, import-graph walking, constructor annotation inspection, frozen-dataclass decoration checks, transition-map enumeration, event-id/timestamp checks, replay/decision runtime checks, protected-file hashing, sensitive-literal regex over string constants, and assertion-presence analysis.

| Group | Tests |
|---|---|
| Structure/layering | `test_every_module_parses_and_imports_without_circular_dependency`, `test_no_forbidden_runtime_dependency_roots_are_imported`, `test_no_fastapi_router_construction_or_route_decorators`, `test_factory_and_main_do_not_import_or_reference_health_core` |
| SOLID/no stubs/DI | `test_no_empty_concrete_functions_or_literal_fake_success_returns`, `test_patient_scoping_services_take_the_identity_port_by_constructor`, `test_all_immutable_entities_are_frozen_dataclasses` |
| Events/audit | `test_event_and_aggregate_enums_are_declared_exactly_once_in_shared_module`, `test_legal_transition_maps_cover_every_state_and_are_terminal`, `test_event_emitters_append_immutable_events_with_synthetic_ids` |
| Offline/isolation/recovery | `test_outbox_ordering_is_deterministic_and_replay_is_idempotent`, `test_conflict_resolution_accounts_for_every_candidate_event`, `test_cross_tenant_patient_resolution_fails_closed` |
| Protection/honesty | `test_final_decision_and_protected_governance_file_hash_is_unchanged`, `test_no_ddl_or_migration_artifacts_inside_health_core`, `test_no_secret_or_real_identifier_literals_in_source`, `test_health_core_test_suite_has_no_skipped_or_xfail_tests`, `test_all_test_functions_contain_an_assertion_or_raising_validator` |

**Result:** `18 passed, 1 warning in 1.49s` (final recheck).

Gaps found by the review are reported here rather than encoded as fake passing tests.

---

## 4. Findings by severity

### MEDIUM

**F-01 — Shared event vocabulary has semantic gaps; two state changes reuse another event’s name.**  
`common/event_types.py` has no `organization.registered`, `encounter.started`, `diagnosis.resolved` or `practitioner.deactivated`. `clinical/services.py:78-82` maps `IN_PROGRESS` to `ENCOUNTER_CREATED`; diagnosis resolution emits `DIAGNOSIS_RECORDED` with an explicit `transition` payload. This was disclosed by WS-A and independently confirmed in source. It is not fake success, but downstream consumers cannot distinguish create from start/resolve by event type alone. Owner action: add explicit shared vocabulary values before promotion; do not let individual workstreams invent local strings.

**F-02 — Authorization boundaries are declarative only; runtime services enforce tenant/patient scoping, not RBAC/ABAC.**  
`contracts/authorization.py` defines 22 non-public boundaries and `integration/auth_boundaries.py` declares client roles, but clinical/lab service methods contain no role/permission checks. Acceptable in the isolated synthetic slice because nothing is exposed; blocking for any future boundary activation. Owner action: enforce the declared permissions in the eventual boundary layer.

**F-03 — Local error contract is not FHIR R4 `OperationOutcome`-complete.**  
`contracts/errors.py` implements the canonical JSON envelope (`code`, `message`, `details`, `request_id`, `timestamp`, `detail`, `detail_ar`) but contains no `OperationOutcome`/`application/fhir+json` mapping. `GOVERNANCE/NATIONAL_SERVICE_CONTRACTS.md` (E7, R-ERR-1) expects canonical envelope **plus** FHIR `OperationOutcome` for FHIR requests. Since no route is exposed, this is local-alpha only; it must not be presented as a national production contract.

### LOW

**F-04 — Terminology validation is structural, not release-aware.**  
ICD codes are pattern-checked, LOINC check digits are not recomputed and UCUM units are an allow-list. No clinical interpretation, thresholding or CDS is provided. This matches the disclosed synthetic scope but must not be mistaken for clinical-grade validation.

**F-05 — Client/RTL coverage is declaration-level, not end-to-end.**  
WS-D inspected Android, iOS, Flutter desktop and hospital desktop read-only. No synthetic demo screen was identified; iOS `isRTL` defaults false until an Arabic locale/saved language is set; hospital-desktop offline cache DDL contains legacy real-identifier-shaped column names (observed only, not modified). The synthetic Python slice’s Arabic/RTL tests validate its own declaration surface, not real client behavior.

### PROCESS / RESOLVED

**F-06 — Concurrent owner edits caused a transient event-contract/test drift.**  
During the review window, lab event constants were promoted to `EventType`, contract payloads were tightened, and `NOTE_ADDED` aggregate semantics moved between `MEDICAL_RECORD` and `ENCOUNTER`. At 13:45 the suite transiently failed:

`tests/health_core/test_clinical_encounter.py::test_notes_are_scoped_to_encounter_and_emit_note_added` — expected `AggregateType.ENCOUNTER`, observed `AggregateType.MEDICAL_RECORD`.

By the final recheck (13:49 onward), service, catalogue and test were consistent on `ENCOUNTER`, the cross-module conformance file had landed, and **382/382** tests passed. No WS-E source/test file other than the two allowed deliverables was modified. This is not a final-state code defect, but it proves review results are snapshot-sensitive; any promotion must re-run these exact gates after all concurrent writes stop.

### INFORMATIONAL / NOT A HEALTH CORE DEFECT

- `mypy`: 2 pre-existing `no-untyped-def` errors in `backend/app/domain/order_state.py:63,81`; zero Health Core errors. Phase Zero explicitly treats this as baseline.
- pytest warning: Starlette `TestClient`/httpx deprecation; pre-existing and unrelated.

---

## 5. Exact test results and commands

All commands were run from the pinned toolchain; no environment, dependency or production service was modified.

```bash
# From /home/samertts/workspace/projects/gula-integration/backend
ENV=test RUNTIME_MODE=test PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=.:.. \
/tmp/opencode/mpi-venv/bin/python -m pytest tests/health_core -q --tb=short
# 382 passed, 1 warning in 3.14s

ENV=test RUNTIME_MODE=test PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=.:.. \
/tmp/opencode/mpi-venv/bin/python -m pytest tests/health_core/test_quality_review_static.py -q --tb=short
# 18 passed, 1 warning in 1.49s

# From repository root
/tmp/opencode/mpi-venv/bin/python -m ruff check backend/app/health_core backend/tests/health_core
# All checks passed!

# From repository root
MYPYPATH=backend /tmp/opencode/mpi-venv/bin/python -m mypy \
  --config-file pyproject.toml backend/app/health_core
# backend/app/domain/order_state.py:63: error: Function is missing a type annotation ...
# backend/app/domain/order_state.py:81: error: Function is missing a type annotation ...
# Found 2 errors in 1 file (checked 38 source files)
# Zero errors attributable to app.health_core.
```

Independent live event-conformance diagnostic (read-only, over real emitted clinical + lab events):

```bash
# From backend/, using /tmp/opencode/healthcore-accel/diagnose_event_conformance.py
ENV=test RUNTIME_MODE=test PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=.:.. \
/tmp/opencode/mpi-venv/bin/python /tmp/opencode/healthcore-accel/diagnose_event_conformance.py
# Shared EventType values: 27
# No BAD/contract-violation lines.
```

---

## 6. Protection integrity and change discipline

| Artifact | Final observation |
|---|---|
| `gula-integration` HEAD | `2827c1ff1032918aa2541aa0b47bb7f2e5d6cac0` — unchanged |
| `FINAL_DECISION.md` | md5 `effdfeaf10234678d83b2668c4489552`; HOLD text intact at lines 13, 36, 47, 361 |
| MPI audit docs | `MPI_INDEPENDENT_AUDIT_FINDINGS.md` `ea3969d0…`, `MPI_FINAL_INDEPENDENT_AUDIT.md` `1a02c015…` — both match baseline |
| `gula-platform` | HEAD `f478676b6fc375338648dde46fbf076c015a3f91`, status 0 — untouched |
| Working tree | Baseline 463 entries → 533 pre-report entries, **0 removed**; additions are exactly the Health Core package/tests and acceleration reports; this report adds 1 expected entry |
| WS-E writes | Only `backend/tests/health_core/test_quality_review_static.py` and this report |
| Forbidden git actions | None: no commit, push, merge, rebase, PR, deploy, `git add`, `git reset` or `git clean` |
| Runtime/production | No production DB, migration, DDL, deployment, real patient record or secret used |

---

## 7. Owner-gated limitations

This review cannot and does not certify:

1. Lifting the HOLD or authorizing production/release activity.
2. Real MPI/NHID/canonical-patient integration; the identity seam is deliberately synthetic and in-memory.
3. National FHIR/HL7 profiles, terminology releases, real analyzer integration, or clinical-safety behavior.
4. Runtime RBAC/ABAC enforcement; only declarative boundaries exist (F-02).
5. Persistence, durability, concurrency across workers, broker publication or multi-container deployment.
6. Real Android/iOS/Flutter/desktop end-to-end behavior or complete RTL certification (F-05).
7. Any change to baseline protected/user-modified files outside the two WS-E writable paths.

---

## 8. Synthetic safety statement

Every identifier observed in this slice is an opaque `SYN-` fixture; no NHID, national ID, name, DOB, phone, credential or real patient record is stored or processed. All repositories and event logs are in-memory and process-local. There is no database, migration, DDL, filesystem persistence, HTTP client, socket, broker publisher, FastAPI router, route registration or `factory.py`/`main.py` wiring. The package is an isolated synthetic development artifact. It is safe to retain in this workspace as uncommitted, non-activated code; it is **not** safe to promote as a national production service without the findings above being closed and an explicit owner decision.

---

## 9. Bottom line for the Program Director

- **Current isolated synthetic vertical slice:** structurally sound, fully green, protection intact.
- **Blocking defects in final synthetic test gate:** none.
- **Promotion blockers:** F-01 (event semantics), F-02 (runtime authorization), F-03 (FHIR error contract).
- **Release decision:** unchanged — **HOLD**.
