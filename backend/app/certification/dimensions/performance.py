from __future__ import annotations

from pathlib import Path

from app.engineering.performance.benchmark import PerformanceBenchmark

from . import DimensionEvaluator, DimensionResult


class PerformanceEvaluator(DimensionEvaluator):
    RESPONSE_TIME_THRESHOLD_MS = 500.0
    THROUGHPUT_MIN_RPS = 100

    def evaluate(self, module_path: str | None = None) -> DimensionResult:
        target = Path(module_path) if module_path else self.project_root
        benchmark = PerformanceBenchmark(target)

        startup = benchmark.measure_startup_time()
        self._add_evidence(
            "startup_time_ms",
            value=startup.value,
            source="PerformanceBenchmark",
            passed=startup.passed if startup.passed is not None else True,
        )
        if startup.value > self.RESPONSE_TIME_THRESHOLD_MS and startup.value > 0:
            self._add_remediation(
                f"Reduce startup time ({startup.value}ms) below {self.RESPONSE_TIME_THRESHOLD_MS}ms",
                severity="medium",
                effort="4h",
            )

        import_time = benchmark.measure_import_time("app")
        self._add_evidence(
            "import_time_ms",
            value=import_time.value,
            source="PerformanceBenchmark",
            passed=import_time.passed if import_time.passed is not None else True,
        )
        if import_time.value > 500 and import_time.value > 0:
            self._add_remediation(
                f"Reduce import time ({import_time.value}ms) — consider lazy imports",
                severity="medium",
                effort="2h",
            )

        connection_pooling = self._check_connection_pooling(target)
        self._add_evidence(
            "connection_pooling",
            value=connection_pooling,
            source="AST scan",
            passed=connection_pooling,
        )
        if not connection_pooling:
            self._add_remediation(
                "Use SQLAlchemy connection pooling instead of per-request connections",
                severity="high",
                effort="4h",
            )

        caching = self._check_caching(target)
        self._add_evidence(
            "caching_usage",
            value=caching,
            source="AST scan",
            passed=caching,
        )
        if not caching:
            self._add_remediation(
                "Add Redis caching layer for frequently accessed data",
                severity="medium",
                effort="6h",
            )

        async_patterns = self._check_async_patterns(target)
        self._add_evidence(
            "async_endpoints",
            value=async_patterns,
            source="AST scan",
            passed=async_patterns,
        )
        if not async_patterns:
            self._add_remediation(
                "Use async/await for I/O-bound endpoints (FastAPI native)",
                severity="low",
                effort="3h",
            )

        n_plus_one = self._detect_n_plus_one(target)
        self._add_evidence(
            "n_plus_one_queries",
            value=n_plus_one,
            source="AST scan",
            passed=n_plus_one == 0,
        )
        if n_plus_one:
            self._add_remediation(
                f"Fix {n_plus_one} N+1 query patterns — use joinedload/subqueryload",
                severity="high",
                effort=str(n_plus_one) + "h",
            )

        score = 1.0
        if startup.value > self.RESPONSE_TIME_THRESHOLD_MS and startup.value > 0:
            score -= 0.1
        if import_time.value > 500 and import_time.value > 0:
            score -= 0.05
        if not connection_pooling:
            score -= 0.15
        if not caching:
            score -= 0.1
        if not async_patterns:
            score -= 0.05
        score -= n_plus_one * 0.03

        return self._result(score)

    def _check_connection_pooling(self, target: Path) -> bool:
        for py_file in target.rglob("*.py"):
            try:
                content = py_file.read_text()
                if "create_engine" in content and "pool_size" in content:
                    return True
            except Exception:
                continue
        return False

    def _check_caching(self, target: Path) -> bool:
        for py_file in target.rglob("*.py"):
            try:
                content = py_file.read_text()
                if "redis" in content.lower() or "cache" in content.lower():
                    return True
            except Exception:
                continue
        return False

    def _check_async_patterns(self, target: Path) -> bool:
        count = 0
        for py_file in target.rglob("*.py"):
            try:
                content = py_file.read_text()
                if "async def" in content:
                    count += 1
            except Exception:
                continue
        return count >= 3

    def _detect_n_plus_one(self, target: Path) -> int:
        count = 0
        for py_file in target.rglob("*.py"):
            try:
                content = py_file.read_text()
                if "for" in content and "query" in content.lower():
                    import ast
                    try:
                        tree = ast.parse(content)
                        for node in ast.walk(tree):
                            if isinstance(node, ast.For):
                                for child in ast.walk(node):
                                    if isinstance(child, ast.Call) and hasattr(child.func, "attr"):
                                        if child.func.attr in ("query", "get", "all"):
                                            count += 1
                    except SyntaxError:
                        continue
            except Exception:
                continue
        return count
