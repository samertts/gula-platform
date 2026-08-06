"""Unit tests for scripts/reencrypt-encryption-key.py (key rotation re-encryption)."""

from __future__ import annotations

import os
import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3]))

from scripts import reencrypt_encryption_key as rr
from shared.security.encryption import decrypt_value, encrypt_value

OLD_KEY = os.getenv("ENCRYPTION_KEY", "6TJUTgJxBREYK9_yDy6VMXBw1HPwwxv1kiynV0WaAdw=")
NEW_KEY = "R5XU7m7iWRKE9_zaDy6VMXBw1HPwwxv1kiynV0WaBcx="


class TestReencryptValue:
    def test_fernert_token_is_reencrypted(self):
        token = encrypt_value("07001234567", OLD_KEY)
        result = rr.reencrypt_value(OLD_KEY, NEW_KEY, token)
        assert result is not None
        assert result != token
        assert decrypt_value(result, NEW_KEY) == "07001234567"

    def test_value_encrypted_with_other_key_untouched(self):
        from cryptography.fernet import Fernet

        other = Fernet.generate_key().decode()
        token = encrypt_value("secret", other)
        assert rr.reencrypt_value(OLD_KEY, NEW_KEY, token) == token

    def test_plain_hmac_value_untouched(self):
        hmac_hex = "a" * 64
        assert rr.reencrypt_value(OLD_KEY, NEW_KEY, hmac_hex) == hmac_hex

    def test_empty_and_none_untouched(self):
        assert rr.reencrypt_value(OLD_KEY, NEW_KEY, "") == ""
        assert rr.reencrypt_value(OLD_KEY, NEW_KEY, None) is None

    def test_garbage_string_untouched(self):
        assert rr.reencrypt_value(OLD_KEY, NEW_KEY, "not-a-token") == "not-a-token"


class TestReencryptRows:
    class _FakeEngine:
        def __init__(self):
            self._calls = []

        def begin(self):
            return self

        def __enter__(self):
            return self

        def __exit__(self, *exc):
            return False

        def execute(self, *a, **k):
            self._calls.append((a, k))

    def _make_calls(self):
        calls = []

        def update(engine, table, column, row_id, new_value):
            calls.append((row_id, new_value))

        return calls, update

    def test_batches_reencrypted_and_untouched(self):
        token1 = encrypt_value("1", OLD_KEY)
        token2 = encrypt_value("2", OLD_KEY)
        rows = [(1, token1), (2, "f" * 64), (3, token2)]
        calls, update = self._make_calls()

        def fetch(engine, table, column, last_id, batch_size):
            return rows if last_id is None else []

        summary = rr.reencrypt_rows(
            self._FakeEngine(), "t", "c", OLD_KEY, NEW_KEY,
            fetch=fetch, update=update,
        )
        assert summary == {"reencrypted": 2, "untouched": 1, "failed": 0}
        assert [c[0] for c in calls] == [1, 3]
        assert decrypt_value(calls[0][1], NEW_KEY) == "1"
        assert decrypt_value(calls[1][1], NEW_KEY) == "2"

    def test_dry_run_does_not_write(self):
        token = encrypt_value("x", OLD_KEY)
        calls, update = self._make_calls()

        def fetch(engine, table, column, last_id, batch_size):
            return [(1, token)] if last_id is None else []

        summary = rr.reencrypt_rows(
            self._FakeEngine(), "t", "c", OLD_KEY, NEW_KEY,
            dry_run=True, fetch=fetch, update=update,
        )
        assert summary["reencrypted"] == 1
        assert calls == []

    def test_paging_across_batches(self):
        token = encrypt_value("p", OLD_KEY)
        seen = []

        def fetch(engine, table, column, last_id, batch_size):
            seen.append(last_id)
            if last_id is None:
                return [(1, token)]
            if last_id == 1:
                return [(2, token)]
            return []

        _calls, update = self._make_calls()
        summary = rr.reencrypt_rows(
            self._FakeEngine(), "t", "c", OLD_KEY, NEW_KEY,
            batch_size=1, fetch=fetch, update=update,
        )
        assert summary["reencrypted"] == 2
        assert seen == [None, 1, 2]


class TestMain:
    def test_missing_keys_returns_2(self, capsys):
        assert rr.main(["--old-key", "", "--new-key", ""]) == 2

    def test_identical_keys_returns_2(self, capsys):
        assert rr.main(["--old-key", OLD_KEY, "--new-key", OLD_KEY]) == 2

    def test_missing_database_url_returns_2(self, monkeypatch, capsys):
        monkeypatch.delenv("DATABASE_URL", raising=False)
        assert rr.main(["--old-key", OLD_KEY, "--new-key", NEW_KEY]) == 2


class TestIdentifierValidation:
    def test_accepts_plain_identifiers(self):
        assert rr._validate_identifier("national_citizens", "table") == "national_citizens"
        assert rr._validate_identifier("national_id_hash", "column") == "national_id_hash"

    def test_rejects_sql_injection_identifiers(self):
        payload = "national_id_hash; DROP TABLE audit_logs"
        with pytest.raises(SystemExit):
            rr._validate_identifier(payload, "column")

    def test_rejects_quoted_identifier(self):
        with pytest.raises(SystemExit):
            rr._validate_identifier("national_id_hash' OR '1'='1", "column")

    def test_main_rejects_injection_table(self, monkeypatch, capsys):
        monkeypatch.setenv("DATABASE_URL", "sqlite:///memory")
        with pytest.raises(SystemExit):
            rr.main(["--old-key", OLD_KEY, "--new-key", NEW_KEY,
                     "--table", "citizens; DELETE FROM audit_logs"])
