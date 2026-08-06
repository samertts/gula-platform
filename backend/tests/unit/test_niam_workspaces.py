from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest
from app.identity.workspaces.models import (
    WORKSPACE_MEMBER_ROLES,
    WORKSPACE_TYPES,
    Workspace,
    WorkspaceMembership,
    WorkspaceRole,
)
from app.identity.workspaces.services import (
    WorkspaceError,
    WorkspaceIsolationError,
    WorkspaceService,
)
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.fixture
def mock_session():
    session = MagicMock()
    session.add = MagicMock()
    session.flush = AsyncMock()
    session.execute = AsyncMock()
    return session


class TestWorkspaceModels:
    def test_workspace_types_complete(self):
        for t in [
            "citizen",
            "personal",
            "professional",
            "laboratory",
            "pharmacy",
            "radiology",
            "hospital",
            "blood_bank",
            "public_health",
            "insurance",
            "research",
            "government",
        ]:
            assert t in WORKSPACE_TYPES

    def test_member_roles_complete(self):
        for r in ["owner", "admin", "manager", "member", "viewer"]:
            assert r in WORKSPACE_MEMBER_ROLES

    def test_workspace_model_instantiation(self):
        w = Workspace(
            id=...,
            uuid=str(uuid.uuid4()),
            workspace_id="WS-1",
            owner_identity_id="id1",
            owner_person_id="p1",
            organization_id="org1",
            name_en="Central Lab",
            name_ar="المختبر المركزي",
            workspace_type="laboratory",
            status="active",
            is_active=True,
        )
        assert w.name_en == "Central Lab"
        assert w.workspace_type == "laboratory"

    def test_membership_model_instantiation(self):
        m = WorkspaceMembership(
            id=...,
            uuid=str(uuid.uuid4()),
            membership_id="M-1",
            workspace_id="ws1",
            identity_id="id1",
            person_id="p1",
            role_name="owner",
            status="active",
            active_workspace=True,
            is_active=True,
        )
        assert m.role_name == "owner"
        assert m.active_workspace is True

    def test_role_model_instantiation(self):
        r = WorkspaceRole(
            id=...,
            uuid=str(uuid.uuid4()),
            role_id="R-1",
            workspace_id="ws1",
            name="technician",
            permissions=["results:write", "results:read"],
            is_system=False,
            is_active=True,
        )
        assert "results:write" in r.permissions


