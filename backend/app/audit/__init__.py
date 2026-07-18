"""Audit module — decorator + log_action."""

from __future__ import annotations

import functools
import logging
from typing import Any, Callable

from fastapi import Request
from sqlalchemy.orm import Session as SASession

from ..services.audit_service import log_action

logger = logging.getLogger("gula.audit")


def audit_log(action: str) -> Callable:
    """Decorator that writes an audit log entry on successful endpoint execution."""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            result = func(*args, **kwargs)
            try:
                request: Request | None = kwargs.get("request") or next(
                    (a for a in args if isinstance(a, Request)), None
                )
                db: SASession | None = kwargs.get("db") or next(
                    (a for a in args if isinstance(a, SASession)), None
                )
                if request and db:
                    user_id = getattr(request.state, "user_id", None) or 0
                    lab_id = getattr(request.state, "lab_id", None) or 0
                    log_action(
                        db=db,
                        action=action,
                        resource_type="FHIR",
                        resource_id=kwargs.get("resource_id") or kwargs.get("resource_type", ""),
                        user_id=user_id,
                        lab_id=lab_id,
                        details={"method": request.method, "path": request.url.path},
                    )
            except Exception:
                logger.warning("audit_log decorator failed", exc_info=True)
            return result
        return wrapper
    return decorator


__all__ = ["audit_log", "log_action"]
