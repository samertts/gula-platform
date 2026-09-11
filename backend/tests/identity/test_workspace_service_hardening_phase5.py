"""Workspace service hardening tests for IAM Phase 5."""

from __future__ import annotations

from types import SimpleNamespace

import pytest
from app.identity.models.account import AccountStatus, AccountType
from app.identity.models.workspace import WorkspaceStatus, WorkspaceType
from app.identity.services.workspace_service import WorkspaceAccessDenied, WorkspaceService


class _Scalars:
    def __init__(self, rows):
        self.rows = rows

    def all(self):
        return list(self.rows)


class _Result:
    def __init__(self, *, rows=(), scalar=None):
        self._rows = rows
        self._scalar = scalar

    def scalars(self):
        return _Scalars(self._rows)

    def scalar_one_or_none(self):
        return self._scalar


class _AsyncSession:
    def __init__(self, results):
        self.results = list(results)
        self.added = []
        self.flush_count = 0

    def execute(self, statement):
        assert self.results, "Unexpected database query in workspace test"
        return self.results.pop(0)

    def add(self, value):
        self.added.append(value)

    def flush(self):
        self.flush_count += 1



def account(account_id="account-1", identity_id="identity-1"):
    return SimpleNamespace(
        id=account_id,
        uuid=f"uuid-{account_id}",
        identity_id=identity_id,
        account_type=AccountType.human.value,
        status=AccountStatus.active.value,
        is_active=True,
    )


def workspace(workspace_id="workspace-1", *, status=WorkspaceStatus.active.value, owner="account-1"):
    return SimpleNamespace(
        id=workspace_id,
        uuid=f"uuid-{workspace_id}",
        workspace_key=f"citizen:{owner}",
        workspace_type=WorkspaceType.citizen.value,
        name="Citizen Workspace",
        name_ar="مساحة المواطن",
        status=status,
        owner_account_id=owner,
        organization_id=None,
        facility_id=None,
        department_id=None,
        professional_type=None,
        is_personal=True,
        version=1,
    )


def test_switch_creates_server_context_for_eligible_active_workspace():
    target = workspace()
    session = _AsyncSession(
        [
            _Result(rows=[target]),
            _Result(rows=[]),
            _Result(scalar=None),
        ],
    )

    context = WorkspaceService(session).switch(account(), "session-1", target.id)

    assert context.account_id == "account-1"
    assert context.identity_id == "identity-1"
    assert context.workspace_id == target.id
    assert context.version == 1
    assert session.added == [context]
    assert session.flush_count == 1


def test_switch_rejects_restricted_workspace_even_when_listed():
    target = workspace(status=WorkspaceStatus.restricted.value)
    session = _AsyncSession([_Result(rows=[target]), _Result(rows=[])])

    with pytest.raises(WorkspaceAccessDenied, match="not available"):
        WorkspaceService(session).switch(account(), "session-1", target.id)

    assert session.added == []


def test_switch_rejects_existing_context_owned_by_another_account():
    target = workspace()
    foreign_context = SimpleNamespace(
        account_id="account-2",
        is_active=True,
        workspace_id="workspace-foreign",
        version=4,
    )
    session = _AsyncSession(
        [_Result(rows=[target]), _Result(rows=[]), _Result(scalar=foreign_context)],
    )

    with pytest.raises(WorkspaceAccessDenied, match="does not belong"):
        WorkspaceService(session).switch(account(), "session-1", target.id)

    assert session.added == []


def test_existing_citizen_workspace_is_returned_without_duplicate_side_effect():
    existing = workspace()
    session = _AsyncSession([_Result(scalar=existing)])

    result = WorkspaceService(session).ensure_citizen_workspace(account())

    assert result is existing
    assert session.added == []
    assert session.flush_count == 0


def test_ineligible_account_cannot_provision_citizen_workspace():
    inactive = account()
    inactive.status = AccountStatus.suspended.value
    session = _AsyncSession([])

    assert WorkspaceService(session).ensure_citizen_workspace(inactive) is None
    assert session.added == []


def test_professional_workspace_requires_verified_record_before_lookup():
    session = _AsyncSession([_Result(scalar=None)])

    result = WorkspaceService(session).ensure_professional_workspace(account(), "physician")

    assert result is None
    assert session.added == []
