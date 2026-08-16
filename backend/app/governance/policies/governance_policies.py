from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

from app._compat import UTC


class GovernanceAction(Enum):
    CREATE_NODE = "create_node"
    UPDATE_NODE = "update_node"
    DELETE_NODE = "delete_node"
    CREATE_DELEGATION = "create_delegation"
    REVOKE_DELEGATION = "revoke_delegation"
    APPOINT_ACTING = "appoint_acting"
    DECLARE_EMERGENCY = "declare_emergency"
    ISSUE_HEALTH_NUMBER = "issue_health_number"
    MERGE_IDENTITY = "merge_identity"
    SPLIT_IDENTITY = "split_identity"
    REGISTER_LAB = "register_lab"
    DESIGNATE_REFERENCE = "designate_reference"
    APPROVE_POLICY = "approve_policy"
    CLASSIFY_DATA = "classify_data"
    DEPLOY_AI_MODEL = "deploy_ai_model"
    REGISTER_CONNECTOR = "register_connector"
    MODIFY_INTEROP_PROTOCOL = "modify_interop_protocol"


class GovernanceRiskLevel(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class GovernancePolicyDecision:
    allowed: bool
    risk: GovernanceRiskLevel
    action: GovernanceAction
    reason: str
    context: dict[str, Any] = field(default_factory=dict)
    ts: str = ""


class GovernancePolicyEngine:
    def __init__(self):
        self._policies: dict[GovernanceAction, dict] = {
            GovernanceAction.CREATE_NODE: {"risk": GovernanceRiskLevel.MEDIUM, "require_approval": False},
            GovernanceAction.UPDATE_NODE: {"risk": GovernanceRiskLevel.LOW, "require_approval": False},
            GovernanceAction.DELETE_NODE: {"risk": GovernanceRiskLevel.CRITICAL, "require_approval": True},
            GovernanceAction.CREATE_DELEGATION: {"risk": GovernanceRiskLevel.MEDIUM, "require_approval": True},
            GovernanceAction.REVOKE_DELEGATION: {"risk": GovernanceRiskLevel.MEDIUM, "require_approval": True},
            GovernanceAction.APPOINT_ACTING: {"risk": GovernanceRiskLevel.HIGH, "require_approval": True},
            GovernanceAction.DECLARE_EMERGENCY: {"risk": GovernanceRiskLevel.HIGH, "require_approval": True},
            GovernanceAction.ISSUE_HEALTH_NUMBER: {"risk": GovernanceRiskLevel.LOW, "require_approval": False},
            GovernanceAction.MERGE_IDENTITY: {"risk": GovernanceRiskLevel.CRITICAL, "require_approval": True},
            GovernanceAction.SPLIT_IDENTITY: {"risk": GovernanceRiskLevel.CRITICAL, "require_approval": True},
            GovernanceAction.REGISTER_LAB: {"risk": GovernanceRiskLevel.MEDIUM, "require_approval": False},
            GovernanceAction.DESIGNATE_REFERENCE: {"risk": GovernanceRiskLevel.HIGH, "require_approval": True},
            GovernanceAction.APPROVE_POLICY: {"risk": GovernanceRiskLevel.HIGH, "require_approval": True},
            GovernanceAction.CLASSIFY_DATA: {"risk": GovernanceRiskLevel.HIGH, "require_approval": True},
            GovernanceAction.DEPLOY_AI_MODEL: {"risk": GovernanceRiskLevel.CRITICAL, "require_approval": True},
            GovernanceAction.REGISTER_CONNECTOR: {"risk": GovernanceRiskLevel.MEDIUM, "require_approval": False},
            GovernanceAction.MODIFY_INTEROP_PROTOCOL: {"risk": GovernanceRiskLevel.HIGH, "require_approval": True},
        }

    def evaluate(
        self,
        action: GovernanceAction,
        context: dict[str, Any] | None = None,
    ) -> GovernancePolicyDecision:
        policy = self._policies.get(action)
        if not policy:
            return GovernancePolicyDecision(
                allowed=False,
                risk=GovernanceRiskLevel.CRITICAL,
                action=action,
                reason=f"Unknown governance action: {action.value}",
                context=context or {},
                ts=datetime.now(UTC).isoformat(),
            )

        return GovernancePolicyDecision(
            allowed=True,
            risk=policy["risk"],
            action=action,
            reason=f"Policy allows {action.value} at risk level {policy['risk'].value}",
            context={
                **(context or {}),
                "require_approval": policy["require_approval"],
            },
            ts=datetime.now(UTC).isoformat(),
        )

    def require_elevated_approval(
        self, action: GovernanceAction, user_role: str | None = None,
    ) -> bool:
        policy = self._policies.get(action)
        if not policy:
            return True
        if not policy["require_approval"]:
            return False
        elevated_roles = ["system_admin", "national_admin", "ministry_admin"]
        return user_role not in elevated_roles


governance_policy_engine = GovernancePolicyEngine()
