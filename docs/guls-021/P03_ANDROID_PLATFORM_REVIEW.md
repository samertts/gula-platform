# P03 — Android Platform Review

Program: GULA-GULS-021
Scope: Read-only review of `mobile/android` in `/tmp/opencode/gula-guls-021` on `execution/gula-guls-021`
Baseline: `main` at `2ee9e8bcb9d81e9cac6801f5dea9b86d59beaffa`
Review date: 2026-11-21
Status: **NOT READY — BLOCKED**

## 1. Boundary and method

This document records a read-only source inspection of the Android client. No source file in `mobile/android` was modified. No native Gradle build, unit test, or instrumentation test was executed in this environment. The protected workspace was not touched, and no merge, deployment, production access, or human approval is claimed.

The authoritative platform inventory is `CONTEXT.md` in `/tmp/opencode/gula-guls-021-evidence/`. Directory and file inspection was limited to confirming the paths and code claims listed below.

## 2. Tool availability

The local toolchain probe (`run_checks.sh`, `local_toolchain.log`, exit 0) reported:

| Tool         | Result          |
| ------------ | --------------- |
| `java`       | `/usr/bin/java` |
| `gradle`     | `NOT_FOUND`     |
| `swift`      | `NOT_FOUND`     |
| `xcodebuild` | `NOT_FOUND`     |
| `flutter`    | `NOT_FOUND`     |
| `dotnet`     | `NOT_FOUND`     |

Java is present, but Gradle is not installed locally. The repository contains `mobile/android/gradlew`, `mobile/android/gradle/wrapper/`, `build.gradle.kts`, `settings.gradle.kts`, and a CI workflow; none of them were executed here. The absence of Gradle is a local verification limitation, not a claim that Android CI cannot build elsewhere.

## 3. Existing localization resources

| Area                  | Observed state                                                                                                     | Source                                                                                                            |
| --------------------- | ------------------------------------------------------------------------------------------------------------------ | ----------------------------------------------------------------------------------------------------------------- |
| Base strings          | English default resource set                                                                                       | `mobile/android/app/src/main/res/values/strings.xml`                                                              |
| Arabic strings        | Arabic resource set for `values-ar`                                                                                | `mobile/android/app/src/main/res/values-ar/strings.xml`                                                           |
| Language preference   | Encrypted preference `locale`, default `"ar"`                                                                      | `mobile/android/app/src/main/java/io/gula/android/security/EncryptedPrefs.kt` (`KEY_LOCALE`, getter default `ar`) |
| Language selection UI | Settings offers only `ar` and `en`; `SettingsViewModel.setLocale()` writes the encrypted preference and view state | `ui/features/settings/SettingsScreen.kt`, `ui/features/settings/SettingsViewModel.kt`                             |
| Locale manager        | `LocaleManager.setLocale()`, `getCurrentLocale()`, and `isRtl()` exist but are not called from application code    | `util/LocaleManager.kt`; no external call sites found under `app/src`                                             |
| Additional languages  | No Sorani (`ckb`), Turkmen, or Syriac resource directories found                                                   | `res/values*/strings.xml` inspection                                                                              |

The Android client therefore has static bilingual (Arabic/English) resources plus an encrypted language preference. Writing the preference does not currently reconfigure the activity locale, and no dynamic catalog layer is present.

## 4. Offline storage

| Area                   | Observed state                                                                                                                                                                        | Source                                                                                                                   |
| ---------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------ |
| Primary local database | Room database named `gula_database`                                                                                                                                                   | `data/local/GulaDatabase.kt`, `util/Constants.kt` (`DB_NAME`)                                                            |
| Offline queue          | Sync queue entity, DAO, and `ProcessOfflineQueueUseCase`                                                                                                                              | `data/local/entity/SyncQueueEntity.kt`, `data/local/dao/SyncQueueDao.kt`, `domain/usecase/ProcessOfflineQueueUseCase.kt` |
| Background work        | `SyncWorker`, `DataCleanupWorker`, and `NotificationWorker` define periodic requests and `enqueue(context)` helpers                                                                   | `work/*.kt`                                                                                                              |
| Work scheduling        | No application-level calls to those `enqueue()` helpers were found in the inspected source; only the helper definitions and the WorkManager initializer in the manifest were observed | `work/*.kt`, `AndroidManifest.xml`                                                                                       |
| Secure preferences     | `EncryptedSharedPreferences` with AES256_GCM/SIV keys, including `locale`                                                                                                             | `security/EncryptedPrefs.kt`                                                                                             |

