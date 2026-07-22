from __future__ import annotations

import logging
import uuid
from datetime import datetime, timedelta
from typing import Any

from sqlalchemy.orm import Session

from app._compat import UTC
from app.models.authorization import (
    AuthorizationAudit,
    BreakGlassSession,
    Delegation,
    FieldSecurity,
    Permission,
    Policy,
    Role,
    RoleAssignment,
    RoleGroup,
    RoleGroupMember,
    RolePermission,
)
from app.models.organization import Facility, Organization
from app.models.tenant import Tenant
from app.models.user import User
from shared.rbac import (
    get_permissions_for_role as shared_get_permissions,
)
from shared.rbac import (
    has_permission_str,
)

logger = logging.getLogger("gula.services.authorization")


class PermissionService:
    def __init__(self, db: Session):
        self.db = db

    def get_all(self, domain: str | None = None, skip: int = 0, limit: int = 100) -> list[Permission]:
        q = self.db.query(Permission)
        if domain:
            q = q.filter(Permission.domain == domain)
        return q.offset(skip).limit(limit).all()

    def get_by_id(self, permission_id: str) -> Permission | None:
        return self.db.query(Permission).filter(Permission.permission_id == permission_id).first()

    def get_domains(self) -> list[str]:
        rows = self.db.query(Permission.domain).distinct().order_by(Permission.domain).all()
        return [r[0] for r in rows]

    def count(self, domain: str | None = None) -> int:
        q = self.db.query(Permission)
        if domain:
            q = q.filter(Permission.domain == domain)
        return q.count()


class RoleService:
    def __init__(self, db: Session):
        self.db = db

    def get_all(self, level: str | None = None, skip: int = 0, limit: int = 100) -> list[Role]:
        q = self.db.query(Role)
        if level:
            q = q.filter(Role.level == level)
        return q.offset(skip).limit(limit).all()

    def get_by_id(self, role_id: str) -> Role | None:
        return self.db.query(Role).filter(Role.role_id == role_id).first()

    def get_permissions(self, role_id: str) -> list[Permission]:
        role = self.get_by_id(role_id)
        if not role:
            return []
        return (
            self.db.query(Permission)
            .join(RolePermission, RolePermission.permission_id == Permission.permission_id)
            .filter(RolePermission.role_id == role_id)
            .all()
        )

    def get_inherited_permissions(self, role_id: str) -> list[str]:
        role = self.db.query(Role).filter(Role.role_id == role_id).first()
        if not role:
            return []
        perms = set()
        if role.parent_role_id:
            parent_perms = self.get_inherited_permissions(role.parent_role_id)
            perms.update(parent_perms)
        for p in self.get_permissions(role_id):
            perms.add(p.permission_id)
        return sorted(perms)

    def get_levels(self) -> list[dict[str, Any]]:
        rows = self.db.query(Role.level).distinct().order_by(Role.level).all()
        levels = []
        for r in rows:
            level = r[0]
            count = self.db.query(Role).filter(Role.level == level).count()
            levels.append({"level": level, "count": count})
        return levels

    def get_hierarchy(self) -> list[dict[str, Any]]:
        top_level = self.db.query(Role).filter(Role.parent_role_id.is_(None)).all()
        result = []
        for role in top_level:
            result.append(self._build_tree(role))
        return result

    def _build_tree(self, role: Role) -> dict[str, Any]:
        children = self.db.query(Role).filter(Role.parent_role_id == role.role_id).all()
        return {
            "role_id": role.role_id,
            "name_en": role.name_en,
            "name_ar": role.name_ar,
            "level": role.level,
            "children": [self._build_tree(c) for c in children],
        }


class RoleGroupService:
    def __init__(self, db: Session):
        self.db = db

    def get_all(self) -> list[RoleGroup]:
        return self.db.query(RoleGroup).all()

    def get_roles(self, group_id: str) -> list[Role]:
        members = self.db.query(RoleGroupMember).filter(RoleGroupMember.group_id == group_id).all()
        role_ids = [m.role_id for m in members]
        return self.db.query(Role).filter(Role.role_id.in_(role_ids)).all() if role_ids else []


class RoleAssignmentService:
    def __init__(self, db: Session):
        self.db = db

    def get_for_user(self, user_id: int) -> list[RoleAssignment]:
        return self.db.query(RoleAssignment).filter(
            RoleAssignment.user_id == user_id,
            RoleAssignment.status == "active",
        ).all()

    def get_assigned_roles(self, user_id: int) -> list[Role]:
        assignments = self.get_for_user(user_id)
        role_ids = [a.role_id for a in assignments]
        return self.db.query(Role).filter(Role.role_id.in_(role_ids)).all() if role_ids else []

    def get_effective_permissions(self, user_id: int) -> dict[str, Any]:
        roles = self.get_assigned_roles(user_id)
        permissions = set()
        mfa_required = False
        for role in roles:
            role_perms = self.db.query(RolePermission).filter(RolePermission.role_id == role.role_id).all()
            for rp in role_perms:
                permissions.add(rp.permission_id)
            if role.requires_mfa:
                mfa_required = True
            if role.parent_role_id:
                parent_perms = self.db.query(RolePermission).filter(
                    RolePermission.role_id == role.parent_role_id
                ).all()
                for rp in parent_perms:
                    permissions.add(rp.permission_id)
        return {
            "permissions": sorted(permissions),
            "mfa_required": mfa_required,
        }

    def assign_role(
        self,
        user_id: int,
        role_id: str,
        assigned_by: int | None = None,
        organization_id: int | None = None,
        facility_id: int | None = None,
        expires_at: datetime | None = None,
        is_primary: bool = True,
    ) -> RoleAssignment:
        existing = self.db.query(RoleAssignment).filter(
            RoleAssignment.user_id == user_id,
            RoleAssignment.role_id == role_id,
            RoleAssignment.status == "active",
        ).first()
        if existing:
            return existing
        assignment = RoleAssignment(
            user_id=user_id,
            role_id=role_id,
            assigned_by=assigned_by,
            organization_id=organization_id,
            facility_id=facility_id,
            expires_at=expires_at,
            is_primary=is_primary,
            status="active",
        )
        self.db.add(assignment)
        self.db.commit()
        self.db.refresh(assignment)
        return assignment

    def revoke_role(self, user_id: int, role_id: str) -> bool:
        assignment = self.db.query(RoleAssignment).filter(
            RoleAssignment.user_id == user_id,
            RoleAssignment.role_id == role_id,
            RoleAssignment.status == "active",
        ).first()
        if not assignment:
            return False
        assignment.status = "revoked"
        self.db.commit()
        return True

    def get_users_with_role(self, role_id: str) -> list[User]:
        assignments = self.db.query(RoleAssignment).filter(
            RoleAssignment.role_id == role_id,
            RoleAssignment.status == "active",
        ).all()
        user_ids = [a.user_id for a in assignments]
        return self.db.query(User).filter(User.id.in_(user_ids)).all() if user_ids else []


class PolicyService:
    def __init__(self, db: Session):
        self.db = db

    def get_active_policies(self) -> list[Policy]:
        now = datetime.now(UTC)
        return self.db.query(Policy).filter(
            Policy.status == "published",
            (Policy.validity_start.is_(None) | (Policy.validity_start <= now)),
            (Policy.validity_end.is_(None) | (Policy.validity_end >= now)),
        ).order_by(Policy.priority).all()

    def evaluate_policies(
        self,
        subject: dict[str, Any],
        resource_type: str,
        action: str,
        resource_attrs: dict[str, Any] | None = None,
        environment: dict[str, Any] | None = None,
    ) -> tuple[str, list[dict[str, Any]]]:
        policies = self.get_active_policies()
        applied = []
        for policy in policies:
            if self._policy_matches(policy, subject, resource_type, action, resource_attrs, environment):
                applied.append({
                    "policy_id": policy.policy_id,
                    "policy_name": policy.name_en,
                    "effect": policy.effect,
                })
                if policy.effect == "deny":
                    return "deny", applied
        if applied:
            return "allow", applied
        return "deny", []

    def _policy_matches(
        self,
        policy: Policy,
        subject: dict[str, Any],
        resource_type: str,
        action: str,
        resource_attrs: dict[str, Any] | None,
        environment: dict[str, Any] | None,
    ) -> bool:
        target = policy.target or {}
        conditions = policy.conditions or {}
        if target.get("resource") and resource_type not in target["resource"]:
            resource_patterns = target["resource"]
            if not any(
                resource_type.startswith(p.rstrip("*")) for p in resource_patterns
            ):
                return False
        if target.get("action") and action not in target["action"]:
            return False
        if target.get("roles") and subject.get("role") not in target["roles"]:
            return False
        if target.get("user_types") and subject.get("user_type") not in target["user_types"]:
            return False
        if conditions.get("governorate"):
            if subject.get("governorate_id") not in conditions["governorate"]:
                return False
        if conditions.get("time_of_day"):
            current_hour = datetime.now(UTC).hour
            allowed = conditions["time_of_day"]
            if not (allowed.get("start", 0) <= current_hour <= allowed.get("end", 23)):
                return False
        return True


