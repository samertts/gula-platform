# Commit 1.3 Verification Report

**Commit:** `b393aac3` — `refactor(workflows): migrate live identity/workflows engine to canonical app.workflows (ADR-028)`
**Branch:** `remediate-security-001`
**Date:** 2026-08-07

This is the permanent verification record for **Commit 1.3**, the third commit
of the **structural migration phase** governed by ADR-028
(`docs/constitution/33_STRUCTURAL_MIGRATION_CONSTITUTION.md`). It is the
**first live-component Shared Core migration**: the acknowledged
`workflow_engine` reimplementation finding
(`backend/app/identity/workflows/engine.py`) is migrated **into** the
canonical provider path `backend/app/workflows/`, rather than archived —
because the canonical `workflow_engine` providers are **not behaviorally
equivalent** to the live engine.

Commits 1.1/1.2 (`4b115f32`, `576ade1d`) archived provably-dead facades.
Commit 1.3 is different in kind: it **elevates a live implementation to its
canonical path** (57 → 51 findings).

---

## 0. Migration Impact Report (ADR-028 Rule 4)

### Files moved (2)

| From | To | Evidence |
|---|---|---|
| `backend/app/identity/workflows/engine.py` | `backend/app/workflows/engine.py` | Live `WorkflowEngine` (237 LOC) — canonical `workflow_engine` provider must host it |
| `backend/app/identity/workflows/models.py` | `backend/app/workflows/models.py` | `niam_wf_*` ORM models (4268 B) — must move with engine so canonical provider stays self-contained (shared core must not import from a domain) |

`git mv` preserves full history (rename detected) → **a single `git revert`
of this commit restores the previous state** (ADR-028 Rule 6).

### Files created

| File | Purpose |
|---|---|
| `backend/app/workflows/__init__.py` | Makes the canonical package a regular package (was an empty namespace directory) |
| `docs/baselines/COMMIT_1_3_VERIFICATION_REPORT.md` | This report |

### Files removed / replaced

None. Both modules survive byte-for-byte at their new canonical location
(ADR-028 Rule 5: prefer moving before deleting).

### Duplicate code eliminated

The acknowledged finding `workflow_engine` (signal
`WorkflowEngine|WorkflowManager|WorkflowExecutor|def execute_workflow`,
matched `backend/app/identity/workflows/engine.py::WorkflowEngine`) is
resolved: the live implementation now **is** the canonical provider. The
`shared/workflow/engine.py` 75-LOC synchronous in-memory engine and the
`backend/app/capabilities/workflow_engine/` stub remain in the tree as
dormant canonical-provider shells (unused, no runtime importers — verified)
but the *duplicate live* engine no longer exists outside the canonical path.

### LOC reduction

| File | Lines |
|---|---|
| `identity/workflows/engine.py` | 237 |
| `identity/workflows/models.py` | ~115 |
| **Total relocated into canonical path** | **352** |

### Dependency changes

None at package level. `app.workflows.engine` imports `app.workflows.models`
(relative, unchanged) and `app.identity.base` (`IdentityBaseEntity` — a
Shared Core provider, allowed). `routes.py` dependency changed from
`app.identity.workflows.engine` → `app.workflows.engine` (identity domain →
Shared Core: the correct direction).

### API impact

**None.** OpenAPI schema is **byte-identical** before/after (`cmp` clean,
1696 paths, 119 routes). The route layer stays at
`backend/app/identity/workflows/routes.py` (prefix `/workflows`, tag "NIAM
Workflows"), preserving `/niam/workflows/*` (definitions, instances,
approvals) and `/workflow-engine/*` surface exactly.

### Frontend impact

**None.** Zero frontend files changed. `tsc` (0 errors), `eslint` (0 errors,
1 pre-existing warning in `public/sw.js`), `vitest` (122/122), `vite build`
(3.34 s) all pass. `WorkflowsPage.tsx` consumes `/niam/workflows/*` via raw
`api.get/post` — endpoint paths unchanged.

### Rollback procedure

```
git revert <commit-hash>
```

Single revert restores `engine.py`/`models.py` to `identity/workflows/` and
reverts the `routes.py` + `test_niam_v2.py` re-points. No database migration,
no data change, no service restart dependency beyond a normal deploy.

---

## 1. Architecture Decision Rationale (required for live-component migrations)

