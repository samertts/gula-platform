from __future__ import annotations

import pytest
from app.domain_platform.binding import WorkspaceBinding, WorkspaceBindingError, WorkspaceBindingRegistry
from app.domain_platform.certification import CERTIFICATION_CHECKS, DomainCertificationEngine
from app.domain_platform.contracts import ContractRegistry, CrossDomainGateway
from app.domain_platform.core import (
    ALLOWED_CROSS_DOMAIN_CHANNELS,
    BLUEPRINT_SECTIONS,
    DOMAIN_LIFECYCLE_TRANSITIONS,
    ContractKind,
    DomainContract,
    DomainManifest,
    assert_blueprint_rule,
    lifecycle_transition_allowed,
)
from app.domain_platform.isolation import (
    DomainIsolationReport,
    IsolationFinding,
    IsolationValidator,
)
from app.domain_platform.lifecycle import DomainLifecycle, LifecycleError
from app.domain_platform.manifest import (
    CANONICAL_DOMAINS,
    FORBIDDEN_DOMAIN_OWNERSHIP,
    list_domains,
    workspace_ui_for,
)
from app.domain_platform.shared_core import (
    SHARED_CORE_CATALOG,
    SHARED_CORE_SERVICES,
    is_infrastructure_reimplementation,
    is_shared_core_import,
)
from app.domain_platform.versioning import (
    InvalidVersionError,
    DomainVersionRegistry,
    compare_versions,
    is_compatible,
    parse_version,
)

MANDATORY_SHARED_CORE = {"identity", "authentication", "authorization", "audit", "event_bus"}


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
        "shared_core": {svc: "shared_core" for svc in MANDATORY_SHARED_CORE},
    }
    base.update(overrides)
    return DomainManifest(**base)


# ── Blueprint ──────────────────────────────────────────────────────────────


class TestBlueprint:
    def test_blueprint_sections(self):
        assert list(BLUEPRINT_SECTIONS) == [
            "entities",
            "services",
            "policies",
            "api",
            "events",
            "workflows",
            "reports",
            "ui",
        ]

    def test_blueprint_rule_accepts_bound_workspace(self):
        assert assert_blueprint_rule(_manifest()) is None

    def test_blueprint_rule_rejects_foreign_workspace(self):
        with pytest.raises(ValueError):
            assert_blueprint_rule(_manifest(workspace_type="pharmacy"))

    def test_manifest_round_trip(self):
        manifest = _manifest()
        assert manifest.code == "laboratory"
        assert manifest.version == "1.0.0"
        assert manifest.workspace_type == "laboratory"
        assert set(manifest.blueprint) <= set(BLUEPRINT_SECTIONS)

    def test_canonical_domains_complete(self):
        codes = set(CANONICAL_DOMAINS)
        for code in [
            "laboratory",
            "pharmacy",
            "radiology",
            "hospital",
            "blood_bank",
            "public_health",
            "insurance",
            "emergency",
            "research",
            "citizen_portal",
            "provider_portal",
        ]:
            assert code in codes

    def test_every_canonical_domain_has_full_blueprint(self):
        for manifest in CANONICAL_DOMAINS.values():
            assert set(manifest.blueprint) <= set(BLUEPRINT_SECTIONS), manifest.code
            assert manifest.workspace_type, manifest.code

    def test_canonical_domains_are_bound_to_workspaces(self):
        for manifest in CANONICAL_DOMAINS.values():
            assert manifest.workspace_type, manifest.code

    def test_forbidden_ownership_empty(self):
        assert FORBIDDEN_DOMAIN_OWNERSHIP == {}

    def test_workspace_ui_is_scoped(self):
        for manifest in CANONICAL_DOMAINS.values():
            allowed = workspace_ui_for(manifest.workspace_type)
            assert all(item in allowed for item in manifest.ui)


# ── Shared Core ────────────────────────────────────────────────────────────


