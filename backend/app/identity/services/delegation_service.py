"""B5 — scoped, revocable, depth-limited delegation into canonical authority.

Owner directive GULA-MASTER-AUTH-2026-11-19 §5/B5 (AUD-SEC-008).

This service is a thin policy/validation layer. It never creates a role, a
permission, an account or a second authorization engine. A delegation is only
an *input* to the single canonical authority
(``RolePermissionService.effective_permissions``), which already enforces
RBAC/ABAC scope, role status, permission status, expiry and audit.

Invariants (all fail-closed):

* only an account that already holds the canonical role (directly or via a
  shallower delegation) in the same organization may delegate it;
* self-delegation is forbidden;
* the delegate must be an active canonical account;
* the delegated permission keys are a verified non-empty subset of what the
  ACTOR actually holds for that role (a direct assignment holds the full active
  catalog; a delegation-based holding holds only that delegation's own verified
  subset) — unknown or unheld keys are rejected, never widened;
* the delegated scope cannot exceed the delegator's own holding scope;
* the delegation is time-bounded and revocable;
* ``depth`` is capped (deep-limited), so authority cannot be re-delegated
  indefinitely;
* every grant, denial and revocation is written to the canonical NIAM audit
  log via ``AuditService``.
"""

from __future__ import annotations

import secrets
from datetime import datetime, timedelta
from typing import Any

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app._compat import UTC
from app.identity.models.account import Account
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
from app.identity.services.audit_service import AuditService
from app.identity.services.membership_service import MembershipService

MAX_DELEGATION_DEPTH = 3
MAX_DELEGATION_HOURS = 720
MIN_DELEGATION_HOURS = 1

_SCOPE_FIELDS = ("facility_id", "department_id", "unit_id", "workspace_id")


class DelegationPolicyError(ValueError):
    """Invalid delegation request (fail-closed, stable machine reason)."""


class DelegationDenied(PermissionError):
    """Actor lacks canonical authority to grant/revoke this delegation."""


