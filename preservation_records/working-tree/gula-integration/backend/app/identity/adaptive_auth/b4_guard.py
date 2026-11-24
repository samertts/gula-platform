"""B4 — server-side authorization for cross-account security administration.

This module is deliberately a *thin policy layer* on top of the canonical
primitives that already exist in NIAM. It introduces no new role catalog, no
new permission engine, no new MFA engine and no new audit store:

* identity + active-session resolution → ``NiamActor`` / ``get_current_niam_actor``
* cross-account authority → canonical ``niam_roles`` / ``niam_role_assignments``
  (the narrow ``master_admin`` / ``security_administrator`` subset)
* recent proof of possession → ``StepUpService.assert_fresh`` (owner-approved
  300-second window)
* audit → canonical immutable ``AuditService`` / ``niam_audit_entries``

Security invariants enforced here (owner directive GULA-MASTER-AUTH-2026-11-19,
section 4):

1. Self-service is resolved from the authenticated principal; a client-supplied
   ``account_id`` is an untrusted *lookup hint*, never proof of authorization.
2. MFA challenge and verification are strictly self-only, even for administrators.
3. Cross-account access requires an active, verifiable, unexpired, unrevoked
   assignment to exactly ``master_admin`` or ``security_administrator``.
4. Cross-account access requires fresh, own-account step-up evidence.
5. Actor, target, session and evidence identifiers are re-read server-side.
6. Every cross-account action (allowed or denied) is written to the immutable
   audit log with actor, target, purpose, action, result and evidence.
7. Deny by default: any ambiguity, missing row, inactive state or error denies.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app._compat import UTC
from app.identity.api.workspaces import NiamActor
from app.identity.models.account import Account, AccountStatus
from app.identity.models.audit import AuditAction
from app.identity.models.authorization import (
    CatalogStatus,
    Role,
    RoleAssignment,
    RoleAssignmentStatus,
)
from app.identity.models.session import UserSession
from app.identity.services.audit_service import AuditService
from app.identity.services.step_up_service import StepUpError, StepUpService

# Narrow B4 authority: a strict subset of the broader AUD-SEC-001 control-plane
# set. ministry_admin / organization_administrator / compliance_officer may
# reach the control plane but may NOT perform cross-account MFA administration.
B4_CROSS_ACCOUNT_ROLES = frozenset({"master_admin", "security_administrator"})


class B4Denied(HTTPException):
    """Fail-closed denial for a B4 authorization decision."""

    def __init__(self, detail: str, status_code: int = status.HTTP_403_FORBIDDEN) -> None:
        super().__init__(status_code=status_code, detail=detail)


def _as_utc(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    return value if value.tzinfo is not None else value.replace(tzinfo=UTC)


async def _load_actor_state(db: AsyncSession, actor: NiamActor) -> tuple[Account, Any]:
    """Re-read actor account + session from the database; never trust cached claims."""
    account = (
        await db.execute(select(Account).where(Account.id == actor.account.id))
    ).scalar_one_or_none()
    session = (
        await db.execute(select(UserSession).where(UserSession.id == actor.session.id))
    ).scalar_one_or_none()
    if account is None or session is None:
        raise B4Denied("actor_not_found")
    if (
        account.status != AccountStatus.active.value
        or not account.is_active
        or account.is_locked
    ):
        raise B4Denied("actor_ineligible")
    if session.account_id != account.id or session.token_jti != actor.session.token_jti:
        raise B4Denied("session_substitution")
    if not session.is_active or _as_utc(session.terminated_at) is not None:
        raise B4Denied("session_revoked")
    if _as_utc(session.expires_at) is None or _as_utc(session.expires_at) <= datetime.now(UTC):
        raise B4Denied("session_expired")
    return account, session


async def _has_cross_account_role(db: AsyncSession, account: Account) -> bool:
    """Resolve narrow cross-account authority from the canonical RBAC catalog."""
    now = datetime.now(UTC)
    result = await db.execute(
        select(RoleAssignment.id)
        .join(Role, Role.id == RoleAssignment.role_id)
        .where(
            RoleAssignment.account_id == account.id,
            RoleAssignment.status == RoleAssignmentStatus.active.value,
            RoleAssignment.revoked_at.is_(None),
            or_(RoleAssignment.expires_at.is_(None), RoleAssignment.expires_at > now),
            Role.status == CatalogStatus.active.value,
            Role.role_key.in_(B4_CROSS_ACCOUNT_ROLES),
        )
    )
    return result.first() is not None


async def _audit_decision(
    db: AsyncSession,
    *,
    action: AuditAction,
    actor_account: Account,
    target_account: Account | None,
    session: Any,
    outcome: str,
    operation: str,
    purpose: str,
    evidence_event_id: str | None = None,
    reason: str | None = None,
    required: bool = False,
) -> None:
    """Write a cross-account authorization decision to the immutable audit log.

    ``required=True`` (successful cross-account access) fails closed if the
    audit write fails: no unaudited cross-account action may proceed.
    """
    metadata: dict[str, Any] = {
        "b4": True,
        "operation": operation,
        "purpose": purpose,
        "actor_account_id": actor_account.id,
        "target_account_id": target_account.id if target_account else None,
        "session_id": session.id,
        "session_jti": session.token_jti,
        "evidence_event_id": evidence_event_id,
        "reason": reason,
    }
    try:
        await AuditService(db).record(
            action=action,
            actor_id=actor_account.id,
            actor_type="account",
            target_type="account",
            target_id=target_account.id if target_account else None,
            session_id=session.id,
            outcome=outcome,
            metadata=metadata,
            error_message=reason,
        )
    except Exception:
        if required:
            raise
        # Denials stand even if the best-effort audit write is unavailable.


async def authorize_account_operation(
    db: AsyncSession,
    actor: NiamActor,
    requested_account_id: str | None,
    *,
    operation: str,
    purpose: str,
    mfa_self_only: bool = False,
    cross_account_allowed: bool = True,
) -> Account:
    """Authorize an account-scoped adaptive-auth operation, deny by default.

    Returns the server-resolved target ``Account``. The caller MUST use the
    returned row's ``id`` for any downstream query — never the client hint.
    """
    actor_account, session = await _load_actor_state(db, actor)

    # No target supplied → the actor's own account (self-service).
    if requested_account_id is None or requested_account_id == "":
        return actor_account

    target = (
        await db.execute(select(Account).where(Account.id == requested_account_id))
    ).scalar_one_or_none()
    if target is None:
        raise B4Denied("target_not_found")

    if target.id == actor_account.id:
        return target  # self-service: no elevated role or step-up required

    # From here on this is a cross-account administrative action.
    if mfa_self_only:
        await _audit_decision(
            db,
            action=AuditAction.authz_deny,
            actor_account=actor_account,
            target_account=target,
            session=session,
            outcome="denied",
            operation=operation,
            purpose=purpose,
            reason="mfa_self_only",
        )
        raise B4Denied("mfa_self_only")

    if not cross_account_allowed:
        raise B4Denied("cross_account_not_allowed")

    if not await _has_cross_account_role(db, actor_account):
        await _audit_decision(
            db,
            action=AuditAction.authz_privilege_escalation_attempt,
            actor_account=actor_account,
            target_account=target,
            session=session,
            outcome="denied",
            operation=operation,
            purpose=purpose,
            reason="cross_account_role_denied",
        )
        raise B4Denied("cross_account_role_denied")

    try:
        evidence = await StepUpService(db).assert_fresh(actor, purpose=purpose)
    except StepUpError as exc:
        await _audit_decision(
            db,
            action=AuditAction.step_up_failed,
            actor_account=actor_account,
            target_account=target,
            session=session,
            outcome="denied",
            operation=operation,
            purpose=purpose,
            reason=str(exc),
        )
        raise B4Denied("fresh_step_up_required") from exc

    await _audit_decision(
        db,
        action=AuditAction.authz_allow_sensitive,
        actor_account=actor_account,
        target_account=target,
        session=session,
        outcome="success",
        operation=operation,
        purpose=purpose,
        evidence_event_id=evidence.event_id,
        required=True,
    )
    return target


async def resolve_own_mfa_challenge(db: AsyncSession, actor: NiamActor, mfa_id: str) -> Any:
    """Resolve an MFA challenge only if it belongs to the authenticated actor."""
    from .models import AdaptiveMFASession

    actor_account, session = await _load_actor_state(db, actor)
    challenge = (
        await db.execute(
            select(AdaptiveMFASession).where(AdaptiveMFASession.mfa_id == mfa_id)
        )
    ).scalar_one_or_none()
    if challenge is None or challenge.account_id != actor_account.id:
        await _audit_decision(
            db,
            action=AuditAction.authz_deny,
            actor_account=actor_account,
            target_account=None,
            session=session,
            outcome="denied",
            operation="mfa_verify",
            purpose="self_only_mfa",
            reason="mfa_self_only_or_unknown",
        )
        raise B4Denied("mfa_self_only")
    return challenge


async def resolve_session_target(
    db: AsyncSession,
    actor: NiamActor,
    session_id: str,
    *,
    purpose: str,
) -> Any:
    """Resolve a session server-side, then authorize access to its owning account.

    Prevents an attacker from probing/terminating arbitrary sessions by id
    (IDOR): the owning account is derived from the database row, never trusted
    from the caller.
    """
    target_session = (
        await db.execute(select(UserSession).where(UserSession.id == session_id))
    ).scalar_one_or_none()
    if target_session is None:
        raise B4Denied("session_not_found")
    await authorize_account_operation(
        db,
        actor,
        target_session.account_id,
        operation="session_validity_check",
        purpose=purpose,
    )
    return target_session