class TestSharedCore:
    def test_catalog_matches_service_list(self):
        assert set(SHARED_CORE_CATALOG) == set(SHARED_CORE_SERVICES)

    def test_shared_core_has_core_services(self):
        for service in ["identity", "authentication", "authorization", "organizations", "audit"]:
            assert service in SHARED_CORE_CATALOG

    def test_shared_core_provides_key_infrastructure(self):
        for service in [
            "event_bus",
            "notifications",
            "workflow_engine",
            "rule_engine",
            "barcode_engine",
            "qr_engine",
            "files",
            "scheduler",
        ]:
            assert service in SHARED_CORE_CATALOG

    def test_shared_core_import_detected(self):
        assert is_shared_core_import("app.identity.services.identity_service")
        assert is_shared_core_import("shared.security.encryption")
        assert is_shared_core_import("app.fhir.mappers")

    def test_non_shared_import_not_detected(self):
        assert is_shared_core_import("app.lims.services.blood_service") is False
        assert is_shared_core_import("app.pharmacy.services.drug_service") is False

    def test_infrastructure_reimplementation_detected(self):
        assert "cache" in is_infrastructure_reimplementation(
            "import redis\nclient = redis.Redis(host='x')"
        )
        assert "qr" in is_infrastructure_reimplementation("import qrcode\nimg = qrcode.make('x')")
        assert "queue" in is_infrastructure_reimplementation("from celery import Celery")
        assert "database" in is_infrastructure_reimplementation("engine = create_engine('x')")

    def test_domain_entities_do_not_trip_signals(self):
        assert is_infrastructure_reimplementation("class RareDiseaseRegistry:") == []
        assert is_infrastructure_reimplementation("def generate_qr(self, citizen_id):") == []


# ── Lifecycle ──────────────────────────────────────────────────────────────


class TestLifecycle:
    def test_install_enters_installed(self):
        lifecycle = DomainLifecycle("laboratory")
        assert lifecycle.install(version="1.0.0") == "installed"
        assert lifecycle.state.value == "installed"

    def test_activate_from_installed(self):
        lifecycle = DomainLifecycle("laboratory")
        lifecycle.install(version="1.0.0")
        assert lifecycle.activate() == "active"
        assert lifecycle.state.value == "active"

    def test_invalid_transition_rejected(self):
        lifecycle = DomainLifecycle("laboratory")
        lifecycle.install(version="1.0.0")
        with pytest.raises(LifecycleError):
            lifecycle.suspend()

    def test_suspend_activate_cycle(self):
        lifecycle = DomainLifecycle("laboratory")
        lifecycle.install(version="1.0.0")
        lifecycle.activate()
        assert lifecycle.suspend() == "suspended"
        assert lifecycle.state.value == "suspended"
        assert lifecycle.activate() == "active"
        assert lifecycle.state.value == "active"

    def test_upgrade_through_upgrading(self):
        lifecycle = DomainLifecycle("laboratory")
        lifecycle.install(version="1.0.0")
        lifecycle.activate()
        assert lifecycle.upgrade("1.1.0") == "active"
        assert lifecycle.state.value == "active"
        assert lifecycle.versions.latest.version == "1.1.0"

    def test_upgrade_rejects_lower_version(self):
        lifecycle = DomainLifecycle("laboratory")
        lifecycle.install(version="1.0.0")
        lifecycle.activate()
        with pytest.raises(LifecycleError):
            lifecycle.upgrade("0.9.0")

    def test_rollback_restores_version(self):
        lifecycle = DomainLifecycle("laboratory")
        lifecycle.install(version="1.0.0")
        lifecycle.activate()
        lifecycle.upgrade("1.1.0")
        assert lifecycle.rollback() == "1.0.0"

    def test_rollback_requires_previous_version(self):
        lifecycle = DomainLifecycle("laboratory")
        lifecycle.install(version="1.0.0")
        lifecycle.activate()
        with pytest.raises(LifecycleError):
            lifecycle.rollback()

    def test_transition_table_consistent(self):
        for state, targets in DOMAIN_LIFECYCLE_TRANSITIONS.items():
            for target in targets:
                assert lifecycle_transition_allowed(state, target)
            assert lifecycle_transition_allowed(state, "made_up") is False

    def test_all_operations_record_events(self):
        lifecycle = DomainLifecycle("laboratory")
        lifecycle.install(version="1.0.0")
        lifecycle.activate()
        lifecycle.suspend()
        lifecycle.activate()
        assert len(lifecycle.history) == 4
        assert {event.action for event in lifecycle.history} == {"install", "activate", "suspend"}

    def test_health_check(self):
        lifecycle = DomainLifecycle("laboratory")
        lifecycle.install(version="1.0.0")
        lifecycle.activate()
        health = lifecycle.health_check()
        assert health["state"] == "active"
        assert health["version"] == "1.0.0"
        assert health["healthy"] is True

    def test_metrics(self):
        lifecycle = DomainLifecycle("laboratory")
        lifecycle.install(version="1.0.0")
        lifecycle.activate()
        metrics = lifecycle.metrics()
        assert metrics["state"] == "active"
        assert metrics["transition_count"] == 2

    def test_backup_and_restore(self):
        lifecycle = DomainLifecycle("laboratory")
        lifecycle.install(version="1.0.0")
        backup_id = lifecycle.backup(label="pre-upgrade")
        lifecycle.restore(backup_id)
        assert lifecycle.backups[0]["label"] == "pre-upgrade"


