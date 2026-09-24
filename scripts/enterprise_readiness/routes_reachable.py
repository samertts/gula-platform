"""Reachable API operations, measured by booting the app.

Counting route decorators overstates the surface (2,406 declared vs 2,102
reachable at the time of writing) because many modules are never registered.
And a plain walk of ``app.routes`` understates it: this FastAPI version stores
nested routers as lazy ``_IncludedRouter`` wrappers, so a naive walk returns
only the four docs routes. Follow ``original_router`` to materialise them.

    ENV=development RUNTIME_MODE=test DATABASE_URL=... \
      python3 scripts/enterprise_readiness/routes_reachable.py
"""
from __future__ import annotations

import collections
import json
import os
from pathlib import Path

from app.factory import create_app
from fastapi.routing import APIRoute

SP = Path(os.getenv("GULA_SCAN_DIR", "/tmp/gula-scan"))
SP.mkdir(parents=True, exist_ok=True)
METHODS = ("GET", "POST", "PUT", "PATCH", "DELETE")


def walk(routes, prefix: str = ""):
    for r in routes:
        if isinstance(r, APIRoute):
            module = getattr(getattr(r, "endpoint", None), "__module__", "?")
            yield prefix + (r.path or ""), module, sorted(
                m for m in (r.methods or set()) if m in METHODS
            )
            continue
        original = getattr(r, "original_router", None)
        if original is not None:
            ctx = getattr(r, "include_context", None)
            yield from walk(original.routes, prefix + (getattr(ctx, "prefix", "") or ""))


def main() -> None:
    app = create_app()
    rows = [
        {"path": path, "module": module, "methods": methods}
        for path, module, methods in walk(app.routes)
        if methods
    ]
    (SP / "reachable_routes.json").write_text(json.dumps(rows, indent=0), encoding="utf-8")
    by_domain = collections.Counter()
    for r in rows:
        parts = r["module"].split(".")
        by_domain[parts[1] if len(parts) > 1 else "?"] += len(r["methods"])
    print(json.dumps({
        "reachable_operations": sum(len(r["methods"]) for r in rows),
        "distinct_paths": len({r["path"] for r in rows}),
        "route_modules": len({r["module"] for r in rows}),
        "by_defining_package": by_domain.most_common(),
    }, indent=2))


if __name__ == "__main__":
    main()
