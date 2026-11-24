# QA AUDIT — PROGRAM-GULA-PARALLEL-001 (AGENT 09)

**Agent:** A09 — Testing & Quality Assurance auditor
**Date:** 2026-11-19
**Wave:** A (parallel read-only discovery)
**Scope:** existing test estate, test effectiveness, missing-category cross-reference, CI test wiring, stored test evidence
**Report status:** EVIDENCE-BASED; NO TESTS EXECUTED BY THIS AUDIT

---

## 0. Authorization and method (Arabic: التفويض والمنهجية)

| Constraint | Compliance |
|---|---|
| Read-only on all Wave A source/config/test files | ✅ No source, config, or test file was written |
| Write only to 3 owned paths under `docs/parallel-program/qa/` | ✅ This file + `REGRESSION_TEST_PLAN.md` + `TEST_RESULTS.md` |
| No git state changes | ✅ Only `git status`, `git ls-files`, `git diff`, `git show` (read-only) |
| No full suite / E2E / build execution | ✅ No test, gate, or build command was run |
| 378 protected paths of user work | ✅ Reported only; none modified |
| Evidence-based findings with `path:line` | ✅ Every finding cites a concrete path/line or exact excerpt |
| Speculation explicitly labeled | ✅ See A09-008 impact statement |

**Method:** read-only `find`/`wc` counts, `grep`, `sed`/`read`, `git status --porcelain`, `git ls-files`, and a **read-only in-memory Python AST parse** (`python3 - <<'PY'`) that parsed test source text without importing modules or writing files. Speculation is marked `[UNVERIFIED — Wave D]`.

**Protected files encountered (report-only):** `frontend-v3/package.json` (`M`), `frontend-v3/src/components/navigation/MobileBottomNav.test.tsx` (`M`), `backend/tests/test_comprehensive.py` (`M`), all of `backend/tests/communication_providers/**` and `backend/tests/health_core/**` (untracked user work), `.github/workflows/frontend-pwa.yml` and `.github/workflows/security-hardening.yml` (user-modified). None were touched.

---

## 1. Test inventory (verified counts — read-only `find`/`wc`)

### 1.1 Backend (pytest)

| Category | Path | Verified count | Ownership note |
|---|---|---:|---|
| All files under `backend/tests/` | `backend/tests/**` | **729** files incl. caches / **362** non-cache | — |
| Test functions (`test_*.py` files) | `backend/tests/**` | **335** files | 219 tracked, **116 untracked (USER)** |
| `test_*.py` anywhere in `backend/` | `backend/**` | **377** files | includes non-`tests/` copies |
| `conftest.py` | `backend/tests/**` | **5** | — |
| AST-parsed test functions | `backend/tests/**` | **4,379** functions | static parse only |
| `health_core` | `backend/tests/health_core/` | **43** `test_*.py` | untracked USER tree |
| `unit` | `backend/tests/unit/` | **31** `test_*.py` | mixed tracked/untracked |
| `kernel` | `backend/tests/kernel/` | **41** | — |
| `identity` | `backend/tests/identity/` | **23** | — |
| `blood_bank` | `backend/tests/blood_bank/` | **9** | — |
| `communication` | `backend/tests/communication/` | **8** | untracked USER |
| `kernel_hardening` | `backend/tests/kernel_hardening/` | **7** | — |
| `integration` | `backend/tests/integration/` | **5** | — |
| `notifications` / `communication_providers` | — | **4 / 4** | latter untracked USER |
| `security` / `migrations` / `contracts` / `booking` | — | **1 / 1 / 1 / 1** | — |
| `skills` | `backend/tests/skills/` | **0** `test_*.py` | helper packages only |

**Discrepancy note (`85+ files claimed`):** the verified on-disk count is **335** `test_*.py` files under `backend/tests/` (plus 42 elsewhere in `backend/`), not 85+. The claimed figure is stale or counts a different subset. Historical documentation likewise does not reconcile with the current tree: `GOVERNANCE/NATIONAL_INTEGRATION/ADVERSARIAL_REVIEW_RECORD.md:15` claims `773 passed` in `tests/health_core` while only 43 test files exist there; `reports/PHASE_10_IMPLEMENTATION.md:69` claims `38 passed / 11 files` while 15 frontend test files exist now. These are **different trees/times**, not a current measurement.

