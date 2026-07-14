from __future__ import annotations

from app.national.security.abac import ABACEngine
from app.national.security.rbac import NationalPermission, NationalRole, RBACEngine


class CitizenPolicy:
    def __init__(self) -> None:
        self.abac = ABACEngine()
        self.rbac = RBACEngine()

    def can_read(self, user_role: NationalRole, resource_owner: str | None = None) -> bool:
        return self.rbac.has_permission(user_role, NationalPermission.CITIZEN_READ)

    def can_create(self, user_role: NationalRole) -> bool:
        return self.rbac.has_permission(user_role, NationalPermission.CITIZEN_CREATE)

    def can_update(self, user_role: NationalRole) -> bool:
        return self.rbac.has_permission(user_role, NationalPermission.CITIZEN_UPDATE)

    def can_merge(self, user_role: NationalRole) -> bool:
        return self.rbac.has_permission(user_role, NationalPermission.CITIZEN_MERGE)
