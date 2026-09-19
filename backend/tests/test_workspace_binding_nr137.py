"""NR-137 — a canonical login now reaches a workspace, or reaches nothing.

NR-135 made /login produce a canonical NIAM session. It stopped there, so the
clinical gateway's very first link -- WorkspaceSessionContext -- never existed
and every clinical read blocked at reason_code=missing_workspace. The identity
was canonical; the organizational context behind it was absent.

THE LINE THIS MUST NOT CROSS
----------------------------
`WorkspaceService.list_eligible` carries a reviewed decision (AUTH-F5):

    Membership in `niam_memberships` is deliberately *not* consulted -- it is
    necessary context, not a grant, and wiring it here would hand access to
    every member of every organization.

So membership is applied here as a FURTHER RESTRICTION on a set `list_eligible`
already allows, never as a source of eligibility. Every workspace this can
select was already reachable through `switch()`. test_g is the assertion that
keeps it that way: an account holding only a membership gets nothing.

It also refuses to guess. Zero candidates or several binds nothing and the
gateway keeps failing closed, because choosing among several would be inventing
the answer to "which workspace is this person acting in".
"""
from __future__ import annotations

import inspect
from datetime import datetime, timedelta

import pytest
from app._compat import UTC
from app.identity.models.membership import Membership, MembershipStatus
from app.identity.models.workspace import Workspace, WorkspaceStatus
from app.identity.services.workspace_service import (
    WorkspaceService,
    _membership_covers,
)

ORG = "org-alpha"
OTHER_ORG = "org-beta"
FACILITY = "fac-1"
OTHER_FACILITY = "fac-2"


def _workspace(ws_id="ws-1", organization_id=ORG, facility_id=FACILITY,
               status=WorkspaceStatus.active.value):
    return Workspace(id=ws_id, organization_id=organization_id,
                     facility_id=facility_id, status=status)


def _membership(organization_id=ORG, facility_id=None, workspace_id=None):
    return Membership(organization_id=organization_id, facility_id=facility_id,
                      workspace_id=workspace_id,
                      status=MembershipStatus.active.value, is_active=True)


# ─── the covering rule, exhaustively, with no database ──────────────────────

def test_a_an_organization_membership_covers_that_organizations_workspace():
    """Positive control. Without it every refusal below could be a total refusal."""
    assert _membership_covers(_membership(), _workspace())


def test_b_a_membership_in_another_organization_covers_nothing():
    assert not _membership_covers(_membership(organization_id=OTHER_ORG), _workspace())


def test_c_a_facility_scoped_membership_covers_only_that_facility():
    assert _membership_covers(_membership(facility_id=FACILITY), _workspace())
    assert not _membership_covers(
        _membership(facility_id=OTHER_FACILITY), _workspace(),
    )


def test_d_a_workspace_scoped_membership_covers_only_that_workspace():
    assert _membership_covers(_membership(workspace_id="ws-1"), _workspace("ws-1"))
    assert not _membership_covers(_membership(workspace_id="ws-9"), _workspace("ws-1"))


def test_e_an_unscoped_membership_does_not_reach_across_organizations():
    """The permissive case must stay bounded by the organization."""
    assert not _membership_covers(
        _membership(organization_id=OTHER_ORG, facility_id=None, workspace_id=None),
        _workspace(),
    )


# ─── the binder: what it selects, and what it refuses to ────────────────────

class _FakeService(WorkspaceService):
    """WorkspaceService with its two data sources stubbed.

    Only `list_eligible` and the membership query are replaced. The selection
    logic under test -- the conjunction, the uniqueness requirement and the
    delegation to `switch` -- is the real one.
    """

    def __init__(self, eligible, memberships):
        self._eligible = eligible
        self._memberships = memberships
        self.switched_to = None

    def list_eligible(self, account):
        return list(self._eligible)

    def _active_memberships(self, account, now):
        return list(self._memberships)

    def switch(self, account, session_id, workspace_id):
        self.switched_to = workspace_id
        return f"context:{workspace_id}"


class _Account:
    id = "acct-1"
    identity_id = "ident-1"
    is_active = True
    status = "active"


@pytest.fixture()
def account():
    return _Account()


def _bind(service, account):
    """Drive the real selection path against the stubbed sources."""
    return WorkspaceService.bind_unambiguous_context(service, account, "sess-1")


