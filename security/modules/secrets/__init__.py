"""GSF-002: Secrets Module — Encrypted secret storage.

Manages secure storage and retrieval of secrets (API keys, database credentials,
certificates) with support for multiple backends including HashiCorp Vault,
AWS Secrets Manager, and encrypted local storage.

Exports:
    SecretType: Enumeration of supported secret types
    SecretMetadata: Secret metadata model
    SecretRotationPolicy: Rotation policy configuration
    SecretValidationResult: Secret strength validation result
    SecretConfig: Backend configuration model
    SecretManager: Unified secret management service
    SecretScanner: Secret detection and scanning
    RotationEngine: Automatic secret rotation engine
    SecretBackend: Abstract secret storage backend
    SecretRotator: Abstract rotation policy
    SecretValidator: Abstract validation interface
"""

from security.modules.secrets.base import SecretBackend, SecretRotator, SecretValidator
from security.modules.secrets.models import (
    SecretConfig,
    SecretMetadata,
    SecretRotationPolicy,
    SecretType,
    SecretValidationResult,
)
from security.modules.secrets.rotation import RotationEngine
from security.modules.secrets.scanner import SecretScanner
from security.modules.secrets.service import SecretManager

__all__ = [
    "SecretBackend",
    "SecretConfig",
    "SecretManager",
    "SecretMetadata",
    "SecretRotator",
    "SecretRotationPolicy",
    "SecretScanner",
    "SecretType",
    "SecretValidationResult",
    "SecretValidator",
    "RotationEngine",
]
