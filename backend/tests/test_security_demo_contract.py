from __future__ import annotations

from typing import Any

import pytest
from app.models.lab import Lab
from app.models.lab_user import LabUser
from app.models.user import User

from shared.auth.passwords import hash_password


def test_auth_hardening_middleware_is_registered() -> None:
    from app.main import app

    middleware_names = {middleware.cls.__name__ for middleware in app.user_middleware}
    assert "CSRFMiddleware" in middleware_names
    assert "GlobalRateLimitMiddleware" in middleware_names


def test_global_rate_limit_fails_closed_without_shared_cache(client: Any, monkeypatch: pytest.MonkeyPatch) -> None:
    from app import middleware
    from app.security import redis_client
    from app.security.redis_client import _MemoryStore

    monkeypatch.setattr(middleware, "IS_PRODUCTION", True)
    monkeypatch.setattr(redis_client, "cache", _MemoryStore())

    response = client.get("/test-types")
    assert response.status_code == 503
    assert response.headers["Retry-After"] == "5"


def test_failed_login_is_a_safe_401(client: Any) -> None:
    response = client.post("/login", json={"email": "nobody@example.com", "password": "wrong-password"})
    assert response.status_code == 401
    assert "traceback" not in response.text.lower()


def test_user_verification_round_trip(client: Any, db: Any) -> None:
    user = User(
        email="citizen@example.com",
        phone="+9647701111111",
        password_hash=hash_password("CitizenPassword123!"),
        full_name="Demo Citizen",
        role="citizen",
        is_active=True,
        is_verified=False,
    )
    db.add(user)
    db.commit()

    requested = client.post("/auth/verification/request", json={"identifier": user.email})
    assert requested.status_code == 202
    code = requested.json().get("demo_code")
    assert code and len(code) == 6

    confirmed = client.post(
        "/auth/verification/confirm",
        json={"identifier": user.email, "code": code},
    )
    assert confirmed.status_code == 200
    db.refresh(user)
    assert user.is_verified is True

    logged_in = client.post(
        "/login",
        json={"email": user.email, "password": "CitizenPassword123!"},
    )
    assert logged_in.status_code == 200
    assert logged_in.cookies.get("access_token")


def test_verification_resend_is_throttled_and_code_is_single_use(client: Any, db: Any) -> None:
    user = User(
        email="citizen-verification-replay@example.com",
        phone="+9647701111122",
        password_hash=hash_password("CitizenPassword123!"),
        full_name="Replay Citizen",
        role="citizen",
        is_active=True,
        is_verified=False,
    )
    db.add(user)
    db.commit()

    first = client.post(
        "/auth/verification/request",
        json={"identifier": user.email},
    )
    code = first.json().get("demo_code")
    assert first.status_code == 202
    assert code and len(code) == 6

    resend = client.post(
        "/auth/verification/request",
        json={"identifier": user.email},
    )
    assert resend.status_code == 202
    assert "demo_code" not in resend.json()

    confirmed = client.post(
        "/auth/verification/confirm",
        json={"identifier": user.email, "code": code},
    )
    assert confirmed.status_code == 200

    replay = client.post(
        "/auth/verification/confirm",
        json={"identifier": user.email, "code": code},
    )
    assert replay.status_code == 400


def test_verification_provider_failure_never_succeeds(client: Any, db: Any, monkeypatch: pytest.MonkeyPatch) -> None:
    user = User(
        email="citizen-verification-provider@example.com",
        phone="+9647701111144",
        password_hash=hash_password("CitizenPassword123!"),
        full_name="Provider Failure Citizen",
        role="citizen",
        is_active=True,
        is_verified=False,
    )
    db.add(user)
    db.commit()

    class _FailureService:
        def send_email(self, *_args: Any, **_kwargs: Any) -> Any:
            return type("Delivery", (), {"success": False})()

        def send_sms(self, *_args: Any, **_kwargs: Any) -> Any:
            return type("Delivery", (), {"success": False})()

    monkeypatch.setattr(
        "app.notifications.service.get_service",
        lambda: _FailureService(),
    )
    response = client.post(
        "/auth/verification/request",
        json={"identifier": user.email},
    )

    assert response.status_code == 202
    assert "demo_code" not in response.json()
    db.refresh(user)
    assert user.is_verified is False


