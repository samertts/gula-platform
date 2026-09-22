# NIAM Sync/Async Closure Engine — Lifecycle Category-F, Class 1 of 5: `GuardianService`

Part of the `lifecycle` Category-F closure (41 occurrences across 5 service
classes). Unlike every prior batch (Category A: a dependency swap), this
class has no `__init__`, its methods took an explicit `db: Session` and
used the legacy sync `db.query(...).filter(...)` API, and its routes
constructed it as `GuardianService(db)` against a class with no
constructor — a real, independent `TypeError` on every call, not merely
the usual async/await mismatch.

Processed as one atomic unit per the user's explicit methodology: full
per-route ownership classification before any conversion, fail-closed
defaults where no capability legitimately fits, and full proof (compile,
real HTTP, real PostgreSQL, audit, transaction rollback, negative proof,
regression) before declaring this class closed.

## Authorization model (established before conversion)

| Route | Classification | Rule |
|---|---|---|
| `POST /guardians` (`create_guardianship`) | Category A (self-owned) | Actor's own resolved person must equal `guardian_person_id` — a person may only register *themselves* as a guardian, never claim guardianship on someone else's behalf. |
| `GET /guardians/dependents/{guardian_person_id}` (`get_dependents`) | Category A | Actor's own person must equal the path's `guardian_person_id`. |
| `GET /guardians/guardians/{dependent_person_id}` (`get_guardians`) | Category A | Actor's own person must equal the path's `dependent_person_id`. |
| `POST /guardians/{id}/terminate` (`terminate_guardianship`) | Category A | Pre-fetch the record; actor's own person must equal its `guardian_person_id`. |
| `POST /guardians/{id}/delegate-access` (`delegate_guardian_access`) | Category A | Same pre-fetch-and-check as terminate. |
| `POST /guardians/{id}/verify` (`verify_guardianship`) | Category C (administrative) | **Fails closed for everyone**, including the guardian of record. Confirming a guardianship claim is legitimate (court order / civil registry) is a real-world authority NIAM's 4-value `PlatformCapability` enum (`federation_manage`/`trust_manage`/`certificates_manage`/`governance_manage`) does not model. Reusing any of those would misrepresent what they mean, so this returns a deterministic 403 (`_NO_ADMIN_AUTHORITY_AVAILABLE`) rather than inventing a capability. |

`_resolve_actor_person_id` resolves the actor's own `Person` via
`Account.identity_id -> IdentityRecord.person_id` (lifecycle resources are
keyed by `person_id`, unlike `adaptive_auth`'s direct `account_id`).
`_require_self_person` raises 403 on any mismatch or unresolved actor
person. `_require_admin_authority_unavailable` mirrors the established
`_POLICY_AUTHORITY_UNAVAILABLE` precedent in `adaptive_auth/routes.py`.

## Repair

- `GuardianService.__init__(self, session: AsyncSession)` added; `self.session`,
  `self.audit = CanonicalAuditService(session)`.
- All 6 public methods (+`get_guardian`/`_get_guardian` helpers) rewritten
  from `db.query(...).filter(...).first()/.all()` to
  `select(...)` + `await self.session.execute(...)`; mutations use
  `self.session.add`/`await self.session.flush()`.
- Every mutation now calls `await self.audit.record(AuditEventInput(...))`
  (category `LIFECYCLE`, action `lifecycle.guardianship.*`).
- Routes: `get_db` → `get_niam_db`; `actor: NiamActor = Depends(get_current_niam_actor)`
  added to all 6; ownership checks per the table above; `await db.commit()`
  added to all 4 mutating routes.

## Real HTTP + PostgreSQL proof

Full matrix against 3 seeded identities (guardian, dependent, unrelated
third party) plus an expired session:

- `create_guardianship`: no-token 401, expired-session 401, other-actor
  impersonation 403, self 200.
- `get_dependents` / `get_guardians`: no-token 401, other-actor 403, self
  200 (correct record count).
- `delegate_access` / `terminate_guardianship`: no-token 401, other-actor
  403, self 200 (both against the real created record).
- `verify_guardianship`: no-token 401, **guardian's own attempt 403**,
  unrelated-actor attempt 403 — fails closed uniformly.
- Nonexistent `guardian_id` on `terminate`: 500 (pre-existing,
  file-wide `ValueError`→500 gap — see below, not introduced by this
  repair, not fixed here).

**Fresh-session persistence proof** (separate sync engine/session):
guardian record persisted, correctly attributed to the guardian actor's
person, `verified_by` still `None` (both verify attempts were blocked
before reaching the service), `delegated_access` set only by the
self-authorized call, `status` correctly `terminated` after the
self-authorized terminate.

## Failure injection (rollback proof)

Monkeypatched `AsyncSession.commit` to raise after a control
`create_guardianship` succeeded. Result: `500` on the injected call, and a
fresh-session query confirmed the control guardian row persisted while the
injected-failure row is entirely absent — no partial/orphaned write.

## Negative proof (authorization-focused)

Temporarily removed the `_require_self_person` self-check from
`create_guardianship` and confirmed an unrelated actor's impersonation
attempt flipped from `403` to **`200`**. Restored `routes.py` from a
pre-change backup; `md5sum` (`e0188f34e4436d2b87649d4568276a92` before and
after) confirmed byte-identical restoration before continuing.

## Regression

Added `tests/identity/test_lifecycle_guardian_phaseF1.py` (7 tests) as a
permanent CI guard on this authorization boundary, following this test
suite's established pattern for this layer (fake session/actor, no real
async engine — see `test_platform_authority_phase10.py`'s own docstring):
covers `_require_self_person` pass/mismatch/unresolved-actor,
`_resolve_actor_person_id`, `create_guardianship` self-vs-impersonation,
and `verify_guardianship`'s fail-closed-for-everyone behavior.

`pytest tests/identity/ tests/test_migrations.py
tests/test_migration_resilience.py`: **262 passed, 4 skipped** (was 255
passed before this class's 7 new tests) — zero regressions.

## A pre-existing, unrelated bug found and documented (NOT fixed): file-wide `ValueError`→500

None of `lifecycle/routes.py`'s routes (before or after this repair) catch
`ValueError` from the service layer's "not found" checks (e.g.
`_get_guardian` raising `ValueError(f"GuardianAccount not found: ...")`),
unlike `admin/routes.py`, `certificates/routes.py`, and
`compliance/routes.py`, which do catch it and return a clean `404`/`422`.
Confirmed via `terminate_guardianship` against a nonexistent
`guardian_id`: `500` instead of a clean `404`. This is orthogonal to the
sync/async defect and to this class's authorization scope — a UX/error-shape
defect, not a data-integrity or security issue — and affects the whole
file, not just `GuardianService`. **Not fixed here**; flagged for a future,
separately-scoped pass across all 5 lifecycle service classes.

## GATE 1

All items satisfied: per-route ownership classification, repair, real
HTTP+PostgreSQL proof, failure-injection rollback proof, negative proof
with byte-identical restoration, permanent regression tests, zero
regressions in the full identity+migration suite.

## RESULT — Lifecycle class 1/5 (`GuardianService`) — **VERIFIED**

Sync/async + authorization closure confirmed end-to-end for all 6 routes,
not merely "the crash disappeared." Lifecycle Category-F remaining scope:
`EnterpriseRegistrationService` (6 routes, already-known arity-mismatch +
missed-await bugs), `WorkforceService` (9), `GovernmentHRService` (9),
`CitizenService` (11) — each to be processed one class at a time with the
same rigor.
