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

## 14. NR-045 repaired, and what it revealed (NR-047)

### The defect, exactly

`niam_audit_entries.uuid` is `NOT NULL` with no server default, and
`IdentityBaseEntity` supplies `id`, `created_at` and `updated_at` but not
`uuid`. `AuditService` (event_version 1) passed one explicitly;
`CanonicalAuditService` (event_version 2) did not. Every v2 insert therefore
violated the constraint — and because the clinical gateway audits before it
allows *and* before it denies, **every** `/api/v1/clinical/*` request answered
503.

### Are the two services the same contract?

No, and that settles the repair. They are two generations over one table,
separated by `event_version`, each with its own chain head lookup
(`_last_canonical_hash` filters `event_version == "2"`), its own hash payload,
and its own verifier. v2's payload carries `decision`, `reason_code`,
`workspace_id`, `data_classification`, `request_id` and `correlation_id` —
fields v1 has no concept of and which the gateway depends on. Consolidating v2
into v1 would destroy them and invalidate every existing v2 hash. So the repair
is to satisfy the existing schema contract, not to merge the services.

### The repair

One line, on the column:

```python
uuid = Column(String(36), unique=True, nullable=False, index=True, default=_audit_entry_uuid)
```

Why the column rather than the service: it makes **one** place authoritative for
every writer of this table, instead of adding a second generator beside v1's.
`AuditService` still passes its own value, which takes precedence, so v1 is
byte-identical. `uuid` is deliberately absent from `_canonical_payload`, so
populating it cannot alter any entry hash, past or future.

No migration: a Python-side default emits no DDL — the compiled column is still
`uuid VARCHAR(36) NOT NULL`. No constraint weakened, no field made nullable, no
second hash-chain implementation, no separate commit, no change to the
gateway's fail-closed behaviour.

### What is now proved

Against migrated PostgreSQL 16.13: the insert succeeds with a canonical uuid4
and a populated `entry_hash`; two consecutive entries chain correctly and
`verify()` returns `VALID` with zero violations; the audit row is visible inside
its own transaction and **absent from another connection after rollback**;
`record()` never commits. End to end over real HTTP, the gateway now answers
**403 where it answered 503**, with the denial readable in `niam_audit_entries`
(`decision=deny`, `reason_code=missing_workspace`, `source=clinical_gateway`).

Negative proof: removing the column default fails six tests; restored.

### NR-047 — the wall the ALLOW path actually hits

With NR-045 repaired, a fully authorized fixture was assembled: active account,
live session, active workspace bound to that session, active NIAM organization
and facility, an active membership, a migrated `lab_user` link, an active
lab-to-facility binding, an active employment and clinical assignment, and the
seeded `patients.read` permission granted through a role assignment in exactly
that scope.

It still does not reach 200 — and not for an authorization reason.
`ClinicalAuthorizationContextService` selects the `Organization` entity, whose
ORM declares `org_id`, `org_type`, `parent_org_id` and `updated_at` while the
migrated `organizations` table has `organization_id`, `organization_type` and
neither of the last two. PostgreSQL answers `UndefinedColumn`; the resolver's
`except Exception` converts it to `invalid_context`.

That is **NR-047**, registered P1 against National Core / operational models. It
is unrelated to NR-044.1 and unrelated to NR-045, and reconciling an operational
domain's ORM to its migration is outside this batch's scope — it is the same
shape of work M3/M4 did for Pharmacy, and probably belongs with NR-022.

**So NR-044.1 stays PARTIALLY VERIFIED.** The blocker moved and became far more
precisely located, but the ALLOW half is still unproven, and half an
authorization proof is not a verified conversion.

## 15. NR-044.2 — the service layer executes (recorded after implementation)

### 15.1 What was measured first

The ledger was re-derived from source before anything was edited. Eighteen
modules under `app/identity/services/` annotated `AsyncSession`; sixteen of them
awaited a session directly and were in the ledger, and two more
(`authentication_service.py`, `authorization_service.py`) awaited only
repositories — which NR-044.1 had already made synchronous, so they were broken
*by* that batch rather than in spite of it.

Classification of every remaining item, by the rule the batch was given:

