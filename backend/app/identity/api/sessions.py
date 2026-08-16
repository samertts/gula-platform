from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.identity.api.workspaces import NiamActor, get_current_niam_actor
from app.identity.services.session_service import SessionService

router = APIRouter(prefix="/sessions", tags=["NIAM Sessions"])


@router.get("/account/{account_id}")
async def list_sessions(
    account_id: str,
    actor: NiamActor = Depends(get_current_niam_actor),
    db: AsyncSession = Depends(get_db),
) -> dict[str, object]:
    if str(actor.account.id) != account_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Session scope does not belong to the authenticated account",
        )
    service = SessionService(db)
    sessions = await service.get_active_sessions(str(actor.account.id))
    return {"sessions": [{"uuid": s.uuid, "id": s.id} for s in sessions]}


@router.post("/{session_uuid}/terminate")
async def terminate_session(
    session_uuid: str,
    reason: str = "manual",
    actor: NiamActor = Depends(get_current_niam_actor),
    db: AsyncSession = Depends(get_db),
) -> dict[str, object]:
    service = SessionService(db)
    session = await service.repo.get_by_uuid(session_uuid)
    if not session:
        return {"error": "not_found"}
    if str(session.account_id) != str(actor.account.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Session does not belong to the authenticated account",
        )
    await service.terminate(session.id, reason)
    return {"success": True}


@router.post("/account/{account_id}/terminate-all")
async def terminate_all_sessions(
    account_id: str,
    reason: str = "manual",
    actor: NiamActor = Depends(get_current_niam_actor),
    db: AsyncSession = Depends(get_db),
) -> dict[str, object]:
    if str(actor.account.id) != account_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Session scope does not belong to the authenticated account",
        )
    service = SessionService(db)
    await service.terminate_all(str(actor.account.id), reason)
    return {"success": True}