# ── Versioning ─────────────────────────────────────────────────────────────


class TestVersioning:
    def test_parse_valid(self):
        assert parse_version("1.2.3") == (1, 2, 3)

    def test_parse_invalid(self):
        with pytest.raises(InvalidVersionError):
            parse_version("not-a-version")

    def test_compare(self):
        assert compare_versions("1.2.3", "1.2.4") < 0
        assert compare_versions("2.0.0", "1.9.9") > 0
        assert compare_versions("1.0.0", "1.0.0") == 0

    def test_is_compatible_patch_and_minor(self):
        assert is_compatible("1.0.0", "1.0.1")
        assert is_compatible("1.0.0", "1.5.0")

    def test_is_compatible_major_is_breaking(self):
        assert is_compatible("1.0.0", "2.0.0") is False

    def test_registry_rejects_lower_version(self):
        registry = DomainVersionRegistry("laboratory")
        registry.add("1.0.0", certified=True)
        with pytest.raises(InvalidVersionError):
            registry.add("0.9.0")

    def test_registry_rejects_duplicate_version(self):
        registry = DomainVersionRegistry("laboratory")
        registry.add("1.0.0", certified=True)
        with pytest.raises(InvalidVersionError):
            registry.add("1.0.0", certified=True)

    def test_registry_accepts_breaking_only_if_certified(self):
        registry = DomainVersionRegistry("laboratory")
        registry.add("1.0.0", certified=True)
        with pytest.raises(InvalidVersionError):
            registry.add("2.0.0", certified=False)
        registry.add("2.0.0", certified=True)
        assert registry.latest.version == "2.0.0"


# ── Contracts ──────────────────────────────────────────────────────────────


class TestContracts:
    def _contract(self, contract_id: str, **overrides) -> DomainContract:
        base = {
            "contract_id": contract_id,
            "provider_domain": "laboratory",
            "consumer_domain": "pharmacy",
            "kind": ContractKind.rest,
            "version": "1.0.0",
            "endpoint": "/api/laboratory/results",
            "documentation_url": "https://docs.gula.iq/laboratory/results",
            "status": "published",
        }
        base.update(overrides)
        return DomainContract(**base)

    def test_registry_accepts_valid_contract(self):
        registry = ContractRegistry()
        contract = self._contract("ct-1")
        registry.register(contract)
        assert registry.get("ct-1") == contract

    def test_registry_rejects_self_reference(self):
        registry = ContractRegistry()
        with pytest.raises(ValueError):
            registry.register(self._contract("ct-2", consumer_domain="laboratory"))

    def test_registry_rejects_unversioned(self):
        registry = ContractRegistry()
        with pytest.raises(InvalidVersionError):
            registry.register(self._contract("ct-3", version=""))

    def test_registry_rejects_undocumented(self):
        registry = ContractRegistry()
        with pytest.raises(ValueError):
            registry.register(self._contract("ct-4", documentation_url=""))

    def test_registry_rejects_unknown_kind(self):
        registry = ContractRegistry()
        with pytest.raises(ValueError):
            registry.register(self._contract("ct-5", kind="ftp"))

    def test_duplicate_rejected(self):
        registry = ContractRegistry()
        registry.register(self._contract("ct-6"))
        with pytest.raises(ValueError):
            registry.register(self._contract("ct-6"))

    def test_enforce_tracks_violations(self):
        registry = ContractRegistry()
        with pytest.raises(ValueError):
            registry.register(self._contract("ct-7", consumer_domain="laboratory"))
        report = registry.enforce()
        assert report.passes is False
        assert report.violations

    def test_gateway_allows_published_contract(self):
        registry = ContractRegistry()
        registry.register(self._contract("ct-8"))
        gateway = CrossDomainGateway(registry)
        assert gateway.resolve("laboratory", "pharmacy", ContractKind.rest) is not None
        assert gateway.assert_allowed("laboratory", "pharmacy", ContractKind.rest)

    def test_gateway_denies_without_contract(self):
        gateway = CrossDomainGateway(ContractRegistry())
        assert gateway.resolve("pharmacy", "laboratory", ContractKind.rest) is None
        with pytest.raises(PermissionError):
            gateway.assert_allowed("pharmacy", "laboratory", ContractKind.rest)

    def test_gateway_denies_unpublished(self):
        registry = ContractRegistry()
        registry.register(self._contract("ct-9", status="draft"))
        assert CrossDomainGateway(registry).resolve("laboratory", "pharmacy", ContractKind.rest) is None

    def test_allowed_channels(self):
        assert ALLOWED_CROSS_DOMAIN_CHANNELS == ("public_api", "fhir_api", "hl7", "event_bus", "contract")