| Class | Meaning | Count |
| --- | --- | --- |
| **A** — DB-only async, convert | no `asyncio`, no `httpx`, no `async with`, no `async for`; every await is a database call or a call to another converted function | **18 of 18** in `identity/services`, plus `services/clinical_scope_bridge_service.py` (a direct dependency of a converted service) |
| **B** — DB plus genuine async I/O | — | **0** |
| **C** — no database, deliberate async seam | `OrganizationVerificationProvider.verify` and the `verification_service.py` provider protocol: not-connected stubs that hold no session and exist as the boundary where a future external HTTP call will land | **2**, left async |

There was no judgement call inside the scope. A grep for `asyncio`, `httpx`,
`aiohttp`, `anyio`, `async with` and `async for` across all 27 files in
`identity/services/` returns only the `AsyncSession` import lines themselves.

### 15.2 What changed

* **`identity/services/` (16 modules, 109 `async def`, 245 `await`)** — converted
  to the synchronous `Session`. Authentication, accounts, persons, sessions,
  devices, memberships, workspaces, consents, incidents, legacy mapping, the
  clinical authorization context, the authorization decision service, the RBAC
  service and both audit writers.
* **`services/clinical_scope_bridge_service.py`** — converted. It is awaited by
  `ClinicalAuthorizationContextService`, so it had to move with it.
* **`identity/api/` (13 modules)** — converted. Two reasons, and the second is
  the important one. Its handlers call the services, so the call sites had to
  change; and a handler left as `async def` while calling a now-synchronous
  service would run blocking psycopg work **on the event loop**, which is worse
  than the unreachable code it replaced. FastAPI runs a plain `def` handler in a
  threadpool, which is where blocking database work belongs. The one handler
  left `async` is `niam_health`, which touches nothing.
* **`identity/policy_engine.py`** — converted; it is a thin facade over
  `AuthorizationDecisionService`.
* **`clinical_gateway/session_facade.py` — deleted.** `SyncSessionAsyncFacade`
  wrapped a synchronous `Session` in awaitable methods so the gateway could reuse
  the async identity services, and the gateway drove them with `asyncio.run()` —
  a fresh event loop per authorization and per audit write, inside a request.
  With the services synchronous, the shim and the loops are gone and the gateway
  passes its own `Session` straight through.

Four `AsyncSession` annotations on parameters fed by `Depends(get_db)` were
removed along the way. That annotation was the original lie: it said one thing
and the provider did another, which is how NR-044 stayed invisible for so long.

### 15.3 Ledger movement

40 modules → **20**. Twenty-one removed, **none added**, and one *discovered*.

What remains is the identity sub-package layer — `trust`, `admin`, `compliance`,
`federation`, `governance`, `notifications`, `certificates`, `adaptive_auth`,
`bootstrap`, `workflows` — plus `capabilities/` (4), `national/` (2) and
`reference/` (1). That is NR-044.3.

### 15.4 Two findings this batch produced

**NR-048 — the gateway reported any internal fault as an authorization denial.**
`ClinicalGatewayContextResolver.resolve` caught `Exception` and converted
everything into `invalid_context`, rendered as 403. That is precisely how NR-047
presented: `column organizations.org_id does not exist` reached the client as
what looked like a policy decision, and was written into the immutable audit
chain as one. NR-044's `TypeError` was swallowed by the same handler. The catch
is now `(ClinicalAuthorizationContextError, ClinicalScopeBridgeError)` — the two
vocabularies that actually mean "refused". Anything else propagates and surfaces
as a 500: still denied, but as a fault rather than as a decision. Fixed here
because the spec permits changing exception semantics where the current
behaviour is demonstrably incorrect and directly related — and NR-047 is the
demonstration.

**NR-049 — the ledger had a blind spot, and it had one all along.** The AST
guard matched a session owner only as a bare name or an attribute chain ending
`.session` / `.db`. `app/reference/infrastructure/repositories.py` stores its
session on `self._session` and awaits it twenty-odd times, so the guard had
never seen it. Widening the rule to `._session` and `.facade` raised the count
from 19 to 20. The guard is fixed here; converting the module belongs to
NR-044.3. A guard that under-reports is how this whole finding stayed hidden in
the first place, so the correction matters more than the one module it found.

