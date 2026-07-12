from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class Role(Enum):
    GUEST = "guest"
    PATIENT = "patient"
    TECHNICIAN = "technician"
    DOCTOR = "doctor"
    SUPERVISOR = "supervisor"
    ADMIN = "admin"
    MASTER_ADMIN = "master_admin"
    MINISTRY = "ministry"


class Permission(Enum):
    READ_PATIENT = "read:patient"
    WRITE_PATIENT = "write:patient"
    READ_ORDER = "read:order"
    WRITE_ORDER = "write:order"
    READ_RESULT = "read:result"
    WRITE_RESULT = "write:result"
    VALIDATE_RESULT = "validate:result"
    READ_SAMPLE = "read:sample"
    WRITE_SAMPLE = "write:sample"
    MANAGE_LAB = "manage:lab"
    MANAGE_USERS = "manage:users"
    MANAGE_TIERS = "manage:tiers"
    VIEW_AUDIT = "view:audit"
    VIEW_METRICS = "view:metrics"
    MANAGE_SYSTEM = "manage:system"
    MANAGE_INTEGRATIONS = "manage:integrations"
    ACCESS_DOCS = "access:docs"


ROLE_PERMISSIONS: dict[Role, list[Permission]] = {
    Role.GUEST: [],
    Role.PATIENT: [Permission.READ_PATIENT],
    Role.TECHNICIAN: [
        Permission.READ_PATIENT, Permission.READ_ORDER, Permission.WRITE_ORDER,
        Permission.READ_RESULT, Permission.WRITE_RESULT, Permission.READ_SAMPLE, Permission.WRITE_SAMPLE,
    ],
    Role.DOCTOR: [
        Permission.READ_PATIENT, Permission.READ_ORDER, Permission.READ_RESULT,
        Permission.VALIDATE_RESULT, Permission.READ_SAMPLE,
    ],
    Role.SUPERVISOR: [
        Permission.READ_PATIENT, Permission.WRITE_PATIENT, Permission.READ_ORDER, Permission.WRITE_ORDER,
        Permission.READ_RESULT, Permission.WRITE_RESULT, Permission.VALIDATE_RESULT,
        Permission.READ_SAMPLE, Permission.WRITE_SAMPLE,
        Permission.MANAGE_LAB, Permission.VIEW_AUDIT, Permission.VIEW_METRICS,
    ],
    Role.ADMIN: [
        Permission.READ_PATIENT, Permission.WRITE_PATIENT, Permission.READ_ORDER, Permission.WRITE_ORDER,
        Permission.READ_RESULT, Permission.WRITE_RESULT, Permission.VALIDATE_RESULT,
        Permission.READ_SAMPLE, Permission.WRITE_SAMPLE,
        Permission.MANAGE_LAB, Permission.MANAGE_USERS, Permission.VIEW_AUDIT, Permission.VIEW_METRICS,
        Permission.ACCESS_DOCS,
    ],
    Role.MASTER_ADMIN: [p for p in Permission],
    Role.MINISTRY: [
        Permission.READ_PATIENT, Permission.READ_ORDER, Permission.READ_RESULT,
        Permission.VIEW_METRICS, Permission.VIEW_AUDIT,
    ],
}


@dataclass
class User:
    id: int = 0
    username: str = ""
    email: str = ""
    role: Role = Role.TECHNICIAN
    lab_id: int = 0
    is_active: bool = True

    def has_permission(self, permission: Permission) -> bool:
        return permission in ROLE_PERMISSIONS.get(self.role, [])

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id, "username": self.username, "email": self.email,
            "role": self.role.value, "lab_id": self.lab_id, "is_active": self.is_active,
        }


@dataclass
class AccessPolicy:
    user: User
    resource_type: str
    resource_id: int | None = None

    def can_read(self) -> bool:
        return self.user.has_permission(Permission.READ_PATIENT)

    def can_write(self) -> bool:
        return self.user.has_permission(Permission.WRITE_PATIENT)

    def can_manage(self) -> bool:
        return self.user.has_permission(Permission.MANAGE_LAB)


__all__ = ["User", "Role", "Permission", "AccessPolicy", "ROLE_PERMISSIONS"]
