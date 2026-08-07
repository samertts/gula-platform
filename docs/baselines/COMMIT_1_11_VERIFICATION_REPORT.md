# Commit 1.11 Verification Report

**Commit:** `63d2f2bf` — `refactor(national): archive dead risk-based-auth cluster + refresh architect/optimizer state (ADR-028)`
**Branch:** `remediate-security-001`
**Date:** 2026-08-07
**Framework:** PROGRAM-01 Execution Framework (13-stage lifecycle, §2 matrix, §3 exit criteria)

This is the permanent verification record for **Commit 1.11**, the eleventh
commit of the **structural migration phase** governed by ADR-028
(`docs/constitution/33_STRUCTURAL_MIGRATION_CONSTITUTION.md`) and executed
under the **PROGRAM-01 Execution Framework** (`PROGRAM-01_EXECUTION_FRAMEWORK.md`).
It migrates acknowledged finding **#22** (`identity` Shared Core capability:
`services/risk_based_auth_service.py`) by archiving it plus its two test files.

Commit 1.10 (`c6f906d8`) archived the dead national identity service cluster
(44 → 43). This is **Wave 1 order 8** (43 → 42).

---

## 0. Migration Impact Report (ADR-028 Rule 4)

### Files moved (3)

| From | To | Evidence |
|---|---|---|
| `backend/app/services/risk_based_auth_service.py` (300 LOC: `RiskBasedAuthService`, `AuthContext`, `AuthDecision`, `AdaptiveAuthWeights`, `AuthRiskLevel`, `RequiredAction` enums) | `archive/platform-shared-core/risk_based_auth_service.py` | Zero live consumers repo-wide; **no `__init__.py` re-export existed**; `backend/app` contains no reference outside the module itself. Superseded by canonical `identity/adaptive_auth` (live) |
| `backend/tests/test_risk_based_auth.py` (288 LOC: `TestRiskBasedAuth`) | `archive/platform-shared-core/test_risk_based_auth.py` | Sole consumer was the module itself (tests of dead code) |
| `backend/tests/unit/test_risk_based_auth_service.py` (317 LOC) | `archive/platform-shared-core/test_risk_based_auth_service.py` | Sole consumer was the module itself (tests of dead code) |

All three `git mv` renames were **detected at 100% similarity (0 insertions /
0 deletions)** → **a single `git revert 63d2f2bf` restores the previous state**
(ADR-028 Rule 6).

### Files removed

None. All three files were *moved*, not deleted (ADR-028 Rule 5); they survive
byte-for-byte at `archive/platform-shared-core/`.

### Files replaced

None. Canonical provider `identity/adaptive_auth` was not modified.

### Duplicate code eliminated

One Shared Core duplicate removed from the active tree:
- `RiskBasedAuthService` — reimplementation of the `identity` capability
  (canonical `identity/adaptive_auth`, live). Dead — never wired to any route,
  never instantiated outside its own tests.

### LOC reduction

| File | Lines |
|---|---|
| `services/risk_based_auth_service.py` (whole module) | 300 |
| `tests/test_risk_based_auth.py` (whole file) | 288 |
| `tests/unit/test_risk_based_auth_service.py` (whole file) | 317 |
| **Total removed from active tree** | **905** |
| Archived (preserved, non-active) | +905 |

### Dependency changes

- `backend/app/services/__init__.py` required **no change** — it never
  re-exported `RiskBasedAuthService` (verified: no reference in any
  `backend/app` file outside the module itself).
- `backend/tests/` no longer collects the two risk-based-auth test files;
  no remaining test imports them (verified: zero references repo-wide).

### API impact

**None.** OpenAPI schema is **unchanged** — no route, model, or permission
touched. `RiskBasedAuthService` was never wired to a route. Boot verified:
**119 routes** (unchanged).

### Frontend impact

**None.** Zero frontend files changed.

### Rollback procedure

```
git revert 63d2f2bf
```

Single revert restores all three files in place (git mv fully reversible) and
restores the test collection. No database migration, no data change.

---

## 1. Migration Metrics (permanent section)

### Tech debt reduction

| Metric | Commit 1.10 | Commit 1.11 | Δ |
|---|---|---|---|
| Shared Core findings (acknowledged) | 43 | **42** | −1 |
| Duplicate Shared Core implementations (active tree) | identity dup (national) removed | **identity dup (risk-based-auth) removed** | −1 |
| Archived files count (`archive/platform-shared-core/`) | 15 | **18** | +3 |
| LOC removed from active tree | 1250 | **+905 = 2155** | −905 |

### Shared Core consolidation progress

- Canonical `identity` providers (`backend/app/identity`, incl.
  `identity/adaptive_auth`) keep their live consumers (unchanged — the
  archived module did not consume them).
- 42 of the original 57 acknowledged findings remain; every migration removes
  a duplicate, never adds one.

### Architecture health trend

| Gate | Commit 1.10 | Commit 1.11 |
|---|---|---|
| Architecture constitution | PASS (43 ack, 0 new) | **PASS (42 ack, 0 new)** |
| Domain certification | 11/11 | **11/11** |
| Country-agnostic | PASS | **PASS** |
| Policy engine | PASS | **PASS** |

Findings trend is monotonically decreasing (57 → 42); new findings remain 0
(baseline-gated).

### Repository size trend

Active-tree LOC decreases (1250 → 2155 removed cumulative); the archive grows
by 905 lines of preserved-but-dead code. Active production code strictly
shrinks.

### Active vs Archived modules

| State | Count | Location |
|---|---|---|
| Active (production) | unchanged | `backend/app/**` |
| Archived (dead, preserved) | 18 files (14 modules + 4 test files) | `archive/platform-shared-core/` |

