# Commit 1.12 Verification Report

**Commit:** *(pending hash)* — `refactor(national): archive dead EmergencyQR service twins (ADR-028)`
**Branch:** `remediate-security-001`
**Date:** 2026-08-07
**Framework:** PROGRAM-01 Execution Framework (13-stage lifecycle, §2 matrix, §3 exit criteria)

This is the permanent verification record for **Commit 1.12**, the twelfth
commit of the **structural migration phase** governed by ADR-028
(`docs/constitution/33_STRUCTURAL_MIGRATION_CONSTITUTION.md`) and executed
under the **PROGRAM-01 Execution Framework** (`PROGRAM-01_EXECUTION_FRAMEWORK.md`).
It migrates two acknowledged findings of the **`qr_engine`** Shared Core
capability: **#27** (`citizen_platform/identity.py::EmergencyQRService`) and
**#28** (`governance/services/citizen_platform_persistence.py::PersistedEmergencyQRService`).

Commit 1.11 (`63d2f2bf`) archived the dead risk-based-auth service (43 → 42).
This is **Wave 1 order 9** (42 → 40).

---

## 0. Migration Impact Report (ADR-028 Rule 4)

### Files moved (0) / extracted (2)

No whole files moved — this migration **extracts two dead classes** from live
modules (Commit 1.7 `AuditLogger` precedent), preserving the surrounding
non-finding code in place.

| Extracted (archived) | Source (edited) | Evidence |
|---|---|---|
| `EmergencyQR` dataclass + `EmergencyQRService` (in-memory token scheme) → `archive/platform-shared-core/citizen_platform_emergency_qr.py` | `backend/app/citizen_platform/identity.py` | The module's only externally-imported symbol is `HealthIdentityService` (finding #19, Retain — imported by `citizen_platform/sdk.py:17` and `citizen_platform/integration.py:22`). `EmergencyQRService`/`EmergencyQR` had zero consumers repo-wide |
| `PersistedEmergencyQRService` (DB twin) → `archive/platform-shared-core/citizen_platform_persisted_emergency_qr.py` | `backend/app/governance/services/citizen_platform_persistence.py` | Dead twin of the dead in-memory class; zero importers of the whole module, zero consumers of the class |

Both archived classes were preserved **byte-for-byte** (their class bodies are
unchanged; only the module docstring/header was added for provenance). A
**single `git revert`** of the implementation commit restores the classes in
place (the removal is a small deletion, trivially reversible).

### Files removed

None. Both classes survive byte-for-byte at `archive/platform-shared-core/`
(ADR-028 Rule 5).

### Files replaced

None. Canonical provider `shared/qr` was not modified.

### Duplicate code eliminated

Two Shared Core duplicates removed from the active tree:
- `EmergencyQRService` — in-memory token-based reimplementation of the `qr_engine`
  capability (canonical `shared/qr`, real image generation).
- `PersistedEmergencyQRService` — DB-persisted twin of the above.

### LOC reduction

| File | Lines |
|---|---|
| `citizen_platform/identity.py` — `EmergencyQR` + `EmergencyQRService` + now-unused `hmac` import | −56 |
| `governance/services/citizen_platform_persistence.py` — `PersistedEmergencyQRService` + now-unused imports (`hmac`, `QRCodeRecord`, `QRCodeRepository`, `timedelta`) | −65 |
| **Total removed from active tree** | **−121** |

### Dependency changes

- `citizen_platform/identity.py` no longer imports `shared.security.hmac`
  (its only user was `EmergencyQRService`). `uuid`/`datetime`/`UTC`/`Any`
  remain (used by `IdentityRecoveryService`).
- `governance/services/citizen_platform_persistence.py` no longer imports
  `shared.security.hmac`, `QRCodeRecord`, `QRCodeRepository`, or `timedelta`
  (all used only by `PersistedEmergencyQRService`). The remaining classes
  (`PersistedIdentityRecoveryService`, `PersistedGuardianService`,
  `PersistedFamilyAccountService`) still import cleanly.
- The archive modules import `app.governance.models.citizen_platform`
  (`QRCodeRecord`) and `app.governance.repositories` (`QRCodeRepository`) —
  those modules remain in the active tree (not findings) and are preserved.

### API impact

