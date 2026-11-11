# Evidence — what a failing protected clinical command leaves behind

**Executed:** 2026-09-25 · **Packet:** WP-002 (P0) · **Claimed by:** ABU_ALI
**Evidence:** REAL_HTTP_POSTGRES at canonical head `20260909_0001` + STATIC ratchet
**Result:** NR-024 root-caused and split; **NR-033 opened**; FM-026 executed

## Environment

| Field          | Value                                                                                                       |
| -------------- | ----------------------------------------------------------------------------------------------------------- |
| Database       | `gula_canon`, PostgreSQL 16, built by migrations alone to `20260909_0001`, 423 tables                       |
| Schema lineage | `claude/p0-1-hospital-migrations` @ `efcc4b6e` — the only chain on which head builds                        |
| App code       | `app/clinical/` is **byte-identical** between that lineage and this branch (`git diff` empty)               |
| Tests          | `test_clinical_failure_trace.py` **8 passed** · `test_guard_reject_coverage.py` **3 passed** (static, 0.4s) |

## What NR-024 said, and what is actually true

NR-024 recorded: _a failing protected clinical command writes no receipt and no audit
row_, because `guard.reject` writes to the database that just refused the statement —
"the failure path shares its dependency with the thing it guards."

That explanation is **wrong**, and the finding splits in two. Both halves were
established by execution, and the second is the control that makes the first mean
something.

### (a) Six blood bank commands have no rejection path at all — NR-033

An AST census over **all 36** guarded commands:

| Domain        | claim | complete | reject | commands with **no** reject |
| ------------- | ----- | -------- | ------ | --------------------------- |
| blood_bank    | 13    | 13       | 7      | **6**                       |
| critical_care | 8     | 8        | 8      | 0                           |
| lims          | 7     | 7        | 15     | 0                           |
| radiology     | 4     | 4        | 4      | 0                           |
| pharmacy      | 2     | 2        | 2      | 0                           |
| ems           | 1     | 1        | 1      | 0                           |

The six: `blood.reservation.create`, `blood.reservation.release`,
`blood.sample.create`, `blood.reaction.create`, `blood.return.create`,
`blood.discard.create`. Their `except` branch is
`db.rollback(); _raise_blood_error(exc); raise` — it rolls back and re-raises
without recording anything.

Measured on `POST /blood-bank/reservations` with a failure injected at
`after_business_effect`:

| Observation          | Result                 |
| -------------------- | ---------------------- |
| HTTP status          | ≥ 400                  |
| Rejection audit rows | **0**                  |
| Receipts             | **0**                  |
| Clinical effect      | **0** — clean rollback |
| Audit-failure metric | **0**                  |

So the guard's fallback is not fragile here. It is **unreachable**, because the code
that would call it does not exist. Blocking the audit table is not even needed to
show the gap.

### (b) Where a rejection path does exist, the fallback fires — and masks the reason

**Positive control.** Without this, "no counter incremented" is equally consistent
with a broken counter, a broken trigger, or a metrics singleton imported twice.

The ICU verify route **does** call `guard.reject`. Driven into a real clinical
refusal (the initiator verifying their own high-alert infusion) while a
`BEFORE INSERT` trigger makes the database refuse audit rows:

| Observation                     | Result                                                 |
| ------------------------------- | ------------------------------------------------------ |
| Audit-failure counter           | **incremented** — the fallback works                   |
| Clinical reason in the response | **absent** — replaced by the audit failure             |
| Durable state                   | unchanged: `awaiting_verification`, `verified_by` NULL |

That isolates the cause exactly: **the blood bank gap is a missing rejection path,
not a broken fallback.** And it executes **FM-026 (masking)** for the first time —
`reject()` re-raises after incrementing, so the caller is told the audit write
failed rather than why the clinical command was refused.

Two secondary facts, both read from the objects rather than the source:

- `log_action` **does** `db.flush()` inside the guard's `try`, so the `except` branch
  is genuinely reachable. The shared-dependency theory fails on this point.
- `record_audit_failure` increments an **in-memory dict behind a lock**
  (`app/clinical/observability.py`). It is per-process and per-worker, does not
  survive a restart, and is not in the audit trail. "A metric was recorded" reads
  like durable evidence and is not.

## Per-stage census

For each stage the reservation path reaches, a failure was injected and the surviving
trace measured. Every stage left _something_ (a receipt, an audit row, or a metric) —
the assertion is deliberately weak on form and strong on existence, because a
clinical command failing with no trace at all is what NR-024 is about.

`after_commit` is the interesting one: it fires **after** `db.commit()`, so the
reservation is durable and the success **is** audited (asserted: exactly one success
row). On this route no rejection row follows, because the route has no reject path —
so no contradictory pair arises here. Whether a route that has _both_ can record a
rejection for an effect that committed is **NOT_TESTED**.

## Negative proofs

| Mutation                                        | Expected                       | Observed                                                                            |
| ----------------------------------------------- | ------------------------------ | ----------------------------------------------------------------------------------- |
| Drop one operation from the ratchet baseline    | "no new gap" must fail         | **2 failed**                                                                        |
| Add an operation that _does_ have a reject path | "exactly six" must fail        | **1 failed**                                                                        |
| Truncate the module list the census reads       | the positive control must fail | **failed** — _"only 13 guarded operations found; the ratchets above prove nothing"_ |
| Restore                                         | all must pass                  | **3 passed**                                                                        |

The third is there because a sweep over an empty list passes vacuously; the census
asserts the size of the surface it found.

## Scope

- **VERIFIED:** the six-command gap, its root cause, the working fallback on routes
  that have a reject path, the in-memory nature of that fallback, and FM-026 masking.
- **NOT_TESTED:** a rejection recorded for an effect that already committed on a route
  that has both paths; and injection-based rollback for ICU, since `critical_care`
  has **no** `maybe_fail` call site.
- **Not fixed:** adding a rejection path changes what a refused clinical command
  returns, which is a clinical response contract and the owner's decision — NR-033.
  A ratchet prevents a seventh appearing silently.
