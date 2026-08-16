from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.identity.api.workspaces import NiamActor, get_current_niam_actor
from app.identity.services.session_service import SessionService

router = APIRouter(prefix="/sessions", tags=["NIAM Sessions"])


def _owned_account(actor: NiamActor, account_id: str) -> None:
    if str(actor.account.id) != str(account_id):
        # Do not reveal whether another account exists.
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sessions not found")


def _serialize_session(session, *, current_uuid: str | None = None) -> dict[str, object | None]:
    return {
        "uuid": session.uuid,
        "id": session.id,
        "session_type": session.session_type,
        "is_current": session.uuid == current_uuid,
        "device_id": session.device_id,
        "user_agent": session.user_agent,
        "ip_address": session.ip_address,
        "started_at": session.started_at,
        "last_activity_at": session.last_activity_at,
        "expires_at": session.expires_at,
        "auth_method": session.auth_method,
        "mfa_used": session.mfa_used,
    }


@router.get("/account/{account_id}")
async def list_sessions(
    account_id: str,
    actor: NiamActor = Depends(get_current_niam_actor),
    db: AsyncSession = Depends(get_db),
) -> dict[str, object]:
    _owned_account(actor, account_id)
    service = SessionService(db)
    sessions = await service.get_active_sessions(account_id)
    return {"sessions": [_serialize_session(session, current_uuid=actor.session.uuid) for session in sessions]}


@router.post("/{session_uuid}/terminate")
async def terminate_session(
    session_uuid: str,
    reason: str = "manual",
    actor: NiamActor = Depends(get_current_niam_actor),
    db: AsyncSession = Depends(get_db),
) -> dict[str, object]:
    service = SessionService(db)
    session = await service.repo.get_by_uuid(session_uuid)
    if not session or str(session.account_id) != str(actor.account.id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    # Every session termination goes through the authentication service so
    # access and refresh JTIs are revoked together; DB-only termination is not
    # sufficient for server-authoritative logout.
    from app.identity.services.authentication_service import AuthenticationService

    await AuthenticationService(db).logout(session.uuid, account_id=str(actor.account.id))
    await db.commit()
    return {"success": True, "session_uuid": session.uuid}


@router.post("/account/{account_id}/terminate-all")
async def terminate_all_sessions(
    account_id: str,
    reason: str = "manual",
    actor: NiamActor = Depends(get_current_niam_actor),
    db: AsyncSession = Depends(get_db),
) -> dict[str, object]:
    _owned_account(actor, account_id)
    from app.identity.services.authentication_service import AuthenticationService

    count = await AuthenticationService(db).logout_all_sessions(account_id)
    await db.commit()
    return {"success": True, "terminated": count, "reason": reason}
