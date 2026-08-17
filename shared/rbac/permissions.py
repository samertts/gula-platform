from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class Role(Enum):
    SUPER_ADMIN = "super_admin"
    LAB_ADMIN = "lab_admin"
    LAB_TECH = "lab_tech"
    DOCTOR = "doctor"
    PATHOLOGIST = "pathologist"
    NURSE = "nurse"
    RECEPTIONIST = "receptionist"
    CITIZEN = "citizen"
    MINISTRY = "ministry"
    RESEARCHER = "researcher"


class Permission(Enum):
    READ_PATIENTS = "read:patients"
    WRITE_PATIENTS = "write:patients"
    READ_ORDERS = "read:orders"
    WRITE_ORDERS = "write:orders"
    READ_RESULTS = "read:results"
    WRITE_RESULTS = "write:results"
    READ_SAMPLES = "read:samples"
    WRITE_SAMPLES = "write:samples"
    MANAGE_USERS = "manage:users"
    MANAGE_LABS = "manage:labs"
    VIEW_AUDIT = "view:audit"
    MANAGE_SYSTEM = "manage:system"
    VIEW_ANALYTICS = "view:analytics"


_RBAC_MATRIX: dict[Role, set[Permission]] = {
    Role.SUPER_ADMIN: set(Permission),
    Role.LAB_ADMIN: {
        Permission.READ_PATIENTS,
        Permission.WRITE_PATIENTS,
        Permission.READ_ORDERS,
        Permission.WRITE_ORDERS,
        Permission.READ_RESULTS,
        Permission.WRITE_RESULTS,
        Permission.READ_SAMPLES,
        Permission.WRITE_SAMPLES,
        Permission.MANAGE_USERS,
        Permission.VIEW_AUDIT,
        Permission.VIEW_ANALYTICS,
    },
    Role.LAB_TECH: {
        Permission.READ_PATIENTS,
        Permission.READ_ORDERS,
        Permission.WRITE_ORDERS,
        Permission.READ_RESULTS,
        Permission.WRITE_RESULTS,
        Permission.READ_SAMPLES,
        Permission.WRITE_SAMPLES,
    },
    Role.DOCTOR: {
        Permission.READ_PATIENTS,
        Permission.READ_ORDERS,
        Permission.WRITE_ORDERS,
        Permission.READ_RESULTS,
        Permission.READ_SAMPLES,
    },
    Role.PATHOLOGIST: {
        Permission.READ_PATIENTS,
        Permission.READ_ORDERS,
        Permission.READ_RESULTS,
        Permission.WRITE_RESULTS,
        Permission.READ_SAMPLES,
        Permission.VIEW_ANALYTICS,
    },
    Role.NURSE: {
        Permission.READ_PATIENTS,
        Permission.READ_ORDERS,
        Permission.READ_SAMPLES,
        Permission.WRITE_SAMPLES,
    },
    Role.RECEPTIONIST: {
        Permission.READ_PATIENTS,
        Permission.WRITE_PATIENTS,
        Permission.READ_ORDERS,
        Permission.WRITE_ORDERS,
        Permission.READ_SAMPLES,
    },
    Role.CITIZEN: {
        Permission.READ_RESULTS,
    },
    Role.MINISTRY: {
        Permission.READ_PATIENTS,
        Permission.READ_ORDERS,
        Permission.READ_RESULTS,
        Permission.VIEW_ANALYTICS,
        Permission.VIEW_AUDIT,
    },
    Role.RESEARCHER: {
        Permission.READ_RESULTS,
        Permission.VIEW_ANALYTICS,
    },
}


# ── Extended Role Hierarchy (backend-compatible string API) ───────────────────
# These mirror the richer role/permission model used by the GULA monolith.

