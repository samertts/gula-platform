from __future__ import annotations

import json
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.identity.admin.models import (
    EnterprisePortal,
    FHIRConnection,
    PortalBranch,
    PortalFacility,
    PortalSubscription,
)
from app.identity.admin.services import EnterprisePortalService
from app.identity.api.workspaces import NiamActor, get_current_niam_actor
from app.identity.services.authorization_decision import (
    AuthorizationActor,
    AuthorizationDecisionService,
    AuthorizationRequest,
)
from app.identity.services.canonical_audit import CanonicalAuditService

router = APIRouter(prefix="/admin", tags=["NIAM Admin"])


def _require_permission(
    actor: NiamActor,
    db: Session,
    *,
    organization_id: str,
    permission_key: str,
) -> None:
    decision = AuthorizationDecisionService(db).authorize(
        AuthorizationActor(account=actor.account, session=actor.session),
        AuthorizationRequest(
            subject_account_id=actor.account.id,
            action="read" if permission_key.endswith(".read") else "manage",
            resource_type=permission_key.split(".", 1)[0],
            permission_key=permission_key,
            organization_id=organization_id,
            sensitivity="high" if permission_key.endswith(".read") else "critical",
            resource_context={"exists": True, "organization_id": organization_id},
        ),
    )
    if not decision.allowed:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Administrative authorization denied")


def _safe_connection_payload(connection: FHIRConnection) -> dict[str, Any]:
    payload = connection.to_dict()
    payload.pop("credentials_encrypted", None)
    return payload


@router.post("/portals")
def create_portal(
    org_id: str,
    name: str,
    portal_type: str,
    features: str = "{}",
    actor: NiamActor = Depends(get_current_niam_actor),
    db: Session = Depends(get_db),
):
    _require_permission(actor, db, organization_id=org_id, permission_key="organization.manage")
    try:
        parsed_features = json.loads(features) if features else None
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="features must be valid JSON") from exc
    portal = EnterprisePortalService(db).create_portal(
        org_id=org_id,
        name=name,
        portal_type=portal_type,
        features=parsed_features,
        created_by=actor.account.id,
    )
    return {"portal": portal.to_dict()}


@router.get("/portals/organization/{org_id}")
def list_org_portals(
    org_id: str,
    actor: NiamActor = Depends(get_current_niam_actor),
    db: Session = Depends(get_db),
):
    _require_permission(actor, db, organization_id=org_id, permission_key="organization.read")
    portals = EnterprisePortalService(db).get_portals_for_org(org_id)
    return {"portals": [portal.to_dict() for portal in portals]}


@router.post("/portals/{portal_id}/branches")
def add_branch(
    portal_id: str,
    org_id: str,
    name_en: str,
    name_ar: str,
    address: str = "",
    phone: str = "",
    email: str = "",
    manager_person_id: str = "",
    actor: NiamActor = Depends(get_current_niam_actor),
    db: Session = Depends(get_db),
):
    portal = (
        db.execute(
            select(EnterprisePortal).where(EnterprisePortal.portal_id == portal_id, EnterprisePortal.is_active.is_(True)),
        )
    ).scalar_one_or_none()
    if portal is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Portal not found")
    if portal.organization_id != org_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Portal organization mismatch")
    _require_permission(actor, db, organization_id=portal.organization_id, permission_key="organization.manage")
    branch = EnterprisePortalService(db).add_branch(
        portal_id=portal.id,
        org_id=portal.organization_id,
        name_en=name_en,
        name_ar=name_ar,
        address=address or None,
        phone=phone or None,
        email=email or None,
        manager_person_id=manager_person_id or None,
        actor_id=actor.account.id,
    )
    return {"branch": branch.to_dict()}


@router.post("/branches/{branch_id}/facilities")
def add_facility(
    branch_id: str,
    org_id: str,
    name_en: str,
    name_ar: str,
    facility_type: str,
    license_number: str = "",
    accreditation: str = "",
    address: str = "",
    actor: NiamActor = Depends(get_current_niam_actor),
    db: Session = Depends(get_db),
):
    branch = (
        db.execute(
            select(PortalBranch).where(PortalBranch.branch_id == branch_id, PortalBranch.is_active.is_(True)),
        )
    ).scalar_one_or_none()
    if branch is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Branch not found")
    if branch.organization_id != org_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Branch organization mismatch")
    _require_permission(actor, db, organization_id=branch.organization_id, permission_key="organization.manage")
    facility = EnterprisePortalService(db).add_facility(
        branch_id=branch.id,
        org_id=branch.organization_id,
        name_en=name_en,
        name_ar=name_ar,
        facility_type=facility_type,
        license_number=license_number or None,
        accreditation=accreditation or None,
        address=address or None,
        actor_id=actor.account.id,
    )
    return {"facility": facility.to_dict()}


@router.post("/facilities/{facility_id}/departments")
def add_department(
    facility_id: str,
    name_en: str,
    name_ar: str,
    dept_type: str = "",
    head_person_id: str = "",
    actor: NiamActor = Depends(get_current_niam_actor),
    db: Session = Depends(get_db),
):
    organization_id = (
        db.execute(
            select(PortalFacility.organization_id).where(PortalFacility.facility_id == facility_id, PortalFacility.is_active.is_(True)),
        )
    ).scalar_one_or_none()
    if organization_id is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Facility not found")
    _require_permission(actor, db, organization_id=organization_id, permission_key="organization.manage")
    department = EnterprisePortalService(db).add_department(
        facility_id=facility_id,
        name_en=name_en,
        name_ar=name_ar,
        dept_type=dept_type or None,
        head_person_id=head_person_id or None,
        organization_id=organization_id,
        actor_id=actor.account.id,
    )
    return {"department": department.to_dict()}


@router.get("/subscriptions/{org_id}")
def get_subscription(
    org_id: str,
    actor: NiamActor = Depends(get_current_niam_actor),
    db: Session = Depends(get_db),
):
    _require_permission(actor, db, organization_id=org_id, permission_key="organization.read")
    subscription = EnterprisePortalService(db).get_subscription(org_id)
    return {"subscription": subscription.to_dict() if subscription else None}


@router.post("/subscriptions")
def create_subscription(
    org_id: str,
    plan_type: str,
    user_limit: int = 0,
    storage_limit: int = 0,
    api_call_limit: int = 0,
    billing_cycle: str = "monthly",
    billing_amount: int = 0,
    currency: str = "IQD",
    auto_renew: bool = False,
    actor: NiamActor = Depends(get_current_niam_actor),
    db: Session = Depends(get_db),
):
    _require_permission(actor, db, organization_id=org_id, permission_key="subscription.manage")
    subscription = EnterprisePortalService(db).manage_subscription(
        org_id=org_id,
        plan_type=plan_type,
        user_limit=user_limit or None,
        storage_limit=storage_limit or None,
        api_call_limit=api_call_limit or None,
        billing_cycle=billing_cycle,
        billing_amount=billing_amount or None,
        currency=currency,
        auto_renew=auto_renew,
        actor_id=actor.account.id,
    )
    return {"subscription": subscription.to_dict()}


@router.put("/subscriptions/{sub_id}")
def update_subscription(
    sub_id: str,
    plan_type: str = "",
    billing_cycle: str = "",
    billing_amount: int = 0,
    auto_renew: bool = False,
    actor: NiamActor = Depends(get_current_niam_actor),
    db: Session = Depends(get_db),
):
    subscription = (
        db.execute(
            select(PortalSubscription).where(PortalSubscription.sub_id == sub_id, PortalSubscription.is_active.is_(True)),
        )
    ).scalar_one_or_none()
    if subscription is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subscription not found")
    _require_permission(actor, db, organization_id=subscription.organization_id, permission_key="subscription.manage")
    kwargs: dict[str, Any] = {"auto_renew": auto_renew}
    if plan_type:
        kwargs["plan_type"] = plan_type
    if billing_cycle:
        kwargs["billing_cycle"] = billing_cycle
    if billing_amount:
        kwargs["billing_amount"] = billing_amount
    updated = EnterprisePortalService(db).update_subscription(sub_id, actor_id=actor.account.id, **kwargs)
    return {"subscription": updated.to_dict() if updated else None}


@router.post("/fhir-connections")
def create_fhir_connection(
    org_id: str,
    name: str,
    fhir_version: str,
    base_url: str,
    auth_type: str,
    actor: NiamActor = Depends(get_current_niam_actor),
    db: Session = Depends(get_db),
):
    _require_permission(actor, db, organization_id=org_id, permission_key="integration.manage")
    try:
        connection = EnterprisePortalService(db).create_fhir_connection(
            org_id=org_id,
            name=name,
            fhir_version=fhir_version,
            base_url=base_url,
            auth_type=auth_type,
            credentials_encrypted=None,
            actor_id=actor.account.id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
    return {"fhir_connection": _safe_connection_payload(connection)}


@router.get("/fhir-connections/organization/{org_id}")
def list_fhir_connections(
    org_id: str,
    actor: NiamActor = Depends(get_current_niam_actor),
    db: Session = Depends(get_db),
):
    _require_permission(actor, db, organization_id=org_id, permission_key="organization.read")
    connections = EnterprisePortalService(db).get_fhir_connections_for_org(org_id)
    return {"fhir_connections": [_safe_connection_payload(connection) for connection in connections]}


@router.post("/fhir-connections/{conn_id}/test")
async def test_fhir_connection(
    conn_id: str,
    actor: NiamActor = Depends(get_current_niam_actor),
    db: Session = Depends(get_db),
):
    connection = (
        db.execute(
            select(FHIRConnection).where(FHIRConnection.conn_id == conn_id, FHIRConnection.is_active.is_(True)),
        )
    ).scalar_one_or_none()
    if connection is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="FHIR connection not found")
    _require_permission(actor, db, organization_id=connection.organization_id, permission_key="integration.manage")
    # NR-044.3 Class B: this is the one identity service method that is still a
    # coroutine, because it performs a genuine httpx call to an external FHIR
    # server between two database statements. Its database work is synchronous
    # now; the HTTP boundary is not, so the route still awaits it.
    return await EnterprisePortalService(db).test_fhir_connection(conn_id, actor_id=actor.account.id)


@router.get("/audit-log/{org_id}")
def get_audit_log(
    org_id: str,
    limit: int = Query(default=100, ge=1, le=100),
    actor: NiamActor = Depends(get_current_niam_actor),
    db: Session = Depends(get_db),
):
    _require_permission(actor, db, organization_id=org_id, permission_key="audit.read")
    entries = CanonicalAuditService(db).search(organization_id=org_id, limit=limit)
    return {"audit_log": [{"id": entry.id, "event_type": entry.event_type, "action": entry.action, "decision": entry.decision, "occurred_at": entry.occurred_at.isoformat()} for entry in entries]}
