from __future__ import annotations

import secrets
from datetime import datetime

from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app._compat import UTC
from app.identity.models.audit import AuditAction
from app.identity.models.authorization import (
    CatalogStatus,
    Permission,
    Role,
    RoleAssignment,
    RoleAssignmentStatus,
    RolePermission,
)
from app.identity.models.delegation import DelegationStatus, NiamDelegation
from app.identity.models.membership import Membership, MembershipStatus
from app.identity.services.audit_service import AuditService
from app.identity.services.delegation_service import MAX_DELEGATION_DEPTH
from app.identity.services.membership_service import MembershipService

LEGAL_ROLE_ASSIGNMENT_TRANSITIONS: dict[str, frozenset[str]] = {
    RoleAssignmentStatus.pending.value: frozenset({RoleAssignmentStatus.active.value, RoleAssignmentStatus.revoked.value}),
    RoleAssignmentStatus.active.value: frozenset({RoleAssignmentStatus.suspended.value, RoleAssignmentStatus.expired.value, RoleAssignmentStatus.revoked.value}),
    RoleAssignmentStatus.suspended.value: frozenset({RoleAssignmentStatus.active.value, RoleAssignmentStatus.expired.value, RoleAssignmentStatus.revoked.value}),
    RoleAssignmentStatus.expired.value: frozenset({RoleAssignmentStatus.revoked.value}),
    RoleAssignmentStatus.revoked.value: frozenset(),
}


class RoleAuthorizationDenied(PermissionError):
    """Raised when an actor cannot manage or use a scoped role."""


class RoleAssignmentStateError(ValueError):
    """Raised for invalid role assignment transitions."""


class AuthorizationCatalogError(ValueError):
    """Raised for invalid or disabled role/permission catalog entries."""


