# Workstream D — Application Integration Readiness Report

**Report ID:** HC-WS-D-001
**Date:** 2026-11-18
**Program:** GULA Accelerated Parallel Health Core Development
**Repository:** `gula-integration` · branch `integration/gula-unification-v1`
**HEAD (unchanged):** `2827c1ff1032918aa2541aa0b47bb7f2e5d6cac0`
**Classification:** `SYNTHETIC DEVELOPMENT / READINESS CONTRACTS ONLY` — no production activation
**Data:** synthetic `SYN-` fixtures only; no real patient data, no national identifier, no secret

---

## 1. Read-only client inventory (inspected, NOT modified)

All paths below were read from the `gula-integration` checkout. **No file under
`frontend-v3/`, `mobile/`, `mobile-expo/`, `mobile/desktop/` or `hospital_desktop/`
was created, edited, deleted or reformatted by this workstream.** The inventory
is evidence for readiness planning, not a claim that the clients are integrated.

| Client | Stack (observed) | Test runner / config paths | API base URL + auth configuration | Arabic RTL + i18n | Synthetic / dev surfaces observed |
|---|---|---|---|---|---|
| **Web** (`frontend-v3/`) | React 19.2 + Vite 8 + TypeScript 5.7 + Tailwind 4; `src/api/client.ts` uses axios + TanStack Query | `package.json` (`test` → vitest, `test:e2e` → Playwright); `vitest.config.ts`, `vite.config.ts`, `playwright.config.ts`, `eslint.config.js`, `src/test/setup.ts`, `e2e/*.spec.ts` | `src/api/client.ts`: live base = `import.meta.env.VITE_API_BASE_URL ?? "/api"`; demo base is deliberately same-origin `"/demo-api"`; mode kept in `sessionStorage` key `gula.api-mode`; `withCredentials: true`, `/auth/refresh` response interceptor; example values in `.env.example`; dev proxy in `vite.config.ts` | `index.html` = `<html lang="ar" dir="rtl">`; `src/i18n/{ar.ts,locales.ts}` + `src/main.tsx` imports `@/i18n`; `src/contexts/LocaleContext.tsx` maps `getLocaleDirection(...) === "rtl"`; PWA manifest `lang: ar`, `dir: rtl`; several pages set `dir="rtl"`; `vitest-axe` present | Public **Demo Mode** with fixed synthetic personas (`DEMO_PERSONAS`, `syntheticDemoUser`, `startDemoSession`) in `src/api/client.ts`; `src/api/demoIsolation.test.ts`; `src/pages/auth/LoginPage.tsx`; synthetic-labelled workspace/finance/device pages (e.g. `DeviceIntegrationWorkspacePage.tsx`) |
| **Android** (`mobile/android/`) | Kotlin + Gradle KTS + Compose + Hilt/KSP; `applicationId iq.gula.lab` (namespace `io.gula.android`) | `mobile/android/app/build.gradle.kts` (`testInstrumentationRunner = androidx.test.runner.AndroidJUnitRunner`); `app/src/test/**` (JVM unit), `app/src/androidTest/**` (instrumented); sources under `app/src/main/java/io/gula/android/**` | `BuildConfig.API_BASE_URL` injected via `app/build.gradle.kts`; consumed by `di/NetworkModule.kt:88` and `data/remote/interceptor/AuthInterceptor.kt:62,104` for `/auth/refresh`; certificate pinning for `api.gula-platform.org` in `CertificatePinningInterceptor.kt`; `res/xml/network_security_config.xml` | `app/src/main/res/values-ar/{strings.xml,themes.xml}` alongside default `values/`; Compose UI under `ui/features/**` (Arabic resources present; RTL completeness not certified here) | Offline queue tests (`ProcessOfflineQueueUseCaseTest.kt`, `SyncIntegrationTest.kt`); no synthetic-patient demo screen identified in this read-only pass |
| **iOS** (`mobile/ios/`) | Swift / SwiftUI sources; Core layers for networking, auth, offline and security | XCTest sources in `GulaTests/` and `GulaUITests/` (e.g. `APIClientTests.swift`, `SyncEngineTests.swift`, `LoginUITests.swift`); Fastlane config `mobile/fastlane/Fastfile`; **no `.xcodeproj`/`.xcworkspace` for the iOS app is present in this checkout**, so the Xcode test-target config could not be inspected | `Core/Networking/APIClient.swift`: `api_base_url` from `UserDefaults`, default `https://api.gula-platform.org/api/v1`; access/refresh tokens in Keychain via `Core/Auth/KeychainManager.swift`; `APIAuthMiddleware.swift`, `CertificatePinner.swift` | `UI/Theme/RTLManager.swift` (`isRTL` from `Locale`/saved language, `ar_IQ` locale, flipped alignments); `Gula/Resources/ar.lproj/Localizable.strings` + `String+Localization.swift`; **default `isRTL = false` until locale/saved language is Arabic** — gap recorded in §6 | No synthetic/demo patient page identified; `IOSUpdateGate` and offline conflict resolver (`Core/Offline/ConflictResolver.swift`) exist |
| **Expo mobile** (`mobile-expo/`) | Expo 54 + React Native 0.81.5 + TypeScript strict | `package.json` (`test` → `jest --runInBand`); `jest.config.js` (`jest-expo`, `**/__tests__/**/*.test.ts`), `tsconfig.json`; `__tests__/SpeechRecognitionService.test.ts` | **No API client, base-URL setting or auth token store present**; `App.tsx` explicitly notes a production submit must call the authenticated GULA API; `README.md` states the example never sends data to a backend | Arabic UI copy and microphone permission strings in `app.json` / components, but **no locale library, no direction/RTL setting** in code — gap recorded in §6 | Voice-draft example only (`src/speech/**`, `VoiceInputButton`, `VoiceInputOverlay`): explicit mic press → review → append/replace; no clinical record write |
| **Flutter desktop** (`mobile/desktop/`) | Flutter/Dart (`sdk >=3.10`, `flutter >=3.13`), dio, drift/sqlite, Riverpod, go_router | `pubspec.yaml`; `test/unit/**`, `test/widgets/**`, `test/integration_test/**`, `macos/RunnerTests/`; `analysis_options.yaml` | `lib/core/utils/constants.dart`: `defaultApiUrl = https://api.gula-platform.org/api/v1`; `lib/core/auth/auth_manager.dart` + `secure_storage.dart`; URL validated by `lib/core/security/api_url_validator.dart`; `main.dart:90` passes the URL to `authProvider.initialize` | `lib/core/theme/theme_provider.dart` starts `Locale('ar','IQ')`, `isRtl = true`; `lib/l10n/{app_ar.arb,app_en.arb,l10n.dart}`; `flutter_localizations` in `pubspec.yaml` | No synthetic demo patient screen identified; offline/local DB present (inspected only) |
| **Hospital desktop** (`hospital_desktop/`) | Python/PySide6 desktop app (Qt), requests, local sqlite cache | `tests/test_security_config.py` (pytest); `requirements.txt`; no dedicated pytest config file in the directory | `config.py`: `DEFAULT_API_BASE_URL = https://api.gula-platform.org/api/v1` + `validate_api_base_url` host allow-list; `api_client.py` bearer token + refresh; `session.py` encrypted token store | `main.py:64-66` sets Qt `RightToLeft` when `config.language == "ar"` (default `ar`); `l10n.py` `ArStrings` / `EnStrings` + `TranslationManager`; `widgets/dialogs.py:41-43` sets layout direction | No synthetic/demo patient page identified. **Note (read-only observation):** `offline.py` local-cache DDL declares legacy columns with real-identifier names; WS-D did not copy, execute or modify that schema |

