# NR-044 — Architecture Resolution: one database access model

Companion to `verification-wiring.md` (AUTH-005) and
`nr-044-blast-radius.json` (the machine-readable inventory).

**Status: NR-044 remains OPEN — the decision is measured and recommended here;
the conversion is a separate batch.** Nothing was converted in this batch.

---

## 1. Root cause, exactly

`app/database.py::get_db` yields a synchronous `sqlalchemy.orm.Session`. Fifty
modules perform `await <session>.<db method>()`. **No `create_async_engine`
exists anywhere in `app/`.** Awaiting the result of a synchronous `execute`
raises before any statement is sent.

The identity platform was written against an async session contract the
application never provided. The `AsyncSession` annotations are decorative.

## 2. The runtime call graph, measured

The decisive measurement is two functions in the same file that differ only in
colour, given the same token and the same session object:

```
get_current_niam_actor       (async) -> TypeError: object ChunkedIteratorResult
                                        can't be used in 'await' expression
get_current_niam_actor_sync  (sync)  -> HTTPException 401: Inactive or invalid
                                        NIAM session
```

The sync twin **executed the query**, found no matching session and returned a
correct authorization decision. The async original never reached the database.

`get_current_niam_actor` is the dependency on the entire `/niam/*` router
(`router.include_router(..., dependencies=[Depends(get_current_niam_actor)])`),
so the failure is at the door:

```
HTTP /niam/*  →  get_current_niam_actor  →  await db.execute(...)  →  TypeError
                 ^^^^^^^^^^^^^^^^^^^^^^ fails here, before any handler
```

| Path | Classification |
|---|---|
| `/niam/*` — every route, all sub-routers | **UNREACHABLE** — fails at the shared auth dependency |
| `/admin/citizen-relationships/*` | **REACHABLE** — sync route, sync service, sync session |
| `/clinical_gateway/*` | **REACHABLE** — deliberately uses `get_current_niam_actor_sync` |
| `/auth/*`, `/login`, legacy routes | **REACHABLE** — sync throughout |
| async identity services/repositories | **UNREACHABLE** except via tests that supply their own object |

**Blocked NIAM capabilities:** accounts, persons, identities, sessions,
workspaces, memberships, roles, consents, devices, security, audit, governance,
trust/assurance, lifecycle, federation, certificates, workflows, notifications,
adaptive auth, admin, compliance.

## 3. Blast radius (AST, not grep)

| Measure | Count |
|---|---|
| Modules performing `await <session>.<db method>()` | **50** |
| `await`-database call sites | **460** |
| `async def` inside those modules | **506** |
| `AsyncSession` annotations | **131** |
| `async with` context managers | **45** |
| `async for` | **0** |
| `Depends(get_db)` in those modules | **83** |

By package: `identity` 43, `capabilities` 4, `national` 2, `services` 1.

### Why each function is async

| Category | Count | Meaning |
|---|---|---|
| every `await` is a database await | **251** | mechanical conversion |
| mixes database and non-database awaits | **96** | the non-database awaits are almost all calls to *other functions in the same layer* — `self._audit`, `_require_permission`, `self.repo.get_by_id`, `self.audit.record`. Async by cascade, not by need |
| no database await at all | **159** | out of scope; leave alone |
| **genuine async I/O** (network, sleep, file) | **1** | `identity/admin/services.py:450`, an `httpx` client call |

That last row is the finding that settles the question. **Across 506 async
functions there is exactly one that is async for a reason other than the
database.** The async-ness is a cascade from a database contract that was never
implemented.

## 4. Option A — introduce a real AsyncEngine

Not implemented. Measured.

Technically feasible without a new dependency: `psycopg[binary]>=3.3.4` is
already required and SQLAlchemy's psycopg dialect supports async; `greenlet` is
present. `asyncpg` is absent but not needed.

| Cost | Evidence |
|---|---|
| Second engine and pool | `app/database.py` already builds a primary and a read-replica pool. A third would be added, per worker |
| Connection budget | `_WORKERS × (_POOL_SIZE + _MAX_OVERFLOW)` = 2 × (5 + 10) = 30 today, plus the replica pool. An async pool adds the same again against PostgreSQL's 100 |
| Transaction boundaries | two independent units of work. A request touching both a sync route and an async service commits twice, with no shared transaction and no two-phase commit |
| Dual architecture | **Yes, permanently.** 53 routers are sync; the 50 async modules would keep a separate session type, lifecycle and testing strategy |
| Failure modes | a sync path and an async path can see different snapshots of the same row within one request; the audit hash-chain could interleave across two transactions |
| Tests | 31 files already use `pytest.mark.asyncio`; they would need a real async engine fixture against migrated PostgreSQL |
| Operational | two pools to size, monitor and exhaust independently; `make health-deep` and the pool telemetry in `database.py` report one engine |

