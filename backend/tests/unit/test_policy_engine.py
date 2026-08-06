"""PROGRAM-BETA-COMMIT-0.2 — Architecture Policy Engine tests (ADR-027).

Covers:
  * the common ``Policy`` interface (engine consumes any implementation)
  * severity/status semantics and deterministic verdict aggregation
  * the ordered ``PolicyRegistry`` and the ``PolicyEngine`` run loop
  * baselines/waivers (acknowledged debt never blocks; unknown debt fails)
  * machine-readable (JSON) and human-readable (Markdown) reports
  * the Dormancy Policy as the first implemented policy (per-domain +
    repository modes, exact Commit 0.1 semantics)
  * the nine registered-but-disabled future policies (catalog lockstep)
  * backward compatibility: certification still 10 checks, 11/11 CERTIFIED
"""

from __future__ import annotations

import json

import pytest
from app.domain_platform.certification import CERTIFICATION_CHECKS, DomainCertificationEngine
from app.domain_platform.core import DomainManifest
from app.domain_platform.dormancy import (
    DormancyRegistry,
    ModuleLifecycleState,
    load_default_dormancy_source,
)
from app.domain_platform.manifest import list_domains
from app.domain_platform.policies import (
    POLICY_CATALOG,
    Policy,
    PolicyBaseline,
    PolicyContext,
    PolicyEngine,
    PolicyFinding,
    PolicyRegistry,
    PolicyReport,
    PolicyResult,
    PolicySeverity,
    PolicyStatus,
    PolicyWaiver,
    build_default_registry,
    compute_status,
)
from app.domain_platform.policies.dormancy_policy import DormancyPolicy

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
        "shared_core": dict.fromkeys(MANDATORY_SHARED_CORE, "shared_core"),
    }
    base.update(overrides)
    return DomainManifest(**base)


class _StubPolicy:
    """A minimal, structurally-valid Policy the engine can consume."""

    def __init__(
        self,
        name: str = "stub_policy",
        *,
        enabled: bool = True,
        status: PolicyStatus = PolicyStatus.PASS,
        findings: list[PolicyFinding] | None = None,
    ) -> None:
        self.name = name
        self.description = f"{name} test policy"
        self.enabled = enabled
        self._status = status
        self._findings = findings or []
        self.calls = 0

    def evaluate(self, context: PolicyContext) -> PolicyResult:
        self.calls += 1
        return PolicyResult(
            policy=self.name,
            status=self._status,
            summary=f"{self.name} evaluated",
            findings=self._findings,
        )


def _finding(
    code: str = "TEST-001",
    severity: PolicySeverity = PolicySeverity.MINOR,
    *,
    message: str = "finding",
    path: str | None = None,
    domain: str | None = None,
) -> PolicyFinding:
    return PolicyFinding(code=code, severity=severity, message=message, path=path, domain=domain)


# ── Policy interface ────────────────────────────────────────────────────────


class TestPolicyInterface:
    def test_engine_consumes_any_policy_implementation(self):
        registry = PolicyRegistry().register(_StubPolicy())
        report = PolicyEngine(registry=registry).run(PolicyContext())
        assert report.verdict == "PASS"
        assert report.results[0].policy == "stub_policy"

    def test_concrete_policies_satisfy_protocol(self):
        from app.domain_platform.policies.dormancy_policy import DormancyPolicy
        from app.domain_platform.policies.future import LIFECYCLE_POLICY

        assert isinstance(DormancyPolicy(), Policy)
        assert isinstance(LIFECYCLE_POLICY, Policy)

    def test_runtime_check_rejects_incomplete_policy(self):
        class _Broken:
            name = "broken"

        assert isinstance(_Broken(), Policy) is False

    def test_disabled_policy_is_never_executed(self):
        stub = _StubPolicy(enabled=False)
        registry = PolicyRegistry().register(stub)
        report = PolicyEngine(registry=registry).run(PolicyContext())
        assert stub.calls == 0
        assert report.results == []
        assert report.verdict == "PASS"


# ── Severity / status semantics ─────────────────────────────────────────────


