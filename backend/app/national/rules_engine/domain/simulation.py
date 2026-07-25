from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from app._compat import UTC
from app.national.rules_engine.domain.entities import (
    RuleDefinition,
    RuleEvaluationContext,
)
from app.national.rules_engine.domain.expression_engine import ExpressionEngine


@dataclass
class SimulationReport:
    rule_id: str
    rule_name: str
    passed: bool
    outcome: str
    message: str
    execution_time_ms: float
    details: list[str] = field(default_factory=list)
    triggered_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def to_dict(self) -> dict[str, Any]:
        return {
            "rule_id": self.rule_id,
            "rule_name": self.rule_name,
            "passed": self.passed,
            "outcome": self.outcome,
            "message": self.message,
            "execution_time_ms": self.execution_time_ms,
            "details": self.details,
            "triggered_at": self.triggered_at.isoformat(),
        }


@dataclass
class BatchSimulationResult:
    total: int = 0
    passed: int = 0
    failed: int = 0
    blocked: int = 0
    warned: int = 0
    reports: list[SimulationReport] = field(default_factory=list)
    total_execution_time_ms: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "total": self.total,
            "passed": self.passed,
            "failed": self.failed,
            "blocked": self.blocked,
            "warned": self.warned,
            "reports": [r.to_dict() for r in self.reports],
            "total_execution_time_ms": self.total_execution_time_ms,
        }


class SimulationEngine:
    def __init__(self, expression_engine: ExpressionEngine | None = None) -> None:
        self.engine = expression_engine or ExpressionEngine()

    def run_simulation(
        self, rule: RuleDefinition, context: RuleEvaluationContext,
    ) -> SimulationReport:
        start = datetime.now(UTC)
        result = self.engine.evaluate_rule(rule, context.data)
        elapsed = (datetime.now(UTC) - start).total_seconds() * 1000.0
        passed = result.outcome.value in ("pass", "warning")
        details = [result.message] if result.message else []
        return SimulationReport(
            rule_id=rule.id,
            rule_name=rule.name,
            passed=passed,
            outcome=result.outcome.value,
            message=result.message,
            execution_time_ms=elapsed,
            details=details,
        )

    def batch_simulate(
        self,
        rules: list[RuleDefinition],
        contexts: list[RuleEvaluationContext],
    ) -> list[BatchSimulationResult]:
        results: list[BatchSimulationResult] = []
        for context in contexts:
            batch = BatchSimulationResult()
            for rule in rules:
                report = self.run_simulation(rule, context)
                batch.total += 1
                if report.outcome == "pass":
                    batch.passed += 1
                elif report.outcome in ("fail", "error"):
                    batch.failed += 1
                elif report.outcome == "block":
                    batch.blocked += 1
                elif report.outcome == "warning":
                    batch.warned += 1
                batch.reports.append(report)
                batch.total_execution_time_ms += report.execution_time_ms
            results.append(batch)
        return results

    def generate_report(self, result: BatchSimulationResult | SimulationReport) -> dict[str, Any]:
        if isinstance(result, SimulationReport):
            return result.to_dict()
        return result.to_dict()
