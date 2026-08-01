"""Unit tests for audit_service — hash-chained tamper-evident audit trail."""

from __future__ import annotations

import hashlib
import os

os.environ.setdefault("ENV", "test")
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("SECRET_KEY", "test-secret-key-not-for-production-" + "x" * 32)
os.environ.setdefault("ENCRYPTION_KEY", "6TJUTgJxBREYK9_yDy6VMXBw1HPwwxv1kiynV0WaAdw=")
os.environ.setdefault("NID_HMAC_KEY", "a" * 64)
os.environ.setdefault("REDIS_URL", "")
os.environ.setdefault("AUDIT_ANCHOR_KEY", "test-anchor-key-" + "k" * 32)
os.environ.setdefault("AUDIT_ANCHOR_DIR", "/tmp/gula-test-anchors")

import pytest
from app.database import Base
from app.models.audit_log import AuditLog
from app.services import audit_service
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool


@pytest.fixture(autouse=True)
def _isolate_anchors(tmp_path, monkeypatch):
    """Pin the anchor directory per test regardless of module import order."""
    monkeypatch.setattr(audit_service, "_ANCHOR_DIR", tmp_path / "anchors")
    yield


@pytest.fixture(scope="function")
def db_session():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    TestSession = sessionmaker(bind=engine)
    session = TestSession()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


def _entry(action="create", resource_type="patient", details="hello", created_at=None):
    from datetime import UTC, datetime

    return AuditLog(
        user_id=1,
        user_role="admin",
        action=action,
        resource_type=resource_type,
        resource_id=10,
        details=details,
        ip_address="127.0.0.1",
        created_at=created_at or datetime(2026, 1, 1, 12, 0, 0, tzinfo=UTC),
    )


def _aware_copy(entry):
    """SQLite drops tzinfo on round-trip; restore it like verify_audit_chain does."""
    copy = AuditLog(
        id=entry.id,
        user_id=entry.user_id,
        user_role=entry.user_role,
        action=entry.action,
        resource_type=entry.resource_type,
        resource_id=entry.resource_id,
        details=entry.details,
        ip_address=entry.ip_address,
        created_at=entry.created_at,
    )
    if copy.created_at is not None and copy.created_at.tzinfo is None:
        from datetime import UTC

        copy.created_at = copy.created_at.replace(tzinfo=UTC)
    return copy


class TestComputeChainHash:
    def test_deterministic_for_same_entry(self):
        e1 = _entry()
        e2 = _entry()
        assert audit_service._compute_chain_hash("0" * 64, e1) == audit_service._compute_chain_hash(
            "0" * 64, e2
        )

    def test_changes_with_prev_hash(self):
        e = _entry()
        h1 = audit_service._compute_chain_hash("0" * 64, e)
        h2 = audit_service._compute_chain_hash("f" * 64, e)
        assert h1 != h2

    def test_tamper_detection(self):
        e = _entry(details="original")
        h = audit_service._compute_chain_hash("0" * 64, e)
        e.details = "tampered"
        assert audit_service._compute_chain_hash("0" * 64, e) != h

    def test_output_is_sha256_hex(self):
        h = audit_service._compute_chain_hash("0" * 64, _entry())
        assert len(h) == 64
        int(h, 16)

    def test_links_entries_into_chain(self):
        e1 = _entry(details="first")
        e2 = _entry(details="second")
        e1.id, e2.id = 1, 2
        h1 = audit_service._compute_chain_hash("0" * 64, e1)
        h2 = audit_service._compute_chain_hash(h1, e2)
        assert h1 != h2
        assert audit_service._compute_chain_hash(h1, e2) == h2  # replay-safe