class TestWorkspaceService:
    async def test_create_workspace_valid(self, mock_session):
        mock_session.execute = AsyncMock(
            return_value=MagicMock(
                scalar_one_or_none=lambda: None,  # _get_or_create_system_role: no existing
            )
        )
        service = WorkspaceService(mock_session)
        ws = await service.create_workspace(
            owner_identity_id="id1",
            owner_person_id="p1",
            name_en="Lab",
            name_ar="مختبر",
            workspace_type="laboratory",
            organization_id="org1",
        )
        assert ws.workspace_type == "laboratory"
        assert ws.status == "active"
        assert mock_session.add.called
        mock_session.flush.assert_awaited()

    async def test_create_workspace_invalid_type(self, mock_session):
        service = WorkspaceService(mock_session)
        with pytest.raises(WorkspaceError):
            await service.create_workspace(
                owner_identity_id="id1",
                owner_person_id="p1",
                name_en="X",
                name_ar="س",
                workspace_type="nonsense_type",
            )

    async def test_check_permission_denies_non_member(self, mock_session):
        mock_session.execute = AsyncMock(return_value=MagicMock(scalar_one_or_none=lambda: None))
        service = WorkspaceService(mock_session)
        assert await service.check_permission("ws1", "id1", "results:read") is False

    async def test_check_permission_owner_allowed(self, mock_session):
        member = WorkspaceMembership(
            id=...,
            uuid=str(uuid.uuid4()),
            membership_id="M-1",
            workspace_id="ws1",
            identity_id="id1",
            person_id="p1",
            role_name="owner",
            status="active",
            is_active=True,
        )
        mock_session.execute = AsyncMock(return_value=MagicMock(scalar_one_or_none=lambda: member))
        service = WorkspaceService(mock_session)
        assert await service.check_permission("ws1", "id1", "anything") is True

    async def test_check_permission_role_grant(self, mock_session):
        member = WorkspaceMembership(
            id=...,
            uuid=str(uuid.uuid4()),
            membership_id="M-1",
            workspace_id="ws1",
            identity_id="id1",
            person_id="p1",
            role_id="r1",
            role_name="technician",
            status="active",
            is_active=True,
        )
        role = WorkspaceRole(
            id="r1",
            uuid=str(uuid.uuid4()),
            role_id="R-1",
            workspace_id="ws1",
            name="technician",
            permissions=["results:read"],
            is_system=False,
            is_active=True,
        )
        mock_session.execute = AsyncMock(
            side_effect=[
                MagicMock(scalar_one_or_none=lambda: member),  # check 1: member
                MagicMock(scalar_one_or_none=lambda: role),  # check 1: role
                MagicMock(scalar_one_or_none=lambda: member),  # check 2: member
                MagicMock(scalar_one_or_none=lambda: role),  # check 2: role
            ]
        )
        service = WorkspaceService(mock_session)
        assert await service.check_permission("ws1", "id1", "results:read") is True
        assert await service.check_permission("ws1", "id1", "results:write") is False

    async def test_isolation_across_workspaces(self, mock_session):
        # Member of ws1 with admin role; NOT a member of ws2. check_permission
        # for ws2 must be False (permissions never cross workspaces).
        member = WorkspaceMembership(
            id=...,
            uuid=str(uuid.uuid4()),
            membership_id="M-1",
            workspace_id="ws1",
            identity_id="id1",
            person_id="p1",
            role_name="admin",
            status="active",
            is_active=True,
        )
        mock_session.execute = AsyncMock(
            side_effect=[
                MagicMock(scalar_one_or_none=lambda: member),  # ws1 membership
                MagicMock(scalar_one_or_none=lambda: None),  # ws2 membership
            ]
        )
        service = WorkspaceService(mock_session)
        assert await service.check_permission("ws1", "id1", "x") is True
        assert await service.check_permission("ws2", "id1", "x") is False

    async def test_has_role_rejects_suspended_member(self, mock_session):
        member = WorkspaceMembership(
            id=...,
            uuid=str(uuid.uuid4()),
            membership_id="M-1",
            workspace_id="ws1",
            identity_id="id1",
            person_id="p1",
            role_name="owner",
            status="suspended",
            is_active=True,
        )
        mock_session.execute = AsyncMock(return_value=MagicMock(scalar_one_or_none=lambda: member))
        service = WorkspaceService(mock_session)
        assert await service.has_role("ws1", "id1", {"owner"}) is False

    async def test_update_workspace_denied_for_non_admin(self, mock_session):
        member = WorkspaceMembership(
            id=...,
            uuid=str(uuid.uuid4()),
            membership_id="M-1",
            workspace_id="ws1",
            identity_id="id1",
            person_id="p1",
            role_name="member",
            status="active",
            is_active=True,
        )
        mock_session.execute = AsyncMock(return_value=MagicMock(scalar_one_or_none=lambda: member))
        service = WorkspaceService(mock_session)
        with pytest.raises(WorkspaceIsolationError):
            await service.update_workspace("ws1", "id1", name_en="Renamed")

    async def test_suspend_workspace_requires_owner(self, mock_session):
        member = WorkspaceMembership(
            id=...,
            uuid=str(uuid.uuid4()),
            membership_id="M-1",
            workspace_id="ws1",
            identity_id="id1",
            person_id="p1",
            role_name="admin",
            status="active",
            is_active=True,
        )
        ws = Workspace(
            id="ws1",
            uuid=str(uuid.uuid4()),
            workspace_id="WS-1",
            owner_identity_id="id0",
            owner_person_id="p0",
            name_en="Lab",
            name_ar="مختبر",
            workspace_type="laboratory",
            status="active",
            is_active=True,
        )
        mock_session.execute = AsyncMock(
            side_effect=[
                MagicMock(scalar_one_or_none=lambda: ws),  # get_workspace
                MagicMock(scalar_one_or_none=lambda: member),  # has_role
            ]
        )
        service = WorkspaceService(mock_session)
        with pytest.raises(WorkspaceIsolationError):
            await service.suspend_workspace("ws1", "id1")

    async def test_select_active_workspace_requires_membership(self, mock_session):
        ws = Workspace(
            id="ws1",
            uuid=str(uuid.uuid4()),
            workspace_id="WS-1",
            owner_identity_id="id0",
            owner_person_id="p0",
            name_en="Lab",
            name_ar="مختبر",
            workspace_type="laboratory",
            status="active",
            is_active=True,
        )
        mock_session.execute = AsyncMock(
            side_effect=[
                MagicMock(scalar_one_or_none=lambda: ws),  # get_workspace
                MagicMock(scalar_one_or_none=lambda: None),  # member lookup
            ]
        )
        service = WorkspaceService(mock_session)
        with pytest.raises(WorkspaceIsolationError):
            await service.select_active_workspace("id1", "WS-1")

    async def test_invite_member_rejects_invalid_role(self, mock_session):
        member = WorkspaceMembership(
            id=...,
            uuid=str(uuid.uuid4()),
            membership_id="M-1",
            workspace_id="ws1",
            identity_id="id1",
            person_id="p1",
            role_name="owner",
            status="active",
            is_active=True,
        )
        mock_session.execute = AsyncMock(return_value=MagicMock(scalar_one_or_none=lambda: member))
        service = WorkspaceService(mock_session)
        with pytest.raises(WorkspaceError):
            await service.invite_member("ws1", "id1", "x@y.z", "superuser")
