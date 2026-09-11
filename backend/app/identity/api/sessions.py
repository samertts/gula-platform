from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.identity.services.session_service import SessionService

router = APIRouter(prefix="/sessions", tags=["NIAM Sessions"])


@router.get("/account/{account_id}")
def list_sessions(
    account_id: str,
    db: Session = Depends(get_db),
) -> dict[str, object]:
    service = SessionService(db)
    sessions = service.get_active_sessions(account_id)
    return {"sessions": [{"uuid": s.uuid, "id": s.id} for s in sessions]}


@router.post("/{session_uuid}/terminate")
def terminate_session(
    session_uuid: str,
    reason: str = "manual",
    db: Session = Depends(get_db),
) -> dict[str, object]:
    service = SessionService(db)
    session = service.repo.get_by_uuid(session_uuid)
    if not session:
        return {"error": "not_found"}
    service.terminate(session.id, reason)
    return {"success": True}


@router.post("/account/{account_id}/terminate-all")
def terminate_all_sessions(
    account_id: str,
    reason: str = "manual",
    db: Session = Depends(get_db),
) -> dict[str, object]:
    service = SessionService(db)
    service.terminate_all(account_id, reason)
    return {"success": True}
