"""SEC-015 — tamper-evident audit chain integrity regression suite.

Covers the SQLite chain-linkage defect introduced by commit ``f0b021bd3``
(which regressed the earlier fix in ``2cdc5479``): ``log_action`` on a
non-PostgreSQL dialect read the predecessor hash AFTER flushing the new row,
so the just-inserted NULL-hash row was selected as its own predecessor and
every row was chained to the genesis hash.

All payloads are synthetic. No production data, no secrets, no DB migration
operations, and no manual hash re-stitching: every assertion verifies the
records exactly as ``log_action`` persisted them.
"""

from __future__ import annotations

import ast
import re
import shutil
import tempfile
import threading
from itertools import pairwise
from pathlib import Path

import pytest
from app.models.audit_log import AuditLog
from app.services.audit_service import (
    _GENESIS_HASH,
    _canonical_audit_timestamp,
    _compute_chain_hash,
    log_action,
    verify_audit_chain,
)
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker


def _is_hash(value: str | None) -> bool:
    return bool(value) and re.fullmatch(r"[0-9a-f]{64}", value) is not None


def _new_log(db, action: str, **kwargs) -> AuditLog:
    """Append one synthetic audit row through the public API and return it."""
    log_action(
        db,
        action=action,
        resource_type="synthetic_test",
        resource_id=kwargs.pop("resource_id", 1),
        user_id=kwargs.pop("user_id", 1),
        user_role=kwargs.pop("user_role", "tester"),
        **kwargs,
    )
    return db.query(AuditLog).order_by(AuditLog.id.desc()).first()


class TestAuditChainConstruction:
    """Chain construction on the SQLite (non-PG) dialect used by the test suite."""

    def test_first_event_chains_from_genesis(self, db):
        entry = _new_log(db, "first_event")

        assert _is_hash(entry.chain_hash)
        assert entry.chain_hash == _compute_chain_hash(_GENESIS_HASH, entry)
        report = verify_audit_chain(db)
        assert report["status"] == "intact"
        assert report["entries_checked"] == 1

    def test_two_sequential_events_link_to_predecessor(self, db):
        first = _new_log(db, "event_1")
        db.commit()
        second = _new_log(db, "event_2")
        db.commit()

        assert second.chain_hash == _compute_chain_hash(first.chain_hash, second)
        report = verify_audit_chain(db)
        assert report["verified"] is True
        assert report["broken_entries"] == []

    def test_multiple_events_in_one_transaction(self, db):
        written = [_new_log(db, f"batch_{i}", details={"i": i}) for i in range(4)]

        for prev, current in pairwise(written):
            assert current.chain_hash == _compute_chain_hash(prev.chain_hash, current)

        report = verify_audit_chain(db)
        assert report["status"] == "intact"
        assert report["entries_checked"] == 4

    def test_multiple_committed_transactions(self, db):
        written = []
        for i in range(4):
            written.append(_new_log(db, f"committed_{i}", details={"i": i}))
            db.commit()

        for prev, current in pairwise(written):
            assert current.chain_hash == _compute_chain_hash(prev.chain_hash, current)
        assert verify_audit_chain(db)["verified"] is True

    def test_persisted_hash_verification_without_repair(self, db):
        for i in range(3):
            _new_log(db, f"persist_{i}")
            db.commit()

        db.expire_all()
        report = verify_audit_chain(db)

        assert report["status"] == "intact", report["broken_entries"]
        assert report["entries_checked"] == 3

    def test_timestamp_uses_canonical_utc_representation(self, db):
        entry = _new_log(db, "timestamp_event")
        assert entry.created_at is not None
        canonical = _canonical_audit_timestamp(entry.created_at)
        assert canonical is not None
        assert canonical.endswith("+00:00")
        # The same canonicalization is applied at write time and verify time.
        assert entry.chain_hash == _compute_chain_hash(_GENESIS_HASH, entry)