# ── Workspace binding ──────────────────────────────────────────────────────


class TestWorkspaceBinding:
    def test_binding_for_domain(self):
        registry = WorkspaceBindingRegistry()
        binding = registry.binding_for_domain("laboratory")
        assert isinstance(binding, WorkspaceBinding)
        assert binding.workspace_type == "laboratory"

    def test_unknown_domain_has_no_binding(self):
        registry = WorkspaceBindingRegistry()
        assert registry.binding_for_domain("not_a_domain") is None

    def test_domain_for_workspace(self):
        registry = WorkspaceBindingRegistry()
        assert registry.domain_for_workspace("laboratory") == "laboratory"
        assert registry.domain_for_workspace("citizen") == "citizen_portal"

    def test_assert_domain_workspace_passes_for_binding(self):
        registry = WorkspaceBindingRegistry()
        registry.assert_domain_workspace("laboratory", "laboratory")

    def test_assert_domain_workspace_rejects_mismatch(self):
        registry = WorkspaceBindingRegistry()
        with pytest.raises(WorkspaceBindingError):
            registry.assert_domain_workspace("laboratory", "pharmacy")

    def test_ui_scoped_to_own_workspace(self):
        registry = WorkspaceBindingRegistry()
        ui = registry.binding_for_domain("laboratory").ui
        for item in ui:
            registry.assert_ui_allowed("laboratory", item)
        with pytest.raises(WorkspaceBindingError):
            registry.assert_ui_allowed("laboratory", "pharmacy_ui")


# ── Isolation ──────────────────────────────────────────────────────────────


