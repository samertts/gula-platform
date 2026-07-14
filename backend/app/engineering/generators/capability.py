from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from backend.app.engineering.generators.base import BaseGenerator, GenerateResult


@dataclass
class EntityField:
    name: str
    type: str = "str"
    required: bool = True
    indexed: bool = False
    unique: bool = False
    default: str | None = None


@dataclass
class CapabilitySpec:
    name: str
    description: str = ""
    domain: str = "core"
    layer: str = "application"
    owner: str = "platform-team"
    entities: list[EntityField] | None = None
    commands: list[str] = field(default_factory=list)
    events: list[str] = field(default_factory=list)
    queries: list[str] = field(default_factory=list)
    policies: list[str] = field(default_factory=list)
    permissions: list[str] = field(default_factory=list)
    dependencies: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    version: str = "1.0.0"
    with_api: bool = True
    with_tests: bool = True
    with_adr: bool = True
    with_docs: bool = True
    with_migration: bool = False
    with_docker: bool = False
    with_ci: bool = False
    with_sbom: bool = True


_ENTITY_TPL = '''from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
from uuid import uuid4


@dataclass
class {entity}:
    id: str = field(default_factory=lambda: str(uuid4()))
{fields}
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
'''

_DTO_TPL = '''from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class {dto}CreateRequest:
{create_fields}


@dataclass
class {dto}UpdateRequest:
{update_fields}


@dataclass
class {dto}Response:
{response_fields}
'''

_REPOSITORY_TPL = '''from __future__ import annotations

from typing import Optional


class {repo}Repository:
    async def get(self, id: str) -> Optional[{entity_name}]:
        raise NotImplementedError

    async def list(self, skip: int = 0, limit: int = 100) -> list[{entity_name}]:
        raise NotImplementedError

    async def create(self, entity: {entity_name}) -> {entity_name}:
        raise NotImplementedError

    async def update(self, entity: {entity_name}) -> {entity_name}:
        raise NotImplementedError

    async def delete(self, id: str) -> bool:
        raise NotImplementedError

    async def count(self) -> int:
        raise NotImplementedError
'''

_REPOSITORY_IMPL_TPL = '''from __future__ import annotations

from typing import Optional

from {module_path}.domain.entities import {entity_name}
from {module_path}.domain.repository import {repo}Repository


class SQLAlchemy{repo}Repository({repo}Repository):
    def __init__(self, session_factory):
        self._session_factory = session_factory

    async def get(self, id: str) -> Optional[{entity_name}]:
        async with self._session_factory() as session:
            return await session.get({entity_name}, id)

    async def list(self, skip: int = 0, limit: int = 100) -> list[{entity_name}]:
        async with self._session_factory() as session:
            result = await session.execute(
                select({entity_name}).offset(skip).limit(limit)
            )
            return list(result.scalars().all())

    async def create(self, entity: {entity_name}) -> {entity_name}:
        async with self._session_factory() as session:
            session.add(entity)
            await session.commit()
            return entity

    async def update(self, entity: {entity_name}) -> {entity_name}:
        async with self._session_factory() as session:
            session.add(entity)
            await session.commit()
            return entity

    async def delete(self, id: str) -> bool:
        async with self._session_factory() as session:
            entity = await session.get({entity_name}, id)
            if not entity:
                return False
            await session.delete(entity)
            await session.commit()
            return True

    async def count(self) -> int:
        async with self._session_factory() as session:
            result = await session.execute(select({entity_name}))
            return len(result.scalars().all())
'''

_SERVICE_TPL = '''from __future__ import annotations

from typing import Optional


class {service}Service:
    def __init__(self, repository: {repo}Repository):
        self._repository = repository

    async def get(self, id: str) -> Optional[{entity_name}]:
        return await self._repository.get(id)

    async def list(self, skip: int = 0, limit: int = 100) -> list[{entity_name}]:
        return await self._repository.list(skip=skip, limit=limit)

    async def create(self, data: {entity_name}) -> {entity_name}:
        return await self._repository.create(data)

    async def update(self, data: {entity_name}) -> {entity_name}:
        return await self._repository.update(data)

    async def delete(self, id: str) -> bool:
        return await self._repository.delete(id)
'''

