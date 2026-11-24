# Devices — Outbox Claim Concurrency Guard (CAS)

**Domain selected via evidence-based discovery**, continuing the master
directive's execution queue after `payments`: `app/devices/` (`device_*` /
`wearable_*` tables) is LIVE, unconditionally registered
(`app/factory.py:652`, no feature gate), backed by 6 dedicated migrations
(`device_integration`, `device_adapter_registry`,
`device_monitoring_alerting`, `device_tenant_isolation`, `device_outbox`,
`device_gateway_registry`) plus `wearable_measurements`, not touched by
this session or by Abu Ali's recent commits.

## Role-gate and tenant-scope audit — CLEAN

Every mutating route in `app/devices/routes.py` requires
`Depends(require_institutional_permission("lab:manage"))` (writes) or
`"lab:read"` (reads), and every service call is scoped by `actor.lab_id`.
`ingest_wearable_measurement`/`list_wearable_measurements`/
`clinician_baseline_summary` correctly validate `Patient.id ==
payload.patient_id AND Patient.lab_id == lab_id` before touching any
wearable data — no BOLA: a caller cannot read or write measurements for a
patient outside their own lab, even by guessing a valid `patient_id`.

## Finding — P0 (proven): outbox claim has no concurrency guard

`app/devices/outbox.py::process_batch` — the transactional-outbox worker
reachable via `POST /device-integration/outbox/process` — read "due"
messages with a plain, unlocked `SELECT` before marking them `"processing"`
and invoking the dispatcher. Since GULA runs multiple backend replicas in
production (`make scale REPLICAS=N`, `docker-compose.scale.yml`), two
concurrent calls to this endpoint (e.g. two replicas each triggered by an
external cron, or one manual + one scheduled call) can both claim and
dispatch the **same** message.

Proven against two real threads with separate DB connections on a real
disposable PostgreSQL 16 database: both threads claimed the identical
outbox message and the dispatcher was invoked twice
(`dispatch_calls: [1, 1]`). The current default dispatcher only simulates
delivery (no real socket), so today's actual blast radius is limited to a
duplicated `attempts` bump — but this worker is explicitly documented as
exercising "durable queue semantics" ahead of real device-command
dispatch (`outbox.py`'s own module docstring), so the double-dispatch bug
is real and would directly duplicate a physical device command (e.g. a
printer job, a gateway config push) the moment a real dispatcher is wired
in — the same class of P0 already closed 6 times this session
(`lab-slice-*-cas`, `imaging-slice-order-status-cas`,
`ems-ambulance-status-cas`, `nhdw-admission-vertical-slice`'s CAS rows,
`payments-capture-refund-cas`).

`DeviceOutboxMessage` has no `version` column, so — matching precedent —
fixed with row locking: `.with_for_update(skip_locked=True)` on the claim
query (the idiomatic outbox-pattern primitive: each concurrent worker
skips rows another worker already claimed, rather than blocking on them,
which is the correct behavior for a batch dispatcher). Zero schema change.

## REAL POSTGRESQL PROOF

Two real threads, separate SQLAlchemy sessions/connections, against
`gula_pay_race` (disposable PostgreSQL 16), synchronized with a
`threading.Barrier`, dispatching one queued message:

| | Pre-fix (stashed) | Post-fix (restored) |
|---|---|---|
| `dispatch_calls` (message ids the dispatcher was invoked for) | `[1, 1]` | `[1]` |
| Thread results | both `processed: 1, delivered: 1` | one `processed: 1, delivered: 1`, one `processed: 0` (its claim query returned nothing — the row was already locked and skipped) |
| Final message status/attempts | `delivered` / `1` (last-writer-wins on the unlocked `attempts` counter, masking that dispatch itself ran twice) | `delivered` / `1` |

## Negative proof

`git stash`ed the fix (byte-identical revert, `md5sum`-confirmed), reproduced
the race, `git stash pop` restored the fix (re-confirmed byte-identical),
re-ran — no longer reproduces.

## REGRESSION

```
tests/identity/ tests/test_migrations.py tests/test_migration_resilience.py
tests/test_device_outbox.py
  → 301 passed, 4 skipped, zero failures (Python 3.12 venv, this repo's
    actual runtime)
```

New permanent regression test in `tests/test_device_outbox.py`:
`test_outbox_claim_query_is_row_locked_with_skip_locked` — spies on
`sqlalchemy.orm.Query.with_for_update` to confirm `process_batch`'s own
claim query (not a separately-constructed lookalike) calls it with
`skip_locked=True`. Negative-proofed: fails with `AssertionError:
process_batch's claim query must call Query.with_for_update()` against
the pre-fix code.

## SCOPE NOTE — documented, not fixed this pass

`ingest_wearable_webhook` (`routes.py`) authenticates with a single
**global** per-provider HMAC secret (`GULA_WEARABLE_WEBHOOK_SECRET_*`),
not a per-lab secret, and trusts the webhook envelope's own `lab_id`
field. A holder of that shared secret could attribute a measurement to an
arbitrary `lab_id`/`patient_id` pair (cross-tenant data injection) —
constrained today to `simulation_only=True` payloads only (the route
hard-rejects any non-simulation payload with 409, and
`ingest_wearable_measurement` separately re-validates the patient belongs
to the declared lab, so this cannot leak or corrupt real clinical data
yet). Same severity tier as the already-documented `ai-approval-no-tenant`
P2 — real but capped, and closing it (per-lab webhook secrets, or signing
the `lab_id` itself into the HMAC) is a genuine design decision, not
something to invent unilaterally in a CAS-focused pass.

## Status

**FIXED — VERIFIED** (real-Postgres-proven, negative-proofed, zero regressions)
