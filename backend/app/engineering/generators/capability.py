from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from backend.app.engineering.generators.base import BaseGenerator, GenerateResult


@dataclass
class CapabilitySpec:
    name: str
    description: str = ""
    domain: str = "clinical"
    layer: str = "application"
    commands: list[str] = field(default_factory=list)
    events: list[str] = field(default_factory=list)
    queries: list[str] = field(default_factory=list)


class CapabilityGenerator(BaseGenerator):
    def generate(self, **kwargs: Any) -> GenerateResult:
        spec = kwargs.get("spec", kwargs.get("capability"))
        if isinstance(spec, dict):
            spec = CapabilitySpec(**spec)
        if spec is None:
            spec = CapabilitySpec(name=kwargs.get("name", "unnamed"))

        cap = spec.name.lower().replace(" ", "_")
        Cap = spec.name[0].upper() + spec.name[1:]

        self._ensure_dir(cap)
        (self.target_dir / cap / "__init__.py").touch()

        self._write(f"{cap}/__init__.py", f"""from __future__ import annotations

\"\"\"{spec.name} Capability: {spec.description}\"\"\"
""")

        self._write(f"{cap}/contract.py", f"""from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class {Cap}Input:
    pass


@dataclass
class {Cap}Output:
    success: bool = True
""")

        self._write(f"{cap}/capability.py", f"""from __future__ import annotations

from typing import Any


class {Cap}Capability:
    \"\"\"{spec.name} capability in the {spec.domain} domain ({spec.layer} layer).\"\"\"

    def __init__(self) -> None:
        pass

    async def execute(self, input_data: Any) -> Any:
        return {{"success": True}}

    async def validate(self, input_data: Any) -> bool:
        return True
""")

        if spec.commands:
            cmds = []
            for cmd_name in spec.commands:
                Cmd = cmd_name[0].upper() + cmd_name[1:]
                cmds.append(cmd_name)
                self._write(f"{cap}/commands/{cmd_name}.py", f"""from __future__ import annotations

from dataclasses import dataclass


@dataclass
class {Cmd}Command:
    pass
""")
            self._write(f"{cap}/commands/__init__.py", f"""from __future__ import annotations

from {".".join(f"{cap}.commands.{c}" for c in cmds)} import {", ".join(c[0].upper() + c[1:] for c in cmds)}Command
""")

        if spec.events:
            evts = []
            for evt_name in spec.events:
                Evt = evt_name[0].upper() + evt_name[1:]
                evts.append(evt_name)
                self._write(f"{cap}/events/{evt_name}.py", f"""from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass
class {Evt}Event:
    occurred_at: datetime = datetime.utcnow()
""")
            self._write(f"{cap}/events/__init__.py", f"""from __future__ import annotations

from {".".join(f"{cap}.events.{e}" for e in evts)} import {", ".join(e[0].upper() + e[1:] for e in evts)}Event
""")

        if spec.queries:
            qrs = []
            for qry_name in spec.queries:
                Qry = qry_name[0].upper() + qry_name[1:]
                qrs.append(qry_name)
                self._write(f"{cap}/queries/{qry_name}.py", f"""from __future__ import annotations

from dataclasses import dataclass


@dataclass
class {Qry}Query:
    pass
""")
            self._write(f"{cap}/queries/__init__.py", f"""from __future__ import annotations

from {".".join(f"{cap}.queries.{q}" for q in qrs)} import {", ".join(q[0].upper() + q[1:] for q in qrs)}Query
""")

        return self._result
