"""P-01 / AUD-F01 — dormant raw audit writer must delegate to the canonical chain.

Synthetic-only regression tests against the disposable SQLite test DB. No PHI,
production DB, real audit anchor, or secret is used.
"""

from __future__ import annotations

import ast
import json
from pathlib import Path

import pytest
from app.control_plane.audit import EnterpriseAudit
from app.models.audit_log import AuditLog
from app.services.audit_service import log_action, verify_audit_chain

from shared.audit.service import AuditService, create_audit_entry, query_audit_log

SHARED_SERVICE = Path(__file__).resolve().parents[2] / "shared" / "audit" / "service.py"


def test_f01_legacy_writer_creates_canonical_chained_row(db):
    """The legacy entry point must produce a row the canonical verifier accepts."""
    result = create_audit_entry(
        db,
        action="control.test_deploy",
        entity_type="component",
        entity_id=42,
        user_id=1,
        lab_id=1,
        details={"version": "synthetic-1"},
    )
    entry = db.query(AuditLog).filter(AuditLog.action == "control.test_deploy").one()
    assert entry.resource_type == "component"
    assert entry.resource_id == 42
    assert entry.chain_hash is not None
    assert int(result["id"]) == entry.id
    assert verify_audit_chain(db)["verified"] is True


def test_f01_legacy_writer_does_not_commit_callers_transaction(db):
    """Internal commit() breaks caller atomicity and is forbidden in every writer."""
    create_audit_entry(
        db,
        action="control.test_atomic",
        entity_type="component",
        entity_id=43,
        user_id=1,
        lab_id=1,
    )
    assert db.in_transaction(), "legacy audit writer committed the caller's transaction"


def test_f01_legacy_query_reads_canonical_schema(db):
    """Reads must target canonical columns and map back to the legacy shape."""
    log_action(
        db,
        action="control.test_cfg",
        resource_type="config",
        resource_id=7,
        user_id=1,
        lab_id=1,
        details={"k": "synthetic"},
    )
    rows = query_audit_log(db, entity_type="config", entity_id=7)
    assert len(rows) == 1
    assert rows[0]["entity_type"] == "config"
    assert str(rows[0]["entity_id"]) == "7"
    assert rows[0]["chain_hash"] is not None


def test_f01_non_integer_entity_id_is_preserved_in_details(db):
    """String identifiers (config keys, component names) must not be discarded."""
    create_audit_entry(
        db,
        action="control.test_string_id",
        entity_type="config",
        entity_id="smtp.host",
        user_id=1,
        lab_id=1,
        details={"note": "synthetic"},
    )
    entry = db.query(AuditLog).filter(AuditLog.action == "control.test_string_id").one()
    assert entry.resource_id is None
    details = json.loads(entry.details)
    assert details["legacy_entity_id"] == "smtp.host"
    assert details["legacy_entity_type"] == "config"


def test_f01_enterprise_audit_and_service_delegate_to_canonical_writer(db):
    """Both dormant facades must reach the canonical chain, not a second hash algorithm."""
    EnterpriseAudit(db).log_deployment("svc-alpha", "synthetic-1", user_id=1)
    AuditService(db).log("control.test_service", "policy", 9, user_id=1, lab_id=1)
    actions = {row.action for row in db.query(AuditLog).all()}
    assert {"control.deployment", "control.test_service"} <= actions
    assert verify_audit_chain(db)["verified"] is True


def test_f01_source_has_no_raw_insert_no_internal_commit(db):
    """Static guard: no raw audit INSERT and no commit() in any shared audit writer."""
    source = SHARED_SERVICE.read_text(encoding="utf-8")
    assert "INSERT INTO audit_logs" not in source
    tree = ast.parse(source)
    commits = [
        node.lineno
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "commit"
    ]
    assert commits == [], f"internal commit() in shared audit writer at lines {commits}"


def test_f01_concurrent_writer_cannot_hijack_legacy_response(db, monkeypatch):
    """The returned id must identify OUR row even if another writer inserts first."""
    from app.services import audit_service as canonical

    real_log_action = canonical.log_action
    state = {"calls": 0}

    def racing_log_action(**kwargs):
        state["calls"] += 1
        if state["calls"] == 1:
            # Deterministic race: a competing writer that read the same
            # predecessor inserts a lower-id row before our row is selected.
            real_log_action(
                db=db,
                action="control.concurrent_decoy",
                resource_type="component",
                resource_id=999,
                user_id=1,
                lab_id=1,
            )
        return real_log_action(**kwargs)

    monkeypatch.setattr(canonical, "log_action", racing_log_action)
    result = create_audit_entry(
        db,
        action="control.concurrent_target",
        entity_type="component",
        entity_id=1001,
        user_id=1,
        lab_id=1,
    )
    decoy = db.query(AuditLog).filter(AuditLog.action == "control.concurrent_decoy").one()
    ours = db.query(AuditLog).filter(AuditLog.action == "control.concurrent_target").one()
    assert decoy.id < ours.id
    assert result["id"] == ours.id, "legacy response attributed another writer's row"
    assert result["chain_hash"] == ours.chain_hash


def test_f01_non_numeric_entity_id_filter_escapes_like_wildcards(db):
    """A literal '%' in an identifier must not match unrelated rows."""
    create_audit_entry(
        db, action="control.like_abc", entity_type="config", entity_id="abc", user_id=1, lab_id=1
    )
    create_audit_entry(
        db, action="control.like_xyz", entity_type="config", entity_id="xyz", user_id=1, lab_id=1
    )
    assert query_audit_log(db, entity_type="config", entity_id="a%") == []
    exact = query_audit_log(db, entity_type="config", entity_id="abc")
    assert len(exact) == 1
    assert exact[0]["action"] == "control.like_abc"


def test_f01_legacy_hash_is_no_longer_used_by_any_writer():
    """compute_chain_hash may remain for P-04 tooling, but no writer may call it."""
    source = SHARED_SERVICE.read_text(encoding="utf-8")
    tree = ast.parse(source)
    callers = []
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name in {
            "create_audit_entry",
            "log",
            "query_audit_log",
        }:
            for sub in ast.walk(node):
                if (
                    isinstance(sub, ast.Call)
                    and isinstance(sub.func, ast.Name)
                    and sub.func.id == "compute_chain_hash"
                ):
                    callers.append((node.name, sub.lineno))
    assert callers == [], f"legacy hash still used by writers: {callers}"
