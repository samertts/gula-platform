from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any

from app.national.background_platform.domain.entities import (
    JobDefinition,
    JobDependency,
    JobExecution,
    JobSchedule,
)
from app.national.background_platform.domain.enums import JobCategory, JobPriority, JobStatus


class JobRepository(ABC):
    @abstractmethod
    async def save(self, job: JobDefinition) -> JobDefinition: ...

    @abstractmethod
    async def get(self, job_id: str) -> JobDefinition | None: ...

    @abstractmethod
    async def list(
        self,
        skip: int = 0,
        limit: int = 100,
        **filters: Any,
    ) -> list[JobDefinition]: ...

    @abstractmethod
    async def delete(self, job_id: str, soft: bool = True) -> None: ...

    @abstractmethod
    async def find_by_status(
        self,
        status: JobStatus,
        skip: int = 0,
        limit: int = 100,
    ) -> list[JobDefinition]: ...

    @abstractmethod
    async def find_by_category(
        self,
        category: JobCategory,
        skip: int = 0,
        limit: int = 100,
    ) -> list[JobDefinition]: ...

    @abstractmethod
    async def find_by_priority(
        self,
        priority: JobPriority,
        skip: int = 0,
        limit: int = 100,
    ) -> list[JobDefinition]: ...

    @abstractmethod
    async def find_due(
        self,
        before: datetime | None = None,
        skip: int = 0,
        limit: int = 100,
    ) -> list[JobDefinition]: ...

    @abstractmethod
    async def count_by_status(self, status: JobStatus) -> int: ...


class JobScheduleRepository(ABC):
    @abstractmethod
    async def save(self, schedule: JobSchedule) -> JobSchedule: ...

    @abstractmethod
    async def get(self, schedule_id: str) -> JobSchedule | None: ...

    @abstractmethod
    async def list(
        self,
        skip: int = 0,
        limit: int = 100,
        **filters: Any,
    ) -> list[JobSchedule]: ...

    @abstractmethod
    async def delete(self, schedule_id: str) -> None: ...

    @abstractmethod
    async def find_due_schedules(
        self,
        before: datetime | None = None,
        skip: int = 0,
        limit: int = 100,
    ) -> list[JobSchedule]: ...

    @abstractmethod
    async def find_by_job_id(
        self,
        job_id: str,
        skip: int = 0,
        limit: int = 100,
    ) -> list[JobSchedule]: ...


class JobExecutionRepository(ABC):
    @abstractmethod
    async def save(self, execution: JobExecution) -> JobExecution: ...

    @abstractmethod
    async def get(self, execution_id: str) -> JobExecution | None: ...

    @abstractmethod
    async def list(
        self,
        skip: int = 0,
        limit: int = 100,
        **filters: Any,
    ) -> list[JobExecution]: ...

    @abstractmethod
    async def find_by_job_id(
        self,
        job_id: str,
        skip: int = 0,
        limit: int = 100,
    ) -> list[JobExecution]: ...

    @abstractmethod
    async def find_recent(
        self,
        limit: int = 50,
        status: JobStatus | None = None,
    ) -> list[JobExecution]: ...

    @abstractmethod
    async def get_stats(self) -> dict[str, Any]: ...


class JobDependencyRepository(ABC):
    @abstractmethod
    async def save(self, dependency: JobDependency) -> JobDependency: ...

    @abstractmethod
    async def get(self, dependency_id: str) -> JobDependency | None: ...

    @abstractmethod
    async def list(
        self,
        skip: int = 0,
        limit: int = 100,
        **filters: Any,
    ) -> list[JobDependency]: ...

    @abstractmethod
    async def delete(self, dependency_id: str) -> None: ...

    @abstractmethod
    async def find_by_job_id(
        self,
        job_id: str,
    ) -> list[JobDependency]: ...

    @abstractmethod
    async def find_dependents(
        self,
        depends_on_job_id: str,
    ) -> list[JobDependency]: ...
