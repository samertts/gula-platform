from __future__ import annotations
from app.services.route_audit import audit_route_mutation

import logging
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app._compat import UTC
from app.database import get_db
from app.models.authorization import BreakGlassSession
from app.models.user import User
from app.security.dependencies import get_current_user
from app.services.authorization_service import (
    AuthorizationAuditService,
    AuthorizationCheckService,
    BreakGlassService,
    DelegationService,
    FieldSecurityService,
    IdentityService,
    MenuService,
    PermissionService,
    PolicyService,
    RoleAssignmentService,
    RoleService,
)

logger = logging.getLogger("gula.routes.authorization")

router = APIRouter(prefix="/authz", tags=["authorization"])


class PermissionCheckRequest(BaseModel):
    permission: str = Field(..., description="Permission ID to check")
    resource_attrs: dict[str, Any] | None = None
    environment: dict[str, Any] | None = None
    justification: str | None = Field(None, max_length=500)


class BatchPermissionCheckRequest(BaseModel):
    permissions: list[str] = Field(..., min_length=1, max_length=100)
    resource_attrs: dict[str, Any] | None = None
    environment: dict[str, Any] | None = None


class AssignRoleRequest(BaseModel):
    user_id: int
    role_id: str
    organization_id: int | None = None
    facility_id: int | None = None
    expires_at: str | None = None
    is_primary: bool = True


class DelegationCreateRequest(BaseModel):
    delegate_id: int
    role_id: str
    reason: str = Field(..., min_length=10, max_length=500)
    duration_hours: int = Field(..., ge=1, le=720)
    scope: dict[str, Any] | None = None


class BreakGlassActivateRequest(BaseModel):
    emergency_category: str = Field(..., pattern="^(clinical|technical|security|compliance|system_failure)$")
    justification: str = Field(..., min_length=10, max_length=500)
    patient_id: int | None = None
    duration_minutes: int = Field(60, ge=15, le=480)


# ── Permission Endpoints ───────────────────────────────────────────────────────


