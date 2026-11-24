"""P-13 / AUD-F15 — financial audit integrity regression tests.

Every test in this module uses synthetic data, an isolated SQLite test database,
and a feature-flagged in-process call. No production service, real financial
record, PHI, or secret is used.

The tests are written against the required behaviour (audit and financial
mutation commit atomically, with a compatible canonical log_action signature).
They fail against the pre-fix implementation.
"""

from __future__ import annotations

import ast
import inspect
from pathlib import Path
from types import SimpleNamespace

import pytest
from app.financial import routes as financial_routes
from app.financial import services as financial_services
from app.financial.models import FinProvider, FinTransaction
from app.models.audit_log import AuditLog
from app.services import audit_service
from app.services.audit_service import log_action, verify_audit_chain

ROUTES_PATH = Path(__file__).resolve().parents[1] / "app" / "financial" / "routes.py"


def _log_action_calls(source: str) -> list[ast.Call]:
    tree = ast.parse(source)
    return [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "log_action"
    ]


@pytest.fixture()
def financial_enabled(monkeypatch):
    """Enable the financial engine inside this test process only."""
    monkeypatch.setattr(financial_routes, "ENABLE_FINANCIAL_ENGINE", True)
    monkeypatch.setattr(financial_services, "_engine_enabled", lambda: True)


@pytest.fixture()
def provider(db, make_lab, financial_enabled):
    lab = make_lab()
    row = FinProvider(lab_id=lab.id, name="Synthetic provider", status="active")
    db.add(row)
    db.flush()
    return lab, row


def test_p13_every_financial_log_action_keyword_matches_canonical_signature():
    """AUD-F15: invalid keywords raised TypeError after the money was committed."""
    signature = inspect.signature(log_action)
    calls = _log_action_calls(ROUTES_PATH.read_text(encoding="utf-8"))
    assert calls, "expected canonical audit calls in financial routes"

    invalid = [
        (call.lineno, keyword.arg)
        for call in calls
        for keyword in call.keywords
        if keyword.arg not in signature.parameters
    ]
    assert invalid == [], f"invalid log_action keywords: {invalid}"


def test_p13_transaction_audit_is_written_before_commit(db, provider, monkeypatch):
    """Audit flush must precede the financial commit, or a 500 loses the trail."""
    lab, _ = provider
    events: list[str] = []

    def _audit_spy(**kwargs):
        events.append("audit")
        return

    original_commit = db.commit

    def _commit_spy():
        events.append("commit")
        return original_commit()

    monkeypatch.setattr(financial_routes, "log_action", _audit_spy)
    monkeypatch.setattr(db, "commit", _commit_spy)

    financial_routes.create_transaction(
        amount=100.0,
        description="synthetic transaction",
        transaction_type="billing",
        current_user=SimpleNamespace(id=1, lab_id=lab.id),
        db=db,
    )
    assert events == ["audit", "commit"], events


def test_p13_transaction_success_writes_one_chained_audit_row(db, provider):
    """One request => exactly one financial mutation and one compatible audit row."""
    lab, _ = provider
    before_txns = db.query(FinTransaction).count()
    before_audit = db.query(AuditLog).filter_by(action="financial.transaction.created").count()

    response = financial_routes.create_transaction(
        amount=150.25,
        description="synthetic success",
        transaction_type="billing",
        current_user=SimpleNamespace(id=1, lab_id=lab.id),
        db=db,
    )

    assert response["status"] == "pending"
    assert response["amount"] == 150.25
    assert db.query(FinTransaction).count() == before_txns + 1
    rows = (
        db.query(AuditLog)
        .filter_by(action="financial.transaction.created")
        .order_by(AuditLog.id)
        .all()
    )
    assert len(rows) == before_audit + 1
    row = rows[-1]
    assert row.resource_type == "fin_transaction"
    assert row.resource_id == response["id"]
    assert verify_audit_chain(db)["verified"] is True


