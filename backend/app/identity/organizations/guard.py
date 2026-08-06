from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.identity.models.niam_organization import NIAMOrganization
from app.identity.workspaces.services import WorkspaceService


class OrganizationAccessDeniedError(Exception):
    pass


@dataclass
class OrganizationAccessDecision:
    allowed: bool
    reason: str
    scope: str | None = None


class OrganizationAccessGuard:
    """Phase 3 — cross-organization administration guard.

    Enforces that an organization owner (or a workspace owner bound to that
    organization) can only administer the organization they belong to. Zero
    cross-domain administration: no actor may mutate, read, or manage another
    organization's records through this platform.
    """

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.workspaces = WorkspaceService(session)

    async def get_organization(self, org_id: str) -> NIAMOrganization | None:
        stmt = select(NIAMOrganization).where(
            NIAMOrganization.id == org_id,
            NIAMOrganization.is_active.is_(True),
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def assert_actor_can_administer_org(
        self,
        actor_identity_id: str,
        org_id: str,
        operation: str = "administer",
    ) -> OrganizationAccessDecision:
        org = await self.get_organization(org_id)
        if not org:
            return OrganizationAccessDecision(False, "organization_not_found")

        # The actor may administer the target organization when they own (or
        # hold the owner role in) an active workspace bound to that
        # organization. Zero cross-domain administration: an actor whose
        # workspaces belong to another organization is always denied.
        workspaces = await self.workspaces.get_workspaces_for_identity(actor_identity_id)
        for workspace in workspaces:
            if workspace.organization_id != org_id or not workspace.is_active:
                continue
            if workspace.owner_identity_id == actor_identity_id:
                return OrganizationAccessDecision(True, "org_owner", scope=org_id)
            member = await self.workspaces._find_member_by_identity(
                workspace.id, actor_identity_id
            )
            if member and member.is_active and member.role_name == "owner":
                return OrganizationAccessDecision(True, "workspace_owner", scope=org_id)

        raise OrganizationAccessDeniedError(
            f"actor {actor_identity_id} may not {operation} organization {org_id}"
        )

    async def can_administer_org(self, actor_identity_id: str, org_id: str) -> bool:
        try:
            decision = await self.assert_actor_can_administer_org(actor_identity_id, org_id)
        except OrganizationAccessDeniedError:
            return False
        return decision.allowed
