from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.identity.api.workspaces import NiamActor, get_current_niam_actor
from app.identity.models.authorization import Permission, Role, RoleAssignment
from app.identity.models.membership import Membership
from app.identity.models.workspace import Workspace, WorkspaceSessionContext, WorkspaceStatus
from app.identity.services.authorization_decision import (
    AuthorizationActor,
    AuthorizationDecisionService,
    AuthorizationRequest,
)
from app.identity.services.authorization_service_v2 import (
    AuthorizationCatalogError,
    RoleAssignmentStateError,
    RoleAuthorizationDenied,
    RolePermissionService,
)
from app.identity.services.membership_service import MembershipService

router = APIRouter(prefix="/roles", tags=["NIAM Roles"])


class RoleAssignmentRequest(BaseModel):
    account_id: str = Field(min_length=1, max_length=26)
    membership_id: str = Field(min_length=1, max_length=26)
    role_id: str = Field(min_length=1, max_length=26)
    facility_id: str | None = Field(default=None, max_length=26)
    department_id: str | None = Field(default=None, max_length=26)
    unit_id: str | None = Field(default=None, max_length=26)
    workspace_id: str | None = Field(default=None, max_length=26)


class RoleRevokeRequest(BaseModel):
    reason: str | None = Field(default=None, max_length=500)


def serialize_role(role: Role) -> dict[str, object]:
    return {
        "id": role.id,
        "uuid": role.uuid,
        "role_key": role.role_key,
        "name": role.name,
        "name_ar": role.name_ar,
        "scope_type": role.scope_type,
        "status": role.status,
        "is_system": role.is_system,
        "version": role.version,
    }


def serialize_permission(permission: Permission) -> dict[str, object]:
    return {
        "id": permission.id,
        "uuid": permission.uuid,
        "permission_key": permission.permission_key,
        "name": permission.name,
        "name_ar": permission.name_ar,
        "resource": permission.resource,
        "action": permission.action,
        "sensitivity": permission.sensitivity,
        "status": permission.status,
        "version": permission.version,
    }


def serialize_assignment(assignment: RoleAssignment) -> dict[str, object]:
    return {
        "id": assignment.id,
        "uuid": assignment.uuid,
        "account_id": assignment.account_id,
        "membership_id": assignment.membership_id,
        "role_id": assignment.role_id,
        "organization_id": assignment.organization_id,
        "facility_id": assignment.facility_id,
        "department_id": assignment.department_id,
        "unit_id": assignment.unit_id,
        "workspace_id": assignment.workspace_id,
        "scope_type": assignment.scope_type,
        "status": assignment.status,
        "expires_at": assignment.expires_at.isoformat() if assignment.expires_at else None,
        "version": assignment.version,
    }


@router.get("")
async def list_roles(
    actor: NiamActor = Depends(get_current_niam_actor),
    db: AsyncSession = Depends(get_db),
):
    del actor
    roles = await RolePermissionService(db).list_roles()
    return {"roles": [serialize_role(role) for role in roles]}


@router.get("/permissions")
async def list_permissions(
    actor: NiamActor = Depends(get_current_niam_actor),
    db: AsyncSession = Depends(get_db),
):
    del actor
    permissions = await RolePermissionService(db).list_permissions()
    return {"permissions": [serialize_permission(permission) for permission in permissions]}


async def _require_phase8_decision(
    actor: NiamActor,
    db: AsyncSession,
    request: AuthorizationRequest,
) -> None:
    decision = await AuthorizationDecisionService(db).authorize(
        AuthorizationActor(account=actor.account, session=actor.session),
        request,
    )
    if not decision.allowed:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Authorization denied")


async def _resolve_trusted_scope(
    actor: NiamActor,
    db: AsyncSession,
    *,
    organization_id: str,
    facility_id: str | None,
    department_id: str | None,
    unit_id: str | None,
    workspace_id: str | None,
) -> dict[str, str | None]:
    context = await db.scalar(
        select(WorkspaceSessionContext).where(
            WorkspaceSessionContext.session_id == actor.session.id,
            WorkspaceSessionContext.account_id == actor.account.id,
            WorkspaceSessionContext.is_active.is_(True),
        ),
    )
    if context is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Workspace context is required")
    workspace = await db.get(Workspace, context.workspace_id)
    if workspace is None or workspace.status != WorkspaceStatus.active.value:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Workspace context is unavailable")
    if workspace.organization_id != organization_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Organization context mismatch")

    resolved = {
        "organization_id": workspace.organization_id,
        "facility_id": workspace.facility_id,
        "department_id": workspace.department_id,
        "unit_id": None,
        "workspace_id": workspace.id,
    }
    for field, requested in (
        ("facility_id", facility_id),
        ("department_id", department_id),
        ("unit_id", unit_id),
        ("workspace_id", workspace_id),
    ):
        if requested is not None and requested != resolved[field]:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Authorization scope mismatch")
    return resolved


