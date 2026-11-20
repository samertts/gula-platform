# P07 — Delivery API, Preferences, and Clinical Gates

Program: GULA-GULS-021
Scope: language-pack delivery, byte-range resume, token handling, stable error codes, preference gating, data-saver/roaming checks, clinical catalog gating, and residual findings M3–M6/M9
Execution branch: `execution/gula-guls-021` in `/tmp/opencode/gula-guls-021`
Evidence directory: `/tmp/opencode/gula-guls-021-evidence`
Date: 2026-11-21
Status: **NOT READY — BLOCKED**

## 1. Boundary

This document is written from the repository's actual code and tests (`backend/app/localization/delivery.py`, `preferences.py`, `clinical.py`, `pack_manager.py`, `backend/app/core/error_contract.py`, `backend/app/factory.py`, `backend/app/routes/localization.py`, `backend/tests/localization/`, `backend/tests/test_error_contract.py`) and from the recorded evidence logs. It is documentation only: no test, build, CI job, merge, deployment, production access, or human approval was performed while writing it. Controls already verified in P00 are not duplicated as new claims.

## 2. Delivery API surface

`create_router()` in `backend/app/localization/delivery.py` mounts `/api/v1/localization`:

| Endpoint                                      | Behavior                                                                                                                                                                                                                                            |
| --------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `GET /languages`                              | Lists all registry entries via `public_dict()` with `installed` and `lifecycle_state` from the `PackManager`; reports `fallback_language="en"`.                                                                                                     |
| `GET /languages/{language_id}/manifest`       | Resolves the registered language, verifies the stored pack, and returns the signed manifest; unknown languages return `LANGUAGE_NOT_FOUND` (404), missing packs `PACK_NOT_AVAILABLE` (404), verification failures `PACK_VERIFICATION_FAILED` (409). |
| `POST /language-packs/{language_id}/download` | Applies locale, approval, installation, network, and storage gates; verifies the pack before issuing a short-lived token; returns download URL, expected size/hash, signature metadata, and `expires_in`.                                           |
| `GET /downloads/{download_id}`                | Returns transport progress after constant-time token comparison.                                                                                                                                                                                    |
| `DELETE /downloads/{download_id}`             | Cancels a session after token comparison; returns `DOWNLOAD_CANCELLED`.                                                                                                                                                                             |
| `GET /downloads/{download_id}/content`        | Serves full bytes or a byte range after token comparison and expiry check.                                                                                                                                                                          |

## 3. Byte-range resume (M3)

`download_content()` parses `Range: bytes=<start>[-<end>]` with a strict full-match regex. Invalid or out-of-range requests return `INVALID_RANGE` (416). Responses set `Cache-Control: no-store`, `Accept-Ranges: bytes`, and a `Content-Range` header for ranged requests, and use HTTP 206 for ranges, 200 otherwise.

Each served range is recorded and merged into `covered_ranges`. Only a merged range beginning at byte 0 counts as delivered: `covered = merged[0][1] + 1 if merged and merged[0][0] == 0 else 0`. A tail-only request therefore yields `downloaded_bytes = 0` and status `DOWNLOADING`; status becomes `COMPLETE` only when the contiguous prefix covers the whole pack. The transport status is deliberately `COMPLETE`/`DOWNLOADING` — `READY` remains reserved for a verified, installed pack in the `PackManager` lifecycle. Evidence: `test_delivery_api.py::test_download_progress_resumes_from_byte_range` (206 prefix + remainder → `COMPLETE`, `progress == 1.0`, `resumable is False`) and `::test_tail_only_range_never_marks_download_complete` (tail-only → `DOWNLOADING`, 0 bytes, resumable). `test_pack_manager.py::test_resumable_download_and_concurrent_guard` and `::test_download_size_mismatch_fails` cover the manager-side resume path and oversized-transfer rejection.

## 4. Token handling and expiry (M9)

`request_download()` uses `secrets.token_urlsafe(18)` for the download ID and `secrets.token_urlsafe(32)` for the token. The record stores `expires_at = time.monotonic() + TOKEN_TTL_SECONDS` with `TOKEN_TTL_SECONDS = 300`. Status, cancel, and content endpoints compare the presented token with `secrets.compare_digest()`; the content endpoint accepts either the `token` query parameter or an `Authorization: Bearer` header. Missing/incorrect tokens return `INVALID_DOWNLOAD_TOKEN` (403). `EXPIRY_GRACE_SECONDS = 5` keeps an expired record briefly so `download_content()` can return the explicit `DOWNLOAD_TOKEN_EXPIRED` (403) before `_purge_expired()` removes it. Evidence: `test_delivery_api.py::test_download_status_and_short_lived_content` (valid token accepted, wrong token → `INVALID_DOWNLOAD_TOKEN`, `cache-control == no-store`) and `::test_progress_requires_download_token` (403 for absent token).

