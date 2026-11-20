# GULS Coverage Report

Date: 2026-11-20  
Program: GULA-GULS-020  
Base revision: `2ee9e8bcb9d81e9cac6801f5dea9b86d59beaffa`

## Registry coverage

| Language | Internal ID | BCP 47 tag | Class | Active | Publishable | Declared UI coverage | Clinical status |
|---|---|---|---|---|---|---:|---|
| Arabic | `ar` | `ar` | core | yes | yes | 100% | blocked |
| English | `en` | `en` | core | yes | yes | 100% | approved source |
| Kurdish Sorani | `ckb` | `ckb` | core | yes | yes | 58% | blocked |
| Iraqi Turkmen | `PENDING_TURKMEN_IQ` | none | core | no | no | 0% | blocked |
| Syriac | `PENDING_SYRIAC` | none | core | no | no | 0% | blocked |
| Persian | `fa` | `fa-IR` | downloadable | yes | no | 0% | blocked |
| Urdu | `ur` | `ur-PK` | downloadable | yes | no | 0% | blocked |
| Turkish | `tr` | `tr-TR` | downloadable | yes | no | 0% | blocked |
| French | `fr` | `fr-FR` | downloadable | yes | no | 0% | blocked |
| German | `de` | `de-DE` | downloadable | yes | no | 0% | blocked |
| Russian | `ru` | `ru-RU` | downloadable | yes | no | 0% | blocked |
| Chinese (Simplified) | `zh` | `zh-CN` | downloadable | yes | no | 0% | blocked |
| Hindi | `hi` | `hi-IN` | downloadable | yes | no | 0% | blocked |
| Bengali | `bn` | `bn-BD` | downloadable | yes | no | 0% | blocked |

Totals: 14 registry entries; 12 active; 3 publishable; 11 blocked. Publishable entries are `ar`, `en`, and `ckb`; their clinical catalogs remain blocked except English source terminology.

## Existing catalog coverage measured from source

| Source | Catalogs | Leaf strings | Observation |
|---|---|---:|---|
| `frontend-v3/src/i18n/en.ts` | English | 241 | Reference catalog |
| `frontend-v3/src/i18n/ar.ts` | Arabic | 241 | Full parity with English |
| `frontend-v3/src/i18n/ku.ts` | Existing `ku` identifier | 125 | 116 strings missing; identifier is not approved for Sorani |
| `frontend-v3/src/i18n/tk.ts` | Existing `tk` identifier | 125 | 116 strings missing; standard unverified |
| `frontend-v3/src/i18n/syr.ts` | Existing `syr` identifier | 125 | 116 strings missing; standard unverified |
| `platform/ui/i18n/locales/en.json` | English | 138 | Separate legacy runtime |
| `platform/ui/i18n/locales/ar.json` | Arabic | 138 | Full parity inside legacy runtime |

The measured values were produced by counting literal leaf strings in the sources. The 58% registry value for `ckb` is a conservative published-coverage declaration, not a claim that the existing partial `ku` catalog is approved Sorani.

## Dynamic-pack coverage

No production language packs are published by this change. Synthetic only:

- Backend signed-pack verification, delivery, install, update, rollback, and failure tests use `synthetic_test_only` packs with `GULS_ALLOW_SYNTHETIC_PACKS=1`.
- Synthetic packs are rejected when the flag is disabled.
- `fa` is the synthetic fixture language; no foreign-language production translation is claimed.
- No `L4` clinical translation is present in any catalog.

## Test coverage

| Area | Test file | Tests |
|---|---|---:|
| Clinical governance | `backend/tests/localization/test_clinical_governance.py` | 6 |
| Delivery API | `backend/tests/localization/test_delivery_api.py` | 10 |
| Existing runtime compatibility | `backend/tests/localization/test_existing_runtime_compat.py` | 2 |
| Pack manager and safety | `backend/tests/localization/test_pack_manager.py` | 20 |
| Preference compatibility | `backend/tests/localization/test_preference_compat.py` | 2 |
| Registry and runtime | `backend/tests/localization/test_registry_runtime.py` | 25 |
| Frontend GULS runtime/RTL | `frontend-v3/src/guls/guls.test.ts` | 9 |
| Frontend locale identifiers | `frontend-v3/src/i18n/mobileNavResources.test.ts` | 2 |
| Total focused GULS tests (backend) |  | 67 |
| Total focused GULS tests (frontend) |  | 11 |

Focused backend command: `PYTHONPATH=backend python3.11 -m pytest -q backend/tests/localization` — 67 passed.  
Same suite on Python 3.12 venv — 67 passed.  
Focused frontend command: `npx vitest run --passWithNoTests --exclude 'e2e/**' src/guls/guls.test.ts src/i18n/mobileNavResources.test.ts` — 11 passed.  
TypeScript typecheck: `npx tsc --noEmit -p tsconfig.json --pretty false` — passed.  
Frontend lint: `npm run lint` — passed with zero warnings.  
Ruff: `/tmp/opencode/gula-guls-020-venv/bin/ruff check <changed paths>` — all checks passed.

## Known gaps

- No Arabic/Sorani font assets or licenses were found; glyph coverage is not claimed.
- No automated visual regression fixtures were found for mixed-direction clinical tables, PDFs, charts, or printing.
- Web Service Worker/IndexedDB pack caching and mobile/desktop dynamic pack storage are not implemented.
- Full repository regression results and pre-existing failures are recorded in `TEST_EVIDENCE.md`.
