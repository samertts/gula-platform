# NIAM Sync/Async Closure Engine — Lifecycle Category-F, Class 3 of 5: `WorkforceService`

Third lifecycle class. `WorkforceService` had **no `__init__` at all** and
every one of its 9 methods took an explicit `db: Session`, while
`routes.py` constructed it as `WorkforceService(db)` — a real `TypeError`
at construction time (a class with no constructor override cannot accept
a positional argument), before the method call is even attempted. Worse
than the usual async/await mismatch, and worse than
`EnterpriseRegistrationService`'s arity mismatch (that class at least had
a working `__init__`).

## Authorization model

**All 8 mutations fail closed for everyone** (Category C, administrative,
no fitting capability):

| Route | Why fail-closed |
|---|---|
| `request_employee`, `validate_national_id`, `validate_license`, `check_conflicts`, `approve_request`, `activate_account`, `terminate_employment`, `preserve_history` | Every one of these is an organization/HR-side action performed *on* a person's employment request by requesting-org staff — there is no `person_id`-vs-actor self-service angle anywhere in this class (unlike `CitizenService`). None of the 4 existing `PlatformCapability` values (`federation_manage`/`trust_manage`/`certificates_manage`/`governance_manage`) model "workforce onboarding authority" — reusing any would misrepresent what they mean. |
| `get_request_status` | Read, left authenticated-only, matching this file's established pattern for reads. |

This is a genuinely different outcome from `EnterpriseRegistrationService`
(where `governance_manage` was direct, proven reuse) — the rule is applied
faithfully in both directions: reuse when the semantics actually fit,
fail closed when they don't, never invent a new one either way.

## Repair

- `WorkforceService.__init__(self, session: AsyncSession)` added;
  `self.session`, `self.audit = CanonicalAuditService(session)`.
- All 9 methods (+ `_get_request` helper) converted to `async def`, using
  `select(...)` + `await self.session.execute(...)` instead of
  `db.query().filter()`.
- Every mutation now calls `await self.audit.record(AuditEventInput(...))`
  with `reason_code="ADMIN_AUTHORITY_UNAVAILABLE"` (so the audit trail
  itself records that these calls, if ever reached, ran without a real
  capability check — relevant only to the direct service-layer proof
  below, since the route layer never reaches the service today).
- Routes: `get_db` → `get_niam_db`; `actor: NiamActor` added to all 9;
  `_require_admin_authority_unavailable()` added as the first line of all
  8 mutations (before touching `db` or the service at all); `await
  db.commit()` added to the 8 mutations.

## Real HTTP + PostgreSQL proof (two independent parts)

Because every mutation is unconditionally blocked, the proof has two
parts, matching the requirement to distinguish "the sync/async defect is
closed" from "the authorization decision is closed":

1. **HTTP-level** (the actual reachable behavior today): all 8 mutations
   return `401` (no token) / `403` (authenticated, any actor, deterministic
   — never a silent `200`). The 1 read route: `401` (no token) / `200`
   (authenticated, no data — nothing was ever created, since every
   mutation is blocked).
2. **Service-level** (bypassing HTTP, using the real NIAM async session
   via `open_niam_session()` against real PostgreSQL): proves the
   underlying async conversion itself is correct and would work
   end-to-end the day a real capability is designed — full workflow
   `request_employee` → `validate_national_id` → `validate_license` →
   `check_conflicts` → `approve_request` → `activate_account` →
   `get_request_status` (mid-flow read: `"activated"`) →
   `terminate_employment` → `preserve_history`, all against a real seeded
   `NIAMOrganization`/`Person` (the same business-key-vs-internal-id FK
   pattern as every prior batch).

**Fresh-session persistence proof**: `status="terminated"`,
`is_active=False`, `national_id_hash="nidhash1"`, `license_number="LIC-1"`,
`historical_preserved=True`, `termination_reason="role eliminated"` — all
9 method calls' effects correctly persisted.

## Failure injection (rollback proof)

Since the HTTP layer never reaches the service, this was run at the
service layer: monkeypatched `AsyncSession.flush` to raise during a
second `request_employee` call (after a control call succeeded and
committed). Result: the injected call raised, and a fresh-session query
confirmed the control row persisted while the injected-failure row is
entirely absent.

## Negative proof (authorization-focused)

Temporarily removed `_require_admin_authority_unavailable()` from
`approve_workforce_request` and confirmed a zero-capability authenticated
actor's approve request against a real `WorkforceRequest` flipped from
`403` to **`200`**. The untouched sibling route (`terminate`) was
re-checked in the same run as a sanity control and remained `403`.
Restored `routes.py` from a pre-change backup; `md5sum`
(`92e1745f1a26d42d3933d5cc47cc2899` before and after) confirmed
byte-identical restoration.

## Regression

Added `tests/identity/test_lifecycle_workforce_phaseF3.py` (9 tests,
parametrized across all 8 mutations + the 1 read).

`pytest tests/identity/ tests/test_migrations.py
tests/test_migration_resilience.py`: **275 passed, 4 skipped** (was 266
before this class's 9 new tests) — zero regressions.

## GATE 1

All items satisfied: per-route classification (all 8 mutations correctly
have zero self-service angle, unlike `CitizenService`'s upcoming mixed
model), repair, real HTTP proof (fail-closed matrix) + real PostgreSQL
service-layer proof (sync/async correctness independent of the
authorization gate), failure-injection rollback proof, negative proof
with byte-identical restoration, permanent regression tests, zero
regressions.

## RESULT — Lifecycle class 3/5 (`WorkforceService`) — **VERIFIED**

Sync/async closed for all 9 routes; authorization correctly closed via
fail-closed default for all 8 mutations (no capability invented, no
route left silently authenticated-only). Remaining lifecycle Category-F
scope: `GovernmentHRService` (9, expected same fail-closed shape — no
read route at all), `CitizenService` (11, mixed self-service/admin
model).
