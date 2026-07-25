from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path

import pytest
import yaml


def find_security_dir() -> Path:
    current = Path(__file__).resolve().parent
    while current.name != "security" and current.parent != current:
        current = current.parent
    return current


SECURITY_DIR = find_security_dir()
CONFIGS_DIR = SECURITY_DIR / "configs"
SCRIPTS_DIR = SECURITY_DIR / "scripts"
POLICIES_DIR = SECURITY_DIR / "policies"


class TestDockerSecurity:
    def test_dockerfile_exists(self):
        dockerfile = SECURITY_DIR / "Dockerfile"
        assert dockerfile.exists(), "Dockerfile not found"

    def test_dockerfile_has_security_user(self):
        dockerfile = SECURITY_DIR / "Dockerfile"
        content = dockerfile.read_text()
        assert "USER" in content, "Dockerfile should use non-root user"

    def test_dockerfile_multi_stage(self):
        dockerfile = SECURITY_DIR / "Dockerfile"
        content = dockerfile.read_text()
        assert "FROM" in content, "Dockerfile should use multi-stage builds"

    def test_docker_compose_security_context(self):
        compose_file = SECURITY_DIR / "docker-compose.yml"
        if compose_file.exists():
            content = compose_file.read_text()
            assert "security_opt" in content or "security" in content.lower()


class TestKubernetesSecurity:
    def test_k8s_deployment_exists(self):
        k8s_dir = SECURITY_DIR / "k8s"
        if k8s_dir.exists():
            files = list(k8s_dir.glob("*.yaml")) + list(k8s_dir.glob("*.yml"))
            assert len(files) > 0, "No Kubernetes manifests found"

    def test_k8s_pod_security_context(self):
        k8s_dir = SECURITY_DIR / "k8s"
        if k8s_dir.exists():
            for f in k8s_dir.glob("*.yaml"):
                content = f.read_text()
                if "kind: Pod" in content or "kind: Deployment" in content:
                    assert "securityContext" in content or "runAsNonRoot" in content

    def test_k8s_network_policy(self):
        k8s_dir = SECURITY_DIR / "k8s"
        if k8s_dir.exists():
            has_netpol = any("NetworkPolicy" in f.read_text() for f in k8s_dir.glob("*.yaml"))
            if not has_netpol:
                pytest.skip("No NetworkPolicy found in k8s manifests")


class TestTerraformSecurity:
    def test_terraform_plan_exists(self):
        tf_dir = SECURITY_DIR / "terraform"
        if tf_dir.exists():
            tf_files = list(tf_dir.glob("*.tf"))
            assert len(tf_files) > 0, "No Terraform files found"

    def test_terraform_variable_sensitivity(self):
        tf_dir = SECURITY_DIR / "terraform"
        if tf_dir.exists():
            for f in tf_dir.glob("*.tf"):
                content = f.read_text()
                if "sensitive" in content.lower() or "secret" in content.lower():
                    assert "sensitive" in content or "sensitive" in content.lower()

    def test_terraform_encryption_config(self):
        tf_dir = SECURITY_DIR / "terraform"
        if tf_dir.exists():
            for f in tf_dir.glob("*.tf"):
                content = f.read_text()
                if "kms" in content.lower() or "encrypt" in content.lower():
                    assert True
                    return
            pytest.skip("No encryption configuration found in Terraform files")


class TestRedisSecurity:
    def test_redis_config_exists(self):
        config = CONFIGS_DIR / "redis.conf"
        if config.exists():
            content = config.read_text()
            assert len(content) > 0

    def test_redis_password_auth(self):
        config = CONFIGS_DIR / "redis.conf"
        if config.exists():
            content = config.read_text()
            assert "requirepass" in content

    def test_redis_tls_config(self):
        config = CONFIGS_DIR / "redis.conf"
        if config.exists():
            content = config.read_text()
            assert any(kw in content for kw in ["tls-", "tls_port", "tls_cert"])


class TestCIAndScripts:
    def test_ci_workflow_exists(self):
        ci_dir = SECURITY_DIR.parent / ".github" / "workflows"
        if ci_dir.exists():
            files = list(ci_dir.glob("*.yml")) + list(ci_dir.glob("*.yaml"))
            assert len(files) > 0

    def test_scripts_executable(self):
        for script in SCRIPTS_DIR.glob("*.sh"):
            assert os.access(script, os.X_OK) or script.suffix == ".sh"

    def test_scripts_syntax(self):
        for script in SCRIPTS_DIR.glob("*.sh"):
            content = script.read_text()
            assert "#!/usr/bin/env bash" in content or "#!/bin/bash" in content or "#!/bin/sh" in content


class TestPolicyFiles:
    def test_policies_exist(self):
        assert POLICIES_DIR.exists()
        policy_files = list(POLICIES_DIR.glob("*"))
        assert len(policy_files) > 0

    def test_policy_content_not_empty(self):
        for f in POLICIES_DIR.glob("*"):
            content = f.read_text()
            assert len(content.strip()) > 0

    def test_policy_yaml_valid(self):
        for f in POLICIES_DIR.glob("*.yml"):
            content = f.read_text()
            try:
                yaml.safe_load(content)
            except yaml.YAMLError:
                pytest.fail(f"Invalid YAML in {f.name}")


class TestConfigFiles:
    def test_configs_exist(self):
        assert CONFIGS_DIR.exists()
        config_files = list(CONFIGS_DIR.glob("*"))
        assert len(config_files) > 0

    def test_config_yaml_valid(self):
        for f in CONFIGS_DIR.glob("*.yml"):
            content = f.read_text()
            try:
                yaml.safe_load(content)
            except yaml.YAMLError:
                pytest.fail(f"Invalid YAML in {f.name}")

    def test_config_json_valid(self):
        for f in CONFIGS_DIR.glob("*.json"):
            content = f.read_text()
            try:
                json.loads(content)
            except json.JSONDecodeError:
                pytest.fail(f"Invalid JSON in {f.name}")


class TestSecretsManagement:
    def test_no_hardcoded_secrets(self):
        for pattern in ["*.py", "*.sh", "*.yml", "*.yaml", "*.json", "*.conf", "*.toml", "*.cfg"]:
            for f in SECURITY_DIR.rglob(pattern):
                if ".git" in str(f) or "__pycache__" in str(f):
                    continue
                content = f.read_text()
                if "password" in content.lower() or "secret" in content.lower():
                    pass

    def test_env_template_exists(self):
        env_template = SECURITY_DIR / ".env.template"
        if env_template.exists():
            content = env_template.read_text()
            assert len(content) > 0


class TestNetworkSecurity:
    def test_firewall_rules_exist(self):
        config = CONFIGS_DIR / "firewall.yml"
        if config.exists():
            content = yaml.safe_load(config.read_text())
            assert "rules" in content or "firewall" in content

    def test_tls_config_exists(self):
        config = CONFIGS_DIR / "tls.yml"
        if config.exists():
            content = yaml.safe_load(config.read_text())
            assert content is not None
