"""P-03 chain-integrity correction — PostgreSQL 16 evidence.

DISPOSABLE PG16 ONLY. ``GULA_P03_PG_DSN`` must point at a throwaway database
migrated to ``20261119_0003``. Synthetic rows only. This workstream closes the
hash-chain fork defect; it does not decide P-03 D1–D5 control-plane boundaries.
"""

from __future__ import annotations

import os
import threading
import time
from collections.abc import Iterator
from typing import Any

import app.services.mpi.models  # noqa: F401 - registers an unrelated HEAD relationship
import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker

DSN = os.getenv("GULA_P03_PG_DSN", "")
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


def _write(session_factory: Any, resource_id: int) -> None:
    import app.services.audit_service as audit_service

    db = session_factory()
    try:
        audit_service.log_action(
            db,
            action="control.release",
            resource_type="release",
            resource_id=resource_id,
            user_id=9001,
            user_role="system:p03-evidence",
            details={"workstream": "P-03"},
        )
        db.commit()
    finally:
        db.close()


def test_concurrent_writers_preserve_one_chain(sessions: Any, engine: Any) -> None:
    import app.services.audit_service as audit_service

    barrier = threading.Barrier(2, timeout=20)

    def writer(resource_id: int) -> None:
        barrier.wait()
        _write(sessions, resource_id)

    threads = [threading.Thread(target=writer, args=(rid,)) for rid in (91001, 91002)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=40)
    assert all(not thread.is_alive() for thread in threads)

    with sessions() as db:
        verification = audit_service.verify_audit_chain(db)
    assert verification["verified"] is True, verification
    assert verification["entries_checked"] == 2
    with engine.connect() as conn:
        hashes = conn.execute(text("SELECT chain_hash FROM audit_logs ORDER BY id")).scalars().all()
    assert all(hashes)


def test_repeatable_read_and_autocommit_fail_before_sequence_consumption(
    sessions: Any, engine: Any
) -> None:
    import app.services.audit_service as audit_service

    def sequence_value() -> int:
        with engine.connect() as conn:
            sequence = conn.execute(
                text("SELECT pg_get_serial_sequence('audit_logs', 'id')"),
            ).scalar_one()
            return int(conn.execute(text(f"SELECT last_value FROM {sequence}")).scalar_one())

    before = sequence_value()

    with pytest.raises(audit_service.AuditChainIsolationError):
        with engine.connect().execution_options(isolation_level="REPEATABLE READ") as conn:
            db = Session(bind=conn)
            audit_service.log_action(db, "test.rr", "test", user_id=9001)
            db.rollback()

    with pytest.raises(audit_service.AuditChainIsolationError):
        with engine.connect().execution_options(isolation_level="AUTOCOMMIT") as conn:
            db = Session(bind=conn)
            audit_service.log_action(db, "test.autocommit", "test", user_id=9001)

    assert sequence_value() == before
    with engine.connect() as conn:
        assert conn.execute(text("SELECT COUNT(*) FROM audit_logs")).scalar_one() == 0


def test_anchor_is_emitted_only_after_commit(sessions: Any, monkeypatch: Any) -> None:
    import app.services.audit_service as audit_service

    emitted: list[tuple[int, str]] = []
    monkeypatch.setattr(audit_service, "_ANCHOR_INTERVAL", 1)
    monkeypatch.setattr(audit_service, "_write_anchor", lambda i, h: emitted.append((i, h)))

    db = sessions()
    audit_service.log_action(db, "test.anchor", "test", user_id=9001)
    assert emitted == [], "anchor must not be emitted before commit"
    db.commit()
    assert len(emitted) == 1
    db.close()

    db = sessions()
    audit_service.log_action(db, "test.rollback", "test", user_id=9001)
    db.rollback()
    assert len(emitted) == 1, "rolled-back row must not emit an anchor"
    db.close()


def test_transaction_scoped_lock_is_held_until_commit(sessions: Any) -> None:
    import app.services.audit_service as audit_service

    acquired = threading.Event()
    release = threading.Event()
    errors: list[Exception] = []

    def first_writer() -> None:
        db = sessions()
        try:
            audit_service.log_action(db, "test.lock", "test", user_id=9001, resource_id=92001)
            acquired.set()
            release.wait(timeout=20)
            db.commit()
        except Exception as exc:
            errors.append(exc)
            db.rollback()
        finally:
            db.close()

    thread = threading.Thread(target=first_writer)
    thread.start()
    assert acquired.wait(timeout=20)

    started = time.monotonic()
    _write(sessions, 92002)
    waited = time.monotonic() - started
    release.set()
    thread.join(timeout=40)

    assert errors == []
    assert waited > 0.05, "second writer should wait for the first commit"
    with sessions() as db:
        assert audit_service.verify_audit_chain(db)["verified"] is True


def test_historical_chain_and_detected_fork_are_not_rewritten(sessions: Any, engine: Any) -> None:
    import app.services.audit_service as audit_service

    for resource_id in (93001, 93002, 93003):
        _write(sessions, resource_id)

    with sessions() as db:
        intact = audit_service.verify_audit_chain(db)
    assert intact["verified"] is True
    assert intact["entries_checked"] == 3

    # Inject a fork through INSERT only. Append-only triggers forbid repair.
    with engine.begin() as conn:
        for resource_id in (94001, 94002):
            conn.execute(
                text(
                    "INSERT INTO audit_logs (user_id, user_role, action, resource_type, "
                    "resource_id, details, chain_hash, created_at) "
                    "VALUES (9001, 'system:p03-evidence', 'fork.inject', 'test', "
                    ":rid, '{}', :hash, now())"
                ),
                {"rid": resource_id, "hash": "f" * 64},
            )

    with sessions() as db:
        detected = audit_service.verify_audit_chain(db)
    assert detected["verified"] is False
    assert len(detected["broken_entries"]) >= 2

    with sessions() as db:
        audit_service.log_action(db, "test.append-after-detection", "test", user_id=9001)
        db.commit()
    with engine.connect() as conn:
        follow_up_hash = conn.execute(
            text("SELECT chain_hash FROM audit_logs ORDER BY id DESC LIMIT 1")
        ).scalar_one()
    assert follow_up_hash


@pytest.mark.parametrize("writers", [10, 20, 50])
@pytest.mark.parametrize("repetition", range(3))
def test_repeated_stress_has_no_forks(
    writers: int, repetition: int, sessions: Any, engine: Any
) -> None:
    import app.services.audit_service as audit_service

    barrier = threading.Barrier(writers, timeout=30)
    errors: list[Exception] = []

    def writer(index: int) -> None:
        try:
            barrier.wait()
            _write(sessions, 95000 + index)
        except Exception as exc:
            errors.append(exc)

    threads = [threading.Thread(target=writer, args=(i,)) for i in range(writers)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=60)

    assert errors == []
    assert all(not thread.is_alive() for thread in threads)
    with engine.connect() as conn:
        count = conn.execute(text("SELECT COUNT(*) FROM audit_logs")).scalar_one()
    assert count == writers
    with sessions() as db:
        verification = audit_service.verify_audit_chain(db)
    assert verification["verified"] is True, verification