### 1.2 Frontend v3 (Vitest / Playwright)

| Category | Path | Verified count |
|---|---|---:|
| Unit/component test files | `frontend-v3/src/**/*.test.*` | **15** (7 `.test.tsx`, 8 `.test.ts`) |
| Test cases (`it(`/`test(`) | same | **54** occurrences |
| E2E spec files | `frontend-v3/e2e/*.spec.ts` | **12** (+1 `helpers.ts`) |
| E2E test declarations | same | **22** `test(` occurrences (one spec loops over 9 viewports → runtime count higher) |
| Snapshot files / `toMatchSnapshot` | `frontend-v3/src/**` | **0 / 0** (no trivial snapshots present) |
| `vitest-axe` in devDependencies | `frontend-v3/package.json:59` | present |
| Config files | `playwright.config.ts`, `vitest.config.ts` | 1 each (both clean/unmodified) |

### 1.3 Other test surfaces

| Surface | Verified count | Character |
|---|---:|---|
| `GLOSI/tests/` | **1** `test_registry.py` (+`.pyc`) | Python registry test |
| `test_library/` | **2** test modules (`test_library_demo.py`, `test_search.py`) + 2 support files | Python |
| root `tests/` | **14** files | chaos/load/stress/recovery/spike **scripts** (`.sh`, `.js`, `.py`, `.yaml`), not pytest unit tests |
| root `k6/` | **1** (`k6/load_test.js`) | load test |
| Other pytest surfaces | `nhop-platform/tests`, `platform/tests`, `mobile-expo/__tests__`, `scripts/tests`, `hospital_desktop/tests`, `assessment/testing`, `docs/testing` | present, out of A09 primary scope |
| Config files repo-wide | Playwright **1**, Vitest **3**, Jest **1** | `apps/gula-platform-ui-refresh`, `apps/gula-web-suite`, `frontend-v3`, `mobile-expo` |

---

## 2. Missing-category cross-reference — **do not claim absent**

Per instructions, each requested category was checked against existing files. **All seven categories exist in some form**; the gaps are depth/wiring, not absence.

| Requested category | Present? | Evidence | Real gap (if any) |
|---|---|---|---|
| E2E | ✅ Yes | 12 specs in `frontend-v3/e2e/`; `playwright.config.ts:1-39`; `.github/workflows/frontend-e2e.yml:34-41` | Chromium-only project (A09-009); branch trigger gap (A09-003); hardcoded chromium path (A09-008) |
| Contract tests | ✅ Yes | 14 files incl. `backend/tests/contracts/test_integration_envelope.py`, `backend/tests/health_core/test_contracts_*.py` (6), `test_clinical_gateway_contracts.py`, `test_error_contract.py` | `verify:contracts` governance gate not wired in CI (A09-011) |
| Integration tests | ✅ Yes | `backend/tests/integration/` 5 files (e.g. `test_identity_bundle.py`, `test_integration_inbox.py`); `health_core/test_integration_*.py` | 7 migration tests skip without DB URL (A09-013) |
| Accessibility (vitest-axe) | ✅ Yes | `frontend-v3/src/components/shared/PageComponents.a11y.test.tsx:3,13-16`; `.../workspace/WorkspaceSelector.a11y.test.tsx:3,53-55`; `backend/tests/health_core/test_integration_arabic_rtl_a11y.py` | Only 2 FE components; `color-contrast` disabled in both; no CI axe gate (A09-010) |
| Security tests | ✅ Yes | 40+ files, e.g. `backend/tests/test_security.py`, `test_security_regression.py`, `test_tenant_isolation_matrix.py`, `backend/tests/security/test_security_headers.py`, `unit/test_webauthn_hardening.py` | One security-intent test is a no-op (A09-001) |
| Offline tests | ✅ Yes | `backend/tests/test_offline_sync.py`, `test_offline_conflict_synthetic.py`, `health_core/test_integration_offline.py` | No browser-level offline E2E (observation, not "missing") |
| Migration tests | ✅ Yes | `backend/tests/migrations/test_migration_graph_integrity.py`, `test_migrations.py`, `test_migration_resilience.py`, 4 identity migration tests | Strict PG16 migration schema gate documents 119 failures (A09-004); skips (A09-013) |