Verification gap: the expired-token branch exists in code (`delivery.py` lines 23–26, 87–94, 238–239) but no test in the 81-test localization suite directly advances time to assert the `DOWNLOAD_TOKEN_EXPIRED` response. This is a code-level fix with indirect test coverage, not an independently asserted control.

## 5. Stable error codes (H2)

All delivery and preference errors are raised as `HTTPException(detail={"code": ..., "message": ...})`. Codes used by the API include `LANGUAGE_NOT_FOUND`, `LANGUAGE_NOT_ACTIVE`, `LOCALE_MISMATCH`, `ALREADY_INSTALLED`, `PACK_NOT_AVAILABLE`, `PACK_VERIFICATION_FAILED`, `DOWNLOAD_BLOCKED_BY_DATA_SAVER`, `DOWNLOAD_BLOCKED_BY_ROAMING`, `INSUFFICIENT_STORAGE`, `DOWNLOAD_NOT_FOUND`, `INVALID_DOWNLOAD_TOKEN`, `DOWNLOAD_TOKEN_EXPIRED`, `INVALID_RANGE`, `DOWNLOAD_CANCELLED`, and `INVALID_FALLBACK_LANGUAGE`.

`stable_http_detail()` in `backend/app/core/error_contract.py` accepts only an exact two-key `{code, message}` mapping with a validated uppercase code (`^[A-Z][A-Z0-9_]{2,63}$`) and a safe one-line message (non-empty, ≤200 characters, no CR/LF/tab/NUL), and only for status < 500. `factory._http_exception_handler()` passes the code through to `build_error_payload(explicit_code=...)`, and the fixed English message is not overwritten by the `detail_ar` compatibility field when an explicit code is present. Evidence: `test_error_contract.py::test_stable_http_detail_is_preserved_only_for_exact_shape`, `::test_factory_handler_preserves_guls_stable_code_without_arabic_override`, `::test_public_http_detail_does_not_echo_structured_or_server_error_details`, `::test_validation_details_omits_submitted_input_values`, plus the delivery tests asserting `response.json()["detail"]["code"]`.

## 6. Preference gating (H1, M4)

`validate_preference()` in `backend/app/localization/preferences.py` requires the requested language to resolve and to satisfy `is_active`, a non-null `locale_tag`, `is_publishable`, `approval_status == "approved"`, and `linguistic_approval_status == "approved"`; otherwise it returns `LANGUAGE_NOT_ACTIVE` (409) or `LANGUAGE_NOT_FOUND` (404). Only English is accepted as fallback (`INVALID_FALLBACK_LANGUAGE`, 422). The effective language remains `en` until the pack reaches `READY`; `download_required` is true when a ready pack is absent and `auto_download` is enabled. Evidence: `test_delivery_api.py::test_preference_rejects_blocked_downloadable_language` (`fa` → 409 `LANGUAGE_NOT_ACTIVE`), `::test_preference_rejects_pending_language`, `::test_preference_rejects_non_english_fallback`, and `::test_preference_stays_english_until_pack_ready`.

The production adapter reuses `accessibility_profiles.preferences["language"]` rather than adding a duplicate table, increments `profile.version`, writes an audit entry, and commits. Residual risk M4 remains: GULS and legacy accessibility share the same preference key, and the in-memory test store has no ETag/`If-Match`; concurrent writers in a multi-writer deployment need explicit optimistic concurrency before production.

## 7. Data-saver, roaming, and storage checks

`DownloadRequest` accepts `data_saver_enabled`, `allow_metered_network`, `roaming`, `allow_roaming`, and `available_storage_bytes` (non-negative). The download endpoint rejects `data_saver_enabled && !allow_metered_network` with `DOWNLOAD_BLOCKED_BY_DATA_SAVER` (409), rejects `roaming && !allow_roaming` with `DOWNLOAD_BLOCKED_BY_ROAMING` (409), and rejects a reported storage capacity below `2 * requiredBytes` with `INSUFFICIENT_STORAGE` (409). Evidence: `test_delivery_api.py::test_download_policy_blocks_data_saver` and the quota check in `test_delivery_api.py::test_download_status_and_short_lived_content`. This is a conservative client-reported check, not a measurement of real device storage.

## 8. Clinical catalog gating (C1, H4, M7, M8)

`request_download()` calls `pack_manager.verify()` before returning a token, so delivery cannot bypass the same governance applied at install. `verify()` calls `validate_pack_governance()` with the manifest catalogs and extracted files. `clinical.py` derives `actual_catalogs` from `catalogs/<name>.json` archive entries, rejects declared/actual mismatch, and applies the clinical approval gate to archive contents; a hidden `catalogs/clinical.json` is therefore rejected. L3/L4 terminology must carry a valid `ApprovalRecord`, with three distinct roles and a documented clinical reviewer for L4. `verify()` also checks manifest file set, per-file SHA-256 and size, `content_size`, `content_hash`, expected hash, and signature. Evidence: `test_clinical_governance.py::test_hidden_clinical_catalog_is_rejected`, `::test_clinical_catalog_gate_uses_archive_contents`, `::test_l4_role_separation_is_enforced_during_pack_governance`, and `test_pack_manager.py::test_clinical_catalog_cannot_be_signed_without_clinical_approval`, `::test_expected_hash_mismatch_is_rejected`.

