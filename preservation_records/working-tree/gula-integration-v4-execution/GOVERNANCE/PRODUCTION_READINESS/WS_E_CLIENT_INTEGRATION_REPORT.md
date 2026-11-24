# Workstream E — Client Integration Contract Report

**Report ID:** HC-WSE-CLIENT-001
**Date:** 2026-11-18
**Program:** GULA Production Readiness Acceleration Program — WORKSTREAM E (Client Integration)
**Repository:** `gula-integration` · branch `integration/gula-unification-v1`
**HEAD (unchanged):** `2827c1ff1032918aa2541aa0b47bb7f2e5d6cac0`
**Classification:** `SYNTHETIC DEVELOPMENT / READINESS CONTRACTS ONLY` — no production activation
**Data:** synthetic fixture vocabulary only; no real patient data, national identifier or secret
**Decision status:** `GOVERNANCE/FINAL_DECISION.md` remains **HOLD**; MPI remains **REJECT**. Unchanged.

---

## 1. Scope and protection integrity

- All inspection of client trees was **read-only** (`ls`, `find`, `grep`, `sed`, file existence checks). No client
  application file was created, edited, deleted, formatted, built or executed.
- The read-only WS-D package `backend/app/health_core/integration/**` and WS-C `contracts/**` were imported as
  authoritative contract sources but never modified.
- `gula-platform` was **not written to**: read-only verification showed status `0` entries and HEAD `f478676b`.
- Protected artifacts verified by checksum after the work:
  - `GOVERNANCE/FINAL_DECISION.md` — md5 `effdfeaf10234678d83b2668c4489552` (HOLD text at lines 13, 36, 47).
  - `GOVERNANCE/IDENTITY_REMEDIATION/MPI_INDEPENDENT_AUDIT_FINDINGS.md` — md5 `ea3969d09aaf7b0b28a065838b44a594` (verdict `REJECT`).
  - `GOVERNANCE/IDENTITY_REMEDIATION/MPI_FINAL_INDEPENDENT_AUDIT.md` — md5 `1a02c01563c93b07a7cdb92c0462bf36` (line 80: `# REJECT`).
- No commit, push, merge, rebase, PR, deploy, `git add`, `git reset`, `git clean`, DDL, migration, production DB,
  real patient record, secret, new dependency, FastAPI router, route, `factory.py` or `main.py` change was performed.

---

## 2. Exact read-only client inspection findings

Discovery was performed over the checkout root. Extra directories `client/` (a small Vite/React shell) and
`contracts/sdk/dart/` (a generated Dart SDK) were observed but are not client application projects in the six
platform set and were not written to. Every statement below is backed by a concrete observed path.

