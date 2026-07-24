from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


@dataclass
class SBOMComponent:
    name: str
    version: str
    type: str = "library"
    licenses: list[str] = field(default_factory=list)


class SBOMGenerator:
    def __init__(self, project_root: Path | str):
        self.project_root = Path(project_root)

    def generate(self, output_path: str | None = None) -> dict[str, Any]:
        components = self._extract_dependencies()
        sbom = {
            "bomFormat": "CycloneDX",
            "specVersion": "1.4",
            "serialNumber": f"urn:uuid:{datetime.now(timezone.utc).timestamp()}",
            "version": 1,
            "metadata": {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "tools": [{"name": "gula-engineering", "version": "2.1.0"}],
            },
            "components": [c.__dict__ for c in components],
        }
        if output_path:
            path = Path(output_path)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(sbom, indent=2))
        return sbom

    def _extract_dependencies(self) -> list[SBOMComponent]:
        components = []
        pyproject = self.project_root / "pyproject.toml"
        if pyproject.exists():
            try:
                import tomllib

                data = tomllib.loads(pyproject.read_text())
                deps = data.get("project", {}).get("dependencies", [])
                for dep in deps:
                    name = dep.split(">")[0].split("=")[0].split("<")[0].split("[")[0].strip()
                    version = (
                        dep.split("=")[-1].strip().strip("^~>=<\"'") if "=" in dep else "latest"
                    )
                    components.append(SBOMComponent(name=name, version=version))
            except Exception:
                pass
        return components


class DependencyAuditor:
    def __init__(self, project_root: Path | str):
        self.project_root = Path(project_root)

    def audit(self) -> list[dict[str, Any]]:
        issues = []
        try:
            result = subprocess.run(
                ["pip", "list", "--format=json", "--outdated"],
                capture_output=True,
                text=True,
                timeout=60,
            )
            outdated = json.loads(result.stdout)
            for pkg in outdated:
                issues.append(
                    {
                        "name": pkg.get("name"),
                        "current": pkg.get("version"),
                        "latest": pkg.get("latest_version"),
                        "type": "outdated",
                    },
                )
        except (FileNotFoundError, subprocess.TimeoutExpired, json.JSONDecodeError):
            pass
        return issues
