from __future__ import annotations

from datetime import datetime

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app._compat import UTC
from app.identity.models.session import UserSession
from app.identity.repositories.session_repository import SessionRepository


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

    async def terminate(
        self,
        session_id: str,
        reason: str = "manual",
        *,
        terminated_by: str = "system",
    ) -> None:
        await self.repo.terminate_session(
            session_id=session_id,
            reason=reason,
            terminated_by=terminated_by,
        )

    async def terminate_all(
        self,
        account_id: str,
        reason: str = "manual",
        *,
        terminated_by: str = "system",
    ) -> None:
        await self.repo.terminate_all_for_account(
            account_id=account_id,
            reason=reason,
            terminated_by=terminated_by,
        )

    async def enforce_single_session(self, account_id: str, current_session_id: str) -> list[UserSession]:
        stmt = (
            select(self.repo.model_class)
            .where(
                self.repo.model_class.account_id == account_id,
                self.repo.model_class.is_active.is_(True),
                self.repo.model_class.id != current_session_id,
            )
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
        stmt = (
            select(self.repo.model_class)
            .where(
                self.repo.model_class.policy_id == policy_id,
                self.repo.model_class.is_active.is_(True),
            )
        )
        result = await self.repo.session.execute(stmt)
        return list(result.scalars().all())
