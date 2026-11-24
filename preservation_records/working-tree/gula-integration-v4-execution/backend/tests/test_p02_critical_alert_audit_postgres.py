"""P-02 / AUD-F02 — approved PostgreSQL RED/GREEN regression suite (REV3 baseline).

DISPOSABLE POSTGRESQL 16 ONLY.  Set ``GULA_P02_PG_DSN`` to a DSN for the throwaway
database created for this workstream.  The module refuses to run on SQLite.  No
production database, PHI, provider API, secret value or real service is used; every
row inserted here is explicitly synthetic.  The fixtures verify the migrated schema,
the append-only triggers, the READ COMMITTED default and the Alembic head before any
assertion runs.

RED is executed from an untouched ``git archive HEAD`` tree; GREEN from the working
tree.  The import below registers the ``Citizen`` mapper required by an unrelated
HEAD relationship so the failures isolate the P-02 audit-bypass defect itself.
"""

from __future__ import annotations

import asyncio
import hashlib
import os
import threading
from collections.abc import Iterator
from typing import Any

import app.services.mpi.models
import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

DSN = os.getenv("GULA_P02_PG_DSN", "")
pytestmark = pytest.mark.skipif(
    not DSN,
    reason="GULA_P02_PG_DSN is required; a disposable PostgreSQL 16 database is mandatory",
)


@pytest.fixture(scope="module")
def pg_engine() -> Iterator[Any]:
    engine = create_engine(DSN)
    with engine.connect() as conn:
        assert conn.dialect.name == "postgresql", "SQLite substitution is prohibited"
        assert "PostgreSQL 16" in conn.execute(text("SELECT version()")).scalar_one()
        assert conn.execute(text("SELECT version_num FROM alembic_version")).scalar_one() == (
            "20261119_0003"
        )
        assert conn.execute(text("SHOW transaction_isolation")).scalar_one() == "read committed"
        columns = {
            row[0]
            for row in conn.execute(
                text(
                    "SELECT column_name FROM information_schema.columns WHERE table_name='audit_logs'"
                )
            )
        }
        assert {"chain_hash", "lab_id", "action", "resource_type", "resource_id"} <= columns
        triggers = {
            row[0]
            for row in conn.execute(
                text(
                    "SELECT tgname FROM pg_trigger "
                    "WHERE tgrelid='audit_logs'::regclass AND NOT tgisinternal"
                )
            )
        }
        assert {"trg_audit_logs_no_update", "trg_audit_logs_no_delete"} <= triggers
    yield engine
    engine.dispose()


@pytest.fixture(scope="module")
def seed(pg_engine: Any) -> Iterator[dict[str, Any]]:
    with pg_engine.begin() as conn:
        lab_id = conn.execute(
            text(
                "INSERT INTO labs (name, is_active) VALUES ('SYNTHETIC_P02_LAB', true) RETURNING id"
            )
        ).scalar_one()
        patient_id = conn.execute(
            text(
                "INSERT INTO patients (lab_id, full_name, phone) "
                "VALUES (:lid, 'SYNTHETIC_P02_PATIENT', '+0000000000') RETURNING id"
            ),
            {"lid": lab_id},
        ).scalar_one()
        order_id = conn.execute(
            text("INSERT INTO lab_orders (patient_id, lab_id) VALUES (:pid, :lid) RETURNING id"),
            {"pid": patient_id, "lid": lab_id},
        ).scalar_one()
    yield {"lab_id": lab_id, "patient_id": patient_id, "order_id": order_id}
    with pg_engine.begin() as conn:
        conn.execute(text("DELETE FROM lab_orders WHERE id = :oid"), {"oid": order_id})
        conn.execute(text("DELETE FROM patients WHERE id = :pid"), {"pid": patient_id})
        conn.execute(text("DELETE FROM labs WHERE id = :lid"), {"lid": lab_id})


@pytest.fixture()
def clean_audit(pg_engine: Any) -> None:
    with pg_engine.begin() as conn:
        conn.execute(text("TRUNCATE TABLE audit_logs RESTART IDENTITY"))


@pytest.fixture()
def ai_module(monkeypatch: Any, pg_engine: Any) -> Any:
    import app.routes.ai as ai

    monkeypatch.setattr(ai, "SessionLocal", sessionmaker(bind=pg_engine))
    ai._INTERPRET_CACHE.clear()
    return ai


def _alert_rows(pg_engine: Any) -> Any:
    with pg_engine.connect() as conn:
        return (
            conn.execute(
                text(
                    "SELECT id, action, lab_id, chain_hash, resource_id FROM audit_logs ORDER BY id"
                )
            )
            .mappings()
            .all()
        )


def _chain_verified(ai_module: Any) -> bool:
    from app.services.audit_service import verify_audit_chain

    db = ai_module.SessionLocal()
    try:
        return bool(verify_audit_chain(db)["verified"])
    finally:
        db.close()


def test_gate_environment_is_disposable_postgres(pg_engine: Any) -> None:
    """Gate proof is part of the suite: no SQLite and the disposable database is targeted."""
    with pg_engine.connect() as conn:
        assert conn.execute(text("SELECT current_database()")).scalar_one() == "gula_int_gate"


def test_r1_canonical_chain_row(
    pg_engine: Any, clean_audit: Any, seed: dict[str, Any], ai_module: Any
) -> None:
    db = ai_module.SessionLocal()
    try:
        ai_module._emit_critical_alert(db, seed["order_id"], ["SYN_CRIT"], "synthtoken")
    finally:
        db.close()
    rows = _alert_rows(pg_engine)
    assert len(rows) == 1
    assert rows[0]["action"] == "critical_result_alert"
    assert rows[0]["chain_hash"] is not None
    assert _chain_verified(ai_module) is True


