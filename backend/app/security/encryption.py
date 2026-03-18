import os
import logging
from cryptography.fernet import Fernet

_logger = logging.getLogger("gula.encryption")

# Use persistent key from environment variable
# Generate one with: python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
_key = os.getenv("ENCRYPTION_KEY")
if _key:
    try:
        cipher = Fernet(_key.encode() if isinstance(_key, str) else _key)
    except Exception:
        _logger.error(
            "[SECURITY] ENCRYPTION_KEY is invalid (must be a URL-safe base64-encoded 32-byte key). "
            "Generate one with: python3 -c \"from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())\". "
            "Falling back to ephemeral key - encrypted data will be LOST on restart."
        )
        _key = Fernet.generate_key()
        cipher = Fernet(_key)
else:
    # Fallback: generate ephemeral key - data won't persist across restarts
    _key = Fernet.generate_key()
    cipher = Fernet(_key)
    _logger.warning(
        "[SECURITY] ENCRYPTION_KEY not set! Using ephemeral key. "
        "Encrypted data will be LOST on restart. Set ENCRYPTION_KEY env var for production."
    )


def encrypt(data: str) -> str:
    """Encrypt a string value."""
    return cipher.encrypt(data.encode()).decode()


def decrypt(data: str) -> str:
    """Decrypt an encrypted string value."""
    return cipher.decrypt(data.encode()).decode()
