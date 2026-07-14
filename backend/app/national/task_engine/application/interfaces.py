from __future__ import annotations

import random
from abc import ABC, abstractmethod
from typing import Any


class AssignmentEngine(ABC):
    @abstractmethod
    async def assign(self, task: Any, candidates: list[str], context: dict | None = None) -> str | None: ...


class RoundRobinAssigner(AssignmentEngine):
    def __init__(self) -> None:
        self._index: dict[str, int] = {}

    async def assign(self, task: Any, candidates: list[str], context: dict | None = None) -> str | None:
        if not candidates:
            return None
        queue_id = task.queue_id or "default"
        idx = self._index.get(queue_id, 0)
        assignee = candidates[idx % len(candidates)]
        self._index[queue_id] = idx + 1
        return assignee


class LeastBusyAssigner(AssignmentEngine):
    async def assign(self, task: Any, candidates: list[str], context: dict | None = None) -> str | None:
        if not candidates:
            return None
        return candidates[0]


class SkillBasedAssigner(AssignmentEngine):
    async def assign(self, task: Any, candidates: list[str], context: dict | None = None) -> str | None:
        if not candidates:
            return None
        return candidates[0] if candidates else None


class LoadBalancedAssigner(AssignmentEngine):
    async def assign(self, task: Any, candidates: list[str], context: dict | None = None) -> str | None:
        if not candidates:
            return None
        return random.choice(candidates)


class SLAEngine(ABC):
    @abstractmethod
    async def calculate_sla_status(self, task: Any) -> str: ...

    @abstractmethod
    async def check_sla(self, sla_def: Any, task: Any) -> bool: ...


class KPIEngine(ABC):
    @abstractmethod
    async def calculate(self, tasks: list[Any]) -> dict[str, Any]: ...


class SimpleKPIEngine(KPIEngine):
    async def calculate(self, tasks: list[Any]) -> dict[str, Any]:
        total = len(tasks)
        completed = sum(1 for t in tasks if t.status.value == "completed")
        failed = sum(1 for t in tasks if t.status.value == "failed")
        overdue = sum(1 for t in tasks if t.is_overdue)
        avg_duration = 0.0
        durations = [
            (t.completed_at - t.started_at).total_seconds()
            for t in tasks if t.completed_at and t.started_at
        ]
        if durations:
            avg_duration = sum(durations) / len(durations)
        return {
            "total": total,
            "completed": completed,
            "failed": failed,
            "overdue": overdue,
            "completion_rate": round(completed / total * 100, 2) if total else 0.0,
            "avg_duration_s": round(avg_duration, 2),
            "overdue_rate": round(overdue / total * 100, 2) if total else 0.0,
        }