**Conclusion:** no whole category is missing. Findings focus on effectiveness, determinism, and wiring.

---

## 3. Ineffective / fake test evidence

### 3.1 Confirmed no-op and unfalsifiable assertions

| ID | Evidence (exact excerpt) | Why ineffective |
|---|---|---|
| A09-001 | `backend/tests/test_comprehensive.py:675-687` — docstring `"""Production mode must fail without SECRET_KEY."""`, `result = subprocess.run(...)`, then `assert True` | `result.returncode` / stderr never inspected; assertion is unfalsifiable. **Pre-existing in HEAD** (`git show HEAD:...` shows same line), but file is user-modified elsewhere → report only. |
| A09-005a | `backend/tests/test_db_adaptive.py:188` — `assert ec2["refused"] != 99999 or True  # only fails if internal state leaked` | `or True` makes it **always pass**; comment contradicts behavior. File is clean/tracked. |
| A09-005b | `backend/tests/communication_providers/test_secrets.py:39` — `assert "/run/secrets" in os.environ.get("PATH", "") or True  # placeholder guard` | Same unfalsifiable pattern; untracked USER file → report only. |
| A09-012a | `backend/tests/test_niam.py:336` and `:379` — `assert True` after `await svc.deactivate_person(...)` / `await svc.terminate(...)` | Only proves "no exception"; no state verification. Files clean/tracked. |
| A09-012b | `backend/tests/identity/test_identity_service.py:152` — `assert True  # Might not generate all` | Redundant placeholder after one real assertion. File clean/tracked. |

**Not flagged (verified legitimate):** `or True` in side-effecting lambdas (`test_telegram_webhook_security.py:80`, `test_hard_scenarios.py:291,309`, `test_background.py:65`) is a return-value idiom, not an assertion. Multiple `pass` occurrences in `test_document_intelligence.py:441-490` are mock/no-op methods; `integration/test_identity_bundle.py:90-95` uses `try/except/else` with an explicit `AssertionError`. No snapshots exist (`0` files, `0` `toMatchSnapshot`).

### 3.2 Skip / TODO scan

- **20** pytest skip/xfail call sites in `backend/tests/**` (path-exact list available in working notes). Most are legitimate environment guards: `pytest.skip("MIGRATION_DATABASE_URL or DATABASE_URL is required")` (`identity/test_clinical_gateway_migration_phase10b.py:14`), 7 blood-bank `skipif(not POSTGRES_URL, ...)` markers, 4 bcrypt-conditional skips (`test_security.py:113,122,130,138`).
- `backend/tests/test_hard_scenarios.py:348,359` — `pytest.skip("LabResult model not found — skipping")` can mask a model-regression as a skip (A09-013).
- **0** frontend `describe.skip` / `it.skip` / `test.todo` / `xit` / `xdescribe` occurrences.
- TODO/FIXME grep hits in tests are domain assertions about *"NOT IMPLEMENTED"* contract text (e.g. `test_terminology_checkdigit.py:178`), not abandoned test bodies.
- **AST scan:** 4,379 test functions parsed; **60** contain no direct `assert`, `raise`, `pytest.raises` or `pytest.fail`. Sampling shows most delegate to helper assertions (`_assert_release_denial` at `test_lims_release_capability_gate.py:28-32`, `_assert_operation_outcome` at `unit/test_fhir_http_endpoints.py:205`, `_run` at `test_startup_guard.py:57-91`). A few are explicit smoke tests (`test_observability_invariants.py:128-144`: "Must not raise" / "Should be idempotent") — weak but intentional (A09-012c, P3). This is an **observation**, not a 60-test defect claim.

---

## 4. CI test wiring review (PROGRAM_CONTROL §5)

