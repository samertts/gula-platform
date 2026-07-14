from __future__ import annotations

import pytest

from backend.app.integration.connector.registry import ConnectorRegistry
from backend.app.integration.connector.sdk import ConnectorSDK
from backend.app.integration.connector.spec import (
    ConnectorEndpoint,
    ConnectorSpec,
    ConnectorType,
)


class TestConnectorSDK:
    def test_generate_python_client(self):
        registry = ConnectorRegistry()
        spec = ConnectorSpec(
            name="patient-api",
            description="Patient management API",
            connector_type=ConnectorType.REST,
            endpoints=[ConnectorEndpoint(url="https://api.example.com/patients", method="GET")],
        )
        registry.register(spec)
        sdk = ConnectorSDK(registry)
        artifact = sdk.generate_client(spec.id, "python")
        assert artifact.language == "python"
        assert "PatientApi" in artifact.code
        assert artifact.dependencies == ["httpx>=0.27.0"]

    def test_get_artifact(self):
        registry = ConnectorRegistry()
        spec = ConnectorSpec(name="test", connector_type=ConnectorType.REST)
        registry.register(spec)
        sdk = ConnectorSDK(registry)
        sdk.generate_client(spec.id)
        artifact = sdk.get_artifact(spec.id)
        assert artifact is not None
        assert artifact.version == "1.0.0"
