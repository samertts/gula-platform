"""Unit tests for GULA-LEARNER-001 — Phase 0 audit, Phase 8 quality, Phase 9 search."""

from __future__ import annotations

import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3]))

from scripts.learner import quality
from scripts.learner import search as search_module
from scripts.learner.audit import AUDIT_PATTERNS, audit_system, render_markdown
from scripts.learner.quality import (
    QUALITY_CHECKS,
    _check_broken_references,
    _check_confidence,
    _check_duplicate_ids,
    _check_graph,
    _check_registry,
    _check_versions,
    run_quality,
)
from scripts.learner.search import (
    _rank,
    _tokens,
    build_index,
    count_documents,
    recommendations,
    search,
)


class TestAudit:
    def test_audit_patterns_cover_all_components(self):
        for component in ("registry", "graph", "memory", "skills", "playbooks",
                          "runbooks", "adr", "constitution", "bridge-files",
                          "templates", "reports", "search-indexes"):
            assert component in AUDIT_PATTERNS

    def test_audit_system_covers_twelve_components(self):
        items = audit_system()
        assert len(items) == 12

    def test_audit_deterministic(self):
        first = [item.item_id for item in audit_system()]
        second = [item.item_id for item in audit_system()]
        assert first == second

    def test_render_markdown_includes_verdict(self):
        items = audit_system()
        markdown = render_markdown(items)
        assert "LEARNER_AUDIT_REPORT.md" in markdown
        assert "AUDIT COMPLETE" in markdown
        assert "12/12" in markdown


