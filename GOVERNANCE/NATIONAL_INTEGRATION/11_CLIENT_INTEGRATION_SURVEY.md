# WS-06 Survey — Client Integration

**Document:** 11 · **Status:** `TESTED` (contract guards) / `BLOCKED` (real platforms).

## Surface
`backend/app/health_core/client_integration/` (6 modules), `test_client_integration_manifests.py`, `test_client_integration_guards.py`, `test_integration_arabic_rtl_a11y.py`, `test_integration_api_client.py`; frontend contract docs `GOVERNANCE/FRONTEND_INTEGRATION_REPORT.md`.

## Verified evidence (prior cycle, unchanged)
- F-04 fix: `validate_all_manifests` resolves caller observations per platform and passes `observation=`; fail-closed `NO_OBSERVATION_FOR_PLATFORM`.
- Arabic-first RTL and accessibility guards pass.
- 30 client tests; source classification (`FINAL_05_CLIENT_INTEGRATION.md`): `end_to_end_verified = False`. This program records the contract guards as `TESTED`; real device E2E is `BLOCKED`.
- Original decision: 101 classified frontend contract drifts; acceptance is a product/owner decision.

## Gaps
| Gap | Classification | Route |
|---|---|---|
| iOS application | `NOT IMPLEMENTED` | Xcode project absent from checkout (`05` §7) |
| Expo API / real RTL/i18n runtime layer | `BLOCKED` | no platform authorization |
| Real device E2E | `BLOCKED` | no platform/endpoint |
| 101 frontend drift acceptance | `BLOCKED` | Frontend owner decision |

## Program action
Keep manifest guards fail-closed; no demo counted as E2E or production validation.
