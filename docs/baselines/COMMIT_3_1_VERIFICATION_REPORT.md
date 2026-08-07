# PROGRAM-01 — Commit 3.1 Verification Report

**Finding:** #24 + #49 — `notifications`
**Class:** Canonical Provider Completion (ADR-029, ADR-032)
**Commit:** 3.1
**Date:** 2026-08-07 (finalized 2026-08-07)
**Baseline:** 37 → 35 acknowledged findings

---

## 1. Executive Summary

The identity notification **queue** (`identity/notifications/services.py`, #24) and
**queue-only send route** (`identity/notifications/routes.py` `send_notification`, #49)
were promoted into the canonical `backend/app/notifications` provider, which previously
held only the synchronous delivery half. The move is a pure **completion**: the queue is
the ONLY DB-backed notification persistence layer (`niam_notif_*` tables, migration
`20260723_0002`) and remains the backing store of the live `/niam/notifications/*` API.
The old namespace is fully vacated with no facade; the queue class was renamed
`NotificationService` → `NotificationQueueService` to remove a name collision with the
canonical sync delivery `NotificationService`.

**Result:** architecture constitution findings **37 → 35**, OpenAPI contract
byte-identical (2028 methods / 1696 paths), full backend suite **4977 passed / 0 failed**,
all gates PASS. **VERDICT: APPROVED for commit.**

## 2. Files Changed

**Moved via `git mv` (history preserved):**

| From | To | LOC |
|---|---|---|
| `backend/app/identity/notifications/models.py` | `backend/app/notifications/models.py` | 76 |
| `backend/app/identity/notifications/services.py` | `backend/app/notifications/services.py` | 285 |
| `backend/app/identity/notifications/routes.py` | `backend/app/notifications/routes.py` | 198 |
| `backend/app/identity/notifications/__init__.py` | removed (empty, not public API) | 0 |

**Source edits (behavior-preserving):**

- `backend/app/notifications/services.py` — class `NotificationService` →
  `NotificationQueueService` (name collision with canonical sync `NotificationService`
  in `app/notifications/service.py`, exported by `__init__.py`).
- `backend/app/notifications/routes.py` — 11 `NotificationService(db)` →
  `NotificationQueueService(db)`; relative import updated.
- `backend/app/identity/api/router.py` — import re-pointed to `app.notifications.routes`;
  `router.include_router(notifications_routes)`.
- `backend/tests/test_niam_v2.py` — 2 model imports re-pointed to `app.notifications.models`.

**Added:**

- `backend/tests/unit/test_notifications_queue_promoted.py` — 23 regression tests.

**Governance artifacts (regenerated):**

- `.ai/core/architecture/constitution_baseline.json` (37 → 35), `docs/api/backend_inventory.json`
  (787 endpoints / 53 route files / 146 model files), ADR-032 + ADR-033,
  `docs/adr/README.md`, classification, dashboard, Shared Core report, verification report.

## 3. Canonical Provider Verification

| Provider | Check | Result |
|---|---|---|
| `backend/app/notifications` | delivery (`service.py`) + promoted queue (`models/services/routes.py`); no competing duplicate remains | **PASS** |
| `backend/app/identity/notifications` | vacated; zero in-repo references (repo-wide grep) | **PASS** |
| NIAM router | `app/identity/api/router.py` re-pointed; `/niam/notifications/*` still mounted | **PASS** |
| Consumer inventory | exactly 2 references existed pre-move (router import + `test_niam_v2.py`), both re-pointed | **PASS** |
| Retained dependency | `app/notifications/models.py` extends `IdentityBaseEntity` (behavior-required: Ellipsis `id` resolution + `to_dict()` + audit columns) — documented exception in ADR-032; `app.identity` is platform infrastructure, not a healthcare domain | **PASS** |

## 4. Before vs After Metrics

| Metric | Before (Wave 2) | After (Commit 3.1) |
|---|---|---|
| Architecture findings | 37 | **35** (−2: #24, #49) |
| OpenAPI paths | 1696 | 1696 (identical) |
| OpenAPI methods | 2028 | 2028 (identical) |
| Route entries (boot) | 119 | 119 |
| Backend tests | 4954 passed / 0 failed | **4977 passed / 0 failed** (+23) |
| `app/notifications` surface | delivery only | delivery + queue + templates + preferences |
| Notification persistence layers | 3 (legacy/NIAM/national) | 2 (canonical/national) |
| Warnings | 148 | 148 |
| Full-suite runtime | ~9m | **10m45s** (645.71s) |

## 5. Architecture Metrics

| Metric | Value |
|---|---|
| Constitution findings | 35 acknowledged, **0 new** |
| Baseline delta | 37 → 35 (−2) |
| Country-agnostic scan | PASS |
| Policy Engine | PASS (1 enabled policy evaluated) |
| Shared Core catalog | 50 services (unchanged) |

## 6. Shared Core Findings (35 acknowledged, 0 new)

`scripts/architecture.py gate` → **PASS**:

```
Shared Core scan: 35 findings (35 acknowledged, 0 new)
Domain certification: 11/11 (isolation PASS)
Country-agnostic: PASS
Policy Engine: PASS (1 enabled policy/policies evaluated)
```

No new reimplementation signals introduced by this commit. Baseline regenerated to
35 records; `identity/notifications` absent from `constitution_baseline.json`.

## 7. Domain Certification

| Check | Result |
|---|---|
| Domain certification | **11/11** PASS |
| Domain isolation | PASS (0 findings in all 6 categories) |
| Cross-domain administration | none introduced (move within platform infra layer) |

## 8. Backend Test Results

Full suite with PostgreSQL:

```
DATABASE_URL=postgresql://postgres:gula_dev_2026@172.18.0.3:5432/gula
backend/tests — 4977 passed, 148 warnings in 645.71s (10:45)
```

- **4977 passed / 0 failed** (4954 baseline + 23 notifications-queue promotion tests).
- Related suites (niam_v2 + promoted + architecture + domain): 161 passed.
- No new warnings attributable to the migration.

## 9. Frontend Verification

- **No frontend files changed** by Commit 3.1.
- OpenAPI contract byte-identical → generated client (`frontend-v3/src/api/generated/client.ts`)
  unchanged.
- `tsc --noEmit`: **0 errors** (exit 0).
- ESLint baseline unchanged (no frontend diff).

## 10. OpenAPI Compatibility

- **PASS** — before/after spec diff **byte-identical** (2028 methods / 1696 paths),
  method-level params (name/in/required/schema.type) verified equal.
- Post-move re-check on live boot: 1696 paths, including **9** `/niam/notifications/*`
  paths (pending, send, send-template, templates, preferences/{id}, queue/{id}/sent,
  queue/{id}/delivered, queue/{id}/read, queue/{recipient_id}).
- Duplicate Operation ID warnings (connectors routes) are pre-existing and unrelated.

## 11. Build Status

| Check | Result |
|---|---|
| Backend boot with PG | **PASS** — 119 route entries, "All platform routes registered" |
| PostgreSQL | **PASS** — PG 16.14 @ `172.18.0.3:5432`, `gula` DB, 351 tables, single alembic head |
| Ruff (changed scope) | **PASS** — 0 violations |
| py_compile / imports | **PASS** — all touched modules import cleanly |
| Inventory regeneration | **PASS** — `backend_inventory.json` (787 endpoints / 53 route files / 146 model files) |
| Frontend tsc | **PASS** — 0 errors |

## 12. Rollback Procedure

- **Rollback class:** M (single `git revert <hash>`).
- Reverts: 3 file moves (back to `app/identity/notifications/`), the class rename, the
  re-pointed consumers, the regression tests, the ADRs, and the regenerated baseline
  (37 findings) **atomically**.
- No data involved — DB tables and DDL (`niam_notif_*`, migration `20260723_0002`) are
  untouched by this commit, so no data migration or coordination is required.

## 13. Risks

| Risk | Severity | Mitigation |
|---|---|---|
| `IdentityBaseEntity` coupling persists in promoted models | Low | Documented ADR-032 decision; `app.identity` is platform infra, not a domain; revisit if NIAM is ever extracted |
| Name collision (two `NotificationService`s) | Medium | Resolved via `NotificationQueueService` rename + regression test asserting canonical import path |
| PG reachable only at container IP `172.18.0.3:5432` | Low (env) | `DATABASE_URL` documented; localhost refused is a host-network artifact, not a code issue |
| Engine state-file regeneration noise on gate runs | Low | Governance JSONs restored to committed state; gate verdict is the signal |

## 14. Unexpected Observations

1. **`app.routes` deferred-routing quirk:** `ENV=test` boot lists 119 entries as deferred
   `_IncludedRouter` objects (only 4 eager top-level paths); recursive traversal shows 0
   APIRoutes until materialization. Contract verified via the authoritative OpenAPI spec
   instead (1696 paths), not `app.routes`.
2. **Re-running the gate regenerates synthetic engine state** (optimizer benchmark entries
   OPT-000077..079, orchestrator registry rows, timestamp churn across 15 governance JSONs).
   These are engine self-test artifacts, not program data; restored to committed state.
3. **`gula-backend` container has been `Exited` for 7 days** — verification was run against
   the host venv + live PG container, not the stale container.

## 15. Final Certification Verdict

**APPROVED.**

- Constitution gate PASS (35 ack, 0 new) · Domain 11/11 · Country-agnostic PASS.
- OpenAPI byte-identical · Boot 119 routes · Full suite **4977 passed / 0 failed**.
- Ruff clean · Frontend tsc 0 · Baseline 37 → **35**.
- Rollback = single `git revert` (class M, no data).

Commit 3.1 (order 13) is complete. Commit 3.2 (order 14, search) and Commit 3.3
(order 15, PDF) shall not begin without explicit approval.
