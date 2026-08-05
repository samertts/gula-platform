"""Unit tests for GULA-LEARNER-001 — Phase 3 playbooks, Phase 4 runbooks, Phase 5 memory."""

from __future__ import annotations

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3]))

from scripts.learner import memory, playbooks, runbooks
from scripts.learner.memory import (
    add_graph_node,
    evolve_memory,
    find_memory_by_title,
    graph_nodes,
    graph_size,
    link_item,
    memory_exists,
    persist_memory,
)
from scripts.learner.playbooks import (
    PLAYBOOK_STEPS,
    find_playbook_by_title,
    generate_playbook,
    next_playbook_id,
    persist_playbook,
    playbook_exists,
)
from scripts.learner.runbooks import (
    RUNBOOK_STEPS,
    find_runbook_by_title,
    generate_runbook,
    next_runbook_id,
    persist_runbook,
    runbook_exists,
)


class TestPlaybooks:
    def test_steps_cover_seven_kinds(self):
        assert len(PLAYBOOK_STEPS) == 7
        for kind in ("deployment", "recovery", "debugging", "performance",
                     "security", "testing", "infrastructure"):
            assert kind in PLAYBOOK_STEPS

    def test_generate_playbook_all_kinds(self):
        for kind in PLAYBOOK_STEPS:
            playbook = generate_playbook(kind)
            assert playbook is not None
            assert playbook.kind == "playbook"
            assert playbook.status == "verified"
            assert playbook.confidence == "verified"

    def test_generate_playbook_invalid_kind(self):
        assert generate_playbook("bogus") is None

    def test_generate_playbook_steps_numbered(self):
        playbook = generate_playbook("deployment")
        assert playbook is not None
        body = playbook.body
        assert "1. Confirm the release is reviewed and gated" in body
        assert "## Steps" in body
        assert "## Verification" in body

    def test_generate_playbook_embeds_solution(self):
        from scripts.learner.core import Extraction

        extraction = Extraction(source="x", solution="deployed with rollback")
        playbook = generate_playbook("recovery", extraction)
        assert playbook is not None
        assert "deployed with rollback" in playbook.body

    def test_next_playbook_id_isolated(self, tmp_path, monkeypatch):
        monkeypatch.setattr(playbooks, "PLAYBOOK_DIR", tmp_path)
        assert next_playbook_id() == "PLAYBOOK-000001"

    def test_next_playbook_id_sequences(self, tmp_path, monkeypatch):
        monkeypatch.setattr(playbooks, "PLAYBOOK_DIR", tmp_path)
        (tmp_path / "PLAYBOOK-000003_x.md").write_text("x", encoding="utf-8")
        assert next_playbook_id() == "PLAYBOOK-000004"

    def test_persist_playbook(self, tmp_path, monkeypatch):
        monkeypatch.setattr(playbooks, "PLAYBOOK_DIR", tmp_path)
        playbook = generate_playbook("security")
        assert playbook is not None
        path = persist_playbook(playbook)
        assert path.exists()
        text = path.read_text(encoding="utf-8")
        assert playbook.item_id in text
        assert "## Goal" in text

    def test_playbook_exists_and_find(self, tmp_path, monkeypatch):
        monkeypatch.setattr(playbooks, "PLAYBOOK_DIR", tmp_path)
        assert playbook_exists("X") is False
        playbook = generate_playbook("deployment", title="Custom Deployment Playbook")
        assert playbook is not None
        persist_playbook(playbook)
        assert playbook_exists("Custom Deployment Playbook") is True
        found = find_playbook_by_title("Custom Deployment Playbook")
        assert found is not None
        assert found.item_id == playbook.item_id


