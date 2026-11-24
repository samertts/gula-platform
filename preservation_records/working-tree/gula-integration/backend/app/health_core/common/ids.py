"""Synthetic identifier primitives.

All Health Core development identifiers are prefixed ``SYN-`` and are generated
locally. This module also rejects shapes that resemble real national identifiers
so a real NID can never leak into a synthetic fixture by accident.
"""

from __future__ import annotations

import re
from uuid import uuid4

from app.health_core.common.errors import InvalidSyntheticReferenceError

SYNTHETIC_PREFIX = "SYN-"
_PREFIX_RE = re.compile(r"^[A-Z]{2,8}$")
_DIGIT_ONLY_RE = re.compile(r"^\d{5,}$")
_LONG_ALNUM_RE = re.compile(r"^[A-Z0-9]{9,}$")


def new_synthetic_id(prefix: str) -> str:
    """Return a new locally generated synthetic id, e.g. ``SYN-PAT-3F2A…``."""
    clean = prefix.strip().upper().replace("-", "")
    if not _PREFIX_RE.fullmatch(clean):
        raise ValueError(f"invalid synthetic id prefix: {prefix!r}")
    return f"{SYNTHETIC_PREFIX}{clean}-{uuid4().hex[:12].upper()}"


def is_synthetic_id(value: object) -> bool:
    """Cheap ``SYN-`` prefix and minimum-length *shape* check, not a proof of generation.

    Hand-written fixture ids such as ``SYN-KEY-0001`` and arbitrary suffixes
    deliberately pass so synthetic tests stay concise; only the prefix and a
    minimum length are required. Boundaries that must accept a strictly generated
    identifier use the per-type validators in ``fhir/support.py`` or
    ``require_synthetic_ref`` with an explicit prefix. Do not rely on this
    predicate alone to validate untrusted input.
    """
    return isinstance(value, str) and value.startswith(SYNTHETIC_PREFIX) and len(value) > 8


def reject_national_identifier(value: str, *, field: str) -> None:
    """Reject values that look like a national id, phone, or real-world key.

    This is a deliberate allow-list boundary: Health Core development accepts
    only opaque ``SYN-`` references, never raw identifiers.
    """
    if not isinstance(value, str):
        raise InvalidSyntheticReferenceError(
            f"{field} must be a string synthetic reference",
            details={"field": field},
        )
    stripped = value.strip()
    if not stripped:
        raise InvalidSyntheticReferenceError(f"{field} must not be empty", details={"field": field})
    if _DIGIT_ONLY_RE.fullmatch(stripped) or _LONG_ALNUM_RE.fullmatch(stripped):
        raise InvalidSyntheticReferenceError(
            f"{field} resembles a real identifier; use a synthetic SYN- reference",
            details={"field": field},
        )
