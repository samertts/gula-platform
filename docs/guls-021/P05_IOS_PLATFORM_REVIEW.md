# P05 — iOS Platform Review

Program: GULA-GULS-021
Scope: Read-only review of `mobile/ios` in `/tmp/opencode/gula-guls-021` on `execution/gula-guls-021`
Baseline: `main` at `2ee9e8bcb9d81e9cac6801f5dea9b86d59beaffa`
Review date: 2026-11-21
Status: **NOT READY — BLOCKED**

## 1. Boundary and method

This document records a read-only source inspection of the iOS client. No file in `mobile/ios` was modified. No Swift build, Xcode build, simulator test, or CI job was executed locally. The authoritative platform inventory is `CONTEXT.md` in `/tmp/opencode/gula-guls-021-evidence/`; path and code inspection was used only to confirm those claims.

No merge, deployment, production access, code-signing operation, or human approval is claimed.

## 2. Tool availability and project availability

The local toolchain probe (`run_checks.sh`, `local_toolchain.log`, exit 0) reported `swift=NOT_FOUND` and `xcodebuild=NOT_FOUND`; only `java=/usr/bin/java` was present. The other probed tools (`gradle`, `flutter`, `dotnet`) were also `NOT_FOUND`.

The inspected iOS tree contains 118 Swift files, `Info.plist`, resources, entitlements, tests, and UI tests, but **no `*.xcodeproj`, `*.xcworkspace`, `Podfile`, or `Package.swift`** was found. A CI project-availability gate exists; it was not run in this environment. A buildable Xcode project must therefore be supplied or generated before native verification can proceed.

## 3. Existing localization resources

| Area                 | Observed state                                                                                                                    | Source                                                                              |
| -------------------- | --------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------- |
| Bundle localizations | `CFBundleLocalizations = [en, ar]`; `CFBundleDevelopmentRegion = ar`                                                              | `Gula/Info.plist`                                                                   |
| Base strings         | English `Localizable.strings` and `Localizable.stringsdict`                                                                       | `Gula/Resources/Localizable.strings`, `Localizable.stringsdict`                     |
| Arabic strings       | Arabic strings in `ar.lproj`                                                                                                      | `Gula/Resources/ar.lproj/Localizable.strings`                                       |
| Lookup helper        | `String.localized`, `localized(with:)`, `localized(forLanguage:)`                                                                 | `Gula/String+Localization.swift`                                                    |
| Language setting     | `AppLanguage` enum supports only `english ("en")` and `arabic ("ar")`; selection persisted under `app_language` in `UserDefaults` | `Gula/Core/UI/ThemeManager.swift`, `Gula/Features/Settings/SettingsViewModel.swift` |
| Additional languages | No Sorani (`ckb`), Turkmen, or Syriac localization resources found                                                                | Resource inspection                                                                 |

The iOS client is statically bilingual (Arabic/English). It does not consume the shared registry and contains no dynamic catalog layer.

## 4. Offline storage

| Area            | Observed state                                                                                                                                  | Source                                                                                          |
| --------------- | ----------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------- |
| Local database  | CoreData stack with repositories for patients, orders, results, samples, notifications, and sync queue entities                                 | `Gula/Core/Storage/CoreDataStack.swift`, `Core/Storage/Repositories/*`, `Core/Storage/Models/*` |
| Synchronization | `SyncEngine`, `SyncQueue`, `NetworkSynchronizer`, `ConflictResolver`                                                                            | `Gula/Core/Offline/*`                                                                           |
| Background work | `BackgroundTaskManager`; identifiers `com.gula.sync`, `com.gula.cleanup`, `com.gula.refresh` declared via `BGTaskSchedulerPermittedIdentifiers` | `Gula/Core/Background/BackgroundTaskManager.swift`, `Info.plist`                                |
| Secrets         | Keychain-backed session/token storage                                                                                                           | `Gula/Core/Auth/KeychainManager.swift`, `Core/Security/SessionManager.swift`                    |
| Connectivity    | `NetworkMonitor` and offline UI banners                                                                                                         | `Gula/Core/Networking/NetworkMonitor.swift`, `UI/Components/GulaOfflineBanner.swift`            |

This is clinical data offline support. No pack archive store, Ed25519 verification, manifest digest validation, or GULS lifecycle state exists in the iOS client.

## 5. RTL handling and fonts