| Gate command (exists in manifest) | Wired in CI? | Evidence |
|---|---|---|
| backend `pytest tests/` | ✅ `ci.yml:288-301` (`cd backend; python -m pytest tests/ -v --timeout=60 -x`); `make test` at `Makefile:207-208`; nightly `nightly.yml:112-121` | runs with PostgreSQL+Redis services |
| backend clinical safety regression subset | ✅ `ci.yml:266-286` — all 7 referenced files verified present | — |
| backend identity/security/migration gates | ✅ `iam-hardening.yml:46,109,143,194` — all 8 referenced files verified present | runs `-m "not integration"` |
| frontend `npm test` (vitest) | ⚠️ Only `iam-hardening.yml:143` (`npm --prefix frontend-v3 run test -- --run`); **not in `ci.yml`** | inherits `--passWithNoTests` (A09-002) |
| frontend `test:e2e` | ⚠️ Not invoked via script; `frontend-e2e.yml:38` uses `npx playwright test` directly (functionally equivalent) | — |
| `check:bundle` | ✅ `frontend-bundle-budget.yml:43` | — |
| `typecheck` / `lint` | ✅ `iam-hardening.yml:147-149`, `frontend-pwa.yml:75-76` (user-modified workflow) | — |
| `verify:unification`, `verify:contracts`, `verify:integration-boundary`, `verify:data-sources`, `verify:audit-artifacts`, aggregate `check` | ❌ **Zero matches repo-wide in `.github/workflows/`** (verified by grep) | commands exist at `frontend-v3/package.json:14-21` but are never executed in CI (A09-011) |
| `test:coverage` | ❌ Not wired; declared at root `package.json:14`; provider absent (A09-007) | — |
| `test:watch` | N/A (interactive) | — |

**Trigger gap (A09-003):** `ci.yml:4-8` pushes only `main, staging, release/*`; `frontend-e2e.yml:4-12` only `main, release, develop`; `iam-hardening.yml:4-8` pushes only `main, feat/iam/**`. The program branch `integration/gula-unification-v1` (`PROGRAM_CONTROL.md:30`) triggers **no** test workflow on push. PRs to `main` would trigger `ci.yml`, `frontend-e2e.yml` (frontend paths), and `iam-hardening.yml`.

**Note on workflow ownership:** `.github/workflows/frontend-pwa.yml` and `.github/workflows/security-hardening.yml` are user-modified (PROGRAM_CONTROL §2.2); `frontend-e2e.yml`, `ci.yml`, `iam-hardening.yml` were read only in Wave A and fall under A08's CI scope.

---

## 5. Stored failing-test evidence — verified vs claimed

**Verified by this audit (filesystem facts only):**
- `0` JUnit/XML result files matching test/junit/pytest/result/artifact anywhere in the repo.
- `0` `.log` files (non-`node_modules`) anywhere in the repo — no raw pytest/vitest/playwright output committed.
- The directories searched: `STATUS/`, `EVIDENCE/`, `reports/`, `docs/reports/`, `GOVERNANCE/`, `GLOSI/REPORTS/`, `assessment/reports/`.

**Claimed in documentation (NOT re-executed, NOT verified by A09):**

| Source (path:line) | Claim | Status |
|---|---|---|
| `GOVERNANCE/NATIONAL_TESTING_STRATEGY.md:55` | E-001 strict migration-only PG16 clone: **753 passed / 119 failed / 0 skipped** (53 modules / 872 tests, exit 1) | DOCUMENTED FAILURE — unverified here |
| `GOVERNANCE/NATIONAL_TESTING_STRATEGY.md:57` | E-002 repeat: 750 / 122 (119 reproduced + 3 self-poisoned, F-005) | DOCUMENTED FAILURE — unverified here |
| `GOVERNANCE/NATIONAL_TESTING_STRATEGY.md:56,58-59` | E-003 SQLite control 872 passed; 194 synthetic passed; E-062 12 passed | DOCUMENTED PASS — unverified here |
| `GOVERNANCE/NATIONAL_INTEGRATION/ADVERSARIAL_REVIEW_RECORD.md:101-103` | NR-011 FK test: 1 passed in isolation; **1 failed / 1658 deselected when co-collected** with `tests/identity` (`NoReferencedTableError: niam_adaptive_mfa_sessions.session_id → niam_user_sessions.id`); broad selection **1654 passed / 4 skipped / 1 failed** | DOCUMENTED INTERMITTENT FAILURE — unverified here |
| `GOVERNANCE/NATIONAL_INTEGRATION/status_registry.json:472` | Same broad-regression disclosure recorded in machine-readable registry | DOCUMENTED — unverified here |
| `GOVERNANCE/NATIONAL_INTEGRATION/status_registry.json:529,583` | Later full-suite runs **4913 passed / 27 skipped** and final-tree **4945 passed / 27 skipped / 203 warnings**, exit 0 | DOCUMENTED PASS — unverified here; supersedes earlier numbers per `:584` |
| `GOVERNANCE/REPOSITORY_UNIFICATION_REPORT.md:56` | Full backend suite **3135 passed / 27 skipped**, 577.65 s | DOCUMENTED PASS — unverified here |
| `reports/discovery/17_RISK_REGISTER.md:39` | Risk R16 "No E2E tests" — **contradicted** by 12 Playwright specs present today; stale risk record | STALE CLAIM |

