# GULS Threat Model

## Trust boundaries

1. Pack distribution server or object store to client device.
2. Client download cache to pack verifier.
3. Pack verifier to local installation directory.
4. Local installed catalog to application runtime.
5. Application runtime to clinical display surface.

The delivery API is auxiliary. A compromised or unavailable delivery service cannot change an already installed pack because installation requires a trusted signature and local verification.

## Threats and mitigations

| Threat | Mitigation | Evidence |
|---|---|---|
| Tampered pack in transit | SHA-256 per file, aggregate content hash, and Ed25519 signature | `test_modified_content_after_signing_is_rejected`, `test_unsigned_or_wrong_key_pack_is_rejected` |
| Malicious archive path traversal | Reject absolute paths, `..`, and unsafe file types before extraction | `test_path_traversal_is_rejected` |
| Executable payload in pack | Allow-list of data-only extensions; deny-list of executable/binary/script extensions | `test_executable_file_is_rejected` |
| Symlink attack | Symlink archive entries are rejected | `PackManager._safe_extract` |
| Archive decompression abuse | 10 MiB per-file and 50 MiB total limits | `test_oversized_file_is_rejected` |
| Malformed manifest | Strict Pydantic validation with `extra="forbid"` | `test_invalid_manifest_is_rejected` |
| Incompatible pack | Engine, direction, script, locale, and language checks | `test_engine_compatibility_is_enforced` |
| Unapproved synthetic content in production | `approval_status` gate and `GULS_ALLOW_SYNTHETIC_PACKS` flag | `test_unapproved_pack_is_rejected_in_production_mode` |
| Downgrade attack | Semantic version comparison rejects lower versions | `test_downgrade_is_rejected` |
| Partial/corrupt download treated as ready | Partial sessions remain `DOWNLOADING`/resumable; only verified packs reach `READY` | `test_resumable_download_and_concurrent_guard`, `test_download_size_mismatch_fails` |
| Download token leakage or replay | Short-lived random token, `no-store`, constant-time comparison | `test_download_status_and_short_lived_content` |
| Data saver/roaming violation | Explicit policy checks before download authorization | `test_download_policy_blocks_data_saver` |
| Raw translation-key leakage | Key validation; empty string on missing key; English fallback | `test_missing_key_never_leaks_raw_key` |
| Clinical value mutation by localization | Protected-field invariant and separate display fields | `test_clinical_values_units_and_identifiers_never_change` |
| Unapproved L4 clinical text | Distinct roles and mandatory clinical reviewer | `test_l4_without_clinical_approval_cannot_be_published` |
| Concurrent install races | In-progress state guard for downloads | `test_resumable_download_and_concurrent_guard` |
| State confusion | Explicit allowed state transitions | `test_explicit_state_transition_is_validated` |

## Residual risks

- The trusted signing key must be protected outside this repository. This implementation contains no private key.
- Font files are allowed because some scripts require them, but each font license and glyph coverage must be reviewed before publication.
- Automated RTL visual regression for complex clinical layouts is not yet available.
- Clinical approval evidence is a human process; code can enforce its presence but cannot create it.

## Security invariants

No script execution, no raw-key leakage, no unapproved pack activation, no clinical value mutation, and no `READY` state before verification and installation.
