"""Unit tests for GULA-REVIEWER-001 — CLI integration with the Kernel."""

from __future__ import annotations

import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3]))

from scripts.reviewer.cli import REVIEWER_COMMANDS


class TestCliRegistry:
    def test_all_phase_commands(self):
        expected = {
            "reviewer-audit",
            "reviewer-review",
            "reviewer-area",
            "reviewer-gate",
            "reviewer-report",
            "reviewer-check",
        }
        assert expected <= set(REVIEWER_COMMANDS)

    def test_each_area_shortcut_present(self):
        for area in {"architecture", "code", "security", "tests",
                     "deployment", "documentation", "performance", "knowledge"}:
            assert f"reviewer-{area}" in REVIEWER_COMMANDS

    def test_each_command_callable(self):
        for name, fn in REVIEWER_COMMANDS.items():
            assert callable(fn), name

    def test_no_duplicate_commands(self):
        assert len(REVIEWER_COMMANDS) == len(set(REVIEWER_COMMANDS))


class TestKernelIntegration:
    def test_kernel_cli_has_reviewer_commands(self):
        from scripts.kernel.cli import COMMANDS

        for name in REVIEWER_COMMANDS:
            assert name in COMMANDS
            assert callable(COMMANDS[name])

    def test_kernel_commits_are_present(self):
        from scripts.kernel.cli import COMMANDS

        assert "builder-check" in COMMANDS
        assert "ext-check" in COMMANDS
        assert "reviewer-check" in COMMANDS
