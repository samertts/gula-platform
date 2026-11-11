# NIAM Sync/Async Closure Engine — Batch 2: `notifications`

Phase 5 of the "NIAM SYNC/ASYNC CLOSURE ENGINE — REAL P1 CLOSURE — BOUNDED
BATCHES WITH AUTOMATIC GATES" workstream. Target: 11 occurrences in
`app/identity/notifications/routes.py`.

## Discovery and classification

All 11 routes (`send_notification`, `create_template`, `list_templates`,
`get_queue`, `mark_read`, `get_preferences`, `update_preferences`,
`send_template_notification`, `mark_notification_sent`,
`mark_notification_delivered`, `get_pending_notifications`) declared `db:
AsyncSession = Depends(get_db)` against `NotificationService` (already
correctly `__init__(self, session: AsyncSession)`, real `await
self.session.execute/.flush()`). **Category A**, identical to the pattern
proven and fixed four times already this session (certificates,
TrustFramework, `trust.py`, `workflows`).

The same two additional defects found in Batch 1 (`workflows`) recurred
here, in the identical shape:

1. **Crash bug**: 4 model constructors in `services.py`
   (`send_notification`'s and `send_template`'s `NotificationQueue`,
   `update_preferences`'s `NotificationPreference`, `create_template`'s
   `NotificationTemplate`) each passed a literal `id=...` (Ellipsis),
   overriding `IdentityBaseEntity`'s ULID default. Confirmed via
   `models.py`: all three model classes inherit `IdentityBaseEntity` with
   no local `id` override.
2. **Missing commit**: none of the 7 mutating routes (`send_notification`,
   `create_template`, `mark_read`, `update_preferences`,
   `send_template_notification`, `mark_notification_sent`,
   `mark_notification_delivered`) called `await db.commit()` — same
   `niam-no-commit` pattern as `workflows`.

## Repair

- `app/identity/notifications/routes.py`: `Depends(get_db)` →
  `Depends(get_niam_db)` on all 11 routes; `await db.commit()` added after
  the service call in the 7 mutating routes.
- `app/identity/notifications/services.py`: removed the erroneous `id=...,`
  kwarg from all 4 constructors.

## Deliberate scope decision — no new Platform Authority capability added

Same reasoning as `workflows`
(`docs/security/NIAM_SYNC_ASYNC_BATCH1_WORKFLOWS_STATUS.md`):
`notifications` is a generic, domain-agnostic delivery/preferences engine
with no existing `PlatformCapability` mapping, and several operations
(`mark_read`, `update_preferences`) are naturally recipient-scoped rather
than platform-administrative. The parent router already applies
`_AUTH_REQUIRED = [Depends(get_current_niam_actor)]` at `include_router()`
time (`app/identity/api/router.py:52`) — authentication-only semantics
preserved unchanged, not weakened or strengthened by this batch.

## Real HTTP + PostgreSQL proof

Seeded one real account with a valid session and a separate expired
session. Full matrix, all 11 routes, against real PostgreSQL
(`gula_certproof`):

| Route | No token | Expired session | Valid session |
|---|---|---|---|
| `POST /send` (send_notification) | 401 | 401 | 200 |
| `POST /templates` (create_template) | 401 | 401 | 200 |
| `GET /templates` (list_templates) | 401 | 401 | 200 |
| `GET /queue/{id}` (get_queue) | 401 | 401 | 200 |
| `POST /queue/{id}/read` (mark_read) | 401 | 401 | 200 |
| `GET /preferences/{id}` (get_preferences) | 401 | 401 | 200 |
| `PUT /preferences/{id}` (update_preferences) | 401 | 401 | 200 |
| `POST /send-template` (send_template_notification) | 401 | 401 | 200 |
| `POST /queue/{id}/sent` (mark_notification_sent) | 401 | 401 | 200 |
| `POST /queue/{id}/delivered` (mark_notification_delivered) | 401 | 401 | 200 |
| `GET /pending` (get_pending_notifications) | 401 | 401 | 200 |

`send_template_notification` initially correctly returned
`template_not_found` for a freshly-created (`is_active=False`) template —
`create_template` creates templates inactive by design (same pattern as
`workflows`' `create_definition`, no activation route exposed in either
module) — not a bug; the proof activates the template directly via DB
before exercising `send_template_notification`, matching the technique
already used for `workflows`.

**Fresh-session persistence proof**: both notification-queue rows
persisted with real 26-char ULIDs (one `read`, one taken through
`queued → sent → delivered`); the template persisted with a real ULID; the
preference persisted with a real ULID and `enabled=true`.

## Failure injection (rollback proof)

Monkeypatched `AsyncSession.commit` to raise immediately after
`send_notification`'s flush. Result: `500`, and a fresh-session query
confirmed **zero orphaned rows** for that request. A control request
after the monkeypatch was removed returned `200` and persisted normally.

## Negative proof

Reintroduced the `id=...` bug into `send_notification`'s constructor only,
re-ran the rollback-proof script: both the injected-failure request and a
plain control request now returned **500** (confirmed real —
`psycopg2`/`asyncpg` cannot adapt a Python `Ellipsis` parameter), proving
the regression is genuine. Restored `services.py` from a pre-change
backup; `md5sum` and `git diff` both confirmed byte-identical restoration
to the fixed state (4-line removal only, matching the intended fix)
before continuing.

## Regression

`pytest tests/identity/ tests/test_migrations.py
tests/test_migration_resilience.py`: **255 passed, 4 skipped** — identical
to the Batch 1 baseline, no regressions from this batch's changes.

## GATE 1 (applied per-batch)

- All 11 occurrences correctly classified: **yes** (Category A, confirmed
  identical to the proven pattern).
- All defects repaired, including the two additional ones (crash bug,
  missing commit), not just the mechanical dependency swap: **yes**.
- Compile + lint clean: **yes**.
- Regression suite: **yes**, 255 passed / 4 skipped, no change from
  baseline.
- Real HTTP proof (11/11 routes, 3-state matrix): **yes**.
- Real PostgreSQL persistence proof: **yes**.
- Transaction/rollback (failure injection) proof: **yes**, zero orphaned
  rows.
- Negative proof (defect reintroduced, real failure confirmed, source
  restored byte-identical): **yes**.
- No new Platform Authority capability invented where none of the
  workstream's proven precedent fits — documented as a deliberate scope
  decision, not silently skipped: **yes**.

## RESULT

**VERIFIED.** Sync/async defect count: 127 → 116 (11 closed:
`notifications`). Batch 3 (`compliance`, 8 occurrences) may now begin.
