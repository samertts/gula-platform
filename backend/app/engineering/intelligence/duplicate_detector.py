from __future__ import annotations

import ast
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class DuplicateBlock:
    code_hash: str
    files: list[tuple[str, int]]
    lines_of_code: int
    similarity: float = 1.0


class DuplicateDetector:
    def __init__(self, project_root: Path | str, min_lines: int = 6):
        self.project_root = Path(project_root)
        self.min_lines = min_lines

    def detect(self) -> list[DuplicateBlock]:
        blocks: dict[str, list[tuple[str, int]]] = defaultdict(list)

        for py_file in self.project_root.rglob("*.py"):
            if "test" in py_file.parts or "__pycache__" in py_file.parts:
                continue
            try:
                tree = ast.parse(py_file.read_text())
            except SyntaxError:
                continue
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    lines = node.end_lineno - node.lineno + 1 if node.end_lineno else 0
                    if lines >= self.min_lines:
                        code_hash = self._hash_node(node)
                        if code_hash:
                            blocks[code_hash].append((str(py_file.relative_to(self.project_root)), node.lineno))

        duplicates = []
        for code_hash, locations in blocks.items():
            if len(locations) > 1:
                lines_of_code = 0
                if locations:
                    fp = self.project_root / locations[0][0]
                    try:
                        content = fp.read_text().split("\n")
                        start = locations[0][1]
                        lines_of_code = len(content[start:start + 20])
                    except Exception:
                        lines_of_code = 0
                duplicates.append(
                    DuplicateBlock(
                        code_hash=code_hash,
                        files=locations,
                        lines_of_code=lines_of_code,
                    )
                )

        return duplicates

    def _hash_node(self, node: ast.AST) -> str | None:
        try:
            return str(hash(ast.dump(node, indent=0)))
        except Exception:
            return None


class DeadCodeDetector:
    def __init__(self, project_root: Path | str):
        self.project_root = Path(project_root)

    def detect(self) -> list[dict[str, Any]]:
        dead = []
        defined = self._collect_definitions()
        for py_file in self.project_root.rglob("*.py"):
            if "test" in py_file.parts or "__pycache__" in py_file.parts:
                continue
            try:
                tree = ast.parse(py_file.read_text())
            except SyntaxError:
                continue
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    name = node.name
                    refs = defined.get(name, [])
                    is_defined_here = [r for r in refs if r[0] == str(py_file.relative_to(self.project_root))]
                    is_used_elsewhere = [r for r in refs if r[0] != str(py_file.relative_to(self.project_root))]
                    if len(is_defined_here) == 1 and not is_used_elsewhere and not name.startswith("test_") and not name.startswith("__"):
                        dead.append({
                            "file": str(py_file.relative_to(self.project_root)),
                            "line": node.lineno,
                            "name": name,
                            "type": "unused_function",
                        })
        return dead

    def _collect_definitions(self) -> dict[str, list[tuple[str, int]]]:
        defs: dict[str, list[tuple[str, int]]] = defaultdict(list)
        for py_file in self.project_root.rglob("*.py"):
            if "test" in py_file.parts or "__pycache__" in py_file.parts:
                continue
            try:
                tree = ast.parse(py_file.read_text())
            except SyntaxError:
                continue
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    defs[node.name].append((str(py_file.relative_to(self.project_root)), node.lineno))
        return defs
