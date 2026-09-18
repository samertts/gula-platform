"""Governance mutations reach the canonical audit chain, and it exists (NR-109).

`GovernanceRepository._write_audit` ran on every create, update and delete of
every governance entity -- identity records, QR codes, recovery requests,
guardians, break-glass access grants, merge proposals, merged identity records.
It wrote a `HealthNumberAudit` row, and it was wrong four ways at once, which is
why it survived a detector, a reviewer and a passing test suite:

1. The table it wrote, `gov_health_number_audit`, is mapped by the ORM and
   built by NO migration. Executed against PostgreSQL at 20260916_0001: adding
   a break-glass record and flushing raised
       ProgrammingError: relation "gov_health_number_audit" does not exist
   while all six governance entity tables were built. Every write through this
   class failed at flush, emergency break-glass grants included.
2. It put the entity's id in the `health_number` column, so a break-glass grant
   and an identity merge were recorded as health-number events -- polluting the
   one trail an auditor would query for a health number's history.
3. `changed_by` was the literal "system" for every caller.
4. It is not the SHA-256 chained `audit_logs`, so it was not tamper-evident.

`audit_resource` was already supplied correctly by the subclasses --
`BreakGlassAccessRepository` passes "gov_break_glass" -- stored, and then never
read.

WHY THE SUITE WAS GREEN. `test_persisted_identity_governance.py` builds its
schema with `GovernanceBase.metadata.create_all`, so it CREATED
`gov_health_number_audit` and tested against a table production does not have.
That is NR-036 in one file: a schema built from ORM metadata certifies the ORM,
not the database.
"""
from __future__ import annotations

import ast
import os
from pathlib import Path

import pytest

from .orm_resolution import built_tables, qualified_models

_BACKEND = Path(__file__).resolve().parents[1]
_APP = _BACKEND / "app"
_GOV_BASE = _APP / "governance" / "repositories" / "base.py"

#: Function names that mean "this writes an audit record".
_AUDIT_WRITERS = ("_write_audit", "write_audit", "log_audit", "record_audit")


#: Audit writers whose target table no migration builds, and which are NOT
#: NR-109's defect. Both write a rich, correct, domain-specific record -- the
#: MPI one is itself SHA-256 hash-chained with a prev_hash and a real
#: decided_by_user_id -- so rewriting them onto log_action would LOSE evidence,
#: not add it. What they need is the table, and creating a table is a migration:
#: CLAUDE.md reserves DB schema changes for human approval, so they are declared
#: here rather than guessed at.
#:
#: SHRINK-ONLY. An entry leaves when its migration lands. A NEW audit writer
#: pointed at an unbuilt table is NR-109 again and fails the test above.
DECLARED_UNBUILT_AUDIT_TARGETS: dict[str, str] = {
    "national_merge_audit":
        "app/services/mpi/resolver.py::_write_audit -- Master Patient Index "
        "merge decisions. Already hash-chained (prev_hash + canonical JSON + "
        "SHA-256) and already records the deciding user. Needs a migration.",
    "gov_national_audit_events":
        "app/governance/services/security_governance_service.py::"
        "log_audit_event -- national security audit events, with actor_id, "
        "actor_role, resource, action, status, severity, ip_address and "
        "node_id. This is what POST /governance/audit-events writes, so that "
        "endpoint still cannot succeed even now that NR-108 has authenticated "
        "it. Needs a migration.",
}

#: The ledger is a ratchet.
_UNBUILT_CEILING = 2


def _source(path: Path) -> str:
    return path.read_text(encoding="utf-8")


# --------------------------------------------------------------------------
# The specific repair
# --------------------------------------------------------------------------

