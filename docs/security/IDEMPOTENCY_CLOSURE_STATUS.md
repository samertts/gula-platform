# Idempotency Closure Status

Bounded Phase-2 pass: inventory every idempotency mechanism found in the
repo, classify each (ACTIVE / DORMANT / DEAD / DUPLICATE / CANONICAL /
VULNERABLE / UNKNOWN), and specifically resolve the previously-flagged
`app/core/idempotency.py` (whether it has callers, per this directive's
explicit instruction not to repair or delete it before checking).

## Mechanisms found

### 1. `app/clinical/command_guard.py::ClinicalCommandGuard` — **ACTIVE, CANONICAL, VERIFIED SAFE**

The real, production idempotency mechanism for clinical state-changing
commands. Used by 7 domains: `radiology`, `critical_care`, `lims`,
`blood_bank`, `pharmacy`, `ems`, `hospital` (`app/routes/hospital.py`).

- **Mechanism**: `claim()` inserts a `ClinicalCommandReceipt` row scoped
  by `(lab_id, actor_user_id, operation, idempotency_key)`, backed by a
  real DB unique constraint. If the flush raises `IntegrityError`
  (a concurrent request won the race), the guard rolls back and returns
  `409 clinical_command_in_progress_or_complete` — the claim is
  genuinely atomic, not a check-then-insert race.
- Same key reused with a **different payload** (fingerprint mismatch) is
  explicitly rejected (`idempotency_key_reused`), not silently replayed.
- The docstring states the required contract explicitly: "Callers must
  keep `claim` and `complete` in the same database transaction as the
  state write" — this is the transaction-boundary invariant Phase 3
  asks about, already documented at the source.
- **Already proven** by `tests/blood_bank/test_failure_injection_postgres.py`
  (9 tests, re-run this session against a genuinely head-migrated real
  Postgres 16 database as part of the Biomedical/Blood-Bank audit,
  32/32 passed including the blood_bank suite) — covers failure-after-claim,
  failure-after-business-effect, failure-after-inventory-movement, and
  failure-after-audit-preparation, each asserting the rolled-back attempt
  leaves no orphan and a same-key retry succeeds exactly once.
- **Disposition: VERIFIED SAFE.** No change needed.

### 2. `app/core/idempotency.py::idempotency_check` — **DORMANT, and VULNERABLE-IF-ACTIVATED**

A generic, header-based (`Idempotency-Key`) FastAPI dependency, backed by
a separate `idempotency_keys` table (real migration:
`20250322_0000_create_base_schema.py`).

**Caller check (as this directive explicitly requires before touching
it)**: grepped the entire repo for any import of this module. **Zero
call sites anywhere** — not one route in `app/routes/`, nor any
`*/api/routes.py`, imports or depends on `idempotency_check`. The only
reference in the whole repository is its own isolated unit test
(`tests/test_idempotency.py`). Its own module docstring even lists 4
routes it claims to protect (`POST /api/orders`, `/api/results`,
`/api/results/{id}/validate`, `/api/samples`) — none of them actually
declare `Depends(idempotency_check)`. **Disposition: DORMANT** — built,
migrated, tested in isolation, never wired to a live endpoint.

**Not repaired or deleted**, per this directive's explicit instruction.
Documented instead, including a latent defect found while reading it:

**VULNERABLE-IF-ACTIVATED**: the "new key" path does:
```python
db.execute(text("INSERT INTO idempotency_keys (...) VALUES (...) ON CONFLICT (key) DO NOTHING"))
db.flush()
...
return IdempotencyResult(is_duplicate=False, ...)
```
It never checks whether *this* request's own `INSERT` actually won the
`ON CONFLICT` race (no `rowcount` check, no `RETURNING`). Two concurrent
requests presenting the same **never-before-seen** key would both read
"no existing row" in the preceding `SELECT`, both attempt the insert
(one silently no-ops due to the conflict), and **both** still return
`is_duplicate=False` — both would proceed to execute business logic and
both would later call `.cache()`, defeating the exact guarantee
idempotency exists to provide. This is the identical root-cause shape as
the 6 concurrency defects already closed this session (unlocked
check-then-act), here in the module the directive specifically asked
about. **Not fixed this pass** — the module has no live caller, so there
is no reachable vulnerability today; fixing dead code would be exactly
the "broaden scope without a live defect" this directive's own success
condition warns against. Recorded so it is never fixed-by-assumption
or wired into a route without first closing this gap (check
`result.rowcount == 1` after the insert, and only return
`is_duplicate=False` when it does; otherwise re-query and either return
the winner's cached response or fail closed with 409).

### 3. `app/payments/models.py::PaymentIntent.idempotency_key` — **ACTIVE, VERIFIED SAFE**

Real DB `UniqueConstraint("institution_id", "idempotency_key")`, used by
`create_intent`. Already audited this session (`payments-capture-refund-cas`)
— the intent-creation race is closed at the DB constraint level; the
capture/refund CAS fix this session closes the separate concurrency gap
downstream of intent creation. No new finding here.

### 4. `app/devices/outbox.py::enqueue_message` — **ACTIVE, VERIFIED SAFE**

Real DB `UniqueConstraint("lab_id", "idempotency_key")` on
`DeviceOutboxMessage`, with an explicit same-key-different-envelope
rejection (`ValueError`), matching the `ClinicalCommandGuard` contract
shape. Already audited this session (`device-outbox-claim-cas`).

### 5. `app/services/outbox_service.py::OutboxWorker` — **ACTIVE, CANONICAL**

Not itself a client-facing idempotency key, but the platform's durable
at-least-once delivery mechanism (already classified `VERIFIED SAFE` in
`docs/security/SYSTEMIC_CONCURRENCY_FINDINGS.md`).

### 6. `app/kernel/event_bus/outbox.py::OutboxPattern` — **DEAD**

Already classified this session — race-shaped but its claim methods have
zero call sites. No idempotency-key concept at all (in-memory only).

### 7. `app/capabilities/*/commands/*.py` (46 files, 9 of 10 sub-packages) — **DEAD, newly discovered this pass**

While searching for other "dedup/command_id/claim" idempotency patterns,
found a large, previously-uncounted command-pattern architecture under
`app/capabilities/`: `clinical_foundation`, `document_management`,
`encounter_management`, `healthcare_consent`, `provider_management`,
`reporting_service`, `search_service`, `storage_service`,
`workflow_engine` — each has its own `routes.py` and a `commands/`
subpackage. **Only `fhir_interoperability`'s router is ever imported by
`app/factory.py`** — grepped exhaustively for any reference to the other
9 routers' modules from anywhere in the codebase: zero. These 9
sub-packages (46 command files + 9 unmounted `routes.py` files) are
entirely unreachable over HTTP. This corrects
`docs/architecture/LIVE_RUNTIME_SURFACE_MAP.md`'s earlier
`LIVE / NO-OWNED-MODELS` bucket for `capabilities` — it should not be
counted as "needs per-router confirmation," it is now confirmed DEAD for
9 of its 10 routers. Whatever idempotency conventions those command
files use internally were not audited (dead code, out of scope per this
directive's own "do not broaden scope" instruction), beyond confirming
they are unreachable.

## Idempotency contract, stated once (per this directive's instruction to document the contract before choosing semantics)

Where idempotency is enforced in this codebase (`ClinicalCommandGuard`,
payments, devices outbox), the contract is uniform:

> Same logical operation + same scope (`lab_id`/`institution_id`) + same
> idempotency key → the first request's side effect is claimed
> atomically via a real DB uniqueness constraint (not a check-then-insert
> race); a genuine concurrent duplicate is rejected with `409`, not
> silently replayed with a cached body (none of the three ACTIVE
> mechanisms actually implement response replay today — `ClinicalCommandGuard`
> and the outbox implementations reject the duplicate outright;
> `app/core/idempotency.py`, the one that *does* implement response
> replay/caching, is the one that's unreachable). Same key + different
> payload is always rejected explicitly, never silently overwritten.

## Disposition summary

| Mechanism | Status |
|---|---|
| `ClinicalCommandGuard` | VERIFIED SAFE (ACTIVE, CANONICAL) |
| `app/core/idempotency.py` | DORMANT — documented, not fixed (no live caller); latent VULNERABLE-IF-ACTIVATED race recorded for whoever wires it up next |
| Payments `PaymentIntent.idempotency_key` | VERIFIED SAFE (ACTIVE) |
| Devices `DeviceOutboxMessage.idempotency_key` | VERIFIED SAFE (ACTIVE) |
| `outbox_service.py` | VERIFIED SAFE (ACTIVE, CANONICAL) |
| `kernel/event_bus/outbox.py` | DEAD |
| `app/capabilities/*` (9 of 10 routers) | DEAD — newly discovered, corrects the live-surface map |

## Not done this pass

Per-LIVE-endpoint idempotency-requirement determination (Phase 2's full
questionnaire: "is idempotency required for every live mutating
endpoint?") was not performed exhaustively across all ~23 confirmed
table-backed domains — only the mechanisms actually present were
inventoried and classified. A full per-endpoint idempotency-necessity
audit (order creation, sample creation, dispensing, transfusion,
appointments, referrals, certificates, API keys, external integrations)
is a separate, larger pass, recorded as NOT STARTED in
`docs/security/NEXT_CLOSURE_BASELINE.md`.
