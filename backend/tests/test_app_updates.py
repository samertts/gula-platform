from app.routes.app_updates import build_policy, router, version_is_less
from fastapi import FastAPI
from fastapi.testclient import TestClient


def test_manifest_endpoint_returns_policy(monkeypatch):
    monkeypatch.setenv("GULA_WEB_LATEST_VERSION", "2.6.0")
    monkeypatch.setenv("GULA_WEB_MINIMUM_SUPPORTED_VERSION", "2.5.0")
    app = FastAPI()
    app.include_router(router)

    response = TestClient(app).get("/app-updates?platform=web&version=2.4.0")

    assert response.status_code == 200
    payload = response.json()
    assert payload["schema_version"] == 1
    assert payload["policies"]["web"]["force_update"] is True


def test_version_comparison_is_semantic():
    assert version_is_less("2.4.10", "2.5.0")
    assert not version_is_less("2.5.0", "2.5.0")
    assert not version_is_less("2.5.1", "2.5.0")


def test_policy_marks_optional_update(monkeypatch):
    monkeypatch.setenv("GULA_WEB_LATEST_VERSION", "2.6.0")
    monkeypatch.setenv("GULA_WEB_MINIMUM_SUPPORTED_VERSION", "2.5.0")
    policy = build_policy("web", "2.5.0")
    assert policy.update_available is True
    assert policy.force_update is False
    assert policy.minimum_supported_version == "2.5.0"


def test_policy_marks_forced_update(monkeypatch):
    monkeypatch.setenv("GULA_ANDROID_LATEST_VERSION", "2.6.0")
    monkeypatch.setenv("GULA_ANDROID_MINIMUM_SUPPORTED_VERSION", "2.5.0")
    policy = build_policy("android", "2.4.0")
    assert policy.update_available is True
    assert policy.force_update is True


def test_policy_clamps_invalid_minimum_above_latest(monkeypatch):
    monkeypatch.setenv("GULA_WINDOWS_LATEST_VERSION", "2.5.0")
    monkeypatch.setenv("GULA_WINDOWS_MINIMUM_SUPPORTED_VERSION", "3.0.0")
    policy = build_policy("windows", "2.4.0")
    assert policy.minimum_supported_version == "2.5.0"
    assert policy.force_update is True


def test_malformed_versions_use_safe_default(monkeypatch):
    monkeypatch.setenv("GULA_LINUX_LATEST_VERSION", "not-a-version")
    monkeypatch.setenv("GULA_LINUX_MINIMUM_SUPPORTED_VERSION", "2.5.0")
    policy = build_policy("linux", "2.5.0")
    assert policy.latest_version == "2.5.0"
    assert policy.force_update is False