**Interpretation:** the repository contains internally consistent *narrative* evidence, including disclosed failures, but **no machine-verifiable artifacts**. A09 did not execute any gate; therefore no pass/fail result is asserted by this audit. See `TEST_RESULTS.md`.

---

## 6. Findings register

Format: ID · Severity · Title · Evidence · Affected components · Root cause · Safe-fix possible? · Approval required?

### A09-001 — P1 — Production secret-guard test is a no-op (`assert True`)
- **Evidence:** `backend/tests/test_comprehensive.py:675-687` — docstring `Production mode must fail without SECRET_KEY.`; `result = subprocess.run([...], capture_output=True, text=True)`; line 687: `assert True`. `result.returncode` never read. Same line exists at HEAD (`git show HEAD:...`).
- **Affected components:** backend config/startup security assurance; A04 (Security), A07 (Backend).
- **Root cause:** placeholder assertion left in a migrated test; no return-code/stderr check.
- **Safe-fix possible?** **No** — file is user-modified (` M backend/tests/test_comprehensive.py`, protected).
- **Approval required?** **Yes** — user must release the file; A04 must review the intended security assertion before Wave C.

### A09-002 — P1 — Frontend unit-test gate can pass with zero tests
- **Evidence:** `frontend-v3/package.json:13` `"test": "vitest run --passWithNoTests --exclude 'e2e/**'"`, `:22` same flag; root `package.json:13-15` delegates; `.github/workflows/iam-hardening.yml:143` invokes that script.
- **Affected components:** frontend-v3 quality gate; all frontend regression assurance; A08, A09.
- **Root cause:** `--passWithNoTests` suppresses the natural "no tests found" failure, masking collection errors or an empty suite.
- **Safe-fix possible?** **No** — `frontend-v3/package.json` is user-modified (PROGRAM_CONTROL §2.2).
- **Approval required?** **Yes** — user release + A08 gate-owner sign-off (changes CI semantics).

### A09-003 — P1 — Test workflows not triggered on the integration branch
- **Evidence:** `.github/workflows/ci.yml:4-8` (`branches: [main, staging, 'release/*']`), `frontend-e2e.yml:4-12` (`[main, release, develop]`), `iam-hardening.yml:4-8` (`main`, `feat/iam/**`); current branch `integration/gula-unification-v1` per `PROGRAM_CONTROL.md:30`.
- **Affected components:** all backend/frontend/E2E gates; A08.
- **Root cause:** branch filters predate the integration branch.
- **Safe-fix possible?** **No** — CI files are A08 scope; two workflows are user-modified; Wave A is read-only.
- **Approval required?** **Yes** — orchestrator + A08 approval; CI semantics change.

### A09-004 — P1 — Documented strict migration-schema gate has 119 failures; no raw artifact to verify
- **Evidence:** `GOVERNANCE/NATIONAL_TESTING_STRATEGY.md:55` `753 passed / 119 failed / 0 skipped` (exit 1); `:57` `750 / 122`; `GOVERNANCE/ARCHITECTURE_DECISION_PACKAGE_W1.md:62-64`; repository-wide search: 0 XML results, 0 `.log` files.
- **Affected components:** migration/ORM schema parity, release readiness; A07, A08.
- **Root cause:** documented drift between migration-only PG16 clone and SQLite `create_all()` control (F-063); historical, disclosed, not closed.
- **Safe-fix possible?** **No** — schema/migration changes and real-DB execution are prohibited by program control.
- **Approval required?** **Yes** — A07 + owner decision; Wave D must re-run an approved gate and capture artifacts.

