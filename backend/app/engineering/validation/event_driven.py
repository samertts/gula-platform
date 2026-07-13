from __future__ import annotations

import ast
from dataclasses import dataclass
from pathlib import Path


@dataclass
class EventDrivenIssue:
    file: str
    line: int
    pattern: str
    message: str
    severity: str = "warning"


class EventDrivenValidator:
    def __init__(self, project_root: Path | str):
        self.project_root = Path(project_root)
        self.issues: list[EventDrivenIssue] = []

    def validate(self) -> list[EventDrivenIssue]:
        self.issues = []
        for py_file in self.project_root.rglob("*.py"):
            if "test" in py_file.parts or "__pycache__" in py_file.parts:
                continue
            try:
                tree = ast.parse(py_file.read_text())
            except SyntaxError:
                continue
            self._check_event_immutability(py_file, tree)
            self._check_event_naming(py_file, tree)
            self._check_event_handler_structure(py_file, tree)
            self._check_event_bus(py_file, tree)
            self._check_outbox_pattern(py_file, tree)
        return self.issues

    def _check_event_immutability(self, file: Path, tree: ast.AST) -> None:
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef) and "Event" in node.name:
                mutable_field = False
                for child in node.body:
                    if isinstance(child, ast.AnnAssign) and child.value:
                        if isinstance(child.value, (ast.List, ast.Dict)):
                            mutable_field = True
                    if isinstance(child, ast.Assign):
                        for target in child.targets:
                            if isinstance(target, ast.Name):
                                for ancestor in ast.walk(tree):
                                    if (
                                        isinstance(ancestor, ast.FunctionDef)
                                        and ancestor.name == "__post_init__"
                                    ):
                                        pass
                if mutable_field:
                    self.issues.append(
                        EventDrivenIssue(
                            file=str(file.relative_to(self.project_root)),
                            line=node.lineno,
                            pattern="IMMUT",
                            message=f"Event '{node.name}' has mutable default fields — events should be immutable",
                        )
                    )

    def _check_event_naming(self, file: Path, tree: ast.AST) -> None:
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                name = node.name
                if "Event" in name:
                    if not (name.endswith(("Event", "ed", "en"))):
                        if not any(
                            word in name
                            for word in [
                                "Created",
                                "Updated",
                                "Deleted",
                                "Submitted",
                                "Approved",
                                "Rejected",
                                "Completed",
                                "Failed",
                                "Started",
                                "Finished",
                            ]
                        ):
                            self.issues.append(
                                EventDrivenIssue(
                                    file=str(file.relative_to(self.project_root)),
                                    line=node.lineno,
                                    pattern="NAME",
                                    message=f"Event '{name}' should use past-tense naming (e.g., {name}Created)",
                                    severity="info",
                                )
                            )

    def _check_event_handler_structure(self, file: Path, tree: ast.AST) -> None:
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef) and "Handler" in node.name and "Event" in node.name:
                has_handle = any(
                    isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name == "handle"
                    for n in node.body
                )
                if not has_handle:
                    self.issues.append(
                        EventDrivenIssue(
                            file=str(file.relative_to(self.project_root)),
                            line=node.lineno,
                            pattern="HNDL",
                            message=f"Event handler '{node.name}' should implement a 'handle' method",
                        )
                    )

    def _check_event_bus(self, file: Path, tree: ast.AST) -> None:
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                if "EventBus" in node.name or "EventDispatcher" in node.name:
                    has_publish = any(
                        isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
                        and n.name in ("publish", "dispatch", "emit", "send")
                        for n in node.body
                    )
                    has_subscribe = any(
                        isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
                        and n.name in ("subscribe", "register", "listen", "on")
                        for n in node.body
                    )
                    if not has_publish:
                        self.issues.append(
                            EventDrivenIssue(
                                file=str(file.relative_to(self.project_root)),
                                line=node.lineno,
                                pattern="BUS",
                                message=f"Event bus '{node.name}' should implement a publish method",
                            )
                        )
                    if not has_subscribe:
                        self.issues.append(
                            EventDrivenIssue(
                                file=str(file.relative_to(self.project_root)),
                                line=node.lineno,
                                pattern="BUS",
                                message=f"Event bus '{node.name}' should implement a subscribe method",
                            )
                        )

    def _check_outbox_pattern(self, file: Path, tree: ast.AST) -> None:
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef) and "Event" in node.name:
                if "outbox" in file.parts or "outbox" in file.read_text().lower():
                    return
