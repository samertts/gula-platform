# TEST RESULTS — PROGRAM-GULA-PARALLEL-001 (AGENT 09)

**Agent:** A09 — Testing & Quality Assurance
**Date:** 2026-11-19
**Wave:** A (read-only discovery)
**Purpose:** Record *stored* test evidence and distinguish **verified filesystem facts** from **documentation claims**.

---

## ⚠️ EXECUTION DISCLAIMER — READ FIRST

> **NO TESTS WERE EXECUTED BY THIS AUDIT.**
> Agent 09 did **not** run pytest, Vitest, Playwright, E2E, builds, coverage, Alembic, or any gate command.
> No pass/fail status in this document is a result produced by A09.
> All numbers below are either (a) **verified filesystem counts** (files/paths only) or (b) **claims transcribed from existing repository documents**, explicitly marked `CLAIM — UNVERIFIED`.
> Wave D (orchestrator) will execute the gates defined in `REGRESSION_TEST_PLAN.md` §1/§4 and produce the authoritative results in `INTEGRATION_LOG.md`.

**Arabic:** لم يتم تنفيذ أي اختبار من قِبل هذا التدقيق. جميع الأرقام أدناه إما عدّ ملفات مُتحقَّق منه أو أقوال موثّقة في مستندات موجودة لم يتم التحقق منها.

---

## 1. What A09 actually verified (filesystem facts only)

| Check | Command type (read-only) | Verified result |
|---|---|---|
| `backend/tests/**` test files | `find … -name 'test_*.py'` | **335** files (219 tracked, 116 untracked USER) |
| All Python files under `backend/tests/` | `find … -name '*.py'` | **360** (335 tests + conftest/support) |
| `backend/tests/health_core/` | `find` | **43** `test_*.py` |
| `backend/tests/unit/` | `find` | **31** `test_*.py` |
| `frontend-v3/src/**/*.test.*` | `find` | **15** files (54 `it(`/`test(` declarations) |
| `frontend-v3/e2e/*.spec.ts` | `find` | **12** files (22 `test(` declarations; one loops 9 viewports) |
| `GLOSI/tests`, `test_library`, root `tests/`, root `k6/` | `find` | 1 / 2 / 14 / 1 files |
| Test functions in `backend/tests/**` | in-memory Python AST parse (no imports, no writes) | **4,379** parsed functions |
| JUnit/XML result artifacts | `find . -name '*.xml' …` filtered by test/junit/pytest/result/artifact | **0 found** |
| Raw `.log` files (non-`node_modules`) | `find . -name '*.log'` | **0 found** |
| Coverage provider installed in `frontend-v3/node_modules/@vitest/` | directory check | **absent** (both `coverage-v8` and `coverage-istanbul`) |
| Snapshot files | `find …/__snapshots__` | **0 found** |
| Frontend skip/todo markers | `grep` | **0 found** |

**Conclusion:** the repository contains **no committed machine-readable test results**. There is nothing for A09 to parse as an executed run.

---

## 2. Stored failing-test evidence (documentation claims — NOT re-executed)

### 2.1 Largest disclosed failure — migration-only schema gate

| Field | Value |
|---|---|
| Source | `GOVERNANCE/NATIONAL_TESTING_STRATEGY.md:55` |
| Exact claim | `E-001 \| strict #1, authoritative, migration-only PG16 clone \| 753 passed / 119 failed / 0 skipped (53 modules / 872 tests, exit 1)` |
| Repeat claim | `GOVERNANCE/NATIONAL_TESTING_STRATEGY.md:57` — E-002: `750 / 122` (119 reproduced + 3 self-poisoned, F-005) |
| Corroboration | `GOVERNANCE/ARCHITECTURE_DECISION_PACKAGE_W1.md:62-64` — "Run #1: 753 passed / 119 failed", "Run #2: 750 / 122", SQLite control 872 passed |
| Control claim | `GOVERNANCE/NATIONAL_TESTING_STRATEGY.md:56` — E-003 SQLite `create_all()` control: 872 passed / 0 failed (`control only, not migration compatibility (F-063)`) |
| Status | **CLAIM — UNVERIFIED** (no XML/log artifact present; A09 did not run the gate) |
| Severity linkage | A09-004 (P1) |
| Required action | Wave D re-run under an approved gate, or formal carry-forward with residual-risk note |