| Platform | Project present? | Evidence observed (repo-relative) | API/client layer | Auth boundary | Error handling | Offline/outbox | Sync/conflict | Arabic RTL + a11y |
|---|---|---|---|---|---|---|---|---|
| **Web** | **YES** | `frontend-v3/package.json`, `frontend-v3/vite.config.ts`, `frontend-v3/index.html`, `frontend-v3/src/api/client.ts`, `frontend-v3/vitest.config.ts`, `frontend-v3/playwright.config.ts` | **PRESENT** — `src/api/client.ts`, `src/api/endpoints.ts`; `VITE_API_BASE_URL ?? "/api"`, same-origin demo `"/demo-api"`, `withCredentials`, `/auth/refresh` interceptor | **PRESENT** — `src/api/demoIsolation.test.ts`, `src/api/client.writeBarrier.test.ts` plus the interceptor | **PARTIAL** — `src/hooks/useApiError.ts` reads only legacy `detail`; `src/components/shared/AsyncBoundary.tsx` present | **ABSENT** — no `frontend-v3/src/offline` or `src/api/offlineOutbox.ts`; only monitoring types in `src/types/backend.ts`, simulated Outbox UI in `src/pages/devices/DeviceIntegrationWorkspacePage.tsx`, generated `frontend-v3/dist/sw.js` | **ABSENT** — no `src/sync` or `src/api/conflictResolver.ts`; `src/pages/patient-visit/PatientVisitReadinessPage.tsx` explicitly records version conflict/audit as unproven | **PRESENT** — `index.html` has `lang="ar" dir="rtl"`; `src/contexts/LocaleContext.tsx` maps `getLocaleDirection(...) === "rtl"`; `package.json` includes `vitest-axe` |
| **Android** | **YES** | `mobile/android/settings.gradle.kts`, `mobile/android/app/build.gradle.kts`, `app/src/main/java/io/gula/android/**` | **PRESENT** — `di/NetworkModule.kt` consumes `BuildConfig.API_BASE_URL`; `data/remote/interceptor/AuthInterceptor.kt` | **PRESENT** — `AuthInterceptor.kt`, `data/remote/interceptor/CertificatePinningInterceptor.kt`, `res/xml/network_security_config.xml` | **PRESENT** — `data/remote/interceptor/ErrorInterceptor.kt`, `data/repository/ParseError.kt`, `ui/components/core/GulaErrorView.kt` | **PRESENT** — `data/local/dao/SyncQueueDao.kt`, `domain/usecase/ProcessOfflineQueueUseCase.kt`, tests `ProcessOfflineQueueUseCaseTest.kt`, `SyncIntegrationTest.kt` | **PARTIAL** — `domain/usecase/SyncDataUseCase.kt`, `data/repository/SyncRepositoryImpl.kt`; only SQLite `OnConflictStrategy.REPLACE`, no `ResolveConflictsUseCase.kt`, no decision/audit record | **PARTIAL** — `res/values-ar/strings.xml`, `res/values-ar/themes.xml`; RTL/a11y completeness not certified by this pass |
| **iOS** | **NO** (sources only) | `mobile/ios/GulaAppDelegate.swift`, `Gula/Core/...`, `Gula/GulaTests/**` exist; **`mobile/ios/Gula.xcodeproj` and `mobile/ios/Gula.xcworkspace` are absent** — `find mobile/ios -type d -name '*.xcodeproj' -o -name '*.xcworkspace'` returned nothing. The only Xcode project outside archives is the Flutter macOS runner `mobile/desktop/macos/Runner.xcodeproj` — **not** an iOS app project | **PARTIAL (source only)** — `Gula/Core/Networking/APIClient.swift`, default `https://api.gula-platform.org/api/v1` | **PARTIAL (source only)** — `Gula/Core/Networking/APIAuthMiddleware.swift`, `Core/Auth/KeychainManager.swift` | **PARTIAL (source only)** — `Gula/Core/Networking/APIError.swift` | **PARTIAL (source only)** — `Core/Offline/SyncQueue.swift`, `SyncEngine.swift`, `NetworkSynchronizer.swift` | **PARTIAL (source only)** — `Core/Offline/ConflictResolver.swift`; no buildable/testable target inspected | **PARTIAL** — `Gula/UI/Theme/RTLManager.swift` has `@Published var isRTL: Bool = false` until an Arabic locale/saved language is set; `Gula/Resources/ar.lproj/Localizable.strings` present |
| **Flutter desktop** | **YES** | `mobile/desktop/pubspec.yaml`, `lib/**`, `macos/Runner.xcodeproj`, `macos/Runner.xcworkspace`, `linux/**`, `test/unit/**` | **PRESENT** — `lib/core/api/api_client.dart`, `lib/core/utils/constants.dart`, `lib/core/security/api_url_validator.dart` | **PRESENT** — `lib/core/auth/auth_manager.dart`, `lib/core/auth/secure_storage.dart` | **PARTIAL** — `lib/core/api/api_exceptions.dart` parses `detail`/`message` only, not canonical envelope fields or `detail_ar` | **PRESENT** — `lib/core/offline/database.dart`, `sync_queue_manager.dart`, `sync_engine.dart` | **PRESENT** — `lib/core/offline/conflict_resolver.dart` declares `localWins/remoteWins/lastWriterWins/manual/merge`, `ConflictRecord`, `ConflictResolution` | **PRESENT** — `lib/core/theme/theme_provider.dart` defaults `Locale('ar','IQ')`, `_isRtl = true`; `lib/l10n/app_ar.arb` present |
| **Hospital desktop** | **YES** | `hospital_desktop/requirements.txt`, `run.py`, `config.py`, `main.py`, `api_client.py`, `session.py`, `offline.py`, `l10n.py`, `tests/test_security_config.py` | **PRESENT** — `api_client.py`, host allow-list and base URL in `config.py` | **PRESENT** — `session.py` encrypted token store, bearer/refresh in `api_client.py` | **PARTIAL** — `api_client.py` reads legacy `detail` only (`ApiError`, `ValidationError`) | **PRESENT** — `offline.py` sqlite `sync_log` with pending/synced/failed states | **PARTIAL** — `offline.py::resolve_conflict` compares `updated_at` timestamps only; no immutable disposition/audit record | **PRESENT** — `main.py:64-66` sets Qt `RightToLeft` when `config.language == "ar"` (default `ar`); `l10n.py`, `widgets/dialogs.py:41-43` |
| **Expo mobile** | **YES** | `mobile-expo/package.json`, `app.json`, `App.tsx`, `README.md`, `src/speech/**`, `__tests__/SpeechRecognitionService.test.ts` | **ABSENT** — no `src/api` or `src/api/client.ts`; `App.tsx:39` says a production submit must call the authenticated GULA API; `README.md` states the example never sends data to a backend | **ABSENT** — no `src/auth` or token store | **PARTIAL** — `src/speech/types.ts` and `SpeechRecognitionService.ts` define speech-specific errors only | **ABSENT** — no `src/offline`; README documents only local draft save | **ABSENT** — no `src/sync`, no conflict decision or audit | **ABSENT** — Arabic UI copy and mic permission strings in `app.json`, but no `src/i18n`/`src/localization`, no locale library or direction/RTL code |

