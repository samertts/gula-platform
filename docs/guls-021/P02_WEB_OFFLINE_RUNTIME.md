# P02 — Web Offline Runtime

Program: GULA-GULS-021
Scope: `execution/gula-guls-021` at PR #308 head `8097a55849769c4f17e0cc731da1c180e5bc9305`, corrected in the isolated branch
Baseline: `main` at `2ee9e8bcb9d81e9cac6801f5dea9b86d59beaffa`
Date: 2026-11-21
Status: **NOT READY — BLOCKED**

## 1. Purpose and boundary

This document records the Web offline runtime added under `frontend-v3/src/guls/offline/`, the related VitePWA cache configuration change, the evidence for those changes, and the remaining wiring gap. It is documentation only: no application code, configuration, protected workspace, CI state, or PR was modified by this review.

Sources inspected: `frontend-v3/src/guls/offline/*.ts`, `frontend-v3/vite.config.ts`, `frontend-v3/src/guls/runtime.ts`, `frontend-v3/src/guls/registry.ts`, `frontend-v3/src/i18n/`, `frontend-v3/package.json`, the GULS-021 evidence logs, and the baseline copy of `vite.config.ts` for comparison.

No merge, deployment, production database access, production key use, native client build, or human linguistic/clinical approval is implied by this document.

## 2. New Web offline modules

The new directory is untracked in the GULS-021 branch (`changed_files.log`), with nine TypeScript files: eight implementation/barrel files and one test file.

| File              | Responsibility                                   | Evidence visible in source                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                         |
| ----------------- | ------------------------------------------------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `types.ts`        | Stable contract and shared interfaces            | `GulsOfflineCode` enumerates fail-closed codes such as `GULS_PACK_UNSUPPORTED`, `GULS_PACK_INVALID_ARCHIVE`, `GULS_PACK_UNSAFE_PATH`, `GULS_PACK_FILE_TYPE_FORBIDDEN`, `GULS_PACK_TOO_LARGE`, `GULS_PACK_MANIFEST_INVALID`, `GULS_PACK_HASH_MISMATCH`, `GULS_PACK_SIGNATURE_INVALID`, `GULS_PACK_POLICY_REJECTED`, `GULS_PACK_INCOMPATIBLE`, quota/network/cancel/incomplete codes. `GulsFailure` carries the code and parameters. `PackManifest`, `InstalledPackRecord`, `StagingRecord`, `PackLifecycleState`, `StorageStatus`, and `StorageDriver` define the runtime boundary. |
| `storage.ts`      | Native IndexedDB persistence                     | `IndexedDbPackStorage` opens database `guls-offline` version 1 with `active`, `previous`, `staging`, and `meta` object stores. `activate()` and `rollback()` are multi-store transactions that preserve the previous version, set `READY`, or mark `ROLLBACK_REQUIRED`. `listReady()` excludes `DISABLED` and `ROLLBACK_REQUIRED`. `MemoryPackStorage` is explicitly non-durable and intended for tests/restricted browsers.                                                                                                                                                       |
| `zip.ts`          | Data-only ZIP extraction                         | Reads the ZIP central directory and end-of-central-directory record directly with `DataView`; supports stored and deflate-raw entries through native `DecompressionStream`. Rejects unsafe paths, symlinks, executable/script suffixes, duplicate members, unsupported compression, member sizes above 10 MiB, total uncompressed bytes above 50 MiB, and more than 256 archive members.                                                                                                                                                                                           |
| `verify.ts`       | Client-side verification and policy enforcement  | `validateManifest()` checks schema/version, identifiers, script/direction, hashes, sizes, file paths, approval status, and signature shape. `sha256()`, `contentHash()`, and `verifySignature()` use native Web Crypto (`SHA-256`, Ed25519 import/verify) and fail closed. `verifyPack()` checks language/locale/script/direction/engine compatibility, synthetic signer-key binding, archive-derived catalogs, rejects a clinical catalog in a dynamic pack, validates per-file and content hashes and `content_size`, then verifies the signature.                               |
| `download.ts`     | Policy-checked, resumable download               | `checkTransferPolicy()` handles offline state, data-saver, cellular/slow-network and roaming rules, and a conservative quota check of `2 * requiredBytes`. `downloadPack()` stages chunks in the `StorageDriver`, uses `Range` on resume, `cache: "no-store"`, `AbortController` plus an explicit abort race, and retry delays of 500/1000/2000 ms.                                                                                                                                                                                                                                |
| `runtime.ts`      | Offline resolution, activation, recovery, lookup | `readyLanguageIds()` always adds bundled English (`BUNDLED_FALLBACK_LANGUAGE = "en"`). `resolveOffline()` delegates to the GULS resolver with locally ready IDs. `activatePack()` activates a verified pack. `verifyStoredRecord()` recomputes the content hash. `recoverPack()` rolls back or disables a corrupt active record. `translateOffline()` reads only `catalogs/common.json` and falls back cleanly. `assertPublishable()` blocks unapproved registry entries.                                                                                                          |
| `swCache.ts`      | Versioned Cache Storage helpers                  | Defines `GULS_SW_CACHE_VERSION = "v1"`, `GULS_LOCALIZATION_CACHE = "guls-localization-v1"`, and `GULS_PWA_OFFLINE_PAGE = "/offline.html"`. `invalidateLocalizationCache()` and `purgeObsoleteLocalizationCaches()` operate through the native `caches` API and are safe when `caches` is unavailable.                                                                                                                                                                                                                                                                              |
| `index.ts`        | Barrel export                                    | Re-exports all seven modules above; it is the single public entry point for the offline runtime.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                   |
| `offline.test.ts` | Focused Vitest coverage                          | Thirteen tests cover valid signed packs, tampered content, untrusted keys, hidden clinical catalog rejection, path traversal, short archives, member-count limits, duplicate members, activation/rollback, corrupted-record recovery, English fallback, metered-network blocking, and resumable/cancellable download.                                                                                                                                                                                                                                                              |

