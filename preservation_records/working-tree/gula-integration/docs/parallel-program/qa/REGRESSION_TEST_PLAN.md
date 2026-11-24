# REGRESSION TEST PLAN — PROGRAM-GULA-PARALLEL-001 (AGENT 09)

**Agent:** A09 — Testing & Quality Assurance
**Date:** 2026-11-19
**Phase:** Wave A deliverable — **plan only, no test files written**
**Gate execution owner:** Wave D (orchestrator). A09 does not execute gates in Wave A.

---

## 0. Purpose and constraints (Arabic: الغرض والقيود)

This plan defines a **concrete regression suite** mapped to the 9 agent scopes, with exact gate commands and working directories. It identifies the tests that **must be added** before/with safe remediation in Wave C. It deliberately does **not** create test files, modify existing tests, run suites, or change configuration.

**Hard constraints carried from `PROGRAM_CONTROL.md` / `AGENT_ASSIGNMENTS.md`:**
1. Wave A is read-only on source/config/tests; A09 writes only its 3 owned Markdown reports.
2. `frontend-v3/package.json`, `frontend-v3/package-lock.json`, `.github/workflows/frontend-pwa.yml`, `.github/workflows/security-hardening.yml`, `frontend-v3/src/components/navigation/MobileBottomNav.test.tsx`, and all untracked `backend/tests/**` files are **USER work — protected**.
3. No test/migration/build execution against real data; no Alembic against any DB.
4. Wave C requires an approved remediation register, confirmed ownership, clean files, and no open P0 on the component.
5. Gate commands must be run from the directory where they are defined (`PROGRAM_CONTROL.md:192-193`, `CONFLICT_REGISTER.md` CR-004).

---

## 1. Gate command catalogue (verified to exist — read from manifests)

| # | Gate | Working directory | Exact command | Defined at | Currently wired in CI? |
|---|---|---|---|---|---|
| G1 | Backend full pytest | `backend/` | `python -m pytest tests/ -v --timeout=60` | `Makefile:207-208`, `ci.yml:288-301` | ✅ `ci.yml` (branch-limited) |
| G2 | Backend clinical safety subset | `backend/` | `python -m pytest -q --timeout=60 tests/test_clinical_command_guard_p0.py … tests/test_icu_lab_workflow_p0.py` (7 files) | `ci.yml:266-286` | ✅ `ci.yml` |
| G3 | Backend identity (non-integration) | `backend/` | `python -m pytest tests/identity tests/test_clinical_gateway_contracts.py tests/test_clinical_gateway_service.py -m "not integration" -q` | `iam-hardening.yml:46` | ✅ `iam-hardening.yml` |
| G4 | Backend migration graph | `backend/` | `pytest tests/migrations/test_migration_graph_integrity.py` + `alembic check` (no DB execution) | `backend/tests/migrations/`, `ci.yml:119-177` | ✅ `ci.yml` migration-check |
| G5 | Backend migration integration (DB) | `backend/` | `pytest tests/identity/test_*migration_phase*.py -q` | `iam-hardening.yml:109` | ⚠️ Skips without `MIGRATION_DATABASE_URL` |
| G6 | Frontend unit/component | `frontend-v3/` | `npm run test` → `vitest run --passWithNoTests --exclude 'e2e/**'` | `frontend-v3/package.json:13` | ⚠️ Only `iam-hardening.yml:143` |
| G7 | Frontend E2E | `frontend-v3/` | `npm run test:e2e` → `playwright test` (CI equivalent: `npx playwright test` with `CI=true`) | `frontend-v3/package.json:23`, `frontend-e2e.yml:34-41` | ⚠️ `npx` form only; branch-limited |
| G8 | Frontend typecheck | `frontend-v3/` | `npm run typecheck` | `frontend-v3/package.json:12` | ✅ `iam-hardening.yml:149` |
| G9 | Frontend lint | `frontend-v3/` | `npm run lint` | `frontend-v3/package.json:11` | ✅ `iam-hardening.yml:147` |
| G10 | Frontend production build | `frontend-v3/` | `npm run build` | `frontend-v3/package.json:8` | ✅ `frontend-e2e.yml:36`, `iam-hardening.yml:153` |
| G11 | Bundle budget | `frontend-v3/` | `npm run check:bundle` | `frontend-v3/package.json:9` | ✅ `frontend-bundle-budget.yml:43` |
| G12 | Unification/contract/boundary/data-source/audit verifiers | `frontend-v3/` | `npm run verify:unification`, `verify:contracts`, `verify:integration-boundary`, `verify:data-sources`, `verify:audit-artifacts`, `generate:data-source-inventory`, `generate:route-gate` | `frontend-v3/package.json:14-20` | ❌ **Not wired** (A09-011) |
| G13 | Aggregate frontend check | `frontend-v3/` | `npm run check` | `frontend-v3/package.json:21` | ❌ Local only |
| G14 | Frontend coverage | root → `frontend-v3/` | `npm run test:coverage` → `vitest … --coverage` | root `package.json:14` | ❌ Broken: no coverage provider (A09-007) |
| G15 | Nightly backend integration | `backend/` | `pytest tests/ -v --tb=long -ra --maxfail=5 --junitxml=pytest-integration.xml` | `nightly.yml:112-121` | ✅ schedule + dispatch only |
| G16 | Chaos / load / recovery scripts | repo root | `make chaos`, `make scenario-test`, `bash tests/chaos/chaos_test.sh all` | `Makefile:210-218` | ⚠️ `nightly.yml:124+` (chaos job) |

