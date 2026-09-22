# NIAM Sync/Async Closure Engine — Lifecycle Category-F, Class 5 of 5 (final): `CitizenService`

Fifth and final lifecycle class, and the one class with a genuine mixed
self-service/administrative authorization model (unlike `WorkforceService`/
`GovernmentHRService`, which fail closed entirely).

## Discovery

Same structural defect as `WorkforceService`/`GovernmentHRService`: no
`__init__` at all, every method took an explicit `db: Session`, while
`routes.py` constructed it as `CitizenService(db)` — a construction-time
`TypeError` on every call.

## Authorization model (11 routes, per-route classification)

| Route | Classification | Rule |
|---|---|---|
| `register_citizen` | Category A (self) | Actor's own resolved person must equal `person_id` — a person may only register *themselves* as a citizen. |
| `send_otp`, `verify_otp`, `record_consent`, `deactivate` | Category A (self) | Pre-fetch the citizen record (mirrors `GuardianService`'s terminate/delegate pattern); actor's own person must equal `citizen.person_id`. |
| `get_citizen_status` | Category A (self) | Actor's own person must equal the path's `person_id` directly. |
| `link_family_member` | Category A (self, **citizen side**) | Adding a family/emergency contact confers no authority over the citizen, so the actor must own the citizen record itself. |
| `link_guardian` | Category A (self, **guardian side**, not citizen side) | Creates the same kind of `GuardianAccount` record as `GuardianService.create_guardianship` (already closed in lifecycle class 1) — that route's established rule (a person may only register *themselves* as a guardian, never claim guardianship on someone else's behalf) is applied identically here, for consistency across the two entry points that create the same resource type. The actor must be the *prospective guardian*, not the citizen. |
| `verify_identity`, `issue_health_id` | Category C (administrative) | Confirming identity documents / issuing a national health id are administrative/registry acts; no existing `PlatformCapability` fits. Fails closed for everyone, including the citizen themselves. |
| `record_death` | Category C (administrative), **inherently third-party** | A deceased person cannot call this API themselves, so there is no self-service angle to even consider. Fails closed. |

This is the deliberate opposite of `link_family_member`'s ownership side
for `link_guardian` — flagged explicitly in both the discovery report and
the route comments, since it is easy to assume all "citizen sub-resource"
routes share one ownership direction when they don't.

## Repair

