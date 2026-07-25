from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


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
        return True

    async def evaluate_action(self, policy: Any, context: PolicyContext) -> str:
        return "allow"

    async def filter_resources(
        self,
        resources: list[Any],
        context: PolicyContext,
    ) -> list[Any]:
        return resources
