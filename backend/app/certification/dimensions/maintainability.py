from __future__ import annotations

import ast
import math
import statistics
from pathlib import Path

from app.engineering.intelligence.duplicate_detector import DuplicateDetector

from . import DimensionEvaluator, DimensionResult


class MaintainabilityEvaluator(DimensionEvaluator):
    def evaluate(self, module_path: str | None = None) -> DimensionResult:
        target = Path(module_path) if module_path else self.project_root

        complexity = self._measure_cyclomatic_complexity(target)
        avg_complexity = statistics.mean(complexity) if complexity else 0
        high_complexity = sum(1 for c in complexity if c > 10)
        self._add_evidence(
            "avg_cyclomatic_complexity",
            value=round(avg_complexity, 2),
            source="Radon-style AST analysis",
            passed=avg_complexity <= 10,
        )
        self._add_evidence(
            "high_complexity_functions",
            value=high_complexity,
            source="AST scan",
            passed=high_complexity == 0,
        )
        if high_complexity:
            self._add_remediation(
                f"Refactor {high_complexity} functions with cyclomatic complexity > 10",
                severity="medium",
                effort=str(high_complexity * 2) + "h",
            )

        maintainability_index = self._calculate_maintainability_index(target)
        self._add_evidence(
            "maintainability_index",
            value=round(maintainability_index, 2),
            source="MI calculation",
            passed=maintainability_index >= 65,
        )
        if maintainability_index < 65:
            self._add_remediation(
                f"Improve maintainability index ({round(maintainability_index, 1)} vs target 65)",
                severity="medium",
                effort="8h",
            )

        detector = DuplicateDetector(target)
        duplicates = detector.detect()
        total_duplicate_lines = sum(d.lines_of_code for d in duplicates)
        self._add_evidence(
            "duplicate_blocks",
            value=len(duplicates),
            source="DuplicateDetector",
            passed=len(duplicates) <= 5,
        )
        self._add_evidence(
            "duplicate_lines",
            value=total_duplicate_lines,
            source="DuplicateDetector",
            passed=total_duplicate_lines <= 50,
        )
        if len(duplicates) > 5:
            self._add_remediation(
                f"Eliminate {len(duplicates)} duplicate code blocks",
                severity="medium",
                effort=str(len(duplicates)) + "h",
            )

        function_length = self._measure_function_length(target)
        avg_length = statistics.mean(function_length) if function_length else 0
        long_functions = sum(1 for length in function_length if length > 50)
        self._add_evidence(
            "avg_function_length",
            value=round(avg_length, 1),
            source="AST scan",
            passed=avg_length <= 30,
        )
        self._add_evidence(
            "long_functions",
            value=long_functions,
            source="AST scan",
            passed=long_functions == 0,
        )
        if long_functions:
            self._add_remediation(
                f"Break down {long_functions} functions exceeding 50 lines",
                severity="low",
                effort=str(long_functions) + "h",
            )

        total_lines, total_files = self._count_lines(target)
        self._add_evidence(
            "total_lines_of_code",
            value=total_lines,
            source="Line count",
        )
        self._add_evidence(
            "total_python_files",
            value=total_files,
            source="File count",
        )

        comment_ratio = self._measure_comment_ratio(target)
        self._add_evidence(
            "comment_ratio_pct",
            value=round(comment_ratio, 1),
            source="AST scan",
            passed=0.05 <= comment_ratio <= 0.30,
        )
        if comment_ratio < 0.05:
            self._add_remediation(
                f"Add more code comments (current ratio {comment_ratio * 100:.1f}%, target 5-30%)",
                severity="low",
                effort="4h",
            )
        if comment_ratio > 0.30:
            self._add_remediation(
                "Reduce excessive comments — prefer self-documenting code",
                severity="low",
                effort="2h",
            )

        score = 1.0
        if avg_complexity > 10:
            score -= min((avg_complexity - 10) * 0.02, 0.2)
        score -= high_complexity * 0.02
        if maintainability_index < 65:
            score -= min((65 - maintainability_index) * 0.005, 0.15)
        score -= len(duplicates) * 0.02
        score -= long_functions * 0.01
        if comment_ratio < 0.05 or comment_ratio > 0.30:
            score -= 0.05

        return self._result(score)

    def _measure_cyclomatic_complexity(self, target: Path) -> list[int]:
        complexities = []
        for py_file in target.rglob("*.py"):
            if "test" in py_file.parts or "__pycache__" in py_file.parts:
                continue
            try:
                tree = ast.parse(py_file.read_text())
                for node in ast.walk(tree):
                    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        complexity = 1
                        for child in ast.walk(node):
                            if isinstance(child, (ast.If, ast.While, ast.For, ast.AsyncFor)):
                                complexity += 1
                            elif isinstance(child, ast.BoolOp):
                                complexity += len(child.values) - 1
                            elif isinstance(child, (ast.ExceptHandler, ast.With, ast.AsyncWith)):
                                complexity += 1
                        complexities.append(complexity)
            except SyntaxError:
                continue
        return complexities

    def _calculate_maintainability_index(self, target: Path) -> float:
        total_lines, total_files = self._count_lines(target)
        if total_files == 0:
            return 100.0
        complexities = self._measure_cyclomatic_complexity(target)
        avg_cc = statistics.mean(complexities) if complexities else 1
        halstead_volume = self._estimate_halstead_volume(target)
        mi = max(
            0,
            171
            - 5.2 * math.log(max(halstead_volume, 1))
            - 0.23 * avg_cc * 10
            - 16.2 * math.log(max(total_lines / max(total_files, 1), 1)),
        )
        return min(mi, 100)

    def _measure_function_length(self, target: Path) -> list[int]:
        lengths = []
        for py_file in target.rglob("*.py"):
            if "test" in py_file.parts or "__pycache__" in py_file.parts:
                continue
            try:
                tree = ast.parse(py_file.read_text())
                for node in ast.walk(tree):
                    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.end_lineno and node.lineno:
                        lengths.append(node.end_lineno - node.lineno + 1)
            except SyntaxError:
                continue
        return lengths

    def _count_lines(self, target: Path) -> tuple[int, int]:
        total = 0
        files = 0
        for py_file in target.rglob("*.py"):
            if "test" in py_file.parts or "__pycache__" in py_file.parts:
                continue
            try:
                lines = len(py_file.read_text().splitlines())
                total += lines
                files += 1
            except Exception:
                continue
        return total, files

    def _measure_comment_ratio(self, target: Path) -> float:
        comments = 0
        total = 0
        for py_file in target.rglob("*.py"):
            if "test" in py_file.parts or "__pycache__" in py_file.parts:
                continue
            try:
                tree = ast.parse(py_file.read_text())
                if hasattr(tree, "body"):
                    for node in ast.walk(tree):
                        if (
                            isinstance(node, ast.Expr)
                            and isinstance(node.value, ast.Constant)
                            and isinstance(node.value.value, str)
                        ):
                            comments += 1
                total += 1
            except SyntaxError:
                continue
        total = max(total, 1)

        raw_comments = 0
        raw_lines = 0
        for py_file in target.rglob("*.py"):
            if "test" in py_file.parts or "__pycache__" in py_file.parts:
                continue
            try:
                content = py_file.read_text()
                lines = content.splitlines()
                raw_lines += len(lines)
                for line in lines:
                    stripped = line.strip()
                    if stripped.startswith("#"):
                        raw_comments += 1
            except Exception:
                continue
        raw_lines = max(raw_lines, 1)
        return raw_comments / raw_lines

    def _estimate_halstead_volume(self, target: Path) -> float:
        operators = set()
        operands = set()
        for py_file in target.rglob("*.py"):
            if "test" in py_file.parts or "__pycache__" in py_file.parts:
                continue
            try:
                tree = ast.parse(py_file.read_text())
                for node in ast.walk(tree):
                    if isinstance(node, ast.operator):
                        operators.add(type(node).__name__)
                    elif isinstance(node, ast.Name):
                        operands.add(node.id)
            except SyntaxError:
                continue
        n1 = max(len(operators), 1)
        n2 = max(len(operands), 1)
        return n1 + n2
