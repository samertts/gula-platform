from __future__ import annotations

import ast
import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path

from . import DimensionEvaluator, DimensionResult


class TestCoverageEvaluator(DimensionEvaluator):
    TARGET_LINE_COVERAGE = 80.0
    TARGET_BRANCH_COVERAGE = 70.0

    def evaluate(self, module_path: str | None = None) -> DimensionResult:
        target = Path(module_path) if module_path else self.project_root

        line_coverage = self._get_line_coverage(target)
        self._add_evidence(
            "line_coverage_pct",
            value=line_coverage,
            source="Coverage XML / pytest-cov",
            passed=line_coverage >= self.TARGET_LINE_COVERAGE if line_coverage >= 0 else True,
        )
        if 0 <= line_coverage < self.TARGET_LINE_COVERAGE:
            self._add_remediation(
                f"Increase line coverage from {line_coverage}% to {self.TARGET_LINE_COVERAGE}%",
                severity="high",
                effort="8h",
            )

        branch_coverage = self._get_branch_coverage(target)
        self._add_evidence(
            "branch_coverage_pct",
            value=branch_coverage,
            source="Coverage XML / pytest-cov",
            passed=branch_coverage >= self.TARGET_BRANCH_COVERAGE if branch_coverage >= 0 else True,
        )
        if 0 <= branch_coverage < self.TARGET_BRANCH_COVERAGE:
            self._add_remediation(
                f"Increase branch coverage from {branch_coverage}% to {self.TARGET_BRANCH_COVERAGE}%",
                severity="high",
                effort="8h",
            )

        test_count, test_files = self._count_tests(target)
        self._add_evidence(
            "test_count",
            value=test_count,
            source="Test file scan",
            passed=test_count > 10,
        )
        self._add_evidence(
            "test_files",
            value=test_files,
            source="Test file scan",
            passed=test_files > 3,
        )
        if test_count <= 10:
            self._add_remediation(
                f"Write more tests (found {test_count}, minimum 10 recommended)",
                severity="medium",
                effort="6h",
            )

        source_count = self._count_source_files(target)
        test_to_source_ratio = round(test_files / max(source_count, 1), 2)
        self._add_evidence(
            "test_to_source_ratio",
            value=test_to_source_ratio,
            source="File count",
            passed=test_to_source_ratio >= 0.5,
        )
        if test_to_source_ratio < 0.5:
            self._add_remediation(
                f"Improve test-to-source ratio ({test_to_source_ratio}, target >= 0.5)",
                severity="medium",
                effort="4h",
            )

        property_tests = self._count_property_tests(target)
        self._add_evidence(
            "property_based_tests",
            value=property_tests,
            source="AST scan",
            passed=property_tests > 0,
        )
        if not property_tests:
            self._add_remediation(
                "Add property-based tests using Hypothesis",
                severity="low",
                effort="4h",
            )

        integration_tests = self._count_integration_tests(target)
        self._add_evidence(
            "integration_tests",
            value=integration_tests,
            source="File name scan",
            passed=integration_tests > 2,
        )
        if integration_tests <= 2:
            self._add_remediation(
                "Add integration tests for critical paths",
                severity="medium",
                effort="6h",
            )

        score = 1.0
        if line_coverage >= 0 and line_coverage < self.TARGET_LINE_COVERAGE:
            score -= min((self.TARGET_LINE_COVERAGE - line_coverage) * 0.01, 0.3)
        if branch_coverage >= 0 and branch_coverage < self.TARGET_BRANCH_COVERAGE:
            score -= min((self.TARGET_BRANCH_COVERAGE - branch_coverage) * 0.01, 0.2)
        if test_count <= 10:
            score -= 0.1
        if test_to_source_ratio < 0.5:
            score -= 0.05
        if not property_tests:
            score -= 0.03
        if integration_tests <= 2:
            score -= 0.05

        return self._result(score)

    def _get_line_coverage(self, target: Path) -> float:
        xml_path = target / "coverage.xml" or target.parent / "coverage.xml"
        if xml_path.exists():
            try:
                tree = ET.parse(xml_path)
                root = tree.getroot()
                for package in root.iter("package"):
                    if "line-rate" in package.attrib:
                        return float(package.attrib["line-rate"]) * 100
            except Exception:
                pass
        try:
            result = subprocess.run(
                ["python", "-m", "coverage", "report", "--precision=1"],
                capture_output=True,
                text=True,
                cwd=str(target),
                timeout=30,
            )
            for line in result.stdout.splitlines():
                if "TOTAL" in line:
                    parts = line.split()
                    if len(parts) >= 4:
                        return float(parts[-1].replace("%", ""))
        except (FileNotFoundError, subprocess.TimeoutExpired, ValueError):
            pass
        return -1.0

    def _get_branch_coverage(self, target: Path) -> float:
        xml_path = target / "coverage.xml" or target.parent / "coverage.xml"
        if xml_path.exists():
            try:
                tree = ET.parse(xml_path)
                root = tree.getroot()
                for package in root.iter("package"):
                    if "branch-rate" in package.attrib:
                        return float(package.attrib["branch-rate"]) * 100
            except Exception:
                pass
        return -1.0

    def _count_tests(self, target: Path) -> tuple[int, int]:
        count = 0
        test_files = 0
        for py_file in target.rglob("test_*.py"):
            if "__pycache__" in py_file.parts:
                continue
            test_files += 1
            try:
                tree = ast.parse(py_file.read_text())
                for node in ast.walk(tree):
                    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        if node.name.startswith("test_"):
                            count += 1
            except SyntaxError:
                continue
        for py_file in target.rglob("*_test.py"):
            if "__pycache__" in py_file.parts:
                continue
            if py_file.name.startswith("test_"):
                continue
            test_files += 1
            try:
                tree = ast.parse(py_file.read_text())
                for node in ast.walk(tree):
                    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        if node.name.startswith("test_"):
                            count += 1
            except SyntaxError:
                continue
        return count, test_files

    def _count_source_files(self, target: Path) -> int:
        count = 0
        for py_file in target.rglob("*.py"):
            if "test" in py_file.parts or "__pycache__" in py_file.parts:
                continue
            count += 1
        return count

    def _count_property_tests(self, target: Path) -> int:
        count = 0
        for py_file in target.rglob("*.py"):
            if "__pycache__" in py_file.parts:
                continue
            try:
                content = py_file.read_text()
                if "hypothesis" in content.lower() or "given(" in content or "@given" in content:
                    count += 1
            except Exception:
                continue
        return count

    def _count_integration_tests(self, target: Path) -> int:
        count = 0
        for py_file in target.rglob("*.py"):
            if "__pycache__" in py_file.parts:
                continue
            if "integration" in py_file.name.lower() or "e2e" in py_file.name.lower():
                try:
                    tree = ast.parse(py_file.read_text())
                    for node in ast.walk(tree):
                        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                            if node.name.startswith("test_"):
                                count += 1
                except SyntaxError:
                    continue
        return count