**Wave D execution rule:** run each gate from its listed working directory, capture stdout/stderr **plus exit code** into an artifact, and record in `INTEGRATION_LOG.md`. Do not infer pass/fail from exit code alone when `--passWithNoTests` or env-gated skips are in play (A09-002, A09-013).

---

## 2. Regression suite mapped to the 9 agent scopes

For each scope: what to run, which existing tests are authoritative, and what A09 needs added. Paths are **existing files, read-only** unless listed under §3.

### A01 — Repository & Architecture
- **Gates:** G1 (full backend), G6+G12+G13 (frontend verifiers), G10.
- **Authoritative existing tests:** `backend/tests/unit/test_nr011_metadata_discovery.py` (documented 14/14), `backend/tests/unit/test_national_integration_registry.py` (documented 31/31), `frontend-v3/scripts/verify-*.mjs` invoked by G12.
- **Regression focus:** module-boundary and route-gate drift after any dependency change; verify G12 scripts actually execute in CI.
- **Add for safe remediation (§3):** T-01 (gate-wiring smoke test).

### A02 — Frontend Design System
- **Gates:** G6, G8, G9, G10, G11; axe subset of G6.
- **Authoritative existing tests:** `frontend-v3/src/components/shared/PageComponents.a11y.test.tsx`, `WorkspaceSelector.a11y.test.tsx`, `Button.test.tsx`, `frontend-v3/e2e/dark-mode.spec.ts`.
- **Regression focus:** RTL direction, theme tokens, contrast (currently suppressed — A09-010), shared-component rendering.
- **Add (§3):** T-04 (contrast a11y test), T-05 (token/RTL regression test if A02 remediates shared components).

### A03 — Frontend Clinical Workflows
- **Gates:** G6 (page tests), G7 (E2E clinical specs), G10.
- **Authoritative existing tests:** `frontend-v3/src/pages/ehr/EhrPage.test.tsx`, `frontend-v3/src/pages/patient-visit/PatientVisitReadinessPage.test.tsx`, `frontend-v3/src/pages/migration/LegacyRouteBridge.test.ts`, `frontend-v3/e2e/{patients,orders,results,samples,fhir,billing-insurance,navigation}.spec.ts`.
- **Regression focus:** clinical page navigation, safe-empty states, route bridging.
- **Add (§3):** T-06 (safe-empty regression for changed pages), T-07 (E2E browser-launch robustness).

### A04 — Security & Identity
- **Gates:** G2, G3, G5, G6, G7 (`auth.spec.ts`).
- **Authoritative existing tests:** `backend/tests/test_security.py`, `test_security_regression.py`, `test_tenant_isolation_matrix.py`, `backend/tests/security/test_security_headers.py`, `backend/tests/identity/test_*_phase*.py`, `unit/test_webauthn_hardening.py`, `unit/test_aud_sec_001_control_plane_authorization.py`, `frontend-v3/e2e/auth.spec.ts`.
- **Regression focus:** auth/RBAC/tenant isolation; the no-op production secret guard (A09-001) must become a real assertion before this scope is trusted.
- **Add (§3):** T-02 (no-op assertion regression), T-08 (secret-guard subprocess contract test).

### A05 — Clinical Data & Interoperability
- **Gates:** G1, G2, G4; `health_core` subset: `python -m pytest tests/health_core -q --tb=short`.
- **Authoritative existing tests:** `backend/tests/health_core/test_contracts_*.py` (6), `test_fhir_http_endpoints.py`-equivalents (`health_core/test_fhir_http_endpoints.py` where present), `test_terminology_*.py`, `test_journey_contract_reliability_synthetic.py`, `frontend-v3/e2e/fhir.spec.ts`.
- **Regression focus:** FHIR R4 contracts, terminology provenance, clinical safety P0 subset; **do not invent clinical logic**.
- **Add (§3):** T-09 (contract-guard regression for any clinical test change).

