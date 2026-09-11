"""AUTH-005 Phase 2: which identity controls can actually execute.

A control that cannot run is not a control. AUTH-005 set out to prove
server-authoritative assurance at the service and database level rather than by
reading a function signature — and doing so surfaced why the signature was all
there was to read.

`get_db` yields a synchronous `sqlalchemy.orm.Session`. Thirty-six modules under
`app/identity/` annotated `AsyncSession` and `await session.execute(...)`, and no
`create_async_engine` exists anywhere in `app/`. Awaiting a sync result raises
`TypeError: object ChunkedIteratorResult can't be used in 'await' expression`
before any statement reaches the database.

So the NIAM async service layer — the trust/assurance routes, workspace
eligibility, membership, the repositories — was unreachable at runtime. That is
recorded as NR-044 and is being closed in batches against the synchronous
architecture the application already has (Option B: no second engine, no second
pool, no second transaction boundary):

* NR-044.1 converted the repositories and the actor dependency.
* NR-044.2 converted `identity/services/` (16 modules), `identity/api/`,
  `identity/policy_engine.py` and `services/clinical_scope_bridge_service.py`,
  and deleted `SyncSessionAsyncFacade` — the shim that made a synchronous
  Session look awaitable so the clinical gateway could drive async services
  through `asyncio.run()`. The ledger below fell from 40 modules to 20.
* NR-044.3 owns what remains: the identity sub-packages (trust, admin,
  compliance, federation, governance, notifications, certificates,
  adaptive_auth, bootstrap, workflows), `capabilities/`, `national/` and
  `reference/`.

NR-044 reframes two earlier findings rather than excusing them:

* NR-038 was never exploitable. The route raised before writing a row, so the
  client-authored assurance level could not be persisted. Removing the client's
  authorship is still correct and is still pinned, but the claim "latent behind
  NIAM authentication" was too generous — it is latent behind a type error.
* The AUTH-005 workspace-eligibility narrowing (NR-043) is correct code in a
  function that cannot currently run.

The synchronous half *does* run and is where the clinical risk lives:
`CitizenRelationshipService`, `identity_link_policy` and `verification_workflow`
are all sync, reachable, and proven against migrated PostgreSQL in
`test_identity_link_and_assurance.py`. Since NR-044.2 the authentication,
workspace, membership, authorization-decision and canonical-audit services are
in that half too.

These tests pin the defect. When a batch fixes part of it they fail, which is
the signal to rewrite them to pin the resolution — not to delete them. That has
now happened twice.
"""

from __future__ import annotations

import ast
import inspect
import pathlib
import typing

import pytest
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

APP = pathlib.Path(__file__).resolve().parents[1] / "app"


def test_get_db_yields_a_synchronous_session() -> None:
    from app.database import get_db

    assert not inspect.isasyncgenfunction(get_db), (
        "get_db became an async generator; NR-044 may be resolved — re-derive these tests"
    )


def test_no_async_engine_exists_anywhere_in_the_application() -> None:
    """The root of it. Async sessions need an async engine; there is none."""
    users = sorted(
        path.relative_to(APP).as_posix()
        for path in APP.rglob("*.py")
        if "__pycache__" not in path.parts
        and "create_async_engine" in path.read_text(encoding="utf-8", errors="ignore")
    )
    assert users == [], (
        f"an async engine now exists ({users}); NR-044 is moving and the identity "
        "platform's async services may be reachable — re-derive these tests"
    )


