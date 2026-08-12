from __future__ import annotations

from app.national.security.rbac import NationalPermission, NationalRole, RBACEngine


class PatientPolicy:
    def __init__(self) -> None:
        self.rbac = RBACEngine()

    def can_read(self, user_role: NationalRole) -> bool:
        return self.rbac.has_permission(user_role, NationalPermission.PATIENT_READ)

    def can_create(self, user_role: NationalRole) -> bool:
        return self.rbac.has_permission(user_role, NationalPermission.PATIENT_CREATE)

    def can_update(self, user_role: NationalRole) -> bool:
        return self.rbac.has_permission(user_role, NationalPermission.PATIENT_UPDATE)
