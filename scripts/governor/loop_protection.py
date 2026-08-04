"""Phase 6 — Loop Protection.

Prevent infinite reviews, optimization, learning, and planning. Set maximum
retries, maximum review cycles, maximum optimization cycles, and escalate to
a human when limits are reached.
"""

from __future__ import annotations

from dataclasses import dataclass, field

MAX_LIMITS = {
    "retries": 3,
    "review_cycles": 3,
    "optimization_cycles": 3,
    "learning_cycles": 3,
    "planning_cycles": 5,
}


@dataclass
class LoopCounters:
    """Per-mission cycle counters that stop runaway loops."""

    mission_id: str
    retries: int = 0
    review_cycles: int = 0
    optimization_cycles: int = 0
    learning_cycles: int = 0
    planning_cycles: int = 0
    exceeded: list[str] = field(default_factory=list)

    def increment(self, kind: str) -> LoopCounters:
        key = f"{kind}_cycles" if kind in {
            "review", "optimization", "learning", "planning",
        } else "retries"
        setattr(self, key, getattr(self, key) + 1)
        if getattr(self, key) > MAX_LIMITS[key]:
            label = {
                "retries": "retries",
                "review_cycles": "review cycles",
                "optimization_cycles": "optimization cycles",
                "learning_cycles": "learning cycles",
                "planning_cycles": "planning cycles",
            }[key]
            if label not in self.exceeded:
                self.exceeded.append(label)
        return self

    @property
    def is_exceeded(self) -> bool:
        return bool(self.exceeded)


def escalate_message(counters: LoopCounters) -> str:
    """Build the escalation message to a human when limits are reached."""
    if not counters.exceeded:
        return ""
    return (
        f"LOOP LIMIT EXCEEDED for mission {counters.mission_id}: "
        f"{', '.join(counters.exceeded)}. Escalating to human."
    )
