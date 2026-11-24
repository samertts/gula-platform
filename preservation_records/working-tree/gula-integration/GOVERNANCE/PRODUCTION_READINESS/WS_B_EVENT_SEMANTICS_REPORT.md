# WORKSTREAM B — EVENT SEMANTICS REPORT

**Program:** GULA Production Readiness Acceleration Program
**Workstream:** WS-B (Event Semantics) — closure of WS-E finding F-01
**Repository:** `/home/samertts/workspace/projects/gula-integration`
**Branch:** `integration/gula-unification-v1` · **HEAD:** `2827c1ff1032918aa2541aa0b47bb7f2e5d6cac0` (unchanged)
**Data class:** SYNTHETIC ONLY — no database, migration, broker, deployment, real patient record or secret.
**Governing decision:** `GOVERNANCE/FINAL_DECISION.md` remains **HOLD** (md5 `effdfeaf10234678d83b2668c4489552`); MPI verdict remains **REJECT**. This report is development evidence only — not a clinical-readiness, release, safety or production-approval claim.
**Git discipline:** no commit, push, merge, rebase, PR, deploy, `git add`, `git reset` or `git clean`.
**Latest re-verification:** 2026-11-18 — WS-B-focused suites and ruff are green; the wider
Health Core snapshot contains six failures in concurrent, non-WS-B files (§5). No WS-B code
or protected artifact changed during re-verification.

---

## 1. Scope and source findings

Reviewed first: `GOVERNANCE/ACCELERATION/QUALITY_ARCHITECTURE_REVIEW.md` §4 F-01 and
`GOVERNANCE/ACCELERATION/ACCELERATED_EXECUTION_REPORT.md` §6 and §7.

F-01 stated four missing shared values (`organization.registered`, `encounter.started`,
`diagnosis.resolved`, `practitioner.deactivated`) and two ambiguous reuses:
`planned -> in_progress` emitted `ENCOUNTER_CREATED`; diagnosis resolution emitted
`DIAGNOSIS_RECORDED` with a `transition` payload.

Only the ten explicitly owned paths were written. `gula-platform` remained byte-untouched
(HEAD `f478676b6fc375338648dde46fbf076c015a3f91`, status 0 throughout). MPI files and all
other workstreams' source, tests and governance reports were read-only.

---

## 2. Exact changes

| Path | Change |
|---|---|
| `backend/app/health_core/common/event_types.py` | Added `EventType.ORGANIZATION_REGISTERED = "organization.registered"`, `ENCOUNTER_STARTED = "encounter.started"`, `DIAGNOSIS_RESOLVED = "diagnosis.resolved"`, `PRACTITIONER_DEACTIVATED = "practitioner.deactivated"`. Added `AggregateType.ORGANIZATION = "organization"`. Marked `ENCOUNTER_CREATED` / `DIAGNOSIS_RECORDED` in comments as retained pre-1.1.0 ambiguous legacy values. Added immutable `LEGACY_EVENT_TYPE_MAP`, the legacy marker constants and `canonical_event_type(event_type, *, payload=None)`. |
| `backend/app/health_core/common/events.py` | Added `EVENT_SCHEMA_VERSION = "1.1.0"`. Added additive `DomainEvent.schema_version: str = EVENT_SCHEMA_VERSION` and optional keyword-only `schema_version` parameter to `new_event()`; all pre-existing call signatures remain valid. |
| `backend/app/health_core/common/__init__.py` | Re-exported the new types, version, legacy map, marker constants and `canonical_event_type`. |
| `backend/app/health_core/contracts/events.py` | Added four `EventDefinition` entries (one per new `EventType`) with correct aggregates and required payload keys. Re-exported the version/compatibility symbols from the contract module. |
| `backend/app/health_core/contracts/__init__.py` | Re-exported the new contract symbols. |
| `backend/app/health_core/clinical/services.py` | `TRANSITION_EVENTS[IN_PROGRESS]` now maps to `EventType.ENCOUNTER_STARTED`; `DiagnosisService.resolve()` now emits `EventType.DIAGNOSIS_RESOLVED`. Every legacy payload key was preserved. `NOTE_ADDED` aggregate remains `AggregateType.ENCOUNTER`. Organisation-registration docstring now records the handoff decision (§8). |
| `backend/tests/health_core/test_clinical_encounter.py` | Only the lifecycle event-type expectation changed: second event is `ENCOUNTER_STARTED`, not `ENCOUNTER_CREATED`. |
| `backend/tests/health_core/test_clinical_diagnosis_observation.py` | Only the resolve expectation changed: one legacy `DIAGNOSIS_RECORDED` plus one new `DIAGNOSIS_RESOLVED`; the `transition == "resolve"` assertion was retained on the resolved event. |
| `backend/tests/health_core/test_event_semantics.py` | **New** — 25 real producer/consumer conformance tests (detailed in §4). |
| This file | WS-B report. |

