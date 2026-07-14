from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any

from app.national.observability.domain.entities import (
    AlertEvent,
    AlertRule,
    Dashboard,
    DashboardPanel,
    HealthCheck,
    MetricPoint,
    ServiceGraph,
    TraceSpan,
)
from app.national.observability.domain.enums import AlertSeverity, AlertStatus


class MetricRepository(ABC):

    @abstractmethod
    async def save(self, metric: MetricPoint) -> MetricPoint: ...

    @abstractmethod
    async def save_many(self, metrics: list[MetricPoint]) -> list[MetricPoint]: ...

    @abstractmethod
    async def query(
        self,
        name: str | None = None,
        tags: dict[str, str] | None = None,
        from_time: datetime | None = None,
        to_time: datetime | None = None,
        aggregate: str = "avg",
        group_by: list[str] | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]: ...

    @abstractmethod
    async def get_stats(self) -> dict[str, Any]: ...

    @abstractmethod
    async def get_metric_names(self) -> list[str]: ...


class TraceSpanRepository(ABC):

    @abstractmethod
    async def save(self, span: TraceSpan) -> TraceSpan: ...

    @abstractmethod
    async def get(self, span_id: str) -> TraceSpan | None: ...

    @abstractmethod
    async def find_by_trace(self, trace_id: str) -> list[TraceSpan]: ...

    @abstractmethod
    async def search(
        self,
        service: str | None = None,
        operation: str | None = None,
        min_duration: float | None = None,
        max_duration: float | None = None,
        from_time: datetime | None = None,
        to_time: datetime | None = None,
        status: str | None = None,
        skip: int = 0,
        limit: int = 100,
    ) -> list[TraceSpan]: ...

    @abstractmethod
    async def get_stats(self) -> dict[str, Any]: ...


class HealthCheckRepository(ABC):

    @abstractmethod
    async def save(self, check: HealthCheck) -> HealthCheck: ...

    @abstractmethod
    async def get(self, check_id: str) -> HealthCheck | None: ...

    @abstractmethod
    async def list(self) -> list[HealthCheck]: ...

    @abstractmethod
    async def find_by_name(self, name: str) -> HealthCheck | None: ...

    @abstractmethod
    async def get_overall_status(self) -> dict[str, Any]: ...


class AlertRuleRepository(ABC):

    @abstractmethod
    async def save(self, rule: AlertRule) -> AlertRule: ...

    @abstractmethod
    async def get(self, rule_id: str) -> AlertRule | None: ...

    @abstractmethod
    async def list(
        self,
        skip: int = 0,
        limit: int = 100,
    ) -> list[AlertRule]: ...

    @abstractmethod
    async def delete(self, rule_id: str) -> None: ...

    @abstractmethod
    async def find_enabled(self) -> list[AlertRule]: ...


class AlertEventRepository(ABC):

    @abstractmethod
    async def save(self, event: AlertEvent) -> AlertEvent: ...

    @abstractmethod
    async def get(self, event_id: str) -> AlertEvent | None: ...

    @abstractmethod
    async def list(
        self,
        status: AlertStatus | None = None,
        severity: AlertSeverity | None = None,
        rule_id: str | None = None,
        skip: int = 0,
        limit: int = 100,
    ) -> list[AlertEvent]: ...

    @abstractmethod
    async def find_firing(self) -> list[AlertEvent]: ...

    @abstractmethod
    async def get_active_count_by_severity(self) -> dict[str, int]: ...


class DashboardRepository(ABC):

    @abstractmethod
    async def save(self, dashboard: Dashboard) -> Dashboard: ...

    @abstractmethod
    async def get(self, dashboard_id: str) -> Dashboard | None: ...

    @abstractmethod
    async def list(
        self,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Dashboard]: ...

    @abstractmethod
    async def delete(self, dashboard_id: str) -> None: ...


class DashboardPanelRepository(ABC):

    @abstractmethod
    async def save(self, panel: DashboardPanel) -> DashboardPanel: ...

    @abstractmethod
    async def save_many(self, panels: list[DashboardPanel]) -> list[DashboardPanel]: ...

    @abstractmethod
    async def find_by_dashboard(self, dashboard_id: str) -> list[DashboardPanel]: ...

    @abstractmethod
    async def delete_by_dashboard(self, dashboard_id: str) -> None: ...


class ServiceGraphRepository(ABC):

    @abstractmethod
    async def save(self, graph: ServiceGraph) -> ServiceGraph: ...

    @abstractmethod
    async def get(self, service_name: str) -> ServiceGraph | None: ...

    @abstractmethod
    async def list(self) -> list[ServiceGraph]: ...

    @abstractmethod
    async def delete(self, service_name: str) -> None: ...
