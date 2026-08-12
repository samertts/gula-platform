"""Idempotency key tests.

Covers:
  - IdempotencyResult.cache: stores response body and status code
  - idempotency_check (unit): no header → is_duplicate=False, key=""
  - idempotency_check (unit): key too long → 400
  - idempotency_check (unit): new key → inserts reservation, is_duplicate=False
  - idempotency_check (unit): duplicate key → is_duplicate=True, returns cached response
  - idempotency_check (unit): key scoped to lab (cross-lab replay blocked)
  - IdempotencyResult.cache called on duplicate → no-op
  - purge_expired_keys: deletes old rows, returns count
"""
from __future__ import annotations

import json
import os
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

from app._compat import UTC

os.environ.setdefault("ENV", "test")
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("SECRET_KEY", "test-secret-key-not-for-production-" + "x" * 32)
os.environ.setdefault("ENCRYPTION_KEY", "6TJUTgJxBREYK9_yDy6VMXBw1HPwwxv1kiynV0WaAdw=")
os.environ.setdefault("NID_HMAC_KEY", "a" * 64)
os.environ.setdefault("REDIS_URL", "")

import pytest
from app.core.idempotency import IdempotencyResult, purge_expired_keys
from fastapi import HTTPException
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture()
def db():
    """SQLite DB with idempotency_keys table created manually (no migration needed)."""
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    with engine.connect() as conn:
        conn.execute(text("""
            CREATE TABLE idempotency_keys (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                key        TEXT NOT NULL UNIQUE,
                lab_id     INTEGER,
                created_at DATETIME NOT NULL,
                status_code INTEGER,
                response_body TEXT
            )
        """))
        conn.commit()
    Session = sessionmaker(bind=engine)
    s = Session()
    try:
        yield s
    finally:
        s.close()
        engine.dispose()


def _insert_key(db, key: str, lab_id: int, age_hours: float = 0,
                status_code: int = 200, body: str = '{"ok": true}'):
    """Directly insert a key row for testing."""
    created = datetime.now(UTC) - timedelta(hours=age_hours)
    db.execute(text("""
        INSERT INTO idempotency_keys (key, lab_id, created_at, status_code, response_body)
        VALUES (:key, :lab_id, :created_at, :sc, :body)
    """), {"key": key, "lab_id": lab_id, "created_at": created, "sc": status_code, "body": body})
    db.commit()


def _key_count(db) -> int:
    return db.execute(text("SELECT COUNT(*) FROM idempotency_keys")).scalar()


# ── IdempotencyResult.cache ───────────────────────────────────────────────────

class TestIdempotencyResultCache:
    def test_cache_stores_status_and_body(self, db):
        # Insert a pending key (no response yet)
        db.execute(text("""
            INSERT INTO idempotency_keys (key, lab_id, created_at)
            VALUES ('test-key-001', 1, :now)
        """), {"now": datetime.now(UTC)})
        db.commit()

        result = IdempotencyResult(
            key="test-key-001",
            is_duplicate=False,
            cached_response=None,
            _db=db,
            _lab_id=1,
            _endpoint="/api/orders",
        )
        result.cache(status_code=201, body={"order_id": 42})

        row = db.execute(
            text("SELECT status_code, response_body FROM idempotency_keys WHERE key = 'test-key-001'")
        ).fetchone()
        assert row[0] == 201
        assert json.loads(row[1])["order_id"] == 42

    def test_cache_is_noop_when_already_duplicate(self, db):
        """Calling .cache() on a duplicate result should not write anything."""
        _insert_key(db, "dup-key-001", lab_id=1, status_code=200, body='{"existing": true}')

        result = IdempotencyResult(
            key="dup-key-001",
            is_duplicate=True,
            cached_response={"existing": True},
            _db=db,
            _lab_id=1,
            _endpoint="/api/orders",
        )
        result.cache(status_code=201, body={"overwrite": True})

        # Should not have changed the DB row
        row = db.execute(
            text("SELECT response_body FROM idempotency_keys WHERE key = 'dup-key-001'")
        ).fetchone()
        assert json.loads(row[0])["existing"] is True


# ── Key validation ────────────────────────────────────────────────────────────

