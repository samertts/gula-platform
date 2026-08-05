"""Unit tests for GULA-REVIEWER-001 — decision engine, report, and gate."""

from __future__ import annotations

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3]))

from scripts.kernel.core import Severity
from scripts.reviewer.core import Decision, ReviewFinding, decide_overall
from scripts.reviewer.decision import decide, summary_lines
from scripts.reviewer.report import gate, run


def make_area_report(*decisions: str):
    """Build a ReviewReport-shaped object from area decisions (strings)."""
    from scripts.reviewer.core import AreaReview, ReviewReport

    return ReviewReport(
        target="t",
        area_reviews=[
            AreaReview(area=f"a{i}", decision=d, score=100.0, findings=[])
            for i, d in enumerate(decisions)
        ],
        decision=decide_overall([AreaReview(area=f"a{i}", decision=d) for i, d in enumerate(decisions)]),
        overall_score=100.0,
    )


class TestGate:
    def test_pass_gates_zero(self):
        report = make_area_report(Decision.PASS.value)
        assert gate(report) == 0

    def test_warnings_gate_zero(self):
        report = make_area_report(Decision.PASS.value, Decision.PASS_WITH_WARNINGS.value)
        assert gate(report) == 0

    def test_reject_gates_one(self):
        report = make_area_report(Decision.PASS.value, Decision.REJECT.value)
        assert gate(report) == 1


class TestSummaryLines:
    def test_summary_contains_verdict_and_areas(self):
        report = make_area_report(Decision.PASS.value, Decision.PASS_WITH_WARNINGS.value)
        lines = summary_lines(report)
        assert any("Reviewer verdict:" in line for line in lines)
        assert any("a0" in line for line in lines)

    def test_summary_lists_high_findings(self):
        from scripts.reviewer.core import AreaReview, ReviewReport

        finding = ReviewFinding("security", Severity.CRITICAL, "critical", detail="boom")
        report = ReviewReport(
            target="t",
            area_reviews=[AreaReview(area="security", findings=[finding],
                                     score=0.0, decision=Decision.REJECT.value)],
            decision=Decision.REJECT.value,
            overall_score=0.0,
        )
        lines = summary_lines(report)
        assert any("High/critical findings: 1" in line for line in lines)
        assert any("critical" in line for line in lines)


class TestReportRender:
    def test_report_writes_markdown_and_json(self, tmp_path, monkeypatch):
        from scripts.reviewer import report as report_mod

        state_dir = tmp_path / "state"
        state_dir.mkdir(parents=True, exist_ok=True)
        monkeypatch.setattr(report_mod, "REVIEWER_REPORT_PATH", tmp_path / "REVIEWER.md")
        monkeypatch.setattr(report_mod, "STATE_DIR", state_dir)
        report = make_area_report(Decision.PASS.value, Decision.PASS_WITH_WARNINGS.value)
        out = run(report)
        assert out.exists()
        text = out.read_text(encoding="utf-8")
        assert "REVIEWER_IMPLEMENTATION_REPORT.md" in text
        assert report.decision in text
        state_file = state_dir / "latest_review.json"
        assert state_file.exists()