class AuthorizationCheckService:
    def __init__(self, db: Session):
        self.db = db
        self.policy_service = PolicyService(db)

    def check_permission(
        self,
        user: User,
        permission_id: str,
        resource_attrs: dict[str, Any] | None = None,
        environment: dict[str, Any] | None = None,
        justification: str | None = None,
    ) -> dict[str, Any]:
        decision_id = str(uuid.uuid4())
        now = datetime.now(UTC)

        perm = self.db.query(Permission).filter(Permission.permission_id == permission_id).first()
        if not perm:
            self._log_decision(decision_id, user, permission_id, "deny", resource_type="unknown", policies_applied=[], context={"reason": "permission_not_found"})
            return self._build_response(decision_id, "deny", "Permission not found", perm)

        roles = self.db.query(RoleAssignment).filter(
            RoleAssignment.user_id == user.id,
            RoleAssignment.status == "active",
        ).all()
        if not roles:
            self._log_decision(decision_id, user, permission_id, "deny", perm.domain, [], resource_attrs, risk_score=perm.is_sensitive)
            return self._build_response(decision_id, "deny", "No roles assigned", perm)

        role_ids = [r.role_id for r in roles]
        assigned_perms = (
            self.db.query(RolePermission)
            .filter(RolePermission.role_id.in_(role_ids), RolePermission.permission_id == permission_id)
            .first()
        )
        if not assigned_perms:
            has_legacy = has_permission_str(user.role if hasattr(user, "role") else "", permission_id)
            if not has_legacy:
                self._log_decision(decision_id, user, permission_id, "deny", perm.domain, [], resource_attrs, risk_score=perm.is_sensitive)
                return self._build_response(decision_id, "deny", "Permission not assigned", perm)

        break_glass = self.db.query(BreakGlassSession).filter(
            BreakGlassSession.user_id == user.id,
            BreakGlassSession.status == "active",
            BreakGlassSession.expires_at > now,
        ).first()
        is_emergency = bool(break_glass)

        if perm.requires_mfa and not getattr(user, "mfa_enabled", False):
            self._log_decision(decision_id, user, permission_id, "deny", perm.domain, [], resource_attrs, risk_score=perm.is_sensitive, is_emergency=is_emergency)
            return self._build_response(decision_id, "deny", "MFA required for this permission", perm)

        if perm.requires_justification and not justification:
            self._log_decision(decision_id, user, permission_id, "deny", perm.domain, [], resource_attrs, risk_score=perm.is_sensitive, is_emergency=is_emergency)
            return self._build_response(decision_id, "deny", "Justification required", perm)

        subject = self._build_subject(user)
        abac_decision, applied_policies = self.policy_service.evaluate_policies(
            subject, perm.domain, perm.action, resource_attrs, environment
        )
        if abac_decision == "deny" and applied_policies:
            self._log_decision(decision_id, user, permission_id, "deny", perm.domain, applied_policies, resource_attrs, risk_score=perm.is_sensitive, is_emergency=is_emergency)
            return self._build_response(decision_id, "deny", "Denied by policy", perm, applied_policies, is_emergency)

        self._log_decision(decision_id, user, permission_id, "allow", perm.domain, applied_policies, resource_attrs, risk_score=perm.is_sensitive, is_emergency=is_emergency)
        return self._build_response(decision_id, "allow", "Access granted", perm, applied_policies, is_emergency)

    def check_many(
        self,
        user: User,
        permission_ids: list[str],
        resource_attrs: dict[str, Any] | None = None,
        environment: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        results = {}
        for pid in permission_ids:
            result = self.check_permission(user, pid, resource_attrs, environment)
            results[pid] = result
        return {
            "results": results,
            "granted": all(r["decision"] == "allow" for r in results.values()),
        }

    def get_granted_permissions(
        self,
        user: User,
        domain: str | None = None,
    ) -> list[str]:
        roles = self.db.query(RoleAssignment).filter(
            RoleAssignment.user_id == user.id,
            RoleAssignment.status == "active",
        ).all()
        role_ids = [r.role_id for r in roles]
        if not role_ids:
            return []
        q = self.db.query(RolePermission).filter(RolePermission.role_id.in_(role_ids))
        assigned = {rp.permission_id for rp in q.all()}
        legacy = set()
        if user.role:
            all_legacy = shared_get_permissions(user.role)
            legacy.update(all_legacy)
        combined = assigned | legacy
        if domain:
            perm_rows = self.db.query(Permission).filter(Permission.permission_id.in_(combined), Permission.domain == domain).all()
            return sorted(p.permission_id for p in perm_rows)
        return sorted(combined)

    def _build_subject(self, user: User) -> dict[str, Any]:
        return {
            "id": user.id,
            "role": getattr(user, "role", ""),
            "user_type": getattr(user, "user_type", None),
            "lab_id": getattr(user, "lab_id", None),
            "organization_id": getattr(user, "organization_id", None),
            "governorate_id": getattr(user, "governorate_id", None),
        }

    def _build_response(
        self,
        decision_id: str,
        decision: str,
        reason: str,
        perm: Permission | None = None,
        applied_policies: list[dict[str, Any]] | None = None,
        is_emergency: bool = False,
    ) -> dict[str, Any]:
        return {
            "decision_id": decision_id,
            "decision": decision,
            "reason": reason,
            "permission_id": perm.permission_id if perm else None,
            "permission_name": perm.name_en if perm else None,
            "domain": perm.domain if perm else None,
            "is_sensitive": perm.is_sensitive if perm else None,
            "is_emergency": is_emergency,
            "requires_mfa": perm.requires_mfa if perm else False,
            "requires_justification": perm.requires_justification if perm else False,
            "policies_applied": applied_policies or [],
        }

    def _log_decision(
        self,
        decision_id: str,
        user: User,
        permission_id: str,
        decision: str,
        resource_type: str,
        policies_applied: list | None = None,
        context: dict[str, Any] | None = None,
        risk_score: bool | float | None = None,
        is_emergency: bool = False,
    ) -> AuthorizationAudit:
        audit = AuthorizationAudit(
            decision_id=decision_id,
            user_id=user.id,
            user_role=getattr(user, "role", None),
            action=permission_id,
            resource_type=resource_type,
            decision=decision,
            policies_applied=policies_applied,
            policy_engine="rbac+abac",
            context=context,
            risk_score=float(risk_score) if isinstance(risk_score, bool) else risk_score,
            is_emergency=is_emergency,
        )
        self.db.add(audit)
        self.db.commit()
        return audit


class MenuService:
    def __init__(self, db: Session):
        self.db = db

    def get_menu_for_user(
        self,
        user: User,
        all_permissions: list[str] | None = None,
    ) -> list[dict[str, Any]]:
        if all_permissions is None:
            authz = AuthorizationCheckService(self.db)
            all_permissions = authz.get_granted_permissions(user)
        perm_set = set(all_permissions)

        structure = [
            {
                "id": "dashboard",
                "key": "dashboard",
                "label_en": "Dashboard",
                "label_ar": "لوحة التحكم",
                "icon": "LayoutDashboard",
                "path": "/dashboard",
                "permission": "dashboard.view",
                "children": [],
            },
            {
                "id": "patients",
                "key": "patients",
                "label_en": "Patients",
                "label_ar": "المرضى",
                "icon": "Users",
                "path": "/patients",
                "permission": "patient.view",
                "children": [
                    {
                        "id": "patients-list",
                        "key": "patients.list",
                        "label_en": "Patient List",
                        "label_ar": "قائمة المرضى",
                        "icon": "List",
                        "path": "/patients/list",
                        "permission": "patient.view",
                    },
                    {
                        "id": "patients-register",
                        "key": "patients.register",
                        "label_en": "Register Patient",
                        "label_ar": "تسجيل مريض",
                        "icon": "UserPlus",
                        "path": "/patients/register",
                        "permission": "patient.create",
                    },
                ],
            },
            {
                "id": "orders",
                "key": "orders",
                "label_en": "Orders",
                "label_ar": "الطلبات",
                "icon": "ClipboardList",
                "path": "/orders",
                "permission": "order.view",
                "children": [
                    {
                        "id": "orders-list",
                        "key": "orders.list",
                        "label_en": "Order List",
                        "label_ar": "قائمة الطلبات",
                        "icon": "List",
                        "path": "/orders/list",
                        "permission": "order.view",
                        "children": [],
                    },
                    {
                        "id": "orders-create",
                        "key": "orders.create",
                        "label_en": "New Order",
                        "label_ar": "طلب جديد",
                        "icon": "PlusCircle",
                        "path": "/orders/create",
                        "permission": "order.create",
                        "children": [],
                    },
                ],
            },
            {
                "id": "results",
                "key": "results",
                "label_en": "Results",
                "label_ar": "النتائج",
                "icon": "FlaskConical",
                "path": "/results",
                "permission": "result.view",
                "children": [
                    {
                        "id": "results-entry",
                        "key": "results.entry",
                        "label_en": "Result Entry",
                        "label_ar": "إدخال النتائج",
                        "icon": "Edit",
                        "path": "/results/entry",
                        "permission": "result.create",
                        "children": [],
                    },
                    {
                        "id": "results-review",
                        "key": "results.review",
                        "label_en": "Review Results",
                        "label_ar": "مراجعة النتائج",
                        "icon": "CheckCircle",
                        "path": "/results/review",
                        "permission": "result.review",
                        "children": [],
                    },
                    {
                        "id": "results-history",
                        "key": "results.history",
                        "label_en": "Result History",
                        "label_ar": "سجل النتائج",
                        "icon": "History",
                        "path": "/results/history",
                        "permission": "result.view",
                        "children": [],
                    },
                ],
            },
            {
                "id": "samples",
                "key": "samples",
                "label_en": "Samples",
                "label_ar": "العينات",
                "icon": "TestTube",
                "path": "/samples",
                "permission": "sample.view",
                "children": [],
            },
            {
                "id": "analytics",
                "key": "analytics",
                "label_en": "Analytics",
                "label_ar": "التحليلات",
                "icon": "BarChart3",
                "path": "/analytics",
                "permission": "stats.view",
                "children": [
                    {
                        "id": "analytics-dashboard",
                        "key": "analytics.dashboard",
                        "label_en": "Analytics Dashboard",
                        "label_ar": "لوحة التحليلات",
                        "icon": "PieChart",
                        "path": "/analytics/dashboard",
                        "permission": "stats.view",
                        "children": [],
                    },
                    {
                        "id": "analytics-epidemiology",
                        "key": "analytics.epidemiology",
                        "label_en": "Epidemiology",
                        "label_ar": "علم الأوبئة",
                        "icon": "Activity",
                        "path": "/analytics/epidemiology",
                        "permission": "stats.epidemiology",
                        "children": [],
                    },
                    {
                        "id": "analytics-reports",
                        "key": "analytics.reports",
                        "label_en": "Reports",
                        "label_ar": "التقارير",
                        "icon": "FileText",
                        "path": "/analytics/reports",
                        "permission": "stats.reports",
                        "children": [],
                    },
                ],
            },
            {
                "id": "quality",
                "key": "quality",
                "label_en": "Quality Control",
                "label_ar": "مراقبة الجودة",
                "icon": "ShieldCheck",
                "path": "/quality",
                "permission": "quality.view",
                "children": [],
            },
            {
                "id": "inventory",
                "key": "inventory",
                "label_en": "Inventory",
                "label_ar": "المخزون",
                "icon": "Package",
                "path": "/inventory",
                "permission": "inventory.view",
                "children": [],
            },
            {
                "id": "staff",
                "key": "staff",
                "label_en": "Staff",
                "label_ar": "الموظفون",
                "icon": "UsersRound",
                "path": "/staff",
                "permission": "user.view",
                "children": [
                    {
                        "id": "staff-list",
                        "key": "staff.list",
                        "label_en": "Staff List",
                        "label_ar": "قائمة الموظفين",
                        "icon": "List",
                        "path": "/staff/list",
                        "permission": "user.view",
                        "children": [],
                    },
                    {
                        "id": "staff-roles",
                        "key": "staff.roles",
                        "label_en": "Role Management",
                        "label_ar": "إدارة الأدوار",
                        "icon": "Shield",
                        "path": "/staff/roles",
                        "permission": "role.manage",
                        "children": [],
                    },
                ],
            },
            {
                "id": "settings",
                "key": "settings",
                "label_en": "Settings",
                "label_ar": "الإعدادات",
                "icon": "Settings",
                "path": "/settings",
                "permission": "settings.view",
                "children": [
                    {
                        "id": "settings-lab",
                        "key": "settings.lab",
                        "label_en": "Lab Settings",
                        "label_ar": "إعدادات المختبر",
                        "icon": "FlaskRound",
                        "path": "/settings/lab",
                        "permission": "lab.manage",
                        "children": [],
                    },
                    {
                        "id": "settings-users",
                        "key": "settings.users",
                        "label_en": "User Management",
                        "label_ar": "إدارة المستخدمين",
                        "icon": "UserCog",
                        "path": "/settings/users",
                        "permission": "user.manage",
                        "children": [],
                    },
                    {
                        "id": "settings-authorization",
                        "key": "settings.authorization",
                        "label_en": "Authorization",
                        "label_ar": "التفويض",
                        "icon": "KeyRound",
                        "path": "/settings/authorization",
                        "permission": "authorization.manage",
                        "children": [],
                    },
                    {
                        "id": "settings-policies",
                        "key": "settings.policies",
                        "label_en": "Policies",
                        "label_ar": "السياسات",
                        "icon": "FileCheck",
                        "path": "/settings/policies",
                        "permission": "policy.manage",
                        "children": [],
                    },
                    {
                        "id": "settings-delegations",
                        "key": "settings.delegations",
                        "label_en": "Delegations",
                        "label_ar": "التفويضات",
                        "icon": "UserCheck",
                        "path": "/settings/delegations",
                        "permission": "delegation.manage",
                        "children": [],
                    },
                    {
                        "id": "settings-audit",
                        "key": "settings.audit",
                        "label_en": "Audit Log",
                        "label_ar": "سجل التدقيق",
                        "icon": "ScrollText",
                        "path": "/settings/audit",
                        "permission": "audit.view",
                        "children": [],
                    },
                ],
            },
            {
                "id": "ai",
                "key": "ai",
                "label_en": "AI Services",
                "label_ar": "خدمات الذكاء الاصطناعي",
                "icon": "Brain",
                "path": "/ai",
                "permission": "ai.view",
                "children": [],
            },
            {
                "id": "devices",
                "key": "devices",
                "label_en": "Devices",
                "label_ar": "الأجهزة",
                "icon": "Monitor",
                "path": "/devices",
                "permission": "device.view",
                "children": [],
            },
            {
                "id": "edge",
                "key": "edge",
                "label_en": "Edge Sites",
                "label_ar": "المواقع البعيدة",
                "icon": "Wifi",
                "path": "/edge",
                "permission": "edge.view",
                "children": [],
            },
            {
                "id": "compliance",
                "key": "compliance",
                "label_en": "Compliance",
                "label_ar": "الامتثال",
                "icon": "Scale",
                "path": "/compliance",
                "permission": "compliance.view",
                "children": [],
            },
            {
                "id": "help",
                "key": "help",
                "label_en": "Help & Support",
                "label_ar": "المساعدة والدعم",
                "icon": "LifeBuoy",
                "path": "/help",
                "permission": None,
                "children": [],
            },
        ]

        return self._filter_menu(structure, perm_set)

    def _filter_menu(
        self, items: list[dict[str, Any]], permissions: set[str]
    ) -> list[dict[str, Any]]:
        result = []
        for item in items:
            perm = item.get("permission")
            has_perm = perm is None or perm in permissions
            children = item.get("children", [])
            filtered_children = self._filter_menu(children, permissions) if children else []
            if has_perm or filtered_children:
                item_copy = dict(item)
                item_copy["children"] = filtered_children
                result.append(item_copy)
        return result


class FieldSecurityService:
    def __init__(self, db: Session):
        self.db = db

    def get_field_mask(
        self,
        resource_type: str,
        field_name: str,
        user_role: str | None = None,
        org_type: str | None = None,
    ) -> dict[str, Any]:
        field_def = self.db.query(FieldSecurity).filter(
            FieldSecurity.resource_type == resource_type,
            FieldSecurity.field_name == field_name,
        ).first()
        if not field_def:
            return {"level": "public", "masked": False, "encrypted": False}
        effective_level = field_def.default_level
        if user_role and field_def.levels_by_role:
            role_levels = field_def.levels_by_role
            if user_role in role_levels:
                effective_level = role_levels[user_role]
        if org_type and field_def.levels_by_org_type:
            org_levels = field_def.levels_by_org_type
            if org_type in org_levels:
                effective_level = org_levels[org_type]
        is_restricted = effective_level in ("restricted", "confidential", "secret")
        return {
            "level": effective_level,
            "masked": is_restricted and bool(field_def.masking_pattern),
            "masking_pattern": field_def.masking_pattern if is_restricted else None,
            "encrypted": field_def.encryption_required,
            "consent_required": field_def.consent_required,
            "audit_access": field_def.audit_access,
        }

    def mask_value(self, value: str, pattern: str | None = None) -> str:
        if not pattern:
            if len(value) <= 4:
                return "*" * len(value)
            return value[:2] + "*" * (len(value) - 4) + value[-2:]
        result = list(value)
        mask_char = "*"
        i = 0
        for ch in pattern:
            if ch == "*":
                if i < len(result):
                    result[i] = mask_char
                i += 1
            else:
                i += 1
        return "".join(result)


class DelegationService:
    def __init__(self, db: Session):
        self.db = db

    def create_delegation(
        self,
        delegator_id: int,
        delegate_id: int,
        role_id: str,
        reason: str,
        duration_hours: int,
        scope: dict[str, Any] | None = None,
    ) -> Delegation:
        now = datetime.now(UTC)
        delegation = Delegation(
            delegator_id=delegator_id,
            delegate_id=delegate_id,
            role_id=role_id,
            delegation_type="temporary",
            scope=scope,
            reason=reason,
            starts_at=now,
            expires_at=now + timedelta(hours=duration_hours),
            status="active",
        )
        self.db.add(delegation)
        self.db.commit()
        self.db.refresh(delegation)
        return delegation

    def revoke_delegation(self, delegation_id: int, revoked_by: int) -> bool:
        delegation = self.db.query(Delegation).filter(Delegation.id == delegation_id).first()
        if not delegation or delegation.status != "active":
            return False
        delegation.status = "revoked"
        delegation.revoked_at = datetime.now(UTC)
        delegation.revoked_by = revoked_by
        self.db.commit()
        return True

    def get_active_for_user(self, user_id: int) -> list[Delegation]:
        now = datetime.now(UTC)
        return self.db.query(Delegation).filter(
            (Delegation.delegator_id == user_id) | (Delegation.delegate_id == user_id),
            Delegation.status == "active",
            Delegation.expires_at > now,
        ).all()


class BreakGlassService:
    def __init__(self, db: Session):
        self.db = db

    def activate(
        self,
        user_id: int,
        emergency_category: str,
        justification: str,
        patient_id: int | None = None,
        duration_minutes: int = 60,
    ) -> BreakGlassSession:
        now = datetime.now(UTC)
        session = BreakGlassSession(
            user_id=user_id,
            emergency_category=emergency_category,
            justification=justification,
            patient_id=patient_id,
            started_at=now,
            expires_at=now + timedelta(minutes=duration_minutes),
            status="active",
        )
        self.db.add(session)
        self.db.commit()
        self.db.refresh(session)
        return session

    def deactivate(self, session_id: int) -> bool:
        session = self.db.query(BreakGlassSession).filter(BreakGlassSession.id == session_id).first()
        if not session or session.status != "active":
            return False
        session.status = "deactivated"
        session.deactivated_at = datetime.now(UTC)
        self.db.commit()
        return True

    def get_active(self, user_id: int) -> BreakGlassSession | None:
        now = datetime.now(UTC)
        return self.db.query(BreakGlassSession).filter(
            BreakGlassSession.user_id == user_id,
            BreakGlassSession.status == "active",
            BreakGlassSession.expires_at > now,
        ).first()

    def get_all_active(self) -> list[BreakGlassSession]:
        now = datetime.now(UTC)
        return self.db.query(BreakGlassSession).filter(
            BreakGlassSession.status == "active",
            BreakGlassSession.expires_at > now,
        ).all()


class AuthorizationAuditService:
    def __init__(self, db: Session):
        self.db = db

    def query(
        self,
        user_id: int | None = None,
        decision: str | None = None,
        resource_type: str | None = None,
        is_emergency: bool | None = None,
        skip: int = 0,
        limit: int = 100,
    ) -> tuple[list[AuthorizationAudit], int]:
        q = self.db.query(AuthorizationAudit)
        if user_id is not None:
            q = q.filter(AuthorizationAudit.user_id == user_id)
        if decision is not None:
            q = q.filter(AuthorizationAudit.decision == decision)
        if resource_type is not None:
            q = q.filter(AuthorizationAudit.resource_type == resource_type)
        if is_emergency is not None:
            q = q.filter(AuthorizationAudit.is_emergency == is_emergency)
        total = q.count()
        q = q.order_by(AuthorizationAudit.created_at.desc()).offset(skip).limit(limit)
        return q.all(), total


class IdentityService:
    def __init__(self, db: Session):
        self.db = db

    def get_identity_context(self, user: User) -> dict[str, Any]:
        org = None
        if user.organization_id:
            org = self.db.query(Organization).filter(Organization.id == user.organization_id).first()
        tenant = None
        if user.tenant_id:
            tenant = self.db.query(Tenant).filter(Tenant.id == user.tenant_id).first()
        facility = None
        if user.facility_id:
            facility = self.db.query(Facility).filter(Facility.id == user.facility_id).first()
        role_assignments = self.db.query(RoleAssignment).filter(
            RoleAssignment.user_id == user.id,
            RoleAssignment.status == "active",
        ).all()
        roles = []
        for ra in role_assignments:
            role = self.db.query(Role).filter(Role.role_id == ra.role_id).first()
            if role:
                roles.append({
                    "role_id": role.role_id,
                    "name_en": role.name_en,
                    "name_ar": role.name_ar,
                    "level": role.level,
                    "organization_id": ra.organization_id,
                    "facility_id": ra.facility_id,
                    "is_primary": ra.is_primary,
                    "scope": self._compute_scope(ra),
                })
        return {
            "user": {
                "id": user.id,
                "email": user.email,
                "full_name": user.full_name,
                "user_type": user.user_type,
                "role": user.role,
                "mfa_enabled": user.mfa_enabled,
                "is_active": user.is_active,
                "is_verified": user.is_verified,
            },
            "organization": {
                "id": org.id,
                "name_en": org.name_en,
                "name_ar": org.name_ar,
                "org_type": org.org_type,
                "governorate_id": org.governorate_id,
            } if org else None,
            "tenant": {
                "id": tenant.id,
                "name_en": tenant.name_en,
                "name_ar": tenant.name_ar,
                "tenant_type": tenant.tenant_type,
            } if tenant else None,
            "facility": {
                "id": facility.id,
                "name_en": facility.name_en,
                "name_ar": facility.name_ar,
                "facility_type": facility.facility_type,
            } if facility else None,
            "roles": roles,
            "governorate_id": user.governorate_id,
        }

    def _compute_scope(self, assignment: RoleAssignment) -> dict[str, Any]:
        scope: dict[str, Any] = {"type": "self"}
        if assignment.organization_id:
            scope["type"] = "organization"
            scope["organization_id"] = assignment.organization_id
        if assignment.facility_id:
            scope["type"] = "facility"
            scope["facility_id"] = assignment.facility_id
        return scope
