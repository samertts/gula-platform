# P08 — i18n, RTL, and Fonts Across Surfaces

Program: GULA-GULS-021
Scope: Read-only review of `frontend-v3`, `mobile/android`, `mobile/ios`, `mobile/desktop`, and adjacent clients
Baseline: `main` at `2ee9e8bcb9d81e9cac6801f5dea9b86d59beaffa`
Review date: 2026-11-21
Status: **NOT READY — BLOCKED**

## 1. Purpose and boundary

This document consolidates the localization, right-to-left layout, and font evidence across the Web frontend and native/adjacent clients. It is based on `CONTEXT.md` in `/tmp/opencode/gula-guls-021-evidence/` and read-only source inspection. No client source was modified. No native build was run: `gradle`, `swift`, `xcodebuild`, `flutter`, and `dotnet` are `NOT_FOUND` locally; `java` is present at `/usr/bin/java`.

No human linguistic/clinical approval, font licence approval, merge, deployment, or production access is claimed.

## 2. Web frontend (`frontend-v3`)

| Area                  | Observed state                                                                                                                                                                                                                                                                                   | Source                                                                   |
| --------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------ |
| i18next resources     | `ar`, `en`, and Sorani exposed as `ckb` (from `ku.ts`); `fallbackLng: "en"`; no raw-key leakage configuration (`returnNull: false`)                                                                                                                                                              | `src/i18n/index.ts`, `src/i18n/ar.ts`, `en.ts`, `ku.ts`                  |
| Selectable locales    | `localeOptions` contains only approved local `ar`, `en`, `ckb`; legacy mapping `ku → ckb`, `tk → en`, `syr → en`; stored locale normalized via `gula.locale` in `localStorage`                                                                                                                   | `src/i18n/locales.ts`                                                    |
| Legacy catalogs       | `tk.ts` and `syr.ts` exist but are not registered as i18next resources; they are unverified and not publishable                                                                                                                                                                                  | `src/i18n/tk.ts`, `syr.ts`, `index.ts`                                   |
| RTL standard          | `containerAttributes()` emits `dir` and `lang`; logical CSS properties are enumerated; physical properties are explicitly forbidden for components                                                                                                                                               | `src/guls/rtl.ts`                                                        |
| PWA shell             | `VitePWA` `registerType: "autoUpdate"`; manifest `lang: "ar"`, `dir: "rtl"`; Workbox precache and image/font `CacheFirst` caches; language-list `NetworkFirst` cache (`guls-localization-v1`)                                                                                                    | `vite.config.ts`                                                         |
| GULS runtime          | `src/guls/registry.ts` imports the shared 14-entry registry; `runtime.ts` provides fail-safe resolution; `src/guls/offline/*` adds tokenized download with data-saver/metered/roaming and quota checks, archive verification, IndexedDB storage, activation/rollback, and offline catalog lookup | `src/guls/*`, `src/guls/offline/*`                                       |
| Pack caching boundary | Pack bytes are deliberately excluded from Workbox precache/runtime caches and stored in IndexedDB by the offline runtime                                                                                                                                                                         | `vite.config.ts` comment and `src/guls/offline/storage.ts`, `runtime.ts` |
| Font stack            | `--font-sans: "Tajawal", "Noto Naskh Arabic", ui-sans-serif, system-ui, sans-serif`; `--font-mono: "JetBrains Mono", ...`                                                                                                                                                                        | `src/index.css`                                                          |

The Web surface is the only surface in this execution with a newly implemented offline GULS pack layer. That layer is code plus focused tests, not a production deployment; the full frontend suite is still red (section 6).

## 3. Native and adjacent clients