No FastAPI router, route, `factory.py`/`main.py` change, DDL, migration, dependency, secret or
production activation was introduced. No assertion was deleted, weakened, skipped or xfailed.

---

## 3. Requirement status

| # | Requirement | Status | Evidence |
|---:|---|---|---|
| 1 | Four explicit lifecycle `EventType` values | **VERIFIED** | Exact dotted strings asserted in `test_explicit_lifecycle_values_have_exact_dotted_strings`; `AggregateType.ORGANIZATION` added for the organisation aggregate. |
| 2 | Change the two ambiguous emitters | **VERIFIED** | `test_encounter_start_emits_explicit_event_with_all_legacy_payload_keys`, `test_diagnosis_resolve_emits_explicit_event_with_all_legacy_payload_keys`, `test_no_*_reuse_remains`, AST scope test. All legacy payload keys retained; `NOTE_ADDED` aggregate unchanged. |
| 2a | Emit practitioner-deactivation event if a path exists | **NOT APPLICABLE** | `PractitionerRegistry` has no deactivation method/state transition; only `register(active=False)` at creation. Adding a new command surface would exceed F-01 scope. The value is reserved in the shared vocabulary. |
| 2b | Emit organization-registered event if a path exists | **PARTIALLY VERIFIED / BLOCKED (handoff)** | `register_organization()` exists and is still silent. Emitting would make the read-only `test_cross_module_conformance.py::test_real_clinical_events_conform_to_ws_c_catalogue` fail its exact `len(slices.clinical_events) == 8` assertion (would become 9). That file is outside my write ownership and is an explicit green gate, so the emitter was not changed. Vocabulary + catalogue + validation are ready; see §8. |
| 3 | Every new `EventType` has an `EventDefinition` | **VERIFIED** | `set(EVENT_CATALOGUE) == set(EventType)` (existing `test_contracts_events.py` + new test); four new definitions validated with real keys and fail-closed missing-key checks. |
| 4 | Legacy values retained, mapping + schema version | **VERIFIED** | Legacy values unchanged and comment-marked; immutable `LEGACY_EVENT_TYPE_MAP`; payload-aware `canonical_event_type()` (a blind 1:1 map would be wrong because genuine create/record events still use the legacy names); `EVENT_SCHEMA_VERSION` documented. Migration requirements documented below, **not executed**. |
| 5 | Producer-consumer conformance, no ambiguous reuse, immutable synthetic ids | **VERIFIED** | New 25-test suite + read-only cross-module conformance 12/12; emitted clinical and lab events validated against the real catalogue; `SYN-` ids, UTC timestamps and frozen records asserted. |
| 6 | `new_event()` backward compatible, opaque `SYN-` ids | **VERIFIED** | New parameter is keyword-only with a default; old-style call tested; `to_dict()` envelope asserted; all ids remain `SYN-` from `new_synthetic_id`. |

---

## 4. New conformance suite (`test_event_semantics.py`, 25 tests)

- Exact dotted values and retention of the two legacy strings.
- Catalogue completeness and four definitions' aggregate + required-key sets; each definition validated with a generated synthetic sample, plus fail-closed missing-key cases.
- Real clinical lifecycle producer (`_ClinicalSlice`): practitioner + organisation + facility + encounter create + `IN_PROGRESS` transition + note + diagnosis record + resolve + observation + record open = 9 real events, every one validated by `validate_domain_event()`.
- Real lab producer: order → specimen → collected → received → testing → result → verification = 11 real events, every one validated, and none misusing the new lifecycle values.
- Explicit-event payload assertions including all legacy keys (`transition`, `from_status`, `to_status`, `version`, `status`), correct from/to states and versions.
- Runtime and AST proof that the legacy names occur only in `create`/`record` and that the new `ENCOUNTER_STARTED` value is the `IN_PROGRESS` mapping; no legacy overload remains in emitter paths.
- `NOTE_ADDED` aggregate still `ENCOUNTER`.
- Compatibility mapping: legacy-shaped events reconstructed with `dataclasses.replace()` from real emitted events and correctly disambiguated; genuine create/record events preserved; unregistered types fail closed.
- Schema version exported identically from `common` and `contracts` and present on every real event; old-style `new_event()` call still works.
- Frozen event records, `SYN-` ids, UTC ISO timestamps, naive timestamp rejection.

---

## 5. Exact commands and results

