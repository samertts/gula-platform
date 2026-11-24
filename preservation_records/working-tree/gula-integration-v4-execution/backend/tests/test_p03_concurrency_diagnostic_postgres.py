"""P-03 / AUD-F03 — T9 concurrency diagnostic (DEFERRED / DIAGNOSTIC ONLY).

SCOPE NOTICE
------------
The approved P-03 REV3 packet (§2, §6 T9, §7, §8) explicitly DEFERS concurrent
chain integrity to a separate ``P-03-CONCURRENCY`` design package and states that
no single-process GREEN result may be presented as multi-worker chain-integrity
evidence. This module is therefore **diagnostic evidence only**:

* it proves the HEAD race on an isolated disposable PostgreSQL 16 database;
* it does NOT implement, fix, accept or authorize any P-03 change;
* it is NOT a P-03 acceptance gate (T9 is not an acceptance condition);
* no production code was modified to obtain these results.

DISPOSABLE POSTGRESQL 16 ONLY. ``GULA_P03_PG_DSN`` must point at the throwaway
database created for this workstream. The module refuses SQLite. All written rows
are synthetic (``user_id=9001``, ``SYNTH_P03_CONCURRENCY``, resource ids 91001/91002).
The RED run must use an untouched ``git archive HEAD`` tree, because the working
tree contains uncommitted mixed-provenance changes in ``audit_service.py``
(including an advisory lock) that would mask the defect.
"""

from __future__ import annotations

import contextlib
import json
import os
import threading
from collections.abc import Iterator
from typing import Any

import app.services.mpi.models  # registers the Citizen mapper required by an unrelated HEAD relationship
import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

DSN = os.getenv("GULA_P03_PG_DSN", "")
pytestmark = pytest.mark.skipif(
    not DSN,
    reason="GULA_P03_PG_DSN is required; a disposable PostgreSQL 16 database is mandatory",
)


@pytest.fixture(scope="module")
def pg_engine() -> Iterator[Any]:
    engine = create_engine(DSN)
    with engine.connect() as conn:
        assert conn.dialect.name == "postgresql", "SQLite substitution is prohibited"
        assert "PostgreSQL 16" in conn.execute(text("SELECT version()")).scalar_one()
        assert conn.execute(text("SELECT current_database()")).scalar_one() == "gula_int_gate"
        assert conn.execute(text("SELECT version_num FROM alembic_version")).scalar_one() == (
            "20261119_0003"
        )
        assert conn.execute(text("SHOW transaction_isolation")).scalar_one() == "read committed"
        columns = {
            row[0]
            for row in conn.execute(
                text(
                    "SELECT column_name FROM information_schema.columns "
                    "WHERE table_name='audit_logs'"
                )
            )
        }
        assert {
            "chain_hash",
            "lab_id",
            "action",
            "resource_type",
            "resource_id",
        } <= columns
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


@pytest.fixture(autouse=True)
def clean_audit(pg_engine: Any) -> None:
    with pg_engine.begin() as conn:
        conn.execute(text("TRUNCATE TABLE audit_logs RESTART IDENTITY"))


def _run_two_writers(pg_engine: Any, monkeypatch: Any) -> tuple[list[Any], dict[str, Any]]:
    """Run two HEAD canonical writers against the same chain head.

    A barrier is injected *in the test harness only* at the unlocked
    ``_get_last_chain_hash`` read. It converts the latent timing race into a
    deterministic one without changing production code. Each writer uses its
    own PostgreSQL session and commits independently.
    """
    import app.services.audit_service as audit_service

    original_head_reader = audit_service._get_last_chain_hash
    barrier = threading.Barrier(2, timeout=20)

    def synchronized_head_reader(db: Any) -> str:
        head = original_head_reader(db)
        barrier.wait()
        return head

    monkeypatch.setattr(audit_service, "_get_last_chain_hash", synchronized_head_reader)
    session_factory = sessionmaker(bind=pg_engine)
    errors: list[Exception] = []

    def write(resource_id: int) -> None:
        db = session_factory()
        try:
            audit_service.log_action(
                db,
                action="control.release",
                resource_type="release",
                resource_id=resource_id,
                user_id=9001,
                user_role="system:diagnostic",
                lab_id=None,
                details={"diagnostic": "SYNTH_P03_CONCURRENCY"},
            )
            db.commit()
        except Exception as exc:
            errors.append(exc)
            with contextlib.suppress(Exception):
                db.rollback()
        finally:
            db.close()

    threads = [
        threading.Thread(target=write, args=(resource_id,)) for resource_id in (91001, 91002)
    ]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=40)
    assert errors == [], f"concurrent writer errors: {errors!r}"
    assert all(not thread.is_alive() for thread in threads), "writer thread did not finish"

    with pg_engine.connect() as conn:
        rows = (
            conn.execute(text("SELECT id, resource_id, chain_hash FROM audit_logs ORDER BY id"))
            .mappings()
            .all()
        )
    verification_db = session_factory()
    try:
        verification = audit_service.verify_audit_chain(verification_db)
    finally:
        verification_db.close()
    return list(rows), dict(verification)


def test_t9_red_concurrent_writers_must_preserve_chain(pg_engine: Any, monkeypatch: Any) -> None:
    """DESIRED behavior. Expected to FAIL at HEAD: this is the RED proof.

    A later P-03-CONCURRENCY design package may turn this GREEN. This packet
    does not implement that fix and does not claim this result as acceptance.
    """
    rows, verification = _run_two_writers(pg_engine, monkeypatch)
    assert len(rows) == 2, f"expected two synthetic rows, got {len(rows)}"
    assert all(row["chain_hash"] for row in rows), "no NULL-chain row is permitted"
    assert verification["verified"] is True, (
        "HEAD concurrency defect reproduced: two writers read one unlocked chain "
        "head and produced a fork rejected by verify_audit_chain: "
        + json.dumps(verification.get("broken_entries", []), sort_keys=True)
    )


def test_t9_diagnostic_records_shared_predecessor(pg_engine: Any, monkeypatch: Any) -> None:
    """Characterization of the defect mechanism; expected to PASS at HEAD.

    This test documents *why* the RED test fails and is not an acceptance test.
    """
    rows, verification = _run_two_writers(pg_engine, monkeypatch)
    assert len(rows) == 2
    assert rows[0]["id"] != rows[1]["id"], "sequence must reserve distinct ids"
    assert all(row["chain_hash"] for row in rows)
    assert verification["verified"] is False, "HEAD must exhibit the chain fork"
    assert len(verification["broken_entries"]) >= 1
