"""AUTH-005 Phase 2: which identity controls can actually execute.

A control that cannot run is not a control. AUTH-005 set out to prove
server-authoritative assurance at the service and database level rather than by
reading a function signature — and doing so surfaced why the signature was all
there was to read.

`get_db` yields a synchronous `sqlalchemy.orm.Session`. Thirty-six modules under
`app/identity/` annotate `AsyncSession` and `await session.execute(...)`, and no
`create_async_engine` exists anywhere in `app/`. Awaiting a sync result raises
`TypeError: object ChunkedIteratorResult can't be used in 'await' expression`
before any statement reaches the database.

So the NIAM async service layer — the trust/assurance routes, workspace
eligibility, membership, the repositories — is unreachable at runtime. That is
recorded as NR-044, and it reframes two earlier findings rather than excusing
them:

* NR-038 was never exploitable. The route raised before writing a row, so the
  client-authored assurance level could not be persisted. Removing the client's
  authorship is still correct and is still pinned, but the claim "latent behind
  NIAM authentication" was too generous — it is latent behind a type error.
* The AUTH-005 workspace-eligibility narrowing (NR-043) is correct code in a
  function that cannot currently run.

The synchronous half *does* run and is where the clinical risk lives:
`CitizenRelationshipService`, `identity_link_policy` and `verification_workflow`
are all sync, reachable, and proven against migrated PostgreSQL in
`test_identity_link_and_assurance.py`.

These tests pin the defect. When the async runtime is fixed they fail, which is
the signal to rewrite them to pin the resolution — not to delete them.
"""

from __future__ import annotations

import inspect
import pathlib

import pytest

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


def test_the_async_identity_services_are_numerous_enough_to_matter() -> None:
    """Scope, pinned so it cannot quietly grow or be understated."""
    import re

    pattern = re.compile(r"await\s+(self\.session|self\.db|db|session)\.execute\(")
    modules = sorted(
        path.relative_to(APP).as_posix()
        for path in APP.rglob("*.py")
        if "__pycache__" not in path.parts
        and pattern.search(path.read_text(encoding="utf-8", errors="ignore"))
    )
    assert len(modules) >= 30, (
        f"only {len(modules)} modules await a session execute; if the count fell "
        "sharply the async layer may have been converted — re-derive NR-044"
    )
    for expected in (
        "identity/services/workspace_service.py",
        "identity/services/membership_service.py",
        "identity/trust/services.py",
    ):
        assert expected in modules, f"{expected} is no longer async; re-derive NR-044"


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


def test_the_assurance_service_depends_on_that_broken_primitive() -> None:
    """And therefore cannot reach the database to write a profile.

    This is why NR-038 was never exploitable: the route raised before a
    client-authored assurance level could be persisted.
    """
    from app.identity.trust.services import AssuranceService

    assert inspect.iscoroutinefunction(AssuranceService.derive_profile)
    source = inspect.getsource(AssuranceService._verification_results)
    assert "await self.session.execute(" in source, (
        "the assurance service no longer awaits a session execute; NR-044 may be "
        "resolved for this path — re-derive these tests"
    )


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