class TestSeverityAndStatus:
    def test_severity_ordering(self):
        rank = {PolicySeverity.INFO: 0, PolicySeverity.MINOR: 1, PolicySeverity.MAJOR: 2, PolicySeverity.CRITICAL: 3}
        assert rank[PolicySeverity.INFO] < rank[PolicySeverity.CRITICAL]

    @pytest.mark.parametrize(
        ("severities", "expected"),
        [
            ([], PolicyStatus.PASS),
            ([PolicySeverity.INFO], PolicyStatus.PASS),
            ([PolicySeverity.MINOR], PolicyStatus.WARN),
            ([PolicySeverity.MAJOR], PolicyStatus.FAIL),
            ([PolicySeverity.CRITICAL], PolicyStatus.FAIL),
            ([PolicySeverity.INFO, PolicySeverity.MINOR], PolicyStatus.WARN),
            ([PolicySeverity.INFO, PolicySeverity.MAJOR], PolicyStatus.FAIL),
            ([PolicySeverity.MINOR, PolicySeverity.CRITICAL], PolicyStatus.FAIL),
        ],
    )
    def test_compute_status_deterministic(self, severities, expected):
        assert compute_status([_finding(severity=s) for s in severities]) is expected

    def test_result_severity_is_worst_finding(self):
        result = PolicyResult(
            policy="p",
            status=PolicyStatus.FAIL,
            summary="s",
            findings=[_finding(severity=PolicySeverity.INFO), _finding(severity=PolicySeverity.CRITICAL)],
        )
        assert result.severity is PolicySeverity.CRITICAL
        assert result.passed is False

    def test_result_severity_info_when_clean(self):
        result = PolicyResult(policy="p", status=PolicyStatus.PASS, summary="s")
        assert result.severity is PolicySeverity.INFO
        assert result.passed is True


# ── PolicyRegistry ──────────────────────────────────────────────────────────


class TestPolicyRegistry:
    def test_register_get_names_in_order(self):
        registry = PolicyRegistry()
        registry.register(_StubPolicy("b"))
        registry.register(_StubPolicy("a"))
        assert registry.names() == ["b", "a"]
        assert registry.get("b").name == "b"

    def test_duplicate_registration_rejected(self):
        registry = PolicyRegistry()
        registry.register(_StubPolicy("x"))
        with pytest.raises(ValueError):
            registry.register(_StubPolicy("x"))

    def test_unknown_policy_rejected(self):
        with pytest.raises(KeyError):
            PolicyRegistry().get("nope")

    def test_enabled_returns_only_enabled_in_order(self):
        registry = PolicyRegistry()
        registry.register(_StubPolicy("one", enabled=False))
        registry.register(_StubPolicy("two", enabled=True))
        registry.register(_StubPolicy("three", enabled=True))
        assert [p.name for p in registry.enabled()] == ["two", "three"]

    def test_to_manifest_documents_catalog(self):
        registry = PolicyRegistry()
        registry.register(_StubPolicy("a", enabled=True))
        registry.register(_StubPolicy("b", enabled=False))
        manifest = registry.to_manifest()
        assert manifest[0] == {"name": "a", "description": "a test policy", "enabled": True}
        assert manifest[1]["enabled"] is False

    def test_default_registry_is_catalog_lockstep(self):
        registry = build_default_registry()
        assert len(registry) == len(POLICY_CATALOG)
        assert registry.names() == list(POLICY_CATALOG)


# ── PolicyEngine run loop ───────────────────────────────────────────────────


