# Translation Key Conventions

Canonical validation: `TRANSLATION_KEY_RE` in `backend/app/localization/runtime.py` and `TRANSLATION_KEY` in `frontend-v3/src/guls/runtime.ts`.

## Syntax

```text
^(ui|action|label|message|error|clinical)\.[a-z0-9_]+(?:\.[a-z0-9_-]+){0,4}$
```

Examples:

- `ui.home`
- `action.save_record`
- `label.patient_identifier`
- `error.patient_not_found`
- `clinical.allergy_warning`

Keys are lowercase, stable, and semantic. They are never clinical identifiers, LOINC/UCUM/ICD codes, national IDs, or patient data.

## Namespaces

| Namespace | Use | Clinical review |
|---|---|---|
| `ui` | Navigation, layout, buttons, static screen text | L1 |
| `action` | Operation labels | L1 |
| `label` | Field and column labels | L1/L2 depending on meaning |
| `message` | Confirmation and informational text | L1/L2 |
| `error` | Stable error codes mapped to localized catalog text | L1/L2 |
| `clinical` | Display text for clinical concepts | L3/L4 |

## Rules

1. A key identifies meaning, not English wording. Do not encode English sentences in key names.
2. Parameters use `{name}` placeholders. Translators may reorder them. Parameter values are never translated.
3. A missing key resolves to the English catalog. If neither catalog contains the key, the UI renders empty text; it never renders the raw key.
4. Strict mode raises `MissingTranslationError` for build-time catalog validation.
5. Adding a key to a non-English catalog without adding it to English is invalid.
6. Clinical keys require an approval record and terminology binding before publication.
7. Key renames are breaking changes and require catalog migration in the same release.

## Backend error codes

Backend services return `StableMessage` objects containing a code such as `PATIENT_NOT_FOUND` and parameters such as `{"id": "SYNTHETIC-1"}`. The UI maps the code through the `error` namespace. This keeps logs, APIs, and audits language-independent.