class TestIsolation:
    def _domain(self, code: str, modules: list[str], tmp_path) -> DomainManifest:
        manifest = _manifest(code=code)
        manifest.modules = modules
        return manifest

    def test_cross_domain_import_detected(self, tmp_path):
        (tmp_path / "alpha").mkdir()
        (tmp_path / "beta").mkdir()
        (tmp_path / "alpha" / "models.py").write_text("from beta.services import do_thing\n")
        (tmp_path / "beta" / "services.py").write_text("def do_thing():\n    pass\n")
        validator = IsolationValidator(
            [self._domain("laboratory", ["alpha/models.py"], tmp_path),
             self._domain("pharmacy", ["beta/services.py"], tmp_path)],
            repo_root=str(tmp_path),
        )
        findings = validator.detect_cross_domain_imports()
        assert len(findings) == 1
        assert findings[0].kind == "cross_domain_import"

    def test_no_cross_domain_via_shared_core(self, tmp_path):
        (tmp_path / "alpha").mkdir()
        (tmp_path / "alpha" / "models.py").write_text(
            "from app.identity.services.identity_service import IdentityService\n"
        )
        validator = IsolationValidator(
            [self._domain("laboratory", ["alpha/models.py"], tmp_path)],
            repo_root=str(tmp_path),
        )
        assert validator.detect_cross_domain_imports() == []

    def test_permission_leakage_detected(self):
        alpha = _manifest(code="laboratory", api=["/api/v1/laboratory/results"])
        beta = _manifest(code="pharmacy", api=["/api/v1/pharmacy/orders"])
        validator = IsolationValidator([alpha, beta])
        findings = validator.detect_permission_leakage()
        assert len(findings) == 1
        assert findings[0].kind == "permission_leakage"

    def test_no_permission_leakage_within_own_namespace(self):
        alpha = _manifest(code="laboratory", api=["/api/v1/laboratory/results"])
        validator = IsolationValidator([alpha])
        assert validator.detect_permission_leakage() == []

    def test_circular_dependency_detected(self, tmp_path):
        (tmp_path / "alpha").mkdir()
        (tmp_path / "alpha" / "a.py").write_text("import alpha.b\n")
        (tmp_path / "alpha" / "b.py").write_text("import alpha.a\n")
        validator = IsolationValidator(
            [self._domain("laboratory", ["alpha/a.py", "alpha/b.py"], tmp_path)],
            repo_root=str(tmp_path),
        )
        findings = validator.detect_circular_dependencies()
        assert len(findings) >= 1
        assert findings[0].kind == "circular_dependency"

    def test_direct_db_coupling_detected(self, tmp_path):
        (tmp_path / "alpha").mkdir()
        (tmp_path / "alpha" / "db.py").write_text(
            "from sqlalchemy import create_engine\nengine = create_engine('postgresql://x')\n"
        )
        validator = IsolationValidator(
            [self._domain("laboratory", ["alpha/db.py"], tmp_path)],
            repo_root=str(tmp_path),
        )
        findings = validator.detect_direct_db_coupling()
        assert len(findings) == 1
        assert findings[0].kind == "direct_db_coupling"

    def test_table_overlap_detected(self):
        alpha = _manifest(code="laboratory", tables=["results"])
        beta = _manifest(code="pharmacy", tables=["results"])
        validator = IsolationValidator([alpha, beta])
        findings = validator.detect_table_overlaps()
        assert len(findings) == 1
        assert findings[0].kind == "cross_domain_table"

    def test_run_builds_report(self, tmp_path):
        alpha = _manifest(code="laboratory")
        beta = _manifest(code="pharmacy")
        report = IsolationValidator([alpha, beta]).run()
        assert isinstance(report, DomainIsolationReport)
        assert report.passes is True

    def test_report_tracks_categories(self):
        report = DomainIsolationReport(
            cross_domain=[IsolationFinding(kind="cross_domain_import", severity="critical", message="x")],
            db_coupling=[IsolationFinding(kind="direct_db_coupling", severity="critical", message="y")],
        )
        assert report.passes is False
        assert len(report.all_findings) == 2


# ── Certification ──────────────────────────────────────────────────────────


class TestCertification:
    def test_certification_checks_complete(self):
        assert len(CERTIFICATION_CHECKS) == 9

    def test_certify_clean_domain(self):
        engine = DomainCertificationEngine()
        result = engine.certify_domain(_manifest())
        assert result.passed is True
        assert result.score == 100

    def test_certify_fails_on_isolation_findings(self):
        report = DomainIsolationReport(
            db_coupling=[
                IsolationFinding(
                    kind="direct_db_coupling",
                    severity="critical",
                    message="domain 'laboratory' creates its own engine",
                )
            ]
        )
        engine = DomainCertificationEngine(isolation_report=report)
        result = engine.certify_domain(_manifest())
        assert result.passed is False
        assert result.score < 100

    def test_certify_missing_shared_core_fails(self):
        engine = DomainCertificationEngine()
        manifest = _manifest(shared_core={"identity": "shared_core"})
        result = engine.certify_domain(manifest)
        assert result.passed is False
        assert any(c.check == "shared_core_usage_100" and not c.passed for c in result.checks)

    def test_certify_invalid_version_fails(self):
        engine = DomainCertificationEngine()
        result = engine.certify_domain(_manifest(version="not-semver"))
        assert result.passed is False
        assert any(c.check == "backward_compatibility" and not c.passed for c in result.checks)

    def test_portal_domain_cannot_administer(self):
        engine = DomainCertificationEngine()
        manifest = _manifest(code="citizen_portal", services=["admin_service"])
        result = engine.certify_domain(manifest)
        assert any(
            c.check == "no_cross_domain_administration" and not c.passed for c in result.checks
        )

    def test_platform_certification_aggregate(self):
        engine = DomainCertificationEngine()
        verdict = engine.platform_certification([_manifest(code="laboratory"), _manifest(code="pharmacy")])
        assert verdict["verdict"] == "CERTIFIED"
        assert verdict["passed"] == 2
        assert verdict["total"] == 2
        assert verdict["score"] == 100

    def test_canonical_domains_all_certify(self):
        engine = DomainCertificationEngine()
        verdict = engine.platform_certification(list_domains())
        assert verdict["verdict"] == "CERTIFIED"
        assert verdict["score"] == 100
