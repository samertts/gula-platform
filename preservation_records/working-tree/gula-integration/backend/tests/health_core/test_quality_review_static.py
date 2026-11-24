"""WS-E independent structural review tests for the synthetic Health Core package.

These tests are deliberately different from ``test_sandbox_guards.py``: they use
AST structure, class-inheritance analysis, constructor-inspection, runtime
state-machine checks and protection-integrity checks rather than the guard's
flat import/name denylist.  They assert properties that HOLD in the reviewed
slice; gaps found by the review are reported in
``GOVERNANCE/ACCELERATION/QUALITY_ARCHITECTURE_REVIEW.md`` instead of being
silently encoded as passing tests.

Anchoring: ``Path(__file__).parents[2]`` is ``backend/`` and ``parents[3]`` is
the repository root (the integration workspace, never the protected platform).
"""

from __future__ import annotations

import ast
import hashlib
import importlib
import pkgutil
from pathlib import Path

import pytest

BACKEND_ROOT = Path(__file__).resolve().parents[2]
REPO_ROOT = Path(__file__).resolve().parents[3]
HEALTH_CORE = BACKEND_ROOT / "app" / "health_core"
TEST_DIR = Path(__file__).resolve().parent

FINAL_DECISION_MD5 = "effdfeaf10234678d83b2668c4489552"


def _source_files() -> list[Path]:
    assert HEALTH_CORE.is_dir(), f"missing package: {HEALTH_CORE}"
    return sorted(HEALTH_CORE.rglob("*.py"))


def _trees() -> list[tuple[Path, ast.Module]]:
    return [(p, ast.parse(p.read_text(encoding="utf-8"), filename=str(p))) for p in _source_files()]


# ---------------------------------------------------------------------------
# 1. Structural integrity / layering
# ---------------------------------------------------------------------------


def test_every_module_parses_and_imports_without_circular_dependency() -> None:
    """Every source file is valid Python and the package imports acyclically."""
    assert len(_source_files()) >= 20, "expected the full multi-workstream package"
    import app.health_core as package

    names = sorted(m.name for m in pkgutil.walk_packages(package.__path__, package.__name__ + "."))
    assert len(names) >= 30
    for name in names:
        importlib.import_module(name)


def test_no_forbidden_runtime_dependency_roots_are_imported() -> None:
    """No module imports a DB/broker/HTTP/real-identity root (AST, not prose)."""
    forbidden = {
        "sqlalchemy",
        "alembic",
        "psycopg",
        "asyncpg",
        "httpx",
        "aiohttp",
        "requests",
        "urllib3",
        "socket",
        "redis",
        "kafka",
        "boto3",
        "fastapi",
        "starlette",
        "app.services.mpi",
        "app.health_data",
        "app.identity",
        "app.database",
    }
    violations: list[str] = []
    for path, tree in _trees():
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                modules = [alias.name for alias in node.names]
            elif isinstance(node, ast.ImportFrom):
                modules = [node.module or ""]
            else:
                continue
            for module in modules:
                for bad in forbidden:
                    if module == bad or module.startswith(bad + "."):
                        violations.append(f"{path.relative_to(BACKEND_ROOT)}:{node.lineno} {module}")
    assert not violations, "forbidden runtime dependency roots:\n" + "\n".join(violations)


def test_no_fastapi_router_construction_or_route_decorators() -> None:
    """No router object, HTTP-method decorator or include_router call exists."""
    http_methods = {"get", "post", "put", "patch", "delete", "head", "options", "api_route"}
    violations: list[str] = []
    for path, tree in _trees():
        for node in ast.walk(tree):
            if (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Name)
                and node.func.id in {"APIRouter", "include_router"}
            ):
                violations.append(f"{path.relative_to(BACKEND_ROOT)}:{node.lineno} call {node.func.id}")
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                for decorator in node.decorator_list:
                    target = decorator.func if isinstance(decorator, ast.Call) else decorator
                    if isinstance(target, ast.Attribute) and target.attr in http_methods:
                        violations.append(
                            f"{path.relative_to(BACKEND_ROOT)}:{node.lineno} route decorator .{target.attr}"
                        )
    assert not violations, "stub route/router construction:\n" + "\n".join(violations)


