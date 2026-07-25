GSF-005: Authorization Module — RBAC/ABAC policy engine.

Provides fine-grained access control for the GULA platform combining
Role-Based Access Control (RBAC) and Attribute-Based Access Control (ABAC)
with a Rego-powered policy engine (OPA integration). Supports resource-level,
action-level, and field-level authorization.

Exports:
    AuthorizationEngine: Core authorization decision engine
    RbacProvider: Role-based access control
    AbacProvider: Attribute-based access control
    PolicyEngine: Rego/OPA policy evaluation
    ResourceScope: Fine-grained resource scoping
    PermissionRegistry: Centralized permission catalog
    PolicyEnforcer: Middleware-compatible enforcement point
"""

from security.modules.authorization.engine import AuthorizationEngine
from security.modules.authorization.rbac import RbacProvider
from security.modules.authorization.abac import AbacProvider
from security.modules.authorization.policy import PolicyEngine
from security.modules.authorization.resource import ResourceScope
from security.modules.authorization.registry import PermissionRegistry
from security.modules.authorization.enforcer import PolicyEnforcer

__all__ = [
    "AuthorizationEngine",
    "RbacProvider",
    "AbacProvider",
    "PolicyEngine",
    "ResourceScope",
    "PermissionRegistry",
    "PolicyEnforcer",
]
