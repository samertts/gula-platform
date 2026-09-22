# NIAM Sync/Async Closure Engine — Lifecycle Category-F, Class 2 of 5: `EnterpriseRegistrationService`

Second lifecycle class. `start_registration` was already converted in a
prior session as the one representative Category-F repair; this class
closes the remaining 6 methods (`validate_license`, `submit_inspection`,
`assess_risk`, `approve_registration`, `reject_registration`,
`get_registration_status`, plus private helpers `_get_registration`/
`_complete_step`).

## Discovery

`EnterpriseRegistrationService.__init__` already takes a single
`session: AsyncSession` (from the prior partial conversion), but these 6
methods still took an explicit `db: Session` as their first business
parameter and used the legacy sync `db.query()` API, while `routes.py`
called them as `EnterpriseRegistrationService(db)` then
`await svc.validate_license(reg_id, license_document, validated_by)` —
**a real arity mismatch**: `db` silently bound into the `reg_id`
parameter slot, `reg_id`'s value bound into `license_document`, etc., not
merely the usual dependency-typing crash. A second, independent bug: the
sync callers invoked the now-async `_add_step`/`_complete_step` without
`await`, which would silently create-and-drop a coroutine (the step row
would never be written even after the arity bug is fixed).

## Authorization model

All 5 mutations (`validate_license`, `submit_inspection`, `assess_risk`,
`approve_registration`, `reject_registration`) are **Category C**
(administrative) — the identical workflow, same file, same class as
`start_registration`, which already established
`PlatformCapability.governance_manage` as the fitting capability for this
exact workflow. This is direct reuse of an already-proven-fitting
capability, not a new one. `get_registration_status` stays a read,
authenticated-only, matching the file's established pattern for reads
(e.g. `get_enterprise_status`, its own route).

## Repair

- All 6 methods (+ 2 private helpers) converted to `async def`, using
  `self.session` instead of an explicit `db` parameter, `select(...)` +
  `await self.session.execute(...)` instead of `db.query().filter()`.
- Every mutation now calls `await self.audit.record(AuditEventInput(...))`.
- Routes: `get_db` → `get_niam_db`; `actor: NiamActor` added to all 6;
  `await require_platform_capability(actor, db, PlatformCapability.governance_manage.value)`
  added to the 5 mutating routes; `await db.commit()` added to all 5.

## Two additional pre-existing bugs found and fixed (in-scope — both live inside the exact method being converted)

1. **`_add_step`'s `uuid=step_name`**: `EnterpriseRegistrationStep.uuid` has
   a table-wide **unique** constraint, but `_add_step` set it to the bare
   `step_name` (e.g. `"license_validation"`) — identical across every
   registration in the system. The *second* registration to ever reach
   that step, system-wide, would hit a `UniqueViolation` and 500. This
   predates this session (introduced by the original `start_registration`
   repair) but lives inside `_add_step`, the exact private helper this
   class's conversion touches, and blocked this class's own proof from
   completing with more than one registration — fixed by using
   `uuid=str(uuid4())` (a real, always-unique value; nothing else in the
   codebase reads this column, confirmed via grep) instead of the
   collision-prone business string.
2. **Audit `action` string length vs. deployed schema**: this session's
   new `submit_inspection` audit call used
   `action="lifecycle.enterprise_registration.submit_inspection"` (51
   chars). `IdentityAuditEntry.action` is declared `String(120)` in the
   ORM model, but the **actually deployed** column (confirmed via
   `\d niam_audit_entries`) is `character varying(50)` — a real,
   pre-existing schema/model drift unrelated to this repair. Every other
   action string in this file (including the other 4 new ones) happens to
   fit under 50 chars, so this was previously invisible. Not a migration
   fix (out of this batch's scope — schema changes require separate
   review per the Migration Policy); the action string itself was
   shortened to `"lifecycle.enterprise_registration.inspect"` (41 chars),
   consistent with the naming already used by the other 4 actions.

## Real HTTP + PostgreSQL proof

Full workflow proven end-to-end against a real seeded `NIAMOrganization`
(the FK `EnterpriseRegistration.organization_id` requires a real internal
id, not an arbitrary caller-supplied string — the same business-key-vs-
internal-id pattern found in every prior batch's proof-writing, handled
here by seeding a real org and using its `.id`):
`register` (401/403/200) → `validate-license` (401/403/200) → `inspect`
(401/200) → `assess-risk` (200) → `approve` (200, certificate issued) →
`get_enterprise_status` (401/200 read). Separate `reject` path proven
(401/403/200) on a second registration. Nonexistent `reg_id` on
`validate-license`: 500 (pre-existing file-wide `ValueError`→500 gap,
same as documented in the GuardianService closure — not fixed here).

**Fresh-session persistence proof**: registration 1 correctly `approved`
with a certificate id set and all 4 workflow steps
(`license_validation`, `inspection`, `risk_assessment`, `approval`)
persisted and marked `completed`; registration 2 correctly `rejected` and
`is_active=False`.

## Failure injection (rollback proof)

Monkeypatched `AsyncSession.commit` to raise on a second registration's
`approve` call after a control registration's `approve` succeeded.
Result: `500` on the injected call; fresh-session query confirmed the
control registration `approved` while the injected one remained `draft`
(its status change never persisted) — no partial write.

## Negative proof (authorization-focused)

Temporarily removed `require_platform_capability(...)` from
`approve_enterprise_registration` and confirmed a zero-capability actor's
approve request flipped from `403` to **`200`**. `start_registration`'s
own (untouched) gate was re-checked in the same run as a sanity control
and remained `403`. Restored `routes.py` from a pre-change backup;
`md5sum` (`7c252262577af7c7a213666075c38072` before and after) confirmed
byte-identical restoration.

## Regression

Added `tests/identity/test_lifecycle_enterprise_phaseF2.py` (4 tests):
capability-gate-blocks, capability-gate-allows, reject uses the same
gate, and the read route has no gate.

`pytest tests/identity/ tests/test_migrations.py
tests/test_migration_resilience.py`: **266 passed, 4 skipped** (was 262
before this class's 4 new tests) — zero regressions.

## GATE 1

All items satisfied: discovery (arity mismatch + missed-await confirmed),
repair, 2 in-scope pre-existing bugs fixed (both live inside the exact
methods converted), real HTTP+PostgreSQL proof of the full workflow,
failure-injection rollback proof, negative proof with byte-identical
restoration, permanent regression tests, zero regressions.

## RESULT — Lifecycle class 2/5 (`EnterpriseRegistrationService`) — **VERIFIED**

All 7 routes in this class (the 1 pre-existing `start_registration` plus
these 6) now share one uniform authorization model and pass a real,
multi-registration end-to-end workflow proof. Remaining lifecycle
Category-F scope: `WorkforceService` (9), `GovernmentHRService` (9),
`CitizenService` (11).