def test_factory_and_main_do_not_import_or_reference_health_core() -> None:
    """The synthetic package is not wired into production startup (AST imports)."""
    for filename in ("factory.py", "main.py"):
        path = BACKEND_ROOT / "app" / filename
        assert path.is_file()
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        refs = [
            node.lineno
            for node in ast.walk(tree)
            if (isinstance(node, ast.ImportFrom) and (node.module or "").startswith("app.health_core"))
            or (isinstance(node, ast.Import) and any(a.name.startswith("app.health_core") for a in node.names))
        ]
        assert not refs, f"{filename} references health_core at {refs}"


# ---------------------------------------------------------------------------
# 2. SOLID / no stubs / dependency inversion
# ---------------------------------------------------------------------------


def _interface_method_ids(tree: ast.Module) -> set[int]:
    """Node ids of methods that belong to a Protocol/ABC class (or are abstract)."""
    ids: set[int] = set()
    for node in ast.walk(tree):
        if not isinstance(node, ast.ClassDef):
            continue
        bases = {ast.unparse(base) for base in node.bases}
        is_interface = any(
            "Protocol" in base or "ABC" in base or "Abstract" in base for base in bases
        )
        for child in node.body:
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                decorators = {ast.unparse(d) for d in child.decorator_list}
                if is_interface or "abstractmethod" in decorators:
                    ids.add(id(child))
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            decorators = {ast.unparse(d) for d in node.decorator_list}
            if "abstractmethod" in decorators:
                ids.add(id(node))
    return ids


def test_no_empty_concrete_functions_or_literal_fake_success_returns() -> None:
    """Interfaces may use ``...``; concrete code must be real and never `return True`."""
    violations: list[str] = []
    for path, tree in _trees():
        interface_methods = _interface_method_ids(tree)
        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            if id(node) in interface_methods:
                continue
            # A function nested in a Protocol/ABC class and containing only ... is an interface.
            body = [s for s in node.body if not (isinstance(s, ast.Expr) and isinstance(s.value, ast.Constant) and isinstance(s.value.value, str))]
            if not body or all(
                (isinstance(s, ast.Expr) and isinstance(s.value, ast.Constant) and s.value.value is Ellipsis)
                or isinstance(s, ast.Pass)
                for s in body
            ):
                violations.append(f"{path.relative_to(BACKEND_ROOT)}:{node.lineno} empty body {node.name}")
            for ret in ast.walk(node):
                if isinstance(ret, ast.Return) and isinstance(ret.value, ast.Constant) and ret.value.value is True:
                    violations.append(f"{path.relative_to(BACKEND_ROOT)}:{ret.lineno} return True in {node.name}")
    assert not violations, "stub/fake-success code:\n" + "\n".join(violations)


def test_patient_scoping_services_take_the_identity_port_by_constructor() -> None:
    """Every service that touches a patient depends on PatientIdentityPort (AST)."""
    expected = {
        "clinical/services.py": {
            "EncounterService",
            "DiagnosisService",
            "ObservationService",
            "MedicalRecordService",
        },
        "lab/services.py": {"LabWorkflowService"},
        "integration/api_client.py": {"InMemorySyntheticApiClient"},
    }
    for rel, class_names in expected.items():
        path = HEALTH_CORE / rel
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        classes = {n.name: n for n in ast.walk(tree) if isinstance(n, ast.ClassDef)}
        for class_name in class_names:
            assert class_name in classes, f"{rel}: missing {class_name}"
            init = next(
                (n for n in classes[class_name].body if isinstance(n, ast.FunctionDef) and n.name == "__init__"),
                None,
            )
            assert init is not None, f"{rel}:{class_name} has no __init__"
            annotations = [
                ast.unparse(arg.annotation)
                for arg in (*init.args.args, *init.args.kwonlyargs)
                if arg.annotation is not None
            ]
            assert any("PatientIdentityPort" in a for a in annotations), (
                f"{rel}:{class_name} does not depend on PatientIdentityPort"
            )


