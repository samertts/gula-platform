"""SEC-015 / F-01 — PostgreSQL isolation guard regression suite.

This module verifies that ``log_action`` refuses audit writes whenever the
*active* transaction cannot guarantee serialization of the hash chain:

  * ``READ COMMITTED``            -> writes succeed, chain stays intact
  * ``REPEATABLE READ``           -> rejected before any audit write
  * ``SERIALIZABLE``              -> rejected before any audit write
  * raw ``SET TRANSACTION``       -> cannot bypass the guard
  * ``AUTOCOMMIT``                -> rejected (advisory lock cannot span it)
  * undeterminable isolation      -> fails closed

It also proves concurrent READ COMMITTED writers are serialized, rejected
writers consume no sequence values, rollback leaves an intact chain, and the
database-level append-only triggers still reject UPDATE/DELETE.

DISPOSABLE POSTGRESQL 16 ONLY
-----------------------------
Set ``GULA_AUDIT_PG16_TEST_DSN`` to a DSN for a throwaway PostgreSQL 16
database used exclusively by this module. The module creates and drops its
own ``audit_logs`` table and triggers inside that database. Without the
variable, the PostgreSQL cases skip with an explicit reason; the structural
cases (which need no database) still run. No production database, Redis,
RabbitMQ, MinIO, PHI or secret is used. All payloads are synthetic.
"""

from __future__ import annotations

import ast
import inspect
import os
import threading
import time
from pathlib import Path

import pytest
from app.models.audit_log import AuditLog
from app.services.audit_service import (
    _AUDIT_SAFE_ISOLATION_LEVELS,
    AuditChainIsolationError,
    log_action,
    verify_audit_chain,
)
from sqlalchemy import create_engine, text
from sqlalchemy.engine import base as _sa_engine_base
from sqlalchemy.orm import sessionmaker

_DSN = os.getenv("GULA_AUDIT_PG16_TEST_DSN", "")


# ─── helpers ──────────────────────────────────────────────────────────────────


def _row_count(engine) -> int:
    with engine.connect() as conn:
        return int(conn.execute(text("SELECT count(*) FROM audit_logs")).scalar_one())


def _sequence_state(engine) -> tuple[int, bool]:
    """Current sequence state without consuming a value."""
    with engine.connect() as conn:
        row = conn.execute(text("SELECT last_value, is_called FROM audit_logs_id_seq")).one()
        return int(row[0]), bool(row[1])


def _session(engine, isolation: str | None = None, autocommit: bool = False):
    target = engine
    if isolation is not None:
        target = target.execution_options(isolation_level=isolation)
    if autocommit:
        target = create_engine(_DSN, isolation_level="AUTOCOMMIT")
    return sessionmaker(bind=target)()


def _log(db, action: str, resource_id: int, user_id: int) -> None:
    log_action(
        db,
        action=action,
        resource_type="synthetic_test",
        resource_id=resource_id,
        user_id=user_id,
        user_role="tester",
    )


# ─── fixtures ─────────────────────────────────────────────────────────────────


@pytest.fixture(scope="module")
def pg_engine():
    if not _DSN:
        pytest.skip(
            "GULA_AUDIT_PG16_TEST_DSN is not set; a disposable PostgreSQL 16 "
            "database is required for the F-01 isolation suite"
        )
    engine = create_engine(_DSN)
    with engine.begin() as conn:
        AuditLog.__table__.drop(conn, checkfirst=True)
        AuditLog.__table__.create(conn)
        conn.execute(
            text(
                """
                CREATE OR REPLACE FUNCTION audit_logs_deny_mutation()
                RETURNS trigger LANGUAGE plpgsql AS $$
                BEGIN
                    RAISE EXCEPTION
                        'audit_logs is append-only: % operation is not permitted',
                        TG_OP;
                END;
                $$
                """
            )
        )
        conn.execute(text("DROP TRIGGER IF EXISTS trg_audit_logs_no_update ON audit_logs"))
        conn.execute(text("DROP TRIGGER IF EXISTS trg_audit_logs_no_delete ON audit_logs"))
        conn.execute(
            text(
                """
                CREATE TRIGGER trg_audit_logs_no_update
                BEFORE UPDATE ON audit_logs
                FOR EACH ROW EXECUTE FUNCTION audit_logs_deny_mutation()
                """
            )
        )
        conn.execute(
            text(
                """
                CREATE TRIGGER trg_audit_logs_no_delete
                BEFORE DELETE ON audit_logs
                FOR EACH ROW EXECUTE FUNCTION audit_logs_deny_mutation()
                """
            )
        )
    yield engine
    with engine.begin() as conn:
        AuditLog.__table__.drop(conn, checkfirst=True)
    engine.dispose()


