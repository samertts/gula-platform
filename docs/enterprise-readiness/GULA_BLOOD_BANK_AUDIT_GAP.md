# Blood Bank Audit Coverage — NR-027

**Batch:** BATCH-2.6
**Status:** the finding as recorded in BATCH-2.5 was **substantially wrong** and
is corrected here. The canonical paths were already audited.

---

## 1. The correction

BATCH-2.5 recorded NR-027 as *"No Blood Bank mutation writes an audit log
entry"*, on this evidence: a search for `audit` across
`backend/app/blood_bank/application/service.py` returns nothing.

The search result was accurate. The conclusion did not follow. **The audit write
lives in the route layer, not the service layer.** Every guarded Blood Bank
route calls `ClinicalCommandGuard.complete()`, and that method calls
`log_action(...)` into the SHA-256 hash-chained `audit_logs` table — with the
actor, tenant, resource, state transition, both versions, the idempotency key
and a reason — inside the caller's transaction.

I generalised from one file to a domain. The lesson is the same one NR-021 and
NR-018 each taught: a negative result in one module is not a negative result for
the system.

## 2. Measured coverage

Twenty-one mutating routes in `backend/app/blood_bank/api/routes.py`:

| Coverage | Routes |
|---|---|
| Clinical command receipt **and** hash-chained audit entry | **13** |
| Neither | **8** (one of which, `POST /crossmatch/check`, mutates nothing) |

So the real gap is **7 mutating routes**, not 21:

```
POST /donors                        register_donor
POST /donors/{donor_id}/defer       defer_donor
POST /donations                     register_donation
POST /donations/{id}/complete       complete_donation
POST /components                    process_component
POST /requests                      create_blood_request
POST /samples/{id}/transition       transition_patient_blood_sample
```

These are the donor/donation/component/request paths — the legacy generation.
The canonical `*_safely` transfusion, issue, crossmatch, reservation, reaction,
return and discard paths are all in the covered 13.

## 3. What the covered path actually records

`ClinicalCommandGuard.complete()` writes an `audit_logs` row containing:

| §8 requirement | Where it lands |
|---|---|
| actor | `user_id` (Integer, from `current_user.id`) |
| tenant | `lab_id` |
| entity | `resource_type` |
| entity ID | `details.resource_id` (string; the column is Integer) |
| action | `action = "clinical.<operation>"` |
| previous state | `details.state_before` |
| new state | `details.state_after` |
| reason / context | `details.reason`, `details.version_before/after` |
| timestamp | `created_at` |
| correlation / idempotency | `details.idempotency_key` |

`details` is inside the chain-hash preimage, so the string identifiers and the
state transition are tamper-evident even though the typed columns cannot hold
them.

## 4. The four properties §8 requires, proven

`backend/tests/blood_bank/test_audit_chain_coverage.py`, against PostgreSQL:

| Property | Test | Result |
|---|---|---|
| one mutation → one clinical effect **and** exactly one audit event | `test_one_mutation_writes_one_effect_and_one_audit_event` | PASS |
| the entry is chained, tenant-scoped, actor-attributed, and carries the transition | same test | PASS |
| idempotent replay adds no second audit event | `test_idempotent_replay_adds_no_second_audit_event` | PASS |
| a failure rolls back the effect and the audit entry together | `test_failure_rolls_back_the_effect_and_the_audit_event_together` | PASS |

Replay safety is structural rather than incidental: `guard.claim()` rejects a
reused idempotency key *before* `complete()` is reached, so a replay cannot
produce a second audit row by construction.

## 5. Two facts the tests surfaced

- **`audit_logs` is genuinely append-only.** A PL/pgSQL trigger
  (`audit_logs_deny_mutation`) rejects `DELETE` and `UPDATE`. The first version
  of these tests tried to clean up after themselves and was refused by the
  database. They now measure the rows a command *adds*, above a watermark, and
  never touch the chain. That refusal is the control working.
- **`AuditLog.resource_id` and `user_id` are `Integer`.** Blood Bank identifiers
  are `String(26)`/`String(100)`. The string identity therefore lives in
  `details` rather than in the typed column. This is a real modelling
  limitation, not a defect in the Blood Bank: it is the same identity split
  recorded in the National Core identity contract.