def test_all_immutable_entities_are_frozen_dataclasses() -> None:
    """Domain entities and records are frozen/slotted, so state changes are explicit."""
    targets = [
        HEALTH_CORE / "common" / "events.py",
        HEALTH_CORE / "clinical" / "entities.py",
        HEALTH_CORE / "lab" / "models.py",
        HEALTH_CORE / "integration" / "api_client.py",
    ]
    checked = 0
    for path in targets:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if not isinstance(node, ast.ClassDef):
                continue
            decorators = [ast.unparse(d) for d in node.decorator_list]
            if not any(d.startswith("dataclass") for d in decorators):
                continue
            checked += 1
            assert any("frozen=True" in d for d in decorators), f"{path.name}:{node.lineno} not frozen"
            assert any("slots=True" in d for d in decorators), f"{path.name}:{node.lineno} not slotted"
    assert checked >= 15, f"expected many frozen records, found {checked}"


# ---------------------------------------------------------------------------
# 3. Event vocabulary / auditability
# ---------------------------------------------------------------------------


def test_event_and_aggregate_enums_are_declared_exactly_once_in_shared_module() -> None:
    """The shared vocabulary classes exist once, in common/event_types.py only."""
    found: dict[str, list[str]] = {"EventType": [], "AggregateType": []}
    for path, tree in _trees():
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef) and node.name in found:
                found[node.name].append(str(path.relative_to(BACKEND_ROOT)))
    assert found["EventType"] == ["app/health_core/common/event_types.py"], found
    assert found["AggregateType"] == ["app/health_core/common/event_types.py"], found


def test_legal_transition_maps_cover_every_state_and_are_terminal() -> None:
    """Every state has a transition rule and terminal states cannot advance."""
    from app.health_core.clinical.entities import (
        LEGAL_ENCOUNTER_TRANSITIONS,
        EncounterStatus,
    )
    from app.health_core.lab.models import (
        LEGAL_SPECIMEN_TRANSITIONS,
        LEGAL_VERIFICATION_TRANSITIONS,
        SpecimenStatus,
        VerificationStatus,
    )

    for enum, rules in (
        (EncounterStatus, LEGAL_ENCOUNTER_TRANSITIONS),
        (SpecimenStatus, LEGAL_SPECIMEN_TRANSITIONS),
        (VerificationStatus, LEGAL_VERIFICATION_TRANSITIONS),
    ):
        assert set(rules) == set(enum), f"{enum.__name__}: missing states {set(enum) - set(rules)}"
        for state, targets in rules.items():
            assert all(isinstance(t, enum) for t in targets), f"non-enum target in {state}"
    assert LEGAL_ENCOUNTER_TRANSITIONS[EncounterStatus.DISCHARGED] == frozenset()
    assert LEGAL_ENCOUNTER_TRANSITIONS[EncounterStatus.CANCELLED] == frozenset()
    assert LEGAL_SPECIMEN_TRANSITIONS[SpecimenStatus.FINAL] == frozenset()
    assert LEGAL_VERIFICATION_TRANSITIONS[VerificationStatus.REJECTED] == frozenset()


def test_event_emitters_append_immutable_events_with_synthetic_ids() -> None:
    """State changes append frozen events with SYN- ids and UTC timestamps."""
    from app.health_core.clinical.context import ClinicalContext
    from app.health_core.common import DomainEvent, is_synthetic_id
    from app.health_core.identity.synthetic import SyntheticPatientRegistry

    registry = SyntheticPatientRegistry()
    tenant = "SYN-LAB-0001"
    patient = registry.register_patient(tenant_id=tenant)
    context = ClinicalContext(identity=registry)
    # One real state change: a medical-record open emits an immutable event.
    view = context.medical_records.open(
        scope=__import__(
            "app.health_core.clinical.entities", fromlist=["RecordScope"]
        ).RecordScope(tenant_id=tenant, patient_refs=(patient.ref,))
    )
    assert view.item_count == 0
    events = context.event_history()
    assert events and isinstance(events[0], DomainEvent)
    for event in events:
        assert is_synthetic_id(event.event_id)
        assert is_synthetic_id(event.tenant_id)
        assert event.occurred_at.endswith("+00:00")


