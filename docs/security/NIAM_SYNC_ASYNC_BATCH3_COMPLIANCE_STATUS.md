# NIAM Sync/Async Closure Engine — Batch 3: `compliance`

Phase 6 of the "NIAM SYNC/ASYNC CLOSURE ENGINE — REAL P1 CLOSURE — BOUNDED
BATCHES WITH AUTOMATIC GATES" workstream. Target: 8 occurrences in
`app/identity/compliance/routes.py`.

## Discovery and classification

All 8 routes (`register_framework`, `list_frameworks`, `get_framework`,
`run_check`, `list_checks`, `generate_report`, `get_report`,
`get_org_compliance_status`) declared `db: AsyncSession = Depends(get_db)`
against `ComplianceService` (already correctly `__init__(self, session:
AsyncSession)`) and `AuthorizationDecisionService` (also already correctly
written for a real `AsyncSession`, confirmed by reading
`app/identity/services/authorization_decision.py`). **Category A**,
identical to the pattern proven and fixed in every prior batch this
session.

Unlike `workflows` and `notifications`, this module is materially more
mature:

- **No `id=...` crash bug** — `ComplianceService` uses `_ulid()` directly
  for business-key fields (`framework_id`, `check_id`, `report_id`) and
  never overrides the model's own `id` default. Confirmed via
  `models.py`.
- **Real, pre-existing ABAC authorization** — `_require_compliance_permission`
  already calls the full `AuthorizationDecisionService` (membership
  resolution, role/permission catalog lookup, policy evaluation), not
  just authentication. This is exactly the kind of existing authorization
  semantics rule #6 requires this batch to preserve unchanged, not
  extend or replace.
- **Canonical audit already wired in** — `ComplianceService.__init__`
  already constructs `self.audit = CanonicalAuditService(session)` and
  records `COMPLIANCE_FRAMEWORK_REGISTERED` / `COMPLIANCE_CHECK_EXECUTED` /
  `COMPLIANCE_REPORT_GENERATED` events.

The one defect shared with prior batches: **missing commit**. None of the
3 mutating routes (`register_framework`, `run_check`, `generate_report`)
called `await db.commit()` — same `niam-no-commit` pattern.

## Repair

- `app/identity/compliance/routes.py`: `Depends(get_db)` →
  `Depends(get_niam_db)` on all 8 routes (import reordered by `ruff --fix`
  to satisfy import sorting); `await db.commit()` added after the service
  call in the 3 mutating routes.
- No changes to `services.py` (no crash bug present) and no changes to
  `_require_compliance_permission`'s ABAC logic (preserved exactly).

## A notable behavioral finding from the negative proof

Reverting `register_framework`'s dependency back to `get_db` did **not**
produce a visible crash. Instead, every request — including one from an
actor with a fully valid Membership/Role/Permission/RoleAssignment grant —
returned **403** with reason `internal_failure`. Root cause:
`AuthorizationDecisionService.authorize()` wraps its entire `_evaluate()`
call in a blanket `try/except Exception`, which silently catches the
sync/async `TypeError` (`await`-ing a plain `Session.execute()` result)
and converts it into an authorization deny rather than letting it surface
as a 500. This means the pre-fix compliance module was not merely
"crashing" — it was **silently and unconditionally deny-closed for every
request, including legitimately authorized ones**, with no visible signal
that anything was wrong. Fail-closed is the safe direction (not a security
bypass), but it is a materially different, more severe failure mode than
`workflows`/`notifications`' visible `TypeError`, and worth surfacing
explicitly rather than assuming "no crash" meant "no bug."

## Real HTTP + PostgreSQL proof

Seeded two accounts: one with no ABAC grant, one with a real, full grant
(`Membership` + `Role` + `Permission` catalog entries for
`compliance.manage`/`compliance.read`/`compliance.report` + `RolePermission`
+ active `RoleAssignment`) scoped to one real `NIAMOrganization`. Full
matrix, all 8 routes, against real PostgreSQL:

| Route | No token | Expired session | No permission | Granted |
|---|---|---|---|---|
| `POST /frameworks` (register_framework) | 401 | 401 | 403 | 200 |
| `GET /frameworks` (list_frameworks) | 401 | 401 | 403 | 200 |
| `GET /frameworks/{id}` (get_framework) | 401 | 401 | 403 | 200 |
| `POST /checks` (run_check) | 401 | 401 | 403 | 200 |
| `GET /checks/{type}/{id}` (list_checks) | 401 | 401 | 403 | 200 |
| `POST /reports` (generate_report) | 401 | 401 | 403 | 200 |
| `GET /reports/{id}` (get_report) | 401 | 401 | 403 | 200 |
| `GET /status/{org_id}` (get_org_compliance_status) | 401 | 401 | 403 | see below |

**Fresh-session persistence proof**: framework persisted with
`status="active"`; check persisted with `status="passed"`; report
persisted with `overall_score=100`, correctly aggregated from the one
passed check — proving `register_framework`, `run_check`, and
`generate_report`'s newly-added commits actually durably persist data.

### `get_org_compliance_status` — a separate, pre-existing, out-of-scope bug

The authenticated-and-granted request to this one read-only route returns
`500`, not `200`. Root cause (confirmed from the server log):
`Function.__init__() got an unexpected keyword argument 'else_'` — the
service method uses `func.case((ComplianceCheck.status == "passed", 1),
else_=0)`, but `func.case` (SQLAlchemy's generic "call a SQL function
named case" helper) does not accept `else_`; the correct API is the
standalone `sqlalchemy.case(...)` construct. This error is raised while
**constructing** the SQL expression in Python, before any statement is
sent to the database — proof that it is completely unrelated to the
sync/async engine choice (it would fail identically under a real
`AsyncSession` or a real `Session`). This is a distinct, pre-existing
defect in `ComplianceService.get_org_compliance_status`, out of scope for
this batch (not a sync/async occurrence — the route's Category-A defect
*is* fixed, proven by the fact that authentication and the full ABAC chain
now execute correctly, including two real async DB round-trips inside
`AuthorizationDecisionService`, before failing on this unrelated bug).
**Not fixed here** — documented as a new, separate finding for a future,
correctly-scoped pass (a one-line fix: `from sqlalchemy import case` and
`case((cond, 1), else_=0)` in place of `func.case`).

## Failure injection (rollback proof)

Monkeypatched `AsyncSession.commit` to raise immediately after
`register_framework`'s flush. Result: `500`, and a fresh-session query
confirmed **zero orphaned rows** for that framework name. A control
request after the monkeypatch was removed returned `200` and persisted
normally.

## Negative proof

Reverted `register_framework`'s dependency to `get_db` (the actual
Category-A defect, not a synthetic stand-in) and re-ran the same
authorized request: it returned `403` (silently converted from the
underlying `TypeError`, as explained above) instead of `200` — confirmed a
real, reproducible regression via the actual defect this batch fixes.
Restored `routes.py` from a pre-change backup; `md5sum` and `git diff`
both confirmed byte-identical restoration to the fixed state (the
intended 2-line/1-import diff only) before continuing.

## Regression

`pytest tests/identity/ tests/test_migrations.py
tests/test_migration_resilience.py`: **255 passed, 4 skipped** — identical
to the Batch 1/2 baseline.

## GATE 1

- All 8 occurrences correctly classified: **yes** (Category A, no
  crash-bug variant present here, confirmed by reading `services.py` in
  full).
- All applicable defects repaired (dependency swap + 3 missing commits);
  existing ABAC authorization and canonical audit deliberately left
  untouched, matching rule #6: **yes**.
- Compile + lint clean: **yes**.
- Regression suite: **yes**, 255 passed / 4 skipped, no change from
  baseline.
- Real HTTP proof (8/8 routes, 4-state matrix against a real ABAC grant):
  **yes**.
- Real PostgreSQL persistence proof: **yes**.
- Transaction/rollback (failure injection) proof: **yes**, zero orphaned
  rows.
- Negative proof using the actual Category-A defect (not a substitute),
  confirmed real regression, source restored byte-identical: **yes**.
- A newly-discovered, unrelated bug (`get_org_compliance_status`'s
  `func.case` misuse) found and precisely documented rather than silently
  left unmentioned or fixed outside this batch's scope: **yes**.

## RESULT

**VERIFIED.** Sync/async defect count: 116 → 108 (8 closed:
`compliance`). One new, separate, out-of-scope finding recorded above for
a future pass. Batch 4 (`admin`, 12 occurrences) may now begin.
