"""Real PostgreSQL concurrency proof for Blood Bank transactional primitives.

Run with BLOOD_BANK_POSTGRES_URL pointing at a disposable PostgreSQL database.
The test is intentionally skipped, not passed, when infrastructure is absent.
"""
from __future__ import annotations

import os
import threading

import pytest
from sqlalchemy import create_engine, text

POSTGRES_URL = os.getenv("BLOOD_BANK_POSTGRES_URL")
pytestmark = pytest.mark.skipif(not POSTGRES_URL, reason="BLOOD_BANK_POSTGRES_URL is not configured")


def test_two_transactions_one_row_lock_winner() -> None:
    engine = create_engine(POSTGRES_URL, future=True, pool_size=2, max_overflow=0)
    with engine.begin() as conn:
        conn.execute(text("DROP TABLE IF EXISTS blood_bank_lock_probe_shared"))
        conn.execute(text("CREATE TABLE blood_bank_lock_probe_shared (id integer primary key, state text not null)"))
        conn.execute(text("INSERT INTO blood_bank_lock_probe_shared VALUES (1, 'available')"))

    barrier = threading.Barrier(2)
    outcomes: list[str] = []
    outcome_lock = threading.Lock()

    def attempt() -> None:
        with engine.connect() as conn:
            tx = conn.begin()
            try:
                barrier.wait(timeout=10)
                row = conn.execute(text("SELECT state FROM blood_bank_lock_probe_shared WHERE id=1 FOR UPDATE")).scalar_one()
                if row == "available":
                    conn.execute(text("UPDATE blood_bank_lock_probe_shared SET state='reserved' WHERE id=1"))
                    tx.commit()
                    result = "success"
                else:
                    tx.rollback()
                    result = "conflict"
            except Exception:
                tx.rollback()
                result = "error"
            with outcome_lock:
                outcomes.append(result)

    threads = [threading.Thread(target=attempt) for _ in range(2)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=20)
    assert sorted(outcomes) == ["conflict", "success"]
    with engine.begin() as conn:
        assert conn.execute(text("SELECT state FROM blood_bank_lock_probe_shared WHERE id=1")).scalar_one() == "reserved"
        conn.execute(text("DROP TABLE blood_bank_lock_probe_shared"))
    engine.dispose()
