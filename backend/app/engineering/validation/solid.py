from __future__ import annotations

import ast
from dataclasses import dataclass
from pathlib import Path


@dataclass
class SOLIDIssue:
    file: str
    line: int
    principle: str
    message: str
    severity: str = "warning"


class SOLIDValidator:
    def __init__(self, project_root: Path | str):
        self.project_root = Path(project_root)
        self.issues: list[SOLIDIssue] = []

    def validate(self) -> list[SOLIDIssue]:
        self.issues = []
        for py_file in self.project_root.rglob("*.py"):
            if "tests" in py_file.parts or "__pycache__" in py_file.parts:
                continue
            self._check_file(py_file)
        return self.issues

    def _check_file(self, file_path: Path) -> None:
        try:
            tree = ast.parse(file_path.read_text())
        except SyntaxError:
            return
        classes = [n for n in ast.walk(tree) if isinstance(n, ast.ClassDef)]
        for cls in classes:
            self._check_single_responsibility(file_path, cls)
            self._check_open_closed(file_path, cls)
            self._check_liskov(file_path, cls)
            self._check_interface_segregation(file_path, cls)
            self._check_dependency_inversion(file_path, cls)

    def _check_single_responsibility(self, file: Path, cls: ast.ClassDef) -> None:
        methods = [n for n in cls.body if isinstance(n, ast.FunctionDef)]
        if len(methods) > 15:
            self.issues.append(
                SOLIDIssue(
                    file=str(file),
                    line=cls.lineno,
                    principle="SRP",
                    message=f"Class '{cls.name}' has {len(methods)} methods — consider splitting",
                    severity="warning",
                )
            )

    def _check_open_closed(self, file: Path, cls: ast.ClassDef) -> None:
        for node in cls.body:
            if (
                isinstance(node, ast.FunctionDef)
                and node.name.startswith("__")
                and "type" in node.name.lower()
            ):
                for child in ast.walk(node):
                    if isinstance(child, ast.If):
                        for if_node in ast.walk(child):
                            if isinstance(if_node, ast.Compare):
                                self.issues.append(
                                    SOLIDIssue(
                                        file=str(file),
                                        line=if_node.lineno,
                                        principle="OCP",
                                        message=f"Type check in '{cls.name}.{node.name}' — violates Open/Closed",
                                        severity="warning",
                                    )
                                )

    def _check_liskov(self, file: Path, cls: ast.ClassDef) -> None:
        for node in cls.body:
            if isinstance(node, ast.FunctionDef):
                if any(
                    isinstance(n, ast.Raise) and "NotImplementedError" in ast.dump(n)
                    for n in ast.walk(node)
                ):
                    self.issues.append(
                        SOLIDIssue(
                            file=str(file),
                            line=node.lineno,
                            principle="LSP",
                            message=f"'{cls.name}.{node.name}' raises NotImplementedError — may violate Liskov",
                            severity="info",
                        )
                    )

    def _check_interface_segregation(self, file: Path, cls: ast.ClassDef) -> None:
        for node in cls.body:
            if isinstance(node, ast.FunctionDef) and any(
                isinstance(n, ast.Raise) and "raise" in ast.dump(n)
                for n in ast.walk(node)
                if isinstance(n, ast.Raise)
            ):
                pass  # Too noisy to flag every raise

    def _check_dependency_inversion(self, file: Path, cls: ast.ClassDef) -> None:
        for node in cls.body:
            if isinstance(node, ast.FunctionDef):
                for child in ast.walk(node):
                    if isinstance(child, ast.Call) and isinstance(child.func, ast.Attribute):
                        if "Session" in ast.dump(child) or "Connection" in ast.dump(child):
                            self.issues.append(
                                SOLIDIssue(
                                    file=str(file),
                                    line=child.lineno,
                                    principle="DIP",
                                    message=f"Direct DB dependency in '{cls.name}.{node.name}' — inject abstraction",
                                    severity="warning",
                                )
                            )
