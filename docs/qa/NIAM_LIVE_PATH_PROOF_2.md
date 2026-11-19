# NIAM Live Path Proof 2 — After the Async DB Boundary Fix

Phase 10.6.5, Part A. Real app (`app.main.app`, built by the real
`app.factory.create_app()` factory — not a hand-built app), real disposable
PostgreSQL 16, real disposable Redis, real HTTP requests via
`fastapi.testclient.TestClient` as a context manager (real `lifespan` /
`startup_guard` runs), real JWTs minted via `app.security.auth.create_token`.
No service function was called directly — every case below is an actual
HTTP request through the real ASGI app.

## What changed (Part A implementation)

**New file**: `backend/app/identity/niam_async_db.py` — a NIAM-only async
engine/session (`get_niam_db`), lazily constructed from the same
`DATABASE_URL` via the `psycopg` v3 driver (already declared in
`requirements.txt`, already installed; not a new dependency). Does not
touch `app/database.py` or `get_db()`.

**Modified** (3 call sites only):
- `backend/app/identity/api/workspaces.py` — `get_current_niam_actor`'s own
  `db` dependency: `Depends(get_db)` → `Depends(get_niam_db)`.
- `backend/app/identity/federation/routes.py` — `update_provider`'s own
  `db` param only (18 sibling endpoints in the same file untouched).
- `backend/app/identity/trust/routes.py` — `update_framework`'s own `db`
  param only (32 sibling endpoints untouched).

**Untouched**: `app/database.py`, every other NIAM route/service, all
non-NIAM domains, all migrations (no schema change — the new engine talks
to the exact same tables).

**Tests**: `tests/identity/` (199 tests) re-run after the change —
195 passed, 4 skipped, same as before. No regression. `tests/conftest.py`
was NOT modified: no existing test exercises a NIAM route over real HTTP
(confirmed via `grep -rln 'client\.\(put\|post\|get\|patch\)("/niam'
tests/` → zero matches), so no test can reach the new dependency's real
engine construction; it stays inert unless a future test calls these
routes over HTTP, at which point it would need the same
`dependency_overrides` treatment `get_db` already gets.

## Method

Disposable PostgreSQL 16 (`initdb --auth=trust`, `pg_ctl` on a scratch
socket/port), migrated with the real Alembic chain up to `20260815_0022`
(the pre-existing, unrelated `pharmacy_drug_substitution_rules` FK
type-mismatch bug — found in Phase 10, confirmed still present, still out
of scope — blocks a bare `upgrade head` identically to Phase 10.6),
remaining NIAM tables created via the real ORM metadata
(`IdentityBase.metadata.create_all`, via `import app.main` to register
every model first — mirrors `tests/conftest.py`'s own session-fixture
precedent). Disposable Redis (`redis-server`) was also started this time
(Phase 10.6 didn't need it — this run needed the real `startup_guard` to
reach `system_ready=True`, which requires Redis reachability; `ENV` set to
`development` to avoid unrelated production-only friction like
`DocsAuthMiddleware`, `RUNTIME_MODE` left at its default `api`, not `test`
— the real, non-test-bypassed startup path was exercised).

Two real identities/accounts/sessions were seeded directly via the sync
ORM (seeding infra, not the code under test): one with no Platform
Authority grants, one with `platform.federation.manage` +
`platform.trust.manage` granted via real
`niam_platform_authority_assignments` rows. Two real JWTs were minted via
the app's own `create_token`, each backed by a real `niam_sessions` row
with the token's actual `jti`.

## STEP 1 — request matrix (real HTTP, both routes)

| Case | Federation (`PUT /niam/federation/providers/{id}`) | Trust (`PUT /niam/niam/trust/frameworks/{id}`) |
|---|---|---|
| No token | **401** `AUTHENTICATION_REQUIRED` | **401** `AUTHENTICATION_REQUIRED` |
| Valid token, missing capability | **403** `FORBIDDEN — Platform authority denied` | **403** `FORBIDDEN — Platform authority denied` |
| Valid token, correct capability | **500** `INTERNAL_ERROR` (see below) | **500** `INTERNAL_ERROR` (same cause) |

**This is the core Part A result.** In Phase 10.6 (before this fix), the
*authenticated* cases never got past `get_current_niam_actor`'s own DB
query — `500`, `object ChunkedIteratorResult can't be used in 'await'
expression`, always, for any request with a bearer token. Now: the 401 and
403 cases are both **real, correct, empirically observed outcomes** — the
async DB boundary fix works. Authentication runs a genuine async Postgres
query (confirmed via `psycopg`'s async cursor appearing in the stack, see
below) and returns the right answer; authorization (`require_platform_capability`
→ `PlatformAuthorityService.has_capability`) also runs a genuine async
query and returns the right answer.

## STEP 2 — the new 500: a separate, pre-existing, real bug

With `raise_server_exceptions=True`, the actual exception (not the
generic `INTERNAL_ERROR` envelope) was captured for the federation case:

```
sqlalchemy.exc.IntegrityError: (psycopg.errors.NotNullViolation)
null value in column "uuid" of relation "niam_audit_entries"
violates not-null constraint
...
File ".../app/identity/services/canonical_audit.py", line 177, in record
    await self.session.flush()
```

The stack trace runs through real `psycopg` async machinery
(`sqlalchemy/dialects/postgresql/psycopg.py`, `psycopg/cursor_async.py`,
`greenlet_spawn`/`await_only`) — this is a genuine async round-trip to
real PostgreSQL, not a sync session in disguise. **The async DB boundary
is not the failure here; it is what got us this far.**

**Root cause, verified against the model and every sibling call site**:
`IdentityAuditEntry.uuid` (`app/identity/models/audit.py:229`) is
`Column(String(36), unique=True, nullable=False, index=True)` — no
`default=`. `CanonicalAuditService.record()`
(`app/identity/services/canonical_audit.py`) constructs a new
`IdentityAuditEntry(...)` without ever setting `uuid=`. Every other
model-construction call site in this exact codebase sets it explicitly:
```
$ grep -n "uuid=" app/identity/platform_authority/services.py \
    app/identity/federation/services.py app/identity/trust/services.py
platform_authority/services.py:72:   uuid=str(uuid.uuid4()),
federation/services.py:63,156,217,267,341:   uuid=str(uuid.uuid4()),
trust/services.py:64,166,264,350,435,529:   uuid=str(uuid.uuid4()),
```
`canonical_audit.py`'s `record()` is the **only** outlier. This is a
genuine, isolated, pre-existing bug (an omission, not a design gap) — it
has apparently never been exercised against a real NOT-NULL-enforcing
database before this run (the existing test suite never writes a real
`IdentityAuditEntry` row to a real, constraint-checked engine for this
path). **Not fixed here** — `canonical_audit.py` is shared business logic
well outside "the smallest possible NIAM-only async DB boundary," and the
task's own GATE lists "data-integrity issue" as a stop-and-report
condition, not a silently-patch condition.

## STEP 3 — consequence: nothing persists (a second, compounding, separate finding)

Neither `FederationService.update_provider` nor
`TrustFrameworkService.update_framework` — nor `CanonicalAuditService.record`
— ever calls `.commit()`; only `.flush()`. Confirmed:
`grep -rn "\.commit()" app/identity/federation/services.py
app/identity/trust/services.py app/identity/platform_authority/services.py
app/identity/services/canonical_audit.py` → zero matches. This is not new
behavior from this phase's fix — `get_db()` itself never commits either
(`app/database.py`'s `finally: db.close()`, no commit on the success
path) — so this has been true since before this phase, for every NIAM
write through this dependency. Combined with STEP 2's crash aborting the
transaction outright, **no field update and no audit record persists for
the "correct capability" case today**, independently confirmed via a
fresh, separate DB session after the request:

```json
"db_evidence": {
  "provider_name_en": "Original Name",       // unchanged
  "provider_issuer_url": "https://issuer.example",  // unchanged
  "framework_name_en": "Original Framework Name",   // unchanged
  "framework_id_unchanged": true
},
"audit_evidence": { "count": 0, "event_types": [] }
```

## STEP 4 — a third, separate, pre-existing defect found while seeding TRUST

