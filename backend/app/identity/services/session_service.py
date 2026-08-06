from __future__ import annotations

from datetime import datetime

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app._compat import UTC
from app.identity.models.session import UserSession
from app.identity.repositories.session_repository import SessionRepository


class SessionPolicyError(Exception):
    pass


class MaxConcurrentSessionsError(SessionPolicyError):
    pass


class WorkspaceBindingError(SessionPolicyError):
    pass


class SessionService:
    def __init__(self, session: AsyncSession) -> None:
        self.repo = SessionRepository(session)

    async def get_session(self, session_id: str) -> UserSession | None:
        return await self.repo.get_by_id(session_id)

    async def get_active_sessions(self, account_id: str) -> list[UserSession]:
        return await self.repo.find_by_account_id(account_id)

    async def update_activity(self, session_id: str) -> None:
        session = await self.repo.get_by_id(session_id)
        if session:
            session.last_activity_at = datetime.now(UTC)
            await self.repo.session.flush()

    async def terminate(self, session_id: str, reason: str = "manual") -> None:
        await self.repo.terminate_session(
            session_id=session_id,
            reason=reason,
            terminated_by="system",
        )

    async def terminate_all(self, account_id: str, reason: str = "manual") -> None:
        await self.repo.terminate_all_for_account(account_id=account_id, reason=reason)

    async def enforce_single_session(
        self, account_id: str, current_session_id: str
    ) -> list[UserSession]:
        stmt = select(self.repo.model_class).where(
            self.repo.model_class.account_id == account_id,
            self.repo.model_class.is_active.is_(True),
            self.repo.model_class.id != current_session_id,
        )
        result = await self.repo.session.execute(stmt)
        other_sessions = list(result.scalars().all())

        for s in other_sessions:
            await self.repo.terminate_session(
                session_id=s.id,
                reason="single_session_enforced",
                terminated_by="policy",
            )
            s.governance_action = "single_session_enforced"
            await self.repo.session.flush()

        return other_sessions

    async def expire_stale_sessions(self) -> int:
        now = datetime.now(UTC)
        stmt = (
            update(self.repo.model_class)
            .where(
                self.repo.model_class.expires_at < now,
                self.repo.model_class.is_active.is_(True),
            )
            .values(
                is_active=False,
                terminated_at=now,
                termination_reason="session_expired",
                terminated_by="system",
                governance_action="terminated_by_policy",
            )
        )
        result = await self.repo.session.execute(stmt)
        await self.repo.session.flush()
        return result.rowcount

    async def get_sessions_by_policy(self, policy_id: str) -> list[UserSession]:
        stmt = select(self.repo.model_class).where(
            self.repo.model_class.policy_id == policy_id,
            self.repo.model_class.is_active.is_(True),
        )
        result = await self.repo.session.execute(stmt)
        return list(result.scalars().all())

    async def bind_workspace(self, session_id: str, workspace_id: str) -> UserSession:
        """Bind a session to exactly one active workspace (Phase 7)."""
        session = await self.repo.get_by_id(session_id)
        if not session or not session.is_active:
            raise WorkspaceBindingError("session_not_active")
        if session.workspace_id and session.workspace_id != workspace_id:
            # Rebinding is explicit: terminate the previous binding instead of
            # silently mutating an in-flight authorization scope.
            session.workspace_id = workspace_id
            session.workspace_bound_at = datetime.now(UTC)
            await self.repo.session.flush()
            return session
        session.workspace_id = workspace_id
        session.workspace_bound_at = datetime.now(UTC)
        await self.repo.session.flush()
        return session

    async def unbind_workspace(self, session_id: str) -> UserSession:
        session = await self.repo.get_by_id(session_id)
        if not session:
            raise WorkspaceBindingError("session_not_found")
        session.workspace_id = None
        session.workspace_bound_at = None
        await self.repo.session.flush()
        return session

    async def get_workspace_bound_sessions(self, workspace_id: str) -> list[UserSession]:
        stmt = select(self.repo.model_class).where(
            self.repo.model_class.workspace_id == workspace_id,
            self.repo.model_class.is_active.is_(True),
        )
        result = await self.repo.session.execute(stmt)
        return list(result.scalars().all())

    async def enforce_max_concurrent_sessions(
        self,
        account_id: str,
        max_sessions: int,
        keep_current: bool = True,
        current_session_id: str | None = None,
    ) -> list[UserSession]:
        """Enforce a maximum number of concurrent active sessions.

        When the account exceeds ``max_sessions``, the oldest active sessions
        are terminated oldest-first. Returns the terminated sessions.
        """
        if max_sessions < 1:
            raise SessionPolicyError("max_sessions_must_be_positive")

        stmt = (
            select(self.repo.model_class)
            .where(
                self.repo.model_class.account_id == account_id,
                self.repo.model_class.is_active.is_(True),
            )
            .order_by(self.repo.model_class.started_at)
        )
        result = await self.repo.session.execute(stmt)
        active = list(result.scalars().all())

        if keep_current and current_session_id:
            active = [s for s in active if s.id != current_session_id]

        # Capacity after accounting for the current session being preserved.
        capacity = max_sessions - (1 if keep_current and current_session_id else 0)

        # Keep the NEWEST `capacity` sessions; terminate the oldest excess.
        overflow = max(0, len(active) - capacity)

        terminated: list[UserSession] = []
        for s in active[:overflow]:
            await self.repo.terminate_session(
                session_id=s.id,
                reason="max_concurrent_sessions",
                terminated_by="policy",
            )
            s.governance_action = "max_concurrent_sessions"
            await self.repo.session.flush()
            terminated.append(s)
        return terminated
