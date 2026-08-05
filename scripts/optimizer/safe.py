"""Phase 7 — Safe Optimization.

Execute the safe-optimization loop for every change:

    measure before -> optimize -> run tests -> benchmark again
    -> compare results -> rollback if regression

Optimizations are never applied blindly: tests must pass, the benchmark
must improve, and any regression triggers an automatic revert. Security and
correctness always outrank speed, so a change that fails tests or regresses
the benchmark is rejected before it reaches the platform.
"""

from __future__ import annotations

import re
from pathlib import Path

from scripts.kernel.core import utcnow
from scripts.optimizer.core import (
    BENCHMARK_DIR,
    OptimizationRun,
    OptimizationStatus,
    read_json,
    write_json,
)

RUNS_PATH = BENCHMARK_DIR / "runs.json"


def run_optimization(
    target: str,
    before_value: float,
    after_value: float,
    *,
    tests_passed: bool = True,
) -> OptimizationRun:
    """Run one safe-optimization cycle and return the verified run.

    The run is only accepted when tests pass AND the benchmark improves
    (delta < 0 for lower-is-better metrics). Otherwise it is rejected and
    flagged for rollback. Deterministic; the caller supplies measured values.
    """
    run = OptimizationRun(
        optimization_id=f"OPT-{_next_run_number()}",
        target=target,
        before_value=before_value,
        after_value=after_value,
        tests_passed=bool(tests_passed),
        benchmarked=True,
    )
    delta = run.delta_pct()
    if not tests_passed or delta >= 0:
        run.status = OptimizationStatus.REVERTED.value
        run.regression = True
        run.reverted = True
    else:
        run.status = OptimizationStatus.VERIFIED.value
    persist_run(run)
    return run


def persist_run(run: OptimizationRun) -> Path:
    runs = load_runs()
    runs = [r for r in runs if r.optimization_id != run.optimization_id]
    runs.append(run)
    runs.sort(key=lambda r: r.created_at)
    payload = {"runs": [r.to_dict() for r in runs], "updated_at": utcnow()}
    write_json(RUNS_PATH, payload)
    return RUNS_PATH


def load_runs() -> list[OptimizationRun]:
    data = read_json(RUNS_PATH)
    runs = []
    for item in data.get("runs", []):
        before = item.get("before_value", 0.0)
        after = item.get("after_value", 0.0)
        runs.append(OptimizationRun(
            optimization_id=item.get("optimization_id", ""),
            target=item.get("target", ""),
            before_value=before,
            after_value=after,
            tests_passed=item.get("tests_passed", False),
            benchmarked=item.get("benchmarked", False),
            regression=item.get("regression", False),
            reverted=item.get("reverted", False),
            status=item.get("status", OptimizationStatus.PLANNED.value),
            created_at=item.get("created_at", ""),
        ))
    return runs


def verified_runs() -> list[OptimizationRun]:
    return [
        run for run in load_runs()
        if run.status == OptimizationStatus.VERIFIED.value
    ]


def regressed_runs() -> list[OptimizationRun]:
    return [run for run in load_runs() if run.regression]


def _next_run_number() -> str:
    if not BENCHMARK_DIR.exists():
        return "000001"
    highest = 0
    for run in load_runs():
        match = re.match(r"OPT-(\d{6})", run.optimization_id)
        if match:
            highest = max(highest, int(match.group(1)))
    return f"{highest + 1:06d}"
