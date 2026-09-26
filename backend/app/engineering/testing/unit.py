from __future__ import annotations

from typing import Any

from backend.app.engineering.generators.base import BaseGenerator, GenerateResult


class UnitTestGenerator(BaseGenerator):
    def generate(self, **kwargs: Any) -> GenerateResult:
        module_path = kwargs.get("module_path", "")
        module_name = module_path.replace("/", ".").replace(".py", "")
        class_name = kwargs.get("class_name", module_path.split("/")[-1].replace(".py", "").title())

        content = f"""from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from {module_name} import {class_name}


class Test{class_name}:
    def test_init(self):
        instance = {class_name}()
        assert instance is not None

    def test_repr(self):
        instance = {class_name}()
        result = repr(instance)
        assert result is not None

    def test_str(self):
        instance = {class_name}()
        result = str(instance)
        assert result is not None
"""
        self._write(f"test_{module_path.replace('/', '_')}", content)
        return self._result


class IntegrationTestGenerator(BaseGenerator):
    def generate(self, **kwargs: Any) -> GenerateResult:
        module_path = kwargs.get("module_path", "module")
        entity = kwargs.get("entity", "Entity")

        content = f"""from __future__ import annotations

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from models.{module_path} import Base
from repositories.{module_path}_repository import {entity}Repository


@pytest.fixture()
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine, tables=own_tables(Base))
    session = sessionmaker(bind=engine)()
    yield session
    session.close()


class Test{entity}Repository:
    def test_create(self, db_session):
        repo = {entity}Repository(db_session)
        entity = repo.create({entity}())
        assert entity.id is not None

    def test_get(self, db_session):
        repo = {entity}Repository(db_session)
        entity = repo.create({entity}())
        found = repo.get(entity.id)
        assert found is not None
        assert found.id == entity.id
"""
        self._write(f"test_integration_{module_path}.py", content)
        return self._result