**Inspection conclusion:** six platform roots exist, but the iOS **Xcode project is absent**; Expo has no API, auth,
offline, sync or RTL/i18n layer; Web has no client outbox/conflict layer; Android and hospital desktop have no
auditable conflict decision layer; iOS has source-only layers and an LTR-by-default RTL manager; every real client's
error handling is partial against the canonical envelope. These are recorded as facts, not repaired by WS-E.

---

## 3. Files created (exclusive write ownership only)

| File | Purpose |
|---|---|
| `backend/app/health_core/client_integration/__init__.py` | Public re-export surface; explicitly states that validation ≠ integration. |
| `backend/app/health_core/client_integration/platforms.py` | `Platform`, `LayerKey`, `LayerStatus`, `ImplementationStatus`, `REQUIRED_LAYERS`. |
| `backend/app/health_core/client_integration/observations.py` | Immutable `OBSERVED_CLIENTS` snapshot with concrete evidence/absence-probe paths from §2; `verify_observation()` re-checks them on disk without writing. |
| `backend/app/health_core/client_integration/manifests.py` | Per-platform `ClientManifest` plus canonical target declarations (WS-C operations → real WS-D method bindings, auth, error envelope, offline, sync, RTL); `derive_implementation_status()`. |
| `backend/app/health_core/client_integration/validators.py` | Fail-closed `validate_manifest()` / `validate_all_manifests()` with structured reason codes; derives operations from `DOMAIN_OPERATIONS` and checks every contract family. |
| `backend/app/health_core/client_integration/report.py` | `build_coverage_report()` / `render_coverage_report()`; keeps contract validation separate from end-to-end verification. |
| `backend/tests/health_core/test_client_integration_manifests.py` | 22 positive/negative tests, including runtime idempotent replay and audited conflict decisions. |
| `backend/tests/health_core/test_client_integration_guards.py` | 5 static guards: no client/route/persistence/network surface, no skips, structured errors. |
| `GOVERNANCE/PRODUCTION_READINESS/WS_E_CLIENT_INTEGRATION_REPORT.md` | This report. |

No other file was written. All new files are uncommitted by design.

---

## 4. Contract model and fail-closed reasons

- **API compatibility:** operation names are derived at validation time from WS-C `contracts/catalogue.py::DOMAIN_OPERATIONS`
  (22 operations across 11 domains). A manifest missing or adding one fails with `MISSING_WS_C_OPERATION` /
  `UNKNOWN_WS_C_OPERATION`. Bindings must match the exact set of `SyntheticApiClient.__abstractmethods__` (20 real methods);
  invented methods fail with `UNKNOWN_CLIENT_METHOD`. The two WS-C domains `organization` and `facility` map explicitly to
  the one WS-D `organization_facility` method pair; this alias is declared, never inferred.
