from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import Any

from app._compat import UTC
from app.national.background_platform.domain.entities import JobDefinition, JobExecution


class JobExecutor(ABC):

    @abstractmethod
    async def execute(self, job: JobDefinition, execution: JobExecution) -> dict[str, Any]: ...

    @abstractmethod
    async def cancel(self, job: JobDefinition, execution: JobExecution) -> None: ...

    @abstractmethod
    async def can_execute(self, job: JobDefinition) -> bool: ...


class ScheduleCalculator(ABC):

    @abstractmethod
    def calculate_next_run(
        self,
        cron_expression: str,
        after: datetime | None = None,
    ) -> datetime: ...

    @abstractmethod
    def validate_expression(self, expression: str) -> bool: ...


class SimpleScheduleCalculator(ScheduleCalculator):

    def calculate_next_run(
        self,
        cron_expression: str,
        after: datetime | None = None,
    ) -> datetime:
        base = after or datetime.now(UTC)
        return base + timedelta(minutes=5)

    def validate_expression(self, expression: str) -> bool:
        try:
            parts = expression.strip().split()
            if len(parts) != 5:
                return False
            return all(part.strip() for part in parts)
        except Exception:
            return False
