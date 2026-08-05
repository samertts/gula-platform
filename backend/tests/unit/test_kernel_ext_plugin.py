"""Unit tests for GULA-KERNEL-EXT-001 Phase 1 — Plugin SDK."""

from __future__ import annotations

import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3]))

from scripts.kernel.core import ENGINE_REGISTRY, Severity
from scripts.kernel.ext import plugin
from scripts.kernel.ext.plugin import (
    ISOLATION_LEVELS,
    LIFECYCLE_STATES,
    PERMISSION_CATEGORIES,
    PluginError,
    PluginManifest,
    PluginRegistry,
    PluginSandbox,
    certify,
    discover,
    manifest_from_engine,
    resolve_dependencies,
    validate_manifest,
    validate_version,
)


def _manifest(**overrides) -> PluginManifest:
    base = {
        "name": "test-plugin",
        "version": "1.0.0",
        "entrypoint": "scripts.kernel.test_plugin",
        "contract": {
            "inputs": ["x"],
            "outputs": ["y"],
            "events": [],
            "errors": [],
            "artifacts": [],
            "ownership": ["test"],
            "dependencies": [],
            "health": "healthy",
            "progress": "idle",
            "checkpoint": "none",
            "capabilities": ["do thing"],
            "resources": {"max_files": 5, "max_minutes": 5},
            "timeout": 300,
            "retry": 3,
            "version": "1.0.0",
            "status": "idle",
        },
    }
    base.update(overrides)
    return PluginManifest(**base)


class TestManifest:
    def test_valid_manifest_passes(self):
        assert validate_manifest(_manifest()) == []

    def test_semver_required(self):
        findings = validate_manifest(_manifest(version="not-semver"))
        assert any(f.id == "PLUGIN-VERSION" for f in findings)

    def test_missing_name_critical(self):
        findings = validate_manifest(_manifest(name="  "))
        assert any(f.id == "PLUGIN-NAME" for f in findings)

    def test_entrypoint_required(self):
        findings = validate_manifest(_manifest(entrypoint="nodots"))
        assert any(f.id == "PLUGIN-ENTRY" for f in findings)

    def test_isolation_validation(self):
        findings = validate_manifest(_manifest(isolation="nope"))
        assert any(f.id == "PLUGIN-ISO" for f in findings)

    def test_permission_validation(self):
        findings = validate_manifest(_manifest(permissions=["root"]))
        assert any(f.id == "PLUGIN-PERM" for f in findings)

    def test_contract_required_fields(self):
        manifest = _manifest()
        manifest.contract = {}
        findings = validate_manifest(manifest)
        assert any(f.id == "PLUGIN-CONTRACT" for f in findings)

    def test_dependency_reference_format(self):
        findings = validate_manifest(_manifest(dependencies=["nodots"]))
        assert any(f.id == "PLUGIN-DEP" for f in findings)

    def test_is_valid_true_for_good(self):
        assert plugin.is_valid(_manifest())

    def test_is_valid_false_for_bad(self):
        assert not plugin.is_valid(_manifest(version="bad"))


class TestVersion:
    def test_valid_semvers(self):
        assert validate_version("1.0.0")
        assert validate_version("0.1.2")
        assert validate_version("10.20.30")

    def test_invalid_semvers(self):
        assert not validate_version("1.0")
        assert not validate_version("v1.0.0")
        assert not validate_version("1.0.0-beta")


class TestRegistry:
    def test_register_and_get(self):
        registry = PluginRegistry()
        record = registry.register(_manifest())
        assert registry.get("test-plugin") is record

    def test_register_duplicate_same_version_ok(self):
        registry = PluginRegistry()
        registry.register(_manifest())
        registry.register(_manifest())

    def test_register_duplicate_different_version_raises(self):
        registry = PluginRegistry()
        registry.register(_manifest())
        with pytest.raises(PluginError):
            registry.register(_manifest(version="2.0.0"))

    def test_register_invalid_raises(self):
        registry = PluginRegistry()
        with pytest.raises(PluginError):
            registry.register(_manifest(version="bad"))

    def test_install_activate_deactivate(self):
        registry = PluginRegistry()
        registry.register(_manifest())
        assert registry.install("test-plugin").state == "installed"
        assert registry.activate("test-plugin").state == "active"
        assert registry.deactivate("test-plugin").state == "disabled"

    def test_uninstall_removes(self):
        registry = PluginRegistry()
        registry.register(_manifest())
        registry.uninstall("test-plugin")
        assert registry.get("test-plugin") is None

    def test_uninstall_missing_raises(self):
        registry = PluginRegistry()
        with pytest.raises(PluginError):
            registry.uninstall("nope")

    def test_hot_reload(self):
        registry = PluginRegistry()
        registry.register(_manifest())
        registry.activate("test-plugin")
        record = registry.reload("test-plugin")
        assert record.state == "active"
        assert record.loaded_at

    def test_list_by_state(self):
        registry = PluginRegistry()
        registry.register(_manifest(name="a"))
        registry.register(_manifest(name="b"))
        registry.activate("a")
        assert [r.manifest.name for r in registry.list("active")] == ["a"]

    def test_snapshot_contains_all(self):
        registry = PluginRegistry()
        registry.register(_manifest())
        assert "test-plugin" in registry.snapshot()

    def test_lifecycle_states_ordered(self):
        assert list(LIFECYCLE_STATES) == [
            "draft", "registered", "validated", "installed", "active",
            "disabled", "deprecated", "uninstalled",
        ]


