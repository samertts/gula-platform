from __future__ import annotations

import pytest

from app.kernel import Kernel
from app.kernel.exceptions import ServiceNotFoundError
from app.kernel.runtime.service_registry import ServiceRegistry


class TestServiceRegistryFunctionality:
    def test_register_and_get(self, kernel: Kernel):
        sr = ServiceRegistry()
        kernel.register_component("service_registry", sr)
        sr.register("test_service", {"key": "value"})
        assert sr.has("test_service")
        assert sr.get("test_service") == {"key": "value"}
        assert sr.get_required("test_service") == {"key": "value"}
        with pytest.raises(ServiceNotFoundError):
            sr.get_required("nonexistent")

    def test_unregister(self):
        sr = ServiceRegistry()
        sr.register("svc", {"data": 1})
        assert sr.has("svc")
        sr.unregister("svc")
        assert not sr.has("svc")

    def test_list(self):
        sr = ServiceRegistry()
        sr.register("a", 1)
        sr.register("b", 2)
