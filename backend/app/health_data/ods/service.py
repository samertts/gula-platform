from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any

from app._compat import UTC

logger = logging.getLogger("gula.health_data.ods.service")


class ODSRefreshPolicy(Enum):
    REALTIME = "realtime"
    EVERY_MINUTE = "every_minute"
    EVERY_5_MINUTES = "every_5_minutes"
    EVERY_15_MINUTES = "every_15_minutes"
    EVERY_HOUR = "every_hour"
    DAILY = "daily"
    MANUAL = "manual"


@dataclass
class ODSRefreshResult:
    entity_type: str
    rows_refreshed: int
    duration_ms: float
    error: str | None = None
    refreshed_at: datetime = field(default_factory=lambda: datetime.now(UTC))


class ODSService:
    def __init__(self):
        self._materialized: dict[str, list[dict[str, Any]]] = {}
        self._refresh_policies: dict[str, ODSRefreshPolicy] = {}
        self._last_refresh: dict[str, datetime] = {}

    def register_view(self, name: str, policy: ODSRefreshPolicy = ODSRefreshPolicy.MANUAL) -> None:
        self._refresh_policies[name] = policy
        self._materialized[name] = []
        logger.info("ODS view registered: %s (policy=%s)", name, policy.value)

    def unregister_view(self, name: str) -> None:
        self._refresh_policies.pop(name, None)
        self._materialized.pop(name, None)

    def set_data(self, view_name: str, data: list[dict[str, Any]]) -> None:
        self._materialized[view_name] = data
        self._last_refresh[view_name] = datetime.now(UTC)

    def get_data(self, view_name: str) -> list[dict[str, Any]]:
        return self._materialized.get(view_name, [])

    def query(
        self,
        view_name: str,
        filters: dict[str, Any] | None = None,
        sort_by: str | None = None,
        sort_desc: bool = False,
        limit: int = 100,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        data = self.get_data(view_name)

        if filters:
            filtered = []
            for row in data:
                match = True
                for key, value in filters.items():
                    if key not in row or row[key] != value:
                        match = False
                        break
                if match:
                    filtered.append(row)
            data = filtered

        if sort_by:
            data = sorted(data, key=lambda r: r.get(sort_by, ""), reverse=sort_desc)

        return data[offset : offset + limit]

    async def refresh(
        self,
        view_name: str,
        source_fn: Any = None,
    ) -> ODSRefreshResult:
        import time

        start = time.monotonic()

        if not source_fn:
            logger.warning("No source function provided for ODS view: %s", view_name)
            return ODSRefreshResult(entity_type=view_name, rows_refreshed=0, duration_ms=0)

        try:
            if asyncio.iscoroutinefunction(source_fn):
                data = await source_fn()
            else:
                data = source_fn()

            self.set_data(view_name, data)
            duration = (time.monotonic() - start) * 1000

            logger.info(
                "ODS view refreshed: %s (%d rows) in %.1fms", view_name, len(data), duration
            )
            return ODSRefreshResult(
                entity_type=view_name,
                rows_refreshed=len(data),
                duration_ms=round(duration, 1),
            )
        except Exception as exc:
            duration = (time.monotonic() - start) * 1000
            logger.error("ODS view refresh failed: %s: %s", view_name, exc)
            return ODSRefreshResult(
                entity_type=view_name,
                rows_refreshed=0,
                duration_ms=round(duration, 1),
                error=str(exc),
            )

    def get_policy(self, view_name: str) -> ODSRefreshPolicy | None:
        return self._refresh_policies.get(view_name)

    def needs_refresh(self, view_name: str) -> bool:
        policy = self.get_policy(view_name)
        if not policy or policy == ODSRefreshPolicy.MANUAL:
            return False

        last = self._last_refresh.get(view_name)
        if not last:
            return True

        elapsed = datetime.now(UTC) - last
        thresholds = {
            ODSRefreshPolicy.REALTIME: timedelta(seconds=5),
            ODSRefreshPolicy.EVERY_MINUTE: timedelta(minutes=1),
            ODSRefreshPolicy.EVERY_5_MINUTES: timedelta(minutes=5),
            ODSRefreshPolicy.EVERY_15_MINUTES: timedelta(minutes=15),
            ODSRefreshPolicy.EVERY_HOUR: timedelta(hours=1),
            ODSRefreshPolicy.DAILY: timedelta(days=1),
        }
        return elapsed >= thresholds.get(policy, timedelta(hours=1))
