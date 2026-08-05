"""GULA-KERNEL-EXT-001 Phase 4 — Migration Framework.

Versioned, reversible migrations for knowledge, policies, plugins,
registry entries, and config. Every migration is a plan with prechecks,
forward steps, and rollback steps; execution is audited and persisted.
Rollback semantics follow the Kernel recovery layer (scripts/kernel/
recovery.py) — this module orchestrates, it does not re-implement retry.
"""

from __future__ import annotations

import json
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from ..core import utcnow
from .compatibility import is_breaking_change

MIGRATION_DIR = ".ai/core/migrations/"

MIGRATION_TARGETS = ("knowledge", "policy", "plugin", "registry", "config")
MIGRATION_STATES = ("planned", "approved", "executed", "failed", "rolled_back")

StepFn = Callable[[], None]


class MigrationError(Exception):
    """Raised for invalid migration inputs or failed execution."""


@dataclass
class MigrationStep:
    """One forward or rollback step of a migration plan."""

    description: str
    fn: StepFn


@dataclass
class MigrationPlan:
    """A versioned, reversible migration between two versions."""

    id: str
    title: str
    target: str
    from_version: str
    to_version: str
    steps: list[MigrationStep]
    rollback_steps: list[MigrationStep] = field(default_factory=list)
    precheck: StepFn | None = None
    state: str = "planned"
    created_at: str = field(default_factory=utcnow)
    executed_at: str = ""
    notes: str = ""

    def __post_init__(self) -> None:
        if not self.id.startswith("MIGR-"):
            raise MigrationError(f"migration id must start with MIGR-: {self.id!r}")
        if self.target not in MIGRATION_TARGETS:
            raise MigrationError(f"unknown target: {self.target!r}")
        if self.state not in MIGRATION_STATES:
            raise MigrationError(f"unknown state: {self.state!r}")

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "target": self.target,
            "from_version": self.from_version,
            "to_version": self.to_version,
            "state": self.state,
            "created_at": self.created_at,
            "executed_at": self.executed_at,
            "notes": self.notes,
        }


class MigrationEngine:
    """Registers, executes, and rolls back migration plans."""

    def __init__(self) -> None:
        self._plans: dict[str, MigrationPlan] = {}
        self._history: list[dict[str, Any]] = []

    def register(self, plan: MigrationPlan) -> MigrationPlan:
        if plan.id in self._plans:
            raise MigrationError(f"migration already registered: {plan.id}")
        self._plans[plan.id] = plan
        self._history.append({"event": "registered", "id": plan.id, "at": utcnow()})
        return plan

    def get(self, plan_id: str) -> MigrationPlan:
        try:
            return self._plans[plan_id]
        except KeyError:
            raise MigrationError(f"unknown migration: {plan_id}") from None

    def plans(self, state: str | None = None) -> list[MigrationPlan]:
        if state is None:
            return list(self._plans.values())
        return [p for p in self._plans.values() if p.state == state]

    def execute(self, plan_id: str) -> MigrationPlan:
        plan = self.get(plan_id)
        if plan.state not in {"planned", "approved"}:
            raise MigrationError(
                f"migration {plan_id} cannot execute from state {plan.state!r}"
            )
        try:
            if plan.precheck is not None:
                plan.precheck()
            for step in plan.steps:
                step.fn()
        except Exception as exc:
            plan.state = "failed"
            self._history.append({"event": "failed", "id": plan.id, "at": utcnow(), "detail": str(exc)})
            self.rollback(plan_id)
            raise MigrationError(f"migration {plan_id} failed: {exc}") from exc
        plan.state = "executed"
        plan.executed_at = utcnow()
        self._history.append({"event": "executed", "id": plan.id, "at": plan.executed_at})
        return plan

    def rollback(self, plan_id: str) -> MigrationPlan:
        plan = self.get(plan_id)
        if not plan.rollback_steps:
            raise MigrationError(f"migration {plan_id} has no rollback steps")
        for step in plan.rollback_steps:
            step.fn()
        plan.state = "rolled_back"
        self._history.append({"event": "rolled_back", "id": plan.id, "at": utcnow()})
        return plan

    def is_breaking(self, plan_id: str) -> bool:
        plan = self.get(plan_id)
        return is_breaking_change(plan.from_version, plan.to_version)

    def snapshot(self) -> dict[str, Any]:
        return {
            "schema_version": "1.0.0",
            "plans": [p.to_dict() for p in self._plans.values()],
            "history": list(self._history),
        }

    def save(self, path: str | Path) -> Path:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(self.snapshot(), indent=2) + "\n", encoding="utf-8")
        return path


def _demo_plan() -> MigrationPlan:
    """Deterministic in-memory demo migration used by the CLI and tests."""

    state: dict[str, Any] = {"schema_version": "1.0.0"}

    def forward() -> None:
        state["schema_version"] = "1.0.1"

    def backward() -> None:
        state["schema_version"] = "1.0.0"

    return MigrationPlan(
        id="MIGR-000001",
        title="demo policy catalog schema bump",
        target="policy",
        from_version="1.0.0",
        to_version="1.0.1",
        steps=[MigrationStep("bump schema_version to 1.0.1", forward)],
        rollback_steps=[MigrationStep("restore schema_version to 1.0.0", backward)],
        precheck=lambda: None,
        notes="CLI demo; state is in-memory, never touches real artifacts",
    )
