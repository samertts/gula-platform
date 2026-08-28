from datetime import datetime

from sqlalchemy import select, update

from app._compat import UTC
from app.identity.models.session import UserSession
from app.identity.repositories.base import IdentityRepositoryBase


class SessionRepository(IdentityRepositoryBase[UserSession]):

    model_class = UserSession

    async def find_by_token_jti(self, jti: str) -> UserSession | None:
        stmt = select(self.model_class).where(
            self.model_class.token_jti == jti,
            self.model_class.is_active.is_(True),
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def find_by_refresh_token_jti(self, jti: str) -> UserSession | None:
        stmt = select(self.model_class).where(
            self.model_class.refresh_token_jti == jti,
            self.model_class.is_active.is_(True),
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def find_any_by_refresh_token_jti(self, jti: str) -> UserSession | None:
        stmt = select(self.model_class).where(self.model_class.refresh_token_jti == jti)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def terminate_refresh_family(self, family_id: str, *, reason: str, detected_at: datetime) -> None:
        stmt = (
            update(self.model_class)
            .where(
                self.model_class.refresh_family_id == family_id,
                self.model_class.is_active.is_(True),
            )
            .values(
                is_active=False,
                terminated_at=detected_at,
                termination_reason=reason,
                refresh_reuse_detected_at=detected_at,
            )
        )
        await self.session.execute(stmt)
        await self.session.flush()

    async def find_by_account_id(self, account_id: str) -> list[UserSession]:
        stmt = (
            select(self.model_class)
            .where(
                self.model_class.account_id == account_id,
                self.model_class.is_active.is_(True),
            )
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def terminate_session(self, session_id: str, reason: str, terminated_by: str) -> None:
        stmt = (
            update(self.model_class)
            .where(self.model_class.id == session_id)
            .values(
                is_active=False,
                terminated_at=datetime.now(UTC),
                termination_reason=reason,
                terminated_by=terminated_by,
            )
        )
        await self.session.execute(stmt)
        await self.session.flush()

    async def terminate_all_for_account(self, account_id: str, reason: str) -> None:
        stmt = (
            update(self.model_class)
            .where(
                self.model_class.account_id == account_id,
                self.model_class.is_active.is_(True),
            )
            .values(
                is_active=False,
                terminated_at=datetime.now(UTC),
                termination_reason=reason,
            )
        )
        await self.session.execute(stmt)
        await self.session.flush()