def test_the_unconverted_async_surface_matches_the_ledger() -> None:
    """Scope, measured the same way in both tests.

    An earlier version counted with a regex over `.execute(` while the ledger
    was built by AST over every session method, so the two disagreed (33 vs 40)
    the moment the numbers mattered. There is one definition now:
    `_modules_awaiting_the_database`.
    """
    modules = _modules_awaiting_the_database()
    assert modules == DECLARED_UNREACHABLE_ASYNC_DB_MODULES, (
        "the unconverted async surface and the ledger disagree; NR-044 batches "
        "must shrink both together"
    )

    # Still unconverted — and every one of them is dead, which is why. Named
    # here so that if any of them ever becomes importable, this list is the
    # thing that has to be re-derived rather than quietly carried forward.
    for expected in (
        "capabilities/document_management/infrastructure/repository.py",
        "capabilities/workflow_engine/infrastructure/repository.py",
    ):
        assert expected in modules, (
            f"{expected} no longer awaits a session — re-derive the ledger and its "
            "D classification"
        )
    # Converted by NR-044.1, .2 and .3, and therefore required to be absent.
    for converted in ("identity/repositories/base.py",
                      "identity/repositories/account_repository.py",
                      "identity/services/workspace_service.py",
                      "identity/services/membership_service.py",
                      "identity/services/canonical_audit.py",
                      "identity/services/authorization_decision.py",
                      "identity/api/memberships.py",
                      "identity/api/roles.py",
                      "identity/trust/services.py",
                      "identity/trust/routes.py",
                      "identity/admin/services.py",
                      "identity/governance/services.py",
                      "identity/compliance/services.py",
                      "identity/federation/services.py",
                      "identity/certificates/services.py",
                      "identity/adaptive_auth/services.py",
                      "identity/notifications/services.py",
                      "identity/workflows/engine.py",
                      "identity/bootstrap/seed.py",
                      "reference/infrastructure/repositories.py",
                      "national/task_engine/infrastructure/repository.py",
                      "national/workflow_runtime/infrastructure/repository.py",
                      "services/clinical_scope_bridge_service.py"):
        assert converted not in modules, (
            f"{converted} awaits a session again; the NR-044 conversion has regressed"
        )


@pytest.mark.asyncio
async def test_awaiting_a_result_from_the_session_get_db_yields_raises() -> None:
    """The behavioural proof AUTH-005 Phase 2 asked for.

    Not a signature check and not Pydantic. This performs the exact operation
    every one of those thirty-six modules performs — `await session.execute(...)`
    on the session type the application actually supplies — and shows it raising
    before any result can be used.

    Probed with `SELECT 1` deliberately: the failure is in the session
    primitive, not in any one table or service, so proving it this way does not
    depend on which schema happens to be bound.
    """
    from app.database import SessionLocal
    from sqlalchemy import text

    session = SessionLocal()
    try:
        with pytest.raises(TypeError, match="can't be used in 'await' expression"):
            await session.execute(text("SELECT 1"))
    finally:
        session.close()


def test_the_assurance_service_no_longer_depends_on_a_broken_primitive() -> None:
    """NR-044.3 — the inverse of what this test used to assert.

    It previously pinned the defect: `AssuranceService.derive_profile` was a
    coroutine awaiting a session that is not awaitable, which is why NR-038 was
    never exploitable — the route raised before a client-authored assurance
    level could be persisted. The premise has changed, so the assertion is
    inverted rather than deleted.

    Note carefully what this does and does not prove. It proves the assurance
    service can now execute. It does NOT promote NR-038: that needs the route's
    own behaviour proved against real PostgreSQL, which is a separate piece of
    evidence, and the absence of an exception is not the presence of a control.
    """
    from app.identity.trust.services import AssuranceService

    assert not inspect.iscoroutinefunction(AssuranceService.derive_profile), (
        "the assurance service is a coroutine again; it would stop reaching the database"
    )
    source = inspect.getsource(AssuranceService._verification_results)
    assert "await " not in source, (
        "the assurance service awaits again — NR-044.3 has regressed for this path"
    )
    assert "self.session.execute(" in source


def test_every_remaining_ledger_module_is_provably_unimportable() -> None:
    """The D classification, asserted rather than asserted-to-have-been-checked.

    NR-044.3 left six modules unconverted and classified them dead. "Dead" is a
    claim about the world, so it is checked here on every run: each one must
    still raise ModuleNotFoundError naming the root that does not exist. If one
    starts importing, it is no longer dead, and its disposition has to be
    re-derived rather than inherited.
    """
    import importlib

    assert set(DECLARED_UNIMPORTABLE) == DECLARED_UNREACHABLE_ASYNC_DB_MODULES, (
        "the ledger and the unimportability evidence disagree"
    )
    for module_path, missing_root in DECLARED_UNIMPORTABLE.items():
        dotted = "app." + module_path.removesuffix(".py").replace("/", ".")
        with pytest.raises(ModuleNotFoundError) as failure:
            importlib.import_module(dotted)
        assert missing_root in str(failure.value), (
            f"{dotted} no longer fails on {missing_root!r} — re-derive its classification"
        )


