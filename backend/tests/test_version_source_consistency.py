from __future__ import annotations

from pathlib import Path

from app.config import APP_VERSION
from app.contracts.events import get_asyncapi_spec
from app.engineering.security.sbom import SBOMGenerator
from app.fhir._capabilities import get_capability_statement
from app.kernel.integration import get_kernel_config
from app.knowledge_graph.fhir_catalog import FHIRCatalog
from pytest import MonkeyPatch


def test_platform_metadata_uses_canonical_app_version(tmp_path: Path) -> None:
    assert get_asyncapi_spec()["info"]["version"] == APP_VERSION
    assert get_capability_statement()["software"]["version"] == APP_VERSION
    assert FHIRCatalog().get_capability_statement()["software"]["version"] == APP_VERSION
    assert SBOMGenerator(tmp_path).generate()["metadata"]["tools"][0]["version"] == APP_VERSION


def test_kernel_uses_canonical_version_when_environment_override_is_absent(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.delenv("APP_VERSION", raising=False)

    assert get_kernel_config().version == APP_VERSION


def test_kernel_preserves_explicit_environment_override(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setenv("APP_VERSION", "test-override")

    assert get_kernel_config().version == "test-override"
