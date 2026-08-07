# Commit 1.8 Verification Report

**Commit:** `94cb3279` — `refactor(national): archive dead security audit module (ADR-028)`
**Branch:** `remediate-security-001`
**Date:** 2026-08-07
**Framework:** PROGRAM-01 Execution Framework (13-stage lifecycle, §2 matrix, §3 exit criteria)

This is the permanent verification record for **Commit 1.8**, the eighth
commit of the **structural migration phase** governed by ADR-028
(`docs/constitution/33_STRUCTURAL_MIGRATION_CONSTITUTION.md`) and executed
under the **PROGRAM-01 Execution Framework** (`PROGRAM-01_EXECUTION_FRAMEWORK.md`).
It migrates acknowledged finding **#7** (`audit` Shared Core capability) by
archiving the provably-dead `backend/app/national/security/audit.py` module
(`SecurityAuditEvent` + `SecurityAuditService`).

Commit 1.1 (`4b115f32`) archived four `platform/` facades (57 → 53). Commit
1.2 (`576ade1d`) archived `identity/events.py` (53 → 52). Commit 1.3
(`b393aac3`) promoted the live workflow engine (52 → 51). Commits 1.4
(`7ec3536c`) / 1.5 (`2ceb373c`) removed two false positives (51 → 49). Commit
1.6 (`bf52a744`) archived `EncryptedSyncStore` (49 → 48). Commit 1.7
(`6c35ead6`) archived doc-intel `AuditLogger` (48 → 47). Commit 1.8 is Wave 1
order 5 (47 → 46).

---

## 0. Migration Impact Report (ADR-028 Rule 4)

### Files moved (1)

| From | To | Evidence |
|---|---|---|
| `backend/app/national/security/audit.py` (75 LOC: `SecurityAuditEvent` dataclass + `SecurityAuditService` in-memory hash-chained service) | `archive/platform-shared-core/national_security_audit.py` | Zero production importers repo-wide; superseded by canonical `identity/services/audit_service.py` (Shared Core `audit`) |

`git mv` preserves full history — **rename detected at 100% similarity,
0 insertions / 0 deletions** → **a single `git revert` of this commit restores
the previous state** (ADR-028 Rule 6).

### Files removed

None. The module was *moved*, not deleted (ADR-028 Rule 5). It survives
byte-for-byte (75 LOC confirmed) at `archive/platform-shared-core/`.

### Files replaced

None. The canonical `identity/services/audit_service.py` provider was not
modified.

### Duplicate code eliminated

`national/security/audit.py` was a reimplementation of the `audit` Shared Core
capability (signal `class\s+\w*(?:AuditService|AuditLogger|AuditLogRepository)\b`,
matched class `SecurityAuditService`). The canonical provider is
`backend/app/identity/services/audit_service.py` (immutable hash-chained
`AuditService`). This commit removes one duplicate `audit` implementation from
the active tree.

### LOC reduction

| File | Lines |
|---|---|
| `national/security/audit.py` (whole module) | 75 |
| `national/security/__init__.py` (2 imports + 2 `__all__` entries) | 4 |
| **Total removed from active tree** | **79** |
| Archived (preserved, non-active) | +75 |

### Dependency changes

None. The archived module imported only `dataclasses`, `datetime`, `typing`,
and `app._compat.UTC` (all stdlib/repo-core). No package gained or lost a
dependency. The `__init__.py` re-exports were removed (nothing imported them).

### API impact

**None.** OpenAPI schema is **unchanged** — no route, model, or permission was
touched. The module was never imported by a route or service; app boot
verified: 119 routes.

### Frontend impact

**None.** Zero frontend files changed. No frontend consumer references the
archived symbols.

### Rollback procedure

```
git revert 94cb3279
```

Single revert restores `national/security/audit.py` in place (git mv is fully
reversible) and restores the `__init__.py` re-exports. No database migration,
no data change, no service restart dependency beyond a normal deploy.

---

## 1. Migration Metrics (permanent section)

### Tech debt reduction

