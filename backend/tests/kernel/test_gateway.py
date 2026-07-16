from __future__ import annotations

import pytest

from app.kernel import Kernel
from app.kernel.gateway.discovery import ServiceDiscovery, ServiceEndpoint
from app.kernel.gateway.health_routing import HealthRouter
from app.kernel.gateway.routing import InternalRouter, Route


class TestServiceDiscovery:
    def test_register_and_discover(self, kernel: Kernel):
        sd = ServiceDiscovery(kernel)
        endpoint = ServiceEndpoint(
            name="test-service",
            host="localhost",
            port=8080,
        )
        sd.register(endpoint)
        assert sd.discover("test-service") is not None
        assert sd.discover("nonexistent") is None

    def test_list(self, kernel: Kernel):
        sd = ServiceDiscovery(kernel)
        sd.register(ServiceEndpoint(name="a", host="localhost", port=1))
        sd.register(ServiceEndpoint(name="b", host="localhost", port=2))
        assert len(sd.list_services()) == 2

    def test_unregister(self, kernel: Kernel):
        sd = ServiceDiscovery(kernel)
        sd.register(ServiceEndpoint(name="a", host="localhost", port=1))
        sd.unregister("a")
        assert sd.discover("a") is None


class TestInternalRouter:
    def test_route_matching(self):
        router = InternalRouter()

        def handler():
            pass

        router.register(Route(path="/api/v1/users", method="GET", handler=handler))
        match = router.match("/api/v1/users", "GET")
        assert match is not None
        assert match.path == "/api/v1/users"
        assert router.match("/api/v1/users", "POST") is None


class TestHealthRouter:
    def test_check_all(self):
        hr = HealthRouter()

        def db_check():
            return {"status": "ok"}

        def fail_check():
            raise RuntimeError("down")

        hr.register("database", db_check)
        hr.register("cache", fail_check)
        results = hr.check_all()
        assert results["database"]["healthy"]
        assert not results["cache"]["healthy"]


class TestServiceEndpointDefaults:
    def test_defaults(self):
        ep = ServiceEndpoint(name="test", host="localhost", port=8080)
        assert ep.protocol == "http"
        assert ep.health_path == "/health"
        assert ep.metadata == {}