def test_the_detector_sees_a_session_held_under_any_attribute_name() -> None:
    """NR-049, as a property of the detector rather than a patched string list.

    The old detector matched owners by suffix — `.session`, `.db` — and so could
    not see `reference/infrastructure/repositories.py`, which uses
    `self._session`. Widening the list would have moved the blind spot to the
    next name someone chose. Ownership is resolved from the `__init__`
    annotation now, so the attribute may be called anything.

    Both halves are asserted: an oddly-named session IS seen, and an unrelated
    attribute that was never assigned a Session is NOT.
    """
    import ast as _ast

    seen = _ast.parse(
        "class R:\n"
        "    def __init__(self, session: AsyncSession) -> None:\n"
        "        self._quite_unusual_name = session\n"
        "    async def go(self):\n"
        "        await self._quite_unusual_name.execute('x')\n",
    )
    owners = _session_owners(seen)
    assert "self._quite_unusual_name" in owners
    assert any(
        isinstance(n, _ast.Await) and _awaits_a_session_call(n, owners)
        for n in _ast.walk(seen)
    ), "a session held under an unusual attribute name is invisible to the detector again"

    unrelated = _ast.parse(
        "class R:\n"
        "    def __init__(self, cache) -> None:\n"
        "        self.result_db = cache\n"
        "    async def go(self):\n"
        "        await self.result_db.get('x')\n",
    )
    unrelated_owners = _session_owners(unrelated)
    assert "self.result_db" not in unrelated_owners
    assert not any(
        isinstance(n, _ast.Await) and _awaits_a_session_call(n, unrelated_owners)
        for n in _ast.walk(unrelated)
    ), "an attribute that merely ends in .db is being counted as a session again"


def test_the_clinically_significant_path_is_synchronous_and_reachable() -> None:
    """What *does* run, and is therefore what AUTH-005 had to get right.

    Health-identity linkage is the security boundary with patient consequences.
    It is synchronous end to end — route, workflow, policy and workflow writer —
    so its controls execute, and are proven against migrated PostgreSQL.
    """
    for module in (
        "routes/citizen_relationship_admin.py",
        "identity/services/citizen_relationship_service.py",
        "identity/services/identity_link_policy.py",
        "identity/services/verification_workflow.py",
    ):
        source = (APP / module).read_text(encoding="utf-8")
        assert "AsyncSession" not in source, f"{module} became async; its controls would stop executing"
        assert "await " not in source, f"{module} gained an await; re-verify it can still run"


# ── NR-044 permanent guard ───────────────────────────────────────────────────

# Every module that performs `await <session>.<db method>()`, found by AST so
# that comments and string literals do not count. While no async engine exists,
# each of these is an unreachable database path. The ledger makes the set
# explicit: adding a module is a review, and removing them all is the signal
# that the architecture decision was executed.
DECLARED_UNREACHABLE_ASYNC_DB_MODULES = frozenset({
    # Four modules remain, and each is unreachable twice over: it awaits a
    # session that is not awaitable, AND its own package raises
    # `ModuleNotFoundError: No module named 'document_management'` — the
    # capability `__init__` uses a bare top-level import that resolves against
    # nothing. Converting them would be repairing code no interpreter can load.
    # That whole tree is NR-050, a decision that belongs to its owner, so
    # NR-044.3 classified these D (dead, evidenced) and left them.
    "capabilities/document_management/infrastructure/repository.py",
    "capabilities/encounter_management/infrastructure/repository.py",
    "capabilities/provider_management/infrastructure/repository.py",
    "capabilities/workflow_engine/infrastructure/repository.py",
})

