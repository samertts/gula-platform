from __future__ import annotations
from datetime import UTC

from dataclasses import dataclass, field
from typing import Any

from backend.app.engineering.generators.base import BaseGenerator, GenerateResult


@dataclass
class RepositorySpec:
    name: str
    table: str = ""
    has_soft_delete: bool = True
    has_version_lock: bool = True
    has_audit: bool = True
    methods: list[str] = field(
        default_factory=lambda: ["get", "list", "create", "update", "delete", "count"],
    )
    interface: bool = True
    impl: bool = True


class RepositoryGenerator(BaseGenerator):
    def generate(self, **kwargs: Any) -> GenerateResult:
        spec = kwargs.get("spec", kwargs.get("repository"))
        if isinstance(spec, dict):
            spec = RepositorySpec(**spec)
        if spec is None:
            spec = RepositorySpec(name=kwargs.get("name", "Entity"))

        module = spec.name.lower()
        mod = spec.name[0].upper() + spec.name[1:]

        if spec.interface:
            methods = []
            for m in spec.methods:
                sig = self._method_signature(m, mod)
                methods.append(f"    {sig}")
            self._write(
                f"domain/repositories/{module}_repository.py",
                f'''"""Repository interface for {mod}."""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional


class {mod}Repository(ABC):
{chr(10).join(methods)}
''',
            )

        if spec.impl:
            impl_methods = []
            for m in spec.methods:
                impl_methods.append(self._impl_method(m, mod, spec))

            self._write(
                f"infrastructure/repositories/{module}_repository.py",
                f'''"""SQLAlchemy repository for {mod}."""
from __future__ import annotations

from datetime import UTC, datetime
from typing import Optional

from sqlalchemy.orm import Session

from models.{module} import {mod}
from domain.repositories.{module}_repository import {mod}Repository as {mod}RepositoryInterface


class {mod}RepositoryImpl({mod}RepositoryInterface):
    def __init__(self, session: Session):
        self.session = session
        self.model = {mod}

    {chr(10).join(impl_methods)}
''',
            )

        return self._result

    def _method_signature(self, method: str, mod: str) -> str:
        sigs = {
            "get": "async def get(self, id: int) -> Optional[{mod}]: ...",
            "list": "async def list(self, skip: int = 0, limit: int = 100) -> list[{mod}]: ...",
            "create": "async def create(self, entity: {mod}) -> {mod}: ...",
            "update": "async def update(self, entity: {mod}) -> {mod}: ...",
            "delete": "async def delete(self, id: int) -> bool: ...",
            "count": "async def count(self) -> int: ...",
        }
        return sigs.get(method, f"async def {method}(self) -> None: ...").format(mod=mod)

    def _impl_method(self, method: str, mod: str, spec: RepositorySpec) -> str:
        soft_del_filter = (
            "\n        query = query.filter(self.model.deleted_at.is_(None))"
            if spec.has_soft_delete
            else ""
        )
        soft_del_body = (
            "\n        entity.deleted_at = datetime.now(UTC)"
            if spec.has_soft_delete
            else "\n        self.session.delete(entity)"
        )

        methods = {
            "get": f"async def get(self, id: int) -> Optional[{mod}]:\n        return self.session.query(self.model).filter(self.model.id == id).first()",
            "list": f"async def list(self, skip: int = 0, limit: int = 100) -> list[{mod}]:\n        query = self.session.query(self.model){soft_del_filter}\n        return query.offset(skip).limit(limit).all()",
            "create": f"async def create(self, entity: {mod}) -> {mod}:\n        self.session.add(entity)\n        await self.session.flush()\n        return entity",
            "update": f"async def update(self, entity: {mod}) -> {mod}:\n        self.session.merge(entity)\n        await self.session.flush()\n        return entity",
            "delete": f"async def delete(self, id: int) -> bool:\n        entity = await self.get(id)\n        if not entity:\n            return False{soft_del_body}\n        await self.session.flush()\n        return True",
            "count": "async def count(self) -> int:\n        query = self.session.query(self.model)\n        return query.count()",
        }
        return methods.get(method, f"async def {method}(self) -> None: pass")
