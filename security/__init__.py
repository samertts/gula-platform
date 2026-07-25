GULA Security Framework (GSF) — Permanent Enterprise Security Subsystem.

GSF provides comprehensive security capabilities for the GULA National Healthcare
Platform, covering identity, secrets, cryptography, authentication, authorization,
audit, compliance, and infrastructure security domains.

Typical usage:
    from security import GSF_VERSION
    from security.modules.identity import IdentityProvider
    from security.modules.crypto import CryptoEngine
    from security.modules.authentication import Authenticator
"""

import importlib.metadata as _metadata

try:
    GSF_VERSION = _metadata.version("gula-security-framework")
except _metadata.PackageNotFoundError:
    GSF_VERSION = "1.0.0"

__version__ = GSF_VERSION
__author__ = "GULA Platform Engineering"
__license__ = "Apache-2.0"

__all__ = [
    "GSF_VERSION",
]
