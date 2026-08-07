from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class WorkflowStepExecutor(ABC):
    @abstractmethod
    async def execute(
        self,
        step_type: str,
        step_name: str,
        input_data: dict[str, Any],
        context: dict[str, Any],
    ) -> dict[str, Any]: ...

    @abstractmethod
    async def compensate(
        self,
        step_type: str,
        step_name: str,
        execution_data: dict[str, Any],
    ) -> None: ...


class WorkflowApprovalHandler(ABC):
    @abstractmethod
    async def request_approval(
        self,
        execution_id: str,
        step_id: str,
        roles: list[str],
        context: dict[str, Any],
    ) -> None: ...

    @abstractmethod
    async def approve(
        self,
        execution_id: str,
        step_id: str,
        approver_id: str,
        comments: str | None = None,
    ) -> bool: ...

    @abstractmethod
    async def reject(
        self,
        execution_id: str,
        step_id: str,
        approver_id: str,
        comments: str | None = None,
    ) -> bool: ...


class WorkflowTimerHandler(ABC):
    @abstractmethod
    async def schedule_timeout(
        self,
        execution_id: str,
        step_id: str,
        timeout_s: float,
    ) -> str: ...

    @abstractmethod
    async def cancel_timer(self, timer_id: str) -> None: ...
