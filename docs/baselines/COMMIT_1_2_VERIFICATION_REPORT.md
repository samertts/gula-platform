# Commit 1.2 Verification Report

**Commit:** `PENDING` — `refactor(identity): archive dead shared.events reimplementation (ADR-028)`
**Branch:** `remediate-security-001`
**Date:** 2026-08-07

This is the permanent verification record for **Commit 1.2**, the second
commit of the **structural migration phase** governed by ADR-028
(`docs/constitution/33_STRUCTURAL_MIGRATION_CONSTITUTION.md`). It migrates the
next acknowledged Shared Core reimplementation finding
(`.ai/core/architecture/constitution_baseline.json`) to the canonical provider
by archiving the provably-dead `backend/app/identity/events.py` module and
re-pointing its sole consumer to the canonical `shared/events` bus.

Commit 1.1 (`4b115f32`) archived four dead `platform/` facades (57 → 53
findings). Commit 1.2 continues the same evidence-based, archive-first,
one-commit-at-a-time discipline.

---

## 0. Migration Impact Report (ADR-028 Rule 4)

### Files moved (1)

| From | To | Evidence |
|---|---|---|
| `backend/app/identity/events.py` | `archive/platform-shared-core/identity_events.py` | Zero production importers repo-wide; superseded by canonical `shared/events` (Shared Core `events`) |

`git mv` preserves full history (rename detected, 0 insertions / 0 deletions)
→ **a single `git revert` of this commit restores the previous state**
(ADR-028 Rule 6).

### Files removed

None. The module was *moved*, not deleted (ADR-028 Rule 5). The file survives
byte-for-byte (34 LOC confirmed) at `archive/platform-shared-core/`.

### Files replaced

None. `backend/app/identity/events.py` no longer exists in the active tree;
its capability is supplied by the existing canonical `shared/events` provider.

### Duplicate code eliminated

`identity/events.py` was a reimplementation of the `events` Shared Core
capability (signal `class\s+\w*(?:EventBus|EventEmitter|MessageBus)\b`,
matched class `IdentityEventBus`). The canonical provider is
`shared/events` (`shared/events/bus.py::EventBus`). This commit removes one
duplicate `events` implementation from the active tree.

### LOC reduction

| File | Lines |
|---|---|
| `identity/events.py` | 34 |
| **Total moved out of active tree** | **34** |

### Dependency changes

None. The archived module imported only `typing` (stdlib). Re-pointing its
sole test consumer to `shared.events` added the already-present
`shared/events` dependency to `test_niam.py` only; no package gained or lost
a dependency.

### API impact

**None.** OpenAPI schema is **byte-identical** before/after (`cmp` clean,
1696 paths, 119 routes). The archived module was not registered in any
router; `app.identity.events` had zero production consumers, so no runtime or
API surface changes.

### Frontend impact

**None.** Zero frontend files changed. `tsc` (0 errors), `eslint` (0 errors,
1 pre-existing warning in `public/sw.js`), `vitest` (122/122), `vite build`
(3.42 s) all pass. No frontend consumer references the archived module.

### Rollback procedure

```
git revert <commit-hash>
```

Single revert restores `identity/events.py` in place and reverts the
`test_niam.py` re-point (git mv is fully reversible). No database migration,
no data change, no service restart dependency beyond a normal deploy.

---

## 1. Migration Metrics (permanent section, applies to every future commit)

### Tech debt reduction

| Metric | Commit 1.1 | Commit 1.2 | Δ |
|---|---|---|---|
| Shared Core findings (acknowledged) | 53 | **52** | −1 |
| Duplicate Shared Core implementations (active tree) | 4 facades | **3** (events removed) | −1 |
| Active production modules | unchanged | unchanged (events was dead, not active) | 0 |
| Archived modules count (`archive/platform-shared-core/`) | 4 | **5** | +1 |
| LOC removed from active tree | 313 | **+34 = 347** | −34 |
| Estimated maintenance complexity reduction | 4 dead facades no longer scanned | 1 duplicate bus no longer maintained | −1 subsystem |

### Shared Core consolidation progress

