# Commit 1.9 Verification Report

**Commit:** `33e1a22f` — `refactor(integration): archive dead ESB message bus and API auth modules (ADR-028)`
**Branch:** `remediate-security-001`
**Date:** 2026-08-07
**Framework:** PROGRAM-01 Execution Framework (13-stage lifecycle, §2 matrix, §3 exit criteria)

This is the permanent verification record for **Commit 1.9**, the ninth
commit of the **structural migration phase** governed by ADR-028
(`docs/constitution/33_STRUCTURAL_MIGRATION_CONSTITUTION.md`) and executed
under the **PROGRAM-01 Execution Framework** (`PROGRAM-01_EXECUTION_FRAMEWORK.md`).
It migrates two acknowledged findings — **#17** (`events` Shared Core
capability: `integration/esb/message_bus.py`) and **#42** (`authorization`
capability: `integration/api_management/auth.py`) — by archiving them (with a
third dead module, `api_management/gateway.py`, which is the only consumer of
#42 and must move in the same commit to preserve package importability).

Commit 1.8 (`94cb3279`) archived the dead national `SecurityAuditService`
(46 → 44 after this commit). This is Wave 1 order 6 (46 → 44).

---

## 0. Migration Impact Report (ADR-028 Rule 4)

### Files moved (3)

| From | To | Evidence |
|---|---|---|
| `backend/app/integration/esb/message_bus.py` (111 LOC: `ESBMessageBus` async bus with DLQ/priority/idempotency) | `archive/platform-shared-core/esb_message_bus.py` | Zero live consumers repo-wide; sole references were `esb/__init__.py` + `integration/__init__.py` re-exports (removed with the moves). Superseded by canonical `shared/events` |
| `backend/app/integration/api_management/auth.py` (76 LOC: `APIAuth` in-memory API-key + HMAC auth) | `archive/platform-shared-core/api_management_auth.py` | Zero live consumers; dead reimplementation of `identity/services/authorization_service.py` + `shared/rbac`. Sole consumer was `gateway.py` (also dead, moved below) |
| `backend/app/integration/api_management/gateway.py` (109 LOC: `APIGateway`, `GatewayRoute`) | `archive/platform-shared-core/api_management_gateway.py` | The **only consumer of `APIAuth`**; itself dead (never instantiated — no live caller, no test). Moved in the same commit so `api_management` remains import-clean (behavior preservation, ADR-028 Rule 1) |

All three `git mv` renames were **detected at 100% similarity (0 insertions /
0 deletions)** → **a single `git revert 33e1a22f` restores the previous state**
(ADR-028 Rule 6).

### Files removed

None. All three modules were *moved*, not deleted (ADR-028 Rule 5); they
survive byte-for-byte at `archive/platform-shared-core/`.

### Files replaced

None. Canonical providers (`shared/events`, `identity/services/authorization_service.py`,
`shared/rbac`) were not modified.

### Duplicate code eliminated

Two Shared Core duplicates removed from the active tree:
- `ESBMessageBus` — reimplementation of the `events` capability (canonical `shared/events`, sync pub/sub)
- `APIAuth` — reimplementation of the `authorization` capability (canonical `identity/services/authorization_service.py` + `shared/rbac`)
- Plus `APIGateway` — dead duplicate of the integration-gateway concept (the live
  `integration/gateway.py` `GatewayRegistry`/`MessageGateway` is a *different* module,
  untouched).

### LOC reduction

| File | Lines |
|---|---|
| `esb/message_bus.py` (whole module) | 111 |
| `api_management/auth.py` (whole module) | 76 |
| `api_management/gateway.py` (whole module) | 109 |
| `esb/__init__.py` (1 import + 1 `__all__` entry) | 2 |
| `api_management/__init__.py` (2 imports + 2 `__all__` entries) | 4 |
| `integration/__init__.py` (2 imports in api_management block + 1 import in esb block + 3 `__all__` entries) | 6 |
| **Total removed from active tree** | **308** |
| Archived (preserved, non-active) | +296 |

### Dependency changes

- `integration/esb/` no longer imports `message_bus`; its remaining modules
  (`dead_letter`, `idempotency`, `priority`, `router`, `types`) do not depend
  on `message_bus` (verified: none import it).
- `integration/api_management/` no longer imports `auth`/`gateway`;
  `portal.py` (dormant, kept) depends only on `catalog.py` (live, kept).
- Top-level `app.integration` package still imports cleanly.

### API impact

**None.** OpenAPI schema is **unchanged** — no route, model, or permission
touched. The **`/integration/catalog` route is preserved and live**:
`integration/routes.py:142` lazily imports `APICatalog` from
`api_management` — that symbol still resolves (catalog.py kept). Boot
verified: **119 routes**.

### Frontend impact

**None.** Zero frontend files changed.

### Rollback procedure

```
git revert 33e1a22f
```

Single revert restores all three modules in place (git mv fully reversible)
and restores the `__init__.py` re-exports. No database migration, no data
change.

---

## 1. Migration Metrics (permanent section)

### Tech debt reduction

| Metric | Commit 1.8 | Commit 1.9 | Δ |
|---|---|---|---|
| Shared Core findings (acknowledged) | 46 | **44** | −2 |
| Duplicate Shared Core implementations (active tree) | audit dup (national) removed | **events dup (ESB) + authorization dup (API auth) removed** | −2 |
| Archived modules count (`archive/platform-shared-core/`) | 8 | **11** | +3 |
| LOC removed from active tree | 600 | **+308 = 908** | −308 |

### Shared Core consolidation progress

- Canonical `events` provider (`shared/events`) keeps its live consumers
  (unchanged by this commit — `message_bus.py` did not consume it).
- Canonical `authorization` providers (`identity/services/authorization_service.py`,
  `shared/rbac`) keep their live consumers (unchanged — `auth.py` did not
  consume them).
- 44 of the original 57 acknowledged findings remain; every migration removes
  a duplicate, never adds one.

### Architecture health trend

| Gate | Commit 1.8 | Commit 1.9 |
|---|---|---|
| Architecture constitution | PASS (46 ack, 0 new) | **PASS (44 ack, 0 new)** |
| Domain certification | 11/11 | **11/11** |
| Country-agnostic | PASS | **PASS** |
| Policy engine | PASS | **PASS** |

Findings trend is monotonically decreasing (57 → 44); new findings remain 0
(baseline-gated).

### Repository size trend

Active-tree LOC decreases (600 → 908 removed cumulative); the archive grows by
296 lines of preserved-but-dead code. Active production code strictly shrinks.

### Active vs Archived modules

| State | Count | Location |
|---|---|---|
| Active (production) | unchanged | `backend/app/**` |
| Archived (dead, preserved) | 11 | `archive/platform-shared-core/` |

### Production readiness trend

All quality gates stable across Commit 1.8 → 1.9: backend tests pass (0 fail),
architecture gate PASS, validate fast PASS, ruff baseline unchanged. No
regressions introduced.

---

## 2. What Changed

| File | Change |
|---|---|
| `backend/app/integration/esb/message_bus.py` → `archive/platform-shared-core/esb_message_bus.py` | **Moved** (`git mv`, rename detected 100%) — finding #17, whole dead module |
| `backend/app/integration/api_management/auth.py` → `archive/platform-shared-core/api_management_auth.py` | **Moved** (`git mv`, rename detected 100%) — finding #42, whole dead module |
| `backend/app/integration/api_management/gateway.py` → `archive/platform-shared-core/api_management_gateway.py` | **Moved** (`git mv`, rename detected 100%) — dead consumer of #42, moved to keep package import-clean |
| `backend/app/integration/esb/__init__.py` | Removed `ESBMessageBus` import + `__all__` entry; `DeadLetterService`/`ESBRouter`/`IdempotencyService`/`PriorityService` untouched |
| `backend/app/integration/api_management/__init__.py` | Removed `APIAuth`/`APIGateway` imports + `__all__` entries; `APICatalog`/`APIPortal` untouched |
| `backend/app/integration/__init__.py` | Removed `APIAuth`, `APIGateway` (api_management block) + `ESBMessageBus` (esb block) imports and their `__all__` entries |
| `.ai/core/architecture/constitution_baseline.json` | Regenerated: **46 → 44 acknowledged findings** (+ 2 country findings, unchanged) |
| Master docs (`MASTER_ARCHITECTURE_v2`, `SHARED_CORE_REGISTRY`, `MASTER_REMAINING_WORK`, `ARCHITECTURE_CERTIFICATION`) | Regenerated via `scripts/architecture/docs.py` + `scripts/architecture.py report` |
| `docs/baselines/ARCHITECTURAL_MIGRATION_CLASSIFICATION.md` | #17/#42 rows marked **DONE — Commit 1.9**; §9 evidence note + §10 Next Action updated; Wave commit numbering shifted (1.9→1.10→…) |
| `PROGRAM-01_DASHBOARD.md` | Metrics M1/M2/M3/M4/M5/M7/M8/M10/M11 + events/authorization rows + Wave 1 status + commit log updated |
| `docs/brain/PROJECT_BRAIN.md` + `docs/brain/brain_index.json` | Regenerated via `scripts/project_brain.py --json` |

## 3. Dead-Code Evidence (ADR-028 Rule 2)

Objective evidence gathered before the moves:

**Finding #17 — `ESBMessageBus` / `message_bus.py`:**
- **No production consumers**: `rg` repo-wide shows references only inside the
  `esb` package itself and the two package `__init__.py` re-exports (removed).
- **No importers**: nobody imports `app.integration.esb.message_bus` or
  `from app.integration import ESBMessageBus` outside the `__init__` files.
- **No tests**: zero hits in `backend/tests/` or `backend/app/**/tests/`.
- **No dynamic imports**: no `importlib` target references the module.
- **No frontend consumers**: zero references in `.ts`/`.tsx`.
- **Superseded**: maps to canonical `shared/events` (sync pub/sub).

**Finding #42 — `APIAuth` / `auth.py`:**
- **No production consumers**: only `api_management/__init__.py` (re-export),
  `integration/__init__.py` (re-export), and `gateway.py` (its sole live-code
  consumer, itself dead — see below).
- **No tests, no dynamic imports, no frontend consumers**.
- **Superseded**: maps to `identity/services/authorization_service.py` +
  `shared/rbac` (person-RBAC; the machine-API-key mechanism was never wired).

**`gateway.py` / `APIGateway` (moved as dependency of #42):**
- **Dead**: `APIGateway`/`GatewayRoute` referenced only by the two `__init__.py`
  re-exports and gateway.py itself; never instantiated anywhere; zero tests.
- The live gateway subsystem is the *different* module
  `integration/gateway.py` (`GatewayRegistry`/`MessageGateway`), which is
  referenced by `integration/routes.py` and was **not touched**.

**Live code protected (verified before commit):**
- `api_management/catalog.py` (`APICatalog`) is LIVE via the
  `/integration/catalog` route (`integration/routes.py:142` lazy import
  calling `.list_services()`/`.count()`) — **kept**.
- `api_management/portal.py` (`APIPortal`) is dormant but not a finding —
  **kept** (never remove dormant modules; GULA Constitution).
- The remaining `esb/` modules (`dead_letter`, `idempotency`, `priority`,
  `router`, `types`) are not findings — **kept**.

All moved modules satisfy Rule 2: **unused**, **superseded**, and (for #17/#42)
**duplicated**.

## 4. Canonical-Provider Orphan Check (mandatory after every migration)

Requirement: no canonical provider may become orphaned after a migration; each
must keep ≥ 1 active consumer or carry an explicit architectural justification.

Canonical providers affected: **`events` → `shared/events`** and
**`authorization` → `identity/services/authorization_service.py` + `shared/rbac`**.

Neither migrated module consumed its canonical provider (both were standalone
reimplementations), so **no canonical consumer was removed**:
- `shared/events` consumers unchanged.
- `identity/services/authorization_service.py` consumers unchanged (live).

**Verdict: PASS.**

## 5. Behavior Preservation Verification (ADR-028 Rule 1)

| Concern | Before | After | Verdict |
|---|---|---|---|
| Runtime behavior | app boots, tests pass | app boots (**119 routes**), tests pass | ✅ unchanged |
| API behavior | no route touched | **no route touched** (`/integration/catalog` still live via `APICatalog`) | ✅ unchanged |
| Business rules | — | no rule touched | ✅ |
| Security/authorization | gates PASS | gates PASS | ✅ |
| Audit behavior | — | no audit path touched | ✅ |
| Database behavior | no migration, no DDL | **no DB change** | ✅ |
| Import integrity | `app.integration` imports clean | `app.integration` (and all submodules) import clean | ✅ unchanged |

The moved modules were dead: no runtime path could observe a behavior
difference. The import chain was re-verified: `app.integration`,
`app.integration.esb`, `app.integration.api_management` all import OK under the
repo's standard test environment (the `shared` root is on `PYTHONPATH`).

## 6. Verification Cycle (ADR-028 Rule 7 / Framework §2)

| Gate | Result |
|---|---|
| Architecture gate `scripts/architecture.py check` | **PASS** — 44 findings (44 acknowledged, **0 new**), domain 11/11 isolation PASS, country-agnostic PASS, policy engine PASS |
| `scripts/architecture.py baseline` | baseline written: **44 findings, 2 country findings** |
| Governance tests `pytest test_architecture_constitution.py test_domain_platform.py test_governance_scripts.py -q` | **111 passed, 0 failed** |
| Route/governance integration tests `pytest test_governance.py test_routes_labs.py -q` | **124 passed, 0 failed** (route-level, exercise `app.integration` wiring) |
| Ruff `ruff check integration/__init__.py integration/esb/__init__.py integration/api_management/__init__.py` | 0 violations |
| Enterprise validation `scripts/enterprise_validation_engine.py --scope fast` | **VERDICT: PASS** — ruff 379 (baseline 379), tsc 0, eslint 0, brain fresh, 56 migrations |
| App boot smoke test | app boots OK, **119 routes** (unchanged) |
| AST parse of touched files | OK (all three `__init__.py`) |
| `git mv` rename detection | **100% similarity** (0 insertions / 0 deletions) on all three moves |
| Removed-symbol test scan | zero tests import `ESBMessageBus`/`APIAuth`/`APIGateway`/`api_management`/`integration/esb` |

## 7. Baseline Reduction

```
Shared Core acknowledged findings:  46 → 44   (−2)
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

- All three archived modules are preserved byte-for-byte at
  `archive/platform-shared-core/` (git mv, 100% rename similarity) and are
  excluded from the architecture scan roots (`backend/app`, `shared`) by
  location.
- Scope was intentionally minimal and strictly tied to findings #17/#42 plus
  the mandatory `gateway.py` dependency. The **live** `/integration/catalog`
  route and its `APICatalog` provider, the dormant `APIPortal`, and the
  remaining `esb/` supporting modules were all left untouched.
- Commit 1.9 scope (2 findings). Next: Wave 1 order 7 — #20 national
  `identity_service` (dead route) archive (classification precedent).
- A concurrent author's uncommitted files (`.ai/core/architect/state/**`,
  `.ai/core/optimizer/state/**`, `.ai/core/orchestrator/**`,
  `ARCHITECT_IMPLEMENTATION_REPORT.md`, `MISSION_STATUS.md`,
  `OPTIMIZER_IMPLEMENTATION_REPORT.md`) are outside this commit's scope and
  were left untouched.
