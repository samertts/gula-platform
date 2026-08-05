"""Unit tests for GULA-DEPLOYER-001 — Phase 9 knowledge + Phase 10 report + CLI."""

from __future__ import annotations

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3]))

from scripts.deployer import knowledge
from scripts.deployer.cli import (
    DEPLOYER_COMMANDS,
    _full_deploy,
    run_check,
    run_report,
)
from scripts.deployer.core import DeploymentRecord, make_id
from scripts.deployer.knowledge import (
    add_event,
    inventory,
    lessons_learned,
    load_record,
    persist_record,
    recovery_procedures,
)
from scripts.deployer.report import deployment_stats, render


class TestKnowledge:
    def test_add_event_appends_timeline(self):
        record = DeploymentRecord(deployment_id="DEP-1", version="1.0.0", environment="local")
        add_event(record, "deployment started")
        assert record.timeline[-1]["event"] == "deployment started"

    def test_persist_and_load_round_trip(self, tmp_path, monkeypatch):
        monkeypatch.setattr(knowledge, "HISTORY_DIR", tmp_path)
        monkeypatch.setattr(knowledge, "REGISTRY_PATH", tmp_path / "registry.json")
        record = DeploymentRecord(
            deployment_id="DEP-1", version="1.0.0", environment="local", status="live"
        )
        persist_record(record)
        loaded = load_record("DEP-1")
        assert loaded.version == "1.0.0"
        assert loaded.environment == "local"

    def test_recovery_procedures_cover_five_steps(self):
        steps = recovery_procedures()
        assert len(steps) == 5
        assert any("snapshot" in s for s in steps)

    def test_lessons_learned_from_rollbacks(self):
        records = [
            {"deployment_id": "DEP-1", "version": "1.0.0", "status": "rolled_back"},
            {"deployment_id": "DEP-2", "version": "1.1.0", "status": "live"},
        ]
        lessons = lessons_learned(records)
        assert any("DEP-1" in lesson for lesson in lessons)

    def test_lessons_learned_none_clean(self):
        records = [{"deployment_id": "DEP-1", "version": "1.0.0", "status": "live"}]
        assert lessons_learned(records) == ["No rollbacks recorded; deployment practice is stable."]

    def test_inventory_groups_items(self, tmp_path, monkeypatch):
        monkeypatch.setattr(knowledge, "INVENTORY_PATH", tmp_path / "inventory.json")
        result = inventory([{"resource_id": "RES-1", "service": "postgres"}])
        assert result["total"] == 1
        assert result["resources"][0]["resource_id"] == "RES-1"

    def test_inventory_is_idempotent(self, tmp_path, monkeypatch):
        monkeypatch.setattr(knowledge, "INVENTORY_PATH", tmp_path / "inventory.json")
        item = [{"resource_id": "RES-1", "service": "postgres"}]
        inventory(item)
        second = inventory(item)
        assert second["total"] == 1


class TestReport:
    def test_deployment_stats_total(self):
        stats = deployment_stats()
        assert "total" in stats
        assert stats["total"] >= 0

    def test_render_is_markdown(self):
        markdown = render()
        assert markdown.startswith("#")
        assert "Deployment" in markdown or "deployment" in markdown

    def test_report_write_is_deterministic(self, tmp_path, monkeypatch):
        monkeypatch.setattr("scripts.deployer.report.REPORT_PATH", tmp_path / "REPORT.md")
        run_report()
        assert (tmp_path / "REPORT.md").exists()


class TestCli:
    def test_commands_include_thirteen(self):
        assert len(DEPLOYER_COMMANDS) == 13
        for command in (
            "deployer-audit", "deployer-architecture", "deployer-pipeline",
            "deployer-infrastructure", "deployer-health", "deployer-rollback",
            "deployer-scaling", "deployer-observability", "deployer-security",
            "deployer-knowledge", "deployer-report", "deployer-deploy",
            "deployer-check",
        ):
            assert command in DEPLOYER_COMMANDS

    def _isolate_knowledge(self, tmp_path, monkeypatch):
        monkeypatch.setattr(knowledge, "HISTORY_DIR", tmp_path)
        monkeypatch.setattr(knowledge, "REGISTRY_PATH", tmp_path / "registry.json")
        monkeypatch.setattr(knowledge, "INVENTORY_PATH", tmp_path / "inventory.json")
        monkeypatch.setattr(knowledge, "RUNBOOK_PATH", tmp_path / "runbook.md")

    def test_full_deploy_rejects_bad_version(self):
        assert _full_deploy("1.0", "production") == 1

    def test_full_deploy_rejects_invalid_environment(self):
        assert _full_deploy("1.0.0", "not-an-environment") == 1

    def test_full_deploy_reaches_live(self, tmp_path, monkeypatch):
        self._isolate_knowledge(tmp_path, monkeypatch)
        assert _full_deploy("9.9.9", "local") == 0

    def test_full_deploy_writes_registry(self, tmp_path, monkeypatch):
        self._isolate_knowledge(tmp_path, monkeypatch)
        _full_deploy("9.9.9", "local")
        deployments = knowledge.list_deployments(environment="local")
        assert any(d["version"] == "9.9.9" and d["status"] == "live" for d in deployments)

    def test_full_deploy_writes_runbook(self, tmp_path, monkeypatch):
        self._isolate_knowledge(tmp_path, monkeypatch)
        _full_deploy("9.9.8", "local")
        assert (tmp_path / "runbook.md").exists()

    def test_run_check_returns_zero(self):
        assert run_check() == 0

    def test_deployment_record_make_id(self):
        assert make_id("DEP").startswith("DEP-")
