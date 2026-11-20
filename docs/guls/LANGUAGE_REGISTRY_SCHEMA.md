# Language Registry Schema

Canonical file: `shared/guls/language_registry.json`  
JSON Schema: `shared/guls/language_registry.schema.json`  
Loader: `backend.app.localization.language_registry.LanguageRegistry`

## Top-level fields

| Field | Type | Contract |
|---|---|---|
| `registry_version` | string | Semantic version of the registry format. |
| `engine_compatibility` | string | Supported runtime engine range. |
| `fallback_language` | string | Must be `en`. |
| `languages` | array | Language definitions; at least five entries. |

## Language fields

| Field | Contract |
|---|---|
| `language_id` | Stable internal identifier; not assumed to equal a locale tag. |
| `locale_tag` | Validated BCP 47 subset or `null` while a standard is pending. |
| `native_name` | Native display name or `null` when unapproved. |
| `english_name` | English display name. |
| `language` | Language name, separate from dialect. |
| `dialect` | Dialect or `null`. |
| `region` | Two-letter region or three-digit region, or `null`. |
| `script` | Four-letter ISO 15924 script code or `null`. |
| `direction` | `rtl`, `ltr`, or `null` while unapproved. |
| `classification` | `core` or `downloadable`. |
| `is_active` | Whether the language may be selected/installed. |
| `is_publishable` | Whether a pack may be published. |
| `approval_status` | `approved`, `blocked`, or `synthetic_test_only`. |
| `linguistic_approval_status` | `approved` or `blocked`. |
| `clinical_approval_status` | `approved`, `approved_source`, or `blocked`. |
| `pack_version` | Semantic version of the registered pack. |
| `minimum_engine_version` | Minimum compatible engine version. |
| `translation_coverage` | Number from 0 to 1. |
| `terminology_version` | Semantic version or `null`. |
| `catalogs` | Catalog identifiers included in the pack. |
| `notes` | Human-readable approval and safety notes. |

## Core entries

`ar`, `en`, and `ckb` are active and publishable for UI catalogs. `PENDING_TURKMEN_IQ` and `PENDING_SYRIAC` are explicit placeholders with `null` locale tag, script, direction, and native name. They are not installable and not publishable.

## Foreign entries

`fa`, `ur`, `tr`, `fr`, `de`, `ru`, `zh`, `hi`, and `bn` have validated BCP 47 locale tags and directions. Their catalogs remain blocked until reviewed. Synthetic packs are permitted only in test environments.

## Compatibility rules

- Adding a new language must not change existing `language_id` values.
- A language may not become active without an approved locale tag and direction.
- Any change to `fallback_language` other than `en` is rejected by the loader.
- The loader rejects duplicate `language_id` values and invalid locale tags.
