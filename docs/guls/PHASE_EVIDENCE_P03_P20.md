# P03–P20 Phase Evidence

Date: 2026-11-20  
Program: GULA-GULS-020  
Branch: `execution/gula-guls-020`  
Base revision: `2ee9e8bcb9d81e9cac6801f5dea9b86d59beaffa`

## How to read this document

P00–P02 are recorded in `P00_BASELINE_AND_PRESERVATION.md`, `P01_ARCHITECTURE_AND_GAP_ANALYSIS.md`, and `P02_ARCHITECTURE_DECISIONS.md`. This document records the remaining work packages P03–P20 and maps each to the concrete artifacts and verification evidence produced in the isolated branch. Phase labels follow the program work breakdown; where a capability is intentionally not implemented or remains blocked, the status column states that explicitly rather than implying completion.

## Evidence matrix

| Phase | Work package | Artifacts | Verification | Status |
|---|---|---|---|---|
| P03 | Central language registry with BCP 47 validation | `shared/guls/language_registry.json`, `shared/guls/language_registry.schema.json`, `backend/app/localization/language_registry.py`, `frontend-v3/src/guls/registry.ts`, `docs/guls/LANGUAGE_REGISTRY_SCHEMA.md` | `registry_schema_validation=PASS languages=14`; registry/runtime tests (25); `test_registry_contains_five_core_entries`; `test_bcp47_subset_validation`; `test_registry_load_rejects_malformed_entries` | Complete |
| P04 | Core local languages (`ar`, `en`, `ckb`) and English fallback | `backend/app/localization/runtime.py`, `frontend-v3/src/guls/runtime.ts`, `backend/app/platform/i18n.py`, `frontend-v3/src/i18n/index.ts`, `frontend-v3/src/i18n/locales.ts` | Existing-runtime tests (2); frontend runtime tests; `test_backend_i18n_uses_english_fallback_for_unknown_locale`; locale identifier test; catalog counts in `COVERAGE_REPORT.md` | Complete for approved identifiers; Sorani catalog coverage declared at 58% |
| P05 | RTL/LTR standard and formatting | `frontend-v3/src/guls/rtl.ts`, `docs/guls/RTL_LTR_STANDARD.md` | `directionFor` tests, `containerAttributes`, `logicalDirectionStyles`, digit/date/number formatting tests | Complete for text and layout helpers; font assets unresolved |
| P06 | Key conventions and terminology policy | `docs/guls/KEY_CONVENTIONS.md`, `docs/guls/TERMINOLOGY_POLICY.md`, translation-key regex in backend and frontend runtime | `is_valid_translation_key` tests; snake_case key acceptance; no raw-key leakage test | Complete |
| P07 | Signed pack schema and key management | `shared/guls/language_pack.schema.json`, `backend/app/localization/pack_schema.py`, `tools/guls_sign_pack.py`, `docs/guls/PACK_SCHEMA.md`, `docs/guls/SIGNING_KEY_MANAGEMENT.md` | `pack_schema_validation=PASS approval_status=synthetic_test_only`; signature/hash tests; ruff and py_compile | Complete; no production key generated or used |
| P08 | Pack lifecycle, atomic install, rollback | `backend/app/localization/pack_manager.py` | Lifecycle-state tests (20), including atomic swap, stale-directory recovery, previous-version preservation, blocked-pack rejection, hash mismatch, compatibility failure | Complete |
| P09 | Secure delivery API and download controls | `backend/app/localization/delivery.py`, `backend/app/routes/localization.py` | Delivery tests (10): progress, byte-range resume, cancellation, expiry purge, unknown-language 404, token validation, network policy checks | Complete for service-level delivery; CDN/storage integration is deployment-scoped |
| P10 | Language preference API and legacy compatibility | `backend/app/localization/preferences.py`, `backend/app/routes/user_preferences.py`, `docs/guls/MIGRATION_ASSESSMENT.md` | Preference tests in delivery suite; `test_preference_compat.py` (2); legacy accessibility regression (5) | Complete; shared-key HTTP 500 issue resolved |
| P11 | Frontend dynamic-pack selection runtime | `frontend-v3/src/guls/`, `frontend-v3/src/types/api.ts`, `frontend-v3/src/i18n/` | Focused frontend suite: 11 passed; TypeScript typecheck and lint passed | Complete at runtime/type level; no UI component for pack download was added |
| P12 | Clinical terminology and L1–L4 approval gating | `backend/app/localization/clinical.py`, `docs/guls/APPROVAL_WORKFLOW.md`, `docs/guls/TERMINOLOGY_POLICY.md` | Clinical governance tests (6); signed-path governance test; L4 approval record test | Complete as enforcement; all L4 and all clinical catalogs remain blocked pending human approval |
| P13 | Offline usage | `docs/guls/OFFLINE_GUIDE.md`, pack manager local state | Pack lifecycle works from local installed catalogs; no service worker or IndexedDB tests | Partial by design; web offline caching and mobile/desktop pack storage not implemented |
| P14 | Threat model and security controls | `docs/guls/THREAT_MODEL.md`, pack manager path/signature/size checks, delivery token checks | Adversarial tests: unsafe archive, path traversal, symlink, signature mismatch, hash mismatch, malformed public key | Complete for implemented surface; no penetration test performed |
| P15 | Approval workflow and governance | `docs/guls/APPROVAL_WORKFLOW.md`, `docs/guls/SIGNING_KEY_MANAGEMENT.md` | Governance enforcement tests in P08/P12; no human approval claimed | Complete as documented workflow and code enforcement |
| P16 | API contracts and registry/pack documentation | `docs/guls/API_CONTRACTS.md`, `docs/guls/LANGUAGE_REGISTRY_SCHEMA.md`, `docs/guls/PACK_SCHEMA.md` | Route wiring verified in `backend/app/factory.py`; API tests in delivery suite | Complete |
| P17 | Test evidence | `docs/guls/TEST_EVIDENCE.md`, `docs/guls/COVERAGE_REPORT.md` | Exact commands and outputs recorded; 67 backend tests, 11 frontend tests, static checks | Complete with documented full-frontend baseline failure |
| P18 | Migration assessment | `docs/guls/MIGRATION_ASSESSMENT.md` | No Alembic revision added; existing `accessibility_profiles.preferences` reused; compatibility tests | Complete; no database migration required |
| P19 | Deployment and rollback guidance | `docs/guls/DEPLOYMENT_GUIDE.md`, `docs/guls/ROLLBACK_GUIDE.md`, `docs/guls/SIGNING_KEY_MANAGEMENT.md` | Procedures documented; no production deployment performed | Complete as documentation only |
| P20 | Final report and draft PR gate | `docs/guls/FINAL_REPORT.md`, this document | Gate review against all verification outputs; Draft PR opened only if gates pass | Complete |

## Consolidated gate status

| Gate | Result |
|---|---|
| Focused backend tests (3.11 and 3.12) | 67 passed |
| Focused frontend tests | 11 passed |
| Legacy accessibility regression | 5 passed |
| TypeScript typecheck | passed |
| Frontend lint | passed, zero warnings |
| Ruff | all checks passed |
| Python compile (3.12) | passed |
| JSON schema validation | registry 14 languages; pack synthetic fixture passed |
| Full frontend suite | 2 pre-existing failures in unmodified `MobileBottomNav.test.tsx`; documented, not a GULS regression |
| Protected workspace | unchanged |
| Human linguistic/clinical approval | not claimed; blocked languages and L4 remain gated |

## Explicitly not claimed

- Iraqi Turkmen and Syriac language standards or scripts.
- Any L4 clinical translation or clinical decision use of unreviewed machine translation.
- Production signing key generation, rotation, or use.
- Web Service Worker/IndexedDB pack caching and mobile/desktop dynamic pack storage.
- Arabic/Sorani font asset coverage or licensing.
- Production deployment, database access, merge, or human approvals.
