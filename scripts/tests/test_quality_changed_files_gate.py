from __future__ import annotations

import json
import subprocess
import sys
from collections import Counter
from pathlib import Path
from typing import Any

import pytest

from scripts import quality_changed_files_gate as gate
from scripts.quality_changed_files_gate import (
    ToolResult,
    compare_counts,
    execution_blockers,
    normalise_path,
    parse_mypy_text,
    parse_ruff_json,
    run_mypy,
    run_ruff,
)


def test_parse_ruff_json_normalises_paths_and_preserves_codes(tmp_path: Path) -> None:
    payload = json.dumps(
        [
            {
                "filename": str(tmp_path / "backend/app/security/auth.py"),
                "code": "RUF001",
                "message": "ambiguous unicode character",
                "location": {"row": 12, "column": 4},
            }
        ]
    )

    diagnostics = parse_ruff_json(tmp_path, payload)

    assert len(diagnostics) == 1
    assert diagnostics[0].path == "backend/app/security/auth.py"
    assert diagnostics[0].line == 12
    assert diagnostics[0].code == "RUF001"


def test_parse_mypy_text_accepts_error_codes(tmp_path: Path) -> None:
    output = (
        f"{tmp_path}/backend/app/security/auth.py:8: error: Missing return statement  "
        "[return]\n"
    )

    diagnostics = parse_mypy_text(tmp_path, output)

    assert len(diagnostics) == 1
    assert diagnostics[0].path == "backend/app/security/auth.py"
    assert diagnostics[0].line == 8
    assert diagnostics[0].code == "return"


def test_compare_counts_fails_only_on_increase() -> None:
    baseline = Counter({"a.py": 3, "b.py": 2})
    head = Counter({"a.py": 3, "b.py": 1, "c.py": 1})

    assert compare_counts(baseline, head, "gate") == [
        "gate: c.py: 0 -> 1 (+1)"
    ]


def test_normalise_path_handles_relative_and_absolute_paths(tmp_path: Path) -> None:
    assert normalise_path(tmp_path, "./backend/app/auth.py") == "backend/app/auth.py"
    assert normalise_path(tmp_path, str(tmp_path / "backend/app/auth.py")) == (
        "backend/app/auth.py"
    )


# ── A tool that did not run must never read as clean ───────────────────────
#
# Regression for the false PASS: the gate reported "0 diagnostics" and exited
# PASS while MyPy had exited 2 without analysing anything, because baseline and
# head failed identically and the old check only fired when the two differed.


def _completed(returncode: int, stdout: str = "", stderr: str = "") -> Any:
    return subprocess.CompletedProcess(
        args=["mypy"], returncode=returncode, stdout=stdout, stderr=stderr
    )


@pytest.fixture()
def one_python_file(tmp_path: Path) -> Path:
    target = tmp_path / "sample.py"
    target.write_text("x = 1\n", encoding="utf-8")
    return tmp_path


@pytest.mark.parametrize("runner", [run_mypy, run_ruff])
def test_a_clean_run_is_measured_and_reports_nothing(
    monkeypatch: pytest.MonkeyPatch, one_python_file: Path, runner: Any
) -> None:
    """Exit 0: the tool ran and found nothing. That is a genuine pass."""
    monkeypatch.setattr(gate, "run", lambda *a, **k: _completed(0, stdout="[]"))
    result = runner(one_python_file, ["sample.py"], "changed-files")
    assert result.measured is True
    assert result.execution_error is None
    assert result.diagnostics == ()
    assert execution_blockers(result, result) == []


def test_mypy_findings_are_measured_and_counted(
    monkeypatch: pytest.MonkeyPatch, one_python_file: Path
) -> None:
    """Exit 1: the tool ran and found errors. Those must reach the comparison."""
    monkeypatch.setattr(
        gate,
        "run",
        lambda *a, **k: _completed(
            1, stdout="sample.py:1: error: Something is wrong  [assignment]\n"
        ),
    )
    result = run_mypy(one_python_file, ["sample.py"], "changed-files")
    assert result.measured is True
    assert len(result.diagnostics) == 1
    assert result.diagnostics[0].code == "assignment"
    # A candidate that adds an error to a previously clean file is a regression.
    clean = ToolResult("mypy", "changed-files", 0, (), "", "")
    assert compare_counts(clean.counts, result.counts, "MyPy") == [
        "MyPy: sample.py: 0 -> 1 (+1)"
    ]


@pytest.mark.parametrize("returncode", [2, 3, -11])
@pytest.mark.parametrize("runner", [run_mypy, run_ruff])
def test_a_failed_run_yields_no_diagnostics_and_blocks(
    monkeypatch: pytest.MonkeyPatch, one_python_file: Path, returncode: int, runner: Any
) -> None:
    """The defect itself.

    A tool that exits outside {0, 1} did not complete. Its empty diagnostic list
    means "unknown", so it must not be measured, must not be counted, and must
    block — including when the baseline failed in exactly the same way, which is
    the normal case because both sides run in the same environment.
    """
    monkeypatch.setattr(
        gate,
        "run",
        lambda *a, **k: _completed(
            returncode, stderr="No module named 'sqlalchemy'"
        ),
    )
    result = runner(one_python_file, ["sample.py"], "changed-files")
    assert result.measured is False
    assert result.execution_error
    assert result.diagnostics == ()
    # Identical failure on both sides: previously silent, now two blockers.
    blockers = execution_blockers(result, result)
    assert len(blockers) == 2
    assert all("did not run" in b for b in blockers)


def test_an_unmeasured_baseline_blocks_even_when_the_candidate_is_clean() -> None:
    """Non-regression cannot be established against a baseline that never ran."""
    unmeasured = ToolResult("mypy", "changed-files", 2, (), "", "boom", "boom")
    measured = ToolResult("mypy", "changed-files", 0, (), "", "")
    blockers = execution_blockers(unmeasured, measured)
    assert len(blockers) == 1
    assert "nothing to compare against" in blockers[0]


def test_a_failed_run_cannot_be_mistaken_for_a_clean_one() -> None:
    """The two states the gate used to conflate, stated side by side."""
    ran_clean = ToolResult("mypy", "changed-files", 0, (), "", "")
    never_ran = ToolResult("mypy", "changed-files", 2, (), "", "boom", "boom")
    assert ran_clean.diagnostics == never_ran.diagnostics == ()
    assert ran_clean.measured is not never_ran.measured
    assert execution_blockers(ran_clean, ran_clean) == []
    assert execution_blockers(never_ran, never_ran) != []


def test_the_gate_honours_a_real_subprocess_exit_code(one_python_file: Path) -> None:
    """End-to-end through the real ``run``, not a monkeypatched one.

    Proves the interpretation composes with actual process execution rather
    than only with a stubbed CompletedProcess.
    """
    real = gate.run((sys.executable, "-c", "import sys; sys.exit(2)"), one_python_file)
    assert real.returncode == 2
    assert real.returncode not in (0, 1), "exit 2 must not be inside the measured range"
