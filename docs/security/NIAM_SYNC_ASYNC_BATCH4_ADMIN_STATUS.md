# NIAM Sync/Async Closure Engine — Batch 4: `admin`

Phase 7 of the "NIAM SYNC/ASYNC CLOSURE ENGINE — REAL P1 CLOSURE — BOUNDED
BATCHES WITH AUTOMATIC GATES" workstream. Target: 12 occurrences in
`app/identity/admin/routes.py`.

## Discovery and classification

All 12 routes (`create_portal`, `list_org_portals`, `add_branch`,
`add_facility`, `add_department`, `get_subscription`,
`create_subscription`, `update_subscription`, `create_fhir_connection`,
`list_fhir_connections`, `test_fhir_connection`, `get_audit_log`) declared
`db: AsyncSession = Depends(get_db)` against `EnterprisePortalService`
(already correctly `__init__(self, session: AsyncSession)`) and the same
`AuthorizationDecisionService` used by `compliance`. **Category A**,
identical to every prior batch.

Same profile as `compliance` (Batch 3): no `id=...` crash bug
(`EnterprisePortalService` uses `_ulid()` directly, and the shared
`IdentityRepositoryBase.create()` helper never overrides `id`), real
per-organization ABAC already wired in via `_require_permission`, and
canonical audit already wired in (`self.audit = CanonicalAuditService(session)`,
`_record_admin_event` called from every mutating method). The one shared
defect: **missing commit** on all 8 mutating routes (`create_portal`,
`add_branch`, `add_facility`, `add_department`, `create_subscription`,
`update_subscription`, `create_fhir_connection`, `test_fhir_connection`).

## Repair

- `app/identity/admin/routes.py`: `Depends(get_db)` → `Depends(get_niam_db)`
  on all 12 routes; `await db.commit()` added after the service call in
  the 8 mutating routes.
