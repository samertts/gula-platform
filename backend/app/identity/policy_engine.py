"""DEPRECATED — identity policy engine stub (fail-closed).

.. warning::
    This module is **deprecated**. The allow-by-default behavior it used to
    expose has been removed: every decision now defaults to **DENY**.

    Use the canonical authorization services instead:

    * :class:`app.services.authorization_service.AuthorizationCheckService`
    * :class:`app.services.authorization_service.PolicyService`

    ``PolicyContext`` is kept only for backward compatibility with existing
    call sites and tests; ``PolicyEngine`` now fails closed so it can never
    silently grant access.
"""

from __future__ import annotations

import warnings
from dataclasses import dataclass, field
from typing import Any

warnings.warn(
    "app.identity.policy_engine is deprecated; use "
    "AuthorizationCheckService/PolicyService from "
    "app.services.authorization_service instead.",
    DeprecationWarning,
    stacklevel=2,
)


@dataclass
class PolicyContext:
    subject_id: str
    subject_type: str
    action: str
    resource_type: str
    resource_id: str | None = None
    organization_id: str | None = None
    environment: dict[str, Any] = field(default_factory=dict)


class PolicyEngine:
    async def evaluate(self, context: PolicyContext) -> bool:
        return False

    async def evaluate_action(self, policy: Any, context: PolicyContext) -> str:
        return "deny"

    async def filter_resources(
        self,
        resources: list[Any],
        context: PolicyContext,
    ) -> list[Any]:
        return []