class TestAnchorHmac:
    def test_hmac_verifies_roundtrip(self):
        data = "v1|2026-08-01T00:00:00Z|100|abcd"
        sig = audit_service._anchor_hmac(data)
        assert audit_service._verify_anchor_hmac(data, sig) is True

    def test_hmac_rejects_tampered_data(self):
        data = "v1|2026-08-01T00:00:00Z|100|abcd"
        sig = audit_service._anchor_hmac(data)
        assert audit_service._verify_anchor_hmac(data + "x", sig) is False

    def test_hmac_rejects_wrong_key(self):
        data = "v1|2026-08-01T00:00:00Z|100|abcd"
        wrong_sig = audit_service._anchor_hmac(data, b"wrong-key")
        assert audit_service._verify_anchor_hmac(data, wrong_sig) is False

    def test_hmac_is_keyed_not_plain_hash(self):
        data = "test-data"
        assert audit_service._anchor_hmac(data) != hashlib.sha256(data.encode()).hexdigest()


class TestLogAction:
    def test_logs_entry_with_chain(self, db_session):
        audit_service.log_action(
            db_session, action="create", resource_type="patient", resource_id=7,
            user_id=3, user_role="technician", details="created patient", ip_address="10.0.0.1",
        )
        entry = db_session.query(AuditLog).one()
        assert entry.action == "create"
        assert entry.resource_type == "patient"
        assert entry.resource_id == 7
        assert entry.user_role == "technician"
        assert entry.details == "created patient"
        assert entry.chain_hash and len(entry.chain_hash) == 64

    def test_second_entry_chains_from_first(self, db_session):
        audit_service.log_action(db_session, "create", "patient")
        audit_service.log_action(db_session, "update", "patient")
        entries = db_session.query(AuditLog).order_by(AuditLog.id).all()
        assert entries[0].chain_hash != entries[1].chain_hash
        recomputed = audit_service._compute_chain_hash(entries[0].chain_hash, _aware_copy(entries[1]))
        assert recomputed == entries[1].chain_hash

    def test_genesis_hash_used_for_first(self, db_session):
        audit_service.log_action(db_session, "create", "patient")
        entry = db_session.query(AuditLog).one()
        assert audit_service._compute_chain_hash(audit_service._GENESIS_HASH, _aware_copy(entry)) == entry.chain_hash


class TestVerifyAuditChain:
    def test_verify_intact_chain(self, db_session):
        for i in range(5):
            audit_service.log_action(db_session, "create", "patient", resource_id=i)
        result = audit_service.verify_audit_chain(db_session, limit=100)
        assert result["verified"] is True
        assert result["entries_checked"] == 5

    def test_verify_detects_tampered_entry(self, db_session):
        audit_service.log_action(db_session, "create", "patient")
        audit_service.log_action(db_session, "update", "patient")
        tampered = db_session.query(AuditLog).filter(AuditLog.action == "create").one()
        tampered.details = "FORGED"
        db_session.commit()
        result = audit_service.verify_audit_chain(db_session, limit=100)
        assert result["verified"] is False

    def test_verify_detects_chain_break(self, db_session):
        audit_service.log_action(db_session, "create", "patient")
        entry = db_session.query(AuditLog).one()
        entry.chain_hash = "0" * 64
        db_session.commit()
        result = audit_service.verify_audit_chain(db_session, limit=100)
        assert result["verified"] is False


class TestAnchors:
    def test_anchor_written_at_interval(self, db_session, monkeypatch):
        monkeypatch.setattr(audit_service, "_ANCHOR_INTERVAL", 1)
        for i in range(3):
            audit_service.log_action(db_session, "create", "patient", resource_id=i)
        files = audit_service._all_anchor_files()
        assert files
        data = files[0].read_text(encoding="utf-8").strip().splitlines()
        assert data, "anchor lines should exist"
        assert len(data) == 3

    def test_get_latest_anchor(self, db_session, monkeypatch):
        monkeypatch.setattr(audit_service, "_ANCHOR_INTERVAL", 1)
        audit_service.log_action(db_session, "create", "patient")
        anchor = audit_service.get_latest_anchor()
        assert anchor is not None
        assert anchor["hmac_verified"] is True
        assert anchor["total_anchors"] >= 1

    def test_no_anchors_returns_none(self):
        assert audit_service.get_latest_anchor() is None