@pytest.fixture()
def clean_pg(pg_engine):
    with pg_engine.begin() as conn:
        conn.execute(text("TRUNCATE audit_logs RESTART IDENTITY"))
    return pg_engine


# ─── structural guard (no database required) ─────────────────────────────────


class TestGuardStructure:
    def test_guard_precedes_advisory_lock_and_public_api_is_unchanged(self):
        source = Path(__file__).parents[2] / "app" / "services" / "audit_service.py"
        tree = ast.parse(source.read_text(encoding="utf-8"))
        fn = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "log_action")

        params = [a.arg for a in fn.args.args]
        assert params == [
            "db",
            "action",
            "resource_type",
            "resource_id",
            "user_id",
            "user_role",
            "lab_id",
            "details",
            "ip_address",
        ]

        dialect_ifs = [
            n
            for n in ast.walk(fn)
            if isinstance(n, ast.If)
            and ("postgresql" in ast.unparse(n.test) or "is_postgres" in ast.unparse(n.test))
        ]
        assert len(dialect_ifs) == 1
        pg_branch = ast.unparse(dialect_ifs[0].body)
        assert "_require_audit_safe_isolation" in pg_branch
        assert "pg_advisory_xact_lock" in pg_branch
        assert pg_branch.index("_require_audit_safe_isolation") < pg_branch.index(
            "pg_advisory_xact_lock"
        )
        assert pg_branch.index("pg_advisory_xact_lock") < pg_branch.index("_get_last_chain_hash")

    def test_only_read_committed_is_accepted_and_exception_type_is_stable(self):
        assert set(_AUDIT_SAFE_ISOLATION_LEVELS) == {"READ COMMITTED"}
        assert issubclass(AuditChainIsolationError, RuntimeError)


# ─── PostgreSQL 16 isolation behaviour ───────────────────────────────────────


class TestIsolationAcceptance:
    def test_read_committed_writes_succeed_and_chain_is_intact(self, clean_pg):
        db = _session(clean_pg, isolation="READ COMMITTED")
        try:
            for i in range(3):
                _log(db, f"rc_{i}", i, 1)
                db.commit()
            rows = db.query(AuditLog).order_by(AuditLog.id.asc()).all()
            assert len(rows) == 3
            assert all(r.chain_hash for r in rows)
            report = verify_audit_chain(db)
            assert report["status"] == "intact", report["broken_entries"]
            assert report["entries_checked"] == 3
        finally:
            db.close()

    @pytest.mark.parametrize("isolation", ["REPEATABLE READ", "SERIALIZABLE"])
    def test_snapshot_isolation_is_rejected_before_any_write(self, clean_pg, isolation):
        seq_before = _sequence_state(clean_pg)
        db = _session(clean_pg, isolation=isolation)
        try:
            assert db.connection().get_isolation_level() == isolation
            with pytest.raises(AuditChainIsolationError) as exc:
                _log(db, f"blocked_{isolation.replace(' ', '_')}", 1, 1)
            assert "READ COMMITTED" in str(exc.value)
            assert isolation in str(exc.value)
            db.rollback()
        finally:
            db.close()

        assert _row_count(clean_pg) == 0, "rejected writer persisted an audit row"
        assert _sequence_state(clean_pg) == seq_before, "rejected writer consumed a sequence value"

    def test_raw_set_transaction_cannot_bypass_the_guard(self, clean_pg):
        """The guard reads the active transaction level, not the engine default."""
        seq_before = _sequence_state(clean_pg)
        db = _session(clean_pg)
        try:
            db.execute(text("SET TRANSACTION ISOLATION LEVEL SERIALIZABLE"))
            assert db.connection().get_isolation_level() == "SERIALIZABLE"
            with pytest.raises(AuditChainIsolationError) as exc:
                _log(db, "raw_set_bypass", 1, 1)
            assert "SERIALIZABLE" in str(exc.value)
            db.rollback()
        finally:
            db.close()

        assert _row_count(clean_pg) == 0
        assert _sequence_state(clean_pg) == seq_before

    def test_autocommit_is_rejected_before_any_write(self, clean_pg):
        """AUTOCOMMIT releases the transaction-scoped lock after the SELECT."""
        seq_before = _sequence_state(clean_pg)
        engine = create_engine(_DSN, isolation_level="AUTOCOMMIT")
        db = sessionmaker(bind=engine)()
        try:
            with pytest.raises(AuditChainIsolationError) as exc:
                _log(db, "autocommit_bypass", 1, 1)
            assert "AUTOCOMMIT" in str(exc.value)
        finally:
            db.close()
            engine.dispose()

        assert _row_count(clean_pg) == 0
        assert _sequence_state(clean_pg) == seq_before

    def test_undeterminable_isolation_fails_closed(self, clean_pg, monkeypatch):
        seq_before = _sequence_state(clean_pg)

        def _boom(self):  # pragma: no cover - invoked by the guard
            raise RuntimeError("simulated undeterminable isolation")

        monkeypatch.setattr(_sa_engine_base.Connection, "get_isolation_level", _boom)
        db = _session(clean_pg, isolation="READ COMMITTED")
        try:
            with pytest.raises(AuditChainIsolationError) as exc:
                _log(db, "undeterminable", 1, 1)
            assert "cannot determine" in str(exc.value)
            db.rollback()
        finally:
            db.close()

        assert _row_count(clean_pg) == 0
        assert _sequence_state(clean_pg) == seq_before


