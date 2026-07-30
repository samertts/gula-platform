from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.engineering.generators.base import BaseGenerator, GenerateResult


@dataclass
class PluginSpec:
    name: str
    description: str = ""
    version: str = "0.1.0"
    author: str = "GULA Engineering"
    hooks: list[str] = field(default_factory=lambda: ["on_startup", "on_shutdown", "on_request"])
    dependencies: list[str] = field(default_factory=list)


class PluginGenerator(BaseGenerator):
    def generate(self, **kwargs: Any) -> GenerateResult:
        spec = kwargs.get("spec", kwargs.get("plugin"))
        if isinstance(spec, dict):
            spec = PluginSpec(**spec)
        if spec is None:
            spec = PluginSpec(name=kwargs.get("name", "unnamed-plugin"))

        pkg = spec.name.lower().replace("-", "_").replace(" ", "_")
        p_cap = spec.name[0].upper() + spec.name[1:]

        self._ensure_dir(pkg)
        (self.target_dir / pkg / "__init__.py").touch()

        self._write(
            f"{pkg}/plugin.py",
            f"""from __future__ import annotations

from typing import Any


class {p_cap}Plugin:
    \"\"\"Plugin: {spec.description}\"\"\"

    def __init__(self, config: dict[str, Any] | None = None) -> None:
        self.config = config or {{}}
        self._initialized = False

    @property
    def name(self) -> str:
        return "{spec.name}"

    @property
    def version(self) -> str:
        return "{spec.version}"

    async def on_startup(self) -> None:
        self._initialized = True

    async def on_shutdown(self) -> None:
        self._initialized = False

    async def on_request(self, scope: dict, receive: Any, send: Any) -> None:
        pass

    async def execute(self, action: str, **kwargs: Any) -> Any:
        return None
""",
        )

        hooks_code = "\n".join(f"    async def {hook}(self) -> None: pass" for hook in spec.hooks)
        self._write(
            f"{pkg}/hooks.py",
            f"""from __future__ import annotations

from abc import ABC, abstractmethod


class {p_cap}Hook(ABC):
    @abstractmethod
    async def execute(self) -> None:
        ...

    {hooks_code.replace(chr(10), chr(10) + "    ")}
""",
        )

        self._write(
            f"{pkg}/config.py",
            f"""from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class {p_cap}Config:
    enabled: bool = True
    settings: dict = field(default_factory=dict)
""",
        )

        self._write(
            f"{pkg}/pyproject.toml",
            f"""[build-system]
requires = ["setuptools>=80", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "{spec.name}"
version = "{spec.version}"
description = "{spec.description}"
requires-python = ">=3.11"
dependencies = {spec.dependencies}
""",
        )

        self._write(
            "README.md",
            f"""# {spec.name}

{spec.description}

## Hooks

{chr(10).join(f"- `{h}`" for h in spec.hooks)}
""",
        )

        return self._result