**None.** OpenAPI schema is **unchanged** — no route, model, or permission
touched. Neither class was wired to a route. Boot verified: **119 routes**
(unchanged).

### Frontend impact

**None.** Zero frontend files changed.

### Rollback procedure

```
git revert <implementation-commit-hash>
```

Single revert restores both classes in place (small deletions, fully
reversible). No database migration, no data change.

---

## 1. Migration Metrics (permanent section)

### Tech debt reduction

| Metric | Commit 1.11 | Commit 1.12 | Δ |
|---|---|---|---|
| Shared Core findings (acknowledged) | 42 | **40** | −2 |
| Duplicate Shared Core implementations (active tree) | identity dup removed | **qr_engine dups ×2 removed** | −2 |
| Archived modules count (`archive/platform-shared-core/`) | 18 | **20** | +2 |
| LOC removed from active tree | 2151 | **+121 = 2272** | −121 |

### Shared Core consolidation progress

- Canonical `qr_engine` provider (`shared/qr`) keeps its live consumers
  (unchanged — the archived classes did not consume it).
- 40 of the original 57 acknowledged findings remain; every migration removes
  a duplicate, never adds one.

### Architecture health trend

| Gate | Commit 1.11 | Commit 1.12 |
|---|---|---|
| Architecture constitution | PASS (42 ack, 0 new) | **PASS (40 ack, 0 new)** |
| Domain certification | 11/11 | **11/11** |
| Country-agnostic | PASS | **PASS** |
| Policy engine | PASS | **PASS** |

Findings trend is monotonically decreasing (57 → 40); new findings remain 0
(baseline-gated).

### Repository size trend

Active-tree LOC decreases (2151 → 2272 removed cumulative); the archive grows
by 2 modules. Active production code strictly shrinks.

### Active vs Archived modules

| State | Count | Location |
|---|---|---|
| Active (production) | unchanged | `backend/app/**` |
| Archived (dead, preserved) | 20 files | `archive/platform-shared-core/` |

### Production readiness trend

All quality gates stable across Commit 1.11 → 1.12: backend tests pass (0
fail), architecture gate PASS, ruff baseline unchanged (379), boot 119 routes.
No regressions introduced.

---

## 2. What Changed