This is application-data offline support (patients, orders, results, samples, notifications, sync queue). It is not GULS language-pack storage: there is no pack archive store, no signature verification, no manifest digest checking, and no registry-driven pack lifecycle in this client.

## 5. RTL handling

`LocaleManager.setLocale()` creates a configuration context with the selected locale on Android 13+ and uses the deprecated configuration path below that; `isRtl()` treats `ar` (or a right-to-left display name) as RTL. These functions are the extent of the observed RTL implementation and are currently unwired. The settings screen only persists a string. Mirroring of controls, logical spacing, mirroring of icons, numeric/identifier direction, and RTL screenshot verification have not been demonstrated for the Android client.

## 6. GULS dynamic-pack integration

No GULS dynamic-pack integration exists in `mobile/android` (or anywhere under `mobile/`): a case-insensitive search for `guls`, `GULS`, `language_pack`, `languagePack`, `pack_manager`, and `packManager` returned no matches. Consequently the Android client has none of the following:

- consumption of `shared/guls/language_registry.json`;
- pack list/download flows backed by the localization API;
- Ed25519 verification or digest checks in the client;
- an install/activate/rollback UI for downloadable languages;
- offline translation lookup from a verified pack.

The backend GULS delivery API and the Web offline runtime are separate surfaces; their existence does not imply Android support. Documentation that previously implied general client offline language support must be read as Web-only until a client integration exists.

## 7. Verification still required

Before any Android offline-language claim can be made:

1. Run the Gradle wrapper or CI Android job on a machine with a supported toolchain; record build and unit-test results. Gradle is `NOT_FOUND` locally, so this pass could not do so.
2. Run instrumentation tests on a device/emulator at or above `minSdk 26` (configured in `app/build.gradle.kts`), including locale switching from settings and process restart.
3. Verify that changing the encrypted `locale` preference actually updates the activity locale and layout direction; wire or replace `LocaleManager` as appropriate.
4. Verify Room database creation/migration, encrypted preference keystore behavior, and offline queue/sync behavior on a real device.
5. Add and review RTL screenshots for Arabic, including numeric and clinical identifier direction, and confirm logical spacing in Compose.
6. Design and implement GULS client integration (registry, signed pack verification, storage, activation, fallback, and uninstall/rollback) and then verify it natively.
7. Resolve the repository-wide red CI gate before treating any Android-related claim as merge-ready.

None of these steps has been completed in this pass.

## 8. Test evidence relevant to this review

| Check                         | Command                                                                                                                                                                                                    | Exit | Result                                                                                     | Log                                                |
| ----------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---: | ------------------------------------------------------------------------------------------ | -------------------------------------------------- |
| Local toolchain inventory     | `for tool in java gradle swift xcodebuild flutter dotnet; do if command -v "$tool" >/dev/null 2>&1; then printf "%s=%s\n" "$tool" "$(command -v "$tool")"; else printf "%s=NOT_FOUND\n" "$tool"; fi; done` |    0 | `java=/usr/bin/java`; `gradle`, `swift`, `xcodebuild`, `flutter`, `dotnet` = `NOT_FOUND`   | `local_toolchain.log`                              |
| PR #308 checks (context only) | `gh pr checks 308`                                                                                                                                                                                         |    1 | 10 failing checks; `mergeStateStatus=UNSTABLE`; same failures reproduce on baseline `main` | `pr308_checks.log`, `P00_INDEPENDENT_REVIEW.md` §3 |

No Android-specific test command was run; there is no Android pass/fail count to report. The focused backend suite (`81 passed`, exit 0) and focused frontend suite (`3 files, 21 tests`, exit 0) validate other surfaces only.

## 9. Residual risks and blockers

- Static Arabic/English resources and an unwired locale manager cannot satisfy multi-language or dynamic-pack requirements.
- WorkManager workers are defined but not scheduled from application code; offline synchronization behavior is unverified.
- No native build toolchain locally; no Android build or device test evidence exists for this execution.
- No GULS dynamic-pack integration, so the Android client cannot install, verify, or use downloadable language packs.
- Human linguistic/clinical approvals are absent for blocked content; the client must not become a bypass around registry gates.
- CI is red and `UNSTABLE`; no merge readiness is claimed.

**Final status: NOT READY — BLOCKED**
