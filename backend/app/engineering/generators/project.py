from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.engineering.generators.base import BaseGenerator, GenerateResult


@dataclass
class ProjectSpec:
    name: str
    version: str = "0.1.0"
    description: str = ""
    python_version: str = ">=3.11"
    package_name: str | None = None
    author: str = "GULA Engineering"
    license: str = "Proprietary"
    dependencies: list[str] = field(default_factory=list)
    dev_dependencies: list[str] = field(default_factory=list)


class ProjectGenerator(BaseGenerator):
    def generate(self, **kwargs: Any) -> GenerateResult:
        spec = kwargs.get("spec", kwargs.get("project_spec"))
        if isinstance(spec, dict):
            spec = ProjectSpec(**spec)
        if spec is None:
            spec = ProjectSpec(name=kwargs.get("name", "unnamed"))

        pkg = spec.package_name or spec.name.replace("-", "_").replace(".", "_")

        self._write(
            "pyproject.toml",
            f"""[build-system]
requires = ["setuptools>=80", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "{spec.name}"
version = "{spec.version}"
description = "{spec.description}"
requires-python = "{spec.python_version}"
license = {{ text = "{spec.license}" }}

dependencies = {spec.dependencies}

[project.optional-dependencies]
dev = {spec.dev_dependencies}

[tool.ruff]
target-version = "py311"
line-length = 100
fix = true

[tool.ruff.lint]
select = ["E", "W", "F", "I", "N", "UP", "B", "SIM", "C4", "PIE", "RET", "T20", "RUF", "Q"]
ignore = ["E501"]

[tool.mypy]
strict = true
python_version = "3.11"

[tool.pytest.ini_options]
minversion = "8.0"
testpaths = ["tests"]
asyncio_mode = "auto"
""",
        )

        src_dir = self._ensure_dir(f"src/{pkg}")
        (src_dir / "__init__.py").touch()

        self._ensure_dir("tests")
        (self.target_dir / "tests" / "__init__.py").touch()

        self._write(
            "tests/conftest.py",
            '"""Shared test fixtures."""\nimport pytest\n',
        )

        self._write(
            "README.md",
            f"# {spec.name}\n\n{spec.description}\n",
        )

        self._write(
            ".gitignore",
            """__pycache__/
*.py[cod]
*.egg-info/
dist/
build/
.venv/
.env
""",
        )

        return self._result