@router.get("/permissions")
def list_permissions(
    domain: str | None = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    svc = PermissionService(db)
    items = svc.get_all(domain=domain, skip=skip, limit=limit)
    total = svc.count(domain=domain)
    return {
        "items": [
            {
                "permission_id": p.permission_id,
                "name_en": p.name_en,
                "name_ar": p.name_ar,
                "domain": p.domain,
                "resource": p.resource,
                "action": p.action,
                "risk_level": p.risk_level,
                "is_sensitive": p.is_sensitive,
                "requires_mfa": p.requires_mfa,
                "requires_justification": p.requires_justification,
            }
            for p in items
        ],
        "total": total,
        "skip": skip,
        "limit": limit,
    }


@router.get("/permissions/domains")
def list_permission_domains(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    svc = PermissionService(db)
    return {"domains": svc.get_domains()}


@router.get("/permissions/{permission_id}")
def get_permission(
    permission_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    svc = PermissionService(db)
    perm = svc.get_by_id(permission_id)
    if not perm:
        raise HTTPException(status_code=404, detail="Permission not found")
    return perm


# ── Role Endpoints ─────────────────────────────────────────────────────────────


@router.get("/roles")
def list_roles(
    level: str | None = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    svc = RoleService(db)
    items = svc.get_all(level=level, skip=skip, limit=limit)
    return {
        "items": [
            {
                "role_id": r.role_id,
                "name_en": r.name_en,
                "name_ar": r.name_ar,
                "level": r.level,
                "parent_role_id": r.parent_role_id,
                "is_temporary": r.is_temporary,
                "is_delegatable": r.is_delegatable,
                "requires_mfa": r.requires_mfa,
            }
            for r in items
        ],
        "total": len(items),
        "skip": skip,
        "limit": limit,
    }


@router.get("/roles/levels")
def list_role_levels(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    svc = RoleService(db)
    return {"levels": svc.get_levels()}


@router.get("/roles/hierarchy")
def get_role_hierarchy(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    svc = RoleService(db)
    return {"hierarchy": svc.get_hierarchy()}


@router.get("/roles/{role_id}")
def get_role(
    role_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    svc = RoleService(db)
    role = svc.get_by_id(role_id)
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
    return {
        "role_id": role.role_id,
        "name_en": role.name_en,
        "name_ar": role.name_ar,
        "description": role.description,
        "level": role.level,
        "parent_role_id": role.parent_role_id,
        "is_temporary": role.is_temporary,
        "is_delegatable": role.is_delegatable,
        "requires_mfa": role.requires_mfa,
        "is_active": role.is_active,
    }


@router.get("/roles/{role_id}/permissions")
def get_role_permissions(
    role_id: str,
    inherited: bool = Query(False),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    svc = RoleService(db)
    if inherited:
        perms = svc.get_inherited_permissions(role_id)
    else:
        perm_objs = svc.get_permissions(role_id)
        perms = [p.permission_id for p in perm_objs]
    return {"role_id": role_id, "permissions": perms}


# ── Permission Check Endpoints ─────────────────────────────────────────────────


@router.post("/check")
def check_permission(
    req: PermissionCheckRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    svc = AuthorizationCheckService(db)
    return svc.check_permission(
        current_user,
        req.permission,
        resource_attrs=req.resource_attrs,
        environment=req.environment,
        justification=req.justification,
    )


@router.post("/check/batch")
def check_permissions_batch(
    req: BatchPermissionCheckRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    svc = AuthorizationCheckService(db)
    return svc.check_many(
        current_user,
        req.permissions,
        resource_attrs=req.resource_attrs,
        environment=req.environment,
    )


@router.get("/me/permissions")
def get_my_permissions(
    domain: str | None = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    svc = AuthorizationCheckService(db)
    permissions = svc.get_granted_permissions(current_user, domain=domain)
    return {
        "user_id": current_user.id,
        "permissions": permissions,
        "count": len(permissions),
    }


# ── Menu Endpoints ─────────────────────────────────────────────────────────────


@router.get("/me/menu")
def get_my_menu(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    check_svc = AuthorizationCheckService(db)
    menu_svc = MenuService(db)
    perms = check_svc.get_granted_permissions(current_user)
    menu = menu_svc.get_menu_for_user(current_user, all_permissions=perms)
    return {"menu": menu}


# ── Identity Endpoints ─────────────────────────────────────────────────────────


@router.get("/me")
def get_my_identity(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    svc = IdentityService(db)
    context = svc.get_identity_context(current_user)
    context["user"]["role"] = current_user.role
    context["user"]["lab_id"] = current_user.lab_id
    context["user"]["provider"] = "gula"
    return context


# ── Field Security Endpoints ───────────────────────────────────────────────────


@router.get("/field-security/{resource_type}/{field_name}")
def get_field_security(
    resource_type: str,
    field_name: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    svc = FieldSecurityService(db)
    return svc.get_field_mask(
        resource_type,
        field_name,
        user_role=current_user.role if hasattr(current_user, "role") else None,
        org_type=None,
    )


@router.post("/field-security/mask")
def mask_field_value(
    value: str,
    resource_type: str = Query(...),
    field_name: str = Query(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    fs_svc = FieldSecurityService(db)
    field_info = fs_svc.get_field_mask(
        resource_type,
        field_name,
        user_role=current_user.role if hasattr(current_user, "role") else None,
        org_type=None,
    )
    if field_info["masked"]:
        masked = fs_svc.mask_value(value, field_info["masking_pattern"])
        return {"original": value, "masked": masked, "level": field_info["level"]}
    return {"original": value, "masked": value, "level": field_info["level"]}


# ── Delegation Endpoints ───────────────────────────────────────────────────────


@audit_route_mutation(action="route.create_delegation", resource_type="authorization")
@router.post("/delegations", status_code=201)
def create_delegation(
    req: DelegationCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    svc = DelegationService(db)
    return svc.create_delegation(
        delegator_id=current_user.id,
        delegate_id=req.delegate_id,
        role_id=req.role_id,
        reason=req.reason,
        duration_hours=req.duration_hours,
        scope=req.scope,
    )


@audit_route_mutation(action="route.revoke_delegation", resource_type="authorization")
@router.delete("/delegations/{delegation_id}")
def revoke_delegation(
    delegation_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    svc = DelegationService(db)
    success = svc.revoke_delegation(delegation_id, revoked_by=current_user.id)
    if not success:
        raise HTTPException(status_code=404, detail="Delegation not found or already revoked")
    return Response(status_code=204, response_model=None)


@router.get("/delegations")
def list_my_delegations(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    svc = DelegationService(db)
    delegations = svc.get_active_for_user(current_user.id)
    return {
        "items": [
            {
                "id": d.id,
                "delegator_id": d.delegator_id,
                "delegate_id": d.delegate_id,
                "role_id": d.role_id,
                "delegation_type": d.delegation_type,
                "reason": d.reason,
                "starts_at": d.starts_at.isoformat(),
                "expires_at": d.expires_at.isoformat(),
                "status": d.status,
            }
            for d in delegations
        ],
    }


# ── Break Glass Endpoints ──────────────────────────────────────────────────────


@router.post("/break-glass/activate", status_code=201)
def activate_break_glass(
    req: BreakGlassActivateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    existing = db.query(BreakGlassSession).filter(
        BreakGlassSession.user_id == current_user.id,
        BreakGlassSession.status == "active",
        BreakGlassSession.expires_at > datetime.now(UTC),
    ).first()
    if existing:
        raise HTTPException(status_code=409, detail="An active break-glass session already exists")
    svc = BreakGlassService(db)
    session = svc.activate(
        user_id=current_user.id,
        emergency_category=req.emergency_category,
        justification=req.justification,
        patient_id=req.patient_id,
        duration_minutes=req.duration_minutes,
    )
    return {
        "session_id": session.id,
        "status": session.status,
        "started_at": session.started_at,
        "expires_at": session.expires_at,
        "warning": "All actions during this session are logged and will be reviewed.",
    }


@router.post("/break-glass/{session_id}/deactivate")
def deactivate_break_glass(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    svc = BreakGlassService(db)
    success = svc.deactivate(session_id)
    if not success:
        raise HTTPException(status_code=404, detail="Break-glass session not found or already deactivated")
    return {"status": "deactivated"}


@router.get("/break-glass/active")
def get_active_break_glass(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    svc = BreakGlassService(db)
    session = svc.get_active(current_user.id)
    if not session:
        return {"active": False, "session": None}
    return {
        "active": True,
        "session": {
            "id": session.id,
            "emergency_category": session.emergency_category,
            "justification": session.justification,
            "started_at": session.started_at,
            "expires_at": session.expires_at,
        },
    }


# ── Audit Endpoints ────────────────────────────────────────────────────────────


@router.get("/audit")
def query_authorization_audit(
    user_id: int | None = Query(None),
    decision: str | None = Query(None, pattern="^(allow|deny)$"),
    resource_type: str | None = Query(None),
    is_emergency: bool | None = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    svc = AuthorizationAuditService(db)
    items, total = svc.query(
        user_id=user_id,
        decision=decision,
        resource_type=resource_type,
        is_emergency=is_emergency,
        skip=skip,
        limit=limit,
    )
    return {
        "items": [
            {
                "decision_id": a.decision_id,
                "user_id": a.user_id,
                "user_role": a.user_role,
                "action": a.action,
                "resource_type": a.resource_type,
                "resource_id": a.resource_id,
                "decision": a.decision,
                "is_emergency": a.is_emergency,
                "created_at": a.created_at.isoformat() if a.created_at else None,
            }
            for a in items
        ],
        "total": total,
        "skip": skip,
        "limit": limit,
    }


# ── Policy Endpoints ───────────────────────────────────────────────────────────


@router.get("/policies")
def list_policies(
    status: str | None = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    svc = PolicyService(db)
    policies = svc.get_active_policies()
    return {
        "items": [
            {
                "policy_id": p.policy_id,
                "name_en": p.name_en,
                "name_ar": p.name_ar,
                "effect": p.effect,
                "priority": p.priority,
                "category": p.category,
            }
            for p in policies
        ],
    }


# ── Role Assignment Endpoints ──────────────────────────────────────────────────


@router.get("/assignments")
def list_my_assignments(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    svc = RoleAssignmentService(db)
    assignments = svc.get_for_user(current_user.id)
    return {
        "items": [
            {
                "role_id": a.role_id,
                "organization_id": a.organization_id,
                "facility_id": a.facility_id,
                "is_primary": a.is_primary,
                "is_delegated": a.is_delegated,
                "status": a.status,
                "expires_at": a.expires_at.isoformat() if a.expires_at else None,
            }
            for a in assignments
        ],
    }


@router.post("/assignments", status_code=201)
def assign_role(
    req: AssignRoleRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    expires_at = None
    if req.expires_at:
        try:
            expires_at = datetime.fromisoformat(req.expires_at)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid expires_at format") from None
    svc = RoleAssignmentService(db)
    return svc.assign_role(
        user_id=req.user_id,
        role_id=req.role_id,
        assigned_by=current_user.id,
        organization_id=req.organization_id,
        facility_id=req.facility_id,
        expires_at=expires_at,
        is_primary=req.is_primary,
    )


@audit_route_mutation(action="route.revoke_role_assignment", resource_type="authorization")
@router.delete("/assignments/{user_id}/{role_id}")
def revoke_role_assignment(
    user_id: int,
    role_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    svc = RoleAssignmentService(db)
    success = svc.revoke_role(user_id, role_id)
    if not success:
        raise HTTPException(status_code=404, detail="Role assignment not found")
    return Response(status_code=204, response_model=None)


# ── Routes Endpoint ────────────────────────────────────────────────────────────


ROUTES_REGISTRY: list[dict[str, Any]] = [
    {"path": "/dashboard", "permission": None, "label_en": "Dashboard", "label_ar": "لوحة التحكم"},
    {"path": "/patients", "permission": "patient.view", "label_en": "Patients", "label_ar": "المرضى"},
    {"path": "/patients/list", "permission": "patient.view", "label_en": "Patient List", "label_ar": "قائمة المرضى"},
    {"path": "/patients/register", "permission": "patient.create", "label_en": "Register Patient", "label_ar": "تسجيل مريض"},
    {"path": "/patients/{id}", "permission": "patient.view", "label_en": "Patient Detail", "label_ar": "تفاصيل المريض"},
    {"path": "/patients/{id}/edit", "permission": "patient.update", "label_en": "Edit Patient", "label_ar": "تعديل المريض"},
    {"path": "/orders", "permission": "order.view", "label_en": "Orders", "label_ar": "الطلبات"},
    {"path": "/orders/list", "permission": "order.view", "label_en": "Order List", "label_ar": "قائمة الطلبات"},
    {"path": "/orders/create", "permission": "order.create", "label_en": "New Order", "label_ar": "طلب جديد"},
    {"path": "/orders/{id}", "permission": "order.view", "label_en": "Order Detail", "label_ar": "تفاصيل الطلب"},
    {"path": "/results", "permission": "result.view", "label_en": "Results", "label_ar": "النتائج"},
    {"path": "/results/entry", "permission": "result.create", "label_en": "Result Entry", "label_ar": "إدخال النتائج"},
    {"path": "/results/review", "permission": "result.review", "label_en": "Review Results", "label_ar": "مراجعة النتائج"},
    {"path": "/results/history", "permission": "result.view", "label_en": "Result History", "label_ar": "سجل النتائج"},
    {"path": "/samples", "permission": "sample.view", "label_en": "Samples", "label_ar": "العينات"},
    {"path": "/analytics", "permission": "stats.view", "label_en": "Analytics", "label_ar": "التحليلات"},
    {"path": "/analytics/dashboard", "permission": "stats.view", "label_en": "Analytics Dashboard", "label_ar": "لوحة التحليلات"},
    {"path": "/analytics/epidemiology", "permission": "stats.epidemiology", "label_en": "Epidemiology", "label_ar": "علم الأوبئة"},
    {"path": "/analytics/reports", "permission": "stats.reports", "label_en": "Reports", "label_ar": "التقارير"},
    {"path": "/quality", "permission": "quality.view", "label_en": "Quality Control", "label_ar": "مراقبة الجودة"},
    {"path": "/inventory", "permission": "inventory.view", "label_en": "Inventory", "label_ar": "المخزون"},
    {"path": "/staff", "permission": "user.view", "label_en": "Staff", "label_ar": "الموظفون"},
    {"path": "/staff/roles", "permission": "role.manage", "label_en": "Role Management", "label_ar": "إدارة الأدوار"},
    {"path": "/settings", "permission": "settings.view", "label_en": "Settings", "label_ar": "الإعدادات"},
    {"path": "/settings/lab", "permission": "lab.manage", "label_en": "Lab Settings", "label_ar": "إعدادات المختبر"},
    {"path": "/settings/users", "permission": "user.manage", "label_en": "User Management", "label_ar": "إدارة المستخدمين"},
    {"path": "/settings/authorization", "permission": "authorization.manage", "label_en": "Authorization", "label_ar": "التفويض"},
    {"path": "/settings/policies", "permission": "policy.manage", "label_en": "Policies", "label_ar": "السياسات"},
    {"path": "/settings/delegations", "permission": "delegation.manage", "label_en": "Delegations", "label_ar": "التفويضات"},
    {"path": "/settings/audit", "permission": "audit.view", "label_en": "Audit Log", "label_ar": "سجل التدقيق"},
    {"path": "/ai", "permission": "ai.view", "label_en": "AI Services", "label_ar": "خدمات الذكاء الاصطناعي"},
    {"path": "/devices", "permission": "device.view", "label_en": "Devices", "label_ar": "الأجهزة"},
    {"path": "/edge", "permission": "edge.view", "label_en": "Edge Sites", "label_ar": "المواقع البعيدة"},
    {"path": "/compliance", "permission": "compliance.view", "label_en": "Compliance", "label_ar": "الامتثال"},
    {"path": "/help", "permission": None, "label_en": "Help & Support", "label_ar": "المساعدة والدعم"},
]


@router.get("/routes")
def list_routes(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    check_svc = AuthorizationCheckService(db)
    granted = set(check_svc.get_granted_permissions(current_user))
    accessible = []
    for route in ROUTES_REGISTRY:
        perm = route.get("permission")
        if perm is None or perm in granted:
            accessible.append(route)
    return {"routes": accessible, "total": len(accessible), "available": len(ROUTES_REGISTRY)}