## 9. Residual risks M3–M6/M9

| ID  | Status                          | Disposition / residual detail                                                                                                                                                                                                                             |
| --- | ------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| M3  | Fixed, with transport semantics | Contiguous-prefix coverage prevents a partial range from being marked `READY`; transport uses `COMPLETE`/`DOWNLOADING`. Clients must still stop treating any transport completion as lifecycle readiness.                                                 |
| M4  | Residual                        | Shared `accessibility_profiles.preferences["language"]` key; no ETag/`If-Match` in the in-memory store. Requires concurrency control before multi-writer production.                                                                                      |
| M5  | Residual                        | Download sessions and pack lifecycle state live in process memory/local files per process (`downloads` dict and `PackManager._state`). Multi-replica production requires shared persistent state.                                                         |
| M6  | Partially mitigated, residual   | Default root moved from `/tmp` to `Path.home() / ".gula" / "language-packs"`; state file is written via tmp + `os.replace`. The state is not cryptographically signed and still relies on OS-level protection; a shared-state design remains outstanding. |
| M9  | Fixed in code, verification gap | Five-second expiry grace and explicit `DOWNLOAD_TOKEN_EXPIRED` path exist, but no focused test directly asserts that branch.                                                                                                                              |

Additional non-blocking review notes carried forward: only ephemeral test keys were used, there is no dynamic-pack installation UI wiring in the clients, and client cache behavior was unversioned before this pass. These do not change the gate outcome.

## 10. Verification evidence (exact commands, exit codes, counts)

| Check / log                    | Exact command                                                                                                                                    | Exit | Recorded result                                                        |
| ------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------ | ---: | ---------------------------------------------------------------------- |
| `backend_pytest_py312`         | `PYTHONPATH=backend /tmp/opencode/gula-guls-020-venv/bin/python -m pytest -q backend/tests/localization backend/tests/test_error_contract.py`    |    0 | `collected 81 items`; `81 passed, 1 warning in 1.43s`                  |
| `backend_pytest_py311`         | `PYTHONPATH=backend python3.11 -m pytest -q backend/tests/localization backend/tests/test_error_contract.py`                                     |    0 | `collected 81 items`; `81 passed, 1 warning in 1.31s`                  |
| `frontend_focused_tests`       | `npx vitest run --passWithNoTests --exclude 'e2e/**' src/guls/guls.test.ts src/guls/offline/offline.test.ts src/i18n/mobileNavResources.test.ts` |    0 | `Test Files  3 passed (3)`; `Tests  24 passed (24)`                    |
| `frontend_typecheck`           | `npx tsc --noEmit -p tsconfig.json --pretty false`                                                                                               |    0 | Empty log                                                              |
| `frontend_lint`                | `npm run lint -- --max-warnings=0`                                                                                                               |    0 | ESLint completed with no findings                                      |
| `frontend_prettier_check`      | `npx prettier --check src/guls/offline/*.ts vite.config.ts`                                                                                      |    0 | `All matched files use Prettier code style!`                           |
| `frontend_full_tests`          | `npm test`                                                                                                                                       |    1 | `1 failed \| 17 passed (18)` files; `2 failed \| 76 passed (78)` tests |
| `frontend_full_tests_baseline` | `npm test` (baseline worktree)                                                                                                                   |    1 | `1 failed \| 15 passed (16)` files; `2 failed \| 54 passed (56)` tests |
| `pr308_checks`                 | `gh pr checks 308`                                                                                                                               |    1 | 10 named failing gates plus generic `test` job; CI red / `UNSTABLE`    |

The full frontend failures at both revisions are the same two `MobileBottomNav.test.tsx` tests (`uses translated labels and marks a nested route as current`, `announces an open menu state`), with the component and test byte-identical at both revisions. Full CI is **red**, and pre-existing baseline failures do not justify a GULS regression claim; they also do not provide a green merge gate. The `ruff format --check` conflict is a separate pre-existing toolchain blocker (exit 1, `pack_manager.py` only), documented in `P01_BACKEND_CORE_REVIEW.md`.

## 11. Conclusion

Delivery, preference, and clinical gates are implemented coherently and covered by the focused suites, with the M3 and M9 code fixes described above. M4 and M5 remain genuine residual risks, M6 is only partially mitigated, and the M9 expiry branch lacks direct test assertion. No merge, deployment, production access, or human linguistic/clinical approval occurred, and CI remains red. Final status: **NOT READY — BLOCKED**.