Option A **creates a second database-access architecture by definition**, which
is the outcome Phase 6 exists to prevent.

## 5. Option B — converge on the synchronous Session

Not implemented. Measured.

| Cost | Evidence |
|---|---|
| Modules | 50 |
| Call sites | 460 `await` removals |
| Functions | 251 mechanical, 96 cascade, 1 genuine (`httpx`, keep async or move behind a sync wrapper) |
| Annotations | 131 `AsyncSession` → `Session` |
| Context managers | 45 `async with` → `with` |
| Dependencies | none — `Depends(get_db)` already yields exactly the right type; 83 sites become *correct* rather than changed |
| Transactions | one unit of work per request, the model the other 53 routers already use |
| Pools | unchanged; no new connections |
| Migrations | **none** |
| Tests | the 31 `asyncio`-marked files lose their marks; identity tests gain the ability to hit migrated PostgreSQL the way `test_identity_link_and_assurance.py` already does |
| Precedent | `get_current_niam_actor_sync` is this conversion, already in the tree, written because the clinical gateway had to work |

## 6. Comparison

| Dimension | Option A | Option B |
|---|---|---|
| Files affected | 50 + `database.py` + 31 test files + fixtures | 50 + 31 test files |
| Runtime paths | two, permanently | one |
| DB architectures | **two** | **one** |
| Transaction complexity | two units of work per request, no shared transaction | one |
| Connection pools | +1 per worker (30 → 60 against 100) | unchanged |
| Test complexity | async engine fixture on migrated PostgreSQL, plus the sync one | the existing sync fixture, already proven |
| CI impact | new async fixture in the PostgreSQL gate | none beyond re-running |
| Operational | two pools to size and monitor | unchanged |
| Failure modes | split-snapshot within a request; interleaved audit chain | none introduced |
| Maintenance | every service must know its colour | one colour |
| Performance requirement | **no evidence of one** — no measured concurrency need in the identity path | n/a |
| Migration risk | none | none |
| Security risk | two audit transaction boundaries | none introduced |
| Long-term fit | diverges from 53 sync routers | converges on them |

## 7. Recommendation — **Option B**, on the evidence

1. **One genuine async I/O site in 506 async functions.** The async-ness is a
   cascade from an unimplemented contract, not a design requirement.
2. **No measured performance requirement.** Nothing in the repository states or
   tests a concurrency target for identity operations.
3. **Option A guarantees dual architecture**; Phase 6 asks for exactly one.
4. **The conversion already exists**, written by this codebase's own authors for
   the one path that had to work, and it demonstrably returns correct
   authorization decisions.
5. **Option B costs no connections and no migrations.**

## 8. Canonical database access model (Phase 6)

* **Session type** — `sqlalchemy.orm.Session`, synchronous, one per request.
* **Lifecycle** — `Depends(get_db)`; the dependency opens, yields, rolls back on
  exception and closes.
* **Transaction ownership** — the route owns the unit of work; services flush,
  the outermost caller commits.
* **Repository contract** — synchronous methods taking a `Session`.
* **Service contract** — synchronous. A service is `async` only if it performs
  genuine non-database I/O, and then it takes its session as a parameter rather
  than holding one across an await.
* **Testing** — migration-backed tables are tested against migrated PostgreSQL
  (TEST-001), never `create_all`.
* **Background execution** — the worker uses the same sync session per unit of
  work.

## 9. Should the conversion be a separate batch? **Yes.**

460 call sites across 50 modules and 31 test files is not a controlled change,
and the spec's own instruction is to stop at that point. The proposed boundary:

| Batch | Scope | Why this order |
|---|---|---|---|
| **NR-044.1** | `identity/repositories/` (10 modules) + `identity/api/workspaces.py` actor dependency | the leaves, plus the one dependency that unblocks *every* `/niam/*` route | **DONE** |
| **NR-044.2** | `identity/services/` (≈20 modules) | depends on the repositories | pending approval |
| **NR-044.3** | `identity/{trust,admin,governance,compliance,federation,certificates,…}` sub-packages and their routes | depends on the services | pending approval |
| **NR-044.4** | `capabilities/`, `national/`, `services/` stragglers (7 modules) | independent; can run any time after 1 | pending approval |
| **NR-044.5** | test conversion and ledger retirement | last, once the ledger is empty | pending approval |