#: The evidence for the D classification, asserted on every run rather than
#: taken on trust. "Dead" is a claim about the world; if one of these starts
#: importing it is no longer dead and its disposition must be re-derived.
#:
#: The two `national/*` repositories were nearly classified D on the same
#: evidence and it would have been wrong. They import
#: `backend.app.database.SessionLocal`, which fails under a bare interpreter
#: rooted at `backend/` — but PYTHONPATH includes the repository root in CI and
#: under pytest, so they import fine where it counts, and their routers are
#: registered in `factory.py`. They were reachable, broken endpoints, not dead
#: code, and NR-044.3 converted them. The lesson is in the guard: importability
#: is measured in the environment the application actually runs in.
DECLARED_UNIMPORTABLE = {
    "capabilities/document_management/infrastructure/repository.py": "document_management",
    "capabilities/encounter_management/infrastructure/repository.py": "encounter_management",
    "capabilities/provider_management/infrastructure/repository.py": "provider_management",
    "capabilities/workflow_engine/infrastructure/repository.py": "workflow_engine",
}

_DB_METHODS = frozenset({
    "execute", "commit", "flush", "refresh", "scalars", "scalar",
    "get", "delete", "merge", "stream", "rollback", "close", "begin",
    "begin_nested", "connection",
    # `add` is synchronous on AsyncSession too, so `await session.add(...)` is
    # always wrong. Listing it costs nothing today (it matches nothing) and
    # closes the hole if someone writes it tomorrow.
    "add",
})

#: Bare parameter names that are a session when nothing better is known. The
#: ownership analysis below is the primary mechanism; this is the fallback for
#: module-level functions that take a session as an argument.
_SESSION_PARAM_NAMES = frozenset({"session", "db", "sess", "_session", "_db"})


def _attr_chain(node) -> str:

    parts = []
    while isinstance(node, ast.Attribute):
        parts.append(node.attr)
        node = node.value
    if isinstance(node, ast.Name):
        parts.append(node.id)
    return ".".join(reversed(parts))


def _session_owners(tree) -> set[str]:
    """Resolve what actually holds a session in this module, by annotation.

    NR-049 exists because the previous version of this detector matched owner
    names by string — `.session` and `.db` — and so could not see
    `reference/infrastructure/repositories.py`, which keeps its session on
    `self._session`. Widening the string list would only move the blind spot:
    the next module to name it `self._sess` or `self.conn` would be invisible
    again, and an unrelated attribute that happened to end in `.db` would be a
    false positive.

    So ownership is derived instead of guessed. Every `__init__` is read, any
    parameter whose annotation mentions `Session` is treated as a session, and
    the attribute it is assigned to becomes an owner for this module. A module
    that calls its session `self.whatever` is caught; a module with an unrelated
    `self.audit_db` that was never assigned a Session is not.
    """

    owners: set[str] = set(_SESSION_PARAM_NAMES)
    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        annotated_sessions = {
            arg.arg
            for arg in node.args.args + node.args.kwonlyargs
            if arg.annotation is not None and "Session" in ast.unparse(arg.annotation)
        }
        owners |= annotated_sessions
        if node.name != "__init__":
            continue
        for stmt in ast.walk(node):
            if not (isinstance(stmt, ast.Assign) and isinstance(stmt.value, ast.Name)):
                continue
            if stmt.value.id not in annotated_sessions:
                continue
            for target in stmt.targets:
                if (
                    isinstance(target, ast.Attribute)
                    and isinstance(target.value, ast.Name)
                    and target.value.id == "self"
                ):
                    owners.add(f"self.{target.attr}")
    return owners


def _awaits_a_session_call(await_node, owners: set[str]) -> bool:

    value = await_node.value
    if not (isinstance(value, ast.Call) and isinstance(value.func, ast.Attribute)):
        return False
    chain = _attr_chain(value.func)
    owner, _, method = chain.rpartition(".")
    if method not in _DB_METHODS:
        return False
    return owner in owners


def _modules_awaiting_the_database() -> set[str]:

    found = set()
    for path in APP.rglob("*.py"):
        if "__pycache__" in path.parts:
            continue
        try:
            tree = ast.parse(path.read_text(encoding="utf-8", errors="ignore"))
        except SyntaxError:
            continue
        owners = _session_owners(tree)
        if any(isinstance(n, ast.Await) and _awaits_a_session_call(n, owners) for n in ast.walk(tree)):
            found.add(path.relative_to(APP).as_posix())
    return found