### 2.2 Intermittent / order-dependent failure

| Field | Value |
|---|---|
| Source | `GOVERNANCE/NATIONAL_INTEGRATION/ADVERSARIAL_REVIEW_RECORD.md:101-103` |
| Exact claim (lines 101-103) | `NR-011 FK test in isolation → 1 passed`; `Co-collected with tests/identity → 1 failed, 1658 deselected` with `NoReferencedTableError: niam_adaptive_mfa_sessions.session_id → niam_user_sessions.id`; `Full broad selection → 1654 passed / 4 skipped / 1 failed` |
| Machine-readable mirror | `GOVERNANCE/NATIONAL_INTEGRATION/status_registry.json:472` (`broad_regression_disclosure`) |
| Related acceptance doc | `GOVERNANCE/NATIONAL_INTEGRATION/14_FINAL_ACCEPTANCE_REPORT.md:82` — same `1654 passed / 4 skipped / 1 failed` |
| Status | **CLAIM — UNVERIFIED** |
| Severity linkage | A09-006 (P2) |
| Required action | Must remain disclosed; re-check in Wave D step D11 (isolated + co-collected). Do not suppress via skip/xfail |

### 2.3 Later passed-run claims (for reconciliation, not verification)

| Source (path:line) | Claimed result | Status |
|---|---|---|
| `GOVERNANCE/NATIONAL_INTEGRATION/status_registry.json:529` | `4913 passed, 27 skipped, 202 warnings in 576.09s, EXIT=0` | CLAIM — UNVERIFIED |
| `GOVERNANCE/NATIONAL_INTEGRATION/status_registry.json:583-584` | Final tree `4945 passed, 27 skipped, 203 warnings in 469.50s, EXIT=0`; supersedes 4913 | CLAIM — UNVERIFIED |
| `GOVERNANCE/NATIONAL_INTEGRATION/status_registry.json:565` | Targeted+neighbor `87 passed`; final-tree full regression `4945 passed` | CLAIM — UNVERIFIED |
| `GOVERNANCE/REPOSITORY_UNIFICATION_REPORT.md:56` | `3135 passed, 27 skipped, 0 failed; 577.65s; exit 0` (`/tmp/opencode/full_suite_integration_2.log`) | CLAIM — UNVERIFIED; referenced log **not in repo** |
| `GOVERNANCE/REFERENCE_STATE_REPORT.md:84` | `3135 passed, 27 skipped, 165 warnings in 577.65s` | CLAIM — UNVERIFIED |
| `GOVERNANCE/NATIONAL_INTEGRATION/ADVERSARIAL_REVIEW_RECORD.md:86-89` | `235 passed` focused; `103 passed` terminology; `773 passed, 1 warning` health_core | CLAIM — UNVERIFIED |
| `EVIDENCE/BASELINE/BASELINE_REPORT.md:13` | Explicit statement: "no local test suite, database migration, build, deployment, or security scan was executed as part of this setup" | VERIFIED TEXT (document says no tests were run); downstream numbers at `:36-38` remain CLAIMS |

### 2.4 Frontend / synthetic pass claims

| Source (path:line) | Claimed result | Status |
|---|---|---|
| `reports/PHASE_10_IMPLEMENTATION.md:69` | `38 passed / 11 files` frontend-v3 tests | CLAIM — UNVERIFIED; current tree has 15 test files |
| `reports/IAM_PHASE_09_IMPLEMENTATION.md:62-63` | `162 passed, 3 deselected` identity regression; `10 passed` Phase 9 | CLAIM — UNVERIFIED |
| `reports/IAM_PHASE_08_IMPLEMENTATION.md:44-48` | `152 passed, 2 deselected`; `test_niam.py 44 passed`; `10 files / 34 tests` frontend | CLAIM — UNVERIFIED |
| `GOVERNANCE/NATIONAL_TESTING_STRATEGY.md:45,59` | E-062 `12 tests / 0 failures in 0.69s`; 20/20 verifier checks | CLAIM — UNVERIFIED |
| `GOVERNANCE/NATIONAL_PLATFORM_STABILIZATION_REPORT.md:52` | 9 synthetic suites, `194 tests passed / 0 failed` | CLAIM — UNVERIFIED |

