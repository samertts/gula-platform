from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from app._compat import UTC
from app.kernel.gateway.discovery import ServiceDiscovery, ServiceEndpoint
from app.kernel.integration import get_kernel

logger = logging.getLogger("gula.control_plane.service_manager")


@dataclass
class ServiceDescriptor:
    name: str
    version: str
    host: str = "localhost"
    port: int = 0
    protocol: str = "http"
    health_path: str = "/health"
    dependencies: list[str] = field(default_factory=list)
    status: str = "registered"
    metadata: dict[str, Any] = field(default_factory=dict)
    registered_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())


class ServiceManager:
    _instance: ServiceManager | None = None

    def __init__(self):
        if ServiceManager._instance is not None:
            raise RuntimeError("ServiceManager is a singleton.")
        self._services: dict[str, ServiceDescriptor] = {}
        ServiceManager._instance = self

    @classmethod
    def get_instance(cls) -> ServiceManager:
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def _get_discovery(self) -> ServiceDiscovery | None:
        kernel = get_kernel()
        return kernel.get_component("service_discovery")

    def register(
        self,
        name: str,
        version: str = "1.0.0",
        host: str = "localhost",
        port: int = 0,
        protocol: str = "http",
        health_path: str = "/health",
        dependencies: list[str] | None = None,
        metadata: dict | None = None,
    ) -> ServiceDescriptor:
        descriptor = ServiceDescriptor(
            name=name,
            version=version,
            host=host,
            port=port,
            protocol=protocol,
            health_path=health_path,
            dependencies=dependencies or [],
            metadata=metadata or {},
        )
        self._services[name] = descriptor

        sd = self._get_discovery()
        if sd:
            endpoint = ServiceEndpoint(
                name=name,
                host=host,
                port=port,
                protocol=protocol,
                health_path=health_path,
                metadata=metadata or {},
            )
            sd.register(endpoint)
            logger.info("Service registered in kernel discovery: %s", name)

        logger.info("Service registered: %s v%s", name, version)
        return descriptor

    def unregister(self, name: str) -> None:
        self._services.pop(name, None)
        sd = self._get_discovery()
        if sd:
            sd.unregister(name)

    def get(self, name: str) -> ServiceDescriptor | None:
        return self._services.get(name)

    def list_services(self) -> list[ServiceDescriptor]:
        return list(self._services.values())

    def resolve(self, name: str) -> ServiceDescriptor | None:
        sd = self._get_discovery()
        if sd:
            endpoint = sd.discover(name)
            if endpoint:
                return ServiceDescriptor(
                    name=endpoint.name,
                    version="1.0.0",
                    host=endpoint.host,
                    port=endpoint.port,
                    protocol=endpoint.protocol,
                    health_path=endpoint.health_path,
                )
        return self._services.get(name)

    def dependency_map(self) -> dict[str, list[str]]:
        return {name: svc.dependencies for name, svc in self._services.items()}

    async def health_check(self, name: str) -> dict[str, Any]:
        svc = self._services.get(name)
        if not svc:
            return {"service": name, "status": "not_found"}
        try:
            import httpx

            url = f"{svc.protocol}://{svc.host}:{svc.port}{svc.health_path}"
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.get(url)
                return {
                    "service": name,
                    "status": "healthy" if resp.is_success else "unhealthy",
                    "status_code": resp.status_code,
                }
        except Exception as e:
            return {"service": name, "status": "unreachable", "error": str(e)}

    def version_summary(self) -> dict[str, str]:
        return {name: svc.version for name, svc in self._services.items()}
