"""PROGRAM-BETA-COMMIT-0.1 — Dormancy Registry + certification check 10.

Covers:
  * the DormancySource interface (the engine depends only on it)
  * the canonical source (ADR-026 archive set, platform/ disposition)
  * in-memory registry semantics (register, prefix match, protection)
  * the JSON-file source (configurable data source #1)
  * the source factory (canonical / inmemory / json / future providers)
  * the 10th certification check ``dormancy_policy``
  * backward compatibility: engine defaults unchanged, 11/11 certification
"""

from __future__ import annotations

import json

import pytest
from app.domain_platform.certification import CERTIFICATION_CHECKS, DomainCertificationEngine
from app.domain_platform.core import DomainManifest
from app.domain_platform.dormancy import (
    CANONICAL_DORMANCY_REGISTRY,
    DormancyRecord,
    DormancyRegistry,
    DormancyRegistryError,
    DormancySource,
    DormancySourceError,
    JsonDormancySource,
    ModuleLifecycleState,
    build_dormancy_source,
    load_default_dormancy_source,
)
from app.domain_platform.manifest import list_domains

MANDATORY_SHARED_CORE = {"identity", "authentication", "authorization", "audit", "event_bus"}

ARCHIVE_SET = ("ai", "nhop-platform", "edge_agent")
DORMANT_SET = ("backend/app/national_data",)


def _manifest(code: str = "laboratory", **overrides) -> DomainManifest:
    workspace = {
        "laboratory": "laboratory",
        "pharmacy": "pharmacy",
        "radiology": "radiology",
        "hospital": "hospital",
        "blood_bank": "blood_bank",
        "public_health": "public_health",
        "insurance": "insurance",
        "emergency": "hospital",
        "research": "research",
        "citizen_portal": "citizen",
        "provider_portal": "professional",
    }.get(code, "laboratory")
    base = {
        "code": code,
        "name_en": "Test Domain",
        "name_ar": "مجال الاختبار",
        "version": "1.0.0",
        "workspace_type": workspace,
        "description": "test",
        "shared_core": dict.fromkeys(MANDATORY_SHARED_CORE, "shared_core"),
    }
    base.update(overrides)
    return DomainManifest(**base)


def _write_config(tmp_path, records, *, extra: dict | None = None) -> object:
    path = tmp_path / "dormancy.json"
    payload: dict = {"schema_version": 1}
    payload.update(extra or {})
    payload["records"] = records
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


# ── Interface ───────────────────────────────────────────────────────────────


class _FakeSource:
    """A minimal, structurally-valid DormancySource the engine can consume."""

    def __init__(self, archived: list[str] | None = None) -> None:
        self._records = {m: DormancyRecord(m, ModuleLifecycleState.archived, "fake", "2026-08-06") for m in (archived or [])}

    def find_record(self, module):
        return self._records.get(module)

    def record_of(self, module):
        return self._records.get(module)

    def state_of(self, module):
        record = self._records.get(module)
        return record.state if record else None

    def is_declared(self, module):
        return module in self._records

    def is_protected(self, module):
        return module in self._records

    def undeclared(self, modules):
        return [m for m in modules if m not in self._records]

    def modules_in_state(self, state):
        return [m for m, r in self._records.items() if r.state == ModuleLifecycleState(state)]

    def assert_not_removed(self, removed_modules):
        blocked = [m for m in removed_modules if m in self._records]
        if blocked:
            raise DormancyRegistryError("fake protection: " + ", ".join(blocked))

    def to_dict(self):
        return {"records": [r.to_dict() for r in self._records.values()]}

    def __len__(self):
        return len(self._records)


class TestDormancySourceInterface:
    def test_engine_consumes_any_source_implementation(self):
        engine = DomainCertificationEngine(dormancy_registry=_FakeSource())
        result = engine.certify_domain(_manifest())
        assert result.passed is True

    def test_engine_uses_injected_source_for_check(self):
        engine = DomainCertificationEngine(
            dormancy_registry=_FakeSource(archived=["ai/agent.py"])
        )
        manifest = _manifest(modules=["ai/agent.py"])
        check = next(
            c for c in engine.certify_domain(manifest).checks if c.check == "dormancy_policy"
        )
        assert check.passed is False
        assert check.severity == "critical"

    def test_concrete_sources_implement_interface(self):
        assert isinstance(DormancyRegistry(), DormancySource)
        assert isinstance(CANONICAL_DORMANCY_REGISTRY, DormancySource)
        assert isinstance(build_dormancy_source("inmemory"), DormancySource)

    def test_runtime_check_rejects_incomplete_source(self):
        class _Broken:
            def find_record(self, module):  # incomplete protocol
                return None

        assert isinstance(_Broken(), DormancySource) is False

    def test_engine_default_source_is_interface(self):
        engine = DomainCertificationEngine()
        assert isinstance(engine.dormancy_registry, DormancySource)