_ROUTES_TPL = '''from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends

from backend.app.security.dependencies import get_current_user, require_permission

router = APIRouter(prefix="/{prefix}", tags=["{tag}"])


@router.get("/")
async def list_{prefix}(
    skip: int = 0,
    limit: int = 100,
    current_user: Any = Depends(get_current_user),
) -> dict:
    return {{"items": [], "total": 0, "skip": skip, "limit": limit}}


@router.get("/{{id}}")
async def get_{prefix}(
    id: str,
    current_user: Any = Depends(get_current_user),
) -> dict:
    return {{"id": id}}


@router.post("/")
async def create_{prefix}(
    data: dict,
    current_user: Any = Depends(get_current_user),
) -> dict:
    return {{"success": True, "id": ""}}


@router.put("/{{id}}")
async def update_{prefix}(
    id: str,
    data: dict,
    current_user: Any = Depends(get_current_user),
) -> dict:
    return {{"success": True}}


@router.delete("/{{id}}")
async def delete_{prefix}(
    id: str,
    current_user: Any = Depends(get_current_user),
) -> dict:
    return {{"success": True}}
'''

_HEALTH_TPL = '''from __future__ import annotations

from fastapi import APIRouter

router = APIRouter(prefix="/{prefix}/health", tags=["health"])


@router.get("/")
async def health_check() -> dict:
    return {{"status": "ok", "capability": "{cap_name}", "version": "{version}"}}


@router.get("/ready")
async def readiness() -> dict:
    return {{"ready": True, "capability": "{cap_name}"}}
'''

_POLICIES_TPL = '''from __future__ import annotations


class {cap}Policy:
    def __init__(self):
        self._rules: list[dict] = []

    def evaluate(self, context: dict) -> list[str]:
        violations = []
        for rule in self._rules:
            if not rule.get("condition", lambda c: True)(context):
                violations.append(rule.get("message", "Policy violation"))
        return violations

    def add_rule(self, condition, message: str):
        self._rules.append({{"condition": condition, "message": message}})
'''

_PERMISSIONS_TPL = '''from __future__ import annotations

from enum import Enum


class {cap}Permission(Enum):
{permissions}

    def describe(self) -> str:
        descriptions = {{{desc_map}}}
        return descriptions.get(self, self.value)
'''

_UNIT_TEST_TPL = '''from __future__ import annotations

import pytest


class Test{cap}Capability:
    @pytest.fixture
    def capability(self):
        from {module_path}.capability import {cap}Capability
        return {cap}Capability()

    @pytest.mark.asyncio
    async def test_execute(self, capability):
        result = await capability.execute({{}})
        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_validate(self, capability):
        result = await capability.validate({{}})
        assert result is True
'''

_INTEGRATION_TEST_TPL = '''from __future__ import annotations

import pytest
from fastapi.testclient import TestClient


class Test{cap}API:
    @pytest.mark.asyncio
    async def test_health(self, client: TestClient):
        response = client.get("/{prefix}/health/")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
'''

_ADR_TPL = '''# ADR-{seq:04d}: {cap} Capability

- **Status:** proposed
- **Date:** {date}
- **Domain:** {domain}
- **Layer:** {layer}
- **Owner:** {owner}

## Context

{description}

## Decision

Build the {cap_name} capability as a reusable platform capability.

## Consequences

- Enables consistent {description_lower} across all platform modules
- Adds 1 new capability to the Capability Registry
- Requires integration with Kernel lifecycle management

## Compliance

- [ ] Registered in CapabilityRegistry
- [ ] All quality gates pass
- [ ] OpenAPI specification generated
- [ ] ADR documented
- [ ] Tests written and passing
'''

_README_TPL = '''# {cap} Capability

**Domain:** {domain} | **Layer:** {layer} | **Version:** {version}

## Description

{description}

## Dependencies

{deps}

## API

{api_docs}

## Events

{events_docs}

## Commands

{commands_docs}

## Queries

{queries_docs}

## Quality

- Quality Score: 0.0
- Security Score: 0.0
- Performance Score: 0.0
- Reuse Score: 1.0

## License

Proprietary - GULA Platform
'''

