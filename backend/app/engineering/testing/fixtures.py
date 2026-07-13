from __future__ import annotations

from typing import Any

from backend.app.engineering.generators.base import BaseGenerator, GenerateResult


class FixturesGenerator(BaseGenerator):
    def generate(self, **kwargs: Any) -> GenerateResult:
        module = kwargs.get("module", "app")
        entities = kwargs.get("entities", ["User", "Item", "Order"])
        use_faker = kwargs.get("use_faker", True)

        fixtures = []
        for entity in entities:
            fixtures.append(self._entity_fixture(entity, use_faker))

        content = f'''"""Test fixtures for {module}."""
from __future__ import annotations

from typing import Any, AsyncGenerator, Generator

import pytest
{"from faker import Faker" if use_faker else ""}

{"faker = Faker()" if use_faker else ""}

{chr(10).join(fixtures)}
'''
        self._write("conftest.py", content)

        return self._result

    def _entity_fixture(self, entity: str, use_faker: bool) -> str:
        entity_lower = entity.lower()
        fake_attrs = ""
        if use_faker:
            fake_attrs = f"""
    return {entity}(
        id=faker.random_int(min=1, max=99999),
        name=faker.name(),
        created_at=datetime.utcnow(),
    )"""
        else:
            fake_attrs = f"""
    return {entity}(
        id=1,
        name="test-{entity_lower}",
        created_at=datetime.utcnow(),
    )"""

        return f'''
@pytest.fixture
def {entity_lower}_factory() -> Any:
    """Factory fixture for {entity}."""
    from datetime import datetime{fake_attrs}


@pytest.fixture
async def {entity_lower}() -> Any:
    """Single {entity} instance."""
    return {entity}(
        id=1,
        name="test-{entity_lower}",
    )


@pytest.fixture
async def {entity_lower}s() -> list:
    """Multiple {entity} instances."""
    return [
        {entity}(id=i, name=f"test-{entity_lower}-{{i}}")
        for i in range(1, 4)
    ]
'''