class TestQuality:
    def test_quality_checks_seven(self):
        assert len(QUALITY_CHECKS) == 7

    def test_run_quality_health_bounded(self):
        report = run_quality()
        assert 0 <= report.health_score <= 100
        assert len(report.checks) == 7

    def test_duplicate_ids_detected(self, tmp_path, monkeypatch):
        for directory_name in ("SKILL_DIR", "PLAYBOOK_DIR", "RUNBOOK_DIR", "MEMORY_DIR"):
            monkeypatch.setattr(quality, directory_name, tmp_path / directory_name)
        (tmp_path / "SKILL_DIR").mkdir()
        duplicate = (
            '---\nid: SKILL-000001\ntype: skill\ntitle: X\nversion: "1.0"\n'
            "status: verified\nconfidence: verified\n---\n"
        )
        (tmp_path / "SKILL_DIR" / "SKILL-000001_a.md").write_text(duplicate, encoding="utf-8")
        (tmp_path / "SKILL_DIR" / "SKILL-000001_b.md").write_text(duplicate, encoding="utf-8")
        from scripts.learner.core import QualityReport

        report = QualityReport()
        assert _check_duplicate_ids(report) is False
        assert report.duplicate_ids == ["SKILL-000001"]

    def test_broken_references_detected(self, tmp_path, monkeypatch):
        for directory_name in ("SKILL_DIR", "PLAYBOOK_DIR", "RUNBOOK_DIR", "MEMORY_DIR"):
            monkeypatch.setattr(quality, directory_name, tmp_path / directory_name)
        skill_dir = tmp_path / "SKILL_DIR"
        playbook_dir = tmp_path / "PLAYBOOK_DIR"
        skill_dir.mkdir()
        playbook_dir.mkdir()
        (tmp_path / "PLAYBOOK_DIR" / "PLAYBOOK-000001_x.md").write_text(
            "PLAYBOOK-000001\n", encoding="utf-8"
        )
        (tmp_path / "SKILL_DIR" / "SKILL-000001_x.md").write_text(
            "references PLAYBOOK-000099\n", encoding="utf-8"
        )
        from scripts.learner.core import QualityReport

        report = QualityReport()
        assert _check_broken_references(report) is False
        assert any("PLAYBOOK-000099" in ref for ref in report.broken_references)

    def test_no_broken_references_when_linked(self, tmp_path, monkeypatch):
        for directory_name in ("SKILL_DIR", "PLAYBOOK_DIR", "RUNBOOK_DIR", "MEMORY_DIR"):
            monkeypatch.setattr(quality, directory_name, tmp_path / directory_name)
        (tmp_path / "SKILL_DIR").mkdir()
        (tmp_path / "PLAYBOOK_DIR").mkdir()
        (tmp_path / "SKILL_DIR" / "SKILL-000001_x.md").write_text(
            "related: PLAYBOOK-000001\n", encoding="utf-8"
        )
        (tmp_path / "PLAYBOOK_DIR" / "PLAYBOOK-000001_x.md").write_text(
            "PLAYBOOK-000001\n", encoding="utf-8"
        )
        from scripts.learner.core import QualityReport

        report = QualityReport()
        assert _check_broken_references(report) is True

    def test_confidence_accepts_vocabulary_and_numeric(self, tmp_path, monkeypatch):
        monkeypatch.setattr(quality, "SKILL_DIR", tmp_path / "SKILL_DIR")
        (tmp_path / "SKILL_DIR").mkdir()
        from scripts.learner.core import QualityReport

        report = QualityReport()
        (tmp_path / "SKILL_DIR" / "SKILL-000001_x.md").write_text(
            "confidence: verified\n", encoding="utf-8"
        )
        assert _check_confidence(report) is True

        (tmp_path / "SKILL_DIR" / "SKILL-000002_x.md").write_text(
            "confidence: 90%\n", encoding="utf-8"
        )
        assert _check_confidence(report) is True

        (tmp_path / "SKILL_DIR" / "SKILL-000003_x.md").write_text(
            "confidence: bogus\n", encoding="utf-8"
        )
        assert _check_confidence(report) is False

    def test_versions_consistent(self, tmp_path, monkeypatch):
        monkeypatch.setattr(quality, "SKILL_DIR", tmp_path / "SKILL_DIR")
        (tmp_path / "SKILL_DIR").mkdir()
        from scripts.learner.core import QualityReport

        report = QualityReport()
        (tmp_path / "SKILL_DIR" / "SKILL-000001_x.md").write_text(
            'version: "1.0"\n', encoding="utf-8"
        )
        assert _check_versions(report) is True

    def test_registry_consistent(self, tmp_path, monkeypatch):
        from scripts.learner.core import QualityReport

        for directory_name in ("SKILL_DIR", "PLAYBOOK_DIR", "RUNBOOK_DIR", "MEMORY_DIR"):
            monkeypatch.setattr(quality, directory_name, tmp_path / directory_name)
        monkeypatch.setattr(quality, "REGISTRY", tmp_path / "REGISTRY.md")
        for directory_name in ("SKILL_DIR", "PLAYBOOK_DIR", "RUNBOOK_DIR", "MEMORY_DIR"):
            (tmp_path / directory_name).mkdir()
        (tmp_path / "REGISTRY.md").write_text(
            "SKILL-000001 SKILL-000002\n", encoding="utf-8"
        )
        (tmp_path / "SKILL_DIR" / "SKILL-000001_x.md").write_text("x", encoding="utf-8")
        (tmp_path / "SKILL_DIR" / "SKILL-000002_x.md").write_text("x", encoding="utf-8")
        report = QualityReport()
        assert _check_registry(report) is True

        (tmp_path / "SKILL_DIR" / "SKILL-000003_x.md").write_text("x", encoding="utf-8")
        report = QualityReport()
        assert _check_registry(report) is False

    def test_graph_consistent(self, tmp_path, monkeypatch):
        from scripts.learner.core import QualityReport

        monkeypatch.setattr(quality, "GRAPH_INDEX", tmp_path / "graph.json")
        (tmp_path / "graph.json").write_text(json.dumps({
            "nodes": [
                {"id": "A", "related": ["B"]},
                {"id": "B", "related": []},
            ]
        }), encoding="utf-8")
        report = QualityReport()
        assert _check_graph(report) is True

        (tmp_path / "graph.json").write_text(json.dumps({
            "nodes": [
                {"id": "A", "related": ["MISSING"]},
            ]
        }), encoding="utf-8")
        report = QualityReport()
        assert _check_graph(report) is False