def test_the_governance_repository_writes_the_canonical_chained_log() -> None:
    src = _source(_GOV_BASE)
    tree = ast.parse(src)
    writer = next(
        (n for n in ast.walk(tree)
         if isinstance(n, ast.FunctionDef) and n.name == "_write_audit"),
        None,
    )
    assert writer is not None, (
        "_write_audit is gone from GovernanceRepository; if auditing moved, "
        "point this test at wherever it moved to rather than deleting it"
    )
    # Strip the docstring before scanning. The rewritten _write_audit explains
    # the defect in prose, and the prose necessarily contains the strings this
    # test looks for -- a scan of the whole function accused the explanation.
    code = list(writer.body)
    if code and isinstance(code[0], ast.Expr) and isinstance(code[0].value, ast.Constant) \
            and isinstance(code[0].value.value, str):
        code = code[1:]
    body = "\n".join(ast.unparse(stmt) for stmt in code)
    assert "log_action(" in body, (
        "the governance repository no longer calls log_action, so its "
        "mutations are outside the hash-chained audit log again"
    )
    assert "HealthNumberAudit" not in body, (
        "the governance repository is writing HealthNumberAudit again. That "
        "table is built by no migration, and it records every entity as a "
        "health-number event"
    )
    # Precise, not a substring. A substring check passed a perturbation that
    # replaced `resource_type=self._audit_resource` with a literal, because
    # the identifier still appeared in the action string on the line above --
    # the guard would have let the defect back in while reporting green.
    call = next(
        (n for n in ast.walk(writer)
         if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)
         and n.func.id == "log_action"),
        None,
    )
    assert call is not None, "log_action is not called by name in _write_audit"
    resource_type = next(
        (kw.value for kw in call.keywords if kw.arg == "resource_type"), None,
    )
    assert resource_type is not None, (
        "log_action is called without resource_type, so every governance "
        "entity lands in the audit log unlabelled"
    )
    assert ast.unparse(resource_type) == "self._audit_resource", (
        f"_write_audit ignores the audit_resource its subclasses supply and "
        f"passes {ast.unparse(resource_type)!r} instead, so every entity is "
        f"recorded under the wrong resource type -- the exact defect NR-109 "
        f"fixed. BreakGlassAccessRepository declares 'gov_break_glass' and "
        f"expects it to be used."
    )
    assert '"system"' not in body and "'system'" not in body, (
        "the actor is hard-coded again; an unattributed NULL is honest, "
        'a literal "system" is a false claim about who acted'
    )


def test_every_governance_repository_declares_what_it_audits() -> None:
    """Guard the guard: subclasses must exist, and must name their resource."""
    repos = _APP / "governance" / "repositories"
    declared: dict[str, str] = {}
    subclasses = 0
    for path in sorted(repos.glob("*.py")):
        if path.name == "base.py":
            continue
        tree = ast.parse(_source(path))
        for cls in (n for n in ast.walk(tree) if isinstance(n, ast.ClassDef)):
            if not any("GovernanceRepository" in ast.unparse(b) for b in cls.bases):
                continue
            subclasses += 1
            body = ast.unparse(cls)
            if "audit_resource=" in body:
                declared[cls.name] = body
    assert subclasses >= 5, (
        f"only {subclasses} GovernanceRepository subclasses found; the scan "
        f"has stopped seeing them and every assertion here is vacuous"
    )
    assert declared, (
        "no subclass passes audit_resource=, so the resource type this test "
        "checks is never exercised"
    )


# --------------------------------------------------------------------------
# The defect CLASS, not just this instance
# --------------------------------------------------------------------------

def test_no_audit_writer_targets_a_table_no_migration_builds() -> None:
    """An audit row written to a table that does not exist audits nothing.

    Worse than nothing: it raises inside the caller's transaction and takes the
    operation it was meant to record down with it. This is the generalisation
    of NR-109 -- the same shape could appear in any package.
    """
    models = qualified_models()          # (module, class) -> tablename
    by_class: dict[str, set[str]] = {}
    for (_module, cls), table in models.items():
        by_class.setdefault(cls, set()).add(table)
    built = built_tables()
    assert len(built) > 300, (
        f"built_tables() returned only {len(built)} tables; the migration scan "
        f"has broken and this test would accuse every writer"
    )

    offenders: list[str] = []
    scanned = 0
    declared = set(DECLARED_UNBUILT_AUDIT_TARGETS)
    for path in sorted(_APP.rglob("*.py")):
        if "__pycache__" in path.parts:
            continue
        try:
            tree = ast.parse(_source(path))
        except (SyntaxError, UnicodeDecodeError):
            continue
        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            if not any(name in node.name for name in _AUDIT_WRITERS):
                continue
            scanned += 1
            for call in ast.walk(node):
                if not (isinstance(call, ast.Call) and isinstance(call.func, ast.Name)):
                    continue
                tables = by_class.get(call.func.id)
                if not tables:
                    continue
                for table in tables:
                    if table not in built and table not in declared:
                        offenders.append(
                            f"{path.relative_to(_BACKEND)}:{node.name} writes "
                            f"{call.func.id} -> {table}, which no migration builds"
                        )
    assert scanned >= 1, (
        "no audit-writing function was found at all, so this scan proves "
        "nothing; the naming convention it keys on has changed"
    )
    assert not offenders, "\n".join(offenders)


def test_the_unbuilt_audit_ledger_cannot_grow() -> None:
    assert len(DECLARED_UNBUILT_AUDIT_TARGETS) <= _UNBUILT_CEILING, (
        f"DECLARED_UNBUILT_AUDIT_TARGETS has "
        f"{len(DECLARED_UNBUILT_AUDIT_TARGETS)} entries, above the ceiling of "
        f"{_UNBUILT_CEILING}. It may only shrink: a new audit writer aimed at "
        f"a table no migration builds is the NR-109 defect, not a new "
        f"exemption."
    )


def test_the_unbuilt_audit_ledger_has_not_rotted() -> None:
    """An entry must leave once its migration lands."""
    built = built_tables()
    now_built = sorted(t for t in DECLARED_UNBUILT_AUDIT_TARGETS if t in built)
    assert not now_built, (
        f"these tables are now built by a migration: {now_built}. Remove them "
        f"from DECLARED_UNBUILT_AUDIT_TARGETS -- that is the ratchet "
        f"tightening, which is the point."
    )


def test_the_resource_id_normaliser_has_exactly_one_implementation() -> None:
    """NR-105 happened because two copies of one rule drifted apart.

    The blood bank service and ClinicalCommandGuard each carried their own
    copy of the varchar-to-INTEGER normalise. Both now delegate to
    audit_service.normalize_resource_id. This pins that.
    """
    from app.services.audit_service import normalize_resource_id

    assert normalize_resource_id(None) is None
    assert normalize_resource_id("41") == 41
    assert normalize_resource_id("f87d5271-812f-471c-a0e3-effca44a1866") is None

    duplicates = []
    for path in sorted(_APP.rglob("*.py")):
        if "__pycache__" in path.parts or path.name == "audit_service.py":
            continue
        src = _source(path)
        if "except (TypeError, ValueError):" in src and "int(resource_id)" in src:
            duplicates.append(str(path.relative_to(_BACKEND)))
    assert not duplicates, (
        f"these modules carry their own copy of the resource-id normalise "
        f"instead of calling audit_service.normalize_resource_id: {duplicates}"
    )


# --------------------------------------------------------------------------
# Execution proof (PostgreSQL only)
# --------------------------------------------------------------------------

_PG_URL = os.environ.get("MIGRATION_DATABASE_URL", "")

pg_only = pytest.mark.skipif(
    "postgres" not in _PG_URL,
    reason="needs the real migrated schema; the point is which tables exist",
)


@pytest.fixture()
def pg_session():
    from app.factory import create_app
    from sqlalchemy import create_engine
    from sqlalchemy.orm import Session, configure_mappers

    create_app()
    configure_mappers()
    engine = create_engine(_PG_URL, future=True)
    conn = engine.connect()
    outer = conn.begin()
    session = Session(bind=conn, join_transaction_mode="create_savepoint")
    try:
        yield session
    finally:
        session.close()
        outer.rollback()
        conn.close()
        engine.dispose()


@pg_only
@pytest.mark.integration
def test_a_break_glass_grant_persists_and_lands_in_the_chain(pg_session) -> None:
    import uuid

    from app.governance.models.identity import GovernanceBreakGlassAccess
    from app.governance.repositories.break_glass_repository import (
        BreakGlassAccessRepository,
    )
    from app.models.audit_log import AuditLog
    from sqlalchemy import inspect, text

    tables = set(inspect(pg_session.get_bind()).get_table_names())
    assert "gov_break_glass_accesses" in tables, (
        "the entity table is missing, so this test cannot say anything about "
        "the audit path"
    )
    assert "gov_health_number_audit" not in tables, (
        "gov_health_number_audit now exists. If a migration built it "
        "deliberately, say so here -- but the governance repositories must "
        "still audit into the chained log, not into a health-number trail"
    )

    repo = BreakGlassAccessRepository(pg_session)
    assert repo._audit_resource == "gov_break_glass"

    access_id = str(uuid.uuid4())
    repo.add(GovernanceBreakGlassAccess(
        id=access_id, user_id="nr109-probe", reason="emergency",
        reason_detail="NR-109", patient_id="nr109-patient",
    ))
    pg_session.flush()

    persisted = pg_session.execute(
        text("select count(*) from gov_break_glass_accesses where id=:i"),
        {"i": access_id},
    ).scalar_one()
    assert persisted == 1, (
        "the break-glass grant did not persist; before NR-109 this raised "
        "ProgrammingError because the audit write targeted a missing table"
    )

    rows = pg_session.query(AuditLog).filter(
        AuditLog.resource_type == "gov_break_glass").all()
    assert len(rows) == 1, f"expected one audit row, got {len(rows)}"
    assert rows[0].action == "governance.gov_break_glass.create"
    assert rows[0].chain_hash, "the audit row is outside the hash chain"
    assert access_id in (rows[0].details or ""), (
        "audit_logs.resource_id is INTEGER and the key is a UUID, so the "
        "unabridged identifier must survive in details or the row names "
        "no resource at all"
    )

    # False-positive check: a resource nobody wrote must come back empty.
    assert pg_session.query(AuditLog).filter(
        AuditLog.resource_type == "gov_never_written").count() == 0
