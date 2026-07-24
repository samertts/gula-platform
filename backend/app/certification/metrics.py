from __future__ import annotations

import ast
import statistics
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path

from .enums import MetricCategory


@dataclass
class MetricResult:
    name: str
    value: float | str | bool
    category: MetricCategory
    unit: str = ""
    threshold: float | None = None
    passed: bool | None = None
    details: dict | None = None


class BaseMetricCollector(ABC):
    def __init__(self, project_root: Path | str):
        self.project_root = Path(project_root)

    @abstractmethod
    def collect(self) -> MetricResult:
        ...


class CodeCoverage(BaseMetricCollector):
    def collect(self) -> MetricResult:
        total_lines = 0
        covered_lines = 0
        for py_file in self.project_root.rglob("*.py"):
            if "test" in py_file.parts or "__pycache__" in py_file.parts:
                continue
            try:
                tree = ast.parse(py_file.read_text())
                for node in ast.walk(tree):
                    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        total_lines += 1
            except SyntaxError:
                continue
        for _tgz_file in self.project_root.rglob(".coverage"):
            total_lines += 1
            covered_lines += 1

        test_count = 0
        for py_file in self.project_root.rglob("test_*.py"):
            try:
                tree = ast.parse(py_file.read_text())
                for node in ast.walk(tree):
                    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name.startswith("test_"):
                        test_count += 1
            except SyntaxError:
                continue

        coverage_pct = round(min((test_count / max(total_lines, 1)) * 100, 100), 1)
        return MetricResult(
            name="code_coverage",
            value=coverage_pct,
            category=MetricCategory.COVERAGE,
            unit="%",
            threshold=80.0,
            passed=coverage_pct >= 80.0,
        )


class CyclomaticComplexity(BaseMetricCollector):
    def collect(self) -> MetricResult:
        complexities = []
        for py_file in self.project_root.rglob("*.py"):
            if "test" in py_file.parts or "__pycache__" in py_file.parts:
                continue
            try:
                tree = ast.parse(py_file.read_text())
                for node in ast.walk(tree):
                    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        cc = 1
                        for child in ast.walk(node):
                            if isinstance(child, (ast.If, ast.While, ast.For, ast.AsyncFor)):
                                cc += 1
                            elif isinstance(child, ast.BoolOp):
                                cc += len(child.values) - 1
                            elif isinstance(child, (ast.ExceptHandler, ast.With, ast.AsyncWith)):
                                cc += 1
                        complexities.append(cc)
            except SyntaxError:
                continue

        avg = round(statistics.mean(complexities), 2) if complexities else 0.0
        high = sum(1 for c in complexities if c > 10)
        return MetricResult(
            name="cyclomatic_complexity",
            value=avg,
            category=MetricCategory.COMPLEXITY,
            unit="avg",
            threshold=10.0,
            passed=avg <= 10.0,
            details={"high_complexity_count": high, "total_functions": len(complexities)},
        )


class MaintainabilityIndex(BaseMetricCollector):
    def collect(self) -> MetricResult:
        mi_values = []
        for py_file in self.project_root.rglob("*.py"):
            if "test" in py_file.parts or "__pycache__" in py_file.parts:
                continue
            try:
                content = py_file.read_text()
                lines = len(content.splitlines())
                tree = ast.parse(content)
                total_ops = 0
                total_operands = 0
                for node in ast.walk(tree):
                    if isinstance(node, ast.operator):
                        total_ops += 1
                    elif isinstance(node, ast.Name):
                        total_operands += 1
                vol = max(total_ops + total_operands, 1)
                cc_total = 0
                func_count = 0
                for node in ast.walk(tree):
                    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        func_count += 1
                        cc = 1
                        for child in ast.walk(node):
                            if isinstance(child, (ast.If, ast.While, ast.For)):
                                cc += 1
                        cc_total += cc
                avg_cc = cc_total / max(func_count, 1)
                import math
                mi = max(0, 171 - 5.2 * math.log(vol) - 0.23 * avg_cc - 16.2 * math.log(max(lines / max(func_count, 1), 1)))
                mi_values.append(min(mi, 100))
            except (SyntaxError, ValueError):
                continue

        avg_mi = round(statistics.mean(mi_values), 2) if mi_values else 100.0
        return MetricResult(
            name="maintainability_index",
            value=avg_mi,
            category=MetricCategory.MAINTAINABILITY,
            unit="score",
            threshold=65.0,
            passed=avg_mi >= 65.0,
        )


