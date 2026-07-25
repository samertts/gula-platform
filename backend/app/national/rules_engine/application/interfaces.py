from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from app.national.rules_engine.domain.entities import RuleDefinition


class RuleValidator(ABC):
    @abstractmethod
    async def validate_syntax(self, rule: RuleDefinition) -> list[str]: ...

    @abstractmethod
    async def validate_semantics(self, rule: RuleDefinition) -> list[str]: ...

    @abstractmethod
    async def validate_conflicts(
        self, rule: RuleDefinition, existing_rules: list[RuleDefinition],
    ) -> list[str]: ...

    @abstractmethod
    async def validate(
        self, rule: RuleDefinition, existing_rules: list[RuleDefinition] | None = None,
    ) -> dict[str, Any]: ...