- **Authentication boundaries:** reuses WS-D `validate_boundaries()` and `is_permitted()`. Anonymous roles, anonymous
  reads/writes, viewer writes and any `bypass_paths` fail closed (`ANONYMOUS_ROLE`, `PUBLIC_WRITE`, `ANONYMOUS_ACCESS_ALLOWED`,
  `IMPLICIT_VIEWER_WRITE`, `BYPASS_PATH`). `PermissionModel.IMPLICIT` and non-exact role matching are rejected.
- **Error handling:** canonical field tuple is read from WS-D/WS-C `contracts/errors.py::ERROR_RESPONSE_BODIES`
  (`code`, `message`, `details`, `request_id`, `timestamp`, `detail`, `detail_ar`). Missing `detail_ar`, missing legacy
  `detail` or a claimed FHIR adapter fails. No FHIR adapter is claimed anywhere (F-03 remains an owner-gated gap).
- **Offline:** outbox, replay, event-id idempotence, deterministic `(occurred_at, sequence)` ordering and the exact
  `ApplyStatus` vocabulary are required; a durability claim fails because the sandbox is process-local only.
- **Synchronization:** the exact `ConflictStrategy`, `Disposition`, audit-record and no-silent-drop declarations are
  required; a clinical content merge claim fails (not implemented).
- **Arabic RTL + a11y:** locale `ar`, `Direction.RTL`, the five `RequirementKind` capabilities, contrast ≥ 4.5:1 and error
  announcement are required; the read-only WS-D requirement/surface catalogues are also revalidated.
- **Honesty gate:** `adapter_bound=True`, `end_to_end_verified=True` or `ImplementationStatus.IMPLEMENTED` always fail;
  an absent project claimed implemented fails with `ABSENT_PROJECT_CLAIMED_IMPLEMENTED`.

---

## 5. Requirements matrix

| # | Requirement | Status | Evidence |
|---|---|---|---|
| 1 | Read-only inspection of actual client trees; concrete paths; no inferred projects | **VERIFIED** | §2 above: 6 roots inspected, iOS project absence proven by `find`; `client/` and `contracts/sdk/dart/` explained; inspection commands are read-only. |
| 2 | Per-platform manifests + validators for all 6 layers, explicit NOT IMPLEMENTED/BLOCKED classification | **VERIFIED** | 6 `ClientManifest` objects; `derive_implementation_status()`; coverage table in §6; iOS `not_implemented`, all others `blocked`. |
| 3a | API compatibility with WS-C `DOMAIN_OPERATIONS`; mismatch fails closed | **VERIFIED** | 22 ops compared to catalogue; 20 abstract methods bound; negative tests `test_api_operation_mismatch_fails_closed`, `test_invented_client_method_fails_closed`. |
| 3b | Authentication boundaries: anonymous/bypass rejected; no implicit permissions | **VERIFIED** | Reuses WS-D boundary validator + `is_permitted`; negative tests `test_anonymous_writes_and_bypass_paths_fail_closed`, `test_implicit_permissions_fail_closed`. |
| 3c | Canonical error envelope + Arabic detail | **PARTIALLY VERIFIED** | Envelope/field declarations and validator verified; **real client handling remains partial in 4 apps and absent as a canonical layer in Expo** — a declaration cannot make a client parse an envelope. F-03/FHIR adapter still owner-gated. |
| 3d | Offline outbox/replay declarations | **PARTIALLY VERIFIED** | Declarations and validator verified; runtime replay idempotence proved on WS-D in-memory primitives. Real durability/outbox in clients is not verified (Android/Flutter/desktop have local queues only; Web/Expo absent). |
| 3e | Sync conflict decisions + audit declarations | **PARTIALLY VERIFIED** | Declarations, vocabulary checks and one audited `resolve_conflict` runtime test verified. Real audited conflict decisions are absent on Web, Expo, Android (SQLite REPLACE only) and partial on hospital desktop; iOS is source-only. |
| 3f | Arabic RTL + a11y declarations | **PARTIALLY VERIFIED** | Declaration/catalogue validator verified. Real a11y behavior is not certified: iOS defaults LTR, Android resources only, Expo absent, Web/Flutter/desktop have RTL mechanisms but no WS-E WCAG run. |
| 4 | Validators fail closed on missing layers / false implementation claims | **VERIFIED** | `LAYER_STATUS_MISMATCH`, `ABSENT_PROJECT_CLAIMED_IMPLEMENTED`, `UNVERIFIED_IMPLEMENTED_CLAIM`, `UNVERIFIED_ADAPTER_CLAIM`, `UNVERIFIED_END_TO_END_CLAIM`; negative tests in §7. |
| 5 | Positive + negative tests, no skips/xfakes, real assertions | **VERIFIED** | 27/27 scoped tests pass; guard test asserts AST-level no skip/xfail decorators and real assertions. |
| 6 | Clear contract-vs-e2e distinction in report | **VERIFIED** | §6 and §8; every coverage row has `end_to_end_verified = False`; rendered report states `End-to-end verified = NO`. |

