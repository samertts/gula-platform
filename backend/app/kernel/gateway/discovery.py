from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from app.kernel.gateway.circuit_breaker import CircuitBreakerManager
from app.kernel.gateway.health_routing import HealthRouter
from app.kernel.gateway.rate_limiting import RateLimiter
from app.kernel.gateway.routing import InternalRouter
from app.kernel.gateway.validation import RequestValidator

if TYPE_CHECKING:
    from app.kernel import Kernel

logger = logging.getLogger("gula.kernel.gateway")


@dataclass
class ServiceEndpoint:
    name: str
    host: str
    port: int
    protocol: str = "http"
    health_path: str = "/health"
    metadata: dict = field(default_factory=dict)


class ServiceDiscovery:
    def __init__(self, kernel: Kernel):
        self.kernel = kernel
        self._services: dict[str, ServiceEndpoint] = {}
        self.router = InternalRouter()
        self.health_router = HealthRouter()
        self.circuit_breaker = CircuitBreakerManager()
        self.rate_limiter = RateLimiter()
        self.validator = RequestValidator()

    def register(self, endpoint: ServiceEndpoint) -> None:
        self._services[endpoint.name] = endpoint

    def unregister(self, name: str) -> None:
        self._services.pop(name, None)

    def discover(self, name: str) -> ServiceEndpoint | None:
        return self._services.get(name)

    def list_services(self) -> list[ServiceEndpoint]:
        return list(self._services.values())
