"""P0-C regression tests — WebAuthn relying-party config and challenge lifecycle.

Synthetic values only. These tests pin defects where:
  * RP ID/origin were hardcoded to production values (broke every other env),
  * ``json.dumps(default=str)`` corrupted the base64url challenge,
  * registration and authentication shared one challenge key,
  * cache failures were swallowed and challenges were reusable (replay).
"""

from __future__ import annotations

import base64
import json

import pytest
from app.security.mfa_service import MFAService, WebAuthnError
from app.security.redis_client import cache

from shared.auth.webauthn import (
    _b64url_decode,
    _challenge_bytes,
    _serialize_options,
    validate_relying_party,
)

USER_ID = 424242


@pytest.fixture(autouse=True)
def _clean_challenge_keys():
    for purpose in ("reg", "auth"):
        key = MFAService._challenge_key(USER_ID, purpose)
        cache.delete(key)
        cache.delete(f"{key}:consumed")
    yield
    for purpose in ("reg", "auth"):
        key = MFAService._challenge_key(USER_ID, purpose)
        cache.delete(key)
        cache.delete(f"{key}:consumed")


# ── Relying-party validation (invalid origin / RP config) ────────────────────


@pytest.mark.parametrize(
    ("rp_id", "origin"),
    [
        ("", "https://app.gula.health"),
        ("bad id", "https://app.gula.health"),
        ("gula.health", ""),
        ("gula.health", "ftp://app.gula.health"),
        ("gula.health", "https://"),
        ("gula.health", "http://app.gula.health"),  # HTTPS required off localhost
        ("gula.health", "https://evil.example.com"),  # host must match RP
    ],
)
def test_validate_relying_party_rejects_invalid_config(rp_id, origin):
    with pytest.raises(ValueError):
        validate_relying_party(rp_id, origin)


def test_validate_relying_party_accepts_matching_https_and_localhost():
    validate_relying_party("gula.health", "https://app.gula.health")
    validate_relying_party("gula.health", "https://gula.health")
    validate_relying_party("localhost", "http://localhost:5173")


# ── Byte fidelity: base64url, not Python repr ────────────────────────────────


def test_serialize_options_emits_valid_base64url_challenge():
    raw = bytes(range(32))
    serialized = _serialize_options({"challenge": raw, "kind": "KIND"})
    challenge = serialized["challenge"]
    assert isinstance(challenge, str)
    assert "b'" not in challenge
    assert base64.urlsafe_b64decode(challenge + "=" * (-len(challenge) % 4)) == raw
    assert serialized["kind"] == "KIND"  # Enum-like values fall through


def test_challenge_bytes_strict_decoding():
    raw = b"synthetic-challenge"
    encoded = base64.urlsafe_b64encode(raw).rstrip(b"=").decode()
    assert _challenge_bytes(encoded) == raw
    assert _challenge_bytes(raw) == raw
    with pytest.raises(ValueError):
        _challenge_bytes("")
    with pytest.raises(ValueError):
        _challenge_bytes("!!!not-base64!!!")
    with pytest.raises(ValueError):
        _b64url_decode("")


# ── Challenge lifecycle: namespaces, missing, replay, store errors ──────────


def test_registration_and_authentication_challenges_are_namespaced():
    reg_key = MFAService._challenge_key(USER_ID, "reg")
    auth_key = MFAService._challenge_key(USER_ID, "auth")
    assert reg_key != auth_key

    MFAService._store_challenge(USER_ID, "reg", "reg-challenge")
    with pytest.raises(WebAuthnError, match="missing or expired"):
        MFAService._consume_challenge(USER_ID, "auth")
    assert MFAService._consume_challenge(USER_ID, "reg") == "reg-challenge"


def test_missing_challenge_fails_closed():
    with pytest.raises(WebAuthnError, match="missing or expired"):
        MFAService._consume_challenge(USER_ID, "reg")


def test_expired_challenge_fails_closed(monkeypatch):
    MFAService._store_challenge(USER_ID, "reg", "will-expire")
    key = MFAService._challenge_key(USER_ID, "reg")
    # Force expiry via the memory store's clock by rewriting with ex=1 then
    # simulating time advancement on the stored entry.
    cache.set(key, "will-expire", ex=1)
    data = cache._data  # memory-store internal, test-only
    value, _ = data[key]
    data[key] = (value, 0.0)
    with pytest.raises(WebAuthnError, match="missing or expired"):
        MFAService._consume_challenge(USER_ID, "reg")


def test_challenge_is_single_use_replay_rejected():
    MFAService._store_challenge(USER_ID, "reg", "one-shot")
    assert MFAService._consume_challenge(USER_ID, "reg") == "one-shot"
    with pytest.raises(WebAuthnError, match="already been used"):
        MFAService._consume_challenge(USER_ID, "reg")


def test_new_ceremony_clears_prior_consumed_claim():
    MFAService._store_challenge(USER_ID, "reg", "first")
    MFAService._consume_challenge(USER_ID, "reg")
    MFAService._store_challenge(USER_ID, "reg", "second")
    assert MFAService._consume_challenge(USER_ID, "reg") == "second"


def test_store_errors_are_not_swallowed(monkeypatch):
    import app.security.redis_client as redis_client

    def _boom(_operation):
        raise RuntimeError("store unavailable")

    monkeypatch.setattr(redis_client, "security_store", _boom)
    with pytest.raises(RuntimeError, match="store unavailable"):
        MFAService._store_challenge(USER_ID, "reg", "x")
    with pytest.raises(RuntimeError, match="store unavailable"):
        MFAService._consume_challenge(USER_ID, "reg")


def test_complete_registration_without_challenge_raises_webauthn_error():
    service = MFAService(db=None)
    with pytest.raises(WebAuthnError):
        service.complete_webauthn_registration(USER_ID, {"id": "synthetic"})


def test_complete_authentication_without_challenge_raises_webauthn_error():
    # A fabricated device row so the lookup passes; the challenge is still
    # missing, so verification must fail closed.
    class _FakeDevice:
        credential_id = "synthetic-credential"
        public_key = json.dumps({"public_key": ""})
        sign_count = 0

    class _FakeQuery:
        def filter(self, *_args, **_kwargs):
            return self

        def first(self):
            return _FakeDevice()

    class _FakeDb:
        def query(self, *_args):
            return _FakeQuery()

    service = MFAService(db=_FakeDb())
    with pytest.raises(WebAuthnError):
        service.complete_webauthn_authentication(
            USER_ID, {"id": "synthetic-credential"},
        )