@router.get("/effective")
async def effective_permissions(
    organization_id: str = Query(min_length=1, max_length=26),
    facility_id: str | None = Query(default=None, max_length=26),
    department_id: str | None = Query(default=None, max_length=26),
    unit_id: str | None = Query(default=None, max_length=26),
    workspace_id: str | None = Query(default=None, max_length=26),
    actor: NiamActor = Depends(get_current_niam_actor),
    db: AsyncSession = Depends(get_db),
):
    resolved = await _resolve_trusted_scope(
        actor,
        db,
        organization_id=organization_id,
        facility_id=facility_id,
        department_id=department_id,
        unit_id=unit_id,
        workspace_id=workspace_id,
    )
    await _require_phase8_decision(
        actor,
        db,
        AuthorizationRequest(
            subject_account_id=actor.account.id,
            action="read",
            resource_type="membership",
            permission_key="membership.read",
            organization_id=resolved["organization_id"],
            facility_id=resolved["facility_id"],
            department_id=resolved["department_id"],
            unit_id=resolved["unit_id"],
            workspace_id=resolved["workspace_id"],
            resource_context=dict(resolved),
        ),
    )
    permissions = await RolePermissionService(db).effective_permissions(
        actor.account.id,
        resolved["organization_id"] or organization_id,
        facility_id=resolved["facility_id"],
        department_id=resolved["department_id"],
        unit_id=resolved["unit_id"],
        workspace_id=resolved["workspace_id"],
    )
    return {**resolved, "permissions": sorted(permissions)}


@router.post("/assignments", status_code=status.HTTP_201_CREATED)
async def assign_role(
    body: RoleAssignmentRequest,
    actor: NiamActor = Depends(get_current_niam_actor),
    db: AsyncSession = Depends(get_db),
):
    target_membership = await db.get(Membership, body.membership_id)
    if target_membership is None or target_membership.account_id != body.account_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Role assignment denied")
    await _require_phase8_decision(
        actor,
        db,
        AuthorizationRequest(
            subject_account_id=actor.account.id,
            action="assign",
            resource_type="role",
            permission_key="role.assign",
            organization_id=target_membership.organization_id,
            facility_id=body.facility_id,
            department_id=body.department_id,
            unit_id=body.unit_id,
            workspace_id=body.workspace_id,
            sensitivity="critical",
            resource_context={
                "organization_id": target_membership.organization_id,
                "facility_id": body.facility_id,
                "department_id": body.department_id,
                "unit_id": body.unit_id,
                "workspace_id": body.workspace_id,
            },
        ),
    )
    try:
        assignment = await RolePermissionService(db).grant_role(
            actor_id=actor.account.id,
            account_id=body.account_id,
            membership_id=body.membership_id,
            role_id=body.role_id,
            facility_id=body.facility_id,
            department_id=body.department_id,
            unit_id=body.unit_id,
            workspace_id=body.workspace_id,
        )
    except RoleAuthorizationDenied as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Role assignment denied") from exc
    except AuthorizationCatalogError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
    except RoleAssignmentStateError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    return serialize_assignment(assignment)


@router.post("/assignments/{assignment_id}/revoke")
async def revoke_role(
    assignment_id: str,
    body: RoleRevokeRequest | None = None,
    actor: NiamActor = Depends(get_current_niam_actor),
    db: AsyncSession = Depends(get_db),
):
    existing_assignment = await db.get(RoleAssignment, assignment_id)
    if existing_assignment is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role assignment not found")
    await _require_phase8_decision(
        actor,
        db,
        AuthorizationRequest(
            subject_account_id=actor.account.id,
            action="revoke",
            resource_type="role",
            resource_id=assignment_id,
            organization_id=existing_assignment.organization_id,
            sensitivity="critical",
            resource_context={
                "exists": True,
                "organization_id": existing_assignment.organization_id,
            },
        ),
    )
    try:
        assignment = await RolePermissionService(db).revoke_role(assignment_id, actor.account.id, body.reason if body else None)
    except RoleAuthorizationDenied as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Role revocation denied") from exc
    except RoleAssignmentStateError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    return serialize_assignment(assignment)


@router.get("/assignments")
async def list_role_assignments(
    organization_id: str = Query(min_length=1, max_length=26),
    account_id: str | None = Query(default=None, max_length=26),
    actor: NiamActor = Depends(get_current_niam_actor),
    db: AsyncSession = Depends(get_db),
):
    target_account = account_id or actor.account.id
    if target_account != actor.account.id and not await MembershipService(db)._can_manage_organization(actor.account.id, organization_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Role assignment listing denied")
    result = await db.execute(
        select(RoleAssignment).where(
            RoleAssignment.account_id == target_account,
            RoleAssignment.organization_id == organization_id,
        ).order_by(RoleAssignment.created_at.desc()),
    )
    return {"assignments": [serialize_assignment(item) for item in result.scalars().all()]}
