# Payments — Cash Capture / Refund Concurrency Guard (CAS)

**Domain selected via evidence-based discovery**, following the same method
already established in this repair queue (`ems-domain-discovery`,
`nhdw-admission-vertical-slice`): `app/payments/` (`pay_*` tables) is a
LIVE, unconditionally-registered domain (5 routers wired in
`app/factory.py`) backed by 5 real migrations
(`20260812_0002_gula_health_payments_foundation.py` and siblings), not
touched by this session or by Abu Ali's recent commits
(`care_continuum`/`ehr`/`identity`/`national`/`national_data`/
`orm_topology.py`/`trust`), and structurally different from the
schema-only `app/financial/` package (`ENABLE_FINANCIAL_ENGINE`-gated,
off-limits per `CLAUDE.md`) — `payments` has no feature gate and is live
in production today.

## Role-gate and tenant-scope audit — CLEAN

Every mutating route across all 5 files (`routes.py`, `control_routes.py`,
`fx_routes.py`, `orchestration_routes.py`, `subscription_routes.py`) already
has `Depends(require_permission(...))` plus `assert_institution_access(...)`
tenant-scope enforcement on every institution-scoped resource. No role-gate
or BOLA gap was found — this domain was already at the same maturity level
Laboratory/Imaging/EMS/Nursing/NHDW reached only after their own audits.

## Finding — P0 (proven): no concurrency guard on money-mutating rows

`grep -rn "with_for_update" app/payments/` returned **zero matches across
the entire package**. `capture_cash`, `close_cash_shift`, `approve_refund`,
and `process_cash_refund` in `app/payments/service.py` each read a
`PaymentIntent`/`CashShift`/`PaymentRefund`/`PaymentInvoice` row with a
plain, unlocked `SELECT`, then mutated it — the exact TOCTOU shape already
fixed five times this session (`lab-slice-cancel-order-cas`,
`lab-slice-device-ingestion-cas`, `imaging-slice-order-status-cas`,
`ems-ambulance-status-cas`, `nhdw-admission-vertical-slice`'s CAS rows) —
except here the race produces duplicated real-money ledger postings, not
just a clinical status flip.

None of `PaymentIntent`/`CashShift`/`PaymentRefund`/`PaymentInvoice` has a
`version` column, so — matching the established precedent from
`lab-slice-sample-version-column` (no schema change, reuse existing
concurrency primitives) — the fix uses `SELECT ... FOR UPDATE` (pessimistic
row locking), zero schema risk, zero migration.

## REAL POSTGRESQL PROOF (both directions)

Two independent race scripts, each using two genuine Python threads with
**separate SQLAlchemy sessions/connections** against a real disposable
PostgreSQL 16 database (`gula_pay_race`), synchronized with a
`threading.Barrier` so both threads reach the mutation path together:

### 1. Double cash capture (`capture_cash`)

| | Pre-fix (stashed) | Post-fix (restored) |
|---|---|---|
| Thread results | both `("ok", <different attempt ids>)` | both `("ok", <same attempt id>)` |
| SUCCEEDED `PaymentAttempt` rows for the intent | **2** | 1 |
| Ledger `CASH_ON_HAND` debit lines / total | **2 / $200.00** | 1 / $100.00 |
| Invoice total | $100.00 | $100.00 |

A single $100 CASH payment intent was captured twice concurrently,
posting **$200 to the general ledger's cash account** against a $100
invoice.

### 2. Double refund payout (`process_cash_refund`)

| | Pre-fix (stashed) | Post-fix (restored) |
|---|---|---|
| Thread results | both `("ok", "SUCCEEDED")` | one `("ok", "SUCCEEDED")`, one `("error", "PaymentStateError: Only approved refunds can be processed")` |
| Ledger `REFUNDS_AND_ALLOWANCES` debit lines / total | **2 / $200.00** | 1 / $100.00 |

A single approved $100 refund was processed twice concurrently, posting
**$200 in refund payouts** for a $100 paid invoice.

## Negative proof (both races)

For each race: the fix was `git stash`ed (byte-identical revert, confirmed
via `md5sum` before/after), the race reproduced against the pre-fix code,
then `git stash pop` restored the fix (re-confirmed byte-identical via
`md5sum` against a separate backup copy) before re-running the same race,
which no longer reproduces.

## FIX

`app/payments/service.py`: `_intent`/`_invoice`/`_refund`/`_cash_shift`
gained a `for_update: bool = False` keyword (default preserves existing
read-only call sites unchanged — `get_invoice`, `list_payment_providers`,
etc. never lock). `capture_cash` now locks the intent, cash shift, and
invoice; `close_cash_shift` locks the shift; `approve_refund` locks the
refund; `process_cash_refund` locks the refund, cash shift, and invoice;
`request_refund` locks the intent (closes a secondary race where two
concurrent refund *requests* against the same intent could each pass the
"amount does not exceed remaining refundable balance" check against a
stale `reserved` aggregate, since each creates an independent `PaymentRefund`
row that would later be locked individually at approval/processing time —
the intent-level lock now serializes refund-amount reservation itself).

## REGRESSION

```
tests/identity/ tests/test_migrations.py tests/test_migration_resilience.py
tests/test_payments_foundation.py tests/test_payment_orchestration.py
tests/test_payments_route_registration.py
  → 306 passed, 4 skipped, zero failures (Python 3.12 venv, matching this
    repo's actual runtime; the ambient `python` in this shell resolves to
    3.11 and cannot even import `app.identity.repositories.base`'s PEP 695
    generic syntax — an unrelated, pre-existing environment quirk, not a
    regression from this change)
```

Two new permanent regression tests added to `tests/test_payments_foundation.py`:
- `test_capture_cash_money_lookups_are_row_locked` — asserts the
  money-mutating lookups compile to real `SELECT ... FOR UPDATE` against
  the production (PostgreSQL) dialect. Negative-proofed: fails with
  `TypeError: PaymentService._intent() got an unexpected keyword argument
  'for_update'` against the pre-fix code.
- `test_concurrent_capture_is_idempotent_not_duplicated` — pins the
  single-connection idempotency contract the lock now makes race-proof.

SQLite (this suite's default) cannot reproduce the underlying race itself
(single-writer locking masks it, which is exactly why the existing suite
never caught this bug) — the two real-Postgres scripts above are the
actual proof; the SQLite tests pin the code-level guarantee.

## SCOPE NOTE — not fixed this pass, documented

The same zero-`with_for_update()` gap exists in the sibling
`control_service.py` (financial-control approval workflow),
`fx_service.py` (FX rate/quote/fee-policy management),
`orchestration_service.py` (payment-rail/routing-rule config), and
`subscription_service.py` (institutional billing cycles). None of these
move cash directly the way `capture_cash`/`process_cash_refund` do — a
duplicate-apply race there is a governance/workflow-integrity issue (same
tier as the already-documented `governance.submit_appeal` P2), not a
direct double-money-movement defect — so they were not fixed in this
bounded pass. If prioritized, the identical `for_update=True` pattern
applies directly; no new mechanism needed.

## Status

**FIXED — VERIFIED** (real-Postgres-proven, both directions, negative-proofed, zero regressions)
