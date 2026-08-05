"""Unit tests for GULA-DEPLOYER-001 — Phase 2 execution + Phase 3 infrastructure."""

from __future__ import annotations

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3]))

import pytest

from scripts.deployer.core import ReleaseArtifact
from scripts.deployer.execution import (
    BUILDABLE_SERVICES,
    PIPELINE_STAGES,
    build_pipeline,
    create_artifact,
    release_notes,
    sign_artifact,
    validate_compose,
    validate_container,
    validate_version,
)
from scripts.deployer.infrastructure import (
    certificate_spec,
    desired_network,
    manage_resources,
    render_plan,
    reverse_proxy_spec,
    secrets_spec,
)


class TestVersion:
    def test_valid_semver(self):
        assert validate_version("1.0.0") is True
        assert validate_version("1.4.0") is True
        assert validate_version("0.0.1") is True
        assert validate_version("2.10.3") is True

    def test_prerelease_is_valid_semver(self):
        assert validate_version("1.0.0-rc1") is True

    def test_v_prefix_is_valid_semver(self):
        assert validate_version("v1.0.0") is True

    def test_invalid_semver(self):
        assert validate_version("1.0") is False
        assert validate_version("1.0.0.1") is False
        assert validate_version("") is False


class TestPipeline:
    def test_pipeline_has_eight_stages(self):
        assert len(PIPELINE_STAGES) == 8

    def test_pipeline_stages_ordered(self):
        stages = build_pipeline("1.0.0")
        assert len(stages) == 8
        assert stages[0] == "build:backend:1.0.0"
        assert stages[-1] == "deploy:backend:1.0.0"

    def test_pipeline_rejects_bad_version(self):
        with pytest.raises(ValueError):
            build_pipeline("1.0")

    def test_pipeline_includes_sign_and_tag(self):
        stages = build_pipeline("1.0.0")
        assert "sign-image:backend:1.0.0" in stages
        assert "tag-version:backend:1.0.0" in stages

    def test_buildable_services_exact(self):
        assert set(BUILDABLE_SERVICES) == {"backend", "frontend", "worker", "api-gateway"}


class TestArtifact:
    def test_create_artifact_default_registry(self):
        artifact = create_artifact("backend", "1.0.0")
        assert artifact.artifact_id.startswith("REL-")
        assert artifact.registry == "registry.gula.iq"
        assert artifact.signed is True
        assert artifact.validated is True

    def test_create_artifact_custom_digest(self):
        artifact = create_artifact("frontend", "1.0.0", digest="sha256:abc")
        assert artifact.digest == "sha256:abc"

    def test_create_artifact_image_built(self):
        artifact = create_artifact("backend", "1.4.0")
        assert artifact.image == "registry.gula.iq/backend:1.4.0"

    def test_create_artifact_rejects_bad_version(self):
        with pytest.raises(ValueError):
            create_artifact("backend", "1.0")

    def test_sign_artifact_marks_signed(self):
        artifact = ReleaseArtifact(artifact_id="REL-1", name="backend", version="1.0.0")
        signed = sign_artifact(artifact)
        assert signed.signed is True

    def test_release_notes_contains_version(self):
        artifact = create_artifact("backend", "1.4.0")
        notes = release_notes(artifact)
        assert "1.4.0" in notes
        assert "backend" in notes


class TestContainerValidation:
    def test_valid_dockerfile(self):
        dockerfile = "\n".join([
            "FROM python:3.12-slim",
            "RUN useradd --create-home app",
            "USER app",
            "HEALTHCHECK CMD curl -f http://localhost:8000/health",
        ])
        assert validate_container(dockerfile) == []

    def test_missing_non_root(self):
        dockerfile = "FROM python:3.12-slim\nHEALTHCHECK CMD true"
        problems = validate_container(dockerfile)
        assert any("USER" in p for p in problems)

    def test_missing_healthcheck(self):
        dockerfile = "FROM python:3.12-slim\nUSER app"
        problems = validate_container(dockerfile)
        assert any("HEALTHCHECK" in p for p in problems)

    def test_unpinned_base(self):
        dockerfile = "FROM python\nUSER app\nHEALTHCHECK CMD true"
        problems = validate_container(dockerfile)
        assert any("pin" in p for p in problems)

    def test_compose_with_restart_and_network(self):
        compose = "services:\n  api:\n    restart: always\n    networks: [gula-net]\n"
        assert validate_compose(compose) == []

    def test_compose_missing_network(self):
        compose = "services:\n  api:\n    restart: always\n"
        problems = validate_compose(compose)
        assert any("network" in p for p in problems)


class TestInfrastructure:
    def test_manage_resources_covers_datastores(self):
        resources = manage_resources()
        services = {r.service for r in resources}
        assert {"postgres", "redis", "rabbitmq", "minio"} <= services

    def test_managed_resources_are_managed(self):
        resources = manage_resources()
        assert all(r.managed is True for r in resources)

    def test_manage_resources_filters_unknown(self):
        resources = manage_resources(("postgres", "unknown-service"))
        assert [r.service for r in resources] == ["postgres"]

    def test_desired_network_is_overlay(self):
        network = desired_network()
        assert network.kind == "network"
        assert network.spec["driver"] == "overlay"
        assert network.spec["encrypted"] is True

    def test_reverse_proxy_spec_has_domain(self):
        proxy = reverse_proxy_spec("gula.iq")
        assert proxy.spec["domain"] == "gula.iq"
        assert proxy.spec["hsts"] is True

    def test_certificate_spec_uses_letsencrypt(self):
        cert = certificate_spec("gula.iq")
        assert cert.spec["issuer"] == "letsencrypt"
        assert cert.spec["renew"] is True

    def test_secrets_spec_uses_vault(self):
        secrets = secrets_spec("vault")
        assert secrets.spec["provider"] == "vault"
        assert secrets.spec["rotation_days"] == 90

    def test_render_plan_contains_resources(self):
        plan = render_plan([desired_network(), certificate_spec("gula.iq")])
        assert "network" in plan
        assert "certificate" in plan
        assert "domain" in plan
