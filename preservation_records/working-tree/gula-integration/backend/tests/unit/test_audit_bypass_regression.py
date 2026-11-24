"""Regression tests for AUDIT-BYPASS-001.

``app.routes.ai._emit_critical_alert`` previously constructed ``AuditLog``
directly. Because ``AuditLog.chain_hash`` has no default, those rows were
written with a NULL chain hash and were SKIPPED by ``verify_audit_chain`` —
placing critical-result clinical alerts outside the tamper-evident audit chain.

The fix routes the write through the single canonical writer
``app.services.audit_service.log_action``. These tests guard both the structural
property (no direct AuditLog construction remains in any route module) and the
behavioural property (the emitted alert is chained and correctly attributed).

All identifiers and payloads are synthetic. No production data is used.
"""

from __future__ import annotations

import ast
import json
import pathlib

APP_DIR = pathlib.Path(__file__).resolve().parents[2] / "app"
ROUTES_DIR = APP_DIR / "routes"


def _direct_auditlog_constructions(source: str) -> list[int]:
    """Line numbers of direct ``AuditLog(...)`` constructions in a source string.

    Detects three bypass forms so the guard cannot be evaded by aliasing:
      1. bare ``AuditLog(...)``;
      2. attribute form ``models.AuditLog(...)`;
      3. aliased import ``from ... import AuditLog as X`` then ``X(...)``.

    The read-side use ``db.query(AuditLog)`` is NOT a construction (AuditLog is
    an argument, not a callee) and is correctly ignored.
    """
    tree = ast.parse(source)
    aliases: set[str] = {"AuditLog"}
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            for alias in node.names:
                if alias.name == "AuditLog":
                    aliases.add(alias.asname or alias.name)
    hits: list[int] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        is_bare = isinstance(func, ast.Name) and func.id in aliases
        is_attribute = isinstance(func, ast.Attribute) and func.attr == "AuditLog"
        if is_bare or is_attribute:
            hits.append(node.lineno)
    return hits


def test_no_direct_auditlog_construction_in_any_route_module():
    """No HTTP route module may bypass the canonical chained audit writer."""
    offenders: list[str] = []
    for path in ROUTES_DIR.rglob("*.py"):
        hits = _direct_auditlog_constructions(path.read_text(encoding="utf-8"))
        for line in hits:
            offenders.append(f"{path.relative_to(APP_DIR)}:{line}")
    assert offenders == [], "direct AuditLog construction in routes: " + ", ".join(offenders)


def test_critical_alert_is_written_through_canonical_chained_writer(db, monkeypatch, tmp_path):
    """The emitted critical alert has a non-NULL chain hash and correct fields."""
    from app.models.audit_log import AuditLog
    from app.routes.ai import _emit_critical_alert
    from app.services import audit_service

    # Prevent anchor-file side effects (anchor behaviour is covered elsewhere).
    monkeypatch.setattr(audit_service, "_ANCHOR_DIR", tmp_path)
    monkeypatch.setattr(audit_service, "_ANCHOR_INTERVAL", 10**9)
    monkeypatch.setattr(audit_service, "_write_anchor", lambda *_a, **_k: None)

    _emit_critical_alert(
        db,
        order_id=4242,
        critical_tests=["SYN-TROPONIN", "SYN-K"],
        token_prefix="SYN-TOKEN",
    )

    row = (
        db.query(AuditLog)
        .filter(AuditLog.action == "critical_result_alert")
        .order_by(AuditLog.id.desc())
        .first()
    )
    assert row is not None
    assert row.resource_type == "lab_order"
    assert row.resource_id == 4242
    assert row.user_role == "system:ai"
    assert row.user_id is None
    assert row.chain_hash is not None and len(row.chain_hash) == 64
    assert json.loads(row.details) == {
        "critical_tests": ["SYN-TROPONIN", "SYN-K"],
        "token_prefix": "SYN-TOKEN",
        "source": "ai_interpret",
    }


def test_critical_alert_is_included_in_chain_verification(db, monkeypatch, tmp_path):
    """verify_audit_chain sees the critical alert (it is no longer skipped)."""
    from app.models.audit_log import AuditLog
    from app.routes.ai import _emit_critical_alert
    from app.services import audit_service

    monkeypatch.setattr(audit_service, "_ANCHOR_DIR", tmp_path)
    monkeypatch.setattr(audit_service, "_ANCHOR_INTERVAL", 10**9)
    monkeypatch.setattr(audit_service, "_write_anchor", lambda *_a, **_k: None)

    emitting = _emit_critical_alert
    emitting(db, order_id=9001, critical_tests=["SYN-CRIT"], token_prefix="SYN-P")

    row = (
        db.query(AuditLog)
        .filter(AuditLog.action == "critical_result_alert")
        .order_by(AuditLog.id.desc())
        .first()
    )
    assert row is not None and row.chain_hash is not None
    report = audit_service.verify_audit_chain(db)
    assert report["verified"] is True
    assert report["status"] in {"intact", "empty"}
    assert report["entries_checked"] >= 1