class TestPolicyEngine:
    def test_runs_enabled_policies_in_registration_order(self):
        registry = PolicyRegistry()
        registry.register(_StubPolicy("first", status=PolicyStatus.PASS))
        registry.register(_StubPolicy("second", status=PolicyStatus.WARN))
        report = PolicyEngine(registry=registry).run(PolicyContext())
        assert [r.policy for r in report.results] == ["first", "second"]

    def test_verdict_fail_when_any_policy_fails(self):
        registry = PolicyRegistry()
        registry.register(_StubPolicy("ok"))
        registry.register(
            _StubPolicy("bad", status=PolicyStatus.FAIL, findings=[_finding(severity=PolicySeverity.MAJOR)])
        )
        report = PolicyEngine(registry=registry).run(PolicyContext())
        assert report.verdict == "FAIL"

    def test_verdict_warn_when_only_warn_policies(self):
        registry = PolicyRegistry().register(
            _StubPolicy("warn", status=PolicyStatus.WARN, findings=[_finding(severity=PolicySeverity.MINOR)])
        )
        report = PolicyEngine(registry=registry).run(PolicyContext())
        assert report.verdict == "WARN"

    def test_verdict_pass_when_all_clean(self):
        registry = PolicyRegistry().register(_StubPolicy("ok"))
        assert PolicyEngine(registry=registry).run(PolicyContext()).verdict == "PASS"

    def test_skipped_policies_do_not_affect_verdict(self):
        from app.domain_platform.policies.future import LIFECYCLE_POLICY

        registry = PolicyRegistry()
        registry.register(LIFECYCLE_POLICY)
        registry.register(_StubPolicy("ok"))
        report = PolicyEngine(registry=registry).run(PolicyContext())
        assert report.verdict == "PASS"
        assert all(r.status is not PolicyStatus.SKIPPED for r in report.results)

    def test_results_are_deterministic(self):
        registry = build_default_registry()
        first = PolicyEngine(registry=registry).run(PolicyContext())
        second = PolicyEngine(registry=registry).run(PolicyContext())
        assert [r.to_dict() for r in first.results] == [r.to_dict() for r in second.results]

    def test_report_is_byte_identical_across_runs(self):
        registry = build_default_registry()
        context = PolicyContext(domains=list_domains(), dormancy_source=load_default_dormancy_source())
        first = PolicyEngine(registry=registry).run(context)
        second = PolicyEngine(registry=registry).run(context)
        assert first.to_dict() == second.to_dict()
        assert json.dumps(first.to_dict(), indent=2, sort_keys=True) == json.dumps(
            second.to_dict(), indent=2, sort_keys=True
        )
        assert first.render_markdown() == second.render_markdown()
        assert "generated_at" not in first.to_dict()
        assert "duration_ms" not in first.results[0].to_dict()

    def test_separate_engines_produce_identical_output(self):
        context = PolicyContext(domains=list_domains(), dormancy_source=load_default_dormancy_source())
        first = PolicyEngine(registry=build_default_registry()).run(context)
        second = PolicyEngine(registry=build_default_registry()).run(context)
        assert first.to_dict() == second.to_dict()
        assert first.render_markdown() == second.render_markdown()


# ── Baselines / waivers ─────────────────────────────────────────────────────


class TestPolicyBaseline:
    def test_missing_file_is_empty_baseline(self, tmp_path):
        baseline = PolicyBaseline.load(tmp_path / "nope.json")
        assert baseline.waivers == []
        assert baseline.to_dict() == {"waivers": []}

    def test_invalid_json_raises(self, tmp_path):
        path = tmp_path / "baseline.json"
        path.write_text("{not json", encoding="utf-8")
        with pytest.raises(ValueError):
            PolicyBaseline.load(path)

    def test_waivers_not_list_raises(self, tmp_path):
        path = tmp_path / "baseline.json"
        path.write_text(json.dumps({"waivers": "x"}), encoding="utf-8")
        with pytest.raises(ValueError):
            PolicyBaseline.load(path)

    def test_waiver_missing_fields_raises(self, tmp_path):
        path = tmp_path / "baseline.json"
        path.write_text(json.dumps({"waivers": [{"policy": "x"}]}), encoding="utf-8")
        with pytest.raises(ValueError):
            PolicyBaseline.load(path)

    def test_loads_waivers_from_file(self, tmp_path):
        path = tmp_path / "baseline.json"
        path.write_text(
            json.dumps({"waivers": [{"policy": "p", "code": "P-1", "path": "a.py"}]}),
            encoding="utf-8",
        )
        baseline = PolicyBaseline.load(path)
        assert baseline.waivers[0].policy == "p"
        assert baseline.waivers[0].code == "P-1"
        assert baseline.waivers[0].path == "a.py"

    def test_waiver_removes_finding_and_recomputes_status(self):
        baseline = PolicyBaseline([PolicyWaiver("p", "P-1")])
        result = PolicyResult(
            policy="p",
            status=PolicyStatus.FAIL,
            summary="s",
            findings=[_finding(code="P-1", severity=PolicySeverity.CRITICAL)],
        )
        waived = baseline.waive(result)
        assert waived.status is PolicyStatus.PASS
        assert waived.findings == []
        assert waived.waived == 1

    def test_waiver_respects_path(self):
        baseline = PolicyBaseline([PolicyWaiver("p", "P-1", path="a.py")])
        result = PolicyResult(
            policy="p",
            status=PolicyStatus.FAIL,
            summary="s",
            findings=[
                _finding(code="P-1", severity=PolicySeverity.CRITICAL, path="a.py"),
                _finding(code="P-1", severity=PolicySeverity.CRITICAL, path="b.py"),
            ],
        )
        waived = baseline.waive(result)
        assert waived.waived == 1
        assert [f.path for f in waived.findings] == ["b.py"]
        assert waived.status is PolicyStatus.FAIL

    def test_unmatched_waiver_keeps_failing(self):
        baseline = PolicyBaseline([PolicyWaiver("p", "OTHER")])
        result = PolicyResult(
            policy="p",
            status=PolicyStatus.FAIL,
            summary="s",
            findings=[_finding(code="P-1", severity=PolicySeverity.CRITICAL)],
        )
        waived = baseline.waive(result)
        assert waived.status is PolicyStatus.FAIL
        assert waived.waived == 0

    def test_waiver_policy_is_scoped(self):
        baseline = PolicyBaseline([PolicyWaiver("other", "P-1")])
        result = PolicyResult(
            policy="p",
            status=PolicyStatus.FAIL,
            summary="s",
            findings=[_finding(code="P-1", severity=PolicySeverity.CRITICAL)],
        )
        assert baseline.waive(result).status is PolicyStatus.FAIL


