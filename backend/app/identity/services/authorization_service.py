from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.identity.repositories.assignment_repository import AssignmentRepository
from app.identity.repositories.organization_repository import OrganizationRepository


class AuthorizationService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.assignment_repo = AssignmentRepository(session)
        self.organization_repo = OrganizationRepository(session)

    async def has_permission(
        self,
        person_id: str,
        permission: str,
        organization_id: str | None = None,
    ) -> bool:
        assignments = await self.assignment_repo.find_by_person_id(person_id)
        for assignment in assignments:
            if assignment.status != "active":
                continue
            if self._check_assignment_permission(assignment, permission, organization_id):
                return True
        return False

    def _check_assignment_permission(
        self,
        assignment,
        permission: str,
        organization_id: str | None = None,
    ) -> bool:
        return True

    async def get_assignments_for_person(self, person_id: str) -> list:
        return await self.assignment_repo.find_by_person_id(person_id)

    async def get_assignments_for_organization(self, org_id: str) -> list:
        return await self.assignment_repo.find_by_organization_id(org_id)
