from __future__ import annotations

import ast
from dataclasses import dataclass
from pathlib import Path


@dataclass
class CQRSIssue:
    file: str
    line: int
    pattern: str
    message: str
    severity: str = "warning"


class CQRSValidator:
    def __init__(self, project_root: Path | str):
        self.project_root = Path(project_root)
        self.issues: list[CQRSIssue] = []

    def validate(self) -> list[CQRSIssue]:
        self.issues = []
        for py_file in self.project_root.rglob("*.py"):
            if "test" in py_file.parts or "__pycache__" in py_file.parts:
                continue
            try:
                tree = ast.parse(py_file.read_text())
            except SyntaxError:
                continue
            self._check_command_query_separation(py_file, tree)
            self._check_command_return_type(py_file, tree)
            self._check_query_side_effects(py_file, tree)
            self._check_handler_structure(py_file, tree)
            self._check_bus_pattern(py_file, tree)
        return self.issues

    def _check_command_query_separation(self, file: Path, tree: ast.AST) -> None:
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                name = node.name
                if "Handler" in name:
                    for child in ast.walk(node):
                        if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)) and child.name in ("handle", "__call__") and "Command" in name and "Query" in name:
                            self.issues.append(
                                CQRSIssue(
                                    file=str(file.relative_to(self.project_root)),
                                    line=node.lineno,
                                    pattern="CQS",
                                    message=f"Handler '{name}' handles both commands and queries — CQRS requires separation",
                                ),
                            )

    def _check_command_return_type(self, file: Path, tree: ast.AST) -> None:
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef) and "Command" in node.name:
                for child in ast.walk(node):
                    if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        for decorator in child.decorator_list:
                            if hasattr(decorator, "attr") and "returns" in decorator.attr:
                                pass
                        returns = child.returns
                        if returns and child.name in ("handle", "__call__") and ("Response" in ast.dump(returns) or "Result" in ast.dump(returns)):
                            self.issues.append(
                                CQRSIssue(
                                    file=str(file.relative_to(self.project_root)),
                                    line=child.lineno,
                                    pattern="CMD",
                                    message=f"Command handler '{node.name}.{child.name}' returns data — commands should return void or success/failure",
                                ),
                            )

    def _check_query_side_effects(self, file: Path, tree: ast.AST) -> None:
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef) and "Query" in node.name:
                for child in ast.walk(node):
                    if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)) and child.name in ("handle", "__call__"):
                        has_session_commit = any(
                            "commit" in ast.dump(n)
                            for n in ast.walk(child)
                            if isinstance(n, ast.Call)
                        )
                        if has_session_commit:
                            self.issues.append(
                                CQRSIssue(
                                    file=str(file.relative_to(self.project_root)),
                                    line=child.lineno,
                                    pattern="QRS",
                                    message=f"Query handler '{node.name}.{child.name}' performs write operations — queries must be side-effect free",
                                ),
                            )

    def _check_handler_structure(self, file: Path, tree: ast.AST) -> None:
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef) and "Handler" in node.name:
                has_handle = any(
                    isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name == "handle"
                    for n in node.body
                )
                if not has_handle:
                    self.issues.append(
                        CQRSIssue(
                            file=str(file.relative_to(self.project_root)),
                            line=node.lineno,
                            pattern="HND",
                            message=f"Handler '{node.name}' should implement a 'handle' method",
                        ),
                    )

    def _check_bus_pattern(self, file: Path, tree: ast.AST) -> None:
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef) and "Bus" in node.name:
                has_dispatch = any(
                    isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
                    and n.name in ("dispatch", "ask", "send", "publish")
                    for n in node.body
                )
                if not has_dispatch:
                    self.issues.append(
                        CQRSIssue(
                            file=str(file.relative_to(self.project_root)),
                            line=node.lineno,
                            pattern="BUS",
                            message=f"Bus '{node.name}' should implement dispatch/ask methods",
                        ),
                    )
