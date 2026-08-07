# COMMIT 3.6 VERIFICATION REPORT — Program-01 Wave 4 (Workflow Runtime Retirement)

- **Order:** 19 (ADR-036) · **Commit:** (pending) · **Branch:** `remediate-security-001`
- **Finding:** #44 (`workflow_engine` — `national/workflow_runtime` wired-but-500) → **31 → 27**
- **Scope:** Archive the broken national `workflow_runtime` package (0-byte service → every
  `/national/workflows/*` handler raised ImportError / HTTP 500) and re-point consumers to the
  canonical `backend/app/workflows/engine.py::WorkflowEngine` at `/niam/workflows`.

---

## 1. Executive Summary

Commit 3.6 retires the **wired-but-broken** `national/workflow_runtime` package,
the last of the Wave 4 Shared Core `workflow_engine` reimplementation findings.
The package's `application/service.py` was **0 bytes**, so every one of its 20
wired endpoints returned HTTP 500; `backend/app/platform/workflow.py` was dead
code (zero importers) that lazily imported the broken service. All 15 files were
preserved via `git mv` into `archive/platform-shared-core/` with provenance
headers (ADR-028 archive-first, reversible via a single `git revert`); the
frontend national page, generated-client section, nav entry, and the
generator/zero-drift registries were re-pointed/removed atomically. The
canonical live engine (`/niam/workflows`) is the single workflow implementation.
**Architecture gate: PASS (27 findings, 27 ack, 0 new) · Full backend suite
5066 passed / 0 failed · OpenAPI −22 methods / −19 paths, all and only the
`/national/workflows/*` broken surface · Boot 118 routes · 14 new regression
tests.**

## 2. Files Changed

| File | Change | Notes |
|---|---|---|
| `backend/app/national/workflow_runtime/*` (13 files) | **Archived** via `git mv` → `archive/platform-shared-core/national_workflow_runtime_*.py` | flat named files + provenance headers |
| `backend/app/platform/workflow.py` | **Archived** → `archive/platform-shared-core/platform_workflow.py` | dead code (zero importers) |
| `backend/app/national/workflow_runtime/{application,domain,infrastructure}/__init__.py` | **Deleted** | package vacated, no facade |
| `backend/app/factory.py` | workflow router `include_router` removed | `/national/workflows/*` surface gone |
| `frontend-v3/src/pages/national/workflow-runtime/NationalWorkflowRuntimeApiPage.tsx` | **Deleted** | only consumed the 500 surface |
| `frontend-v3/src/routes/index.tsx` | route + lazy import removed | canonical `/niam/workflows` page is live |
| `frontend-v3/src/permissions/index.ts` | nav entry removed | |
| `frontend-v3/src/api/generated/client.ts` | `national.workflow_runtime.api` section removed (API object + 10 hooks) | −74 lines |
| `scripts/generate_frontend_client.py` | module registry entry removed | |
| `scripts/zero_drift_engine.py` | nav metadata entry removed | |
| `backend/tests/unit/test_workflow_runtime_retired.py` | **NEW** — 14 regression tests | namespace vacated, canonical intact, signals gone, archive provenance |
| `.ai/core/architecture/constitution_baseline.json` | baseline regenerated **31 → 27** | −4 (see §4) |
| ADR-036 + 14 docs/catalog/certification references | updated to reflect retirement | WORKFLOW_CATALOG, MODULE_DEPENDENCY_MATRIX, DIGITAL_DNA_ATLAS, EXTENSION_GUIDE, CHANGELOG, catalogs, coverage reports, master docs |

**Total: +14 archived, +1 new test file, −1 page, −4 `__init__` markers, −1 factory block.**
No dependencies added, no lockfile change, no schema/data change.

## 3. Architecture Findings (Shared Core Scan)

- Removed (signal `def\s+execute_workflow\s*\(`):
  - #44 `backend/app/national/workflow_runtime/api/routes.py`
- No other `workflow_engine` signal remains anywhere under `backend/app` (grep + scan verified).
- The canonical allowlisted path `backend/app/workflows` matches the remaining
  `class ... WorkflowEngine` signal and is exempt by the gate.
- Also absent from the scan (already resolved by committed Orders 16–18, baseline
  regeneration deferred to this commit): the `audit` signals at
  `document_intelligence/application/wiring.py` (ADR-031) and
  `national/task_engine/infrastructure/repository.py` (ADR-031), and the
  `notifications` signal at `national/notification_platform/api/routes.py` (ADR-032).

## 4. Baseline Regeneration

The on-disk baseline (31 findings, regenerated at Wave 3) still listed three
findings that Orders 16–18 had already resolved in code without a baseline
re-run. This commit regenerates the baseline against the current scan:

| Baseline | Count | Delta |
|---|---|---|
| Wave 3 certification (Commit 3.3) | 31 | — |
| − Order 16 (doc-intel audit → canonical, ADR-031) | 30 | −1 |
| − Order 17 (task_engine audit → canonical, ADR-031) | 29 | −1 |
| − Order 18 (notification adapters → canonical, ADR-032) | 28 | −1 |
| − Order 19 (this commit, workflow_runtime → canonical, ADR-036) | **27** | −1 |

Regenerated via `scripts/architecture.py baseline` → 27 findings + 2 country
findings. Gate re-run: **PASS (27 ack, 0 new)**. Master docs
(`MASTER_REMAINING_WORK.md` et al.) regenerated via `architecture docs`.

