from __future__ import annotations

import logging
import os

logger = logging.getLogger("gula.generators.module")

_ROUTE_TPL = '''from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter

logger = logging.getLogger("gula.{name}")

router = APIRouter(prefix="/api/v1/{name}", tags=["{name_caps}"])


@router.get("")
async def list_{name}() -> list[dict[str, Any]]:
    return []


@router.post("")
async def create_{name}(data: dict[str, Any]) -> dict[str, Any]:
    return {"id": 0, **data}
'''

_MODEL_TPL = '''from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import Column, DateTime, Integer, String
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class {model_name}(Base):
    __tablename__ = "{table_name}"

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC), nullable=False)
'''

_TEST_TPL = '''"""Tests for {name} module."""

from __future__ import annotations


def test_{name}_list():
    assert True


def test_{name}_create():
    assert True
'''


class ModuleGenerator:
    def __init__(self, name: str, target_dir: str = "backend/app") -> None:
        self._name = name.lower().replace("-", "_")
        self._name_caps = name.replace("-", " ").title().replace(" ", "")
        self._target_dir = target_dir

    def generate(self) -> None:
        routes_dir = os.path.join(self._target_dir, "routes")
        models_dir = os.path.join(self._target_dir, "models")
        tests_dir = os.path.join(self._target_dir.replace("app", "tests"), self._name)
        os.makedirs(routes_dir, exist_ok=True)
        os.makedirs(models_dir, exist_ok=True)
        os.makedirs(tests_dir, exist_ok=True)

        route_path = os.path.join(routes_dir, f"{self._name}.py")
        if not os.path.exists(route_path):
            with open(route_path, "w") as f:
                f.write(_ROUTE_TPL.format(name=self._name, name_caps=self._name_caps))
            logger.info("Created route: %s", route_path)

        model_path = os.path.join(models_dir, f"{self._name}.py")
        if not os.path.exists(model_path):
            model_name = "".join(word.capitalize() for word in self._name.split("_"))
            with open(model_path, "w") as f:
                f.write(_MODEL_TPL.format(model_name=model_name, table_name=self._name))
            logger.info("Created model: %s", model_path)

        test_path = os.path.join(tests_dir, f"test_{self._name}.py")
        if not os.path.exists(test_path):
            with open(test_path, "w") as f:
                f.write(_TEST_TPL.format(name=self._name))
            logger.info("Created test: %s", test_path)

        logger.info("Module '%s' generated successfully", self._name)


__all__ = ["ModuleGenerator"]
