from __future__ import annotations

import logging
import uuid
from datetime import datetime
from typing import Any

from app._compat import UTC
from app.kernel.event_bus.bus import EventBus
from app.kernel.event_bus.events import Event
from app.notifications.service import NotificationService
from app.national.rules_engine.domain.entities import (
    RuleDefinition,
    RuleEvaluationContext,
    RuleEvaluationResult,
)
from app.national.rules_engine.domain.enums import RuleOutcome, RuleSeverity, RuleStatus, RuleTrigger
from app.national.rules_engine.domain.events import (
    RuleActivatedEvent,
    RuleCreatedEvent,
    RuleDeactivatedEvent,
    RuleEvaluatedEvent,
    RuleSimulationEvent,
    RuleUpdatedEvent,
    RuleViolationEvent,
)
from app.national.rules_engine.domain.expression_engine import ExpressionEngine
from app.national.rules_engine.domain.repository import RuleRepository
from app.national.rules_engine.domain.simulation import SimulationEngine
from app.national.rules_engine.exceptions import (
    RuleConflictError,
    RuleEvaluationError,
    RuleNotFoundError,
    RuleValidationError,
    RuleVersionError,
)

logger = logging.getLogger("gula.national.rules_engine")


class RulesEngineService:

    def __init__(
        self,
        repository: RuleRepository,
        event_bus: EventBus,
        notification_service: NotificationService | None = None,
        expression_engine: ExpressionEngine | None = None,
        simulation_engine: SimulationEngine | None = None,
    ) -> None:
        self.repository = repository
        self.event_bus = event_bus
        self.notification_service = notification_service
        self.expression_engine = expression_engine or ExpressionEngine()
        self.simulation_engine = simulation_engine or SimulationEngine(self.expression_engine)
        self._cache: dict[str, list[RuleDefinition]] = {}
        self._cache_timestamp: datetime | None = None
        self._cache_ttl_seconds = 300

    async def register_rule(self, rule: RuleDefinition) -> RuleDefinition:
        rule.id = rule.id or str(uuid.uuid4())
        rule.version = 1
        rule.status = RuleStatus.DRAFT
        errors = await self._validate_rule(rule)
        if errors:
            raise RuleValidationError(rule.id, "; ".join(errors))
        saved = await self.repository.save(rule)
        self._publish_event(RuleCreatedEvent(
            rule_id=saved.id,
            rule_name=saved.name,
            category=saved.category,
            rule_version=saved.version,
            aggregate_id=saved.id,
            payload={"name": saved.name, "category": saved.category.value},
        ))
        self._invalidate_cache()
        return saved

    async def activate_rule(self, rule_id: str) -> RuleDefinition:
        rule = await self._get_rule_or_raise(rule_id)
        if rule.status != RuleStatus.DRAFT and rule.status != RuleStatus.INACTIVE:
            raise RuleValidationError(rule_id, f"Cannot activate rule in status {rule.status.value}")
        rule.status = RuleStatus.ACTIVE
        updated = await self.repository.save(rule)
        self._publish_event(RuleActivatedEvent(
            rule_id=updated.id,
            rule_name=updated.name,
            aggregate_id=updated.id,
            payload={"name": updated.name},
        ))
        self._invalidate_cache()
        return updated

    async def deactivate_rule(self, rule_id: str) -> RuleDefinition:
        rule = await self._get_rule_or_raise(rule_id)
        if rule.status != RuleStatus.ACTIVE:
            raise RuleValidationError(rule_id, f"Cannot deactivate rule in status {rule.status.value}")
        rule.status = RuleStatus.INACTIVE
        updated = await self.repository.save(rule)
        self._publish_event(RuleDeactivatedEvent(
            rule_id=updated.id,
            rule_name=updated.name,
            aggregate_id=updated.id,
            payload={"name": updated.name},
        ))
        self._invalidate_cache()
        return updated

    async def evaluate(
        self,
        context: RuleEvaluationContext,
        execution_mode: str = "synchronous",
    ) -> list[RuleEvaluationResult]:
        rules = await self._get_active_rules_for_context(context)
        if not rules:
            return []
        results: list[RuleEvaluationResult] = []
        for rule in sorted(rules, key=lambda r: r.priority, reverse=True):
            try:
                result = self.expression_engine.evaluate_rule(rule, context.data)
                results.append(result)
                self._publish_event(RuleEvaluatedEvent(
                    rule_id=rule.id,
                    context=context.data,
                    result={
                        "outcome": result.outcome.value,
                        "message": result.message,
                        "execution_time_ms": result.execution_time_ms,
                    },
                    trigger=context.trigger.value,
                    aggregate_id=rule.id,
                    payload={"outcome": result.outcome.value},
                ))
                if result.outcome in (
                    RuleOutcome.FAIL, RuleOutcome.ERROR, RuleOutcome.BLOCK,
                    RuleOutcome.FLAG, RuleOutcome.ESCALATE,
                ):
                    self._publish_event(RuleViolationEvent(
                        rule_id=rule.id,
                        rule_name=rule.name,
                        severity=rule.severity.value,
                        resource_type=context.resource_type,
                        resource_id=context.resource_id,
                        message=result.message,
                        context=context.data,
                        aggregate_id=rule.id,
                        payload={
                            "outcome": result.outcome.value,
                            "severity": rule.severity.value,
                        },
                    ))
                    await self._send_violation_notification(rule, result, context)
                if result.outcome == RuleOutcome.BLOCK and execution_mode == "synchronous":
                    break
            except Exception as exc:
                logger.error("Rule evaluation failed for %s: %s", rule.id, exc)
                results.append(RuleEvaluationResult(
                    rule_id=rule.id,
                    rule_name=rule.name,
                    outcome=RuleOutcome.ERROR,
                    severity=rule.severity,
                    message=f"Evaluation error: {exc}",
                ))
        return results

    async def simulate(
        self,
        rule: RuleDefinition,
        context: RuleEvaluationContext,
    ) -> dict[str, Any]:
        report = self.simulation_engine.run_simulation(rule, context)
        self._publish_event(RuleSimulationEvent(
            rule_id=rule.id,
            context=context.data,
            result=report.to_dict(),
            simulated=True,
            aggregate_id=rule.id,
            payload={"outcome": report.outcome},
        ))
        return report.to_dict()

    async def batch_simulate(
        self,
        rules: list[RuleDefinition],
        contexts: list[RuleEvaluationContext],
    ) -> list[dict[str, Any]]:
        results = self.simulation_engine.batch_simulate(rules, contexts)
        return [r.to_dict() for r in results]

    async def create_new_version(self, rule_id: str, updates: dict[str, Any]) -> RuleDefinition:
        rule = await self._get_rule_or_raise(rule_id)
        if rule.status == RuleStatus.ARCHIVED:
            raise RuleVersionError(rule_id, rule.version, -1)
        new_rule = RuleDefinition(
            id=str(uuid.uuid4()),
            name=updates.get("name", rule.name),
            description=updates.get("description", rule.description),
            category=updates.get("category", rule.category),
            severity=updates.get("severity", rule.severity),
            status=RuleStatus.DRAFT,
            conditions=updates.get("conditions", rule.conditions),
            actions=updates.get("actions", rule.actions),
            priority=updates.get("priority", rule.priority),
            version=rule.version + 1,
            tags=updates.get("tags", rule.tags),
            effective_from=updates.get("effective_from", rule.effective_from),
            effective_to=updates.get("effective_to", rule.effective_to),
            metadata=updates.get("metadata", rule.metadata),
        )
        errors = await self._validate_rule(new_rule)
        if errors:
            raise RuleValidationError(new_rule.id, "; ".join(errors))
        saved = await self.repository.save(new_rule)
        self._publish_event(RuleCreatedEvent(
            rule_id=saved.id,
            rule_name=saved.name,
            category=saved.category,
            rule_version=saved.version,
            aggregate_id=saved.id,
            payload={"name": saved.name, "version": saved.version, "source_rule_id": rule_id},
        ))
        self._invalidate_cache()
        return saved

    async def get_rule(self, rule_id: str) -> RuleDefinition:
        return await self._get_rule_or_raise(rule_id)

    async def list_rules(
        self,
        category: str | None = None,
        status: str | None = None,
        search: str | None = None,
        skip: int = 0,
        limit: int = 100,
    ) -> list[RuleDefinition]:
        filters: dict[str, Any] = {}
        if category:
            from app.national.rules_engine.domain.enums import RuleCategory
            filters["category"] = RuleCategory(category).value if hasattr(RuleCategory, "_value2member_map_") else RuleCategory(category)
        if status:
            from app.national.rules_engine.domain.enums import RuleStatus
            filters["status"] = RuleStatus(status).value if hasattr(RuleStatus, "_value2member_map_") else RuleStatus(status)
        return await self.repository.list(skip=skip, limit=limit, **filters)

    async def delete_rule(self, rule_id: str) -> None:
        await self._get_rule_or_raise(rule_id)
        await self.repository.delete(rule_id)
        self._invalidate_cache()

    async def get_evaluation_history(self, rule_id: str) -> list[dict[str, Any]]:
        rule = await self._get_rule_or_raise(rule_id)
        return []

    async def list_categories(self) -> list[str]:
        from app.national.rules_engine.domain.enums import RuleCategory
        return [c.value for c in RuleCategory]

    async def _get_rule_or_raise(self, rule_id: str) -> RuleDefinition:
        rule = await self.repository.get(rule_id)
        if not rule:
            raise RuleNotFoundError(rule_id)
        return rule

    async def _get_active_rules_for_context(self, context: RuleEvaluationContext) -> list[RuleDefinition]:
        now = datetime.now(UTC)
        if self._cache and self._cache_timestamp:
            age = (now - self._cache_timestamp).total_seconds()
            if age < self._cache_ttl_seconds:
                return self._cache.get("active", [])
        rules = await self.repository.find_active()
        self._cache["active"] = rules
        self._cache_timestamp = now
        return rules

    def _invalidate_cache(self) -> None:
        self._cache = {}
        self._cache_timestamp = None

    async def _validate_rule(self, rule: RuleDefinition) -> list[str]:
        errors: list[str] = []
        if not rule.name or not rule.name.strip():
            errors.append("Rule name is required")
        if not rule.conditions:
            errors.append("Rule must have at least one condition")
        for condition in rule.conditions:
            if not condition.field:
                errors.append("Each condition must have a field specified")
        return errors

    async def _send_violation_notification(
        self,
        rule: RuleDefinition,
        result: RuleEvaluationResult,
        context: RuleEvaluationContext,
    ) -> None:
        if not self.notification_service:
            return
        try:
            subject = f"Rule Violation: {rule.name}"
            body = (
                f"Rule '{rule.name}' (ID: {rule.id}) violated.\n"
                f"Severity: {rule.severity.value}\n"
                f"Outcome: {result.outcome.value}\n"
                f"Message: {result.message}\n"
                f"Resource: {context.resource_type}/{context.resource_id}\n"
                f"Tenant: {context.tenant_id}"
            )
            self.notification_service.send(
                channel="alert",
                to="admin",
                subject=subject,
                body=body,
                priority="high" if rule.severity in (RuleSeverity.CRITICAL, RuleSeverity.BLOCKER) else "normal",
            )
        except Exception as exc:
            logger.error("Failed to send violation notification for rule %s: %s", rule.id, exc)

    def _publish_event(self, domain_event: Any) -> None:
        try:
            event = Event(
                name=domain_event.event_type,
                data=domain_event.payload if hasattr(domain_event, "payload") else {},
                correlation_id=domain_event.correlation_id if hasattr(domain_event, "correlation_id") else "",
                tenant_id=domain_event.tenant_id if hasattr(domain_event, "tenant_id") else "",
            )
            self.event_bus.publish(event)
        except Exception as exc:
            logger.error("Failed to publish event %s: %s", getattr(domain_event, "event_type", "unknown"), exc)
