from __future__ import annotations

import logging
from collections.abc import Callable
from functools import wraps
from typing import Any

from app.control_plane.policy.manager import PolicyManager

logger = logging.getLogger("gula.control_plane.policy.enforcer")


class PolicyEnforcer:
    def __init__(self, policy_manager: PolicyManager):
        self._pm = policy_manager

    def enforce(self, action: str, context: dict[str, Any] | None = None) -> None:
        result = self._pm.evaluate(action, context or {})
        if not result.get("allowed", True):
            violations = result.get("violations", [])
            reasons = "; ".join(v.get("reason", "") for v in violations)
            raise PermissionError(f"Policy denied action '{action}': {reasons}")

    def enforce_or_warn(self, action: str, context: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        result = self._pm.evaluate(action, context or {})
        if not result.get("allowed", True):
            logger.warning("Policy violation for '%s': %s", action, result.get("violations", []))
        return result.get("violations", [])

    def decorate(self, action: str):
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            def wrapper(*args: Any, **kwargs: Any) -> Any:
                self.enforce(action)
                return func(*args, **kwargs)
            return wrapper
        return decorator

    async def enforce_async(self, action: str, context: dict[str, Any] | None = None) -> None:
        self.enforce(action, context)

    def check(self, action: str, context: dict[str, Any] | None = None) -> bool:
        try:
            self.enforce(action, context)
            return True
        except PermissionError:
            return False
