from __future__ import annotations

from datetime import datetime

from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

from app._compat import UTC
from app.identity.models.audit import AuditAction
from app.identity.models.session import UserSession
from app.identity.models.workspace import WorkspaceSessionContext
from app.identity.services.audit_service import AuditService


async def revoke_account_access(
    session: AsyncSession,
    *,
    account_id: str,
    reason_code: str,
    actor_id: str | None = None,
    organization_id: str | None = None,
    facility_id: str | None = None,
    workspace_id: str | None = None,
) -> tuple[int, int]:
    """Invalidate sessions and cached workspace contexts at an access boundary.

    The helper intentionally does not commit. The caller's lifecycle mutation and
    its revocation evidence must commit atomically or roll back together. When the
    affected scope is broader than one workspace, all sessions and contexts for
    the account are invalidated to prevent stale privilege from surviving a
    membership, role, or organization boundary change.
    """
    now = datetime.now(UTC)
    session_result = await session.execute(
        update(UserSession)
        .where(
            UserSession.account_id == account_id,
            UserSession.is_active.is_(True),
        )
        .values(
            is_active=False,
            terminated_at=now,
            termination_reason=reason_code,
            terminated_by=actor_id or "system",
            governance_action="access_revocation",
        ),
    )
    context_query = update(WorkspaceSessionContext).where(
        WorkspaceSessionContext.account_id == account_id,
        WorkspaceSessionContext.is_active.is_(True),
    )
    if workspace_id is not None:
        context_query = context_query.where(WorkspaceSessionContext.workspace_id == workspace_id)
    context_result = await session.execute(
        context_query.values(
            is_active=False,
            version=WorkspaceSessionContext.version + 1,
        ),
    )
    session_count = int(session_result.rowcount or 0)
    context_count = int(context_result.rowcount or 0)
    await AuditService(session).record(
        AuditAction.session_revoked,
        actor_id=actor_id or "system",
        actor_type="account",
        target_type="account",
        target_id=account_id,
        organization_id=organization_id,
        facility_id=facility_id,
        workspace_id=workspace_id,
        reason_code=reason_code,
        metadata={
            "reason_code": reason_code,
            "revoked_session_count": session_count,
            "invalidated_context_count": context_count,
        },
        outcome="success",
    )
    await session.flush()
    return session_count, context_count