- No changes to `services.py`, `_require_permission`'s ABAC logic, or
  audit wiring — all preserved exactly (rule #6).

## A second pre-existing, unrelated, out-of-scope bug found: `add_department`

`add_department`'s route resolves the target facility by its **business**
`facility_id` (correct — this is the URL path parameter's contract) to get
the facility's `organization_id`, but then passes that same business-key
string straight through to `EnterprisePortalService.add_department(facility_id=...)`.
`PortalDepartment.facility_id` is a real FK to `niam_admin_facilities.id`
(the **internal** ULID) — the route never fetches that internal `id` from
its own lookup query. Every real call to this endpoint fails with a
`psycopg.errors.ForeignKeyViolation`, **independent of sync or async
engine choice** — confirmed by the negative proof's control observation
that 401/401/403 all execute correctly (proving the auth/ABAC layers, and
this batch's fix, work fine) before the granted request hits this separate
defect. **Not fixed here** — out of scope for a sync/async batch (a
route/service field-mapping bug, not a Category-A occurrence). Recommended
fix for a future, correctly-scoped pass: have the route's lookup query
select `PortalFacility.id` alongside `organization_id` and pass that `id`
as `facility_id` to the service call.

This is the second such finding this session (after `compliance`'s
`func.case` bug in Batch 3), reinforcing that "the sync/async fix makes
the route reachable" is not the same claim as "the route is bug-free" —
each newly-reachable route surfaces whatever was already broken beneath
the crash, and this workstream's discipline is to report those precisely
rather than silently expand the batch's scope to fix them.

## Real HTTP + PostgreSQL proof

Seeded two accounts (no ABAC grant, and a full grant — `Membership` +
`Role` + 5 `Permission` catalog entries covering
`organization.manage`/`organization.read`/`subscription.manage`/
`integration.manage`/`audit.read` + `RolePermission` + active
`RoleAssignment`) scoped to one real `NIAMOrganization`. Full matrix, all
12 routes, against real PostgreSQL:

| Route | No token | Expired session | No permission | Granted |
|---|---|---|---|---|
| `POST /portals` (create_portal) | 401 | 401 | 403 | 200 |
| `GET /portals/organization/{id}` (list_org_portals) | 401 | 401 | 403 | 200 |
| `POST /portals/{id}/branches` (add_branch) | 401 | 401 | 403 | 200 |
| `POST /branches/{id}/facilities` (add_facility) | 401 | 401 | 403 | 200 |
| `POST /facilities/{id}/departments` (add_department) | 401 | 401 | 403 | 500 — pre-existing, unrelated bug (see above) |
| `GET /subscriptions/{org_id}` (get_subscription) | 401 | 401 | 403 | 200 |
| `POST /subscriptions` (create_subscription) | 401 | 401 | 403 | 200 |
| `PUT /subscriptions/{id}` (update_subscription) | 401 | 401 | 403 | 200 |
| `POST /fhir-connections` (create_fhir_connection) | 401 | 401 | 403 | 200 |
| `GET /fhir-connections/organization/{id}` (list_fhir_connections) | 401 | 401 | 403 | 200 |
| `POST /fhir-connections/{id}/test` (test_fhir_connection) | 401 | 401 | 403 | 200 (real outbound httpx call to an allowlisted host; the service's own `except Exception` branch handles any network failure and still returns 200 with `success: false` — no crash channel) |
| `GET /audit-log/{org_id}` (get_audit_log) | 401 | 401 | 403 | 200 |

**Fresh-session persistence proof**: portal, branch, facility, subscription
(`plan_type` correctly updated to `"enterprise_plus"` by `update_subscription`),
and FHIR connection (`last_test_at` set by `test_fhir_connection`) all
persisted with real data; `department_persisted: false` as expected, given
the pre-existing bug above.

## Failure injection (rollback proof)

Monkeypatched `AsyncSession.commit` to raise immediately after
`create_portal`'s flush. Result: `500`, and a fresh-session query confirmed
**zero orphaned rows** for that portal name. A control request after the
monkeypatch was removed returned `200` and persisted normally.

## Negative proof

Reverted `create_portal`'s dependency to `get_db` (the actual Category-A
defect). Re-ran the rollback-proof script's two requests: both the
injected-failure request and the plain control request returned `403` —
the same silent-swallow-to-deny behavior observed in `compliance`'s Batch
3 negative proof (`AuthorizationDecisionService.authorize()`'s blanket
`except Exception` converts the sync/async `TypeError` into an
`internal_failure` deny). Confirmed a real, reproducible regression via
the actual defect this batch fixes. Restored `routes.py` from a
pre-change backup; `md5sum` and `git diff` both confirmed byte-identical
restoration to the fixed state before continuing.

## Regression

`pytest tests/identity/ tests/test_migrations.py
tests/test_migration_resilience.py`: **255 passed, 4 skipped** — identical
to the Batch 1/2/3 baseline.

## GATE 1

- All 12 occurrences correctly classified: **yes** (Category A, no
  crash-bug variant, confirmed by reading `services.py` and
  `repositories/base.py` in full).
- All applicable defects repaired (dependency swap + 8 missing commits);
  existing ABAC authorization and canonical audit deliberately left
  untouched: **yes**.
- Compile + lint clean: **yes**.
- Regression suite: **yes**, 255 passed / 4 skipped, no change from
  baseline.
- Real HTTP proof (12/12 routes, 4-state matrix against a real ABAC
  grant): **yes**.
- Real PostgreSQL persistence proof: **yes**.
- Transaction/rollback (failure injection) proof: **yes**, zero orphaned
  rows.
- Negative proof using the actual Category-A defect, confirmed real
  regression, source restored byte-identical: **yes**.
- A newly-discovered, unrelated bug (`add_department`'s facility-id
  field-mapping defect) found and precisely documented rather than
  silently left unmentioned or fixed outside this batch's scope: **yes**.

## RESULT

**VERIFIED.** Sync/async defect count: 108 → 96 (12 closed: `admin`). One
new, separate, out-of-scope finding recorded above for a future pass.
Batch 5 (`adaptive_auth`, 16 occurrences, security-sensitive — explicit
"DO NOT use mechanical transformation alone") may now begin.