# ---------------------------------------------------------------------------
# 4. Offline / conflicts / tenant isolation / failure recovery
# ---------------------------------------------------------------------------


def test_outbox_ordering_is_deterministic_and_replay_is_idempotent() -> None:
    """Order is (occurred_at, sequence); duplicate ids replay without re-apply."""
    from app.health_core.common import new_event
    from app.health_core.integration.offline import (
        ApplyStatus,
        OfflineOutbox,
        ReplayJournal,
        replay,
    )

    box = OfflineOutbox()
    first = new_event(
        event_type="patient.registered",
        aggregate_type="patient",
        aggregate_id="SYN-PAT-000000000001",
        tenant_id="SYN-LAB-0001",
        occurred_at=__import__("datetime").datetime.fromisoformat("2026-01-01T00:00:02+00:00"),
    )
    second = new_event(
        event_type="patient.registered",
        aggregate_type="patient",
        aggregate_id="SYN-PAT-000000000002",
        tenant_id="SYN-LAB-0001",
        occurred_at=__import__("datetime").datetime.fromisoformat("2026-01-01T00:00:01+00:00"),
    )
    e1 = box.enqueue(first)
    e2 = box.enqueue(second)
    assert [e.sequence for e in box.ordered_entries()] == [e2.sequence, e1.sequence]
    assert box.enqueue(first) is e1
    journal = ReplayJournal()
    decisions = replay(box, journal)
    assert [d.status for d in decisions] == [ApplyStatus.APPLIED, ApplyStatus.APPLIED]
    replay_again = replay(box, journal)
    assert all(d.status is ApplyStatus.DUPLICATE for d in replay_again)


def test_conflict_resolution_accounts_for_every_candidate_event() -> None:
    """Every rejected/superseded event has a disposition and an audit record."""
    from app.health_core.common import new_event, new_synthetic_id
    from app.health_core.integration.conflicts import (
        ConflictCase,
        ConflictStrategy,
        Disposition,
        assert_no_silent_drops,
        resolve_conflict,
    )

    events = tuple(
        new_event(
            event_type="patient.registered",
            aggregate_type="patient",
            aggregate_id="SYN-PAT-000000000001",
            tenant_id="SYN-LAB-0001",
            payload={"seq": index},
        )
        for index in range(3)
    )
    case = ConflictCase(
        conflict_id=new_synthetic_id("CFL"),
        aggregate_key="SYN-LAB-0001/patient/SYN-PAT-000000000001",
        tenant_id="SYN-LAB-0001",
        events=events,
        expected_version=1,
        observed_version=3,
    )
    decision = resolve_conflict(case, ConflictStrategy.KEEP_LAST_WITH_AUDIT)
    assert_no_silent_drops(decision)
    assert len(decision.dispositions) == 3
    non_accepted = [d for d in decision.dispositions if d.disposition is not Disposition.ACCEPTED]
    assert len(non_accepted) == 2 and len(decision.audit) == 2


def test_cross_tenant_patient_resolution_fails_closed() -> None:
    """A patient reference from tenant B cannot be resolved inside tenant A."""
    from app.health_core.common import TenantMismatchError
    from app.health_core.identity.synthetic import SyntheticPatientRegistry

    registry = SyntheticPatientRegistry()
    patient_b = registry.register_patient(tenant_id="SYN-LAB-0002")
    with pytest.raises(TenantMismatchError):
        registry.resolve_patient(tenant_id="SYN-LAB-0001", patient_ref=patient_b.ref)


# ---------------------------------------------------------------------------
# 5. Protection integrity / no secrets / no DDL / no hidden skips
# ---------------------------------------------------------------------------


def test_final_decision_and_protected_governance_file_hash_is_unchanged() -> None:
    """The HOLD decision file still has its pre-review md5."""
    target = REPO_ROOT / "GOVERNANCE" / "FINAL_DECISION.md"
    assert target.is_file()
    digest = hashlib.md5(target.read_bytes()).hexdigest()
    assert digest == FINAL_DECISION_MD5, f"FINAL_DECISION.md changed: {digest}"