After NR-044.1 the whole NIAM router's *gate* becomes reachable, so it is the
batch that converts the most blocked surface per line changed. See §12 for what
that did and did not turn out to mean.

## 10. AUTH-005 findings this would unblock

| Finding | Now | After NR-044 |
|---|---|---|
| **NR-038** | PARTIALLY VERIFIED — authorship removed, route unexecutable | eligible for **VERIFIED** once the route can be exercised end to end |
| **AUTH-F5 / NR-043** | PARTIALLY VERIFIED — narrowing correct, `list_eligible` unexecutable | eligible for **VERIFIED**, and the six behavioural cases become writable |
| **NR-039** | VERIFIED | unchanged — synchronous already |
| **NR-040** | VERIFIED | unchanged — synchronous already |
| **NR-035** | VERIFIED | unchanged — legacy auth is synchronous |

None of these may be re-graded before the runtime is repaired.

## 11. The guard

`backend/tests/test_identity_platform_runtime.py` carries an AST-based ledger of
the 50 modules. It accepts exactly two states and refuses the silent middle:

* **an async engine exists** → the test fails deliberately, because the ledger
  has outlived its purpose and must be replaced by a reachability test;
* **no async engine** → the set of modules awaiting a session must equal the
  ledger, so a new unreachable path is a failure and a converted one is a
  prompt to shrink the ledger.

Proven in both directions: adding a module that awaits a session fails with
`['identity/services/_nr044_probe.py'] now await a database session while no
async engine exists`; introducing `create_async_engine` fails with `An async
engine now exists. NR-044's premise has changed`. Both reverted.

It is AST-based rather than grep-based: comments and string literals do not
count, and the session-owner and method names are matched structurally.

## 12. Outcome of NR-044.1 (recorded after implementation)

Converted: the ten modules of `app/identity/repositories/` and the actor
dependency in `app/identity/api/workspaces.py`. Nothing else. No `AsyncEngine`,
no `AsyncSession`, no `asyncpg`, no second pool, no migration, no change to
National Core or AUTH-F10.

### What is now reachable, stated precisely

`get_current_niam_actor` executes against PostgreSQL and returns a correct 401
or a `NiamActor`. Every `/niam/*` route passes through it, so the door opens.
The route handlers in `workspaces.py` are still `async def` and still `await`
`WorkspaceService`, which still annotates `AsyncSession` — so an individual
handler still raises `TypeError` past the gate. **`/niam/*` is gated, not yet
served.** Serving it is NR-044.2 (services) and NR-044.3 (routes). Any claim
that NR-044.1 made the NIAM router work end to end would be false.

Consequently NR-038 and NR-043 stay **PARTIALLY VERIFIED**. Their behavioural
proof needs the service layer, not the gate.

### Two behaviour changes that are not refactors

1. **The gate is stricter than either predecessor.** `get_current_niam_actor`
   (async) did not filter `Account.is_locked`; `get_current_niam_actor_sync`
   did. Converging kept the check, so a locked account is now refused where the
   async twin would have admitted it had it ever been able to run. Pinned by
   `test_a_locked_account_is_refused` against real PostgreSQL.
2. **A latent `ModuleNotFoundError` was fixed.** `IdentityRepositoryBase.count`
   read `from sqlalchemy.func import count`. `sqlalchemy.func` is an attribute
   of the package, not a module, so the import raises. It was invisible while
   the layer could not execute and surfaced on the first real call. Now
   `from sqlalchemy import func`, pinned by
   `test_the_repository_layer_reaches_postgresql`.

### Ledger

`DECLARED_UNREACHABLE_ASYNC_DB_MODULES` shrank from 50 to 40 — exactly the ten
repositories, `added: []`. The guard's two-state contract is unchanged.

### Tests touched, and why

`tests/identity/test_workspace_api_hardening_phase5.py` asserted the actor
dependency was awaitable and handed it a fake session exposing only
`async execute`. Three tests were made synchronous and the fake taught the
`query(...).join(...).filter(...).first()` chain. That file proves the HTTP
boundary against a fake and cannot prove a predicate — which is precisely how
the missing `is_locked` filter stayed out of sight. The predicates are proved
against migrated PostgreSQL in `tests/test_identity_link_and_assurance.py`.

