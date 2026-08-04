"""Secret resolution for GULA Communication Providers (PROGRAM-COMM-002).

Every provider loads configuration ONLY from:

  - Environment variables (``COMMUNICATION_*``-prefixed or provider-native)
  - Docker secrets  (``/run/secrets/<name>``)
  - Kubernetes secrets (mounted files, conventionally ``/etc/secrets/<name>``
    or any directory configured through ``GULA_SECRETS_DIR``)
  - Cloud secrets (injected by the platform as env vars or mounted files;
    the resolver treats them uniformly — no vendor-specific coupling)

Provider code never hardcodes API keys, tokens, webhook URLs or phone
numbers. Values resolved here are intended for redaction-aware logging via
:class:`shared.communication_providers.base.Redactor`.
"""

from __future__ import annotations

import logging
import os
from collections.abc import Mapping
from dataclasses import dataclass

logger = logging.getLogger("gula.communication.providers.secrets")

# Docker mounts secrets at /run/secrets/<name>; Kubernetes deployments in this
# platform mount secrets at /etc/secrets/<name> (overridable).
DOCKER_SECRETS_DIR = "/run/secrets"
KUBERNETES_SECRETS_DIR = "/etc/secrets"
_ENV_OVERRIDE = "GULA_SECRETS_DIR"


def _secrets_dirs() -> list[str]:
    """Candidate secret directories in lookup priority order."""
    overrides = os.getenv(_ENV_OVERRIDE, "").strip()
    if overrides:
        return [d for d in overrides.split(":") if d]
    return [DOCKER_SECRETS_DIR, KUBERNETES_SECRETS_DIR]


@dataclass(frozen=True)
class SecretSpec:
    """How a provider names its secret in each source.

    ``env_names`` are checked in order (first non-empty wins); ``file_names``
    are the docker/k8s secret file names (lowercased by convention).
    """

    env_names: tuple[str, ...]
    file_names: tuple[str, ...] = ()


class SecretResolver:
    """Resolve named secrets from env → docker → k8s → cloud-mounted files.

    DI-friendly: ``env`` and ``secret_dirs`` are injectable for tests; the
    defaults read the real process environment.
    """

    def __init__(
        self,
        env: Mapping[str, str] | None = None,
        secret_dirs: list[str] | None = None,
    ) -> None:
        self._env = env if env is not None else os.environ
        self._secret_dirs = secret_dirs if secret_dirs is not None else _secrets_dirs()

    def resolve(self, spec: SecretSpec, default: str = "") -> str:
        """First non-empty value wins: env vars, then secret files."""
        for name in spec.env_names:
            value = self._env.get(name, "")
            if value:
                return value
        for name in spec.file_names:
            value = self._read_secret_file(name)
            if value is not None:
                return value
        return default

    def resolve_required(self, spec: SecretSpec, hint: str) -> str:
        """Like :meth:`resolve` but logs a structured warning when missing."""
        value = self.resolve(spec)
        if not value:
            logger.warning(
                "communication_provider_secret_missing hint=%s sources=%s",
                hint,
                ",".join(spec.env_names),
            )
        return value

    def get(self, env_name: str, default: str = "") -> str:
        """Resolve a plain environment value (no secret-file fallback)."""
        return self._env.get(env_name, default)

    def get_bool(self, env_name: str, default: bool = False) -> bool:
        value = self._env.get(env_name, "")
        if value == "":
            return default
        return value.strip().lower() in ("1", "true", "yes", "on")

    def get_int(self, env_name: str, default: int) -> int:
        value = self._env.get(env_name, "")
        if value == "":
            return default
        try:
            return int(value)
        except ValueError:
            logger.warning("communication_provider_config_invalid name=%s", env_name)
            return default

    def _read_secret_file(self, name: str) -> str | None:
        """Read a secret file, returning None when absent/unreadable."""
        for directory in self._secret_dirs:
            path = os.path.join(directory, name)
            if not os.path.isfile(path):
                continue
            try:
                with open(path, encoding="utf-8") as fh:
                    value = fh.read().strip()
                if value:
                    return value
            except OSError:
                logger.warning("communication_provider_secret_unreadable path=%s", path)
        return None


def webhook_secret_name(kind: str) -> SecretSpec:
    """Convention: ``<KIND>_WEBHOOK_URL`` env + ``<kind>_webhook_url`` file."""
    upper = kind.upper()
    return SecretSpec(
        env_names=(f"{upper}_WEBHOOK_URL",),
        file_names=(f"{kind}_webhook_url",),
    )


def token_secret_name(kind: str) -> SecretSpec:
    """Convention: ``<KIND>_API_KEY`` / ``<KIND>_BOT_TOKEN`` env + file."""
    upper = kind.upper()
    return SecretSpec(
        env_names=(f"{upper}_API_KEY", f"{upper}_BOT_TOKEN", f"{upper}_TOKEN"),
        file_names=(f"{kind}_api_key", f"{kind}_bot_token"),
    )


__all__ = [
    "DOCKER_SECRETS_DIR",
    "KUBERNETES_SECRETS_DIR",
    "SecretResolver",
    "SecretSpec",
    "token_secret_name",
    "webhook_secret_name",
]
