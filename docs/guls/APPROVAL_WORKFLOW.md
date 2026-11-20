# Language Approval Workflow

## Registry approval

A language becomes selectable only after all of the following are recorded:

1. Stable internal `language_id`.
2. Verified BCP 47 `locale_tag` or an explicit `null` placeholder.
3. Verified language, dialect, region, and ISO 15924 script.
4. Verified `direction`.
5. Linguistic approval identity and date.
6. Clinical approval status appropriate to the catalogs included.

Iraqi Turkmen and Syriac remain blocked because items 2–5 are not verified. Kurmanji can be added later as a separate registry entry with its own verified tag and script; it does not reuse `ckb`.

## Catalog approval

| Step | Owner | Evidence |
|---|---|---|
| Draft translation | Translator | Source keys, translated strings, terminology version |
| Linguistic review | Linguistic reviewer | Approval record with distinct identity |
| Clinical review | Clinical reviewer | Required for L3/L4; mandatory and distinct for L4 |
| Technical validation | Release engineering | Schema, signature, completeness, coverage, safe archive |
| Publication | Release authority | Signed pack and release manifest |

`ApprovalRecord` enforces distinct roles and rejects L4 without a clinical reviewer. Role identities are stored; no approval may be inferred from a commit, file name, or automated test.

## Pack publication

1. Build with `tools/guls_sign_pack.py` using a protected Ed25519 key.
2. Mark approved content `approved`; mark synthetic verification fixtures `synthetic_test_only`.
3. Publish to the configured pack distribution root.
4. Confirm the API manifest endpoint verifies the pack.
5. Enable installation only after the signature key is trusted in the target environment.

Synthetic packs cannot be installed when `GULS_ALLOW_SYNTHETIC_PACKS=0`.

## Change control

Any change to a clinical string, terminology version, direction, script, or locale tag requires a new approval record and a new pack version. Downgrades are rejected. Withdrawal requires disabling the registry entry or removing the distribution artifact, not editing an installed pack in place.

## Current blockers

- Turkmen standard, dialect, and script: unverified.
- Syriac variety and script: unverified.
- Arabic/Sorani clinical catalogs: human clinical approval not documented.
- Font licensing and glyph coverage: not evidenced by repository assets.
