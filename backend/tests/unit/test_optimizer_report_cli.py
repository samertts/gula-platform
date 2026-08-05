"""Unit tests for GULA-OPTIMIZER-001 — report + CLI wiring."""

from __future__ import annotations

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3]))

from scripts.optimizer import cli
from scripts.optimizer.report import build_report


class TestCliCommands:
    def test_all_thirteen_commands_registered(self):
        assert len(cli.OPTIMIZER_COMMANDS) == 13

    def test_command_names_are_prefixed(self):
        for name in cli.OPTIMIZER_COMMANDS:
            assert name.startswith("optimizer-")

    def test_specific_commands_present(self):
        for name in ("optimizer-audit", "optimizer-analyze",
                     "optimizer-bottlenecks", "optimizer-architecture",
                     "optimizer-resources", "optimizer-dx", "optimizer-debt",
                     "optimizer-optimize", "optimizer-evolve",
                     "optimizer-validate", "optimizer-report",
                     "optimizer-run", "optimizer-check"):
            assert name in cli.OPTIMIZER_COMMANDS

    def test_run_check_returns_zero(self, capsys):
        code = cli.run_check()
        assert code == 0
        captured = capsys.readouterr()
        assert "ALL OPTIMIZER CHECKS PASSED" in captured.out


class TestReport:
    def test_build_report_writes_file(self, tmp_path, monkeypatch):
        from scripts.optimizer import analyze as analyze_module
        from scripts.optimizer import report as report_module

        monkeypatch.setattr(analyze_module, "BENCHMARK_PATH", tmp_path / "bench.json")
        monkeypatch.setattr(analyze_module, "BENCHMARK_DIR", tmp_path)
        monkeypatch.setattr(report_module, "REPORT_PATH", tmp_path / "report.md")
        report_module.load_baseline = list
        report_module.load_bottlenecks = list
        report_module.load_debt = list
        report_module.load_dx = list
        report_module.load_proposals = list
        report_module.load_runs = list
        path = report_module.build_report()
        assert path.name == "report.md"
        text = path.read_text(encoding="utf-8")
        assert "GULA-OPTIMIZER-001" in text
        assert "Optimization Engine" in text

    def test_build_report_real_repo(self):
        path = build_report()
        text = path.read_text(encoding="utf-8")
        assert "## Baseline Metrics" in text
        assert "## Verdict" in text
        assert "GULA-OPTIMIZER-001 COMPLETE" in text


class TestKernelIntegration:
    def test_kernel_exposes_optimizer_commands(self):
        from scripts.kernel import cli as kernel_cli

        for name in ("optimizer-check", "optimizer-run", "optimizer-audit"):
            assert name in kernel_cli.COMMANDS

    def test_kernel_check_runs(self, capsys):
        from scripts.kernel import cli as kernel_cli

        code = kernel_cli.run_check()
        assert code == 0