def test_p13_audit_failure_blocks_financial_commit(db, provider, monkeypatch):
    """A failed audit cannot leave a committed, unaudited financial mutation."""

    events: list[str] = []

    def _failing_audit(**kwargs):
        events.append("audit")
        raise RuntimeError("synthetic audit outage")

    original_commit = db.commit

    def _commit_spy():
        events.append("commit")
        return original_commit()

    monkeypatch.setattr(financial_routes, "log_action", _failing_audit)
    monkeypatch.setattr(db, "commit", _commit_spy)
    before = db.query(FinTransaction).count()

    with pytest.raises(RuntimeError, match="synthetic audit outage"):
        financial_routes.create_transaction(
            amount=999.0,
            description="must not be committed",
            transaction_type="billing",
            current_user=SimpleNamespace(id=1, lab_id=provider[0].id),
            db=db,
        )

    assert events == ["audit"], events
    db.rollback()
    assert db.query(FinTransaction).count() == before


def test_p13_real_canonical_audit_failure_rolls_back_money(db, provider, monkeypatch):
    """M1: force the REAL canonical writer to fail after flush, not a spy.

    The transaction row is flushed before log_action; a failure inside the
    canonical writer must leave it uncommitted so the request dependency can
    roll it back. No mocked audit function is used here.
    """
    lab, _ = provider
    before = db.query(FinTransaction).count()

    def _boom(*args, **kwargs):
        raise RuntimeError("synthetic canonical audit outage")

    # The real log_action resolves AuditLog from its own module globals.
    monkeypatch.setattr(audit_service, "AuditLog", _boom)

    with pytest.raises(RuntimeError, match="synthetic canonical audit outage"):
        financial_routes.create_transaction(
            amount=777.0,
            description="real audit failure",
            transaction_type="billing",
            current_user=SimpleNamespace(id=1, lab_id=lab.id),
            db=db,
        )

    db.rollback()
    assert db.query(FinTransaction).count() == before


def test_p13_financial_engine_disabled_returns_404_and_writes_nothing(db, monkeypatch):
    """Default production posture stays disabled; no mutation and no audit row."""
    monkeypatch.setattr(financial_routes, "ENABLE_FINANCIAL_ENGINE", False)
    before_txns = db.query(FinTransaction).count()
    before_audit = db.query(AuditLog).count()

    with pytest.raises(Exception) as exc:
        financial_routes.create_transaction(
            amount=10.0,
            transaction_type="billing",
            current_user=SimpleNamespace(id=1, lab_id=1),
            db=db,
        )
    assert getattr(exc.value, "status_code", None) == 404
    assert db.query(FinTransaction).count() == before_txns
    assert db.query(AuditLog).count() == before_audit


def test_p13_billing_cycle_audit_is_written_before_commit(db, provider, monkeypatch):
    """The run-cycle path has the same commit-before-audit defect."""
    lab, _ = provider
    events: list[str] = []

    monkeypatch.setattr(
        financial_routes.BillingService,
        "run_billing_cycle",
        staticmethod(lambda _db: []),
    )

    def _audit_spy(**kwargs):
        events.append("audit")

    original_commit = db.commit

    def _commit_spy():
        events.append("commit")
        return original_commit()

    monkeypatch.setattr(financial_routes, "log_action", _audit_spy)
    monkeypatch.setattr(db, "commit", _commit_spy)

    result = financial_routes.run_billing_cycle(
        current_user=SimpleNamespace(id=1, lab_id=lab.id),
        db=db,
    )
    assert result["invoices_generated"] == 0
    assert events == ["audit", "commit"], events


def test_p13_billing_cycle_success_writes_chainable_audit_row(db, provider):
    """Run-cycle succeeds with a compatible canonical resource_type."""
    lab, _ = provider
    before = db.query(AuditLog).filter_by(action="financial.billing.cycle_run").count()

    result = financial_routes.run_billing_cycle(
        current_user=SimpleNamespace(id=1, lab_id=lab.id),
        db=db,
    )

    assert "invoices_generated" in result
    rows = (
        db.query(AuditLog)
        .filter_by(action="financial.billing.cycle_run")
        .order_by(AuditLog.id)
        .all()
    )
    assert len(rows) == before + 1
    assert rows[-1].resource_type == "fin_billing_cycle"
    assert verify_audit_chain(db)["verified"] is True