# ── PolicyReport (machine-readable + human-readable) ───────────────────────


class TestPolicyReport:
    def test_to_dict_is_machine_readable(self):
        registry = build_default_registry()
        report = PolicyEngine(registry=registry).run(PolicyContext())
        data = report.to_dict()
        assert data["engine"] == "architecture_policy_engine"
        assert data["verdict"] == "PASS"
        assert len(data["registered_policies"]) == 10
        assert data["results"][0]["policy"] == "dormancy_policy"
        assert data["results"][0]["status"] == "pass"
        assert "findings" in data["results"][0]
        json.dumps(data)  # must be JSON-serializable

    def test_render_markdown_is_human_readable(self):
        registry = PolicyRegistry()
        registry.register(
            _StubPolicy(
                "sample",
                status=PolicyStatus.WARN,
                findings=[_finding(code="S-1", severity=PolicySeverity.MINOR, path="x.py")],
            )
        )
        report = PolicyEngine(registry=registry).run(PolicyContext())
        text = report.render_markdown()
        assert "# Architecture Policy Engine" in text
        assert "sample" in text
        assert "warn" in text
        assert "S-1" in text

    def test_verdict_reflects_waived_debt(self):
        registry = PolicyRegistry().register(
            _StubPolicy("p", status=PolicyStatus.FAIL, findings=[_finding(code="P-1", severity=PolicySeverity.CRITICAL)])
        )
        baseline = PolicyBaseline([PolicyWaiver("p", "P-1")])
        report = PolicyEngine(registry=registry, baseline=baseline).run(PolicyContext())
        assert report.verdict == "PASS"
        assert report.results[0].waived == 1


# ── Dormancy Policy through the engine (first implemented policy) ──────────


