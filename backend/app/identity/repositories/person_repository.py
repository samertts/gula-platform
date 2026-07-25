from sqlalchemy import select

from app.identity.models.person import Person
from app.identity.repositories.base import IdentityRepositoryBase


class PersonRepository(IdentityRepositoryBase[Person]):
    model_class = Person

    async def find_by_national_id_hash(self, hash_value: str) -> Person | None:
        stmt = select(self.model_class).where(
            self.model_class.national_id_hash == hash_value,
            self.model_class.is_active.is_(True),
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def find_by_health_id(self, health_id: str) -> Person | None:
        stmt = select(self.model_class).where(
            self.model_class.health_id == health_id,
            self.model_class.is_active.is_(True),
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def find_by_phone(self, phone: str) -> Person | None:
        stmt = select(self.model_class).where(
            self.model_class.phone == phone,
            self.model_class.is_active.is_(True),
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def find_by_email(self, email: str) -> Person | None:
        stmt = select(self.model_class).where(
            self.model_class.email == email,
            self.model_class.is_active.is_(True),
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def search_by_name(self, query: str, skip: int = 0, limit: int = 20) -> list[Person]:
        stmt = (
            select(self.model_class)
            .where(
                self.model_class.is_active.is_(True),
            )
            .offset(skip)
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
