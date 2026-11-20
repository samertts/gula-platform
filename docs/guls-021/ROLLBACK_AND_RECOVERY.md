# Rollback and Recovery

Program: GULA-GULS-021
Date: 2026-11-21
Status: **NOT READY — BLOCKED**

## 1. Scope

This document records rollback and recovery mechanisms that exist in the GULS-021 branch and the procedures for preserving the work itself. It is documentation only: no rollback was executed against production, staging, a database, or a deployed client. The authoritative gate record is `FINAL_ACCEPTANCE_REPORT.md`.

## 2. Backend atomic install and previous-version preservation

Implementation: `backend/app/localization/pack_manager.py`.

1. **Verify before write.** `PackManager.install()` calls `verify()` first. Signature, manifest file set, per-file SHA-256 digest, content size, content hash, governance, and archive safety are checked before any filesystem change.
2. **Reject downgrades.** If `current_active` exists and the requested `pack_version` is lower, `CompatibilityError("language-pack downgrade is not permitted")` is raised.
3. **Stage and fsync.** `_write_pack()` writes all payload files into `.staging-<version>-<token>`, flushes and `fsync`s each file, then renames the staging directory into `packs/<language>/<version>`.
4. **Restore on swap failure.** If a target version already exists, it is moved to `.backup-<version>-<token>` before the swap. If the swap fails, the backup is renamed back to the target and the staging directory is removed.
5. **Preserve the previous version.** On success, `state.json` records `previous_version = current_active`, `active_version = manifest.pack_version`, and `state = READY`.
6. **Failure path.** Any exception during the state transitions or write restores `active_version` to `current_active` and sets state to `READY` when a previous active version existed, otherwise `FAILED`. The active files were never replaced on this path.
7. **Crash-consistent state file.** `_save_state()` writes `state.json.tmp`, flushes and `fsync`s it, then uses `os.replace()` for atomic replacement.
8. **Manual restore.** `PackManager.rollback(language_id)` promotes `previous_version` to `active_version`, clears `previous_version`, sets state to `READY`, and persists the state. It raises `PackError` when no previous version exists.

Recovery note: `active_catalog()` requires state `READY` and an active version; a failed install therefore leaves the last verified catalog serving traffic.

## 3. State machine rollback fix (M1)

The original `ROLLBACK_REQUIRED` state permitted transitions only to `READY` or `DISABLED`, leaving no clean retry path. The corrected transition map now includes:

- `ROLLBACK_REQUIRED -> NOT_INSTALLED`
- `ROLLBACK_REQUIRED -> READY`
- `ROLLBACK_REQUIRED -> DISABLED`

`install()` explicitly accepts `ROLLBACK_REQUIRED` and routes it through `NOT_INSTALLED -> QUEUED -> DOWNLOADING -> VERIFYING -> INSTALLING`. This removes the dead end so a reinstall after a rollback is possible. The change is covered by the focused backend suite (81 passing tests on Python 3.11 and 3.12).

## 4. Web IndexedDB activation, rollback, and corruption recovery

Implementation: `frontend-v3/src/guls/offline/storage.ts` and `runtime.ts`.

- Database: `guls-offline`, version 1, with object stores `active`, `previous`, `staging`, and `meta`.
- **Activation:** `activate(record)` runs one readwrite transaction over `active`, `previous`, and `meta`. If the old record has a different `packVersion`, it is copied to `previous`; the new record becomes `active`; `state.<languageId>` is set to `READY`. The transaction completes atomically.
- **Rollback:** `rollback(languageId)` runs one readwrite transaction that restores the `previous` record into `active`, deletes the `previous` entry, and sets state back to `READY`. If no previous record exists, it sets `ROLLBACK_REQUIRED` and returns `false`.
- **Corruption recovery:** `recoverPack(languageId)` re-hashes stored files with `contentHash()`. If the active record fails verification, it calls `rollback()`; if no valid record can be restored, it calls `disable()` so the language is no longer reported as ready. `translateOffline()` falls back to the bundled English catalog when no valid record is available.
- **Readiness filtering:** `listReady()` excludes languages whose meta state is `DISABLED` or `ROLLBACK_REQUIRED`; `readyLanguageIds()` always adds bundled English.
- **Staging isolation:** downloads are kept in the `staging` store and are not promoted to `active` until verification succeeds.
- **Memory driver:** `MemoryPackStorage` mirrors the same semantics for tests/restricted browsers but is explicitly not durable across restarts.

