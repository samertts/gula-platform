from __future__ import annotations

import ast
import json
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class DependencyNode:
    name: str
    path: str
    type: str = "module"
    imports: list[str] = field(default_factory=list)
    imported_by: list[str] = field(default_factory=list)


class DependencyGraphGenerator:
    def __init__(self, project_root: Path | str):
        self.project_root = Path(project_root)

    def generate(self) -> dict[str, DependencyNode]:
        graph: dict[str, DependencyNode] = {}

        for py_file in sorted(self.project_root.rglob("*.py")):
            if (
                "test" in py_file.parts
                or "__pycache__" in py_file.parts
                or ".venv" in py_file.parts
            ):
                continue
            relative = str(py_file.relative_to(self.project_root))
            if relative not in graph:
                graph[relative] = DependencyNode(
                    name=py_file.stem,
                    path=relative,
                )
            try:
                tree = ast.parse(py_file.read_text())
            except SyntaxError:
                continue

            for node in ast.walk(tree):
                if isinstance(node, ast.ImportFrom):
                    if node.module:
                        mod = node.module
                        if mod not in graph[relative].imports:
                            graph[relative].imports.append(mod)
                elif isinstance(node, ast.Import):
                    for alias in node.names:
                        if alias.name not in graph[relative].imports:
                            graph[relative].imports.append(alias.name)

        for name, node in graph.items():
            for imp in node.imports:
                imp_path = imp.replace(".", "/") + ".py"
                for other_name in graph:
                    if other_name.endswith((imp_path, imp + "/__init__.py")):
                        if name not in graph[other_name].imported_by:
                            graph[other_name].imported_by.append(name)

        return graph

    def write_json(self, output_path: str | Path = "dependency_graph.json") -> None:
        graph = self.generate()
        data = {
            name: {
                "name": node.name,
                "path": node.path,
                "type": node.type,
                "imports": node.imports,
                "imported_by": node.imported_by,
            }
            for name, node in graph.items()
        }
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, indent=2))

    def write_mermaid(self, output_path: str | Path = "dependency_graph.md") -> None:
        graph = self.generate()
        lines = ["# Dependency Graph\n", "```mermaid\nflowchart LR\n"]
        for name in graph:
            safe_name = name.replace("-", "_").replace(".", "_").replace("/", "_")
            display = graph[name].path
            lines.append(f"    {safe_name}[{display}]\n")
        for name, node in graph.items():
            safe_name = name.replace("-", "_").replace(".", "_").replace("/", "_")
            for imp in node.imports[:5]:
                imp_path = imp.replace(".", "/") + ".py"
                for other_name in graph:
                    if other_name.endswith((imp_path, imp + "/__init__.py")):
                        safe_other = (
                            other_name.replace("-", "_").replace(".", "_").replace("/", "_")
                        )
                        lines.append(f"    {safe_name} --> {safe_other}\n")
                        break
        lines.append("```\n")
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("".join(lines))

    def find_cyclic_dependencies(self) -> list[list[str]]:
        graph = self.generate()
        adj: dict[str, list[str]] = defaultdict(list)
        for name, node in graph.items():
            for imp in node.imports:
                imp_path = imp.replace(".", "/") + ".py"
                for other_name in graph:
                    if other_name.endswith((imp_path, imp + "/__init__.py")):
                        adj[name].append(other_name)
                        break

        cycles = []
        visited: set[str] = set()
        rec_stack: set[str] = set()
        parent: dict[str, str | None] = {}

        def dfs(u: str) -> None:
            visited.add(u)
            rec_stack.add(u)
            for v in adj.get(u, []):
                if v not in visited:
                    parent[v] = u
                    dfs(v)
                elif v in rec_stack:
                    cycle = [v]
                    cur = u
                    while cur and cur != v:
                        cycle.append(cur)
                        cur = parent.get(cur)
                    cycle.append(v)
                    cycle.reverse()
                    cycles.append(cycle)
            rec_stack.discard(u)

        for name in graph:
            if name not in visited:
                parent[name] = None
                dfs(name)

        return cycles


class DependencyAuditor:
    def __init__(self, project_root: Path | str):
        self.project_root = Path(project_root)
        self.graph = DependencyGraphGenerator(project_root)

    def audit(self) -> dict:
        graph = self.graph.generate()
        cycles = self.graph.find_cyclic_dependencies()

        total_modules = len(graph)
        total_imports = sum(len(n.imports) for n in graph.values())
        orphaned = [n for n, node in graph.items() if not node.imported_by and not node.imports]
        hubs = sorted(
            [(n, len(node.imported_by)) for n, node in graph.items()],
            key=lambda x: -x[1],
        )[:10]

        return {
            "total_modules": total_modules,
            "total_imports": total_imports,
            "avg_imports_per_module": round(total_imports / max(total_modules, 1), 2),
            "orphaned_modules": len(orphaned),
            "cyclic_dependency_count": len(cycles),
            "cyclic_dependencies": cycles[:10],
            "top_dependency_hubs": hubs,
            "orphaned_list": orphaned[:10],
        }
