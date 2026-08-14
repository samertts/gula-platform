from __future__ import annotations

import ast
import re
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FRONTEND_V3 = ROOT / "frontend-v3/src"
FRONTEND_V2 = ROOT / "frontend-v2/src"
BACKEND = ROOT / "backend/app"
REPORTS = ROOT / "reports"


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def md(value: object) -> str:
    return str(value).replace("|", "\\|").replace("\n", " ").strip() or "—"


def iter_source(root: Path, suffixes: tuple[str, ...]) -> list[Path]:
    return sorted(
        path
        for path in root.rglob("*")
        if path.is_file() and path.suffix in suffixes and "node_modules" not in path.parts and "dist" not in path.parts and "build" not in path.parts
    )


def literal_string(node: ast.AST | None) -> str | None:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    return None


def extract_frontend_v3_routes() -> list[dict[str, str]]:
    path = FRONTEND_V3 / "routes/index.tsx"
    text = read(path)
    rows: list[dict[str, str]] = []
    for line_number, line in enumerate(text.splitlines(), 1):
        match = re.search(r'\{\s*(?:path:\s*)?["\']([^"\']+)["\']\s*,\s*element:\s*(.*)\}', line)
        if not match:
            continue
        route = "/" + match.group(1).lstrip("/")
        element = match.group(2).rstrip("},")
        if route == "//*":
            route = "/*"
        # All children of the second root route are nested under ProtectedRoute;
        # login/register are the only public entries in the registry.
        auth_required = route not in {"/login", "/register"}
        role_match = re.search(r"RoleGuard roles=\{([^}]+)\}", element)
        role = role_match.group(1).replace("\"", "'") if role_match else "authenticated"
        status = "LEGACY_BRIDGE" if "LegacyRouteBridge" in element else "ROUTE_REGISTERED"
        rows.append(
            {
                "path": route,
                "method": "GET",
                "page": element.split("<")[1].split(">", 1)[0] if "<" in element else element[:80],
                "auth": "YES" if auth_required else "NO",
                "role": role,
                "permission": "UI role guard only; backend decision required" if auth_required else "public",
                "workspace": "UNVERIFIED",
                "backend": "UNVERIFIED",
                "status": status,
                "source": f"{path.relative_to(ROOT)}:{line_number}",
            },
        )
    return rows


def extract_frontend_v2_routes() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for path in iter_source(FRONTEND_V2, (".tsx", ".ts", ".jsx", ".js")):
        text = read(path)
        for line_number, line in enumerate(text.splitlines(), 1):
            for match in re.finditer(r'<Route[^>]*path=["\']([^"\']+)["\']', line):
                rows.append(
                    {
                        "path": match.group(1),
                        "method": "GET",
                        "page": "legacy route element",
                        "auth": "OUTER SESSION GATE",
                        "role": "UNVERIFIED",
                        "permission": "UNVERIFIED",
                        "workspace": "UNVERIFIED",
                        "backend": "UNVERIFIED",
                        "status": "LEGACY",
                        "source": f"{path.relative_to(ROOT)}:{line_number}",
                    },
                )
    return rows


def extract_backend_endpoints() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for path in iter_source(BACKEND, (".py",)):
        try:
            tree = ast.parse(read(path))
        except SyntaxError:
            continue
        prefixes: dict[str, str] = {}
        for node in ast.walk(tree):
            if not isinstance(node, ast.Assign) or not isinstance(node.value, ast.Call):
                continue
            if not isinstance(node.value.func, ast.Name) or node.value.func.id != "APIRouter":
                continue
            if not node.targets or not isinstance(node.targets[0], ast.Name):
                continue
            prefix = ""
            for keyword in node.value.keywords:
                if keyword.arg == "prefix":
                    prefix = literal_string(keyword.value) or ""
            prefixes[node.targets[0].id] = prefix
        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            for decorator in node.decorator_list:
                if not isinstance(decorator, ast.Call) or not isinstance(decorator.func, ast.Attribute):
                    continue
                if decorator.func.attr.lower() not in {"get", "post", "put", "patch", "delete", "options", "head"}:
                    continue
                if not isinstance(decorator.func.value, ast.Name):
                    continue
                route = literal_string(decorator.args[0]) if decorator.args else ""
                if route is None:
                    route = "{dynamic}"
                prefix = prefixes.get(decorator.func.value.id, "")
                source = read(path)
                function_start = getattr(node, "lineno", 1)
                function_end = getattr(node, "end_lineno", function_start)
                function_text = "\n".join(source.splitlines()[function_start - 1 : function_end])
                auth = "YES" if "Depends(get_current_niam_actor)" in function_text or "get_current_user" in function_text or "require_" in function_text else "UNVERIFIED"
                rows.append(
                    {
                        "method": decorator.func.attr.upper(),
                        "path": (prefix.rstrip("/") + "/" + route.lstrip("/")).replace("//", "/") or "/",
                        "service": str(path.relative_to(ROOT)),
                        "resource": node.name,
                        "auth": auth,
                        "permission": "UNVERIFIED",
                        "policy": "UNVERIFIED",
                        "tenant": "UNVERIFIED",
                        "organization": "UNVERIFIED",
                        "facility": "UNVERIFIED",
                        "workspace": "UNVERIFIED",
                        "database": "UNVERIFIED",
                        "status": "IMPLEMENTED_SOURCE",
                    },
                )
    return sorted(rows, key=lambda item: (item["path"], item["method"], item["service"]))


