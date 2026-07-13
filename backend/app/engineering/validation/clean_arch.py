from __future__ import annotations

import ast
from dataclasses import dataclass
from pathlib import Path


@dataclass
class ArchitectureIssue:
    file: str
    line: int
    message: str
    severity: str = "error"


class CleanArchitectureValidator:
    LAYERS = {
        "domain": {"rules": ["models", "domain", "entities"]},
        "application": {"rules": ["services", "use_cases", "dtos", "commands", "queries"]},
        "infrastructure": {"rules": ["repositories", "database", "external", "cache"]},
        "presentation": {"rules": ["routes", "api", "controllers", "middleware"]},
    }

    ALLOWED_IMPORTS = {
        "domain": ["domain", "shared"],
        "application": ["domain", "application", "shared"],
        "infrastructure": ["domain", "application", "infrastructure", "shared"],
        "presentation": ["application", "infrastructure", "presentation", "shared"],
    }

    def __init__(self, project_root: Path | str):
        self.project_root = Path(project_root)
        self.issues: list[ArchitectureIssue] = []

    def validate(self) -> list[ArchitectureIssue]:
        self.issues = []
        for py_file in self.project_root.rglob("*.py"):
            if "tests" in py_file.parts or "__pycache__" in py_file.parts:
                continue
            self._check_file(py_file)
        return self.issues

    def _check_file(self, file_path: Path) -> None:
        relative = file_path.relative_to(self.project_root)
        layer = self._detect_layer(relative)
        if layer is None:
            return
        try:
            tree = ast.parse(file_path.read_text())
        except SyntaxError:
            return
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                if node.module:
                    self._check_import(relative, layer, node.module, node.lineno)
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    self._check_import(relative, layer, alias.name, node.lineno)

    def _detect_layer(self, relative: Path) -> str | None:
        for layer_name, config in self.LAYERS.items():
            for rule in config["rules"]:
                if rule in relative.parts:
                    return layer_name
        return None

    def _check_import(self, file: Path, layer: str, imported: str, line: int) -> None:
        allowed = self.ALLOWED_IMPORTS.get(layer, [])
        imported_layer = self._detect_import_layer(imported)
        if imported_layer and imported_layer not in allowed:
            self.issues.append(
                ArchitectureIssue(
                    file=str(file),
                    line=line,
                    message=f"Layer violation: '{layer}' importing from '{imported_layer}' ({imported})",
                    severity="error",
                )
            )

    def _detect_import_layer(self, module: str) -> str | None:
        for layer_name, config in self.LAYERS.items():
            for rule in config["rules"]:
                if module.startswith(rule):
                    return layer_name
        return None