### A09-005 — P2 — Unfalsifiable `or True` assertions
- **Evidence:** `backend/tests/test_db_adaptive.py:188` `assert ec2["refused"] != 99999 or True  # only fails if internal state leaked`; `backend/tests/communication_providers/test_secrets.py:39` `assert "/run/secrets" in os.environ.get("PATH", "") or True  # placeholder guard`.
- **Affected components:** DB adaptive-counter snapshot semantics; secret-resolution default-dir guard; A07, A09.
- **Root cause:** placeholder expression added with a misleading comment; `or True` short-circuits the check.
- **Safe-fix possible?** **Partial** — `test_db_adaptive.py` is clean/tracked (yes, after Wave C assignment); `test_secrets.py` is untracked USER work (no).
- **Approval required?** **Yes** — Wave C is not authorized; the untracked file additionally needs user release.

### A09-006 — P2 — Intermittent cross-suite test failure (order dependence)
- **Evidence:** `GOVERNANCE/NATIONAL_INTEGRATION/ADVERSARIAL_REVIEW_RECORD.md:101-103` — `test_nr011_metadata_discovery.py::test_cross_metadata_foreign_keys_resolve` passes alone, fails when co-collected with `tests/identity` (`NoReferencedTableError: niam_adaptive_mfa_sessions.session_id → niam_user_sessions.id`); broad run `1654 passed / 4 skipped / 1 failed`. Mirrored in `status_registry.json:472`.
- **Affected components:** backend test collection isolation; A07, A09.
- **Root cause:** SQLAlchemy global `MetaData` interaction between identity models and the NR-011 merge probe (documented characterization).
- **Safe-fix possible?** **No** — requires source/fixture isolation decision beyond A09's write set.
- **Approval required?** **Yes** — A07 review; must remain disclosed, not suppressed.

### A09-007 — P2 — Coverage gate declared but non-functional
- **Evidence:** root `package.json:14` `"test:coverage": "npm --prefix frontend-v3 run test -- --coverage"`; `frontend-v3/package.json:13` (no coverage config); `frontend-v3/vitest.config.ts:1-12` (no `coverage` block); `frontend-v3/package-lock.json:9818-9850` lists `@vitest/coverage-v8` / `-istanbul` only as **optional peerDependencies**; directories `frontend-v3/node_modules/@vitest/coverage-v8` and `.../coverage-istanbul` **absent**.
- **Affected components:** frontend coverage measurement/release evidence; A08.
- **Root cause:** provider never declared as a direct devDependency; no thresholds configured.
- **Safe-fix possible?** **No** — requires editing user-modified `frontend-v3/package.json` (+ lockfile, also USER).
- **Approval required?** **Yes** — user release; A08 approval; dependency addition must satisfy Free/Open-Source-First (both providers are OSS, MIT).

### A09-008 — P2 — Two E2E specs hardcode `/usr/bin/chromium` without CI override
- **Evidence:** `frontend-v3/e2e/reports-safe-empty.spec.ts:3-7` and `frontend-v3/e2e/dark-mode.spec.ts:3-7` — `executablePath: process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE ?? "/usr/bin/chromium"`. `playwright.config.ts:25-27` reads the same env var but `frontend-e2e.yml:34-41` sets only `PLAYWRIGHT_BASE_URL` and `CI`.
- **Affected components:** frontend E2E gate (12 specs); A08, A09.
- **Root cause:** per-spec `test.use` overrides the config's browser-resolution logic; CI installs Playwright's bundled Chromium (`npx playwright install chromium --with-deps`, `frontend-e2e.yml:34`) rather than `/usr/bin/chromium`.
- **Safe-fix possible?** **Yes** — the two spec files are clean/tracked; a one-line removal of the hardcoded fallback is safe in Wave C.
- **Approval required?** **Yes** — Wave C authorization + orchestrator-assigned test file paths. **Impact [UNVERIFIED — Wave D]:** whether the runner happens to provide `/usr/bin/chromium` cannot be established by static audit.

### A09-009 — P2 — E2E is single-browser, single-device-project
- **Evidence:** `frontend-v3/playwright.config.ts:20-30` — `projects: [{ name: "chromium", use: { ...devices["Desktop Chrome"] } }]`. No Firefox/WebKit/mobile project. `reports-safe-empty.spec.ts:9-19,47` emulates 9 viewports via `setViewportSize`, which is not a device/emulation project.
- **Affected components:** cross-browser/RTL mobile assurance; A02, A03, A09.
- **Root cause:** config intentionally minimal.
- **Safe-fix possible?** **Yes** — config file is clean/tracked (Wave C, assigned).
- **Approval required?** **Yes** — A08/A09 orchestrator approval; additional browser binaries affect CI time and dependency policy.

