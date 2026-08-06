from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest
from app.identity.models.niam_organization import NIAMOrganization
from app.identity.organizations.guard import (
    OrganizationAccessDeniedError,
    OrganizationAccessGuard,
)
from app.identity.workspaces.models import Workspace, WorkspaceMembership


def _org(org_id: str, active: bool = True) -> NIAMOrganization:
    return NIAMOrganization(
        id=org_id,
        uuid=str(uuid.uuid4()),
        org_id=f"ORG-{org_id}",
        name_en="Org",
        name_ar="منظمة",
        org_type="hospital",
        status="active" if active else "suspended",
        is_active=active,
    )


def _ws(ws_id: str, org_id: str, owner_identity_id: str, active: bool = True) -> Workspace:
    return Workspace(
        id=ws_id,
        uuid=str(uuid.uuid4()),
        workspace_id=f"WS-{ws_id}",
        owner_identity_id=owner_identity_id,
        owner_person_id="p1",
        organization_id=org_id,
        name_en="Lab",
        name_ar="مختبر",
        workspace_type="laboratory",
        status="active" if active else "suspended",
        is_active=active,
    )


def _member(ws_id: str, identity_id: str, role_name: str, active: bool = True) -> WorkspaceMembership:
    return WorkspaceMembership(
        id=...,
        uuid=str(uuid.uuid4()),
        membership_id=f"M-{ws_id}-{identity_id}",
        workspace_id=ws_id,
        identity_id=identity_id,
        person_id="p1",
        role_name=role_name,
        status="active" if active else "suspended",
        is_active=active,
    )


@pytest.fixture
def mock_session():
    session = MagicMock()
    session.add = MagicMock()
    session.flush = AsyncMock()
    session.execute = AsyncMock()
    return session


class TestOrganizationAccessGuard:
    @staticmethod
    def _scalars_unique_all(items):
        result = MagicMock()
        result.scalars.return_value.unique.return_value.all.return_value = items
        return result

    async def test_org_owner_can_administer(self, mock_session):
        org = _org("org1")
        ws = _ws("ws1", "org1", "id1")
        mock_session.execute = AsyncMock(
            side_effect=[
                MagicMock(scalar_one_or_none=lambda: org),  # get_organization
                self._scalars_unique_all([ws]),  # workspaces
            ]
        )
        guard = OrganizationAccessGuard(mock_session)
        decision = await guard.assert_actor_can_administer_org("id1", "org1")
        assert decision.allowed is True
        assert decision.scope == "org1"

    async def test_workspace_owner_can_administer(self, mock_session):
        org = _org("org1")
        ws = _ws("ws1", "org1", "id1")
        mock_session.execute = AsyncMock(
            side_effect=[
                MagicMock(scalar_one_or_none=lambda: org),
                self._scalars_unique_all([ws]),
            ]
        )
        guard = OrganizationAccessGuard(mock_session)
        assert await guard.can_administer_org("id1", "org1") is True

    async def test_member_of_other_org_denied(self, mock_session):
        org = _org("org1")
        ws_other = _ws("ws99", "org99", "id1")
        mock_session.execute = AsyncMock(
            side_effect=[
                MagicMock(scalar_one_or_none=lambda: org),
                self._scalars_unique_all([ws_other]),
            ]
        )
        guard = OrganizationAccessGuard(mock_session)
        assert await guard.can_administer_org("id1", "org1") is False

    async def test_non_member_raises(self, mock_session):
        org = _org("org1")
        mock_session.execute = AsyncMock(
            side_effect=[
                MagicMock(scalar_one_or_none=lambda: org),
                self._scalars_unique_all([]),
            ]
        )
        guard = OrganizationAccessGuard(mock_session)
        with pytest.raises(OrganizationAccessDeniedError):
            await guard.assert_actor_can_administer_org("id1", "org1", operation="update")

    async def test_missing_org_denied(self, mock_session):
        mock_session.execute = AsyncMock(return_value=MagicMock(scalar_one_or_none=lambda: None))
        guard = OrganizationAccessGuard(mock_session)
        assert await guard.can_administer_org("id1", "ghost-org") is False

    async def test_inactive_workspace_does_not_grant(self, mock_session):
        org = _org("org1")
        ws_inactive = _ws("ws1", "org1", "id1", active=False)
        mock_session.execute = AsyncMock(
            side_effect=[
                MagicMock(scalar_one_or_none=lambda: org),
                self._scalars_unique_all([ws_inactive]),
            ]
        )
        guard = OrganizationAccessGuard(mock_session)
        assert await guard.can_administer_org("id1", "org1") is False

    async def test_org_owner_role_via_membership(self, mock_session):
        org = _org("org1")
        ws = _ws("ws1", "org1", "id0")  # owned by someone else
        member = _member("ws1", "id1", "owner", active=True)
        mock_session.execute = AsyncMock(
            side_effect=[
                MagicMock(scalar_one_or_none=lambda: org),
                self._scalars_unique_all([ws]),
                MagicMock(scalar_one_or_none=lambda: member),
            ]
        )
        guard = OrganizationAccessGuard(mock_session)
        decision = await guard.assert_actor_can_administer_org("id1", "org1")
        assert decision.allowed is True
        assert decision.reason == "workspace_owner"