Seeding a single `TrustFramework` row via the ORM (`sync_db.commit()`)
raised, before any HTTP request was even sent:
```
sqlalchemy.exc.NoReferencedTableError: Foreign key associated with column
'niam_trust_frameworks.authority_id' could not find table
'niam_identity_authorities' with which to generate a foreign key
```
`TrustFramework.authority_id` (`app/identity/trust/models.py:35`)
references `niam_identity_authorities` — a table **no model anywhere in
the codebase defines** (`grep -rn "niam_identity_authorities" app/` finds
only the two FK-string references in `trust/models.py`, no table). This
crashes on **any** ORM flush/commit of a `TrustFramework` row (insert or
update — it's a mapper-configuration failure, not a data problem), so it
would fire identically inside the real route's own
`await self.session.flush()` too, independent of sync/async. Worked
around for seeding only (raw SQL `INSERT`, bypassing the ORM mapper for
that one row) so the real HTTP path could still be exercised. Not fixed —
would require either a real `niam_identity_authorities` model + migration,
or removing the dangling FK, neither authorized by this phase's scope
("Do NOT create a migration unless schema changes are proven necessary").

## FEDERATION

`ROUTE(reached) → AUTH(reached, real async query, correct 401) → AUTHORIZATION(reached, real async query, correct 403) → DB(real async Postgres round-trip proven) → SERVICE(reached, own update presumably applied in-session) → AUDIT WRITE(crashes — separate pre-existing bug, STEP 2) → PERSISTENCE(none — STEP 3)`

**Last VERIFIED boundary for the async DB boundary itself: DB reached,
real async I/O confirmed, both auth and authorization decisions correct.**
**Last VERIFIED boundary for the full round trip: service layer, blocked
before commit by an unrelated, pre-existing audit-write defect.**

## TRUST

Same shape, plus the additional pre-existing `authority_id` FK defect
(STEP 4) which had to be routed around just to seed the test row (not
present in the live HTTP path only because nothing in this proof updates
`authority_id`; the real route's own flush would hit it too the moment
any `TrustFramework` row is inserted OR updated by the ORM — confirmed by
the mapper-level nature of the error, not a value-dependent one).

`ROUTE(reached, at the pre-existing double-prefixed /niam/niam/trust/... path) → AUTH(reached, real async query, correct 401) → AUTHORIZATION(reached, real async query, correct 403) → DB(real async Postgres round-trip proven) → SERVICE(reached) → AUDIT WRITE(crashes — same bug as federation, shared code) → PERSISTENCE(none)`

## DATABASE

**ASYNC, for the two fixed routes.** `get_niam_db()` yields a real
`sqlalchemy.ext.asyncio.AsyncSession` bound to a `psycopg` v3
`create_async_engine`. Confirmed via the real `psycopg.cursor_async`/
`greenlet_spawn` frames in the STEP 2 traceback — this is not an
inference, it's the literal call stack of a live request. All other NIAM
routes remain on the original sync-labeled-async `get_db()`, unchanged,
exactly as scoped.

## RESULT

**PARTIALLY VERIFIED**

The specific, narrow thing Part A set out to prove — *does the NIAM
async DB boundary now work for the two target routes* — is **VERIFIED**:
authentication and authorization both execute genuine async Postgres
queries and return correct results (401/403), which was categorically
impossible before this fix (100% failure rate, same exception, every
time, per Phase 10.6).

The *full* round trip (service mutation actually persisted + a real audit
record written) is **BLOCKED**, by two separate, pre-existing,
newly-discovered defects unrelated to sync/async at all:
1. `CanonicalAuditService.record()` never sets `IdentityAuditEntry.uuid`,
   a `NOT NULL` column with no default — every real (non-test-double)
   canonical audit write crashes against any real constraint-enforcing
   database.
2. No code in this call chain (`get_db()` included) ever calls
   `.commit()` — flush-only, so even absent bug #1, a successful request
   would still not durably persist anything past session close.
3. (Trust only) `TrustFramework.authority_id` references a table that
   doesn't exist as any model — crashes any ORM flush/commit of that
   class, insert or update.

None of these three are caused by, or fixable within, "the smallest
possible NIAM-only async DB boundary" — they are pre-existing defects in
shared business logic (`canonical_audit.py`), the base DB dependency
pattern (`get_db()`, unchanged since before this session), and an
unrelated model (`trust/models.py`), respectively. Per this phase's GATE
("If Part A has: unexpected architectural blocker ... data-integrity
issue ... STOP and report"), this is recorded here rather than silently
patched.

## Files changed (Part A)

| File | Change |
|---|---|
| `backend/app/identity/niam_async_db.py` | **new** — NIAM-only async engine/session |
| `backend/app/identity/api/workspaces.py` | `get_current_niam_actor`'s `db` dep: `get_db` → `get_niam_db` |
| `backend/app/identity/federation/routes.py` | `update_provider`'s `db` param only: `get_db` → `get_niam_db` |
| `backend/app/identity/trust/routes.py` | `update_framework`'s `db` param only: `get_db` → `get_niam_db` |

No migration, no schema change, no other route/service touched.

## Tests executed

| Check | Result |
|---|---|
| `python -m py_compile` (4 changed files) | PASS |
| `ruff check` (4 changed files) | PASS (0 findings) |
| `pytest tests/identity/` (199 tests) | PASS — 195 passed, 4 skipped (unchanged from before this fix) |
| Live HTTP proof, both routes, 3 auth scenarios each | See RESULT above — auth/authz VERIFIED, full round-trip BLOCKED |

## Resource usage

One disposable PostgreSQL 16 instance (`initdb`/`pg_ctl`, scratch
directory, torn down after), one disposable Redis instance (required this
time for the real, non-bypassed `startup_guard` to reach
`system_ready=True`; Phase 10.6 didn't need it), one real app boot per
proof run (~15–20s factory + startup_guard time), a handful of HTTP
requests per run. No production data. No network calls outside localhost.
Both disposable instances stopped and their data directories removed at
the end of this phase.

## Remaining blockers (for Part A's own scope)

1. `CanonicalAuditService.record()` missing `uuid=` — one-line, high
   confidence, but is a change to shared business logic outside this
   phase's authorized file list.
2. No commit anywhere in the NIAM write path (`get_db()` included) —
   pre-existing, not introduced by this phase, but blocks any real
   persistence proof until addressed.
3. `TrustFramework.authority_id`'s dangling FK to a nonexistent
   `niam_identity_authorities` table — pre-existing, blocks any real
   ORM write to `TrustFramework` (this phase's seeding step routed
   around it with raw SQL only for setup, not as a fix).

**None of these three were introduced by, or are required to complete,
Part A's actual mandate** (the async DB boundary itself, now proven
working). They are reported here, per the GATE, rather than fixed,
pending an explicit decision on whether fixing them falls inside or
outside this effort's authorized scope.