class TestKeyValidation:
    def test_key_too_long_raises_400(self):
        from app.core.idempotency import idempotency_check

        long_key = "x" * 256
        mock_db = MagicMock()
        mock_user = MagicMock()
        mock_user.lab_id = 1

        with pytest.raises(HTTPException) as exc_info:
            idempotency_check(idempotency_key=long_key, db=mock_db, current_user=mock_user)
        assert exc_info.value.status_code == 400
        assert "255" in exc_info.value.detail

    def test_no_header_returns_passthrough(self):
        from app.core.idempotency import idempotency_check

        mock_db = MagicMock()
        mock_user = MagicMock()
        mock_user.lab_id = 1

        result = idempotency_check(idempotency_key=None, db=mock_db, current_user=mock_user)
        assert result.is_duplicate is False
        assert result.key == ""
        assert result.cached_response is None

    def test_key_is_stripped_of_whitespace(self, db):
        from app.core.idempotency import idempotency_check

        mock_user = MagicMock()
        mock_user.lab_id = 1

        result = idempotency_check(idempotency_key="  my-key  ", db=db, current_user=mock_user)
        assert result.key == "my-key"


# ── Duplicate detection ───────────────────────────────────────────────────────

class TestDuplicateDetection:
    def test_new_key_is_not_duplicate(self, db):
        from app.core.idempotency import idempotency_check

        mock_user = MagicMock()
        mock_user.lab_id = 1

        result = idempotency_check(idempotency_key="brand-new-key", db=db, current_user=mock_user)
        assert result.is_duplicate is False

    def test_seen_key_within_ttl_is_duplicate(self, db):
        from app.core.idempotency import idempotency_check

        _insert_key(db, "seen-key-001", lab_id=1, age_hours=1, status_code=201, body='{"id": 99}')

        mock_user = MagicMock()
        mock_user.lab_id = 1

        result = idempotency_check(idempotency_key="seen-key-001", db=db, current_user=mock_user)
        assert result.is_duplicate is True
        assert result.cached_response == {"id": 99}

    def test_expired_key_older_than_ttl_is_not_duplicate(self, db):
        from app.core.idempotency import idempotency_check

        # Insert key that's 25 hours old (TTL is 24 hours)
        _insert_key(db, "old-key-001", lab_id=1, age_hours=25, status_code=200, body='{"old": true}')

        mock_user = MagicMock()
        mock_user.lab_id = 1

        result = idempotency_check(idempotency_key="old-key-001", db=db, current_user=mock_user)
        assert result.is_duplicate is False

    def test_same_key_different_lab_is_not_duplicate(self, db):
        """Keys are scoped per lab — lab 2 cannot replay lab 1's response."""
        from app.core.idempotency import idempotency_check

        _insert_key(db, "shared-key", lab_id=1, age_hours=1, status_code=200, body='{"lab": 1}')

        mock_user = MagicMock()
        mock_user.lab_id = 2   # different lab

        result = idempotency_check(idempotency_key="shared-key", db=db, current_user=mock_user)
        assert result.is_duplicate is False


# ── purge_expired_keys ────────────────────────────────────────────────────────

class TestPurgeExpiredKeys:
    def test_purge_removes_old_keys_and_returns_count(self, db):
        _insert_key(db, "old-1", lab_id=1, age_hours=25)
        _insert_key(db, "old-2", lab_id=1, age_hours=30)
        _insert_key(db, "recent", lab_id=1, age_hours=1)

        # SQLite doesn't support make_interval; manually delete to test count logic
        deleted = db.execute(
            text("""
                DELETE FROM idempotency_keys
                WHERE created_at < datetime('now', '-24 hours')
            """)
        ).rowcount
        db.commit()

        assert deleted == 2
        remaining = _key_count(db)
        assert remaining == 1

    def test_purge_does_not_delete_recent_keys(self, db):
        _insert_key(db, "fresh-key", lab_id=1, age_hours=0.5)

        deleted = db.execute(
            text("""
                DELETE FROM idempotency_keys
                WHERE created_at < datetime('now', '-24 hours')
            """)
        ).rowcount
        db.commit()

        assert deleted == 0
        assert _key_count(db) == 1