class TestRunbooks:
    def test_steps_cover_eight_kinds(self):
        assert len(RUNBOOK_STEPS) == 8
        for kind in ("incidents", "recovery", "monitoring", "production",
                     "maintenance", "scaling", "backup", "rollback"):
            assert kind in RUNBOOK_STEPS

    def test_generate_runbook_all_kinds(self):
        for kind in RUNBOOK_STEPS:
            runbook = generate_runbook(kind)
            assert runbook is not None
            assert runbook.kind == "runbook"
            assert runbook.status == "verified"

    def test_generate_runbook_invalid_kind(self):
        assert generate_runbook("bogus") is None

    def test_generate_runbook_procedure(self):
        runbook = generate_runbook("production")
        assert runbook is not None
        assert "## Procedure" in runbook.body
        assert "## Success Criteria" in runbook.body
        assert "1. Verify the deployed version and environment" in runbook.body

    def test_next_runbook_id_isolated(self, tmp_path, monkeypatch):
        monkeypatch.setattr(runbooks, "RUNBOOK_DIR", tmp_path)
        assert next_runbook_id() == "RUNBOOK-000001"

    def test_persist_runbook(self, tmp_path, monkeypatch):
        monkeypatch.setattr(runbooks, "RUNBOOK_DIR", tmp_path)
        runbook = generate_runbook("backup")
        assert runbook is not None
        path = persist_runbook(runbook)
        assert path.exists()
        assert "## Purpose" in path.read_text(encoding="utf-8")

    def test_runbook_exists_and_find(self, tmp_path, monkeypatch):
        monkeypatch.setattr(runbooks, "RUNBOOK_DIR", tmp_path)
        assert runbook_exists("Y") is False
        runbook = generate_runbook("rollback", title="Custom Rollback Runbook")
        assert runbook is not None
        persist_runbook(runbook)
        assert runbook_exists("Custom Rollback Runbook") is True
        found = find_runbook_by_title("Custom Rollback Runbook")
        assert found is not None
        assert found.item_id == runbook.item_id


class TestMemory:
    def test_evolve_memory_invalid_kind(self, tmp_path, monkeypatch):
        monkeypatch.setattr(memory, "MEMORY_DIR", tmp_path)
        try:
            evolve_memory("bogus")
            raised = False
        except ValueError:
            raised = True
        assert raised

    def test_evolve_memory_kinds(self, tmp_path, monkeypatch):
        monkeypatch.setattr(memory, "MEMORY_DIR", tmp_path)
        for kind in ("project", "engineering", "decision", "architecture", "deployment"):
            item = evolve_memory(kind, body="note")
            assert item.kind == "memory"
            assert kind in item.tags

    def test_persist_memory(self, tmp_path, monkeypatch):
        monkeypatch.setattr(memory, "MEMORY_DIR", tmp_path)
        item = evolve_memory("engineering", title="Memory Entry", body="note")
        path = persist_memory(item)
        assert path.exists()
        text = path.read_text(encoding="utf-8")
        assert item.item_id in text
        assert "# KNOW-" in text

    def test_memory_exists_and_find(self, tmp_path, monkeypatch):
        monkeypatch.setattr(memory, "MEMORY_DIR", tmp_path)
        assert memory_exists("Nonexistent Entry") is False
        item = evolve_memory("engineering", title="My Memory Entry", body="note")
        persist_memory(item)
        assert memory_exists("My Memory Entry") is True
        found = find_memory_by_title("My Memory Entry")
        assert found is not None
        assert found.item_id == item.item_id

    def test_link_item_dedupes(self):
        from scripts.learner.core import KnowledgeItem

        item = KnowledgeItem(item_id="SKILL-000001", kind="skill", title="X",
                             tags=["skill"])
        link_item(item, ["PLAYBOOK-000001", "PLAYBOOK-000001"])
        assert item.tags.count("PLAYBOOK-000001") == 1

    def test_add_graph_node_and_size(self, tmp_path, monkeypatch):
        monkeypatch.setattr(memory, "GRAPH_DIR", tmp_path)
        monkeypatch.setattr(memory, "GRAPH_INDEX", tmp_path / "graph.json")
        add_graph_node("A", kind="skill", title="A", related=["B"])
        add_graph_node("B", kind="runbook", title="B", related=["A"])
        assert graph_size() == 2
        nodes = graph_nodes()
        assert {node["id"] for node in nodes} == {"A", "B"}

    def test_add_graph_node_refresh_same_id(self, tmp_path, monkeypatch):
        monkeypatch.setattr(memory, "GRAPH_DIR", tmp_path)
        monkeypatch.setattr(memory, "GRAPH_INDEX", tmp_path / "graph.json")
        add_graph_node("A", kind="skill", title="A", related=["B"])
        add_graph_node("A", kind="skill", title="A", related=["B", "C"])
        add_graph_node("C", kind="memory", title="C", related=[])
        assert graph_size() == 2
        node_a = next(node for node in graph_nodes() if node["id"] == "A")
        assert node_a["related"] == ["B", "C"]