class TestDependencies:
    def test_simple_chain(self):
        registry = PluginRegistry()
        registry.register(_manifest(name="leaf"))
        registry.register(_manifest(name="mid", dependencies=["leaf"]))
        registry.register(_manifest(name="root", dependencies=["mid"]))
        assert resolve_dependencies(registry, "root") == ["leaf", "mid", "root"]

    def test_missing_dependency_raises(self):
        registry = PluginRegistry()
        registry.register(_manifest(name="root", dependencies=["missing"]))
        with pytest.raises(PluginError):
            resolve_dependencies(registry, "root")

    def test_cycle_detected(self):
        registry = PluginRegistry()
        registry.register(_manifest(name="a", dependencies=["b"]))
        registry.register(_manifest(name="b", dependencies=["a"]))
        with pytest.raises(PluginError):
            resolve_dependencies(registry, "a")


class TestSandbox:
    def test_denied_action(self):
        sandbox = PluginSandbox(["read"], "sandbox")
        assert not sandbox.can("write")
        assert sandbox.can("read")

    def test_sandbox_deny_list(self):
        sandbox = PluginSandbox(["read"], "sandbox")
        denied = sandbox.deny_list()
        assert "network" in denied
        assert "deployment" in denied

    def test_secrets_permission_finding(self):
        findings = PluginSandbox(["read", "secrets"], "restricted").evaluate()
        assert any(f.id == "PLUGIN-SECRETS" for f in findings)

    def test_deployment_permission_finding(self):
        findings = PluginSandbox(["read", "deployment"], "restricted").evaluate()
        assert any(f.id == "PLUGIN-DEPLOY" for f in findings)

    def test_embedded_privileged_finding(self):
        findings = PluginSandbox(["read", "network"], "embedded").evaluate()
        assert any(f.id == "PLUGIN-ISO-PERM" for f in findings)

    def test_permission_categories_complete(self):
        assert "read" in PERMISSION_CATEGORIES
        assert "deployment" in PERMISSION_CATEGORIES


class TestCertify:
    def test_certified_clean(self):
        assert certify(_manifest()) == []

    def test_license_check(self):
        findings = certify(_manifest(license="GPL-3.0"))
        assert any(f.id == "PLUGIN-LICENSE" for f in findings)

    def test_approved_licenses(self):
        for lic in ["MIT", "Apache-2.0", "BSD-3-Clause", "MPL-2.0"]:
            assert not [f for f in certify(_manifest(license=lic)) if f.id == "PLUGIN-LICENSE"]

    def test_hard_findings_flow_through(self):
        findings = certify(_manifest(version="bad"))
        assert any(f.id == "PLUGIN-VERSION" for f in findings)


class TestManifestFromEngine:
    def test_all_engines_become_plugins(self):
        for name, meta in ENGINE_REGISTRY.items():
            manifest = manifest_from_engine(name, meta)
            assert is_valid(manifest)
            assert manifest.name == name
            assert manifest.version == meta["version"]

    def test_engine_contract_preserved(self):
        manifest = manifest_from_engine("builder", ENGINE_REGISTRY["builder"])
        assert manifest.contract["capabilities"] == ENGINE_REGISTRY["builder"]["capabilities"]


class TestDiscover:
    def test_discover_empty_dir(self, tmp_path):
        assert discover(tmp_path) == []

    def test_discover_finds_plugin_json(self, tmp_path):
        (tmp_path / "plugin.json").write_text(
            '{"name":"p1","version":"1.0.0","entrypoint":"mod.p1","contract":{}}',
            encoding="utf-8",
        )
        found = discover(tmp_path)
        assert len(found) == 1
        assert found[0].name == "p1"

    def test_discover_ignores_bad_json(self, tmp_path):
        (tmp_path / "plugin.json").write_text("{invalid", encoding="utf-8")
        assert discover(tmp_path) == []

    def test_discover_ignores_missing_fields(self, tmp_path):
        (tmp_path / "plugin.json").write_text('{"name":"p1"}', encoding="utf-8")
        assert discover(tmp_path) == []


class TestRender:
    def test_render_includes_plugin(self):
        registry = PluginRegistry()
        registry.register(_manifest())
        rendered = plugin.render_plugin_markdown(registry)
        assert "test-plugin" in rendered


def is_valid(manifest: PluginManifest) -> bool:
    return not [
        f for f in validate_manifest(manifest)
        if f.severity in {Severity.HIGH, Severity.CRITICAL}
    ]
