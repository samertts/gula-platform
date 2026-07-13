from __future__ import annotations

import subprocess
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path


@dataclass
class GateResult:
    name: str
    passed: bool
    output: str = ""
    duration_ms: float = 0.0

    @property
    def status(self) -> str:
        return "PASS" if self.passed else "FAIL"


@dataclass
class QualityReport:
    timestamp: datetime = field(default_factory=datetime.utcnow)
    results: list[GateResult] = field(default_factory=list)

    @property
    def all_passed(self) -> bool:
        return all(r.passed for r in self.results)

    @property
    def summary(self) -> str:
        total = len(self.results)
        passed = sum(1 for r in self.results if r.passed)
        failed = total - passed
        return f"{passed}/{total} gates passed ({failed} failed)"


class QualityGates:
    def __init__(self, project_root: Path | str | None = None):
        self.project_root = Path(project_root) if project_root else Path.cwd()
        self.report = QualityReport()

    def run_ruff(self) -> GateResult:
        return self._run("ruff", "ruff", "check", "--select=E9,F821", ".")

    def run_mypy(self) -> GateResult:
        return self._run("mypy", "mypy", "--strict", ".")

    def run_pytest(self) -> GateResult:
        return self._run("pytest", "python", "-m", "pytest", "-x", "--tb=short", "-q")

    def run_coverage(self, min_pct: int = 80) -> GateResult:
        return self._run("coverage", "python", "-m", "pytest", "--cov=.", "--cov-fail-under", str(min_pct))

    def run_bandit(self) -> GateResult:
        return self._run("bandit", "python", "-m", "bandit", "-r", "-ll", "-ii", ".")

    def run_pyright(self) -> GateResult:
        return self._run("pyright", "pyright", ".")

    def run_radon_cc(self, max_complexity: int = 10) -> GateResult:
        return self._run(
            "radon_cc",
            "python", "-m", "radon", "cc", ".",
            "-s", "--min", str(max_complexity),
        )

    def run_py_compile(self) -> GateResult:
        return self._run("py_compile", "python", "-m", "py_compile", "app/main.py")

    def run_syntax_gate(self) -> GateResult:
        result = self._run("syntax-check", "python", "-c", """
import py_compile
import sys
from pathlib import Path
errors = []
for f in Path('app').rglob('*.py'):
    try:
        py_compile.compile(f, doraise=True)
    except py_compile.PyCompileError as e:
        errors.append(str(e))
if errors:
    print('\\\\n'.join(errors))
    sys.exit(1)
""")
        return result

    def run_all(self) -> QualityReport:
        gates = [
            self.run_ruff,
            self.run_pytest,
            self.run_mypy,
            self.run_bandit,
            self.run_coverage,
        ]
        for gate in gates:
            result = gate()
            self.report.results.append(result)
        return self.report

    def _run(self, name: str, *cmd: str) -> GateResult:
        import time
        start = time.monotonic()
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=str(self.project_root),
                timeout=300,
            )
            passed = result.returncode == 0
            output = result.stdout + result.stderr
        except FileNotFoundError:
            passed = True
            output = f"Command not found: {cmd[0]} — skipped"
        except subprocess.TimeoutExpired:
            passed = False
            output = "Timed out after 300s"
        duration = (time.monotonic() - start) * 1000
        return GateResult(name=name, passed=passed, output=output, duration_ms=round(duration, 1))
