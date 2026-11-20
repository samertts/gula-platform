from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.identity.models.audit import AuditAction
from app.identity.services.audit_service import AuditService
from app.identity.services.session_service import SessionService

from .ownership import record_authorization_denial, require_account_scope
from .workspaces import NiamActor, get_current_niam_actor

router = APIRouter(prefix="/sessions", tags=["NIAM Sessions"])


@router.get("/account/{account_id}")
async def list_sessions(
    account_id: str,
    actor: NiamActor = Depends(get_current_niam_actor),
    db: AsyncSession = Depends(get_db),
) -> dict[str, object]:
    scoped_account_id = await require_account_scope(db, actor, account_id)
    service = SessionService(db)
    sessions = await service.get_active_sessions(scoped_account_id)
    return {"sessions": [{"uuid": s.uuid, "id": s.id} for s in sessions]}


@router.post("/{session_uuid}/terminate")
async def terminate_session(
    session_uuid: str,
    reason: str = Query(default="manual", min_length=1, max_length=100),
    actor: NiamActor = Depends(get_current_niam_actor),
    db: AsyncSession = Depends(get_db),
) -> dict[str, object]:
    service = SessionService(db)
    session = await service.repo.get_by_uuid(session_uuid)
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    if session.account_id != actor.account.id:
        await record_authorization_denial(
            db,
            actor,
            target_type="session",
            target_id=session_uuid,
            reason="session_scope_mismatch",
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access to this session is not permitted",
        )

    await service.terminate(
        session.id,
        reason,
        terminated_by=actor.account.id,
    )
    await AuditService(db).record(
        AuditAction.session_terminated,
        actor_id=actor.account.id,
        actor_type="account",
        target_type="session",
        target_id=session.uuid,
        session_id=actor.session.uuid,
        metadata={"reason": reason},
    )
    return {"success": True}


@router.post("/account/{account_id}/terminate-all")
async def terminate_all_sessions(
    account_id: str,
    reason: str = Query(default="manual", min_length=1, max_length=100),
    actor: NiamActor = Depends(get_current_niam_actor),
    db: AsyncSession = Depends(get_db),
) -> dict[str, object]:
    scoped_account_id = await require_account_scope(db, actor, account_id)
    service = SessionService(db)
    await service.terminate_all(
        scoped_account_id,
        reason,
        terminated_by=actor.account.id,
    )
    await AuditService(db).record(
        AuditAction.session_terminated,
        actor_id=actor.account.id,
        actor_type="account",
        target_type="account_sessions",
        target_id=scoped_account_id,
        session_id=actor.session.uuid,
        metadata={"reason": reason, "all_sessions": True},
    )
    return {"success": True}