- Canonical `events` provider (`shared/events`) now has exactly one consumer
  path: `backend/app/core/events.py` (re-export) + `national/services/*`
  direct imports. The identity-domain duplicate is gone.
- 52 of the original 57 acknowledged findings remain; every migration removes
  a duplicate, never adds one.

### Architecture health trend

| Gate | Commit 1.1 | Commit 1.2 |
|---|---|---|
| Architecture constitution | PASS (53 ack, 0 new) | **PASS (52 ack, 0 new)** |
| Domain certification | 11/11 | **11/11** |
| Country-agnostic | PASS | **PASS** |
| Policy engine | PASS | **PASS** |

Findings trend is monotonically decreasing (57 → 53 → 52); new findings
remain 0 (baseline-gated).

### Repository size trend

Active-tree LOC decreases (313 → 347 removed cumulative); the archive
grows by 34 lines of preserved-but-dead code. Net repository code is stable;
active production code strictly shrinks.

### Active vs Archived modules

| State | Count | Location |
|---|---|---|
| Active (production) | unchanged | `backend/app/**` |
| Archived (dead, preserved) | 5 | `archive/platform-shared-core/` |

### Production readiness trend

All quality gates stable or improving across Commit 1.1 → 1.2: backend 4993
tests pass (0 fail), OpenAPI byte-identical, frontend green, gates green.
No regressions introduced.

---

## 2. What Changed

| File | Change |
|---|---|
| `backend/app/identity/events.py` → `archive/platform-shared-core/identity_events.py` | Moved (dead `events` Shared Core reimplementation; canonical = `shared/events`) |
| `backend/tests/test_niam.py` | Re-pointed sole consumer `from app.identity.events import IdentityEventBus, event_bus` → canonical `from shared.events import EventBus, events`; `publish` → `emit` (canonical API), docstring updated |
| `.ai/core/architecture/constitution_baseline.json` | Regenerated: **53 → 52 acknowledged findings** (+ 2 country findings, unchanged) |

## 3. Dead-Code Evidence (ADR-028 Rule 2)

Objective evidence gathered before the move:

- **`grep` across `backend/`, `shared/`, `scripts/`, `frontend-v3/`**: the only
  reference to `app.identity.events` / `IdentityEventBus` / `event_bus`
  (identity-domain) is `backend/tests/test_niam.py:9`. The `national/events/`
  package is a **different module** (`app.national.events.identity_events`,
  checked — unrelated).
- **No dynamic imports**: no `importlib` target references `app.identity.events`.
- **No frontend consumers**: zero references in `.ts`/`.tsx`.
- **Not part of the identity app graph**: `backend/app/identity/__init__.py`
  imports only `.api.router`; `identity/api/router.py` imports
  `notifications` and `workflows` routes but **not** `events`.
- **`app.identity.events` module resolution verified**:
  `import app.identity.events` → `backend/app/identity/events.py` (the
  sibling empty `events/` directory has no `__init__.py`, is untracked by
  git, and is not a package).
- **Superseded**: maps to exactly one canonical provider in
  `SHARED_CORE_CATALOG` (`events` → `shared/events`), already consumed by
  live production code.

This module is therefore: **unused**, **superseded**, and **duplicated** —
satisfying Rule 2 for archiving.

## 4. Canonical-Provider Orphan Check (mandatory after every migration)

Requirement: no canonical provider may become orphaned after a migration;
each must keep ≥ 1 active consumer or carry an explicit architectural
justification.

Canonical provider affected by this migration: **`events` → `shared/events`**.

Active production consumers **after** migration:

- `backend/app/core/events.py` — re-exports the canonical singleton
  (`from shared.events import EventBus, events`) and is itself consumed by
  live services: `order_service`, `test_result_service`, `outbox_service`,
  `data_platform_service`, `communication` — all reachable from `factory.py`
  routes.
- `backend/app/national/services/family_service.py`
- `backend/app/national/services/citizen_service.py`

**Verdict: PASS.** The canonical `shared/events` provider keeps multiple
active consumers; it is not orphaned. The archived `IdentityEventBus` was
itself the duplicate, not the provider.

