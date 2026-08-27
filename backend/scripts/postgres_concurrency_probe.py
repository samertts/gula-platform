"""Run a disposable PostgreSQL row-lock/one-winner proof.

This is a database-primitive proof, not a production deployment or a substitute
for a multi-worker API test. It requires GULA_PROOF_DATABASE_URL and creates a
uniquely named temporary table in the public schema, then removes it.
"""
from __future__ import annotations

import os
import sys
import threading
import uuid
from concurrent.futures import ThreadPoolExecutor

import psycopg2

TABLE = f"gula_vs02_lock_probe_{uuid.uuid4().hex[:12]}"


def connect():
    url = os.environ.get("GULA_PROOF_DATABASE_URL")
    if not url:
        raise SystemExit("GULA_PROOF_DATABASE_URL is required; no database is selected implicitly")
    return psycopg2.connect(url)


def claim(slot_id: str, barrier: threading.Barrier) -> str:
    conn = connect()
    try:
        conn.autocommit = False
        barrier.wait(timeout=10)
        with conn.cursor() as cur:
            cur.execute(f"SELECT slot_id, booked FROM {TABLE} WHERE slot_id = %s FOR UPDATE", (slot_id,))
            row = cur.fetchone()
            if row is None:
                conn.rollback()
                return "missing"
            if row[1]:
                conn.rollback()
                return "conflict"
            cur.execute(f"UPDATE {TABLE} SET booked = TRUE WHERE slot_id = %s", (slot_id,))
            conn.commit()
            return "winner"
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def main() -> int:
    owner = connect()
    try:
        owner.autocommit = True
        with owner.cursor() as cur:
            cur.execute(f"CREATE TABLE {TABLE} (slot_id varchar(64) PRIMARY KEY, booked boolean NOT NULL DEFAULT FALSE)")
            cur.execute(f"INSERT INTO {TABLE} (slot_id) VALUES ('synthetic-slot')")
        barrier = threading.Barrier(2)
        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(lambda _: claim("synthetic-slot", barrier), range(2)))
        assert sorted(results) == ["conflict", "winner"], results
        with owner.cursor() as cur:
            cur.execute(f"SELECT booked FROM {TABLE} WHERE slot_id = 'synthetic-slot'")
            assert cur.fetchone() == (True,)
        sys.stdout.write("postgres_row_lock_proof=pass\n")
        sys.stdout.write("results=" + ",".join(sorted(results)) + "\n")
        return 0
    finally:
        with owner.cursor() as cur:
            cur.execute(f"DROP TABLE IF EXISTS {TABLE}")
        owner.close()


if __name__ == "__main__":
    raise SystemExit(main())
