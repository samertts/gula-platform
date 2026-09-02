"""Concurrent proof for the canonical ClinicalCommandGuard idempotency claim."""
from __future__ import annotations

import os
import threading

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from app.clinical.command_guard import ClinicalCommandGuard
from app.models.clinical_command import ClinicalCommandReceipt

POSTGRES_URL = os.getenv("BLOOD_BANK_POSTGRES_URL")
pytestmark = pytest.mark.skipif(not POSTGRES_URL, reason="BLOOD_BANK_POSTGRES_URL is not configured")


def test_concurrent_same_idempotency_key_claims_once() -> None:
    engine = create_engine(POSTGRES_URL, future=True, pool_size=4, max_overflow=0)
    Session = sessionmaker(bind=engine, expire_on_commit=False)
    # The repository currently has duplicate 20260819_0003 revisions, so the
    # unrelated command-receipt migration is not on the targeted Blood Bank
    # chain. Create the exact canonical SQLAlchemy table only in this disposable
    # verification database; production migrations remain untouched.
    ClinicalCommandReceipt.__table__.create(bind=engine, checkfirst=True)
    lab_id, actor_id, key = 991003, 7001, "BB-ISSUE-CONCURRENT-001"
    with engine.begin() as conn:
        conn.execute(text("INSERT INTO labs (id, name, is_active) VALUES (:id, :name, true) ON CONFLICT (id) DO NOTHING"), {"id": lab_id, "name": "Synthetic Blood Bank Verification Lab"})
        conn.execute(text("INSERT INTO lab_users (id, lab_id, name, email, password_hash, role, is_active, perm_version) VALUES (:id, :lab_id, :name, :email, :password_hash, :role, true, 1) ON CONFLICT (id) DO NOTHING"), {"id": actor_id, "lab_id": lab_id, "name": "Synthetic Verifier", "email": "synthetic-verifier@example.invalid", "password_hash": "!synthetic-only", "role": "blood_bank_technician"})
    cleanup = Session()
    try:
        cleanup.query(ClinicalCommandReceipt).filter(ClinicalCommandReceipt.lab_id == lab_id, ClinicalCommandReceipt.idempotency_key == key).delete(synchronize_session=False)
        cleanup.commit()
    finally:
        cleanup.close()

    barrier = threading.Barrier(2)
    outcomes: list[str] = []
    errors: list[str] = []
    lock = threading.Lock()

    def attempt() -> None:
        session = Session()
        try:
            barrier.wait(timeout=10)
            guard = ClinicalCommandGuard(session, actor_user_id=actor_id, lab_id=lab_id, actor_role="blood_bank_technician")
            guard.claim(operation="blood.issue", resource_type="blood_request", resource_id="request-1", idempotency_key=key, payload={"quantity": 1})
            session.commit()
            result = "claimed"
        except Exception as exc:
            session.rollback()
            result = "conflict" if type(exc).__name__ == "HTTPException" else f"error:{type(exc).__name__}"
            errors.append(str(exc))
        finally:
            session.close()
        with lock:
            outcomes.append(result)

    threads = [threading.Thread(target=attempt) for _ in range(2)]
    for thread in threads: thread.start()
    for thread in threads: thread.join(timeout=30)

    verify = Session()
    try:
        assert sorted(outcomes) == ["claimed", "conflict"], errors
        assert verify.query(ClinicalCommandReceipt).filter(ClinicalCommandReceipt.lab_id == lab_id, ClinicalCommandReceipt.idempotency_key == key).count() == 1
    finally:
        verify.close()
        cleanup = Session()
        cleanup.query(ClinicalCommandReceipt).filter(ClinicalCommandReceipt.lab_id == lab_id, ClinicalCommandReceipt.idempotency_key == key).delete(synchronize_session=False)
        cleanup.commit(); cleanup.close(); engine.dispose()