| File | Change |
|---|---|
| `backend/app/citizen_platform/identity.py` | Removed `EmergencyQR` dataclass + `EmergencyQRService` class (finding #27) + now-unused `from shared.security.hmac import hmac_sign, hmac_verify` import. `HealthIdentityService` (#19, Retain) + `IdentityRecoveryService` (dormant, not a finding) untouched |
| `backend/app/governance/services/citizen_platform_persistence.py` | Removed `PersistedEmergencyQRService` (finding #28) + now-unused imports (`hmac`, `QRCodeRecord`, `QRCodeRepository`, `timedelta`). `PersistedIdentityRecoveryService`/`PersistedGuardianService`/`PersistedFamilyAccountService` untouched |
| `archive/platform-shared-core/citizen_platform_emergency_qr.py` | **New** — `EmergencyQR` + `EmergencyQRService` preserved byte-for-byte (Commit 1.7 precedent) |
| `archive/platform-shared-core/citizen_platform_persisted_emergency_qr.py` | **New** — `PersistedEmergencyQRService` preserved byte-for-byte |
| `.ai/core/architecture/constitution_baseline.json` | Regenerated: **42 → 40 acknowledged findings** (+ 2 country findings, unchanged) |
| Master docs (`MASTER_ARCHITECTURE_v2`, `SHARED_CORE_REGISTRY`, `MASTER_REMAINING_WORK`, `ARCHITECTURE_CERTIFICATION`) | Regenerated via `scripts/architecture/docs.py` + `scripts/architecture.py report` |
| `docs/baselines/ARCHITECTURAL_MIGRATION_CLASSIFICATION.md` | #27/#28 rows marked **DONE — Commit 1.12**; §9 evidence note + §10 Next Action updated |
| `PROGRAM-01_DASHBOARD.md` | Metrics M1/M3/M4/M5/M7/M8/M11 + qr_engine row + Wave 1 status + commit log updated |

## 3. Dead-Code Evidence (ADR-028 Rule 2)

Objective evidence gathered before the extraction:

**Finding #27 — `EmergencyQRService` / `citizen_platform/identity.py`:**
- **No production consumers**: the module's only externally-imported symbol is
  `HealthIdentityService` (verified: `citizen_platform/sdk.py:17`,
  `citizen_platform/integration.py:22` both import only `HealthIdentityService`).
  `EmergencyQRService`/`EmergencyQR` appear nowhere else in `backend/app`,
  `backend/tests`, `scripts/`, `shared/`, or `frontend-v3/`.
- **No tests**: zero test references repo-wide.
- **No dynamic imports**, **no frontend consumers**.
- **Superseded**: maps to canonical `shared/qr` (real image generation; the
  in-memory token scheme was a different, never-wired mechanism).

**Finding #28 — `PersistedEmergencyQRService` / `citizen_platform_persistence.py`:**
- **No production consumers**: the whole module has zero importers
  (`rg citizen_platform_persistence` → no matches); the class appears nowhere
  else.
- **No tests, no dynamic imports, no frontend consumers**.
- **Dead twin**: DB-persisted counterpart of the dead in-memory class.

**Live code protected (verified before commit):**
- `HealthIdentityService` (#19, Retain as Domain-Owned) — live via
  `citizen_platform/sdk.py` + `integration.py` — **kept**.
- `IdentityRecoveryService` (dormant, not a finding) — **kept**.
- `PersistedIdentityRecoveryService`, `PersistedGuardianService`,
  `PersistedFamilyAccountService` (dormant domain code, not findings) — **kept**
  (never remove dormant modules; GULA Constitution).
- `app.governance.models.citizen_platform` + `citizen_platform_repositories`
  (QR model/repo backing tables) — **kept** in the active tree (not findings).

All extracted code satisfies Rule 2: **unused** and **superseded**.

## 4. Canonical-Provider Orphan Check (mandatory after every migration)

Requirement: no canonical provider may become orphaned after a migration; each
must keep ≥ 1 active consumer or carry an explicit architectural justification.

Canonical provider affected: **`qr_engine` → `shared/qr`**.

The archived classes did not consume their canonical provider (both were
standalone reimplementations), so **no canonical consumer was removed**:
- `shared/qr` consumers unchanged.

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
| Import integrity | `app.citizen_platform` + `app.governance.services` import clean | both import clean (verified: package import smoke PASS) | ✅ unchanged |

The extracted classes were dead: no runtime path could observe a behavior
difference.

## 6. Verification Cycle (ADR-028 Rule 7 / Framework §2)

| Gate | Result |
|---|---|
| Architecture gate `scripts/architecture.py check` | **PASS** — 40 findings (40 acknowledged, **0 new**), domain 11/11 isolation PASS, country-agnostic PASS, policy engine PASS |
| `scripts/architecture.py baseline` | baseline written: **40 findings, 2 country findings** |
| Ruff on changed scope (identity.py, persistence module, 2 archive files) | 0 violations (3 import-sort fixes applied) |
| App boot smoke test | app boots OK, **119 routes** (unchanged) |
| Package import smoke | `app.citizen_platform` (incl. sdk/integration), `app.governance.services.citizen_platform_persistence`, both archive modules import OK |
| AST parse of touched files | OK |
| Removed-symbol scan | zero references to `EmergencyQR`/`EmergencyQRService`/`PersistedEmergencyQRService` in the active tree |
| Database compatibility | no migration, no DDL; chain intact |
| Permissions | no permission touched; authorization gates PASS |
| Frontend compatibility | zero frontend changes (tsc/eslint/vitest/build green on baseline) |

## 7. Baseline Reduction

```
Shared Core acknowledged findings:  42 → 40   (−2)
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

- Both archived classes are preserved byte-for-byte at
  `archive/platform-shared-core/` with provenance docstrings and are excluded
  from the architecture scan roots (`backend/app`, `shared`) by location.
- Scope was intentionally minimal and strictly tied to findings #27/#28.
  Non-finding dormant code in both edited modules was left untouched
  (GULA Constitution: never remove dormant enterprise modules).
- Commit 1.12 scope (2 findings). Next: Wave 1 order 10 — #25
  `workflow_runtime/application/interfaces.py::WorkflowNotifier` (orphan ABC)
  archive.