### Why the old location leaves the active tree

`identity/workflows/engine.py` was a **reimplementation** of the Shared Core
`workflow_engine` capability inside the identity domain. Per
`backend/app/domain_platform/shared_core.py`, `workflow_engine` is a
guarded Shared Core capability whose canonical providers are
`app.workflows.*`, `shared/workflow/*`, and
`app.capabilities.workflow_engine` (see `SHARED_CORE_CATALOG` and
`SHARED_CORE_PROVIDER_PREFIXES`). The engine lived under `app.identity.` —
outside the canonical provider set — so the architecture constitution
flagged it (`SHARED_CORE_SIGNALS` scan), and Domain Sovereignty treats it as
a cross-domain duplication. Keeping it would keep the finding open forever.

### Why the canonical location now owns it

| Canonical candidate | State before Commit 1.3 | Verdict |
|---|---|---|
| `backend/app/workflows/` | Empty directory, no `__init__.py` | **Chosen** — the canonical home; populated by this migration |
| `shared/workflow/engine.py` | 75-LOC synchronous in-memory engine; **no persistence, approvals, or DB** | NOT behaviorally equivalent — cannot host the live engine |
| `backend/app/capabilities/workflow_engine/` | Stub; `domain/repository.py` raises `NotImplementedError` | NOT behaviorally equivalent — cannot host the live engine |

Since no canonical provider could host the live engine, archiving
(Commits 1.1/1.2 approach) was **impossible**: the persisted `/niam/workflows`
API must keep working. The correct ADR-028 move is **elevate, not archive** —
the live engine *becomes* the canonical provider. This both resolves the
finding and populates the empty canonical directory with real behavior.

### Ownership analysis (before → after)

| Concern | Before | After |
|---|---|---|
| Engine implementation | `identity/workflows/engine.py` (identity domain) | `workflows/engine.py` (Shared Core canonical) |
| ORM models (`niam_wf_*`) | `identity/workflows/models.py` | `workflows/models.py` (registers on `IdentityBase.metadata` — unchanged) |
| API routes `/niam/workflows/*` | `identity/workflows/routes.py` | **unchanged** — stays in identity, imports canonical engine |
| Authorization | route-level, unchanged | unchanged |
| Registry / catalog | duplicate outside canonical set | canonical path recognized by `SHARED_CORE_CATALOG` + `_is_canonical` |

`app.workflows.*` was already in `SHARED_CORE_PROVIDER_PREFIXES`
(`domain_platform/shared_core.py`), so the moved engine is **automatically
exempt** from the reimplementation scan (canonical file under a canonical
prefix) — verified by the gate dropping 52 → 51.

---

## 2. Migration Metrics (permanent section)

### Tech debt reduction

| Metric | Commit 1.2 | Commit 1.3 | Δ |
|---|---|---|---|
| Shared Core findings (acknowledged) | 52 | **51** | −1 |
| Duplicate live implementations | 1 (workflow engine) | **0** | −1 |
| Canonical provider directories populated | 0 | **1** (`backend/app/workflows/`) | +1 |
| Active-tree LOC (live engine) | in identity domain | in canonical path | 0 (relocated) |
| Findings trend | 57 → 52 | **57 → 51** | monotonic |

### Architecture health trend

| Gate | Commit 1.2 | Commit 1.3 |
|---|---|---|
| Architecture constitution | PASS (52 ack, 0 new) | **PASS (51 ack, 0 new)** |
| Domain certification | 11/11 | **11/11** |
| Country-agnostic | PASS | **PASS** |
| Policy engine | PASS | **PASS** |
| Kernel check | — | **ALL CHECKS PASSED** |

---

## 3. Consumer Impact Analysis (Rule: every live migration)

### Direct consumers of `identity/workflows/engine.py` (re-pointed)

| Consumer | Before | After |
|---|---|---|
| `backend/app/identity/workflows/routes.py` (`WorkflowEngine(db)` at lines 10,29,51,61,77,95,110,128,143) | `from .engine import WorkflowEngine` | `from app.workflows.engine import WorkflowEngine` |

`assert_shared_core_or_domain_exception()` (route helper) PASS — the identity
route layer correctly consumes a Shared Core provider.

### Runtime wiring (unchanged path)

