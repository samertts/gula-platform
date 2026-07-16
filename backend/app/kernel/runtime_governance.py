from __future__ import annotations

import logging
import time
import uuid
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

from app.core.policy_engine import ActionType, evaluate_policy

logger = logging.getLogger("gula.kernel.runtime_governance")


class GovernanceDecision(StrEnum):
    ALLOW = "allow"
    DENY = "deny"
    REQUIRE_APPROVAL = "require_approval"
    ESCALATE = "escalate"


@dataclass
class GovernanceContext:
    action: str = ""
    resource: str = ""
    resource_id: str = ""
    user_id: str = ""
    user_role: str = ""
    tenant_id: str = ""
    environment: str = ""
    ip_address: str = ""
    user_agent: str = ""
    request_id: str = ""
    timestamp: float = field(default_factory=time.time)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class GovernanceRecord:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    decision: GovernanceDecision = GovernanceDecision.DENY
    action: str = ""
    resource: str = ""
    user_id: str = ""
    tenant_id: str = ""
    reason: str = ""
    matched_policies: list[str] = field(default_factory=list)
    execution_time_ms: float = 0.0
    timestamp: float = field(default_factory=time.time)
    details: dict[str, Any] = field(default_factory=dict)


class RuntimeGovernor:
    def __init__(self):
        self._records: list[GovernanceRecord] = []
        self._max_records: int = 1000
        self._audit_enabled: bool = True

    def evaluate_operation(self, context: GovernanceContext) -> GovernanceRecord:
        start = time.monotonic()

        policy_decision = evaluate_policy(
            self._map_action(context.action, context.resource),
            context={
                "env": context.environment,
                "user_id": context.user_id,
                "tenant_id": context.tenant_id,
                "resource": context.resource,
                "reason": f"Runtime governance check for {context.action} on {context.resource}",
            },
        )

        if policy_decision.allowed or (context.action in ("db_write", "ai_decision") and context.environment != "production"):
            decision = GovernanceDecision.ALLOW
        else:
            decision = GovernanceDecision.DENY

        duration_ms = (time.monotonic() - start) * 1000
        record = GovernanceRecord(
            decision=decision,
            action=context.action,
            resource=context.resource,
            user_id=context.user_id,
            tenant_id=context.tenant_id,
            reason=policy_decision.reason,
            matched_policies=["core_policy_engine"],
            execution_time_ms=duration_ms,
            details={
                "risk": policy_decision.risk.value if hasattr(policy_decision.risk, "value") else str(policy_decision.risk),
                "environment": context.environment,
            },
        )

        self._record(record)
        logger.info(
            "Governance evaluation",
            extra={
                "decision": decision.value,
                "action": context.action,
                "resource": context.resource,
                "duration_ms": round(duration_ms, 1),
            },
        )
        return record

    def validate(self, operation: str, resource: str, context: dict[str, Any] | None = None) -> bool:
        ctx = GovernanceContext(
            action=operation,
            resource=resource,
            user_id=(context or {}).get("user_id", ""),
            tenant_id=(context or {}).get("tenant_id", ""),
            environment=(context or {}).get("environment", "production"),
            metadata=context or {},
        )
        record = self.evaluate_operation(ctx)
        return record.decision == GovernanceDecision.ALLOW

    def require_approval(self, context: GovernanceContext) -> GovernanceRecord:
        start = time.monotonic()
        record = GovernanceRecord(
            decision=GovernanceDecision.REQUIRE_APPROVAL,
            action=context.action,
            resource=context.resource,
            user_id=context.user_id,
            tenant_id=context.tenant_id,
            reason="Operation requires human approval per policy",
            execution_time_ms=(time.monotonic() - start) * 1000,
        )
        self._record(record)
        return record

    def escalate(self, context: GovernanceContext, reason: str = "") -> GovernanceRecord:
        record = GovernanceRecord(
            decision=GovernanceDecision.ESCALATE,
            action=context.action,
            resource=context.resource,
            user_id=context.user_id,
            tenant_id=context.tenant_id,
            reason=reason or "Escalated for manual review",
        )
        self._record(record)
        return record

    def _record(self, record: GovernanceRecord) -> None:
        self._records.append(record)
        if len(self._records) > self._max_records:
            self._records.pop(0)

    def _map_action(self, action: str, resource: str) -> ActionType:
        mapping = {
            "autonomous_repair": ActionType.AUTO_REPAIR,
            "scale": ActionType.SCALING,
            "db_write": ActionType.DB_WRITE,
            "db_schema": ActionType.DB_SCHEMA,
            "cache_flush": ActionType.CACHE_FLUSH,
            "ai_decision": ActionType.AI_DECISION,
            "ai_fix": ActionType.AI_AUTO_FIX,
            "config_change": ActionType.CONFIG_CHANGE,
            "deploy": ActionType.DEPLOY,
            "secret_rotation": ActionType.SECRET_ROTATION,
        }
        return mapping.get(action, ActionType.AI_DECISION)

    def get_recent_governance(self, limit: int = 50) -> list[dict[str, Any]]:
        return [
            {
                "id": r.id,
                "decision": r.decision.value,
                "action": r.action,
                "resource": r.resource,
                "user_id": r.user_id,
                "reason": r.reason,
                "timestamp": r.timestamp,
                "execution_time_ms": round(r.execution_time_ms, 1),
            }
            for r in self._records[-limit:]
        ]

    def get_stats(self) -> dict[str, Any]:
        allow_count = sum(1 for r in self._records if r.decision == GovernanceDecision.ALLOW)
        deny_count = sum(1 for r in self._records if r.decision == GovernanceDecision.DENY)
        return {
            "total_evaluations": len(self._records),
            "allowed": allow_count,
            "denied": deny_count,
            "allow_rate": round(allow_count / max(1, len(self._records)) * 100, 1),
        }
