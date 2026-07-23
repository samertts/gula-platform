"""Backend capability discovery — single source of truth for frontend generation.

Generates a complete inventory of all backend API endpoints, models, services,
and modules. Used by the frontend code generator to produce typed clients.
"""

from __future__ import annotations

import ast
import json
import os
import re
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any


BACKEND_DIR = Path(__file__).resolve().parent.parent / "backend" / "app"
OUTPUT_DIR = Path(__file__).resolve().parent.parent / "docs" / "api"


@dataclass
class Endpoint:
    method: str
    path: str
    function: str
    module: str
    params: list[dict[str, Any]] = field(default_factory=list)
    body_schema: str | None = None
    response_schema: str | None = None
    description: str = ""
    tags: list[str] = field(default_factory=list)


@dataclass
class BackendModule:
    name: str
    path: str
    endpoints: list[Endpoint] = field(default_factory=list)
    sub_modules: list[str] = field(default_factory=list)
    services: list[str] = field(default_factory=list)
    models: list[str] = field(default_factory=list)


def discover_endpoints() -> dict[str, BackendModule]:
    """Walk all backend route files and extract API endpoints."""
    modules: dict[str, BackendModule] = {}

    route_pattern = re.compile(
        r'@router\.(get|post|put|patch|delete|options)\s*\(\s*"([^"]+)"\s*\)'
    )
    func_pattern = re.compile(r"async def (\w+)\s*\(")
    router_prefix = re.compile(r'APIRouter\(.*prefix\s*=\s*"([^"]+)"')
    tag_pattern = re.compile(r'tags\s*=\s*\[([^\]]+)\]')

    for root, dirs, files in os.walk(BACKEND_DIR):
        for fname in files:
            if not fname.endswith(".py") or not fname == "routes.py":
                continue
            fpath = Path(root) / fname
            rel = fpath.relative_to(BACKEND_DIR)
            mod_name = str(rel.parent).replace("/", ".")

            try:
                content = fpath.read_text(encoding="utf-8")
            except Exception:
                continue

            prefix = ""
            tags: list[str] = []
            for match in router_prefix.finditer(content):
                prefix = match.group(1)
            for match in tag_pattern.finditer(content):
                raw = match.group(1)
                tags = [t.strip().strip("\"'") for t in raw.split(",")]

            endpoints: list[Endpoint] = []
            func_name = ""

            for line in content.splitlines():
                rm = route_pattern.search(line)
                if rm:
                    method, route_path = rm.groups()
                    full_path = prefix + route_path
                fm = func_pattern.search(line)
                if fm:
                    func_name = fm.group(1)
                    if func_name.startswith("_"):
                        continue
                    endpoints.append(Endpoint(
                        method=method.upper(),
                        path=full_path,
                        function=func_name,
                        module=mod_name,
                        tags=tags,
                    ))

            if endpoints:
                module = modules.get(mod_name, BackendModule(
                    name=mod_name,
                    path=str(rel.parent),
                ))
                module.endpoints.extend(endpoints)
                modules[mod_name] = module

    return modules


def discover_models() -> dict[str, list[str]]:
    """Walk model files and extract model class names."""
    modules: dict[str, list[str]] = {}
    class_pattern = re.compile(r"^class (\w+)\(.*Base.*\):")

    for root, dirs, files in os.walk(BACKEND_DIR):
        for fname in files:
            if not fname.endswith(".py") or fname == "__init__.py":
                continue
            fpath = Path(root) / fname
            parent_dir = str(fpath.relative_to(BACKEND_DIR).parent)
            if "models" not in str(fpath) and "models" not in parent_dir:
                continue

            content = fpath.read_text(encoding="utf-8", errors="ignore")
            models_found = []
            for line in content.splitlines():
                cm = class_pattern.match(line)
                if cm:
                    models_found.append(cm.group(1))

            if models_found:
                key = f"{parent_dir}/{fname}"
                modules[key] = models_found

    return modules


def generate_inventory() -> dict[str, Any]:
    """Generate the complete backend capability inventory."""
    modules = discover_endpoints()
    models = discover_models()

    inventory = {
        "modules": {
            name: asdict(mod) for name, mod in sorted(modules.items())
        },
        "models": models,
        "total_endpoints": sum(len(m.endpoints) for m in modules.values()),
        "total_route_files": len(modules),
        "total_model_files": len(models),
    }
    return inventory


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    inventory = generate_inventory()

    output = OUTPUT_DIR / "backend_inventory.json"
    output.write_text(json.dumps(inventory, indent=2, default=str))
    print(f"Backend inventory written to {output}")
    print(f"  Total endpoints: {inventory['total_endpoints']}")
    print(f"  Total route files: {inventory['total_route_files']}")
    print(f"  Total model files: {inventory['total_model_files']}")


if __name__ == "__main__":
    main()
