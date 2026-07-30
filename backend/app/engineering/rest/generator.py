from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.engineering.generators.base import BaseGenerator, GenerateResult


@dataclass
class RESTSpec:
    name: str
    prefix: str = ""
    version: str = "v1"
    tags: list[str] = field(default_factory=list)
    operations: list[str] = field(
        default_factory=lambda: ["list", "get", "create", "update", "delete"],
    )
    auth: bool = True
    pagination: bool = True


class RESTGenerator(BaseGenerator):
    def generate(self, **kwargs: Any) -> GenerateResult:
        spec = kwargs.get("spec", kwargs.get("rest"))
        if isinstance(spec, dict):
            spec = RESTSpec(**spec)
        if spec is None:
            spec = RESTSpec(name=kwargs.get("name", "resource"))

        module = spec.name.lower()
        mod = spec.name[0].upper() + spec.name[1:]
        prefix = spec.prefix or f"/api/{spec.version}/{module}s"
        tags = spec.tags or [mod]

        handlers = []
        if "list" in spec.operations:
            handlers.append(self._list_endpoint(module, mod, spec))
        if "get" in spec.operations:
            handlers.append(self._get_endpoint(module, mod))
        if "create" in spec.operations:
            handlers.append(self._create_endpoint(module, mod))
        if "update" in spec.operations:
            handlers.append(self._update_endpoint(module, mod))
        if "delete" in spec.operations:
            handlers.append(self._delete_endpoint(module, mod))

        content = f'''"""REST API for {mod}."""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query

router = APIRouter(prefix="{prefix}", tags={tags})

{chr(10).join(handlers)}
'''
        self._write(f"routes/{module}.py", content)

        self._write(
            "routes/__init__.py",
            f"""from __future__ import annotations

from .{module} import router as {module}_router
""",
        )

        return self._result

    def _list_endpoint(self, module: str, mod: str, spec: RESTSpec) -> str:
        pagination = (
            """
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
"""
            if spec.pagination
            else ""
        )
        return f'''@router.get("/")
async def list_{module}s(
    {pagination}):
    """List all {mod}s."""
    return {{"items": [], "total": 0}}


'''

    def _get_endpoint(self, module: str, mod: str) -> str:
        return f'''@router.get("/{{{module}_id}}")
async def get_{module}({module}_id: int):
    """Get a {mod} by ID."""
    raise HTTPException(status_code=404, detail="{mod} not found")


'''

    def _create_endpoint(self, module: str, mod: str) -> str:
        return f'''@router.post("/", status_code=201)
async def create_{module}(payload: dict[str, Any]):
    """Create a new {mod}."""
    return payload


'''

    def _update_endpoint(self, module: str, mod: str) -> str:
        return f'''@router.put("/{{{module}_id}}")
async def update_{module}({module}_id: int, payload: dict[str, Any]):
    """Update a {mod}."""
    raise HTTPException(status_code=404, detail="{mod} not found")


'''

    def _delete_endpoint(self, module: str, mod: str) -> str:
        return f'''@router.delete("/{{{module}_id}}", status_code=204)
async def delete_{module}({module}_id: int):
    """Delete a {mod}."""
    raise HTTPException(status_code=404, detail="{mod} not found")


'''