### A06 — Offline & Distributed Systems
- **Gates:** G1 (offline subset), G15/G16 (reliability/chaos).
- **Authoritative existing tests:** `backend/tests/test_offline_sync.py`, `test_offline_conflict_synthetic.py`, `health_core/test_integration_offline.py`, `health_core/test_reliability_durable_queue.py`, `kernel_hardening/` suite.
- **Regression focus:** idempotency, durable queue, conflict resolution, retries; blood-bank DB tests are skipped without `BLOOD_BANK_POSTGRES_URL` (A09-013) — record skip reasons explicitly.
- **Add (§3):** T-10 (skip-visibility assertion guard), T-11 (offline E2E smoke).

### A07 — Backend, API & Database
- **Gates:** G1, G2, G4, G5, G15.
- **Authoritative existing tests:** `backend/tests/integration/`, `backend/tests/contracts/`, `test_migrations.py`, `test_migration_resilience.py`, `test_db_adaptive.py`, `test_clinical_gateway_contracts.py`.
- **Regression focus:** API contracts, DB error handling (A09-005a snapshot-copy test), **order-dependence** of `test_nr011_metadata_discovery.py::test_cross_metadata_foreign_keys_resolve` (A09-006) — run isolated **and** co-collected with `tests/identity`.
- **Add (§3):** T-03 (unfalsifiable-assertion detector), T-12 (collection-order determinism check).

### A08 — DevOps, Performance & Reliability
- **Gates:** G1, G11, G15, G16, plus **all currently unwired gates G12/G14**.
- **Authoritative existing tests:** `frontend-v3/scripts/check-bundle-size.mjs`, `verify-*.mjs`, `k6/load_test.js`, `tests/load/*`, `tests/chaos/*`.
- **Regression focus:** CI trigger coverage for `integration/gula-unification-v1` (A09-003), coverage provider availability (A09-007), artifact capture (XML/log).
- **Add (§3):** T-01 (gate-wiring), T-13 (coverage-provider availability check).

### A09 — Testing & QA (self-scope)
- **Gates:** all of G1–G16 in Wave D; in Wave A only static inventory was performed.
- **Regression focus:** test effectiveness itself — no `assert True`/`or True` placeholders, no `--passWithNoTests` false pass, no silent skip increases, no stale artifact claims.
- **Add (§3):** T-02, T-03, T-10, T-12 plus T-14 (test-count floor guard).

---

## 3. Tests that must be added for safe remediation (Wave C — assigned files only)

**No files below were created.** These are specifications for orchestrator-assigned, independent test files. Each must be verified clean (`git status --porcelain -- <file>` empty) and disjoint from user work before Wave C writes.

| ID | Proposed file (new, A09-owned on assignment) | Behavior to assert | Linked finding |
|---|---|---|---|
| T-01 | `scripts/tests/test_ci_gate_wiring.py` | Parse `.github/workflows/*.yml` (read-only) and assert the integration branch pattern plus G12 verifier commands appear in at least one workflow; fails if absent. | A09-003, A09-011 |
| T-02 | `backend/tests/unit/test_qa_noop_assertion_guard.py` | AST-scan designated high-risk test files and assert no bare `assert True` / `or True` unfalsifiable assertion remains; whitelist side-effect lambdas. | A09-001, A09-005, A09-012 |
| T-03 | `backend/tests/unit/test_db_snapshot_copy_regression.py` | Replace the semantics of `test_db_adaptive.py:188`: mutate returned counter dict and assert internal counters unchanged. | A09-005a |
| T-04 | `frontend-v3/src/components/shared/PageComponents.contrast.a11y.test.tsx` | Run `axe` with `color-contrast` **enabled** on loading states; fails on WCAG 1.4.3 violations. Requires A02 sign-off. | A09-010 |
| T-05 | `frontend-v3/src/components/shared/TokenRtlRegression.test.tsx` | Assert RTL `dir`, token resolution, and no horizontal overflow for shared components (only if A02 remediates them). | A09-010 |
| T-06 | `frontend-v3/src/pages/reports/SafeEmptyRegression.test.tsx` | Assert safe-empty state and absence of export action when data source unbound (mirrors E2E `reports-safe-empty.spec.ts` at unit level). | A03 scope |
| T-07 | `frontend-v3/e2e/browser-launch.spec.ts` | Minimal smoke spec with **no** hardcoded `executablePath`; verifies browser launches under CI config. Replaces reliance on `/usr/bin/chromium`. | A09-008 |
| T-08 | `backend/tests/unit/test_production_secret_guard_contract.py` | Assert `subprocess.run(...)` exit code != 0 and stderr contains `SECRET_KEY` when production secrets missing; replaces `test_comprehensive.py:687` intent. Must be written **after** user releases that file or as an independent new test. | A09-001 |
| T-09 | `backend/tests/contracts/test_contract_guard_regression.py` | Assert FHIR/terminology contract error shapes (`OperationOutcome`, issue codes) remain stable after clinical test edits. | A05 scope, A09-004 |
| T-10 | `backend/tests/unit/test_skip_budget.py` | Collect skip reasons and assert no increase in "model not found" skips vs frozen baseline; keeps disclosed skips visible. | A09-013 |
| T-11 | `frontend-v3/e2e/offline-smoke.spec.ts` | Playwright `context.setOffline(true)` + service-worker-blocked config; assert cached shell renders an offline-safe state (no patient data). | A06 scope |
| T-12 | `backend/tests/unit/test_collection_order_determinism.py` | Programmatic pytest collection of NR-011 + identity modules; assert zero `NoReferencedTableError` (must run in isolation **and** co-collected). | A09-006 |
| T-13 | `scripts/tests/test_coverage_provider_available.py` | Assert a coverage provider is declared in `frontend-v3/package.json` **or** that `test:coverage` is removed; guards against a silently broken coverage gate. | A09-007 |
| T-14 | `frontend-v3/src/test/testCountFloor.test.ts` | Assert Vitest collects ≥ N test cases (N = verified 54 minus allowed churn) so `--passWithNoTests` cannot hide an empty suite. | A09-002 |