| Surface                                         | Localization                                                                                                                     | RTL                                                                                  | Fonts                                                                                              | GULS pack integration |
| ----------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------ | -------------------------------------------------------------------------------------------------- | --------------------- |
| `mobile/android`                                | `values/strings.xml` and `values-ar/strings.xml`; encrypted `locale` preference defaults to `ar`; settings offers `ar`/`en` only | `LocaleManager.setLocale()`/`isRtl()` exist but are not called from application code | No `.ttf`/`.otf` assets found in repository                                                        | None                  |
| `mobile/ios`                                    | `CFBundleLocalizations=[en, ar]`, `ar.lproj`, `Localizable.strings`; `app_language` in `UserDefaults`                            | `RTLManager` and `ThemeManager` force semantic content attributes for Arabic only    | `UIAppFonts` references NotoKufiArabic and Inter binaries; font files not found in repository      | None                  |
| `mobile/desktop` (Flutter)                      | Custom `l10n.dart` maps plus `app_ar.arb`/`app_en.arb`; `ar_IQ`/`en_US`; fallback `ar_IQ`                                        | `ThemeProvider` sets `isRtl` for `ar` only                                           | `GoogleFonts.notoSansArabicTextTheme()` / `interTextTheme()`; no bundled font/licence assets found | None                  |
| `apps/gula-web-suite/android` (WebView wrapper) | Only `res/values/strings.xml`; web content supplies its own UI                                                                   | No independent RTL implementation observed                                           | No font assets observed                                                                            | None                  |
| `mobile-expo`                                   | No GULS-related localization integration found                                                                                   | Not assessed in this pass                                                            | Not assessed in this pass                                                                          | None                  |
| `hospital_desktop`                              | No GULS-related localization integration found                                                                                   | Not assessed in this pass                                                            | Not assessed in this pass                                                                          | None                  |
| `platform/ui/i18n`, `packages/uap`              | No GULS references found                                                                                                         | Not assessed in this pass                                                            | Not assessed in this pass                                                                          | None                  |

Adjacent clients may have their own unrelated localization mechanisms; the finding here is narrowly that none consumes the GULS registry or supports dynamic packs. Detailed native findings are in `P03_ANDROID_PLATFORM_REVIEW.md`, `P05_IOS_PLATFORM_REVIEW.md`, and `P06_DESKTOP_PLATFORM_REVIEW.md`.

## 4. Free/OFL font candidates and constraints

Research identified these free/OFL candidates (`CONTEXT.md`, section "Standards research (P04)"; Google Fonts METADATA/licence sources):

- **Noto Naskh Arabic** — Arabic body text; also referenced in the Web font stack.
- **Noto Sans Arabic** — Arabic UI text; used by Flutter desktop typography through `google_fonts`.
- **Noto Kufi Arabic** — Arabic display/UI text; referenced by the iOS `UIAppFonts` list and `FontManager`.
- **Noto Sans** — Latin companion for mixed-script UI.
- **Noto Sans Syriac Eastern / Noto Sans Syriac Western** — candidates only; selection is blocked on the East/West Syriac human decision (see `P04_LANGUAGE_STANDARDS_AND_REGISTRY.md`).

These are free, open-source font options. The platform constitution prefers open source and self-hosted assets; font files and their SIL Open Font License texts should be vendored or verified in deployment artifacts rather than assumed from a CDN at runtime. **No font binary or font licence file was found in the repository during this review.** Glyph coverage and shaping for Arabic, Sorani, any future Turkmen script, and Syriac have not been verified.

## 5. What remains unverified

1. Actual font files and licence texts in each build/deployment artifact (Web bundle, Android APK, iOS app bundle, desktop packages).
2. Offline font availability for the Web PWA font cache and Flutter's `google_fonts` runtime caching.
3. Glyph coverage, shaping, and fallback across Arabic, Sorani (`ckb`), and any future Turkmen/Syriac scripts; Syriac font choice is human-blocked.
4. RTL screenshots and layout tests for Arabic on every client, including mirrored icons, logical spacing, and non-reversal of numeric and clinical identifiers.
5. Native client builds and tests: `gradle`, `swift`, `xcodebuild`, `flutter`, and `dotnet` are `NOT_FOUND` locally; only `java` exists. No native build was run in this execution.
6. GULS dynamic-pack integration on every client other than Web; all native clients remain blocked.
7. Human linguistic and clinical approvals; Arabic and Sorani clinical catalogs remain blocked, Turkmen and Syriac remain inactive placeholders, and downloadable languages remain unpublishable.
8. Repository-wide CI is red; this is not a merge-ready state.