## 13. NR-044.1 final verification (evidence-based closeout)

NR-044.1 was re-examined against the standard that a conversion is proved by
running it, not by reading it. No application code changed: `git status` for
`backend/app/` is empty against the commit under test. What changed is the
strength of the guard and the depth of the runtime proof.

**Classification: PARTIALLY VERIFIED.** Everything below passed except one
thing, and that one thing is load-bearing enough to withhold the grade.

### What is now proved rather than asserted

| Invariant | How |
|---|---|
| One engine architecture | `database.engine` and the optional `read_engine` are both `sqlalchemy.engine.Engine`; `SessionLocal`/`ReadSessionLocal` bind to them; **no** module under `app/identity/` constructs an engine or a `sessionmaker` |
| No `AsyncEngine` | zero `create_async_engine` in `app/` |
| No second pool | the guard above; the read replica is the same synchronous `create_engine`, off by default, and predates NR-044 |
| The actor takes the canonical session | `typing.get_type_hints` resolves `db` to `sqlalchemy.orm.Session` (not a string compare), and its default resolves to `get_db`, which is a plain generator |
| Genuine async I/O preserved | the `httpx.AsyncClient` call in `identity/admin/services.py` is still async — Option B converts database colour, not I/O colour |
| Ledger exact | 40 modules, two-state contract unchanged; `add` added to the watched methods |

### Runtime, on migrated PostgreSQL 16.13, through the real dependency graph

Authentication: unauthenticated → 401; malformed token → 401; foreign-signed
token → 401; expired token → 401 **with the session row still live**, which
proves the refusal comes from claim validation rather than a missed lookup;
locked, suspended, revoked-session, wrong-jti and cross-account actors all
refused.

Authorization: an eight-step denial ladder through
`ClinicalGatewayContextResolver`, each step provoked by a real row and each
naming a *different* boundary — `missing_workspace` → `workspace_inactive` →
`invalid_context` (organization suspended) → `invalid_context` (facility
suspended) → `membership_missing` → `membership_missing` for a membership in
another organization → `legacy_identity_unresolved`. A resolver that had
stopped executing could not produce that sequence; it would raise the same
error every time. Tenant isolation and NR-035's `source_kind` discriminator are
both proved inside that ladder.

Transaction: the gate, both repositories and the resolver hold the *same*
`Session`; a row flushed but uncommitted through one is visible through the
others; the transaction is still open afterwards. No parallel database path.

Negative proof, four reversible perturbations, all restored: async actor → 18
failures across three files; one repository reverted → 4; an `AsyncEngine`
introduced → 3; a second `sessionmaker` inside `app/identity/` → 1.

### Why not VERIFIED

The authorization **allow** path could not be exercised, because of a defect the
verification itself found: **NR-045**. `CanonicalAuditService.record()` inserts
into `niam_audit_entries` without the NOT NULL `uuid`, so the insert always
violates the constraint. The clinical gateway audits before it allows *and*
before it denies, so **every** `/api/v1/clinical/*` request answers 503. It
fails closed — nothing leaks — but the gateway is inert and its canonical audit
trail is empty.

This is not caused by NR-044.1; it was simply unreachable behind a gate that
could not authenticate, and invisible to tests that monkeypatch the audit call.
It is registered, pinned by a test that asserts the defect, and left unfixed
because fixing it is outside NR-044.1's scope.

**NR-046** was also found: the actor dependency never consults
`UserSession.expires_at`. Also pre-existing — the converted query is
byte-for-byte the old `get_current_niam_actor_sync`, and the async twin omitted
it too. Exposure is bounded by the access token's own `exp`, which *is*
enforced.

### What stays open, and why no dependent finding was closed

* **NR-038** — PARTIALLY VERIFIED. Its route is still unexecutable (NR-044.3).
* **AUTH-F5 / NR-043** — PARTIALLY VERIFIED. `list_eligible` is still
  unexecutable (NR-044.2).
* **NR-035** — unchanged and independently re-proved on the clinical path: a
  `user`-kind legacy link is refused where a `lab_user` link is required.

Closing any of these on the strength of NR-044.1 would be closing them on the
gate rather than on the thing each one actually asserts.
