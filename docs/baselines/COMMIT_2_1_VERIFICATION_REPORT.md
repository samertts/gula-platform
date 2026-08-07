# PROGRAM-01 — Commit 2.1 Verification Report

**Finding:** #43 — `rule_engine`
**Class:** Canonical Provider Promotion (ADR-029, ADR-035)
**Commit:** 2.1
**Date:** 2026-08-07
**Baseline:** 38 → 37 acknowledged findings

---

## 1. Migration Summary

| Item | Detail |
|---|---|
| Finding | `national/rules_engine/domain/expression_engine.py` — `ExpressionEngine.evaluate_rule` (complete) |
| Canonical provider | `shared/rules_engine` (was domain types only; now types + engine) |
| Why promotion | The finding is the **ONLY real `evaluate_rule` in the platform**; the canonical provider had no engine. Archiving/deleting would remove working behavior. |
| Action | `git mv` `expression_engine.py` → `shared/rules_engine/engine.py` (history preserved); imports re-pointed to `shared.rules_engine.domain.*` + `datetime.UTC`; 3 consumers re-pointed atomically |
| ADR | ADR-035 accepted first (rule engine promotion); governed by ADR-029 (promotion) + ADR-028 (migration) |

## 2. Dead-code / Reimplementation Evidence

- **Not a removal:** `ExpressionEngine` is live — instantiated by
  `RulesEngineService` (application/service.py:54) and `SimulationEngine`
  (domain/simulation.py:63), both reachable from the registered
  `/national/rules/*` router (factory.py:627, 11 endpoints).
- **Not an archive:** no duplicate canonical engine existed. `shared/rules_engine`
  contained only `domain/entities.py` + `domain/enums.py` (types); the kernel's
  `rules_runtime.py` implements its own execution loop against the shared types
  and is unrelated.
- **Ownership correction:** the only complete `evaluate_rule` implementation is
  promoted into the designated canonical path, satisfying the constitution
  signal (`rule_engine` → `shared/rules_engine`) at its source.

## 3. Migration Impact Report

**Files moved (git mv, history preserved):**

- `backend/app/national/rules_engine/domain/expression_engine.py`
  → `shared/rules_engine/engine.py` (234 LOC, byte-identical logic; only the
  import block changed: `app._compat.UTC` → `datetime.UTC`,
  `app.national.rules_engine.domain.*` → `shared.rules_engine.domain.*`)

**Consumers re-pointed atomically (same commit):**

- `backend/app/national/rules_engine/application/service.py` — imports
  `ExpressionEngine` from `shared.rules_engine.engine`
- `backend/app/national/rules_engine/domain/simulation.py` — imports
  `ExpressionEngine` from `shared.rules_engine.engine`
- `backend/app/national/rules_engine/__init__.py` — re-exports
  `EvaluationResult`, `ExpressionEngine` from the canonical engine (package
  public surface preserved)

**Canonical provider enriched:**

- `shared/rules_engine/__init__.py` — now exports `EvaluationResult`,
  `ExpressionEngine` from `shared.rules_engine.engine`

**New regression test:**

- `backend/tests/unit/test_rules_engine_promoted.py` — 14 tests covering
  evaluate_rule outcomes (pass/error/block/warning/fail by severity), missing
  fields, dict-based evaluate (and/or/not/single, unknown operator, contains,
  matches + invalid regex, between, exists/not_exists, nested dict/list path
  resolution), and the package re-export identity.

**Old namespace:** `app.national.rules_engine.domain.expression_engine`
vacated (no facade per ADR-029 Rule 4); zero in-repo references remain
(verified by repo-wide grep).

**API impact:** NONE — `/national/rules/*` routes, request/response models,
and OpenAPI surface untouched.

**Frontend impact:** NONE.

**Dependency changes:** NONE (both modules already imported by the backend).

**LOC delta:** net 0 (move) + 14 new test LOC.

## 4. Canonical-Provider Orphan Check

| Provider | Check | Result |
|---|---|---|
| `shared/rules_engine` | engine.py imports only `shared.rules_engine.domain.*` + stdlib; no `app.*` import (correct Shared-Core dependency direction) | **PASS** |
| `backend/app/national/rules_engine` | still consumed by factory router; service/simulation re-pointed; no dangling import | **PASS** |
| Kernel `rules_runtime` | untouched, still imports shared domain types | **PASS** |

## 5. Behavior Preservation

- **Smoke (live API):** `evaluate_rule` on an empty rule → `PASS`; dict-based
  `evaluate` EQ → passes. Package re-export identity: `app.national.rules_engine
  .ExpressionEngine is shared.rules_engine.ExpressionEngine` → True.
- **Boot:** app boots, **119 routes** (identical to Wave 1 final state).
- **Regression suite:** backend **4954 passed / 0 failed** (4940 baseline +
  14 new rules-engine tests), 148 warnings.
- **OpenAPI:** no contract change (route registration untouched).
- **DB:** no DDL change.

## 6. Verification Matrix (Commit 2.1)

| # | Verification | Result |
|---|---|---|
| 1 | Architecture Constitution | **PASS** — 37 findings (37 ack, **0 new**) |
| 2 | Policy Engine | **PASS** |
| 3 | Domain Certification | **PASS** — 11/11, isolation PASS |
| 4 | OpenAPI | **PASS** — no contract change |
| 5 | Generated Clients | **PASS** — no model change |
| 6 | Frontend Compatibility | **PASS** — tsc 0, eslint 0 errors (1 pre-existing warning), vitest 122/122, vite build OK |
| 7 | Permissions | **PASS** — no route/permission touched |
| 8 | Database Compatibility | **PASS** — no DDL change |
| 9 | Behavior Preservation | **PASS** — live-API smoke + 4954-suite |
| 10 | Performance | **PASS** — no hot-path change (move only) |
| 11 | Regression Tests | **PASS** — 4954 passed / 0 failed |
| 12 | Build Validation | **PASS** — boot 119 routes; py_compile clean on all touched modules |
| 13 | CI (`make validate`) | **PASS** — full suite green (see above) |
| 14 | Repository Health | **PASS** — ruff 0 on changed scope (2 I001 auto-fixed) |
| 15 | Orphan Check | **PASS** — §4 |
| 16 | Ruff changed scope | **PASS** — 0 remaining |

## 7. Baseline & Rollback

- Baseline regenerated: 38 → **37** acknowledged findings (`constitution_baseline.json`).
- **Rollback class:** L (instant, zero coordination). Single
  `git revert <hash>` restores the engine to the national namespace and the
  canonical provider to types-only; no data or coordination involved.

## 8. Report Trail

- ADR-035 (this promotion): `docs/adr/ADR-035-rule-engine-promotion.md`
- Classification §2.13 (marked DONE): `docs/baselines/ARCHITECTURAL_MIGRATION_CLASSIFICATION.md`
- Dashboard: `PROGRAM-01_DASHBOARD.md`
- Regenerated docs: MASTER_ARCHITECTURE_v2.md, SHARED_CORE_REGISTRY.md,
  MASTER_REMAINING_WORK.md, ARCHITECTURE_CERTIFICATION.md
