# P01 - Architecture and Gap Analysis

## Scope inspected

frontend-v3, platform/ui, packages/uap, backend platform i18n, backend national language reference entity, shared localization helper, existing user-preference API and schema, Android string resources, migration names, localization-related tests, and Arabic localization audit documentation.

## Confirmed duplication

Four independent language runtimes exist:

1. `frontend-v3/src/i18n/index.ts` (i18next).
2. `platform/ui/i18n/i18n.ts` + `I18nProvider.tsx` (custom).
3. `packages/uap/src/runtime/i18n/index.ts` (Zustand).
4. `backend/app/platform/i18n.py` (service registry).

`shared/localization.py` adds a fifth file-based helper. These implementations disagree on supported identifiers, fallback behavior, and missing-key behavior.

## Identifier inconsistencies

| System | Identifiers observed | Issue |
|---|---|---|
| frontend-v3 | `ar`, `en`, `ku`, `tk`, `syr` | Uses `ku` instead of approved `ckb`; `tk`/`syr` standards unapproved. |
| platform/ui | `ar`, `en` | No Sorani or foreign languages. |
| UAP | `ar`, `en`, `ku`, `tr`, `fa`, `ckb` | Includes foreign languages without catalogs; mixes `ku` and `ckb`. |
| backend i18n | `ar`, `en`, `ku`, `ckb` | No `tk`/`syr`; unknown locale fell back to Arabic. |
| user preferences | `ar`, `en`, `ku`, `tk`, `syr` | Does not include `ckb`; stores identifier in accessibility JSON. |

## Coverage findings

- frontend-v3 Arabic/English catalogs: 241 leaf strings each, no missing-key difference between the pair.
- frontend-v3 Sorani, Turkmen, Syriac catalogs: 125 leaf strings each; 116 keys missing relative to Arabic/English.
- platform/ui Arabic/English catalogs: 138 keys each.
- No localized catalog files were found for `fa`, `ur`, `tr`, `fr`, `de`, `ru`, `zh`, `hi`, or `bn`.
- Only one localization-specific test file was found: `frontend-v3/src/i18n/mobileNavResources.test.ts`.

## RTL/LTR findings

- frontend-v3 uses `dir` through locale metadata; logical CSS usage was not consistently evidenced.
- platform/ui sets `document.documentElement.dir` and a wrapper `dir`, but only distinguishes Arabic from everything else.
- UAP declares `tk` as LTR and `syr` implicitly LTR without approved standards.
- No font assets were found in the tree; font licensing and glyph coverage remain unresolved.
- No automated tests were found for mixed-direction medical identifiers, decimals, units, tables, charts, forms, PDFs, printing, or screen readers.

## API and database findings

- No `/api/v1/localization/` routes exist.
- `accessibility_profiles` already stores a language preference in JSON; a new `user_language_preferences` table would duplicate existing capability.
- `ref_languages` exists as a reference entity but lacks the fields required for pack lifecycle, direction as an enum, engine compatibility, approval, and terminology version.
- No migration was added for GULS. Additive schema work is deferred pending compatibility review; this implementation adds no database migration.

## Delivery and offline findings

- No existing CDN/object-storage abstraction was found for language packs.
- No resumable download, signature verification, checksum verification, safe archive extraction, atomic installation, or rollback implementation exists.
- Web storage uses localStorage for the locale code only; no IndexedDB or Service Worker pack cache was found.
- Android contains default and Arabic string resources only; no dynamic-pack mechanism exists.
- iOS and desktop language-pack storage were not found in the inspected tree.

## Clinical localization findings

- No centralized clinical terminology localization registry exists.
- No evidence of LOINC/UCUM/ICD binding for translated display text.
- No approval-role separation or L1-L4 content classification workflow exists.
- Existing machine-generated or partial catalogs must not be treated as approved clinical content.

## Reuse decisions

1. Keep i18next in frontend-v3; add a GULS adapter beside it rather than replacing it.
2. Reuse `accessibility_profiles.preferences` for language preference storage.
3. Reuse FastAPI/Pydantic for delivery and preference APIs.
4. Reuse `cryptography` for Ed25519 verification and `zipfile` for safe data-only archives.
5. Reuse `arabic-reshaper` and `python-bidi` for display-only shaping; never mutate stored strings.
6. Treat existing Sorani catalogs as UI-only partial coverage; do not claim clinical approval.
7. Treat existing Turkmen and Syriac catalogs as unverified pending standards; do not publish them as core approved packs.

## Gate outcome

The coverage map is established and no unresolved conflict blocks the additive foundation. Turkmen/Syriac standards, font licensing, and clinical approvals remain explicit blockers for their publication, not for the architecture.
