# P04 — Language Standards and Registry Findings

Program: GULA-GULS-021
Scope: Standards research and read-only review of `shared/guls/language_registry.json` and frontend legacy mappings
Baseline: `main` at `2ee9e8bcb9d81e9cac6801f5dea9b86d59beaffa`
Review date: 2026-11-21
Status: **NOT READY — BLOCKED**

## 1. Purpose and authority

This document records the authoritative standards findings for the GULS-021 correction pass and the current state of the shared language registry. It is based on the evidence brief `CONTEXT.md` (section "Standards research (P04)") and read-only inspection of the registry and `frontend-v3/src/i18n/locales.ts`.

No new language was approved, no registry entry was activated, no human linguistic or clinical approval was obtained, and no merge or production action is claimed.

## 2. Authoritative standards findings

Sources consulted in the research summarized by the evidence brief: IANA Language Subtag Registry file dated **2026-11-18**, **RFC 5646**, **SIL ISO 639-3**, **ISO 639-3 change request 2020-039**, **ISO 15924**, Unicode **Blocks.txt**, CLDR **likelySubtags.xml**, and Google Fonts **METADATA/licences** files.

### 2.1 Turkmen

| Question            | Finding                                                                                                                                                        |
| ------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Short code          | `tk` is the correct ISO 639-1 / BCP 47 code for Turkmen.                                                                                                       |
| Three-letter code   | `tuk` is the ISO 639-3 code for Turkmen.                                                                                                                       |
| `tki`               | Rejected on **2024-10-15** (ISO 639-3 change request 2020-039). It must not be used as a language identifier.                                                  |
| Iraqi-specific code | No Iraq-specific ISO 639 or IANA-registered language code exists.                                                                                              |
| Candidate tags      | `tk-IQ`, `tk-Arab-IQ`, and `tk-Latn-IQ` are well-formed BCP 47 strings from registered subtags, but well-formedness is not registration or community approval. |
| CLDR                | CLDR has only `tk → tk_Latn_TM` (Latin script, Turkmenistan). It does not resolve the Iraqi script or community choice.                                        |
| Decision status     | Script and community choice remain **human-blocked**. The registry placeholder must not be activated on the basis of these candidates alone.                   |

### 2.2 Syriac

| Question         | Finding                                                                                                                                                                   |
| ---------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Macrolanguage    | `syr` is an ISO 639 macrolanguage, not a specific approved variety.                                                                                                       |
| Individual codes | `aii` (Assyrian Neo-Aramaic), `cld` (Chaldean Neo-Aramaic), and `syc` (Syriac) are individual codes.                                                                      |
| Scripts          | ISO 15924 registers `Syrc`, `Syre`, `Syrj`, and `Syrn`.                                                                                                                   |
| Decision status  | East/West Syriac variety and script selection remain **human/community-blocked**. No Syriac variant may be published until a documented specialist decision records both. |

### 2.3 Kurdish

| Question       | Finding                                                                                                                                                       |
| -------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Sorani         | `ckb` is confirmed; CLDR maps `ckb → ckb_Arab_IQ`. This is the initial approved Kurdish registry entry.                                                       |
| Kurmanji       | `kmr` is confirmed as a distinct code. It must be added, if ever, as a separate registry entry with its own verified tag and script; it must not reuse `ckb`. |
| Legacy mapping | `frontend-v3/src/i18n/locales.ts` maps legacy `ku → ckb`. This is a compatibility mapping, not a standards decision about Kurmanji.                           |

### 2.4 CLDR and Unicode scope

CLDR likely-subtag data provides useful default mappings (`tk → tk_Latn_TM`, `ckb → ckb_Arab_IQ`) but does not approve a community, dialect, or clinical translation. Unicode blocks and ISO 15924 script codes establish that characters and scripts exist; they do not approve a locale for publication. IANA/RFC 5646 well-formedness is necessary but not sufficient.

### 2.5 Fonts (standards input only)

Free/OFL font candidates identified by the research are **Noto Naskh Arabic**, **Noto Sans Arabic**, **Noto Kufi Arabic**, **Noto Sans**, and **Noto Sans Syriac/Eastern/Western**. These come from Google Fonts METADATA/licence information. Font assets and licence files still require deployment verification; no font binaries or licence files were found in the repository during this review. See `P08_I18N_RTL_AND_FONTS.md` for the cross-surface font assessment.

## 3. Shared registry state

`shared/guls/language_registry.json` (schema `language_registry.schema.json`) contains **14 entries**:

| Group                     | Entries                                                          | State                                                                                                                                                                                                                                                                |
| ------------------------- | ---------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Core, active, publishable | `ar`, `en`, `ckb`                                                | `is_active: true`, `is_publishable: true`, `approval_status: approved`, `linguistic_approval_status: approved`; English is the mandatory fallback and source language. Arabic and Sorani clinical catalogs are still `blocked`; only their UI catalogs are approved. |
| Inactive placeholders     | `PENDING_TURKMEN_IQ`, `PENDING_SYRIAC`                           | `locale_tag: null`, `script: null`, `direction: null`, `is_active: false`, `is_publishable: false`, all approvals `blocked`, coverage 0.0. They are placeholders only.                                                                                               |
| Downloadable, blocked     | `fa`, `ur`, `tr`, `fr`, `de`, `ru`, `zh`, `hi`, `bn` (9 entries) | `is_active: true` but `is_publishable: false`, `approval_status: blocked`, `linguistic_approval_status: blocked`, `clinical_approval_status: blocked`, coverage 0.0. Synthetic test packs only until reviewed and published.                                         |

Registry consequences:

- Only `ar`, `en`, and `ckb` may be selected as an approved local language or used as a publishable pack target.
- Turkmen and Syriac must remain inactive with `null` locale tags until documented human decisions establish tag, dialect, region, script, and direction.
- Downloadable languages are blocked/unpublishable. The corrected preference endpoint rejects them unless active, publishable, locale-assigned, and both linguistically and overall approved.
- `frontend-v3/src/i18n/tk.ts` and `frontend-v3/src/i18n/syr.ts` contain legacy strings, but `frontend-v3/src/i18n/index.ts` exposes only `ar`, `en`, and `ckb` (the Sorani resource under `ckb`). The legacy `tk`/`syr` identifiers normalize to `en` in `locales.ts`; those legacy catalogs are unverified and must not be published as core packs.

## 4. Human-approval blockers

The standards findings resolve code syntax only. They do not resolve any of the following, all of which remain blockers:

1. Turkmen dialect/script/community choice and a documented linguistic approval identity/date.
2. Syriac variety and script choice and a documented specialist linguistic approval identity/date.
3. Documented human clinical approval for Arabic and Sorani clinical catalogs (currently `blocked` in the registry).
4. L4 role separation: translator, linguistic reviewer, and clinical reviewer must be three distinct recorded identities; no approval may be inferred from a commit, file name, or automated test.
5. Font asset licence and glyph/shaping verification for each approved script (see P08).

No approval of any of these items occurred during GULS-021.

## 5. Verification evidence

| Check                         | Command                                                                                                                                       | Exit | Result                              | Log                                                   |
| ----------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------- | ---: | ----------------------------------- | ----------------------------------------------------- |
| Registry JSON schema          | `python3.11 -c 'import json,jsonschema; ... jsonschema.validate(...)'` (system Python 3.11 because `jsonschema` is absent from the GULS venv) |    0 | `registry_schema=PASS languages=14` | `registry_schema.log`, `P00_INDEPENDENT_REVIEW.md` §6 |
| Focused backend, Python 3.12  | `PYTHONPATH=backend /tmp/opencode/gula-guls-020-venv/bin/python -m pytest -q backend/tests/localization backend/tests/test_error_contract.py` |    0 | 81 passed, 1 warning                | `backend_pytest_py312.log`                            |
| Focused backend, Python 3.11  | `PYTHONPATH=backend python3.11 -m pytest -q backend/tests/localization backend/tests/test_error_contract.py`                                  |    0 | 81 passed, 1 warning                | `backend_pytest_py311.log`                            |
| Ruff lint on touched Python   | `/tmp/opencode/gula-guls-020-venv/bin/ruff check ...`                                                                                         |    0 | All checks passed                   | `ruff_check_touched.log`                              |
| PR #308 checks (context only) | `gh pr checks 308`                                                                                                                            |    1 | 10 failing checks; `UNSTABLE`       | `pr308_checks.log`                                    |

Evidence note: the first automated invocation exited 1 because `jsonschema` is absent from the GULS virtual environment. `registry_schema_rerun.log` records the corrected system-Python-3.11 invocation at exit 0 with `registry_schema=PASS languages=14`. Both the original and corrected exit codes are retained in `summary.txt`; the corrected rerun is the authoritative schema-validation result.

`ruff format --check` on the touched Python set exits 1 for a pre-existing toolchain conflict (Ruff 0.16.10 with `target-version=py314` rewrites a parenthesized `except (ValueError, TypeError):` into syntax invalid on Python 3.11/3.12). The parenthesized form was intentionally retained; see `P00_INDEPENDENT_REVIEW.md` §6.

## 6. Residual risks and blockers

- Registry entries for Turkmen and Syriac are placeholders; publishing either without human standards decisions would be unsupported.
- Downloadable languages remain unpublishable; any UI or preference path must continue to enforce the registry gates.
- Legacy `tk`/`syr` resources remain in the frontend source but are not selectable; accidental re-exposure would mislead users.
- No human linguistic or clinical approval is claimed; clinical catalogs for Arabic and Sorani remain blocked.
- CI remains red; no merge, production, or national readiness is implied.

**Final status: NOT READY — BLOCKED**
