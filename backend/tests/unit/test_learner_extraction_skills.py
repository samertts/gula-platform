"""Unit tests for GULA-LEARNER-001 — Phase 1 extraction, Phase 2 skills."""

from __future__ import annotations

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3]))

from scripts.learner import extract, skills
from scripts.learner.extract import (
    extract_from_deployment,
    extract_from_mission,
    list_extractions,
    missing_fields,
    persist_extraction,
)
from scripts.learner.skills import (
    find_skill_by_title,
    generate_skill,
    infer_category,
    next_skill_id,
    persist_skill,
    skill_exists,
)


class TestExtraction:
    def test_extract_builds_structured_record(self):
        extraction = extract.extract(
            "mission:ORN-1",
            problem="p",
            cause="c",
            solution="s",
            alternative_solutions=["a1"],
            rejected_solutions=["r1"],
            tradeoffs=["t1"],
            risks=["risk"],
            lessons=["lesson"],
            performance_impact="perf",
            security_impact="sec",
            recommendations=["rec"],
            reusable=True,
        )
        assert extraction.problem == "p"
        assert extraction.solution == "s"
        assert extraction.reusable is True
        assert extraction.lessons == ["lesson"]

    def test_extract_defaults_lists_empty(self):
        extraction = extract.extract("mission:ORN-1", problem="p")
        assert extraction.alternative_solutions == []
        assert extraction.rejected_solutions == []
        assert extraction.reusable is False

    def test_extract_from_mission_deterministic(self):
        mission = {"objective": "Build X", "mission_type": "bug", "status": "done"}
        extraction = extract_from_mission(mission)
        assert extraction.source == "mission:unknown"
        assert "Build X" in extraction.problem
        assert extraction.lessons
        assert extraction.reusable is True

    def test_extract_from_mission_not_reusable(self):
        mission = {"objective": "X", "mission_type": "documentation", "status": "done"}
        extraction = extract_from_mission(mission)
        assert extraction.reusable is False

    def test_extract_from_deployment(self):
        deployment = {
            "deployment_id": "DEP-1",
            "version": "1.2.0",
            "environment": "production",
            "status": "live",
            "validations": [
                {"component": "api", "status": "pass"},
                {"component": "database", "status": "fail"},
            ],
            "rollbacks": [],
        }
        extraction = extract_from_deployment(deployment)
        assert extraction.source == "deployment:DEP-1"
        assert "1.2.0" in extraction.solution
        assert "database" in extraction.risks[0]
        assert extraction.reusable is True

    def test_extract_from_deployment_rollback_lesson(self):
        deployment = {
            "deployment_id": "DEP-2",
            "version": "1.0.0",
            "environment": "staging",
            "status": "rolled_back",
            "validations": [{"component": "api", "status": "fail"}],
            "rollbacks": [{"status": "rolled_back"}],
        }
        extraction = extract_from_deployment(deployment)
        assert any("rollback" in lesson.lower() for lesson in extraction.lessons)
        assert extraction.reusable is False

    def test_missing_fields(self):
        extraction = extract_from_mission({"objective": "X", "mission_type": "bug"})
        missing = missing_fields(extraction)
        assert "problem" not in missing
        assert "alternative_solutions" in missing
        assert "rejected_solutions" in missing

    def test_persist_and_list_extractions(self, tmp_path, monkeypatch):
        monkeypatch.setattr(extract, "EXTRACTION_DIR", tmp_path)
        extraction = extract.extract("mission:ORN-1", problem="p", solution="s")
        path = persist_extraction(extraction)
        assert path.exists()
        loaded = extract.load_extraction(path)
        assert loaded.source == "mission:ORN-1"
        assert loaded.solution == "s"
        assert len(list_extractions()) == 1


class TestSkills:
    def test_next_skill_id_isolated(self, tmp_path, monkeypatch):
        monkeypatch.setattr(skills, "SKILL_DIR", tmp_path)
        assert next_skill_id() == "SKILL-000001"

    def test_next_skill_id_sequences(self, tmp_path, monkeypatch):
        monkeypatch.setattr(skills, "SKILL_DIR", tmp_path)
        (tmp_path / "SKILL-000003_x.md").write_text("x", encoding="utf-8")
        (tmp_path / "SKILL-000007_y.md").write_text("x", encoding="utf-8")
        assert next_skill_id() == "SKILL-000008"

    def test_infer_category_by_keywords(self):
        from scripts.learner.core import Extraction

        assert infer_category(Extraction(
            source="x", solution="docker compose deployment rollout")) == "infrastructure"
        assert infer_category(Extraction(
            source="x", problem="react typescript component page")) == "frontend"
        assert infer_category(Extraction(
            source="x", problem="pytest coverage test suite")) == "testing"

    def test_infer_category_falls_back_to_tooling(self):
        from scripts.learner.core import Extraction

        assert infer_category(Extraction(source="x", problem="zzz qqq")) == "tooling"

    def test_generate_skill_rejects_invalid_confidence(self):
        extraction = extract.extract("mission:ORN-1", problem="deploy docker", reusable=True)
        try:
            generate_skill(extraction, confidence="bogus")
            raised = False
        except ValueError:
            raised = True
        assert raised

    def test_generate_skill_rejects_invalid_difficulty(self):
        extraction = extract.extract("mission:ORN-1", problem="deploy docker", reusable=True)
        try:
            generate_skill(extraction, difficulty="bogus")
            raised = False
        except ValueError:
            raised = True
        assert raised

    def test_generate_skill_none_when_not_reusable(self):
        extraction = extract.extract("mission:ORN-1", problem="deploy docker")
        assert generate_skill(extraction) is None

    def test_generate_skill_fields(self):
        extraction = extract.extract(
            "mission:ORN-1",
            problem="Docker build fails during CI deployment",
            solution="Pin base image and add healthcheck",
            security_impact="verified",
            reusable=True,
        )
        skill = generate_skill(extraction, title="Docker CI Fix", technology="docker")
        assert skill is not None
        assert skill.skill_id.startswith("SKILL-")
        assert skill.title == "Docker CI Fix"
        assert skill.technology == "docker"
        assert skill.version == "1.0"
        assert skill.verification  # defaulted from security impact

    def test_persist_skill_writes_markdown(self, tmp_path, monkeypatch):
        monkeypatch.setattr(skills, "SKILL_DIR", tmp_path)
        extraction = extract.extract("mission:ORN-1", problem="deploy", reusable=True)
        skill = generate_skill(extraction, title="Deploy Skill", technology="docker")
        assert skill is not None
        path = persist_skill(skill)
        assert path.exists()
        text = path.read_text(encoding="utf-8")
        assert skill.skill_id in text
        assert 'version: "1.0"' in text
        assert "## Problem" in text
        assert "## Solution" in text

    def test_skill_exists_and_find(self, tmp_path, monkeypatch):
        monkeypatch.setattr(skills, "SKILL_DIR", tmp_path)
        assert skill_exists("No Skill Here") is False
        extraction = extract.extract("mission:ORN-1", problem="deploy", reusable=True)
        skill = generate_skill(extraction, title="My Unique Skill", technology="docker")
        assert skill is not None
        persist_skill(skill)
        assert skill_exists("My Unique Skill") is True
        found = find_skill_by_title("My Unique Skill")
        assert found is not None
        assert found.skill_id == skill.skill_id

    def test_find_skill_by_title_missing(self, tmp_path, monkeypatch):
        monkeypatch.setattr(skills, "SKILL_DIR", tmp_path)
        assert find_skill_by_title("Missing") is None
