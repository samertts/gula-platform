# GULA Localization API Contracts

Base paths are mounted by `backend/app/factory.py` through `backend/app/routes/localization.py`. All error payloads use a stable `code` in `detail`; messages are fixed English diagnostic strings and are never translated. Backend business errors use stable codes and parameters from `StableMessage` rather than translated prose.

## `GET /api/v1/localization/languages`

Returns the registry projection and current local lifecycle state.

```json
{
  "registry_version": "1.0.0",
  "fallback_language": "en",
  "languages": [
    {
      "language_id": "ckb",
      "locale_tag": "ckb",
      "native_name": "کوردیی ناوەندی",
      "english_name": "Kurdish Sorani",
      "direction": "rtl",
      "script": "Arab",
      "region": "IQ",
      "classification": "core",
      "approval_status": "approved",
      "is_active": true,
      "is_publishable": true,
      "pack_version": "1.0.0",
      "translation_coverage": 0.58,
      "installed": false,
      "lifecycle_state": "NOT_INSTALLED"
    }
  ]
}
```

Pending Turkmen and Syriac entries are returned with `null` locale tag, script, and direction, `is_active: false`, and `is_publishable: false`.

## `GET /api/v1/localization/languages/{language_id}/manifest`

Returns the verified signed manifest for a published pack.

| Condition | Status | Code |
|---|---|---|
| No published pack | 404 | `PACK_NOT_AVAILABLE` |
| Verification/compatibility failure | 409 | `PACK_VERIFICATION_FAILED` |
| Success | 200 | Signed manifest JSON |

## `POST /api/v1/localization/language-packs/{language_id}/download`

Creates a short-lived download authorization. This endpoint is called only after a user explicitly selects the language.

Request:

```json
{
  "locale_tag": "fa-IR",
  "data_saver_enabled": false,
  "allow_metered_network": false,
  "roaming": false,
  "allow_roaming": false,
  "available_storage_bytes": 52428800
}
```

Response:

```json
{
  "download_id": "string",
  "language_id": "fa",
  "pack_version": "1.0.0",
  "download_url": "/api/v1/localization/downloads/{download_id}/content?token=...",
  "expected_size": 12345,
  "expected_hash": "sha256",
  "signature_metadata": {
    "signer_key_id": "gula-release-2026-01",
    "publisher": "GULA National Language Board",
    "signature_present": true
  },
  "expires_in": 300
}
```

Policy failures use stable codes: `LANGUAGE_NOT_FOUND`, `LANGUAGE_NOT_ACTIVE`, `LOCALE_MISMATCH`, `ALREADY_INSTALLED`, `DOWNLOAD_BLOCKED_BY_DATA_SAVER`, `DOWNLOAD_BLOCKED_BY_ROAMING`, `INSUFFICIENT_STORAGE`, `PACK_NOT_AVAILABLE`, and `PACK_VERIFICATION_FAILED`.

## `GET /api/v1/localization/downloads/{download_id}`

Returns progress for a download session: `status`, `downloaded_bytes`, `total_bytes`, `progress`, `last_error`, and `resumable`. A partial download reports `partial_download_resumable` rather than `READY`.

## `GET /api/v1/localization/downloads/{download_id}/content`

Streams the pack with `Cache-Control: no-store`. The short-lived token is compared with `secrets.compare_digest`. Expired or invalid tokens return `DOWNLOAD_TOKEN_EXPIRED` or `INVALID_DOWNLOAD_TOKEN`.

## `PUT /api/v1/users/me/preferences/language`

Stores the preference in the existing `accessibility_profiles.preferences` JSON. No new user-language table or migration is introduced.

Request:

```json
{
  "preferred_language": "fa-IR",
  "fallback_language": "en",
  "auto_download": true
}
```

Response:

```json
{
  "preferred_language": "fa",
  "fallback_language": "en",
  "effective_language": "en",
  "direction": "ltr",
  "lifecycle_state": "NOT_INSTALLED",
  "auto_download": true,
  "download_required": true
}
```

The effective language remains English until the requested pack is installed and `READY`. Any fallback other than `en` returns `INVALID_FALLBACK_LANGUAGE`.

## Stable service messages

`StableMessage` carries `code`, `parameters`, and optional `correlation_id`. `code` must match `[A-Z][A-Z0-9_]{2,63}`. It never carries translated prose. Clients map codes to localized UI catalogs. Missing catalog keys resolve to English; they never leak raw keys.
