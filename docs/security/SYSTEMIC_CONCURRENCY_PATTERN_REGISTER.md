# Systemic Concurrency Pattern Register

Per the cross-domain pattern-analysis requirement: once the same defect
shape appears in 3+ domains, it stops being a series of individual
findings and becomes a systemic pattern that should be named, tracked,
and checked for on sight in every future domain audit.

## Pattern: "unused OptimisticLockMixin, no terminal-state guard"

**Shape**: a service method does `db.query(Model).filter_by(id=x).first()`
(no `.with_for_update()`), mutates 3+ fields including a `status`
transition, and commits — while `Model` already inherits
`OptimisticLockMixin` (a `version` column exists and is never read or
incremented anywhere in the file). The terminal state of the status
field (a value after which no further transition should be legal) is
never checked before overwriting it.

**Confirmed in 3 domains this session**, each independently proven on
real PostgreSQL 16, each fixed identically:

| Domain | Method | Terminal state | Commit |
|---|---|---|---|
| `app/biomedical` | `complete_work_order` (+ `update_device_status`, `create_work_order`'s device-status flip) | `WorkOrderStatus.COMPLETED` | `40aee3b6` |
| `app/command_center` | `resolve_emergency`, `fulfill_resource` | `"resolved"`, `"fulfilled"` | (this pass) |
| `app/public_health` | `update_alert_status` | `OutbreakStatus.DECLARED_OVER` | (this pass) |

**Also matches** (different domains, same root shape, found and fixed
earlier this session before this register existed): `payments-capture-refund-cas`
(`app/payments/service.py`, no version column existed there — pessimistic
lock used directly), `device-outbox-claim-cas` (`app/devices/outbox.py`,
`SKIP LOCKED` claim variant). Six total closures of the same underlying
defect class this session.

**Canonical safe pattern** (what every fix above converges on):

```python
model = self.db.query(Model).filter_by(id=x).with_for_update().first()
if not model:
    raise NotFoundError()
if model.status == TERMINAL_VALUE:
    raise AlreadyInTerminalStateError()   # a new, distinct exception —
                                          # never reuse the 404 not-found
                                          # error for this; map it to 409
... mutate ...
model.version = (model.version or 0) + 1
self.db.commit()
```

**Unsafe variant already eliminated at the source in 2 domains**
(`blood_bank`, `critical_care`) by a prior engineering pass, before this
session started: a "legacy method + `_safely`-suffixed hardened method"
convention, with routes exclusively calling the `_safely` variant and the
legacy one left in place but confirmed DEAD_OR_UNREACHABLE. This session
did not introduce that convention name in the 3 newly-fixed domains —
fixed the existing method in place instead, since there was no
already-published "unsafe legacy twin" contract to preserve for those 3.

## Detector opportunity — evaluated, NOT built

Per the same discipline already applied earlier this session
(`imaging-slice-detector-decision`): a deterministic AST-based detector
for "method reads a model with `OptimisticLockMixin`, mutates a `status`
field, commits, and never calls `.with_for_update()`" is plausible in
principle (unlike the report-audit-call-order detector that shipped
earlier this session, this one doesn't need cross-procedural analysis —
the read, mutate, and commit are usually in the same function). **Not
built this pass** — three confirmed instances is enough to name the
pattern and check for it manually in every future domain audit, but
building and validating a repo-wide scanner is a separate, non-trivial
piece of work (it would need to resolve which base class a model
inherits transitively, distinguish INSERT-only from read-modify-write
call shapes, and avoid false positives on the `_safely`-convention
domains that intentionally keep an unlocked legacy twin around as dead
code). Recorded as a candidate for a dedicated pass, not fabricated here.

## Regression guard convention

Every fix above added a test that does two things without needing a real
Postgres connection (SQLite can't reproduce the race, but can pin the
code-level contract):
1. Spies on `sqlalchemy.orm.Query.with_for_update` to prove the actual
   production code path calls it (not a separately-constructed lookalike
   query).
2. Directly asserts that a second call after the first success raises
   the new terminal-state exception, with the second call's payload
   never applied.

## Domains not yet checked for this pattern

`blood_bank`/`critical_care` — checked, already safe (pattern present in
a different, already-hardened form). Every other LIVE + TABLE-BACKED
domain in `docs/architecture/LIVE_RUNTIME_SURFACE_MAP.md` that has not
yet had a vertical-slice audit (`insurance`'s live routes are
schema-latent so excluded; `national`/`governance` likewise) should be
checked for this exact shape as the first, cheapest concurrency check
before any deeper audit.

## Pattern 2 (new, this pass): "Python `not` applied to a SQLAlchemy column instead of `~`"

**Not a concurrency defect** (recorded here per this batch's own
documentation-update instructions, since this file is the established
place this session registers "same shape found 3+ times" defects; a
correctness-pattern register would be the more precise home if one
existed).

**Shape**: `.filter(Model.id == x, Model.lab_id == y, not Model.is_deleted)`
(or `is_revoked`/`is_active`). Python evaluates `not <InstrumentedAttribute>`
immediately at query-*construction* time, not at SQL-execution time — a
bare column attribute has no special `__bool__` override, so `bool(Model.column)`
is always `True` (default object truthiness) and `not Model.column` is
always the literal Python `False`. Confirmed directly:
```python
>>> bool(Foo.is_deleted)
True
>>> not Foo.is_deleted
False
```
and confirmed that `.filter(False)` compiles to `WHERE 0 = 1` — the
query unconditionally matches **zero rows**, regardless of what data
actually exists. The correct SQLAlchemy idiom is `~Model.is_deleted`
(the library's boolean-NOT operator on a column expression), which
already appears dozens of times correctly elsewhere in this same
codebase — this is a same-file typo/inconsistency, not a
misunderstanding of the ORM.

**Confirmed in 4 domains this session** (this pass):

| Domain | Site | Fixed this pass? |
|---|---|---|
| `app/services/hospital_service.py:152` (`_get_entity`, shared by 17 call sites) | `not model.is_deleted` | **Yes** — `~model.is_deleted`, proven via real HTTP two-request reproduction/fix, negative-proofed |
| `app/radiology/pacs.py:365,375,388` | `not ImageShare.is_revoked` (3 call sites, 2 methods) | No — different, unaudited domain, out of this batch's bound |
| `app/pharmacy/routes.py:504` | `not model.is_deleted` | No — different, unaudited domain, out of this batch's bound |
| `app/routes/admin.py:257` | `not Lab.is_active` | No — different, unaudited domain, out of this batch's bound |

**Impact class**: every affected query call always returns "not found" /
empty, regardless of real data — the opposite failure mode from most
security bugs (fails closed, not open), so this reads as an
availability/correctness bug rather than an authorization bypass. In
Hospital's case specifically, it silently broke 10+ routes' nested-entity
lookups (campus/building/department/room/bed/OT/equipment) until fixed
this pass.

**Not built this pass**: a repo-wide AST-based detector (matching the
`scripts/setattr_mass_assignment_guard.py`/`scripts/log_action_arg_order_guard.py`
convention already established for other systemic patterns this
session). The 3 remaining known sites above are a small, bounded,
next-batch candidate — grep for `not [A-Za-z_.]+\.is_(deleted|revoked|active)\b`
inside a `.filter(` call finds all of them; a proper detector would need
to handle multi-line `.filter(...)` calls and avoid false positives on
legitimate value-assignment negation (e.g. `lab.is_active = not
lab.is_active`, confirmed NOT a bug — it's a plain Python boolean
toggle, not a query filter).

## Pattern 3 (new, this pass, Hospital-specific so far — not yet confirmed systemic): "route/service never calls `db.commit()`"

**Shape**: a route calls a service method that does
`db.add(...)`/`db.flush()` (or a route does its own `setattr` loop +
`db.flush()`) and returns a success response, but neither the route nor
the service ever calls `db.commit()`. Since `get_db()`
(`app/database.py`) uses `sessionmaker(autocommit=False, ...)` and only
rolls back on exception, the transaction is implicitly discarded when
the request-scoped session closes — the caller sees a 200/201 with
what looks like a persisted record, but the very next request (a fresh
session, matching real production behavior) cannot find it.

**Confirmed in 1 domain so far this session** (Hospital, 18 routes —
see GAP-7 in `docs/security/AUTHORIZATION_GAP_REGISTER.md` for full
proof). Below this register's own normal 3-domain naming threshold, so
this is recorded as a single-domain finding to watch for, not yet
promoted to a named cross-domain pattern. **Worth checking manually**
in any future domain audit: does every route that mutates state via a
service method calling only `db.add()`/`db.flush()` have an explicit
`db.commit()` somewhere in its call path? This repo's own shared-session
test-client fixture (`tests/conftest.py`'s `client`) masks this defect
shape completely (see GAP-7's "why this was invisible" note) — a
domain's tests all passing is not evidence this pattern is absent
there.
