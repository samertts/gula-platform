from sqlalchemy import select

from app.identity.models.employment import Employment
from app.identity.repositories.base import IdentityRepositoryBase


class EmploymentRepository(IdentityRepositoryBase[Employment]):

    model_class = Employment

    def find_by_person_id(self, person_id: str) -> list[Employment]:
        stmt = (
            select(self.model_class)
            .where(
                self.model_class.person_id == person_id,
                self.model_class.is_active.is_(True),
            )
        )
        result = self.session.execute(stmt)
        return list(result.scalars().all())

    def find_by_organization_id(self, org_id: str) -> list[Employment]:
        stmt = (
            select(self.model_class)
            .where(
                self.model_class.organization_id == org_id,
                self.model_class.is_active.is_(True),
            )
        )
        result = self.session.execute(stmt)
        return list(result.scalars().all())

    def find_primary_employment(self, person_id: str) -> list[Employment]:
        stmt = (
            select(self.model_class)
            .where(
                self.model_class.person_id == person_id,
                self.model_class.is_primary_employment.is_(True),
                self.model_class.is_active.is_(True),
            )
        )
        result = self.session.execute(stmt)
        return list(result.scalars().all())
