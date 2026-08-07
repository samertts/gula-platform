# PROGRAM-01 — Commit 3.1 Verification Report

**Finding:** #24 + #49 — `notifications`
**Class:** Canonical Provider Completion (ADR-029, ADR-032)
**Commit:** 3.1
**Date:** 2026-08-07
**Baseline:** 37 → 35 acknowledged findings

---

## 1. Migration Summary

| Item | Detail |
|---|---|
| Finding | `identity/notifications/services.py` — `NotificationService` (queue-only, #24) and `identity/notifications/routes.py` — `send_notification` (queue-only, #49) |
| Canonical provider | `backend/app/notifications` (was delivery-only; now delivery + queue + templates + preferences) |
| Why completion | The canonical provider delivers but has no persistence; the finding is the **ONLY DB-backed notification queue/template/preference layer in the platform** (`niam_notif_*` tables, migration `20260723_0002`), backing the live `/niam/notifications/*` API. The two are **complementary halves** — promote the missing half, then re-point. |
| Action | `git mv` `models.py`/`services.py`/`routes.py` → `app/notifications/` (history preserved); queue class renamed `NotificationService` → `NotificationQueueService`; consumers re-pointed atomically |
| ADR | ADR-032 accepted first (notifications queue completion); governed by ADR-029 (completion) + ADR-028 (migration) |

## 2. Reimplementation Evidence

- **Not a removal:** the queue layer is live — 11 route handlers mounted at
  `/niam/notifications/*` via the NIAM router, backed by real DB tables.
- **Not an archive:** no canonical queue existed; `backend/app/notifications`
  was delivery-only (`service.py`, Telegram channels).
- **Complementary halves:** canonical delivers; finding queues. Ownership
  correction completes the canonical provider with its missing persistence
  half, satisfying the constitution signal (`notifications` →
  `backend/app/notifications`) at its source.
- **Consumer inventory (complete):** `rg "identity.notifications"` across
  `backend/app` + `backend/tests` → exactly 2 references: the NIAM router
  import and `test_niam_v2.py` (2 model imports). Package `__init__.py` was
  empty (0 bytes) — not a public API.

## 3. Migration Impact Report

**Files moved (git mv, history preserved):**

- `backend/app/identity/notifications/models.py` → `backend/app/notifications/models.py` (76 LOC)
- `backend/app/identity/notifications/services.py` → `backend/app/notifications/services.py` (285 LOC)
- `backend/app/identity/notifications/routes.py` → `backend/app/notifications/routes.py` (198 LOC)
- `backend/app/identity/notifications/__init__.py` — removed (empty, not a public API)

**Source edits (behavior-preserving):**

- `app/notifications/services.py` — class renamed `NotificationService` →
  `NotificationQueueService` (required: the canonical package already defines a
  different `NotificationService` in `service.py`, exported by `__init__.py`).
- `app/notifications/routes.py` — 11 `NotificationService(db)` →
  `NotificationQueueService(db)`; relative `.services` import updated.
- `backend/app/identity/api/router.py` — import re-pointed to
  `app.notifications.routes`; `include_router(notifications_routes)`.
- `backend/tests/test_niam_v2.py` — 2 model imports re-pointed to
  `app.notifications.models`.

**Retained dependency (documented, behavior-required):**

- `app/notifications/models.py` still extends `IdentityBaseEntity`
  (`app.identity.base`): its `before_insert` listener resolves the `id=...`
  Ellipsis placeholder used by every call site, and it provides `to_dict()`,
  `created_at`, `updated_at` matching the `niam_notif_*` tables. `app.identity`
  is platform infrastructure (NIAM), not one of the 11 healthcare domains; the
  dependency does not invert the domain graph (see ADR-032 Decision 4).

**New regression test:**

- `backend/tests/unit/test_notifications_queue_promoted.py` — 23 tests:
  canonical import paths + vacated old namespace, unchanged table names, base
  class + Ellipsis-id resolution, `to_dict`, and `NotificationQueueService`
  behavior (send/send_template rendering/None, mark_sent/delivered/read +
  not-found, get_pending, preferences get/update-create/update, create_template
  inactive-by-default, list_templates, queue-for-recipient) + router
  prefix/tags/mount.

**Old namespace:** `app.identity.notifications` vacated (no facade per
ADR-029 Rule 4); zero in-repo references remain (verified by repo-wide grep).

**API impact:** NONE — `/niam/notifications/*` paths, methods, parameters, and
response shapes byte-identical. OpenAPI diff vs pre-change: **identical**
(2028 methods / 1696 paths; 9 `/niam/notifications` paths).

**Frontend impact:** NONE (no frontend files changed; byte-identical OpenAPI
contract → generated client unchanged).

**Dependency changes:** NONE (all moved modules already imported by the backend).

**DB changes:** NONE — `niam_notif_*` tables and migration
`20260723_0002_niam_completion_tables.py` untouched.

**LOC delta:** net 0 (move) + 23 new test LOC.

## 4. Canonical-Provider Orphan Check

| Provider | Check | Result |
|---|---|---|
| `backend/app/notifications` | delivery (`service.py`) + promoted queue (`models/services/routes.py`); no competing duplicate remains | **PASS** |
| `backend/app/identity/notifications` | vacated; zero in-repo references | **PASS** |
| NIAM router | `app/identity/api/router.py` re-pointed; `/niam/notifications/*` still mounted via factory niam include | **PASS** |

## 5. Behavior Preservation

- **Boot:** app boots, **119 routes** (identical to Wave 2 final state).
- **OpenAPI:** byte-identical contract (2028 methods / 1696 paths), verified by
  a before/after OpenAPI diff.
- **Regression suite:** backend **4977 passed / 0 failed** (4954 baseline +
  23 new queue tests), 148 warnings, 9m34s.
- **DB:** no DDL change; `id=...` Ellipsis resolution and `to_dict()` semantics
  verified by regression tests.
- **Ruff:** clean on all changed scope (1 I001 auto-fixed in router.py).

## 6. Verification Matrix (Commit 3.1)

| # | Verification | Result |
|---|---|---|
| 1 | Architecture Constitution | **PASS** — 35 findings (35 ack, **0 new**) |
| 2 | Policy Engine | **PASS** |
| 3 | Domain Certification | **PASS** — 11/11, isolation PASS |
| 4 | OpenAPI | **PASS** — before/after diff identical (2028 methods / 1696 paths) |
| 5 | Generated Clients | **PASS** — no contract/model change |
| 6 | Frontend Compatibility | **PASS** — no frontend files changed; OpenAPI identical |
| 7 | Permissions | **PASS** — no route/permission touched |
| 8 | Database Compatibility | **PASS** — no DDL change |
| 9 | Behavior Preservation | **PASS** — boot 119 + 23 regression tests + byte-identical OpenAPI |
| 10 | Performance | **PASS** — no hot-path change (move only) |
| 11 | Regression Tests | **PASS** — 4977 passed / 0 failed |
| 12 | Build Validation | **PASS** — boot 119 routes; all touched modules import cleanly |
| 13 | Repository Health | **PASS** — ruff 0 on changed scope |
| 14 | Inventory | **PASS** — `docs/api/backend_inventory.json` regenerated (identity/notifications removed) |
| 15 | Orphan Check | **PASS** — §4 |

## 7. Baseline & Rollback

- Baseline regenerated: 37 → **35** acknowledged findings
  (`constitution_baseline.json`; 2 country findings unchanged).
- **Rollback class:** M (single `git revert <hash>` restores all moved files,
  the class rename, and the re-pointed consumers atomically; no data or schema
  involved — tables unchanged).

## 8. Report Trail

- ADR-032 (this completion): `docs/adr/ADR-032-notifications-queue-completion.md`
- Classification §2.7 + §10 (marked DONE): `docs/baselines/ARCHITECTURAL_MIGRATION_CLASSIFICATION.md`
- Dashboard: `PROGRAM-01_DASHBOARD.md`
- Shared Core report: `docs/certification/SHARED_CORE_REPORT.md`
- Inventory: `docs/api/backend_inventory.json` (regenerated)
- ADR index: `docs/adr/README.md`