All commands used the pinned toolchain `/tmp/opencode/mpi-venv/bin/python` (Python 3.12.13,
pytest 9.1.1, ruff 0.16.10, mypy 2.4.1). Environment: `ENV=test RUNTIME_MODE=test
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=.:..`, run from `backend/`.

```bash
# Task-specified focused command (latest re-verification, 2026-11-18)
ENV=test RUNTIME_MODE=test PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=.:.. \
/tmp/opencode/mpi-venv/bin/python -m pytest \
  tests/health_core/test_event_semantics.py \
  tests/health_core/test_clinical_encounter.py \
  tests/health_core/test_clinical_diagnosis_observation.py \
  tests/health_core/test_contracts_events.py \
  tests/health_core/test_cross_module_conformance.py -q --tb=short
# 95 passed, 1 warning in 1.37s  (0 failed / 0 skipped)

# Read-only cross-module conformance, standalone (latest re-verification)
... -m pytest tests/health_core/test_cross_module_conformance.py -q --tb=short
# 12 passed, 1 warning in 0.44s
# Earlier isolated new-suite run: 25 passed, 1 warning in 0.79s.

# Full Health Core suite, baseline BEFORE WS-B writes (historical)
... -m pytest tests/health_core -q --tb=short
# 385 passed, 1 warning in 4.14s

# Full Health Core suite, latest snapshot (concurrent workstreams active)
... -m pytest tests/health_core -q --tb=short
# 641 collected — 6 failed, 635 passed, 1 warning in 8.98s
# Failures:
#   test_quality_review_static.py::test_health_core_test_suite_has_no_skipped_or_xfail_tests
#   test_quality_review_static.py::test_all_test_functions_contain_an_assertion_or_raising_validator
#   test_terminology_validators.py::test_loinc_curated_codes_are_accepted_with_declared_version[718-7]
#   test_terminology_validators.py::test_loinc_curated_codes_are_accepted_with_declared_version[777-3]
#   test_terminology_validators.py::test_ucum_curated_units_are_accepted_exactly[/min]
#   test_terminology_validators.py::test_ucum_format_negatives_are_invalid[mmol//L]
# Root causes are outside WS-B ownership: a concurrent SyntaxError in
# tests/health_core/test_terminology_provenance.py:22 (`UCUM_CODES if False else
# UCUM_UNITS,` inside an import) breaks the two AST-scanning tests, and the
# four terminology-validator assertions reflect concurrent terminology changes.
# Historical snapshots: 544 passed / 5 failed, then 516 passed / 9 failed while
# other workstreams were mid-edit. WS-B never modified, suppressed or skipped
# any of these failures.

# Full suite excluding the three currently failing concurrent-write test files
... -m pytest tests/health_core -q --tb=short \
  --ignore=tests/health_core/test_quality_review_static.py \
  --ignore=tests/health_core/test_terminology_provenance.py \
  --ignore=tests/health_core/test_terminology_validators.py
# 535 passed, 1 warning in 3.56s

# Ruff — from repository root, only WS-B-owned paths
/tmp/opencode/mpi-venv/bin/python -m ruff check <the nine WS-B source/test paths>
# All checks passed!

# MyPy — from repository root (latest re-verification)
MYPYPATH=backend /tmp/opencode/mpi-venv/bin/python -m mypy \
  --config-file pyproject.toml backend/app/health_core
