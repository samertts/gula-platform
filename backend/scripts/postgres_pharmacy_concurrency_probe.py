"""Run a disposable PostgreSQL stock-lock proof for canonical pharmacy rules.

This is a database-primitive proof, not a production API or multi-worker staging
proof. It requires GULA_PROOF_DATABASE_URL and creates/removes uniquely named
synthetic tables in the public schema.
"""
from __future__ import annotations

import os
import sys
import threading
import uuid
from concurrent.futures import ThreadPoolExecutor

import psycopg2

BATCH_TABLE = f"gula_pharmacy_batch_probe_{uuid.uuid4().hex[:12]}"
LEDGER_TABLE = f"gula_pharmacy_ledger_probe_{uuid.uuid4().hex[:12]}"


def connect():
    url = os.environ.get("GULA_PROOF_DATABASE_URL")
    if not url:
        raise SystemExit("GULA_PROOF_DATABASE_URL is required; no database is selected implicitly")
    return psycopg2.connect(url)


def dispense(quantity: int, barrier: threading.Barrier) -> str:
    conn = connect()
    try:
        conn.autocommit = False
        barrier.wait(timeout=10)
        with conn.cursor() as cur:
            cur.execute(f"SELECT quantity_available FROM {BATCH_TABLE} WHERE batch_id = %s FOR UPDATE", ("synthetic-batch",))
            row = cur.fetchone()
            if row is None or row[0] < quantity:
                conn.rollback()
                return "conflict"
            cur.execute(f"UPDATE {BATCH_TABLE} SET quantity_available = quantity_available - %s WHERE batch_id = %s", (quantity, "synthetic-batch"))
            cur.execute(f"INSERT INTO {LEDGER_TABLE} (batch_id, quantity_delta) VALUES (%s, %s)", ("synthetic-batch", -quantity))
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
            cur.execute(f"CREATE TABLE {BATCH_TABLE} (batch_id varchar(64) PRIMARY KEY, quantity_available integer NOT NULL CHECK (quantity_available >= 0))")
            cur.execute(f"CREATE TABLE {LEDGER_TABLE} (id bigserial PRIMARY KEY, batch_id varchar(64) NOT NULL, quantity_delta integer NOT NULL CHECK (quantity_delta < 0))")
            cur.execute(f"INSERT INTO {BATCH_TABLE} (batch_id, quantity_available) VALUES ('synthetic-batch', 3)")
        barrier = threading.Barrier(2)
        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(lambda _: dispense(3, barrier), range(2)))
        assert sorted(results) == ["conflict", "winner"], results
        with owner.cursor() as cur:
            cur.execute(f"SELECT quantity_available FROM {BATCH_TABLE} WHERE batch_id = 'synthetic-batch'")
            assert cur.fetchone() == (0,)
            cur.execute(f"SELECT COUNT(*) FROM {LEDGER_TABLE}")
            assert cur.fetchone() == (1,)
        sys.stdout.write("postgres_pharmacy_stock_lock_proof=pass\n")
        sys.stdout.write("results=" + ",".join(sorted(results)) + "\n")
        sys.stdout.write("final_quantity_available=0\n")
        return 0
    finally:
        with owner.cursor() as cur:
            cur.execute(f"DROP TABLE IF EXISTS {LEDGER_TABLE}")
            cur.execute(f"DROP TABLE IF EXISTS {BATCH_TABLE}")
        owner.close()


if __name__ == "__main__":
    raise SystemExit(main())