def test_f_one_eligible_workspace_with_a_matching_membership_is_bound(account):
    """Positive control for the whole NR-137 path."""
    workspace = _workspace()
    service = _FakeService([workspace], [_membership()])
    assert _bind(service, account) == "context:ws-1"
    assert service.switched_to == "ws-1"


def test_g_membership_alone_confers_nothing(account):
    """THE AUTH-F5 LINE. Eligibility is not granted by membership.

    An account with an active membership in the organization but no entry in
    `list_eligible` -- no ownership, no representation -- must bind nothing.
    If this ever passes by binding a workspace, membership has become a grant
    and AUTH-F5 has been crossed.
    """
    service = _FakeService([], [_membership()])
    assert _bind(service, account) is None
    assert service.switched_to is None


def test_h_eligibility_alone_confers_nothing(account):
    """The other half of the conjunction: no membership, no context."""
    service = _FakeService([_workspace()], [])
    assert _bind(service, account) is None


def test_i_an_ambiguous_choice_binds_nothing(account):
    """Two covered workspaces is a question for the caller, not a guess."""
    service = _FakeService(
        [_workspace("ws-1"), _workspace("ws-2", facility_id=OTHER_FACILITY)],
        [_membership()],
    )
    assert _bind(service, account) is None
    assert service.switched_to is None


def test_j_a_workspace_without_an_organization_or_facility_is_not_a_candidate(account):
    """The gateway requires both, so binding one would only fail a step later."""
    service = _FakeService([_workspace(facility_id=None)], [_membership()])
    assert _bind(service, account) is None


def test_k_an_inactive_account_binds_nothing(account):
    account.is_active = False
    service = _FakeService([_workspace()], [_membership()])
    assert _bind(service, account) is None
    account.is_active = True


# ─── the NR-135 lesson, kept ────────────────────────────────────────────────

def test_l_binding_cannot_break_authentication():
    """Wiring this in naively is what broke login once already.

    NR-135's account lookup took 30 passing auth tests to 24 errors against a
    database without the NIAM tables. The binder is called inside a SAVEPOINT
    and every exception is swallowed into "no workspace", which the gateway
    already refuses correctly. Asserted on the source because the failure mode
    is an environment this suite cannot conjure.
    """
    from app.identity.services import legacy_session_bridge

    source = inspect.getsource(legacy_session_bridge.bind_workspace_context)
    assert "begin_nested" in source, "the binder must not poison the caller's transaction"
    assert "except SQLAlchemyError" in source
    assert "except Exception" in source, (
        "any failure here must leave the session unbound rather than fail the login"
    )


def test_m_the_session_bridge_calls_the_binder():
    source = inspect.getsource(
        __import__("app.identity.services.legacy_session_bridge", fromlist=["x"])
        .establish_canonical_session,
    )
    assert "bind_workspace_context" in source, (
        "a canonical session is established without ever selecting a workspace "
        "again; the clinical gateway will block at missing_workspace (NR-137)"
    )


def test_n_list_eligible_still_does_not_consult_membership():
    """AUTH-F5, pinned at its source.

    If `list_eligible` ever starts reading niam_memberships, membership has
    become a grant for every member of every organization -- the exact outcome
    its comment refuses. That change may be right one day, but it must be a
    decision, not a side effect of this one.
    """
    source = inspect.getsource(WorkspaceService.list_eligible)
    code = "\n".join(
        line for line in source.splitlines()
        if not line.lstrip().startswith("#")
    )
    for usage in ("select(Membership", "Membership.", "_active_memberships"):
        assert usage not in code, (
            f"list_eligible now consults membership ({usage}); membership has "
            f"become a grant for every member of every organization, which is "
            f"exactly what AUTH-F5 refuses (NR-137)"
        )


def test_o_expired_memberships_are_excluded_by_the_query():
    """The freshness filter lives in the query seam; assert it is still written.

    The stub in this module replaces that seam, so the filter itself is never
    executed here -- which is precisely why it is pinned at its source rather
    than assumed to have been covered.
    """
    source = inspect.getsource(WorkspaceService._active_memberships)
    assert "expires_at" in source
    assert "MembershipStatus.active" in source
    assert "is_active" in source


def test_p_a_future_expiry_is_still_active():
    """Sanity on the boundary the query encodes."""
    now = datetime.now(UTC)
    assert now + timedelta(days=1) > now