def extract_app_surfaces() -> list[dict[str, str]]:
    surfaces = [
        ("frontend-v3", "web", "frontend-v3", "Unified web application", "unified/bridge", "frontend-v3/src/routes/index.tsx"),
        ("frontend-v2", "web legacy", "frontend-v2", "Legacy web application", "legacy", "frontend-v2/src/App.tsx"),
        ("gula-web-suite", "web", "apps/gula-web-suite", "Public web suite", "bridge catalog", "frontend-v3/src/pages/migration/frontendSurfaceCatalog.ts"),
        ("citizen", "web app", "platform/apps/citizen", "Citizen application source", "catalog unified", "frontend-v3/src/pages/migration/frontendSurfaceCatalog.ts"),
        ("doctor", "web app", "platform/apps/doctor", "Doctor application source", "safe bridge", "frontend-v3/src/pages/migration/frontendSurfaceCatalog.ts"),
        ("hospital", "web app", "platform/apps/hospital", "Hospital application source", "catalog unified", "frontend-v3/src/pages/migration/frontendSurfaceCatalog.ts"),
        ("laboratory", "web app", "platform/apps/laboratory", "Laboratory application source", "catalog unified", "frontend-v3/src/pages/migration/frontendSurfaceCatalog.ts"),
        ("ministry", "web app", "platform/apps/ministry", "Ministry application source", "catalog unified", "frontend-v3/src/pages/migration/frontendSurfaceCatalog.ts"),
        ("nurse", "web app", "platform/apps/nurse", "Nursing application source", "safe bridge", "frontend-v3/src/pages/migration/frontendSurfaceCatalog.ts"),
        ("pharmacy", "web app", "platform/apps/pharmacy", "Pharmacy application source", "catalog unified", "frontend-v3/src/pages/migration/frontendSurfaceCatalog.ts"),
        ("radiology", "web app", "platform/apps/radiology", "Radiology application source", "safe bridge", "frontend-v3/src/pages/migration/frontendSurfaceCatalog.ts"),
        ("mobile-desktop", "Flutter desktop", "mobile/desktop", "Desktop application", "SDK unavailable", "mobile/desktop/pubspec.yaml"),
        ("mobile-android", "Android", "mobile/android", "Android application", "source present; build unverified", "mobile/android"),
        ("mobile-ios", "iOS", "mobile/ios", "iOS application", "source present; build unverified", "mobile/ios"),
    ]
    return [
        {
            "application": name,
            "platform": platform,
            "path": path,
            "screen": screen,
            "role": "UNVERIFIED",
            "workspace": "UNVERIFIED",
            "backend": "UNVERIFIED",
            "status": status if (ROOT / path).exists() else "MISSING_SOURCE",
            "owner": "GULA Platform",
            "notes": source,
        }
        for name, platform, path, screen, status, source in surfaces
    ]


def write_report(path: Path, title: str, header: str, rows: list[dict[str, str]], columns: list[str]) -> None:
    lines = [f"# {title}", "", header, "", "| " + " | ".join(columns) + " |", "|" + "|".join(["---"] * len(columns)) + "|"]
    for row in rows:
        lines.append("| " + " | ".join(md(row.get(column, "—")) for column in columns) + " |")
    lines.extend(["", f"**Rows:** {len(rows)}. All `UNVERIFIED` values require contract-level follow-up; they are not claims of functionality.", ""])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def build_matrix(frontend_routes: list[dict[str, str]], backend_endpoints: list[dict[str, str]]) -> list[dict[str, str]]:
    rows = []
    backend_paths = {item["path"] for item in backend_endpoints}
    for route in frontend_routes:
        backend = "UNVERIFIED"
        status = "MISSING_BACKEND_OR_UNVERIFIED"
        if route["path"] in backend_paths:
            backend = route["path"]
            status = "PARTIAL"
        if route["status"] == "LEGACY_BRIDGE":
            status = "LEGACY_OR_BRIDGE"
        rows.append(
            {
                "screen": route["page"],
                "action": "route entry",
                "http_method": route["method"],
                "frontend_route": route["path"],
                "backend_route": backend,
                "request_schema": "UNVERIFIED",
                "response_schema": "UNVERIFIED",
                "auth": route["auth"],
                "permission": route["permission"],
                "policy": "UNVERIFIED",
                "organization": "UNVERIFIED",
                "facility": "UNVERIFIED",
                "workspace": route["workspace"],
                "error_codes": "UNVERIFIED",
                "test": "UNVERIFIED",
                "status": status,
            },
        )
    return rows


