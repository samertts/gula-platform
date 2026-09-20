"""NR-016 — a tool that did not run may never be counted as a clean result.

THE DEFECT THIS PINS
--------------------
`scripts/quality_changed_files_gate.py` is the gate that certifies changed
files. It printed `baseline.mypy_changed: 0 diagnostics ... PASS` while MyPy had
exited 2 without analysing anything ("No module named 'sqlalchemy'"). Two causes
combined:

  * diagnostics were parsed regardless of the exit code, so a failed run
    contributed an empty list that read as clean; and
  * the execution-error check fired only when the head's error *differed* from
    the baseline's -- never the case when both sides run in the same
    environment, which is the usual case.

A tool that never ran was certifying the change. That is the false-green class
in its purest form: not a wrong answer, but a non-answer reported as a good one.

WHY THIS MODULE EXISTS AT ALL
-----------------------------
The fix was recorded as FIXED -- VERIFIED and had no test. Every other gate in
this repository is protected by the gate itself; the gate is the one thing that
cannot be. If it silently returns to counting empty output as clean, nothing
downstream notices, because every check it guards keeps reporting PASS.

WHAT IS ASSERTED
----------------
`measured`, `state` and `execution_blockers` are the three things NR-016
changed, and they are pure functions of a ToolResult, so this needs no
subprocess, no database and no network. The gate's own status mapping
(blockers -> BLOCKED) is asserted through the same values `main()` branches on.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

_GATE = Path(__file__).resolve().parents[2] / "scripts" / "quality_changed_files_gate.py"


@pytest.fixture(scope="module")
def gate():
    """Load the gate by path.

    `scripts/` is not an importable package, and the gate is invoked by CI as a
    file. Loading it the same way keeps this test honest about what ships.
    """
    spec = importlib.util.spec_from_file_location("quality_changed_files_gate", _GATE)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    try:
        yield module
    finally:
        sys.modules.pop(spec.name, None)


def _result(gate, *, scope: str, returncode: int, execution_error: str | None):
    """A run that produced no diagnostics -- the shape the defect turned green."""
    return gate.ToolResult(
        tool="mypy",
        scope=scope,
        returncode=returncode,
        diagnostics=(),
        stdout="",
        stderr="",
        execution_error=execution_error,
    )


def test_a_a_real_clean_run_still_passes(gate):
    """Positive control.

    Without it, a gate that blocked on everything would satisfy every assertion
    below while making the pipeline useless -- and "always BLOCKED" is just as
    uninformative as "always PASS", only louder.
    """
    clean = _result(gate, scope="changed", returncode=0, execution_error=None)

    assert clean.measured is True
    assert clean.state == "CLEAN"
    assert gate.execution_blockers(clean, clean) == []


def test_b_a_tool_that_did_not_run_is_not_clean(gate):
    """The finding. Zero diagnostics from a crashed run is UNKNOWN, not CLEAN."""
    crashed = _result(
        gate, scope="changed", returncode=2,
        execution_error="No module named 'sqlalchemy'",
    )

    assert crashed.measured is False
    assert crashed.state == "DID_NOT_RUN", (
        "a tool that exited 2 without analysing anything reported a state that "
        "a consumer could count as evidence (NR-016)"
    )
    assert crashed.state != "CLEAN"


def test_c_an_identical_failure_on_both_sides_still_blocks(gate):
    """The exact shape that slipped through.

    The old check compared the two sides' execution errors and fired only on a
    difference. Both sides run in the same environment, so a missing dependency
    fails identically on both -- the comparison was empty and the gate printed
    PASS. Two blockers are expected here, one per side.
    """
    same = "No module named 'sqlalchemy'"
    baseline = _result(gate, scope="changed", returncode=2, execution_error=same)
    head = _result(gate, scope="changed", returncode=2, execution_error=same)

    blockers = gate.execution_blockers(baseline, head)

    assert len(blockers) == 2, (
        f"an identical execution failure on both sides produced {len(blockers)} "
        "blockers; when it produces none the gate reports PASS on no analysis "
        "at all (NR-016)"
    )
    assert any("candidate" in b for b in blockers)
    assert any("baseline" in b for b in blockers)


def test_d_an_unmeasured_baseline_blocks_on_its_own(gate):
    """A clean head is not enough.

    Non-regression is a comparison. If the baseline produced no analysis there
    is nothing to compare against, so a green head proves nothing -- the gate
    must block rather than accept the head's own cleanliness as the answer.
    """
    baseline = _result(gate, scope="changed", returncode=2, execution_error="boom")
    head = _result(gate, scope="changed", returncode=0, execution_error=None)

    blockers = gate.execution_blockers(baseline, head)

    assert len(blockers) == 1
    assert "baseline" in blockers[0]
    assert "nothing to compare against" in blockers[0]


def test_e_a_completed_exit_code_with_an_error_is_unmeasured_not_clean(gate):
    """The third state, which is neither of the obvious two.

    `state` deliberately separates DID_NOT_RUN from UNMEASURED: a tool can exit
    inside its own success range and still have been invoked wrongly. Collapsing
    the two back into `measured` alone is how "unknown" starts reading as
    "clean" again.
    """
    odd = _result(gate, scope="changed", returncode=1, execution_error="invoked wrongly")

    assert odd.state == "UNMEASURED"
    assert odd.state != "CLEAN"
    assert odd.measured is False
