# TrustFramework State Machine Status

Closes `docs/security/NEXT_P0_P1_SECURITY_STATUS.md`'s
`niam-trust-no-state-machine` finding (P2): "`TrustFramework` has no
transition guard — `activate_framework` unconditionally sets `active`
regardless of prior status."

## Transition matrix (built from the code's own pre-existing behavior)

| Current state | Operation | Next state | Authority | Preconditions | Audit | Concurrency |
|---|---|---|---|---|---|---|
| (none) | `create_framework` | `draft` | `platform.trust.manage` (was missing — fixed) | none | `TRUST_FRAMEWORK_CREATED` (was missing — fixed) | unique `framework_id` constraint (DB-level) |
| `draft` | `activate_framework` | `active` | `platform.trust.manage` | entity exists | `TRUST_FRAMEWORK_ACTIVATED` | row lock (`FOR UPDATE`, added this pass) |
| `active` | `activate_framework` (repeat) | `active` (no-op) | `platform.trust.manage` | entity exists | none (idempotent — no duplicate audit) | row lock |
| `superseded` | `activate_framework` | **denied** (409) | — | terminal-state guard (added this pass) | none | row lock |
| `draft`/`active` | `supersede_framework` | `superseded` | `platform.trust.manage` (service-level; no route) | entity exists, not already terminal | `TRUST_FRAMEWORK_SUPERSEDED` (was missing — fixed) | row lock |
| `superseded` | `supersede_framework` (repeat) | **denied** | — | terminal-state guard | none | row lock |
| any | `update_framework` | unchanged (field-only: `name_en`/`name_ar`/`version`/`effective_date`) | `platform.trust.manage` (already fixed, Workstream 1) | entity exists | `TRUST_FRAMEWORK_UPDATED` (already present) | none (doesn't touch `status`) |

`supersede_framework` has no HTTP route — an existing, deliberate
precedent from Workstream 1 ("not fabricated a route for an operation
with no prior HTTP entry point"), unchanged here. Its transition logic
was hardened anyway so a future route (or a direct service caller) gets
the same guarantees.

## What was found vs. what was invented

Found (not invented): the three real states (`draft`/`active`/
`superseded`) and the two real transition operations already existed in
`app/identity/trust/services.py`. Found the real gap: `activate_framework`
set `status = "active"` with **zero** precondition check — a framework
already `superseded` could be silently reactivated by anyone holding
`trust.manage`.

Added (smallest guard, no new architecture): a `_TERMINAL_STATUSES`
frozenset (`{"superseded"}`), a `TrustFrameworkInvalidTransition`
exception mapped to HTTP 409, and idempotent-no-op handling for
`active -> active`. No generic workflow engine, no new status values, no
new columns.

## Concurrency (PostgreSQL row locking, no schema change)

`IdentityBaseEntity` has no optimistic-lock `version` column (checked —
none exists), and adding one would be a migration requiring human
approval per this repo's own migration policy. Used
`select(...).with_for_update()` instead (`_get_framework_for_update`) —
zero schema change, works with the existing architecture.

**Real proof:** a raw `psycopg2` connection opened its own transaction
and ran `SELECT id FROM niam_trust_frameworks WHERE framework_id = %s
FOR UPDATE` on a real seeded framework, held for 2 seconds without
committing. Concurrently (separate thread), the real app's
`POST .../activate` endpoint was called via `TestClient` on the *same*
framework row. Measured: the HTTP call did not return until **2.01s**
had elapsed (`blocked_for_at_least_hold_duration: true`), and the raw
connection's lock was confirmed released before the app's response came
back. This is a genuine database-level block, not a Python-level mock —
two conflicting transitions on the same framework cannot both proceed
concurrently.

## Real HTTP + PostgreSQL proof (full sequence, one script)

1. `create_framework` — no token → 401; no capability → 403; correct
   capability → 200, `tfw-1` created in `draft`.
2. `activate_framework("tfw-1")` — `draft -> active`, 200.
3. `activate_framework("tfw-1")` again — idempotent, 200, **same** status,
   fresh-session audit count for `TRUST_FRAMEWORK_ACTIVATED` on this
   framework stayed at **1** (not 2) — no duplicate audit on the no-op.
4. `supersede_framework("tfw-1", <real successor id>)` via direct service
   call (no route) — `active -> superseded`.
5. `activate_framework("tfw-1")` again — **409**,
   `"invalid_transition: cannot activate a framework in status 'superseded'"`.
6. Concurrency proof (above) against a second framework, `tfw-lock-2`.

Fresh-session evidence: `tfw-1` final status `superseded`, `tfw-lock-2`
final status `active` (after the lock released), all audit rows have a
non-null `uuid` and `actor_id`.

## GATE B

- Transition matrix is explicit: **yes** (table above).
- Valid transitions work: **yes**.
- Invalid transitions fail: **yes** (409, real HTTP proof).
- Concurrent conflict is controlled: **yes** (real row-lock timing proof).
- Audit is correct: **yes** (create/activate/supersede all audited;
  idempotent re-activate correctly emits no duplicate).
- Persistence is correct: **yes** (fresh-session proof).

## RESULT

**VERIFIED.**

## Related, not fixed this pass (documented, not silently expanded into)

`app/identity/trust/routes.py`'s other ~20 endpoints (assurance
profiles, trust anchors, federation trust, identity proofing, trust
evaluations) share the identical pre-fix shape found here
(`Depends(get_db)` broken sync/async mismatch, most with zero
capability check) — quantified in
`docs/security/NEXT_P0_P1_SECURITY_STATUS.md`'s new
`niam-broad-sync-db-mismatch` finding. Fixing all of them is a
"generic repository rewrite" outside this operation's bounded scope
(explicitly disallowed); only the `TrustFramework`-specific surface
(`create_framework`/`list_frameworks`/`get_framework`, directly part of
the state machine this phase was asked to secure) was touched.
