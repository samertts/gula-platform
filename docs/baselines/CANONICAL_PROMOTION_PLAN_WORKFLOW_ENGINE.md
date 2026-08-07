# Canonical Promotion Plan — Workflow Engine

**Canonical Promotion Plan for Commit 1.3**
**Status:** Executed under ADR-029
**Date:** 2026-08-07
**Governance:** ADR-028 (Structural Migration Rules), ADR-029 (Canonical Provider Promotion), ADR-024 (Platform Constitution)

This document is the mandatory planning artifact that precedes the migration
of the live identity workflow engine into the canonical Shared Core provider
path. It is produced **before any code moves** and every claim below was
verified before the `git mv` was issued. The execution evidence lives in
`docs/baselines/COMMIT_1_3_VERIFICATION_REPORT.md`; this plan records the
*decision rationale and strategy* that the execution implements.

---

## 1. Decision Type

This is **NOT a Shared Core removal**.

This is a **Canonical Provider Promotion**: the live implementation currently
residing outside the canonical provider set (in the identity domain) becomes
the canonical provider. No behavior is lost; architectural ownership is
corrected.

| | Removal | Promotion (this plan) |
|---|---|---|
| Live code | archived/deleted | **moved into canonical path** |
| Canonical provider | pre-existing, takes over | **populated by the live code** |
| Behavior | must be re-supplied by canonical | **carried intact by the moving code** |
| Finding resolution | baseline −1 (archive) | baseline −1 (ownership corrected) |

---

## 2. Why the current canonical provider is insufficient

The Shared Core `workflow_engine` capability is defined in
`backend/app/domain_platform/shared_core.py:86`:

```python
"workflow_engine": {
    "provider": "backend/app/workflows",
    "description": "Workflow engine for multi-step clinical and operational flows.",
},
```

Three provider locations are recognized by the canonical provider prefix set
(`SHARED_CORE_PROVIDER_PREFIXES`, `shared_core.py:238` and surrounding):

| Canonical candidate | State at planning time | Behaviorally equivalent to live engine? |
|---|---|---|
| `backend/app/workflows/` | Empty directory; no `__init__.py`; not a package | **n/a** — empty, holds no implementation |
| `shared/workflow/engine.py` | 75-LOC synchronous **in-memory** engine | **NO** — no persistence, no approvals, no DB, no async session |
| `backend/app/capabilities/workflow_engine/` | Stub; `domain/repository.py` raises `NotImplementedError` | **NO** — not implemented |

Evidence for the equivalence verdict (gathered before the move):

