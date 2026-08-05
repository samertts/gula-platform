"""Unit tests for GULA-BUILDER-001 Phase 8 — Output/report + Phase 0 audit."""

from __future__ import annotations

import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3]))

from scripts.builder.report import (
    ImplementationRecord,
    readiness,
    render_markdown,
    write_report,
)


def _record(**overrides):
    values = {
        "mission_id": "MSN-REPORT",
        "objective": "Build Patient Management",
        "mission_type": "feature",
        "complexity": "moderate",
        "risk": "low",
        "completed_work": ["analyzed", "implemented", "tested"],
        "created_files": ["app/patients.py"],
        "updated_files": ["docs/api.md"],
        "architecture": ["builder -> kernel"],
        "future_improvements": ["telemetry"],
        "remaining_risks": [],
    }
    values.update(overrides)
    return ImplementationRecord(**values)


class TestReadiness:
    def test_max_with_work_and_no_risks(self):
        record = _record(completed_work=[f"w{i}" for i in range(10)])
        assert readiness(record) == 100.0

    def test_penalized_by_risks(self):
        record = _record(remaining_risks=["risk1", "risk2", "risk3"])
        assert readiness(record) < 100.0

    def test_bounded_zero(self):
        record = _record(completed_work=[], remaining_risks=["a", "b", "c", "d", "e", "f"])
        assert readiness(record) >= 0.0

    def test_bounded_max(self):
        record = _record(completed_work=["a"] * 20, remaining_risks=[])
        assert readiness(record) <= 100.0


class TestRender:
    def test_render_includes_sections(self):
        text = render_markdown(_record())
        for section in (
            "## Completed Work",
            "## Created Files",
            "## Updated Files",
            "## Architecture",
            "## Future Improvements",
            "## Remaining Risks",
        ):
            assert section in text

    def test_render_includes_mission(self):
        text = render_markdown(_record())
        assert "MSN-REPORT" in text
        assert "Build Patient Management" in text

    def test_render_empty_lists(self):
        text = render_markdown(_record(completed_work=[], created_files=[], updated_files=[]))
        assert "_none_" in text


class TestWrite:
    def test_write_report(self, tmp_path):
        path = write_report(_record(), tmp_path / "REPORT.md")
        assert path.exists()
        text = path.read_text(encoding="utf-8")
        assert text.startswith("# BUILDER_IMPLEMENTATION_REPORT.md")

    def test_to_dict(self):
        data = _record().to_dict()
        assert data["mission_id"] == "MSN-REPORT"
        assert isinstance(data["completed_work"], list)


class TestAudit:
    def test_audit_discovers_categories(self):
        from scripts.builder.audit import audit_repository

        discoveries = audit_repository()
        assert len(discoveries) >= 8

    def test_audit_render(self):
        from scripts.builder.audit import audit_findings, audit_repository, render_audit_markdown

        discoveries = audit_repository()
        findings = audit_findings(discoveries)
        text = render_audit_markdown(discoveries, findings)
        assert "# BUILDER_AUDIT_REPORT.md" in text
        assert "## Findings" in text
