"""Small adapter for route-level immutable audit records.

Clinical and national resources commonly use UUID/string identifiers while the
legacy audit table keeps an optional integer resource_id column. String IDs are
therefore retained in the tamper-evident details payload rather than being
silently coerced or dropped.
"""

from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from app.services.audit_service import log_action


def _numeric_user_id(user: Any) -> int | None:
    value = getattr(user, "id", user)
    if isinstance(value, int):
        return value
    if isinstance(value, str) and value.isdigit():
        return int(value)
    return None


def audit_mutation(
    db: Session,
    *,
    action: str,
    resource_type: str,
    resource_id: Any = None,
    user: Any = None,
    lab_id: int | None = None,
    before: dict[str, Any] | None = None,
    after: dict[str, Any] | None = None,
    details: dict[str, Any] | None = None,
) -> None:
    payload: dict[str, Any] = {
        "before": before,
        "after": after,
    }
    if details:
        payload.update(details)
    if resource_id is not None and not isinstance(resource_id, int):
        payload["resource_id"] = str(resource_id)
    log_action(
        db,
        action,
        resource_type=resource_type,
        resource_id=resource_id if isinstance(resource_id, int) else None,
        user_id=_numeric_user_id(user),
        user_role=getattr(user, "role", None),
        lab_id=lab_id if lab_id is not None else getattr(user, "lab_id", None),
        details=payload,
    )
