"""Primitive PostgreSQL proof for the Hospital bed-allocation critical section.

This is deliberately not an API multi-worker test. It uses uniquely named,
temporary synthetic tables and removes them on exit; no canonical or production
clinical rows are read or written.
"""
from __future__ import annotations

import os
import sys
import threading
import uuid
from concurrent.futures import ThreadPoolExecutor

import psycopg2

PREFIX = f"gula_hospital_lock_probe_{uuid.uuid4().hex[:12]}"
BEDS = f"{PREFIX}_beds"
ALLOCATIONS = f"{PREFIX}_allocations"


def connect():
    url = os.environ.get("GULA_PROOF_DATABASE_URL")
    if not url:
        raise SystemExit("GULA_PROOF_DATABASE_URL is required; no database is selected implicitly")
    return psycopg2.connect(url)


def allocate(worker_id: str, barrier: threading.Barrier) -> str:
    conn = connect()
    try:
        conn.autocommit = False
        barrier.wait(timeout=10)
        with conn.cursor() as cur:
            cur.execute(f"SELECT status FROM {BEDS} WHERE bed_id = %s FOR UPDATE", ("synthetic-bed",))
            row = cur.fetchone()
            if row is None:
                conn.rollback()
                return "missing"
            if row[0] != "AVAILABLE":
                conn.rollback()
                return "conflict"
            cur.execute(f"SELECT allocation_id FROM {ALLOCATIONS} WHERE bed_id = %s AND active = TRUE FOR UPDATE", ("synthetic-bed",))
            if cur.fetchone() is not None:
                conn.rollback()
                return "conflict"
            cur.execute(f"INSERT INTO {ALLOCATIONS} (allocation_id, bed_id, worker_id, active) VALUES (%s, %s, %s, TRUE)", (str(uuid.uuid4()), "synthetic-bed", worker_id))
            cur.execute(f"UPDATE {BEDS} SET status = 'OCCUPIED' WHERE bed_id = %s", ("synthetic-bed",))
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
            cur.execute(f"CREATE TABLE {BEDS} (bed_id varchar(64) PRIMARY KEY, status varchar(24) NOT NULL)")
            cur.execute(f"CREATE TABLE {ALLOCATIONS} (allocation_id varchar(64) PRIMARY KEY, bed_id varchar(64) NOT NULL REFERENCES {BEDS}(bed_id), worker_id varchar(64) NOT NULL, active boolean NOT NULL)")
            cur.execute(f"CREATE UNIQUE INDEX {PREFIX}_active_bed_unique ON {ALLOCATIONS} (bed_id) WHERE active = TRUE")
            cur.execute(f"INSERT INTO {BEDS} (bed_id, status) VALUES ('synthetic-bed', 'AVAILABLE')")
        barrier = threading.Barrier(2)
        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(lambda worker: allocate(worker, barrier), ("synthetic-worker-a", "synthetic-worker-b")))
        assert sorted(results) == ["conflict", "winner"], results
        with owner.cursor() as cur:
            cur.execute(f"SELECT status FROM {BEDS} WHERE bed_id = 'synthetic-bed'")
            assert cur.fetchone() == ("OCCUPIED",)
            cur.execute(f"SELECT count(*) FROM {ALLOCATIONS} WHERE bed_id = 'synthetic-bed' AND active = TRUE")
            assert cur.fetchone() == (1,)
        sys.stdout.write("postgres_hospital_bed_lock_proof=pass\n")
        sys.stdout.write("results=" + ",".join(sorted(results)) + "\n")
        return 0
    finally:
        with owner.cursor() as cur:
            cur.execute(f"DROP TABLE IF EXISTS {ALLOCATIONS}")
            cur.execute(f"DROP TABLE IF EXISTS {BEDS}")
        owner.close()


if __name__ == "__main__":
    raise SystemExit(main())