## 5. Behavior Preservation Verification (ADR-028 Rule 1)

| Concern | Before | After | Verdict |
|---|---|---|---|
| Runtime behavior | app boots, 4993 tests pass | app boots, **4993 tests pass, 0 fail** | ✅ unchanged |
| API behavior | 1696 OpenAPI paths | **byte-identical** OpenAPI (119 routes) | ✅ unchanged |
| Business rules | — | no rule touched | ✅ |
| Security/authorization | gates PASS | gates PASS | ✅ |
| Audit behavior | audit tests pass | audit tests pass | ✅ |
| Database behavior | no migration, no DDL | **no DB change** | ✅ |

The `TestEventBus` suite semantics are preserved exactly: subscribe → emit →
handler receives payload (2/2 tests pass against the canonical bus). The
canonical `EventBus.subscribe`/`emit` API supersedes the archived
`subscribe`/`publish` stub with identical observable behavior.

## 6. Verification Cycle (ADR-028 Rule 7)

| Gate | Result |
|---|---|
| Backend suite `pytest tests/ -q` | **4993 passed, 0 failed, 148 warnings** (593.21 s) — identical to Commit 1.1 baseline |
| Architecture gate `scripts/architecture.py check` | **PASS** — 52 findings (52 acknowledged, **0 new**), domain 11/11 isolation PASS, country-agnostic PASS, policy engine PASS |
| Domain gate `scripts/domains.py check` | PASS — isolation PASS, certification 11/11 |
| Ruff `ruff check backend/app` | **379 violations (baseline 379)** — no new |
| Ruff `ruff check backend/tests/test_niam.py` | 0 violations (isort auto-fixed import ordering) |
| OpenAPI byte-compat `cmp` | **BYTE-IDENTICAL** (1696 paths) — regenerated with correct `PYTHONPATH`, not a stale file |
| Frontend `tsc --noEmit` | 0 errors |
| Frontend `eslint .` | 0 errors (1 pre-existing warning in `public/sw.js`) |
| Frontend `vitest run` | **122 passed (9 files)** |
| Frontend `vite build` | built in 3.42 s |
| Policy/domain/architecture/event unit tests | **108 passed** (2 event + 17 architecture + 18 governance + policy engine) |
| App boot smoke test | `create_app` OK, 119 routes |

## 7. Baseline Reduction

```
Shared Core acknowledged findings:  53 → 52   (−1)
Country-hardening findings:          2 →  2   (unchanged)
New findings:                         0
```

Regenerated via `scripts/architecture.py baseline` after the migration —
acknowledged debt only ever shrinks.

## 8. Backend-as-Source-of-Truth Verification

| Concern | Result |
|---|---|
| OpenAPI compatibility | byte-identical (1696 paths) |
| Frontend compatibility | zero frontend changes; tsc/eslint/vitest/build green |
| Generated client compatibility | no client model changed (OpenAPI byte-identical) |
| Permissions compatibility | no permission touched; authorization gates PASS |
| Request/response model compatibility | no model changed; OpenAPI byte-identical |

## 9. Notes

- The archived module is preserved byte-for-byte in
  `archive/platform-shared-core/identity_events.py` and is excluded from the
  architecture scan roots (`backend/app`, `shared`) by location.
- The sibling empty `backend/app/identity/events/` directory (untracked, no
  `__init__.py`) was left in place; it is not a package and is not part of
  this commit.
- Commit 1.2 scope is intentionally minimal (1 finding): every remaining
  finding lives in **live** modules (`document_intelligence`, `kernel`,
  `integration`, `identity/notifications`, `identity/workflows`, `national/*`,
  services) or strategic national-layer code — future commits will re-point
  live consumers rather than archive.
- A concurrent author's uncommitted files (`.ai/core/architect/state/**`,
  `.ai/core/optimizer/state/benchmarks/runs.json`,
  `.ai/core/orchestrator/history/registry.json`, `ARCHITECT_IMPLEMENTATION_REPORT.md`,
  `MISSION_STATUS.md`, `OPTIMIZER_IMPLEMENTATION_REPORT.md`) are outside this
  commit's scope and were left untouched.