---

## 6. Actual coverage classification (generated from validated manifests)

| Platform | Project present | Classification | Layers (present/partial/absent) | Manifest valid | End-to-end verified |
|---|---|---|---|---|---|
| web | YES | BLOCKED | 3 / 1 / 2 | YES | NO |
| android | YES | BLOCKED | 4 / 2 / 0 | YES | NO |
| ios | NO | NOT IMPLEMENTED | 0 / 6 / 0 | YES | NO |
| flutter | YES | BLOCKED | 5 / 1 / 0 | YES | NO |
| desktop | YES | BLOCKED | 4 / 2 / 0 | YES | NO |
| expo | YES | BLOCKED | 0 / 1 / 5 | YES | NO |

`Manifest valid = YES` means **the declaration is complete, WS-C/WS-D aligned and consistent with the read-only
filesystem observation**. It does **not** mean the layer works in the client. `End-to-end verified = NO` for every
platform: no client file was modified, no client build/test was run by WS-E, and no synthetic adapter was bound.

Representative blocking reasons recorded in code (first two per platform):
`web`: error_handling partial, offline_outbox absent; `android`: sync_conflict partial, arabic_rtl_a11y partial;
`ios`: project absent (`mobile/ios/Gula.xcodeproj`, `mobile/ios/Gula.xcworkspace`), api_client source-only;
`flutter`: error_handling partial, no SyntheticApiClient adapter bound; `desktop`: error_handling partial,
sync_conflict partial; `expo`: api_client absent, auth_boundary absent.

---

## 7. Exact commands and results

Run with the pinned toolchain `/tmp/opencode/mpi-venv/bin/python`.

```bash
# From backend/ — scoped WS-E deliverables
ENV=test RUNTIME_MODE=test PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=.:.. \
/tmp/opencode/mpi-venv/bin/python -m pytest tests/health_core/test_client_integration*.py -q --tb=short
# 27 passed, 1 warning in 0.70s
# (22 manifest/validator + 5 static guard tests)

# From repository root — lint
/tmp/opencode/mpi-venv/bin/python -m ruff check \
  backend/app/health_core/client_integration backend/tests/health_core/test_client_integration*.py
# All checks passed!

# From repository root — types
MYPYPATH=backend /tmp/opencode/mpi-venv/bin/python -m mypy \
  --config-file pyproject.toml backend/app/health_core/client_integration
# backend/app/domain/order_state.py:63: error: Function is missing a type annotation ...
# backend/app/domain/order_state.py:81: error: Function is missing a type annotation ...
# Found 2 errors in 1 file (checked 6 source files)
# ZERO errors attributable to the new client_integration files (pre-existing baseline).

# From backend/ — full synthetic Health Core suite
ENV=test RUNTIME_MODE=test PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=.:.. \
/tmp/opencode/mpi-venv/bin/python -m pytest tests/health_core -q --tb=short
# 652 passed, 4 failed, 1 warning in 7.50s
```

