"""Configuration tests for the isolated staging deployment boundary."""

import importlib
import sys

import pytest

STAGING_ENVIRONMENT = {
    "ENV": "staging",
    "RUNTIME_MODE": "api",
    "FEATURE_BACKGROUND_TASKS": "false",
    "BASE_URL": "https://api.staging.gula-platform.example",
    "CORS_ORIGINS": "https://staging.gula-platform.example",
    "TRUSTED_HOSTS": "api.staging.gula-platform.example",
    "GULA_DATABASE_URL": "postgresql://staging:isolated@db.example/staging",
    "REDIS_URL": "redis://cache.example:6379/0",
    "SECRET_KEY": "Q9wL2vR7mK4xH8zC1nF6pT3yB5dJ0sA9qE2uI7oG4lV8",
    "REFRESH_TOKEN_SECRET": "R4mX8zL2qH7vC1kN6pD3yB9wF5jA0sE4uI7oG2lV8tQ9",
    "ENCRYPTION_KEY": "M6rK1vH9qT4zC8nL2pF7yB3wD0jA5sE1uI9oG4lV8xQ2",
    "NID_HMAC_KEY": "N8qL3vR7mK1xH5zC9pF2yB6wD0jA4sE8uI7oG1lV9tQ3",
    "AUDIT_ANCHOR_KEY": "A5mX9zL3qH7vC1kN6pD2yB8wF4jR0sE6uI1oG5lV9tQ7",
}


def _load_config(monkeypatch: pytest.MonkeyPatch, **overrides: str):
    """Import config under a temporary, fully isolated environment."""
    environment = {**STAGING_ENVIRONMENT, **overrides}
    with monkeypatch.context() as scoped_env:
        for name, value in environment.items():
            scoped_env.setenv(name, value)
        if "DEMO_MODE" not in overrides:
            scoped_env.delenv("DEMO_MODE", raising=False)
        sys.modules.pop("app.config", None)
        try:
            return importlib.import_module("app.config")
        finally:
            sys.modules.pop("app.config", None)


def test_staging_uses_hardened_production_guards(monkeypatch: pytest.MonkeyPatch) -> None:
    config = _load_config(monkeypatch)

    assert config.IS_STAGING is True
    assert config.IS_PRODUCTION is True
    assert config.USE_SECURE_COOKIES is True
    assert config.background_tasks_enabled() is False


def test_staging_requires_explicit_network_allowlists(monkeypatch: pytest.MonkeyPatch) -> None:
    with pytest.raises(SystemExit, match="CORS_ORIGINS"):
        _load_config(monkeypatch, CORS_ORIGINS="")

    with pytest.raises(SystemExit, match="TRUSTED_HOSTS"):
        _load_config(monkeypatch, TRUSTED_HOSTS="")


def test_staging_rejects_demo_mode(monkeypatch: pytest.MonkeyPatch) -> None:
    with pytest.raises(SystemExit, match="DEMO_MODE"):
        _load_config(monkeypatch, DEMO_MODE="true")
