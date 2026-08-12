from .permissions import (
    EXTENDED_ALL_PERMISSIONS,
    # Extended string-based API (backend-compatible)
    EXTENDED_ROLE_LEVELS,
    EXTENDED_ROLE_PERMISSIONS,
    EXTENDED_VALID_ROLES,
    Permission,
    RBACMatrix,
    Role,
    can_manage_role,
    get_permissions_for_role,
    get_role_level,
    has_permission,
    has_permission_str,
    require_permission,
)

__all__ = [
    "EXTENDED_ALL_PERMISSIONS",
    "EXTENDED_ROLE_LEVELS",
    "EXTENDED_ROLE_PERMISSIONS",
    "EXTENDED_VALID_ROLES",
    "Permission",
    "RBACMatrix",
    "Role",
    "can_manage_role",
    "get_permissions_for_role",
    "get_role_level",
    "has_permission",
    "has_permission_str",
    "require_permission",
]