- `shared/workflow/engine.py` has **zero runtime importers** (repo-wide grep
  for `shared.workflow` matches only `scripts/architecture/core.py:61`, the
  scanner's canonical-path allowlist). It cannot host the live `/niam/workflows`
  API.
- `app.capabilities.workflow_engine` is a capability scaffold whose repository
  deliberately raises `NotImplementedError`; its `/workflow-engine/*` routes
  are **not registered** in `factory.py` (verified during Commit 1.3 analysis).
- The live engine (`identity/workflows/engine.py::WorkflowEngine`, 237 LOC)
  is an async, SQLAlchemy-backed engine with persisted definitions, instances,
  approvals, and notifications (`niam_wf_*` tables). None of the canonical
  shells can satisfy that contract.

**Conclusion:** Archiving the live engine (Commits 1.1/1.2 approach) is
impossible — the persisted `/niam/workflows` API must keep working and no
canonical provider can host it. The only correct migration is to promote the
live implementation into the (empty) canonical path.

---

## 3. Why the live implementation is the correct long-term owner

1. **It is the only real implementation.** The empty `app.workflows/` directory
   and the two shells hold no functional workflow engine. The live engine is
   the sole realization of the `workflow_engine` capability.
2. **It is production-proven.** It backs the live `/niam/workflows/*` route
   surface, exercised by the 89-test NIAM workflow suite and 4993-test backend
   suite. Promoting it preserves proven behavior.
3. **It matches the catalog's intended owner.** `SHARED_CORE_CATALOG`
   designates `backend/app/workflows` as the provider. The live engine is a
   natural fit for that home; the catalog's declared owner simply never got
   populated.
4. **Shared Core must not depend on a domain.** Today the canonical
   `workflow_engine` capability is *nominally* owned by `app.workflows` while
   the actual implementation lives in `app.identity` — an inverted dependency
   (Shared Core concept implemented inside a domain). Promoting fixes the
   ownership inversion.
5. **Domain Sovereignty is served.** Moving the engine out of the identity
   domain and into Shared Core makes the engine reusable by all domains
   (referral workflows, QA, operations) without cross-domain imports —
   exactly what `domain_platform/shared_core.py` intends.

---

## 4. Migration strategy

**Archive-and-repoint is rejected** (see §2). The strategy is **promote**:

1. `git mv backend/app/identity/workflows/engine.py backend/app/workflows/engine.py`
2. `git mv backend/app/identity/workflows/models.py backend/app/workflows/models.py`
   — models must move with the engine so the canonical provider is
   self-contained (Shared Core must not import `app.identity.workflows.models`).
3. Create `backend/app/workflows/__init__.py` to turn the namespace directory
   into a regular package (canonical provider package).
4. Re-point the identity route layer to the canonical engine:
   `from app.workflows.engine import WorkflowEngine`.
5. Re-point the test consumer (`test_niam_v2.py`) model imports to
   `app.workflows.models`.
6. Delete stale `__pycache__` in `identity/workflows/`.
7. Regenerate the constitution baseline (expected 52 → 51).

`git mv` preserves history (rename detected) → a single `git revert` of the
commit restores the prior state (ADR-028 Rule 6).

---

## 5. Compatibility strategy

| Dimension | Strategy | Evidence gate |
|---|---|---|
| API | Route layer **stays** in identity at the same prefix/tag; engine module path changes only | OpenAPI byte-identical, 1696 paths |
| Runtime | Engine class, methods, and async SQLAlchemy behavior unchanged | 4993-test suite identical |
| Database | Models still inherit `IdentityBaseEntity` → register on `IdentityBase.metadata`; `niam_wf_*` tables unchanged | Table-name verification |
| Authorization | Route-layer permission checks untouched | Gates PASS |
| Audit | No audit path changed | Audit tests PASS |

Compatibility is achieved by moving the *implementation* and re-pointing the
*consumers*, never by changing the *contract*.

---

## 6. Namespace strategy

| Element | Before | After |
|---|---|---|
| Engine module | `app.identity.workflows.engine` | `app.workflows.engine` |
| Models module | `app.identity.workflows.models` | `app.workflows.models` |
| Route module | `app.identity.workflows.routes` | **unchanged** (identity owns the `/niam/workflows` API) |
| Package | `identity/workflows/` (engine+models+routes) | `app.workflows/` (engine+models, canonical) + `identity/workflows/` (routes only) |
| API namespace | `/niam/workflows/*` | **unchanged** |

The canonical package `app.workflows` becomes the single home of the
`workflow_engine` Shared Core implementation. The identity package keeps only
its *interface to the platform* (the route layer), which is domain-owned by
design.

`app.workflows.` is already a canonical provider prefix
(`SHARED_CORE_PROVIDER_PREFIXES`, `shared_core.py:238`), so files under
`backend/app/workflows/` are recognized as canonical by the architecture
scanner (`scripts/architecture/core.py::_is_canonical`) — the moved engine is
automatically exempt from the reimplementation finding.

---

## 7. Import compatibility

**Internal imports (unchanged):** `engine.py` imports `from .models import ...`
— a relative import that survives the move because both files move together.

**Module-internal absolute imports:** `models.py` imports
`from app.identity.base import IdentityBaseEntity`. `app.identity` is itself a
Shared Core provider prefix, so this is a **canonical → canonical** import —
allowed and preserved verbatim (models keep registering on `IdentityBase`
metadata).

**Consumer imports (re-pointed):**

| Consumer | Before | After |
|---|---|---|
| `identity/workflows/routes.py` (9 call sites) | `from .engine import WorkflowEngine` | `from app.workflows.engine import WorkflowEngine` |
| `tests/test_niam_v2.py:402,417,434` | `from app.identity.workflows.models import ...` | `from app.workflows.models import ...` |
| `identity/api/router.py:14` | `from app.identity.workflows import routes` | **unchanged** (routes stay put) |

No `importlib`/`getattr`/string-import/plugin/runtime-registration coupling
exists (Hidden Coupling Audit clean).

---

## 8. Backward compatibility

- **API:** `/niam/workflows/{definitions,instances,approvals}` — identical
  paths, methods, request/response models, and permissions.
- **Frontend:** `WorkflowsPage.tsx` (raw `api.get/post`) and the committed
  generated client (`niam_workflowsApi` hooks, `client.ts:1131-1145`) consume
  URL paths only — no module-path dependency. Zero frontend changes needed.
- **Data:** `niam_wf_definitions`, `niam_wf_instances`, `niam_wf_approvals`,
  `niam_wf_notifications` stay on `IdentityBase.metadata`; no migration, no DDL.
- **Consumers:** the two re-pointed imports are the *only* references to the
  old module path (verified by repo-wide grep) — no other code observes the
  old location.

The old namespace `app.identity.workflows.engine/models` is vacated, not
re-exported: both modules moved (promotion, not facade). A compatibility
re-export is deliberately **not** created to avoid re-importing a duplicate
module under the identity namespace (which would re-open the finding). All
in-repo consumers were re-pointed atomically in the same commit.

---

## 9. Domain Platform implications

- `backend/app/domain_platform/shared_core.py` **does not change**: the
  `workflow_engine` catalog entry already names `backend/app/workflows` as
  provider, and `app.workflows.` is already a canonical provider prefix. The
  catalog was *ahead of reality* — this promotion makes reality match it.
- Domain Sovereignty improves: the identity domain no longer *implements* a
  Shared Core capability; it *consumes* it via its route layer
  (`assert_shared_core_or_domain_exception` on the route import path PASS).
- The domain isolation validator sees the engine leave `app.identity` →
  Shared Core, removing a potential cross-domain implementation of a core
  capability.
- `DomainCertificationEngine`/`platform_certification` (11/11) remains
  unaffected — no domain gained or lost an owned capability boundary.

---

## 10. Shared Core implications

- The `workflow_engine` capability finally has a **real, populated canonical
  provider** (`backend/app/workflows/`), instead of an empty directory plus
  two non-equivalent shells.
- The dormant shells (`shared/workflow/engine.py`,
  `app/capabilities/workflow_engine/`) are **left untouched** — they remain
  dormant canonical-provider shells with zero runtime importers. They are
  pre-existing state, not introduced by this migration, and not orphaned by
  it (Canonical-Provider Orphan Check PASS).
- Shared Core provider discovery (`_is_canonical`) recognizes the promoted
  engine automatically; the reimplementation signal for the finding
  (`WorkflowEngine` class under a non-canonical path) no longer fires.

---

## 11. Architecture Constitution implications

- The acknowledged finding at
  `.ai/core/architecture/constitution_baseline.json`
  (`backend/app/identity/workflows/engine.py`, capability `workflow_engine`)
  is **resolved by ownership correction**, not by deletion: 52 → 51.
- The gate (`scripts/architecture.py gate/check`) continues to fail on any
  **new** reimplementation; the promoted provider is exempt because it is
  canonical by path. Expected post-migration gate: **PASS, 51 acknowledged,
  0 new**.
- No rule of the Architecture Constitution is relaxed. The exemption that
  applies is the pre-existing canonical-provider exemption — the promoted
  code is genuinely canonical, not whitelisted-by-exception.
- The promotion is recorded as **ADR-029** (this decision changes canonical
  ownership of the Workflow Engine and therefore requires an ADR per the
  Documentation Policy).

---

## 12. Verification gates (executed after the move)

| Gate | Target |
|---|---|
| Backend suite | 4993 passed, 0 failed (identical to baseline) |
| OpenAPI byte-compare | byte-identical, 1696 paths |
| Architecture gate | PASS, 51 acknowledged, 0 new |
| Domain gate | 11/11 isolation PASS |
| Kernel check | ALL PASS |
| Ruff | 379 baseline, no new |
| Frontend | tsc 0 / eslint 0 (1 pre-existing warn) / vitest 122 / build OK |
| Orphan check | canonical providers not orphaned |
| Hidden coupling | clean |

## 13. Rollback

```
git revert <commit-hash>
```

Single revert restores `engine.py`/`models.py` to `identity/workflows/`,
reverts the two consumer re-points, and restores the 52-finding baseline. No
DB migration, no data change.

---

## References

- ADR-028 — Structural Migration Rules (`docs/adr/ADR-028-structural-migration.md`)
- ADR-029 — Canonical Provider Promotion (`docs/adr/ADR-029-canonical-provider-promotion.md`)
- `backend/app/domain_platform/shared_core.py` — `SHARED_CORE_CATALOG`, `SHARED_CORE_PROVIDER_PREFIXES`
- `.ai/core/architecture/constitution_baseline.json`
- `docs/baselines/COMMIT_1_3_VERIFICATION_REPORT.md` — execution evidence
