# Commit 1.13 Verification Report

**Commit:** *(pending hash)* — `refactor(national): archive orphan WorkflowNotifier ABC (ADR-028)`
**Branch:** `remediate-security-001`
**Date:** 2026-08-07
**Framework:** PROGRAM-01 Execution Framework (13-stage lifecycle, §2 matrix, §3 exit criteria)

This is the permanent verification record for **Commit 1.13**, the thirteenth
commit of the **structural migration phase** governed by ADR-028
(`docs/constitution/33_STRUCTURAL_MIGRATION_CONSTITUTION.md`) and executed
under the **PROGRAM-01 Execution Framework** (`PROGRAM-01_EXECUTION_FRAMEWORK.md`).
It migrates one acknowledged finding of the **`notifications`** Shared Core
capability: **#25** (`national/workflow_runtime/application/interfaces.py::WorkflowNotifier`).

Commit 1.12 (`9f52dc2a`) archived the dead EmergencyQR service twins (42 → 40).
This is **Wave 1 order 10** (40 → 39).

---

## 0. Migration Impact Report (ADR-028 Rule 4)

### Files moved (0) / extracted (1)

No whole files moved — this migration **extracts one orphan ABC** from a live
module (Commit 1.7 `AuditLogger` / Commit 1.12 `EmergencyQR` precedent),
preserving the surrounding non-finding code in place.

| Extracted (archived) | Source (edited) | Evidence |
|---|---|---|
| `WorkflowNotifier` (ABC, 3 abstract methods) → `archive/platform-shared-core/workflow_runtime_notifier.py` | `backend/app/national/workflow_runtime/application/interfaces.py` | The whole `workflow_runtime/application/` package has **zero importers** repo-wide; the only workflow_runtime lazy import (`api/routes.py:29`) targets the dormant `app.national.n.application.service` (a different package), not this one. `WorkflowNotifier` had zero consumers |

The archived ABC is preserved **byte-for-byte** (class body unchanged; only the
module docstring/header was added for provenance). A **single `git revert`**
of the implementation commit restores the class in place.

### Files removed

None. `WorkflowNotifier` survives byte-for-byte at
`archive/platform-shared-core/workflow_runtime_notifier.py` (ADR-028 Rule 5).

### Files replaced

None. Canonical provider `backend/app/workflows` was not modified.

### Duplicate code eliminated

One Shared Core duplicate removed from the active tree: `WorkflowNotifier` — an
orphan notification ABC (a `notifications` reimplementation surface), never
implemented or consumed; the live canonical is `backend/app/workflows`.

### LOC reduction

| File | Lines |
|---|---|
| `national/workflow_runtime/application/interfaces.py` — `WorkflowNotifier` (23 L, incl. trailing blank) | −23 |
| **Total removed from active tree** | **−23** |

### Dependency changes

- `workflow_runtime/application/interfaces.py` still imports `ABC`/`abstractmethod`
  (used by the remaining `WorkflowStepExecutor`, `WorkflowApprovalHandler`,
  `WorkflowTimerHandler` ABCs) and `Any` (used by `WorkflowStepExecutor`).
  **No imports removed.**
- The archive module imports `ABC`/`abstractmethod`/`Any` independently.

### API impact

**None.** OpenAPI schema is **unchanged** — no route, model, or permission
touched. The ABC was never wired. Boot verified: **119 routes** (unchanged).

### Frontend impact

**None.** Zero frontend files changed.

### Rollback procedure

```
git revert <implementation-commit-hash>
```

Single revert restores the class in place (a 23-line deletion, fully
reversible). No database migration, no data change.

---

## 1. Migration Metrics (permanent section)

### Tech debt reduction

| Metric | Commit 1.12 | Commit 1.13 | Δ |
|---|---|---|---|
| Shared Core findings (acknowledged) | 40 | **39** | −1 |
| Duplicate Shared Core implementations (active tree) | qr twins removed | **notifications orphan removed** | −1 |
| Archived modules count (`archive/platform-shared-core/`) | 20 | **21** | +1 |
| LOC removed from active tree | 2272 | **+23 = 2295** | −23 |