class TestAuditChainTamperDetection:
    """Tamper detection must still fail closed after the linkage fix."""

    def test_tampered_payload_is_detected(self, db):
        first = _new_log(db, "original")
        _new_log(db, "second")
        db.commit()

        db.execute(
            text("UPDATE audit_logs SET details = :d WHERE id = :i"),
            {"d": "TAMPERED", "i": first.id},
        )
        db.commit()

        report = verify_audit_chain(db)
        assert report["verified"] is False
        assert report["status"] == "tampered"
        assert first.id in [b["id"] for b in report["broken_entries"]]

    def test_tampered_predecessor_hash_is_detected(self, db):
        first = _new_log(db, "event_1")
        _new_log(db, "event_2")
        db.commit()

        db.execute(
            text("UPDATE audit_logs SET chain_hash = :h WHERE id = :i"),
            {"h": "f" * 64, "i": first.id},
        )
        db.commit()

        report = verify_audit_chain(db)
        assert report["verified"] is False
        broken_ids = [b["id"] for b in report["broken_entries"]]
        assert first.id in broken_ids

    def test_missing_predecessor_is_detected(self, db):
        first = _new_log(db, "event_1")
        second = _new_log(db, "event_2")
        third = _new_log(db, "event_3")
        db.commit()
        first_id, second_id, third_id = first.id, second.id, third.id

        db.execute(text("DELETE FROM audit_logs WHERE id = :i"), {"i": first_id})
        db.commit()

        report = verify_audit_chain(db)
        assert report["verified"] is False
        # verify_audit_chain uses each row's STORED hash as the next
        # predecessor, so deleting row 1 is detected exactly at the first
        # surviving row (row 2): its stored hash was chained to the deleted
        # row, while verification recomputes from genesis. Row 3 remains
        # internally consistent with row 2's stored hash and is NOT flagged.
        # Asserting the exact boundary — not a tautology such as
        # `third_id >= second_id` — pins this precise detection behaviour.
        broken_ids = [b["id"] for b in report["broken_entries"]]
        assert broken_ids == [second_id]

    def test_null_chain_hash_legacy_row_is_skipped_not_falsely_verified(self, db):
        # Simulate a pre-chain legacy row with an explicit NULL chain_hash.
        db.execute(
            text(
                "INSERT INTO audit_logs "
                "(user_id, user_role, lab_id, action, resource_type, resource_id, "
                " details, ip_address, created_at, chain_hash) "
                "VALUES (1, 'legacy', NULL, 'legacy_event', 'synthetic_test', 0, "
                " NULL, NULL, CURRENT_TIMESTAMP, NULL)"
            ),
        )
        db.flush()

        chained = _new_log(db, "modern_event")
        db.commit()

        assert _is_hash(chained.chain_hash)
        report = verify_audit_chain(db)
        assert report["entries_checked"] == 2
        # The legacy NULL row is skipped and the modern row chains from genesis.
        assert report["verified"] is True


class TestAuditChainStructuralGuard:
    """Guard the exact regression so a future refactor cannot reintroduce it."""

    def test_predecessor_hash_is_read_before_insert_in_both_dialect_branches(self):
        source = Path(
            __file__
        ).parents[2] / "app" / "services" / "audit_service.py"
        tree = ast.parse(source.read_text(encoding="utf-8"))
        fn = next(
            n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "log_action"
        )

        def _calls(node: ast.AST, name: str, attr: bool = False) -> list[int]:
            lines: list[int] = []
            for child in ast.walk(node):
                if not isinstance(child, ast.Call) or not isinstance(child.func, ast.Name if not attr else ast.Attribute):
                    continue
                if getattr(child.func, "id" if not attr else "attr", None) == name:
                    lines.append(child.lineno)
            return lines

        # Locate the dialect branch (the regression lived in its non-PG else).
        dialect_ifs = [
            n
            for n in ast.walk(fn)
            if isinstance(n, ast.If)
            and (
                "postgresql" in ast.unparse(n.test)
                or "is_postgres" in ast.unparse(n.test)
            )
        ]
        assert len(dialect_ifs) == 1

        # The PostgreSQL branch must take a transaction-scoped advisory lock
        # before reading its predecessor, otherwise concurrent workers fork
        # the chain across processes.
        pg_branch_source = ast.unparse(dialect_ifs[0].body)
        assert "pg_advisory_xact_lock" in pg_branch_source
        assert pg_branch_source.index("pg_advisory_xact_lock") < pg_branch_source.index(
            "_get_last_chain_hash"
        )

        # The SQLite branch must acquire a transaction-scoped write
        # reservation before reading its predecessor. A process-local lock is
        # insufficient because it is released before the caller commits.
        sqlite_branch_source = ast.unparse(dialect_ifs[0].orelse)
        assert "UPDATE audit_logs" in sqlite_branch_source
        assert sqlite_branch_source.index("UPDATE audit_logs") < sqlite_branch_source.index(
            "_get_last_chain_hash"
        )

        for branch in (dialect_ifs[0].body, dialect_ifs[0].orelse):
            prev_lines = [line for stmt in branch for line in _calls(stmt, "_get_last_chain_hash")]
            add_lines = [line for stmt in branch for line in _calls(stmt, "add", attr=True)]
            assert prev_lines and add_lines, "both branches must read hash and add row"
            # The predecessor MUST be resolved before the row is added:
            # f0b021bd3 regressed this in the else branch by reading it after
            # db.flush(), which selected the new NULL-hash row as predecessor.
            assert min(prev_lines) < min(add_lines), (
                f"predecessor read after insert in branch at lines {prev_lines}/{add_lines}"
            )


