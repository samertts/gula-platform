from __future__ import annotations

import ast
from dataclasses import dataclass
from pathlib import Path


@dataclass
class DDDIssue:
    file: str
    line: int
    principle: str
    message: str
    severity: str = "warning"


class DDDValidator:
    def __init__(self, project_root: Path | str):
        self.project_root = Path(project_root)
        self.issues: list[DDDIssue] = []

    def validate(self) -> list[DDDIssue]:
        self.issues = []
        for py_file in self.project_root.rglob("*.py"):
            if "test" in py_file.parts or "__pycache__" in py_file.parts:
                continue
            try:
                tree = ast.parse(py_file.read_text())
            except SyntaxError:
                continue
            self._check_ubiquitous_language(py_file, tree)
            self._check_value_objects(py_file, tree)
            self._check_aggregate_boundaries(py_file, tree)
            self._check_repository_abstraction(py_file, tree)
            self._check_domain_events(py_file, tree)
        return self.issues

    def _check_ubiquitous_language(self, file: Path, tree: ast.AST) -> None:
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                name = node.name
                if "Manager" in name or "Util" in name or "Helper" in name:
                    self.issues.append(
                        DDDIssue(
                            file=str(file.relative_to(self.project_root)),
                            line=node.lineno,
                            principle="UL",
                            message=f"Class '{name}' uses anemic naming — prefer domain language over '{'/'.join(word for word in ['Manager', 'Util', 'Helper'] if word in name)}'",
                        ),
                    )

    def _check_value_objects(self, file: Path, tree: ast.AST) -> None:
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                if "ValueObject" in node.name or "value_object" in file.parts:
                    has_immutable = any(
                        isinstance(n, ast.Assign)
                        and any(
                            isinstance(t, ast.Attribute) and t.attr == "__hash__"
                            for t in ast.walk(n)
                        )
                        for n in node.body
                    )
                    if not has_immutable:
                        self.issues.append(
                            DDDIssue(
                                file=str(file.relative_to(self.project_root)),
                                line=node.lineno,
                                principle="VO",
                                message=f"Value Object '{node.name}' should implement __hash__ for immutability",
                                severity="info",
                            ),
                        )

    def _check_aggregate_boundaries(self, file: Path, tree: ast.AST) -> None:
        if "aggregate" in file.parts:
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    if not any(
                        isinstance(n, ast.FunctionDef) and n.name.startswith("apply")
                        for n in node.body
                    ):
                        self.issues.append(
                            DDDIssue(
                                file=str(file.relative_to(self.project_root)),
                                line=node.lineno,
                                principle="AGG",
                                message=f"Aggregate '{node.name}' should have apply_* methods for event application",
                                severity="info",
                            ),
                        )

    def _check_repository_abstraction(self, file: Path, tree: ast.AST) -> None:
        if "repository" in file.parts:
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    if not any(
                        isinstance(n, ast.ClassDef)
                        or (isinstance(n, ast.FunctionDef) and n.name == "__init__")
                        for n in node.body
                    ):
                        pass
                    has_interface = any(
                        isinstance(n, ast.Name) and n.id == "ABC" for n in ast.walk(node)
                    )
                    if "sqlalchemy" in file.read_text().lower() and not has_interface:
                        self.issues.append(
                            DDDIssue(
                                file=str(file.relative_to(self.project_root)),
                                line=node.lineno,
                                principle="REPO",
                                message=f"Repository '{node.name}' should implement a domain interface",
                            ),
                        )

    def _check_domain_events(self, file: Path, tree: ast.AST) -> None:
        if "event" in file.parts:
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    event_has_timestamp = any(
                        "occurred_at" in ast.dump(n)
                        or "occurred_on" in ast.dump(n)
                        or "timestamp" in ast.dump(n)
                        for n in ast.walk(node)
                    )
                    if not event_has_timestamp:
                        self.issues.append(
                            DDDIssue(
                                file=str(file.relative_to(self.project_root)),
                                line=node.lineno,
                                principle="EVT",
                                message=f"Domain event '{node.name}' should include a timestamp",
                                severity="info",
                            ),
                        )
