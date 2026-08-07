# Commit 1.6 Verification Report

**Commit:** `bf52a744` — `refactor(offline): archive dead EncryptedSyncStore reimplementation (ADR-028)`
**Branch:** `remediate-security-001`
**Date:** 2026-08-07

This is the permanent verification record for **Commit 1.6**, the sixth
commit of the **structural migration phase** governed by ADR-028
(`docs/constitution/33_STRUCTURAL_MIGRATION_CONSTITUTION.md`). It migrates the
next acknowledged Shared Core reimplementation finding
(`.ai/core/architecture/constitution_baseline.json`, #3) to the canonical
provider by archiving the provably-dead `EncryptedSyncStore` class from
`backend/app/services/offline_sync_service.py`.

Commit 1.1 (`4b115f32`) archived four dead `platform/` facades (57 → 53
findings). Commit 1.2 (`576ade1d`) archived `identity/events.py` (53 → 52).
Commit 1.3 (`b393aac3`) promoted the live identity/workflows engine to
canonical `app.workflows`. Commits 1.4 (`7ec3536c`) and 1.5 (`2ceb373c`)
removed two scanner false positives via signal-precision fixes (52 → 49).
Commit 1.6 continues the same evidence-based, archive-first,
one-commit-at-a-time discipline with the first dead-code archive of Wave 1.

---

## 0. Migration Impact Report (ADR-028 Rule 4)

### Files moved (1)

| From | To | Evidence |
|---|---|---|
| `backend/app/services/offline_sync_service.py` (class `EncryptedSyncStore`, lines 272–326) | `archive/platform-shared-core/encrypted_sync_store.py` (79 LOC, full class + standalone-execution imports) | Zero production importers repo-wide; superseded by canonical `shared/security/encryption.py` (Shared Core `encryption`) |

The class body is preserved byte-for-byte (verified by inspection) with the
imports required for standalone execution (hashlib/json/logging/zlib/Any +
lazy `cryptography.fernet` import) → **a single `git revert` of this commit
restores the previous state** (ADR-028 Rule 6).

### Files removed

None. The class was *moved*, not deleted (ADR-028 Rule 5). It survives
byte-for-byte at `archive/platform-shared-core/encrypted_sync_store.py`.

### Files replaced

None. No canonical provider was modified; `EncryptedSyncStore` was a
self-contained dead class whose in-memory store capability is not exercised
by any runtime path.

### Duplicate code eliminated

`EncryptedSyncStore` was a reimplementation of the `encryption` Shared Core
capability (signal `\bFernet\s*\(`, matched class `EncryptedSyncStore`). The
canonical provider is `shared/security/encryption.py` (`encrypt_value` /
`decrypt_value`, Fernet, live). This commit removes one duplicate `encryption`
implementation from the active tree.

### LOC reduction

| File | Lines |
|---|---|
| `offline_sync_service.py` (class + blank lines) | 55 |
| `test_offline_sync.py` (`TestEncryptedSyncStore`, 6 tests) | 43 |
| **Total removed from active tree** | **98** |
| Archived (preserved, non-active) | +79 |

### Dependency changes

None. `zlib` was removed from `offline_sync_service.py` imports (it was used
only by the archived class); `hashlib`/`json` remain (used by `OfflineSyncEngine`).
No package gained or lost a dependency.

### API impact

**None.** OpenAPI schema is **unchanged** — no route, model, or permission was
touched (the class had zero production consumers; it was not registered in any
router or imported by any active module).

### Frontend impact

**None.** Zero frontend files changed. No frontend consumer references
`EncryptedSyncStore`.

### Rollback procedure

```
git revert bf52a744
```

Single revert restores `EncryptedSyncStore` in `offline_sync_service.py`, its
`TestEncryptedSyncStore` tests, and the `zlib` import. No database migration,
no data change, no service restart dependency beyond a normal deploy.

---

## 1. Migration Metrics (permanent section, applies to every future commit)

### Tech debt reduction

| Metric | Commit 1.5 | Commit 1.6 | Δ |
|---|---|---|---|
| Shared Core findings (acknowledged) | 49 | **48** | −1 |
| Duplicate Shared Core implementations (active tree) | 3 (search/authentication false positives gone) | **encryption duplicate removed** | −1 |
| Active production modules | unchanged | unchanged (`EncryptedSyncStore` was dead) | 0 |
| Archived modules count (`archive/platform-shared-core/`) | 5 | **6** | +1 |
| LOC removed from active tree | 345 | **+98 = 443** | −98 |
| Estimated maintenance complexity reduction | — | 1 dead encryption class no longer scanned | −1 subsystem |

### Shared Core consolidation progress

- Canonical `encryption` provider (`shared/security/encryption.py`) keeps its
  live consumers (`shared/security/__init__.py`, national/services, etc.) —
  it is **not orphaned** by this migration; the archived class was the
  duplicate, not the provider.
- 48 of the original 57 acknowledged findings remain; every migration removes
  a duplicate, never adds one.

### Architecture health trend

| Gate | Commit 1.5 | Commit 1.6 |
|---|---|---|
| Architecture constitution | PASS (49 ack, 0 new) | **PASS (48 ack, 0 new)** |
| Domain certification | 11/11 | **11/11** |
| Country-agnostic | PASS | **PASS** |
| Policy engine | PASS | **PASS** |

Findings trend is monotonically decreasing (57 → 53 → 52 → 49 → 48); new
findings remain 0 (baseline-gated).

### Repository size trend

Active-tree LOC decreases (345 → 443 removed cumulative); the archive grows
by 79 lines of preserved-but-dead code. Net repository code is stable; active
production code strictly shrinks.

### Active vs Archived modules

| State | Count | Location |
|---|---|---|
| Active (production) | unchanged | `backend/app/**` |
| Archived (dead, preserved) | 6 | `archive/platform-shared-core/` |

### Production readiness trend

All quality gates stable across Commit 1.5 → 1.6: backend tests pass (0 fail),
architecture gate PASS, validate fast PASS, ruff baseline unchanged. No
regressions introduced.

---

## 2. What Changed

| File | Change |
|---|---|
| `backend/app/services/offline_sync_service.py` | Removed dead `EncryptedSyncStore` class (lines 272–326) + now-unused `import zlib`; `OfflineSyncEngine` untouched |
| `backend/tests/test_offline_sync.py` | Removed `EncryptedSyncStore` import + `TestEncryptedSyncStore` class (6 tests); `TestOfflineSyncEngine` suite intact |
| `archive/platform-shared-core/encrypted_sync_store.py` | **NEW** — archived class, byte-for-byte, with header docstring + standalone-execution imports |
| `.ai/core/architecture/constitution_baseline.json` | Regenerated: **49 → 48 acknowledged findings** (+ 2 country findings, unchanged) |
| Master docs (`MASTER_ARCHITECTURE_v2`, `SHARED_CORE_REGISTRY`, `MASTER_REMAINING_WORK`, `ARCHITECTURE_CERTIFICATION`, `DIGITAL_TRUST_PLATFORM`) | Regenerated via `scripts/architecture/docs.py` + `scripts/architecture.py report` |
| `docs/baselines/ARCHITECTURAL_MIGRATION_CLASSIFICATION.md` | Evidence note (§9) + Next Action (§10) for Commit 1.6 |
| `docs/brain/PROJECT_BRAIN.md` + `docs/brain/brain_index.json` | Regenerated via `scripts/project_brain.py --json` |

## 3. Dead-Code Evidence (ADR-028 Rule 2)

Objective evidence gathered before the move:

- **`grep` across `backend/`, `shared/`, `scripts/`, `frontend-v3/`**: the only
  reference to `EncryptedSyncStore` (outside its own definition) is
  `backend/tests/test_offline_sync.py` (import + `TestEncryptedSyncStore`).
- **No dynamic imports**: no `importlib` target references
  `services.offline_sync_service.EncryptedSyncStore`.
- **No frontend consumers**: zero references in `.ts`/`.tsx`.
- **Not part of any route graph**: `offline_sync_service` is not imported by
  `factory.py`, any route module, or the integration layer. The live offline
  path is `backend/app/integration/offline.py::OfflineSyncEngine` — a
  **different module/class** wired in `integration/routes.py` (lines 21, 36,
  262–284) and imported by `integration/__init__.py`. It was verified present
  and untouched.
- **Superseded**: maps to exactly one canonical provider in
  `SHARED_CORE_CATALOG` (`encryption` → `shared/security/encryption.py`,
  live Fernet `encrypt_value`/`decrypt_value`).

This class is therefore: **unused**, **superseded**, and **duplicated** —
satisfying Rule 2 for archiving.

## 4. Canonical-Provider Orphan Check (mandatory after every migration)

Requirement: no canonical provider may become orphaned after a migration;
each must keep ≥ 1 active consumer or carry an explicit architectural
justification.

Canonical provider affected by this migration: **`encryption` →
`shared/security/encryption.py`**.

Active production consumers **after** migration (unchanged by this commit):

- `shared/security/__init__.py` — re-exports the canonical functions.
- Consumers of `shared.security` / `app.security.encryption` wrappers across
  live services and routes (data-at-rest encryption paths).
- `backend/app/document_intelligence/security.py` and
  `backend/app/national/ecosystem/transformation/engine.py` still carry
  acknowledged findings (Fernet matches) — both remain live and are on the
  migration roadmap (Waves 3/5).

**Verdict: PASS.** The canonical `shared/security/encryption.py` provider
keeps active consumers; it is not orphaned. The archived `EncryptedSyncStore`
was itself the duplicate, not the provider.

## 5. Behavior Preservation Verification (ADR-028 Rule 1)

| Concern | Before | After | Verdict |
|---|---|---|---|
| Runtime behavior | app boots, tests pass | app boots, tests pass | ✅ unchanged |
| API behavior | no route touched | **no route touched** | ✅ unchanged |
| Business rules | — | no rule touched | ✅ |
| Security/authorization | gates PASS | gates PASS | ✅ |
| Audit behavior | — | no audit path touched | ✅ |
| Database behavior | no migration, no DDL | **no DB change** | ✅ |

The removed class was dead: no runtime path could observe a behavior
difference. Its 6 tests were removed together with the class; the archived
copy preserves the class body byte-for-byte for reversal.

## 6. Verification Cycle (ADR-028 Rule 7)

| Gate | Result |
|---|---|
| Governance + offline tests `pytest test_architecture_constitution.py test_domain_platform.py test_governance_scripts.py test_offline_sync.py -q` | **125 passed, 0 failed** (incl. 14 offline tests, 6 EncryptedSyncStore tests removed with class) |
| Architecture gate `scripts/architecture.py check` | **PASS** — 48 findings (48 acknowledged, **0 new**), domain 11/11 isolation PASS, country-agnostic PASS, policy engine PASS |
| `scripts/architecture.py baseline` | baseline written: **48 findings, 2 country findings** |
| Ruff `ruff check backend/app/services/offline_sync_service.py backend/tests/test_offline_sync.py` | 0 violations |
| Enterprise validation `scripts/enterprise_validation_engine.py --scope fast` | **VERDICT: PASS** — ruff 379 (baseline 379), tsc 0, eslint 0, brain fresh, 56 migrations |
| AST parse of all touched files | OK (module, test, archive) |

## 7. Baseline Reduction

```
Shared Core acknowledged findings:  49 → 48   (−1)
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

- The archived class is preserved at
  `archive/platform-shared-core/encrypted_sync_store.py` and is excluded from
  the architecture scan roots (`backend/app`, `shared`) by location.
- The live `OfflineSyncEngine` (`backend/app/integration/offline.py`,
  wired in `integration/routes.py`) is a **different module** and was verified
  untouched — the GULA Constitution's dormant-module protection applies to it,
  and it remains in the active tree.
- Commit 1.6 scope is intentionally minimal (1 finding). Next: Wave 1 order 4 —
  #6 doc-intel `AuditLogger` archive.
- A concurrent author's uncommitted files (`.ai/core/architect/state/**`,
  `.ai/core/optimizer/state/benchmarks/runs.json`,
  `.ai/core/orchestrator/history/registry.json`, `ARCHITECT_IMPLEMENTATION_REPORT.md`,
  `MISSION_STATUS.md`, `OPTIMIZER_IMPLEMENTATION_REPORT.md`) are outside this
  commit's scope and were left untouched.
