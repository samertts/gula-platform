from __future__ import annotations

import logging

logger = logging.getLogger("gula.shared.security")


def _get_fernet(key: str | None = None):
    from cryptography.fernet import Fernet
    if key:
        return Fernet(key.encode() if isinstance(key, str) else key)
    return None


def encrypt_value(value: str, key: str) -> str:
    f = _get_fernet(key)
    if f is None:
        raise ValueError("Encryption key is required")
    return f.encrypt(value.encode()).decode()


def decrypt_value(token: str, key: str) -> str:
    from cryptography.fernet import InvalidToken

    f = _get_fernet(key)
    if f is None:
        raise ValueError("Encryption key is required")
    try:
        return f.decrypt(token.encode()).decode()
    except InvalidToken as exc:
        raise ValueError(f"Invalid or corrupted ciphertext: {exc}") from exc


def encrypt_national_id(nid: str, encryption_key: str, hmac_key: str) -> str:
    from shared.security.hmac import hmac_sign
    encrypted = encrypt_value(nid, encryption_key)
    return hmac_sign(encrypted, hmac_key)


def decrypt_national_id(secure_token: str, encryption_key: str, hmac_key: str) -> str | None:
    from shared.security.hmac import hmac_verify
    try:
        payload = secure_token.rsplit(".", 1)[0]
        signature = secure_token.rsplit(".", 1)[1] if "." in secure_token else ""
        if not hmac_verify(payload, signature, hmac_key):
            logger.warning("HMAC verification failed for national ID")
            return None
        return decrypt_value(payload, encryption_key)
    except Exception as exc:
        logger.error("Failed to decrypt national ID: %s", exc)
        return None
