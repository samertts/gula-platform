# NIAM Sync/Async Closure Engine — Batch 7c: `governance` (suspensions + registry)

Final sub-batch of Phase 10 (see `NIAM_SYNC_ASYNC_BATCH7A_GOVERNANCE_AUTHORITIES_STATUS.md`
for the parent batch's scope/sub-batching rationale). Sub-batch 7c:
Suspensions + Registry (8 occurrences) — completes all 24 governance
occurrences (7a: 8, 7b: 8, 7c: 8).

## Discovery

All 8 routes (`suspend_identity`, `lift_suspension`,
`list_active_suspensions`, `get_suspension_history`, `register_identity`,
`get_registration`, `certify_identity`, `revoke_certification`) declared
`db: AsyncSession = Depends(get_db)` against `SuspensionService`/
`RegistryService` (already correctly async). **Category A**. No `id=...`
crash bug.

Same authorization gap as sub-batches 7a/7b. Unlike 7b's `submit_appeal`,
none of this sub-batch's mutations have any self-service ambiguity —
suspending/lifting a suspension, registering an identity, and certifying/
revoking a certification are unambiguously governance-staff actions
performed *on* a person, not *by* them. All 5 mutating routes
(`suspend_identity`, `lift_suspension`, `register_identity`,
`certify_identity`, `revoke_certification`) gated with
`PlatformCapability.governance_manage`, matching the established pattern
with no reservation. 3 reads left authenticated-only.

Since this is the last governance sub-batch, the now-fully-unused
`from app.database import get_db` import was removed from
`routes.py` — all 25 routes in the file now use `get_niam_db`.

## A fourth pre-existing, unrelated bug found and documented (NOT fixed): `certify_identity`

`RegistryService.certify_identity` does
`certifying_authority_id=certifying_authority_id or ""`, but
`IdentityCertificationRegistry.certifying_authority_id` is a **NOT NULL**
foreign key to `niam_gov_authorities.id`. An empty string can never
satisfy that FK (it is neither `NULL` nor a real authority id), so this
route fails with a `ForeignKeyViolation` on every call that doesn't
explicitly supply a real, existing `certifying_authority_id` —
independent of sync/async engine choice, and independent of this batch's
fix. Confirmed via the negative-style investigation: reverting to
`get_db` would produce the identical crash-before-this-code (masking it),
but the bug itself lives entirely in the `or ""` fallback pattern, a
data-model/business-logic defect, not a Category-A occurrence. **Not
fixed here** — the proof instead supplies a real authority id (created via
the already-fixed `create_authority`) to demonstrate the route otherwise
works correctly end-to-end. Recommended future fix: either make the
column nullable (if "uncertified" state should be representable) or
require and validate a real `certifying_authority_id` at the route level
with a clear 422, rather than silently coercing `None` to `""`.

This is the fourth such finding this session (after `compliance`'s
`func.case` misuse, `admin`'s `add_department` field-mapping bug, and
`adaptive_auth`'s `UserSession.account_type` bug) — each newly-reachable
route in this workstream has so far surfaced exactly one pre-existing,
unrelated defect beneath the sync/async crash it used to hide behind.

## Repair

- `Depends(get_db)` → `Depends(get_niam_db)` on all 8 routes; unused
  `get_db` import removed from the file (last governance sub-batch).
- `require_platform_capability(actor, db, PlatformCapability.governance_manage.value)`
  + `await db.commit()` added to the 5 mutating routes.

## Real HTTP + PostgreSQL proof

Full 401/401/403/403/200 matrix for all 5 mutating routes against 3
seeded accounts (no-capability, wrong-capability, correct-capability);
401/200 for the 3 read routes.

**Fresh-session persistence proof**: first suspension correctly `lifted`,
second still `active`; registry entry persisted with a real registration
number; certification (using a real supplied authority id) correctly
`revoked` after `revoke_certification`.

## Failure injection (rollback proof)

Monkeypatched `AsyncSession.commit` to raise after `suspend_identity`'s
flush (reason `"injected"`). Result: `500`, and a fresh-session query
confirmed exactly one suspension row for the test person afterward —
the control request's (reason `"control"`), none orphaned.

## Negative proof (authorization-focused)

Temporarily removed `require_platform_capability(...)` from
`revoke_certification` and confirmed a zero-capability account's request
flipped from `403` to **`200`** (able to revoke an identity certification).
Restored `routes.py` from a pre-change backup; `md5sum` and `git diff`
both confirmed byte-identical restoration before continuing.

## Regression

`pytest tests/identity/ tests/test_migrations.py
tests/test_migration_resilience.py`: **255 passed, 4 skipped** — no
change from baseline.

## GATE 1

All items satisfied: classification, repair, real HTTP+PostgreSQL proof,
failure-injection rollback proof, negative proof with byte-identical
restoration, zero regressions.

## RESULT — Batch 7 (`governance`) complete

**VERIFIED.** All 3 governance sub-batches (7a: authorities/councils/
review-boards, 7b: policy-approvals/appeals, 7c: suspensions/registry)
now closed. Sync/async defect count: 49 → 41 (8 closed this sub-batch;
24 closed across the full governance batch: 65 → 41 overall). One
ambiguity (appeal self-submission, sub-batch 7b) and one new pre-existing
bug (`certify_identity`'s FK-fallback defect, this sub-batch) documented
for future work.

Only the `lifecycle` Category-F work (41 occurrences, per the directive
to be sub-batched into groups of ≤5 routes each, classified into F1-F8
sub-types) remains before the workstream's final consolidated report.
