# Evidence — Recovery under database interruption

**Generated:** 2026-09-25 · **Packet:** WP-005 · **Claimed by:** ABU_ALI ·
**Evidence level:** RECOVERY_PROOF (real PostgreSQL, canonical head)

`FAILURE_MODES.md` recorded eight modes with **no mechanism at all** — FM-010 to
FM-013 and FM-022 to FM-025. That was never a claim that recovery is broken; the
platform ships a circuit breaker, a degraded mode and an auto-repair engine. It was
an admission that nothing in this repository could say either way. This closes two of
the eight, by execution.

## Environment

| Field                | Value                                                                                     |
| -------------------- | ----------------------------------------------------------------------------------------- |
| Database             | `gula_recovery`, PostgreSQL 16, created empty then `alembic upgrade head` → **exit 0**    |
| Schema source        | migrations only — **0 probe-created tables**                                              |
| Stamp                | `20260909_0001` (canonical head) · 423 tables                                             |
| Schema provenance    | `claude/p0-1-hospital-migrations` @ `efcc4b6e`, the only chain on which head is buildable |
| Operation under test | `POST /blood-bank/reservations` → `blood.reservation.create`                              |
| Tests                | `backend/tests/verification/test_recovery_proof.py` — **3 passed**                        |

Why the blood bank and not the ICU infusion: `critical_care_infusions` is unreachable
on any branch an operator can build today (NR-023/NR-028), whereas the blood bank's
seventeen tables match their ORM exactly at head. Recovery is a platform property, so
it is proven on a path that actually exists.

## R1 — INV-TXN-01 across an interruption, not an exception

A guarded claim and a unit state change were written and flushed, then the writing
backend was destroyed from an independent connection with `pg_terminate_backend`.

This is materially different from the exception path already covered. An exception
runs the route's `except` branch and its `rollback`; a terminated backend runs
**neither**. The guarantee therefore has to come from the database, and this is what
shows that it does.

| Assertion                                  | Result                                                     |
| ------------------------------------------ | ---------------------------------------------------------- |
| The writer backend was actually terminated | `pg_terminate_backend` returned `true`                     |
| The dead connection refuses further work   | `OperationalError` — named precisely, not bare `Exception` |
| Receipts for that idempotency key          | **0**                                                      |
| Unit status / version                      | `available` / `1` — unmoved                                |
| Reservations                               | **0**                                                      |

## R2 — INV-IDEM-01, INV-AUDIT-01 and INV-AUDIT-02 across a real process restart

A reservation was created through HTTP (201), then the PostgreSQL cluster was
**actually restarted** (`pg_ctlcluster 16 main restart`), then every invariant was
re-asserted through a brand-new engine so nothing could be answered from a pooled
connection or a stale identity map.

| Assertion                                      | Result                                          |
| ---------------------------------------------- | ----------------------------------------------- |
| Database returns                               | `SELECT 1` succeeds                             |
| Reservation rows                               | identical before and after, byte for byte       |
| Unit status                                    | still `reserved`                                |
| Idempotency receipt                            | identical before and after                      |
| **Replay with the same key after the restart** | **refused** — and still exactly one reservation |
| Audit rows                                     | count not decreased                             |
| Append-only trigger                            | still refuses `DELETE` after the restart        |

The replay is the clinically important one. Had the receipt not survived, the retry a
client sends after an outage would reserve **the same unit of blood a second time**.

Restarting a cluster is destructive to every database on the instance, so the test is
gated behind `GULA_RECOVERY_ALLOW_DB_RESTART=1` — the same shape as
`failure_injection`'s gate. Without the gate it reports that it did not run. A skip
there is **not** evidence that recovery works, and the skip reason says so.

## Negative proofs

Both executed; an assertion that cannot fail proves nothing.

| Mutation                                             | Expected      | Observed                                                               |
| ---------------------------------------------------- | ------------- | ---------------------------------------------------------------------- |
| `commit()` before the kill, so the effect is durable | R1 must fail  | **failed**                                                             |
| Delete the receipt after the restart                 | R2 must fail  | **failed** — `the idempotency receipt did not survive the restart: []` |
| Restore both                                         | all must pass | **3 passed**                                                           |

## Two defects found in this test while building it

Recorded because both would have produced a test that passed while proving nothing:

1. The receipt `INSERT` was written against a guessed schema — `clinical_command_receipts`
   has no `updated_at`, and `id` is a sequence. Corrected from `information_schema`.
2. `harness.client()` was called without `with`. Entering the TestClient is what runs
   the app lifespan and therefore the startup guard; without it `ReadinessMiddleware`
   answers **every** request with 503. The first run returned 503 and would have been
   easy to mistake for a route problem. The ICU slice already used `with`, so that
   mechanism was reused rather than a second one invented.

## Scope — what is still NOT proven

| Mode                            | Status       |
| ------------------------------- | ------------ |
| FM-010 database disconnect      | **VERIFIED** |
| FM-011 database process restart | **VERIFIED** |
| FM-012 dependency timeout       | NOT STARTED  |
| FM-013 dependency 500           | NOT STARTED  |
| FM-022 retry storm              | NOT STARTED  |
| FM-023 stale cache              | NOT STARTED  |
| FM-025 out-of-order event       | NOT STARTED  |

`INV-RECOVERY-01` is therefore **VERIFIED for database interruption and database
restart** and remains unproven for application-service restart and dependency
failure. It is deliberately not recorded as a blanket "recovery verified".

One conditionality is explicit: the schema came from an **unmerged** branch, because
no merged branch can build head. The recovery behaviour proven here is a property of
PostgreSQL and the guard, not of that branch — but the evidence cannot be reproduced
on `main` until the NR-003/NR-028 chain lands.