def test_r2_failure_propagates(
    monkeypatch: Any, pg_engine: Any, clean_audit: Any, seed: dict[str, Any], ai_module: Any
) -> None:
    def boom(*args: Any, **kwargs: Any) -> Any:
        raise RuntimeError("forced-audit-failure")

    monkeypatch.setattr(ai_module, "log_action", boom, raising=False)
    db = ai_module.SessionLocal()
    with pytest.raises(RuntimeError, match="forced-audit-failure"):
        ai_module._emit_critical_alert(db, seed["order_id"], ["SYN_CRIT"], "synthtoken")
    db.close()
    assert _alert_rows(pg_engine) == []


def test_r3_rollback_preserves_original_error(
    monkeypatch: Any, pg_engine: Any, clean_audit: Any, seed: dict[str, Any], ai_module: Any
) -> None:
    import sqlalchemy.orm as orm

    def boom(*args: Any, **kwargs: Any) -> Any:
        raise ValueError("original-audit-error")

    def bad_rollback(self: Any, *args: Any, **kwargs: Any) -> None:
        raise RuntimeError("rollback-failed")

    monkeypatch.setattr(ai_module, "log_action", boom, raising=False)
    monkeypatch.setattr(orm.Session, "rollback", bad_rollback)
    db = ai_module.SessionLocal()
    with pytest.raises(ValueError, match="original-audit-error"):
        ai_module._emit_critical_alert(db, seed["order_id"], ["SYN_CRIT"], "synthtoken")
    db.close()


def test_r4_lab_id_from_order(
    pg_engine: Any, clean_audit: Any, seed: dict[str, Any], ai_module: Any
) -> None:
    db = ai_module.SessionLocal()
    try:
        ai_module._emit_critical_alert(db, seed["order_id"], ["SYN_CRIT"], "synthtoken")
    finally:
        db.close()
    rows = _alert_rows(pg_engine)
    assert len(rows) == 1
    assert rows[0]["lab_id"] == seed["lab_id"]


def test_r5_caller_signal_before_ai(
    monkeypatch: Any, pg_engine: Any, clean_audit: Any, seed: dict[str, Any], ai_module: Any
) -> None:
    """The public endpoint must abort before any AI provider call on audit failure."""
    token = "SYNTH_P02_R5_TOKEN"
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    with pg_engine.begin() as conn:
        result_id = conn.execute(
            text(
                "INSERT INTO lab_results (order_id, test_name, value, unit, token, token_hash) "
                "VALUES (:oid, 'SYN_CRIT', 999, 'mg/dL', :tok, :thash) RETURNING id"
            ),
            {"oid": seed["order_id"], "tok": token, "thash": token_hash},
        ).scalar_one()

    def boom(*args: Any, **kwargs: Any) -> Any:
        raise RuntimeError("forced-audit-failure")

    ai_called = {"value": False}

    async def fake_ai(prompt: Any) -> tuple[str, str]:
        ai_called["value"] = True
        return "Synthetic Arabic explanation", "synthetic"

    monkeypatch.setattr(ai_module, "log_action", boom, raising=False)
    monkeypatch.setattr(ai_module, "_call_ai_with_fallback", fake_ai)
    monkeypatch.setattr(ai_module, "_build_interpret_prompt", lambda *a, **k: "synthetic-prompt")
    monkeypatch.setattr(ai_module, "_detect_conflicts", lambda *a, **k: [])
    monkeypatch.setattr(
        ai_module,
        "_compute_severities",
        lambda rows: [{**r, "severity": ai_module._SEVERITY_CRITICAL} for r in rows],
    )
    ai_module._INTERPRET_CACHE.clear()

    try:
        with pytest.raises(RuntimeError, match="forced-audit-failure"):
            asyncio.run(ai_module.interpret_result_public(token))
        assert ai_called["value"] is False
        assert _alert_rows(pg_engine) == []
    finally:
        with pg_engine.begin() as conn:
            conn.execute(text("DELETE FROM lab_results WHERE id = :rid"), {"rid": result_id})


def test_r6_concurrent_distinct_alerts(
    pg_engine: Any, clean_audit: Any, seed: dict[str, Any], ai_module: Any
) -> None:
    with pg_engine.begin() as conn:
        patient_id = conn.execute(
            text("SELECT patient_id FROM lab_orders WHERE id = :oid"), {"oid": seed["order_id"]}
        ).scalar_one()
        second_order = conn.execute(
            text("INSERT INTO lab_orders (patient_id, lab_id) VALUES (:pid, :lid) RETURNING id"),
            {"pid": patient_id, "lid": seed["lab_id"]},
        ).scalar_one()
    errors: list[Exception] = []

    def run(order_id: Any) -> None:
        db = ai_module.SessionLocal()
        try:
            ai_module._emit_critical_alert(db, order_id, ["SYN_CRIT"], "synthtoken")
        except Exception as exc:
            errors.append(exc)
        finally:
            db.close()

    threads = [
        threading.Thread(target=run, args=(oid,)) for oid in (seed["order_id"], second_order)
    ]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    assert errors == []
    rows = _alert_rows(pg_engine)
    assert len(rows) == 2
    assert _chain_verified(ai_module) is True
    with pg_engine.begin() as conn:
        conn.execute(text("DELETE FROM lab_orders WHERE id = :oid"), {"oid": second_order})


def test_r7_commit_survives_session_close(
    pg_engine: Any, clean_audit: Any, seed: dict[str, Any], ai_module: Any
) -> None:
    db = ai_module.SessionLocal()
    try:
        ai_module._emit_critical_alert(db, seed["order_id"], ["SYN_CRIT"], "synthtoken")
    finally:
        db.close()
    rows = _alert_rows(pg_engine)
    assert len(rows) == 1
    assert rows[0]["chain_hash"] is not None
