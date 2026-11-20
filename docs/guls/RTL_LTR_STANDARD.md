# RTL/LTR Standard

Direction is registry data, not inferred from a string. `backend/app/localization/runtime.py` and `frontend-v3/src/guls/runtime.ts` implement the same resolution contract.

## Direction source of truth

- `ar`: `rtl`, script `Arab`.
- `en`: `ltr`, script `Latn`, mandatory fallback.
- `ckb`: `rtl`, script `Arab`, Sorani.
- `PENDING_TURKMEN_IQ` and `PENDING_SYRIAC`: direction `null` until verified; they resolve to English display behavior and cannot be activated.
- Downloadable languages use their registry direction only; they do not become effective until a verified pack is `READY`.

## Frontend requirements

1. Set `dir` and `lang` from the resolved language (`containerAttributes` in `frontend-v3/src/guls/rtl.ts`).
2. Use logical CSS properties: `margin-inline-start`, `padding-inline-end`, `inset-inline-start`, `text-align: start`, and `border-inline-start`.
3. Avoid physical `left`/`right`, `margin-left`/`margin-right`, and `padding-left`/`padding-right` in localized components.
4. Do not mirror icons, charts, medical diagrams, or result tables globally. Mirror only when the semantic meaning is directional.
5. Use bidi isolation for values such as identifiers, lab codes, and file names.

## Display formatting

- Arabic/Sorani digits may be used for display numbers through `format_number`.
- Identifiers are returned unchanged by `format_identifier`.
- Dates and numeric values are display-only transformations. Stored values remain ISO strings or original numeric values.
- `shape_for_display` uses `arabic-reshaper` and `python-bidi` only for visual presentation. It must never mutate stored content.

## Forbidden behavior

- Character-level reversal of strings by application code.
- Global CSS `transform: scaleX(-1)` on entire screens containing clinical data.
- Translating patient names, lab identifiers, medication codes, units, or reference ranges.
- Treating an unapproved locale tag as evidence of a script or direction.

## Verification evidence

Focused tests cover direction resolution, number formatting, identifier preservation, ISO date preservation, display shaping without mutation, logical CSS helpers, and container attributes. Automated visual regression for mixed-direction tables, PDFs, and charts remains a future gate because no baseline fixtures were found in the repository.