`factory.py:800` → `app.identity.api.router` → `identity/api/router.py:14`
`from app.identity.workflows import routes as workflows_routes` → same route
module, same prefix, same tags. Request flow is byte-identical.

### Test consumers (re-pointed)

`backend/tests/test_niam_v2.py:402,417,434` — `WorkflowDefinition`,
`WorkflowInstance`, `WorkflowApproval` imports moved to
`app.workflows.models`. No test asserts on the module path.

### Frontend / API consumers (no change needed)

`frontend-v3/src/pages/niam/WorkflowsPage.tsx` — raw `api.get/post` on
`/niam/workflows/{definitions,instances}`; paths unchanged.
`frontend-v3/src/api/generated/client.ts:1131-1145` — `niam_workflowsApi`
hooks bind `/niam/workflows/*`; OpenAPI byte-identical → generated client
byte-identical.

### No-owner consumers

`WorkflowNotification` (models.py:85) has no consumer other than itself —
moved with its module, zero impact.

---

## 4. Hidden Coupling Audit (Rule: reflection / importlib / getattr / string imports / plugins / runtime registration / monkeypatching)

Scanned `engine.py`, `models.py`, `routes.py`, `test_niam_v2.py`:

| Mechanism | Found | Verdict |
|---|---|---|
| `importlib` / `__import__` / `import_module` | none | clean |
| `sys.modules` manipulation | none | clean |
| `getattr`/`setattr` on module-level names | none | clean |
| String imports / plugin registration | none | clean |
| Runtime decorator registration | none | clean |
| Monkeypatching of module path | none | clean |
| All imports | static `from .models` / `from app.*` | confirmed |

No hidden coupling to the old module path exists.

---

## 5. Runtime Execution Path (before → after)

```
HTTP request /niam/workflows/definitions (POST)
  → identity/api/router.py:14 (unchanged)
    → identity/workflows/routes.py::create_definition (unchanged)
      → from app.workflows.engine import WorkflowEngine   [was: app.identity.workflows.engine]
        → WorkflowEngine(db).create_definition(...)       [same class, same module behavior]
          → WorkflowDefinition ORM → IdentityBase metadata (unchanged)
            → SQLAlchemy async session (unchanged)
```

Every hop except the engine's module path is unchanged; the engine module
itself is byte-identical at its new location. `engine.__module__` changed
`app.identity.workflows.engine` → `app.workflows.engine` (observable only via
reflection, which no code performs — see §4).

---

## 6. Behavior Preservation Verification (ADR-028 Rule 1)

| Concern | Before | After | Verdict |
|---|---|---|---|
| Runtime behavior | app boots, 4993 tests pass | app boots, **4993 tests pass, 0 fail** (612.29 s) | ✅ unchanged |
| API behavior | 1696 OpenAPI paths | **byte-identical** OpenAPI (1696 paths, 119 routes) | ✅ unchanged |
| Business rules | workflow create/approve/cancel/pending | identical logic (module byte-identical) | ✅ |
| Security/authorization | gates PASS | gates PASS | ✅ |
| Audit behavior | audit tests pass | audit tests pass | ✅ |
| Database behavior | `niam_wf_definitions/instances/approvals/notifications` on `IdentityBase.metadata` | **same 4 tables** on `IdentityBase.metadata` (verified) | ✅ no DB change |

The workflow suite semantics are preserved exactly: `test_niam_v2.py`
workflow tests (89 niam tests pass) exercise create-definition → create-
instance → approve against the canonical-located engine.

---

## 7. Backend-as-Source-of-Truth Verification

| Concern | Result |
|---|---|
| OpenAPI compatibility | byte-identical (1696 paths), regenerated fresh with correct `PYTHONPATH` |
| Frontend compatibility | zero frontend changes; tsc/eslint/vitest/build green |
| Generated client compatibility | OpenAPI byte-identical → `client.ts` regenerated = byte-identical (governance drift is concurrent-author WIP, reverted) |
| Permissions compatibility | no permission touched; authorization gates PASS |
| Request/response model compatibility | no model changed; OpenAPI byte-identical |
| Route compatibility | `/niam/workflows/*` prefix, tag, and handlers unchanged |
| ORM registration | `niam_wf_*` tables still on `IdentityBase.metadata` (not orphaned to another base) |

---

## 8. Verification Cycle (ADR-028 Rule 7)