def test_verification_attempt_limit_is_server_authoritative(client: Any, db: Any) -> None:
    user = User(
        email="citizen-verification-attempts@example.com",
        phone="+9647701111133",
        password_hash=hash_password("CitizenPassword123!"),
        full_name="Attempt Citizen",
        role="citizen",
        is_active=True,
        is_verified=False,
    )
    db.add(user)
    db.commit()

    requested = client.post(
        "/auth/verification/request",
        json={"identifier": user.email},
    )
    assert requested.status_code == 202
    wrong_code = "000001" if requested.json().get("demo_code") != "000001" else "999999"

    for _ in range(5):
        failed = client.post(
            "/auth/verification/confirm",
            json={"identifier": user.email, "code": wrong_code},
        )
        assert failed.status_code == 400

    blocked = client.post(
        "/auth/verification/confirm",
        json={"identifier": user.email, "code": wrong_code},
    )
    assert blocked.status_code == 429
    db.refresh(user)
    assert user.is_verified is False


def test_verification_request_does_not_enumerate_unknown_identifier(client: Any) -> None:
    response = client.post(
        "/auth/verification/request",
        json={"identifier": "unknown-verification@example.com"},
    )
    assert response.status_code == 202
    assert response.json() == {
        "message": "If the account exists, a verification code has been sent."
    }


def test_cross_origin_cookie_write_is_rejected(client: Any, db: Any) -> None:
    lab = Lab(name="CSRF Lab", is_active=True)
    db.add(lab)
    db.flush()
    user = LabUser(
        lab_id=lab.id,
        name="CSRF Admin",
        email="csrf-admin@example.com",
        password_hash=hash_password("AdminPassword123!"),
        role="admin",
        is_active=True,
    )
    db.add(user)
    db.commit()

    logged_in = client.post(
        "/login",
        json={"email": user.email, "password": "AdminPassword123!"},
    )
    assert logged_in.status_code == 200
    rejected = client.post("/logout", headers={"Origin": "https://evil.example"})
    assert rejected.status_code == 403


def test_cross_origin_refresh_cookie_write_is_rejected(client: Any, db: Any) -> None:
    lab = Lab(name="CSRF Refresh Lab", is_active=True)
    db.add(lab)
    db.flush()
    user = LabUser(
        lab_id=lab.id,
        name="CSRF Refresh Admin",
        email="csrf-refresh-admin@example.com",
        password_hash=hash_password("AdminPassword123!"),
        role="admin",
        is_active=True,
    )
    db.add(user)
    db.commit()

    logged_in = client.post(
        "/login",
        json={"email": user.email, "password": "AdminPassword123!"},
    )
    assert logged_in.status_code == 200
    client.cookies.delete("access_token")
    rejected = client.post(
        "/auth/refresh",
        headers={"Origin": "https://evil.example"},
    )
    assert rejected.status_code == 403


def test_demo_access_is_disabled_by_default(client: Any) -> None:
    response = client.post("/demo/access")
    assert response.status_code == 404


def test_web_login_does_not_echo_bearer_tokens(client: Any, db: Any) -> None:
    user = User(
        email="web-session@example.com",
        phone="+9647701112222",
        password_hash=hash_password("WebPassword123!"),
        full_name="Web Session User",
        role="citizen",
        is_active=True,
        is_verified=True,
    )
    db.add(user)
    db.commit()

    response = client.post(
        "/login",
        json={"email": "web-session@example.com", "password": "WebPassword123!"},
    )

    assert response.status_code == 200
    body = response.json()
    assert "access_token" not in body
    assert "token" not in body
    assert "refresh_token" not in body
    assert "access_token=" in response.headers.get("set-cookie", "")
    assert "HttpOnly" in response.headers.get("set-cookie", "")


