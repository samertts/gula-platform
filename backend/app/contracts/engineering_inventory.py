from __future__ import annotations

import argparse
import ast
import json
import sys
from collections.abc import Sequence
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Literal

InventoryStatus = Literal[
    "DISCOVERED",
    "DESIGNING",
    "BUILDING",
    "INTEGRATING",
    "REPAIRING",
    "TESTING",
    "IMPROVING",
    "READY_FOR_REVIEW",
    "READY_FOR_STAGING",
    "READY_FOR_PRODUCTION",
    "EXTERNAL_DEPENDENCY",
]


@dataclass(frozen=True)
class InventoryFinding:
    detected: str
    why: str
    impact: str
    recommended_fix: str
    test_required: str
    status: InventoryStatus
    files: tuple[str, ...] = ()


@dataclass(frozen=True)
class EngineeringInventoryReport:
    root: str
    scanned_files: int
    findings: tuple[InventoryFinding, ...]
    status: InventoryStatus
    production_ready: bool = False

    def to_dict(self) -> dict[str, object]:
        return {
            "root": self.root,
            "scanned_files": self.scanned_files,
            "status": self.status,
            "production_ready": self.production_ready,
            "findings": [asdict(finding) for finding in self.findings],
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2, sort_keys=True)


def _python_files(root: Path) -> tuple[Path, ...]:
    return tuple(sorted(path for path in root.rglob("*.py") if "/__pycache__/" not in str(path)))


def _class_table_names(path: Path) -> tuple[str, ...]:
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except (OSError, SyntaxError, UnicodeDecodeError):
        return ()
    names: list[str] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.ClassDef):
            continue
        for statement in node.body:
            if not isinstance(statement, ast.Assign):
                continue
            if not any(isinstance(target, ast.Name) and target.id == "__tablename__" for target in statement.targets):
                continue
            if isinstance(statement.value, ast.Constant) and isinstance(statement.value.value, str):
                names.append(statement.value.value)
    return tuple(names)


def _literal_routes(path: Path) -> tuple[str, ...]:
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except (OSError, SyntaxError, UnicodeDecodeError):
        return ()
    routes: list[str] = []
    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        for decorator in node.decorator_list:
            if not isinstance(decorator, ast.Call) or not isinstance(decorator.func, ast.Attribute):
                continue
            if decorator.func.attr.lower() not in {"get", "post", "put", "patch", "delete"} or not decorator.args:
                continue
            route = decorator.args[0]
            if isinstance(route, ast.Constant) and isinstance(route.value, str):
                routes.append(route.value)
    return tuple(routes)


