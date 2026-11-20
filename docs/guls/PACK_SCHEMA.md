# GULA Language Pack Schema

Canonical schema: `shared/guls/language_pack.schema.json`  
Python model: `backend/app/localization/pack_schema.py`  
Builder: `backend/app/localization/pack_builder.py`  
Verifier: `backend/app/localization/pack_manager.py`

## Archive contract

A language pack is a ZIP archive containing:

- `manifest.json` — signed canonical manifest.
- `catalogs/*.json` — key/value UI catalogs.
- `terminology/*.json` — approved display terminology with source-code bindings.
- `formatting/*.json` — direction, plural, date, and numeric display policy.
- `metadata/*` — approval records and provenance.
- `fonts/*` — licensed font files only.

No executable, script, dynamic library, symlink, absolute path, or `..` path is permitted. Maximum single file size is 10 MiB; maximum unpacked total is 50 MiB.

## Manifest fields

| Field | Contract |
|---|---|
| `schema_version` | Must be `1.0`. |
| `language_id` | Must match the registry entry and the requested language. |
| `locale_tag` | Must exactly match the approved registry BCP 47 tag. |
| `native_name` | Non-empty display name. |
| `fallback_locale` | Must be `en`. |
| `pack_version` | Semantic version. |
| `minimum_engine_version` | Semantic version; installation fails if the engine is older. |
| `direction` | `rtl` or `ltr`; must match the registry. |
| `script` | ISO 15924 script code; must match the registry. |
| `catalogs` | Non-empty list of catalog identifiers defined by the registry. |
| `terminology_version` | Semantic version of the terminology dataset. |
| `content_hash` | SHA-256 over the sorted `path:sha256:size` lines of all non-manifest files. |
| `content_size` | Sum of all non-manifest file sizes. |
| `publisher` | Non-empty publisher identity. |
| `signer_key_id` | Identifier of the trusted Ed25519 signing key. |
| `approval_status` | `approved` or `synthetic_test_only`. |
| `created_at` | ISO 8601 timestamp. |
| `files` | Exact list of path, SHA-256, and size for every non-manifest file. |
| `signature` | Base64 Ed25519 signature over the canonical manifest without this field. |

## Canonical signing payload

The signature covers `json.dumps(manifest_without_signature, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")`. Any change to a manifest field, catalog file, file list, or content hash invalidates verification.

## Verification order

1. Safe archive extraction and file-type/size checks.
2. Strict manifest schema validation.
3. Language, locale, direction, script, and engine compatibility checks.
4. Approval-status gate; synthetic packs require `GULS_ALLOW_SYNTHETIC_PACKS=1`.
5. Per-file SHA-256 and size verification.
6. Aggregate content hash verification.
7. Ed25519 signature verification against the configured public key.

Installation happens only after every step succeeds. The active version changes only after all files are written and fsynced.

## Approval records

`ApprovalRecord` requires translator and linguistic reviewer identity for every class. L4 additionally requires a documented human clinical reviewer and three distinct roles. L4 records without clinical approval are rejected by the model and by the terminology registry.

## Synthetic packs

Synthetic packs are generated only from test fixtures, labelled `synthetic_test_only`, and gated by an environment flag. They are used to prove download, verification, atomic installation, and rollback behavior. They are not approved translations and must not be shipped as product content.