class RolePermissionService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    @staticmethod
    def assignment_key(
        account_id: str,
        membership_id: str,
        role_id: str,
        organization_id: str,
        facility_id: str | None = None,
        department_id: str | None = None,
        unit_id: str | None = None,
        workspace_id: str | None = None,
    ) -> str:
        return ":".join(
            (
                account_id,
                membership_id,
                role_id,
                organization_id,
                facility_id or "-",
                department_id or "-",
                unit_id or "-",
                workspace_id or "-",
            ),
        )

    @staticmethod
    def transition_assignment(assignment: RoleAssignment, target: RoleAssignmentStatus) -> RoleAssignment:
        current = str(assignment.status)
        if target.value not in LEGAL_ROLE_ASSIGNMENT_TRANSITIONS.get(current, frozenset()):
            raise RoleAssignmentStateError(f"Illegal role assignment transition: {current} -> {target.value}")
        assignment.status = target.value
        assignment.version = (assignment.version or 1) + 1
        return assignment

    async def _audit(
        self,
        action: AuditAction,
        actor_id: str | None,
        target_type: str,
        target_id: str | None,
        organization_id: str | None,
        metadata: dict | None = None,
        outcome: str = "success",
    ) -> None:
        await AuditService(self.session).record(
            action,
            actor_id=actor_id,
            actor_type="account",
            target_type=target_type,
            target_id=target_id,
            organization_id=organization_id,
            metadata=metadata,
            outcome=outcome,
        )

    async def list_roles(self) -> list[Role]:
        result = await self.session.execute(
            select(Role).where(Role.status == CatalogStatus.active.value).order_by(Role.role_key),
        )
        return list(result.scalars().all())

    async def list_permissions(self) -> list[Permission]:
        result = await self.session.execute(
            select(Permission).where(Permission.status == CatalogStatus.active.value).order_by(Permission.permission_key),
        )
        return list(result.scalars().all())

    async def _load_active_membership(self, membership_id: str, account_id: str) -> Membership:
        membership = await self.session.scalar(select(Membership).where(Membership.id == membership_id))
        if membership is None or membership.account_id != account_id or membership.status != MembershipStatus.active.value or not membership.is_active:
            raise RoleAuthorizationDenied("Target membership is not active for this account")
        if membership.expires_at and membership.expires_at <= datetime.now(UTC):
            raise RoleAuthorizationDenied("Target membership has expired")
        return membership

    async def _load_active_role(self, role_id: str) -> Role:
        role = await self.session.scalar(select(Role).where(Role.id == role_id))
        if role is None or role.status != CatalogStatus.active.value:
            raise AuthorizationCatalogError("Role is not active")
        return role

    @staticmethod
    def _scope_matches_membership(membership: Membership, role_scope: str, facility_id: str | None, department_id: str | None, unit_id: str | None, workspace_id: str | None) -> bool:
        return (
            membership.scope_type == role_scope
            and membership.facility_id == facility_id
            and membership.department_id == department_id
            and membership.unit_id == unit_id
            and membership.workspace_id == workspace_id
        )

    async def grant_role(
        self,
        actor_id: str,
        account_id: str,
        membership_id: str,
        role_id: str,
        facility_id: str | None = None,
        department_id: str | None = None,
        unit_id: str | None = None,
        workspace_id: str | None = None,
    ) -> RoleAssignment:
        if actor_id == account_id:
            await self._audit(AuditAction.role_assignment_denied, actor_id, "role", role_id, None, {"reason": "self_escalation"}, outcome="denied")
            raise RoleAuthorizationDenied("Self role assignment is not allowed")
        membership = await self._load_active_membership(membership_id, account_id)
        role = await self._load_active_role(role_id)
        membership_service = MembershipService(self.session)
        if not await membership_service._can_manage_organization(actor_id, membership.organization_id):
            await self._audit(AuditAction.role_assignment_denied, actor_id, "role", role_id, membership.organization_id, {"reason": "organization_authority"}, outcome="denied")
            raise RoleAuthorizationDenied("Actor cannot assign roles in this organization")
        if not self._scope_matches_membership(membership, role.scope_type, facility_id, department_id, unit_id, workspace_id):
            raise RoleAuthorizationDenied("Role scope does not match target membership scope")
        key = self.assignment_key(account_id, membership_id, role_id, membership.organization_id, facility_id, department_id, unit_id, workspace_id)
        existing = await self.session.scalar(select(RoleAssignment).where(RoleAssignment.assignment_key == key))
        if existing:
            if existing.status == RoleAssignmentStatus.active.value:
                return existing
            raise RoleAssignmentStateError("Role assignment key already has a terminal history")
        assignment = RoleAssignment(
            uuid=secrets.token_hex(16),
            assignment_key=key,
            account_id=account_id,
            membership_id=membership_id,
            role_id=role_id,
            organization_id=membership.organization_id,
            facility_id=facility_id,
            department_id=department_id,
            unit_id=unit_id,
            workspace_id=workspace_id,
            scope_type=role.scope_type,
            status=RoleAssignmentStatus.pending.value,
            assigned_by=actor_id,
        )
        self.session.add(assignment)
        await self.session.flush()
        self.transition_assignment(assignment, RoleAssignmentStatus.active)
        assignment.activated_at = datetime.now(UTC)
        await self.session.flush()
        await self._audit(AuditAction.role_assignment_created, actor_id, "role_assignment", assignment.id, assignment.organization_id, {"role_id": role.id, "scope_type": role.scope_type})
        await self._audit(AuditAction.role_assignment_activated, actor_id, "role_assignment", assignment.id, assignment.organization_id, {"role_id": role.id})
        return assignment

    async def revoke_role(self, assignment_id: str, actor_id: str, reason: str | None = None) -> RoleAssignment:
        assignment = await self.session.scalar(select(RoleAssignment).where(RoleAssignment.id == assignment_id))
        if assignment is None:
            raise RoleAuthorizationDenied("Role assignment not found")
        if not await MembershipService(self.session)._can_manage_organization(actor_id, assignment.organization_id):
            raise RoleAuthorizationDenied("Actor cannot revoke roles in this organization")
        self.transition_assignment(assignment, RoleAssignmentStatus.revoked)
        assignment.revoked_at = datetime.now(UTC)
        assignment.revocation_reason = reason
        await self.session.flush()
        await self._audit(AuditAction.role_assignment_revoked, actor_id, "role_assignment", assignment.id, assignment.organization_id, {"reason": reason})
        return assignment

    async def _delegation_chain_valid(
        self, delegation: NiamDelegation, organization_id: str, now: datetime
    ) -> bool:
        """A delegation confers authority only while its ENTIRE chain is live.

        Team C B5 residual — transitive revocation: revoking the original
        delegator's direct role assignment used to leave a live delegation in
        force at enforcement time. Walk delegator -> parent delegation -> ...
        until a live direct ``RoleAssignment`` is reached. Any broken link,
        cycle, missing parent or depth violation fails closed.
        """
        seen: set[str] = set()
        current = delegation
        while True:
            if current.id in seen:
                return False
            seen.add(current.id)
            depth = int(current.depth or 0)
            if depth < 1 or depth > MAX_DELEGATION_DEPTH:
                return False
            delegator = current.delegator_account_id
            direct = await self.session.scalar(
                select(RoleAssignment.id).where(
                    RoleAssignment.account_id == delegator,
                    RoleAssignment.role_id == current.role_id,
                    RoleAssignment.organization_id == organization_id,
                    RoleAssignment.status == RoleAssignmentStatus.active.value,
                    or_(RoleAssignment.expires_at.is_(None), RoleAssignment.expires_at > now),
                    RoleAssignment.revoked_at.is_(None),
                )
            )
            if direct is not None:
                return True
            if depth == 1:
                return False
            parent = await self.session.scalar(
                select(NiamDelegation).where(
                    NiamDelegation.delegate_account_id == delegator,
                    NiamDelegation.role_id == current.role_id,
                    NiamDelegation.organization_id == organization_id,
                    NiamDelegation.depth == depth - 1,
                    NiamDelegation.status == DelegationStatus.active,
                    NiamDelegation.starts_at <= now,
                    NiamDelegation.expires_at > now,
                    NiamDelegation.revoked_at.is_(None),
                ).order_by(NiamDelegation.expires_at.desc())
            )
            if parent is None:
                return False
            current = parent

    async def effective_permissions(
        self,
        account_id: str,
        organization_id: str,
        facility_id: str | None = None,
        department_id: str | None = None,
        unit_id: str | None = None,
        workspace_id: str | None = None,
    ) -> set[str]:
        now = datetime.now(UTC)
        scope_match = and_(
            RoleAssignment.organization_id == organization_id,
            or_(RoleAssignment.facility_id.is_(None), RoleAssignment.facility_id == facility_id),
            or_(RoleAssignment.department_id.is_(None), RoleAssignment.department_id == department_id),
            or_(RoleAssignment.unit_id.is_(None), RoleAssignment.unit_id == unit_id),
            or_(RoleAssignment.workspace_id.is_(None), RoleAssignment.workspace_id == workspace_id),
        )
        result = await self.session.execute(
            select(Permission.permission_key)
            .join(RolePermission, RolePermission.permission_id == Permission.id)
            .join(Role, Role.id == RolePermission.role_id)
            .join(RoleAssignment, RoleAssignment.role_id == Role.id)
            .where(
                RoleAssignment.account_id == account_id,
                RoleAssignment.status == RoleAssignmentStatus.active.value,
                or_(RoleAssignment.expires_at.is_(None), RoleAssignment.expires_at > now),
                Role.status == CatalogStatus.active.value,
                RolePermission.status == CatalogStatus.active.value,
                Permission.status == CatalogStatus.active.value,
                scope_match,
            ),
        )
        direct = set(result.scalars().all())

        # B5 — delegated authority is an INPUT to this same canonical authority,
        # never a second engine. The delegation must be active, in force, within
        # its verified permission subset and depth cap, match the same RBAC/ABAC
        # scope predicate as a direct role assignment, AND still have a live
        # delegator chain (transitive-revocation hardening).
        delegated = (await self.session.execute(
            select(NiamDelegation).where(
                NiamDelegation.delegate_account_id == account_id,
                NiamDelegation.status == DelegationStatus.active,
                NiamDelegation.depth >= 1,
                NiamDelegation.depth <= MAX_DELEGATION_DEPTH,
                NiamDelegation.starts_at <= now,
                NiamDelegation.expires_at > now,
                NiamDelegation.revoked_at.is_(None),
                NiamDelegation.organization_id == organization_id,
                or_(NiamDelegation.facility_id.is_(None), NiamDelegation.facility_id == facility_id),
                or_(NiamDelegation.department_id.is_(None), NiamDelegation.department_id == department_id),
                or_(NiamDelegation.unit_id.is_(None), NiamDelegation.unit_id == unit_id),
                or_(NiamDelegation.workspace_id.is_(None), NiamDelegation.workspace_id == workspace_id),
            )
        )).scalars().all()

        active_keys_by_role: dict[str, set[str]] = {}
        for delegation in delegated:
            if not await self._delegation_chain_valid(delegation, organization_id, now):
                continue
            role_id = delegation.role_id
            if role_id not in active_keys_by_role:
                active_keys_by_role[role_id] = set((await self.session.execute(
                    select(Permission.permission_key)
                    .join(RolePermission, RolePermission.permission_id == Permission.id)
                    .join(Role, Role.id == RolePermission.role_id)
                    .where(
                        RolePermission.role_id == role_id,
                        RolePermission.status == CatalogStatus.active.value,
                        Permission.status == CatalogStatus.active.value,
                        Role.status == CatalogStatus.active.value,
                    )
                )).scalars().all())
            keys = delegation.permission_keys
            if not isinstance(keys, list):
                continue
            direct |= {k for k in keys if isinstance(k, str)} & active_keys_by_role[role_id]
        return direct

    async def has_permission(self, account_id: str, permission_key: str, organization_id: str, **scope: str | None) -> bool:
        permission = await self.session.scalar(
            select(Permission.id).where(
                Permission.permission_key == permission_key,
                Permission.status == CatalogStatus.active.value,
            ),
        )
        if permission is None:
            return False
        permissions = await self.effective_permissions(
            account_id,
            organization_id,
            facility_id=scope.get("facility_id"),
            department_id=scope.get("department_id"),
            unit_id=scope.get("unit_id"),
            workspace_id=scope.get("workspace_id"),
        )
        allowed = permission_key in permissions
        await self._audit(
            AuditAction.permission_enforced if allowed else AuditAction.permission_denied,
            account_id,
            "permission",
            str(permission),
            organization_id,
            {"permission_key": permission_key, "allowed": allowed},
            outcome="success" if allowed else "denied",
        )
        return allowed
