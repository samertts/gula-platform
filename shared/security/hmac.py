from __future__ import annotations

import hashlib
import hmac as _hmac
import logging

logger = logging.getLogger("gula.shared.security.hmac")


def hmac_sign(data: str, key: str) -> str:
    sig = _hmac.new(key.encode(), data.encode(), hashlib.sha256).hexdigest()
    return f"{data}.{sig}"


def hmac_verify(data: str, signature: str, key: str) -> bool:
    expected = _hmac.new(key.encode(), data.encode(), hashlib.sha256).hexdigest()
    return _hmac.compare_digest(expected, signature)
