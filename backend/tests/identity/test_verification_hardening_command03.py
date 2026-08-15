from __future__ import annotations

from types import SimpleNamespace

import pytest
from app.notifications.service import NotificationResult
from app.routes import verification
from app.routes.verification import VerificationConfirmRequest, VerificationRequest
from app.security.redis_client import cache
from fastapi import HTTPException
from starlette.requests import Request


class _Query:
    def __init__(self, user):
        self.user = user

    def filter(self, *_args, **_kwargs):
        return self

    def first(self):
        return self.user


class _Db:
    def __init__(self, user):
        self.user = user

    def query(self, _model):
        return _Query(self.user)

    def commit(self):
        return None


def _request() -> Request:
    return Request(
        {
            "type": "http",
            "method": "POST",
            "path": "/auth/verification/confirm",
            "headers": [],
            "client": ("127.0.0.1", 12345),
            "scheme": "https",
            "server": ("testserver", 443),
        },
    )


def _user(identifier: str):
    return SimpleNamespace(
        id=42,
        email=identifier,
        phone=None,
        is_verified=False,
        is_active=True,
        role="citizen",
        perm_version=1,
    )


def _service(success: bool = True):
    return SimpleNamespace(
        send_email=lambda *_args, **_kwargs: NotificationResult(
            success=success,
            channel="email",
            recipient="redacted@example.invalid",
        ),
        send_sms=lambda *_args, **_kwargs: NotificationResult(
            success=success,
            channel="sms",
            recipient="redacted",
        ),
    )


def _clear(identifier: str):
    for key in (
        verification._cache_key(identifier),
        verification._attempt_key(identifier),
        verification._resend_key(identifier),
        verification._locked_key(identifier),
    ):
        cache.delete(key)


def test_request_verification_is_enumeration_resistant_and_resend_throttled(monkeypatch):
    identifier = "otp-command03@example.com"
    user = _user(identifier)
    db = _Db(user)
    monkeypatch.setattr(verification, "rate_limit_auth", lambda _request: None)
    monkeypatch.setattr(verification, "log_action", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(verification, "IS_PRODUCTION", True)
    monkeypatch.setattr(verification, "DEMO_MODE", False)
    monkeypatch.setattr("app.notifications.service.get_service", lambda: _service())
    _clear(identifier)

    unknown = verification.request_verification(
        VerificationRequest(identifier="unknown-command03@example.com"),
        _request(),
        _Db(None),
    )
    responses = [
        verification.request_verification(VerificationRequest(identifier=identifier), _request(), db)
        for _ in range(4)
    ]

    assert unknown == responses[0] == {"message": verification._GENERIC_MESSAGE}
    assert responses[-1] == {"message": verification._GENERIC_MESSAGE}
    assert cache.get(verification._resend_key(identifier)) == "3"
    _clear(identifier)


def test_provider_failure_never_stores_otp(monkeypatch):
    identifier = "provider-failure-command03@example.com"
    monkeypatch.setattr("app.notifications.service.get_service", lambda: _service(success=False))
    _clear(identifier)

    code = verification._issue_code(_user(identifier), identifier)

    assert code is None
    assert cache.get(verification._cache_key(identifier)) is None
    _clear(identifier)


def test_bruteforce_lock_and_replay_protection(monkeypatch):
    identifier = "bruteforce-command03@example.com"
    user = _user(identifier)
    db = _Db(user)
    monkeypatch.setattr(verification, "rate_limit_auth", lambda _request: None)
    monkeypatch.setattr(verification, "log_action", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(verification, "IS_PRODUCTION", False)
    monkeypatch.setattr(verification, "DEMO_MODE", True)
    monkeypatch.setattr("app.notifications.service.get_service", lambda: _service())
    _clear(identifier)

    issued = verification.request_verification(VerificationRequest(identifier=identifier), _request(), db)
    code = issued["demo_code"]
    for _ in range(4):
        with pytest.raises(HTTPException) as error:
            verification.confirm_verification(
                VerificationConfirmRequest(identifier=identifier, code="000000"),
                _request(),
                db,
            )
        assert error.value.status_code == 400

    with pytest.raises(HTTPException) as locked:
        verification.confirm_verification(
            VerificationConfirmRequest(identifier=identifier, code="000000"),
            _request(),
            db,
        )
    assert locked.value.status_code == 429
    assert cache.get(verification._locked_key(identifier)) == "1"

    with pytest.raises(HTTPException) as replay:
        verification.confirm_verification(
            VerificationConfirmRequest(identifier=identifier, code=code),
            _request(),
            db,
        )
    assert replay.value.status_code == 429
    _clear(identifier)


def test_valid_code_is_single_use(monkeypatch):
    identifier = "single-use-command03@example.com"
    user = _user(identifier)
    db = _Db(user)
    monkeypatch.setattr(verification, "rate_limit_auth", lambda _request: None)
    monkeypatch.setattr(verification, "log_action", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(verification, "IS_PRODUCTION", False)
    monkeypatch.setattr(verification, "DEMO_MODE", True)
    monkeypatch.setattr("app.notifications.service.get_service", lambda: _service())
    _clear(identifier)

    issued = verification.request_verification(VerificationRequest(identifier=identifier), _request(), db)
    code = issued["demo_code"]
    result = verification.confirm_verification(
        VerificationConfirmRequest(identifier=identifier, code=code),
        _request(),
        db,
    )
    assert result["message_ar"] == "تم التحقق من الحساب بنجاح"
    assert user.is_verified is True

    with pytest.raises(HTTPException) as replay:
        verification.confirm_verification(
            VerificationConfirmRequest(identifier=identifier, code=code),
            _request(),
            db,
        )
    assert replay.value.status_code == 400
    _clear(identifier)
