from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from backend.app.engineering.generators.base import BaseGenerator, GenerateResult


@dataclass
class EntityField:
    name: str
    type: str
    required: bool = True
    default: Any | None = None
    max_length: int | None = None
    indexed: bool = False
    unique: bool = False
    foreign_key: str | None = None
    description: str = ""


@dataclass
class EntitySpec:
    name: str
    table_name: str | None = None
    fields: list[EntityField] = field(default_factory=list)
    soft_delete: bool = True
    audit_fields: bool = True
    version_lock: bool = True


class CRUDGenerator(BaseGenerator):
    def generate(self, **kwargs: Any) -> GenerateResult:
        spec = kwargs.get("spec", kwargs.get("entity"))
        if isinstance(spec, dict):
            spec = EntitySpec(**spec)
        if spec is None:
            spec = EntitySpec(name=kwargs.get("name", "Unnamed"))

        table = spec.table_name or f"{spec.name.lower()}s"
        module = spec.name.lower()
        fields = spec.fields

        self._generate_entity(module, spec, table, fields)
        self._generate_repository(module, spec)
        self._generate_service(module, spec)
        self._generate_dto(module, spec, fields)
        self._generate_rest_api(module, spec)

        return self._result

    def _generate_entity(
        self, module: str, spec: EntitySpec, table: str, fields: list[EntityField],
    ) -> None:
        lines = [
            "from __future__ import annotations",
            "",
            "from datetime import datetime",
            "from typing import Optional",
            "from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text",
            "from sqlalchemy.orm import declarative_base",
            "",
            "Base = declarative_base()",
            "",
            "",
        ]
        audit = """
    created_at: datetime = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: datetime = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
"""
        soft_del = "    deleted_at: Optional[datetime] = Column(DateTime, nullable=True)\n"
        version = "    version: int = Column(Integer, default=1, nullable=False)\n"

        lines.append(f"class {spec.name}(Base):")
        lines.append(f'    __tablename__ = "{table}"')
        lines.append("")
        lines.append("    id: int = Column(Integer, primary_key=True, autoincrement=True)")
        for f in fields:
            col_type = self._map_type(f.type)
            nullable = "" if f.required else ", nullable=True"
            default = f", default={f.default}" if f.default is not None else ""
            unique = ", unique=True" if f.unique else ""
            index = ", index=True" if f.indexed else ""
            lines.append(
                f"    {f.name}: {f.type} = Column({col_type}{nullable}{default}{unique}{index})",
            )
        if spec.audit_fields:
            for line in audit.strip("\n").split("\n"):
                lines.append(line)
        if spec.soft_delete:
            lines.append(soft_del.rstrip("\n"))
        if spec.version_lock:
            lines.append(version.rstrip("\n"))
        lines.append("")

        self._write(f"models/{module}.py", "\n".join(lines))

    def _generate_repository(self, module: str, spec: EntitySpec) -> None:
        content = f"""from __future__ import annotations

from typing import Optional

from sqlalchemy.orm import Session

from models.{module} import {spec.name}


class {spec.name}Repository:
    def __init__(self, session: Session):
        self.session = session

    def get(self, entity_id: int) -> Optional[{spec.name}]:
        return self.session.query({spec.name}).filter({spec.name}.id == entity_id).first()

    def list(self, skip: int = 0, limit: int = 100) -> list[{spec.name}]:
        query = self.session.query({spec.name})
        return query.offset(skip).limit(limit).all()

    def create(self, entity: {spec.name}) -> {spec.name}:
        self.session.add(entity)
        self.session.flush()
        return entity

    def update(self, entity: {spec.name}) -> {spec.name}:
        self.session.merge(entity)
        self.session.flush()
        return entity

    def delete(self, entity: {spec.name}) -> None:
        self.session.delete(entity)
        self.session.flush()
"""
        self._write(f"repositories/{module}_repository.py", content)

    def _generate_service(self, module: str, spec: EntitySpec) -> None:
        content = f"""from __future__ import annotations

from typing import Optional

from sqlalchemy.orm import Session

from repositories.{module}_repository import {spec.name}Repository
from models.{module} import {spec.name}


class {spec.name}Service:
    def __init__(self, session: Session):
        self.repository = {spec.name}Repository(session)

    def get(self, entity_id: int) -> Optional[{spec.name}]:
        return self.repository.get(entity_id)

    def list(self, skip: int = 0, limit: int = 100) -> list[{spec.name}]:
        return self.repository.list(skip=skip, limit=limit)

    def create(self, data: dict) -> {spec.name}:
        entity = {spec.name}(**data)
        return self.repository.create(entity)

    def update(self, entity_id: int, data: dict) -> Optional[{spec.name}]:
        entity = self.repository.get(entity_id)
        if not entity:
            return None
        for key, value in data.items():
            setattr(entity, key, value)
        return self.repository.update(entity)

    def delete(self, entity_id: int) -> bool:
        entity = self.repository.get(entity_id)
        if not entity:
            return False
        self.repository.delete(entity)
        return True
"""
        self._write(f"services/{module}_service.py", content)

    def _generate_dto(self, module: str, spec: EntitySpec, fields: list[EntityField]) -> None:
        field_lines = []
        for f in fields:
            req = "" if f.required else " | None = None"
            desc = f"  # {f.description}" if f.description else ""
            field_lines.append(f"    {f.name}: {f.type}{req}{desc}")

        content = f"""from __future__ import annotations

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict


class {spec.name}Create(BaseModel):
{chr(10).join(field_lines)}


class {spec.name}Update(BaseModel):
{chr(10).join(f"    {f.name}: Optional[{f.type}] = None" for f in fields)}


class {spec.name}Response(BaseModel):
    id: int
    created_at: datetime
    updated_at: datetime
    version: int

    model_config = ConfigDict(from_attributes=True)
"""
        self._write(f"dtos/{module}_dto.py", content)

    def _generate_rest_api(self, module: str, spec: EntitySpec) -> None:
        content = f"""from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query

from dtos.{module}_dto import {spec.name}Create, {spec.name}Update, {spec.name}Response
from services.{module}_service import {spec.name}Service

router = APIRouter(prefix="/{module}s", tags=["{spec.name}"])


def get_service() -> {spec.name}Service:
    from app.database import SessionLocal
    session = SessionLocal()
    return {spec.name}Service(session)


@router.get("/", response_model=List[{spec.name}Response])
def list_{module}s(skip: int = Query(0, ge=0), limit: int = Query(100, ge=1, le=1000)):
    service = get_service()
    return service.list(skip=skip, limit=limit)


@router.get("/{{entity_id}}", response_model={spec.name}Response)
def get_{module}(entity_id: int):
    service = get_service()
    entity = service.get(entity_id)
    if not entity:
        raise HTTPException(status_code=404, detail="{spec.name} not found")
    return entity


@router.post("/", response_model={spec.name}Response, status_code=201)
def create_{module}(data: {spec.name}Create):
    service = get_service()
    return service.create(data.model_dump())


@router.put("/{{entity_id}}", response_model={spec.name}Response)
def update_{module}(entity_id: int, data: {spec.name}Update):
    service = get_service()
    entity = service.update(entity_id, data.model_dump(exclude_none=True))
    if not entity:
        raise HTTPException(status_code=404, detail="{spec.name} not found")
    return entity


@router.delete("/{{entity_id}}", status_code=204, response_model=None)
def delete_{module}(entity_id: int):
    service = get_service()
    if not service.delete(entity_id):
        raise HTTPException(status_code=404, detail="{spec.name} not found")
"""
        self._write(f"routes/{module}.py", content)

    def _map_type(self, type_str: str) -> str:
        mapping = {
            "str": "String",
            "int": "Integer",
            "float": "Float",
            "bool": "Boolean",
            "datetime": "DateTime",
            "dict": "Text",
            "list": "Text",
        }
        return mapping.get(type_str, "String")