| Metric | Commit 1.7 | Commit 1.8 | Δ |
|---|---|---|---|
| Shared Core findings (acknowledged) | 47 | **46** | −1 |
| Duplicate Shared Core implementations (active tree) | audit duplicate (doc-intel) removed | **audit duplicate (national) removed** | −1 |
| Active production modules | unchanged | unchanged (module was dead) | 0 |
| Archived modules count (`archive/platform-shared-core/`) | 7 | **8** | +1 |
| LOC removed from active tree | 521 | **+79 = 600** | −79 |
| Estimated maintenance complexity reduction | — | 1 dead audit module (incl. broken `verify_chain`) no longer scanned | −1 subsystem |

### Shared Core consolidation progress

- Canonical `audit` provider (`identity/services/audit_service.py`) keeps its
  active consumers: `identity/services/account_service.py`,
  `identity/services/authentication_service.py`,
  `identity/adaptive_auth/services.py` — it is **not orphaned**.
- 46 of the original 57 acknowledged findings remain; every migration removes
  a duplicate, never adds one.

### Architecture health trend

| Gate | Commit 1.7 | Commit 1.8 |
|---|---|---|
| Architecture constitution | PASS (47 ack, 0 new) | **PASS (46 ack, 0 new)** |
| Domain certification | 11/11 | **11/11** |
| Country-agnostic | PASS | **PASS** |
| Policy engine | PASS | **PASS** |

Findings trend is monotonically decreasing (57 → 46); new findings remain 0
(baseline-gated).

### Repository size trend

Active-tree LOC decreases (521 → 600 removed cumulative); the archive grows by
75 lines of preserved-but-dead code. Net repository code is stable; active
production code strictly shrinks.

### Active vs Archived modules

| State | Count | Location |
|---|---|---|
| Active (production) | unchanged | `backend/app/**` |
| Archived (dead, preserved) | 8 | `archive/platform-shared-core/` |

### Production readiness trend

All quality gates stable across Commit 1.7 → 1.8: backend tests pass (0 fail),
architecture gate PASS, validate fast PASS, ruff baseline unchanged. No
regressions introduced.

---

## 2. What Changed

| File | Change |
|---|---|
| `backend/app/national/security/audit.py` → `archive/platform-shared-core/national_security_audit.py` | **Moved** (`git mv`, rename detected 100%) — whole dead module |
| `backend/app/national/security/__init__.py` | Removed `SecurityAuditEvent`/`SecurityAuditService` from the `from .audit import (...)` line and from `__all__`; all other security exports untouched |
| `scripts/architecture/docs.py` | Narrative §"High-priority migrations" updated: `national/security/audit.py` now noted as archived (Commit 1.8) |
| `.ai/core/architecture/constitution_baseline.json` | Regenerated: **47 → 46 acknowledged findings** (+ 2 country findings, unchanged) |
| Master docs (`MASTER_ARCHITECTURE_v2`, `SHARED_CORE_REGISTRY`, `MASTER_REMAINING_WORK`, `ARCHITECTURE_CERTIFICATION`) | Regenerated via `scripts/architecture/docs.py` + `scripts/architecture.py report` |
| `docs/baselines/ARCHITECTURAL_MIGRATION_CLASSIFICATION.md` | Evidence note (§9) + Next Action (§10) for Commit 1.8 |
| `PROGRAM-01_DASHBOARD.md` | Metrics M1/M2/M3/M4/M5/M7/M8/M11 + audit row + commit log updated |
| `docs/brain/PROJECT_BRAIN.md` + `docs/brain/brain_index.json` | Regenerated via `scripts/project_brain.py --json` |

## 3. Dead-Code Evidence (ADR-028 Rule 2)

Objective evidence gathered before the move:

- **`grep` across `backend/`, `shared/`, `scripts/`, `frontend-v3/`**: the only
  references to `SecurityAuditService` / `SecurityAuditEvent` are within the
  module itself and the `national/security/__init__.py` re-export (removed
  with the move). The `scripts/architecture/docs.py` hit is narrative text
  (updated in this commit).
- **No production consumers**: no route, service, factory, or integration
  module imports these symbols (verified: package-level imports from
  `app.national.security` target `abac`, `rbac`, `break_glass`,
  `minimum_necessary`, `minor_protection`, `purpose_of_use`, `sensitive_records`
  — never `audit`).
- **No tests reference the module**: `grep` of `backend/tests/` and
  `backend/app/national/tests/` shows zero hits.
- **No dynamic imports**: no `importlib` target references the module.
- **No frontend consumers**: zero references in `.ts`/`.tsx`.
- **Superseded**: maps to exactly one canonical provider in
  `SHARED_CORE_CATALOG` (`audit` → `identity/services/audit_service.py`,
  immutable hash-chained `AuditService`).