### Shared Core consolidation progress

- Canonical `backend/app/workflows` keeps its live consumers (unchanged — the
  archived ABC did not consume it).
- 39 of the original 57 acknowledged findings remain; every migration removes
  a duplicate, never adds one.

### Architecture health trend

| Gate | Commit 1.12 | Commit 1.13 |
|---|---|---|
| Architecture constitution | PASS (40 ack, 0 new) | **PASS (39 ack, 0 new)** |
| Domain certification | 11/11 | **11/11** |
| Country-agnostic | PASS | **PASS** |
| Policy engine | PASS | **PASS** |

Findings trend is monotonically decreasing (57 → 39); new findings remain 0
(baseline-gated).

### Repository size trend

Active-tree LOC decreases (2272 → 2295 removed cumulative); the archive grows
by 1 module. Active production code strictly shrinks.

### Active vs Archived modules

| State | Count | Location |
|---|---|---|
| Active (production) | unchanged | `backend/app/**` |
| Archived (dead, preserved) | 21 files | `archive/platform-shared-core/` |

### Production readiness trend

All quality gates stable across Commit 1.12 → 1.13: backend tests pass (0
fail), architecture gate PASS, ruff baseline unchanged (379), boot 119 routes.
No regressions introduced.

---

## 2. What Changed

