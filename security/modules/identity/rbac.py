from __future__ import annotations

import logging
import threading
from typing import Any

from security.modules.identity.models import AccessDecision

logger = logging.getLogger("gula.security.modules.identity.rbac")

_ROLE_HIERARCHY: dict[str, str | None] = {
    "master_admin": None,
    "system_admin": "master_admin",
    "lab_admin": "system_admin",
    "manager": "lab_admin",
    "supervisor": "manager",
    "technician": "supervisor",
    "viewer": "technician",
    "auditor": "viewer",
    "api_service": "auditor",
}

_DEFAULT_ROLES = [
    "master_admin",
    "system_admin",
    "lab_admin",
    "manager",
    "supervisor",
    "technician",
    "viewer",
    "auditor",
    "api_service",
]

_PERMISSION_CATEGORIES = [
    "patients",
    "orders",
    "results",
    "samples",
    "labs",
    "users",
    "roles",
    "settings",
    "audit",
    "reports",
    "fhir",
    "admin",
    "system",
]

_DEFAULT_PERMISSIONS: dict[str, list[str]] = {
    "master_admin": ["*:*"],
    "system_admin": ["admin:*", "system:*", "audit:*", "users:*", "roles:*", "settings:*", "reports:*"],
    "lab_admin": ["patients:*", "orders:*", "results:*", "samples:*", "labs:read", "users:read", "reports:*", "settings:read"],
    "manager": ["patients:*", "orders:*", "results:*", "samples:*", "users:read", "reports:read", "settings:read"],
    "supervisor": ["patients:read", "patients:write", "orders:read", "orders:write", "results:read", "results:write", "samples:read"],
    "technician": ["patients:read", "orders:read", "results:read", "results:write", "samples:read", "samples:write"],
    "viewer": ["patients:read", "orders:read", "results:read", "samples:read", "reports:read"],
    "auditor": ["audit:read", "audit:export", "reports:read"],
    "api_service": ["patients:read", "orders:read", "results:read", "fhir:read"],
}


class RBACEngine:
    def __init__(self) -> None:
        self._role_hierarchy: dict[str, str | None] = dict(_ROLE_HIERARCHY)
        self._permissions: dict[str, set[str]] = {}
        self._user_roles: dict[str, str] = {}
        self._session_cache: dict[str, set[str]] = {}
        self._cache_lock = threading.Lock()
        self._lock = threading.Lock()
        self._init_default_permissions()

        try:
            from shared.rbac import has_permission_str as _shared_has
            self._shared_has = _shared_has
        except ImportError:
            self._shared_has = None

    def _init_default_permissions(self) -> None:
        for role, perms in _DEFAULT_PERMISSIONS.items():
            self._permissions[role] = set(perms)
        for role in _DEFAULT_ROLES:
            if role not in self._permissions:
                self._permissions[role] = set()

    def get_role_ancestors(self, role: str) -> list[str]:
        ancestors: list[str] = []
        current = role
        while current in self._role_hierarchy:
            parent = self._role_hierarchy[current]
            if parent is None:
                break
            ancestors.append(parent)
            current = parent
        return ancestors

    def get_role_descendants(self, role: str) -> list[str]:
        descendants: list[str] = []
        for r, parent in self._role_hierarchy.items():
            if parent == role:
                descendants.append(r)
                descendants.extend(self.get_role_descendants(r))
        return descendants

    def get_inherited_permissions(self, role: str) -> set[str]:
        perms: set[str] = set()
        current: str | None = role
        while current is not None:
            role_perms = self._permissions.get(current, set())
            perms.update(role_perms)
            current = self._role_hierarchy.get(current)
        return perms

    def has_permission(self, role: str, permission: str) -> bool:
        if self._shared_has is not None:
            try:
                return self._shared_has(role, permission)
            except Exception:
                pass

        inherited = self.get_inherited_permissions(role)
        if "*:*" in inherited:
            return True
        if permission in inherited:
            return True
        resource = permission.split(":")[0] if ":" in permission else permission
        wildcard = f"{resource}:*"
        if wildcard in inherited:
            return True
        return False

    def check_access(
        self,
        role: str,
        resource: str,
        action: str,
        context: dict[str, Any] | None = None,
    ) -> AccessDecision:
        _ = context
        permission = f"{resource}:{action}"
        permitted = self.has_permission(role, permission)

        if not permitted:
            return AccessDecision(
                permitted=False,
                reason=f"Role '{role}' lacks permission '{permission}'",
            )

        return AccessDecision(permitted=True, reason="Permission granted")

    def assign_role(self, user_id: str, role: str) -> None:
        if role not in self._permissions:
            raise ValueError(f"Unknown role: {role}")
        with self._lock:
            self._user_roles[user_id] = role
        self.invalidate_session(user_id)

    def get_user_role(self, user_id: str) -> str | None:
        return self._user_roles.get(user_id)

    def remove_user_role(self, user_id: str) -> None:
        with self._lock:
            self._user_roles.pop(user_id, None)
        self.invalidate_session(user_id)

    def register_permission(self, role: str, permission: str) -> None:
        with self._lock:
            if role not in self._permissions:
                self._permissions[role] = set()
            self._permissions[role].add(permission)

    def revoke_permission(self, role: str, permission: str) -> None:
        with self._lock:
            if role in self._permissions:
                self._permissions[role].discard(permission)

    def add_role(self, role: str, parent: str | None = None) -> None:
        with self._lock:
            if role in self._role_hierarchy:
                raise ValueError(f"Role already exists: {role}")
            if parent is not None and parent not in self._role_hierarchy:
                raise ValueError(f"Parent role not found: {parent}")
            self._role_hierarchy[role] = parent
            self._permissions[role] = set()

    def cache_session_permissions(self, session_id: str, role: str) -> None:
        perms = self.get_inherited_permissions(role)
        with self._cache_lock:
            self._session_cache[session_id] = perms

    def get_cached_permissions(self, session_id: str) -> set[str]:
        with self._cache_lock:
            return self._session_cache.get(session_id, set())

    def invalidate_session(self, session_id: str) -> None:
        with self._cache_lock:
            self._session_cache.pop(session_id, None)

    def get_all_permissions_for_role(self, role: str) -> list[str]:
        return sorted(self.get_inherited_permissions(role))

    def list_roles(self) -> list[str]:
        return list(self._role_hierarchy.keys())

    def add_role_hierarchy(self, role: str, parent: str | None) -> None:
        self._role_hierarchy[role] = parent

    def get_role_level(self, role: str) -> int:
        level = 0
        current: str | None = role
        while current is not None:
            level += 1
            current = self._role_hierarchy.get(current)
        return level

    def can_manage_role(self, actor_role: str, target_role: str) -> bool:
        try:
            from shared.rbac import can_manage_role as _shared_can_manage
            return _shared_can_manage(actor_role, target_role)
        except ImportError:
            pass
        actor_level = self.get_role_level(actor_role)
        target_level = self.get_role_level(target_role)
        return actor_level < target_level

    def bulk_check(self, role: str, permissions: list[str]) -> dict[str, bool]:
        return {p: self.has_permission(role, p) for p in permissions}

    def get_effective_permissions(self, user_id: str) -> set[str]:
        role = self.get_user_role(user_id)
        if role is None:
            return set()
        return self.get_inherited_permissions(role)
