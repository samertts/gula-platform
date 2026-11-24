"""P-03-CONCURRENCY independent validation harness.

Runs against any audit implementation selected by PYTHONPATH. Set
``P03_EXPECT_FIXED=0`` to characterize HEAD's fork, or ``1`` to require the
P-03 chain-integrity correction. DISPOSABLE PostgreSQL 16 and synthetic rows
only; no production code is modified by this workstream.
"""

from __future__ import annotations

import os
import threading
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import app.services.mpi.models  # noqa: F401 - registers an unrelated HEAD relationship
import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session, sessionmaker

DSN = os.getenv("GULA_P03_PG_DSN", "")
EXPECT_FIXED = os.getenv("P03_EXPECT_FIXED", "1") == "1"
pytestmark = pytest.mark.skipif(not DSN, reason="GULA_P03_PG_DSN is required for PG16 evidence")


@pytest.fixture(scope="module")
def engine() -> Iterator[Any]:
    eng = create_engine(DSN)
    with eng.connect() as conn:
        assert conn.dialect.name == "postgresql"
        assert "PostgreSQL 16" in conn.execute(text("SELECT version()")).scalar_one()
        db_name = conn.execute(text("SELECT current_database()")).scalar_one()
        assert db_name.startswith("gula_") and (
            "test" in db_name or "gate" in db_name or "crud" in db_name
        )
        assert conn.execute(text("SELECT version_num FROM alembic_version")).scalar_one() == (
            "20261119_0003"
        )
    yield eng
    eng.dispose()


@pytest.fixture()
def sessions(engine: Any) -> Iterator[Any]:
    yield sessionmaker(bind=engine)


@pytest.fixture(autouse=True)
def clean_audit(engine: Any, monkeypatch: Any, tmp_path: Any) -> None:
    import app.services.audit_service as audit_service

    monkeypatch.setattr(audit_service, "_ANCHOR_DIR", tmp_path)
    monkeypatch.setattr(audit_service, "_ANCHOR_INTERVAL", 10**9)
    monkeypatch.setattr(audit_service, "_write_anchor", lambda *_a, **_k: None)
    with engine.begin() as conn:
        conn.execute(text("TRUNCATE TABLE audit_logs RESTART IDENTITY"))


def _log(session_factory: Any, resource_id: int, action: str = "test.concurrent") -> None:
    import app.services.audit_service as audit_service

    db = session_factory()
    try:
        audit_service.log_action(
            db,
            action=action,
            resource_type="test",
            resource_id=resource_id,
            user_id=9002,
            user_role="system:p03-concurrency",
            details={"workstream": "P-03-CONCURRENCY"},
        )
        db.commit()
    finally:
        db.close()


def _verify(session_factory: Any) -> dict[str, Any]:
    import app.services.audit_service as audit_service

    with session_factory() as db:
        return dict(audit_service.verify_audit_chain(db))


def _run_writers(
    engine: Any,
    sessions: Any,
    monkeypatch: Any,
    count: int,
    *,
    force_head_barrier: bool,
) -> tuple[list[Exception], dict[str, Any]]:
    import app.services.audit_service as audit_service

    errors: list[Exception] = []
    start_barrier = threading.Barrier(count, timeout=30)

    if force_head_barrier:
        # HEAD characterization: deterministic fork by pausing every writer
        # after the unlocked predecessor read. Never used against a serialized
        # implementation because the second writer cannot reach that point.
        head_barrier = threading.Barrier(count, timeout=30)
        original = audit_service._get_last_chain_hash

        def synchronized_head(db: Any) -> str:
            head = original(db)
            head_barrier.wait()
            return head

        monkeypatch.setattr(audit_service, "_get_last_chain_hash", synchronized_head)

    def writer(index: int) -> None:
        try:
            start_barrier.wait()
            _log(sessions, 96000 + index)
        except Exception as exc:
            errors.append(exc)

    threads = [threading.Thread(target=writer, args=(i,)) for i in range(count)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=60)
    assert all(not thread.is_alive() for thread in threads)
    return errors, _verify(sessions)


def test_two_writer_fork_behavior_matches_selected_implementation(
    engine: Any, sessions: Any, monkeypatch: Any
) -> None:
    errors, verification = _run_writers(
        engine, sessions, monkeypatch, 2, force_head_barrier=not EXPECT_FIXED
    )
    assert errors == []
    if EXPECT_FIXED:
        assert verification["verified"] is True, verification
        assert verification["entries_checked"] == 2
    else:
        assert verification["verified"] is False, "HEAD fork must be reproducible"
        assert verification["broken_entries"]


