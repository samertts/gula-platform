# Commit 1.1 Verification Report

**Commit:** `4b115f32` — `refactor(platform): archive dead Shared Core reimplementation facades (ADR-028)`
**Branch:** `remediate-security-001`
**Date:** 2026-08-07

This is the permanent verification record for **Commit 1.1**, the first commit
of the **structural migration phase** governed by ADR-028
(`docs/constitution/33_STRUCTURAL_MIGRATION_CONSTITUTION.md`). It migrates the
first tranche of acknowledged Shared Core reimplementation findings
(`.ai/core/architecture/constitution_baseline.json`) to canonical providers by
archiving four provably-dead facade modules in `backend/app/platform/`.

---

## 0. Migration Impact Report (ADR-028 Rule 4)

### Files moved (4)

| From | To | Evidence |
|---|---|---|
| `backend/app/platform/caching.py` | `archive/platform-shared-core/caching.py` | Zero importers repo-wide; superseded by canonical `shared/cache/backends.py` (Shared Core `cache`) |
| `backend/app/platform/audit.py` | `archive/platform-shared-core/audit.py` | Zero importers repo-wide; superseded by canonical `backend/app/services/audit_service.py` (Shared Core `audit`) |
| `backend/app/platform/identity.py` | `archive/platform-shared-core/identity.py` | Zero importers repo-wide; superseded by canonical `backend/app/identity` (Shared Core `identity`) |
| `backend/app/platform/search.py` | `archive/platform-shared-core/search.py` | Zero importers repo-wide; superseded by canonical `backend/app/capabilities/search_service` (Shared Core `search_engine`) |

`git mv` preserves full history → **a single `git revert` of this commit
restores the previous state** (ADR-028 Rule 6).

### Files removed

None. All four modules were *moved*, not deleted (ADR-028 Rule 5).

### Files replaced

None.

### Duplicate code eliminated

Four Shared Core reimplementation facades removed from the active tree. These
modules duplicated capabilities that already have exactly one canonical
provider in `SHARED_CORE_CATALOG`:

- `cache` → `shared/cache/backends.py`
- `audit` → `backend/app/services/audit_service.py`
- `identity` → `backend/app/identity`
- `search_engine` → `backend/app/capabilities/search_service`

### LOC reduction

| File | Lines |
|---|---|
| `platform/caching.py` | 44 |
| `platform/audit.py` | 118 |
| `platform/identity.py` | 76 |
| `platform/search.py` | 75 |
| **Total moved out of active tree** | **313** |

### Dependency changes

None. The four modules imported only canonical/internal packages
(`app.core.cache_manager`, `app.services.audit_service`, `app.security.auth`,
`app.models.audit_log`, `app.national.*`); none of those dependencies changed,
and no package gained/lost dependencies.

### API impact

**None.** OpenAPI schema is **byte-identical** before/after (`cmp` clean,
1696 paths). The `/platform/health` and `/platform/modules` endpoints read
`PlatformRegistry`; the archived modules registered into it only at import
time, and no code imported them, so their capabilities were never present and
their removal changes no response payload.

### Frontend impact

**None.** Zero frontend files changed. `tsc` (0 errors), `eslint` (0 errors,
1 pre-existing warning in `public/sw.js`), `vitest` (122/122), `vite build`
all pass. No frontend consumer references any archived module.

### Rollback procedure

```
git revert <commit-hash>
```

Single revert restores all four files in place (git mv is fully reversible).
No database migration, no data change, no service restart dependency beyond a
normal deploy.

---

## 1. What Changed

| File | Change |
|---|---|
| `backend/app/platform/caching.py` → `archive/platform-shared-core/caching.py` | Moved (dead Shared Core `cache` reimplementation facade) |
| `backend/app/platform/audit.py` → `archive/platform-shared-core/audit.py` | Moved (dead Shared Core `audit` reimplementation facade) |
| `backend/app/platform/identity.py` → `archive/platform-shared-core/identity.py` | Moved (dead Shared Core `identity` reimplementation facade) |
| `backend/app/platform/search.py` → `archive/platform-shared-core/search.py` | Moved (dead Shared Core `search_engine` reimplementation facade) |
| `.ai/core/architecture/constitution_baseline.json` | Regenerated: **57 → 53 acknowledged findings** (+ 2 country findings, unchanged) |
| `docs/adr/ADR-028-structural-migration.md` | New: structural migration rules (7 rules) |
| `docs/constitution/33_STRUCTURAL_MIGRATION_CONSTITUTION.md` | New: migration constitution (R1–R7 + verification cycle) |
| `AGENTS.md` | New: PROGRAM-MIGRATION-001 section referencing ADR-028 |

