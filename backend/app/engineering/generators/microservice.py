from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from backend.app.engineering.generators.base import BaseGenerator, GenerateResult


@dataclass
class MicroserviceSpec:
    name: str
    port: int = 8000
    description: str = ""
    dependencies: list[str] = field(
        default_factory=lambda: ["fastapi", "uvicorn", "pydantic", "httpx"]
    )
    dev_dependencies: list[str] = field(
        default_factory=lambda: ["pytest", "ruff", "mypy", "coverage", "bandit"]
    )
    has_database: bool = True
    has_redis: bool = False
    has_event_bus: bool = True
    has_health_check: bool = True


class MicroserviceGenerator(BaseGenerator):
    def generate(self, **kwargs: Any) -> GenerateResult:
        spec = kwargs.get("spec", kwargs.get("microservice"))
        if isinstance(spec, dict):
            spec = MicroserviceSpec(**spec)
        if spec is None:
            spec = MicroserviceSpec(name=kwargs.get("name", "unnamed-service"))

        self._write(
            "pyproject.toml",
            f"""[build-system]
requires = ["setuptools>=80", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "{spec.name}"
version = "0.1.0"
description = "{spec.description}"
requires-python = ">=3.11"
dependencies = {spec.dependencies}

[project.optional-dependencies]
dev = {spec.dev_dependencies}

[tool.ruff]
target-version = "py311"
line-length = 100

[tool.pytest.ini_options]
testpaths = ["tests"]
asyncio_mode = "auto"
""",
        )

        src = self._ensure_dir("app")
        (src / "__init__.py").touch()

        self._write(
            "app/main.py",
            f'''"""FastAPI application for {spec.name}."""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

logger = logging.getLogger("{spec.name}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting {spec.name}")
    yield
    logger.info("Stopping {spec.name}")


app = FastAPI(
    title="{spec.name}",
    description="{spec.description}",
    version="0.1.0",
    lifespan=lifespan,
)
''',
        )

        if spec.has_health_check:
            self._write(
                "app/health.py",
                f"""from __future__ import annotations

from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/health")
async def health():
    return {{"status": "ok", "service": "{spec.name}"}}


@router.get("/health/ready")
async def ready():
    return {{"status": "ready"}}


@router.get("/health/live")
async def live():
    return {{"status": "alive"}}
""",
            )

        if spec.has_database:
            self._write(
                "app/database.py",
                """from __future__ import annotations

import os

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./data.db")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()


def get_db():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
""",
            )

        self._write(
            "Dockerfile",
            f"""FROM python:3.11-slim

WORKDIR /app
COPY pyproject.toml .
RUN pip install .
COPY app/ app/

EXPOSE {spec.port}

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "{spec.port}"]
""",
        )

        self._ensure_dir("tests")
        (self.target_dir / "tests" / "__init__.py").touch()

        self._write(
            "tests/test_health.py",
            f"""from __future__ import annotations

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["service"] == "{spec.name}"
""",
        )

        return self._result
