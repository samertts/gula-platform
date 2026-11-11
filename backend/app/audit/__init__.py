"""Audit module — decorator + log_action."""

from __future__ import annotations

import functools
import inspect
import logging
from collections.abc import Callable
from typing import Any

from fastapi import Request
from sqlalchemy.orm import Session as SASession

from ..services.audit_service import log_action

logger = logging.getLogger("gula.audit")

#: Rows written under this resource_type are the ones FHIR Provenance search
#: projects (``fhir_search_provenance`` filters on it), so the two ``fhir_*``
#: detail keys are emitted for them and only them.
_FHIR_RESOURCE_TYPE = "FHIR"


def _numeric_or_none(value: Any) -> int | None:
    """Coerce a resource reference to ``AuditLog.resource_id``'s INTEGER column.

    EHR identifiers are 26-character ULIDs. PostgreSQL rejects one outright
    while SQLite would silently accept it, so a non-numeric reference is stored
    in ``details`` instead of being forced into the column.
    """
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, str) and value.isdigit():
        return int(value)
    return None


def audit_log(action: str, resource_type: str = _FHIR_RESOURCE_TYPE) -> Callable:
    """Decorator that writes an audit log entry on successful endpoint execution.

    ``resource_type`` defaults to ``"FHIR"`` for the generic FHIR endpoints this
    decorator was first written for. Every other caller passes its own resource
    so the audit row does not label a clinical record as a FHIR resource.

    The actor is read from the endpoint's ``current_user`` dependency. Nothing in
    ``app/`` populates ``request.state.user_id`` or ``request.state.lab_id`` --
    only ``request_id`` is set, by ``middleware.py`` -- so relying on those wrote
    every row as user 0 of lab 0, which also made the rows invisible to the
    tenant-scoped Provenance search. A row that cannot be attributed is refused
    rather than written anonymously.
    """
    def decorator(func: Callable) -> Callable:
        if inspect.iscoroutinefunction(func):
            # A sync wrapper around a coroutine function returns the un-awaited
            # coroutine and would audit work that never ran.
            raise TypeError(
                f"audit_log cannot wrap the async endpoint {func.__qualname__!r}; "
                "wrapping one would audit a mutation that never executed.",
            )

        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            result = func(*args, **kwargs)
            try:
                request: Request | None = kwargs.get("request") or next(
                    (a for a in args if isinstance(a, Request)), None,
                )
                db: SASession | None = kwargs.get("db") or next(
                    (a for a in args if isinstance(a, SASession)), None,
                )
                if db is None:
                    raise RuntimeError(
                        f"{func.__qualname__} exposes no database session, "
                        "so its mutation cannot be audited.",
                    )
                actor = kwargs.get("current_user")
                user_id = getattr(actor, "id", None)
                lab_id = getattr(actor, "lab_id", None)
                user_role = getattr(actor, "role", None)
                if user_id is None and request is not None:
                    # Retained for any caller that populates request.state itself.
                    user_id = getattr(request.state, "user_id", None)
                    if lab_id is None:
                        lab_id = getattr(request.state, "lab_id", None)
                if user_id is None:
                    raise RuntimeError(
                        f"{func.__qualname__} exposes no authenticated actor, so its "
                        "mutation cannot be attributed and must not be audited anonymously.",
                    )
                resource_ref = kwargs.get("resource_id")
                fhir_resource_type = kwargs.get("resource_type")
                if isinstance(result, dict):
                    fhir_resource_type = fhir_resource_type or result.get("resourceType")
                    resource_ref = resource_ref or result.get("id")
                details: dict[str, Any] = {
                    "record_id": str(resource_ref) if resource_ref is not None else None,
                }
                if resource_type == _FHIR_RESOURCE_TYPE:
                    details["fhir_resource_id"] = details["record_id"]
                    details["fhir_resource_type"] = fhir_resource_type
                if request is not None:
                    details["method"] = request.method
                    details["path"] = request.url.path
                log_action(
                    db=db,
                    action=action,
                    resource_type=resource_type,
                    resource_id=_numeric_or_none(resource_ref),
                    user_id=user_id,
                    user_role=user_role,
                    lab_id=lab_id,
                    details=details,
                )
                db.commit()
            except Exception:
                # Audit integrity takes precedence over mutation availability:
                # the dependency rolls back an uncommitted clinical mutation.
                logger.exception("audit_log decorator failed")
                raise
            return result
        return wrapper
    return decorator


__all__ = ["audit_log", "log_action"]