# ── Canonical source ────────────────────────────────────────────────────────


class TestCanonicalSource:
    def test_archive_set_declared(self):
        for module in ARCHIVE_SET:
            assert CANONICAL_DORMANCY_REGISTRY.state_of(module) == ModuleLifecycleState.archived
        archived = CANONICAL_DORMANCY_REGISTRY.modules_in_state(ModuleLifecycleState.archived)
        assert set(ARCHIVE_SET) <= set(archived)

    def test_platform_is_active_development(self):
        assert CANONICAL_DORMANCY_REGISTRY.state_of("platform") == ModuleLifecycleState.active_development
        assert CANONICAL_DORMANCY_REGISTRY.is_protected("platform") is False

    def test_dormant_modules_declared(self):
        for module in DORMANT_SET:
            assert CANONICAL_DORMANCY_REGISTRY.state_of(module) == ModuleLifecycleState.dormant

    def test_default_config_file_exists_and_loads(self):
        source = load_default_dormancy_source()
        assert len(source) >= len(ARCHIVE_SET) + 1
        assert source.state_of("ai") == ModuleLifecycleState.archived


# ── In-memory registry ──────────────────────────────────────────────────────


class TestDormancyRegistry:
    def test_register_and_state_round_trip(self):
        registry = DormancyRegistry()
        registry.register("backend/app/example", "dormant", "frozen legacy module")
        assert registry.state_of("backend/app/example") == ModuleLifecycleState.dormant
        assert registry.is_declared("backend/app/example") is True
        assert registry.is_protected("backend/app/example") is True

    def test_unknown_state_rejected(self):
        with pytest.raises(DormancyRegistryError):
            DormancyRegistry().register("x", "not-a-state", "n/a")

    def test_empty_module_rejected(self):
        with pytest.raises(DormancyRegistryError):
            DormancyRegistry().register("  ", "dormant", "n/a")

    def test_missing_rationale_rejected(self):
        with pytest.raises(DormancyRegistryError):
            DormancyRegistry().register("x", "dormant", "   ")

    def test_conflicting_redeclaration_rejected(self):
        registry = DormancyRegistry()
        registry.register("x", "dormant", "frozen")
        with pytest.raises(DormancyRegistryError):
            registry.register("x", "active_development", "now active")

    def test_prefix_match_declares_children(self):
        registry = DormancyRegistry()
        registry.register("ai", "archived", "C1.4 archive set")
        assert registry.is_protected("ai/agent.py") is True
        assert registry.is_protected("ai/scripts/generate.py") is True
        assert registry.state_of("ai/agent.py") == ModuleLifecycleState.archived
        assert registry.undeclared(["ai/agent.py", "platform/x"]) == ["platform/x"]

    def test_undeclared_returns_missing(self):
        registry = DormancyRegistry()
        registry.register("backend/app/national_data", "dormant", "warehouse star-schema")
        missing = registry.undeclared(["backend/app/lims/models.py", "backend/app/national_data/dim.py"])
        assert missing == ["backend/app/lims/models.py"]

    def test_assert_not_removed_blocks_protected(self):
        registry = DormancyRegistry()
        registry.register("ai", "archived", "C1.4 archive set")
        with pytest.raises(DormancyRegistryError):
            registry.assert_not_removed(["ai/agent.py", "platform/thing"])
        registry.assert_not_removed(["platform/thing", "backend/app/lims"])

    def test_to_dict_round_trip(self):
        registry = DormancyRegistry()
        registry.register("x", "retired", "superseded")
        data = registry.to_dict()
        assert data["records"][0]["module"] == "x"
        assert data["records"][0]["state"] == "retired"

    def test_protection_rules(self):
        registry = DormancyRegistry()
        for state in (
            ModuleLifecycleState.dormant,
            ModuleLifecycleState.archived,
            ModuleLifecycleState.retired,
        ):
            module = f"m_{state.value}"
            registry.register(module, state, f"{state.value} asset")
            assert registry.is_protected(module) is True
        registry.register("active_mod", "active_development", "live")
        assert registry.is_protected("active_mod") is False

    def test_longest_prefix_wins(self):
        registry = DormancyRegistry()
        registry.register("backend/app", "active_development", "app root")
        registry.register("backend/app/national_data", "dormant", "warehouse")
        assert registry.state_of("backend/app/national_data/models.py") == ModuleLifecycleState.dormant
        assert registry.state_of("backend/app/lims/models.py") == ModuleLifecycleState.active_development


