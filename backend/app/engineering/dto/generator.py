from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from backend.app.engineering.generators.base import BaseGenerator, GenerateResult


@dataclass
class DTOField:
    name: str
    type: str = "str"
    required: bool = True
    description: str = ""
    default: Any | None = None


@dataclass
class DTOSpec:
    name: str
    fields: list[DTOField] = field(default_factory=list)
    include_timestamps: bool = True
    include_id: bool = True
    generate_create: bool = True
    generate_update: bool = True
    generate_response: bool = True


class DTOGenerator(BaseGenerator):
    def generate(self, **kwargs: Any) -> GenerateResult:
        spec = kwargs.get("spec", kwargs.get("dto"))
        if isinstance(spec, dict):
            spec = DTOSpec(**spec)
        if spec is None:
            spec = DTOSpec(name=kwargs.get("name", "Entity"))

        module = spec.name.lower()
        Mod = spec.name[0].upper() + spec.name[1:]

        field_lines = []
        for f in spec.fields:
            opt = " | None = None" if not f.required else ""
            if f.default is not None and f.required:
                default = f" = {f.default!r}"
            elif f.default is not None:
                default = f" = {f.default!r}"
            else:
                default = ""
            desc = f"  # {f.description}" if f.description else ""
            field_lines.append(f"    {f.name}: {f.type}{opt}{default}{desc}")

        parts = []

        if spec.generate_create:
            parts.append(f"""class {Mod}Create(BaseModel):
{chr(10).join(field_lines)}
""")

        if spec.generate_update:
            update_lines = [f"    {f.name}: {f.type} | None = None" for f in spec.fields]
            parts.append(f"""class {Mod}Update(BaseModel):
{chr(10).join(update_lines)}
""")

        if spec.generate_response:
            resp_fields = []
            if spec.include_id:
                resp_fields.append("    id: int")
            resp_fields.extend(field_lines)
            if spec.include_timestamps:
                resp_fields.append("    created_at: datetime")
                resp_fields.append("    updated_at: datetime")
            parts.append(f"""class {Mod}Response(BaseModel):
{chr(10).join(resp_fields)}

    class Config:
        from_attributes = True
""")

        content = f'''"""DTOs for {Mod}."""
from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel

{chr(10).join(parts)}
'''
        self._write(f"dtos/{module}_dto.py", content)

        return self._result
