"""Small adapter for route-level immutable audit records.

Clinical and national resources commonly use UUID/string identifiers while the
legacy audit table keeps an optional integer resource_id column. String IDs are
therefore retained in the tamper-evident details payload rather than being
silently coerced or dropped.
"""

from __future__ import annotations

import functools
import inspect
from typing import Any, Callable, TypeVar, cast

from sqlalchemy.orm import Session

from app.services.audit_service import log_action


def _numeric_user_id(user: Any) -> int | None:
    value = getattr(user, "id", user)
    if isinstance(value, int):
        return value
    if isinstance(value, str) and value.isdigit():
        return int(value)
    return None


F = TypeVar("F", bound=Callable[..., Any])


def audit_route_mutation(
    *,
    action: str = "route_mutation",
    resource_type: str = "http_route",
) -> Callable[[F], F]:
    """Audit a successful write route without storing clinical response payloads.

    This decorator is intentionally fail-closed: if the audit record cannot be
    persisted, the request fails instead of silently reporting success. Routes
    that already capture semantic before/after state should continue to call
    :func:`audit_mutation` directly; this decorator provides the mandatory
    route-level coverage for legacy and service-backed writes.
    """

    def decorator(func: F) -> F:
        def _record(kwargs: dict[str, Any], result: Any) -> None:
            db = kwargs.get("db")
            actor = (
                kwargs.get("current_user")
                or kwargs.get("user")
                or kwargs.get("actor")
                or kwargs.get("reviewer")
                or kwargs.get("principal")
            )
            if db is None:
                raise RuntimeError("audited mutation route is missing a database session")
            route_name = f"{func.__module__}.{func.__name__}"
            resource_id = None
            if isinstance(result, dict):
                candidate = result.get("id") or result.get("resource_id")
                if isinstance(candidate, int):
                    resource_id = candidate
            audit_mutation(
                db,
                action=action,
                resource_type=resource_type,
                resource_id=resource_id,
                user=actor,
                before={"captured": False, "reason": "generic route audit"},
                after={"captured": False, "reason": "response payload redacted"},
                details={"route": route_name, "status": "committed"},
            )
            db.commit()

        if inspect.iscoroutinefunction(func):
            @functools.wraps(func)
            async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
                result = await func(*args, **kwargs)
                _record(kwargs, result)
                return result

            return cast(F, async_wrapper)

        @functools.wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            result = func(*args, **kwargs)
            _record(kwargs, result)
            return result

        return cast(F, sync_wrapper)

    return decorator


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
