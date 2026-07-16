from __future__ import annotations

import pytest

from app.integration.connector.registry import ConnectorRegistry
from app.integration.connector.spec import (
    ConnectorSpec,
    ConnectorStatus,
    ConnectorType,
)


class TestConnectorRegistry:
    def test_register_and_get(self):
        registry = ConnectorRegistry()
        spec = ConnectorSpec(name="test-api", connector_type=ConnectorType.REST)
        registry.register(spec)
        assert registry.get(spec.id) is spec
        assert registry.count() == 1

    def test_find_by_name(self):
        registry = ConnectorRegistry()
        spec = ConnectorSpec(name="my-api", connector_type=ConnectorType.REST)
        registry.register(spec)
        assert registry.find_by_name("my-api") is spec
        assert registry.find_by_name("nonexistent") is None

    def test_list_by_type(self):
        registry = ConnectorRegistry()
        registry.register(ConnectorSpec(name="r1", connector_type=ConnectorType.REST))
        registry.register(ConnectorSpec(name="r2", connector_type=ConnectorType.REST))
        registry.register(ConnectorSpec(name="g1", connector_type=ConnectorType.GRAPHQL))
        assert len(registry.list_by_type(ConnectorType.REST)) == 2
        assert len(registry.list_by_type(ConnectorType.GRAPHQL)) == 1

    def test_list_by_tag(self):
        registry = ConnectorRegistry()
        registry.register(ConnectorSpec(name="a", tags=["prod", "critical"]))
        registry.register(ConnectorSpec(name="b", tags=["prod"]))
        registry.register(ConnectorSpec(name="c", tags=["staging"]))
        assert len(registry.list_by_tag("prod")) == 2
        assert len(registry.list_by_tag("staging")) == 1

    def test_update_status(self):
        registry = ConnectorRegistry()
        spec = ConnectorSpec(name="test", connector_type=ConnectorType.REST)
        registry.register(spec)
        assert spec.status == ConnectorStatus.CREATED
        registry.update_status(spec.id, ConnectorStatus.ACTIVE)
        assert spec.status == ConnectorStatus.ACTIVE

    def test_unregister(self):
        registry = ConnectorRegistry()
        spec = ConnectorSpec(name="test", connector_type=ConnectorType.REST)
        registry.register(spec)
        assert registry.unregister(spec.id) is True
        assert registry.count() == 0
        assert registry.unregister("nonexistent") is False

    def test_record_health(self):
        registry = ConnectorRegistry()
        spec = ConnectorSpec(name="test", connector_type=ConnectorType.REST)
        registry.register(spec)
        registry.record_health(spec.id, "healthy", 42.5)
        assert spec.health.status == "healthy"
        assert spec.health.latency_ms == 42.5

    def test_count_by_type(self):
        registry = ConnectorRegistry()
        registry.register(ConnectorSpec(name="a", connector_type=ConnectorType.REST))
        registry.register(ConnectorSpec(name="b", connector_type=ConnectorType.FHIR))
        counts = registry.count_by_type()
        assert counts.get("rest") == 1
        assert counts.get("fhir") == 1
