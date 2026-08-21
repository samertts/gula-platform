from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum


class CarePlanState(StrEnum):
    DRAFT = "draft"
    PENDING_REVIEW = "pending_review"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


_ALLOWED: dict[CarePlanState, set[CarePlanState]] = {
    CarePlanState.DRAFT: {CarePlanState.PENDING_REVIEW, CarePlanState.CANCELLED},
    CarePlanState.PENDING_REVIEW: {
        CarePlanState.ACTIVE,
        CarePlanState.DRAFT,
        CarePlanState.CANCELLED,
    },
    CarePlanState.ACTIVE: {CarePlanState.PAUSED, CarePlanState.COMPLETED, CarePlanState.CANCELLED},
    CarePlanState.PAUSED: {CarePlanState.ACTIVE, CarePlanState.COMPLETED, CarePlanState.CANCELLED},
    CarePlanState.COMPLETED: set(),
    CarePlanState.CANCELLED: set(),
}


class InvalidCarePlanTransition(ValueError):
    pass


@dataclass
class CarePlan:
    patient_id: int
    condition_code: str
    goals: list[dict]
    state: CarePlanState = CarePlanState.DRAFT
    version: int = 1
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    approved_by: int | None = None

    def transition(
        self, target: CarePlanState, *, actor_id: int, clinician_approved: bool = False
    ) -> CarePlan:
        if actor_id <= 0:
            raise InvalidCarePlanTransition("A positive actor_id is required")
        if target not in _ALLOWED[self.state]:
            raise InvalidCarePlanTransition(f"Transition {self.state} -> {target} is not allowed")
        if target == CarePlanState.ACTIVE and not clinician_approved:
            raise InvalidCarePlanTransition("A clinician approval is required before activation")
        if target == CarePlanState.ACTIVE:
            self.approved_by = actor_id
        self.state = target
        self.version += 1
        self.updated_at = datetime.now(UTC)
        return self

    def update_goals(self, goals: list[dict], *, expected_version: int) -> CarePlan:
        if expected_version != self.version:
            raise InvalidCarePlanTransition(
                "Stale care-plan version; explicit conflict resolution is required"
            )
        if self.state in {CarePlanState.COMPLETED, CarePlanState.CANCELLED}:
            raise InvalidCarePlanTransition("A terminal care plan cannot be modified")
        if not goals:
            raise InvalidCarePlanTransition("At least one measurable goal is required")
        self.goals = goals
        self.version += 1
        self.updated_at = datetime.now(UTC)
        return self