def test_malformed_verification_cache_is_safe_400(client: Any, db: Any) -> None:
    from app.routes import verification as verification_route

    identifier = "malformed-cache@example.com"
    user = User(
        email=identifier,
        phone="+9647701113333",
        password_hash=hash_password("CitizenPassword123!"),
        full_name="Malformed Cache Citizen",
        role="citizen",
        is_active=True,
        is_verified=False,
    )
    db.add(user)
    db.commit()
    verification_route.cache.set(verification_route._cache_key(identifier), "not-json", ex=60)

    response = client.post(
        "/auth/verification/confirm",
        json={"identifier": identifier, "code": "123456"},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid or expired verification code"


def test_web_refresh_hides_tokens_and_native_refresh_preserves_contract(client: Any, db: Any) -> None:
    user = User(
        email="refresh-contract@example.com",
        phone="+9647701114444",
        password_hash=hash_password("RefreshPassword123!"),
        full_name="Refresh Contract User",
        role="citizen",
        is_active=True,
        is_verified=True,
    )
    db.add(user)
    db.commit()

    logged_in = client.post(
        "/login",
        json={"email": user.email, "password": "RefreshPassword123!"},
    )
    assert logged_in.status_code == 200
    assert client.cookies.get("refresh_token")
    assert "access_token" not in logged_in.json()

    native_login = client.post(
        "/login",
        json={"email": user.email, "password": "RefreshPassword123!"},
        headers={"X-Client-Platform": "android"},
    )
    assert native_login.status_code == 200
    assert native_login.json().get("access_token")
    assert native_login.json().get("refresh_token")

    web_refresh = client.post("/auth/refresh", json={})
    assert web_refresh.status_code == 200
    assert "access_token" not in web_refresh.json()
    assert "refresh_token" not in web_refresh.json()
    assert client.cookies.get("refresh_token")

    native_refresh_token = client.cookies.get("refresh_token")
    native_refresh = client.post(
        "/auth/refresh",
        json={"refresh_token": native_refresh_token},
    )
    assert native_refresh.status_code == 200
    native_body = native_refresh.json()
    assert native_body.get("access_token")
    assert native_body.get("refresh_token")

    replay = client.post("/auth/refresh", json={"refresh_token": native_refresh_token})
    assert replay.status_code == 401
    assert "reuse" in replay.json()["detail"].lower()


def test_account_kind_prevents_legacy_id_collision_on_session_and_logout(client: Any, db: Any) -> None:
    lab = Lab(name="Namespace Lab", is_active=True)
    db.add(lab)
    db.flush()
    staff = LabUser(
        lab_id=lab.id,
        name="Colliding Staff",
        email="colliding-staff@example.com",
        password_hash=hash_password("StaffPassword123!"),
        role="admin",
        is_active=True,
        perm_version=1,
    )
    citizen = User(
        email="colliding-citizen@example.com",
        phone="+9647701115555",
        password_hash=hash_password("CitizenPassword123!"),
        full_name="Colliding Citizen",
        role="citizen",
        is_active=True,
        is_verified=True,
        perm_version=1,
    )
    db.add_all([staff, citizen])
    db.commit()
    assert staff.id == citizen.id

    logged_in = client.post(
        "/login",
        json={"email": citizen.email, "password": "CitizenPassword123!"},
    )
    assert logged_in.status_code == 200

    session = client.get("/session")
    assert session.status_code == 200
    assert session.json()["user"]["email"] == citizen.email

    logged_out = client.post("/logout")
    assert logged_out.status_code == 200
    db.refresh(staff)
    db.refresh(citizen)
    assert staff.perm_version == 1
    assert citizen.perm_version == 2


def test_unscoped_legacy_token_is_rejected(client: Any) -> None:
    from app.security.auth import create_token

    token = create_token({"user_id": 1, "role": "citizen", "perm_ver": 1})
    client.cookies.set("access_token", token)

    response = client.get("/session")

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid token account scope"