### 2.5 Stale / contradicted claim

- `reports/discovery/17_RISK_REGISTER.md:39` — `R16 | **No E2E tests** | Integration failures undetected | … | Add Cypress/Playwright`. **Contradicted by current tree**: 12 Playwright specs in `frontend-v3/e2e/` and a configured `playwright.config.ts`. Classified `STALE CLAIM` (A09-015).
- `reports/discovery/01_MASTER_DISCOVERY.md:130` / `05_FRONTEND_ANALYSIS.md:138` — "No evidence of comprehensive frontend test suites" / "No frontend test evidence". Also stale relative to 15 FE test files + 12 E2E specs.

---

## 3. Test-effectiveness observations affecting result trustworthiness

These are **static findings**, not executed results. Full evidence in `QA_AUDIT.md` §3 and §6.

| Finding | Effect on any future pass/fail number |
|---|---|
| A09-002 — `--passWithNoTests` (`frontend-v3/package.json:13,22`) | A "PASS" from `npm run test` does **not** prove any test ran. Wave D must record collected test count. |
| A09-001 — `assert True` (`backend/tests/test_comprehensive.py:687`) | One security-intent test cannot fail; a green suite overstates production-secret guard coverage. |
| A09-005 — `or True` (`test_db_adaptive.py:188`, `test_secrets.py:39`) | Two assertions are unfalsifiable. |
| A09-013 — env-gated skips (20 sites) | A green run may skip DB/migration/model tests entirely; skip reasons must be captured. |
| A09-006 — cross-suite order dependence | Result depends on collection order; isolated PASS ≠ co-collected PASS. |
| A09-014 — 116 untracked backend test files | Local results include user work that a fresh CI checkout cannot reproduce. |
| A09-003 — branch trigger gap | Historical "CI green" claims on `integration/gula-unification-v1` would not come from test workflows. |

---

## 4. Verification status legend

| Label | Meaning |
|---|---|
| **VERIFIED (filesystem)** | A09 read the file/path directly; only existence/count/content established — **not** test outcome. |
| **VERIFIED TEXT** | The quoted sentence exists in the cited document; its factual claim is not endorsed. |
| **CLAIM — UNVERIFIED** | Historical pass/fail number transcribed from a document; no artifact, no re-execution. |
| **STALE CLAIM** | Contradicted by current filesystem state. |
| **UNVERIFIED — Wave D** | Impact cannot be established statically; requires gate execution. |

---

## 5. Handover to Wave D

1. Execute gates per `REGRESSION_TEST_PLAN.md` §1 and §4, from the correct working directories.
2. Capture stdout/stderr, exit code, **collected test count**, and **skip list** as artifacts (JUnit XML where supported). Currently absent artifacts are part of finding A09-015.
3. Replace the `CLAIM — UNVERIFIED` labels above with authoritative results only after orchestrator-run gates.
4. Keep the guarded disclosure for the 119-failure migration gate and the 1-failure cross-suite case visible; do not overwrite historical numbers silently (`GOVERNANCE/NATIONAL_TESTING_STRATEGY.md:51` says preserve verbatim).
5. Do not treat this document as a pass/fail statement for the program.

---

## 6. Final statement

A09 executed **zero** tests and produced **zero** pass/fail results. This document inventories **7 categories of stored claims** and **0 machine-readable result artifacts**, and records 7 static observations that affect how any future result should be interpreted. All source, config, test, and workflow files remain untouched; only the three owned paths under `docs/parallel-program/qa/` were written.
