# P06 — Desktop Platform Review

Program: GULA-GULS-021
Scope: Read-only review of the Flutter desktop client at `mobile/desktop` in `/tmp/opencode/gula-guls-021` on `execution/gula-guls-021`
Baseline: `main` at `2ee9e8bcb9d81e9cac6801f5dea9b86d59beaffa`
Review date: 2026-11-21
Status: **NOT READY — BLOCKED**

## 1. Boundary and method

This document records a read-only source inspection of the Flutter desktop client. No file in `mobile/desktop` was modified. No Flutter build, Dart test, packaging run, or CI job was executed locally. The authoritative platform inventory is `CONTEXT.md` in `/tmp/opencode/gula-guls-021-evidence/`; directory inspection was used only to confirm paths and claims.

No merge, deployment, production access, or human approval is claimed.

## 2. Tool availability and packaging files

The local toolchain probe (`run_checks.sh`, `local_toolchain.log`, exit 0) reported `flutter=NOT_FOUND` and `dotnet=NOT_FOUND`; `java=/usr/bin/java` was present. `gradle`, `swift`, and `xcodebuild` were also `NOT_FOUND`.

The tree contains macOS Xcode project/workspace files (`macos/Runner.xcodeproj`, `macos/Runner.xcworkspace`), Windows and Linux runner/CMake packaging, `packaging/deb/DEBIAN/control`, and `packaging/gula-platform.spec`. These files were inspected only; none were built because Flutter (and `xcodebuild` for macOS) is unavailable locally.

## 3. Existing localization resources

| Area                 | Observed state                                                                                                                                       | Source                                                          |
| -------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------- |
| Custom localization  | `AppLocalization` with inline `arTranslations` and `enTranslations` maps; delegate supports `ar`/`en`; missing keys return the raw key               | `lib/l10n/l10n.dart`                                            |
| Supported locales    | `Locale('ar','IQ')` and `Locale('en','US')`; fallback `ar_IQ`                                                                                        | `lib/l10n/l10n.dart` (`supportedLocales`, `fallbackLocale`)     |
| ARB files            | `app_ar.arb` and `app_en.arb` exist with a larger key set, but the runtime `translate()` path uses the inline maps rather than generated ARB classes | `lib/l10n/app_ar.arb`, `app_en.arb`, `l10n.dart`                |
| Settings             | `SettingsProvider`/`SettingsPage` manage user preferences; `ThemeProvider` holds the active locale                                                   | `lib/features/settings/*`, `lib/core/theme/theme_provider.dart` |
| Additional languages | No `ckb`, Turkmen, or Syriac locale resources found                                                                                                  | `lib/l10n/` inspection                                          |

The desktop client is statically Arabic/English with an incomplete inline map; ARB files are not the observed runtime source of truth. There is no dynamic catalog layer.

## 4. Offline storage

| Area                 | Observed state                                                                                | Source                                                       |
| -------------------- | --------------------------------------------------------------------------------------------- | ------------------------------------------------------------ |
| Local database       | Drift database and generated code; DAOs for patients, orders, results, samples, notifications | `lib/core/offline/database.dart`, `database.g.dart`, `dao/*` |
| Synchronization      | `SyncEngine`, `SyncQueueManager`, `SyncProvider`, `ConflictResolver`, connectivity service    | `lib/core/offline/*`                                         |
| Secure configuration | `secure_config.dart` using `flutter_secure_storage`; certificate pinning and tamper detection | `lib/core/security/*`                                        |
| Updates              | `auto_updater.dart` and `auto_updater` dependency                                             | `lib/core/update/auto_updater.dart`, `pubspec.yaml`          |

This is application-data offline support. No pack archive store, Ed25519 verification, manifest digest validation, registry consumption, or GULS lifecycle state exists in the desktop client.

## 5. RTL handling and fonts

