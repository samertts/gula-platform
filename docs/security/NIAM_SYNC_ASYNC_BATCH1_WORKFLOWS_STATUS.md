# NIAM Sync/Async Closure Engine — Batch 1: `workflows`

Phase 2-4, Gate 1 of the "NIAM SYNC/ASYNC CLOSURE ENGINE — REAL P1 CLOSURE
— BOUNDED BATCHES WITH AUTOMATIC GATES" workstream. Target: 8 occurrences
in `app/identity/workflows/routes.py`.

## Discovery and classification

All 8 routes (`create_definition`, `list_definitions`, `get_definition`,
`start_instance`, `get_instance`, `submit_approval`, `cancel_instance`,
`get_pending_approvals`) declared `db: AsyncSession = Depends(get_db)` —
the broken sync dependency — while `WorkflowEngine` (already correctly
written with `__init__(self, session: AsyncSession)`) does
`await self.session.execute(...)`/`.flush()`. **Category A**, identical to
the pattern proven and fixed three times already this session
(certificates, TrustFramework, `trust.py`).

Two additional, distinct defects were found while reading the module
(neither previously catalogued):

1. **Crash bug**: `WorkflowDefinition`, `WorkflowInstance`, and
   `WorkflowApproval` constructors in `engine.py` (`create_definition`,
   `start_instance`, `submit_approval`) each passed a literal `id=...`
   (Python `Ellipsis`) as an explicit kwarg. Since these models only
   inherit `IdentityBaseEntity`'s `id = Column(String(26), primary_key=True,
   default=_ulid)` with no local override, this overrode the intended ULID
   default and would fail at INSERT time against a real database (confirmed
   in the negative proof below).
2. **Missing commit** (the `niam-no-commit` pattern, not previously fixed
   in this module): none of the 4 mutating routes called `await
   db.commit()`. `get_niam_db()` never auto-commits (by design, mirroring
   `get_db()`'s semantics) — without an explicit route-level commit, every
   mutation was flushed within the request's transaction but rolled back at
   session teardown, so nothing was ever durably persisted despite routes
   returning 200 with populated response bodies.

## Repair

- `app/identity/workflows/routes.py`: `Depends(get_db)` → `Depends(get_niam_db)`
  on all 8 routes; `await db.commit()` added after the engine call in the
  4 mutating routes (`create_definition`, `start_instance`,
  `submit_approval`, `cancel_instance`).
- `app/identity/workflows/engine.py`: removed the erroneous `id=...,` kwarg
  from all 3 constructors, letting `IdentityBaseEntity`'s ULID default apply.

## Deliberate scope decision — no new Platform Authority capability added

Unlike `trust`/`certificates`/`lifecycle`, no `require_platform_capability`
check was added to any of the 8 `workflows` routes. Reasoning:

- `workflows` is a generic, domain-agnostic approval/workflow engine, not a
  platform-administrative surface — there is no existing `PlatformCapability`
  value that represents "manage workflows," and inventing one would not be
  the mechanical, already-proven fix this batch is scoped to.
- Several operations are participant-level, not administrative:
  `submit_approval` is meant to be callable by whichever `approver_id` the
  workflow definition assigns, and `cancel_instance` by a participant in the
  workflow — neither maps to a platform-wide administrative capability the
  way `trust_manage`/`certificates_manage`/`governance_manage` do.
- Existing authorization semantics were preserved exactly as they already
  are: the parent router applies `_AUTH_REQUIRED = [Depends(get_current_niam_actor)]`
  at `include_router()` time (`app/identity/api/router.py:51`) — i.e.
  authentication (a valid, non-expired NIAM session) is and remains the
  only gate. This batch's fix does not weaken or strengthen that.
- Per the workstream's own rule #6 ("preserve existing authorization
  semantics") and rule #26 ("if the pattern is not actually identical, do
  not apply the same mechanical transformation"), the responsible scope for
  this batch is: fix the DB-engine bug, the crash bug, and the missing
  commit — not invent new authorization scoping. This is documented here as
  a deliberate, evidence-based decision, not a silent gap.

## Real HTTP + PostgreSQL proof

Seeded two real accounts (actor, approver) with real `Person`/`IdentityRecord`/
`Account` rows, minted a real JWT + `UserSession`, and a separate expired
session. Full matrix, all 8 routes, against a real PostgreSQL database
(`gula_certproof`):

| Route | No token | Expired session | Valid session |
|---|---|---|---|
| `POST /definitions` (create_definition) | 401 | 401 | 200 |
| `GET /definitions` (list_definitions) | 401 | 401 | 200 |
| `GET /definitions/{id}` (get_definition) | 401 | 401 | 200 |
| `POST /instances` (start_instance) | 401 | 401 | 200 |
| `GET /instances/{id}` (get_instance) | 401 | 401 | 200 |
| `POST /instances/{id}/approve` (submit_approval) | 401 | 401 | 200 |
| `GET /approvals/pending/{id}` (get_pending_approvals) | 401 | 401 | 200 |
| `POST /instances/{id}/cancel` (cancel_instance) | 401 | 401 | 200 |

**Fresh-session persistence proof** (separate sync engine connection, after
the `TestClient` context closed): definition persisted with a real 26-char
ULID `id` (not `Ellipsis`); 2 instances persisted, both with real ULIDs, one
correctly `approved` (after `submit_approval`) and one correctly
`cancelled` (after `cancel_instance`); 1 approval persisted with a real
ULID and `status="approved"`.

## Failure injection (rollback proof)

Monkeypatched `AsyncSession.commit` to raise immediately after the service
layer's flush, on `create_definition`. Result: request returned `500
INTERNAL_ERROR`; a fresh-session query afterward confirmed **zero orphaned
rows** for that `def_id`. A control request after the monkeypatch was
removed succeeded (`200`) and persisted normally — proving the failure was
specific to the injected fault, not a side effect of the patch itself.

## Negative proof

Temporarily reintroduced the `id=...` crash bug into
`engine.create_definition` only, re-ran the same proof script: `POST
/definitions` with a valid session now returned **500 INTERNAL_ERROR**
(confirmed real, not fabricated). Restored `engine.py` from a pre-change
backup; `md5sum` and `git diff` both confirmed byte-identical restoration
to the fixed state before continuing.

## Regression

`pytest tests/identity/ tests/test_migrations.py
tests/test_migration_resilience.py`: **255 passed, 4 skipped**, both before
introducing the fix (baseline) and after (post-fix, post-restore) — zero
regressions. (5 unrelated pre-existing failures seen in one intermediate
run were traced to an invalid `ENCRYPTION_KEY` value in that specific test
invocation's own environment setup, not to any code change — confirmed by
re-running with a valid Fernet key and getting a clean pass.)

## GATE 1

- All 8 occurrences correctly classified: **yes** (Category A, confirmed
  identical to the proven pattern).
- All defects repaired, including the two additional ones found during
  discovery (crash bug, missing commit) — not just the mechanical
  dependency swap: **yes**.
- Compile + lint clean: **yes**.
- Regression suite: **yes**, 255 passed / 4 skipped, no change from
  baseline.
- Real HTTP proof (8/8 routes, 3-state matrix): **yes**.
- Real PostgreSQL persistence proof: **yes**.
- Transaction/rollback (failure injection) proof: **yes**, zero orphaned
  rows.
- Negative proof (defect reintroduced, real failure confirmed, source
  restored byte-identical): **yes**.
- No new Platform Authority capability invented where none of the
  workstream's proven precedent fits — documented as a deliberate scope
  decision, not silently skipped: **yes**.

## RESULT

**VERIFIED.** Sync/async defect count: 135 → 127 (8 closed:
`workflows`). Batch 2 (`notifications`, 11 occurrences) may now begin.