class TechnicalDebt(BaseMetricCollector):
    def collect(self) -> MetricResult:
        debt_minutes = 0
        issues_found = 0
        for py_file in self.project_root.rglob("*.py"):
            if "test" in py_file.parts or "__pycache__" in py_file.parts:
                continue
            try:
                tree = ast.parse(py_file.read_text())
                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef):
                        if node.end_lineno and node.lineno:
                            length = node.end_lineno - node.lineno
                            if length > 50:
                                debt_minutes += length
                                issues_found += 1
            except SyntaxError:
                continue

        duplicate_blocks = 0
        seen_hashes = set()
        for py_file in self.project_root.rglob("*.py"):
            if "test" in py_file.parts or "__pycache__" in py_file.parts:
                continue
            try:
                content = py_file.read_text()
                h = hash(content[:200])
                if h in seen_hashes:
                    duplicate_blocks += 1
                seen_hashes.add(h)
            except Exception:
                continue

        debt_hours = round(debt_minutes / 60, 1)
        return MetricResult(
            name="technical_debt",
            value=debt_hours,
            category=MetricCategory.TECH_DEBT,
            unit="hours",
            threshold=40.0,
            passed=debt_hours <= 40.0,
            details={"long_functions": issues_found, "duplicate_blocks": duplicate_blocks},
        )


class ArchitectureViolations(BaseMetricCollector):
    def collect(self) -> MetricResult:
        violations = 0
        for py_file in self.project_root.rglob("*.py"):
            if "test" in py_file.parts or "__pycache__" in py_file.parts:
                continue
            try:
                content = py_file.read_text()
                tree = ast.parse(content)
                for node in ast.walk(tree):
                    if isinstance(node, ast.ImportFrom) and node.module:
                        if (node.module.startswith("app.domain") and "domain" not in str(py_file)) or (node.module.startswith("app.infrastructure") and "domain" in str(py_file)):
                            violations += 1
            except SyntaxError:
                continue

        return MetricResult(
            name="architecture_violations",
            value=violations,
            category=MetricCategory.ARCHITECTURE,
            unit="violations",
            threshold=10,
            passed=violations <= 10,
        )


class SecurityScore(BaseMetricCollector):
    def collect(self) -> MetricResult:
        vulnerabilities = 0
        secrets_found = 0
        for py_file in self.project_root.rglob("*.py"):
            if "test" in py_file.parts or "__pycache__" in py_file.parts:
                continue
            try:
                content = py_file.read_text()
                patterns = ["sk-", "SECRET_KEY", "ENCRYPTION_KEY", "ghp_", "-----BEGIN"]
                for pattern in patterns:
                    if pattern in content:
                        secrets_found += 1
                if "eval(" in content or "exec(" in content:
                    vulnerabilities += 1
            except Exception:
                continue

        score = max(0, 100 - vulnerabilities * 10 - secrets_found * 15)
        details = {"vulnerabilities": vulnerabilities, "secrets_exposed": secrets_found}
        return MetricResult(
            name="security_score",
            value=score,
            category=MetricCategory.SECURITY,
            unit="score",
            threshold=80.0,
            passed=score >= 80.0,
            details=details,
        )


class PerformanceScore(BaseMetricCollector):
    def collect(self) -> MetricResult:
        async_defs = 0
        sync_defs = 0
        n_plus_one = 0

        for py_file in self.project_root.rglob("*.py"):
            if "test" in py_file.parts or "__pycache__" in py_file.parts:
                continue
            try:
                tree = ast.parse(py_file.read_text())
                for node in ast.walk(tree):
                    if isinstance(node, ast.AsyncFunctionDef):
                        async_defs += 1
                    elif isinstance(node, ast.FunctionDef):
                        sync_defs += 1
                    if isinstance(node, ast.For):
                        for child in ast.walk(node):
                            if isinstance(child, ast.Call) and hasattr(child.func, "attr"):
                                if child.func.attr in ("query", "get", "all"):
                                    n_plus_one += 1
            except SyntaxError:
                continue

        async_ratio = async_defs / max(async_defs + sync_defs, 1)
        score = round(min(100, async_ratio * 100 + 50 - n_plus_one * 5), 1)
        return MetricResult(
            name="performance_score",
            value=score,
            category=MetricCategory.PERFORMANCE,
            unit="score",
            threshold=70.0,
            passed=score >= 70.0,
            details={"async_ratio_pct": round(async_ratio * 100, 1), "n_plus_one_count": n_plus_one},
        )


class ReliabilityScore(BaseMetricCollector):
    def collect(self) -> MetricResult:
        retry_count = 0
        circuit_breaker = False
        health_checks = 0

        for py_file in self.project_root.rglob("*.py"):
            if "test" in py_file.parts or "__pycache__" in py_file.parts:
                continue
            try:
                content = py_file.read_text()
                if "retry" in content.lower() and "backoff" in content.lower():
                    retry_count += 1
                if "circuit_breaker" in content.lower() or "circuitbreaker" in content.lower():
                    circuit_breaker = True
                if "/health" in content:
                    health_checks += 1
            except Exception:
                continue

        score = 0
        if circuit_breaker:
            score += 30
        score += min(retry_count * 10, 30)
        score += min(health_checks * 10, 40)
        return MetricResult(
            name="reliability_score",
            value=score,
            category=MetricCategory.RELIABILITY,
            unit="score",
            threshold=70.0,
            passed=score >= 70.0,
            details={"retry_patterns": retry_count, "circuit_breaker": circuit_breaker, "health_endpoints": health_checks},
        )


