"""Unit tests for GULA-BUILDER-001 — CLI integration with the Kernel."""

from __future__ import annotations

import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3]))

from scripts.builder.cli import BUILDER_COMMANDS


class TestCliRegistry:
    def test_all_phase_commands(self):
        expected = {
            "builder-audit",
            "builder-analyze",
            "builder-plan",
            "builder-impact",
            "builder-execute",
            "builder-recover",
            "builder-knowledge",
            "builder-review",
            "builder-report",
            "builder-check",
        }
        assert expected <= set(BUILDER_COMMANDS)

    def test_each_command_callable(self):
        for name, fn in BUILDER_COMMANDS.items():
            assert callable(fn), name

    def test_no_duplicate_commands(self):
        assert len(BUILDER_COMMANDS) == len(set(BUILDER_COMMANDS))


class TestKernelIntegration:
    def test_kernel_cli_has_builder_commands(self):
        from scripts.kernel.cli import COMMANDS

        for name in BUILDER_COMMANDS:
            assert name in COMMANDS
            assert callable(COMMANDS[name])
