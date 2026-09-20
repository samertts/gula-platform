# NIAM Live Path Proof — Federation/Trust vs. the Real Database Session

Binary runtime fact only. No source file was modified to produce this
result.

## Method

Constructed the real app via the repository's own factory
(`from app.factory import create_app` / `app.main.app` — not a hand-built
app). Ran it against a disposable, freshly-created PostgreSQL 16 instance
(no production data): applied the real migration chain up to
`20260815_0022`, then created the remaining NIAM tables (including
`niam_platform_authority_assignments`) directly via the real ORM models
(the mainline `alembic upgrade head` still hits the pre-existing, unrelated
`pharmacy_drug_substitution_rules` FK type-mismatch bug found in Phase 10 —
worked around for this narrow test the same way, not fixed). Used
`fastapi.testclient.TestClient(app)` as a context manager so the real
`lifespan`/`startup_guard` sequence actually runs. Minted one JWT via the
app's own real `app.security.auth.create_token` (same function
`get_current_niam_actor` decodes) — no real account exists for it; that's
deliberate, since the finding below occurs before any row lookup could
matter.

## STEP 1 — route registration (verified, with one incidental finding)

Using `app.openapi()["paths"]` (the version-correct way to enumerate
effective routes — `app.router.routes` does not flatten sub-included
routers the way earlier assumed in this FastAPI/Starlette version; that
was double-checked and discarded as a false lead before relying on
`openapi()`):

- `federation.update_provider` → **`PUT /niam/federation/providers/{provider_id}`** — registered as expected.
- `trust.update_framework` → **`PUT /niam/niam/trust/frameworks/{framework_id}`** — registered, but at a **double-prefixed path**, not the expected `/niam/trust/frameworks/{framework_id}`.

**Incidental finding, not fixed**: `app/identity/trust/routes.py` declares
`router = APIRouter(prefix="/niam/trust", ...)`, while
`app/identity/federation/routes.py` declares just
`prefix="/federation"`. The NIAM aggregator (`app/identity/api/router.py`)
mounts both under its own `/niam` prefix, so federation correctly resolves
to `/niam/federation/...` while trust resolves to `/niam` + `/niam/trust` =
`/niam/niam/trust/...`. Confirmed pre-existing via `git log -p` on that
line (present before this session's Phase 10 commit). Not touched here —
out of this phase's scope — but the real reachable path for trust is the
double-prefixed one, and that's what was tested below.

## STEP 2/3/4 — the live request

| Request | Result |
|---|---|
| `PUT /niam/federation/providers/prov-1`, no `Authorization` header | `401 AUTHENTICATION_REQUIRED` — route reached, auth dependency correctly denies. |
| `PUT /niam/federation/providers/prov-1`, valid-shaped bearer token (real secret, no matching account row) | **`500 INTERNAL_ERROR`**. Server log: `object ChunkedIteratorResult can't be used in 'await' expression`. |
| `PUT /niam/niam/trust/frameworks/fw-1`, no `Authorization` header | `401 AUTHENTICATION_REQUIRED` — same as federation. |
| `PUT /niam/niam/trust/frameworks/fw-1`, valid-shaped bearer token | **`500 INTERNAL_ERROR`**, identical server log:  `object ChunkedIteratorResult can't be used in 'await' expression`. |

The exception fires inside `get_current_niam_actor` at
`await db.execute(select(Account, UserSession)...)` — `db` is whatever
`Depends(get_db)` yields, which is the real, synchronous `SessionLocal()`
`Session`. `Session.execute()` returns a plain `ChunkedIteratorResult`
immediately (not a coroutine); `await`-ing it raises exactly this
`TypeError`. This happens **before** any Platform Authority check, before
the service layer, before any ORM write — authentication itself never
completes for a request that gets past the bearer-token-presence check.

## FEDERATION

`ROUTE(reached) → AUTH(reached, crashes) → AUTHORIZATION(never reached) → DB(crashes inside auth's own query) → SERVICE(never reached)`
**Last VERIFIED boundary: authentication dependency, at its own database query.**

## TRUST

Identical: `ROUTE(reached, at /niam/niam/trust/... not /niam/trust/...) → AUTH(reached, crashes) → AUTHORIZATION(never reached) → DB(crashes inside auth's own query) → SERVICE(never reached)`
**Last VERIFIED boundary: authentication dependency, at its own database query.**

## DATABASE

**SYNC.** `get_db()` (`app/database.py`) yields a plain `sqlalchemy.orm.Session` from `SessionLocal()` bound to a `create_engine(...)` sync engine. No adapter converts it to `AsyncSession`-compatible behavior; the crash above is the direct, empirical proof of that gap, not an inference from reading imports.

## RESULT

**LIVE_BLOCKED**

Exact blocking exception (verbatim from the live server log, both routes):

```
object ChunkedIteratorResult can't be used in 'await' expression
```

Raised from within `app/identity/api/workspaces.py::get_current_niam_actor`'s
`await db.execute(...)` call, where `db` is the synchronous session `Depends(get_db)`
actually supplies.

## NEXT ACTION

The smallest concrete repair to make this specific path reachable: give
NIAM's `get_current_niam_actor` (and, transitively, every NIAM async
service it feeds) a real `AsyncSession`, sourced from a real
`create_async_engine`-backed session factory — either a dedicated
NIAM-only async engine/dependency (smallest blast radius: no change to the
legacy monolith's sync `get_db`) or a platform-wide async migration
(much larger scope, not proposed here). This is a database/dependency-
wiring fix, not an authorization fix — Phase 6-10's authorization/field-
boundary work is unaffected by it and remains what it always was: correct
at the code level, not yet provably effective at the request level until
this is resolved. Not implemented in this phase, per its own constraints.
