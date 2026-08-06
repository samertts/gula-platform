from __future__ import annotations

import uuid
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock

import pytest
from app._compat import UTC
from app.identity.models.session import UserSession
from app.identity.services.session_service import (
    SessionPolicyError,
    SessionService,
    WorkspaceBindingError,
)


def _session(session_id: str, account_id: str, started_at: datetime, active: bool = True) -> UserSession:
    return UserSession(
        id=session_id,
        uuid=str(uuid.uuid4()),
        account_id=account_id,
        token_jti=f"jti-{session_id}",
        session_type="web",
        is_active=active,
        started_at=started_at,
        last_activity_at=started_at,
        expires_at=started_at + timedelta(hours=8),
    )


@pytest.fixture
def mock_session():
    session = MagicMock()
    session.add = MagicMock()
    session.flush = AsyncMock()
    session.execute = AsyncMock()
    return session


class TestSessionWorkspaceBinding:
    async def test_bind_workspace(self, mock_session):
        s = _session("s1", "acct1", datetime.now(UTC))
        mock_session.execute = AsyncMock(return_value=MagicMock(scalar_one_or_none=lambda: s))
        service = SessionService(mock_session)
        bound = await service.bind_workspace("s1", "ws1")
        assert bound.workspace_id == "ws1"
        assert bound.workspace_bound_at is not None

    async def test_bind_rejects_inactive_session(self, mock_session):
        s = _session("s1", "acct1", datetime.now(UTC), active=False)
        mock_session.execute = AsyncMock(return_value=MagicMock(scalar_one_or_none=lambda: s))
        service = SessionService(mock_session)
        with pytest.raises(WorkspaceBindingError):
            await service.bind_workspace("s1", "ws1")

    async def test_unbind_workspace(self, mock_session):
        s = _session("s1", "acct1", datetime.now(UTC))
        s.workspace_id = "ws1"
        mock_session.execute = AsyncMock(return_value=MagicMock(scalar_one_or_none=lambda: s))
        service = SessionService(mock_session)
        unbound = await service.unbind_workspace("s1")
        assert unbound.workspace_id is None
        assert unbound.workspace_bound_at is None

    async def test_get_workspace_bound_sessions(self, mock_session):
        s1 = _session("s1", "acct1", datetime.now(UTC))
        s1.workspace_id = "ws1"
        mock_session.execute = AsyncMock(
            return_value=MagicMock(scalars=MagicMock(return_value=MagicMock(all=lambda: [s1])))
        )
        service = SessionService(mock_session)
        sessions = await service.get_workspace_bound_sessions("ws1")
        assert len(sessions) == 1
        assert sessions[0].workspace_id == "ws1"


class TestMaxConcurrentSessions:
    async def test_no_termination_under_limit(self, mock_session):
        now = datetime.now(UTC)
        sessions = [_session(f"s{i}", "acct1", now - timedelta(hours=i)) for i in range(2)]
        mock_session.execute = AsyncMock(
            return_value=MagicMock(scalars=MagicMock(return_value=MagicMock(all=lambda: sessions)))
        )
        service = SessionService(mock_session)
        terminated = await service.enforce_max_concurrent_sessions("acct1", 5)
        assert terminated == []

    async def test_terminates_oldest_over_limit(self, mock_session):
        now = datetime.now(UTC)
        sessions = [
            _session("oldest", "acct1", now - timedelta(hours=10)),
            _session("middle", "acct1", now - timedelta(hours=5)),
            _session("newest", "acct1", now - timedelta(hours=1)),
        ]
        mock_session.execute = AsyncMock(
            return_value=MagicMock(scalars=MagicMock(return_value=MagicMock(all=lambda: sessions)))
        )
        service = SessionService(mock_session)
        terminated = await service.enforce_max_concurrent_sessions("acct1", 2)
        assert len(terminated) == 1
        assert terminated[0].id == "oldest"

    async def test_keeps_current_when_over_limit(self, mock_session):
        now = datetime.now(UTC)
        sessions = [
            _session("s1", "acct1", now - timedelta(hours=10)),
            _session("current", "acct1", now - timedelta(hours=1)),
        ]
        mock_session.execute = AsyncMock(
            return_value=MagicMock(scalars=MagicMock(return_value=MagicMock(all=lambda: sessions)))
        )
        service = SessionService(mock_session)
        terminated = await service.enforce_max_concurrent_sessions(
            "acct1", 1, keep_current=True, current_session_id="current"
        )
        assert len(terminated) == 1
        assert terminated[0].id == "s1"

    async def test_terminated_sessions_marked_by_policy(self, mock_session):
        now = datetime.now(UTC)
        sessions = [
            _session("s1", "acct1", now - timedelta(hours=10)),
            _session("s2", "acct1", now - timedelta(hours=1)),
        ]
        mock_session.execute = AsyncMock(
            return_value=MagicMock(scalars=MagicMock(return_value=MagicMock(all=lambda: sessions)))
        )
        service = SessionService(mock_session)
        terminated = await service.enforce_max_concurrent_sessions("acct1", 1)
        assert terminated[0].governance_action == "max_concurrent_sessions"

    async def test_rejects_non_positive_limit(self, mock_session):
        service = SessionService(mock_session)
        with pytest.raises(SessionPolicyError):
            await service.enforce_max_concurrent_sessions("acct1", 0)