Inventory conclusion: the clients have **different stacks, test runners and configuration points**.
This is exactly why WS-D produced a framework-agnostic contract rather than client code. No
client-app file was changed, and no existing client screen is represented as an integrated
Health Core screen.

---

## 2. Files created (strictly inside the permitted writable set)

Production contracts — `backend/app/health_core/integration/`:

| File | Purpose |
|---|---|
| `__init__.py` | Single public surface for the six integration contracts; re-exports only, no logic. |
| `api_client.py` | `SyntheticApiClient` ABC (20 abstract methods: create/list for the 10 eligible domains), `DomainCode`, `ApiResult`, `InMemorySyntheticApiClient` fake. |
| `offline.py` | `OfflineOutbox`, `OutboxEntry`, `ReplayJournal`, `ApplyDecision`/`ApplyStatus`, `aggregate_key`, `replay`. |
| `conflicts.py` | `ConflictStrategy`, `ConflictCase`, `ConflictDecision`, `EventDisposition`, `AuditRecord`, `assert_no_silent_drops`, `resolve_conflict`. |
| `auth_boundaries.py` | `Role`, `Operation` (20), `AuthBoundary`, `DEFAULT_BOUNDARIES`, `validate_boundaries`, `assert_valid_boundaries`, `is_permitted`. |
| `arabic_rtl_a11y.py` | `A11yRequirement` catalogue (5 kinds), `SurfaceAnnotation`/`UiSurfaceAnnotation` (15 required surfaces), `validate_requirement_catalogue`, `validate_surfaces`. |