### Production readiness trend

All quality gates stable across Commit 1.10 → 1.11: backend tests pass (0
fail), architecture gate PASS, ruff baseline unchanged (379), boot 119 routes.
No regressions introduced.

---

## 2. What Changed

| File | Change |
|---|---|
| `backend/app/services/risk_based_auth_service.py` → `archive/platform-shared-core/risk_based_auth_service.py` | **Moved** (`git mv`, rename detected 100%) — finding #22, whole dead module |
| `backend/tests/test_risk_based_auth.py` → `archive/platform-shared-core/test_risk_based_auth.py` | **Moved** — test of dead code |
| `backend/tests/unit/test_risk_based_auth_service.py` → `archive/platform-shared-core/test_risk_based_auth_service.py` | **Moved** — test of dead code |
| `.ai/core/architecture/constitution_baseline.json` | Regenerated: **43 → 42 acknowledged findings** (+ 2 country findings, unchanged) |
| Master docs (`MASTER_ARCHITECTURE_v2`, `SHARED_CORE_REGISTRY`, `MASTER_REMAINING_WORK`, `ARCHITECTURE_CERTIFICATION`) | Regenerated via `scripts/architecture/docs.py` + `scripts/architecture.py report` |
| `docs/baselines/ARCHITECTURAL_MIGRATION_CLASSIFICATION.md` | #22 row marked **DONE — Commit 1.11**; §9 evidence note + §10 Next Action updated |
| `PROGRAM-01_DASHBOARD.md` | Metrics M1/M2/M3/M4/M5/M7/M8/M11 + identity row + Wave 1 status + commit log updated |

## 3. Dead-Code Evidence (ADR-028 Rule 2)

Objective evidence gathered before the moves:

**Finding #22 — `RiskBasedAuthService` / `risk_based_auth_service.py`:**
- **No production consumers**: `rg` repo-wide (`backend/app`, `backend/tests`,
  `scripts/`, `shared/`, `frontend-v3/`) shows references only inside the
  module itself and its own two test files. No `__init__.py` re-export exists
  in `services/__init__.py` (it re-exports other services, not this one).
- **No importers**: nobody imports `app.services.risk_based_auth_service` or
  `from app.services import RiskBasedAuthService`.
- **No dynamic imports**: no `importlib` target references the module.
- **No frontend consumers**: zero references in `.ts`/`.tsx`.
- **Superseded**: maps to canonical `identity/adaptive_auth` (live, with active
  consumers — orphan check PASS, see §4).
- **Dead**: never instantiated outside its own tests.

All moved files satisfy Rule 2: **unused** and **superseded**.

## 4. Canonical-Provider Orphan Check (mandatory after every migration)

Requirement: no canonical provider may become orphaned after a migration; each
must keep ≥ 1 active consumer or carry an explicit architectural justification.

Canonical provider affected: **`identity` → `backend/app/identity` (NIAM), in
particular `identity/adaptive_auth`**.

The archived module did not consume its canonical provider (it was a standalone
reimplementation), so **no canonical consumer was removed**:
- `identity/adaptive_auth` consumers unchanged (live).

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
| Import integrity | `app.services` imports clean | `app.services` imports clean (no re-export was removed) | ✅ unchanged |

The moved files were dead: no runtime path could observe a behavior
difference. The import chain was re-verified under the repo's standard test
environment.

## 6. Verification Cycle (ADR-028 Rule 7 / Framework §2)

| Gate | Result |
|---|---|
| Architecture gate `scripts/architecture.py check` | **PASS** — 42 findings (42 acknowledged, **0 new**), domain 11/11 isolation PASS, country-agnostic PASS, policy engine PASS |
| `scripts/architecture.py baseline` | baseline written: **42 findings, 2 country findings** |
| Ruff on changed scope (`risk_based_auth_service.py`, `services/__init__.py`) | 0 violations |
| App boot smoke test | app boots OK, **119 routes** (unchanged) |
| AST parse of touched files | OK |
| `git mv` rename detection | **100% similarity** (0 insertions / 0 deletions) on all three moves |
| Removed-symbol test scan | zero tests import `RiskBasedAuthService`/`risk_based_auth_service` (pre/post verified) |
| Database compatibility | no migration, no DDL; chain intact |
| Permissions | no permission touched; authorization gates PASS |
| Frontend compatibility | zero frontend changes (tsc/eslint/vitest/build green on baseline) |

## 7. Baseline Reduction

```
Shared Core acknowledged findings:  43 → 42   (−1)
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

- All three archived files are preserved byte-for-byte at
  `archive/platform-shared-core/` (git mv, 100% rename similarity) and are
  excluded from the architecture scan roots (`backend/app`, `shared`) by
  location.
- Scope was intentionally minimal and strictly tied to finding #22 plus its
  own tests. No `__init__.py` change was required (no re-export existed).
- Commit 1.11 also carried a concurrent author's pre-existing dirty files
  (`.ai/core/architect/state/**`, `.ai/core/optimizer/state/**`,
  `.ai/core/orchestrator/**`, `ARCHITECT_IMPLEMENTATION_REPORT.md`,
  `MISSION_STATUS.md`, `OPTIMIZER_IMPLEMENTATION_REPORT.md`,
  `PROGRAM-01_DASHBOARD.md` 3-line commit-log edit). The migration scope of
  this report is the risk-based-auth archive; the concurrent state refresh was
  left as committed by its author.
- Commit 1.11 scope (1 finding). Next: Wave 1 order 9 — #27 `EmergencyQRService`
  + #28 `Persisted*` twins (dead) archive.