- `CitizenService.__init__(self, session: AsyncSession)` added.
- All 11 methods (+ new public `get_citizen` lookup, mirroring
  `GuardianService.get_guardian`'s precedent, + `_get_citizen` helper)
  converted to `async def`, using `select(...)` + `await
  self.session.execute(...)`.
- Every mutation now calls `await self.audit.record(AuditEventInput(...))`
  (`reason_code="SELF_SERVICE"` for the 8 self-owned mutations,
  `"ADMIN_AUTHORITY_UNAVAILABLE"` for the 3 fail-closed ones).
- Routes: `get_niam_db` + `actor: NiamActor` added to all 11; ownership
  checks per the table above; `await db.commit()` added to the 8
  mutations. The now-fully-unused `from app.database import get_db`
  import was removed from `routes.py` (last of the 5 lifecycle classes —
  every route in the file now uses `get_niam_db`). The now-unused
  `from sqlalchemy.orm import Session` import was removed from
  `services.py` for the same reason.

## A related pre-existing bug found and fixed (in-scope — same pattern as class 2's `_add_step` fix)

`link_guardian`'s `GuardianAccount(uuid=f"{citizen_id}-guardian-
{guardian_person_id}", ...)`: `GuardianAccount.uuid` is `String(36)`, but
`guardian_person_id` is a 26-char ULID, so this composite routinely
exceeds 36 chars (confirmed by the real HTTP proof crashing with
`StringDataRightTruncation` on the very first successful-auth attempt).
Same defect shape as the `EnterpriseRegistrationStep.uuid` bug fixed in
lifecycle class 2 — fixed identically, with a real `uuid4()` for the
`uuid` column while `guardian_id` (the FK'able, caller-visible business
key, `String(100)`) keeps its descriptive composite.

**Related, not yet triggered, left undisturbed**: `GuardianService.
create_guardianship` (lifecycle class 1, already `VERIFIED`) sets
`uuid=guardian_id` where `guardian_id` is caller-supplied with no length
constraint beyond the DB's own `String(100)` on that column — a caller-
supplied `guardian_id` longer than 36 chars would hit the identical crash.
This didn't surface in class 1's proof (which used short test values) and
is not touched here, since reopening an already-`VERIFIED` class without
a triggering proof would be scope creep; flagged for a future pass.

## Real HTTP + PostgreSQL proof

Full matrix against 3 seeded identities (citizen, prospective guardian,
unrelated third party):

- `register`: no-token 401, other-actor-impersonation 403, self 200.
- `send-otp` / `verify-otp`: other-actor 403, self 200.
- `verify-identity`: no-token 401, **self 403**, other 403 — fails closed
  uniformly, including for the citizen's own attempt.
- `issue-health-id`: self 403 (fails closed even for the citizen).
- `link-guardian`: no-token 401, **citizen attempting to appoint an
  arbitrary third party 403**, prospective-guardian-self 200 (guardian
  side correctly self-checked).
- `link-family`: other-actor 403, citizen-self 200 (citizen side correctly
  self-checked — opposite direction from `link-guardian`).
- `consent`: other-actor 403, self 200.
- `get_citizen_status`: other-actor 403, self 200 (correct status
  returned).
- `record-death`: self 403 (fails closed even for "self" — this route has
  no legitimate self-service caller by definition).
- `deactivate`: other-actor 403, self 200 (run last, since it flips the
  record inactive).
- Nonexistent `citizen_id` on `send-otp`: 500 (pre-existing, file-wide
  `ValueError`→500 gap, same as documented in lifecycle classes 1 and 2 —
  not fixed here).

**Fresh-session persistence proof**: final `status="deactivated"`,
`is_active=False`; `identity_verified_at`, `health_id`, and `deceased_at`
all still `None` (every blocked attempt at the 3 fail-closed routes truly
never reached the database); guardian record persisted and correctly
attributed to the guardian actor's person; family link persisted.

## Failure injection (rollback proof)

Monkeypatched `AsyncSession.commit` to raise after a control
`register_citizen` succeeded. Result: `500` on the injected call; a
fresh-session query confirmed the control citizen row persisted while the
injected-failure row is entirely absent.

## Negative proof (authorization-focused)

Temporarily removed the guardian-side self-check from
`link_citizen_guardian` and confirmed a citizen could then unilaterally
appoint an arbitrary third party as their own guardian — without that
person's consent — flipping from `403` to **`200`**. The untouched
sibling gate (`verify-identity`) was re-checked in the same run and
stayed `403`. Restored `routes.py` from a pre-change backup; `md5sum`
(`3ecc96a24fd7650bf0d603034cf77823` before and after) confirmed
byte-identical restoration.

## Regression

Added `tests/identity/test_lifecycle_citizen_phaseF5.py` (11 tests)
covering both self-check directions (`register_citizen`/`send_otp` on the
citizen side, `link_guardian` on the guardian side, `link_family_member`
on the citizen side again), all 3 fail-closed routes, and the read route.

`pytest tests/identity/ tests/test_migrations.py
tests/test_migration_resilience.py`: **295 passed, 4 skipped** (was 284
before this class's 11 new tests) — zero regressions.

## GATE 1

All items satisfied: per-route classification (correctly identifying the
opposite self-check directions of `link_guardian` vs. `link_family_member`,
and `record_death`'s inherent third-party nature), repair, one related
in-scope bug fixed, real HTTP+PostgreSQL proof of the full 11-route
matrix, failure-injection rollback proof, negative proof with
byte-identical restoration, permanent regression tests, zero regressions.

## RESULT — Lifecycle class 5/5 (`CitizenService`) — **VERIFIED**

All 11 routes closed for both sync/async and authorization. **This
completes lifecycle Category-F** (41 occurrences: `GuardianService` 6,
`EnterpriseRegistrationService` 6, `WorkforceService` 9,
`GovernmentHRService` 9, `CitizenService` 11 — 41 total) and, with it,
the full 135-occurrence NIAM sync/async closure workstream (Batches 1–7 +
5 lifecycle classes). A consolidated final report follows separately.