def _an_async_engine_exists() -> bool:
    return any(
        "create_async_engine" in path.read_text(encoding="utf-8", errors="ignore")
        for path in APP.rglob("*.py")
        if "__pycache__" not in path.parts
    )


def test_no_async_database_call_exists_without_an_async_engine() -> None:
    """The guard NR-044 leaves behind, whichever way the decision goes.

    Two states are correct and this test accepts exactly one of them at a time:

    * an async engine exists, and async database calls are legitimate — the
      assertion below then fails deliberately, because the ledger has outlived
      its purpose and must be replaced by a reachability test;
    * no async engine exists, and the set of modules awaiting a session is
      exactly the recorded ledger.

    What it refuses is the silent middle: a new module awaiting a session that
    cannot execute, added without anyone noticing.
    """
    actual = _modules_awaiting_the_database()

    if _an_async_engine_exists():
        pytest.fail(
            "An async engine now exists. NR-044's premise has changed: these modules "
            "may be reachable. Replace this ledger with a reachability test rather "
            "than extending it."
        )

    added = sorted(actual - DECLARED_UNREACHABLE_ASYNC_DB_MODULES)
    removed = sorted(DECLARED_UNREACHABLE_ASYNC_DB_MODULES - actual)
    assert not added, (
        f"{added} now await a database session while no async engine exists, so they "
        "cannot execute. Either convert them to the synchronous Session the "
        "application actually provides, or resolve NR-044 first."
    )
    assert not removed, (
        f"{removed} no longer await a session — the NR-044 conversion is underway. "
        "Remove them from DECLARED_UNREACHABLE_ASYNC_DB_MODULES so the ledger keeps "
        "its meaning."
    )


def test_the_niam_actor_dependency_is_one_synchronous_function() -> None:
    """NR-044.1 — the precedent became the rule.

    There were two actor dependencies differing only in colour: an async one
    guarding every `/niam/*` route that could never execute, and a sync one
    written for the clinical gateway because that path had to work. There is one
    now, it is synchronous, and the old name is an alias for it.

    The sync implementation also filtered on `Account.is_locked`, which the
    async twin omitted. Adopting it tightened the gate; that behaviour is
    asserted against the migrated schema in
    tests/test_identity_link_and_assurance.py.
    """
    from app.identity.api import workspaces

    assert not inspect.iscoroutinefunction(workspaces.get_current_niam_actor), (
        "the NIAM actor dependency is async again; it would stop reaching the database"
    )
    assert workspaces.get_current_niam_actor_sync is workspaces.get_current_niam_actor, (
        "the two dependencies diverged again — that is how NR-044 stayed hidden"
    )

    gateway = (APP / "clinical_gateway" / "routes.py").read_text(encoding="utf-8")
    assert "get_current_niam_actor_sync" in gateway, (
        "the clinical gateway no longer uses the actor dependency it was given"
    )


def test_the_repository_layer_is_synchronous() -> None:
    """The leaves NR-044.1 converted, pinned against reversion."""
    repositories = APP / "identity" / "repositories"
    for path in sorted(repositories.glob("*.py")):
        source = path.read_text(encoding="utf-8")
        assert "AsyncSession" not in source, f"{path.name} references AsyncSession again"
        assert "async def " not in source, f"{path.name} has an async def again"
        assert "await " not in source, f"{path.name} awaits again"


# ── NR-044.1 closeout: the invariants the ledger alone could not prove ────────


