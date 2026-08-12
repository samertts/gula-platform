from __future__ import annotations

import logging
import os
import time
from collections.abc import Generator
from contextlib import contextmanager
from dataclasses import dataclass, field
from threading import Lock
from typing import Any

from app.kernel.exceptions import KernelError

logger = logging.getLogger("gula.kernel.resource_manager")


@dataclass
class ResourceLimits:
    max_cpu_percent: float = 80.0
    max_memory_mb: float = 512.0
    max_threads: int = 100
    max_connections: int = 50
    max_file_descriptors: int = 1024
    max_gpu_vram_mb: float = 0.0
    max_storage_mb: float = 1024.0
    max_network_bandwidth_mbps: float = 100.0


@dataclass
class ResourceUsage:
    cpu_percent: float = 0.0
    memory_mb: float = 0.0
    threads: int = 0
    connections: int = 0
    file_descriptors: int = 0
    gpu_vram_mb: float = 0.0
    storage_mb: float = 0.0
    network_bandwidth_mbps: float = 0.0

    @property
    def summary(self) -> dict[str, Any]:
        return {
            "cpu_percent": round(self.cpu_percent, 1),
            "memory_mb": round(self.memory_mb, 1),
            "threads": self.threads,
            "connections": self.connections,
        }


@dataclass
class ResourceMetrics:
    timestamp: float = field(default_factory=time.time)
    usage: ResourceUsage = field(default_factory=ResourceUsage)
    limits: ResourceLimits = field(default_factory=ResourceLimits)
    utilization_percent: dict[str, float] = field(default_factory=dict)

    def compute_utilization(self) -> dict[str, float]:
        result = {}
        if self.limits.max_cpu_percent > 0:
            result["cpu"] = round((self.usage.cpu_percent / self.limits.max_cpu_percent) * 100, 1)
        if self.limits.max_memory_mb > 0:
            result["memory"] = round((self.usage.memory_mb / self.limits.max_memory_mb) * 100, 1)
        if self.limits.max_threads > 0:
            result["threads"] = round((self.usage.threads / self.limits.max_threads) * 100, 1)
        if self.limits.max_gpu_vram_mb > 0:
            result["gpu_vram"] = round((self.usage.gpu_vram_mb / self.limits.max_gpu_vram_mb) * 100, 1)
        self.utilization_percent = result
        return result

    def is_critical(self) -> bool:
        util = self.compute_utilization()
        return any(v > 90.0 for v in util.values())


class ResourcePool:
    def __init__(
        self,
        name: str,
        min_size: int = 1,
        max_size: int = 10,
        target_size: int = 5,
        idle_timeout: float = 300.0,
    ):
        self.name = name
        self.min_size = min_size
        self.max_size = max_size
        self.target_size = target_size
        self.idle_timeout = idle_timeout
        self._pool: list[Any] = []
        self._in_use: int = 0
        self._lock = Lock()
        self._created_count: int = 0
        self._hit_count: int = 0
        self._miss_count: int = 0

    @property
    def available(self) -> int:
        return len(self._pool)

    @property
    def in_use(self) -> int:
        return self._in_use

    @property
    def total(self) -> int:
        return self.available + self.in_use

    def acquire(self) -> Any | None:
        with self._lock:
            if self._pool:
                self._in_use += 1
                self._hit_count += 1
                return self._pool.pop()
        self._miss_count += 1
        return None

    def release(self, resource: Any) -> None:
        with self._lock:
            if self.total < self.max_size:
                self._pool.append(resource)
            self._in_use = max(0, self._in_use - 1)

    @contextmanager
    def use(self) -> Generator[Any | None]:
        resource = self.acquire()
        try:
            yield resource
        finally:
            self.release(resource) if resource else None

    def resize(self, new_target: int) -> None:
        new_target = max(self.min_size, min(self.max_size, new_target))
        self.target_size = new_target
        logger.info("Pool resized", extra={"pool": self.name, "target": new_target})

    def health(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "available": self.available,
            "in_use": self.in_use,
            "total": self.total,
            "min_size": self.min_size,
            "max_size": self.max_size,
            "target_size": self.target_size,
            "hit_rate": round(self._hit_count / max(1, self._hit_count + self._miss_count) * 100, 1),
            "healthy": self.total <= self.max_size,
        }


class ResourceManager:
    def __init__(self):
        self._pools: dict[str, ResourcePool] = {}
        self._limits = ResourceLimits()
        self._lock = Lock()
        self._allocation_history: list[dict[str, Any]] = []

    @property
    def limits(self) -> ResourceLimits:
        return self._limits

    def set_limits(self, limits: ResourceLimits) -> None:
        self._limits = limits
        logger.info("Resource limits updated", extra={"limits": limits.__dict__})

    def create_pool(
        self,
        name: str,
        min_size: int = 1,
        max_size: int = 10,
        target_size: int = 5,
    ) -> ResourcePool:
        with self._lock:
            if name in self._pools:
                raise KernelError(f"Pool already exists: {name}")
            pool = ResourcePool(name, min_size, max_size, target_size)
            self._pools[name] = pool
            logger.info("Pool created", extra={"pool": name, "max": max_size})
            return pool

    def get_pool(self, name: str) -> ResourcePool | None:
        return self._pools.get(name)

    def remove_pool(self, name: str) -> bool:
        with self._lock:
            if name in self._pools:
                del self._pools[name]
                return True
        return False

    def list_pools(self) -> list[ResourcePool]:
        return list(self._pools.values())

    def collect_metrics(self) -> ResourceMetrics:
        try:
            import psutil
            process = psutil.Process(os.getpid())
            usage = ResourceUsage(
                cpu_percent=process.cpu_percent(interval=0.1),
                memory_mb=process.memory_info().rss / (1024 * 1024),
                threads=process.num_threads(),
                file_descriptors=process.num_fds(),
            )
        except (ImportError, AttributeError):
            usage = ResourceUsage()

        metrics = ResourceMetrics(usage=usage, limits=self._limits)
        metrics.compute_utilization()
        return metrics

    def track_allocation(self, resource_type: str, amount: float, tenant_id: str = "") -> None:
        record = {
            "timestamp": time.time(),
            "type": resource_type,
            "amount": amount,
            "tenant_id": tenant_id,
        }
        self._allocation_history.append(record)
        if len(self._allocation_history) > 1000:
            self._allocation_history.pop(0)

    def get_diagnostics(self) -> dict[str, Any]:
        metrics = self.collect_metrics()
        pool_health = {name: pool.health() for name, pool in self._pools.items()}
        return {
            "metrics": {
                "usage": metrics.usage.__dict__,
                "utilization": metrics.utilization_percent,
                "critical": metrics.is_critical(),
            },
            "pools": pool_health,
            "total_pools": len(self._pools),
            "recent_allocations": len(self._allocation_history),
        }