class TestAuditChainConcurrency:
    """Concurrent writers must not produce duplicate or missing chain positions."""

    @pytest.mark.parametrize("threads,per_thread", [(4, 3)])
    def test_concurrent_writers_produce_single_unbroken_chain(self, threads, per_thread):
        tmp_dir = tempfile.mkdtemp(prefix="audit_chain_")
        url = f"sqlite:///{Path(tmp_dir) / 'test.db'}"
        engine = create_engine(
            url,
            connect_args={"check_same_thread": False, "timeout": 30},
        )
        with engine.begin() as conn:
            conn.execute(text("PRAGMA journal_mode=WAL"))
            AuditLog.__table__.create(conn)

        errors: list[Exception] = []

        def writer(worker: int) -> None:
            local_engine = create_engine(
                url,
                connect_args={"check_same_thread": False, "timeout": 30},
            )
            try:
                for i in range(per_thread):
                    # SQLite serializes writers; retry a transaction that lost
                    # the write lock so only committed rows participate.
                    for attempt in range(10):
                        session = sessionmaker(bind=local_engine)()
                        try:
                            log_action(
                                session,
                                action=f"worker_{worker}_{i}",
                                resource_type="synthetic_test",
                                resource_id=i,
                                user_id=worker,
                                user_role="tester",
                            )
                            session.commit()
                            break
                        except Exception as exc:  # pragma: no cover - timing
                            session.rollback()
                            if attempt == 9:
                                errors.append(exc)
                        finally:
                            session.close()
            finally:
                local_engine.dispose()

        jobs = [threading.Thread(target=writer, args=(w,)) for w in range(threads)]
        for job in jobs:
            job.start()
        for job in jobs:
            job.join()

        assert errors == [], errors
        check_session = sessionmaker(bind=engine)()
        try:
            rows = check_session.query(AuditLog).order_by(AuditLog.id.asc()).all()
            assert len(rows) == threads * per_thread
            hashes = [r.chain_hash for r in rows]
            assert all(_is_hash(h) for h in hashes)
            assert len(set(hashes)) == len(hashes), "duplicate chain hashes"
            report = verify_audit_chain(check_session)
            assert report["status"] == "intact", report["broken_entries"]
        finally:
            check_session.close()
            engine.dispose()
            shutil.rmtree(tmp_dir, ignore_errors=True)

    def test_rolled_back_writer_does_not_corrupt_chain(self):
        tmp_dir = tempfile.mkdtemp(prefix="audit_chain_")
        url = f"sqlite:///{Path(tmp_dir) / 'test.db'}"
        engine = create_engine(url, connect_args={"check_same_thread": False})
        with engine.begin() as conn:
            AuditLog.__table__.create(conn)

        session = sessionmaker(bind=engine)()
        try:
            log_action(session, action="discarded", resource_type="synthetic_test")
            session.rollback()

            log_action(session, action="surviving", resource_type="synthetic_test")
            session.commit()
            session.expire_all()

            rows = session.query(AuditLog).order_by(AuditLog.id.asc()).all()
            assert len(rows) == 1
            assert rows[0].action == "surviving"
            assert rows[0].chain_hash == _compute_chain_hash(_GENESIS_HASH, rows[0])
            assert verify_audit_chain(session)["status"] == "intact"
        finally:
            session.close()
            engine.dispose()
            shutil.rmtree(tmp_dir, ignore_errors=True)