# Found 6 errors in 2 files (checked 75 source files)
#   2  backend/app/domain/order_state.py:63,81       — pre-existing baseline
#   4  backend/app/health_core/fhir/deserializers.py — concurrent WS file
# ZERO errors attributable to WS-B-owned files.
# Earlier concurrent snapshot: 16 errors in 5 files (fhir serializers/deserializers
# and reliability modules); all were outside WS-B ownership.
```

The single pytest warning is the pre-existing third-party `StarletteDeprecationWarning`; no
warning originates in WS-B code.

---

## 6. Backward compatibility and migration requirements (documented only)

**Compatibility guarantees delivered**

- No `EventType` value was removed or renamed. `encounter.created` and `diagnosis.recorded`
  keep their original strings and continue to denote genuine create/record events.
- Every legacy payload key on the two changed emitters is retained: encounter start still
  carries `transition`, `from_status`, `to_status`, `version` (plus `encounter_ref`,
  `tenant_id`, `patient_ref`); diagnosis resolution still carries `transition`, `status`,
  `version` (plus `diagnosis_ref`, `encounter_ref`, `patient_ref`).
- `new_event()` accepts every pre-1.1.0 call unchanged; `schema_version` is optional.
- `DomainEvent` gained one defaulted field, so existing keyword constructors and
  `dataclasses.replace()` usage remain valid.

**Event schema version:** `"1.1.0"`. The pre-change vocabulary had no explicit version
(implicitly `"1.0.0"`). This is an additive minor bump.

**Migration requirements — NOT executed, no data touched**

1. Consumers that project `encounter.created` into a "started" state must call
   `canonical_event_type(event.event_type, payload=event.payload)`; only legacy events with
   `transition` truthy and `to_status == "in_progress"` become `encounter.started`. A bare
   name-based rename would corrupt genuine planned-encounter creations.
2. Consumers that project `diagnosis.recorded` into a "resolved" state must apply the same
   helper; only events with `transition == "resolve"` become `diagnosis.resolved`.
3. `LEGACY_EVENT_TYPE_MAP` documents the intended target of each overload and is immutable;
   it is a migration aid, not a publisher-side rewrite.
4. Event envelopes carrying `schema_version` should be branched on that value when a future
   consumer must replay mixed-version logs; a v1.0.0 envelope (no field) is treated as the
   legacy interpretation described above.
5. Persistence, outbox replay and broker publication do not exist in this synthetic slice.
   Any real migration requires a separate owner-approved work package with its own DDL/
   migration proposal. **No migration was executed by WS-B.**

---

## 7. Defects fixed

1. **F-01 ambiguous encounter semantics** — `planned -> in_progress` now emits
   `encounter.started`, with all legacy payload keys preserved.
2. **F-01 ambiguous diagnosis semantics** — `active -> resolved` now emits
   `diagnosis.resolved`, with all legacy payload keys preserved.
3. **F-01 missing shared vocabulary** — all four lifecycle values plus the organisation
   aggregate now exist centrally and are covered by the catalogue and parametrized tests.
4. **No disambiguation path for existing consumers** — added immutable legacy mapping and
   payload-aware `canonical_event_type()` with tests over reconstructed real legacy events.
5. **Unversioned event envelope** — explicit `EVENT_SCHEMA_VERSION` and per-event
   `schema_version`, additive and backward compatible.

---

## 8. Handoff requests and limitations

1. **Organization registration emitter (WS-A / conformance-test owner).** `register_organization()`
   is still silent. Turning it into an `ORGANIZATION_REGISTERED` emit is intentionally deferred:
   the read-only `tests/health_core/test_cross_module_conformance.py` asserts exactly 8 clinical
   events, so the emit would change that gate to 9. The shared value, aggregate, catalogue
   definition and validation sample are already in place. Request: owner updates the expected
   count and adds an emitter assertion, then WS-A or a follow-up workstream enables the emit.
2. **Practitioner deactivation emitter.** No deactivation method exists in `PractitionerRegistry`;
   `PRACTITIONER_DEACTIVATED` is reserved. If a deactivation command is added in an owner-approved
   work, it must emit this value.
3. **Full-suite red state is concurrent, not WS-B.** At the latest re-verification six unrelated
   tests were failing in other workstreams' files (§5): two AST-scanning tests blocked by a
   concurrent syntax error in `test_terminology_provenance.py:22`, and four terminology-validator
   assertions. WS-B did not modify them and does not claim the whole Health Core suite is green;
   the task-scoped suites, the read-only conformance gate and every WS-B-owned file are green.
4. **Synthetic scope only.** No real broker, persistence, replay of historical events, FHIR
   mapping, national profile, clinical-safety behaviour or production activation is provided.
5. **F-02 / F-03 remain owner-gated.** This workstream closes F-01 only; it does not lift HOLD
   or REJECT, and it does not implement runtime RBAC/ABAC or a real FHIR `OperationOutcome` adapter.

---

## 9. Protection integrity

| Artifact | Observation |
|---|---|
| `gula-integration` HEAD | `2827c1ff1032918aa2541aa0b47bb7f2e5d6cac0` — unchanged |
| `FINAL_DECISION.md` | md5 `effdfeaf10234678d83b2668c4489552` — HOLD text intact, untouched |
| MPI audit docs | `MPI_INDEPENDENT_AUDIT_FINDINGS.md` `ea3969d0…`, `MPI_FINAL_INDEPENDENT_AUDIT.md` `1a02c015…` — unchanged |
| `gula-platform` | HEAD `f478676b6fc375338648dde46fbf076c015a3f91`, status 0 — untouched |
| Forbidden git actions | None |
| Runtime / production | No DB, migration, DDL, secret, broker, route, deployment or real data |

**Bottom line:** F-01's vocabulary gaps and both ambiguous reuses are closed with additive,
backward-compatible, fully tested shared code. HOLD and REJECT are unchanged; promotion is not
approved. One emitter enhancement (organization registration) is explicitly handed off because
a read-only gate pins the current event count.
