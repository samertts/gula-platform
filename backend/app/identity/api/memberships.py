from __future__ import annotations

from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database import get_db
from app.identity.api.workspaces import NiamActor, get_current_niam_actor
from app.identity.models.membership import Membership, MembershipApplication, MembershipInvitation
from app.identity.services.authorization_decision import (
    AuthorizationActor,
    AuthorizationDecisionService,
    AuthorizationRequest,
)
from app.identity.services.membership_service import (
    InvitationError,
    MembershipAccessDenied,
    MembershipService,
    MembershipStateError,
    MembershipValidationError,
)

router = APIRouter(prefix="/memberships", tags=["NIAM Memberships"])


class MembershipContextRequest(BaseModel):
    organization_id: str = Field(min_length=1, max_length=26)
    relationship_type: str = Field(min_length=1, max_length=50)
    scope_type: str = Field(min_length=1, max_length=30)
    facility_id: str | None = Field(default=None, max_length=26)
    department_id: str | None = Field(default=None, max_length=26)
    unit_id: str | None = Field(default=None, max_length=26)
    workspace_id: str | None = Field(default=None, max_length=26)


class MembershipApplicationRequest(MembershipContextRequest):
    identity_id: str | None = Field(default=None, max_length=26)


class MembershipInvitationRequest(MembershipContextRequest):
    recipient_account_id: str | None = Field(default=None, max_length=26)
    ttl_hours: int = Field(default=24, ge=1, le=168)


class InvitationTokenRequest(BaseModel):
    token: str = Field(min_length=32, max_length=256)


class MembershipActionRequest(BaseModel):
    reason: str | None = Field(default=None, max_length=500)


def _require_phase8_management(
    actor: NiamActor,
    db: Session,
    *,
    action: str,
    organization_id: str,
    resource_id: str | None = None,
    resource_type: str = "membership",
    resource_exists: bool = False,
) -> None:
    decision = AuthorizationDecisionService(db).authorize(
        AuthorizationActor(account=actor.account, session=actor.session),
        AuthorizationRequest(
            subject_account_id=actor.account.id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            organization_id=organization_id,
            sensitivity="critical" if action in {"approve", "revoke", "suspend", "reactivate"} else "high",
            resource_context={"exists": resource_exists, "organization_id": organization_id},
        ),
    )
    if not decision.allowed:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Membership authorization denied")


def serialize_membership(membership: Membership) -> dict[str, object]:
    return {
        "id": membership.id,
        "uuid": membership.uuid,
        "account_id": membership.account_id,
        "identity_id": membership.identity_id,
        "organization_id": membership.organization_id,
        "facility_id": membership.facility_id,
        "department_id": membership.department_id,
        "unit_id": membership.unit_id,
        "workspace_id": membership.workspace_id,
        "relationship_type": membership.relationship_type,
        "scope_type": membership.scope_type,
        "status": membership.status,
        "source": membership.source,
        "expires_at": membership.expires_at.isoformat() if membership.expires_at else None,
        "version": membership.version,
        "is_active": membership.is_active,
    }


def serialize_application(application: MembershipApplication) -> dict[str, object]:
    return {
        "id": application.id,
        "uuid": application.uuid,
        "account_id": application.account_id,
        "organization_id": application.organization_id,
        "facility_id": application.facility_id,
        "department_id": application.department_id,
        "unit_id": application.unit_id,
        "workspace_id": application.workspace_id,
        "relationship_type": application.relationship_type,
        "scope_type": application.scope_type,
        "status": application.status,
        "submitted_at": application.submitted_at.isoformat() if application.submitted_at else None,
        "version": application.version,
    }


def serialize_invitation(invitation: MembershipInvitation, raw_token: str | None = None) -> dict[str, object]:
    result: dict[str, object] = {
        "id": invitation.id,
        "uuid": invitation.uuid,
        "organization_id": invitation.organization_id,
        "facility_id": invitation.facility_id,
        "department_id": invitation.department_id,
        "unit_id": invitation.unit_id,
        "workspace_id": invitation.workspace_id,
        "relationship_type": invitation.relationship_type,
        "scope_type": invitation.scope_type,
        "status": invitation.status,
        "recipient_account_id": invitation.recipient_account_id,
        "expires_at": invitation.expires_at.isoformat(),
        "version": invitation.version,
    }
    if raw_token is not None:
        result["token"] = raw_token
    return result


@router.get("/me")
def list_my_memberships(
    actor: NiamActor = Depends(get_current_niam_actor),
    db: Session = Depends(get_db),
):
    memberships = MembershipService(db).list_for_account(actor.account.id)
    return {"memberships": [serialize_membership(item) for item in memberships]}


@router.post("/applications", status_code=status.HTTP_201_CREATED)
def submit_membership_application(
    body: MembershipApplicationRequest,
    actor: NiamActor = Depends(get_current_niam_actor),
    db: Session = Depends(get_db),
):
    try:
        application = MembershipService(db).create_application(
            account_id=actor.account.id,
            identity_id=body.identity_id or actor.account.identity_id,
            organization_id=body.organization_id,
            relationship_type=body.relationship_type,
            scope_type=body.scope_type,
            actor_id=actor.account.id,
            facility_id=body.facility_id,
            department_id=body.department_id,
            unit_id=body.unit_id,
            workspace_id=body.workspace_id,
        )
    except MembershipAccessDenied as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Membership application denied") from exc
    except MembershipValidationError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
    return serialize_application(application)


