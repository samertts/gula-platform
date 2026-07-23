from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.identity.services.session_service import SessionService

router = APIRouter(prefix="/sessions", tags=["NIAM Sessions"])


@router.get("/account/{account_id}")
async def list_sessions(
    account_id: str,
    db: AsyncSession = Depends(get_db),
):
    service = SessionService(db)
    sessions = await service.get_active_sessions(account_id)
    return {"sessions": [{"uuid": s.uuid, "id": s.id} for s in sessions]}


@router.post("/{session_uuid}/terminate")
async def terminate_session(
    session_uuid: str,
    reason: str = "manual",
    db: AsyncSession = Depends(get_db),
):
    service = SessionService(db)
    session = await service.repo.get_by_uuid(session_uuid)
    if not session:
        return {"error": "not_found"}
    await service.terminate(session.id, reason)
    return {"success": True}


@router.post("/account/{account_id}/terminate-all")
async def terminate_all_sessions(
    account_id: str,
    reason: str = "manual",
    db: AsyncSession = Depends(get_db),
):
    service = SessionService(db)
    await service.terminate_all(account_id, reason)
    return {"success": True}