class TestDormancyPolicyThroughEngine:
    def test_repo_mode_canonical_domains_pass(self):
        report = PolicyEngine(registry=build_default_registry()).run(
            PolicyContext(
                domains=list_domains(),
                dormancy_source=load_default_dormancy_source(),
            )
        )
        assert report.verdict == "PASS"
        dormancy = next(r for r in report.results if r.policy == "dormancy_policy")
        assert dormancy.status is PolicyStatus.PASS
        assert dormancy.findings == []

    def test_engine_detects_archived_ownership(self):
        registry = build_default_registry()
        context = PolicyContext(
            domains=[_manifest(modules=["ai/agent.py"])],
            dormancy_source=load_default_dormancy_source(),
        )
        report = PolicyEngine(registry=registry).run(context)
        assert report.verdict == "FAIL"
        dormancy = next(r for r in report.results if r.policy == "dormancy_policy")
        assert dormancy.status is PolicyStatus.FAIL
        finding = dormancy.findings[0]
        assert finding.code == "DORMANCY-001"
        assert finding.severity is PolicySeverity.CRITICAL

    def test_engine_detects_dormant_ownership(self):
        registry = build_default_registry()
        context = PolicyContext(
            domains=[_manifest(modules=["backend/app/national_data"])],
            dormancy_source=load_default_dormancy_source(),
        )
        report = PolicyEngine(registry=registry).run(context)
        dormancy = next(r for r in report.results if r.policy == "dormancy_policy")
        assert dormancy.status is PolicyStatus.FAIL
        finding = dormancy.findings[0]
        assert finding.code == "DORMANCY-002"
        assert finding.severity is PolicySeverity.MAJOR

    def test_undeclared_modules_warn_with_minor_finding(self):
        registry = build_default_registry()
        context = PolicyContext(
            domains=[_manifest(modules=["backend/app/lims/models.py"])],
            dormancy_source=load_default_dormancy_source(),
        )
        report = PolicyEngine(registry=registry).run(context)
        assert report.verdict == "WARN"
        dormancy = next(r for r in report.results if r.policy == "dormancy_policy")
        assert dormancy.status is PolicyStatus.WARN
        assert dormancy.passed is False
        finding = dormancy.findings[0]
        assert finding.code == "DORMANCY-003"
        assert finding.severity is PolicySeverity.MINOR
        assert "implicitly active_development" in dormancy.summary

    def test_policy_respects_injected_source(self):
        source = DormancyRegistry()
        source.register("app/example", ModuleLifecycleState.archived, "C1.4 archive set")
        registry = build_default_registry()
        context = PolicyContext(domains=[_manifest(modules=["app/example/old.py"])], dormancy_source=source)
        report = PolicyEngine(registry=registry).run(context)
        assert report.verdict == "FAIL"
        assert report.results[0].findings[0].severity is PolicySeverity.CRITICAL


# ── Realistic regression scenarios (Commit 0.2 strengthening) ──────────────


