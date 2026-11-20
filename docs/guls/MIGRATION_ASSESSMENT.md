# Migration Assessment

Outcome: **No database migration is required.**

## Existing storage reused

`backend/app/models/user_preferences.py` already defines `accessibility_profiles` with a `preferences` JSON object containing a `language` field. The existing API `PUT /user-preferences/accessibility` already persists that field.

The GULS preference endpoint `PUT /api/v1/users/me/preferences/language` writes the following keys into the same JSON object:

- `language`
- `fallback_language`
- `auto_download`

No new table, column, index, or constraint is added. Existing rows remain valid.

## Compatibility changes

`backend/app/routes/user_preferences.py` updates the `AccessibilityLanguage` literal to the set of active registry identifiers (`ar`, `en`, `ckb`, plus the dynamic-pack languages `fa`, `ur`, `tr`, `fr`, `de`, `ru`, `zh`, `hi`, `bn`) and changes the default from `ar` to `en`. A `field_validator` maps retired identifiers (`ku` to `ckb`, `tk` and `syr` to `en`) before schema validation.

Rationale:

- `ku` is not the approved Sorani identifier; `ckb` is.
- `tk` and `syr` do not have verified standards in this program.
- English is the mandatory fallback and predictable default.

The legacy accessibility endpoint and GULS preference endpoint write to the same JSON keys. The GULS endpoint rejects blocked/unpublishable registry entries with `409 LANGUAGE_NOT_ACTIVE`. To avoid a legacy endpoint returning HTTP 500 on profiles that contain GULS keys:

- `AccessibilityResponse` ignores extra keys (`extra="ignore"`).
- `PUT /user-preferences/accessibility` preserves `fallback_language` and `auto_download` when updating the profile.

These are application-level compatibility adjustments only. No database schema is changed.

## Pack metadata

Pack lifecycle state is stored in a local filesystem state file under `GULS_LOCAL_PACK_ROOT`. It is deployment state, not operational database state. No Alembic revision is added.

## Rollout sequence

1. Deploy code and registry data.
2. Configure trusted signing public key and pack distribution root.
3. Update clients to use GULS preference endpoint.
4. Migrate existing `ku` values to `ckb` in the client after user confirmation.
5. Do not migrate `tk`/`syr` values until their standards are approved.

## Reversal

Removing the code leaves the existing accessibility profile JSON intact. No data cleanup is required.
