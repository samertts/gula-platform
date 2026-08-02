from __future__ import annotations

from datetime import date

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.identity.models.license import LicenseStatus, ProfessionalLicense
from app.identity.repositories.assignment_repository import AssignmentRepository
from app.identity.repositories.organization_repository import OrganizationRepository
from shared.rbac.permissions import get_permissions_for_role

# Professional roles whose operational permissions require a valid,
# verified professional license (PROGRAM-05 Rule 3 / Appendix-B).
PROFESSIONAL_ROLE_PREFIXES = (
    "doctor",
    "dentist",
    "pharmacist",
    "nurse",
    "radiographer",
    "technician",
    "laboratory",
    "lab_",
    "medical",
)


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
            if not self._check_assignment_permission(assignment, permission, organization_id):
                continue
            if not await self._is_license_ok(assignment):
                continue
            return True
        return False

    def _check_assignment_permission(
        self,
        assignment,
        permission: str,
        organization_id: str | None = None,
    ) -> bool:
        """Resolve assignment role permissions against the shared RBAC model.

        The assignment's role_id is matched against the canonical shared
        role-permission matrix (single source of truth). Organization
        isolation is enforced: an assignment bound to an organization grants
        permissions only within that organization unless the caller matches.
        """
        if organization_id:
            if assignment.organization_id and assignment.organization_id != organization_id:
                return False
            if assignment.facility_id and assignment.facility_id != organization_id:
                return False
        return permission in get_permissions_for_role(assignment.role_id)

    async def _is_license_ok(self, assignment) -> bool:
        """Professional privileges require a verified, non-expired license.

        PROGRAM-05 Appendix-B: loss of verification (license expired /
        suspended / revoked) immediately revokes operational permissions.
        """
        role = assignment.role_id or ""
        if not role.lower().startswith(PROFESSIONAL_ROLE_PREFIXES):
            return True
        result = await self.session.execute(
            select(ProfessionalLicense).where(ProfessionalLicense.person_id == assignment.person_id)
        )
        today = date.today()
        for lic in result.scalars().all():
            if lic.verified and lic.status == LicenseStatus.active.value:
                if lic.expiry_date is None or lic.expiry_date >= today:
                    return True
        return False

    async def get_assignments_for_person(self, person_id: str) -> list:
        return await self.assignment_repo.find_by_person_id(person_id)

    async def get_assignments_for_organization(self, org_id: str) -> list:
        return await self.assignment_repo.find_by_organization_id(org_id)
