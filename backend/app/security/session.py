"""
Session management helpers for GULA Platform.

bump_perm_version() is the single authoritative place that:
  1. Increments perm_version in the database.
  2. Writes the new version to Redis (invalidating all active JWTs immediately).
  3. Records an audit log entry.

Call it whenever a user's access rights change:
  - role change
  - account activate / deactivate
  - password change
  - lab_id change
"""
import logging
from sqlalchemy.orm import Session
from ..models.lab_user import LabUser
from ..services.audit_service import log_action
from .redis_client import cache

logger = logging.getLogger("gula.session")

# Redis key template — keep in sync with dependencies.py
_PERM_VER_KEY = "user:perm_ver:{user_id}"
# 31 days — longer than any refresh token
_PERM_VER_TTL = 86400 * 31


def perm_ver_key(user_id: int) -> str:
    return _PERM_VER_KEY.format(user_id=user_id)


def bump_perm_version(
    user: LabUser,
    db: Session,
    *,
    actor_id: int | None = None,
    actor_role: str | None = None,
    reason: str = "permission_change",
) -> int:
    """
    Increment user.perm_version, sync to Redis, and write an audit log.

    Returns the new perm_version value.
    """
    old_version = user.perm_version or 1
    new_version = old_version + 1

    user.perm_version = new_version
    # DB commit is the caller's responsibility (allows batching with other changes)

    # Write to Redis immediately so any in-flight request gets the new version
    cache.set(perm_ver_key(user.id), new_version, ex=_PERM_VER_TTL)

    log_action(
        db,
        action="permission_change",
        resource_type="user",
        resource_id=user.id,
        user_id=actor_id,
        user_role=actor_role,
        details=f"{reason}: perm_version {old_version} → {new_version} for user {user.email}",
    )

    logger.info(
        "perm_version bumped for user %d (%s): %d → %d [%s]",
        user.id, user.email, old_version, new_version, reason,
    )
    return new_version


def warm_perm_version(user: LabUser) -> None:
    """
    Write the current perm_version to Redis if not already there.
    Called on login so the fast path in get_current_user always hits Redis.
    """
    key = perm_ver_key(user.id)
    if cache.get(key) is None:
        ver = user.perm_version or 1
        cache.set(key, ver, ex=_PERM_VER_TTL)


def get_perm_version(user_id: int, db_version: int) -> int:
    """
    Return the authoritative perm_version for a user.
    Reads from Redis (fast); falls back to the DB value passed in.
    """
    cached = cache.get(perm_ver_key(user_id))
    if cached is not None:
        return int(cached)
    return db_version
