# NIAM Sync/Async Closure Engine — Batch 7b: `governance` (policy approvals + appeals)

Continuation of Phase 10 (see `NIAM_SYNC_ASYNC_BATCH7A_GOVERNANCE_AUTHORITIES_STATUS.md`
for the parent batch's scope/sub-batching rationale). Sub-batch 7b:
Policy Approvals + Appeals (8 occurrences).

## Discovery

All 8 routes (`submit_policy_approval`, `get_pending_policy_approvals`,
`approve_policy`, `reject_policy`, `submit_appeal`, `list_appeals`,
`assign_appeal_to_council`, `decide_appeal`) declared `db: AsyncSession =
Depends(get_db)` against `PolicyApprovalService`/`AppealService` (already
correctly async). **Category A**. No `id=...` crash bug present.

Same authorization gap as sub-batch 7a: authentication-only. 6 mutations
gated with `PlatformCapability.governance_manage`, matching this file's
established pattern. 2 reads (`get_pending_policy_approvals`,
`list_appeals`) left authenticated-only.

## A genuine ambiguity, resolved conservatively and documented (not guessed)

`submit_appeal` takes a client-supplied `appellant_person_id` — in a real
product, appeals are plausibly citizen-self-submitted (someone appealing
their own suspension), which would argue for a self-service ownership
check like `adaptive_auth`'s `_require_self`. But unlike `adaptive_auth`
(where `account_id` is literally `actor.account.id`), there is **no
established mapping** anywhere in this codebase from a NIAM `actor.account`
to "the Person I represent" that this module could reuse — `appellant_person_id`
is a `Person`, not an `Account`. Rather than invent that mapping
unilaterally (a real identity-model design decision, not a sync/async
fix) or leave the route fully open (the current, broken state), it was
gated the same conservative way as federation's `link_identity` (also
person_id-scoped, no self-service mapping): `governance_manage`,
documented as a choice that would block a hypothetical citizen
self-service appeal flow if that is the intended product behavior. This
is flagged explicitly here rather than silently decided.

`submit_policy_approval` has no such ambiguity — policy submission is
unambiguously a governance-staff action — gated the same way without
reservation.

## Repair

- `Depends(get_db)` → `Depends(get_niam_db)` on all 8 routes.
- `require_platform_capability(actor, db, PlatformCapability.governance_manage.value)`
  + `await db.commit()` added to the 6 mutating routes.

## Real HTTP + PostgreSQL proof

Full 401/401/403/403/200 matrix against 3 seeded accounts (no-capability,
wrong-capability, correct-capability) for all 6 mutating routes; 401/200
for the 2 read routes. A test-script bug (not a code bug) was caught and
fixed: `assign_appeal_to_council`'s `council_id` is a real FK to
`niam_gov_councils.id` (internal ULID); the proof now creates a real
council via the already-fixed `create_council` (sub-batch 7a) and uses
its internal id.

**Fresh-session persistence proof**: both policy workflows correctly
`approved`/`rejected`; the appeal correctly assigned to its council and
`decide_appeal`'s decision (`upheld` → status `rejected`, matching the
service's actual outcome-mapping logic) correctly persisted.

## Failure injection (rollback proof)

Monkeypatched `AsyncSession.commit` to raise after
`submit_policy_approval`'s flush. Result: `500`, zero orphaned rows for
the injected policy_id. Control request after restore: `200`, persisted.

## Negative proof (authorization-focused)

Temporarily removed `require_platform_capability(...)` from
`decide_appeal` and confirmed a zero-capability account's request flipped
from `403` to **`200`** (able to decide an identity appeal). Restored
`routes.py` from a pre-change backup; `md5sum` and `git diff` both
confirmed byte-identical restoration before continuing.

## Regression

`pytest tests/identity/ tests/test_migrations.py
tests/test_migration_resilience.py`: **255 passed, 4 skipped** — no
change from baseline.

## GATE 1

All items satisfied: classification (including the honestly-flagged
appeal-submission ambiguity), repair, real HTTP+PostgreSQL proof,
failure-injection rollback proof, negative proof with byte-identical
restoration, zero regressions.

## RESULT

**VERIFIED.** Sync/async defect count: 57 → 49 (8 closed: `governance`
policy-approvals + appeals). Sub-batch 7c (suspensions + registry, 8
occurrences, the final governance sub-batch) may now begin.