_SBOM_TPL = '''<?xml version="1.0" encoding="UTF-8"?>
<bom xmlns="http://cyclonedx.org/schema/bom/1.5" version="1">
    <metadata>
        <component type="library">
            <name>{cap}</name>
            <version>{version}</version>
            <description>{description}</description>
        </component>
    </metadata>
    <components>
        <component type="library">
            <name>capability-framework</name>
            <version>1.0.0</version>
        </component>
    </components>
</bom>
'''


class CapabilityGenerator(BaseGenerator):
    def __init__(self, target_dir: str | None = None):
        super().__init__(target_dir)
        self._seq = 0

    def generate(self, **kwargs: Any) -> GenerateResult:
        spec = kwargs.get("spec", kwargs.get("capability"))
        if isinstance(spec, dict):
            spec = CapabilitySpec(**spec)
        if spec is None:
            spec = CapabilitySpec(name=kwargs.get("name", "unnamed"))

        cap = spec.name.lower().replace(" ", "_")
        cap_cap = spec.name[0].upper() + spec.name[1:]
        module_path = f"backend.app.capabilities.{cap}"
        prefix = cap.replace("_", "-")

        self.target_dir.mkdir(parents=True, exist_ok=True)

        self._generate_init(cap, cap_cap, spec)
        self._generate_contract(cap, cap_cap, spec)
        self._generate_capability(cap, cap_cap, spec, module_path)

        if spec.entities:
            self._generate_domain(cap, cap_cap, spec)
            self._generate_repository(cap, cap_cap, spec, module_path)
            self._generate_service(cap, cap_cap, spec, module_path)
            self._generate_dto(cap, cap_cap, spec)

        if spec.commands:
            self._generate_commands(cap, cap_cap, spec)
        if spec.events:
            self._generate_events(cap, cap_cap, spec)
        if spec.queries:
            self._generate_queries(cap, cap_cap, spec)
        if spec.policies:
            self._generate_policies(cap, cap_cap, spec)
        if spec.permissions:
            self._generate_permissions(cap, cap_cap, spec)

        if spec.with_api:
            self._generate_routes(cap, cap_cap, spec, prefix)

        self._generate_health(cap, cap_cap, prefix, spec)

        if spec.with_tests:
            self._generate_tests(cap, cap_cap, spec, module_path, prefix)
        if spec.with_adr:
            self._generate_adr(cap, cap_cap, spec)
        if spec.with_docs:
            self._generate_readme(cap, cap_cap, spec)
        if spec.with_sbom:
            self._generate_sbom(cap, spec)

        self._generate_capability_descriptor(cap, cap_cap, spec, prefix, module_path)

        return self._result

    def _generate_init(self, cap: str, cap_cap: str, spec: CapabilitySpec) -> None:
        self._write(
            f"{cap}/__init__.py",
            f'''from __future__ import annotations

"""{
    spec.name
} Capability: {spec.description}

Domain: {spec.domain}
Layer: {spec.layer}
Version: {spec.version}
"""

from {cap}.capability import {cap_cap}Capability

__all__ = ["{cap_cap}Capability"]
''',
        )

    def _generate_contract(self, cap: str, cap_cap: str, spec: CapabilitySpec) -> None:
        self._write(
            f"{cap}/contract.py",
            _CONTRACT_TPL.format(
                cap=cap_cap,
                entities=spec.entities or [],
                commands=spec.commands,
                events=spec.events,
                queries=spec.queries,
            ),
        )

    def _generate_capability(
        self, cap: str, cap_cap: str, spec: CapabilitySpec, module_path: str
    ) -> None:
        deps = "\n".join(f"        # Depends on: {d}" for d in spec.dependencies)
        self._write(
            f"{cap}/capability.py",
            f'''from __future__ import annotations

import logging
from typing import Any

from backend.app.kernel.integration import get_kernel

logger = logging.getLogger("gula.capability.{cap}")


class {cap_cap}Capability:
    """{spec.name} capability in the {spec.domain} domain ({spec.layer} layer).

    {spec.description}
    """

    def __init__(self) -> None:
        self._initialized = False
        self._kernel = None

    async def initialize(self) -> None:
        if self._initialized:
            return
        self._kernel = get_kernel()
        logger.info("{cap_cap} capability initializing")
{deps}
        self._initialized = True
        logger.info("{cap_cap} capability initialized")

    async def execute(self, input_data: Any) -> dict:
        if not self._initialized:
            await self.initialize()
        return {{"success": True, "capability": "{cap}"}}

    async def validate(self, input_data: Any) -> bool:
        return True

    async def on_activate(self) -> None:
        logger.info("{cap_cap} capability activated")

    async def on_deactivate(self) -> None:
        logger.info("{cap_cap} capability deactivated")

    async def health(self) -> dict:
        return {{
            "status": "ok",
            "capability": "{cap}",
            "version": "{spec.version}",
            "initialized": self._initialized,
        }}
''',
        )

    def _generate_domain(
        self, cap: str, cap_cap: str, spec: CapabilitySpec
    ) -> None:
        fields_str = "\n".join(
            f"    {f.name}: {f.type}{'' if f.required else ' = None'}"
            for f in (spec.entities or [])
        )
        entity_name = cap_cap
        self._write(
            f"{cap}/domain/__init__.py",
            f'''from __future__ import annotations

"""Domain layer for {spec.name} capability."""
''',
        )
        self._write(
            f"{cap}/domain/entities.py",
            _ENTITY_TPL.format(
                entity=entity_name,
                fields=fields_str,
            ),
        )
        self._write(
            f"{cap}/domain/repository.py",
            _REPOSITORY_TPL.format(repo=cap_cap, entity_name=entity_name),
        )
        self._write(
            f"{cap}/infrastructure/__init__.py",
            f'''from __future__ import annotations

"""Infrastructure layer for {spec.name} capability."""
''',
        )
        self._write(
            f"{cap}/infrastructure/repository.py",
            _REPOSITORY_IMPL_TPL.format(
                module_path=f"backend.app.capabilities.{cap}",
                entity_name=entity_name,
                repo=cap_cap,
            ),
        )

    def _generate_repository(
        self, cap: str, cap_cap: str, spec: CapabilitySpec, module_path: str
    ) -> None:
        self._write(
            f"{cap}/application/__init__.py",
            f'''from __future__ import annotations

"""Application layer for {spec.name} capability."""
''',
        )

    def _generate_service(
        self, cap: str, cap_cap: str, spec: CapabilitySpec, module_path: str
    ) -> None:
        entity_name = cap_cap
        self._write(
            f"{cap}/application/service.py",
            _SERVICE_TPL.format(
                service=cap_cap,
                repo=cap_cap,
                entity_name=entity_name,
            ),
        )

    def _generate_dto(self, cap: str, cap_cap: str, spec: CapabilitySpec) -> None:
        fields = (spec.entities or [])
        create_fields = "\n".join(
            f"    {f.name}: {f.type}{'' if f.required else ' = None'}"
            for f in fields
        ) or "    pass"
        update_fields = "\n".join(
            f"    {f.name}: {f.type} = None"
            for f in fields
        ) or "    pass"
        response_fields = "\n".join(
            f"    {f.name}: {f.type}"
            for f in fields
        ) or "    pass"
        self._write(
            f"{cap}/dto.py",
            _DTO_TPL.format(
                dto=cap_cap,
                create_fields=create_fields,
                update_fields=update_fields,
                response_fields=response_fields,
            ),
        )

    def _generate_commands(self, cap: str, cap_cap: str, spec: CapabilitySpec) -> None:
        cmds = []
        for cmd_name in spec.commands:
            cmd_cap = cmd_name[0].upper() + cmd_name[1:]
            cmds.append((cmd_name, cmd_cap))
            self._write(
                f"{cap}/commands/{cmd_name}.py",
                f'''from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class {cmd_cap}Command:
    """{cmd_name} command for {spec.name} capability."""
    command_id: str = ""
    timestamp: datetime = field(default_factory=datetime.utcnow)
    data: dict = field(default_factory=dict)
''',
            )
        cmd_imports = "\n".join(f"from .{c} import {c_cap}Command" for c, c_cap in cmds)
        self._write(
            f"{cap}/commands/__init__.py",
            f'''from __future__ import annotations

"""Command definitions for {spec.name} capability."""

{cmd_imports}
''',
        )

    def _generate_events(self, cap: str, cap_cap: str, spec: CapabilitySpec) -> None:
        evts = []
        for evt_name in spec.events:
            evt_cap = evt_name[0].upper() + evt_name[1:]
            evts.append((evt_name, evt_cap))
            self._write(
                f"{cap}/events/{evt_name}.py",
                f'''from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class {evt_cap}Event:
    """{evt_name} event for {spec.name} capability."""
    event_id: str = ""
    occurred_at: datetime = field(default_factory=datetime.utcnow)
    data: dict = field(default_factory=dict)
    version: int = 1
''',
            )
        evt_imports = "\n".join(f"from .{e} import {e_cap}Event" for e, e_cap in evts)
        self._write(
            f"{cap}/events/__init__.py",
            f'''from __future__ import annotations

"""Event definitions for {spec.name} capability."""

{evt_imports}
''',
        )

    def _generate_queries(self, cap: str, cap_cap: str, spec: CapabilitySpec) -> None:
        qrs = []
        for qry_name in spec.queries:
            qry_cap = qry_name[0].upper() + qry_name[1:]
            qrs.append((qry_name, qry_cap))
            self._write(
                f"{cap}/queries/{qry_name}.py",
                f'''from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class {qry_cap}Query:
    """{qry_name} query for {spec.name} capability."""
    filters: dict = field(default_factory=dict)
    skip: int = 0
    limit: int = 100
''',
            )
        qry_imports = "\n".join(f"from .{q} import {q_cap}Query" for q, q_cap in qrs)
        self._write(
            f"{cap}/queries/__init__.py",
            f'''from __future__ import annotations

"""Query definitions for {spec.name} capability."""

{qry_imports}
''',
        )

    def _generate_policies(self, cap: str, cap_cap: str, spec: CapabilitySpec) -> None:
        self._write(
            f"{cap}/policies.py",
            _POLICIES_TPL.format(cap=cap_cap),
        )

    def _generate_permissions(self, cap: str, cap_cap: str, spec: CapabilitySpec) -> None:
        perms = "\n".join(
            f"    {p.upper()} = \"{cap.lower()}:{p.lower()}\""
            for p in spec.permissions
        )
        desc_items = ",\n        ".join(
            f"        \"{cap.lower()}:{p.lower()}\": \"{p.replace('_', ' ').title()}\""
            for p in spec.permissions
        )
        self._write(
            f"{cap}/permissions.py",
            _PERMISSIONS_TPL.format(
                cap=cap_cap,
                permissions=perms,
                desc_map=desc_items,
            ),
        )

    def _generate_routes(self, cap: str, cap_cap: str, spec: CapabilitySpec, prefix: str) -> None:
        self._write(
            f"{cap}/routes.py",
            _ROUTES_TPL.format(prefix=prefix, tag=spec.name.replace("_", " ").title()),
        )

    def _generate_health(self, cap: str, cap_cap: str, prefix: str, spec: CapabilitySpec) -> None:
        self._write(
            f"{cap}/health.py",
            _HEALTH_TPL.format(cap_name=cap, prefix=prefix, version=spec.version),
        )

    def _generate_tests(
        self, cap: str, cap_cap: str, spec: CapabilitySpec, module_path: str, prefix: str
    ) -> None:
        self._write(
            f"{cap}/tests/__init__.py",
            "",
        )
        self._write(
            f"{cap}/tests/test_unit.py",
            _UNIT_TEST_TPL.format(cap=cap_cap, module_path=module_path),
        )
        self._write(
            f"{cap}/tests/test_integration.py",
            _INTEGRATION_TEST_TPL.format(cap=cap_cap, prefix=prefix),
        )

    def _generate_adr(self, cap: str, cap_cap: str, spec: CapabilitySpec) -> None:
        self._write(
            f"{cap}/adr.md",
            _ADR_TPL.format(
                seq=self._seq,
                cap=cap_cap,
                date=datetime.now().strftime("%Y-%m-%d"),
                domain=spec.domain,
                layer=spec.layer,
                owner=spec.owner,
                description=spec.description,
                description_lower=spec.description.lower() if spec.description else "",
                cap_name=spec.name,
            ),
        )
        self._seq += 1

    def _generate_readme(self, cap: str, cap_cap: str, spec: CapabilitySpec) -> None:
        deps = "\n".join(f"- {d}" for d in spec.dependencies) or "None"
        api_docs = "\n".join(f"- `/{cap.replace('_', '-')}/` — REST API" if spec.with_api else "None")
        events_docs = "\n".join(f"- `{e}`" for e in spec.events) or "None"
        commands_docs = "\n".join(f"- `{c}`" for c in spec.commands) or "None"
        queries_docs = "\n".join(f"- `{q}`" for q in spec.queries) or "None"
        self._write(
            f"{cap}/README.md",
            _README_TPL.format(
                cap=spec.name,
                domain=spec.domain,
                layer=spec.layer,
                version=spec.version,
                description=spec.description,
                deps=deps,
                api_docs=api_docs,
                events_docs=events_docs,
                commands_docs=commands_docs,
                queries_docs=queries_docs,
            ),
        )

    def _generate_sbom(self, cap: str, spec: CapabilitySpec) -> None:
        self._write(
            f"{cap}/sbom.xml",
            _SBOM_TPL.format(
                cap=cap,
                version=spec.version,
                description=spec.description,
            ),
        )

    def _generate_capability_descriptor(
        self, cap: str, cap_cap: str, spec: CapabilitySpec, prefix: str, module_path: str
    ) -> None:
        events = "\n".join(
            f'        {{"name": "{e}", "version": 1, "description": "", "type": "domain"}},'
            for e in spec.events
        )
        commands = "\n".join(
            f'        {{"name": "{c}", "description": ""}},'
            for c in spec.commands
        )
        queries = "\n".join(
            f'        {{"name": "{q}", "description": ""}},'
            for q in spec.queries
        )
        entities = "\n".join(
            f'        {{"name": "{e.name}", "description": "", "fields": []}},'
            for e in (spec.entities or [])
        )
        deps = "\n".join(f'        "{d}",' for d in spec.dependencies)
        self._write(
            f"{cap}/capability.json",
            f"""{{
    "capability_id": "{str(uuid.uuid4())}",
    "name": "{spec.name}",
    "version": "{spec.version}",
    "description": "{spec.description}",
    "owner": "{spec.owner}",
    "domain": "{spec.domain}",
    "layer": "{spec.layer}",
    "status": "active",
    "dependencies": [{deps}
    ],
    "events": [{events}
    ],
    "commands": [{commands}
    ],
    "queries": [{queries}
    ],
    "entities": [{entities}
    ],
    "policies": {str([p for p in spec.policies])},
    "permissions": {str([p for p in spec.permissions])},
    "api_endpoints": [
        {{"path": "/{prefix}/", "method": "GET", "auth_required": true}},
        {{"path": "/{prefix}/{{id}}", "method": "GET", "auth_required": true}},
        {{"path": "/{prefix}/", "method": "POST", "auth_required": true}},
        {{"path": "/{prefix}/{{id}}", "method": "PUT", "auth_required": true}},
        {{"path": "/{prefix}/{{id}}", "method": "DELETE", "auth_required": true}},
        {{"path": "/{prefix}/health/", "method": "GET", "auth_required": false}}
    ],
    "required": false,
    "enabled": true,
    "tags": {str(spec.tags)},
    "module_path": "{module_path}",
    "health_endpoint": "/{prefix}/health/"
}}
""",
        )


_CONTRACT_TPL = '''from __future__ import annotations

"""Contracts for {cap} capability - input/output schemas."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class {cap}Input:
    action: str = "execute"
    data: dict = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class {cap}Output:
    success: bool = True
    data: dict = field(default_factory=dict)
    error: str | None = None
    timestamp: datetime = field(default_factory=datetime.utcnow)
'''