class AvailabilityScore(BaseMetricCollector):
    def collect(self) -> MetricResult:
        graceful_shutdown = False
        concurrency_limit = False
        bulkhead = False

        for py_file in self.project_root.rglob("*.py"):
            if "test" in py_file.parts or "__pycache__" in py_file.parts:
                continue
            try:
                content = py_file.read_text()
                if "lifespan" in content and "shutdown" in content:
                    graceful_shutdown = True
                if "ConcurrencyLimit" in content or "MAX_CONCURRENT" in content:
                    concurrency_limit = True
                if "semaphore" in content.lower() or "bulkhead" in content.lower():
                    bulkhead = True
            except Exception:
                continue

        score = 0
        if graceful_shutdown:
            score += 35
        if concurrency_limit:
            score += 35
        if bulkhead:
            score += 30
        return MetricResult(
            name="availability_score",
            value=score,
            category=MetricCategory.AVAILABILITY,
            unit="score",
            threshold=60.0,
            passed=score >= 60.0,
            details={
                "graceful_shutdown": graceful_shutdown,
                "concurrency_limit": concurrency_limit,
                "bulkhead_pattern": bulkhead,
            },
        )


class ScalabilityScore(BaseMetricCollector):
    def collect(self) -> MetricResult:
        stateless = True
        caching = False
        connection_pool = False

        for py_file in self.project_root.rglob("*.py"):
            if "test" in py_file.parts or "__pycache__" in py_file.parts:
                continue
            try:
                content = py_file.read_text()
                if "redis" in content.lower() and ("cache" in content.lower() or "session" in content.lower()):
                    caching = True
                if "pool_size" in content or "PoolSize" in content or "max_overflow" in content:
                    connection_pool = True
            except Exception:
                continue

        score = 0
        if stateless:
            score += 30
        if caching:
            score += 35
        if connection_pool:
            score += 35
        return MetricResult(
            name="scalability_score",
            value=score,
            category=MetricCategory.SCALABILITY,
            unit="score",
            threshold=60.0,
            passed=score >= 60.0,
            details={
                "stateless_design": stateless,
                "caching": caching,
                "connection_pooling": connection_pool,
            },
        )


class DocumentationCoverage(BaseMetricCollector):
    def collect(self) -> MetricResult:
        total = 0
        documented = 0

        for py_file in self.project_root.rglob("*.py"):
            if "test" in py_file.parts or "__pycache__" in py_file.parts:
                continue
            try:
                tree = ast.parse(py_file.read_text())
                for node in ast.walk(tree):
                    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                        total += 1
                        if node.body and isinstance(node.body[0], ast.Expr):
                            if isinstance(node.body[0].value, ast.Constant) and isinstance(node.body[0].value.value, str):
                                documented += 1
            except SyntaxError:
                continue

        pct = round((documented / max(total, 1)) * 100, 1)
        return MetricResult(
            name="documentation_coverage",
            value=pct,
            category=MetricCategory.DOCUMENTATION,
            unit="%",
            threshold=30.0,
            passed=pct >= 30.0,
            details={"total_definitions": total, "documented": documented},
        )


class MetricsCollector:
    COLLECTORS: list[type[BaseMetricCollector]] = [
        CodeCoverage,
        CyclomaticComplexity,
        MaintainabilityIndex,
        TechnicalDebt,
        ArchitectureViolations,
        SecurityScore,
        PerformanceScore,
        ReliabilityScore,
        AvailabilityScore,
        ScalabilityScore,
        DocumentationCoverage,
    ]

    def __init__(self, project_root: Path | str | None = None):
        self.project_root = Path(project_root) if project_root else Path.cwd()

    def collect_all(self) -> list[MetricResult]:
        results = []
        for collector_cls in self.COLLECTORS:
            collector = collector_cls(self.project_root)
            try:
                results.append(collector.collect())
            except Exception:
                results.append(
                    MetricResult(
                        name=collector_cls.__name__,
                        value=0,
                        category=MetricCategory.MAINTAINABILITY,
                        passed=False,
                    ),
                )
        return results

    def collect_category(self, category: MetricCategory) -> list[MetricResult]:
        return [
            r for r in self.collect_all() if r.category == category
        ]

    def collect_one(self, name: str) -> MetricResult | None:
        for r in self.collect_all():
            if r.name.lower() == name.lower():
                return r
        return None
