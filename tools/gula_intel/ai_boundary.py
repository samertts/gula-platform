"""Optional AI adapter boundary — contract only, no provider.

The deterministic core produces structured context.  An AI layer may later
consume that context to explain, summarise, prioritise or propose.  It may
never decide.  Nothing in this module imports or calls a model.
"""
from __future__ import annotations

from typing import Any

# Capabilities an adapter may offer.
ALLOWED = frozenset({"explain", "summarize", "prioritize", "propose"})

# Decisions that remain deterministic forever.  An adapter asserting any of
# these is rejected rather than trusted.
FORBIDDEN = frozenset(
    {
        "authorize_user",
        "determine_clinical_truth",
        "determine_database_truth",
        "bypass_validation",
        "approve_migration",
        "mark_finding_verified",
        "override_security_rule",
        "override_state_machine",
        "decide_production_readiness",
    }
)


class AdapterViolation(RuntimeError):
    """Raised when an adapter attempts a decision reserved for the core."""


def assert_capability(capability: str) -> None:
    if capability in FORBIDDEN:
        raise AdapterViolation(
            f"'{capability}' is a deterministic decision and can never be delegated to AI"
        )
    if capability not in ALLOWED:
        raise AdapterViolation(f"unknown adapter capability '{capability}'")


def build_context(results: list[Any], inventory_summary: dict[str, Any]) -> dict[str, Any]:
    """Structured, already-decided facts an adapter may describe but not alter."""
    return {
        "inventory": inventory_summary,
        "checks": [r.to_dict() for r in results],
        "contract": {
            "allowed": sorted(ALLOWED),
            "forbidden": sorted(FORBIDDEN),
            "note": "Statuses are computed deterministically; an adapter may only render them.",
        },
    }
