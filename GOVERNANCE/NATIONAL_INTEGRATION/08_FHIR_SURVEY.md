# WS-03 Survey — FHIR R4 Interoperability

**Document:** 08 · **Status:** `TESTED` (local adapter) / `NOT IMPLEMENTED` (HTTP endpoint).

## Surface
`backend/app/health_core/fhir/` (6 modules), `backend/app/capabilities/fhir_interoperability/`, `backend/app/national/fhir/`, `backend/app/fhir/`, `backend/app/fhir/_scorecard.py`; FHIR tests: `test_fhir_operation_outcome.py`, `test_fhir_roundtrip.py`, `test_fhir_validation.py`.

## Verified evidence (prior cycle, unchanged)
- OperationOutcome adapter: validated errors mapped to structured FHIR `OperationOutcome`; round-trip and validation suites pass.
- I-2 fix: `diagnostics` detail allowlist + `html.escape(..., quote=True)`; identifier-bearing keys dropped.
- Source classification (`FINAL_03_FHIR_R4.md`): local adapter only, no HTTP/FHIR endpoint in sandbox. This program records the adapter as `TESTED`; the HTTP endpoint is `NOT IMPLEMENTED`.

## Gaps
| Gap | Classification | Reason |
|---|---|---|
| Real FHIR R4 HTTP endpoint | `NOT IMPLEMENTED` | no sandbox endpoint; route activation forbidden |
| National FHIR profiles / terminology binding | `BLOCKED` | depends on WS-04 official datasets + ADR decisions |
| External conformance (vendor/government) | `BLOCKED` | no external authority or endpoint |

## Program action
Maintain adapter regressions; add tests only where they exercise local behaviour. Do not claim interoperability certification.
