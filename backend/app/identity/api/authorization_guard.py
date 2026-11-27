from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app._compat import UTC
from app.identity.api.workspaces import NiamActor
from app.identity.models.membership import Membership, MembershipStatus
from app.identity.services.authorization_decision import (
    AuthorizationActor,
    AuthorizationDecisionService,
    AuthorizationRequest,
)
from app.identity.services.canonical_audit import AuditEventInput, CanonicalAuditService


@dataclass(frozen=True)
class AuthorizationGuardSpec:
    """Trusted, route-specific parameters for one authorization decision."""

    action: str
    resource_type: str
    permission_key: str
    resource_id: str | None = None
    organization_id: str | None = None
    sensitivity: str = "high"
    audit_event_type: str = "authorization.guard.decision"
    resource_context: Mapping[str, Any] = field(default_factory=dict)


async def _sole_active_membership_organization(
    db: AsyncSession,
    account_id: str,
) -> str | None:
    """Resolve an unambiguous active organization scope for global mutations.

    Federation and trust configuration routes are not always addressed by an
    organization identifier. Authorization must still be scoped to a real
    active membership. Ambiguous or absent memberships fail closed.
    """
    result = await db.execute(
        select(Membership).where(
            Membership.account_id == account_id,
            Membership.status == MembershipStatus.active.value,
            Membership.is_active.is_(True),
            Membership.revoked_at.is_(None),
        ),
    )
    now = datetime.now(UTC)
    organizations = {
        membership.organization_id
        for membership in result.scalars().all()
        if membership.organization_id
        and (membership.expires_at is None or membership.expires_at > now)
    }
    if len(organizations) != 1:
        return None
    return next(iter(organizations))


async def require_authorized_action(
    actor: NiamActor,
    db: AsyncSession,
    *,
    spec: AuthorizationGuardSpec,
) -> None:
    """Fail-closed action authorization with canonical v2 decision provenance.

    This is a thin adapter over the canonical ``AuthorizationDecisionService``;
    it does not introduce a second authorization engine. Every guarded mutation
    records a version-2 audit entry through ``CanonicalAuditService`` so the
    decision is included in canonical chain verification.
    """
    organization_id = spec.organization_id or await _sole_active_membership_organization(
        db, actor.account.id
    )
    resource_context: dict[str, Any] = {
        key: value for key, value in spec.resource_context.items() if value is not None
    }
    if organization_id is not None:
        resource_context["organization_id"] = organization_id
    if spec.resource_id is not None:
        resource_context["exists"] = True

    decision = await AuthorizationDecisionService(db).authorize(
        AuthorizationActor(account=actor.account, session=actor.session),
        AuthorizationRequest(
            subject_account_id=actor.account.id,
            action=spec.action,
            resource_type=spec.resource_type,
            resource_id=spec.resource_id,
            permission_key=spec.permission_key,
            organization_id=organization_id,
            sensitivity=spec.sensitivity,
            resource_context=resource_context,
        ),
    )

    await CanonicalAuditService(db).record(
        AuditEventInput(
            event_type=spec.audit_event_type,
            category="security",
            action=spec.action,
            actor_id=actor.account.id,
            actor_identity_id=actor.account.identity_id,
            organization_id=organization_id,
            target_type=spec.resource_type,
            target_id=spec.resource_id,
            decision=decision.decision.value,
            reason_code=decision.reason_code.value,
            source="niam_authorization_guard",
            data_classification="INTERNAL",
            outcome="success" if decision.allowed else "denied",
            metadata={
                "permission_key": spec.permission_key,
                "policy_id": decision.policy_id,
                "policy_version": decision.policy_version,
            },
        )
    )

    if not decision.allowed:
        # The guard runs before state mutation. Commit only the audit decision so
        # a denied request cannot be rolled back into an unaudited outcome.
        await db.commit()
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Authorization denied: {decision.reason_code.value}",
        )