def test_no_ddl_or_migration_artifacts_inside_health_core() -> None:
    """The package contains no migration, DDL statement or schema-version file."""
    forbidden_tokens = ("CREATE TABLE", "ALTER TABLE", "DROP TABLE", "op.create_table", "op.execute")
    for path in _source_files():
        assert "migration" not in path.name.lower(), f"migration file: {path}"
        source = path.read_text(encoding="utf-8")
        for token in forbidden_tokens:
            assert token not in source, f"{path.name} contains DDL token {token}"
    assert not (HEALTH_CORE / "migrations").exists()


def test_no_secret_or_real_identifier_literals_in_source() -> None:
    """String literals contain no national-id-shaped value, phone or credential."""
    import re

    patterns = (
        re.compile(r"^\d{9,}$"),
        re.compile(r"\+?964\d{9,}"),
        re.compile(r"(?i)\b(nhid|national[_-]?id|api[_-]?key|password\s*=|secret\s*=)\b"),
    )
    violations: list[str] = []
    for path, tree in _trees():
        docstrings: set[int] = set()
        for node in ast.walk(tree):
            if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
                doc = ast.get_docstring(node, clean=False)
                if doc is not None and node.body and isinstance(node.body[0], ast.Expr):
                    docstrings.add(id(node.body[0]))
                    docstrings.add(id(node.body[0].value))
        for node in ast.walk(tree):
            if not isinstance(node, ast.Constant) or not isinstance(node.value, str):
                continue
            if id(node) in docstrings:
                continue
            for pattern in patterns:
                if pattern.search(node.value):
                    violations.append(f"{path.relative_to(BACKEND_ROOT)}:{node.lineno} {node.value[:40]!r}")
    assert not violations, "sensitive literal found:\n" + "\n".join(violations)


def test_health_core_test_suite_has_no_skipped_or_xfail_tests() -> None:
    """No test in the reviewed suite is skipped, xfailed or conditionally disabled."""
    violations: list[str] = []
    for path in sorted(TEST_DIR.glob("test_*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                for decorator in node.decorator_list:
                    text = ast.unparse(decorator)
                    lowered = text.lower()
                    if "skip" in lowered or "xfail" in lowered:
                        violations.append(f"{path.name}:{node.lineno} {text}")
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
                attr = node.func.attr
                if attr in {"skip", "xfail", "skipif"} and ast.unparse(node.func.value) == "pytest":
                    violations.append(f"{path.name}:{node.lineno} pytest.{attr}")
    assert not violations, "skipped/xfail tests:\n" + "\n".join(violations)


def test_all_test_functions_contain_an_assertion_or_raising_validator() -> None:
    """No assertion was deleted: every test function checks an outcome."""
    weak: list[str] = []
    for path in sorted(TEST_DIR.glob("test_*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) or not node.name.startswith("test_"):
                continue
            checks = False
            for child in ast.walk(node):
                if isinstance(child, ast.Assert):
                    checks = True
                if (
                    isinstance(child, ast.Call)
                    and isinstance(child.func, ast.Attribute)
                    and isinstance(child.func.value, ast.Name)
                    and child.func.value.id == "pytest"
                    and child.func.attr in {"raises", "warns"}
                ):
                    checks = True
                if (
                    (
                        isinstance(child, ast.Call)
                        and isinstance(child.func, ast.Attribute)
                        and child.func.attr
                        in {
                            "validate_domain_event",
                            "assert_no_silent_drops",
                            "assert_valid_boundaries",
                        }
                    )
                    or (
                        isinstance(child, ast.Call)
                        and isinstance(child.func, ast.Name)
                        and child.func.id
                        in {
                            "validate_domain_event",
                            "assert_no_silent_drops",
                            "assert_valid_boundaries",
                        }
                    )
                ):
                    checks = True
            if not checks:
                weak.append(f"{path.name}:{node.lineno} {node.name}")
    assert not weak, "tests without assertion:\n" + "\n".join(weak)
