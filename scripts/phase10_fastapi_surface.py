from __future__ import annotations

import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
sys.path.insert(0, str(BACKEND))
os.environ.setdefault("ENV", "test")
os.environ.setdefault("RUNTIME_MODE", "test")


def dependency_names(route) -> list[str]:
    names: list[str] = []
    for dependency in getattr(route, "dependant", None).dependencies if getattr(route, "dependant", None) else []:
        call = getattr(dependency, "call", None)
        names.append(getattr(call, "__name__", str(call)))
    return names


def main() -> None:
    from app.main import app
    from fastapi.routing import APIRoute

    rows = []
    for route in app.routes:
        if not isinstance(route, APIRoute):
            continue
        methods = sorted(route.methods or [])
        names = dependency_names(route)
        rows.append(
            {
                "methods": methods,
                "path": route.path,
                "name": route.name,
                "endpoint": f"{route.endpoint.__module__}.{route.endpoint.__name__}",
                "dependencies": names,
                "auth_dependency_present": any(
                    name in {
                        "get_current_user",
                        "get_current_niam_actor",
                        "get_current_user_optional",
                        "require_current_user",
                    }
                    or "auth" in name.lower()
                    for name in names
                ),
            },
        )
    rows.sort(key=lambda row: (row["path"], row["methods"]))
    output = ROOT / "reports/PHASE_10_FASTAPI_MOUNTED_SURFACES.json"
    output.write_text(json.dumps({"count": len(rows), "routes": rows}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"mounted_fastapi_routes={len(rows)}")
    print(f"routes_without_detected_auth={sum(not row['auth_dependency_present'] for row in rows)}")


if __name__ == "__main__":
    main()