EXTENDED_ROLE_LEVELS: dict[str, int] = {
    "master_admin":   100,
    "ministry_admin":  90,
    "province_admin":  80,
    "admin":              50,
    "lab_admin":          50,
    "finance_controller": 70,
    "refund_reviewer":    60,
    "reconciler":         55,
    "finance_auditor":    45,
    "finance_operator":   35,
    "cashier":            25,
    "doctor":             40,
    "staff":              20,
    "lab_staff":          20,
    "technician":         20,
    "citizen":            10,
}

EXTENDED_ALL_PERMISSIONS: list[str] = [
    "patients:read",
    "patients:write",
    "patients:delete",
    "orders:read",
    "orders:write",
    "results:read",
    "results:write",
    "staff:manage",
    "lab:read",
    "lab:manage",
    "dashboard:read",
    "audit:read",
    "platform:manage_labs",
    "platform:manage_users",
    "platform:view_stats",
    "system:admin",
    "payments:read",
    "payments:write",
    "payments:cashier",
    "payments:refund:request",
    "payments:refund:approve",
    "payments:refund:process",
    "payments:reconcile",
    "payments:fx:quote",
    "payments:fx:manage",
    "payments:orchestration:manage",
    "payments:orchestration:route",
    "payments:control:read",
    "payments:control:request",
    "payments:control:approve",
    "payments:control:apply",
    "payments:control:emergency",
    "subscriptions:manage",
    "subscriptions:read",
    "subscriptions:usage",
    "hospital:read",
    "hospital:manage",
    "hospital:flow:read",
    "hospital:flow:write",
    "hospital:triage",
    "hospital:admit",
    "hospital:transfer",
    "hospital:discharge",
    "hospital:appointment:read",
    "hospital:appointment:write",
    "consent:manage",
]

