from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


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
