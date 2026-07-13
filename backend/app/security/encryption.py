"""Encryption — delegates to canonical shared.security.

All encryption operations use the canonical Fernet-based implementation
from the shared library. Backend-specific key loading is kept here for
backward compatibility, but all actual encrypt/decrypt logic is from shared.
"""

from __future__ import annotations

import logging
import os
import sys

from shared.security import decrypt_value as _shared_decrypt
from shared.security import encrypt_value as _shared_encrypt

_logger = logging.getLogger("gula.encryption")
_IS_PRODUCTION = os.getenv("ENV", "production") == "production"

_key = os.getenv("ENCRYPTION_KEY")
if not _key:
    if _IS_PRODUCTION:
        sys.exit(1)
    from cryptography.fernet import Fernet

    _key = Fernet.generate_key().decode()
    _logger.warning(
        "[SECURITY] ENCRYPTION_KEY not set — using ephemeral key. "
        "Set ENCRYPTION_KEY in .env for production."
    )


def encrypt(data: str) -> str:
    return _shared_encrypt(data, _key)


def decrypt(data: str) -> str:
    return _shared_decrypt(data, _key)