# ─── transaction semantics ────────────────────────────────────────────────────


class TestTransactionSemantics:
    def test_concurrent_writers_are_serialized_at_read_committed(self, clean_pg):
        errors: list[Exception] = []
        started = threading.Event()
        finished = threading.Event()

        db_a = _session(clean_pg, isolation="READ COMMITTED")
        try:
            # A holds the advisory lock in an uncommitted transaction.
            _log(db_a, "writer_a", 1, 1)

            def writer_b() -> None:
                db_b = _session(clean_pg, isolation="READ COMMITTED")
                try:
                    started.set()
                    _log(db_b, "writer_b", 2, 2)
                    db_b.commit()
                    finished.set()
                except Exception as exc:  # pragma: no cover - timing
                    errors.append(exc)
                    db_b.rollback()
                finally:
                    db_b.close()

            thread_b = threading.Thread(target=writer_b, daemon=True)
            thread_b.start()
            assert started.wait(10), "writer B did not start"
            time.sleep(0.5)
            assert not finished.is_set(), "writer B did not wait for writer A's advisory lock"
            db_a.commit()
            assert finished.wait(20), "writer B did not finish after writer A committed"
            thread_b.join(timeout=10)
        finally:
            db_a.close()

        assert errors == [], errors
        with clean_pg.connect() as check_conn:
            rows = check_conn.execute(
                text("SELECT id, action, chain_hash FROM audit_logs ORDER BY id ASC")
            ).fetchall()
        assert len(rows) == 2
        assert [r.action for r in rows] == ["writer_a", "writer_b"]
        assert rows[0].chain_hash != rows[1].chain_hash

        db_check = _session(clean_pg, isolation="READ COMMITTED")
        try:
            report = verify_audit_chain(db_check)
            assert report["status"] == "intact", report["broken_entries"]
            assert report["entries_checked"] == 2
        finally:
            db_check.close()

    def test_rollback_after_success_keeps_chain_intact(self, clean_pg):
        db = _session(clean_pg, isolation="READ COMMITTED")
        try:
            _log(db, "discarded", 1, 1)
            db.rollback()
            _log(db, "surviving", 2, 2)
            db.commit()
            db.expire_all()
            rows = db.query(AuditLog).order_by(AuditLog.id.asc()).all()
            assert len(rows) == 1
            assert rows[0].action == "surviving"
            assert verify_audit_chain(db)["status"] == "intact"
        finally:
            db.close()

    def test_append_only_triggers_still_deny_update_and_delete(self, clean_pg):
        db = _session(clean_pg, isolation="READ COMMITTED")
        try:
            _log(db, "protected", 1, 1)
            db.commit()
            row_id = db.query(AuditLog).one().id

            with pytest.raises(Exception) as upd:
                db.execute(
                    text("UPDATE audit_logs SET action = :a WHERE id = :i"),
                    {"a": "forged", "i": row_id},
                )
                db.commit()
            assert "append-only" in str(upd.value)
            db.rollback()

            with pytest.raises(Exception) as dele:
                db.execute(text("DELETE FROM audit_logs WHERE id = :i"), {"i": row_id})
                db.commit()
            assert "append-only" in str(dele.value)
            db.rollback()

            assert verify_audit_chain(db)["status"] == "intact"
        finally:
            db.close()

    def test_inspect_signature_matches_call_contract(self):
        params = list(inspect.signature(log_action).parameters)
        assert params == [
            "db",
            "action",
            "resource_type",
            "resource_id",
            "user_id",
            "user_role",
            "lab_id",
            "details",
            "ip_address",
        ]
