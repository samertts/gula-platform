from __future__ import annotations

from pathlib import Path

from . import DimensionEvaluator, DimensionResult


class ReliabilityEvaluator(DimensionEvaluator):
    def evaluate(self, module_path: str | None = None) -> DimensionResult:
        target = Path(module_path) if module_path else self.project_root

        circuit_breaker = self._check_circuit_breaker(target)
        self._add_evidence(
            "circuit_breaker",
            value=circuit_breaker,
            source="AST scan",
            passed=circuit_breaker,
        )
        if not circuit_breaker:
            self._add_remediation(
                "Implement circuit breaker pattern for external service calls",
                severity="high",
                effort="6h",
            )

        retry_pattern = self._check_retry_pattern(target)
        self._add_evidence(
            "retry_pattern",
            value=retry_pattern,
            source="AST scan",
            passed=retry_pattern,
        )
        if not retry_pattern:
            self._add_remediation(
                "Add retry with exponential backoff for transient failures",
                severity="medium",
                effort="3h",
            )

        graceful_shutdown = self._check_graceful_shutdown(target)
        self._add_evidence(
            "graceful_shutdown",
            value=graceful_shutdown,
            source="AST scan",
            passed=graceful_shutdown,
        )
        if not graceful_shutdown:
            self._add_remediation(
                "Implement graceful shutdown handling (SIGTERM, connection drain)",
                severity="medium",
                effort="4h",
            )

        health_checks = self._check_health_checks(target)
        self._add_evidence(
            "health_check_endpoints",
            value=health_checks,
            source="AST scan",
            passed=health_checks,
        )
        if not health_checks:
            self._add_remediation(
                "Add /health, /health/ready, /health/live endpoints",
                severity="high",
                effort="2h",
            )

        timeout_config = self._check_timeout_config(target)
        self._add_evidence(
            "timeout_configuration",
            value=timeout_config,
            source="AST scan",
            passed=timeout_config,
        )
        if not timeout_config:
            self._add_remediation(
                "Configure timeouts for all external HTTP calls and DB queries",
                severity="medium",
                effort="2h",
            )

        error_handler = self._check_global_error_handler(target)
        self._add_evidence(
            "global_error_handler",
            value=error_handler,
            source="AST scan",
            passed=error_handler,
        )
        if not error_handler:
            self._add_remediation(
                "Add global exception handler for unhandled errors",
                severity="medium",
                effort="2h",
            )

        rate_limiting = self._check_rate_limiting(target)
        self._add_evidence(
            "rate_limiting",
            value=rate_limiting,
            source="AST scan",
            passed=rate_limiting,
        )
        if not rate_limiting:
            self._add_remediation(
                "Add rate limiting middleware to prevent abuse",
                severity="medium",
                effort="3h",
            )

        bulkhead = self._check_bulkhead(target)
        self._add_evidence(
            "bulkhead_pattern",
            value=bulkhead,
            source="AST scan",
            passed=bulkhead,
        )
        if not bulkhead:
            self._add_remediation(
                "Implement bulkhead/isolation pattern for critical vs non-critical paths",
                severity="low",
                effort="4h",
            )

        score = 1.0
        checks = [
            (circuit_breaker, 0.15),
            (retry_pattern, 0.1),
            (graceful_shutdown, 0.1),
            (health_checks, 0.15),
            (timeout_config, 0.1),
            (error_handler, 0.1),
            (rate_limiting, 0.1),
            (bulkhead, 0.05),
        ]
        for passed, penalty in checks:
            if not passed:
                score -= penalty

        return self._result(score)

    def _check_circuit_breaker(self, target: Path) -> bool:
        for py_file in target.rglob("*.py"):
            try:
                content = py_file.read_text()
                if "circuit_breaker" in content.lower() or "circuitbreaker" in content.lower():
                    return True
            except Exception:
                continue
        return False

    def _check_retry_pattern(self, target: Path) -> bool:
        for py_file in target.rglob("*.py"):
            try:
                content = py_file.read_text()
                if "retry" in content.lower() and (
                    "backoff" in content.lower()
                    or "attempt" in content.lower()
                    or "tenacity" in content.lower()
                ):
                    return True
            except Exception:
                continue
        return False

    def _check_graceful_shutdown(self, target: Path) -> bool:
        for py_file in target.rglob("*.py"):
            try:
                content = py_file.read_text()
                if "lifespan" in content or "shutdown" in content.lower() or "SIGTERM" in content:
                    return True
            except Exception:
                continue
        return False

    def _check_health_checks(self, target: Path) -> int:
        count = 0
        for py_file in target.rglob("*.py"):
            try:
                content = py_file.read_text()
                if "/health" in content:
                    count += 1
            except Exception:
                continue
        return count

    def _check_timeout_config(self, target: Path) -> bool:
        for py_file in target.rglob("*.py"):
            try:
                content = py_file.read_text()
                if "timeout" in content.lower() and (
                    "set" in content.lower() or "config" in content.lower()
                ):
                    return True
            except Exception:
                continue
        return False

    def _check_global_error_handler(self, target: Path) -> bool:
        for py_file in target.rglob("*.py"):
            try:
                content = py_file.read_text()
                if (
                    "exception_handler" in content
                    or "ExceptionHandlerMiddleware" in content
                    or "@app.exception_handler" in content
                ):
                    return True
            except Exception:
                continue
        return False

    def _check_rate_limiting(self, target: Path) -> bool:
        for py_file in target.rglob("*.py"):
            try:
                content = py_file.read_text()
                if (
                    "rate_limit" in content.lower()
                    or "RateLimiter" in content
                    or "throttle" in content.lower()
                ):
                    return True
            except Exception:
                continue
        return False

    def _check_bulkhead(self, target: Path) -> bool:
        for py_file in target.rglob("*.py"):
            try:
                content = py_file.read_text()
                if (
                    "bulkhead" in content.lower()
                    or "semaphore" in content.lower()
                    or "ConcurrencyLimit" in content
                ):
                    return True
            except Exception:
                continue
        return False
