# Clinical Terminology Policy

Registry: `backend/app/localization/clinical.py`  
Schemas: `backend/app/localization/pack_schema.py`

## Source of truth

English clinical source text is the authoritative source. Localized strings are display labels only. The following fields are never translated or overwritten:

- `original_value`
- `original_unit`
- `loinc`
- `ucum`
- `code_system`
- `code`
- `result_status`
- patient, lab, encounter, and national identifiers

`ClinicalTerminologyRegistry.assert_unchanged` enforces this invariant in code.

## Content classification

| Class | Meaning | Approval |
|---|---|---|
| L1 | General UI chrome | Translator + linguistic reviewer |
| L2 | Operational healthcare workflow instructions | Translator + linguistic reviewer; domain review recommended |
| L3 | Health education and general medical information | Translator + linguistic reviewer; clinical reviewer required for patient-facing interpretation |
| L4 | High-risk clinical decision content, critical results, dosage, allergy, and consent-critical text | Translator + linguistic reviewer + documented human clinical reviewer; three distinct roles |

No unreviewed machine translation may be used for L3 or L4. Synthetic strings used in tests are marked `synthetic_test_only` and are never publishable.

## Code bindings

Terminology entries may bind translated display text to `loinc`, `ucum`, `code_system`, and `code`. Values must come from authoritative sources. The GULS implementation does not invent codes. A terminology entry with no verified code binding may be used only for L1 UI text.

## Separation of display and data

A translated label such as a localized test name is stored in `translated_display`. The original result, unit, and code remain separate. Formatting functions never mutate stored values. Stable service errors use codes and parameters, not translated sentences.

## Current approval state

- English source terminology: `approved_source`.
- Arabic and Sorani UI catalogs: approved for UI use only; clinical catalogs blocked pending documented human clinical review.
- Iraqi Turkmen and Syriac: blocked pending verified standard, variety, script, and human approval.
- Foreign packs: blocked pending linguistic and clinical review.

No clinical approval is claimed by this implementation.
