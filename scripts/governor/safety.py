"""Phase 9 — AI Safety.

Prevent unsafe refactoring, mass file modification, silent architecture
changes, breaking API changes, unsafe dependency updates, unauthorized
knowledge changes, unauthorized deployment, and unauthorized secret access.
Require approval when needed.
"""

from __future__ import annotations

from dataclasses import dataclass

from .core import MAX_PHASE_FILES

APPROVAL_REQUIRED_ACTIONS = {
    "delete_functionality",
    "breaking_api_change",
    "unsafe_dependency_update",
    "unauthorized_knowledge_change",
    "unauthorized_deployment",
    "unauthorized_secret_access",
    "silent_architecture_change",
}

SECRET_PATTERNS = ("SECRET_KEY=", "API_KEY=", "PASSWORD=", "TOKEN=", "PRIVATE KEY")


@dataclass
class SafetyAssessment:
    """Result of a safety assessment for a proposed action."""

    action: str
    allowed: bool
    requires_approval: bool
    reason: str
    approver: str = ""


def assess_action(action: str, files_affected: int = 0, detail: str = "") -> SafetyAssessment:
    """Assess whether an AI action may proceed.

    Approval is required when the action is in the guarded set, when it would
    modify more than ``MAX_PHASE_FILES`` files in one phase, or when it
    touches secrets.
    """
    action = action.strip().lower()
    requires_approval = action in APPROVAL_REQUIRED_ACTIONS

    if files_affected > MAX_PHASE_FILES:
        return SafetyAssessment(
            action,
            allowed=False,
            requires_approval=True,
            reason=f"mass file modification: {files_affected} > {MAX_PHASE_FILES}",
        )
    if "secret" in action or any(p in detail.upper() for p in SECRET_PATTERNS):
        return SafetyAssessment(
            action,
            allowed=False,
            requires_approval=True,
            reason="unauthorized secret access or exposure",
        )
    if action in {"silent_architecture_change", "breaking_api_change"}:
        return SafetyAssessment(
            action,
            allowed=False,
            requires_approval=True,
            reason=f"{action} requires Architect approval",
            approver="architect",
        )
    if action == "unauthorized_deployment":
        return SafetyAssessment(
            action,
            allowed=False,
            requires_approval=True,
            reason="deployment requires Reviewer approval",
            approver="reviewer",
        )
    if requires_approval:
        return SafetyAssessment(
            action,
            allowed=False,
            requires_approval=True,
            reason=f"{action} requires human approval",
        )
    return SafetyAssessment(action, allowed=True, requires_approval=False,
                            reason="action is safe under the safety policy")
