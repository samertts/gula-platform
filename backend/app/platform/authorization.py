"""Standardized authorization module — wraps security/rbac.py and security/abac.py."""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

from . import PlatformRegistry

logger = logging.getLogger("gula.platform.authorization")


@dataclass
class AuthorizationResult:
    allowed: bool = False
    reason: str | None = None
    context: dict | None = None


class AuthorizationProvider(ABC):
    @abstractmethod
    def check_access(
        self, user: Any, resource: str, action: str, context: dict | None = None
    ) -> AuthorizationResult: ...

    @abstractmethod
    def require_permission(self, permission: str, user: Any) -> AuthorizationResult: ...


class RBACAuthorizationProvider(AuthorizationProvider):
    def check_access(
        self, user: Any, resource: str, action: str, context: dict | None = None
    ) -> AuthorizationResult:
        from ..security.rbac import has_permission

        permission = f"{resource}:{action}"
        if has_permission(user.role, permission):
            return AuthorizationResult(allowed=True)
        return AuthorizationResult(allowed=False, reason=f"Role {user.role} lacks {permission}")

    def require_permission(self, permission: str, user: Any) -> AuthorizationResult:
        from ..security.rbac import has_permission

        if has_permission(user.role, permission):
            return AuthorizationResult(allowed=True)
        return AuthorizationResult(allowed=False, reason=f"Missing permission: {permission}")


class ABACAuthorizationProvider(AuthorizationProvider):
    def __init__(self) -> None:
        from ..security.abac import ABACEngine

        self._engine = ABACEngine()

    def check_access(
        self, user: Any, resource: str, action: str, context: dict | None = None
    ) -> AuthorizationResult:
        subject = {"id": user.id, "role": user.role, "lab_id": getattr(user, "lab_id", None)}
        ctx = context or {}
        allowed = self._engine.can_access(resource, action, subject=subject, resource_attrs=ctx)
        return AuthorizationResult(allowed=allowed)

    def require_permission(self, permission: str, user: Any) -> AuthorizationResult:
        from ..security.rbac import has_permission

        if has_permission(user.role, permission):
            return AuthorizationResult(allowed=True)
        return AuthorizationResult(allowed=False, reason=f"Missing permission: {permission}")


PlatformRegistry.register(
    "authorization",
    RBACAuthorizationProvider(),
    capabilities=[
        {
            "name": "check_access",
            "description": "Check if a user can access a resource with a given action",
        },
        {"name": "require_permission", "description": "Check if a user has a specific permission"},
    ],
)