def scan_repository(repo_root: str | Path) -> EngineeringInventoryReport:
    root = Path(repo_root).resolve()
    backend = root / "backend"
    app = backend / "app"
    files = _python_files(app) if app.exists() else ()
    table_files: dict[str, list[str]] = {}
    route_files: dict[str, list[str]] = {}
    texts: dict[Path, str] = {}
    for path in files:
        relative = str(path.relative_to(root))
        texts[path] = path.read_text(encoding="utf-8", errors="replace")
        for table in _class_table_names(path):
            table_files.setdefault(table, []).append(relative)
        for route in _literal_routes(path):
            route_files.setdefault(route, []).append(relative)

    findings: list[InventoryFinding] = []
    for table, owners in sorted(table_files.items()):
        if len(owners) > 1:
            findings.append(
                InventoryFinding(
                    detected="duplicate_model",
                    why=f"أكثر من ORM class يعلن __tablename__={table}.",
                    impact="قد يحدث architecture drift أو اختلاف migration/authorization بين نموذجين.",
                    recommended_fix="راجع owners وحدد canonical model ثم استخدم migration غير تدميرية قبل deprecation.",
                    test_required="model registry وmigration consistency test",
                    status="REPAIRING",
                    files=tuple(owners),
                ),
            )

    for route, owners in sorted(route_files.items()):
        if len(owners) > 1 and route.startswith("/api/v1/appointments"):
            findings.append(
                InventoryFinding(
                    detected="duplicate_route",
                    why=f"المسار {route} مسجل في أكثر من router.",
                    impact="قد تختلف الصلاحيات أو error contract حسب ترتيب التسجيل.",
                    recommended_fix="أبقِ canonical route واحداً وافصل legacy route خلف deprecation policy.",
                    test_required="route registry وdirect API authorization test",
                    status="REPAIRING",
                    files=tuple(owners),
                ),
            )

    appointment_files = (
        root / "backend/app/clinical/appointments/models.py",
        root / "backend/app/clinical/appointments/schemas.py",
        root / "backend/app/clinical/appointments/authorization.py",
        root / "backend/app/clinical/appointments/service.py",
        root / "backend/app/clinical/appointments/routes.py",
    )
    appointment_present = tuple(str(path.relative_to(root)) for path in appointment_files if path.exists())
    missing_appointment = tuple(str(path.relative_to(root)) for path in appointment_files if not path.exists())
    migration_files = tuple((backend / "migrations/versions").glob("*appointment*")) if (backend / "migrations/versions").exists() else ()
    required_tokens = {
        "authorization": "require_permission",
        "audit": "CanonicalAuditService",
        "idempotency": "Idempotency-Key",
        "concurrency": "with_for_update",
        "error_contract": "DomainError",
    }
    for evidence, token in required_tokens.items():
        evidence_files = tuple(str(path.relative_to(root)) for path in appointment_files if token in texts.get(path, ""))
        if not evidence_files:
            findings.append(
                InventoryFinding(
                    detected=f"missing_{evidence}",
                    why=f"لم يجد الفاحص token evidence صريحاً: {token}.",
                    impact="لا يمكن إثبات الضابط من inventory؛ قد تكون الكتابة غير محمية أو تحتاج مراجعة.",
                    recommended_fix=f"راجع العقد وأضف evidence صريحاً مع اختبار regression لـ{evidence}.",
                    test_required=f"{evidence} negative/integration test",
                    status="REPAIRING",
                    files=appointment_present,
                ),
            )
    if missing_appointment:
        findings.append(
            InventoryFinding(
                detected="contract_mismatch",
                why="Canonical appointment package ناقص بالنسبة إلى الملفات المتوقعة.",
                impact="قد لا يتطابق model أو service أو route أو authorization.",
                recommended_fix="أكمل contract bundle قبل فتح frontend write integration.",
                test_required="API contract and import smoke test",
                status="BUILDING",
                files=missing_appointment,
            ),
        )
    if not migration_files:
        findings.append(
            InventoryFinding(
                detected="missing_migration",
                why="لم يجد inventory migration مسماة للـappointment canonical model.",
                impact="قد تعمل الاختبارات على create_all بينما بيئة الإنتاج لا تملك schema.",
                recommended_fix="أضف additive migration واختبار PostgreSQL قبل staging.",
                test_required="migration schema/FK/index/check test",
                status="BUILDING",
                files=appointment_present,
            ),
        )
    else:
        findings.append(
            InventoryFinding(
                detected="migration_present",
                why="وجد inventory migration canonical appointment.",
                impact="وجود الملف لا يثبت تطبيق migration على PostgreSQL.",
                recommended_fix="شغّل migration test على PostgreSQL واحتفظ بالدليل في CI/staging.",
                test_required="PostgreSQL migration test",
                status="EXTERNAL_DEPENDENCY",
                files=tuple(str(path.relative_to(root)) for path in migration_files),
            ),
        )

    missing_tests = not (root / "backend/tests/test_core_appointment_api.py").exists()
    if missing_tests:
        findings.append(
            InventoryFinding(
                detected="missing_tests",
                why="لم يجد inventory اختبار API canonical appointment.",
                impact="لا يمكن إثبات direct API authorization أو negative cases.",
                recommended_fix="أضف API/security/IDOR/idempotency tests.",
                test_required="API and security suite",
                status="TESTING",
            ),
        )
    findings.append(
        InventoryFinding(
            detected="production_evidence_gap",
            why="inventory محلي ولا يرى remote CI أو staging أو rollback execution.",
            impact="لا يجوز ترقية النتيجة إلى جاهزية إنتاجية.",
            recommended_fix="شغّل remote CI وstaging smoke وrollback evidence عند توفر الصلاحيات.",
            test_required="remote CI, staging, rollback checks",
            status="EXTERNAL_DEPENDENCY",
            files=("backend/app/clinical/appointments",),
        ),
    )
    status: InventoryStatus = "READY_FOR_REVIEW" if not any(f.status in {"BUILDING", "REPAIRING"} for f in findings) else "REPAIRING"
    return EngineeringInventoryReport(str(root), len(files), tuple(findings), status, production_ready=False)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Emit advisory GULA engineering inventory as JSON")
    parser.add_argument("root", nargs="?", default=".", help="repository root")
    parser.add_argument("--output", type=Path, help="optional JSON output path")
    args = parser.parse_args(argv)
    report = scan_repository(args.root)
    payload = report.to_json()
    if args.output:
        args.output.write_text(payload + "\n", encoding="utf-8")
    else:
        sys.stdout.write(payload + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
