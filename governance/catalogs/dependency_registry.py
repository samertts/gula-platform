from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from governance.compiler.models import Dependency


class DependencyRegistry:
    _instance: DependencyRegistry | None = None
    REGISTRY_PATH = Path(__file__).resolve().parent / "dependency_registry.json"

    def __new__(cls) -> DependencyRegistry:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._dependencies: list[Dependency] = []
            cls._instance._loaded = False
        return cls._instance

    def load(self) -> None:
        if self._loaded:
            return
        if self.REGISTRY_PATH.exists():
            data = json.loads(self.REGISTRY_PATH.read_text(encoding="utf-8"))
            self._dependencies = [Dependency(**d) for d in data.get("dependencies", [])]
        else:
            self._dependencies = self._scan_existing_dependencies()
            self.save()
        self._loaded = True

    def save(self) -> None:
        data = {
            "version": "1.0.0",
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "count": len(self._dependencies),
            "dependencies": [d.to_dict() for d in self._dependencies],
        }
        self.REGISTRY_PATH.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

    @property
    def dependencies(self) -> list[Dependency]:
        self.load()
        return self._dependencies

    def search(self, query: str = "", type_filter: str = "", risk: str = "") -> list[Dependency]:
        results = self.dependencies
        if query:
            q = query.lower()
            results = [d for d in results if q in d.name.lower() or q in d.purpose.lower()]
        if type_filter:
            results = [d for d in results if d.type.lower() == type_filter.lower()]
        if risk:
            results = [d for d in results if d.risk.lower() == risk.lower()]
        return results

    def get_by_name(self, name: str) -> Dependency | None:
        for d in self.dependencies:
            if d.name.lower() == name.lower():
                return d
        return None

    def get_by_type(self, type_name: str) -> list[Dependency]:
        return [d for d in self.dependencies if d.type.lower() == type_name.lower()]

    def get_high_risk(self) -> list[Dependency]:
        return [d for d in self.dependencies if d.risk.lower() in ("high", "critical")]

    def get_outdated(self) -> list[Dependency]:
        return [d for d in self.dependencies if d.maintenance_status.lower() in ("inactive", "deprecated", "unknown")]

    def get_by_owner(self, owner: str) -> list[Dependency]:
        return [d for d in self.dependencies if d.owner.lower() == owner.lower()]

    def add_dependency(self, dep: Dependency) -> None:
        self.load()
        existing = self.get_by_name(dep.name)
        if existing:
            self._dependencies.remove(existing)
        self._dependencies.append(dep)
        self.save()

    def remove_dependency(self, name: str) -> bool:
        self.load()
        dep = self.get_by_name(name)
        if dep:
            self._dependencies.remove(dep)
            self.save()
            return True
        return False

    def update_risk(self, name: str, risk: str) -> bool:
        dep = self.get_by_name(name)
        if dep:
            dep.risk = risk
            self.save()
            return True
        return False

    def to_dict(self) -> dict[str, Any]:
        return {
            "dependencies": [d.to_dict() for d in self.dependencies],
            "count": len(self.dependencies),
            "high_risk": len(self.get_high_risk()),
            "outdated": len(self.get_outdated()),
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, ensure_ascii=False)

    def _scan_existing_dependencies(self) -> list[Dependency]:
        repo_root = Path(__file__).resolve().parent.parent.parent
        deps: list[Dependency] = []

        req_txt = repo_root / "backend" / "requirements.txt"
        if req_txt.exists():
            for line in req_txt.read_text().splitlines():
                line = line.strip()
                if not line or line.startswith("#") or line.startswith("-"):
                    continue
                if "==" in line:
                    name, version = line.split("==", 1)
                    version = version.split()[0] if version else "unknown"
                elif ">=" in line:
                    name, version = line.split(">=", 1)
                    version = version.split()[0] if version else "unknown"
                else:
                    name = line.split()[0]
                    version = "unknown"
                deps.append(Dependency(
                    name=name.strip(),
                    version=version.strip(),
                    type="python",
                    purpose="Backend dependency",
                    owner="platform",
                    adr="",
                    license_type="",
                    risk="medium",
                    cves=0,
                    security_score=50,
                    upgrade_strategy="Standard pip upgrade",
                    rollback_strategy="Pin previous version",
                    migration_strategy="Test compatibility first",
                    replacement="",
                    maintenance_status="active",
                    cost=0.0,
                    vendor_lock_in_risk="low",
                ))

        pkg_json = repo_root / "package.json"
        if pkg_json.exists():
            import json as _json
            try:
                data = _json.loads(pkg_json.read_text())
                for name, version in data.get("dependencies", {}).items():
                    deps.append(Dependency(
                        name=name,
                        version=version.strip("^~"),
                        type="node",
                        purpose="Frontend/built dependency",
                        owner="platform",
                        adr="",
                        license_type="",
                        risk="medium",
                        cves=0,
                        security_score=50,
                        upgrade_strategy="Standard npm upgrade",
                        rollback_strategy="Pin previous version",
                        migration_strategy="Test compatibility first",
                        replacement="",
                        maintenance_status="active",
                        cost=0.0,
                        vendor_lock_in_risk="low",
                    ))
            except Exception:
                pass

        return deps
