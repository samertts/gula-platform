from __future__ import annotations

import hashlib
import hmac
import struct
import time
from typing import Any

import pyotp


def generate_totp_secret() -> str:
    return pyotp.random_base32()


def generate_totp_uri(secret: str, email: str, issuer: str = "GULA Health") -> str:
    return pyotp.totp.TOTP(secret).provisioning_uri(name=email, issuer_name=issuer)


def verify_totp(secret: str, token: str, drift: int = 1) -> bool:
    totp = pyotp.TOTP(secret)
    return totp.verify(token, valid_window=drift)


def generate_backup_codes(count: int = 8) -> list[str]:
    import secrets
    return [secrets.token_hex(4).upper() for _ in range(count)]


def verify_backup_code(code: str, stored_hashes: list[str]) -> str | None:
    for stored in stored_hashes:
        if hashlib.sha256(code.encode()).hexdigest() == stored:
            return stored
    return None


def hash_backup_codes(codes: list[str]) -> list[str]:
    return [hashlib.sha256(c.encode()).hexdigest() for c in codes]


def generate_recovery_token() -> str:
    import secrets
    return secrets.token_urlsafe(32)


def verify_hotp(secret: str, token: str, counter: int, window: int = 5) -> tuple[bool, int]:
    for offset in range(window):
        expected = _hotp_at(secret, counter + offset)
        if hmac.compare_digest(str(expected), token):
            return True, counter + offset + 1
    return False, counter


def _hotp_at(secret: str, counter: int) -> str:
    msg = struct.pack(">Q", counter)
    key = _base32_decode(secret)
    h = hmac.new(key, msg, hashlib.sha1).digest()
    offset = h[-1] & 0x0F
    code = (struct.unpack(">I", h[offset:offset + 4])[0] & 0x7FFFFFFF) % 1000000
    return f"{code:06d}"


def _base32_decode(secret: str) -> bytes:
    import base64
    padded = secret.upper() + "=" * ((8 - len(secret) % 8) % 8)
    return base64.b32decode(padded)
