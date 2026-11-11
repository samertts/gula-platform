# Biomedical — Work Order / Device Status Concurrency Guard (CAS)

**Domain selection**: continuing the systemic concurrency sweep, checked
`blood_bank` and `critical_care` first (both `system:admin`-gated,
table-backed, live) — both turned out to already be extensively
concurrency-hardened by a prior engineering pass (a "legacy method + new
`_safely`-suffixed method" convention, with routes exclusively calling the
`_safely` variants and the legacy ones confirmed DEAD_OR_UNREACHABLE via
repo-wide grep). `blood_bank` additionally has a dedicated real-PostgreSQL
concurrency/idempotency/failure-injection test suite
(`tests/blood_bank/`, env-gated on `BLOOD_BANK_POSTGRES_URL`) — re-ran it
against a genuinely `alembic upgrade head`-migrated disposable database
(worked around the pre-existing, already-filed
`nhdw-hospital-structure-migration-gap` blocker by stamping past that one
known-broken migration in a throwaway database only, then continuing the
upgrade — no migration file was modified): **32/32 passed**, confirming
VERIFIED SAFE rather than assuming it from "looks safe."

`biomedical` (12 tables, `system:admin`-gated, live, zero existing test
files) did NOT have the `_safely` convention applied — a real, genuine gap.

## Finding — P1 (proven, admin-gated so bounded blast radius)

`app/biomedical/application/service.py::update_device_status` and
`complete_work_order` each read a `MedicalDeviceModel`/`WorkOrderModel`
row with a plain, unlocked `SELECT`, mutated it, and committed — despite
both models already inheriting `OptimisticLockMixin` (a `version` column
was available and unused). `complete_work_order` additionally had no
terminal-state guard at all: a work order already `"completed"` could be
"completed" again, re-applying its cost totals and re-releasing its
linked device.

Router-level gate is `Depends(require_permission("system:admin"))` (same
as the already-triaged `tenant-scope-sweep` domains) — this bounds
exploitability to admin-tier accounts, so this is classified P1, not P0
(no cross-tenant/unauthenticated path), but it is still a real duplicate-
side-effect bug: two admins (or one admin double-clicking, or a retried
HTTP request) completing the same work order concurrently both succeed.

## REAL POSTGRESQL PROOF

Two real threads, separate SQLAlchemy sessions/connections, against a
disposable PostgreSQL 16 database, synchronized with a
`threading.Barrier`, both calling `complete_work_order` on the same work
order:

| | Pre-fix (stashed) | Post-fix (restored) |
|---|---|---|
| Thread results | both `("ok", <same work order id>)` | one `("ok", ...)`, one `("conflict", "Work order is already completed")` |
| Final work order `version` | 1 (never incremented) | 2 |
| Final device `version` | 1 (never incremented) | 2 |
| Side effects applied | twice (silently) | once |

## Negative proof

`git stash`ed the fix (3 files: `service.py`, `exceptions.py`,
`routes.py`; byte-identical revert/restore confirmed via `md5sum`),
reproduced the double-completion, restored, re-ran — closed.

## FIX

- `update_device_status`: added `.with_for_update()` + `version += 1`.
- `create_work_order`: the linked device's status-flip to
  `UNDER_MAINTENANCE` now goes through `.with_for_update()` + version bump
  too (it was the same unlocked-write shape, just on the create path).
- `complete_work_order`: added `.with_for_update()` on both the work
  order and its linked device, `version += 1` on both, and a terminal-
  state guard (raises a new `WorkOrderAlreadyCompletedError`, mapped to
  `409 Conflict` in `routes.py` — not reusing `WorkOrderNotFoundError`/404,
  which would have been semantically wrong).

No schema change: `version` already existed via `OptimisticLockMixin`,
inherited through `TenantAuditEntity` — the same primitive this session
has now used for payments, devices, and biomedical.

## REGRESSION

New test file `tests/test_biomedical_work_order_cas.py` (biomedical had
zero existing tests) — 4 tests: version-increment + locked-query proof
for both mutation paths, and a direct test that a second completion
attempt is rejected with the payload never applied. Negative-proofed:
collection itself fails against the pre-fix code (the new exception class
doesn't exist yet), let alone the assertions.

```
tests/identity/ tests/test_migrations.py tests/test_migration_resilience.py
tests/test_payments_foundation.py tests/test_payment_orchestration.py
tests/test_payments_route_registration.py tests/test_device_outbox.py
tests/test_biomedical_work_order_cas.py
  → 316 passed, 4 skipped, zero failures
```

## Status

**FIXED — VERIFIED** (real-Postgres-proven, negative-proofed, zero regressions)

## Related, not fixed this pass

`blood_bank`/`critical_care` confirmed already safe (see above).
`command_center` and `public_health` have the same "zero `_safely`
convention, zero existing tests" shape as biomedical did — not yet
individually audited; flagged as the next candidates in
`MUSTAFA_ACTIVE_REPAIR_QUEUE.md`.