def test_exactly_one_database_engine_architecture_exists() -> None:
    """Option B's whole point: one Session type, one engine architecture.

    NR-044 rejected Option A partly because a second `AsyncEngine` would mean a
    second pool (30 -> 60 connections against PostgreSQL's 100) and a second
    transaction boundary per request. This pins that the conversion did not
    smuggle one in.

    The read replica is not a second architecture: it is the same synchronous
    `create_engine`, off unless `READ_REPLICA_ENABLED` is set, and
    `ReadSessionLocal` falls back to the primary engine when it is absent. It
    predates NR-044 and is unrelated to it.
    """
    from app import database

    assert not _an_async_engine_exists(), "an async engine was introduced"

    assert isinstance(database.engine, Engine), "the primary engine is no longer a sync Engine"
    assert database.read_engine is None or isinstance(database.read_engine, Engine), (
        "the read replica engine is no longer a sync Engine"
    )
    assert database.SessionLocal.kw["bind"] is database.engine
    assert database.ReadSessionLocal.kw["bind"] is (database.read_engine or database.engine)

    # No part of the identity platform may construct an engine or a sessionmaker
    # of its own — that is how a second pool would appear without an AsyncEngine.
    offenders = [
        path.relative_to(APP).as_posix()
        for path in (APP / "identity").rglob("*.py")
        if "__pycache__" not in path.parts
        and ("create_engine(" in path.read_text(encoding="utf-8", errors="ignore")
             or "sessionmaker(" in path.read_text(encoding="utf-8", errors="ignore"))
    ]
    assert not offenders, f"{offenders} build their own engine or sessionmaker"


def test_the_actor_dependency_takes_the_canonical_synchronous_session() -> None:
    """Not merely "not a coroutine" — the annotated type is the one get_db yields.

    A dependency could be made synchronous and still annotate `AsyncSession`,
    which is how the original defect read: the annotation said one thing and the
    provider did another. This asserts the two agree.
    """
    from app.database import get_db
    from app.identity.api.workspaces import get_current_niam_actor

    # workspaces.py carries `from __future__ import annotations`, so the raw
    # annotation is the string "Session". Resolve it rather than string-matching:
    # a module that rebinds the name to AsyncSession would pass a string compare
    # and fail this one.
    signature = inspect.signature(get_current_niam_actor)
    hints = typing.get_type_hints(get_current_niam_actor)
    annotation = hints["db"]
    assert annotation is Session, (
        f"the actor dependency annotates {annotation!r}, not the sqlalchemy.orm.Session "
        "that get_db yields"
    )

    default = signature.parameters["db"].default
    assert getattr(default, "dependency", None) is get_db, (
        "the actor dependency no longer resolves its session through get_db"
    )

    # And get_db really yields that type — a synchronous generator, not an async one.
    assert not inspect.isasyncgenfunction(get_db)
    assert inspect.isgeneratorfunction(get_db)


def test_the_one_genuine_async_io_site_is_still_async() -> None:
    """NR-044 measured exactly one real async I/O site in 506 async functions.

    Option B converts database colour, not I/O colour. `test_fhir_connection`
    makes a genuine `httpx` call to an external FHIR server, and that must stay
    async; converting it would be the error in the other direction.

    NR-044.3 is why this test changed. `identity/admin/services.py` used to be
    in the ledger, so the note here said the function was preserved but not yet
    callable. Its database work is synchronous now, so the method executes for
    the first time — and it is the one Class B case in the platform: a single
    coroutine whose DB statements are sync and whose HTTP call is not. The
    route still awaits it, and only it.
    """
    source = (APP / "identity" / "admin" / "services.py").read_text(encoding="utf-8")
    assert "async with httpx.AsyncClient(" in source, (
        "the genuine async I/O site was converted away; Option B converts database "
        "access, not real concurrent I/O"
    )
    assert "await client.get(" in source

    assert "identity/admin/services.py" not in DECLARED_UNREACHABLE_ASYNC_DB_MODULES, (
        "identity/admin/services.py is back in the ledger; its database work should "
        "be synchronous even though its HTTP call is not"
    )

    # Exactly one coroutine survives in the module, and it is that one.
    import ast as _ast

    coroutines = sorted(
        node.name
        for node in _ast.walk(_ast.parse(source))
        if isinstance(node, _ast.AsyncFunctionDef)
    )
    assert coroutines == ["test_fhir_connection"], (
        f"identity/admin/services.py has coroutines {coroutines}; only the httpx "
        "boundary may be one"
    )

    # And its database statements are synchronous — the Class B contract.
    method = source[source.index("async def test_fhir_connection"):]
    method = method[:method.index("\n    def ")] if "\n    def " in method else method
    assert "await self.session" not in method, (
        "the Class B method awaits its session again; its DB work must be synchronous"
    )
    assert "self.session.execute(" in method