### A09-010 — P2 — Accessibility coverage narrow; `color-contrast` disabled in both axe tests
- **Evidence:** `frontend-v3/src/components/shared/PageComponents.a11y.test.tsx:13-16` and `frontend-v3/src/components/workspace/WorkspaceSelector.a11y.test.tsx:53-55` — both call `axe(container, { rules: { "color-contrast": { enabled: false } } })`. Repo-wide grep of `.github/workflows/` found no `axe`/`a11y`/`accessib` gate step. Only 2 of 15 FE test files are a11y tests.
- **Affected components:** design system, RTL/Arabic UI; A02, A09.
- **Root cause:** deliberate rule suppression plus limited component coverage; a11y runs only incidentally inside the vitest script.
- **Safe-fix possible?** **Yes** — both a11y test files are clean/tracked; adding tests is within A09's Wave C role.
- **Approval required?** **Yes** — Wave C assignment; A02 review before re-enabling contrast (may reveal real design defects).

### A09-011 — P2 — Six named verification gates and the aggregate `check` are never run in CI
- **Evidence:** `frontend-v3/package.json:14-21` defines `verify:unification`, `verify:contracts`, `verify:integration-boundary`, `verify:data-sources`, `verify:audit-artifacts`, `generate:*`, `check`. Repo-wide grep for each name across `.github/workflows/` returned **0 matches**; only `check:bundle` is wired (`frontend-bundle-budget.yml:43`). Cf. `PROGRAM_CONTROL.md:183-188`.
- **Affected components:** contract/data-source/route-governance assurance; A08, A01, A07.
- **Root cause:** manifests define gates but pipelines were not updated; `check` exists only as a local aggregate.
- **Safe-fix possible?** **No** — workflow edits are A08 scope and several workflows are user-modified.
- **Approval required?** **Yes** — orchestrator + A08; changing CI semantics.

### A09-012 — P3 — Placeholder/smoke-only assertions in clean tracked tests
- **Evidence:** `backend/tests/test_niam.py:336,379` (`assert True` after state-changing calls); `backend/tests/identity/test_identity_service.py:152` (`assert True  # Might not generate all`); `backend/tests/test_observability_invariants.py:128-144` ("Must not raise" / "Should be idempotent" smoke tests with no observable assertion).
- **Affected components:** identity/session deactivation, observability; A04, A07, A09.
- **Root cause:** tests written as call-smoke rather than behavior verification.
- **Safe-fix possible?** **Yes** — all named files are clean/tracked (Wave C, assigned).
- **Approval required?** **Yes** — Wave C authorization; A04 review for identity semantics.

### A09-013 — P3 — Environment-gated skips can mask regressions
- **Evidence:** `backend/tests/test_hard_scenarios.py:348,359` `pytest.skip("LabResult model not found — skipping")`; 7 blood-bank modules `pytest.mark.skipif(not POSTGRES_URL, reason="BLOOD_BANK_POSTGRES_URL is not configured")` (e.g. `test_failure_injection_postgres.py:15`); 5 identity migration tests skip without `MIGRATION_DATABASE_URL` (e.g. `identity/test_workspace_migration_phase5.py:17`). Total 20 skip call sites.
- **Affected components:** clinical lab model, blood bank, migration assurance; A05, A07, A09.
- **Root cause:** DB-dependent tests are optional-by-default; "model missing" is treated as skip rather than failure.
- **Safe-fix possible?** **No** — needs test-environment provisioning decision, not just a test edit.
- **Approval required?** **Yes** — orchestrator/A07; provisioning a disposable DB is explicitly constrained by program control.

### A09-014 — P2 — 116 untracked backend test files are outside committed CI coverage
- **Evidence:** `git ls-files --others --exclude-standard 'backend/tests/**/test_*.py'` = **116** files, including all of `backend/tests/health_core/**` and `backend/tests/communication/**` (e.g. `backend/tests/health_core/test_client_integration_guards.py`). Only **219** `test_*.py` files are tracked.
- **Affected components:** domain/health-core assurance in CI; A07, A09.
- **Root cause:** large untracked user work tree has never been committed, so a fresh CI checkout cannot run it even though `pytest tests/` would collect it locally.
- **Safe-fix possible?** **No** — USER work; report only.
- **Approval required?** **Yes** — user decides release/commit; A09 must not stage or commit.

