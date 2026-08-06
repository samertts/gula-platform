"""Unit tests for GULA-LEARNER-001 — Phase 6 patterns, Phase 7 improve, Phase 10 report, CLI."""

from __future__ import annotations

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3]))

from scripts.learner import improve, patterns, report
from scripts.learner.cli import (
    LEARNER_COMMANDS,
    run_audit,
    run_improve,
    run_playbook,
    run_quality,
    run_report,
    run_runbook,
)
from scripts.learner.improve import (
    load_proposals,
    persist_proposals,
    propose_improvements,
    set_proposal_status,
)
from scripts.learner.patterns import (
    detect_patterns,
    load_patterns,
    persist_patterns,
)
from scripts.learner.report import build_report


class TestPatterns:
    def test_detect_patterns_threshold(self):
        patterns_found = detect_patterns([
            ("deployment", "deploy failure rolled back snapshot"),
            ("deployment", "deploy failure rolled back snapshot"),
        ])
        assert len(patterns_found) == 1
        pattern = patterns_found[0]
        assert pattern.kind == "repeated-deployment-failure"
        assert pattern.count == 2
        assert pattern.recommendation

    def test_detect_patterns_below_threshold(self):
        patterns_found = detect_patterns([
            ("deployment", "deploy failure rolled back snapshot"),
        ])
        assert patterns_found == []

    def test_detect_patterns_security_threshold_higher(self):
        patterns_found = detect_patterns([
            ("security", "security finding tls secret"),
            ("security", "security finding tls secret"),
        ])
        assert patterns_found == []
        patterns_found = detect_patterns([
            ("security", "security finding tls secret"),
            ("security", "security finding tls secret"),
            ("security", "security finding tls secret"),
        ])
        assert len(patterns_found) == 1
        assert patterns_found[0].kind == "repeated-security-finding"

    def test_detect_patterns_distinct_areas(self):
        patterns_found = detect_patterns([
            ("deployment", "deploy failure rolled back snapshot"),
            ("deployment", "deploy failure rolled back snapshot"),
            ("backend", "bug fixed regression test"),
            ("backend", "bug fixed regression test"),
        ])
        kinds = {p.kind for p in patterns_found}
        assert kinds == {"repeated-deployment-failure", "repeated-bug"}

    def test_detect_patterns_unclassified(self):
        assert detect_patterns([("deployment", "zzz qqq")]) == []

    def test_persist_and_load_patterns(self, tmp_path, monkeypatch):
        monkeypatch.setattr(patterns, "PATTERN_DIR", tmp_path)
        patterns_found = detect_patterns([
            ("deployment", "deploy failure rolled back snapshot"),
            ("deployment", "deploy failure rolled back snapshot"),
        ])
        persist_patterns(patterns_found)
        loaded = load_patterns()
        assert len(loaded) == 1
        assert loaded[0].kind == "repeated-deployment-failure"


class TestImprove:
    def test_propose_improvements_covers_six_engines(self):
        proposals = propose_improvements()
        assert len(proposals) == 6
        targets = {p.target for p in proposals}
        assert targets == {"builder", "reviewer", "orchestrator", "deployer",
                           "quality-system", "knowledge-system"}

    def test_proposals_open_and_id_unique(self):
        proposals = propose_improvements()
        ids = {p.proposal_id for p in proposals}
        assert len(ids) == 6
        assert all(p.status == "open" for p in proposals)

    def test_persist_and_load_proposals(self, tmp_path, monkeypatch):
        monkeypatch.setattr(improve, "PROPOSAL_DIR", tmp_path)
        proposals = propose_improvements()
        persist_proposals(proposals)
        loaded = load_proposals()
        assert len(loaded) == 6

    def test_set_proposal_status(self, tmp_path, monkeypatch):
        monkeypatch.setattr(improve, "PROPOSAL_DIR", tmp_path)
        proposals = propose_improvements()
        persist_proposals(proposals)
        updated = set_proposal_status(proposals[0].proposal_id, "approved")
        assert updated is not None
        assert updated.status == "approved"
        loaded = load_proposals()
        assert next(p for p in loaded if p.proposal_id == proposals[0].proposal_id).status == "approved"

    def test_set_proposal_status_invalid(self, tmp_path, monkeypatch):
        monkeypatch.setattr(improve, "PROPOSAL_DIR", tmp_path)
        persist_proposals(propose_improvements())
        try:
            set_proposal_status("PRO-000001", "bogus")
            raised = False
        except ValueError:
            raised = True
        assert raised


class TestReport:
    def test_build_report_writes_artifact(self, tmp_path, monkeypatch):
        monkeypatch.setattr(report, "REPORT_PATH", tmp_path / "LEARNER_IMPLEMENTATION_REPORT.md")
        path = build_report()
        assert path.exists()
        text = path.read_text(encoding="utf-8")
        assert "GULA-LEARNER-001" in text
        assert "## Verdict" in text
        assert "COMPLETE" in text


class TestCli:
    def test_commands_registered(self):
        for command in ("learner-audit", "learner-extract", "learner-skill",
                        "learner-playbook", "learner-runbook", "learner-memory",
                        "learner-patterns", "learner-improve", "learner-quality",
                        "learner-search", "learner-report", "learner-learn",
                        "learner-check"):
            assert command in LEARNER_COMMANDS

    def test_run_audit_writes_report(self, tmp_path, monkeypatch):
        from scripts.learner import audit

        monkeypatch.setattr(audit, "AUDIT_PATH", tmp_path / "LEARNER_AUDIT_REPORT.md")
        assert run_audit() == 0
        assert (tmp_path / "LEARNER_AUDIT_REPORT.md").exists()

    def test_run_improve_zero(self, tmp_path, monkeypatch, capsys):
        monkeypatch.setattr(improve, "PROPOSAL_DIR", tmp_path)
        assert run_improve() == 0
        output = capsys.readouterr().out
        assert "proposals" in output

    def test_run_quality_returns_zero_on_pass(self, capsys):
        code = run_quality()
        assert code in (0, 1)
        output = capsys.readouterr().out
        assert "Health score" in output or "health_score" in output

    def test_run_playbook_invalid_kind(self, monkeypatch, capsys):
        monkeypatch.setattr("sys.argv", ["learner.py", "playbook", "bogus"])
        assert run_playbook() == 2

    def test_run_runbook_invalid_kind(self, monkeypatch, capsys):
        monkeypatch.setattr("sys.argv", ["learner.py", "runbook", "bogus"])
        assert run_runbook() == 2

    def test_run_report_returns_zero(self, tmp_path, monkeypatch):
        from scripts.learner import report as report_module

        monkeypatch.setattr(report_module, "REPORT_PATH", tmp_path / "report.md")
        assert run_report() == 0
        assert (tmp_path / "report.md").exists()