## 5. Service worker cache invalidation

Implementation: `frontend-v3/src/guls/offline/swCache.ts` and `frontend-v3/vite.config.ts`.

- The localization runtime cache is versioned: `GULS_SW_CACHE_VERSION = "v1"`, producing `guls-localization-v1`.
- `invalidateLocalizationCache()` removes the active versioned cache so the next read repopulates it.
- `purgeObsoleteLocalizationCaches()` removes only caches beginning with `guls-localization-` that are not the current version; unrelated caches are untouched.
- GULS pack bytes are deliberately excluded from Workbox precache/image/font caches and live in IndexedDB. Cache invalidation therefore does not delete or restore pack state; it only clears derived cached responses.
- Activation is not yet wired to a UI flow, so cache invalidation is an available primitive rather than an automatic post-activation step.

## 6. Recovery procedure for operators (documented, not executed)

1. Confirm the affected language and observed symptom (bad translation, failed install, corrupt local pack, or red gate).
2. Backend: check `state.json` for `active_version`, `previous_version`, and `state`. If a valid `previous_version` exists, call `PackManager.rollback(language_id)` or restore the corresponding version directory from the immutable pack store after verifying its signature and hash.
3. If no previous version exists, set the language to `DISABLED` / `NOT_INSTALLED` according to the state machine and require a fresh verified pack; do not force `READY`.
4. Web: verify stored record hashes; if corrupt, let `recoverPack()` restore the previous record or disable the language; clear the `guls-offline` database only as a last resort because it removes staging and previous records.
5. Invalidate `guls-localization-v1` and purge obsolete `guls-localization-*` caches after a pack change; confirm unrelated caches remain.
6. Confirm English fallback remains available and that blocked languages are not published.
7. Record the incident and do not claim recovery success without re-running the focused verification checks relevant to the changed surface.

## 7. PR branch and workspace preservation

| Artifact            | Preservation evidence                                                                                                                                                                                                        |
| ------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| GULS-021 branch     | `execution/gula-guls-021` in `/tmp/opencode/gula-guls-021`, based on PR #308 head `8097a55849769c4f17e0cc731da1c180e5bc9305`; corrections and documentation retained locally. No force-push, destructive reset, or deletion. |
| PR #308             | OPEN draft, `execution/gula-guls-020`, `mergeable=MERGEABLE`, `mergeStateStatus=UNSTABLE`, `mergedAt=null`; inspected only, not modified.                                                                                    |
| PR #307             | OPEN draft, `execution/gula-national-completion-013`, head `f2f950ce7a7b65683f4bfcfede0b1b2a7f0f4fed`; untouched.                                                                                                            |
| Protected workspace | Branch `remediate-security-001`, HEAD `f478676b6fc375338648dde46fbf076c015a3f91`, 6 worktrees, 2 stashes, status SHA-256 `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`; unchanged.                      |
| Draft PR decision   | No stacked Draft PR was opened because the coherent gates did not pass. The branch is preserved for authorized review.                                                                                                       |

## 8. Operational caveats

- No production or staging deployment, database access, PHI access, or production key was used; rollback steps are documented but not rehearsed in a live environment.
- Backend state is process-local (M5) and unsigned (M6); rollback across multiple replicas is not defined without shared persistent state.
- Preference writes are not protected by `ETag`/`If-Match` (M4); a concurrent write can survive a language rollback.
- Browser storage can be cleared by the user or browser policy; `MemoryPackStorage` is not durable.
- Cache invalidation is not bound to pack activation in the UI, and there is no dynamic-pack UI/native installation flow yet.
- Human linguistic and clinical approvals remain absent; rollback does not unblock a language whose registry/governance state is blocked.
- The final status remains **NOT READY — BLOCKED**. Recovery mechanisms reduce data-loss risk but do not satisfy the merge or production gates.
