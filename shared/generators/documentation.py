from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger("gula.generators.doc")


class DocumentationGenerator:
    def __init__(self, target_dir: str = "docs") -> None:
        self._target_dir = Path(target_dir)

    def generate_api_docs(self, routes: list[dict[str, Any]]) -> None:
        self._target_dir.mkdir(parents=True, exist_ok=True)
        lines = ["# API Documentation\n", "", "## Endpoints\n", ""]
        for route in routes:
            lines.append(f"### {route.get('method', 'GET')} `{route.get('path', '/')}`\n")
            if route.get("description"):
                lines.append(f"{route['description']}\n")
            lines.append("")
        path = self._target_dir / "api.md"
        path.write_text("\n".join(lines))
        logger.info("API documentation generated: %s", path)

    def generate_module_docs(self, modules: list[dict[str, Any]]) -> None:
        self._target_dir.mkdir(parents=True, exist_ok=True)
        lines = ["# Module Documentation\n", ""]
        for mod in modules:
            lines.append(f"- **{mod.get('name', 'unknown')}**: {mod.get('description', '')}")
        path = self._target_dir / "modules.md"
        path.write_text("\n".join(lines))
        logger.info("Module documentation generated: %s", path)


__all__ = ["DocumentationGenerator"]
