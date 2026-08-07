"""PROGRAM-ALPHA — Architecture Constitution gate tests (Phase 7)."""

from __future__ import annotations

from pathlib import Path

import pytest

from scripts.architecture.core import (
    CANONICAL_PROVIDERS,
    REPO_ROOT,
    RULES,
    ConstitutionFinding,
    _is_canonical,
    scan,
)
from scripts.architecture.gate import (
    BASELINE_PATH,
    new_country_findings,
    new_findings,
    run_all_gates,
    run_constitution_gate,
    run_country_agnostic_scan,
    run_domain_gate,
)


class TestConstitutionRules:
    def test_every_rule_has_description_and_signals(self):
        for rule_id, rule in RULES.items():
            assert rule["description"], rule_id
            assert isinstance(rule["signals"], tuple) and rule["signals"], rule_id

    def test_every_rule_has_canonical_provider(self):
        for rule_id in RULES:
            assert rule_id in CANONICAL_PROVIDERS, f"{rule_id} lacks providers"

    def test_canonical_providers_are_repo_paths(self):
        for rule_id, providers in CANONICAL_PROVIDERS.items():
            for provider in providers:
                assert not provider.startswith("/"), (rule_id, provider)


class TestIsCanonical:
    def test_canonical_path_exempt(self):
        assert _is_canonical("notifications", "backend/app/notifications/service.py")

    def test_non_canonical_path_not_exempt(self):
        assert not _is_canonical("notifications", "backend/app/lims/services/notify.py")

    def test_exact_file_provider(self):
        assert _is_canonical("qr_engine", "shared/qr")
        assert _is_canonical("audit", "backend/app/identity/models/audit.py")


class TestScan:
    def test_scan_detects_new_notification_reimplementation(self, tmp_path: Path):
        (tmp_path / "mysvc").mkdir(parents=True)
        bad = tmp_path / "mysvc" / "notifier.py"
        bad.write_text("class NotificationService:\n    pass\n", encoding="utf-8")
        findings = scan([tmp_path])
        assert any(
            f.rule_id == "notifications" and str(bad) in f.path for f in findings
        )

    def test_scan_ignores_shared_core(self, tmp_path: Path):
        (tmp_path / "shared" / "notifications").mkdir(parents=True)
        ok = tmp_path / "shared" / "notifications" / "sender.py"
        ok.write_text("class NotificationService:\n    pass\n", encoding="utf-8")
        findings = scan([tmp_path])
        assert not findings

    def test_scan_skips_tests_and_cache_dirs(self, tmp_path: Path):
        (tmp_path / "tests").mkdir(parents=True)
        (tmp_path / "__pycache__").mkdir(parents=True)
        t = tmp_path / "tests" / "x.py"
        c = tmp_path / "__pycache__" / "y.py"
        t.write_text("class NotificationService:\n    pass\n", encoding="utf-8")
        c.write_text("class NotificationService:\n    pass\n", encoding="utf-8")
        assert scan([tmp_path]) == []

    def test_search_engine_signal_is_case_sensitive(self, tmp_path: Path):
        """ResearchService is a research-registry CRUD class, not a search
        engine: the class-name signal must require the literal capital-S
        Search token so embedded lowercase 'search' never false-positives."""
        (tmp_path / "svc").mkdir(parents=True)
        ok = tmp_path / "svc" / "research.py"
        ok.write_text("class ResearchService:\n    pass\n", encoding="utf-8")
        assert scan([tmp_path]) == []

    def test_search_engine_signal_still_flags_real_search_classes(self, tmp_path: Path):
        (tmp_path / "svc").mkdir(parents=True)
        for name in ("SearchService", "DefaultSearchService", "FHIRSearchEngine"):
            f = tmp_path / "svc" / f"{name.lower()}.py"
            f.write_text(f"class {name}:\n    pass\n", encoding="utf-8")
        findings = scan([tmp_path])
        assert len(findings) == 3
        assert all(f.rule_id == "search_engine" for f in findings)

    def test_non_case_sensitive_rules_keep_ignoring_case(self, tmp_path: Path):
        (tmp_path / "svc").mkdir(parents=True)
        f = tmp_path / "svc" / "notifier.py"
        f.write_text("class notificationService:\n    pass\n", encoding="utf-8")
        findings = scan([tmp_path])
        assert any(f2.rule_id == "notifications" for f2 in findings)


class TestBaseline:
    def test_new_findings_excludes_acknowledged(self, tmp_path: Path):
        baseline = [{"rule_id": "events", "path": "backend/app/x/bus.py"}]
        findings = [
            ConstitutionFinding("events", "backend/app/x/bus.py", "class EventBus"),
            ConstitutionFinding("events", "backend/app/y/bus.py", "class EventBus"),
        ]
        new = new_findings.__wrapped__ if hasattr(new_findings, "__wrapped__") else new_findings
        from unittest.mock import patch

        from scripts.architecture.gate import baseline_fingerprint

        with patch("scripts.architecture.gate.load_baseline", return_value=baseline):
            result = new_findings(findings)
        assert len(result) == 1
        assert result[0].path == "backend/app/y/bus.py"

    def test_new_country_findings(self):
        baseline = [{"path": "backend/app/x.py", "marker": r"\bdinar\b"}]
        from unittest.mock import patch

        with patch("scripts.architecture.gate.load_country_baseline", return_value=baseline):
            new = new_country_findings(
                [
                    {"path": "backend/app/x.py", "marker": r"\bdinar\b"},
                    {"path": "backend/app/y.py", "marker": r"\bdinar\b"},
                ]
            )
        assert len(new) == 1
        assert new[0]["path"] == "backend/app/y.py"


class TestRepoGates:
    def test_domain_gate_certifies_all_domains(self):
        result = run_domain_gate()
        assert result["domains_total"] == 11
        assert result["domains_passed"] == 11
        assert result["isolation_passes"] is True
        assert result["certified"] is True

    def test_constitution_gate_passes_repo(self):
        result = run_constitution_gate()
        assert result["passes"] is True
        assert result["new_findings"] == []
        assert result["total_findings"] >= 1

    def test_country_scan_is_baselined(self):
        findings = run_country_agnostic_scan()
        assert len(new_country_findings(findings)) == 0

    def test_full_gate_passes_repo(self):
        result = run_all_gates()
        assert result["verdict"] == "PASS"
        assert result["passed"] is True

    def test_baseline_file_is_committed_and_fresh(self):
        assert BASELINE_PATH.exists()
        from scripts.architecture.gate import load_baseline, load_country_baseline

        assert len(load_baseline()) >= 1
        assert len(load_country_baseline()) >= 1

    def test_repo_scan_has_no_new_findings(self):
        findings = scan([REPO_ROOT / "backend" / "app", REPO_ROOT / "shared"])
        assert len(new_findings(findings)) == 0
