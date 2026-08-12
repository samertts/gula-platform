from sqlalchemy import select

from app.identity.models.assignment import Assignment
from app.identity.repositories.base import IdentityRepositoryBase


class AssignmentRepository(IdentityRepositoryBase[Assignment]):

    model_class = Assignment

    async def find_by_employment_id(self, employment_id: str) -> list[Assignment]:
        stmt = (
            select(self.model_class)
            .where(
                self.model_class.employment_id == employment_id,
                self.model_class.is_active.is_(True),
            )
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def find_by_person_id(self, person_id: str) -> list[Assignment]:
        stmt = (
            select(self.model_class)
            .where(
                self.model_class.person_id == person_id,
                self.model_class.is_active.is_(True),
            )
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def find_by_organization_id(self, org_id: str) -> list[Assignment]:
        stmt = (
            select(self.model_class)
            .where(
                self.model_class.organization_id == org_id,
                self.model_class.is_active.is_(True),
            )
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def find_active(self) -> list[Assignment]:
        stmt = (
            select(self.model_class)
            .where(
                self.model_class.status == "active",
                self.model_class.is_active.is_(True),
            )
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