### 15.5 Evidence

Against migrated PostgreSQL 16.13, single head `20260913_0001`, **no migration
and no schema change in this batch**.

| Proof | Where |
| --- | --- |
| Authentication success — login mints a session row, read back from PostgreSQL | `test_the_authentication_service_now_logs_in_against_postgresql` |
| Authentication denial — wrong password, no session row, failure counter incremented | `test_a_wrong_password_is_denied_and_creates_no_session` |
| Unknown login denied | `test_an_unknown_login_is_denied_without_a_session` |
| Suspended account refused despite a correct password | `test_a_suspended_account_cannot_authenticate_even_with_the_right_password` |
| Lockout honoured while `locked_until` is future, released after | `test_a_locked_account_within_its_lockout_window_cannot_authenticate` |
| Session lifecycle — logout terminates the real row | `test_logout_terminates_the_real_session_row` |
| Workspace eligibility, and citizen-workspace idempotency | `test_the_workspace_service_reads_eligibility_from_postgresql` |
| Authorization ALLOW — HTTP 200, read executes | `test_a_fully_authorized_actor_is_allowed_and_the_read_executes` |
| Authorization DENY ladder — each boundary broken alone from the allowing context | `test_every_denial_boundary_still_holds_from_an_otherwise_valid_context` |
| Audit on an allowed read, valid hash chain | `test_an_allowed_read_is_audited_with_a_valid_chain` |
| Audit on a denial | `test_a_valid_actor_passes_the_gate_and_the_denial_is_audited` |
| Tenant isolation | `test_tenant_isolation_matrix.py`, and the cross-tenant rungs of the denial ladder |
| NR-048 both directions | `test_a_database_fault_is_no_longer_reported_as_a_policy_denial`, `test_a_genuine_context_denial_is_still_translated_to_invalid_context` |
| One engine, one sessionmaker, no `create_async_engine` | `test_exactly_one_database_engine_architecture_exists` |
| Service layer synchronous, seams exempted explicitly | `test_the_identity_service_layer_is_synchronous` |
| No blocking DB work on the event loop | `test_the_identity_api_layer_does_not_block_the_event_loop` |
| The facade and its event loops stay deleted | `test_the_session_facade_shim_is_gone_and_stays_gone` |

Full backend suite: **2916 passed, 173 skipped, 0 failed**.

### 15.6 What may not yet be re-graded

