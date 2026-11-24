# Final Report 02 — Event Semantics (WS-B) + F-01 (HIGH) remediation

**Report ID:** PR-FINAL-02 · **Date:** 2026-11-18 · **Data class:** SYNTHETIC ONLY
**Governing decision:** HOLD / REJECT unchanged. Development evidence only — a validation-only event catalogue, no broker/outbox/publisher.

## 1. Classification

| Deliverable | Classification | Basis |
|---|---|---|
| Shared `EventType` / `AggregateType` vocabulary (27 values, single source of truth) | **VERIFIED** | Aliasing + vocabulary tests; no local duplicate event strings remain |
| `EventDefinition` catalogue + `validate_domain_event()` | **VERIFIED** | 38 catalogue tests; now enforced at the producer boundary |
| Explicit lifecycle semantics (start/admit/transfer/discharge/cancel) | **VERIFIED** | Full six-target lifecycle regression feeds real emitted events into the real validator |
| Event broker / durable outbox / publisher | **NOT IMPLEMENTED** | Validation-only by design — owner-gated |

Overall workstream classification: **VERIFIED (synthetic, validation-only scope)**.

## 2. The HIGH finding — F-01

**Finding (independent correctness review, `ADVERSARIAL_REVIEW_CORRECTNESS.md` §F-01):** the catalogue defined required payload keys for the richer encounter lifecycle events (`ENCOUNTER_STARTED`, `ENCOUNTER_ADMITTED`, `ENCOUNTER_TRANSFERRED`, `ENCOUNTER_DISCHARGED`, `ENCOUNTER_CANCELLED`) and `validate_domain_event()` existed — but **no emitter ever called it**. Real events produced by `EncounterService.transition()` violated their own catalogue (missing `facility_ref`, `from_facility_ref`/`to_facility_ref`, `disposition`, `reason`). The prior conformance fixture only exercised `PLANNED → IN_PROGRESS`, so the four richer payloads were never observed. Previously classified as a **promotion blocker** in the acceleration report §7.

**Fix (behaviour-preserving for valid events, fail-closed for invalid ones):**

1. **Enforcement at the producer boundary** — `ClinicalEventSink._emit()` now calls `validate_domain_event(event)` **before** `self._events.append(event)`. An event that violates its catalogue is rejected before it can reach the sink. The catalogue definitions themselves were **not weakened**.
2. **Real-context payloads** — `transition()` gained optional `to_facility_ref` and `disposition` inputs (both strictly validated) and now populates:
   - `ADMITTED` → `facility_ref` from the encounter's own facility
   - `TRANSFERRED` → `from_facility_ref` (encounter facility) + `to_facility_ref` (validated caller input or the encounter's facility as a real-state default)
   - `DISCHARGED` → `disposition` (validated caller input or the target status value)
   - `CANCELLED` → `reason` from the encounter's real reason
   
   No fabricated identifiers: defaults come from real encounter state. Idempotency fingerprint includes the new inputs, so a replay with different context is not silently conflated.
3. **Legacy shapes preserved** — `ENCOUNTER_CREATED` with `transition` payload and the reconstructed pre-1.1.0 shapes remain intact; no event name or envelope field changed.

## 3. Regression tests added (strict, no skips)

- `test_cross_module_conformance.py::test_every_encounter_lifecycle_transition_emits_a_catalogue_valid_event` — drives a real clinical slice through all six transition targets (PLANNED → IN_PROGRESS → ADMITTED → TRANSFERRED → ADMITTED → DISCHARGED plus a separate CANCELLED encounter), asserts all six transition event types were emitted, calls `validate_domain_event()` on each, and checks the four richer payloads are sourced from real facility/disposition/reason.
- `test_event_semantics.py::test_emit_validates_against_catalogue_before_appending_to_the_sink` — AST structural check: `_emit` contains exactly one `validate_domain_event` call and one `append` call, and validation precedes append. Fails if the enforcement is removed or reordered.

## 4. I-1 ( INFORMATIONAL, lead-owned ) — corrected in this report set

`common/ids.py::is_synthetic_id` docstring had claimed "True only for strings produced by `new_synthetic_id`" while the predicate is a cheap `SYN-` prefix + minimum-length shape check. Tightening the predicate would break 39 legitimate fixture usages; the correct fix was to **correct the overclaim** and point callers to the strict per-type validators (`require_synthetic_ref` with explicit prefix). Regression test `test_is_synthetic_id_is_a_shape_check_and_strict_validation_is_separate` locks in: generated ids pass, hand-written fixture shapes pass, non-SYN / too-short values fail, and strict prefix validation rejects weak shapes. Full disposition in `FINAL_07_ADVERSARIAL_GOVERNANCE.md`.

## 5. Files changed (this cycle)

`backend/app/health_core/clinical/services.py` (baseline-protected, allow-listed with justification), `backend/app/health_core/common/ids.py` (baseline-protected, allow-listed), `backend/tests/health_core/test_cross_module_conformance.py` (baseline-protected, allow-listed), `backend/tests/health_core/test_event_semantics.py` (new test file, approved surface).

## 6. Verification

```bash
cd /home/samertts/workspace/projects/gula-integration/backend
ENV=test RUNTIME_MODE=test PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=.:.. \
  /tmp/opencode/mpi-venv/bin/python -m pytest \
  tests/health_core/test_event_semantics.py \
  tests/health_core/test_cross_module_conformance.py -q --tb=short
# 40 passed (27 event semantics + 13 cross-module conformance)
```
Ruff: `All checks passed!`. Full suite: 773 passed.

## 7. Residual

- Validation-only: no broker, outbox or publisher is created — correct for a synthetic slice; a durable event bus requires owner approval.
- F-01 is **CLOSED**: the acceleration report §7 promotion blocker no longer applies to event validation enforcement; promotion itself remains HOLD-gated.

**End of final report 02.**