**Priority for Wave C:** T-02, T-08, T-03, T-07, T-01 first (P1/P2 findings); then T-04, T-10, T-12, T-13, T-14.

**Explicitly NOT to do:** do not edit `frontend-v3/package.json`, do not edit existing user-modified test files, do not add tests to untracked `backend/tests/health_core/**` or `communication_providers/**`, do not execute Alembic, do not suppress the NR-011 cross-suite failure.

---

## 4. Wave D execution sequence (orchestrator-run; A09 observes/reports)

| Step | Gate(s) | Working directory | Evidence to capture | Blocking conditions |
|---|---|---|---|---|
| D0 | Confirm git status unchanged vs Phase 0 snapshot | repo root | `git status --porcelain` diff | Any new user-work modification → halt |
| D1 | G8, G9 (typecheck/lint) | `frontend-v3/` | stdout + exit | — |
| D2 | G6 (vitest) with **test-count floor T-14** | `frontend-v3/` | stdout + exit + collected count | `--passWithNoTests` masks empty suite → record as FAIL by policy |
| D3 | G10, G11 (build, bundle) | `frontend-v3/` | stdout + exit | — |
| D4 | G12, G13 (verifiers) | `frontend-v3/` | stdout + exit | Currently unwired → run manually, record `MANUAL` |
| D5 | G7 (Playwright, `CI=true`) | `frontend-v3/` | HTML report + list output + exit | Hardcoded chromium path → `[UNVERIFIED]` until observed |
| D6 | G4 (migration graph, no DB writes) | `backend/` | stdout + exit | No real-DB execution |
| D7 | G3, G2 (identity, safety subsets) | `backend/` | `--junitxml` if supported + exit | DB URL-gated skips must be listed |
| D8 | G1 (full backend) | `backend/` | stdout + exit + skip summary | Long-running; orchestrator approval |
| D9 | G5 (migration integration, disposable DB only) | `backend/` | stdout + exit | Requires explicit disposable-DB authorization |
| D10 | G14 (coverage) | root | stdout + exit | Expected failure until A09-007 resolved |
| D11 | T-12 (cross-suite determinism) | `backend/` | isolated + co-collected outputs | Known 1 failure must be disclosed, not suppressed |
| D12 | Consolidate into `INTEGRATION_LOG.md` + `TEST_RESULTS.md` update | orchestrator | authoritative numbers | Supersedes all historical claims |

**Exit criteria for program test quality:**
- No P0 finding open on the affected component.
- G2/G3/G6/G7 pass with **non-zero test counts** and zero new skips.
- G12 verifiers execute (even if manually in D4) with exit 0.
- A09-001, A09-002, A09-003, A09-004 each either remediated under an approved Wave C task or explicitly accepted by the orchestrator with residual-risk note.
- Documented 119-failure gate (A09-004) re-run in D6/D8 or formally carried forward as disclosed.

---

## 5. Honesty statement

This is a **plan**. No gate in §1 was executed by A09, no test file in §2–§3 was created or modified, and no CI file was edited. Test counts quoted here are static inventory figures from `QA_AUDIT.md` §1; pass/fail numbers quoted from governance documents are historical claims recorded in `TEST_RESULTS.md` and are **not** results of this audit.
