from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from inspect import isawaitable

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from app._compat import UTC
from app.config import SESSION_IDLE_TIMEOUT_MINUTES, SESSION_TOUCH_INTERVAL_SECONDS
from app.database import get_db
from app.identity.models.account import Account, AccountStatus
from app.identity.models.audit import AuditAction
from app.identity.models.session import UserSession
from app.identity.models.workspace import Workspace
from app.identity.services.audit_service import AuditService
from app.identity.services.workspace_service import WorkspaceAccessDenied, WorkspaceService
from app.security.auth import decode_token

router = APIRouter(prefix="/workspaces", tags=["NIAM Workspaces"])
_bearer = HTTPBearer(auto_error=False)


@dataclass(frozen=True)
class NiamActor:
    account: Account
    session: UserSession


def _session_is_idle(session: UserSession, now: datetime) -> bool:
    last_activity = getattr(session, "last_activity_at", None)
    if last_activity is None:
        return False
    if last_activity.tzinfo is None:
        last_activity = last_activity.replace(tzinfo=now.tzinfo)
    return now - last_activity > timedelta(minutes=SESSION_IDLE_TIMEOUT_MINUTES)


def _touch_session_sync(db: Session, session: UserSession, now: datetime) -> None:
    last_activity = getattr(session, "last_activity_at", None)
    if last_activity is None:
        return
    if last_activity.tzinfo is None:
        last_activity = last_activity.replace(tzinfo=now.tzinfo)
    if now - last_activity < timedelta(seconds=SESSION_TOUCH_INTERVAL_SECONDS):
        return
    session.last_activity_at = now
    db.commit()


async def _touch_session_async(db: AsyncSession, session: UserSession, now: datetime) -> None:
    last_activity = getattr(session, "last_activity_at", None)
    if last_activity is None:
        return
    if last_activity.tzinfo is None:
        last_activity = last_activity.replace(tzinfo=now.tzinfo)
    if now - last_activity < timedelta(seconds=SESSION_TOUCH_INTERVAL_SECONDS):
        return
    session.last_activity_at = now
    commit = getattr(db, "commit", None)
    if commit is not None:
        result = commit()
        if isawaitable(result):
            await result


def _raw_niam_token(request: Request, credentials: HTTPAuthorizationCredentials | None) -> str:
    raw_token = credentials.credentials if credentials else request.cookies.get("access_token")
    if not raw_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    return raw_token


def get_current_niam_actor_sync(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
    db: Session = Depends(get_db),
) -> NiamActor:
    """Canonical actor dependency for the sync clinical gateway."""
    raw_token = _raw_niam_token(request, credentials)
    payload = decode_token(raw_token)
    if not payload or not payload.get("account_uuid") or not payload.get("jti"):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid NIAM access token")
    actor = (
        db.query(Account, UserSession)
        .join(UserSession, UserSession.account_id == Account.id)
        .filter(
            Account.uuid == payload["account_uuid"],
            Account.status == AccountStatus.active.value,
            Account.is_active.is_(True),
            Account.is_locked.is_(False),
            UserSession.token_jti == payload["jti"],
            UserSession.is_active.is_(True),
        )
        .first()
    )
    if actor is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Inactive or invalid NIAM session")
    now = datetime.now(UTC)
    if _session_is_idle(actor[1], now):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="NIAM session expired due to inactivity")
    _touch_session_sync(db, actor[1], now)
    return NiamActor(account=actor[0], session=actor[1])


async def get_current_niam_actor(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
    db: AsyncSession = Depends(get_db),
) -> NiamActor:
    raw_token = _raw_niam_token(request, credentials)
    payload = decode_token(raw_token)
    if not payload or not payload.get("account_uuid") or not payload.get("jti"):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid NIAM access token")

    result = await db.execute(
        select(Account, UserSession)
        .join(UserSession, UserSession.account_id == Account.id)
        .where(
            Account.uuid == payload["account_uuid"],
            Account.status == AccountStatus.active.value,
            Account.is_active.is_(True),
            Account.is_locked.is_(False),
            UserSession.token_jti == payload["jti"],
            UserSession.is_active.is_(True),
        ),
    )
    actor = result.first()
    if actor is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Inactive or invalid NIAM session")
    now = datetime.now(UTC)
    if _session_is_idle(actor[1], now):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="NIAM session expired due to inactivity")
    await _touch_session_async(db, actor[1], now)
    return NiamActor(account=actor[0], session=actor[1])


def serialize_workspace(workspace: Workspace) -> dict[str, object]:
    return {
        "id": workspace.id,
        "uuid": workspace.uuid,
        "workspace_type": workspace.workspace_type,
        "name": workspace.name,
        "name_ar": workspace.name_ar,
        "status": workspace.status,
        "organization_id": workspace.organization_id,
        "facility_id": workspace.facility_id,
        "department_id": workspace.department_id,
        "professional_type": workspace.professional_type,
        "is_personal": workspace.is_personal,
    }


@router.get("")
async def list_workspaces(actor: NiamActor = Depends(get_current_niam_actor), db: AsyncSession = Depends(get_db)):
    service = WorkspaceService(db)
    citizen = await service.ensure_citizen_workspace(actor.account)
    workspaces = await service.list_eligible(actor.account)
    if citizen and all(item.id != citizen.id for item in workspaces):
        workspaces.append(citizen)
    return {"workspaces": [serialize_workspace(item) for item in workspaces]}


@router.get("/{workspace_id}")
async def get_workspace(workspace_id: str, actor: NiamActor = Depends(get_current_niam_actor), db: AsyncSession = Depends(get_db)):
    service = WorkspaceService(db)
    workspaces = await service.list_eligible(actor.account)
    workspace = next((item for item in workspaces if item.id == workspace_id), None)
    if workspace is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workspace not found")
    return serialize_workspace(workspace)


@router.post("/{workspace_id}/switch")
async def switch_workspace(workspace_id: str, actor: NiamActor = Depends(get_current_niam_actor), db: AsyncSession = Depends(get_db)):
    service = WorkspaceService(db)
    try:
        context = await service.switch(actor.account, actor.session.id, workspace_id)
    except WorkspaceAccessDenied as exc:
        await AuditService(db).record_event(
            AuditAction.workspace_switched.value,
            actor_id=actor.account.id,
            target_type="workspace",
            target_id=workspace_id,
            metadata={"outcome": "denied"},
            outcome="denied",
        )
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Workspace access denied") from exc
    workspace = await db.get(Workspace, context.workspace_id)
    await AuditService(db).record(
        AuditAction.workspace_switched,
        actor_id=actor.account.id,
        actor_type="account",
        target_type="workspace",
        target_id=workspace.id,
        session_id=actor.session.uuid,
        metadata={"context_version": context.version},
    )
    return {"context": {"account_id": context.account_id, "identity_id": context.identity_id, "workspace_id": context.workspace_id, "version": context.version}, "workspace": serialize_workspace(workspace)}
