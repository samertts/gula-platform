from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from backend.app.national.workflow_runtime.domain.entities import (
    SagaLog,
    WorkflowApproval,
    WorkflowCompensation,
    WorkflowDefinition,
    WorkflowExecution,
    WorkflowExecutionStep,
    WorkflowTemplate,
    WorkflowTimer,
)


class WorkflowDefinitionRepository(ABC):
    @abstractmethod
    async def save(self, definition: WorkflowDefinition) -> WorkflowDefinition: ...

    @abstractmethod
    async def get(self, definition_id: str) -> WorkflowDefinition | None: ...

    @abstractmethod
    async def list(
        self, skip: int = 0, limit: int = 100, filters: dict | None = None
    ) -> list[WorkflowDefinition]: ...

    @abstractmethod
    async def find_by_type(self, type: str) -> list[WorkflowDefinition]: ...

    @abstractmethod
    async def find_by_status(self, status: str) -> list[WorkflowDefinition]: ...

    @abstractmethod
    async def find_by_tags(self, tags: list[str]) -> list[WorkflowDefinition]: ...

    @abstractmethod
    async def find_active_version(self, type: str) -> WorkflowDefinition | None: ...

    @abstractmethod
    async def list_versions(self, type: str) -> list[WorkflowDefinition]: ...

    @abstractmethod
    async def delete(self, definition_id: str) -> bool: ...

    @abstractmethod
    async def count(self, filters: dict | None = None) -> int: ...


class WorkflowExecutionRepository(ABC):
    @abstractmethod
    async def save(self, execution: WorkflowExecution) -> WorkflowExecution: ...

    @abstractmethod
    async def get(self, execution_id: str) -> WorkflowExecution | None: ...

    @abstractmethod
    async def list(
        self, skip: int = 0, limit: int = 100, filters: dict | None = None
    ) -> list[WorkflowExecution]: ...

    @abstractmethod
    async def find_by_status(self, status: str) -> list[WorkflowExecution]: ...

    @abstractmethod
    async def find_by_trigger(self, trigger: str) -> list[WorkflowExecution]: ...

    @abstractmethod
    async def find_by_correlation_id(self, correlation_id: str) -> list[WorkflowExecution]: ...

    @abstractmethod
    async def find_stalled(self, timeout_minutes: int = 30) -> list[WorkflowExecution]: ...

    @abstractmethod
    async def get_stats(self) -> dict[str, Any]: ...

    @abstractmethod
    async def count(self, filters: dict | None = None) -> int: ...


class WorkflowExecutionStepRepository(ABC):
    @abstractmethod
    async def save(self, step: WorkflowExecutionStep) -> WorkflowExecutionStep: ...

    @abstractmethod
    async def get(self, step_id: str) -> WorkflowExecutionStep | None: ...

    @abstractmethod
    async def find_by_execution(self, execution_id: str) -> list[WorkflowExecutionStep]: ...

    @abstractmethod
    async def find_by_status(self, status: str) -> list[WorkflowExecutionStep]: ...

    @abstractmethod
    async def find_by_execution_and_step(
        self, execution_id: str, step_id: str
    ) -> WorkflowExecutionStep | None: ...


class WorkflowApprovalRepository(ABC):
    @abstractmethod
    async def save(self, approval: WorkflowApproval) -> WorkflowApproval: ...

    @abstractmethod
    async def get(self, approval_id: str) -> WorkflowApproval | None: ...

    @abstractmethod
    async def find_pending_for_user(self, user_id: str) -> list[WorkflowApproval]: ...

    @abstractmethod
    async def find_by_execution(self, execution_id: str) -> list[WorkflowApproval]: ...


class WorkflowCompensationRepository(ABC):
    @abstractmethod
    async def save(self, compensation: WorkflowCompensation) -> WorkflowCompensation: ...

    @abstractmethod
    async def get(self, compensation_id: str) -> WorkflowCompensation | None: ...

    @abstractmethod
    async def find_by_execution(self, execution_id: str) -> list[WorkflowCompensation]: ...


class WorkflowTimerRepository(ABC):
    @abstractmethod
    async def save(self, timer: WorkflowTimer) -> WorkflowTimer: ...

    @abstractmethod
    async def get(self, timer_id: str) -> WorkflowTimer | None: ...

    @abstractmethod
    async def find_due_timers(self) -> list[WorkflowTimer]: ...

    @abstractmethod
    async def find_by_execution(self, execution_id: str) -> list[WorkflowTimer]: ...


class SagaLogRepository(ABC):
    @abstractmethod
    async def save(self, log: SagaLog) -> SagaLog: ...

    @abstractmethod
    async def find_by_saga(self, saga_id: str) -> list[SagaLog]: ...

    @abstractmethod
    async def list(self, skip: int = 0, limit: int = 100) -> list[SagaLog]: ...


class WorkflowTemplateRepository(ABC):
    @abstractmethod
    async def save(self, template: WorkflowTemplate) -> WorkflowTemplate: ...

    @abstractmethod
    async def get(self, template_id: str) -> WorkflowTemplate | None: ...

    @abstractmethod
    async def list(
        self, skip: int = 0, limit: int = 100, filters: dict | None = None
    ) -> list[WorkflowTemplate]: ...

    @abstractmethod
    async def delete(self, template_id: str) -> bool: ...