EXTENDED_ROLE_PERMISSIONS: dict[str, list[str]] = {
    "master_admin": EXTENDED_ALL_PERMISSIONS,
    "ministry_admin": [
        "patients:read", "orders:read", "results:read", "lab:read",
        "dashboard:read", "audit:read",
        "platform:manage_labs", "platform:manage_users", "platform:view_stats",
        "payments:read",
        "hospital:read", "hospital:manage", "hospital:flow:read", "hospital:flow:write",
        "hospital:triage", "hospital:admit", "hospital:transfer", "hospital:discharge",
        "hospital:appointment:read", "hospital:appointment:write", "consent:manage",
    ],
    "province_admin": [
        "patients:read", "orders:read", "results:read", "lab:read",
        "dashboard:read", "audit:read",
        "platform:manage_labs", "platform:manage_users", "platform:view_stats",
        "hospital:read", "hospital:flow:read", "hospital:appointment:read",
    ],
    "admin": [
        "patients:read", "patients:write", "patients:delete",
        "orders:read", "orders:write",
        "results:read", "results:write",
        "staff:manage", "lab:read", "lab:manage",
        "dashboard:read", "audit:read",
        "platform:manage_users",
        "hospital:read", "hospital:manage", "hospital:flow:read", "hospital:flow:write",
        "hospital:triage", "hospital:admit", "hospital:transfer", "hospital:discharge",
        "hospital:appointment:read", "hospital:appointment:write", "consent:manage",
        "payments:read", "payments:write", "payments:cashier", "payments:refund:request",
        "payments:refund:approve", "payments:refund:process", "payments:reconcile", "payments:fx:quote",
        "payments:orchestration:route", "payments:control:read", "payments:control:request", "subscriptions:read", "subscriptions:usage",
    ],
    "lab_admin": [
        "patients:read", "patients:write", "patients:delete",
        "orders:read", "orders:write",
        "results:read", "results:write",
        "staff:manage", "lab:read", "lab:manage",
        "dashboard:read", "audit:read",
        "platform:manage_users",
        "hospital:read", "hospital:manage", "hospital:flow:read", "hospital:flow:write",
        "hospital:triage", "hospital:admit", "hospital:transfer", "hospital:discharge",
        "hospital:appointment:read", "hospital:appointment:write", "consent:manage",
        "payments:read", "payments:write", "payments:cashier", "payments:refund:request",
        "payments:refund:approve", "payments:refund:process", "payments:reconcile", "payments:fx:quote",
        "payments:orchestration:route", "payments:control:read", "payments:control:request", "subscriptions:read", "subscriptions:usage",
    ],
    "finance_controller": [
        "dashboard:read", "audit:read", "payments:read", "payments:write",
        "payments:refund:approve", "payments:reconcile", "payments:orchestration:manage",
        "payments:control:read", "payments:control:approve", "payments:control:apply",
    ],
    "refund_reviewer": [
        "dashboard:read", "audit:read", "payments:read", "payments:refund:approve",
        "payments:control:read", "payments:control:approve",
    ],
    "reconciler": [
        "dashboard:read", "audit:read", "payments:read", "payments:reconcile",
        "payments:control:read", "payments:control:apply",
    ],
    "finance_auditor": [
        "dashboard:read", "audit:read", "payments:read", "payments:control:read",
    ],
    "finance_operator": [
        "dashboard:read", "payments:read", "payments:write",
        "payments:control:read", "payments:control:request",
    ],
    "cashier": [
        "dashboard:read", "payments:read", "payments:cashier",
        "payments:control:read", "payments:control:request",
    ],
    "doctor": [
        "patients:read", "orders:read", "results:read", "dashboard:read",
        "hospital:read", "hospital:flow:read", "hospital:flow:write",
        "hospital:triage", "hospital:admit", "hospital:transfer", "hospital:discharge",
        "hospital:appointment:read", "hospital:appointment:write",
    ],
    "staff": [
        "patients:read", "patients:write",
        "hospital:read", "hospital:flow:read", "hospital:appointment:read",
        "orders:read", "orders:write",
        "results:read", "results:write",
        "lab:read", "dashboard:read",
        "payments:read", "payments:write", "payments:cashier", "payments:refund:request", "payments:fx:quote",
        "payments:orchestration:route",
    ],
    "lab_staff": [
        "patients:read", "patients:write",
        "hospital:read", "hospital:flow:read", "hospital:appointment:read",
        "orders:read", "orders:write",
        "results:read", "results:write",
        "lab:read", "dashboard:read",
        "payments:read", "payments:write", "payments:cashier", "payments:refund:request", "payments:fx:quote",
        "payments:orchestration:route",
    ],
    "technician": [
        "orders:read", "orders:write",
        "hospital:read", "hospital:flow:read",
        "results:read", "results:write",
        "lab:read", "dashboard:read",
    ],
    "citizen": [],
}

EXTENDED_VALID_ROLES: set[str] = set(EXTENDED_ROLE_PERMISSIONS.keys())


def get_role_level(role: str) -> int:
    return EXTENDED_ROLE_LEVELS.get(role, 0)


def get_permissions_for_role(role: str) -> list[str]:
    return EXTENDED_ROLE_PERMISSIONS.get(role, [])


def has_permission_str(role: str, permission: str) -> bool:
    return permission in get_permissions_for_role(role)


def can_manage_role(actor_role: str, target_role: str) -> bool:
    if target_role == "master_admin":
        return actor_role == "master_admin"
    actor_level = get_role_level(actor_role)
    target_level = get_role_level(target_role)
    return actor_level > target_level and actor_level > 0


# ── Original Enum-based API ───────────────────────────────────────────────────

@dataclass
class RBACMatrix:
    matrix: dict[Role, set[Permission]] = field(default_factory=lambda: _RBAC_MATRIX)

    def has_permission(self, role: Role, permission: Permission) -> bool:
        return permission in self.matrix.get(role, set())

    def get_permissions(self, role: Role) -> set[Permission]:
        return self.matrix.get(role, set())


def has_permission(role: Role, permission: Permission) -> bool:
    return permission in _RBAC_MATRIX.get(role, set())


def require_permission(role: Role, permission: Permission) -> None:
    if not has_permission(role, permission):
        raise PermissionError(f"Role {role.value} does not have permission {permission.value}")