| File | Change |
|---|---|
| `backend/app/national/workflow_runtime/application/interfaces.py` | Removed `WorkflowNotifier` (ABC, finding #25). `WorkflowStepExecutor`/`WorkflowApprovalHandler`/`WorkflowTimerHandler` (not findings) untouched; no import change |
| `archive/platform-shared-core/workflow_runtime_notifier.py` | **New** — `WorkflowNotifier` preserved byte-for-byte (Commit 1.7/1.12 precedent) |
| `.ai/core/architecture/constitution_baseline.json` | Regenerated: **40 → 39 acknowledged findings** (+ 2 country findings, unchanged) |
| Master docs (`MASTER_ARCHITECTURE_v2`, `SHARED_CORE_REGISTRY`, `MASTER_REMAINING_WORK`, `ARCHITECTURE_CERTIFICATION`) | Regenerated via `scripts/architecture/docs.py` + `scripts/architecture.py report` |
| `docs/baselines/ARCHITECTURAL_MIGRATION_CLASSIFICATION.md` | #25 row marked **DONE — Commit 1.13**; Wave-1 order 10 marked done; §9 evidence note + §10 Next Action updated |
| `PROGRAM-01_DASHBOARD.md` | Metrics M1/M3/M4/M5/M7/M8/M11 + notifications row + Wave 1 status + commit log updated |

## 3. Dead-Code Evidence (ADR-028 Rule 2)

Objective evidence gathered before the extraction:

**Finding #25 — `WorkflowNotifier` / `workflow_runtime/application/interfaces.py`:**
- **No production consumers**: `WorkflowNotifier` appears nowhere in
  `backend/app`, `backend/tests`, `scripts/`, `shared/`, or `frontend-v3/`
  (only the class definition itself).
- **Orphan module**: the whole `workflow_runtime/application/` package has zero
  importers repo-wide. Its `__init__.py` is empty; `service.py` is **0 bytes**.
  The one workflow_runtime lazy import (`api/routes.py:29`) targets
  `app.national.n.application.service` — the dormant `national/n` package, a
  *different* package from `workflow_runtime/application/`.
- **No tests**: zero test references repo-wide.
- **No dynamic imports**, **no frontend consumers**.
- **Superseded/orphaned**: notification delivery lives in
  `backend/app/notifications`; the workflow engine surface lives in
  `backend/app/workflows`. This ABC was never implemented, never registered,
  and never consumed.

**Live code protected (verified before commit):**
- `WorkflowStepExecutor`, `WorkflowApprovalHandler`, `WorkflowTimerHandler`
  (orphan ABCs, **not** Shared Core findings — none match a scan signal) —
  **kept** in place (dormant national module preservation; GULA Constitution).
- The rest of the dormant `workflow_runtime/` package (domain/saga/infrastructure
  under `national/n`) — **kept**; the wired-but-broken route finding #44 is a
  separate Wave 4 order (ADR-036).

All extracted code satisfies Rule 2: **unused** and **superseded**.

## 4. Canonical-Provider Orphan Check (mandatory after every migration)

Requirement: no canonical provider may become orphaned after a migration; each
must keep ≥ 1 active consumer or carry an explicit architectural justification.

Canonical providers affected:
- **`notifications` → `backend/app/notifications`**: the archived ABC did not
  consume this canonical (it was an interface only). Live consumers unchanged.
- **`workflow_engine` → `backend/app/workflows`** (the finding was filed under
  `notifications`, but the module lives in the workflow_runtime package whose
  canonical is the workflows engine): `backend/app/workflows` is live and its
  consumers are unchanged.

**Verdict: PASS.**

## 5. Behavior Preservation Verification (ADR-028 Rule 1)

| Concern | Before | After | Verdict |
|---|---|---|---|
| Runtime behavior | app boots, tests pass | app boots (**119 routes**), tests pass | ✅ unchanged |
| API behavior | no route touched | **no route touched** (119 routes, identical set) | ✅ unchanged |
| Business rules | — | no rule touched | ✅ |
| Security/authorization | gates PASS | gates PASS | ✅ |
| Audit behavior | — | no audit path touched | ✅ |
| Database behavior | no migration, no DDL | **no DB change** | ✅ |
| Import integrity | `workflow_runtime.application` not imported anywhere | still not imported anywhere; `interfaces.py` still parses and its remaining ABCs import clean | ✅ unchanged |

The extracted ABC was dead: no runtime path could observe a behavior
difference.

## 6. Verification Cycle (ADR-028 Rule 7 / Framework §2)

| Gate | Result |
|---|---|
| Architecture gate `scripts/architecture.py check` | **PASS** — 39 findings (39 acknowledged, **0 new**), domain 11/11 isolation PASS, country-agnostic PASS, policy engine PASS |
| `scripts/architecture.py baseline` | baseline written: **39 findings, 2 country findings** |
| Ruff on changed scope (interfaces.py, archive module) | 0 violations (unused-import fix applied; SyntaxWarning in archive docstring cleaned) |
| App boot smoke test | app boots OK, **119 routes** (unchanged) |
| AST parse of touched files | OK (py_compile, no warnings with `-W error::SyntaxWarning`) |
| Removed-symbol scan | zero references to `WorkflowNotifier` in the active tree |
| Database compatibility | no migration, no DDL; chain intact |
| Permissions | no permission touched; authorization gates PASS |
| Frontend compatibility | zero frontend changes (tsc/eslint/vitest/build green on baseline) |

## 7. Baseline Reduction

```
Shared Core acknowledged findings:  40 → 39   (−1)
Country-hardening findings:          2 →  2   (unchanged)
New findings:                         0
```

Regenerated via `scripts/architecture.py baseline` after the migration —
acknowledged debt only ever shrinks.

## 8. Backend-as-Source-of-Truth Verification

| Concern | Result |
|---|---|
| OpenAPI compatibility | no route touched; schema unchanged |
| Frontend compatibility | zero frontend changes |
| Generated client compatibility | no client model changed |
| Permissions compatibility | no permission touched; authorization gates PASS |
| Request/response model compatibility | no model changed |

## 9. Notes

- The archived ABC is preserved byte-for-byte at
  `archive/platform-shared-core/workflow_runtime_notifier.py` with a provenance
  docstring and is excluded from the architecture scan roots (`backend/app`,
  `shared`) by location.
- Scope was intentionally minimal and strictly tied to finding #25. The other
  orphan ABCs in `interfaces.py` are **not** findings and were left untouched
  (GULA Constitution: never remove dormant enterprise modules).
- Commit 1.13 scope (1 finding). Next: Wave 1 order 11 (final order) — #39
  `national/workflows/base.py` dead ABC archive.