@router.post("/applications/{application_id}/approve")
def approve_membership_application(
    application_id: str,
    actor: NiamActor = Depends(get_current_niam_actor),
    db: Session = Depends(get_db),
):
    application = db.get(MembershipApplication, application_id)
    if application is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Membership application not found")
    _require_phase8_management(
        actor,
        db,
        action="approve",
        organization_id=application.organization_id,
        resource_id=application_id,
        resource_type="membership_application",
        resource_exists=True,
    )
    try:
        membership = MembershipService(db).approve_application(application_id, actor.account.id)
    except MembershipAccessDenied as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Membership approval denied") from exc
    except MembershipValidationError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except MembershipStateError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    return serialize_membership(membership)


@router.post("/invitations", status_code=status.HTTP_201_CREATED)
def create_membership_invitation(
    body: MembershipInvitationRequest,
    actor: NiamActor = Depends(get_current_niam_actor),
    db: Session = Depends(get_db),
):
    _require_phase8_management(
        actor,
        db,
        action="invite",
        organization_id=body.organization_id,
    )
    try:
        invitation, raw_token = MembershipService(db).create_invitation(
            actor_id=actor.account.id,
            organization_id=body.organization_id,
            relationship_type=body.relationship_type,
            scope_type=body.scope_type,
            recipient_account_id=body.recipient_account_id,
            facility_id=body.facility_id,
            department_id=body.department_id,
            unit_id=body.unit_id,
            workspace_id=body.workspace_id,
            ttl=timedelta(hours=body.ttl_hours),
        )
    except MembershipAccessDenied as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invitation creation denied") from exc
    except MembershipValidationError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
    except InvitationError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    return serialize_invitation(invitation, raw_token=raw_token)


@router.post("/invitations/{invitation_id}/accept")
def accept_membership_invitation(
    invitation_id: str,
    body: InvitationTokenRequest,
    actor: NiamActor = Depends(get_current_niam_actor),
    db: Session = Depends(get_db),
):
    try:
        membership = MembershipService(db).accept_invitation(invitation_id, actor.account.id, body.token)
    except InvitationError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Invitation is invalid or unavailable") from exc
    except MembershipAccessDenied as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invitation acceptance denied") from exc
    except MembershipStateError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    return serialize_membership(membership)


@router.post("/invitations/{invitation_id}/revoke")
def revoke_membership_invitation(
    invitation_id: str,
    actor: NiamActor = Depends(get_current_niam_actor),
    db: Session = Depends(get_db),
):
    invitation = db.get(MembershipInvitation, invitation_id)
    if invitation is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invitation not found")
    _require_phase8_management(
        actor,
        db,
        action="revoke",
        organization_id=invitation.organization_id,
        resource_id=invitation_id,
        resource_type="membership_invitation",
        resource_exists=True,
    )
    try:
        invitation = MembershipService(db).revoke_invitation(invitation_id, actor.account.id)
    except MembershipAccessDenied as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invitation revocation denied") from exc
    except InvitationError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    return serialize_invitation(invitation)


@router.post("/{membership_id}/revoke")
def revoke_membership(
    membership_id: str,
    body: MembershipActionRequest | None = None,
    actor: NiamActor = Depends(get_current_niam_actor),
    db: Session = Depends(get_db),
):
    membership = db.get(Membership, membership_id)
    if membership is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Membership not found")
    _require_phase8_management(
        actor,
        db,
        action="revoke",
        organization_id=membership.organization_id,
        resource_id=membership_id,
        resource_exists=True,
    )
    try:
        membership = MembershipService(db).revoke_membership(membership_id, actor.account.id, body.reason if body else None)
    except MembershipAccessDenied as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Membership revocation denied") from exc
    except MembershipValidationError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except MembershipStateError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    return serialize_membership(membership)


@router.post("/{membership_id}/suspend")
def suspend_membership(
    membership_id: str,
    body: MembershipActionRequest | None = None,
    actor: NiamActor = Depends(get_current_niam_actor),
    db: Session = Depends(get_db),
):
    membership = db.get(Membership, membership_id)
    if membership is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Membership not found")
    _require_phase8_management(
        actor,
        db,
        action="suspend",
        organization_id=membership.organization_id,
        resource_id=membership_id,
        resource_exists=True,
    )
    try:
        membership = MembershipService(db).suspend_membership(membership_id, actor.account.id, body.reason if body else None)
    except MembershipAccessDenied as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Membership suspension denied") from exc
    except MembershipValidationError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except MembershipStateError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    return serialize_membership(membership)


@router.post("/{membership_id}/reactivate")
def reactivate_membership(
    membership_id: str,
    actor: NiamActor = Depends(get_current_niam_actor),
    db: Session = Depends(get_db),
):
    membership = db.get(Membership, membership_id)
    if membership is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Membership not found")
    _require_phase8_management(
        actor,
        db,
        action="reactivate",
        organization_id=membership.organization_id,
        resource_id=membership_id,
        resource_exists=True,
    )
    try:
        membership = MembershipService(db).reactivate_membership(membership_id, actor.account.id)
    except MembershipAccessDenied as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Membership reactivation denied") from exc
    except MembershipValidationError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except MembershipStateError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    return serialize_membership(membership)
