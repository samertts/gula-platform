from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from backend.app.national.task_engine.domain.entities import (
    NationalTask,
    TaskAssignment,
    TaskAuditLog,
    TaskComment,
    TaskEscalation,
    TaskQueue,
    TaskSLADefinition,
)


class NationalTaskRepository(ABC):
    @abstractmethod
    async def save(self, task: NationalTask) -> NationalTask: ...

    @abstractmethod
    async def get(self, task_id: str) -> NationalTask | None: ...

    @abstractmethod
    async def list(
        self, skip: int = 0, limit: int = 100, filters: dict | None = None,
    ) -> list[NationalTask]: ...

    @abstractmethod
    async def find_by_status(self, status: str) -> list[NationalTask]: ...

    @abstractmethod
    async def find_by_assignee(self, assignee_id: str) -> list[NationalTask]: ...

    @abstractmethod
    async def find_by_queue(self, queue_id: str) -> list[NationalTask]: ...

    @abstractmethod
    async def find_by_priority(self, priority: str) -> list[NationalTask]: ...

    @abstractmethod
    async def find_due(self, before: Any) -> list[NationalTask]: ...

    @abstractmethod
    async def find_overdue(self) -> list[NationalTask]: ...

    @abstractmethod
    async def find_escalated(self) -> list[NationalTask]: ...

    @abstractmethod
    async def count_by_status(self) -> dict[str, int]: ...

    @abstractmethod
    async def get_stats(self) -> dict[str, Any]: ...

    @abstractmethod
    async def delete(self, task_id: str) -> bool: ...

    @abstractmethod
    async def count(self, filters: dict | None = None) -> int: ...


class TaskQueueRepository(ABC):
    @abstractmethod
    async def save(self, queue: TaskQueue) -> TaskQueue: ...

    @abstractmethod
    async def get(self, queue_id: str) -> TaskQueue | None: ...

    @abstractmethod
    async def list(self) -> list[TaskQueue]: ...

    @abstractmethod
    async def delete(self, queue_id: str) -> bool: ...


class TaskAssignmentRepository(ABC):
    @abstractmethod
    async def save(self, assignment: TaskAssignment) -> TaskAssignment: ...

    @abstractmethod
    async def get(self, assignment_id: str) -> TaskAssignment | None: ...

    @abstractmethod
    async def find_by_task(self, task_id: str) -> list[TaskAssignment]: ...

    @abstractmethod
    async def find_by_assignee(self, assignee_id: str) -> list[TaskAssignment]: ...


class TaskEscalationRepository(ABC):
    @abstractmethod
    async def save(self, escalation: TaskEscalation) -> TaskEscalation: ...

    @abstractmethod
    async def get(self, escalation_id: str) -> TaskEscalation | None: ...

    @abstractmethod
    async def find_by_task(self, task_id: str) -> list[TaskEscalation]: ...

    @abstractmethod
    async def find_active(self) -> list[TaskEscalation]: ...


class TaskSLARepository(ABC):
    @abstractmethod
    async def save(self, sla: TaskSLADefinition) -> TaskSLADefinition: ...

    @abstractmethod
    async def get(self, sla_id: str) -> TaskSLADefinition | None: ...

    @abstractmethod
    async def find_by_category_and_priority(
        self, category: str, priority: str,
    ) -> TaskSLADefinition | None: ...

    @abstractmethod
    async def list(self) -> list[TaskSLADefinition]: ...


class TaskCommentRepository(ABC):
    @abstractmethod
    async def save(self, comment: TaskComment) -> TaskComment: ...

    @abstractmethod
    async def find_by_task(self, task_id: str) -> list[TaskComment]: ...


class TaskAuditLogRepository(ABC):
    @abstractmethod
    async def save(self, log: TaskAuditLog) -> TaskAuditLog: ...

    @abstractmethod
    async def find_by_task(self, task_id: str) -> list[TaskAuditLog]: ...
