"""Session management helpers for GULA Platform.

bump_perm_version() is the single authoritative place that:
  1. Increments perm_version in the database.
  2. Publishes the new version to the shared security store (Redis), so all
     active JWTs carrying an older perm_ver are rejected immediately.
  3. Records an audit log entry.

Call it whenever a user's access rights change:
  - role change
  - account activate / deactivate
  - password change
  - lab_id change

SECURITY MODEL (P0-D3 / S-06):
  The database value of ``perm_version`` is the authoritative revocation signal
  and is read fresh from the PRIMARY database on every authenticated request
  (``security.dependencies.get_current_user`` uses ``get_db``).  The shared
  store is a fast-path cache only.  No cached value is ever allowed to weaken
  revocation: :func:`get_perm_version` returns ``max(cached, db_version)`` and
  ignores missing, malformed or stale cache entries.  If the shared store is
  unavailable in a production/staging profile, ``security_store()`` raises and
  we deliberately rely on the authoritative DB value (session validity is still
  reliably established) while logging CRITICALLY -- we never silently accept a
  session whose revocation state cannot be determined.
"""

import logging

from sqlalchemy.orm import Session

from ..models.lab_user import LabUser
from ..models.user import User
from ..services.audit_service import log_action
from .redis_client import SecurityStoreUnavailable, security_store

logger = logging.getLogger("gula.session")

# Redis key template — keep in sync with dependencies.py
_PERM_VER_KEY = "user:{account_kind}:perm_ver:{user_id}"
# 31 days — longer than any refresh token
_PERM_VER_TTL = 86400 * 31


def _account_kind(user: object) -> str:
    return "user" if isinstance(user, User) else "lab"


def perm_ver_key(user_id: int, account_kind: str = "lab") -> str:
    return _PERM_VER_KEY.format(account_kind=account_kind, user_id=user_id)


def _coerce_version(value: object) -> int | None:
    """Return ``value`` as a positive int, or ``None`` if it is unusable.

    A cached perm_version must never be trusted unless it is a well-formed
    positive integer.  Reject booleans (``int(True) == 1``), zero, negatives,
    non-numeric strings and numeric-looking garbage.
    """
    if value is None or isinstance(value, bool):
        return None
    try:
        parsed = int(value)  # type: ignore[arg-type]
    except (TypeError, ValueError, OverflowError):
        return None
    return parsed if parsed >= 1 else None


def _security_store_or_none(operation: str):
    """Return the shared store, or ``None`` when security state is unavailable.

    In production/staging ``security_store()`` fails closed by raising
    ``SecurityStoreUnavailable`` when only process-local state is available.
    We log that condition critically and continue with the authoritative DB
    value (never with an unverified session).
    """
    try:
        return security_store(operation)
    except SecurityStoreUnavailable as exc:
        logger.critical("perm_version store unavailable for %s: %s", operation, exc)
        return None


def _store_get(store, key: str):
    """Read a cache key, treating any store/transport error as a cache miss."""
    try:
        return store.get(key)
    except Exception as exc:
        logger.critical("perm_version store read failed for %s: %s", key, exc)
        return None


def _store_set(store, key: str, value: int) -> None:
    """Write a cache key; a store failure is logged, never silently ignored."""
    try:
        store.set(key, value, ex=_PERM_VER_TTL)
    except Exception as exc:
        logger.critical("perm_version store write failed for %s: %s", key, exc)


def bump_perm_version(
    user: LabUser,
    db: Session,
    *,
    actor_id: int | None = None,
    actor_role: str | None = None,
    reason: str = "permission_change",
) -> int:
    """Increment user.perm_version, publish to the store, and write an audit log.

    Returns the new perm_version value.  The DB mutation is authoritative; the
    caller owns the commit (so the bump can be batched with other changes).
    """
    old_version = user.perm_version or 1
    new_version = old_version + 1

    user.perm_version = new_version
    # DB commit is the caller's responsibility (allows batching with other changes)

    # Publish immediately so in-flight requests observe the new version.  This
    # is a fast-path optimisation: the authoritative DB bump above guarantees
    # revocation even when the store is unavailable, so a store failure must not
    # abort the caller (which could otherwise leave the DB bump uncommitted).
    store = _security_store_or_none("Permission version write")
    if store is not None:
        _store_set(store, perm_ver_key(user.id, _account_kind(user)), new_version)

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
        user.id,
        user.email,
        old_version,
        new_version,
        reason,
    )
    return new_version


def warm_perm_version(user: LabUser) -> None:
    """Seed the shared store with the current perm_version on login.

    Missing, malformed or stale entries are corrected on read by
    :func:`get_perm_version`, so a failed warm never weakens revocation.
    """
    key = perm_ver_key(user.id, _account_kind(user))
    store = _security_store_or_none("Permission version warm")
    if store is None:
        return
    if _store_get(store, key) is None:
        _store_set(store, key, user.perm_version or 1)


def get_perm_version(user_id: int, db_version: int, account_kind: str = "lab") -> int:
    """Return the authoritative perm_version for a user.

    ``db_version`` is the value read fresh from the primary DB and is
    authoritative.  The cached value is only a fast path and is combined with
    ``max(...)`` so that a stale, missing or malformed cache entry can never
    keep a revoked session alive.  A store outage falls back to the DB value;
    it never results in accepting a session whose version is unknown.
    """
    authoritative = _coerce_version(db_version) or 1
    store = _security_store_or_none("Permission version read")
    if store is None:
        return authoritative
    cached = _coerce_version(_store_get(store, perm_ver_key(user_id, account_kind)))
    if cached is None:
        return authoritative
    return max(cached, authoritative)
