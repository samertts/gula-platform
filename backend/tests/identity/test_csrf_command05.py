"""Command 05 CSRF and CORS browser-boundary tests."""

from __future__ import annotations

from app.security.csrf import CSRFMiddleware, issue_csrf_cookie
from fastapi import FastAPI, Response
from fastapi.testclient import TestClient


def _app() -> FastAPI:
    app = FastAPI()
    app.add_middleware(CSRFMiddleware)

    @app.post("/mutate")
    def mutate():
        return {"ok": True}

    @app.get("/issue")
    def issue(response: Response):
        issue_csrf_cookie(response)
        return {"ok": True}

    return app


def test_csrf_cookie_is_browser_readable_but_not_an_auth_secret():
    response = TestClient(_app()).get("/issue")
    cookie = response.headers["set-cookie"]
    assert "csrf_token=" in cookie
    assert "HttpOnly" not in cookie


def test_new_cookie_session_requires_matching_double_submit_token(monkeypatch):
    monkeypatch.setenv("ENV", "staging")
    monkeypatch.setenv("CORS_ORIGINS", "http://testserver")
    client = TestClient(_app())
    client.cookies.set("access_token", "access")
    client.cookies.set("csrf_token", "expected")

    accepted = client.post("/mutate", headers={"Origin": "http://testserver", "X-CSRF-Token": "expected"})
    rejected = client.post("/mutate", headers={"Origin": "http://testserver"})

    assert accepted.status_code == 200
    assert rejected.status_code == 403


def test_cross_origin_is_rejected_even_with_matching_token(monkeypatch):
    monkeypatch.setenv("ENV", "staging")
    monkeypatch.setenv("CORS_ORIGINS", "http://testserver")
    client = TestClient(_app())
    client.cookies.set("access_token", "access")
    client.cookies.set("csrf_token", "expected")

    response = client.post("/mutate", headers={"Origin": "https://evil.example", "X-CSRF-Token": "expected"})
    assert response.status_code == 403


def test_production_new_cookie_session_never_uses_test_bypass(monkeypatch):
    monkeypatch.setenv("ENV", "production")
    monkeypatch.setenv("CORS_ORIGINS", "http://testserver")
    client = TestClient(_app())
    client.cookies.set("access_token", "access")
    client.cookies.set("csrf_token", "expected")

    response = client.post("/mutate", headers={"Origin": "http://testserver"})
    assert response.status_code == 403


def test_old_cookie_session_remains_origin_bound_during_rollout(monkeypatch):
    monkeypatch.setenv("ENV", "staging")
    monkeypatch.setenv("CORS_ORIGINS", "http://testserver")
    client = TestClient(_app())
    client.cookies.set("access_token", "legacy-access")

    response = client.post("/mutate", headers={"Origin": "http://testserver"})
    assert response.status_code == 200
