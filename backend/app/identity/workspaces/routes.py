from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_niam_db as get_db
from app.identity.security import get_current_identity

from .services import WorkspaceError, WorkspaceIsolationError, WorkspaceService

router = APIRouter(
    prefix="/workspaces",
    tags=["NIAM Workspaces"],
    dependencies=[Depends(get_current_identity)],
)


def _handle(exc: Exception) -> HTTPException:
    if isinstance(exc, WorkspaceIsolationError):
        return HTTPException(status_code=403, detail=str(exc))
    if isinstance(exc, WorkspaceError):
        return HTTPException(status_code=400, detail=str(exc))
    return HTTPException(status_code=500, detail="internal_error")


@router.post("/")
async def create_workspace(
    owner_identity_id: str,
    owner_person_id: str,
    name_en: str,
    name_ar: str,
    workspace_type: str,
    organization_id: str | None = None,
    description: str | None = None,
    settings: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    import json

    service = WorkspaceService(db)
    try:
        workspace = await service.create_workspace(
            owner_identity_id=owner_identity_id,
            owner_person_id=owner_person_id,
            name_en=name_en,
            name_ar=name_ar,
            workspace_type=workspace_type,
            organization_id=organization_id,
            description=description,
            settings=json.loads(settings) if settings else None,
        )
    except Exception as exc:
        raise _handle(exc) from exc
    return {"workspace": workspace.to_dict()}


@router.get("/{workspace_id}")
async def get_workspace(workspace_id: str, db: AsyncSession = Depends(get_db)):
    service = WorkspaceService(db)
    workspace = await service.get_workspace(workspace_id)
    if not workspace:
        raise HTTPException(status_code=404, detail="workspace_not_found")
    return {"workspace": workspace.to_dict()}


@router.get("/identity/{identity_id}")
async def list_identity_workspaces(identity_id: str, db: AsyncSession = Depends(get_db)):
    service = WorkspaceService(db)
    workspaces = await service.get_workspaces_for_identity(identity_id)
    return {"workspaces": [w.to_dict() for w in workspaces], "count": len(workspaces)}


@router.patch("/{workspace_id}")
async def update_workspace(
    workspace_id: str,
    actor_identity_id: str,
    name_en: str | None = None,
    name_ar: str | None = None,
    description: str | None = None,
    settings: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    import json

    service = WorkspaceService(db)
    try:
        workspace = await service.update_workspace(
            workspace_id=workspace_id,
            actor_identity_id=actor_identity_id,
            name_en=name_en,
            name_ar=name_ar,
            description=description,
            settings=json.loads(settings) if settings else None,
        )
    except Exception as exc:
        raise _handle(exc) from exc
    return {"workspace": workspace.to_dict()}


@router.post("/{workspace_id}/suspend")
async def suspend_workspace(
    workspace_id: str, actor_identity_id: str, db: AsyncSession = Depends(get_db)
):
    service = WorkspaceService(db)
    try:
        workspace = await service.suspend_workspace(workspace_id, actor_identity_id)
    except Exception as exc:
        raise _handle(exc) from exc
    return {"workspace": workspace.to_dict()}


@router.post("/{workspace_id}/select")
async def select_workspace(
    workspace_id: str, identity_id: str, db: AsyncSession = Depends(get_db)
):
    service = WorkspaceService(db)
    try:
        member = await service.select_active_workspace(identity_id, workspace_id)
    except Exception as exc:
        raise _handle(exc) from exc
    return {"selected": True, "workspace_id": workspace_id, "role": member.role_name}


@router.post("/{workspace_id}/roles")
async def create_role(
    workspace_id: str,
    actor_identity_id: str,
    name: str,
    permissions: str,
    description: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    import json

    service = WorkspaceService(db)
    try:
        role = await service.create_role(
            workspace_id=workspace_id,
            actor_identity_id=actor_identity_id,
            name=name,
            permissions=json.loads(permissions) if permissions else [],
            description=description,
        )
    except Exception as exc:
        raise _handle(exc) from exc
    return {"role": role.to_dict()}


@router.get("/{workspace_id}/roles")
async def list_roles(workspace_id: str, db: AsyncSession = Depends(get_db)):
    service = WorkspaceService(db)
    roles = await service.list_roles(workspace_id)
    return {"roles": [r.to_dict() for r in roles]}


@router.post("/{workspace_id}/members")
async def add_member(
    workspace_id: str,
    actor_identity_id: str,
    identity_id: str,
    person_id: str,
    role_name: str,
    db: AsyncSession = Depends(get_db),
):
    service = WorkspaceService(db)
    try:
        member = await service.add_member(
            workspace_id=workspace_id,
            actor_identity_id=actor_identity_id,
            identity_id=identity_id,
            person_id=person_id,
            role_name=role_name,
        )
    except Exception as exc:
        raise _handle(exc) from exc
    return {"member": member.to_dict()}


@router.get("/{workspace_id}/members")
async def list_members(workspace_id: str, db: AsyncSession = Depends(get_db)):
    service = WorkspaceService(db)
    members = await service.list_members(workspace_id)
    return {"members": [m.to_dict() for m in members]}


@router.post("/{workspace_id}/members/{person_id}/remove")
async def remove_member(
    workspace_id: str, person_id: str, actor_identity_id: str, db: AsyncSession = Depends(get_db)
):
    service = WorkspaceService(db)
    try:
        member = await service.remove_member(workspace_id, actor_identity_id, person_id)
    except Exception as exc:
        raise _handle(exc) from exc
    return {"member": member.to_dict()}


@router.post("/{workspace_id}/members/{person_id}/suspend")
async def suspend_member(
    workspace_id: str, person_id: str, actor_identity_id: str, db: AsyncSession = Depends(get_db)
):
    service = WorkspaceService(db)
    try:
        member = await service.suspend_member(workspace_id, actor_identity_id, person_id)
    except Exception as exc:
        raise _handle(exc) from exc
    return {"member": member.to_dict()}


@router.post("/{workspace_id}/members/{person_id}/role")
async def assign_role(
    workspace_id: str,
    person_id: str,
    actor_identity_id: str,
    role_name: str,
    db: AsyncSession = Depends(get_db),
):
    service = WorkspaceService(db)
    try:
        member = await service.assign_role(workspace_id, actor_identity_id, person_id, role_name)
    except Exception as exc:
        raise _handle(exc) from exc
    return {"member": member.to_dict()}


@router.post("/{workspace_id}/invitations")
async def invite_member(
    workspace_id: str,
    actor_identity_id: str,
    invitee_email: str,
    role_name: str,
    invitee_person_id: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    service = WorkspaceService(db)
    try:
        invitation = await service.invite_member(
            workspace_id=workspace_id,
            actor_identity_id=actor_identity_id,
            invitee_email=invitee_email,
            role_name=role_name,
            invitee_person_id=invitee_person_id,
        )
    except Exception as exc:
        raise _handle(exc) from exc
    return {"invitation": invitation.to_dict()}


@router.post("/{workspace_id}/invitations/{invitation_id}/revoke")
async def revoke_invitation(
    workspace_id: str,
    invitation_id: str,
    actor_identity_id: str,
    db: AsyncSession = Depends(get_db),
):
    service = WorkspaceService(db)
    try:
        invitation = await service.revoke_invitation(
            workspace_id, actor_identity_id, invitation_id
        )
    except Exception as exc:
        raise _handle(exc) from exc
    return {"invitation": invitation.to_dict()}


@router.post("/{workspace_id}/permission-templates")
async def create_permission_template(
    workspace_id: str,
    actor_identity_id: str,
    name: str,
    permissions: str,
    description: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    import json

    service = WorkspaceService(db)
    try:
        template = await service.create_permission_template(
            workspace_id=workspace_id,
            actor_identity_id=actor_identity_id,
            name=name,
            permissions=json.loads(permissions) if permissions else [],
            description=description,
        )
    except Exception as exc:
        raise _handle(exc) from exc
    return {"template": template.to_dict()}


@router.get("/{workspace_id}/permission-templates")
async def list_permission_templates(workspace_id: str, db: AsyncSession = Depends(get_db)):
    service = WorkspaceService(db)
    templates = await service.list_permission_templates(workspace_id)
    return {"templates": [t.to_dict() for t in templates]}


@router.post("/{workspace_id}/departments")
async def create_department(
    workspace_id: str,
    actor_identity_id: str,
    name_en: str,
    name_ar: str,
    dept_type: str | None = None,
    head_person_id: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    service = WorkspaceService(db)
    try:
        dept = await service.create_department(
            workspace_id=workspace_id,
            actor_identity_id=actor_identity_id,
            name_en=name_en,
            name_ar=name_ar,
            dept_type=dept_type,
            head_person_id=head_person_id,
        )
    except Exception as exc:
        raise _handle(exc) from exc
    return {"department": dept.to_dict()}


@router.get("/{workspace_id}/departments")
async def list_departments(workspace_id: str, db: AsyncSession = Depends(get_db)):
    service = WorkspaceService(db)
    departments = await service.list_departments(workspace_id)
    return {"departments": [d.to_dict() for d in departments]}


@router.post("/{workspace_id}/teams")
async def create_team(
    workspace_id: str,
    actor_identity_id: str,
    name_en: str,
    name_ar: str,
    department_id: str | None = None,
    leader_person_id: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    service = WorkspaceService(db)
    try:
        team = await service.create_team(
            workspace_id=workspace_id,
            actor_identity_id=actor_identity_id,
            name_en=name_en,
            name_ar=name_ar,
            department_id=department_id,
            leader_person_id=leader_person_id,
        )
    except Exception as exc:
        raise _handle(exc) from exc
    return {"team": team.to_dict()}


@router.get("/{workspace_id}/teams")
async def list_teams(workspace_id: str, db: AsyncSession = Depends(get_db)):
    service = WorkspaceService(db)
    teams = await service.list_teams(workspace_id)
    return {"teams": [t.to_dict() for t in teams]}


@router.post("/{workspace_id}/delegations")
async def delegate_authority(
    workspace_id: str,
    delegated_from_person_id: str,
    delegated_to_person_id: str,
    permissions: str,
    end_at: datetime | None = None,
    db: AsyncSession = Depends(get_db),
):
    import json

    service = WorkspaceService(db)
    try:
        delegation = await service.delegate_authority(
            workspace_id=workspace_id,
            delegated_from_person_id=delegated_from_person_id,
            delegated_to_person_id=delegated_to_person_id,
            permissions=json.loads(permissions) if permissions else [],
            end_at=end_at,
        )
    except Exception as exc:
        raise _handle(exc) from exc
    return {"delegation": delegation.to_dict()}


@router.get("/{workspace_id}/permissions/check")
async def check_permission(
    workspace_id: str, identity_id: str, permission: str, db: AsyncSession = Depends(get_db)
):
    service = WorkspaceService(db)
    allowed = await service.check_permission(workspace_id, identity_id, permission)
    return {"allowed": allowed, "workspace_id": workspace_id, "permission": permission}
