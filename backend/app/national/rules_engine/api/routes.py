from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.national.rules_engine.application.service import RulesEngineService
from app.national.rules_engine.domain.entities import (
    RuleAction,
    RuleCondition,
    RuleDefinition,
    RuleEvaluationContext,
)
from app.national.rules_engine.domain.enums import (
    Operator,
    RuleCategory,
    RuleSeverity,
)
from app.national.rules_engine.exceptions import (
    RuleEvaluationError,
    RuleNotFoundError,
    RuleValidationError,
    RuleVersionError,
)
from app.national.rules_engine.infrastructure.repository import SQLAlchemyRuleRepository

router = APIRouter(prefix="/national/rules", tags=["National Rules Engine"])


def _get_service(db: Session = Depends(get_db)) -> RulesEngineService:
    from app.kernel import Kernel
    from app.kernel.event_bus.bus import EventBus

    kernel = Kernel.get_instance()
    event_bus = kernel.event_bus if hasattr(kernel, "event_bus") else EventBus(kernel)
    repo = SQLAlchemyRuleRepository(db)
    return RulesEngineService(repository=repo, event_bus=event_bus)


@router.post("/evaluate")
async def evaluate_rules(
    context: RuleEvaluationContext,
    service: RulesEngineService = Depends(_get_service),
) -> list[dict[str, Any]]:
    try:
        results = await service.evaluate(context)
        return [
            {
                "rule_id": r.rule_id,
                "rule_name": r.rule_name,
                "outcome": r.outcome.value,
                "severity": r.severity.value,
                "message": r.message,
                "execution_time_ms": r.execution_time_ms,
                "triggered_at": r.triggered_at.isoformat(),
            }
            for r in results
        ]
    except RuleEvaluationError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e)) from e


@router.post("/simulate")
async def simulate_rule(
    rule: RuleDefinition,
    context: RuleEvaluationContext,
    service: RulesEngineService = Depends(_get_service),
) -> dict[str, Any]:
    try:
        return await service.simulate(rule, context)
    except RuleValidationError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e)) from e


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_rule(
    rule: RuleDefinition,
    service: RulesEngineService = Depends(_get_service),
) -> dict[str, Any]:
    try:
        saved = await service.register_rule(rule)
        return {
            "id": saved.id,
            "name": saved.name,
            "category": saved.category.value,
            "status": saved.status.value,
            "version": saved.version,
        }
    except RuleValidationError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e)) from e


@router.get("/")
async def list_rules(
    category: str | None = Query(None),
    status: str | None = Query(None),
    search: str | None = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    service: RulesEngineService = Depends(_get_service),
) -> list[dict[str, Any]]:
    rules = await service.list_rules(
        category=category,
        status=status,
        search=search,
        skip=skip,
        limit=limit,
    )
    return [
        {
            "id": r.id,
            "name": r.name,
            "description": r.description,
            "category": r.category.value,
            "severity": r.severity.value,
            "status": r.status.value,
            "priority": r.priority,
            "version": r.version,
            "tags": r.tags,
            "effective_from": r.effective_from.isoformat() if r.effective_from else None,
            "effective_to": r.effective_to.isoformat() if r.effective_to else None,
        }
        for r in rules
    ]


@router.get("/{rule_id}")
async def get_rule(
    rule_id: str,
    service: RulesEngineService = Depends(_get_service),
) -> dict[str, Any]:
    try:
        rule = await service.get_rule(rule_id)
        return {
            "id": rule.id,
            "name": rule.name,
            "description": rule.description,
            "category": rule.category.value,
            "severity": rule.severity.value,
            "status": rule.status.value,
            "conditions": [
                {
                    "field": c.field,
                    "operator": c.operator.value,
                    "value": c.value,
                    "value_type": c.value_type,
                }
                for c in rule.conditions
            ],
            "actions": [
                {
                    "action_type": a.action_type,
                    "params": a.params,
                }
                for a in rule.actions
            ],
            "priority": rule.priority,
            "version": rule.version,
            "tags": rule.tags,
            "effective_from": rule.effective_from.isoformat() if rule.effective_from else None,
            "effective_to": rule.effective_to.isoformat() if rule.effective_to else None,
            "metadata": rule.metadata,
        }
    except RuleNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e


