# NIAM Sync/Async Closure Engine — Batch 7a: `governance` (authorities/councils/review-boards)

Phase 10 of the "NIAM SYNC/ASYNC CLOSURE ENGINE — REAL P1 CLOSURE —
BOUNDED BATCHES WITH AUTOMATIC GATES" workstream. Governance has 24
total sync/async occurrences; per the directive's explicit instruction
("DO NOT process all 24 blindly"), split into 3 sub-batches of 8 along
the file's own section boundaries. This is sub-batch 7a: Authorities,
Councils, Review Boards (8 occurrences).

## Discovery

`create_authority` (1 of the file's 25 routes) was already fixed in an
earlier phase this session, gated with `PlatformCapability.governance_manage`.
The remaining 7 routes in this sub-batch (`list_authorities`,
`get_authority`, `suspend_authority`, `activate_authority`,
`create_council`, `list_councils`, `get_council`, `create_review_board`)
declared `db: AsyncSession = Depends(get_db)` against `GovernanceService`
(already correctly async). **Category A**.

Same authorization gap shape as `adaptive_auth`/`federation`: no
authorization beyond parent-level authentication. Unlike those two
batches, no new design decision was needed — every mutating route here
(`suspend_authority`, `activate_authority`, `create_council`,
`create_review_board`) is unambiguously the same platform-governance-
administration action already covered by this file's own
`create_authority` precedent. Gated with the same
`PlatformCapability.governance_manage`. The 4 read routes are left
authenticated-only, unchanged.

No `id=...` crash bug present (confirmed via `services.py`).

## Repair

- `Depends(get_db)` → `Depends(get_niam_db)` on all 8 routes.
- `require_platform_capability(actor, db, PlatformCapability.governance_manage.value)`
  added to the 4 mutating routes; `await db.commit()` added to the same 4.

## Real HTTP + PostgreSQL proof

Seeded 3 accounts (no-capability, wrong-capability [`federation_manage`],
correct-capability [`governance_manage`]). Full matrix:

| Route | No token | Expired | No cap. | Wrong cap. | Correct cap. |
|---|---|---|---|---|---|
| `suspend_authority` | 401 | 401 | 403 | 403 | 200 |
| `activate_authority` | 401 | 401 | 403 | 403 | 200 |
| `create_council` | 401 | 401 | 403 | 403 | 200 |
| `create_review_board` | 401 | 401 | 403 | 403 | 200 |

Read routes (`list_authorities`, `get_authority`, `list_councils`,
`get_council`): 401 with no token, 200 for any authenticated actor.

A test-script bug was caught and fixed along the way (not a code bug):
`council.authority_id`/`review_board.authority_id` are real FKs to
`niam_gov_authorities.id` (the internal ULID) — the proof initially
passed the business `authority_id` key instead, causing a
`ForeignKeyViolation`. Corrected by fetching the authority's internal
`id` from `create_authority`'s own response before using it.

**Fresh-session persistence proof**: authority correctly cycled
`active → suspended → active`.

## Failure injection (rollback proof)

Monkeypatched `AsyncSession.commit` to raise after `create_authority`'s
flush. Result: `500`, fresh-session query confirmed **zero orphaned
rows** for the injected-failure authority_id. A control request
afterward returned `200` and persisted.

## Negative proof (authorization-focused)

Temporarily removed `require_platform_capability(...)` from
`suspend_authority` and confirmed a freshly-seeded, zero-capability
account's request flipped from `403` to **`200`**. Restored `routes.py`
from a pre-change backup; `md5sum` and `git diff` both confirmed
byte-identical restoration before continuing.

## Regression

`pytest tests/identity/ tests/test_migrations.py
tests/test_migration_resilience.py`: **255 passed, 4 skipped** — no
change from baseline.

## GATE 1

All items satisfied: classification, repair (dependency + capability +
commit), real HTTP+PostgreSQL proof, failure-injection rollback proof,
negative proof with byte-identical restoration, zero regressions.

## RESULT

**VERIFIED.** Sync/async defect count: 65 → 57 (8 closed:
`governance` authorities/councils/review-boards). Sub-batch 7b (policy
approvals + appeals, 8 occurrences) may now begin.
