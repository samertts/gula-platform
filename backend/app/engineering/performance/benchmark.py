from __future__ import annotations

import subprocess
import time
from dataclasses import dataclass
from pathlib import Path


@dataclass
class BenchmarkResult:
    name: str
    value: float
    unit: str
    threshold: float | None = None
    passed: bool | None = None


class PerformanceBenchmark:
    def __init__(self, project_root: Path | str):
        self.project_root = Path(project_root)
        self.results: list[BenchmarkResult] = []

    def measure_startup_time(self, module_path: str = "app.main:app") -> BenchmarkResult:
        start = time.monotonic()
        try:
            subprocess.run(
                [
                    "python",
                    "-c",
                    f"import importlib; importlib.import_module('{module_path.split(':', maxsplit=1)[0]}')",
                ],
                capture_output=True,
                text=True,
                cwd=str(self.project_root),
                timeout=30,
            )
            elapsed = (time.monotonic() - start) * 1000
            return BenchmarkResult(
                name="startup_time",
                value=round(elapsed, 1),
                unit="ms",
                threshold=2000.0,
                passed=elapsed < 2000,
            )
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return BenchmarkResult(name="startup_time", value=-1, unit="ms")

    def measure_import_time(self, package: str) -> BenchmarkResult:
        start = time.monotonic()
        try:
            subprocess.run(
                ["python", "-c", f"import {package}"],
                capture_output=True,
                cwd=str(self.project_root),
                timeout=30,
            )
            elapsed = (time.monotonic() - start) * 1000
            return BenchmarkResult(
                name=f"import_{package}",
                value=round(elapsed, 1),
                unit="ms",
                threshold=500.0,
                passed=elapsed < 500,
            )
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return BenchmarkResult(name=f"import_{package}", value=-1, unit="ms")

    def measure_binary_size(self, path: str | None = None) -> BenchmarkResult:
        target = Path(path) if path else self.project_root
        try:
            result = subprocess.run(
                ["du", "-sh", "--apparent-size", str(target)],
                capture_output=True,
                text=True,
                timeout=10,
            )
            size_str = result.stdout.split()[0]
            return BenchmarkResult(
                name="binary_size",
                value=0,
                unit=size_str,
            )
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return BenchmarkResult(name="binary_size", value=-1, unit="bytes")

    def run_all(self) -> list[BenchmarkResult]:
        self.results = [
            self.measure_startup_time(),
            # NR-058: a module path in a string is invisible to the AST guard that
            # holds the rest of this rule. Importing `backend.app.kernel` here would
            # have benchmarked a second copy of the kernel, not the one that runs.
            self.measure_import_time("app.kernel"),
        ]
        return self.results
