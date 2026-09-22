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