- **Buggy implementation**: `SecurityAuditService.verify_chain` is logically
  broken (compares each event's hash against the *previous* hash value rather
  than recomputing it), confirming it was never exercised in production.

This module is therefore: **unused**, **superseded**, and **duplicated** —
satisfying Rule 2 for archiving.

## 4. Canonical-Provider Orphan Check (mandatory after every migration)

Requirement: no canonical provider may become orphaned after a migration;
each must keep ≥ 1 active consumer or carry an explicit architectural
justification.

Canonical provider affected by this migration: **`audit` →
`identity/services/audit_service.py`**.

Active production consumers **after** migration (unchanged by this commit):

- `backend/app/identity/services/account_service.py`
- `backend/app/identity/services/authentication_service.py`
- `backend/app/identity/adaptive_auth/services.py`

**Verdict: PASS.** The canonical audit provider keeps 3+ active consumers; it
is not orphaned. The archived module was itself the duplicate, not the provider.

## 5. Behavior Preservation Verification (ADR-028 Rule 1)

| Concern | Before | After | Verdict |
|---|---|---|---|
| Runtime behavior | app boots, tests pass | app boots (119 routes), tests pass | ✅ unchanged |
| API behavior | no route touched | **no route touched** | ✅ unchanged |
| Business rules | — | no rule touched | ✅ |
| Security/authorization | gates PASS | gates PASS | ✅ |
| Audit behavior | — | no audit path touched (canonical audit service unaffected) | ✅ |
| Database behavior | no migration, no DDL | **no DB change** | ✅ |

The removed module was dead and buggy: no runtime path could observe a
behavior difference. The `national/security` package (abac/rbac/break_glass/etc.)
was verified intact via its test suites.

## 6. Verification Cycle (ADR-028 Rule 7 / Framework §2)

| Gate | Result |
|---|---|
| Architecture gate `scripts/architecture.py check` | **PASS** — 46 findings (46 acknowledged, **0 new**), domain 11/11 isolation PASS, country-agnostic PASS, policy engine PASS |
| `scripts/architecture.py baseline` | baseline written: **46 findings, 2 country findings** |
| Governance tests `pytest test_architecture_constitution.py test_domain_platform.py test_governance_scripts.py -q` | **111 passed, 0 failed** |
| National security tests `pytest backend/app/national/tests/unit/test_security.py backend/app/national/tests/security/ -q` | **27 passed, 0 failed** (package integrity confirmed) |
| Ruff `ruff check national/security/__init__.py scripts/architecture/docs.py` | 0 violations |
| Enterprise validation `scripts/enterprise_validation_engine.py --scope fast` | **VERDICT: PASS** — ruff 379 (baseline 379), tsc 0, eslint 0, brain fresh, 56 migrations |
| App boot smoke test | app boots OK, **119 routes** (unchanged) |
| AST parse of touched files | OK (`__init__.py`, archive) |
| `git mv` rename detection | **100% similarity** (0 insertions / 0 deletions) |

## 7. Baseline Reduction

```
Shared Core acknowledged findings:  47 → 46   (−1)
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

- The archived module is preserved byte-for-byte at
  `archive/platform-shared-core/national_security_audit.py` (git mv, 100%
  rename similarity) and is excluded from the architecture scan roots
  (`backend/app`, `shared`) by location.
- The rest of `national/security/` (abac, rbac, break_glass, emergency_access,
  consent_enforcement, etc.) is untouched and its tests pass — scope was
  strictly limited to finding #7.
- Commit 1.8 scope is intentionally minimal (1 finding). Next: Wave 1 order 6 —
  #17 ESB `message_bus` + #42 `APIAuth.check_permission` delete (dead,
  evidence-based, Commit 1.1/1.2 precedent for direct deletion of dead code).
- A concurrent author's uncommitted files (`.ai/core/architect/state/**`,
  `.ai/core/optimizer/state/benchmarks/runs.json`,
  `.ai/core/orchestrator/history/registry.json`, `ARCHITECT_IMPLEMENTATION_REPORT.md`,
  `MISSION_STATUS.md`, `OPTIMIZER_IMPLEMENTATION_REPORT.md`) are outside this
  commit's scope and were left untouched.
