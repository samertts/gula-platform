
from sqlalchemy import select

from app.identity.models.identity import IdentityRecord, IdentityType
from app.identity.repositories.base import IdentityRepositoryBase


class IdentityRepository(IdentityRepositoryBase[IdentityRecord]):

    model_class = IdentityRecord

    async def find_by_person_id(self, person_id: str) -> list[IdentityRecord]:
        stmt = (
            select(self.model_class)
            .where(
                self.model_class.person_id == person_id,
                self.model_class.is_active.is_(True),
            )
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def find_by_type(self, identity_type: IdentityType) -> list[IdentityRecord]:
        stmt = (
            select(self.model_class)
            .where(
                self.model_class.identity_type == identity_type.value,
                self.model_class.is_active.is_(True),
            )
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def find_primary(self, person_id: str) -> IdentityRecord | None:
        stmt = (
            select(self.model_class)
            .where(
                self.model_class.person_id == person_id,
                self.model_class.status == "active",
                self.model_class.is_active.is_(True),
            )
            .limit(1)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
