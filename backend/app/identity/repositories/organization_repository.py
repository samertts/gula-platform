
from sqlalchemy import select

from app.identity.models.niam_organization import NIAMOrganization
from app.identity.repositories.base import IdentityRepositoryBase


class OrganizationRepository(IdentityRepositoryBase[NIAMOrganization]):

    model_class = NIAMOrganization

    def find_by_org_id(self, org_id: str) -> NIAMOrganization | None:
        stmt = select(self.model_class).where(
            self.model_class.org_id == org_id,
            self.model_class.is_active.is_(True),
        )
        result = self.session.execute(stmt)
        return result.scalar_one_or_none()

    def find_by_type(self, org_type: str) -> list[NIAMOrganization]:
        stmt = (
            select(self.model_class)
            .where(
                self.model_class.org_type == org_type,
                self.model_class.is_active.is_(True),
            )
        )
        result = self.session.execute(stmt)
        return list(result.scalars().all())

    def find_by_governorate(self, governorate: str) -> list[NIAMOrganization]:
        stmt = (
            select(self.model_class)
            .where(
                self.model_class.governorate == governorate,
                self.model_class.is_active.is_(True),
            )
        )
        result = self.session.execute(stmt)
        return list(result.scalars().all())

    def find_children(self, parent_id: str) -> list[NIAMOrganization]:
        stmt = (
            select(self.model_class)
            .where(
                self.model_class.parent_org_id == parent_id,
                self.model_class.is_active.is_(True),
            )
        )
        result = self.session.execute(stmt)
        return list(result.scalars().all())
