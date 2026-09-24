from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, cast

from sqlalchemy.orm import Session

from app.identity.services.authorization_decision import (
    AuthorizationDecision,
    AuthorizationDecisionService,
    AuthorizationRequest,
)

if TYPE_CHECKING:
    from app.identity.api.workspaces import NiamActor


@dataclass(frozen=True)
class PolicyContext:
    """Compatibility context for callers migrating to AuthorizationRequest."""

    subject_id: str
    subject_type: str
    action: str
    resource_type: str
    resource_id: str | None = None
    organization_id: str | None = None
    facility_id: str | None = None
    department_id: str | None = None
    unit_id: str | None = None
    workspace_id: str | None = None
    permission_key: str | None = None
    purpose: str | None = None
    purpose_validated: bool = False
    resource_context: dict[str, Any] = field(default_factory=dict)
    environment: dict[str, Any] = field(default_factory=dict)
    sensitivity: str = "medium"
    resource_status: str | None = None
    break_glass: bool = False
    break_glass_authorized: bool = False


class PolicyEngine:
    """Fail-closed compatibility facade over the centralized decision service."""

    def __init__(self, session: Session | None = None, actor: NiamActor | None = None) -> None:
        self.session = session
        self.actor = actor

    def evaluate(self, context: PolicyContext) -> bool:
        decision = self._decision(context)
        return cast(bool, decision.allowed)

    def evaluate_action(self, policy: Any, context: PolicyContext) -> str:
        del policy
        decision = self._decision(context)
        return cast(str, decision.decision.value)

    def filter_resources(
        self,
        resources: list[Any],
        context: PolicyContext,
    ) -> list[Any]:
        if self.session is None or self.actor is None:
            return []
        authorized: list[Any] = []
        for resource in resources:
            resource_id = getattr(resource, "id", None)
            resource_context = dict(context.resource_context)
            resource_context.update(
                {
                    "exists": True,
                    "organization_id": getattr(
                        resource, "organization_id", context.organization_id
                    ),
                    "facility_id": getattr(resource, "facility_id", context.facility_id),
                    "department_id": getattr(resource, "department_id", context.department_id),
                    "workspace_id": getattr(resource, "workspace_id", context.workspace_id),
                },
            )
            resource_context["owner_id"] = getattr(resource, "owner_id", None)
            request = self._request(
                context, resource_id=resource_id, resource_context=resource_context
            )
            if (
                AuthorizationDecisionService(self.session).authorize(self.actor, request)
            ).allowed:
                authorized.append(resource)
        return authorized

    def _decision(self, context: PolicyContext) -> AuthorizationDecision:
        if self.session is None or self.actor is None:
            from app.identity.services.authorization_decision import (
                AuthorizationDecision,
                AuthorizationReason,
            )

            return AuthorizationDecision.deny(AuthorizationReason.session_invalid)
        return AuthorizationDecisionService(self.session).authorize(
            self.actor, self._request(context)
        )

    @staticmethod
    def _request(
        context: PolicyContext,
        *,
        resource_id: str | None = None,
        resource_context: dict[str, Any] | None = None,
    ) -> AuthorizationRequest:
        return AuthorizationRequest(
            subject_account_id=context.subject_id,
            action=context.action,
            resource_type=context.resource_type,
            resource_id=resource_id if resource_id is not None else context.resource_id,
            permission_key=context.permission_key,
            organization_id=context.organization_id,
            facility_id=context.facility_id,
            department_id=context.department_id,
            unit_id=context.unit_id,
            workspace_id=context.workspace_id,
            purpose=context.purpose,
            purpose_validated=context.purpose_validated,
            sensitivity=context.sensitivity,
            resource_status=context.resource_status,
            resource_context=resource_context or context.resource_context,
            environment=context.environment,
            break_glass=context.break_glass,
            break_glass_authorized=context.break_glass_authorized,
        )