class TestRealisticRegressionScenarios:
    """PASS / WARN / FAIL per the DORMANCY-001..003 contract, waivers, and
    verdict aggregation over several policies at once."""

    def test_declared_active_domain_passes(self):
        source = DormancyRegistry()
        source.register("backend/app/lims", ModuleLifecycleState.active_development, "test")
        context = PolicyContext(
            domains=[_manifest(modules=["backend/app/lims/models.py"])],
            dormancy_source=source,
        )
        report = PolicyEngine(registry=build_default_registry()).run(context)
        assert report.verdict == "PASS"
        dormancy = next(r for r in report.results if r.policy == "dormancy_policy")
        assert dormancy.status is PolicyStatus.PASS
        assert dormancy.findings == []

    def test_undeclared_modules_warn(self):
        source = DormancyRegistry()
        source.register("backend/app/lims", ModuleLifecycleState.active_development, "test")
        context = PolicyContext(
            domains=[_manifest(modules=["backend/app/inventory/models.py"])],
            dormancy_source=source,
        )
        report = PolicyEngine(registry=build_default_registry()).run(context)
        assert report.verdict == "WARN"
        dormancy = next(r for r in report.results if r.policy == "dormancy_policy")
        assert dormancy.status is PolicyStatus.WARN
        assert dormancy.findings[0].code == "DORMANCY-003"
        assert dormancy.findings[0].severity is PolicySeverity.MINOR

    def test_dormant_owned_fails_major(self):
        source = DormancyRegistry()
        source.register("backend/app/national_data", ModuleLifecycleState.dormant, "test")
        context = PolicyContext(
            domains=[_manifest(modules=["backend/app/national_data/etl.py"])],
            dormancy_source=source,
        )
        report = PolicyEngine(registry=build_default_registry()).run(context)
        assert report.verdict == "FAIL"
        dormancy = next(r for r in report.results if r.policy == "dormancy_policy")
        assert dormancy.status is PolicyStatus.FAIL
        assert dormancy.severity is PolicySeverity.MAJOR
        assert dormancy.findings[0].code == "DORMANCY-002"

    def test_archived_owned_fails_critical(self):
        source = DormancyRegistry()
        source.register("edge_agent", ModuleLifecycleState.archived, "test")
        context = PolicyContext(
            domains=[_manifest(modules=["edge_agent/src/main.py"])],
            dormancy_source=source,
        )
        report = PolicyEngine(registry=build_default_registry()).run(context)
        assert report.verdict == "FAIL"
        dormancy = next(r for r in report.results if r.policy == "dormancy_policy")
        assert dormancy.status is PolicyStatus.FAIL
        assert dormancy.severity is PolicySeverity.CRITICAL
        assert dormancy.findings[0].code == "DORMANCY-001"

    def test_retired_owned_fails_critical(self):
        source = DormancyRegistry()
        source.register("legacy_sdk", ModuleLifecycleState.retired, "test")
        context = PolicyContext(
            domains=[_manifest(modules=["legacy_sdk/client.py"])],
            dormancy_source=source,
        )
        report = PolicyEngine(registry=build_default_registry()).run(context)
        assert report.verdict == "FAIL"
        dormancy = next(r for r in report.results if r.policy == "dormancy_policy")
        assert dormancy.status is PolicyStatus.FAIL
        assert dormancy.findings[0].code == "DORMANCY-001"

    def test_waiver_of_dormancy_finding_restores_pass(self):
        source = DormancyRegistry()
        source.register("backend/app/national_data", ModuleLifecycleState.dormant, "test")
        context = PolicyContext(
            domains=[_manifest(modules=["backend/app/national_data/etl.py"])],
            dormancy_source=source,
        )
        baseline = PolicyBaseline([PolicyWaiver("dormancy_policy", "DORMANCY-002")])
        report = PolicyEngine(registry=build_default_registry(), baseline=baseline).run(context)
        assert report.verdict == "PASS"
        dormancy = next(r for r in report.results if r.policy == "dormancy_policy")
        assert dormancy.status is PolicyStatus.PASS
        assert dormancy.waived == 1

    def test_multiple_policies_aggregate_verdict(self):
        source = DormancyRegistry()
        source.register("backend/app/lims", ModuleLifecycleState.active_development, "test")
        registry = PolicyRegistry()
        registry.register(DormancyPolicy(dormancy_source=source))
        registry.register(
            _StubPolicy(
                "hard_gate",
                status=PolicyStatus.FAIL,
                findings=[_finding(code="H-1", severity=PolicySeverity.CRITICAL)],
            )
        )
        report = PolicyEngine(registry=registry).run(PolicyContext(domains=[_manifest()]))
        assert report.verdict == "FAIL"
        assert [r.policy for r in report.results] == ["dormancy_policy", "hard_gate"]

    def test_execution_order_is_registration_order(self):
        registry = PolicyRegistry()
        registry.register(_StubPolicy("zeta"))
        registry.register(_StubPolicy("alpha"))
        registry.register(_StubPolicy("gamma"))
        report = PolicyEngine(registry=registry).run(PolicyContext())
        assert [r.policy for r in report.results] == ["zeta", "alpha", "gamma"]


# ── Configuration-only enablement (no engine redesign) ─────────────────────


class TestConfigOnlyEnablement:
    def test_flipping_enabled_flag_executes_without_engine_change(self):
        stub = _StubPolicy("gated", enabled=False)
        registry = PolicyRegistry().register(stub)
        engine = PolicyEngine(registry=registry)
        assert engine.run(PolicyContext()).results == []
        assert stub.calls == 0

        stub.enabled = True
        report = engine.run(PolicyContext())
        assert stub.calls == 1
        assert report.results[0].policy == "gated"
        assert report.verdict == "PASS"

    def test_future_policy_enabled_by_configuration(self):
        registry = build_default_registry()
        shared_core = registry.get("shared_core_policy")
        assert shared_core.enabled is False
        shared_core.enabled = True
        try:
            report = PolicyEngine(registry=registry).run(PolicyContext())
            names = [r.policy for r in report.results]
            assert "shared_core_policy" in names
            skipped = next(r for r in report.results if r.policy == "shared_core_policy")
            assert skipped.status is PolicyStatus.SKIPPED
            assert report.verdict == "PASS"
        finally:
            shared_core.enabled = False