## 2. Dead-Code Evidence (ADR-028 Rule 2)

Objective evidence gathered repo-wide before the move:

- **`grep` across `backend/`, `shared/`, `scripts/`, `frontend-v3/`**: zero
  references to `app.platform.caching`, `app.platform.audit`,
  `app.platform.identity`, `app.platform.search`, `PlatformCacheService`,
  `PlatformSearchService` outside the modules themselves.
- **No dynamic imports**: `importlib.import_module` occurrences target
  engineering/connector modules only; none reference `app.platform.*`.
- **No test imports**: `backend/tests`, `backend/tests_unit` have no reference.
- **No frontend consumers**: zero references in `.ts`/`.tsx`.
- **Not part of the app import graph**: `app.platform.__init__` does not import
  submodules; only `app.platform.{notifications,documents,i18n,sync,routes}`
  are imported anywhere, and all four archived modules are excluded.
- **Superseded**: each maps to exactly one canonical provider in
  `SHARED_CORE_CATALOG`.

These four modules are therefore: **unused**, **superseded**, and
**duplicated** — satisfying Rule 2 for archiving.

## 3. Behavior Preservation Verification (ADR-028 Rule 1)

| Concern | Before | After | Verdict |
|---|---|---|---|
| Runtime behavior | app boots, 4993 tests pass | app boots, **4993 tests pass, 0 fail** | ✅ unchanged |
| API behavior | 1696 OpenAPI paths | **byte-identical** OpenAPI | ✅ unchanged |
| Business rules | — | no rule touched | ✅ |
| Security/authorization | gates PASS | gates PASS | ✅ |
| Audit behavior | audit tests pass | audit tests pass | ✅ |
| Database behavior | no migration, no DDL | **no DB change** | ✅ |

`app.platform.routes` imports cleanly after the move (verified in-process:
`from app.platform.routes import router` → prefix `/platform`).

## 4. Verification Cycle (ADR-028 Rule 7)

| Gate | Result |
|---|---|
| Backend suite `pytest tests/ -q` | **4993 passed, 0 failed** (625.68 s) |
| Architecture gate `scripts/architecture.py check` | **PASS** — 53 findings (53 acknowledged, **0 new**), domain 11/11 isolation PASS, country-agnostic PASS, policy engine PASS |
| Domain gate `scripts/domains.py check` | PASS — isolation PASS, certification 11/11 |
| Kernel gate `scripts/kernel.py check` | ALL KERNEL CHECKS PASSED |
| Ruff `ruff check backend/app` | **379 violations (baseline 379)** — no new |
| OpenAPI byte-compat `cmp` | **BYTE-IDENTICAL** (1696 paths) |
| Frontend `tsc --noEmit` | 0 errors |
| Frontend `eslint .` | 0 errors (1 pre-existing warning in `public/sw.js`) |
| Frontend `vitest run` | **122 passed (9 files)** |
| Frontend `vite build` | built in 3.13 s |
| Policy/domain/architecture unit tests | **88 passed** |
| Enterprise validation `--scope fast` | **VERDICT: PASS** (ruff 379 baseline, tsc 0, eslint 0, brain fresh, migrations intact) |

## 5. Baseline Reduction

```
Shared Core acknowledged findings:  57 → 53   (−4)
Country-hardening findings:          2 →  2   (unchanged)
New findings:                         0
```

Regenerated via `scripts/architecture.py baseline` after the migration —
acknowledged debt only ever shrinks.

## 6. Notes

- The four modules remain preserved byte-for-byte in `archive/platform-shared-core/`
  for future reference; they are excluded from the architecture scan roots
  (`backend/app`, `shared`) by location.
- `platform/notifications.py`, `platform/documents.py`, `platform/i18n.py`,
  `platform/sync.py`, `platform/routes.py` are **live** (imported by
  `citizen_platform` / `integration.offline`) and were intentionally **not**
  touched.
- A concurrent author's uncommitted files (`.ai/core/architect/state/**`,
  `.ai/core/optimizer/state/benchmarks/runs.json`,
  `.ai/core/orchestrator/history/registry.json`, `ARCHITECT_IMPLEMENTATION_REPORT.md`,
  `MISSION_STATUS.md`, `OPTIMIZER_IMPLEMENTATION_REPORT.md`) are outside this
  commit's scope and were left untouched.
