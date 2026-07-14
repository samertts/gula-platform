from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from app.national.rules_engine.domain.entities import RuleDefinition
from app.national.rules_engine.domain.enums import RuleCategory, RuleStatus


class RuleRepository(ABC):
    @abstractmethod
    async def save(self, rule: RuleDefinition) -> RuleDefinition: ...

    @abstractmethod
    async def get(self, rule_id: str) -> RuleDefinition | None: ...

    @abstractmethod
    async def list(self, skip: int = 0, limit: int = 100, **filters: Any) -> list[RuleDefinition]: ...

    @abstractmethod
    async def delete(self, rule_id: str, soft: bool = True) -> None: ...

    @abstractmethod
    async def find_by_category(self, category: RuleCategory, skip: int = 0, limit: int = 100) -> list[RuleDefinition]: ...

    @abstractmethod
    async def find_by_status(self, status: RuleStatus, skip: int = 0, limit: int = 100) -> list[RuleDefinition]: ...

    @abstractmethod
    async def find_by_tags(self, tags: list[str], skip: int = 0, limit: int = 100) -> list[RuleDefinition]: ...

    @abstractmethod
    async def find_active(self, skip: int = 0, limit: int = 100) -> list[RuleDefinition]: ...

    @abstractmethod
    async def count(self, **filters: Any) -> int: ...
