"""Regression tests for AUDIT-POSITIONAL-001.

Commit ``aae20c89`` inserted ``lab_id`` immediately before ``details`` in the
canonical ``app.services.audit_service.log_action`` signature. Dozens of
call sites written earlier passed their arguments positionally, so entity IDs
landed in ``resource_type``, lab IDs in ``user_role`` and detail strings/dicts
in ``lab_id``. The tamper-evident audit log is a protected GULA feature.

These tests guard three layers:
  1. Whole-tree structural guard: no ``log_action`` call may pass more than two
     positional arguments (``db`` and ``action`` may stay positional).
  2. Call-site guard: every fixed call names ``resource_type`` and ``details``
     explicitly with keywords, so a future slot insertion cannot silently
     re-map them.
  3. Behavioural proof: keyword arguments land in the correct ``AuditLog``
     columns, including dict serialisation for ``details``.

All identifiers and payloads are synthetic. No production data is used.
"""

from __future__ import annotations

import ast
import json
import pathlib

import pytest

APP_DIR = pathlib.Path(__file__).resolve().parents[2] / "app"

# The eight files that carried the broken positional calls.
TARGET_FILES = (
    "lims/routes.py",
    "lims/services.py",
    "nhdw/offline.py",
    "nhdw/services.py",
    "nursing/coordination.py",
    "nursing/medication.py",
    "nursing/services.py",
    "services/hospital_service.py",
)


def _log_action_calls(source: str):
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        name = (
            func.id
            if isinstance(func, ast.Name)
            else (func.attr if isinstance(func, ast.Attribute) else None)
        )
        if name == "log_action":
            yield node


def _keyword_names(call: ast.Call) -> set[str]:
    return {kw.arg for kw in call.keywords if kw.arg is not None}


def test_no_positional_log_action_calls_over_two():
    """No call anywhere in the backend may pass >2 positional args.

    ``db`` and ``action`` are the only positional slots permitted; all optional
    audit fields must be keywords. This is the exact class of defect that
    AUDIT-POSITIONAL-001 introduced.
    """
    offenders: list[str] = []
    for path in APP_DIR.rglob("*.py"):
        try:
            source = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):  # pragma: no cover - defensive
            continue
        try:
            for call in _log_action_calls(source):
                if len(call.args) > 2:
                    offenders.append(f"{path.relative_to(APP_DIR)}:{call.lineno} ({len(call.args)} args)")
        except SyntaxError:  # pragma: no cover - generated/vendor files
            continue
    assert offenders == [], "positional log_action calls remain: " + ", ".join(offenders)


@pytest.mark.parametrize("relative", TARGET_FILES)
def test_fixed_call_sites_use_explicit_keywords(relative: str):
    """Every fixed call names ``resource_type``; calls with payload name ``details``."""
    path = APP_DIR / relative
    source = path.read_text(encoding="utf-8")
    calls = list(_log_action_calls(source))
    assert calls, f"expected log_action calls in {relative}"
    for call in calls:
        keywords = _keyword_names(call)
        assert "resource_type" in keywords, (
            f"{relative}:{call.lineno}: resource_type must be an explicit keyword"
        )
        # A resource_type must be a literal string, never an entity ID.
        rt = next(kw.value for kw in call.keywords if kw.arg == "resource_type")
        assert isinstance(rt, ast.Constant) and isinstance(rt.value, str), (
            f"{relative}:{call.lineno}: resource_type must be a string constant"
        )
        # user_role must never receive a dict/list (the old mis-mapping).
        for kw in call.keywords:
            if kw.arg == "user_role":
                assert not isinstance(kw.value, (ast.Dict, ast.List)), (
                    f"{relative}:{call.lineno}: user_role must not hold a payload"
                )


def test_log_action_keyword_mapping_populates_correct_columns(db, monkeypatch, tmp_path):
    """Keyword arguments land in the correct AuditLog columns."""
    from app.models.audit_log import AuditLog
    from app.services import audit_service

    # Prevent anchor-file side effects. Anchor writing is covered elsewhere.
    monkeypatch.setattr(audit_service, "_ANCHOR_DIR", tmp_path)
    monkeypatch.setattr(audit_service, "_ANCHOR_INTERVAL", 10**9)
    monkeypatch.setattr(audit_service, "_write_anchor", lambda *_args, **_kwargs: None)

    audit_service.log_action(
        db,
        action="hospital.create",
        resource_type="hospital",
        resource_id=4242,
        lab_id=77,
        user_id=99,
        user_role="hospital_admin",
        details={"code": "SYN-H-1", "note": "synthetic"},
        ip_address="127.0.0.1",
    )

    row = db.query(AuditLog).order_by(AuditLog.id.desc()).first()
    assert row is not None
    assert row.action == "hospital.create"
    assert row.resource_type == "hospital"
    assert isinstance(row.resource_type, str)
    assert row.resource_id == 4242
    assert row.lab_id == 77
    assert row.user_id == 99
    assert row.user_role == "hospital_admin"
    assert json.loads(row.details) == {"code": "SYN-H-1", "note": "synthetic"}
    assert row.ip_address == "127.0.0.1"
    assert row.chain_hash  # tamper-evident chain still computed


def test_log_action_string_details_are_not_json_encoded(db, monkeypatch, tmp_path):
    """String details pass through unchanged (dicts are JSON-serialised)."""
    from app.models.audit_log import AuditLog
    from app.services import audit_service

    monkeypatch.setattr(audit_service, "_ANCHOR_DIR", tmp_path)
    monkeypatch.setattr(audit_service, "_ANCHOR_INTERVAL", 10**9)
    monkeypatch.setattr(audit_service, "_write_anchor", lambda *_args, **_kwargs: None)

    audit_service.log_action(
        db,
        action="nhdw.sync.apply_batch",
        resource_type="nhdw_sync",
        lab_id=77,
        user_id=99,
        details="Synthetic batch applied",
    )

    row = db.query(AuditLog).order_by(AuditLog.id.desc()).first()
    assert row is not None
    assert row.resource_type == "nhdw_sync"
    assert row.details == "Synthetic batch applied"
