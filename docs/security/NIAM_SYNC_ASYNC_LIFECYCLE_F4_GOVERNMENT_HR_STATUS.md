# NIAM Sync/Async Closure Engine — Lifecycle Category-F, Class 4 of 5: `GovernmentHRService`

Fourth lifecycle class. Same structural defect as `WorkforceService`: **no
`__init__` at all**, every method took an explicit `db: Session`, while
`routes.py` constructed it as `GovernmentHRService(db)` — a construction-
time `TypeError` on every call.

## Authorization model

**All 9 routes fail closed for everyone** (Category C, administrative, no
fitting capability) — same reasoning as `WorkforceService`:

| Route | Why fail-closed |
|---|---|
| `create_appointment`, `approve_appointment`, `create_identity`, `issue_credential`, `activate_account`, `assign_permissions`, `promote`, `transfer`, `retire` | Every one is an HR/appointing-authority action on a government employee's appointment record — no `person_id`-vs-actor self-service angle, and none of the 4 existing `PlatformCapability` values model "government HR appointing authority". |

Unlike `WorkforceService`, this class has **no read route at all** — all 9
occurrences are mutations, so all 9 fail closed with none exempted.

## Repair

- `GovernmentHRService.__init__(self, session: AsyncSession)` added.
- All 9 methods (+ `_get_appointment` helper) converted to `async def`,
  using `select(...)` + `await self.session.execute(...)`.
- Every mutation now calls `await self.audit.record(AuditEventInput(...))`
  with `reason_code="ADMIN_AUTHORITY_UNAVAILABLE"`.
- Routes: `get_db` → `get_niam_db`; `actor: NiamActor` added to all 9;
  `_require_admin_authority_unavailable()` added as the first line of all
  9; `await db.commit()` added to all 9.

## Real HTTP + PostgreSQL proof (two independent parts, same structure as WorkforceService)

1. **HTTP-level**: all 9 routes return `401` (no token) / `403`
   (authenticated, any actor, deterministic — never a silent `200`).
2. **Service-level** (bypassing HTTP, real NIAM async session against real
   PostgreSQL): full workflow `create_appointment` → `approve_appointment`
   → `create_identity` → `issue_credential` → `activate_account` →
   `assign_permissions` → `promote` → `transfer` → `retire`, against real
   seeded `NIAMOrganization`/`Person` rows. Also proved the class's own
   pre-existing sequencing guards still work correctly post-conversion: a
   second appointment's `create_identity` called before HR approval
   correctly raised `ValueError("Cannot create identity: status is draft,
   expected hr_approved")`.

**Fresh-session persistence proof**: `status="retired"`, `is_active=False`,
`position="Senior Analyst"`, `grade="G8"` (post-promotion),
`organization_id`/`department="IT"` correctly updated post-transfer,
`permissions_assigned=True`, `promotion_history`/`transfer_history` each
with 1 entry.

## Failure injection (rollback proof)

Service-layer (same rationale as `WorkforceService`): monkeypatched
`AsyncSession.flush` to raise during a second `create_appointment` call
after a control call succeeded and committed. Result: the injected call
raised; fresh-session query confirmed the control row persisted while the
injected-failure row is entirely absent.

## Negative proof (authorization-focused)

Temporarily removed `_require_admin_authority_unavailable()` from
`approve_government_appointment` and confirmed a zero-capability
authenticated actor's approve request against a real
`GovernmentAppointment` flipped from `403` to **`200`**. The untouched
sibling route (`retire`) stayed `403` in the same run. Restored
`routes.py` from a pre-change backup; `md5sum`
(`93c3da099e78a5c6c0aeb5e41fd5b5b6` before and after) confirmed
byte-identical restoration.

## Regression

Added `tests/identity/test_lifecycle_government_hr_phaseF4.py` (9 tests,
parametrized across all 9 routes — no read route to test separately here).

`pytest tests/identity/ tests/test_migrations.py
tests/test_migration_resilience.py`: **284 passed, 4 skipped** (was 275
before this class's 9 new tests) — zero regressions.

## GATE 1

All items satisfied: classification (all 9 routes correctly have zero
self-service angle and no read route), repair, real HTTP proof
(fail-closed matrix) + real PostgreSQL service-layer proof (full 9-step
workflow, including a pre-existing sequencing guard's correctness),
failure-injection rollback proof, negative proof with byte-identical
restoration, permanent regression tests, zero regressions.

## RESULT — Lifecycle class 4/5 (`GovernmentHRService`) — **VERIFIED**

Sync/async closed for all 9 routes; authorization correctly closed via
fail-closed default for all 9 (no capability invented, no route left
silently authenticated-only). Remaining lifecycle Category-F scope:
`CitizenService` (11 routes, the one class with a genuine mixed
self-service/admin model — final lifecycle class).