# ── Single implementation: gate == certification == engine ────────────────


class TestSingleImplementation:
    def test_gate_report_equals_fresh_engine_report(self):
        from scripts.architecture.policy import run_policy_gate

        context = PolicyContext(
            domains=list_domains(),
            dormancy_source=load_default_dormancy_source(),
        )
        direct = PolicyEngine(registry=build_default_registry()).run(context)
        assert run_policy_gate()["report"] == direct.to_dict()

    def test_certification_uses_the_same_dormancy_rule(self):
        from app.domain_platform.policies.dormancy_policy import DormancyPolicy

        context = PolicyContext(
            domains=list_domains(),
            dormancy_source=load_default_dormancy_source(),
        )
        gate_status = next(
            r for r in PolicyEngine(registry=build_default_registry()).run(context).results
            if r.policy == "dormancy_policy"
        ).status
        policy_status = DormancyPolicy().evaluate(context).status
        certified = DomainCertificationEngine().platform_certification(list_domains())
        assert gate_status is PolicyStatus.PASS
        assert policy_status is PolicyStatus.PASS
        assert certified["verdict"] == "CERTIFIED"


# ── Future policies (catalog lockstep, disabled) ───────────────────────────


class TestFuturePolicies:
    def test_catalog_has_ten_policies(self):
        assert len(POLICY_CATALOG) == 10
        assert POLICY_CATALOG[0] == "dormancy_policy"

    def test_default_registry_enables_only_dormancy(self):
        registry = build_default_registry()
        assert [p.name for p in registry.enabled()] == ["dormancy_policy"]
        assert sum(1 for p in registry.to_manifest() if p["enabled"]) == 1
        assert sum(1 for p in registry.to_manifest() if not p["enabled"]) == 9

    def test_future_policies_evaluate_deterministic_skipped(self):
        from app.domain_platform.policies.future import FUTURE_POLICIES

        for policy in FUTURE_POLICIES:
            result = policy.evaluate(PolicyContext())
            assert result.status is PolicyStatus.SKIPPED
            assert result.findings == []
            assert "not yet implemented" in result.summary

    def test_future_policy_has_no_rule_body(self):
        from app.domain_platform.policies.future import FUTURE_POLICIES

        assert all(p.enabled is False for p in FUTURE_POLICIES)

    def test_all_catalog_entries_registered(self):
        registry = build_default_registry()
        assert all(name in registry for name in POLICY_CATALOG)


# ── Backward compatibility ──────────────────────────────────────────────────


class TestBackwardCompatibility:
    def test_certification_still_ten_checks(self):
        assert len(CERTIFICATION_CHECKS) == 10
        assert CERTIFICATION_CHECKS[-1] == "dormancy_policy"

    def test_engine_constructed_without_args_works(self):
        engine = DomainCertificationEngine()
        result = engine.certify_domain(_manifest())
        assert result.passed is True
        assert result.score == 100

    def test_check_10_delegation_preserves_semantics(self):
        engine = DomainCertificationEngine()
        for modules, expected_severity, expected_passed in [
            (["ai/agent.py"], "critical", False),
            (["backend/app/national_data"], "major", False),
            (["platform"], "info", True),
            (["backend/app/lims/models.py"], "minor", True),
            ([], "info", True),
        ]:
            manifest = _manifest(modules=modules)
            check = next(
                c for c in engine.certify_domain(manifest).checks if c.check == "dormancy_policy"
            )
            assert check.severity == expected_severity
            assert check.passed == expected_passed

    def test_canonical_platform_still_certified(self):
        verdict = DomainCertificationEngine().platform_certification(list_domains())
        assert verdict["verdict"] == "CERTIFIED"
        assert verdict["score"] == 100
        assert verdict["total"] == 11

    def test_policy_gate_consumes_report(self):
        from scripts.architecture.policy import run_policy_gate

        result = run_policy_gate()
        assert result["verdict"] == "PASS"
        assert result["passes"] is True
        assert result["report"]["engine"] == "architecture_policy_engine"
