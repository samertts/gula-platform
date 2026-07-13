from __future__ import annotations

from typing import Any

from backend.app.engineering.generators.base import BaseGenerator, GenerateResult


class FactoriesGenerator(BaseGenerator):
    def generate(self, **kwargs: Any) -> GenerateResult:
        module = kwargs.get("module", "app")
        entities = kwargs.get("entities", ["User", "Item", "Order"])

        factory_classes = []
        for entity in entities:
            factory_classes.append(self._factory_class(entity))

        content = f'''"""Test factories for {module} using factory_boy pattern."""
from __future__ import annotations

import factory
from datetime import datetime


{chr(10).join(factory_classes)}
'''
        self._write(f"factories.py", content)

        return self._result

    def _factory_class(self, entity: str) -> str:
        return f'''
class {entity}Factory(factory.Factory):
    class Meta:
        model = "models.{entity.lower()}.{entity}"

    id = factory.Sequence(lambda n: n + 1)
    name = factory.Faker("name")
    created_at = factory.LazyFunction(datetime.utcnow)
    updated_at = factory.LazyFunction(datetime.utcnow)
'''