Tests — `backend/tests/health_core/` (new files only):

| File | Tests |
|---|---:|
| `test_integration_api_client.py` | 10 |
| `test_integration_offline.py` | 12 |
| `test_integration_conflicts.py` | 12 (parametrised) |
| `test_integration_auth_boundaries.py` | 11 |
| `test_integration_arabic_rtl_a11y.py` | 14 |
| `test_integration_cross_contract.py` | 3 |
| **Total** | **62** |

Report — `GOVERNANCE/ACCELERATION/WS_D_APP_INTEGRATION_REPORT.md` (this file).

No other file was created or modified by WS-D.

---

## 3. Contracts (real, testable behaviour)

### 3.1 `api_client.py` — shared synthetic API client
- `DomainCode` enumerates the **exact 10 readiness-eligible domains** from
  `GOVERNANCE/ACCELERATION/PHASE_ZERO_VERIFICATION.md` §2 (practitioner, organization/facility,
  medical record, encounter, diagnosis, observation, lab order, specimen, lab result, result
  verification). Patient Master Record and the cross-lab patient timeline are **not** included.
- Every operation requires explicit `tenant_id` and `patient_ref: PatientRef` keyword arguments.
  The fake validates the tenant shape as synthetic, resolves the patient through the shared
  `PatientIdentityPort`, and refuses unknown (`UnknownPatientError`) or cross-tenant
  (`TenantMismatchError`) references. It never creates a patient implicitly.
- `InMemorySyntheticApiClient` stores process-local, immutable `ApiResult` records and emits one
  shared `DomainEvent` per create, using `EventType`/`AggregateType` from `common` — directly
  consumable by `OfflineOutbox`. No HTTP library, host, port, credential or transport exists.

### 3.2 `offline.py` — outbox + deterministic replay
- `OfflineOutbox.enqueue` assigns monotonic sequences starting at 1; re-enqueue of an identical
  event is idempotent, while reuse of an `event_id` with a different payload raises
  `InvalidStateTransitionError`.
- `ordered_entries()` sorts by `(occurred_at, sequence)`; `entries` preserves enqueue order.
  Ordering is therefore deterministic and testable even when events arrive out of time order.
- `ReplayJournal.apply` is idempotent by `event_id` and advances each tenant-scoped aggregate
  one version at a time. Divergent (same version), stale and gapped versions each produce an
  explicit `ApplyDecision(status=CONFLICT, reason=…)`; no event is applied twice or discarded.

### 3.3 `conflicts.py` — explicit resolution with audit
- Strategies: `REJECT`, `KEEP_FIRST`, `KEEP_LAST_WITH_AUDIT`. Candidates are sorted by
  `(occurred_at, event_id)` and decision/audit ids are SHA-256 derived, so results are stable
  across input order and repeated calls.
- Every candidate event receives an `EventDisposition`. Every non-accepted event receives an
  `AuditRecord` carrying conflict id, event id, strategy, action, tenant and reason.
  `assert_no_silent_drops` fails closed if counts, ids or audit references diverge.

### 3.4 `auth_boundaries.py` — declarative boundaries, no implementation
- 20 operations (read/write per eligible domain) and six synthetic named roles plus
  `Role.ANONYMOUS` (reserved so it can be *rejected*). No token, session, credential, HTTP
  header or login flow is implemented.
- `validate_boundaries` rejects missing/duplicate/unknown operations, anonymous reads,
  **public writes** (`PUBLIC_WRITE`), any declared bypass path (`BYPASS_PATH`), anonymous as a
  required role, and viewer write grants.
- `is_permitted` uses exact role matching — no hierarchy, no implicit escalation, and it returns
  `False` for any invalid boundary set (fail-closed).

### 3.5 `arabic_rtl_a11y.py` — Arabic-first RTL / WCAG AA catalogue
- Five structured requirement records: field labels (3.3.2), direction (3.1.1), contrast
  (1.4.3, ≥ 4.5:1), focus (2.4.7), error announcement (3.3.1 / 4.1.3), each with Arabic and
  English text.
- 15 required UI surfaces across web, Android, iOS, Flutter desktop and Expo; every
  `UiSurfaceAnnotation` carries locale, direction, localized labels, contrast ratio, focus and
  error-announcement flags. `validate_surfaces` reports missing/duplicate surfaces, non-Arabic
  locale, non-RTL direction, missing labels, low contrast, missing focus and missing error
  announcement. This is a **target contract**, not a certification of existing client code.

---

## 4. Verification evidence

Command (exact, from `…/gula-integration/backend`):

```
ENV=test RUNTIME_MODE=test PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=.:.. \
  /tmp/opencode/mpi-venv/bin/python -m pytest tests/health_core/test_integration_*.py -q --tb=short
```

| Gate | Result |
|---|---|
| WS-D scoped tests | **62 passed / 0 failed** (Python 3.12.13, pytest 9.1.1) |
| Full `tests/health_core/` (includes shared AST sandbox guard + other workstreams) | **349 passed / 0 failed** |
| AST guard `test_sandbox_guards.py` over the expanded `app/health_core` package | **PASS** (no forbidden MPI/DB/network import or name) |
| Ruff (only WS-D paths, line length 100, double quotes) | **All checks passed** |
| mypy `--strict` on `app/health_core/integration` (repo config) | **Success: no issues found in 6 source files** |
| `compileall` on WS-D sources/tests | Exit 0 |
| `FINAL_DECISION.md` md5 | `effdfeaf10234678d83b2668c4489552` — unchanged (HOLD intact) |
| MPI audit documents md5 | both unchanged (REJECT intact) |
| Git HEAD / commits / pushes | unchanged; no commit, push, merge, rebase, PR or deploy by WS-D |
| Pre-existing uncommitted entries | baseline 463 checked: **no baseline entry removed or state-changed**; the 13 new entries are only the 12 code/test files plus this report (§2); other concurrent workstreams added the remainder |
| `factory.py` / `main.py` / production DB / migrations | untouched |

---

## 5. Classification and explicit statements

**Classification:** integration *readiness* — framework-agnostic Python contracts, in-memory
fakes and declarative validators. Nothing here is a runnable client screen, a production API
adapter, or an activated Health Core feature.

- **No identity bypass.** All patient access goes through the shared `PatientIdentityPort`;
  WS-D never imports or calls MPI/NHID/citizen/canonical-patient code and never accepts a real
  identifier. Unknown and cross-tenant references fail closed.
- **No production auth shortcut.** The auth module is declarative only; anonymous access and
  bypass paths are actively rejected. No token, session, cookie or credential is issued, read
  or accepted by WS-D.
- **No client-app modifications.** Web, Android, iOS, Expo, Flutter desktop and hospital desktop
  trees were inventoried read-only; zero files changed there.
- **No production activation.** `app/factory.py` and `app/main.py` were not touched; no route,
  feature flag, wiring, migration, DDL, schema change or production database access exists.
- **No fabricated links.** Every client path in §1 was observed in the checkout; the missing
  iOS Xcode project and the Expo API/RTL gaps are reported as gaps, not inferred as present.
- **No real patient data or secrets** are contained in fixtures, tests or this report.

---

## 6. Residual limitations (handoff, owner-gated)

1. **Not an integration.** These contracts do not make any client talk to a backend. A future,
   owner-authorised workstream must implement thin client adapters against `SyntheticApiClient`
   and add real a11y evidence; WS-D deliberately produces no client code.
2. **Client gaps observed:** Expo has no API client/auth/RTL/i18n; iOS `RTLManager` defaults to
   LTR unless the locale or saved language is Arabic; the iOS Xcode project is absent from this
   checkout; hospital-desktop local cache DDL contains legacy real-identifier-shaped columns
   (read-only observation — WS-D copied none of it). None of these were fixed here.
3. **A11y annotations are targets.** `DEFAULT_SURFACE_ANNOTATIONS` describes the required state;
   it is not evidence that the 15 existing client surfaces pass WCAG AA. Existing client a11y
   tests (e.g. `vitest-axe`) were not executed as part of this scoped run.
4. **Offline scope.** The outbox is in-memory and process-local: no durability, real broker,
   compaction, encryption or cross-device sync. Conflict resolution records decisions and
   audit but does not merge clinical content.
5. **Version model is linear per aggregate.** Gaps and divergent versions are detected; automatic
   three-way merge and clinical-safety adjudication are intentionally out of scope.
6. **Final decision remains HOLD and MPI remains REJECT.** While those stand, no synthetic
   contract may be represented as clinically usable or as a national deployment capability.
7. **Governance status:** this report and the 12 new files are uncommitted by design; integration
   into any branch, CI gate or release requires the Program Director's explicit decision.

---

**End of WS-D report — no production activation performed.**