## 6. Corrected status

**NR-027 — PARTIALLY VERIFIED.**

- Canonical `*_safely` mutation paths: **VERIFIED** — audited, chained,
  transactional, replay-safe, proven by test.
- Seven legacy mutating routes: **OPEN** — no receipt and no audit entry.

## 7. Not done, and why

The seven uncovered routes are the legacy generation described in
`GULA_BLOOD_BANK_LEGACY_BYPASS.md`. Bringing them under the guard means giving
each an idempotency key and a precondition contract — a behavioural API change
on live endpoints, not an audit wiring change. BATCH-2.6 authorises the
canonical paths only, and those needed no change.

`process_component` is the one of the seven that is both reachable and
state-changing; it is the natural first candidate when that work is authorised.

---

# BATCH-2.7 — The seven routes, classified

Every one is authenticated and carries the router-level
`require_permission("system:admin")`. None takes a row lock, calls
`transition()`, or writes an audit record.

| Route | Handler | Service method | Tenant | Lock | State machine | Audit | Idempotency | Class |
|---|---|---|---|---|---|---|---|---|
| `POST /donors` | `register_donor` | `register_donor` | `_owned` ✓ | ✗ | ✗ | ✗ | ✗ | **ACTIVE_LEGACY** |
| `POST /donors/{id}/defer` | `defer_donor` | `defer_donor` | ✓ | ✗ | ✗ | ✗ | ✗ | **ACTIVE_LEGACY** |
| `POST /donations` | `register_donation` | `register_donation` | `_owned` ✓ | ✗ | ✗ | ✗ | ✗ | **ACTIVE_LEGACY** |
| `POST /donations/{id}/complete` | `complete_donation` | `complete_donation` | ✓ | ✗ | ✗ | ✗ | ✗ | **ACTIVE_LEGACY** |
| `POST /components` | `process_component` | `process_component` | `_owned` ✓ | ✗ | ✗ | ✗ | ✗ | **ACTIVE_LEGACY** |
| `POST /requests` | `create_blood_request` | `create_blood_request` | **was ✗ — fixed** | ✗ | ✗ | ✗ | ✗ | **ACTIVE_LEGACY** |
| `POST /samples/{id}/transition` | `transition_patient_blood_sample` | `transition_patient_sample` | ✓ | ✓ | ✓ | ✗ | **required, not claimed** | **ACTIVE_CANONICAL (incomplete)** |
| *(`POST /crossmatch/check`)* | `check_blood_compatibility` | — | n/a | n/a | n/a | n/a | n/a | **non-mutating — not in scope** |

## Two defects this classification found

**`POST /requests` wrote a client-supplied `lab_id`.** `create_blood_request`
was the last route-reachable method still mass-assigning the raw request body
onto a `TenantEntity`. `blood_bank_requests.lab_id` is `NOT NULL`, so a caller
could file a blood request against another laboratory. This is NR-021 residue
and is **fixed** with the same `_owned()` helper — two regressions added, both
proven to fail with the fix reverted.

**`POST /samples/{id}/transition` requires an idempotency key it never
enforces.** It calls `guard.require_expected_version(...)` and
`guard.require_idempotency_key(...)` but discards the returned key and never
calls `guard.claim()`. A replay therefore re-executes the transition. The
service method does take a row lock and does call `transition()`, so this is a
canonical path with its idempotency half missing rather than a legacy one.
**Recorded, not fixed** — completing it means claiming a receipt, which changes
the endpoint's replay behaviour.

## Disposition

The six `ACTIVE_LEGACY` routes are the donor/donation/component/request
generation: reachable, tenant-scoped, unaudited, unlocked, and outside the state
machine. None is an `UNREACHABLE` or `RETIRE_CANDIDATE` — every one is
route-reachable and is the only way to perform its operation. They cannot simply
be deleted; they need an idempotency contract and a precondition contract to
come under `ClinicalCommandGuard`, which is a behavioural API change.

*(The five zero-caller service methods in `GULA_BLOOD_BANK_LEGACY_BYPASS.md` —
`record_transfusion`, `start_transfusion`, `complete_transfusion`, `issue_units`,
`perform_crossmatch` — remain the actual `RETIRE_CANDIDATE` set. They are
service methods with no route, not routes.)*
