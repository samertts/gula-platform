from __future__ import annotations

import os

os.environ.setdefault("ENV", "test")
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("SECRET_KEY", "test-secret-key-not-for-production-" + "x" * 32)
os.environ.setdefault("ENCRYPTION_KEY", "6TJUTgJxBREYK9_yDy6VMXBw1HPwwxv1kiynV0WaAdw=")
os.environ.setdefault("NID_HMAC_KEY", "a" * 64)
os.environ.setdefault("REDIS_URL", "")

import pytest

from shared.security.encryption import (
    decrypt_national_id,
    decrypt_value,
    encrypt_national_id,
    encrypt_value,
)


@pytest.fixture()
def keys() -> tuple[str, str]:
    return (
        "6TJUTgJxBREYK9_yDy6VMXBw1HPwwxv1kiynV0WaAdw=",
        "b" * 64,
    )


def test_encrypt_decrypt_value_round_trip(keys: tuple[str, str]) -> None:
    enc_key, _ = keys
    assert decrypt_value(encrypt_value("plain-text", enc_key), enc_key) == "plain-text"


def test_decrypt_value_rejects_corrupted_token(keys: tuple[str, str]) -> None:
    enc_key, _ = keys
    with pytest.raises(ValueError):
        decrypt_value("garbage-token", enc_key)


def test_national_id_round_trip(keys: tuple[str, str]) -> None:
    enc_key, hmac_key = keys
    token = encrypt_national_id("0123456789012345", enc_key, hmac_key)
    assert "." in token
    assert decrypt_national_id(token, enc_key, hmac_key) == "0123456789012345"


def test_national_id_tamper_detected(keys: tuple[str, str]) -> None:
    enc_key, hmac_key = keys
    token = encrypt_national_id("0123456789012345", enc_key, hmac_key)
    tampered = token[:-4] + "beef" + token[-4:]
    assert decrypt_national_id(tampered, enc_key, hmac_key) is None


def test_national_id_wrong_key_returns_none(keys: tuple[str, str]) -> None:
    enc_key, hmac_key = keys
    token = encrypt_national_id("0123456789012345", enc_key, hmac_key)
    assert decrypt_national_id(token, "other-key-" + "x" * 20, hmac_key) is None


def test_national_id_malformed_returns_none(keys: tuple[str, str]) -> None:
    enc_key, hmac_key = keys
    assert decrypt_national_id("no-dot-at-all", enc_key, hmac_key) is None