# ── JSON-file source ────────────────────────────────────────────────────────


class TestJsonDormancySource:
    def test_loads_records_from_file(self, tmp_path):
        path = _write_config(
            tmp_path,
            [{"module": "ai", "state": "archived", "rationale": "archive set"}],
        )
        source = JsonDormancySource(path)
        assert source.state_of("ai/agent.py") == ModuleLifecycleState.archived
        assert source.is_protected("ai") is True

    def test_missing_file_raises(self, tmp_path):
        with pytest.raises(DormancySourceError):
            JsonDormancySource(tmp_path / "nope.json")

    def test_invalid_json_raises(self, tmp_path):
        path = tmp_path / "bad.json"
        path.write_text("{not json", encoding="utf-8")
        with pytest.raises(DormancySourceError):
            JsonDormancySource(path)

    def test_missing_records_key_raises(self, tmp_path):
        path = tmp_path / "bad.json"
        path.write_text('{"schema_version": 1}', encoding="utf-8")
        with pytest.raises(DormancySourceError):
            JsonDormancySource(path)

    def test_records_not_list_raises(self, tmp_path):
        path = tmp_path / "bad.json"
        path.write_text('{"records": "ai"}', encoding="utf-8")
        with pytest.raises(DormancySourceError):
            JsonDormancySource(path)

    def test_unknown_state_raises(self, tmp_path):
        path = _write_config(
            tmp_path,
            [{"module": "x", "state": "frozen", "rationale": "bad state"}],
        )
        with pytest.raises(DormancySourceError):
            JsonDormancySource(path)

    def test_missing_rationale_raises(self, tmp_path):
        path = _write_config(
            tmp_path,
            [{"module": "x", "state": "dormant"}],
        )
        with pytest.raises(DormancySourceError):
            JsonDormancySource(path)

    def test_duplicate_module_raises(self, tmp_path):
        path = _write_config(
            tmp_path,
            [
                {"module": "ai", "state": "archived", "rationale": "one"},
                {"module": "ai", "state": "dormant", "rationale": "two"},
            ],
        )
        with pytest.raises(DormancySourceError):
            JsonDormancySource(path)

    def test_source_is_read_only_after_load(self, tmp_path):
        path = _write_config(tmp_path, [{"module": "ai", "state": "archived", "rationale": "x"}])
        source = JsonDormancySource(path)
        with pytest.raises(DormancySourceError):
            source.register("platform", "active_development", "nope")


# ── Source factory ──────────────────────────────────────────────────────────


class TestSourceFactory:
    def test_canonical_kind(self):
        source = build_dormancy_source("canonical")
        assert isinstance(source, DormancySource)
        assert source.state_of("ai") == ModuleLifecycleState.archived

    def test_inmemory_kind(self):
        source = build_dormancy_source("inmemory")
        assert isinstance(source, DormancyRegistry)
        assert len(source) == 0

    def test_json_kind(self, tmp_path):
        path = _write_config(
            tmp_path,
            [{"module": "x", "state": "dormant", "rationale": "frozen"}],
        )
        source = build_dormancy_source("json", path=path)
        assert source.state_of("x") == ModuleLifecycleState.dormant

    def test_json_kind_requires_path(self):
        with pytest.raises(DormancySourceError):
            build_dormancy_source("json")

    @pytest.mark.parametrize("kind", ["database", "governance"])
    def test_future_kinds_raise_loudly(self, kind):
        with pytest.raises(DormancySourceError) as excinfo:
            build_dormancy_source(kind)
        assert "future provider" in str(excinfo.value)

    def test_unknown_kind_raises(self):
        with pytest.raises(DormancySourceError):
            build_dormancy_source("spaceship")


