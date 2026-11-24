"""P-04 / AUD-F04 — standalone audit verifier must use the canonical algorithm.

Synthetic-only regression tests against the disposable SQLite test DB. The
verifier is loaded directly from ``scripts/audit_verifier.py`` so the guardian's
subprocess contract (exit 0 intact/empty, 1 tampered, 2 error) is pinned without
touching production services, anchors or secrets.
"""

from __future__ import annotations

import ast
import importlib.util
import sys
from pathlib import Path

from app.models.audit_log import AuditLog
from app.services import audit_service as canonical
from app.services.audit_service import log_action

REPO_ROOT = Path(__file__).resolve().parents[2]
VERIFIER = REPO_ROOT / "scripts" / "audit_verifier.py"


def _load():
    """Load the real standalone verifier module under an isolated name."""
    spec = importlib.util.spec_from_file_location("gula_audit_verifier_f04", VERIFIER)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _one_chained_entry(db):
    log_action(
        db,
        action="control.f04_check",
        resource_type="config",
        resource_id=1,
        user_id=1,
        lab_id=1,
        details={"synthetic": True},
    )
    assert canonical.verify_audit_chain(db)["verified"] is True
    return db.query(AuditLog).one()


def test_f04_intact_canonical_chain_is_not_reported_as_tamper(db, monkeypatch, capsys):
    """The true defect: a healthy canonical chain was reported as tampered."""
    _one_chained_entry(db)
    module = _load()
    monkeypatch.setattr(module, "SessionLocal", lambda: db)
    module.verify_chain()  # must not raise SystemExit(1)
    output = capsys.readouterr().out
    assert "TAMPER DETECTED" not in output
    assert "Integrity Verified" in output


def test_f04_tampered_row_returns_exit_one(db, capsys):
    module = _load()
    entry = _one_chained_entry(db)
    entry.action = "control.f04_tampered"
    db.flush()
    assert module.verify_chain(db) == 1
    assert "TAMPER DETECTED" in capsys.readouterr().out


def test_f04_empty_log_returns_zero(monkeypatch, capsys):
    module = _load()

    class _Scalar:
        def scalar(self):
            return 0

    class _FakeDb:
        def query(self, *_args):
            return _Scalar()

    monkeypatch.setattr(
        module.canonical,
        "verify_audit_chain",
        lambda *_a, **_k: {"status": "empty", "verified": True, "entries_checked": 0, "broken_entries": []},
    )
    assert module.verify_chain(_FakeDb()) == 0
    assert "empty" in capsys.readouterr().out


def test_f04_source_delegates_to_canonical_verifier():
    source = VERIFIER.read_text(encoding="utf-8")
    assert "def compute_hash" not in source, "standalone verifier still forks the hash algorithm"
    assert "hashlib" not in source, "standalone verifier still computes its own SHA-256"
    assert "verify_audit_chain" in source
    tree = ast.parse(source)
    verify_fn = next(
        node
        for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.name == "verify_chain"
    )
    assert not any(
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr in {"exit", "SystemExit"}
        for node in ast.walk(verify_fn)
    ), "verify_chain must return an exit code; only main() may call sys.exit"


def test_f04_checks_beyond_canonical_default_limit(monkeypatch, capsys):
    """The canonical helper defaults to 1000 rows; the tool must cover the whole log."""
    module = _load()
    seen: list[int] = []

    class _Scalar:
        def scalar(self):
            return 1500

    class _FakeDb:
        def query(self, *_args):
            return _Scalar()

    def fake_verify(_db, limit=1000):
        seen.append(limit)
        return {
            "status": "intact",
            "verified": True,
            "entries_checked": limit,
            "broken_entries": [],
        }

    monkeypatch.setattr(module.canonical, "verify_audit_chain", fake_verify)
    assert module.verify_chain(_FakeDb()) == 0
    assert seen and seen[0] >= 1500, f"verifier capped at canonical default: {seen}"


def test_f04_verification_error_returns_distinct_exit_code(monkeypatch, capsys):
    """Errors must be non-zero (guardian alerts) but distinct from tampering."""
    module = _load()

    class _BrokenDb:
        def query(self, *_args):
            raise RuntimeError("synthetic verification failure")

    assert module.verify_chain(_BrokenDb()) == 2
    assert "TAMPER DETECTED" not in capsys.readouterr().out
