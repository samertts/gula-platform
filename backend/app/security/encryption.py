import os
import sys
import logging
from cryptography.fernet import Fernet

_logger = logging.getLogger("gula.encryption")
_IS_PRODUCTION = os.getenv("ENV", "production") == "production"

# Use persistent key from environment variable.
# Generate with: python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
_key = os.getenv("ENCRYPTION_KEY")
if _key:
    try:
        cipher = Fernet(_key.encode() if isinstance(_key, str) else _key)
    except Exception:
        # Detect legacy hex key (64-char hex string from secrets.token_hex(32))
        # and give a more targeted error message.
        _is_hex_key = len(_key) == 64 and all(c in "0123456789abcdefABCDEF" for c in _key)
        if _is_hex_key:
            msg = (
                "[SECURITY] ENCRYPTION_KEY is a 64-char hex string (old format). "
                "Fernet requires a 44-char URL-safe base64 key. "
                "Fix with: bash scripts/fix-encryption-key.sh  "
                "OR regenerate manually: python3 -c \"from cryptography.fernet import Fernet; "
                "print(Fernet.generate_key().decode())\""
            )
        else:
            msg = (
                "[SECURITY] ENCRYPTION_KEY is set but is NOT a valid Fernet key "
                "(must be 32 random bytes, URL-safe base64-encoded, 44 chars). "
                "Fix with: bash scripts/fix-encryption-key.sh  "
                "OR regenerate: python3 -c \"from cryptography.fernet import Fernet; "
                "print(Fernet.generate_key().decode())\""
            )
        if _IS_PRODUCTION:
            # In production, an invalid key is a crash — don't silently lose data.
            print(f"[GULA FATAL] {msg}", file=sys.stderr)
            sys.exit(1)
        _logger.error("%s — Falling back to ephemeral key (data lost on restart)", msg)
        _key = Fernet.generate_key()
        cipher = Fernet(_key)
else:
    if _IS_PRODUCTION:
        # config.py already checks this, but belt-and-suspenders
        print("[GULA FATAL] ENCRYPTION_KEY not set in production.", file=sys.stderr)
        sys.exit(1)
    # Dev fallback
    _key = Fernet.generate_key()
    cipher = Fernet(_key)
    _logger.warning(
        "[SECURITY] ENCRYPTION_KEY not set — using ephemeral key. "
        "Set ENCRYPTION_KEY in .env for production."
    )


def encrypt(data: str) -> str:
    """Encrypt a string value."""
    return cipher.encrypt(data.encode()).decode()


def decrypt(data: str) -> str:
    """Decrypt an encrypted string value."""
    return cipher.decrypt(data.encode()).decode()