### A09-015 — P3 — Historical test counts are inconsistent and unaccompanied by artifacts
- **Evidence:** `reports/PHASE_10_IMPLEMENTATION.md:69` (`38 passed / 11 files`) vs 15 current FE test files; `GOVERNANCE/NATIONAL_INTEGRATION/ADVERSARIAL_REVIEW_RECORD.md:15` (`773 passed` in `tests/health_core`) vs 43 current files; `GOVERNANCE/REPOSITORY_UNIFICATION_REPORT.md:56` (`3135 passed`) vs `status_registry.json:583` (`4945 passed`); `reports/discovery/17_RISK_REGISTER.md:39` claims "No E2E tests" despite 12 specs. No XML or `.log` artifacts in repo.
- **Affected components:** evidence integrity, release reporting; A01, A08, A09.
- **Root cause:** claims from different trees/epochs retained without a single authoritative, artifact-backed baseline.
- **Safe-fix possible?** **No** — Wave D must produce the baseline; A09 cannot execute gates in Wave A.
- **Approval required?** **Yes** — orchestrator to designate the authoritative Wave D gate run.

---

## 7. Finding summary by severity

| Severity | IDs | Count |
|---|---|---:|
| P0 | — | 0 |
| P1 | A09-001, A09-002, A09-003, A09-004 | 4 |
| P2 | A09-005, A09-006, A09-007, A09-008, A09-009, A09-010, A09-011, A09-014 | 8 |
| P3 | A09-012, A09-013, A09-015 | 3 |
| **Total** | | **15** |

**Top 5:** A09-001 (no-op security test), A09-002 (`--passWithNoTests`), A09-003 (integration branch has no test gates), A09-004 (119 documented migration-schema failures, no artifacts), A09-005 (unfalsifiable assertions).

---

## 8. SCOPE_REQUESTs (for orchestrator; no action taken)

| ID | Request | Owner needed | Why A09 cannot act |
|---|---|---|---|
| SR-A09-01 | Authorize replacement of `assert True` at `backend/tests/test_comprehensive.py:687` with a real `returncode`/stderr assertion after user releases the file | user + A04/A07 | File is user-modified (protected) |
| SR-A09-02 | Remove `--passWithNoTests` from `frontend-v3/package.json:13,22` and add a minimum-test-count guard | user + A08 | File is user-modified; CI semantics |
| SR-A09-03 | Extend test workflow triggers to `integration/**` branches (or add a dedicated integration-branch gate) | A08 + orchestrator | Workflow scope; CI semantics change |
| SR-A09-04 | Add `@vitest/coverage-v8` (OSS, MIT) as direct devDependency + coverage thresholds, or remove the broken `test:coverage` script | user + A08 | USER-owned manifest + lockfile |
| SR-A09-05 | Assign exact new test file paths for Wave C (A09 remediator role): e.g. `backend/tests/unit/test_qa_noop_assertion_regression.py`, `frontend-v3/e2e/browser-launch.spec.ts`, `frontend-v3/src/components/shared/PageComponents.contrast.a11y.test.tsx` | orchestrator | Wave C not authorized; A09 may write only assigned test files, never existing user work |
| SR-A09-06 | Provide/authorize raw gate artifacts (JUnit XML + logs) for Wave D to verify the 119-failure E-001 claim and the 1-failure cross-suite disclosure | orchestrator | A09 is forbidden from executing gates in Wave A |
| SR-A09-07 | Decide disposition of `color-contrast` suppression in the two axe tests (re-enable may expose real design defects) | A02 + orchestrator | Design-system scope, not QA-only |

---

## 9. Final statement

Wave A QA audit is complete: **15 findings** (4 P1, 8 P2, 3 P3), **zero P0**. All seven requested test categories were found to exist; the defects are in assertion effectiveness, determinism, artifact availability, and CI wiring. No test was executed, no test file was modified, and no git state was changed. All user-owned paths — including `frontend-v3/src/components/navigation/MobileBottomNav.test.tsx` (` M`) and the untracked `backend/tests/**` trees — are reported only and untouched.
