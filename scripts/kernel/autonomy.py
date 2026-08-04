"""Phase 2 — Autonomy Engine.

Implement autonomy levels L0 (read only) through L8 (dangerous operations).
Higher autonomy levels require human approval. The current autonomy level
gates every action an AI Engine may take without approval.
"""

from __future__ import annotations

from dataclasses import dataclass

from .core import AUTONOMY_LEVELS, AUTONOMY_NAMES

# Action -> minimum autonomy level required to perform it without approval.
ACTION_REQUIREMENTS: dict[str, str] = {
    "read": "L0",
    "analyze": "L1",
    "analyze_and_analyze": "L1",
    "suggest": "L2",
    "modify_workspace": "L3",
    "write_file": "L3",
    "edit_file": "L3",
    "create_file": "L3",
    "commit": "L4",
    "push": "L4",
    "pull_request": "L5",
    "deploy_staging": "L6",
    "deploy_production": "L7",
    "dangerous_operation": "L8",
}

# Actions that always require approval even at the maximum autonomy level.
ALWAYS_APPROVE: set[str] = {
    "delete_functionality",
    "drop_database",
    "expose_credentials",
    "change_license",
    "dangerous_operation",
    "deploy_production",
}


@dataclass
class AutonomyAssessment:
    """Result of an autonomy check for an action."""

    action: str
    required_level: str
    current_level: str
    allowed: bool
    requires_approval: bool
    reason: str


def level_index(level: str) -> int:
    """Return the numeric index of an autonomy level (0..8)."""
    level = level.strip().upper()
    if level not in AUTONOMY_LEVELS:
        raise ValueError(f"Unknown autonomy level '{level}'; expected one of {AUTONOMY_LEVELS}")
    return AUTONOMY_LEVELS.index(level)


def required_level(action: str) -> str:
    """Return the minimum autonomy level required for an action."""
    return ACTION_REQUIREMENTS.get(action.strip().lower(), "L8")


def assess(action: str, current_level: str, details: str = "") -> AutonomyAssessment:
    """Assess whether an action is allowed at the current autonomy level.

    An action is allowed when the current level is at least the required
    level, unless the action always requires human approval.
    """
    action = action.strip().lower()
    required = required_level(action)
    cur = current_level.strip().upper()
    try:
        cur_index = level_index(cur)
        req_index = level_index(required)
    except ValueError as exc:  # pragma: no cover - input guard
        raise ValueError(str(exc)) from exc

    needs_approval = action in ALWAYS_APPROVE
    allowed = cur_index >= req_index and not needs_approval
    reason = (
        "requires approval at all autonomy levels"
        if needs_approval
        else f"requires {required} ({AUTONOMY_NAMES[required]}); current {cur} ({AUTONOMY_NAMES[cur]})"
    )
    return AutonomyAssessment(
        action=action,
        required_level=required,
        current_level=cur,
        allowed=allowed,
        requires_approval=needs_approval or not allowed,
        reason=reason,
    )


def max_autonomous_level() -> str:
    """The highest level an engine may reach without human approval."""
    return "L5"


def approve(current_level: str) -> str:
    """Raise the autonomy level by one step (approval granted)."""
    idx = level_index(current_level)
    if idx >= len(AUTONOMY_LEVELS) - 1:
        return AUTONOMY_LEVELS[-1]
    return AUTONOMY_LEVELS[idx + 1]


def revoke(current_level: str) -> str:
    """Lower the autonomy level by one step (restriction)."""
    idx = level_index(current_level)
    if idx <= 0:
        return AUTONOMY_LEVELS[0]
    return AUTONOMY_LEVELS[idx - 1]
