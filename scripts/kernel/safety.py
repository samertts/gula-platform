"""Phase 10 — Safety Engine.

Prevent infinite loops, infinite reviews, infinite optimizations, infinite
retries, architecture violations, security violations, mass modifications,
unsafe refactoring, dangerous commands, unauthorized deployments, and
unauthorized knowledge updates. Builds on the Governor's safety (Phase 9) and
loop protection (Phase 6) without duplicating their models.
"""

from __future__ import annotations

from dataclasses import dataclass

from scripts.governor.loop_protection import LoopCounters, escalate_message
from scripts.governor.safety import SECRET_PATTERNS
from scripts.governor.safety import assess_action as governor_assess

from .core import MAX_PHASE_FILES

# Commands that are never executed, regardless of approval (deny-first).
DENIED_COMMANDS: tuple[str, ...] = (
    "rm -rf /",
    "mkfs",
    "dd if=",
    "git push --force",
    "git push -f",
    "DROP DATABASE",
    "DROP TABLE",
    "ALTER TABLE ... DROP",
    "chmod 777 /",
)

# Safety-sensitive action kinds (reused from the Governor plus Kernel terms).
UNSAFE_ACTIONS: set[str] = {
    "delete_functionality",
    "breaking_api_change",
    "unsafe_dependency_update",
    "unauthorized_knowledge_change",
    "unauthorized_deployment",
    "unauthorized_secret_access",
    "silent_architecture_change",
    "unsafe_refactoring",
    "mass_modification",
    "dangerous_command",
}


@dataclass
class SafetyAssessment:
    """Combined safety assessment for a proposed action."""

    action: str
    allowed: bool
    requires_approval: bool
    reason: str
    approver: str = ""


def assess_command(command: str) -> SafetyAssessment:
    """Deny dangerous commands outright."""
    normalized = " ".join(command.lower().split())
    for denied in DENIED_COMMANDS:
        if denied.lower() in normalized:
            return SafetyAssessment(
                action="dangerous_command",
                allowed=False,
                requires_approval=False,
                reason=f"command denied by policy: {denied}",
            )
    return SafetyAssessment(
        action="command",
        allowed=True,
        requires_approval=False,
        reason="command is not in the deny list",
    )


def assess_action(
    action: str,
    files_affected: int = 0,
    detail: str = "",
    counters: LoopCounters | None = None,
) -> SafetyAssessment:
    """Assess a proposed action with Governor safety + Kernel loop rules."""
    if any(secret in detail.upper() for secret in SECRET_PATTERNS):
        return SafetyAssessment(
            action=action,
            allowed=False,
            requires_approval=True,
            reason="secret exposure risk",
        )

    if files_affected > MAX_PHASE_FILES:
        return SafetyAssessment(
            action=action,
            allowed=False,
            requires_approval=True,
            reason=f"mass modification: {files_affected} files > {MAX_PHASE_FILES}",
        )

    if counters is not None and counters.is_exceeded:
        return SafetyAssessment(
            action=action,
            allowed=False,
            requires_approval=True,
            reason=escalate_message(counters) or "loop limit exceeded",
            approver="governor",
        )

    governor = governor_assess(action, files_affected, detail)
    if action in UNSAFE_ACTIONS or governor.requires_approval:
        return SafetyAssessment(
            action=action,
            allowed=False,
            requires_approval=True,
            reason=governor.reason or f"{action} requires approval",
            approver=governor.approver,
        )
    return SafetyAssessment(
        action=action,
        allowed=True,
        requires_approval=False,
        reason=governor.reason,
    )


def check_loops(counters: LoopCounters) -> list[str]:
    """Report which loop limits have been exceeded (infinite-loop guard)."""
    return list(counters.exceeded)


def check_mass_modification(files_modified: int) -> SafetyAssessment:
    if files_modified > MAX_PHASE_FILES:
        return SafetyAssessment(
            action="mass_modification",
            allowed=False,
            requires_approval=True,
            reason=f"{files_modified} files exceeds phase budget {MAX_PHASE_FILES}",
        )
    return SafetyAssessment(action="mass_modification", allowed=True,
                            requires_approval=False, reason="within phase budget")


def check_unauthorized_deployment(reviewer_approved: bool) -> SafetyAssessment:
    if not reviewer_approved:
        return SafetyAssessment(
            action="unauthorized_deployment",
            allowed=False,
            requires_approval=True,
            reason="deployment requires Reviewer approval",
            approver="reviewer",
        )
    return SafetyAssessment(action="deployment", allowed=True,
                            requires_approval=False, reason="deployment approved")


def check_unauthorized_knowledge_update(governor_approved: bool) -> SafetyAssessment:
    if not governor_approved:
        return SafetyAssessment(
            action="unauthorized_knowledge_change",
            allowed=False,
            requires_approval=True,
            reason="knowledge update requires Governor approval",
            approver="governor",
        )
    return SafetyAssessment(action="knowledge_update", allowed=True,
                            requires_approval=False, reason="knowledge update approved")


def check_architecture_violation(architect_approved: bool) -> SafetyAssessment:
    if not architect_approved:
        return SafetyAssessment(
            action="silent_architecture_change",
            allowed=False,
            requires_approval=True,
            reason="architecture change requires Architect approval",
            approver="architect",
        )
    return SafetyAssessment(action="architecture_change", allowed=True,
                            requires_approval=False, reason="architecture approved")


def safety_preflight(
    action: str,
    files_affected: int = 0,
    detail: str = "",
    counters: LoopCounters | None = None,
) -> list[SafetyAssessment]:
    """Run the full safety preflight and return every blocking assessment."""
    results = [
        assess_command(detail),
        assess_action(action, files_affected, detail, counters),
    ]
    return [r for r in results if not r.allowed]