class DelegationService:
    """Validate and record delegations; the canonical authority consumes them."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def _audit(
        self,
        action: AuditAction,
        actor_id: str | None,
        target_id: str | None,
        organization_id: str | None,
        metadata: dict[str, Any],
        *,
        outcome: str = "success",
    ) -> None:
        await AuditService(self.session).record(
            action,
            actor_id=actor_id,
            actor_type="account",
            target_type="delegation",
            target_id=target_id,
            organization_id=organization_id,
            metadata=metadata,
            outcome=outcome,
        )

    @staticmethod
    def _scope_contains(holder: Any, requested: dict[str, str | None]) -> bool:
        """A holder with ``None`` in a dimension holds all values in it."""
        for field in _SCOPE_FIELDS:
            held = getattr(holder, field, None)
            asked = requested.get(field)
            if held is not None and held != asked:
                return False
        return True

    async def _holding(self, account_id: str, role_id: str, organization_id: str, now: datetime):
        """Return the shallowest (depth, scope-holder) at which the account holds the role."""
        # 1. Direct canonical role assignment = hop 0 (a delegation becomes 1).
        direct = (
            select(RoleAssignment)
            .where(
                RoleAssignment.account_id == account_id,
                RoleAssignment.role_id == role_id,
                RoleAssignment.organization_id == organization_id,
                RoleAssignment.status == RoleAssignmentStatus.active.value,
                or_(RoleAssignment.expires_at.is_(None), RoleAssignment.expires_at > now),
                RoleAssignment.revoked_at.is_(None),
            )
            .order_by(RoleAssignment.expires_at.asc())
        )
        row = (await self.session.execute(direct)).scalars().first()
        if row is not None:
            return 0, row

        # 2. Existing active delegation received by this account = hop D.
        delegated = (
            select(NiamDelegation)
            .where(
                NiamDelegation.delegate_account_id == account_id,
                NiamDelegation.role_id == role_id,
                NiamDelegation.organization_id == organization_id,
                NiamDelegation.status == DelegationStatus.active,
                NiamDelegation.starts_at <= now,
                NiamDelegation.expires_at > now,
                NiamDelegation.revoked_at.is_(None),
            )
            .order_by(NiamDelegation.depth.asc(), NiamDelegation.expires_at.asc())
        )
        row = (await self.session.execute(delegated)).scalars().first()
        if row is not None:
            return int(row.depth), row
        return None, None

    async def delegate_role(
        self,
        *,
        actor_id: str,
        delegate_account_id: str,
        role_id: str,
        organization_id: str,
        permission_keys: list[str],
        duration_hours: int,
        reason: str,
        facility_id: str | None = None,
        department_id: str | None = None,
        unit_id: str | None = None,
        workspace_id: str | None = None,
    ) -> NiamDelegation:
        """Grant a bounded delegation of a canonical role to an active account."""
        if actor_id == delegate_account_id:
            await self._audit(
                AuditAction.delegation_denied, actor_id, None, organization_id,
                {"reason": "self_delegation", "role_id": role_id}, outcome="denied",
            )
            raise DelegationDenied("Self-delegation is not allowed")

        if not isinstance(duration_hours, int) or not (
            MIN_DELEGATION_HOURS <= duration_hours <= MAX_DELEGATION_HOURS
        ):
            raise DelegationPolicyError("Invalid delegation duration")
        if not isinstance(permission_keys, list) or not permission_keys:
            raise DelegationPolicyError("permission_keys must be a non-empty list")
        if any(not isinstance(key, str) or not key for key in permission_keys):
            raise DelegationPolicyError("Invalid permission key")
        if len(set(permission_keys)) != len(permission_keys):
            raise DelegationPolicyError("Duplicate permission key")
        if not isinstance(reason, str) or len(reason.strip()) < 10:
            raise DelegationPolicyError("A delegation reason of at least 10 characters is required")

        role = await self.session.scalar(select(Role).where(Role.id == role_id))
        if role is None or role.status != CatalogStatus.active.value:
            raise DelegationPolicyError("Delegated role must be an active canonical role")

        delegate = await self.session.scalar(select(Account).where(Account.id == delegate_account_id))
        if delegate is None or not delegate.is_active or delegate.status != "active":
            raise DelegationPolicyError("Delegate account must be active")

        # Verify the requested keys form a subset of the role's ACTIVE catalog.
        allowed_keys = set(
            (
                await self.session.execute(
                    select(Permission.permission_key)
                    .join(RolePermission, RolePermission.permission_id == Permission.id)
                    .where(
                        RolePermission.role_id == role_id,
                        RolePermission.status == CatalogStatus.active.value,
                        Permission.status == CatalogStatus.active.value,
                    )
                )
            ).scalars().all()
        )
        unknown = set(permission_keys) - allowed_keys
        if unknown:
            await self._audit(
                AuditAction.delegation_denied, actor_id, None, organization_id,
                {"reason": "permission_not_in_role", "role_id": role_id,
                 "unknown_keys": sorted(unknown)}, outcome="denied",
            )
            raise DelegationDenied("Requested permissions are not part of the canonical role")

        # Derive the actor's authority from canonical records, never from a client claim.
        now = datetime.now(UTC)
        depth, holder = await self._holding(
            actor_id, role_id, organization_id, now
        )
        if holder is None:
            await self._audit(
                AuditAction.delegation_denied, actor_id, None, organization_id,
                {"reason": "no_holding_authority", "role_id": role_id}, outcome="denied",
            )
            raise DelegationDenied("Actor does not hold the delegated canonical role")

        # SECURITY (Team C B5 HIGH finding — authority laundering): the requested
        # keys must be a subset of what the ACTOR actually holds for this role,
        # not merely the role's catalog. A direct role assignment holds the full
        # active catalog; a delegation-based holding holds only that delegation's
        # own verified subset. Without this guard, an account holding only
        # ``lab_result.read`` through a narrow delegation could re-delegate
        # ``lab_result.export`` from the same role's catalog, which it never held.
        if depth == 0:
            held_keys = set(allowed_keys)
        else:
            raw_held = getattr(holder, "permission_keys", None)
            held_keys = (
                {k for k in raw_held if isinstance(k, str)}
                if isinstance(raw_held, list) else set()
            ) & allowed_keys
        exceeded = set(permission_keys) - held_keys
        if exceeded:
            await self._audit(
                AuditAction.delegation_denied, actor_id, None, organization_id,
                {"reason": "permission_exceeds_holding_authority", "role_id": role_id,
                 "depth": depth, "exceeded_keys": sorted(exceeded)}, outcome="denied",
            )
            raise DelegationDenied(
                "Requested permissions exceed the actor's own holding authority"
            )

        requested_scope = {
            "facility_id": facility_id,
            "department_id": department_id,
            "unit_id": unit_id,
            "workspace_id": workspace_id,
        }
        if not self._scope_contains(holder, requested_scope):
            await self._audit(
                AuditAction.delegation_denied, actor_id, None, organization_id,
                {"reason": "scope_exceeds_authority", "role_id": role_id}, outcome="denied",
            )
            raise DelegationDenied("Delegated scope exceeds the actor's holding scope")

        new_depth = int(depth) + 1
        if new_depth > MAX_DELEGATION_DEPTH:
            await self._audit(
                AuditAction.delegation_denied, actor_id, None, organization_id,
                {"reason": "max_depth_exceeded", "role_id": role_id, "depth": new_depth},
                outcome="denied",
            )
            raise DelegationDenied("Maximum delegation depth exceeded")

        delegation = NiamDelegation(
            uuid=secrets.token_hex(16),
            delegator_account_id=actor_id,
            delegate_account_id=delegate_account_id,
            role_id=role_id,
            organization_id=organization_id,
            facility_id=facility_id,
            department_id=department_id,
            unit_id=unit_id,
            workspace_id=workspace_id,
            scope_type=role.scope_type,
            permission_keys=list(permission_keys),
            depth=new_depth,
            status=DelegationStatus.active,
            reason=reason.strip(),
            starts_at=now,
            expires_at=now + timedelta(hours=duration_hours),
            version=1,
        )
        self.session.add(delegation)
        await self.session.flush()
        await self._audit(
            AuditAction.delegation_granted, actor_id, delegation.id, organization_id,
            {
                "role_id": role_id,
                "delegate_account_id": delegate_account_id,
                "depth": new_depth,
                "permission_keys": list(permission_keys),
                "expires_at": delegation.expires_at.isoformat(),
                "scope": requested_scope,
            },
        )
        return delegation

    async def revoke_delegation(
        self, *, delegation_id: str, actor_id: str, reason: str
    ) -> NiamDelegation:
        """Revoke an active delegation; only its delegator or an org manager may do so."""
        delegation = await self.session.scalar(
            select(NiamDelegation).where(NiamDelegation.id == delegation_id)
        )
        if delegation is None:
            raise DelegationDenied("Delegation not found")
        if delegation.status != DelegationStatus.active:
            raise DelegationDenied("Delegation is already terminal")
        if not isinstance(reason, str) or len(reason.strip()) < 10:
            raise DelegationPolicyError("A revocation reason of at least 10 characters is required")

        is_delegator = delegation.delegator_account_id == actor_id
        is_manager = False
        if not is_delegator:
            is_manager = await MembershipService(self.session)._can_manage_organization(
                actor_id, delegation.organization_id
            )
        if not is_delegator and not is_manager:
            await self._audit(
                AuditAction.delegation_denied, actor_id, delegation.id,
                delegation.organization_id, {"reason": "not_authorized_to_revoke"},
                outcome="denied",
            )
            raise DelegationDenied("Actor cannot revoke this delegation")

        now = datetime.now(UTC)
        delegation.status = DelegationStatus.revoked
        delegation.revoked_at = now
        delegation.revoked_by = actor_id
        delegation.revocation_reason = reason.strip()
        delegation.version = (delegation.version or 1) + 1
        await self.session.flush()
        await self._audit(
            AuditAction.delegation_revoked, actor_id, delegation.id,
            delegation.organization_id,
            {"role_id": delegation.role_id, "depth": delegation.depth, "reason": reason.strip()},
        )
        return delegation


def delegated_permission_row(row: Any) -> str | None:
    """Map an ``effective_permissions`` delegation row to a permission key.

    Fail-closed: only a non-empty JSON list containing the exact key grants it.
    """
    key, allowed = row[0], row[1]
    if not isinstance(key, str) or not isinstance(allowed, list):
        return None
    return key if key in allowed else None


__all__ = [
    "MAX_DELEGATION_DEPTH", "MAX_DELEGATION_HOURS", "MIN_DELEGATION_HOURS",
    "DelegationDenied", "DelegationPolicyError", "DelegationService",
    "delegated_permission_row",
]