- `ThemeProvider` starts with `ar_IQ` and `_isRtl = true`; `setLocale()` sets `_isRtl = locale.languageCode == 'ar'`; `toggleRtl()` exists. RTL is Arabic-only; Sorani and Syriac RTL are not represented. (`lib/core/theme/theme_provider.dart`)
- `AppTypography.arabicTextTheme` uses `GoogleFonts.notoSansArabicTextTheme()` and `latinTextTheme` uses `GoogleFonts.interTextTheme()` (with explicit sizes/weights). `google_fonts` is a declared dependency. (`lib/core/theme/app_typography.dart`, `pubspec.yaml`)
- Fonts obtained through `google_fonts` are fetched/cached at runtime by that package; bundled font files and licence files were not found in the repository. Offline font availability, glyph coverage, and licence text must be verified in the packaged artifact. See `P08_I18N_RTL_AND_FONTS.md`.
- No RTL screenshot tests or numeric/identifier direction checks were run.

## 6. GULS dynamic-pack integration

No GULS dynamic-pack integration exists under `mobile/desktop` (or anywhere under `mobile/`): case-insensitive searches for `guls`, `GULS`, `language_pack`, `languagePack`, `pack_manager`, and `packManager` returned no matches. The desktop client therefore has:

- no registry or blocked-language gate;
- no tokenized download, signature verification, or archive extraction;
- no offline pack storage or verified-catalog translation lookup;
- no install/activate/rollback UI for downloadable languages.

The Web offline pack runtime is the only newly implemented offline pack layer in this execution; it does not apply to Flutter desktop.

## 7. Verification still required

Before any desktop offline-language claim can be made:

1. On a host with Flutter installed, run `flutter analyze`, `flutter test`, and `flutter build` for the intended Linux/Windows/macOS targets; record exact commands, exit codes, and counts. Flutter is `NOT_FOUND` locally, so this pass could not do so.
2. Verify packaging artifacts (`.deb`/RPM spec, Windows runner, macOS app) and the auto-updater path, including signature/update behavior as applicable.
3. Verify Drift database creation/migration, secure storage on each OS, offline sync, and connectivity transitions.
4. Verify locale switching (`ar_IQ`/`en_US`), RTL layout and screenshot expectations, and whether the ARB files or inline maps are authoritative; reconcile the duplication if needed.
5. Verify bundled or runtime-cached font availability, licence files, and shaping/glyph coverage, including offline behavior for `google_fonts`.
6. Design and implement GULS client integration (registry, signed pack verification, storage, activation, fallback, rollback), then verify it on each target OS.
7. Resolve the repository-wide red CI gate before treating any desktop-related claim as merge-ready.

None of these steps has been completed in this pass.

## 8. Test evidence relevant to this review

| Check                         | Command                                                                                                                                                                                                    | Exit | Result                                                        | Log                                                |
| ----------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---: | ------------------------------------------------------------- | -------------------------------------------------- |
| Local toolchain inventory     | `for tool in java gradle swift xcodebuild flutter dotnet; do if command -v "$tool" >/dev/null 2>&1; then printf "%s=%s\n" "$tool" "$(command -v "$tool")"; else printf "%s=NOT_FOUND\n" "$tool"; fi; done` |    0 | `flutter=NOT_FOUND`, `dotnet=NOT_FOUND`; `java=/usr/bin/java` | `local_toolchain.log`                              |
| PR #308 checks (context only) | `gh pr checks 308`                                                                                                                                                                                         |    1 | 10 failing checks; `mergeStateStatus=UNSTABLE`                | `pr308_checks.log`, `P00_INDEPENDENT_REVIEW.md` §3 |

No Flutter/Dart test command was run; there is no desktop pass/fail count to report. Focused backend (`81 passed`, exit 0) and frontend (`3 files, 24 tests`, exit 0) results cover other surfaces only.

## 9. Residual risks and blockers

- No local Flutter toolchain; no desktop build or test evidence exists for this execution.
- Localization is static with two locales; duplicated inline maps and ARB files need reconciliation.
- RTL is Arabic-only and visually unverified; font availability/licensing in packaged artifacts is unverified.
- No GULS dynamic-pack integration, so the desktop client cannot install, verify, or use downloadable packs.
- CI is red and `UNSTABLE`; no merge readiness is claimed.

**Final status: NOT READY — BLOCKED**