class TestSearch:
    def test_tokens_lowercase_and_filter(self):
        tokens = _tokens("Deploy Rollback plan, version 1")
        assert "deploy" in tokens
        assert "rollback" in tokens
        assert all(len(token) >= 3 for token in tokens)

    def test_rank_prefers_matching(self):
        high = _rank({"deploy"}, ["deploy", "deploy", "other"])
        low = _rank({"deploy"}, ["other", "other"])
        assert high > 0
        assert low == 0

    def test_build_index_isolated(self, tmp_path, monkeypatch):
        for directory_name in ("SKILL_DIR", "PLAYBOOK_DIR", "RUNBOOK_DIR", "MEMORY_DIR"):
            monkeypatch.setattr(search_module, directory_name, tmp_path / directory_name)
        for directory_name in ("SKILL_DIR", "PLAYBOOK_DIR", "RUNBOOK_DIR", "MEMORY_DIR"):
            (tmp_path / directory_name).mkdir()
        (tmp_path / "SKILL_DIR" / "SKILL-000001_x.md").write_text(
            "deployment rollback snapshot\n", encoding="utf-8"
        )
        (tmp_path / "RUNBOOK_DIR" / "RUNBOOK-000001_x.md").write_text(
            "database down recovery\n", encoding="utf-8"
        )
        monkeypatch.setattr(search_module, "INDEX_PATH", tmp_path / "index.json")
        path = build_index()
        assert path.exists()
        payload = json.loads(path.read_text(encoding="utf-8"))
        assert len(payload["documents"]) == 2
        assert count_documents() == 2

    def test_search_isolated(self, tmp_path, monkeypatch):
        monkeypatch.setattr(search_module, "SKILL_DIR", tmp_path / "SKILL_DIR")
        monkeypatch.setattr(search_module, "PLAYBOOK_DIR", tmp_path / "PLAYBOOK_DIR")
        monkeypatch.setattr(search_module, "RUNBOOK_DIR", tmp_path / "RUNBOOK_DIR")
        monkeypatch.setattr(search_module, "MEMORY_DIR", tmp_path / "MEMORY_DIR")
        for directory_name in ("SKILL_DIR", "PLAYBOOK_DIR", "RUNBOOK_DIR", "MEMORY_DIR"):
            (tmp_path / directory_name).mkdir()
        (tmp_path / "SKILL_DIR" / "SKILL-000001_x.md").write_text(
            "deployment rollback snapshot recovery\n", encoding="utf-8"
        )
        (tmp_path / "RUNBOOK_DIR" / "RUNBOOK-000001_x.md").write_text(
            "database down recovery\n", encoding="utf-8"
        )
        monkeypatch.setattr(search_module, "INDEX_PATH", tmp_path / "index.json")
        build_index()
        results = search("deployment rollback")
        assert results
        assert results[0]["kind"] == "skill"

    def test_recommendations_prefer_skills(self, tmp_path, monkeypatch):
        monkeypatch.setattr(search_module, "SKILL_DIR", tmp_path / "SKILL_DIR")
        monkeypatch.setattr(search_module, "PLAYBOOK_DIR", tmp_path / "PLAYBOOK_DIR")
        monkeypatch.setattr(search_module, "RUNBOOK_DIR", tmp_path / "RUNBOOK_DIR")
        monkeypatch.setattr(search_module, "MEMORY_DIR", tmp_path / "MEMORY_DIR")
        for directory_name in ("SKILL_DIR", "PLAYBOOK_DIR", "RUNBOOK_DIR", "MEMORY_DIR"):
            (tmp_path / directory_name).mkdir()
        (tmp_path / "SKILL_DIR" / "SKILL-000001_x.md").write_text(
            "deployment rollback snapshot\n", encoding="utf-8"
        )
        (tmp_path / "RUNBOOK_DIR" / "RUNBOOK-000001_x.md").write_text(
            "deployment rollback snapshot\n", encoding="utf-8"
        )
        monkeypatch.setattr(search_module, "INDEX_PATH", tmp_path / "index.json")
        build_index()
        results = recommendations("deployment rollback", top_n=2)
        assert results
        assert results[0]["kind"] == "skill"

    def test_search_empty_query(self, tmp_path, monkeypatch):
        monkeypatch.setattr(search_module, "INDEX_PATH", tmp_path / "index.json")
        assert search("") == []
