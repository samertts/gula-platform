from __future__ import annotations

import re
import secrets
import string
from collections.abc import Generator
from typing import Any


def slugify(text: str) -> str:
    text = text.strip().lower()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_]+", "-", text)
    return text.strip("-")


def truncate(text: str, max_length: int = 100, suffix: str = "...") -> str:
    if len(text) <= max_length:
        return text
    return text[:max_length].rstrip() + suffix


def parse_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (ValueError, TypeError):
        return default


def parse_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (ValueError, TypeError):
        return default


def mask_string(value: str, visible_chars: int = 4, mask_char: str = "*") -> str:
    if len(value) <= visible_chars:
        return value
    return value[:visible_chars] + mask_char * (len(value) - visible_chars)


def generate_token(length: int = 32) -> str:
    chars = string.ascii_letters + string.digits
    return "".join(secrets.choice(chars) for _ in range(length))


_EMAIL_PATTERN = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")
_PHONE_PATTERN = re.compile(r"^\+?[0-9]{10,15}$")
_IRAQI_NID_PATTERN = re.compile(r"^\d{10,14}$")


def is_valid_email(email: str) -> bool:
    return bool(_EMAIL_PATTERN.match(email))


def is_valid_phone(phone: str) -> bool:
    return bool(_PHONE_PATTERN.match(phone))


def is_valid_iraqi_nid(nid: str) -> bool:
    return bool(_IRAQI_NID_PATTERN.match(nid))


def sanitize_html(html: str) -> str:
    import html as _html
    return _html.escape(html)


def chunks(lst: list[Any], size: int) -> Generator[list[Any]]:
    for i in range(0, len(lst), size):
        yield lst[i : i + size]
