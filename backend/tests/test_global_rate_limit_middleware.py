from app.middleware import GlobalRateLimitMiddleware
from fastapi import FastAPI
from fastapi.testclient import TestClient


def _build_app() -> FastAPI:
    app = FastAPI()
    app.add_middleware(
        GlobalRateLimitMiddleware,
        max_requests=2,
        window_seconds=60,
    )

    @app.get("/data")
    async def data():
        return {"ok": True}

    @app.get("/health")
    async def health():
        return {"status": "ok"}

    return app


def test_global_limiter_returns_standard_headers_and_429(monkeypatch):
    monkeypatch.setenv("ENV", "development")
    client = TestClient(_build_app())
    origin = {"X-Forwarded-For": "198.51.100.10"}

    first = client.get("/data", headers=origin)
    second = client.get("/data", headers=origin)
    blocked = client.get("/data", headers=origin)

    assert first.status_code == 200
    assert first.headers["x-ratelimit-limit"] == "2"
    assert first.headers["x-ratelimit-remaining"] == "1"
    assert second.status_code == 200
    assert second.headers["x-ratelimit-remaining"] == "0"
    assert blocked.status_code == 429
    assert blocked.headers["retry-after"].isdigit()
    assert blocked.headers["x-ratelimit-remaining"] == "0"


def test_health_probe_is_not_consumed_by_global_budget(monkeypatch):
    monkeypatch.setenv("ENV", "development")
    client = TestClient(_build_app())
    origin = {"X-Forwarded-For": "198.51.100.11"}

    for _ in range(10):
        assert client.get("/health", headers=origin).status_code == 200

    assert client.get("/data", headers=origin).status_code == 200
