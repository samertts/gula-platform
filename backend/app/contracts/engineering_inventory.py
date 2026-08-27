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
    encounter_files = (
        root / "backend/app/clinical/encounters/models.py",
        root / "backend/app/clinical/encounters/schemas.py",
        root / "backend/app/clinical/encounters/authorization.py",
        root / "backend/app/clinical/encounters/service.py",
        root / "backend/app/clinical/encounters/routes.py",
    )
    encounter_present = tuple(str(path.relative_to(root)) for path in encounter_files if path.exists())
    missing_encounter = tuple(str(path.relative_to(root)) for path in encounter_files if not path.exists())
    encounter_migrations = tuple((backend / "migrations/versions").glob("*encounter*")) if (backend / "migrations/versions").exists() else ()
    encounter_tokens = {
        "authorization": "require_provider",
        "audit": "SyncCanonicalAuditService",
        "idempotency": "Idempotency-Key",
        "concurrency": "with_for_update",
        "versioning": "expected_version",
        "state_machine": "require_transition",
    }
    for evidence, token in encounter_tokens.items():
        evidence_files = tuple(str(path.relative_to(root)) for path in encounter_files if token in texts.get(path, ""))
        if not evidence_files:
            findings.append(
                InventoryFinding(
                    detected=f"missing_encounter_{evidence}",
                    why=f"لم يجد فاحص Encounter token evidence صريحاً: {token}.",
                    impact="قد توجد كتابة سريرية بلا الضابط المطلوب أو لا يمكن إثباته من inventory.",
                    recommended_fix=f"راجع Check-in/Encounter/Clinical Note وأضف evidence واختبار regression لـ{evidence}.",
                    test_required=f"Encounter {evidence} negative/integration test",
                    status="REPAIRING",
                    files=encounter_present,
                ),
            )
    if missing_encounter:
        findings.append(
            InventoryFinding(
                detected="encounter_contract_mismatch",
                why="Canonical encounter package ناقص بالنسبة إلى الملفات المتوقعة.",
                impact="قد لا يتطابق model أو service أو route أو authorization أو schema.",
                recommended_fix="أكمل contract bundle قبل فتح frontend clinical write integration.",
                test_required="Encounter API contract and import smoke test",
                status="BUILDING",
                files=missing_encounter,
            ),
        )
    if not encounter_migrations:
        findings.append(
            InventoryFinding(
                detected="missing_encounter_migration",
                why="لم يجد inventory migration لجداول encounter/clinical note canonical.",
                impact="قد تعمل الاختبارات على create_all بينما بيئة PostgreSQL لا تملك schema.",
                recommended_fix="أضف additive migration وPostgreSQL schema gate قبل staging.",
                test_required="Encounter PostgreSQL migration test",
                status="BUILDING",
                files=encounter_present,
            ),
        )
    else:
        findings.append(
            InventoryFinding(
                detected="encounter_migration_present",
                why="وجد inventory migration canonical encounter/note.",
                impact="وجود الملف لا يثبت تطبيقه على PostgreSQL أو rollback فعلياً.",
                recommended_fix="شغّل migration وdowngrade/re-upgrade في PostgreSQL disposable واحتفظ بملفات الدليل.",
                test_required="PostgreSQL encounter schema/rollback test",
                status="EXTERNAL_DEPENDENCY",
                files=tuple(str(path.relative_to(root)) for path in encounter_migrations),
            ),
        )

    domain_bundles = (
        (
            "laboratory",
            (
                root / "backend/app/clinical/laboratory/models.py",
                root / "backend/app/clinical/laboratory/authorization.py",
                root / "backend/app/clinical/laboratory/service.py",
                root / "backend/app/clinical/laboratory/routes.py",
            ),
            {
                "authorization": "require_permission",
                "audit": "SyncCanonicalAuditService",
                "state_machine": "require_transition",
                "idempotency": "_claim",
                "version": "expected_version",
                "concurrency": "with_for_update",
                "pagination": "offset",
                "chain_of_custody": "CoreSpecimenEvent",
            },
            root / "backend/tests/test_core_lab_result_access_api.py",
        ),
        (
            "result",
            (
                root / "backend/app/clinical/results/models.py",
                root / "backend/app/clinical/results/service.py",
                root / "backend/app/clinical/results/routes.py",
            ),
            {
                "authorization": "require_result_operator",
                "audit": "SyncCanonicalAuditService",
                "state_machine": "require_transition",
                "idempotency": "_claim",
                "version": "expected_version",
                "provenance": "provenance_type",
                "critical_policy": "CRITICAL_ACK_REQUIRED",
                "immutable_correction": "supersedes_id",
            },
            root / "backend/tests/test_core_lab_result_access_api.py",
        ),
        (
            "access",
            (
                root / "backend/app/clinical/access/models.py",
                root / "backend/app/clinical/access/service.py",
                root / "backend/app/clinical/access/routes.py",
            ),
            {
                "authorization": "resolve_scope",
                "audit": "ACCESS_DENIED",
                "state_machine": "REVOKED",
                "idempotency": "_claim",
                "version": "expected_version",
                "pagination": "offset",
                "expiry": "expires_at",
                "purpose": "purpose",
                "scope": "scope_payload",
                "history": "CoreAccessHistory",
            },
            root / "backend/tests/test_core_lab_result_access_api.py",
        ),
        (
            "pharmacy",
            (
                root / "backend/app/clinical/pharmacy/models.py",
                root / "backend/app/clinical/pharmacy/service.py",
                root / "backend/app/clinical/pharmacy/routes.py",
            ),
            {
                "authorization": "require_permission",
                "audit": "SyncCanonicalAuditService",
                "state_machine": "require_transition",
                "idempotency": "_claim",
                "version": "expected_version",
                "concurrency": "with_for_update",
                "immutable_prescription": "signed",
                "ledger": "CoreMedicationStockLedger",
                "no_overdispense": "OverDispenseError",
            },
            root / "backend/tests/test_core_pharmacy_api.py",
        ),
        (
            "imaging",
            (
                root / "backend/app/clinical/imaging/models.py",
                root / "backend/app/clinical/imaging/adapters.py",
                root / "backend/app/clinical/imaging/service.py",
                root / "backend/app/clinical/imaging/routes.py",
            ),
            {
                "authorization": "require_permission",
                "audit": "SyncCanonicalAuditService",
                "state_machine": "require_transition",
                "idempotency": "_claim",
                "version": "expected_version",
                "concurrency": "with_for_update",
                "provenance": "provenance_type",
                "dicom_duplicate": "DICOM_DUPLICATE",
                "immutable_report": "REPORT_ALREADY_FINAL",
                "synthetic_adapter": "SyntheticImagingAdapter",
            },
            root / "backend/tests/test_core_imaging_api.py",
        ),
        (
            "clinical_record",
            (
                root / "backend/app/clinical/record/service.py",
                root / "backend/app/clinical/record/routes.py",
            ),
            {
                "authorization": "_authorize_read",
                "audit": "CLINICAL_RECORD_VIEWED",
                "provenance": "source_domain",
                "pagination": "next_cursor",
                "minimum_necessary": "minimum_necessary",
                "released_only": 'status == "RELEASED"',
                "read_only": "Read-only",
            },
            root / "backend/tests/test_clinical_record_api.py",
        ),
    )
    for domain, bundle_files, tokens, test_file in domain_bundles:
        present = tuple(str(path.relative_to(root)) for path in bundle_files if path.exists())
        for evidence, token in tokens.items():
            evidence_files = tuple(str(path.relative_to(root)) for path in bundle_files if token in texts.get(path, ""))
            if not evidence_files:
                findings.append(
                    InventoryFinding(
                        detected=f"missing_{domain}_{evidence}",
                        why=f"لم يجد فاحص {domain} token evidence صريحاً: {token}.",
                        impact=f"لا يمكن إثبات ضابط {evidence} في {domain} من inventory.",
                        recommended_fix=f"أضف evidence قابل القراءة واختبار regression لـ{domain}/{evidence}.",
                        test_required=f"{domain} {evidence} negative/integration test",
                        status="REPAIRING",
                        files=present,
                    ),
                )
        if not test_file.exists():
            findings.append(
                InventoryFinding(
                    detected=f"missing_{domain}_regression_test",
                    why=f"لم يجد inventory اختبار API مركزي لـ{domain}.",
                    impact="قد توجد semantics صحيحة نظرياً بلا إثبات قابل لإعادة التشغيل.",
                    recommended_fix="أضف API/security/negative/concurrency regression tests.",
                    test_required=f"{domain} regression suite",
                    status="TESTING",
                    files=present,
                ),
            )

    legacy_overlap_files = tuple(
        str(path.relative_to(root))
        for path in (
            root / "backend/app/pharmacy/models.py",
            root / "backend/app/ehr/models/medication.py",
            root / "backend/app/radiology/models.py",
            root / "backend/app/radiology/routes.py",
            root / "backend/app/ehr/models/timeline.py",
        )
        if path.exists()
    )
    if legacy_overlap_files:
        findings.append(
            InventoryFinding(
                detected="legacy_canonical_overlap",
                why="توجد owners legacy متداخلة مع حدود pharmacy/imaging/clinical-record الجديدة.",
                impact="قد يحدث dual-write أو اختلاف authorization/state إذا استُخدمت legacy routes كمصدر حقيقة.",
                recommended_fix="أبقِ legacy read/compatibility فقط، وثّق owner canonical، وأضف migration bridge قابلاً للعكس قبل أي deprecation.",
                test_required="ownership and no-dual-write regression test",
                status="EXTERNAL_DEPENDENCY",
                files=legacy_overlap_files,
            ),
        )

    legacy_lab_routes = tuple(
        str(path.relative_to(root))
        for path in (
            root / "backend/app/routes/results.py",
            root / "backend/app/routes/test_results.py",
        )
        if path.exists()
    )
    if legacy_lab_routes:
        findings.append(
            InventoryFinding(
                detected="legacy_lab_route",
                why="توجد مسارات legacy للمختبر/النتائج إلى جانب canonical Lab/Result Core.",
                impact="قد يحدث اختلاف في authorization أو state أو exposure إذا استُخدمت المسارات القديمة للرحلة الجديدة.",
                recommended_fix="أبقِ legacy خلف deprecation/compatibility policy واستخدم canonical routes للكتابات السريرية الجديدة.",
                test_required="legacy-to-canonical route contract and authorization test",
                status="EXTERNAL_DEPENDENCY",
                files=legacy_lab_routes,
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