def main() -> None:
    frontend_v3_routes = extract_frontend_v3_routes()
    frontend_v2_routes = extract_frontend_v2_routes()
    backend_endpoints = extract_backend_endpoints()
    applications = extract_app_surfaces()
    matrix = build_matrix(frontend_v3_routes, backend_endpoints)
    write_report(
        REPORTS / "PHASE_10_APPLICATION_INVENTORY.md",
        "Phase 10 — جرد التطبيقات والأسطح",
        "هذا الجرد مستخرج من المسارات والملفات الموجودة فعليًا. وجود المصدر لا يثبت اتصالًا تشغيليًا.",
        applications,
        ["application", "platform", "path", "screen", "role", "workspace", "backend", "status", "owner", "notes"],
    )
    write_report(
        REPORTS / "PHASE_10_ROUTE_INVENTORY.md",
        "Phase 10 — جرد المسارات",
        "المسارات أدناه مستخرجة من route registries الفعلية في frontend-v3 وfrontend-v2، مع تمييز الجسر والـlegacy.",
        frontend_v3_routes + frontend_v2_routes,
        ["path", "method", "page", "auth", "role", "permission", "workspace", "backend", "status", "source"],
    )
    write_report(
        REPORTS / "PHASE_10_BACKEND_ENDPOINT_INVENTORY.md",
        "Phase 10 — جرد واجهات Backend",
        "الواجهات مستخرجة من FastAPI decorators في المصدر الفعلي. `UNVERIFIED` تعني أن التحليل السطحي لا يكفي لإثبات التفويض أو النطاق.",
        backend_endpoints,
        ["method", "path", "service", "resource", "auth", "permission", "policy", "tenant", "organization", "facility", "workspace", "database", "status"],
    )
    write_report(
        REPORTS / "PHASE_10_FRONTEND_BACKEND_MATRIX.md",
        "Phase 10 — مصفوفة Frontend/Backend الأولية",
        "المصفوفة تربط route entry بالمسار الخادمي عندما يتطابق اسمه فقط؛ لا تعتبر ذلك إثباتًا لعقد request/response أو authorization.",
        matrix,
        ["screen", "action", "http_method", "frontend_route", "backend_route", "request_schema", "response_schema", "auth", "permission", "policy", "organization", "facility", "workspace", "error_codes", "test", "status"],
    )
    foundation = [
        "# Phase 10 — Foundation Revalidation",
        "",
        "## Evidence-based status",
        "",
        "| Area | Evidence | Status |",
        "|---|---|---|",
        "| IAM Phase 9 source | Branch `feat/iam-phase9-security-audit`, HEAD `c4945fa4`; no uncommitted changes before inventory generation | PASS |",
        "| Backend identity regression | Existing local gate previously passed with 162 passed, 3 deselected | PASS — prior gate; rerun required after Phase 10 changes |",
        "| Frontend-v3 governance scripts | Unification, contracts, integration boundary, data-source governance and route-map generation completed | PASS — governance checks; not proof of functional parity |",
        "| Frontend-v3 route registry | `frontend-v3/src/routes/index.tsx` has protected shell plus role guards and legacy bridge | PARTIAL |",
        "| Frontend-v2 | Source and route registry exist; route-level parity remains unverified | PARTIAL |",
        "| Flutter/Desktop | `mobile/desktop` source exists; Flutter SDK availability/build unverified | UNVERIFIED |",
        "| Android/iOS | Source roots exist; platform build/auth parity unverified | UNVERIFIED |",
        "| Specialized applications | Catalog identifies unified and safe-bridge surfaces; no claim of unsupported clinical functionality | PARTIAL |",
        "| Vercel | Previous remote status reported deployment rate limit | EXTERNAL / UNVERIFIED |",
        "| Legal/government integrations | No fabricated integrations or legal compliance claims | CONSTRAINT SATISFIED |",
        "",
        "## P0/P1 candidates requiring repair before claiming parity",
        "",
        "1. `frontend-v3/src/routes/index.tsx` uses legacy role-name guards as a UX gate; backend authorization remains authoritative, but route/action parity with effective permission keys is not proven.",
        "2. The generated data-source inventory marks most direct API surfaces as `unbound`/`non-operational`; these must remain blocked or be mapped to real contracts rather than silently displaying mock data.",
        "3. `frontend-v2` contains legacy routes with only an outer session gate for many role surfaces; those routes must be classified and bridged/deprecated explicitly, not treated as parity.",
        "4. Mobile and specialized application builds are not verified in this sandbox; no parity claim should be made until their available CI/toolchain gates run.",
        "",
        "The inventory is intentionally conservative. It records missing proof as `UNVERIFIED`, `PARTIAL`, `LEGACY`, or `MISSING_BACKEND` rather than fabricating functionality.",
        "",
    ]
    (REPORTS / "PHASE_10_FOUNDATION_REVALIDATION.md").write_text("\n".join(foundation), encoding="utf-8")
    print(f"frontend_v3_routes={len(frontend_v3_routes)}")
    print(f"frontend_v2_routes={len(frontend_v2_routes)}")
    print(f"backend_endpoints={len(backend_endpoints)}")
    print(f"applications={len(applications)}")
    print(f"matrix_rows={len(matrix)}")


if __name__ == "__main__":
    main()