- `RTLManager.shared` tracks `isRTL`, derives layout direction, mirrors edges/alignment, and writes `app_language` while applying `UIView.appearance().semanticContentAttribute` (`.forceRightToLeft` / `.forceLeftToRight`). `RTLReader` and `RTLStack` provide locale-driven layout helpers. (`Gula/UI/Theme/RTLManager.swift`)
- `ThemeManager.updateLayoutDirection()` also forces semantic content attributes for `UIView`, `UISearchBar`, and `UITextField` based on `AppLanguage.isRTL`. (`Gula/Core/UI/ThemeManager.swift`)
- RTL is Arabic-only; no Sorani or Syriac RTL behavior is implemented. Numeric/identifier non-reversal and mirrored icon/screenshot verification have not been demonstrated.
- `Info.plist` declares `UIAppFonts` entries for `NotoKufiArabic-Regular/Bold/Medium/SemiBold/Light.ttf` and `Inter-Regular/Bold/Medium/SemiBold/Light.ttf`. `FontManager` attempts to register these fonts at runtime and selects them by weight and script. **No `.ttf`/`.otf` font files were found in the repository**, and no font licence files were found; asset presence and licensing must be verified in the actual build artifact. See `P08_I18N_RTL_AND_FONTS.md`.

## 6. GULS dynamic-pack integration

No GULS dynamic-pack integration exists under `mobile/ios` (or anywhere under `mobile/`): case-insensitive searches for `guls`, `GULS`, `language_pack`, `languagePack`, `pack_manager`, and `packManager` returned no matches. The iOS client therefore has:

- no registry consumption or blocked-language gate;
- no pack download token flow, signature verification, or archive handling;
- no offline pack storage or verified-catalog translation lookup;
- no install/activate/rollback UI for downloadable languages.

Backend and Web GULS work must not be represented as iOS support.

## 7. Verification still required

Before any iOS offline-language claim can be made:

1. Supply or generate a buildable Xcode project/workspace (or Swift package) for the 118 Swift files; the current tree has none.
2. On a macOS host with Xcode, run `xcodebuild`/XCTest unit and UI tests and record exact commands, exit codes, and counts. Swift and `xcodebuild` are `NOT_FOUND` locally, so this pass could not do so.
3. Verify that `Info.plist` localizations, `ar.lproj` resources, `app_language` persistence, and RTL semantic attributes work on a simulator/device, including process restart.
4. Verify that all declared `UIAppFonts` binaries are present in the built bundle and that their licences and glyph coverage are acceptable (Arabic at minimum; any future Syriac/Turkmen/script choice separately).
5. Verify CoreData migrations, Keychain access, BGTask registration/execution, and offline sync behavior on device.
6. Design and implement GULS client integration (registry, signed pack verification, storage, activation, fallback, rollback), then verify it natively.
7. Resolve the repository-wide red CI gate before treating any iOS-related claim as merge-ready.

None of these steps has been completed in this pass.

## 8. Test evidence relevant to this review

| Check                         | Command                                                                                                                                                                                                    | Exit | Result                                                          | Log                                                |
| ----------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---: | --------------------------------------------------------------- | -------------------------------------------------- |
| Local toolchain inventory     | `for tool in java gradle swift xcodebuild flutter dotnet; do if command -v "$tool" >/dev/null 2>&1; then printf "%s=%s\n" "$tool" "$(command -v "$tool")"; else printf "%s=NOT_FOUND\n" "$tool"; fi; done` |    0 | `swift=NOT_FOUND`, `xcodebuild=NOT_FOUND`; `java=/usr/bin/java` | `local_toolchain.log`                              |
| Project file discovery        | Read-only glob over `mobile/ios/**/*.{xcodeproj,xcworkspace,pbxproj}`                                                                                                                                      |  n/a | No project/workspace files found                                | This review                                        |
| PR #308 checks (context only) | `gh pr checks 308`                                                                                                                                                                                         |    1 | 10 failing checks; `mergeStateStatus=UNSTABLE`                  | `pr308_checks.log`, `P00_INDEPENDENT_REVIEW.md` §3 |

No iOS-specific test command was run; there is no iOS pass/fail count to report. Focused backend (`81 passed`, exit 0) and frontend (`3 files, 21 tests`, exit 0) results cover other surfaces only.

## 9. Residual risks and blockers

- No buildable iOS project is present in the tree; native compilation is unverified.
- No local Swift/Xcode toolchain; no iOS build or simulator evidence exists for this execution.
- Arabic/English are the only supported bundle languages; no dynamic language support.
- RTL is Arabic-only and visually unverified; declared fonts are not present as repository assets.
- No GULS dynamic-pack integration, so the iOS client cannot install, verify, or use downloadable packs.
- CI is red and `UNSTABLE`; no merge readiness is claimed.

**Final status: NOT READY — BLOCKED**