| Gate | Result |
|---|---|
| Backend suite `pytest tests/ -q` | **4993 passed, 0 failed, 148 warnings** (612.29 s) — identical to Commit 1.2 baseline |
| Architecture gate `scripts/architecture.py check` | **PASS** — 51 findings (51 acknowledged, **0 new**), domain 11/11 isolation PASS, country-agnostic PASS, policy engine PASS |
| Domain gate `scripts/domains.py check` | PASS — isolation PASS, certification 11/11 |
| Kernel check `python -m scripts.kernel.cli check` | **ALL KERNEL CHECKS PASSED** |
| Ruff `ruff check app` | **379 violations (baseline 379)** — no new |
| Ruff `ruff check app/workflows app/identity/workflows tests/test_niam_v2.py` | 0 violations |
| OpenAPI byte-compat | **BYTE-IDENTICAL** (1696 paths) — fresh regen, `==` on full JSON |
| Frontend `tsc --noEmit` | 0 errors |
| Frontend `eslint .` | 0 errors (1 pre-existing warning in `public/sw.js`) |
| Frontend `vitest run` | **122 passed (9 files)** |
| Frontend `vite build` | built in 3.34 s |
| App boot + imports | `WorkflowEngine`, models, routes import OK; 4 tables on `IdentityBase.metadata` |

---

## 9. Baseline Reduction

```
Shared Core acknowledged findings:  52 →  51   (−1)
Country-hardening findings:          2 →   2   (unchanged)
New findings:                         0
Removed finding: backend/app/identity/workflows/engine.py  (workflow_engine)
```

Regenerated via `scripts/architecture.py baseline` after the migration —
acknowledged debt only ever shrinks.

---

## 10. Canonical-Provider Orphan Check (mandatory after every migration)

Canonical providers touched by this migration:

- **`backend/app/workflows/` (now populated)** — active consumers after
  migration: `identity/workflows/routes.py` (production) + `test_niam_v2.py`
  (tests). **NOT orphaned.**
- **`shared/workflow/`** — unchanged, dormant canonical shell. Zero runtime
  importers (verified: `grep` for `shared.workflow` finds only
  `scripts/architecture/core.py:61` canonical-path allowlist). Pre-existing
  dormant state, not orphaned by this migration.
- **`backend/app/capabilities/workflow_engine/`** — unchanged, dormant stub.
  Same status as before; its `/workflow-engine/*` routes were never registered
  in `factory.py` (verified in Commit 1.3 analysis), pre-existing.

**Verdict: PASS.** The migration introduces no new orphan; the canonical
`app.workflows` provider gains its first live consumer.

---

## 11. Notes

- Commit 1.3 scope is intentionally minimal (1 finding): the route layer
  stays in the identity domain (it *owns* the `/niam/workflows` API), while
  the engine + models are canonical. Future commits migrate remaining live
  findings (notifications/audit/authorization/barcode/qr/encryption)
  one at a time with the same discipline.
- `backend/app/national/workflows/base.py` defines a **different**
  `WorkflowEngine[T]` abstract base used by national referral workflows —
  out of scope, untouched.
- The concurrent author's uncommitted files (`.ai/core/**state`,
  `frontend-v3/src/api/generated/*` governance drift, `MISSION_STATUS.md`,
  root reports) are outside this commit's scope and were left untouched —
  the regenerated `client.ts`/`types.ts` drift was **reverted** to keep this
  commit atomic.
- This is the first live-component migration: behavior preservation was
  verified via byte-identical OpenAPI + identical 4993-test suite, not just
  dead-code evidence.

## 12. Governing Documents (this promotion)

This migration is formally classified as a **Canonical Provider Promotion**
(not a Shared Core removal). The governing planning and decision artifacts:

- **`docs/adr/ADR-029-canonical-provider-promotion.md`** — the ADR that
  changes the canonical ownership of the Workflow Engine and defines
  Canonical Provider Promotion as a recognized ADR-028 migration mode.
- **`docs/baselines/CANONICAL_PROMOTION_PLAN_WORKFLOW_ENGINE.md`** — the
  pre-implementation promotion plan: why the canonical candidates are
  insufficient, why the live engine is the long-term owner, migration /
  compatibility / namespace / import / backward-compat strategy, and
  Domain Platform / Shared Core / Architecture Constitution implications.
- **`docs/adr/README.md`** — ADR index updated (ADR-026..029).

