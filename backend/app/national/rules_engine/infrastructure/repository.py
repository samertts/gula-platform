from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy.orm import Session

from app._compat import UTC
from app.national.rules_engine.domain.entities import RuleDefinition
from app.national.rules_engine.domain.enums import RuleCategory, RuleStatus
from app.national.rules_engine.domain.repository import RuleRepository
from app.national.rules_engine.infrastructure.models import RuleEvaluationLog, RuleModel


class SQLAlchemyRuleRepository(RuleRepository):
    def __init__(self, db: Session) -> None:
        self.db = db

    async def save(self, rule: RuleDefinition) -> RuleDefinition:
        model = self.db.query(RuleModel).filter(RuleModel.id == rule.id).first()
        if model:
            model.name = rule.name
            model.description = rule.description
            model.category = rule.category
            model.severity = rule.severity
            model.status = rule.status
            model.conditions = [
                {
                    "field": c.field,
                    "operator": c.operator.value,
                    "value": c.value,
                    "value_type": c.value_type,
                }
                for c in rule.conditions
            ]
            model.actions = [
                {"action_type": a.action_type, "params": a.params} for a in rule.actions
            ]
            model.priority = rule.priority
            model.version = rule.version
            model.tags = rule.tags
            model.effective_from = rule.effective_from
            model.effective_to = rule.effective_to
            model.metadata_ = rule.metadata
        else:
            model = RuleModel(
                id=rule.id,
                name=rule.name,
                description=rule.description,
                category=rule.category,
                severity=rule.severity,
                status=rule.status,
                conditions=[
                    {
                        "field": c.field,
                        "operator": c.operator.value,
                        "value": c.value,
                        "value_type": c.value_type,
                    }
                    for c in rule.conditions
                ],
                actions=[{"action_type": a.action_type, "params": a.params} for a in rule.actions],
                priority=rule.priority,
                version=rule.version,
                tags=rule.tags,
                effective_from=rule.effective_from,
                effective_to=rule.effective_to,
                metadata_=rule.metadata,
            )
            self.db.add(model)
        self.db.commit()
        self.db.refresh(model)
        return model.to_domain()

    async def get(self, rule_id: str) -> RuleDefinition | None:
        model = (
            self.db.query(RuleModel)
            .filter(
                RuleModel.id == rule_id,
                ~RuleModel.is_deleted,
            )
            .first()
        )
        if not model:
            return None
        return model.to_domain()

    async def list(self, skip: int = 0, limit: int = 100, **filters: Any) -> list[RuleDefinition]:
        query = self.db.query(RuleModel).filter(~~RuleModel.is_deleted)
        for key, value in filters.items():
            if hasattr(RuleModel, key) and value is not None:
                query = query.filter(getattr(RuleModel, key) == value)
        models = query.order_by(RuleModel.priority.desc()).offset(skip).limit(limit).all()
        return [m.to_domain() for m in models]

    async def delete(self, rule_id: str, soft: bool = True) -> None:
        model = (
            self.db.query(RuleModel)
            .filter(
                RuleModel.id == rule_id,
                ~RuleModel.is_deleted,
            )
            .first()
        )
        if model:
            if soft:
                model.is_deleted = True
                model.deleted_at = datetime.now(UTC)
            else:
                self.db.delete(model)
            self.db.commit()

    async def find_by_category(
        self, category: RuleCategory, skip: int = 0, limit: int = 100,
    ) -> list[RuleDefinition]:
        models = (
            self.db.query(RuleModel)
            .filter(
                RuleModel.category == category,
                ~RuleModel.is_deleted,
            )
            .order_by(RuleModel.priority.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )
        return [m.to_domain() for m in models]

    async def find_by_status(
        self, status: RuleStatus, skip: int = 0, limit: int = 100,
    ) -> list[RuleDefinition]:
        models = (
            self.db.query(RuleModel)
            .filter(
                RuleModel.status == status,
                ~RuleModel.is_deleted,
            )
            .order_by(RuleModel.priority.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )
        return [m.to_domain() for m in models]

    async def find_by_tags(
        self, tags: list[str], skip: int = 0, limit: int = 100,
    ) -> list[RuleDefinition]:
        models = (
            self.db.query(RuleModel)
            .filter(
                ~~RuleModel.is_deleted,
            )
            .order_by(RuleModel.priority.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )
        result: list[RuleDefinition] = []
        for m in models:
            if m.tags and any(t in m.tags for t in tags):
                result.append(m.to_domain())
        return result

    async def find_active(self, skip: int = 0, limit: int = 100) -> list[RuleDefinition]:
        now = datetime.now(UTC)
        models = (
            self.db.query(RuleModel)
            .filter(
                RuleModel.status == RuleStatus.ACTIVE,
                ~RuleModel.is_deleted,
                (RuleModel.effective_from is None) | (RuleModel.effective_from <= now),
                (RuleModel.effective_to is None) | (RuleModel.effective_to >= now),
            )
            .order_by(RuleModel.priority.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )
        return [m.to_domain() for m in models]

    async def count(self, **filters: Any) -> int:
        query = self.db.query(RuleModel).filter(~~RuleModel.is_deleted)
        for key, value in filters.items():
            if hasattr(RuleModel, key) and value is not None:
                query = query.filter(getattr(RuleModel, key) == value)
        return query.count()

    async def log_evaluation(self, log_entry: RuleEvaluationLog) -> None:
        self.db.add(log_entry)
        self.db.commit()

    async def get_evaluation_logs(
        self,
        rule_id: str,
        skip: int = 0,
        limit: int = 100,
    ) -> list[RuleEvaluationLog]:
        return (
            self.db.query(RuleEvaluationLog)
            .filter(
                RuleEvaluationLog.rule_id == rule_id,
            )
            .order_by(RuleEvaluationLog.triggered_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )
