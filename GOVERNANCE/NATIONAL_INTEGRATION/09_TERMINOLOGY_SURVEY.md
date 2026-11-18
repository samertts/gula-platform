# WS-04 Survey — Terminology

**Document:** 09 · **Status:** `TESTED` (offline validators) / `BLOCKED` (licensed datasets).

## Surface
`backend/app/health_core/terminology/` (8 modules), `backend/app/national/reference/` (ICD/LOINC/SNOMED/UCUM), `test_terminology_provenance.py` (15 tests), `test_terminology_validators.py` (23 tests).

## Verified evidence (prior cycle, unchanged)
- ICD-10 / LOINC / UCUM validation and provenance metadata implemented and tested (38 tests).
- Every validation result carries provenance (system, version, source) — dataset provenance cannot be silently lost.
- Source classification (`FINAL_04_TERMINOLOGY.md`): official datasets offline. This program records the offline validators as `TESTED`; licensed releases are `BLOCKED`.

## Gaps
| Gap | Classification | Route |
|---|---|---|
| SNOMED CT official release | `BLOCKED` | licensed dataset; no license (`05` §7) |
| LOINC check-digit verification | `NOT IMPLEMENTED` | authoritative release unavailable; no algorithm invented |
| Official ICD/UCUM release pinning | `BLOCKED` | dataset owner + supply chain decision |

## Program action
Extend offline validator/provenance regressions only. Never fabricate a licensed release or a check-digit result.
