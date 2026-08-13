
from sqlalchemy import or_, select

from app.identity.models.account import Account
from app.identity.repositories.base import IdentityRepositoryBase


class AccountRepository(IdentityRepositoryBase[Account]):

    model_class = Account

    async def find_by_login(self, login: str) -> Account | None:
        stmt = select(self.model_class).where(
            or_(
                self.model_class.email == login,
                self.model_class.username == login,
            ),
            self.model_class.is_active.is_(True),
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def find_by_email(self, email: str) -> Account | None:
        stmt = select(self.model_class).where(
            self.model_class.email == email,
            self.model_class.is_active.is_(True),
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def find_by_username(self, username: str) -> Account | None:
        stmt = select(self.model_class).where(
            self.model_class.username == username,
            self.model_class.is_active.is_(True),
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def find_by_phone(self, phone: str) -> Account | None:
        stmt = select(self.model_class).where(
            self.model_class.phone == phone,
            self.model_class.is_active.is_(True),
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def find_by_identity_id(self, identity_id: str) -> Account | None:
        stmt = select(self.model_class).where(
            self.model_class.identity_id == identity_id,
            self.model_class.is_active.is_(True),
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def find_locked_accounts(self) -> list[Account]:
        stmt = (
            select(self.model_class)
            .where(
                self.model_class.is_locked.is_(True),
                self.model_class.is_active.is_(True),
            )
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
