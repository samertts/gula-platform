"""Secret resolution tests: env, docker secrets, k8s secrets, cloud-mounted
files (PROGRAM-COMM-002)."""

from __future__ import annotations

import os

from shared.communication_providers.secrets import (
    SecretResolver,
    SecretSpec,
    token_secret_name,
    webhook_secret_name,
)


class TestSecretResolver:
    def test_env_wins(self, tmp_path, monkeypatch):
        monkeypatch.setenv("TEST_API_KEY", "from-env")
        resolver = SecretResolver(secret_dirs=[str(tmp_path)])
        assert resolver.resolve(SecretSpec(env_names=("TEST_API_KEY",))) == "from-env"

    def test_file_fallback(self, tmp_path, monkeypatch):
        (tmp_path / "test_api_key").write_text("from-docker-secret\n")
        resolver = SecretResolver(secret_dirs=[str(tmp_path)])
        assert resolver.resolve(SecretSpec(env_names=("MISSING_ENV",), file_names=("test_api_key",))) == "from-docker-secret"

    def test_env_beats_file(self, tmp_path, monkeypatch):
        (tmp_path / "dual_key").write_text("file-value")
        monkeypatch.setenv("DUAL_ENV", "env-value")
        resolver = SecretResolver(secret_dirs=[str(tmp_path)])
        spec = SecretSpec(env_names=("DUAL_ENV",), file_names=("dual_key",))
        assert resolver.resolve(spec) == "env-value"

    def test_default_when_missing(self, tmp_path):
        resolver = SecretResolver(secret_dirs=[str(tmp_path)])
        assert resolver.resolve(SecretSpec(env_names=("NOT_SET_ANYWHERE",)), default="fallback") == "fallback"

    def test_docker_dir_default(self):
        assert "/run/secrets" in os.environ.get("PATH", "") or True  # placeholder guard
        resolver = SecretResolver()
        assert resolver._secret_dirs[0] == "/run/secrets"

    def test_bool_and_int(self, monkeypatch):
        monkeypatch.setenv("FLAG_A", "true")
        monkeypatch.setenv("FLAG_B", "0")
        monkeypatch.setenv("COUNT", "42")
        resolver = SecretResolver()
        assert resolver.get_bool("FLAG_A") is True
        assert resolver.get_bool("FLAG_B") is False
        assert resolver.get_bool("FLAG_C", default=True) is True
        assert resolver.get_int("COUNT", 0) == 42
        assert resolver.get_int("BAD", 7) == 7

    def test_conventions(self):
        webhook = webhook_secret_name("discord")
        assert webhook.env_names == ("DISCORD_WEBHOOK_URL",)
        assert webhook.file_names == ("discord_webhook_url",)
        token = token_secret_name("slack")
        assert token.env_names == ("SLACK_API_KEY", "SLACK_BOT_TOKEN", "SLACK_TOKEN")

    def test_resolve_required_logs_warning(self, caplog):
        import logging

        resolver = SecretResolver(secret_dirs=["/nonexistent"])
        with caplog.at_level(logging.WARNING):
            value = resolver.resolve_required(SecretSpec(env_names=("NOPE_XYZ",)), hint="test")
        assert value == ""
        assert any("communication_provider_secret_missing" in r.message for r in caplog.records)
