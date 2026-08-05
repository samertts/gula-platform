"""Unit tests for GULA-ARCHITECT-001 — coordination (Phase 8), health (Phase 9),
report (Phase 10), and CLI wiring."""

from __future__ import annotations

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3]))

from scripts.architect import cli
from scripts.architect.coordination import (
    ENGINE_CONTRACTS,
    build_coordination,
    persist_coordination,
    render_markdown as render_coordination,
)
from scripts.architect.core import MATURITY_LEVELS, maturity_level
from scripts.architect.health import (
    measure_health,
    persist_health,
    render_markdown as render_health,
)
from scripts.architect.report import build_report


class TestCoordination:
    def test_build_coordination_returns_six_engines(self):
        contracts = build_coordination()
        assert len(contracts) == 6

    def test_engines_are_the_ai_constellation(self):
        engines = {c.engine for c in build_coordination()}
        assert engines == {"builder", "reviewer", "orchestrator", "learner",
                           "optimizer", "deployer"}

    def test_every_engine_has_role_and_mandate(self):
        for contract in build_coordination():
            assert contract.role
            assert contract.mandate
            assert contract.status in {"integrated", "missing"}

    def test_all_contracts_defined_in_registry(self):
        contracts = build_coordination()
        for contract in contracts:
            assert contract.engine in ENGINE_CONTRACTS

    def test_persist_coordination_writes_file(self, tmp_path):
        path = persist_coordination(tmp_path)
        assert path.exists()
        import json

        data = json.loads(path.read_text(encoding="utf-8"))
        assert len(data["contracts"]) == 6

    def test_render_lists_dependencies(self):
        text = render_coordination(build_coordination())
        assert "Dependencies" in text
        assert "builder" in text


class TestHealth:
    def test_health_covers_six_dimensions(self):
        health = measure_health()
        assert len(health.dimensions) == 6

    def test_health_overall_bounded(self):
        health = measure_health()
        assert 0 <= health.overall <= 100

    def test_health_maturity_bounded(self):
        health = measure_health()
        assert 0 <= health.maturity <= 100

    def test_maturity_level_valid(self):
        health = measure_health()
        names = {name for _, _, name in MATURITY_LEVELS}
        assert health.maturity_level in names

    def test_maturity_level_mapping(self):
        assert maturity_level(5) == "initial"
        assert maturity_level(50) == "defined"
        assert maturity_level(95) == "optimizing"

    def test_persist_health_writes_file(self, tmp_path):
        path = persist_health(tmp_path)
        assert path.exists()
        import json

        data = json.loads(path.read_text(encoding="utf-8"))
        assert "maturity" in data
        assert "maturity_level" in data

    def test_render_contains_maturity(self):
        text = render_health(measure_health())
        assert "Maturity score" in text
        assert "Overall health" in text


class TestReport:
    def test_build_report_writes_file(self, tmp_path, monkeypatch):
        import scripts.architect.report as report_module

        monkeypatch.setattr(report_module, "REPORT_PATH", tmp_path / "report.md")
        path = report_module.build_report()
        assert path.name == "report.md"
        text = path.read_text(encoding="utf-8")
        assert "GULA-ARCHITECT-001" in text
        assert "Readiness score" in text
        assert "Improvement Plan" in text

    def test_build_report_real_repo(self):
        path = build_report()
        text = path.read_text(encoding="utf-8")
        assert "## Verdict" in text
        assert "GULA-ARCHITECT-001 COMPLETE" in text
        assert "maturity" in text


class TestCliCommands:
    def test_all_thirteen_commands_registered(self):
        assert len(cli.ARCHITECT_COMMANDS) == 13

    def test_command_names_are_prefixed(self):
        for name in cli.ARCHITECT_COMMANDS:
            assert name.startswith("architect-")

    def test_specific_commands_present(self):
        for name in ("architect-audit", "architect-model",
                     "architect-decisions", "architect-dependencies",
                     "architect-evolution", "architect-risk",
                     "architect-review", "architect-simulation",
                     "architect-coordination", "architect-health",
                     "architect-report", "architect-run", "architect-check"):
            assert name in cli.ARCHITECT_COMMANDS

    def test_run_check_returns_zero(self, capsys):
        code = cli.run_check()
        assert code == 0
        captured = capsys.readouterr()
        assert "ALL ARCHITECT CHECKS PASSED" in captured.out

    def test_launcher_help(self):
        from scripts.architect import __doc__ as architect_doc

        assert "GULA-ARCHITECT-001" in architect_doc


class TestKernelIntegration:
    def test_kernel_exposes_architect_commands(self):
        from scripts.kernel import cli as kernel_cli

        for name in ("architect-check", "architect-run", "architect-audit",
                     "architect-health", "architect-report"):
            assert name in kernel_cli.COMMANDS
