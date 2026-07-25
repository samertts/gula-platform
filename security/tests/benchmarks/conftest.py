from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

SECURITY_DIR = Path(__file__).resolve().parent.parent.parent
if str(SECURITY_DIR) not in sys.path:
    sys.path.insert(0, str(SECURITY_DIR))


@pytest.fixture(scope="session")
def benchmark_enabled(request):
    return request.config.getoption("--benchmark-disable", default=True) is False


@pytest.fixture(scope="session")
def crypto_fixtures():
    from security.modules.crypto.aes import AES256GCMCipher
    from security.modules.crypto.argon import Argon2idHasher
    from security.modules.crypto.hashing import SHA256Hasher
    from security.modules.crypto.random import SecureRandom
    from security.modules.crypto.signing import Ed25519Signer, HMACSigner

    return {
        "aes": AES256GCMCipher(),
        "argon2": Argon2idHasher(),
        "ed25519": Ed25519Signer(),
        "hmac": HMACSigner(),
        "sha": SHA256Hasher(),
        "random": SecureRandom(),
    }


@pytest.fixture(scope="session")
def auth_fixtures():
    from security.modules.identity.jwt import JWTManager
    from security.modules.identity.rbac import RBACEngine

    return {
        "jwt": JWTManager(),
        "rbac": RBACEngine(),
    }


@pytest.fixture(scope="session")
def audit_fixtures():
    from security.modules.audit.immutable import ImmutableAuditLog
    from security.modules.audit.service import AuditService

    return {
        "audit": AuditService(),
        "immutable": ImmutableAuditLog(),
    }