@pytest.mark.skipif(not EXPECT_FIXED, reason="HEAD has no isolation guard")
def test_isolation_matrix_rejects_unsafe_transactions_before_insert(
    sessions: Any, engine: Any
) -> None:
    import app.services.audit_service as audit_service

    def count_rows() -> int:
        with engine.connect() as conn:
            return int(conn.execute(text("SELECT COUNT(*) FROM audit_logs")).scalar_one())

    for level in ("REPEATABLE READ", "SERIALIZABLE", "AUTOCOMMIT"):
        with pytest.raises(audit_service.AuditChainIsolationError):
            with engine.connect().execution_options(isolation_level=level) as conn:
                db = Session(bind=conn)
                audit_service.log_action(db, "p03.isolation", "test", user_id=9002)
        assert count_rows() == 0, level


@pytest.mark.skipif(not EXPECT_FIXED, reason="HEAD has no advisory lock")
def test_advisory_lock_is_transaction_scoped_and_timeout_is_bounded(
    sessions: Any,
) -> None:
    import app.services.audit_service as audit_service

    acquired = threading.Event()
    release = threading.Event()
    holder_errors: list[Exception] = []

    def holder() -> None:
        db = sessions()
        try:
            audit_service.log_action(db, "p03.lock.holder", "test", user_id=9002)
            acquired.set()
            release.wait(timeout=20)
            db.commit()
        except Exception as exc:
            holder_errors.append(exc)
            db.rollback()
        finally:
            db.close()

    thread = threading.Thread(target=holder)
    thread.start()
    assert acquired.wait(timeout=20)

    contender = sessions()
    try:
        contender.execute(text("SET LOCAL lock_timeout = '1s'"))
        with pytest.raises(OperationalError) as exc_info:
            audit_service.log_action(
                contender, "p03.lock.contender", "test", user_id=9002
            )
        sqlstate = (
            getattr(exc_info.value.orig, "sqlstate", None)
            or getattr(exc_info.value.orig, "pgcode", None)
            or getattr(exc_info.value, "sqlstate", None)
            or getattr(exc_info.value, "pgcode", None)
        )
        assert sqlstate == "55P03", (sqlstate, exc_info.value)
    finally:
        contender.rollback()
        contender.close()
        release.set()
        thread.join(timeout=40)

    assert holder_errors == []
    # Retry the contender after the holder committed; no partial row remains.
    _log(sessions, 97001, action="p03.lock.retry")
    assert _verify(sessions)["verified"] is True

    with sessions() as db:
        advisory_locks = db.execute(
            text(
                "SELECT COUNT(*) FROM pg_locks "
                "WHERE locktype = 'advisory' AND pid = pg_backend_pid()"
            )
        ).scalar_one()
    assert advisory_locks == 0, "transaction-scoped lock must not leak after commit"


@pytest.mark.skipif(not EXPECT_FIXED, reason="HEAD cannot guarantee rollback anchor safety")
def test_rollback_and_replay_do_not_break_chain(sessions: Any, engine: Any, monkeypatch: Any) -> None:
    import app.services.audit_service as audit_service

    emitted: list[Any] = []
    monkeypatch.setattr(audit_service, "_ANCHOR_INTERVAL", 1)
    monkeypatch.setattr(audit_service, "_write_anchor", lambda i, h: emitted.append((i, h)))

    db = sessions()
    audit_service.log_action(db, "p03.rollback", "test", user_id=9002)
    db.rollback()
    db.close()
    assert emitted == []
    with engine.connect() as conn:
        assert conn.execute(text("SELECT COUNT(*) FROM audit_logs")).scalar_one() == 0

    # Duplicate logical operation: no dedupe schema exists yet, so the harness
    # records two individually valid rows and discloses duplicate-event risk.
    _log(sessions, 97002, action="p03.replay")
    _log(sessions, 97002, action="p03.replay")
    verification = _verify(sessions)
    assert verification["verified"] is True
    assert verification["entries_checked"] == 2


@pytest.mark.skipif(not EXPECT_FIXED, reason="stress is an acceptance proof for the fix only")
@pytest.mark.parametrize("writers", [10, 20, 50])
@pytest.mark.parametrize("repetition", range(3))
def test_repeated_stress_has_no_forks_or_lost_events(
    writers: int, repetition: int, sessions: Any, engine: Any, monkeypatch: Any
) -> None:
    errors, verification = _run_writers(
        engine, sessions, monkeypatch, writers, force_head_barrier=False
    )
    assert errors == []
    assert verification["verified"] is True, verification
    assert verification["entries_checked"] == writers


@pytest.mark.skipif(not EXPECT_FIXED, reason="ordering is enforced by the fix")
def test_lock_is_acquired_before_sequence_and_predecessor_read() -> None:
    configured = os.getenv("P03_AUDIT_SOURCE", "")
    source_path = (
        Path(configured)
        if configured
        else Path(__file__).resolve().parents[1] / "app" / "services" / "audit_service.py"
    )
    source = source_path.read_text(encoding="utf-8")
    log_body = source[source.index("def log_action(") :]
    lock_at = log_body.index("pg_advisory_xact_lock")
    sequence_at = log_body.index("nextval(")
    head_at = log_body.index("_get_last_chain_hash(db)")
    assert lock_at < sequence_at < head_at