**Concurrent-change caveat (precise):** the first full-suite attempt failed at collection because a *different,
untracked* file `backend/tests/health_core/test_terminology_provenance.py` was mid-edit by a concurrent owner
(`SyntaxError` at line 22: `UCUM_CODES if False else UCUM_UNITS`). WS-E did not modify it. That file was fixed by its
owner before the second run. The second run's **4 failures are all in other workstreams' terminology files** —
`test_terminology_provenance.py::test_every_curated_entry_points_to_a_line_containing_its_code`,
`...::test_icd_codes_are_actually_tagged_as_icd10_in_the_offline_source`, and
`test_terminology_validators.py::test_loinc_malformed_codes_are_invalid[123-1]`,
`...::test_ucum_format_negatives_are_invalid[mmol//L]`. None references WS-E files; all WS-E tests pass in that same
run. No other workstream's file was touched to "fix" these results.

One unrelated pre-existing warning: Starlette `TestClient`/httpx deprecation.

---

## 8. Limitations (explicit, not presented as implemented)

1. **No end-to-end client behavior is verified.** All six platforms are `BLOCKED` or `NOT IMPLEMENTED`; no client
   screen talks to `SyntheticApiClient`. This is a contract/observation layer, not an adapter.
2. **Absence probes are scoped.** `verify_observation()` proves specific named paths exist or do not exist; it is not
   an exhaustive proof that no alternative implementation exists anywhere in a large client tree.
3. **iOS is not a project in this checkout.** Swift sources and XCTest files exist, but no `.xcodeproj`/`.xcworkspace`
   for the iOS app; no build or XCTest run was possible. The Flutter macOS runner Xcode project is a different project
   and was not counted as iOS.
4. **Expo has no API/auth/offline/sync/RTL layer.** The voice-draft example explicitly does not send data to a backend.
5. **Error handling is partial in real clients.** No observed client consumes the full canonical envelope with
   `detail_ar`; a real FHIR `OperationOutcome` adapter remains owner-gated (F-03).
6. **No a11y certification.** `vitest-axe`, Arabic ARB/strings and RTL flags were observed, not executed or audited;
   iOS `RTLManager` defaults to LTR until an Arabic locale/saved language is set.
7. **Offline remains process-local.** WS-D's outbox/replay is in-memory; no durability, broker, encryption or
   cross-device sync is claimed. Hospital desktop's legacy cache schema was observed only, never copied or executed.
8. **F-01/F-02 and the HOLD remain open.** This workstream does not change event semantics, runtime RBAC/ABAC,
   `GOVERNANCE/FINAL_DECISION.md` (HOLD) or MPI (REJECT).

---

## 9. Handoff requests (owner-gated)

1. Provide an owner-authorized follow-up workstream to implement real thin client adapters against
   `SyntheticApiClient` inside each client project; only then may a platform be reclassified toward `IMPLEMENTED`.
2. Supply the iOS Xcode project/workspace (or a buildable generated project) before any iOS test or RTL claim.
3. For Expo, add API/auth, canonical error handling, outbox/replay, conflict audit and RTL/i18n layers; re-run this
   validator with updated observations (write ownership stays with the Expo owner).
4. Extend real clients to consume the canonical envelope including `detail_ar`, and add the FHIR `OperationOutcome`
   adapter required by F-03 before any national API claim.
5. Add auditable conflict decisions (disposition + immutable audit) to Web/Android/hospital desktop; add a real
   client outbox to Web/Expo.
6. Run client-native test suites (`vitest-axe`, Gradle/JUnit, Flutter tests, PySide6 tests, Expo Jest) with real a11y
   evidence; WS-E did not execute them.
7. Re-run the exact commands in §7 after concurrent owners stop editing; the 4 terminology failures must be resolved
   by their owners before any whole-suite claim.

---

## 10. Bottom line

- Per-platform manifests and fail-closed validators for all six platforms: **implemented, tested, green**.
- Actual client integration: **NOT IMPLEMENTED / BLOCKED everywhere**; contract validation is not integration.
- Production decision: **HOLD unchanged**; MPI **REJECT unchanged**; no activation, no client file modified.

**End of WS-E report — no production activation performed.**
