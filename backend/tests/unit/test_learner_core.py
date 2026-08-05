"""Unit tests for GULA-LEARNER-001 — core constants, enums, dataclasses."""

from __future__ import annotations

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3]))

from scripts.learner.core import (
    AUDIT_COMPONENTS,
    CONFIDENCE_LEVELS,
    DIFFICULTY_LEVELS,
    ENGINES_EVALUATED,
    EXTRACTION_FIELDS,
    MEMORY_KINDS,
    PATTERN_KINDS,
    PLAYBOOK_KINDS,
    QUALITY_CHECKS,
    RUNBOOK_KINDS,
    SKILL_CATEGORIES,
    Extraction,
    KnowledgeItem,
    KnowledgeStatus,
    Pattern,
    Proposal,
    ProposalStatus,
    QualityReport,
    Skill,
    ensure_dirs,
    make_id,
    read_json,
    write_json,
)


class TestEngineConstants:
    def test_audit_components_cover_twelve(self):
        assert len(AUDIT_COMPONENTS) == 12
        for component in ("registry", "graph", "memory", "skills", "playbooks",
                          "runbooks", "adr", "constitution", "bridge-files",
                          "templates", "reports", "search-indexes"):
            assert component in AUDIT_COMPONENTS

    def test_extraction_fields_cover_full_record(self):
        for field in ("problem", "cause", "solution", "alternative_solutions",
                      "rejected_solutions", "tradeoffs", "risks", "lessons",
                      "performance_impact", "security_impact", "recommendations"):
            assert field in EXTRACTION_FIELDS

    def test_skill_categories_include_relevant(self):
        for category in ("infrastructure", "backend", "frontend", "database",
                         "security", "testing", "deployment", "tooling",
                         "architecture", "performance"):
            assert category in SKILL_CATEGORIES

    def test_confidence_and_difficulty_vocabulary(self):
        assert CONFIDENCE_LEVELS == ("low", "medium", "high", "verified")
        assert DIFFICULTY_LEVELS == ("easy", "medium", "hard")

    def test_playbook_kinds_cover_seven(self):
        assert len(PLAYBOOK_KINDS) == 7
        for kind in ("deployment", "recovery", "debugging", "performance",
                     "security", "testing", "infrastructure"):
            assert kind in PLAYBOOK_KINDS

    def test_runbook_kinds_cover_eight(self):
        assert len(RUNBOOK_KINDS) == 8
        for kind in ("incidents", "recovery", "monitoring", "production",
                     "maintenance", "scaling", "backup", "rollback"):
            assert kind in RUNBOOK_KINDS

    def test_memory_kinds_cover_five(self):
        assert len(MEMORY_KINDS) == 5
        for kind in ("project", "engineering", "decision", "architecture", "deployment"):
            assert kind in MEMORY_KINDS

    def test_pattern_kinds_cover_six(self):
        assert len(PATTERN_KINDS) == 6
        for kind in ("repeated-bug", "repeated-refactoring", "repeated-design",
                     "repeated-deployment-failure", "repeated-performance-issue",
                     "repeated-security-finding"):
            assert kind in PATTERN_KINDS

    def test_engines_evaluated_cover_six(self):
        assert len(ENGINES_EVALUATED) == 6
        for engine in ("builder", "reviewer", "orchestrator", "deployer",
                       "quality-system", "knowledge-system"):
            assert engine in ENGINES_EVALUATED

    def test_quality_checks_cover_seven(self):
        assert len(QUALITY_CHECKS) == 7
        for check in ("duplicate-ids", "broken-references", "registry-consistency",
                      "graph-consistency", "version-consistency", "confidence-levels",
                      "knowledge-coverage"):
            assert check in QUALITY_CHECKS


