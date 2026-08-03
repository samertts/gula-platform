from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from shared.rules_engine.domain.enums import (
    Operator,
    RuleCategory,
    RuleOutcome,
    RuleSeverity,
    RuleStatus,
    RuleTrigger,
)


@dataclass
class RuleCondition:
    field: str
    operator: Operator
    value: Any
    value_type: str = "string"


@dataclass
class RuleAction:
    action_type: str
    params: dict[str, Any] = field(default_factory=dict)


@dataclass
class RuleDefinition:
    id: str
    name: str
    description: str = ""
    category: RuleCategory = RuleCategory.POLICY
    severity: RuleSeverity = RuleSeverity.INFO
    status: RuleStatus = RuleStatus.DRAFT
    conditions: list[RuleCondition] = field(default_factory=list)
    actions: list[RuleAction] = field(default_factory=list)
    priority: int = 0
    version: int = 1
    tags: list[str] = field(default_factory=list)
    effective_from: datetime | None = None
    effective_to: datetime | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def is_effective(self) -> bool:
        now = datetime.now(UTC)
        if self.effective_from and now < self.effective_from:
            return False
        return not (self.effective_to and now > self.effective_to)

    @property
    def is_active(self) -> bool:
        return self.status == RuleStatus.ACTIVE and self.is_effective


@dataclass
class RuleEvaluationContext:
    rule_id: str = ""
    trigger: RuleTrigger = RuleTrigger.MANUAL
    resource_type: str = ""
    resource_id: str = ""
    user_id: str = ""
    tenant_id: str = ""
    data: dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class RuleEvaluationResult:
    rule_id: str
    rule_name: str
    outcome: RuleOutcome
    severity: RuleSeverity = RuleSeverity.INFO
    message: str = ""
    actions_taken: list[str] = field(default_factory=list)
    execution_time_ms: float = 0.0
    triggered_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class RuleSet:
    id: str
    name: str
    rules: list[RuleDefinition] = field(default_factory=list)
    strategy: str = "ALL"
