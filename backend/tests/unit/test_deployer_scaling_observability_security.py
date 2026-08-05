"""Unit tests for GULA-DEPLOYER-001 — Phase 6 scaling + Phase 7 observability + Phase 8 security."""

from __future__ import annotations

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3]))

from scripts.deployer.core import ScalingPolicy, SecurityCheck
from scripts.deployer.observability import (
    DASHBOARDS,
    alert_rules,
    dashboard_links,
    observability_config,
    tracing_chain,
)
from scripts.deployer.scaling import (
    default_policies,
    kubernetes_readiness,
    scale_decision,
)
from scripts.deployer.security import (
    deployment_blocked,
    security_summary,
    verify_areas,
    verify_secrets,
)


class TestScaling:
    def test_default_policies_for_services(self):
        policies = default_policies(("backend", "frontend"))
        assert len(policies) == 2
        assert all(p.policy_id.startswith("SCL-") for p in policies)
        assert all(p.enabled is True for p in policies)

    def test_default_policy_bounds(self):
        policies = default_policies(("backend",))
        policy = policies[0]
        assert policy.min_replicas <= policy.max_replicas
        assert policy.mode == "horizontal"

    def test_worker_policy_uses_queue_mode(self):
        policies = default_policies(("worker",))
        assert policies[0].mode == "worker"
        assert policies[0].metric == "queue_depth"

    def _enabled(self, **kwargs) -> ScalingPolicy:
        return ScalingPolicy(
            policy_id=kwargs.get("policy_id", "SCL-1"),
            service=kwargs.get("service", "backend"),
            min_replicas=kwargs.get("min_replicas", 1),
            max_replicas=kwargs.get("max_replicas", 5),
            enabled=True,
        )

    def test_scale_up_within_bounds(self):
        policy = self._enabled()
        decision = scale_decision(policy, current=2, load=90.0)
        assert decision["replicas"] == 3
        assert decision["action"] == "scale_out"

    def test_scale_down_on_low_load(self):
        policy = self._enabled()
        decision = scale_decision(policy, current=4, load=20.0)
        assert decision["replicas"] == 3
        assert decision["action"] == "scale_in"

    def test_scale_respects_max(self):
        policy = self._enabled()
        decision = scale_decision(policy, current=5, load=99.0)
        assert decision["replicas"] == 5
        assert decision["action"] == "at_max"

    def test_scale_respects_min(self):
        policy = self._enabled(min_replicas=2)
        decision = scale_decision(policy, current=1, load=10.0)
        assert decision["replicas"] == 1
        assert decision["action"] == "hold"

    def test_scale_holds_mid_load(self):
        policy = self._enabled()
        decision = scale_decision(policy, current=3, load=50.0)
        assert decision["replicas"] == 3
        assert decision["action"] == "hold"

    def test_scale_disabled_holds(self):
        policy = ScalingPolicy(policy_id="SCL-1", service="backend", enabled=False)
        decision = scale_decision(policy, current=2, load=99.0)
        assert decision["replicas"] == 2
        assert decision["action"] == "hold"

    def test_kube_readiness_reports_hpa(self):
        policies = default_policies(("backend", "frontend"))
        readiness = kubernetes_readiness(policies)
        assert readiness["migratable"] is True
        assert any("HPA" in requirement for requirement in readiness["requires"])


class TestObservability:
    def test_config_for_all_services(self):
        configs = observability_config()
        names = {c.component for c in configs}
        assert names == {"prometheus", "grafana", "alertmanager", "loki", "tempo", "jaeger"}

    def test_configs_default_enabled(self):
        configs = observability_config()
        assert all(c.enabled is True for c in configs)

    def test_config_endpoints_present(self):
        configs = observability_config()
        assert all(c.endpoint for c in configs)

    def test_tracing_chain_uses_otel(self):
        chain = tracing_chain()
        assert chain["collector"] == "otel-collector:4317"
        assert set(chain["backends"]) == {"tempo", "jaeger"}

    def test_alert_rules_include_four(self):
        rules = alert_rules()
        assert len(rules) == 4
        names = {r["name"] for r in rules}
        assert names == {"HighApiLatencyP95", "DatabaseDown", "QueueBacklog", "DiskSpaceLow"}

    def test_alert_rules_have_exprs(self):
        for rule in alert_rules():
            assert rule["expr"]
            assert rule["severity"] in {"warning", "critical"}

    def test_dashboard_links_cover_six(self):
        configs = observability_config()
        links = dashboard_links(configs)
        assert len(links) == len(DASHBOARDS)
        assert all("/d/" in link for link in links)

    def test_dashboard_links_empty_without_grafana(self):
        configs = observability_config(("loki",))
        assert dashboard_links(configs) == []


class TestSecurity:
    def test_verify_secrets_detects_password(self):
        findings = verify_secrets("postgres_password = 'hunter2-secret'")
        assert findings
        assert any("possible secret exposure" in f for f in findings)

    def test_verify_secrets_detects_api_key(self):
        findings = verify_secrets("api_key=ABCDEFGHIJKLMNOPQRST1234567890")
        assert findings

    def test_verify_secrets_detects_secret(self):
        findings = verify_secrets("secret: 0123456789abcdef0123456789abcdef")
        assert findings

    def test_verify_secrets_clean_content(self):
        findings = verify_secrets("export PORT=8000")
        assert findings == []

    def test_verify_areas_all_pass_defaults(self):
        checks = verify_areas()
        assert len(checks) == 9
        assert all(c.passed for c in checks)

    def test_verify_areas_detects_failure(self):
        checks = verify_areas(tls_enabled=False)
        tls = next(c for c in checks if c.area == "tls")
        assert tls.passed is False

    def test_deployment_blocked_on_any_failure(self):
        checks = verify_areas(secrets_clean=False)
        assert deployment_blocked(checks) is True

    def test_deployment_not_blocked_clean(self):
        checks = verify_areas()
        assert deployment_blocked(checks) is False

    def test_security_summary_counts(self):
        checks = verify_areas()
        summary = security_summary(checks)
        assert "9" in summary or "areas" in summary

    def test_security_check_defaults(self):
        check = SecurityCheck(area="tls", finding="none")
        assert check.passed is False
        assert check.severity == "low"