class TestEnums:
    def test_knowledge_status_values(self):
        assert KnowledgeStatus.PLANNED.value == "planned"
        assert KnowledgeStatus.EXTRACTED.value == "extracted"
        assert KnowledgeStatus.VERIFIED.value == "verified"
        assert KnowledgeStatus.OBSOLETE.value == "obsolete"
        assert KnowledgeStatus.DEPRECATED.value == "deprecated"

    def test_proposal_status_values(self):
        assert ProposalStatus.OPEN.value == "open"
        assert ProposalStatus.APPROVED.value == "approved"
        assert ProposalStatus.REJECTED.value == "rejected"
        assert ProposalStatus.IMPLEMENTED.value == "implemented"


class TestDataclasses:
    def test_knowledge_item_defaults(self):
        item = KnowledgeItem(item_id="SKILL-000001", kind="skill", title="X")
        assert item.version == "1.0"
        assert item.status == KnowledgeStatus.EXTRACTED.value
        assert item.confidence == "medium"
        assert item.tags == []

    def test_knowledge_item_round_trip(self):
        item = KnowledgeItem(item_id="SKILL-000001", kind="skill", title="X",
                             tags=["skill"], body="body")
        data = item.to_dict()
        assert data["item_id"] == "SKILL-000001"
        assert data["tags"] == ["skill"]

    def test_extraction_defaults_and_round_trip(self):
        extraction = Extraction(source="mission:ORN-1")
        assert extraction.alternative_solutions == []
        assert extraction.reusable is False
        data = extraction.to_dict()
        restored = Extraction.from_dict(data)
        assert restored.source == extraction.source
        assert restored.reusable is False
        assert restored.lessons == []

    def test_extraction_from_dict_populates_fields(self):
        extraction = Extraction.from_dict({
            "source": "deployment:DEP-1",
            "solution": "deployed",
            "lessons": ["a", "b"],
            "reusable": True,
        })
        assert extraction.solution == "deployed"
        assert extraction.lessons == ["a", "b"]
        assert extraction.reusable is True

    def test_skill_to_dict(self):
        skill = Skill(skill_id="SKILL-000001", title="T", category="tooling")
        data = skill.to_dict()
        assert data["skill_id"] == "SKILL-000001"
        assert data["category"] == "tooling"

    def test_pattern_to_dict(self):
        pattern = Pattern(pattern_id="PAT-000001", kind="repeated-bug",
                          area="backend", count=2, threshold=2)
        data = pattern.to_dict()
        assert data["count"] == 2
        assert data["evidence"] == []

    def test_proposal_to_dict(self):
        proposal = Proposal(proposal_id="PRO-000001", target="builder",
                            title="Improve", rationale="why")
        data = proposal.to_dict()
        assert data["status"] == "open"
        assert data["target"] == "builder"

    def test_quality_report_defaults(self):
        report = QualityReport()
        assert report.health_score == 100
        assert report.registry_consistent is True
        assert report.checks == {}


class TestHelpers:
    def test_make_id_prefix(self):
        identifier = make_id("LEARN")
        assert identifier.startswith("LEARN-")
        assert len(identifier) == len("LEARN-") + 8

    def test_make_id_unique(self):
        assert make_id("LEARN") != make_id("LEARN")

    def test_ensure_dirs_creates_state(self, tmp_path, monkeypatch):
        from scripts.learner import core as core_module

        monkeypatch.setattr(core_module, "STATE_DIR", tmp_path / "state")
        monkeypatch.setattr(core_module, "EXTRACTION_DIR", tmp_path / "extract")
        monkeypatch.setattr(core_module, "PATTERN_DIR", tmp_path / "patterns")
        monkeypatch.setattr(core_module, "PROPOSAL_DIR", tmp_path / "proposals")
        monkeypatch.setattr(core_module, "HISTORY_DIR", tmp_path / "history")
        ensure_dirs()
        for directory in (tmp_path / "state", tmp_path / "extract",
                          tmp_path / "patterns", tmp_path / "proposals",
                          tmp_path / "history"):
            assert directory.exists()

    def test_write_and_read_json_round_trip(self, tmp_path):
        path = tmp_path / "data.json"
        write_json(path, {"key": "value", "n": 1})
        assert read_json(path) == {"key": "value", "n": 1}

    def test_read_json_missing_returns_empty(self, tmp_path):
        assert read_json(tmp_path / "missing.json") == {}