## 6. Verification evidence

| Check                              | Command                                                                                                                                                                                                    | Exit | Result                                                                                                                                                            | Log                                |
| ---------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---: | ----------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------- |
| Focused frontend GULS/i18n tests   | `npx vitest run --passWithNoTests --exclude 'e2e/**' src/guls/guls.test.ts src/guls/offline/offline.test.ts src/i18n/mobileNavResources.test.ts`                                                           |    0 | 3 files, 21 tests passed                                                                                                                                          | `frontend_focused_tests.log`       |
| Frontend typecheck                 | `npx tsc --noEmit -p tsconfig.json --pretty false`                                                                                                                                                         |    0 | clean                                                                                                                                                             | `frontend_typecheck.log`           |
| Frontend lint                      | `npm run lint -- --max-warnings=0`                                                                                                                                                                         |    0 | clean                                                                                                                                                             | `frontend_lint.log`                |
| Prettier check                     | `npx prettier --check src/guls/offline/*.ts vite.config.ts`                                                                                                                                                |    0 | clean                                                                                                                                                             | `frontend_prettier_check.log`      |
| Full frontend suite, GULS-021      | `npm test`                                                                                                                                                                                                 |    1 | `1 failed \| 17 passed (18)` files; `2 failed \| 76 passed (78)` tests; failures in `MobileBottomNav.test.tsx`                                                    | `frontend_full_tests.log`          |
| Full frontend suite, baseline main | `npm test`                                                                                                                                                                                                 |    1 | `1 failed \| 15 passed (16)` files; `2 failed \| 54 passed (56)` tests; same `MobileBottomNav.test.tsx` failures; component/test byte-identical at both revisions | `frontend_full_tests_baseline.log` |
| Focused backend, Python 3.12       | `PYTHONPATH=backend /tmp/opencode/gula-guls-020-venv/bin/python -m pytest -q backend/tests/localization backend/tests/test_error_contract.py`                                                              |    0 | 81 passed, 1 warning                                                                                                                                              | `backend_pytest_py312.log`         |
| Focused backend, Python 3.11       | `PYTHONPATH=backend python3.11 -m pytest -q backend/tests/localization backend/tests/test_error_contract.py`                                                                                               |    0 | 81 passed, 1 warning                                                                                                                                              | `backend_pytest_py311.log`         |
| Local toolchain inventory          | `for tool in java gradle swift xcodebuild flutter dotnet; do if command -v "$tool" >/dev/null 2>&1; then printf "%s=%s\n" "$tool" "$(command -v "$tool")"; else printf "%s=NOT_FOUND\n" "$tool"; fi; done` |    0 | `java=/usr/bin/java`; all native client toolchains `NOT_FOUND`                                                                                                    | `local_toolchain.log`              |
| PR #308 checks (context only)      | `gh pr checks 308`                                                                                                                                                                                         |    1 | 10 failing checks; `mergeStateStatus=UNSTABLE`                                                                                                                    | `pr308_checks.log`                 |

The focused frontend tests validate the new GULS runtime and i18n resource wiring only. They do not make the aggregate frontend suite green, and no native test was executed.

## 7. Residual risks and blockers

- Web has new offline pack code but the aggregate frontend suite is red and PWA/offline behavior is not verified in a browser at scale.
- All native clients lack GULS dynamic-pack integration and cannot be built locally here.
- Arabic-first RTL is implemented unevenly; no cross-client visual verification exists.
- Font assets and licences are unverified; no font binaries exist in the repository.
- Turkmen/Syriac standards, clinical approvals, and font choices remain human-blocked.
- CI remains red and `UNSTABLE`; no merge, production, or national readiness is claimed.

**Final status: NOT READY — BLOCKED**
