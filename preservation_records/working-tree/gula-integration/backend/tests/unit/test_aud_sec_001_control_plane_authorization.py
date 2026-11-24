"""AUD-SEC-001 — adversarial regression tests for NIAM control-plane authorization.

Originally any authenticated NIAM account (valid token + active session) could
mutate national trust control planes — suspend identities, revoke certificates,
alter trust frameworks, terminate federations, issue credentials. Authorization
now requires an explicitly assigned elevated governance role from the canonical
NIAM RBAC catalog, in addition to authentication.

The test database intentionally has no NIAM tables (separate metadata base), so
these tests exercise the dependency logic directly and verify router wiring
introspectively — the established pattern in this repository.
"""
from __future__ import annotations

from types import SimpleNamespace

import pytest
from app.identity.api.access import (
    _CONTROL_PLANE_AUTHORITIES,
    require_niam_control_plane_authority,
)
from app.identity.api.router import router as niam_router
from fastapi import HTTPException

# Representative mutation surface across every affected control plane.
_CONTROL_PLANE_MUTATIONS = [
    ("governance", "/niam/governance/suspensions"),
    ("trust", "/niam/trust/frameworks"),
    ("lifecycle", "/niam/lifecycle/citizen/register"),
    ("federation", "/niam/federation/providers"),
    ("certificates", "/niam/certificates/issue"),
    ("adaptive_auth", "/niam/adaptive-auth/policies"),
    ("notifications", "/niam/notifications/send"),
    ("professional_registry", "/niam/professional-registry/"),
]

_AFFECTED_PLANES = frozenset(
    {
        "/niam/governance",
        "/niam/trust",
        "/niam/lifecycle",
        "/niam/federation",
        "/niam/certificates",
        "/niam/adaptive-auth",
        "/niam/notifications",
        "/niam/professional-registry",
    }
)


class _FakeResult:
    def __init__(self, present: bool):
        self._present = present

    def first(self):
        return ("assignment-id",) if self._present else None


class _FakeDb:
    def __init__(self, present: bool):
        self._present = present

    async def execute(self, *_args, **_kwargs):
        return _FakeResult(self._present)


def _actor():
    return SimpleNamespace(account=SimpleNamespace(id="ACCOUNT-1"), session=SimpleNamespace())


# ── Dependency logic ──────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_denies_account_without_elevated_role():
    with pytest.raises(HTTPException) as exc:
        await require_niam_control_plane_authority(
            actor=_actor(), db=_FakeDb(present=False)
        )
    assert exc.value.status_code == 403


@pytest.mark.asyncio
async def test_allows_account_with_elevated_role():
    actor = _actor()
    resolved = await require_niam_control_plane_authority(
        actor=actor, db=_FakeDb(present=True)
    )
    assert resolved is actor


@pytest.mark.asyncio
async def test_authority_set_is_narrow_and_explicit():
    assert "master_admin" in _CONTROL_PLANE_AUTHORITIES
    assert "security_administrator" in _CONTROL_PLANE_AUTHORITIES
    # Ordinary/read-only roles must never gain control-plane authority.
    for weak in ("citizen", "staff", "organization_viewer", "audit_reviewer"):
        assert weak not in _CONTROL_PLANE_AUTHORITIES


@pytest.mark.asyncio
async def test_query_scopes_to_active_assignment_and_active_role():
    """The guard must query canonical RBAC tables, not trust caller input."""
    captured: dict = {}

    class CapturingDb(_FakeDb):
        async def execute(self, statement, *_args, **_kwargs):
            captured["sql"] = str(statement)
            return _FakeResult(True)

    await require_niam_control_plane_authority(actor=_actor(), db=CapturingDb(True))
    sql = captured["sql"].lower()
    assert "niam_role_assignments" in sql
    assert "niam_roles" in sql
    assert "status" in sql


# ── Router wiring ─────────────────────────────────────────────────────────────


def _include_prefix(route) -> str:
    """Full prefix of a lazily-included router (this FastAPI uses _IncludedRouter)."""
    ctx = getattr(route, "include_context", None)
    if ctx is None:  # older FastAPI: flattened APIRoute
        return getattr(route, "path", "") or ""
    sub = ctx.included_router
    return (ctx.prefix or "") + (getattr(sub, "prefix", "") or "")


def _include_dependencies(route) -> set:
    """The dependency callables applied at include_router() time."""
    ctx = getattr(route, "include_context", None)
    if ctx is None:
        return {d.call for d in route.dependant.dependencies}
    # Newer FastAPI Depends stores the callable in `.dependency`.
    return {getattr(d, "dependency", None) for d in ctx.dependencies}


def test_every_affected_control_plane_requires_authorization():
    wired = []
    for route in niam_router.routes:
        prefix = _include_prefix(route)
        if prefix not in _AFFECTED_PLANES:
            continue
        wired.append(prefix)
        assert require_niam_control_plane_authority in _include_dependencies(route), (
            f"{prefix} is mounted without control-plane authorization"
        )
    assert wired, "no control-plane routes discovered — wiring test is vacuous"
    # All eight affected planes must be present in the wiring.
    assert set(wired) == _AFFECTED_PLANES, (
        f"expected {_AFFECTED_PLANES}, found {set(wired)}"
    )


def test_professional_registry_no_longer_unauthenticated():
    """The professional registry previously had no router-level guard at all."""
    from app.identity.api.workspaces import get_current_niam_actor

    matched = [
        r
        for r in niam_router.routes
        if _include_prefix(r).startswith("/niam/professional-registry")
    ]
    assert matched, "professional-registry router not mounted"
    for route in matched:
        assert require_niam_control_plane_authority in _include_dependencies(route)
    # Authentication is transitive: the control-plane guard itself depends on
    # get_current_niam_actor, so an anonymous caller is rejected with 401.
    import inspect

    src = inspect.getsource(require_niam_control_plane_authority)
    assert "get_current_niam_actor" in src, (
        "control-plane guard must authenticate via get_current_niam_actor"
    )
    assert get_current_niam_actor is not None


# ── Anonymous HTTP boundary (no DB rows required) ─────────────────────────────


@pytest.mark.parametrize("plane,path", _CONTROL_PLANE_MUTATIONS)
def test_anonymous_mutation_denied(client, plane, path):
    resp = client.post(path, json={})
    assert resp.status_code == 401, f"{plane}: anonymous caller was not rejected"
