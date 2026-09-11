from datetime import datetime

from sqlalchemy import select, update

from app._compat import UTC
from app.identity.models.session import UserSession
from app.identity.repositories.base import IdentityRepositoryBase


class SessionRepository(IdentityRepositoryBase[UserSession]):

    model_class = UserSession

    def find_by_token_jti(self, jti: str) -> UserSession | None:
        stmt = select(self.model_class).where(
            self.model_class.token_jti == jti,
            self.model_class.is_active.is_(True),
        )
        result = self.session.execute(stmt)
        return result.scalar_one_or_none()

    def find_by_refresh_token_jti(self, jti: str) -> UserSession | None:
        stmt = select(self.model_class).where(
            self.model_class.refresh_token_jti == jti,
            self.model_class.is_active.is_(True),
        )
        result = self.session.execute(stmt)
        return result.scalar_one_or_none()

    def find_by_account_id(self, account_id: str) -> list[UserSession]:
        stmt = (
            select(self.model_class)
            .where(
                self.model_class.account_id == account_id,
                self.model_class.is_active.is_(True),
            )
        )
        result = self.session.execute(stmt)
        return list(result.scalars().all())

    def terminate_session(self, session_id: str, reason: str, terminated_by: str) -> None:
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
        self.session.execute(stmt)
        self.session.flush()

    def terminate_all_for_account(self, account_id: str, reason: str) -> None:
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
        self.session.execute(stmt)
        self.session.flush()
