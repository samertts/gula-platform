"""Unit tests for GULA-DEPLOYER-001 — core constants, enums, dataclasses."""

from __future__ import annotations

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3]))

from scripts.deployer.core import (
    AUDIT_COMPONENTS,
    ENVIRONMENTS,
    HEALTH_COMPONENTS,
    MANAGED_SERVICES,
    OBSERVABILITY_SERVICES,
    SECURITY_AREAS,
    SERVICES,
    DeploymentStatus,
    DeploymentTarget,
    Environment,
    InfrastructureItem,
    ManagedResource,
    ReleaseArtifact,
    RollbackKind,
    ScalingMode,
    SecurityCheck,
    ValidationCheck,
    ValidationStatus,
    make_id,
)


class TestEngineConstants:
    def test_environments_cover_all_eight(self):
        assert len(ENVIRONMENTS) == 8
        for env in ("local", "development", "testing", "staging", "production",
                    "disaster_recovery", "edge", "offline"):
            assert env in ENVIRONMENTS

    def test_services_include_buildables(self):
        for service in ("backend", "frontend", "worker", "api-gateway"):
            assert service in SERVICES

    def test_managed_services_include_core_datastores(self):
        for service in ("postgres", "redis", "rabbitmq", "minio"):
            assert service in MANAGED_SERVICES

    def test_health_components_include_critical(self):
        for component in ("api", "database", "redis", "authentication", "storage"):
            assert component in HEALTH_COMPONENTS

    def test_observability_services_include_otel_chain(self):
        for service in ("prometheus", "grafana", "loki", "tempo", "jaeger", "alertmanager"):
            assert service in OBSERVABILITY_SERVICES

    def test_security_areas_include_all_nine(self):
        assert len(SECURITY_AREAS) == 9
        for area in ("secrets", "tls", "certificates", "firewall", "container-security",
                     "dependency-security", "least-privilege", "image-scanning",
                     "supply-chain"):
            assert area in SECURITY_AREAS

    def test_audit_components_include_seventeen(self):
        assert len(AUDIT_COMPONENTS) == 17
        assert "docker" in AUDIT_COMPONENTS
        assert "monitoring" in AUDIT_COMPONENTS


class TestEnums:
    def test_environment_members(self):
        assert Environment.PRODUCTION.value == "production"
        assert Environment.LOCAL.value == "local"
        assert Environment.OFFLINE.value == "offline"

    def test_deployment_status_lifecycle(self):
        assert DeploymentStatus.PLANNED.value == "planned"
        assert DeploymentStatus.LIVE.value == "live"
        assert DeploymentStatus.ROLLED_BACK.value == "rolled_back"

    def test_validation_status_members(self):
        assert ValidationStatus.PASS.value == "pass"
        assert ValidationStatus.FAIL.value == "fail"

    def test_rollback_kind_members(self):
        assert RollbackKind.VERSION.value == "version"
        assert RollbackKind.DATABASE.value == "database"

    def test_scaling_mode_members(self):
        assert ScalingMode.HORIZONTAL.value == "horizontal"
        assert ScalingMode.VERTICAL.value == "vertical"
        assert ScalingMode.WORKER.value == "worker"
        assert ScalingMode.QUEUE.value == "queue"


class TestMakeId:
    def test_make_id_has_expected_prefixes(self):
        assert make_id("DEP").startswith("DEP-")
        assert make_id("REL").startswith("REL-")
        assert make_id("SNAP").startswith("SNAP-")

    def test_make_id_has_fixed_length_suffix(self):
        identifier = make_id("DEP")
        suffix = identifier.split("-", 1)[1]
        assert len(suffix) == 8

    def test_make_id_is_deterministic_length(self):
        assert make_id("RES").split("-", 1)[1].isalnum()


class TestDataclasses:
    def test_infrastructure_item_defaults(self):
        item = InfrastructureItem(name="docker", category="runtime")
        assert item.present is False
        assert item.notes == "NOT FOUND"
        assert item.evidence == []

    def test_deployment_target_defaults(self):
        target = DeploymentTarget(environment="production", hosts=["gula.iq"])
        assert target.strategy == "rolling"
        assert target.services == []
        assert target.requires == []

    def test_release_artifact_defaults(self):
        artifact = ReleaseArtifact(artifact_id="REL-1", name="backend", version="1.0.0")
        assert artifact.registry == ""
        assert artifact.signed is False
        assert artifact.validated is False

    def test_validation_check_defaults(self):
        check = ValidationCheck(component="api", check="reachable")
        assert check.status == "pass"
        assert check.latency_ms == 0

    def test_managed_resource_defaults(self):
        resource = ManagedResource(resource_id="RES-1", service="postgres", kind="database")
        assert resource.spec == {}
        assert resource.managed is False

    def test_security_check_defaults(self):
        check = SecurityCheck(area="secrets", finding="none")
        assert check.passed is False
        assert check.severity == "low"
        assert check.evidence == ""
