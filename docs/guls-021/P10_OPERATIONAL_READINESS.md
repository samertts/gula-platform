# P10 — Operational Readiness

Program: GULA-GULS-021
Branch: `execution/gula-guls-021` in `/tmp/opencode/gula-guls-021`
Base: PR #308 head `8097a55849769c4f17e0cc731da1c180e5bc9305`; `main` at `2ee9e8bcb9d81e9cac6801f5dea9b86d59beaffa`
Date: 2026-11-21
Status: **NOT READY — BLOCKED**

## 1. Purpose

This document summarizes the operational evidence for the GULS-021 correction pass. It does not repeat the full command matrix; the authoritative verification record is `FINAL_ACCEPTANCE_REPORT.md`, and the complete blocker register is `BLOCKERS_AND_RISKS.md`.

Readiness is assessed against the coherent gate condition: a change is operationally ready only when automated gates are green, native build targets are verifiable, human linguistic and clinical approvals are recorded, client integration is complete, and key management is defined. That condition is not met.

## 2. Operational capabilities verified in the branch

| Area                   | Evidence                                                                                                                                                         | Operational meaning                                                                                        |
| ---------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------- |
| Backend pack install   | Staging write with `fsync`, rename into place, `.backup-*` restoration on swap failure, `previous_version` retention, downgrade rejection                        | A failed install leaves the currently active pack untouched; previous version can be restored.             |
| State machine recovery | `ROLLBACK_REQUIRED -> NOT_INSTALLED` is now permitted (M1 fix)                                                                                                   | A rollback-required pack can return to a clean retry path instead of remaining in a dead end.              |
| Local state file       | `state.json` written to a temporary file, flushed with `fsync`, then atomically replaced                                                                         | State updates are crash-consistent at the file level, but the file itself is not cryptographically signed. |
| Web offline runtime    | IndexedDB stores `active`, `previous`, `staging`, `meta`; activation is one transaction; rollback restores the previous version in one transaction               | Browser-side pack activation and recovery have a defined atomic path.                                      |
| Corruption recovery    | `recoverPack()` re-hashes stored files, rolls back to the previous valid record, and disables the language if no valid record exists                             | Corrupt local packs do not silently become the active translation source.                                  |
| Cache boundaries       | Pack bytes are kept out of Workbox caches and stored in IndexedDB; `guls-localization-v1` cache can be invalidated and older `guls-localization-*` caches purged | Web cache invalidation is separated from pack state, but activation is not yet wired to a UI flow.         |
| Fallback behavior      | English is bundled and added to the ready set; unknown locales never fall back to Arabic                                                                         | A disabled or blocked language degrades to English rather than an unapproved locale.                       |

Detailed rollback steps and caveats are in `ROLLBACK_AND_RECOVERY.md`.

## 3. Verification signal summary

| Signal                                                  | Result                                                                                                                             | Readiness effect                                                                                      |
| ------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------- |
| Focused backend tests, Python 3.11 and 3.12             | 81 passed, 1 warning each; exit 0                                                                                                  | Supports correctness of the corrected backend paths.                                                  |
| Touched-file Python compile and Ruff lint               | exit 0                                                                                                                             | No syntax or lint defect in touched Python files.                                                     |
| Ruff format check                                       | exit 1 for `pack_manager.py` only, due to the `target-version=py314` conflict                                                      | CI blocker; parenthesized `except` retained for 3.11/3.12 compatibility.                              |
| Focused frontend tests                                  | 3 files, 21 tests, exit 0                                                                                                          | Offline runtime unit behavior is covered.                                                             |
| Frontend typecheck, lint (`--max-warnings=0`), Prettier | exit 0                                                                                                                             | Static frontend gates pass in isolation.                                                              |
| Full frontend suite, GULS-021                           | `2 failed                                                                                                                          | 76 passed (78)` tests, exit 1                                                                         | Aggregate gate red.                                                                      |
| Full frontend suite, baseline `main`                    | `2 failed                                                                                                                          | 54 passed (56)` tests, exit 1                                                                         | Same `MobileBottomNav.test.tsx` failures; pre-existing, not a regression, but still red. |
| PR #308 checks                                          | 10 failing required-style checks; `mergeStateStatus=UNSTABLE`                                                                      | Merge gate is red. Baseline runs reproduce the same failures.                                         |
| Native toolchain                                        | `java` present; `gradle`, `swift`, `xcodebuild`, `flutter`, `dotnet` = `NOT_FOUND`                                                 | Android, iOS, Flutter desktop, and .NET paths cannot be verified locally.                             |
| Registry schema evidence                                | Log text `registry_schema=PASS languages=14`; venv-based runner exit 1; `registry_schema_rerun.log` with system Python 3.11 exit 0 | Original mismatch retained for audit; rerun reproduces the brief's result but does not make CI green. |
| Secret scan on diff                                     | exit 0, no key/token/password matches                                                                                              | No new secret material found in the diff.                                                             |

Exact commands, logs, and exit codes are in `FINAL_ACCEPTANCE_REPORT.md`.

## 4. What is not operationally ready

1. **CI is red.** The corrected branch is not a candidate for merge while required-style checks fail, even though the same failures exist on baseline `main`.
2. **Native builds are unverified.** No Gradle, Swift/Xcode, Flutter, or .NET toolchain is available locally; client inventories confirm that dynamic-pack wiring is absent or incomplete.
3. **Human gates are open.** No linguistic or clinical approver has approved Iraqi Turkmen or Syriac script choices, L3/L4 clinical catalogs, or font assets.
4. **Client integration is incomplete.** The Web offline module exists at runtime level, but no dynamic-pack UI installation flow is wired; Android, iOS, Flutter desktop, and adjacent clients have no GULS dynamic-pack integration.
5. **State remains single-process and unsigned.** M4, M5, and M6 are residual risks: shared preference key without optimistic concurrency, in-memory delivery/lifecycle state, and unsigned local state with deployment-dependent OS protection.
6. **No production key management exists.** Only ephemeral test keys were used; production/staging startup deliberately refuses the synthetic-pack flag.

## 5. Readiness conclusion

Operational readiness is **not achieved**. The corrections are implemented and scoped automated checks pass, but the coherent gate set is blocked by CI, native verification, human approvals, client integration, and key management. The final program status remains **NOT READY — BLOCKED**. No merge, deployment, production access, or Draft PR is authorized by this assessment.