### Native APIs and dependency position

The implementation uses browser/platform primitives only: IndexedDB, Web Crypto, `DecompressionStream`, `Blob`/`Response`, `Cache Storage`, `fetch`, `AbortController`, and `navigator.connection`/`navigator.storage` where available. `frontend-v3/package.json` was not changed, and no new runtime dependency was added; `vite-plugin-pwa` was already present as a dev dependency. This satisfies the "free/open-source first, no new paid dependency, no vendor lock-in" direction for this specific Web change because no new external component is introduced.

## 3. VitePWA cache change

The GULS-021 `vite.config.ts` differs from baseline mainly in quote formatting and one functional Workbox addition. The VitePWA registration remains `autoUpdate`; the existing asset precache, image cache (`image-cache`), and font cache (`font-cache`) are unchanged.

Added runtime cache rule:

- URL pattern: `/\/api\/v1\/localization\/languages(?:\?|$)/`
- Handler: `NetworkFirst`
- Cache name: `guls-localization-v1`
- Network timeout: 5 seconds
- Expiration: 10 entries, 86,400 seconds (one day)
- Cacheable status: `200`

The inline configuration comment states that the language list is safe to cache offline and that pack bytes are deliberately excluded from Workbox because they are verified and stored in IndexedDB by the GULS runtime. The cache name matches `GULS_LOCALIZATION_CACHE` in `swCache.ts`. No GULS pack-byte URL is added to Workbox caching.

## 4. i18n boundary

`src/i18n/index.ts` initializes i18next with `ar`, `en`, and the approved `ckb` identifier for the existing partial Sorani resource; `fallbackLng` is `en`. `src/i18n/locales.ts` exposes only `ar`, `en`, and `ckb` in `localeOptions`; legacy `ku`, `tk`, and `syr` normalize to `ckb`, `en`, and `en` respectively. Dynamic packs are not registered in i18next by this pass. The offline module is therefore a separate runtime path, not an i18next backend.

## 5. Verification evidence

Commands below are the exact commands recorded in `run_checks.sh`; exit codes are from `summary.txt`, and counts/output are from the named logs.

| Check                                       | Command                                                                                                                                          | Exit | Result from log                                                                                          |
| ------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------ | ---: | -------------------------------------------------------------------------------------------------------- |
| Focused frontend tests (from `frontend-v3`) | `npx vitest run --passWithNoTests --exclude 'e2e/**' src/guls/guls.test.ts src/guls/offline/offline.test.ts src/i18n/mobileNavResources.test.ts` |    0 | `Test Files  3 passed (3)`, `Tests  24 passed (24)`; Vitest 4.1.10; non-fatal Vite config-loader warning |
| Frontend typecheck (from `frontend-v3`)     | `npx tsc --noEmit -p tsconfig.json --pretty false`                                                                                               |    0 | Empty log, no diagnostics                                                                                |
| Frontend lint (from `frontend-v3`)          | `npm run lint -- --max-warnings=0`                                                                                                               |    0 | ESLint command completed with no findings                                                                |
| Frontend formatting (from `frontend-v3`)    | `npx prettier --check src/guls/offline/*.ts vite.config.ts`                                                                                      |    0 | `All matched files use Prettier code style!`                                                             |
| Full frontend suite, GULS-021               | `npm test`                                                                                                                                       |    0 | `Test Files  18 passed (18)`; `Tests  78 passed (78)`                                                    |
| Full frontend suite, baseline               | `npm test` (from `/tmp/opencode/gula-guls-021-baseline/frontend-v3`)                                                                             |    1 | `Test Files  1 failed \| 15 passed (16)`; `Tests  2 failed \| 54 passed (56)`                            |
| Backend focused tests, Python 3.12          | `PYTHONPATH=backend /tmp/opencode/gula-guls-020-venv/bin/python -m pytest -q backend/tests/localization backend/tests/test_error_contract.py`    |    0 | `81 passed, 1 warning`                                                                                   |
| Backend focused tests, Python 3.11          | `PYTHONPATH=backend python3.11 -m pytest -q backend/tests/localization backend/tests/test_error_contract.py`                                     |    0 | `81 passed, 1 warning`                                                                                   |
| Frontend production build                   | `npm run build`                                                                                                                                  |    0 | Vite build succeeded; PWA generated 140 precache entries                                                 |

By source inspection, `offline.test.ts` contributes 13 of the 24 focused frontend tests (`guls.test.ts` has 9 and `mobileNavResources.test.ts` has 2). The additional ZIP cases cover short archives, member-count limits, and duplicate member names, matching the extractor's hardening. The full suite now passes on GULS-021 after a separate accessibility-label correction in `MobileBottomNav.tsx`; the uncorrected baseline remains red in that component. `TEST_EVIDENCE.md` is the authoritative register of all 24 evidence commands, including the corrected registry-schema interpreter result.

## 6. Limitations and residual wiring gap

1. **No production wiring.** A source search found call sites for `verifyPack`, `resolveOffline`, `downloadPack`, and the cache helpers only inside the offline module and its test file. There is no application component, i18next backend, route, or UI flow that imports `src/guls/offline/index.ts`. Consequently, no end-user installation or offline translation path is active from this pass.
2. **Cache invalidation is not registered.** `invalidateLocalizationCache()` and `purgeObsoleteLocalizationCaches()` exist but are not invoked by a service-worker activation hook or application bootstrap. The VitePWA cache name is versioned, but automatic migration/cleanup is not demonstrated.
3. **Static i18n resources remain authoritative.** The Web app continues to use bundled `ar`/`en`/`ckb` resources. Dynamic pack selection, installation, and activation UI are absent; the P00 note about no dynamic-pack UI flow remains applicable.
4. **Browser/platform dependence.** IndexedDB, Web Crypto, `DecompressionStream`, and Cache Storage are assumed. Missing capabilities produce explicit `GULS_PACK_UNSUPPORTED` or safe fallbacks; no cross-browser matrix was executed here.
5. **Storage durability is browser-managed.** IndexedDB can be evicted or cleared by the user or browser. The record integrity check recomputes the stored content hash but does not re-verify the Ed25519 signature on every load; signature verification happens during pack verification before activation. No client-state authenticity design is claimed.
6. **Dynamic clinical content is blocked by design.** `verify.ts` rejects an archive-derived `clinical` catalog, regardless of the declared catalog list. Clinical terminology therefore requires a separate approved governance path and human approval.
7. **Aggregate gates remain blocked.** The full frontend suite passes locally, but PR #308 CI is red/UNSTABLE and platform/human approval gates are unresolved. A green local suite is not a merge gate pass.

Final status: **NOT READY — BLOCKED**.
