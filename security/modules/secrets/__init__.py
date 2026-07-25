GSF-002: Secrets Module — Encrypted secret storage.

Manages secure storage and retrieval of secrets (API keys, database credentials,
certificates) with support for multiple backends including HashiCorp Vault,
AWS Secrets Manager, and encrypted local storage.

Exports:
    SecretsEngine: Core secrets management engine
    VaultBackend: HashiCorp Vault backend
    AwsSecretsManagerBackend: AWS Secrets Manager backend
    LocalEncryptedBackend: AES-256-GCM encrypted local storage
    SecretRotator: Automatic secret rotation scheduler
"""

from security.modules.secrets.engine import SecretsEngine
from security.modules.secrets.backends.vault import VaultBackend
from security.modules.secrets.backends.aws import AwsSecretsManagerBackend
from security.modules.secrets.backends.local import LocalEncryptedBackend
from security.modules.secrets.rotation import SecretRotator

__all__ = [
    "SecretsEngine",
    "VaultBackend",
    "AwsSecretsManagerBackend",
    "LocalEncryptedBackend",
    "SecretRotator",
]
