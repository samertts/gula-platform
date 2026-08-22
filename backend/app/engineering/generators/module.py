from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from backend.app.engineering.generators.base import BaseGenerator, GenerateResult


@dataclass
class ModuleSpec:
    name: str
    description: str = ""
    package: str = "app"
    has_entity: bool = True
    has_events: bool = True
    has_commands: bool = True
    has_queries: bool = True
    features: list[str] = field(default_factory=list)


class ModuleGenerator(BaseGenerator):
    def generate(self, **kwargs: Any) -> GenerateResult:
        spec = kwargs.get("spec", kwargs.get("module"))
        if isinstance(spec, dict):
            spec = ModuleSpec(**spec)
        if spec is None:
            spec = ModuleSpec(name=kwargs.get("name", "unnamed"))

        module = spec.name.lower().replace(" ", "_")
        mod = spec.name[0].upper() + spec.name[1:]

        layers = [
            ("domain", ["entities", "events", "value_objects", "exceptions"]),
            ("application", ["commands", "queries", "dtos", "services", "interfaces"]),
            ("infrastructure", ["repositories", "mappers", "unit_of_work"]),
            ("presentation", ["routes", "middleware"]),
        ]

        for layer, dirs in layers:
            base = f"{module}/{layer}"
            self._ensure_dir(base)
            (self.target_dir / base / "__init__.py").touch()
            for d in dirs:
                sub = f"{base}/{d}"
                self._ensure_dir(sub)
                (self.target_dir / sub / "__init__.py").touch()

        self._write(
            f"{module}/__init__.py",
            f"""from __future__ import annotations

\"\"\"{spec.name} Module: {spec.description}\"\"\"
""",
        )

        self._write(
            f"{module}/domain/entities/{module}.py",
            f"""from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime


@dataclass
class {mod}:
    id: int | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))
""",
        )

        if spec.has_events:
            self._write(
                f"{module}/domain/events.py",
                f"""from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime


@dataclass
class {mod}Created:
    {module}_id: int
    occurred_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class {mod}Updated:
    {module}_id: int
    occurred_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class {mod}Deleted:
    {module}_id: int
    occurred_at: datetime = field(default_factory=lambda: datetime.now(UTC))
""",
            )

        if spec.has_commands:
            self._write(
                f"{module}/application/commands/create_{module}.py",
                f"""from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Create{mod}:
    pass


@dataclass
class Update{mod}:
    id: int


@dataclass
class Delete{mod}:
    id: int
""",
            )

        if spec.has_queries:
            self._write(
                f"{module}/application/queries/get_{module}.py",
                f"""from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Get{mod}:
    id: int


@dataclass
class List{mod}s:
    skip: int = 0
    limit: int = 100
""",
            )

        self._write(
            f"{module}/application/services/{module}_service.py",
            f"""from __future__ import annotations

from typing import Optional


class {mod}Service:
    def __init__(self) -> None:
        pass
""",
        )

        self._write(
            f"{module}/application/dtos.py",
            f"""from __future__ import annotations

from datetime import UTC, datetime

from pydantic import BaseModel, ConfigDict


class {mod}Create(BaseModel):
    pass


class {mod}Update(BaseModel):
    pass


class {mod}Response(BaseModel):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
""",
        )

        self._write(
            f"{module}/application/interfaces.py",
            f"""from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional


class {mod}Repository(ABC):
    @abstractmethod
    async def get(self, id: int) -> Optional[...]:
        ...
""",
        )

        self._write(
            f"{module}/infrastructure/repositories/{module}_repository.py",
            f"""from __future__ import annotations

from typing import Optional


class {mod}RepositoryImpl:
    def __init__(self) -> None:
        pass

    async def get(self, id: int) -> Optional[...]:
        return None
""",
        )

        self._write(
            f"{module}/presentation/routes.py",
            f"""from __future__ import annotations

from fastapi import APIRouter

router = APIRouter(prefix="/{module}s", tags=["{mod}"])
""",
        )

        return self._result