# ── Certification check 10 ──────────────────────────────────────────────────


class TestDormancyCertificationCheck:
    def test_tenth_check_registered(self):
        assert len(CERTIFICATION_CHECKS) == 10
        assert CERTIFICATION_CHECKS[-1] == "dormancy_policy"

    def test_clean_domain_passes(self):
        engine = DomainCertificationEngine()
        result = engine.certify_domain(_manifest())
        assert result.passed is True
        check = next(c for c in result.checks if c.check == "dormancy_policy")
        assert check.passed is True
        assert check.severity == "info"

    def test_declared_active_module_passes(self):
        engine = DomainCertificationEngine()
        manifest = _manifest(modules=["platform"])
        result = engine.certify_domain(manifest)
        check = next(c for c in result.checks if c.check == "dormancy_policy")
        assert check.passed is True

    def test_undeclared_module_is_advisory(self):
        engine = DomainCertificationEngine()
        manifest = _manifest(modules=["backend/app/lims/models.py"])
        result = engine.certify_domain(manifest)
        assert result.passed is True
        check = next(c for c in result.checks if c.check == "dormancy_policy")
        assert check.passed is True
        assert check.severity == "info"
        assert "implicitly active_development" in check.details

    def test_archived_module_owned_fails(self):
        engine = DomainCertificationEngine()
        manifest = _manifest(modules=["ai/agent.py"])
        result = engine.certify_domain(manifest)
        assert result.passed is False
        check = next(c for c in result.checks if c.check == "dormancy_policy")
        assert check.passed is False
        assert check.severity == "critical"

    def test_declared_dormant_module_owned_fails(self):
        engine = DomainCertificationEngine()
        manifest = _manifest(modules=["backend/app/national_data"])
        result = engine.certify_domain(manifest)
        assert result.passed is False
        check = next(c for c in result.checks if c.check == "dormancy_policy")
        assert check.passed is False
        assert check.severity == "major"

    def test_real_domain_modules_pass(self):
        engine = DomainCertificationEngine()
        manifest = _manifest(modules=["backend/app/lims/models.py", "backend/app/pharmacy/service.py"])
        result = engine.certify_domain(manifest)
        check = next(c for c in result.checks if c.check == "dormancy_policy")
        assert check.passed is True

    def test_engine_accepts_custom_registry(self):
        registry = DormancyRegistry()
        registry.register("app/example", "active_development", "fresh module")
        engine = DomainCertificationEngine(dormancy_registry=registry)
        manifest = _manifest(modules=["app/example"])
        check = next(c for c in engine.certify_domain(manifest).checks if c.check == "dormancy_policy")
        assert check.passed is True
        registry.register("app/other", "archived", "C1.4 archive set")
        manifest = _manifest(modules=["app/other/old.py"])
        check = next(c for c in engine.certify_domain(manifest).checks if c.check == "dormancy_policy")
        assert check.passed is False
        assert check.severity == "critical"

    def test_engine_accepts_json_source(self, tmp_path):
        path = _write_config(
            tmp_path,
            [{"module": "ai", "state": "archived", "rationale": "archive set"}],
        )
        engine = DomainCertificationEngine(dormancy_registry=JsonDormancySource(path))
        manifest = _manifest(modules=["ai/legacy.py"])
        check = next(c for c in engine.certify_domain(manifest).checks if c.check == "dormancy_policy")
        assert check.passed is False
        assert check.severity == "critical"

    def test_canonical_domains_all_certify_with_tenth_check(self):
        engine = DomainCertificationEngine()
        verdict = engine.platform_certification(list_domains())
        assert verdict["verdict"] == "CERTIFIED"
        assert verdict["score"] == 100
        assert all(
            any(c["check"] == "dormancy_policy" and c["passed"] for c in domain["checks"])
            for domain in verdict["domains"]
        )

    def test_engine_constructed_without_args_is_backward_compatible(self):
        engine = DomainCertificationEngine()
        assert isinstance(engine.dormancy_registry, DormancySource)
        clean = engine.certify_domain(_manifest())
        assert clean.passed is True
        assert clean.score == 100