## 5. Migration Routes (source → canonical)

| Broken source | Canonical target |
|---|---|
| `national/workflow_runtime/api/routes.py` (20 endpoints, `/national/workflows/*`) | `backend/app/workflows/engine.py` → `/niam/workflows` |
| `national/workflow_runtime/application/service.py` (0 bytes) | `backend/app/workflows/engine.py::WorkflowEngine` |
| `national/workflow_runtime/{domain,infrastructure,exceptions}` (types/enums/ABCs/repos) | canonical `app.workflows` models + engine (conceptual); archived verbatim for provenance |
| `platform/workflow.py` (dead lazy-import) | canonical engine (no importer ever reached it) |
| `NationalWorkflowRuntimeApiPage.tsx` (frontend, GET-only 500 page) | `frontend-v3/src/pages/niam/WorkflowsPage.tsx` (live) |

## 6. Test Suite

| Suite | Result |
|---|---|
| Full backend (`ENV=test` + PG) | **5066 passed / 0 failed** (600.65s) |
| Frontend unit (`vitest run`) | **122 passed / 0 failed** (9 files) |
| Ruff (backend) | 378 errors (< 379 baseline; factory.py clean) |
| `tsc --noEmit` | **0 errors** |
| `eslint src --max-warnings=0` | **0 errors** |

## 7. Regression Tests (new in this commit)

`backend/tests/unit/test_workflow_runtime_retired.py` — 14 tests:

- **Namespace vacated** — `app.national.workflow_runtime` and `app.platform.workflow`
  unreachable; `factory.py` no longer references `workflow_runtime`; frontend
  client/routes/nav and both script registries free of the module.
- **Canonical provider intact** — `WorkflowEngine` importable; the NIAM
  workflows router is wired with prefix `/workflows` and routes.
- **Broken surface retired** — archived routes declare the old surface; no
  `def execute_workflow(` signal and no `workflow_runtime` reference remains
  anywhere under `backend/app`.
- **Archive provenance** — archived files exist with `"""Archived Shared Core`
  headers documenting source path, finding, ADR-036, and single-revert
  reversibility; the 0-byte `application/service.py` evidence is documented.

## 8. Consumer Verification

- **Backend:** only `factory.py` imported the router (removed). `platform/workflow.py`
  had zero importers repo-wide (grep-verified) and was archived with it.
- **Frontend:** the single consumer page was removed; the generated-client section
  (API object + 10 hooks) had no other importers (grep-verified); nav entry removed.
  The live canonical page at `/niam/workflows` replaces it.
- **Scripts:** generator registry and zero-drift nav metadata updated in the same commit.
- **Docs:** WORKFLOW_CATALOG, MODULE_DEPENDENCY_MATRIX, DIGITAL_DNA_ATLAS,
  EXTENSION_GUIDE, CHANGELOG, catalogs, coverage reports, and master docs updated.

## 9. OpenAPI Compatibility

- Before (HEAD, ENV=development): **2028 methods / 1696 paths** (matches Wave 3 baseline).
- After: **2006 methods / 1677 paths** → **−22 methods / −19 paths**.
- Removed paths: exactly the 19 `/national/workflows/*` paths (definitions,
  execute, executions, approvals, templates, stats, health). **No paths added,
  no method changes on any shared path.**
- This delta is the documented, expected removal of the broken surface
  (ADR-036 Consequences — NOT a byte-identical regression; every removed path
  returned HTTP 500).
- Duplicate Operation ID warnings (integration/connectors routes) are
  pre-existing and unrelated.

## 10. Build Status

| Check | Result |
|---|---|
| Backend boot | 118 route entries (was 119 — the removed `include_router`) |
| Architecture gate | **PASS** — 27 findings (27 ack, **0 new**), domain 11/11 isolation PASS, country-agnostic PASS, policy PASS |
| Full backend suite | **5066 passed / 0 failed** |
| Frontend unit | 122 passed |
| ruff / tsc / eslint | 378 / 0 / 0 |

## 11. Risks

| Risk | Severity | Mitigation |
|---|---|---|
| Out-of-repo client calling `/national/workflows/*` | Low | Surface returned 500 for every call; canonical `/niam/workflows` is the replacement |
| `workflow_runtime` archived (not importable under `app.national`) | Low | Preserved verbatim in `archive/` with provenance headers; single `git revert` restores |
| Baseline now reflects Orders 16–18 as well | Low (documented) | §4 table records the full 31→27 accounting |

## 12. Rollback Procedure

A single `git revert` of this commit restores: the 15 archived files to their
original paths, the factory wiring, the frontend page/route/nav/client section,
and the script registries. The baseline reverts to 31 (the gate then
acknowledges the workflow_runtime finding again). No data or schema is touched.

## 13. Final Certification Verdict

**PASS** — the broken national `workflow_runtime` 500-surface is retired with
full evidence; the canonical `WorkflowEngine` at `/niam/workflows` is the single
live workflow implementation; architecture gate PASS (27 ack, 0 new); full
backend suite 5066 passed / 0 failed; 14 new regression tests; every deletion is
evidence-based; the migration is independently reversible. **STOP — awaiting
explicit Program Director approval before Wave 5 (orders 20+, national-layer
migrations).**