@router.put("/{rule_id}")
async def update_rule(
    rule_id: str,
    updates: dict[str, Any],
    service: RulesEngineService = Depends(_get_service),
) -> dict[str, Any]:
    try:
        rule = await service.get_rule(rule_id)
        if "name" in updates:
            rule.name = updates["name"]
        if "description" in updates:
            rule.description = updates["description"]
        if "category" in updates:
            rule.category = RuleCategory(updates["category"])
        if "severity" in updates:
            rule.severity = RuleSeverity(updates["severity"])
        if "conditions" in updates:
            rule.conditions = [
                RuleCondition(
                    field=c["field"],
                    operator=Operator(c["operator"]),
                    value=c.get("value"),
                    value_type=c.get("value_type", "string"),
                )
                for c in updates["conditions"]
            ]
        if "actions" in updates:
            rule.actions = [
                RuleAction(action_type=a["action_type"], params=a.get("params", {}))
                for a in updates["actions"]
            ]
        if "priority" in updates:
            rule.priority = updates["priority"]
        if "tags" in updates:
            rule.tags = updates["tags"]
        if "effective_from" in updates:
            from datetime import datetime
            rule.effective_from = datetime.fromisoformat(updates["effective_from"]) if isinstance(updates["effective_from"], str) else updates["effective_from"]
        if "effective_to" in updates:
            from datetime import datetime
            rule.effective_to = datetime.fromisoformat(updates["effective_to"]) if isinstance(updates["effective_to"], str) else updates["effective_to"]
        if "metadata" in updates:
            rule.metadata = updates["metadata"]
        saved = await service.repository.save(rule)
        return {"id": saved.id, "name": saved.name, "status": saved.status.value, "version": saved.version}
    except RuleNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    except RuleValidationError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e)) from e


@router.delete("/{rule_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_rule(
    rule_id: str,
    service: RulesEngineService = Depends(_get_service),
) -> None:
    try:
        await service.delete_rule(rule_id)
    except RuleNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e


@router.post("/{rule_id}/activate")
async def activate_rule(
    rule_id: str,
    service: RulesEngineService = Depends(_get_service),
) -> dict[str, Any]:
    try:
        rule = await service.activate_rule(rule_id)
        return {"id": rule.id, "name": rule.name, "status": rule.status.value}
    except RuleNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    except RuleValidationError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e)) from e


@router.post("/{rule_id}/deactivate")
async def deactivate_rule(
    rule_id: str,
    service: RulesEngineService = Depends(_get_service),
) -> dict[str, Any]:
    try:
        rule = await service.deactivate_rule(rule_id)
        return {"id": rule.id, "name": rule.name, "status": rule.status.value}
    except RuleNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    except RuleValidationError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e)) from e


@router.post("/{rule_id}/version")
async def create_rule_version(
    rule_id: str,
    updates: dict[str, Any],
    service: RulesEngineService = Depends(_get_service),
) -> dict[str, Any]:
    try:
        new_rule = await service.create_new_version(rule_id, updates)
        return {
            "id": new_rule.id,
            "name": new_rule.name,
            "version": new_rule.version,
            "status": new_rule.status.value,
        }
    except RuleNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    except (RuleValidationError, RuleVersionError) as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e)) from e


@router.get("/{rule_id}/versions")
async def list_rule_versions(
    rule_id: str,
    service: RulesEngineService = Depends(_get_service),
) -> list[dict[str, Any]]:
    try:
        rule = await service.get_rule(rule_id)
        rules = await service.repository.list(limit=1000)
        versions = [r for r in rules if r.name == rule.name]
        return [
            {
                "id": r.id,
                "version": r.version,
                "status": r.status.value,
                "created_at": r.metadata.get("created_at") if isinstance(r.metadata, dict) else None,
            }
            for r in sorted(versions, key=lambda x: x.version)
        ]
    except RuleNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e


@router.get("/{rule_id}/evaluations")
async def get_rule_evaluations(
    rule_id: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    service: RulesEngineService = Depends(_get_service),
) -> list[dict[str, Any]]:
    try:
        await service.get_rule(rule_id)
        logs = await service.repository.get_evaluation_logs(rule_id, skip=skip, limit=limit)
        return [
            {
                "id": log.id,
                "outcome": log.outcome.value if hasattr(log.outcome, "value") else str(log.outcome),
                "severity": log.severity.value if log.severity and hasattr(log.severity, "value") else str(log.severity) if log.severity else None,
                "trigger": log.trigger.value if log.trigger and hasattr(log.trigger, "value") else str(log.trigger) if log.trigger else None,
                "resource_type": log.resource_type,
                "resource_id": log.resource_id,
                "execution_time_ms": log.execution_time_ms,
                "triggered_at": log.triggered_at.isoformat() if log.triggered_at else None,
            }
            for log in logs
        ]
    except RuleNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e


@router.get("/categories")
async def list_categories(
    service: RulesEngineService = Depends(_get_service),
) -> list[str]:
    return await service.list_categories()


@router.get("/health")
async def health() -> dict[str, Any]:
    return {"status": "ok", "module": "national_rules_engine", "version": "1.0.0"}