**NR-038** (client-authored assurance level) and **AUTH-F5 / NR-043** (workspace
eligibility ignoring the organization's standing) stay **PARTIALLY VERIFIED**.
`WorkspaceService.list_eligible` is now executable and proven, which is half of
NR-043; but `identity/trust/services.py` — where the assurance writer lives and
where the trust routes consume eligibility — is still in the ledger. Promoting
either on the strength of NR-044.2 alone would be claiming a proof that has not
been run.

## 16. NR-044.3 — the ledger closes, and what closing it exposed

### 16.1 The classification, re-derived before anything was edited

The ledger was rebuilt from source with a stronger detector (§16.2), then every
candidate was classified with evidence rather than by directory:

| Class | Meaning | Items |
| --- | --- | --- |
| **A** — DB-only async, convert | 20 modules | 13 identity sub-package modules (trust, admin, compliance, federation, governance, notifications, certificates, adaptive_auth, bootstrap, workflows and their routes), `reference/infrastructure/repositories.py`, the two `national/` repositories and their application and route layers |
| **B** — DB plus genuine async I/O | **1 method** | `EnterprisePortalService.test_fhir_connection` |
| **C** — deliberate non-DB async seam | 2 | `OrganizationVerificationProvider.verify`, the `verification_service` protocol (unchanged from NR-044.2) |
| **D** — dead, evidenced | 4 | `capabilities/*/infrastructure/repository.py` |
| **E** — false positive | 8 | seven identity route modules and `reference/infrastructure/dependencies.py`, which annotated `AsyncSession` without awaiting a session; annotation corrected |

Ledger: **20 → 4**.

**The two `national/` repositories were nearly classified D, and that would have
been wrong.** They import `backend.app.database.SessionLocal`, which raises
`ModuleNotFoundError: No module named 'backend'` under a bare interpreter rooted
at `backend/`. It would have been easy to record that as proof of death. But
`PYTHONPATH` includes the repository root in CI and under pytest, so they import
fine where it counts — and `factory.py` registers both their routers. They were
reachable, broken endpoints: `async with SessionLocal()` on a *synchronous*
sessionmaker, which has no `__aenter__` and would fail even after the import
resolved. They were converted. The guard now measures importability in the
environment the application actually runs in, and says so.

The four that remain are genuinely dead: every module of those ten capability
packages raises `ModuleNotFoundError` (NR-050). Converting them would mean
repairing code no interpreter can load, and whether that tree lives or is retired
is its owner's decision.

### 16.2 NR-049: the detector stopped guessing

The old rule matched session owners by string — `.session`, `.db` — which is why
`reference/infrastructure/repositories.py` (`self._session`) had been invisible
since the ledger was written. Widening the list would only have moved the blind
spot to the next name someone chose.

Ownership is now *resolved*: every `__init__` is read, any parameter whose
annotation mentions `Session` is treated as one, and the attribute it is assigned
to becomes an owner for that module. A session called `self.whatever` is caught;
an unrelated `self.result_db` that was never assigned a Session is not. Both
halves are asserted.

### 16.3 The one Class B boundary

`EnterprisePortalService.test_fhir_connection` performs a genuine
`httpx.AsyncClient` call to an external FHIR server, between two database
statements. Per the Class B rule its **database work was converted and its HTTP
boundary was not**: it is the only coroutine left in `identity/`, and
`admin/routes.py` still awaits it — only it. The test asserts exactly that, by
AST, so a second coroutine cannot appear unnoticed.

A follow-up option is recorded rather than taken: switching it to `httpx.Client`
would let the whole method be a plain `def` running in FastAPI's threadpool,
which is more consistent with the architecture. That changes real I/O colour, so
it is the user's call, not a conversion to make on the way past.

### 16.4 NR-052 — a control that failed closed by crashing

Proving NR-038 meant calling `_require_assurance_administrator` for the first
time. It raised `AttributeError: type object 'Assignment' has no attribute
'account_id'`.

An assignment belongs to a *person*; an account reaches one through
`Account.identity_id → IdentityRecord.person_id`. So the gate deciding who may
assert an assurance profile for another account had never evaluated. It failed
closed — the error propagates and the request is refused — but as a 500, and the
rule it was supposed to enforce was untested. It now joins through the identity
and keeps that identity's own standing in the conjunction.

This is the third finding in this sequence (with NR-045 and NR-048) that existed
only because the code could not run. That is the argument for this whole
programme in one line: unreachable code is not safe code, it is unexamined code.

### 16.5 NR-038 and AUTH-F5/NR-043, re-graded on evidence

Both had been PARTIALLY VERIFIED since AUTH-005 for the same reason — correct
code that could not execute. Both are now **FIXED — VERIFIED**, against migrated
PostgreSQL:

* **NR-038** — no verification record yields floor assurance; only a record
  written through the real `VerificationWorkflow` state machine raises it; the
  overall is the weakest axis, so a raised IAL does not lift the profile while
  AAL and FAL sit at the floor; asserting for another account is refused 403.
* **NR-043** — an active representative is offered the organization's workspace;
  deactivating the organization removes it; suspending it removes it too. One
  fact changes between assertions, so the predicate is what is proved.

AUTH-F5's open half — whether membership should confer eligibility — is a policy
decision and is untouched.

### 16.6 Evidence

Focused suites, migrated PostgreSQL 16.13, **no migration and no schema change**:
link-and-assurance 60 → **65**, runtime ledger 16 → **14** (three rewritten, three
added), extensibility guards **41**, niam suites **89**.

Negative proofs, each restored: re-introducing an async DB call in a converted
module fails the ledger; re-introducing the NR-049 `self._session` shape fails it
too; restoring `Assignment.account_id` fails the NR-038 gate test; and the four
PROGRAM-EXT-001 perturbations still catch.

The extensibility guards are now gated in CI — one path added to the IAM
workflow's backend job, no new workflow, no `continue-on-error`, no trigger
change.
