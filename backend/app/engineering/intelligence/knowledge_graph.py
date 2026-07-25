from __future__ import annotations

import ast
import json
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class KnowledgeNode:
    id: str
    type: str
    name: str
    file: str
    line: int
    docstring: str = ""
    metadata: dict = field(default_factory=dict)


@dataclass
class KnowledgeEdge:
    source: str
    target: str
    relationship: str
    metadata: dict = field(default_factory=dict)


class KnowledgeGraphGenerator:
    def __init__(self, project_root: Path | str):
        self.project_root = Path(project_root)
        self.nodes: list[KnowledgeNode] = []
        self.edges: list[KnowledgeEdge] = []

    def generate(self) -> dict:
        self.nodes = []
        self.edges = []

        for py_file in self.project_root.rglob("*.py"):
            if (
                "test" in py_file.parts
                or "__pycache__" in py_file.parts
                or ".venv" in py_file.parts
            ):
                continue
            try:
                tree = ast.parse(py_file.read_text())
                self._extract_nodes(py_file, tree)
                self._extract_edges(py_file, tree)
            except SyntaxError:
                continue

        return {
            "nodes": [n.__dict__ for n in self.nodes],
            "edges": [e.__dict__ for e in self.edges],
        }

    def write(self, output_path: str | Path = "knowledge_graph.json") -> None:
        data = self.generate()
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, indent=2))

    def write_mermaid(self, output_path: str | Path = "knowledge_graph.md") -> None:
        data = self.generate()
        lines = ["# Knowledge Graph\n", "```mermaid\nflowchart TD\n"]
        for n in data["nodes"]:
            nid = n["id"].replace("-", "_").replace(".", "_").replace("/", "_")
            lines.append(f'    {nid}["{n["name"]}\\n({n["type"]})"]\n')
        for e in data["edges"]:
            src = e["source"].replace("-", "_").replace(".", "_").replace("/", "_")
            tgt = e["target"].replace("-", "_").replace(".", "_").replace("/", "_")
            lines.append(f"    {src} -->|{e['relationship']}| {tgt}\n")
        lines.append("```\n")
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("".join(lines))

    def _extract_nodes(self, file: Path, tree: ast.AST) -> None:
        relative = str(file.relative_to(self.project_root))

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                docstring = ast.get_docstring(node) or ""
                nid = f"{relative}:{node.lineno}:{node.name}"
                ntype = (
                    "aggregate"
                    if "Aggregate" in node.name
                    else "value_object"
                    if "Value" in node.name
                    else "entity"
                    if "Entity" in node.name
                    else "service"
                    if "Service" in node.name
                    else "repository"
                    if "Repository" in node.name
                    else "controller"
                    if "Controller" in node.name or "Router" in node.name or "Handler" in node.name
                    else "event"
                    if "Event" in node.name
                    else "command"
                    if "Command" in node.name
                    else "query"
                    if "Query" in node.name
                    else "dto"
                    if "DTO" in node.name
                    or "Response" in node.name
                    or "Create" in node.name
                    or "Update" in node.name
                    else "model"
                    if "Model" in node.name
                    else "class"
                )
                self.nodes.append(
                    KnowledgeNode(
                        id=nid,
                        type=ntype,
                        name=node.name,
                        file=relative,
                        line=node.lineno,
                        docstring=docstring,
                    ),
                )

            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if node.name.startswith("__"):
                    continue
                docstring = ast.get_docstring(node) or ""
                nid = f"{relative}:{node.lineno}:{node.name}"
                ntype = (
                    "endpoint"
                    if any(
                        d.attr == "get"
                        or d.attr == "post"
                        or d.attr == "put"
                        or d.attr == "delete"
                        or d.attr == "patch"
                        for d in node.decorator_list
                        if isinstance(d, ast.Attribute)
                    )
                    else "handler"
                    if "handler" in node.name.lower() or "handle" in node.name.lower()
                    else "use_case"
                    if "use_case" in node.name.lower()
                    else "function"
                )
                self.nodes.append(
                    KnowledgeNode(
                        id=nid,
                        type=ntype,
                        name=node.name,
                        file=relative,
                        line=node.lineno,
                        docstring=docstring,
                    ),
                )

    def _extract_edges(self, file: Path, tree: ast.AST) -> None:
        relative = str(file.relative_to(self.project_root))

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                source = f"{relative}:{node.lineno}:{node.name}"

                for child in node.body:
                    if isinstance(child, ast.Assign):
                        for target in child.targets:
                            if isinstance(target, ast.Attribute) and isinstance(
                                target.value,
                                ast.Call,
                            ):
                                if (
                                    hasattr(target.value.func, "attr")
                                    and target.value.func.attr == "get"
                                ):
                                    pass

                for child in ast.walk(node):
                    if isinstance(child, ast.Call) and isinstance(child.func, ast.Attribute):
                        if child.func.attr in ("import_module", "__import__"):
                            for arg in child.args:
                                if isinstance(arg, ast.Constant):
                                    self.edges.append(
                                        KnowledgeEdge(
                                            source=source,
                                            target=str(arg.value),
                                            relationship="imports",
                                        ),
                                    )
                    if isinstance(child, ast.Call) and isinstance(child.func, ast.Attribute):
                        if child.func.attr in ("subscribe", "register", "on", "listen"):
                            for arg in child.args:
                                if isinstance(arg, ast.Name):
                                    self.edges.append(
                                        KnowledgeEdge(
                                            source=source,
                                            target=str(arg.id),
                                            relationship="subscribes_to",
                                        ),
                                    )
                        elif child.func.attr in ("publish", "emit", "dispatch", "send"):
                            for arg in child.args:
                                if isinstance(arg, ast.Name):
                                    self.edges.append(
                                        KnowledgeEdge(
                                            source=source,
                                            target=str(arg.id),
                                            relationship="publishes",
                                        ),
                                    )

                for base in node.bases:
                    if isinstance(base, ast.Name):
                        self.edges.append(
                            KnowledgeEdge(
                                source=source,
                                target=f":::{base.id}",
                                relationship="extends",
                            ),
                        )
